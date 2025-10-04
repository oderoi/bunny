import platform
import subprocess
import sys
import os
from pathlib import Path

def is_in_venv():
    return sys.prefix != sys.base_prefix

def run_pip_install(pkg, extra_args=None, cmake_args=None):
    cmd = [sys.executable, '-m', 'pip', 'install', pkg, '--force-reinstall', '--no-cache-dir']
    if extra_args:
        cmd.extend(extra_args)
    # Set CC/CXX to system Clang to avoid Homebrew LLVM bugs
    os.environ['CC'] = '/usr/bin/clang'
    os.environ['CXX'] = '/usr/bin/clang++'
    if cmake_args:
        os.environ['CMAKE_ARGS'] = cmake_args
    # Prepend /usr/bin to PATH for system tools
    os.environ['PATH'] = f"/usr/bin:{os.environ.get('PATH', '')}"
    try:
        subprocess.check_call(cmd, shell=platform.system() == 'Windows')
        return True
    except subprocess.CalledProcessError as e:
        print(f"Install failed: {e}")
        return False

def check_xcode():
    try:
        subprocess.check_output(['xcode-select', '-p'], stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing Xcode CLI...")
        subprocess.call(['xcode-select', '--install'])  # Prompts GUI; non-blocking

def install_bunny(editable=True):
    # Install bunny package (editable for dev)
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
        print("Manual: pip install . (or -e . for dev)")
        return False
    
# os.environ['GGML_VERBOSE'] = '0'
# os.environ['LLAMA_CPP_VERBOSE'] = '0'

if __name__ == '__main__':
    os.environ['GGML_VERBOSE'] = '0'
    os.environ['LLAMA_CPP_VERBOSE'] = '0'
    print("=== Bunny All-in-One Installer: GPU/CPU Auto-Setup ===")
    
    sys_os = platform.system()
    in_venv = is_in_venv()
    
    if sys_os == 'Darwin':
        check_xcode()  # Ensure Xcode CLI
    
    if not in_venv:
        print("⚠ Not in a virtual environment. Creating 'bunny_env'...")
        venv_cmd = [sys.executable, '-m', 'venv', 'bunny_env']
        subprocess.check_call(venv_cmd)
        
        if sys_os == 'Darwin' or sys_os == 'Linux':
            activate_cmd = f"source bunny_env/bin/activate && python install.py"
        else:  # Windows
            activate_cmd = f"bunny_env\\Scripts\\activate && python install.py"
        print(f"Next: Run '{activate_cmd}' to activate and continue.")
        sys.exit(0)
    
    print("✓ In venv. Installing llama-cpp-python...")
    has_gpu = False
    
    if sys_os == 'Darwin':  # macOS: Metal with system Clang
        print("macOS: Enabling Metal GPU (Apple Silicon/Intel) with system Clang.")
        if run_pip_install('llama-cpp-python', cmake_args='-DGGML_METAL=on'):
            has_gpu = True
            print("✓ Metal-enabled install complete.")
        else:
            print("⚠ Metal build failed; trying CPU fallback.")
            run_pip_install('llama-cpp-python')  # No CMAKE_ARGS for CPU
    else:  # Linux/Windows: NVIDIA
        try:
            subprocess.check_call(['nvidia-smi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
            print("NVIDIA GPU: Installing CUDA 12.4 wheel.")
            extra_url = 'https://abetlen.github.io/llama-cpp-python/whl/cu124'
            if run_pip_install('llama-cpp-python', ['--extra-index-url', extra_url]):
                has_gpu = True
            else:
                print("⚠ CUDA failed; trying CPU.")
                run_pip_install('llama-cpp-python')
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("No NVIDIA GPU: CPU-only install.")
            run_pip_install('llama-cpp-python')
    
    install_bunny(editable=True)
    
    print("\n=== Done! ===")
    print(f"GPU: {'Enabled' if has_gpu else 'CPU-only'}")
    print("Test: b --help")
    print("If Metal issues persist: conda install -c conda-forge llama-cpp-python")
    print("Linux deps: sudo apt install build-essential cmake")