#!/bin/sh
# Bunny AI iOS Installer (Offline-Capable for iSH Shell)
# Handles network issues and provides offline fallbacks

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

# Check network connectivity
check_network() {
    print_header "Checking Network Connectivity"
    
    if ping -c 1 pypi.org >/dev/null 2>&1; then
        print_status "Network connection OK"
        return 0
    else
        print_warning "Network connection issues detected"
        return 1
    fi
}

# Install dependencies for iOS
install_ios_dependencies() {
    print_header "Installing Dependencies for iOS"
    
    print_status "Installing dependencies for iOS (iSH Shell)..."
    apk update
    apk add python3 py3-pip git cmake make gcc g++ musl-dev bash build-base curl-dev linux-headers
    
    print_status "Dependencies installed"
}

# Create mobile-optimized virtual environment with offline fallback
setup_mobile_venv() {
    print_header "Setting up Mobile-Optimized Environment"
    
    # Use smaller virtual environment
    python3 -m venv --system-site-packages bunny_env
    
    # Activate virtual environment (ash compatible)
    . bunny_env/bin/activate
    
    # Try to upgrade pip with network check
    if check_network; then
        print_status "Upgrading pip with network..."
        pip install --upgrade pip setuptools wheel || print_warning "Pip upgrade failed, continuing with system packages"
    else
        print_warning "No network, using system packages"
    fi
    
    # Install minimal dependencies with offline fallback
    if check_network; then
        print_status "Installing Python dependencies with network..."
        pip install "huggingface-hub>=0.20.0" click requests \
            "fastapi==0.95.2" "starlette==0.27.0" "pydantic==1.10.13" \
            "typing_extensions<4.7" "anyio<4" "sniffio<2" "uvicorn==0.23.2" "h11<0.15" || {
            print_warning "Network install failed, trying offline mode..."
            # Try to use system packages
            python3 -c "import huggingface_hub, click, requests, fastapi, uvicorn" 2>/dev/null || {
                print_error "Required packages not available offline"
                print_status "Please check your network connection and try again"
                exit 1
            }
        }
    else
        print_warning "No network, checking for system packages..."
        python3 -c "import huggingface_hub, click, requests, fastapi, uvicorn" 2>/dev/null || {
            print_error "Required packages not available offline"
            print_status "Please connect to internet and try again"
            exit 1
        }
    fi
    
    print_status "Mobile environment ready"
}

# Build llama.cpp for mobile (CPU-only, optimized)
build_mobile_llama() {
    print_header "Building llama.cpp for Mobile"
    
    # Clone llama.cpp (shallow for speed)
    if [ ! -d "llama.cpp" ]; then
        if check_network; then
            print_status "Cloning llama.cpp (shallow)..."
            git clone --depth 1 --single-branch https://github.com/ggerganov/llama.cpp.git
        else
            print_error "No network connection to clone llama.cpp"
            print_status "Please connect to internet and try again"
            exit 1
        fi
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

# Install Bunny with mobile optimizations (offline-capable)
install_mobile_bunny() {
    print_header "Installing Bunny for Mobile"
    
    # Try to install in editable mode with network check
    if check_network; then
        print_status "Installing Bunny package with network..."
        PIP_NO_BUILD_ISOLATION=1 pip install -e . || {
            print_warning "Network install failed, trying offline mode..."
            # Try to install without build isolation
            pip install -e . --no-deps || {
                print_error "Failed to install Bunny package"
                print_status "Please check your network connection and try again"
                exit 1
            }
        }
    else
        print_warning "No network, trying offline installation..."
        pip install -e . --no-deps || {
            print_error "Failed to install Bunny package offline"
            print_status "Please connect to internet and try again"
            exit 1
        }
    fi
    
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
    print_header "Bunny AI iOS Installer (Offline-Capable)"
    
    # Check network first
    if ! check_network; then
        print_warning "Network issues detected. Some features may not work."
        print_status "Continuing with offline-capable installation..."
    fi
    
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
    
    if ! check_network; then
        print_warning "Note: Some features may require internet connection"
    fi
}

# Run installation
main "$@"
