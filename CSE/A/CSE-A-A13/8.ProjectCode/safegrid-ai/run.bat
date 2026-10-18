@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title SafeGrid-AI

REM --- Always run from the folder that contains this .bat ---
cd /d "%~dp0"
echo ============================================================
echo   SafeGrid-AI - Explainable multi-agent power routing
echo   Symbolic Safety Shield + pandapower + FastAPI + React
echo ============================================================
echo.
echo Working directory: %CD%
echo.

REM --- Ports (defaults 8313 / 5313, override in .env) ---
set BACKEND_PORT=8313
set FRONTEND_PORT=5313
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

REM --- 1. Python ---
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found. Install Python 3.10 or newer from https://www.python.org/downloads/
  echo Tick "Add Python to PATH" during setup, then run this file again.
  pause
  exit /b 1
)
echo [OK] Python found:
python --version
echo.

REM --- 2. Virtual environment ---
echo [1/5] Checking the Python virtual environment ^(backend\.venv^)...
if not exist "backend\.venv\Scripts\python.exe" (
  echo   Creating it now...
  python -m venv backend\.venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
  )
) else (
  echo   Found backend\.venv - reusing it.
)
echo.

REM --- 3. Backend dependencies ---
echo [2/5] Installing backend dependencies ^(first run takes a few minutes^)...
"backend\.venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 (
  echo [ERROR] Could not install backend\requirements.txt. Check your internet connection and the messages above.
  pause
  exit /b 1
)
if not exist "backend\.env" (
  copy "backend\.env.example" "backend\.env" >nul
  echo   Created backend\.env from the example file ^(mock LLM, no API key needed^).
)
echo.

REM --- 4. Frontend dependencies ---
node --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js was not found. Install Node.js 18 or newer from https://nodejs.org and run this file again.
  pause
  exit /b 1
)
echo [3/5] Preparing the React frontend...
if not exist "frontend\node_modules" (
  echo   Installing frontend packages - first run only, needs internet...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed. See the messages above.
    pause
    exit /b 1
  )
  popd
) else (
  echo   Frontend packages present - skipping install.
)
echo.

REM --- 5. Start the backend in its own window ---
echo [4/5] Starting the API on http://127.0.0.1:%BACKEND_PORT% ...
set CORS_ORIGINS=http://localhost:%FRONTEND_PORT%,http://127.0.0.1:%FRONTEND_PORT%
start "SafeGrid-AI API :%BACKEND_PORT%" cmd /k "cd /d %~dp0backend && set CORS_ORIGINS=%CORS_ORIGINS%&& .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

REM --- 6. Start the frontend ---
echo [5/5] Starting the console on http://localhost:%FRONTEND_PORT% - keep this window open. Ctrl+C stops it.
echo   ^(Close the "SafeGrid-AI API" window as well to stop the backend.^)
echo   Demo sign-in:  operator@safegrid.ai  /  SafeGrid@2026
echo.
start "" cmd /c "timeout /t 8 /nobreak >nul & start http://localhost:%FRONTEND_PORT%"
cd frontend
call npm run dev
set EXITCODE=%errorlevel%
cd ..

echo.
if %EXITCODE% neq 0 (
  echo [INFO] The frontend exited with code %EXITCODE%.
  echo Common reason: port %FRONTEND_PORT% or %BACKEND_PORT% is already in use.
  echo To check:  netstat -ano ^| findstr :%FRONTEND_PORT%   then   taskkill /PID ^<pid^> /F
) else (
  echo [INFO] Frontend stopped.
)
pause
exit /b %EXITCODE%
