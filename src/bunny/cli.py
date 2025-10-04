import click
import os
import sys
import glob  # For safe str-based scanning
import struct  # For header check
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

# Suppress logs
os.environ['GGML_VERBOSE'] = '0'
os.environ['LLAMA_CPP_VERBOSE'] = '0'

# Lazy import
def get_llama():
    try:
        from llama_cpp import Llama
        return Llama
    except ImportError:
        raise ImportError("llama-cpp-python missing. Run 'python install.py'.")

from huggingface_hub import hf_hub_download

# Registry (BitNet: Native i2_s, flag for fork)
MODEL_REGISTRY = {
    "tinyllama": {
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "bitnet": {
        "repo_id": "microsoft/bitnet-b1.58-2B-4T-gguf",
        "filename": "ggml-model-i2_s.gguf",
        "chat_format": "chatml",
        "requires_special": True  # Needs bitnet.cpp for 1-bit
    },
    "deepseek-r1": {
        "repo_id": "unsloth/DeepSeek-R1-GGUF",
        "filename": "DeepSeek-R1.Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "phi3": {
        "repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "filename": "Phi-3-mini-4k-instruct-q4.gguf",
        "chat_format": "chatml"
    },
    "llama3": {
        "repo_id": "bartowski/Meta-Llama-3-8B-Instruct-GGUF",
        "filename": "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
        "chat_format": "llama3"
    },
    "mistral": {
        "repo_id": "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
        "filename": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "gemma3-270m": {
        "repo_id": "unsloth/gemma-3-270m-it-GGUF",
        "filename": "gemma-3-270m-it-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "gemma3-1b": {
        "repo_id": "unsloth/gemma-3-1b-it-GGUF",
        "filename": "gemma-3-1b-it-Q4_K_M.gguf",
        "chat_format": "chatml"
    }
}

MODEL_DIR = Path.home() / ".bunny" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def is_valid_gguf(path):
    """Fast header check: GGUF magic b'GGUF'."""
    try:
        with open(path, 'rb') as f:
            header = f.read(4)
            return header == b'GGUF'
    except:
        return False


def find_model_file(model_name, expected_filename=None, use_fallback=True):
    """Safe scan: Exact first, then model-specific glob."""
    dir_str = str(MODEL_DIR)
    # Exact match
    if expected_filename:
        local_path = MODEL_DIR / expected_filename
        if local_path.exists() and is_valid_gguf(local_path):
            return local_path

    if not use_fallback:
        return None

    # Model-specific fallback (no cross-match)
    pattern = f"{dir_str}/*{model_name}*.gguf"
    candidates_str = glob.glob(pattern)
    candidates = [Path(c) for c in candidates_str if is_valid_gguf(Path(c))]
    if candidates:
        click.echo(click.style(f"Using alt: {candidates[0].name}", fg="yellow"))
        return candidates[0]
    return None


@click.group()
def main():
    """Bunny: Any GGUF, blazing fast."""
    pass


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
        path = find_model_file(model_name, info["filename"], use_fallback=True)  # Full detect
        status = "✓" if path else "○"
        click.echo(f"  {model_name}: {status}")


@main.command()
@click.argument("model")
@click.option("--ctx-size", default=2048, help="Context.")
@click.option("--max-tokens", default=256, help="Max output.")
def run(model, ctx_size, max_tokens):
    """Run any GGUF."""
    # Custom scan
    if model not in MODEL_REGISTRY:
        path = find_model_file(model)
        info = {"chat_format": None}
    else:
        info = MODEL_REGISTRY[model]
        path = find_model_file(model, info["filename"])

    if not path:
        click.echo(click.style(f"No valid {model}.gguf. Pull or drop in ~/.bunny/models/.", fg="red"))
        return

    if info.get("requires_special"):
        click.echo(click.style(f"⚠ {model} needs special backend (bitnet.cpp): https://github.com/microsoft/BitNet", fg="yellow"))
        click.echo("Clone & install: git clone https://github.com/microsoft/BitNet; cd BitNet; pip install -e .")
        return

    # Silent load
    devnull = open(os.devnull, 'w')
    try:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            Llama = get_llama()
            llm = Llama(
                str(path),
                n_ctx=ctx_size,
                n_gpu_layers=-1,
                chat_format=info.get("chat_format"),
                verbose=False,
                n_threads=os.cpu_count() or 4
            )
    except Exception as e:
        devnull.close()
        click.echo(click.style(f"Load failed: {e}", fg="red"))
        if "bitnet" in model.lower():
            click.echo("Tip: bitnet.cpp fork required for native 1-bit. Alt: Q4 quants.")
        else:
            click.echo("Tip: Verify GGUF header (head -c 4 ~/.bunny/models/*.gguf | hexdump -C | grep '6767').")
        return
    finally:
        try:
            devnull.close()
        except:
            pass

    click.echo(click.style(f"🚀 {model} ready. /exit quit, /clear reset.", fg="green"))
    click.echo("-" * 50)

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    while True:
        try:
            user_input = click.prompt("You", type=str).strip()
        except KeyboardInterrupt:
            click.echo("\nBye!")
            break
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
            output = llm.create_chat_completion(
                messages,
                max_tokens=max_tokens,
                stop=["Human:", "\n\n"],
                temperature=0.7,
                stream=False
            )
            response = output["choices"][0]["message"]["content"].strip()
            messages.append({"role": "assistant", "content": response})
            click.echo(f"Model: {response}")
            click.echo("-" * 50)
        except Exception as e:
            click.echo(click.style(f"Gen error: {e}", fg="red"))


if __name__ == "__main__":
    main()