#!/bin/sh
# Bunny AI iOS Installer (iSH Shell Compatible)
# Uses ash shell instead of bash for iOS compatibility

set -e

# Colors for output (simplified for ash)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if command exists (ash compatible)
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install dependencies for iOS
install_ios_dependencies() {
    print_header "Installing Dependencies for iOS"
    
    print_status "Installing dependencies for iOS (iSH Shell)..."
    apk update
    apk add python3 py3-pip git cmake make gcc musl-dev bash
    
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
    pip install --upgrade pip
    pip install huggingface-hub click requests fastapi uvicorn
    
    print_status "Mobile environment ready"
}

# Build llama.cpp for mobile (CPU-only, optimized)
build_mobile_llama() {
    print_header "Building llama.cpp for Mobile"
    
    # Clone llama.cpp
    if [ ! -d "llama.cpp" ]; then
        print_status "Cloning llama.cpp..."
        git clone https://github.com/ggerganov/llama.cpp.git
    fi
    
    cd llama.cpp
    git pull
    
    mkdir -p build
    cd build
    
    # Mobile-optimized build (CPU-only, smaller binary)
    cmake .. -DCMAKE_BUILD_TYPE=MinSizeRel -DLLAMA_NATIVE=ON
    
    # Build with limited resources
    make -j2
    
    cd ../..
    print_status "Mobile llama.cpp built"
}

# Install Bunny with mobile optimizations
install_mobile_bunny() {
    print_header "Installing Bunny for Mobile"
    
    # Install in editable mode
    pip install -e .
    
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
    print_header "Bunny AI iOS Installer"
    
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
