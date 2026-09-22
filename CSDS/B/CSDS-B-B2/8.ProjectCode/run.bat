@echo off
setlocal
cd /d "%~dp0"
title SignalScout

if not exist "venv\Scripts\python.exe" (
  echo SignalScout is not set up yet. Double-click setup.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo The web app packages are missing. Run setup.bat first.
  pause
  exit /b 1
)

"venv\Scripts\python.exe" scripts\launcher.py %*
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" pause
exit /b %CODE%
