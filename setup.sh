#!/bin/bash
# Bunny Setup (macOS/Linux)

echo "=== Bunny Setup (macOS/Linux) ==="
python3 -m venv bunny_env
source bunny_env/bin/activate
pip install --upgrade pip
export CC=/usr/bin/clang
export CXX=/usr/bin/clang++
export PATH="/usr/bin:$PATH"  # System tools
python install.py
deactivate
echo "Done! Activate: source bunny_env/bin/activate"
echo "Test: b --help"