@echo off
REM Start the AquaVision backend (port 8214) and frontend (port 5214), then open the browser
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first & exit /b 1)
if not exist frontend\node_modules (echo Run setup.bat first & exit /b 1)
if not exist .env copy .env.example .env >nul
set BACKEND_PORT=8214
set FRONTEND_PORT=5214
for /f "tokens=1,2 delims==" %%a in (.env) do (
  if "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
  if "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
)
start "AquaVision backend" cmd /k "cd backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "AquaVision frontend" cmd /k "cd frontend && npm run dev"
echo Waiting for the servers to start...
timeout /t 8 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%
echo AquaVision is running at http://localhost:%FRONTEND_PORT%  (API http://127.0.0.1:%BACKEND_PORT%/docs)
echo Close the two server windows to stop it.
