# Bunny 🐰

Lightweight CLI for GGUF models via llama.cpp. Auto-GPU/CPU.

## One-Command Install (Any OS)

1. Ensure Python 3.9+ (brew install python on macOS; apt/choco on Linux/Win).
2. In bunny/ folder:
   - **macOS/Linux**: `chmod +x setup.sh && ./setup.sh`
   - **Windows**: Double-click `setup.bat` (or run in cmd).
   
   This creates `bunny_env` venv, installs everything (llama-cpp-python GPU-aware), and sets up `b`.

3. Activate venv: `source bunny_env/bin/activate` (macOS/Linux) or `bunny_env\Scripts\activate` (Windows).
4. Test: `b --help` | `b list`.

**GPU**: Auto-enabled (Metal on macOS, CUDA on NVIDIA). CPU fallback if no GPU.

## Usage
- `b pull tinyllama`  # Download
- `b run llama3`      # Chat (GPU if avail.)

Models in `~/.bunny/models/`. Edit `cli.py` for more.

## Troubleshoot
- Build fail? macOS: `xcode-select --install`. Linux: `sudo apt install build-essential cmake`. Windows: Visual Studio Build Tools.
- CUDA version? Edit install.py (e.g., cu121 for 12.1).
- No venv? Run `python install.py` manually after creating one.

## Troubleshooting macOS
- Build fail (LLVM/hash error)? The fixed install.py uses system Clang. If persists: `brew uninstall llvm` (temporarily) or use Conda: `conda create -n bunny python=3.12; conda activate bunny; conda install -c conda-forge llama-cpp-python; pip install .`
- Slow build? Normal (~5min on M1+); GPU speedup post-install.
- Verify GPU: Run `b run tinyllama`; check Activity Monitor > GPU.

# Bunny 🐰

**Blazing-fast local LLMs**: Pull from HF, run on GPU/CPU. Startup <1s, no daemon bloat. Why Bunny? Instant (beats Ollama's lag), seamless (auto-GPU), tiny (50MB vs 1GB+). Your daily driver.

## Install (One-Shot)
macOS/Linux: `./setup.sh`
Windows: `setup.bat`

Activates venv, pulls deps, tunes GPU. Test: `b list`

## Use
- `b pull tinyllama`  # Instant download
- `b run tinyllama`   # Silent load, chat NOW (no logs!)
- `b list`            # Status

Silent & fast: No noise, GPU auto (Metal/CUDA). Caps history for speed.

Models: Edit `cli.py`. More? PRs welcome!

## Why Not Ollama?
- **Speed**: No server spin-up; direct run.
- **Ease**: HF pulls, no Modelfile hassle.
- **Light**: Fits anywhere; cross-OS magic.

Bunny: Because LLMs should hop, not crawl. 🚀