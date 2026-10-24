@echo off
REM SentinelFlow launcher - double-click from Windows Explorer.
REM   run.bat          install what is missing, start API (8415) and the React UI (5415)
REM   run.bat check    install what is missing, then exit without starting servers
setlocal EnableExtensions

REM 1. Move to the folder that contains this script.
cd /d "%~dp0"
echo ============================================================
echo  SentinelFlow - Real-Time DDoS Detection ^& Adaptive Mitigation
echo  Folder: %CD%
echo ============================================================

REM 2. Ports: create .env on first run, then read it.
if not exist ".env" (
  echo BACKEND_HOST=127.0.0.1> .env
  echo BACKEND_PORT=8415>> .env
  echo FRONTEND_PORT=5415>> .env
)
set BACKEND_PORT=8415
set FRONTEND_PORT=5415
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
  if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
)

REM 3. Check Python availability.
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] Python was not found on PATH.
  echo Please install Python 3.11 or 3.12 from https://www.python.org/downloads/
  echo During installation, tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] Node.js ^(npm^) was not found on PATH.
  echo Please install Node.js 20 or newer from https://nodejs.org/
  echo.
  pause
  exit /b 1
)

echo [1/6] Python found:
python --version

REM 4. Create the virtual environment when missing or when it points at a Python that no longer exists.
set NEED_VENV=0
if not exist ".venv\Scripts\python.exe" set NEED_VENV=1
if "%NEED_VENV%"=="0" (
  ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
  if errorlevel 1 set NEED_VENV=1
)
if "%NEED_VENV%"=="1" (
  echo [2/6] Creating virtual environment .venv ...
  if exist ".venv" rmdir /s /q ".venv"
  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo [ERROR] Virtual-environment creation failed. Command: python -m venv .venv
    pause
    exit /b 1
  )
) else (
  echo [2/6] Virtual environment already exists, reusing it.
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate .venv.
  pause
  exit /b 1
)

REM 5. Install Python dependencies.
echo [3/6] Installing Python dependencies from requirements.txt ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [ERROR] Dependency installation failed. See the pip error above.
  pause
  exit /b 1
)

REM 6. Train the model if missing.
echo [4/6] Checking SentinelFlow model ...
if not exist "models\sentinelflow_rf.joblib" (
  echo Model not found - running training and evaluation now ^(may take a few minutes^)...
  python ml\train_model.py
  if errorlevel 1 (
    echo.
    echo [ERROR] Model training failed. See the error above.
    pause
    exit /b 1
  )
) else (
  echo Model found, skipping training.
)

REM 7. Install the frontend dependencies.
echo [5/6] Checking the React frontend ...
if not exist "frontend\node_modules" (
  echo Installing frontend packages ^(first run only^)...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo.
    echo [ERROR] npm install failed. See the error above.
    pause
    exit /b 1
  )
  popd
) else (
  echo Frontend packages found.
)

if /i "%~1"=="check" (
  echo.
  echo Check complete: everything is installed.
  exit /b 0
)

REM 8. Start the API in its own window, then the React UI here.
echo [6/6] Starting SentinelFlow API on http://127.0.0.1:%BACKEND_PORT% and UI on http://127.0.0.1:%FRONTEND_PORT%
start "SentinelFlow API" /min cmd /c "call .venv\Scripts\activate.bat && python app.py"
start "" "http://127.0.0.1:%FRONTEND_PORT%/"
cd frontend
call npm run dev
set EXITCODE=%errorlevel%

echo.
echo SentinelFlow UI stopped ^(exit code %EXITCODE%^). Close the "SentinelFlow API" window to stop the API.
pause
exit /b %EXITCODE%
