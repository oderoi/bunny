#!/bin/sh
# Bunny AI iOS Installer (Fixed for iSH Shell)
# Handles iOS-specific build issues and Linux includes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo "${BLUE}=== $1 ===${NC}"
}

# Install dependencies for iOS
install_ios_dependencies() {
    print_header "Installing Dependencies for iOS"
    
    print_status "Installing dependencies for iOS (iSH Shell)..."
    apk update
    apk add python3 py3-pip git cmake make gcc g++ musl-dev bash build-base curl-dev linux-headers
    
    print_status "Dependencies installed"
}

# Create mobile-optimized virtual environment
setup_mobile_venv() {
    print_header "Setting up Mobile-Optimized Environment"
    
    # Use smaller virtual environment
    python3 -m venv --system-site-packages bunny_env
    
    # Activate virtual environment (ash compatible)
    . bunny_env/bin/activate
    
    # Install minimal dependencies for mobile
    pip install --upgrade pip setuptools wheel
    # iSH (Alpine, i386-musl) cannot build pydantic-core (Rust). Pin FastAPI stack to Pydantic v1.
    pip install "huggingface-hub>=0.20.0" click requests \
        "fastapi==0.95.2" "starlette==0.27.0" "pydantic==1.10.13" \
        "typing_extensions<4.7" "anyio<4" "sniffio<2" "uvicorn==0.23.2" "h11<0.15"
    
    print_status "Mobile environment ready"
}

# Build llama.cpp for mobile (CPU-only, optimized)
build_mobile_llama() {
    print_header "Building llama.cpp for Mobile"
    
    # Clone llama.cpp (shallow for speed)
    if [ ! -d "llama.cpp" ]; then
        print_status "Cloning llama.cpp (shallow)..."
        git clone --depth 1 --single-branch https://github.com/ggerganov/llama.cpp.git
    fi
    
    cd llama.cpp
    git pull --ff-only || true
    
    mkdir -p build
    cd build
    
    # Skip when already built
    if [ -x ../bin/llama-server ]; then
        print_status "llama-server already built — skipping rebuild"
    else
        # Mobile-optimized build (CPU-only, smaller binary)
        # Set C++ compiler explicitly for iOS/iSH
        export CXX=g++
        # iOS-specific flags to avoid Linux-specific includes and HTTP features
        CMAKE_FLAGS="-DCMAKE_BUILD_TYPE=MinSizeRel -DGGML_NATIVE=ON -DLLAMA_CURL=OFF -DLLAMA_HTTP=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=ON -DCMAKE_CXX_COMPILER=g++ -DGGML_CCACHE=OFF"
        if command -v ccache >/dev/null 2>&1; then
            CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache"
        fi
        cmake .. $CMAKE_FLAGS
        # Build with limited resources
        make -j2
    fi
    
    cd ../..
    print_status "Mobile llama.cpp built"
}

# Install Bunny with mobile optimizations
install_mobile_bunny() {
    print_header "Installing Bunny for Mobile"
    
    # Install in editable mode (avoid build isolation on musl targets)
    PIP_NO_BUILD_ISOLATION=1 pip install -e .
    
    # Create mobile-optimized config
    mkdir -p ~/.bunny
    cat > ~/.bunny/mobile_config.json << 'EOF'
{
    "mobile_optimized": true,
    "max_context": 1024,
    "max_tokens": 512,
    "low_memory_mode": true,
    "battery_saver": true
}
EOF
    
    print_status "Bunny installed with mobile optimizations"
}

# Create mobile shortcuts (ash compatible)
create_mobile_shortcuts() {
    print_header "Creating Mobile Shortcuts"
    
    # Create simple startup script
    cat > start_bunny.sh << 'EOF'
#!/bin/sh
cd "$(dirname "$0")"
. bunny_env/bin/activate
echo "Starting Bunny AI..."
b serve_ui --host 0.0.0.0 --port 8080
EOF
    chmod +x start_bunny.sh
    
    # Create chat script
    cat > chat_bunny.sh << 'EOF'
#!/bin/sh
cd "$(dirname "$0")"
. bunny_env/bin/activate
echo "Starting Bunny Chat..."
b run
EOF
    chmod +x chat_bunny.sh
    
    print_status "Mobile shortcuts created"
}

# Test mobile installation
test_mobile_installation() {
    print_header "Testing Mobile Installation"
    
    # Test CLI
    if b --help >/dev/null 2>&1; then
        print_status "Mobile CLI test passed"
    else
        print_warning "Mobile CLI test failed"
        return 1
    fi
    
    print_status "Mobile installation test completed"
}

# Main mobile installation
main() {
    print_header "Bunny AI iOS Installer (Fixed)"
    
    install_ios_dependencies
    setup_mobile_venv
    build_mobile_llama
    install_mobile_bunny
    create_mobile_shortcuts
    test_mobile_installation
    
    print_header "iOS Installation Complete!"
    print_status "Bunny AI is ready for iOS use"
    print_status ""
    print_status "Usage:"
    print_status "  ./start_bunny.sh          # Start web UI"
    print_status "  ./chat_bunny.sh            # Start chat"
    print_status "  b --help                   # Show help"
    print_status ""
    print_status "Web UI will be available at: http://localhost:8080"
    print_status "Access from other devices on your network!"
}

# Run installation
main "$@"
