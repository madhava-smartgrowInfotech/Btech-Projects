@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title CipherGuard Shield

REM --- Always run from the folder that contains this .bat (works even if launched from elsewhere / via symlink) ---
cd /d "%~dp0"
echo ============================================================
echo   CipherGuard Shield - Secure Data Transmission Platform
echo   AES-256-GCM + ECDH P-256 + HKDF  ^|  ThreatSense Engine
echo   XGBoost + 1D CNN + Logistic Regression stacking  ^|  UNSW-NB15
echo ============================================================
echo.
echo Working directory: %CD%
echo.

REM --- 1. Check Python is installed and on PATH ---
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found.
  echo.
  echo Python 3.10 or newer is required. Install it from:
  echo   https://www.python.org/downloads/
  echo.
  echo During setup, check the box labeled "Add Python to PATH".
  echo After installing, close this window and double-click run.bat again.
  echo.
  pause
  exit /b 1
)
echo [OK] Python found:
python --version
echo.

REM --- 2. Create virtual environment only if it does not already exist ---
echo [1/4] Checking Python virtual environment ^(.venv^)...
if not exist ".venv\Scripts\python.exe" (
  echo   .venv not found - creating it now ^(this may take a moment^)...
  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create virtual environment.
    echo Look at the message above for details - common causes: antivirus blocking,
    echo missing permissions, or a corrupted Python install. Try right-clicking
    echo run.bat and choosing "Run as administrator".
    echo.
    pause
    exit /b 1
  )
  echo   Virtual environment created.
) else (
  echo   Found .venv - reusing existing environment.
)
echo.

REM --- 3. Activate venv ---
echo [2/4] Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo.
  echo [ERROR] Failed to activate virtual environment ^(.venv\Scripts\activate.bat^).
  echo The venv may be corrupted - try deleting the .venv folder and running again.
  echo.
  pause
  exit /b 1
)
echo   Activated: %VIRTUAL_ENV%
echo.

REM --- 4. Install / update dependencies ---
echo [3/4] Installing dependencies from requirements.txt ...
echo   This may take 1-2 minutes on the first run - please wait.
echo.
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [WARN] pip upgrade had a warning, continuing anyway...
)
pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [ERROR] Failed to install dependencies from requirements.txt.
  echo Check your internet connection and look at the error above.
  echo You can also try manually:  pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)
echo.
echo   Dependencies ready.
REM optional httpx for internal tests - install if missing
pip show httpx >nul 2>&1
if errorlevel 1 pip install httpx
echo.

REM --- 5. Train models if missing ---
echo [4/6] Checking ThreatSense model artifacts ^(models\ ...^)...
if not exist "models\preprocessor.joblib" (
  echo   No trained models found - training ThreatSense Engine ^(30-60 seconds^)...
  echo   You will see lines like "Training XGBoost..." and "Torch CNN Epoch".
  echo.
  python -m cipherguard.ids.train
  if errorlevel 1 (
    echo.
    echo [ERROR] Model training failed. See the output above.
    echo Common causes: missing dependencies ^(check pip step^) or corrupted data/raw/ files.
    echo Try deleting models\ and reports\ and running again.
    echo.
    pause
    exit /b 1
  )
  echo   Training complete.
) else (
  echo   Models present - skipping training.
  echo   To force retrain, delete the models\ and reports\ folders and run again.
)
echo.

REM --- 6. Read ports from .env (defaults 8305 / 5305) ---
set BACKEND_PORT=8305
set FRONTEND_PORT=5305
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

REM --- 7. React frontend (needs Node.js 18+); falls back to the built-in dashboard if Node is missing ---
set HAVE_NODE=1
node --version >nul 2>&1
if errorlevel 1 set HAVE_NODE=0
if "%HAVE_NODE%"=="1" (
  echo [5/6] Preparing the React frontend in the frontend folder ...
  if not exist "frontend\node_modules" (
    echo   Installing frontend packages - first run only, needs internet...
    pushd frontend
    call npm install
    popd
  ) else (
    echo   Frontend packages present - skipping install.
  )
) else (
  echo [5/6] Node.js not found - skipping the React frontend.
  echo   Install Node.js 18+ from https://nodejs.org to get the new console. The built-in dashboard still works.
)
echo.

REM --- 8. Start backend (own window) bound to 127.0.0.1 ---
echo [6/6] Starting CipherGuard Shield API on http://localhost:%BACKEND_PORT% ...
echo   Binding to 127.0.0.1:%BACKEND_PORT% ^(avoids firewall prompts^).
start "CipherGuard API :%BACKEND_PORT%" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && python -m uvicorn cipherguard.api.main:app --host 127.0.0.1 --port %BACKEND_PORT% --log-level info"

if "%HAVE_NODE%"=="0" (
  echo   Open http://localhost:%BACKEND_PORT% for the built-in dashboard.
  start "" cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:%BACKEND_PORT%"
  echo.
  pause
  exit /b 0
)

echo   Starting the React console on http://localhost:%FRONTEND_PORT% - keep this window open. Ctrl+C stops it.
echo   ^(Close the "CipherGuard API" window as well to stop the backend.^)
echo.
start "" cmd /c "timeout /t 8 /nobreak >nul & start http://localhost:%FRONTEND_PORT%"
cd frontend
call npm run dev
set EXITCODE=%errorlevel%
cd ..

echo.
if %EXITCODE% neq 0 (
  echo [INFO] Frontend exited with code %EXITCODE%.
  echo Common reason: port %FRONTEND_PORT% or %BACKEND_PORT% already in use.
  echo To check:  netstat -ano ^| findstr :%FRONTEND_PORT%   then   taskkill /PID ^<pid^> /F
) else (
  echo [INFO] Frontend stopped.
)
pause
exit /b %EXITCODE%
