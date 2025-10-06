import click
import os
import subprocess
import requests
import time
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import socket
import sys
from pathlib import Path as _Path

# Suppress logs if needed
os.environ['LLAMA_CPP_VERBOSE'] = '0'

from huggingface_hub import hf_hub_download
from .models import MODEL_REGISTRY, MODEL_DIR, is_valid_gguf, find_model_file
from .downloader import get_downloader

# Path to llama-server binary
BUNNY_DIR = Path.home() / ".bunny"
LLAMA_BIN = BUNNY_DIR / "llama.cpp" / "build" / "bin" / "llama-server"
if os.name == 'nt':  # Windows
    LLAMA_BIN = BUNNY_DIR / "llama.cpp" / "build" / "Release" / "llama-server.exe"

def check_server_ready(host='127.0.0.1', port=8080, timeout=30):
    """Poll until server is ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

@click.group()
def main():
    """Bunny: Any GGUF, blazing fast with llama.cpp."""
    if not LLAMA_BIN.exists():
        click.echo(click.style("⚠ llama-server not found. Run 'python install.py' to build.", fg="yellow"))
        raise click.Abort()

@main.command()
@click.argument("model")
@click.option("--repo", help="Custom repo_id.")
@click.option("--file", help="Custom filename.")
@click.option("--progress", is_flag=True, help="Show download progress.")
def pull(model, repo, file, progress):
    """Pull (or custom)."""
    # Progress callback for CLI
    start_time = time.time()
    last_update = start_time
    
    def progress_callback(downloaded, total):
        if total and progress:
            current_time = time.time()
            percent = (downloaded / total) * 100
            
            # Format sizes
            if total < 1e6:
                size_str = f"{downloaded/1e3:.1f}KB / {total/1e3:.1f}KB"
            elif total < 1e9:
                size_str = f"{downloaded/1e6:.1f}MB / {total/1e6:.1f}MB"
            else:
                size_str = f"{downloaded/1e9:.1f}GB / {total/1e9:.1f}GB"
            
            # Calculate speed and ETA
            elapsed = current_time - start_time
            if elapsed > 0 and downloaded > 0:
                speed = downloaded / elapsed
                remaining = total - downloaded
                eta = remaining / speed if speed > 0 else 0
                
                # Format speed
                if speed < 1e6:
                    speed_str = f"{speed/1e3:.1f}KB/s"
                elif speed < 1e9:
                    speed_str = f"{speed/1e6:.1f}MB/s"
                else:
                    speed_str = f"{speed/1e9:.1f}GB/s"
                
                # Format ETA
                if eta < 60:
                    eta_str = f"{eta:.0f}s"
                elif eta < 3600:
                    eta_str = f"{eta/60:.0f}m {eta%60:.0f}s"
                else:
                    eta_str = f"{eta/3600:.0f}h {(eta%3600)/60:.0f}m"
                
                click.echo(f"\r{size_str} ({percent:.1f}%) - {speed_str} - ETA: {eta_str}", nl=False)
            else:
                click.echo(f"\r{size_str} ({percent:.1f}%)", nl=False)
    
    # Status callback for CLI
    def status_callback(status):
        if status == "done":
            click.echo(click.style(f"✓ {model} pulled!", fg="green"))
        elif status == "failed":
            click.echo(click.style(f"Failed to download {model}", fg="red"))
        elif status == "cancelled":
            click.echo(click.style("Download cancelled.", fg="yellow"))
    
    try:
        # Determine model parameters
        if repo and file:
            repo_id = repo
            filename = file
        else:
            if model not in MODEL_REGISTRY:
                click.echo(click.style(f"Unknown '{model}'. Use --repo/--file.", fg="red"))
                return
            info = MODEL_REGISTRY[model]
            repo_id = info.get("repo_id")
            filename = info.get("filename")
        
        # Get HF token
        hf_token = os.environ.get('HF_HUB_TOKEN') or os.environ.get('HF_TOKEN')
        
        click.echo(f"Pulling {model}...")
        
        # Use shared downloader
        downloader = get_downloader(MODEL_DIR)
        job_id = downloader.create_job(model, repo_id, filename, hf_token)
        
        # Set up progress and status callbacks
        job = downloader.get_job(job_id)
        if job:
            job.progress_callback = progress_callback if progress else None
            job.status_callback = status_callback
            
            # Start download
            if downloader.start_download(job_id):
                # Wait for completion
                while job.status in ("queued", "running"):
                    time.sleep(0.5)
                    job = downloader.get_job(job_id)
                    if not job:
                        break
                
                if job and job.status == "done":
                    size_mb = job.size / 1e6 if job.size else 0
                    click.echo(click.style(f"✓ {model} pulled! (~{size_mb:.0f}MB)", fg="green"))
                elif job and job.status == "failed":
                    error_msg = job.error or "Unknown error"
                    click.echo(click.style(f"Failed: {error_msg}", fg="red"))
                elif job and job.status == "cancelled":
                    click.echo(click.style("Download cancelled.", fg="yellow"))
            else:
                click.echo(click.style("Failed to start download", fg="red"))
        else:
            click.echo(click.style("Failed to create download job", fg="red"))
            
    except KeyboardInterrupt:
        click.echo(click.style("Download cancelled.", fg="yellow"))
    except Exception as e:
        click.echo(click.style(f"Failed: {e}", fg="red"))

@main.command()
def list():
    """List models."""
    click.echo("Models:")
    for model_name in MODEL_REGISTRY:
        info = MODEL_REGISTRY[model_name]
        path = find_model_file(model_name, info["filename"], use_fallback=True)
        status = "✓" if path else "○"
        click.echo(f"  {model_name}: {status}")

@main.command()
@click.argument("model")
@click.option("--ctx-size", default=2048, help="Context.")
@click.option("--max-tokens", default=256, help="Max output.")
def run(model, ctx_size, max_tokens):
    """Run any GGUF with llama.cpp server."""
    # Custom scan
    if model not in MODEL_REGISTRY:
        # For unregistered models, attempt to locate by name/glob and assume no special backend is required
        info = {"requires_special": False}
        path = find_model_file(model)
    else:
        info = MODEL_REGISTRY[model]
        path = find_model_file(model, info["filename"])

    if not path:
        click.echo(click.style(f"No valid {model}.gguf. Pull or drop in ~/.bunny/models/.", fg="red"))
        return

    if info.get("requires_special"):
        click.echo(click.style(f"⚠ {model} needs special backend (bitnet.cpp): https://github.com/microsoft/BitNet", fg="yellow"))
        return

    # Server args (auto-detect chat format from metadata)
    args = [
        str(LLAMA_BIN),
        "-m", str(path),
        "--host", "127.0.0.1",
        "--port", "8080",
        "--ctx-size", str(ctx_size),
        "-ngl", "-1",  # All layers on GPU
        "--threads", str(os.cpu_count() or 4),
    ]

    # Start server silently
    devnull = open(os.devnull, 'w')
    try:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            server = subprocess.Popen(args, stdout=devnull, stderr=devnull)
    except Exception as e:
        devnull.close()
        click.echo(click.style(f"Server start failed: {e}", fg="red"))
        return

    # Wait for ready
    if not check_server_ready():
        server.terminate()
        click.echo(click.style("Server failed to start—check model/GPU.", fg="red"))
        return

    click.echo(click.style(f"🚀 {model} ready (llama.cpp). /exit quit, /clear reset.", fg="green"))
    click.echo("-" * 50)

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    try:
        while True:
            user_input = click.prompt("You", type=str).strip()
            if user_input.lower() == "/exit":
                break
            if user_input.lower() == "/clear":
                messages = [{"role": "system", "content": "You are a helpful assistant."}]
                click.echo("Cleared.")
                continue

            messages.append({"role": "user", "content": user_input})
            if len(messages) > 17:
                messages = messages[-17:]

            try:
                payload = {
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False,
                    "stop": ["Human:", "\n\n"]
                }
                response = requests.post("http://127.0.0.1:8080/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                messages.append({"role": "assistant", "content": content})
                click.echo(f"Model: {content}")
                click.echo("-" * 50)
            except Exception as e:
                click.echo(click.style(f"Gen error: {e}", fg="red"))
    except KeyboardInterrupt:
        click.echo("\nBye!")
    finally:
        server.terminate()
        try:
            devnull.close()
        except Exception:
            pass

@main.command()
@click.argument("model")
@click.option("--ctx-size", default=2048, help="Context.")
@click.option("--port", default=8080, type=int, help="Server port.")
@click.option("--no-browser", is_flag=True, help="Don't open web UI in browser (headless mode).")
def serve(model, ctx_size, port, no_browser):
    """Serve model via llama.cpp built-in web UI."""
    # Custom scan (same as run)
    if model not in MODEL_REGISTRY:
        path = find_model_file(model)
        info = {"requires_special": False}
    else:
        info = MODEL_REGISTRY[model]
        path = find_model_file(model, info["filename"])

    if not path:
        click.echo(click.style(f"No valid {model}.gguf. Pull or drop in ~/.bunny/models/.", fg="red"))
        return

    if info.get("requires_special"):
        click.echo(click.style(f"⚠ {model} needs special backend (bitnet.cpp): https://github.com/microsoft/BitNet", fg="yellow"))
        return

    # Server args (llama.cpp built-in UI)
    args = [
        str(LLAMA_BIN),
        "-m", str(path),
        "--host", "0.0.0.0",  # Bind to all interfaces for remote access
        "--port", str(port),
        "--ctx-size", str(ctx_size),
        "-ngl", "-1",  # All layers on GPU
        "--threads", str(os.cpu_count() or 4),
    ]

    click.echo(f"🚀 Starting {model} server on http://0.0.0.0:{port}...")
    devnull = open(os.devnull, 'w')
    try:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            server = subprocess.Popen(args, stdout=devnull, stderr=devnull)
    except Exception as e:
        devnull.close()
        click.echo(click.style(f"Server start failed: {e}", fg="red"))
        return

    # Wait for ready
    if not check_server_ready(host='127.0.0.1', port=port):
        server.terminate()
        click.echo(click.style("Server failed to start—check model/port.", fg="red"))
        return

    click.echo(click.style(f"✓ Server ready! UI: http://127.0.0.1:{port}", fg="green"))
    if not no_browser:
        click.echo(click.style("Opening llama.cpp web UI...", fg="green"))
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}')
    else:
        click.echo(click.style("(Headless mode: Access at http://<your-ip>:{port})", fg="yellow"))

    try:
        server.wait()
    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    finally:
        server.terminate()
        try:
            devnull.close()
        except Exception:
            pass


@main.command()
@click.argument("model")
@click.option("--ctx-size", default=2048, help="Context.")
@click.option("--port", default=8081, type=int, help="llama-server port.")
@click.option("--ui-port", default=8080, type=int, help="UI manager port.")
@click.option("--no-browser", is_flag=True, help="Don't open UI in browser.")
def serve_ui(model, ctx_size, port, ui_port, no_browser):
    """Start local UI manager (serves SPA) and launch llama-server for the model."""
    # Helper to test whether a manager is already running at ui_port
    def _manager_responding(p):
        try:
            resp = requests.get(f"http://127.0.0.1:{p}/api/server/status", timeout=1)
            return resp.status_code == 200
        except Exception:
            return False

    started_uvicorn = False
    uv = None
    devnull = None

    # If the requested ui_port is occupied, prefer to reuse an existing manager if it responds.
    def _port_free(p):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', int(p)))
            s.close()
            return True
        except Exception:
            try:
                s.close()
            except Exception:
                pass
            return False

    if not _port_free(ui_port):
        if _manager_responding(ui_port):
            click.echo(click.style(f"Using existing UI manager on port {ui_port}", fg="green"))
        else:
            # find an ephemeral free port
            s = socket.socket()
            s.bind(('127.0.0.1', 0))
            new_port = s.getsockname()[1]
            s.close()
            click.echo(click.style(f"UI port {ui_port} appears occupied but not a manager; selecting free port {new_port}", fg="yellow"))
            ui_port = new_port

    # Start uvicorn manager using the same Python executable and ensure PYTHONPATH if we didn't reuse one
    if not _manager_responding(ui_port):
        uvicorn_cmd = [
            sys.executable, "-m", "uvicorn", "bunny.web_manager:app", "--host", "127.0.0.1", "--port", str(ui_port)
        ]
        env = os.environ.copy()
        # Ensure bunny package is importable by uvicorn process
        env["PYTHONPATH"] = str(_Path(__file__).resolve().parent.parent)
        devnull = open(os.devnull, 'w')
        try:
            uv = subprocess.Popen(uvicorn_cmd, stdout=devnull, stderr=devnull, env=env)
            started_uvicorn = True
        except Exception as e:
            if devnull is not None:
                try:
                    devnull.close()
                except Exception:
                    pass
            click.echo(click.style(f"Failed to start UI manager: {e}", fg="red"))
            return

        # Wait for manager readiness (poll)
        if not check_server_ready(host='127.0.0.1', port=ui_port, timeout=10):
            if started_uvicorn and uv is not None:
                uv.terminate()
            if devnull is not None:
                try:
                    devnull.close()
                except Exception:
                    pass
            click.echo(click.style("UI manager failed to start in time.", fg="red"))
            return

    # Ask manager to start llama-server for model
    try:
        resp = requests.post(f"http://127.0.0.1:{ui_port}/api/server/start", json={"model": model, "port": port, "ctx_size": ctx_size}, timeout=10)
        if resp.status_code != 200:
            click.echo(click.style(f"Manager failed to start model: {resp.text}", fg="red"))
            if started_uvicorn and uv is not None:
                uv.terminate()
            if devnull is not None:
                try:
                    devnull.close()
                except Exception:
                    pass
            return
    except Exception as e:
        click.echo(click.style(f"Failed to contact UI manager: {e}", fg="red"))
        if started_uvicorn and uv is not None:
            uv.terminate()
        if devnull is not None:
            try:
                devnull.close()
            except Exception:
                pass
        return

    url = f"http://127.0.0.1:{ui_port}"
    click.echo(click.style(f"✓ UI manager running at {url}", fg="green"))
    if not no_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        # If we started uvicorn in this process, wait on it. Otherwise just exit; external manager remains.
        if started_uvicorn and uv is not None:
            uv.wait()
        else:
            # External manager: keep the CLI alive until KeyboardInterrupt to match previous behavior
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nShutting down UI manager...")
    finally:
        if started_uvicorn and uv is not None:
            try:
                uv.terminate()
            except Exception:
                pass
        if devnull is not None:
            try:
                devnull.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()