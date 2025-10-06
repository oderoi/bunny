import glob
import os
from pathlib import Path
from typing import Optional, Dict, Any

MODEL_DIR = Path.home() / ".bunny" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Central registry: Add models here. chat_format for --chat-template if not in metadata.
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "tinyllama": {
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "bitnet": {
        "repo_id": "microsoft/bitnet-b1.58-2B-4T-gguf",
        "filename": "ggml-model-i2_s.gguf",
        "chat_format": "chatml",
        "requires_special": True  # Needs bitnet.cpp
    },
    "deepseek-r1:1.5b": {
        "repo_id": "unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "deepseek-r1:7b": {
        "repo_id": "unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "phi3": {
        "repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "filename": "Phi-3-mini-4k-instruct-q4.gguf",
        "chat_format": "chatml"
    },
    "phi4-mini": {
        "repo_id": "unsloth/Phi-4-mini-reasoning-GGUF",
        "filename": "Phi-4-mini-reasoning-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "llama3": {
        "repo_id": "bartowski/Meta-Llama-3-8B-Instruct-GGUF",
        "filename": "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
        "chat_format": "llama3"
    },
    "llama3.1:8b": {
        "repo_id": "unsloth/Llama-3.1-8B-Instruct-GGUF",
        "filename": "Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "chat_format": "llama3"
    },
    "llama3.2:1b": {
        "repo_id": "unsloth/Llama-3.2-1B-Instruct-GGUF",
        "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "chat_format": "llama3"
    },
    "llama3.2:3b": {
        "repo_id": "unsloth/Llama-3.2-3B-Instruct-GGUF",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "chat_format": "llama3"
    },
    "mistral": {
        "repo_id": "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
        "filename": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "gemma2:2b": {
        "repo_id": "unsloth/gemma-2-it-GGUF",
        "filename": "gemma-2-2b-it.q4_k_m.gguf",
        "chat_format": "chatml"
    },
    "gemma3:270m": {
        "repo_id": "unsloth/gemma-3-270m-it-GGUF",
        "filename": "gemma-3-270m-it-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "gemma3:1b": {
        "repo_id": "unsloth/gemma-3-1b-it-GGUF",
        "filename": "gemma-3-1b-it-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "gemma3:4b": {
        "repo_id": "unsloth/gemma-3-4b-it-GGUF",
        "filename": "gemma-3-4b-it-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "gemma3n:e4b": {
        "repo_id": "unsloth/gemma-3n-E4B-it-GGUF",
        "filename": "gemma-3n-E4B-it-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "gemma3n:e2b": {
        "repo_id": "unsloth/gemma-3n-E2B-it-GGUF",
        "filename": "gemma-3n-E2B-it-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen3:0.6b": {
        "repo_id": "unsloth/Qwen3-0.6B-GGUF",
        "filename": "Qwen3-0.6B-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen3:1.7b": {
        "repo_id": "unsloth/Qwen3-1.7B-GGUF",
        "filename": "Qwen3-1.7B-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen3:4b": {
        "repo_id": "unsloth/Qwen3-4B-GGUF",
        "filename": "Qwen3-4B-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen3:8b": {
        "repo_id": "unsloth/Qwen3-8B-GGUF",
        "filename": "Qwen3-8B-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen2.5-coder:0.5b": {
        "repo_id": "unsloth/Qwen2.5-Coder-0.5B-Instruct-GGUF",
        "filename": "Qwen2.5-Coder-0.5B-Instruct-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen2.5-coder:1.5b": {
        "repo_id": "unsloth/Qwen2.5-Coder-1.5B-Instruct-GGUF",
        "filename": "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen2.5-coder:3b": {
        "repo_id": "unsloth/Qwen2.5-Coder-3B-Instruct-GGUF",
        "filename": "Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen2.5-coder:7b": {
        "repo_id": "unsloth/Qwen2.5-Coder-7B-Instruct-GGUF",
        "filename": "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen2.5:3b": {
        "repo_id": "unsloth/Qwen2.5-VL-3B-Instruct-GGUF",
        "filename": "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
    "qwen2.5:7b": {
        "repo_id": "unsloth/Qwen2.5-VL-7B-Instruct-GGUF",
        "filename": "Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf",
        "chat_format": "chatml"
    },
}


def is_valid_gguf(path: Path) -> bool:
    """Fast header check: GGUF magic b'GGUF'."""
    try:
        with open(path, 'rb') as f:
            header = f.read(4)
            return header == b'GGUF'
    except:
        return False


def find_model_file(model_name: str, expected_filename: Optional[str] = None, use_fallback: bool = True) -> Optional[Path]:
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
        from click import echo, style
        echo(style(f"Using alt: {candidates[0].name}", fg="yellow"))
        return candidates[0]
    return None