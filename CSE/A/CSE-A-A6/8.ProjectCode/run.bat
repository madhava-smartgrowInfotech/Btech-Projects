@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Smart Rider

REM --- Always run from the folder that contains this .bat ---
cd /d "%~dp0"
echo ============================================================
echo   Smart Rider Impairment Warning System ^(two-wheelers^)
echo   FastAPI backend + React frontend  ^|  CSE-A-A6
echo ============================================================
echo.

REM --- 1. Python: prefer 3.14 ^(the version the pinned packages were tested on^), else whatever "python" is ---
set PYLAUNCH=python
py -3.14 --version >nul 2>&1
if not errorlevel 1 set PYLAUNCH=py -3.14
%PYLAUNCH% --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found. Install Python 3.12 or newer from https://www.python.org/downloads/
  echo         and tick "Add Python to PATH", then run this file again.
  pause
  exit /b 1
)

REM --- 2. Virtual environment: rebuild it if it was copied from another PC and points at a missing Python ---
echo [1/6] Checking the Python virtual environment ^(.venv^)...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
  if errorlevel 1 (
    echo   The existing .venv belongs to another computer - recreating it...
    rmdir /s /q .venv
  )
)
if not exist ".venv\Scripts\python.exe" (
  echo   Creating .venv ^(first run only^)...
  %PYLAUNCH% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
  )
)
call ".venv\Scripts\activate.bat"

REM --- 3. Python packages ---
echo [2/6] Installing Python packages ^(first run takes a few minutes^)...
python -m pip install --disable-pip-version-check -q -r requirements.txt -r backend\requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed. Check your internet connection and try again.
  pause
  exit /b 1
)

REM --- 4. Face landmark model ^(one-time download from Google^) ---
if not exist "models\face_landmarker.task" (
  echo [3/6] Downloading the face landmark model ^(one time^)...
  python setup_model.py
  if errorlevel 1 (
    echo [WARNING] The model could not be downloaded. The simulation still works; run "python setup_model.py" later for the camera.
  )
) else (
  echo [3/6] Face landmark model present.
)

REM --- 5. Ports from .env ^(defaults 8306 / 5306^) ---
set BACKEND_PORT=8306
set FRONTEND_PORT=5306
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

REM --- 6. Frontend packages ^(needs Node.js 18 or newer^) ---
node --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js was not found. Install it from https://nodejs.org and run this file again.
  pause
  exit /b 1
)
echo [4/6] Preparing the React frontend ...
if not exist "frontend\node_modules" (
  echo   Installing frontend packages - first run only, needs internet...
  pushd frontend
  call npm install
  popd
) else (
  echo   Frontend packages present - skipping install.
)

REM --- 7. Backend in its own window ---
echo [5/6] Starting the API on http://127.0.0.1:%BACKEND_PORT% ...
start "Smart Rider API :%BACKEND_PORT%" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

REM --- 8. Frontend ^(this window^) ---
echo [6/6] Starting the web app on http://localhost:%FRONTEND_PORT% - keep this window open. Ctrl+C stops it.
echo   ^(Close the "Smart Rider API" window as well to stop the backend.^)
echo   Demo login:  demo@smartrider.app  /  Demo@1234
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
