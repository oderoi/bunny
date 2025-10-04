#!/bin/bash
# Run: chmod +x setup.sh && ./setup.sh

echo "=== Bunny Setup (macOS/Linux) ==="
python3 -m venv bunny_env
source bunny_env/bin/activate
pip install --upgrade pip
export CC=/usr/bin/clang
export CXX=/usr/bin/clang++
export CMAKE_ARGS="-DGGML_METAL=on"  # For macOS Metal
python install.py
deactivate
echo "Done! Activate: source bunny_env/bin/activate"
echo "Test: b --help"