# 🐰 Bunny AI - Universal Local LLM Runner

**Run AI models locally on any device - computers, phones, tablets, and more!**

Bunny AI is a powerful, cross-platform local LLM runner that uses native llama.cpp for maximum performance. It supports GGUF models from Hugging Face and provides both CLI and web interfaces optimized for all devices.

## ✨ Features

- 🚀 **Universal Compatibility**: Runs on all operating systems and devices
- 📱 **Mobile-Optimized**: Touch-friendly interface for phones and tablets
- 🖥️ **Desktop Ready**: Full-featured interface for computers
- 🔧 **Easy Installation**: One-command setup for any platform
- 🌐 **Web Interface**: Access from any device on your network
- 📦 **Model Management**: Download and manage models easily
- ⚡ **High Performance**: Native llama.cpp integration
- 🔒 **Privacy First**: Everything runs locally on your device

## 🚀 Quick Start

### One-Command Installation

**Any Platform:**
```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/bunny/main/install-universal.sh | bash
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/bunny/main/install.bat" -OutFile "install.bat"
.\install.bat
```

**Mobile (Android/iOS):**
```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/bunny/main/install-mobile.sh | bash
```

## 📱 Supported Platforms

### Desktop & Laptop
- ✅ **macOS** (Intel & Apple Silicon)
- ✅ **Windows** (10/11, WSL)
- ✅ **Linux** (Ubuntu, Debian, Arch, Fedora, etc.)

### Mobile Devices
- ✅ **Android** (Termux)
- ✅ **iOS** (iSH Shell)
- ✅ **Linux Mobile** (PinePhone, Librem 5, etc.)

### Server & Cloud
- ✅ **Docker** (Any platform)
- ✅ **VPS/Cloud** (Ubuntu, CentOS, etc.)
- ✅ **Raspberry Pi** (ARM devices)

## 🛠️ Installation Methods

### 1. Universal Installer (Recommended)
```bash
# Download and run universal installer
curl -fsSL https://raw.githubusercontent.com/your-repo/bunny/main/install-universal.sh | bash

# Or clone and run
git clone https://github.com/your-repo/bunny.git
cd bunny
bash install-universal.sh
```

### 2. Platform-Specific Installers

**Linux/macOS:**
```bash
bash install.sh
```

**Windows:**
```cmd
install.bat
```

**Mobile:**
```bash
bash install-mobile.sh
```

### 3. Package Managers

**Snap (Linux):**
```bash
sudo snap install bunny-ai
```

**Homebrew (macOS):**
```bash
brew install bunny-ai
```

**Chocolatey (Windows):**
```powershell
choco install bunny-ai
```

**AUR (Arch Linux):**
```bash
yay -S bunny-ai
```

### 4. Docker
```bash
# Single container
docker run -p 8080:8080 bunny-ai

# Docker Compose (recommended)
git clone https://github.com/your-repo/bunny.git
cd bunny
docker-compose up -d
```

## 🎯 Usage

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
1. Start Bunny AI: `b serve_ui`
2. Open browser: `http://localhost:8080`
3. Access from any device on your network!

### Mobile Access
1. Start Bunny AI on your computer
2. Find your computer's IP address
3. Open browser on phone/tablet
4. Go to `http://YOUR_IP:8080`
5. Enjoy mobile-optimized interface!

## 📱 Mobile Features

### Touch-Optimized Interface
- **Swipe Navigation**: Easy model switching
- **Touch Targets**: Large, finger-friendly buttons
- **Responsive Design**: Adapts to any screen size
- **Offline Support**: Works without internet

### Mobile-Specific Commands
```bash
# Mobile-optimized installation
bash install-mobile.sh

# Start with mobile optimizations
export BUNNY_MOBILE_MODE=true
b serve_ui
```

## 🔧 Configuration

### Environment Variables
```bash
# Hugging Face token (for private models)
export HF_HUB_TOKEN="your_token_here"

# Custom model directory
export BUNNY_HOME="/path/to/models"

# Mobile optimizations
export BUNNY_MOBILE_MODE=true
export BUNNY_LOW_MEMORY=true
export BUNNY_BATTERY_SAVER=true
```

### Mobile Configuration
```json
{
  "mobile_optimized": true,
  "max_context": 1024,
  "max_tokens": 512,
  "low_memory_mode": true,
  "battery_saver": true
}
```

## 🌐 Network Access

### Local Network Access
```bash
# Start with network access
b serve_ui --host 0.0.0.0 --port 8080

# Access from other devices
# http://YOUR_IP:8080
```

### Docker Network Access
```yaml
# docker-compose.yml
services:
  bunny-ai:
    ports:
      - "8080:8080"
    environment:
      - BUNNY_HOST=0.0.0.0
```

## 📦 Model Management

### Download Models
```bash
# Download popular models
b pull tinyllama
b pull qwen3:0.6b
b pull deepseek-r1:1.5b

# Download custom models
b pull custom-model --repo "user/repo" --file "model.gguf"
```

### List Models
```bash
# List all models
b list

# List installed models
b list --installed

# List available models
b list --available
```

## 🔧 Troubleshooting

### Common Issues

**"Command not found: b"**
```bash
# Activate virtual environment
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

## 📊 System Requirements

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

## 🚀 Performance Tips

### Mobile Optimization
```bash
# Enable mobile mode
export BUNNY_MOBILE_MODE=true
export BUNNY_LOW_MEMORY=true
export BUNNY_BATTERY_SAVER=true
```

### Desktop Optimization
```bash
# Use GPU acceleration
export BUNNY_GPU=true
export BUNNY_METAL=true  # macOS
export BUNNY_CUDA=true   # Linux/Windows
```

## 📚 Documentation

- **[Installation Guide](INSTALL.md)**: Detailed installation instructions
- **[API Documentation](docs/API.md)**: API reference
- **[Mobile Guide](docs/MOBILE.md)**: Mobile-specific features
- **[Docker Guide](docs/DOCKER.md)**: Docker deployment
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-repo/bunny.git
cd bunny

# Install development dependencies
bash install-universal.sh --dev

# Run tests
npm test

# Build web UI
npm run ui:build
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Native LLM inference
- [Hugging Face](https://huggingface.co/) - Model repository
- [Material-UI](https://mui.com/) - React components
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework

## 📞 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/your-repo/bunny/issues)
- **Documentation**: [Full documentation](https://github.com/your-repo/bunny/wiki)
- **Community**: [Discord/Forum](https://discord.gg/bunny-ai)

---

**🎉 Enjoy your local AI assistant on any device!**

Made with ❤️ for the open-source community.