#!/bin/sh
# Bunny AI Mobile Installer (Ash Shell Compatible)
# Works with iOS iSH Shell and other ash-based systems

set -e

# Simple colors for ash
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "${BLUE}=== Bunny AI Mobile Installer (iOS Compatible) ===${NC}"

# Check if we're on iOS
if [ -f /usr/bin/ish ]; then
    echo "${GREEN}[INFO]${NC} iOS (iSH Shell) detected"
    PLATFORM="ios"
elif [ -f /data/data/com.termux/files/usr/bin/termux-info ]; then
    echo "${GREEN}[INFO]${NC} Android (Termux) detected"
    PLATFORM="android"
else
    echo "${GREEN}[INFO]${NC} Linux mobile detected"
    PLATFORM="linux"
fi

# Install dependencies
echo "${BLUE}[→]${NC} Installing dependencies..."
if [ "$PLATFORM" = "ios" ]; then
    apk update
    apk add python3 py3-pip git cmake make gcc musl-dev bash
elif [ "$PLATFORM" = "android" ]; then
    pkg update
    pkg install python git cmake clang make
else
    if command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y python3 python3-pip git cmake build-essential
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S python python-pip git cmake base-devel
    fi
fi

# Create virtual environment
echo "${BLUE}[→]${NC} Creating virtual environment..."
python3 -m venv bunny_env
. bunny_env/bin/activate

# Install Python dependencies
echo "${BLUE}[→]${NC} Installing Python dependencies..."
pip install --upgrade pip
pip install huggingface-hub click requests fastapi uvicorn

# Clone and build llama.cpp
echo "${BLUE}[→]${NC} Building llama.cpp..."
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git
fi

cd llama.cpp
git pull
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=MinSizeRel -DLLAMA_NATIVE=ON
make -j2
cd ../..

# Install Bunny package
echo "${BLUE}[→]${NC} Installing Bunny AI..."
pip install -e .

# Create startup scripts
echo "${BLUE}[→]${NC} Creating startup scripts..."
cat > start_bunny.sh << 'EOF'
#!/bin/sh
cd "$(dirname "$0")"
. bunny_env/bin/activate
echo "Starting Bunny AI..."
b serve_ui --host 0.0.0.0 --port 8080
EOF

cat > chat_bunny.sh << 'EOF'
#!/bin/sh
cd "$(dirname "$0")"
. bunny_env/bin/activate
echo "Starting Bunny Chat..."
b run
EOF

chmod +x start_bunny.sh chat_bunny.sh

# Test installation
echo "${BLUE}[→]${NC} Testing installation..."
if b --help >/dev/null 2>&1; then
    echo "${GREEN}[✓]${NC} Installation test passed"
else
    echo "${YELLOW}[!]${NC} Installation test failed"
fi

echo ""
echo "${GREEN}=== Installation Complete! ===${NC}"
echo ""
echo "${GREEN}[INFO]${NC} Usage:"
echo "  ./start_bunny.sh          # Start web UI"
echo "  ./chat_bunny.sh            # Start chat"
echo "  b --help                   # Show help"
echo ""
echo "${GREEN}[INFO]${NC} Web UI will be available at: http://localhost:8080"
echo "${GREEN}[INFO]${NC} Access from other devices on your network!"
