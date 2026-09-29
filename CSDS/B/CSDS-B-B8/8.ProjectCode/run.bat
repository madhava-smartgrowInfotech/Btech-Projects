@echo off
REM Starts the CareWatch backend (port 8208) and frontend (port 5208) and opens the browser.
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Run setup.bat first.
  pause
  exit /b 1
)
start "CareWatch backend" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8208"
start "CareWatch frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 6 /nobreak >nul
start "" http://localhost:5208
