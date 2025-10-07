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
    apk add python3 py3-pip git cmake make gcc g++ musl-dev bash build-base curl-dev
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
pip install --upgrade pip setuptools wheel
# Pin FastAPI stack to Pydantic v1 to avoid Rust pydantic-core on musl/i386
pip install -r requirements-mobile.txt

# Clone and build llama.cpp
echo "${BLUE}[→]${NC} Building llama.cpp..."
# Shallow clone for speed
if [ ! -d "llama.cpp" ]; then
    git clone --depth 1 --single-branch https://github.com/ggerganov/llama.cpp.git
fi

cd llama.cpp
git pull --ff-only || true
mkdir -p build
cd build
# Set C++ compiler explicitly for mobile platforms
export CXX=g++
# Disable CURL on ultra-minimal iOS environments
if [ -x ../bin/llama-server ]; then
    echo "${GREEN}[✓]${NC} llama-server already built"
else
    cmake .. -DCMAKE_BUILD_TYPE=MinSizeRel -DGGML_NATIVE=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=ON -DLLAMA_HTTP=OFF -DCMAKE_CXX_COMPILER=g++
    make -j2
fi
cd ../..

# Install Bunny package
echo "${BLUE}[→]${NC} Installing Bunny AI..."
# Avoid build isolation to use already-installed build deps on musl
PIP_NO_BUILD_ISOLATION=1 pip install -e .

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
