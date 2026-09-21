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
echo [1/4] Checking Python virtual environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
  echo   .venv not found - creating it now (this may take a moment)...
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
  echo [ERROR] Failed to activate virtual environment (.venv\Scripts\activate.bat).
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
pip install --upgrade pip
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
echo [4/5] Checking ThreatSense model artifacts (models\ ...)...
if not exist "models\preprocessor.joblib" (
  echo   No trained models found - training ThreatSense Engine (30-60 seconds)...
  echo   You will see lines like "Training XGBoost..." and "Torch CNN Epoch".
  echo.
  python -m cipherguard.ids.train
  if errorlevel 1 (
    echo.
    echo [ERROR] Model training failed. See the output above.
    echo Common causes: missing dependencies (check pip step) or corrupted data/raw/ files.
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

REM --- 6. Start backend server bound to 127.0.0.1 ---
echo [5/5] Starting CipherGuard Shield on http://localhost:8000 ...
echo   Binding to 127.0.0.1:8000 (avoids firewall prompts).
echo   The command window must stay open while the server is running - this is expected.
echo   Press Ctrl+C or close this window to stop the server.
echo.

REM Open browser shortly after server is up - poll in background so user does not have to type URL.
REM We wait ~4 seconds then try to open; if port not yet ready, user can also click manually.
start "" cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8000 & echo [run.bat] Browser opened at http://localhost:8000 (if it did not open, type http://localhost:8000 manually)"

REM Run server in FOREGROUND so logs are visible and window stays open.
REM IMPORTANT: host is 127.0.0.1, never 0.0.0.0, to avoid firewall prompts and ensure localhost resolution.
python -m uvicorn cipherguard.api.main:app --host 127.0.0.1 --port 8000 --log-level info
set EXITCODE=%errorlevel%

echo.
if %EXITCODE% neq 0 (
  echo [INFO] Server exited with code %EXITCODE%.
  echo Common reason: "port already in use" - close any program using port 8000 or restart your PC, then try again.
  echo To check:  netstat -ano ^| findstr :8000   then   taskkill /PID ^<pid^> /F
) else (
  echo [INFO] Server stopped.
)
echo If the browser did not open automatically, open it manually and go to:  http://localhost:8000
echo.
pause
exit /b %EXITCODE%
