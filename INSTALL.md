# 🐰 Bunny AI - Universal Installation Guide

Bunny AI is designed to run on **all devices and operating systems**. This guide covers installation for computers, phones, and tablets.

## 🚀 Quick Start

### One-Command Installation

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/bunny/main/install.sh | bash
```

**Windows:**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/bunny/main/install.bat" -OutFile "install.bat"
.\install.bat
```

**Mobile (Android/iOS):**
```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/bunny/main/install-mobile.sh | bash
```

## 📱 Mobile Installation

### Android (Termux)
```bash
# Install Termux from F-Droid or Google Play
# Open Termux and run:
pkg update && pkg install git
git clone https://github.com/your-repo/bunny.git
cd bunny
bash install-mobile.sh
```

### iOS (iSH Shell)
```bash
# Install iSH from App Store
# Open iSH and run:
apk add git
git clone https://github.com/your-repo/bunny.git
cd bunny
bash install-mobile.sh
```

### Linux Mobile Devices
```bash
# For devices like PinePhone, Librem 5, etc.
sudo apt update
sudo apt install git
git clone https://github.com/your-repo/bunny.git
cd bunny
bash install-mobile.sh
```

## 💻 Desktop Installation

### macOS
```bash
# Using Homebrew (recommended)
brew install bunny-ai

# Or manual installation
git clone https://github.com/your-repo/bunny.git
cd bunny
bash install.sh
```

### Windows
```powershell
# Using Chocolatey
choco install bunny-ai

# Or manual installation
git clone https://github.com/your-repo/bunny.git
cd bunny
.\install.bat
```

### Linux
```bash
# Ubuntu/Debian
sudo apt install bunny-ai

# Arch Linux (AUR)
yay -S bunny-ai

# Snap
sudo snap install bunny-ai

# Manual installation
git clone https://github.com/your-repo/bunny.git
cd bunny
bash install.sh
```

## 🐳 Docker Installation

### Single Container
```bash
# Build and run
docker build -t bunny-ai .
docker run -p 8080:8080 -v bunny_models:/app/.bunny/models bunny-ai
```

### Docker Compose (Recommended)
```bash
# Clone repository
git clone https://github.com/your-repo/bunny.git
cd bunny

# Start with Docker Compose
docker-compose up -d

# Access web UI at http://localhost:8080
```

### Docker with GPU Support
```bash
# For NVIDIA GPUs
docker run --gpus all -p 8080:8080 -v bunny_models:/app/.bunny/models bunny-ai
```

## 📦 Package Manager Installation

### Snap (Linux)
```bash
sudo snap install bunny-ai
```

### Homebrew (macOS)
```bash
brew install bunny-ai
```

### Chocolatey (Windows)
```powershell
choco install bunny-ai
```

### AUR (Arch Linux)
```bash
yay -S bunny-ai
```

## 🔧 Manual Installation

### Prerequisites
- Python 3.9+
- Git
- CMake
- Build tools (gcc, make, etc.)

### Step-by-Step
1. **Clone repository:**
   ```bash
   git clone https://github.com/your-repo/bunny.git
   cd bunny
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv bunny_env
   source bunny_env/bin/activate  # Linux/macOS
   # or
   bunny_env\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Build llama.cpp:**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   mkdir build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   make -j$(nproc)
   cd ../..
   ```

5. **Test installation:**
   ```bash
   b --help
   ```

## 🌐 Web Interface

After installation, start the web interface:

```bash
# Start web UI
b serve_ui

# Access from any device
# http://localhost:8080
```

The web interface is **mobile-optimized** and works on:
- 📱 Smartphones
- 📱 Tablets
- 💻 Laptops
- 🖥️ Desktops

## 📱 Mobile Access

### From Your Phone
1. Start Bunny AI on your computer
2. Find your computer's IP address
3. Open browser on phone
4. Go to `http://YOUR_IP:8080`
5. Enjoy mobile-optimized interface!

### From Any Device
The web interface automatically detects your device and provides:
- **Mobile**: Touch-optimized interface
- **Desktop**: Full-featured interface
- **Tablet**: Hybrid interface

## 🔧 Configuration

### Environment Variables
```bash
export HF_HUB_TOKEN="your_token_here"  # For private models
export BUNNY_HOME="/path/to/models"    # Custom model directory
```

### Mobile Optimizations
```bash
# Enable mobile mode
export BUNNY_MOBILE_MODE=true
export BUNNY_LOW_MEMORY=true
export BUNNY_BATTERY_SAVER=true
```

## 🚀 Usage Examples

### CLI Usage
```bash
# List available models
b list

# Download a model
b pull tinyllama

# Start chat
b run tinyllama

# Start web interface
b serve_ui tinyllama
```

### Web Interface
1. Open browser to `http://localhost:8080`
2. Select a model
3. Start chatting!
4. Access from any device on your network

## 🔧 Troubleshooting

### Common Issues

**"Command not found: b"**
```bash
# Make sure virtual environment is activated
source bunny_env/bin/activate  # Linux/macOS
bunny_env\Scripts\activate     # Windows
```

**"Build failed"**
```bash
# Install build dependencies
# Ubuntu/Debian:
sudo apt install build-essential cmake git

# macOS:
xcode-select --install
brew install cmake git

# Windows:
# Install Visual Studio Build Tools
```

**"Port already in use"**
```bash
# Use different port
b serve_ui --port 8081
```

### Mobile Issues

**"Permission denied"**
```bash
# Android (Termux):
chmod +x install-mobile.sh
bash install-mobile.sh

# iOS (iSH):
# Make sure you have proper permissions
```

**"Out of memory"**
```bash
# Use smaller models
b pull tinyllama  # Instead of larger models
```

## 📞 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/your-repo/bunny/issues)
- **Documentation**: [Full documentation](https://github.com/your-repo/bunny/wiki)
- **Community**: [Discord/Forum](https://discord.gg/bunny-ai)

## 🎯 System Requirements

### Minimum Requirements
- **RAM**: 2GB (4GB recommended)
- **Storage**: 1GB free space
- **CPU**: Any modern processor
- **OS**: Linux, macOS, Windows, Android, iOS

### Recommended Requirements
- **RAM**: 8GB+ for larger models
- **Storage**: 10GB+ for multiple models
- **GPU**: NVIDIA/AMD/Apple Silicon for acceleration
- **Network**: Internet for model downloads

## 🔄 Updates

```bash
# Update Bunny AI
git pull
pip install -e .

# Update llama.cpp
cd llama.cpp
git pull
cd build
make -j$(nproc)
```

---

**🎉 Enjoy your local AI assistant on any device!**
