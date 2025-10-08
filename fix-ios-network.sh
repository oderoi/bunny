#!/bin/sh
# iOS Network Troubleshooting Script
# Fixes common network issues on iSH Shell

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

# Fix network issues
fix_network() {
    print_header "Fixing iOS Network Issues"
    
    # Update package lists
    print_status "Updating package lists..."
    apk update
    
    # Install network tools
    print_status "Installing network tools..."
    apk add curl wget ca-certificates
    
    # Test connectivity
    print_status "Testing connectivity..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_status "Basic connectivity OK"
    else
        print_warning "Basic connectivity issues"
    fi
    
    # Test DNS
    print_status "Testing DNS resolution..."
    if nslookup pypi.org >/dev/null 2>&1; then
        print_status "DNS resolution OK"
    else
        print_warning "DNS resolution issues"
        print_status "Trying to fix DNS..."
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 1.1.1.1" >> /etc/resolv.conf
    fi
    
    # Test HTTPS
    print_status "Testing HTTPS connectivity..."
    if curl -s https://pypi.org >/dev/null 2>&1; then
        print_status "HTTPS connectivity OK"
    else
        print_warning "HTTPS connectivity issues"
        print_status "Trying to fix SSL certificates..."
        apk add ca-certificates
        update-ca-certificates
    fi
}

# Fix pip issues
fix_pip() {
    print_header "Fixing pip Issues"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    python3 -m pip install --upgrade pip || {
        print_warning "Pip upgrade failed, trying alternative method..."
        curl https://bootstrap.pypa.io/get-pip.py | python3
    }
    
    # Configure pip for mobile
    print_status "Configuring pip for mobile..."
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << 'EOF'
[global]
timeout = 60
retries = 3
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
EOF
    
    # Test pip
    print_status "Testing pip..."
    pip install --upgrade setuptools wheel || {
        print_warning "Pip test failed, trying offline mode..."
        print_status "Using system packages..."
    }
}

# Install with network fixes
install_with_fixes() {
    print_header "Installing with Network Fixes"
    
    # Try to install with retries
    print_status "Installing Python packages with retries..."
    for i in 1 2 3; do
        print_status "Attempt $i/3..."
        if pip install "huggingface-hub>=0.20.0" click requests \
            "fastapi==0.95.2" "starlette==0.27.0" "pydantic==1.10.13" \
            "typing_extensions<4.7" "anyio<4" "sniffio<2" "uvicorn==0.23.2" "h11<0.15"; then
            print_status "Package installation successful"
            return 0
        else
            print_warning "Attempt $i failed, retrying..."
            sleep 5
        fi
    done
    
    print_error "All installation attempts failed"
    return 1
}

# Main troubleshooting
main() {
    print_header "iOS Network Troubleshooting"
    
    fix_network
    fix_pip
    
    if install_with_fixes; then
        print_status "Network issues fixed successfully!"
        print_status "You can now run the installer again"
    else
        print_error "Network issues persist"
        print_status "Try these solutions:"
        print_status "1. Check your internet connection"
        print_status "2. Restart iSH Shell"
        print_status "3. Try using a different network"
        print_status "4. Use the offline installer: sh install-ios-offline.sh"
    fi
}

# Run troubleshooting
main "$@"
