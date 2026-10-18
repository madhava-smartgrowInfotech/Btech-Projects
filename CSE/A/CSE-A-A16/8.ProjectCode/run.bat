@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title SignSpeak

REM --- Always run from the folder that contains this .bat ---
cd /d "%~dp0"
echo ============================================================
echo   SignSpeak - Sign Language Recognition System ^(CNN^)
echo   FastAPI backend + React frontend  ^|  CSE-A-A16
echo ============================================================
echo.

REM --- 1. Python ---
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found. Install Python 3.10 or 3.11 from https://www.python.org/downloads/
  echo         and tick "Add Python to PATH", then run this file again.
  pause
  exit /b 1
)

REM --- 2. Virtual environment ---
echo [1/5] Checking the Python virtual environment ^(.venv^)...
if not exist ".venv\Scripts\python.exe" (
  echo   Creating .venv ^(first run only^)...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
  )
)
call ".venv\Scripts\activate.bat"

REM --- 3. Python packages (TensorFlow is large: the first run takes several minutes) ---
echo [2/5] Installing Python packages from requirements.txt ...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed. Check your internet connection and try again.
  pause
  exit /b 1
)

REM --- 4. Ports from .env (defaults 8316 / 5316) ---
set BACKEND_PORT=8316
set FRONTEND_PORT=5316
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

REM --- 5. Frontend packages (needs Node.js 18 or newer) ---
node --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js was not found. Install it from https://nodejs.org and run this file again.
  pause
  exit /b 1
)
echo [3/5] Preparing the React frontend ...
if not exist "frontend\node_modules" (
  echo   Installing frontend packages - first run only, needs internet...
  pushd frontend
  call npm install
  popd
) else (
  echo   Frontend packages present - skipping install.
)

REM --- 6. Backend in its own window ---
echo [4/5] Starting the API on http://127.0.0.1:%BACKEND_PORT% ...
start "SignSpeak API :%BACKEND_PORT%" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

REM --- 7. Frontend (this window) ---
echo [5/5] Starting the web app on http://localhost:%FRONTEND_PORT% - keep this window open. Ctrl+C stops it.
echo   ^(Close the "SignSpeak API" window as well to stop the backend.^)
echo   The first request waits a few seconds while TensorFlow loads.
echo.
start "" cmd /c "timeout /t 8 /nobreak >nul & start http://localhost:%FRONTEND_PORT%"
cd frontend
call npm run dev
set EXITCODE=%errorlevel%
cd ..

echo.
if %EXITCODE% neq 0 (
  echo [INFO] The web app exited with code %EXITCODE%.
  echo   Common reason: port %FRONTEND_PORT% or %BACKEND_PORT% is already in use.
  echo   To check:  netstat -ano ^| findstr :%FRONTEND_PORT%   then   taskkill /PID ^<pid^> /F
)
pause
exit /b %EXITCODE%
