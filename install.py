import platform
import subprocess
import sys
import os
from pathlib import Path
import shutil

def is_in_venv():
    return sys.prefix != sys.base_prefix

def run_cmd(cmd, cwd=None, env=None):
    """Run shell command."""
    try:
        subprocess.check_call(cmd, shell=True, cwd=cwd, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Cmd failed: {e}")
        return False

def build_llama_cpp():
    """Clone and build llama.cpp."""
    llama_dir = BUNNY_DIR / "llama.cpp"
    if not llama_dir.exists():
        print("Cloning llama.cpp...")
        # Fixed: Clone into BUNNY_DIR with target folder
        if not run_cmd("git clone https://github.com/ggerganov/llama.cpp llama.cpp", cwd=BUNNY_DIR, env=build_env):
            return False

    # Confirm dir exists post-clone
    if not llama_dir.exists():
        print("⚠ Clone failed—dir not created.")
        return False

    print("Updating llama.cpp...")
    if not run_cmd("git pull", cwd=llama_dir, env=build_env):
        print("⚠ Update skipped (possible network/offline).")

    build_dir = llama_dir / "build"
    build_dir.mkdir(exist_ok=True)
    os.chdir(str(build_dir))  # Use str() for safety

    cmake_args = ["cmake", ".."]
    make_cmd = ["make", "-j"]
    if sys_os == "Windows":
        cmake_args += ["-G", "Visual Studio 17 2022", "-A", "x64"]
        make_cmd = ["cmake", "--build", ".", "--config", "Release", "/maxcpucount"]
    else:
        make_cmd[1] += str(os.cpu_count() or 4)

    # Add backend flags
    if has_gpu:
        if sys_os == "Darwin":
            cmake_args += ["-DLLAMA_METAL=ON"]
        else:
            # Assume CUDA if NVIDIA detected
            cmake_args += ["-DLLAMA_CUDA=ON"]

    print("Configuring...")
    if not run_cmd(" ".join(cmake_args), cwd=build_dir, env=build_env):
        return False

    print("Building...")
    if not run_cmd(" ".join(make_cmd), cwd=build_dir, env=build_env):
        return False

    print("✓ llama.cpp built!")
    return True

def install_bunny(editable=True):
    # Install bunny package
    cmd = [sys.executable, '-m', 'pip', 'install']
    if editable:
        cmd.extend(['-e', '.'])
    else:
        cmd.append('.')
    try:
        subprocess.check_call(cmd)
        print("✓ Bunny package installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠ Bunny install failed: {e}")
        return False

BUNNY_DIR = Path.home() / ".bunny"
BUNNY_DIR.mkdir(exist_ok=True)

if __name__ == '__main__':
    print("=== Bunny All-in-One Installer: llama.cpp Native Build ===")
    
    sys_os = platform.system()
    in_venv = is_in_venv()
    
    # Env for build
    build_env = os.environ.copy()
    build_env['PATH'] = f"/usr/bin:{build_env.get('PATH', '')}"  # System tools first
    
    if sys_os == 'Darwin':
        build_env['CC'] = '/usr/bin/clang'
        build_env['CXX'] = '/usr/bin/clang++'
        # Check Xcode
        try:
            subprocess.check_output(['xcode-select', '-p'], stderr=subprocess.DEVNULL)
        except:
            print("Installing Xcode CLI...")
            os.system('xcode-select --install')  # Non-blocking
            input("Press Enter after install...")  # Wait user
    
    if not in_venv:
        print("⚠ Not in a virtual environment. Creating 'bunny_env'...")
        venv_cmd = [sys.executable, '-m', 'venv', 'bunny_env']
        subprocess.check_call(venv_cmd)
        
        if sys_os in ['Darwin', 'Linux']:
            activate = f"source bunny_env/bin/activate && python install.py"
        else:
            activate = f"bunny_env\\Scripts\\activate && python install.py"
        print(f"Next: Run '{activate}' to continue.")
        sys.exit(0)
    
    print("✓ In venv. Upgrading pip...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    
    has_gpu = False
    if sys_os == 'Darwin':
        print("macOS: Building with Metal (Apple Silicon/Intel).")
        has_gpu = True
    else:
        # Check NVIDIA
        try:
            subprocess.check_call(['nvidia-smi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
            print("NVIDIA detected: Building with CUDA.")
            has_gpu = True
            # Ensure CUDA in PATH (assume installed)
            build_env['PATH'] += os.pathsep + '/usr/local/cuda/bin'
        except:
            print("No NVIDIA: CPU-only build.")
    
    # Build llama.cpp
    if not build_llama_cpp():
        print("⚠ llama.cpp build failed. Ensure: git, cmake, build tools.")
        if sys_os == 'Linux':
            print("Run: sudo apt install git cmake build-essential")
        elif sys_os == 'Darwin':
            print("Run: xcode-select --install; brew install cmake git")
        elif sys_os == 'Windows':
            print("Run from 'Developer Command Prompt for VS 2022': cmake, git installed.")
        sys.exit(1)
    
    # FIXED: Change back to project root before installing Bunny
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"Changed to project dir: {project_dir}")
    
    # Install Python deps (no llama-cpp-python)
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'huggingface-hub>=0.20.0', 'click>=8.1.0', 'requests'])
    
    install_bunny(editable=True)
    
    print("\n=== Done! ===")
    print(f"GPU: {'Enabled' if has_gpu else 'CPU-only'}")
    print("Test: b --help | b list")
    print("Models in ~/.bunny/models/. Binary: ~/.bunny/llama.cpp/build/bin/llama-server")
    if sys_os == 'Windows':
        print("Note: Run in VS Developer Prompt if build issues.")