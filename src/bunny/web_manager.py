from pathlib import Path
import os
import subprocess
import time
import requests
import threading
import uuid

from fastapi import FastAPI, HTTPException, Request
import json
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .models import MODEL_REGISTRY, MODEL_DIR, find_model_file
from .downloader import get_downloader
import signal
from huggingface_hub import hf_hub_url
import shutil
import sys
try:
    import psutil  # optional
except Exception:
    psutil = None  # type: ignore
import socket

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Bunny Web Manager (local-only)")

# Simple in-memory process tracker
_server_proc = None
_server_info = {}
_server_log_file = None
_server_log_path = None
_hf_token_file = Path.home() / '.bunny' / '.hf_token'
_settings_file = Path.home() / '.bunny' / 'settings.json'
_workspaces_file = Path.home() / '.bunny' / 'workspaces.json'

_DEFAULT_SETTINGS = {
    "ui": {
        "port": 8080,
        "theme": "dark",
        "font_size": 14,
        "streaming": True
    },
    "server": {
        "host": "127.0.0.1",
        "inference_port": 8081,
        "auto_restart": False,
        "log_level": "info"
    },
    "runtime": {
        "ctx_size": 2048,
        "threads": max(1, (os.cpu_count() or 4)),
        "ngl": -1
    },
    "generation": {
        "temperature": 0.7,
        "top_p": 1.0,
        "top_k": 40,
        "max_tokens": 256,
        "seed": None,
        "stop": []
    },
    "system_prompt": "You are a helpful assistant.",
}

def _load_settings():
    try:
        if _settings_file.exists():
            return json.loads(_settings_file.read_text())
    except Exception:
        pass
    return dict(_DEFAULT_SETTINGS)

def _save_settings(s: dict):
    try:
        _settings_file.parent.mkdir(parents=True, exist_ok=True)
        _settings_file.write_text(json.dumps(s, indent=2))
        return True
    except Exception:
        return False

def _load_workspaces():
    try:
        if _workspaces_file.exists():
            return json.loads(_workspaces_file.read_text())
    except Exception:
        pass
    # default: one Personal workspace with Default project
    default = {
        'workspaces': [
            {
                'id': 'personal',
                'name': 'Personal',
                'projects': [ { 'id': 'default', 'name': 'Default', 'description': '', 'visibility': 'private' } ],
            }
        ],
        'active': { 'workspace_id': 'personal', 'project_id': 'default' }
    }
    return default

def _save_workspaces(w: dict):
    try:
        _workspaces_file.parent.mkdir(parents=True, exist_ok=True)
        _workspaces_file.write_text(json.dumps(w, indent=2))
        return True
    except Exception:
        return False


def _read_hf_token():
    """Try to read HF token from keyring (if available) or fallback file."""
    try:
        import keyring
        tok = keyring.get_password('bunny', 'hf_token')
        if tok:
            return tok
    except Exception:
        pass
    try:
        if _hf_token_file.exists():
            return _hf_token_file.read_text().strip()
    except Exception:
        pass
    return None


def _write_hf_token(token: str):
    try:
        import keyring
        keyring.set_password('bunny', 'hf_token', token)
        return True
    except Exception:
        try:
            _hf_token_file.parent.mkdir(parents=True, exist_ok=True)
            _hf_token_file.write_text(token)
            return True
        except Exception:
            return False


# Download functions now handled by shared downloader module



def _llama_bin_path() -> Path:
    """Return the best-effort path to a compiled `llama-server` binary.

    Search order (first hit returned):
    - ~/.bunny/llama.cpp/build/bin/llama-server
    - workspace-local copies (e.g. GITHUB/llama.cpp, llama-cpp-python/vendor/llama.cpp)
    - system PATH (which llama-server)
    If none found, return the default ~/.bunny path so callers keep previous behavior.
    """
    candidates = []
    bun = Path.home() / ".bunny"
    # default expected location
    candidates.append(bun / "llama.cpp" / "build" / "bin" / "llama-server")
    if os.name == "nt":
        candidates.insert(0, bun / "llama.cpp" / "build" / "Release" / "llama-server.exe")

    # Walk up from this repo's src directory and probe sibling/common locations
    repo_root = Path(__file__).resolve().parent
    # climb a few levels and check for nearby `llama.cpp` folders
    p = repo_root
    for _ in range(5):
        candidates.append(p.parent / "llama.cpp" / "build" / "bin" / "llama-server")
        p = p.parent

    # system PATH fallback
    try:
        import shutil as _sh
        which_path = _sh.which("llama-server")
        if which_path:
            candidates.append(Path(which_path))
    except Exception:
        pass

    # return first existing executable candidate
    for c in candidates:
        try:
            if c and c.exists() and c.is_file():
                # basic executability check
                if os.access(str(c), os.X_OK) or os.name == 'nt':
                    return c
        except Exception:
            continue

    # fallback to the original expected path
    return bun / "llama.cpp" / "build" / "bin" / "llama-server"


