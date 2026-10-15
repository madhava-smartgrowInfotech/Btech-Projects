@echo off
rem PlastiScan - starts the API (port 8114) and the web app (port 5114).
setlocal
cd /d "%~dp0"

if not defined BACKEND_PORT set BACKEND_PORT=8114
if not defined FRONTEND_PORT set FRONTEND_PORT=5114

if not exist ".venv\Scripts\python.exe" (
  echo [setup] Creating Python virtual environment and installing requirements - first run only...
  python -m venv .venv || goto :fail
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt -r backend\requirements.txt || goto :fail
)

if not exist "frontend\node_modules" (
  echo [setup] Installing frontend packages - first run only...
  pushd frontend
  call npm install || (popd & goto :fail)
  popd
)

start "PlastiScan API %BACKEND_PORT%" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "PlastiScan web %FRONTEND_PORT%" cmd /k "cd frontend && npm run dev"

echo.
echo API:  http://127.0.0.1:%BACKEND_PORT%/docs
echo App:  http://localhost:%FRONTEND_PORT%
timeout /t 6 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%
exit /b 0

:fail
echo Setup failed - see the messages above.
exit /b 1
