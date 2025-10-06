import click
import os
import subprocess
import requests
import time
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import socket

# Suppress logs if needed
os.environ['LLAMA_CPP_VERBOSE'] = '0'

from huggingface_hub import hf_hub_download
from .models import MODEL_REGISTRY, MODEL_DIR, is_valid_gguf, find_model_file

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
        except:
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
def pull(model, repo, file):
    """Pull (or custom)."""
    if repo and file:
        click.echo(f"Pulling {model} from {repo}...")
        try:
            hf_hub_download(repo_id=repo, filename=file, local_dir=MODEL_DIR)
            path = MODEL_DIR / file
            if is_valid_gguf(path):
                click.echo(click.style("✓ Pulled & valid!", fg="green"))
            else:
                click.echo(click.style("⚠ Pulled but invalid GGUF—check repo.", fg="yellow"))
        except Exception as e:
            click.echo(click.style(f"Failed: {e}", fg="red"))
        return

    if model not in MODEL_REGISTRY:
        click.echo(click.style(f"Unknown '{model}'. Use --repo/--file.", fg="red"))
        return

    info = MODEL_REGISTRY[model]
    path = find_model_file(model, info["filename"])

    if path:
        click.echo(click.style(f"✓ {model} ready.", fg="green"))
        return

    click.echo(f"Pulling {model}...")
    try:
        hf_hub_download(
            repo_id=info["repo_id"],
            filename=info["filename"],
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False,
            cache_dir=None
        )
        path = find_model_file(model, info["filename"])
        if path and is_valid_gguf(path):
            click.echo(click.style(f"✓ {model} pulled! (~{path.stat().st_size / 1e6:.0f}MB)", fg="green"))
        else:
            click.echo(click.style("⚠ Pulled but invalid—re-check.", fg="yellow"))
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
        path = find_model_file(model)
        chat_template = None
    else:
        info = MODEL_REGISTRY[model]
        path = find_model_file(model, info["filename"])
        chat_template = info.get("chat_format")

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
                response = requests.post("http://127.0.0.1:8080/v1/chat/completions", json=payload)
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
        except:
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
        except:
            pass

if __name__ == "__main__":
    main()