@app.get("/api/models")
def list_models():
    out = []
    for name, info in MODEL_REGISTRY.items():
        # Strict check: only consider exact registry filename installed
        path = find_model_file(name, info.get("filename"), use_fallback=False)
        installed = bool(path)
        size = path.stat().st_size if path else None
        out.append({
            "name": name,
            "repo_id": info.get("repo_id"),
            "filename": info.get("filename"),
            "chat_format": info.get("chat_format"),
            "installed": installed,
            "size": size,
            "path": str(path) if path else None,
        })
    return JSONResponse(out)


@app.post("/api/models/pull")
async def pull_model(req: Request):
    """Start a background pull job and return a job_id. Progress is available via /api/models/pull/stream?job_id=..."""
    body = await req.json()
    model = body.get("model")
    repo = body.get("repo")
    file = body.get("file")
    if not model:
        raise HTTPException(status_code=400, detail="Missing model name")

    # verify huggingface_hub available
    try:
        __import__('huggingface_hub')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'huggingface_hub not available: {e}')

    # Determine model parameters
    if repo and file:
        repo_id = repo
        filename = file
    else:
        if model not in MODEL_REGISTRY:
            raise HTTPException(status_code=400, detail="Unknown model")
        info = MODEL_REGISTRY[model]
        repo_id = info.get("repo_id")
        filename = info.get("filename")

    # Get HF token
    hf_token = os.environ.get('HF_HUB_TOKEN') or os.environ.get('HF_TOKEN')
    if not hf_token:
        hf_token = _read_hf_token()

    # Create download job using shared downloader
    downloader = get_downloader(MODEL_DIR)
    job_id = downloader.create_job(model, repo_id, filename, hf_token)
    
    # Start download
    if downloader.start_download(job_id):
        return JSONResponse({"ok": True, "job_id": job_id})
    else:
        raise HTTPException(status_code=500, detail="Failed to start download")


@app.get("/api/models/pull/status")
def pull_status(job_id: str):
    downloader = get_downloader(MODEL_DIR)
    job = downloader.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert job to dict for JSON response
    job_dict = {
        "id": job.job_id,
        "model": job.model_name,
        "repo": job.repo_id,
        "file": job.filename,
        "status": job.status,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "error": job.error,
        "downloaded": job.downloaded,
        "size": job.size,
        "path": str(job.path) if job.path else None,
        "cancel": job.cancel
    }
    return JSONResponse(job_dict)



@app.post('/api/models/pull/retry')
def pull_retry(job_id: str):
    """Retry a failed or cancelled pull job by job_id. If a .part exists we will resume."""
    downloader = get_downloader(MODEL_DIR)
    job = downloader.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    if job.status not in ('failed', 'cancelled'):
        return JSONResponse({'ok': False, 'error': 'Job not in failed/cancelled state'})
    
    # Get HF token
    hf_token = os.environ.get('HF_HUB_TOKEN') or os.environ.get('HF_TOKEN')
    if not hf_token:
        hf_token = _read_hf_token()
    
    # create a new job entry reusing model/repo/file
    new_job_id = downloader.create_job(job.model_name, job.repo_id, job.filename, hf_token)
    
    # start download in background
    if downloader.start_download(new_job_id):
        return JSONResponse({'ok': True, 'job_id': new_job_id})
    else:
        raise HTTPException(status_code=500, detail="Failed to start retry job")


@app.get("/api/models/pull/stream")
def pull_stream(job_id: str):
    """Stream progress as simple JSON lines over SSE for a given job."""
    downloader = get_downloader(MODEL_DIR)
    job = downloader.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    def event_stream():
        while True:
            job = downloader.get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'error':'not found'})}\n\n"
                break
            
            # send progress snapshot as JSON
            payload = {
                'status': job.status,
                'downloaded': job.downloaded,
                'size': job.size,
                'error': job.error,
                'path': str(job.path) if job.path else None,
            }
            yield f"data: {json.dumps(payload)}\n\n"
            if job.status in ('done', 'failed', 'cancelled'):
                break
            time.sleep(0.6)

    return StreamingResponse(event_stream(), media_type='text/event-stream')


