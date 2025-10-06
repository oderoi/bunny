# Bunny 🐰

Lightweight CLI for GGUF models via **native llama.cpp** (C++). Auto-GPU/CPU, cross-OS. Lower latency than Python bindings.

## Platforms
- **Desktops/Laptops**: Windows, Ubuntu/Linux, macOS (CPU/GPU/M-chips).
- **Phones (Mobile App)**: Build llama.cpp for ARM (Android/iOS examples below). Wrap in app (e.g., Flutter + HTTP to local server). Bunny CLI downloads/runs models; port to mobile via FFI.

## One-Command Install
1. Python 3.9+ (install via brew/apt/choco).
2. In `bunny/` folder:
   - **macOS/Linux**: `chmod +x setup.sh && ./setup.sh`
   - **Windows**: Run `setup.bat` in Command Prompt (prefer VS 2022 Developer Prompt for build).
   
   Creates `bunny_env` venv, clones/builds llama.cpp (GPU-aware), installs deps, sets up `b`.

3. Activate: `source bunny_env/bin/activate` (macOS/Linux) or `bunny_env\Scripts\activate` (Windows).
4. Test: `b --help` | `b list`.

**GPU Auto**: Metal (macOS), CUDA (NVIDIA Linux/Win), CPU fallback. Build ~2-5min.

## Usage
- `b pull tinyllama`  # Download from HF
- `b run tinyllama`   # CLI chat (GPU accel)
- `b serve tinyllama` # llama.cpp built-in web UI (opens browser)
- `b list`            # Status

Serve: Starts OpenAI API at http://0.0.0.0:8080/v1/chat/completions + built-in UI. Headless: `--no-browser`.

Models: `~/.bunny/models/`. Edit `src/bunny/models.py` for more. Binary: `~/.bunny/llama.cpp/build/bin/llama-server`.

## Mobile (Phones)
Bunny CLI is desktop-focused. For phones:
- **Android**: `git clone https://github.com/ggerganov/llama.cpp; cd llama.cpp/examples/android` → Build in Android Studio. Load GGUF from Bunny-pulled models via ADB. Or use [MLC Chat](https://mlc.ai/) app (GGUF support).
- **iOS**: `llama.cpp/examples/ios` → Xcode build for M-chips. Integrate with SwiftUI app.
- **Cross-Mobile App Idea**: Use Flutter + dart:ffi to call llama.cpp lib, or HTTP to local server (run Bunny on tethered laptop). PRs for mobile wrapper welcome!

## Troubleshoot
- **Build Fail**:
  - macOS: `xcode-select --install; brew install cmake git`.
  - Linux: `sudo apt install git cmake build-essential` (CUDA: install toolkit).
  - Windows: Install Visual Studio 2022 (C++), CMake, Git. Run in "Developer Command Prompt".
- **No GPU**: Fallback to CPU. Verify: `nvidia-smi` (Linux/Win) or Activity Monitor (macOS).
- **Server Port**: Uses 8080; kill if conflicted (`lsof -i :8080`).
- **Models**: Ensure GGUF has chat template metadata for best chat.

## Why llama.cpp Native?
- **Faster**: Direct C++ (no Python overhead).
- **Light**: ~10MB binary vs bindings.
- **Portable**: Easy mobile ports.

Bunny: Hop to LLMs anywhere. 🚀