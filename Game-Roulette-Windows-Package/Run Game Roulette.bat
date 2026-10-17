@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto pythonerror
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto installerror
)
".venv\Scripts\python.exe" game_roulette.py
if errorlevel 1 pause
exit /b 0
:pythonerror
echo Could not create a local Python environment. Install Python 3.10+ and try again.
pause
exit /b 1
:installerror
echo Could not install dependencies. Check your internet connection and try again.
pause
exit /b 1