@app.post('/api/models/pull/cancel')
def pull_cancel(job_id: str):
    downloader = get_downloader(MODEL_DIR)
    if not downloader.cancel_job(job_id):
        raise HTTPException(status_code=404, detail='Job not found')
    return JSONResponse({'ok': True})


@app.get("/api/downloads")
def list_downloads():
    """List all download jobs."""
    downloader = get_downloader(MODEL_DIR)
    jobs = downloader.get_all_jobs()
    jobs_dict = {}
    for job in jobs:
        jobs_dict[job.job_id] = {
            "id": job.job_id,
            "model": job.model_name,
            "repo": job.repo_id,
            "file": job.filename,
            "status": job.status,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "error": job.error,
            "downloaded": job.downloaded,
            "size": job.size,
            "path": str(job.path) if job.path else None,
            "cancel": job.cancel
        }
    return JSONResponse(jobs_dict)


@app.get("/api/downloads/active")
def list_active_downloads():
    """List only active (running/queued) download jobs."""
    downloader = get_downloader(MODEL_DIR)
    active_jobs = downloader.get_active_jobs()
    jobs_dict = {}
    for job in active_jobs:
        jobs_dict[job.job_id] = {
            "id": job.job_id,
            "model": job.model_name,
            "repo": job.repo_id,
            "file": job.filename,
            "status": job.status,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "error": job.error,
            "downloaded": job.downloaded,
            "size": job.size,
            "path": str(job.path) if job.path else None,
            "cancel": job.cancel
        }
    return JSONResponse(jobs_dict)


@app.delete("/api/downloads/{job_id}")
def delete_download(job_id: str):
    """Cancel and remove a download job."""
    downloader = get_downloader(MODEL_DIR)
    if not downloader.cancel_job(job_id):
        raise HTTPException(status_code=404, detail='Job not found')
    return JSONResponse({'ok': True})


@app.post("/api/downloads/cleanup")
def cleanup_downloads():
    """Clean up completed/failed jobs older than 1 hour."""
    downloader = get_downloader(MODEL_DIR)
    removed_count = downloader.cleanup_old_jobs()
    return JSONResponse({'ok': True, 'removed_count': removed_count})


@app.post("/api/server/start")
async def server_start(req: Request):
    global _server_proc, _server_info
    body = await req.json()
    model = body.get("model")
    port = int(body.get("port", 8081))
    ctx_size = int(body.get("ctx_size", 2048))

    if _server_proc and _server_proc.poll() is None:
        # If a server is already running with the same model, acknowledge; else signal conflict
        current_model = _server_info.get("model")
        if current_model and isinstance(current_model, str):
            # Resolve desired path (strict if registered)
            desired_path = None
            if model in MODEL_REGISTRY:
                desired_path = find_model_file(model, MODEL_REGISTRY[model].get("filename"), use_fallback=False)
            else:
                desired_path = find_model_file(model)
            if desired_path and str(desired_path) == current_model:
                return JSONResponse({"ok": True, "pid": _server_info.get("pid"), "port": _server_info.get("port"), "note": "Server already running with requested model"})
        return JSONResponse({"ok": False, "error": "Server already running with a different model", "current_model": current_model}, status_code=409)

    # resolve model path
    path = None
    if model in MODEL_REGISTRY:
        # Strict: do not fallback to similarly named files; require exact registry filename
        path = find_model_file(model, MODEL_REGISTRY[model].get("filename"), use_fallback=False)
    else:
        # try fallback glob
        path = find_model_file(model)

    if not path:
        raise HTTPException(status_code=404, detail="Model file not found")

    llbin = _llama_bin_path()
    if not llbin.exists():
        tried = [
            str(Path.home() / ".bunny" / "llama.cpp" / "build" / "bin" / "llama-server"),
            str(Path.home() / ".bunny" / "llama.cpp" / "build" / "Release" / "llama-server.exe"),
        ]
        raise HTTPException(status_code=500, detail={
            "error": "llama-server binary not found",
            "tried_paths": tried,
            "hint": "Build llama.cpp and ensure `llama-server` is available. See the official repo for build instructions.",
            "docs": "https://github.com/ggml-org/llama.cpp"
        })
    args = [
        str(llbin),
        "-m",
        str(path),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--ctx-size",
        str(ctx_size),
        "--threads",
        str(os.cpu_count() or 4),
    ]

    # Start subprocess and capture logs to a file under ~/.bunny/logs
    logs_dir = Path.home() / '.bunny' / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    logname = f"{path.name}-{int(time.time())}.log"
    logpath = logs_dir / logname
    logf = open(str(logpath), 'a', buffering=1)
    proc = subprocess.Popen(args, stdout=logf, stderr=logf)
    # simple wait loop to check readiness
    start = time.time()
    ready = False
    while time.time() - start < 10:
        try:
            # If using Python-based engine, its readiness endpoint is the same OAI-like /v1/models
            r = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=1)
            if r.status_code in (200, 404, 405):
                ready = True
                break
        except Exception:
            time.sleep(0.2)

    _server_proc = proc
    _server_info = {"pid": proc.pid, "port": port, "model": str(path), "started_at": time.time()}
    # store log file handles so we can stream logs
    global _server_log_file, _server_log_path
    _server_log_file = logf
    _server_log_path = logpath

    if not ready:
        return JSONResponse({"ok": False, "pid": proc.pid, "message": "Server started but did not respond within timeout"})

    return JSONResponse({"ok": True, "pid": proc.pid, "port": port})


