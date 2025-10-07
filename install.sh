#!/bin/bash
# Bunny Universal Installer - Cross-Platform Installation Script
# Supports: macOS, Linux, Windows (WSL), Android (Termux), iOS (iSH)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Platform detection
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
    elif [[ "$OSTYPE" == "linux-android"* ]]; then
        PLATFORM="android"
    elif [[ "$OSTYPE" == "linux-musl"* ]]; then
        PLATFORM="alpine"
    else
        PLATFORM="unknown"
    fi
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH="x64" ;;
        arm64|aarch64) ARCH="arm64" ;;
        armv7l) ARCH="arm" ;;
        *) ARCH="unknown" ;;
    esac
}

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install dependencies based on platform
install_dependencies() {
    print_header "Installing Dependencies"
    
    case $PLATFORM in
        "macos")
            print_status "Installing dependencies for macOS..."
            if ! command_exists brew; then
                print_warning "Homebrew not found. Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3 git cmake
            ;;
        "linux")
            print_status "Installing dependencies for Linux..."
            if command_exists apt; then
                sudo apt update
                sudo apt install -y python3 python3-pip python3-venv git cmake build-essential
            elif command_exists yum; then
                sudo yum install -y python3 python3-pip git cmake gcc gcc-c++ make
            elif command_exists pacman; then
                sudo pacman -S python python-pip git cmake base-devel
            elif command_exists zypper; then
                sudo zypper install -y python3 python3-pip git cmake gcc gcc-c++
            fi
            ;;
        "android")
            print_status "Installing dependencies for Android (Termux)..."
            pkg update
            pkg install -y python git cmake clang
            ;;
        "alpine")
            print_status "Installing dependencies for Alpine Linux..."
            apk add --no-cache python3 py3-pip git cmake make gcc musl-dev linux-headers
            ;;
    esac
}

# Create virtual environment
setup_venv() {
    print_header "Setting up Python Virtual Environment"
    
    if [[ -d "bunny_env" ]]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf bunny_env
    fi
    
    python3 -m venv bunny_env
    
    # Activate virtual environment
    source bunny_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_status "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    print_header "Installing Python Dependencies"
    
    # Install core dependencies
    pip install huggingface-hub>=0.20.0 click>=8.1.0 requests>=2.28.0
    
    # Install additional dependencies for web UI
    pip install fastapi uvicorn python-multipart
    
    print_status "Python dependencies installed"
}

# Build llama.cpp
build_llama_cpp() {
    print_header "Building llama.cpp"
    
    # Clone llama.cpp if not exists
    if [[ ! -d "llama.cpp" ]]; then
        print_status "Cloning llama.cpp..."
        git clone https://github.com/ggerganov/llama.cpp.git
    fi
    
    cd llama.cpp
    
    # Update to latest
    git pull
    
    # Create build directory
    mkdir -p build
    cd build
    
    # Configure build
    CMAKE_ARGS="-DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DGGML_NATIVE=ON"
    
    case $PLATFORM in
        "macos")
            if [[ $ARCH == "arm64" ]]; then
                CMAKE_ARGS="$CMAKE_ARGS -DLLAMA_METAL=ON"
                print_status "Building with Metal support for Apple Silicon"
            else
                print_status "Building for Intel Mac"
            fi
            ;;
        "linux"|"alpine")
            # Check for CUDA
            if command_exists nvidia-smi; then
                CMAKE_ARGS="$CMAKE_ARGS -DLLAMA_CUDA=ON"
                print_status "Building with CUDA support"
            else
                print_status "Building CPU-only version"
            fi
            ;;
        "android")
            print_status "Building for Android (CPU-only)"
            ;;
    esac
    
    # Configure
    cmake .. $CMAKE_ARGS
    
    # Build
    make -j$(nproc 2>/dev/null || echo 4)
    
    cd ../..
    print_status "llama.cpp built successfully"
}

# Install Bunny package
install_bunny() {
    print_header "Installing Bunny Package"
    
    # Install in editable mode
    pip install -e .
    
    print_status "Bunny package installed"
}

# Create desktop shortcuts and aliases
create_shortcuts() {
    print_header "Creating Desktop Integration"
    
    # Create desktop entry for Linux
    if [[ $PLATFORM == "linux" ]]; then
        cat > ~/.local/share/applications/bunny.desktop << EOF
[Desktop Entry]
Name=Bunny AI
Comment=Local LLM Runner
Exec=bunny serve_ui
Icon=terminal
Type=Application
Categories=Development;
EOF
        print_status "Desktop entry created"
    fi
    
    # Create shell aliases
    cat >> ~/.bashrc << EOF

# Bunny AI aliases
alias bunny='b'
alias bunny-ui='b serve_ui'
alias bunny-chat='b run'
EOF
    
    # Also add to zsh if it exists
    if [[ -f ~/.zshrc ]]; then
        cat >> ~/.zshrc << EOF

# Bunny AI aliases
alias bunny='b'
alias bunny-ui='b serve_ui'
alias bunny-chat='b run'
EOF
    fi
    
    print_status "Shell aliases created"
}

# Test installation
test_installation() {
    print_header "Testing Installation"
    
    # Test CLI
    if b --help >/dev/null 2>&1; then
        print_status "CLI test passed"
    else
        print_error "CLI test failed"
        return 1
    fi
    
    # Test model listing
    if b list >/dev/null 2>&1; then
        print_status "Model listing test passed"
    else
        print_warning "Model listing test failed (no models installed yet)"
    fi
    
    print_status "Installation test completed"
}

# Main installation function
main() {
    print_header "Bunny AI Universal Installer"
    print_status "Platform: $PLATFORM ($ARCH)"
    
    # Install dependencies
    install_dependencies
    
    # Setup virtual environment
    setup_venv
    
    # Install Python dependencies
    install_python_deps
    
    # Build llama.cpp
    build_llama_cpp
    
    # Install Bunny package
    install_bunny
    
    # Create shortcuts
    create_shortcuts
    
    # Test installation
    test_installation
    
    print_header "Installation Complete!"
    print_status "Bunny AI has been successfully installed"
    print_status "Usage:"
    print_status "  b --help                    # Show help"
    print_status "  b list                      # List available models"
    print_status "  b pull <model>              # Download a model"
    print_status "  b run <model>               # Start chat with model"
    print_status "  b serve_ui <model>          # Start web interface"
    print_status ""
    print_status "Web UI will be available at: http://localhost:8080"
    print_status "Mobile-friendly interface included!"
}

# Run main function
detect_platform
main "$@"
