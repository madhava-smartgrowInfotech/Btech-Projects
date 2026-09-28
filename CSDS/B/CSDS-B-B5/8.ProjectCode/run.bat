@echo off
REM Start SignBridge: backend (8205) and frontend (5205), then open the browser.
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first. & exit /b 1)
if not exist frontend\node_modules (echo Run setup.bat first. & exit /b 1)

set BACKEND_PORT=8205
set FRONTEND_PORT=5205
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
  if "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
  if "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
)

start "SignBridge backend" cmd /k "venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "SignBridge frontend" cmd /k "cd frontend && npm run dev"

echo Waiting for SignBridge to start...
timeout /t 10 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%
echo SignBridge is running at http://localhost:%FRONTEND_PORT%   (demo login: demo@signbridge.app / demo1234)
