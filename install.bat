@echo off
REM Bunny Universal Installer for Windows
REM Supports: Windows 10/11, WSL, Windows Server

setlocal enabledelayedexpansion

echo === Bunny AI Universal Installer for Windows ===

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running as administrator
) else (
    echo [WARN] Not running as administrator. Some features may require elevation.
)

REM Detect Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo [INFO] Windows Version: %VERSION%

REM Check for required tools
echo [INFO] Checking for required tools...

REM Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ from https://python.org
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Git
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Git not found. Please install Git from https://git-scm.com
    pause
    exit /b 1
)

REM Check CMake
cmake --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] CMake not found. Please install CMake from https://cmake.org
    echo [INFO] Or install Visual Studio Build Tools which includes CMake
    pause
    exit /b 1
)

echo [INFO] All required tools found!

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist bunny_env (
    echo [WARN] Virtual environment already exists. Removing...
    rmdir /s /q bunny_env
)

python -m venv bunny_env
if %errorLevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call bunny_env\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install Python dependencies
echo [INFO] Installing Python dependencies...
pip install huggingface-hub>=0.20.0 click>=8.1.0 requests>=2.28.0 fastapi uvicorn python-multipart

REM Clone and build llama.cpp
echo [INFO] Cloning llama.cpp...
if exist llama.cpp (
    echo [INFO] llama.cpp directory exists, updating...
    cd llama.cpp
    git pull
    cd ..
) else (
    git clone https://github.com/ggerganov/llama.cpp.git
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to clone llama.cpp
        pause
        exit /b 1
    )
)

echo [INFO] Building llama.cpp...
cd llama.cpp

REM Create build directory
if not exist build mkdir build
cd build

REM Configure with CMake
echo [INFO] Configuring build...
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
if %errorLevel% neq 0 (
    echo [ERROR] CMake configuration failed
    echo [INFO] Make sure you have Visual Studio 2022 or Build Tools installed
    pause
    exit /b 1
)

REM Build
echo [INFO] Building llama.cpp (this may take several minutes)...
cmake --build . --config Release --maxcpucount
if %errorLevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

cd ..\..
echo [INFO] llama.cpp built successfully!

REM Install Bunny package
echo [INFO] Installing Bunny package...
pip install -e .
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install Bunny package
    pause
    exit /b 1
)

REM Create desktop shortcut
echo [INFO] Creating desktop shortcut...
set DESKTOP=%USERPROFILE%\Desktop
echo [InternetShortcut] > "%DESKTOP%\Bunny AI.url"
echo URL=http://localhost:8080 >> "%DESKTOP%\Bunny AI.url"
echo IconFile=%CD%\bunny_env\Scripts\python.exe >> "%DESKTOP%\Bunny AI.url"
echo IconIndex=0 >> "%DESKTOP%\Bunny AI.url"

REM Create start menu shortcut
echo [INFO] Creating start menu shortcut...
set STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
if not exist "%STARTMENU%\Bunny AI" mkdir "%STARTMENU%\Bunny AI"

REM Create batch file for easy startup
echo @echo off > "%STARTMENU%\Bunny AI\Start Bunny AI.bat"
echo cd /d "%CD%" >> "%STARTMENU%\Bunny AI\Start Bunny AI.bat"
echo call bunny_env\Scripts\activate.bat >> "%STARTMENU%\Bunny AI\Start Bunny AI.bat"
echo b serve_ui >> "%STARTMENU%\Bunny AI\Start Bunny AI.bat"
echo pause >> "%STARTMENU%\Bunny AI\Start Bunny AI.bat"

REM Test installation
echo [INFO] Testing installation...
b --help >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Installation test passed!
) else (
    echo [ERROR] Installation test failed
    pause
    exit /b 1
)

echo.
echo === Installation Complete! ===
echo.
echo [SUCCESS] Bunny AI has been successfully installed!
echo.
echo Usage:
echo   b --help                    # Show help
echo   b list                      # List available models
echo   b pull ^<model^>              # Download a model
echo   b run ^<model^>               # Start chat with model
echo   b serve_ui ^<model^>          # Start web interface
echo.
echo Web UI will be available at: http://localhost:8080
echo Mobile-friendly interface included!
echo.
echo You can start Bunny AI from:
echo   - Start Menu: "Bunny AI" folder
echo   - Desktop: "Bunny AI.url" shortcut
echo   - Command Line: b serve_ui
echo.
pause
