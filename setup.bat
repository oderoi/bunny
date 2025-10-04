@echo off
REM Run: setup.bat (in Command Prompt or PowerShell)

echo === Bunny Setup (Windows) ===
python -m venv bunny_env
call bunny_env\Scripts\activate
python -m pip install --upgrade pip
python install.py
call deactivate  REM Optional; re-activate for use
echo Done! Activate with: call bunny_env\Scripts\activate
echo Test: b --help
pause