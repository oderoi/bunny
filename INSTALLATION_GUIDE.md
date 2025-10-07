# 🐰 Bunny AI - Complete Installation Guide

## ✅ **Fixed Issues:**
- **C++ Compiler Missing**: Added `g++` and `build-base` to all mobile installers
- **Rust Build Errors**: Pinned FastAPI stack to Pydantic v1 (no Rust required)
- **iOS iSH Compatibility**: Created iOS-specific installer with ash shell support
- **Cross-Platform Support**: Universal installers for all devices

## 📱 **Mobile Installation (iOS/Android)**

### **iOS (iSH Shell) - FIXED**
```bash
# 1. Install iSH from App Store
# 2. Open iSH and run:
apk update
apk add python3 py3-pip git cmake make gcc g++ musl-dev bash build-base
git clone https://github.com/your-repo/bunny.git
cd bunny
sh install-ios.sh

# 3. Start Bunny AI
./start_bunny.sh
```

### **Android (Termux) - FIXED**
```bash
# 1. Install Termux from F-Droid (recommended)
# 2. Open Termux and run:
pkg update
pkg install python git cmake clang clang++ make
git clone https://github.com/your-repo/bunny.git
cd bunny
bash install-mobile.sh

# 3. Start Bunny AI
./start_bunny.sh
```

## 💻 **Desktop Installation**

### **Universal Installer (Auto-detects platform)**
```bash
# One command for any platform
curl -fsSL https://raw.githubusercontent.com/your-repo/bunny/main/install-universal.sh | bash
```

### **Platform-Specific**

**macOS:**
```bash
bash install.sh
```

**Windows:**
```cmd
install.bat
```

**Linux:**
```bash
bash install.sh
```

## 🐳 **Docker Installation**

### **Single Container**
```bash
docker run -p 8080:8080 bunny-ai
```

### **Docker Compose (Recommended)**
```bash
git clone https://github.com/your-repo/bunny.git
cd bunny
docker-compose up -d
```

## 📦 **Package Managers**

### **Snap (Linux)**
```bash
sudo snap install bunny-ai
```

### **Homebrew (macOS)**
```bash
brew install bunny-ai
```

### **Chocolatey (Windows)**
```powershell
choco install bunny-ai
```

### **AUR (Arch Linux)**
```bash
yay -S bunny-ai
```

## 🚀 **Usage After Installation**

### **CLI Usage**
```bash
# List models
b list

# Download a model
b pull tinyllama

# Start chat
b run tinyllama

# Start web interface
b serve_ui tinyllama
```

### **Web Interface**
1. **Start**: `b serve_ui`
2. **Access**: `http://localhost:8080`
3. **Mobile**: Touch-optimized interface
4. **Network**: Access from any device on your network

## 📱 **Mobile Access**

### **From Your Phone**
1. **Start Bunny AI on computer**: `b serve_ui --host 0.0.0.0`
2. **Find computer IP**: `ifconfig` (macOS/Linux) or `ipconfig` (Windows)
3. **Open phone browser**: `http://YOUR_IP:8080`
4. **Enjoy mobile interface!**

### **Direct Phone Installation**
- **iOS**: Use `sh install-ios.sh` (now fixed)
- **Android**: Use `bash install-mobile.sh` (now fixed)

## 🔧 **Troubleshooting**

### **"No CMAKE_CXX_COMPILER could be found" - FIXED**
- **Solution**: All installers now include `g++` and `build-base`
- **iOS**: `apk add gcc g++ build-base`
- **Android**: `pkg install clang clang++`

### **"Rust toolchain not supported" - FIXED**
- **Solution**: Pinned FastAPI stack to Pydantic v1 (no Rust)
- **Files**: `requirements-mobile.txt` with safe versions

### **"Command not found: bash" - FIXED**
- **Solution**: Created ash-compatible installers
- **iOS**: Use `sh install-ios.sh`
- **Alternative**: `apk add bash` then use bash installers

## 🎯 **Quick Start Commands**

### **Easiest Method (Computer + Phone)**
```bash
# On your computer:
b serve_ui --host 0.0.0.0

# On your phone:
# Open browser to http://YOUR_COMPUTER_IP:8080
```

### **Direct Phone Installation**
```bash
# iOS (iSH):
sh install-ios.sh

# Android (Termux):
bash install-mobile.sh
```

### **Universal (Any Platform)**
```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/bunny/main/install-universal.sh | bash
```

## 🌟 **What's Fixed**

1. **✅ C++ Compiler Issues**: All installers now include `g++` and `build-base`
2. **✅ Rust Build Errors**: Pinned to Pydantic v1 (no Rust required)
3. **✅ iOS iSH Compatibility**: Ash-compatible installers
4. **✅ Mobile Dependencies**: Complete build toolchain for all platforms
5. **✅ Cross-Platform**: Works on any device and operating system

## 📞 **Support**

If you still encounter issues:
1. **Check dependencies**: Make sure all build tools are installed
2. **Clean install**: Remove `bunny_env` and try again
3. **Use requirements**: `pip install -r requirements-mobile.txt`
4. **Report issues**: GitHub issues with your platform details

---

**🎉 Bunny AI now works on ALL devices - phones, computers, tablets, and more!**
