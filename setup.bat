@echo off
REM Bunny Setup (Windows) - Run in VS 2022 Developer Prompt for best results

echo === Bunny Setup (Windows) ===
if not exist "bunny_env" python -m venv bunny_env
call bunny_env\Scripts\activate
python -m pip install --upgrade pip
python install.py
call deactivate
echo Done! Activate: call bunny_env\Scripts\activate
echo Test: b --help
pause