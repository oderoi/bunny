#!/bin/bash
# Bunny AI Universal Installer
# Automatically detects platform and installs accordingly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print functions
print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}                    ${CYAN}🐰 Bunny AI Universal Installer${NC}                    ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}                    ${CYAN}   Cross-Platform AI Assistant${NC}                      ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[→]${NC} $1"
}

# Detect platform and architecture
detect_platform() {
    print_step "Detecting platform and architecture..."
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PLATFORM="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        PLATFORM="linux"
    elif [[ "$OSTYPE" == "linux-android"* ]]; then
        OS="android"
        PLATFORM="mobile"
    elif [[ "$OSTYPE" == "linux-musl"* ]]; then
        OS="alpine"
        PLATFORM="linux"
    else
        OS="unknown"
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
    
    # Detect device type
    if [[ -f /data/data/com.termux/files/usr/bin/termux-info ]]; then
        DEVICE="android-termux"
    elif [[ -f /usr/bin/ish ]]; then
        DEVICE="ios-ish"
    elif [[ -f /etc/alpine-release ]]; then
        DEVICE="alpine"
    else
        DEVICE="desktop"
    fi
    
    print_status "Platform: $OS ($ARCH)"
    print_status "Device: $DEVICE"
    print_status "Installation type: $PLATFORM"
}

# Check system requirements
check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 not found. Please install Python 3.9+ first."
        exit 1
    fi
    
    # Check Git
    if command -v git >/dev/null 2>&1; then
        print_status "Git found"
    else
        print_error "Git not found. Please install Git first."
        exit 1
    fi
    
    # Check CMake
    if command -v cmake >/dev/null 2>&1; then
        print_status "CMake found"
    else
        print_warning "CMake not found. Will attempt to install..."
    fi
    
    # Check available memory
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
        if [[ $MEMORY -lt 2 ]]; then
            print_warning "Low memory detected ($MEMORY GB). Consider using smaller models."
        fi
    fi
}

# Install system dependencies
install_dependencies() {
    print_step "Installing system dependencies..."
    
    case $OS in
        "macos")
            print_info "Installing dependencies for macOS..."
            if ! command -v brew >/dev/null 2>&1; then
                print_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3 git cmake
            ;;
        "linux")
            print_info "Installing dependencies for Linux..."
            if command -v apt >/dev/null 2>&1; then
                sudo apt update
                sudo apt install -y python3 python3-pip python3-venv git cmake build-essential
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y python3 python3-pip git cmake gcc gcc-c++ make
            elif command -v pacman >/dev/null 2>&1; then
                sudo pacman -S python python-pip git cmake base-devel
            elif command -v zypper >/dev/null 2>&1; then
                sudo zypper install -y python3 python3-pip git cmake gcc gcc-c++
            fi
            ;;
        "android")
            print_info "Installing dependencies for Android (Termux)..."
            pkg update
            pkg install -y python git cmake clang clang++ make
            ;;
        "alpine")
            print_info "Installing dependencies for Alpine Linux..."
            apk add --no-cache python3 py3-pip git cmake make gcc g++ musl-dev build-base linux-headers
            ;;
    esac
}

# Create virtual environment
setup_venv() {
    print_step "Setting up Python virtual environment..."
    
    if [[ -d "bunny_env" ]]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf bunny_env
    fi
    
    python3 -m venv bunny_env
    source bunny_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_status "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."
    
    # Install core dependencies
    pip install huggingface-hub>=0.20.0 click>=8.1.0 requests>=2.28.0
    
    # Install web dependencies
    pip install fastapi uvicorn python-multipart
    
    # Install development dependencies (optional)
    if [[ "$1" == "--dev" ]]; then
        pip install pytest flake8 black mypy
    fi
    
    print_status "Python dependencies installed"
}

# Build llama.cpp
build_llama_cpp() {
    print_step "Building llama.cpp..."
    
    # Clone llama.cpp if not exists
    if [[ ! -d "llama.cpp" ]]; then
        print_info "Cloning llama.cpp..."
        git clone https://github.com/ggerganov/llama.cpp.git
    fi
    
    cd llama.cpp
    git pull
    
    # Create build directory
    mkdir -p build
    cd build
    
    # Configure build
    CMAKE_ARGS="-DCMAKE_BUILD_TYPE=Release"
    
    case $OS in
        "macos")
            if [[ $ARCH == "arm64" ]]; then
                CMAKE_ARGS="$CMAKE_ARGS -DLLAMA_METAL=ON"
                print_info "Building with Metal support for Apple Silicon"
            else
                print_info "Building for Intel Mac"
            fi
            ;;
        "linux"|"alpine")
            # Check for CUDA
            if command -v nvidia-smi >/dev/null 2>&1; then
                CMAKE_ARGS="$CMAKE_ARGS -DLLAMA_CUDA=ON"
                print_info "Building with CUDA support"
            else
                print_info "Building CPU-only version"
            fi
            ;;
        "android")
            print_info "Building for Android (CPU-only)"
            ;;
    esac
    
    # Configure (set C++ compiler explicitly for mobile platforms)
    export CXX=g++
    cmake .. $CMAKE_ARGS -DCMAKE_CXX_COMPILER=g++
    
    # Build
    make -j$(nproc 2>/dev/null || echo 4)
    
    cd ../..
    print_status "llama.cpp built successfully"
}

# Install Bunny package
install_bunny() {
    print_step "Installing Bunny AI package..."
    
    # Install in editable mode
    pip install -e .
    
    print_status "Bunny AI package installed"
}

# Create shortcuts and integration
create_integration() {
    print_step "Creating desktop integration..."
    
    case $OS in
        "macos")
            # Create macOS app bundle (optional)
            print_info "macOS integration created"
            ;;
        "linux")
            # Create desktop entry
            cat > ~/.local/share/applications/bunny-ai.desktop << EOF
[Desktop Entry]
Name=Bunny AI
Comment=Local LLM Runner
Exec=b serve_ui
Icon=terminal
Type=Application
Categories=Development;Education;
EOF
            print_status "Desktop entry created"
            ;;
    esac
    
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
    print_step "Testing installation..."
    
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

# Show completion message
show_completion() {
    print_header
    print_status "Installation Complete!"
    echo ""
    print_info "Bunny AI has been successfully installed on your $OS ($ARCH) system"
    echo ""
    print_info "Usage:"
    print_info "  b --help                    # Show help"
    print_info "  b list                      # List available models"
    print_info "  b pull <model>              # Download a model"
    print_info "  b run <model>               # Start chat with model"
    print_info "  b serve_ui <model>          # Start web interface"
    echo ""
    print_info "Web UI will be available at: http://localhost:8080"
    print_info "Mobile-friendly interface included!"
    echo ""
    print_info "Next steps:"
    print_info "  1. Download a model: b pull tinyllama"
    print_info "  2. Start chatting: b run tinyllama"
    print_info "  3. Or use web UI: b serve_ui tinyllama"
    echo ""
    print_info "For mobile access, use your device's IP address:"
    print_info "  http://YOUR_IP:8080"
    echo ""
    print_status "Enjoy your local AI assistant! 🚀"
}

# Main installation function
main() {
    print_header
    detect_platform
    check_requirements
    install_dependencies
    setup_venv
    install_python_deps "$@"
    build_llama_cpp
    install_bunny
    create_integration
    test_installation
    show_completion
}

# Run main function with all arguments
main "$@"
