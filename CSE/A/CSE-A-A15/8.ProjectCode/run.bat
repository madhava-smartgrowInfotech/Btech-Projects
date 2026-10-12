@echo off
setlocal
cd /d "%~dp0"
if not exist venv (
  echo Run setup.bat first.
  exit /b 1
)
start "CipherVeil backend" /d "%~dp0backend" cmd /k "..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8315"
start "CipherVeil frontend" /d "%~dp0frontend" cmd /k "npm run dev"
timeout /t 6 /nobreak >nul
start "" http://localhost:5315