@app.get('/api/logs/stream')
def logs_stream():
    """SSE stream of the latest server log file (if any)."""
    if not _server_log_path or not _server_log_path.exists():
        raise HTTPException(status_code=404, detail='No log file')

    def event_stream():
        with open(_server_log_path, 'r') as f:
            # seek to end
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
                else:
                    time.sleep(0.5)

    return StreamingResponse(event_stream(), media_type='text/event-stream')


@app.get('/api/logs/download')
def logs_download():
    """Return the current server log file for download (plain text)."""
    if not _server_log_path or not _server_log_path.exists():
        raise HTTPException(status_code=404, detail='No log file')
    try:
        return StreamingResponse(open(str(_server_log_path), 'rb'), media_type='text/plain')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/hf_token')
async def hf_token_set(req: Request):
    body = await req.json()
    token = body.get('token')
    if not token:
        raise HTTPException(status_code=400, detail='Missing token')
    try:
        ok = _write_hf_token(token)
        if ok:
            return JSONResponse({'ok': True})
        raise RuntimeError('failed to save token')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/hf_token')
def hf_token_get():
    try:
        tok = _read_hf_token()
        return JSONResponse({'token': tok})
    except Exception:
        return JSONResponse({'token': None})


@app.get('/api/settings')
def settings_get():
    return JSONResponse(_load_settings())


@app.post('/api/settings')
async def settings_set(req: Request):
    try:
        body = await req.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Merge with defaults to ensure keys exist
    cur = _load_settings()
    def _merge(a,b):
        for k,v in b.items():
            if isinstance(v, dict):
                a[k] = _merge(a.get(k, {}), v)
            else:
                a[k] = v
        return a
    merged = _merge(cur, body)
    if not _save_settings(merged):
        raise HTTPException(status_code=500, detail='Failed to save settings')
    return JSONResponse({'ok': True})


@app.get('/api/workspaces')
def workspaces_get():
    return JSONResponse(_load_workspaces())


@app.post('/api/workspaces')
async def workspaces_set(req: Request):
    try:
        body = await req.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail='invalid body')
    if not _save_workspaces(body):
        raise HTTPException(status_code=500, detail='Failed to save workspaces')
    return JSONResponse({'ok': True})


@app.post("/api/server/stop")
def server_stop():
    global _server_proc, _server_info
    if not _server_proc:
        return JSONResponse({"ok": False, "error": "No server running"})
    try:
        _server_proc.terminate()
        _server_proc.wait(timeout=5)
    except Exception:
        try:
            _server_proc.kill()
        except Exception:
            pass
    _server_proc = None
    _server_info = {}
    return JSONResponse({"ok": True})


@app.post('/api/generation/cancel')
def generation_cancel():
    """Best-effort cancellation of in-flight generation by sending SIGINT to llama-server process.
    Note: this may terminate the server depending on how llama-server handles signals."""
    global _server_proc
    if not _server_proc:
        return JSONResponse({'ok': False, 'error': 'No server running'})
    try:
        _server_proc.send_signal(signal.SIGINT)
        return JSONResponse({'ok': True})
    except Exception:
        try:
            _server_proc.terminate()
            return JSONResponse({'ok': True, 'note': 'terminated'})
        except Exception:
            return JSONResponse({'ok': False, 'error': 'failed to cancel'})


@app.get("/api/server/status")
def server_status():
    global _server_proc, _server_info
    running = bool(_server_proc and _server_proc.poll() is None)
    info = dict(_server_info)
    info.update({"running": running})
    return JSONResponse(info)


@app.post("/api/chat")
async def chat_proxy(req: Request):
    """Proxy non-streaming chat requests to the local llama-server."""
    body = await req.json()
    # If a desired model is provided, enforce that it is installed and matches the running server
    desired_model = body.get('model')
    running = bool(_server_proc and _server_proc.poll() is None)
    running_path = _server_info.get('model')
    if desired_model:
        if desired_model in MODEL_REGISTRY:
            desired_path = find_model_file(desired_model, MODEL_REGISTRY[desired_model].get('filename'), use_fallback=False)
        else:
            desired_path = find_model_file(desired_model)
        if not desired_path:
            raise HTTPException(status_code=404, detail='Requested model is not installed')
        if not running:
            raise HTTPException(status_code=409, detail='No server running for requested model')
        if str(desired_path) != str(running_path or ''):
            raise HTTPException(status_code=409, detail='Different model is currently running')
    # Determine llama port: prefer tracked server, else default 8081
    port = _server_info.get("port", 8081)
    try:
        r = requests.post(f"http://127.0.0.1:{port}/v1/chat/completions", json=body, timeout=120)
        r.raise_for_status()
        return JSONResponse(r.json())
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: Request):
    """Proxy streaming chat requests from llama-server and re-broadcast as SSE."""
    body = await req.json()
    # Enforce model alignment if specified
    desired_model = body.get('model')
    running = bool(_server_proc and _server_proc.poll() is None)
    running_path = _server_info.get('model')
    if desired_model:
        if desired_model in MODEL_REGISTRY:
            desired_path = find_model_file(desired_model, MODEL_REGISTRY[desired_model].get('filename'), use_fallback=False)
        else:
            desired_path = find_model_file(desired_model)
        if not desired_path:
            raise HTTPException(status_code=404, detail='Requested model is not installed')
        if not running:
            raise HTTPException(status_code=409, detail='No server running for requested model')
        if str(desired_path) != str(running_path or ''):
            raise HTTPException(status_code=409, detail='Different model is currently running')
    port = _server_info.get("port", 8081)

    try:
        # forward to llama-server with streaming
        with requests.post(f"http://127.0.0.1:{port}/v1/chat/completions", json=body, stream=True, timeout=300) as r:
            r.raise_for_status()

            def _extract_text_from_choice(choice):
                # Common places where token/text may appear in streamed protocol
                if not isinstance(choice, dict):
                    return ''
                # OpenAI-like streaming: choice.delta.content
                delta = choice.get('delta') or {}
                if isinstance(delta, dict):
                    if 'content' in delta and isinstance(delta['content'], str):
                        return delta['content']
                    # some servers use 'text'
                    if 'text' in delta and isinstance(delta['text'], str):
                        return delta['text']

                # Non-streamed choices: choices[*].message.content (string)
                msg = choice.get('message') or {}
                if isinstance(msg, dict):
                    cont = msg.get('content')
                    if isinstance(cont, str):
                        return cont
                    # sometimes content can be dict/structured
                    if isinstance(cont, dict):
                        # try to extract 'text' or 'content' fields inside
                        if 'text' in cont and isinstance(cont['text'], str):
                            return cont['text']
                # fallback: top-level 'text' or 'content' keys
                if 'text' in choice and isinstance(choice['text'], str):
                    return choice['text']
                if 'content' in choice and isinstance(choice['content'], str):
                    return choice['content']
                return ''

            def event_stream():
                # The frontend expects raw text chunks (it reads the response body
                # and appends bytes to the assistant content). Some servers stream
                # JSON lines (possibly already prefixed with 'data: '); parse those
                # and extract textual deltas, then yield the raw text so the UI
                # receives only the model tokens.
                for raw_line in r.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    # if line is SSE-framed from llama-server (starts with 'data:')
                    if line.startswith('data:'):
                        payload = line[len('data:'):].strip()
                    else:
                        payload = line

                    # handle explicit done sentinel
                    if payload == '[DONE]' or payload == '"[DONE]"':
                        # end of stream
                        break

                    # try to decode JSON payload and extract textual deltas
                    text_to_yield = None
                    try:
                        j = json.loads(payload)
                        # OpenAI-style: j.choices -> list
                        if isinstance(j, dict) and 'choices' in j and isinstance(j['choices'], list):
                            parts = []
                            for ch in j['choices']:
                                t = _extract_text_from_choice(ch)
                                if t:
                                    parts.append(t)
                            if parts:
                                text_to_yield = ''.join(parts)
                        else:
                            # sometimes the server returns a plain dict with text
                            # try common keys
                            for key in ('text', 'content'):
                                if key in j and isinstance(j[key], str):
                                    text_to_yield = j[key]
                                    break
                    except Exception:
                        # not JSON — just pass the payload through
                        pass

                    if text_to_yield is None:
                        # as a last resort, forward the raw payload
                        text_to_yield = payload

                    if text_to_yield:
                        # yield raw text chunk (no SSE framing) so front-end can append
                        yield text_to_yield

                # EOF: nothing else to send; end the response

            # Return a plain text streaming response (the frontend reads raw bytes)
            return StreamingResponse(event_stream(), media_type='text/plain')
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve a minimal static UI if built into web/ui/dist (repo root)
dist_dir = Path(__file__).resolve().parent.parent.parent / "web" / "ui" / "dist"
if dist_dir.exists():
    class _StaticWithSettings(StaticFiles):
        async def get_response(self, path, scope):
            # Inject window.__bunny_settings for index.html only
            if path == '' or path == 'index.html':
                resp = await super().get_response(path, scope)
                try:
                    content = await resp.body()
                except Exception:
                    return resp
                try:
                    s = _load_settings()
                    inject = f"<script>window.__bunny_settings = {json.dumps(s)};</script>"
                    new_body = content.replace(b"</head>", inject.encode('utf-8') + b"</head>")
                    from starlette.responses import Response
                    return Response(content=new_body, status_code=200, media_type='text/html')
                except Exception:
                    return resp
            return await super().get_response(path, scope)

    app.mount("/", _StaticWithSettings(directory=str(dist_dir), html=True), name="static")
else:
    @app.get("/")
    def index():
        return HTMLResponse("<html><body><h3>Bunny UI not built.</h3><p>Build UI into web/ui/dist/ or run the SPA dev server.</p></body></html>")


@app.get('/api/diagnostics/run')
def diagnostics_run():
    info = {}
    try:
        s = _load_settings()
        info['settings'] = s
    except Exception as e:
        info['settings_error'] = str(e)

    # server status
    try:
        running = bool(_server_proc and _server_proc.poll() is None)
        info['server'] = {
            'running': running,
            'pid': _server_info.get('pid'),
            'port': _server_info.get('port'),
            'model': _server_info.get('model')
        }
    except Exception as e:
        info['server_error'] = str(e)

    # models
    try:
        models = []
        for name, m in MODEL_REGISTRY.items():
            # Strict installed check for diagnostics as well
            path = find_model_file(name, m.get('filename'), use_fallback=False)
            models.append({ 'name': name, 'installed': bool(path), 'path': str(path) if path else None })
        info['models'] = models
    except Exception as e:
        info['models_error'] = str(e)

    # ports
    try:
        port = _server_info.get('port', 8081)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        ok = (s.connect_ex(('127.0.0.1', int(port))) == 0)
        s.close()
        info['port_check'] = { 'port': port, 'reachable': ok }
    except Exception as e:
        info['port_check_error'] = str(e)

    # system
    try:
        info['system'] = {
            'python': sys.version,
            'cpu_count': os.cpu_count(),
            'mem_total': psutil.virtual_memory().total if hasattr(psutil, 'virtual_memory') else None,
            'disk_free': shutil.disk_usage(str(Path.home())).free
        }
    except Exception as e:
        info['system_error'] = str(e)

    # logs tail
    try:
        if _server_log_path and _server_log_path.exists():
            with open(_server_log_path, 'rb') as f:
                tail = f.read()[-8192:]
            info['log_tail'] = tail.decode('utf-8', errors='ignore')
        else:
            info['log_tail'] = ''
    except Exception as e:
        info['log_error'] = str(e)

    return JSONResponse(info)


@app.get('/api/ports/free')
def ports_free():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return JSONResponse({'port': p})
