@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title UPI Guardian - setup

echo.
echo   UPI Guardian - one-time setup
echo   ==============================
echo.

rem ---- 1. Python 3.11 --------------------------------------------------------
set "PY="
py -3.11 -c "import sys" >nul 2>nul && set "PY=py -3.11"
if not defined PY (
    python -c "import sys; sys.exit(0 if sys.version_info[:2]==(3,11) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [x] Python 3.11 was not found.
    echo     Install it from https://www.python.org/downloads/release/python-3119/
    echo     and tick "Add python.exe to PATH" during installation. Then run setup.bat again.
    goto :fail
)
echo [ok] Python 3.11 found

rem ---- 2. Node.js ------------------------------------------------------------
where node >nul 2>nul
if errorlevel 1 (
    echo [x] Node.js was not found. Install the LTS version from https://nodejs.org and run setup.bat again.
    goto :fail
)
for /f "delims=" %%v in ('node --version') do echo [ok] Node.js %%v found

rem ---- 3. Python virtual environment + packages -----------------------------
if not exist "venv\Scripts\python.exe" (
    echo [..] Creating Python virtual environment in venv\
    %PY% -m venv venv
    if errorlevel 1 goto :fail
)
echo [..] Installing backend and AI packages (first run takes a few minutes)
"venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"venv\Scripts\python.exe" -m pip install -r backend\requirements.txt --quiet
if errorlevel 1 goto :fail
echo [ok] Python packages installed

if /i "%~1"=="train" (
    echo [..] Installing extra packages for retraining the models
    "venv\Scripts\python.exe" -m pip install -r ml\requirements-train.txt --extra-index-url https://download.pytorch.org/whl/cpu --quiet
    if errorlevel 1 goto :fail
    echo [ok] Training packages installed
)

rem ---- 4. Configuration -----------------------------------------------------
"venv\Scripts\python.exe" scripts\init_env.py
if errorlevel 1 goto :fail

rem ---- 5. Web app packages --------------------------------------------------
echo [..] Installing web app packages
pushd frontend
call npm install --no-audit --no-fund --loglevel=error
if errorlevel 1 (
    popd
    goto :fail
)
popd
echo [ok] Web app packages installed

rem ---- 6. Models --------------------------------------------------------------
if not exist "models\risk_model.joblib" (
    echo [..] Trained models not found - training them now (about 10 minutes on a normal PC^)
    "venv\Scripts\python.exe" ml\train_all.py
    if errorlevel 1 goto :fail
)
echo [ok] Trained models present

rem ---- 7. Voice phrases (needs internet, optional) ---------------------------
echo [..] Preparing spoken warnings in English, Hindi and Telugu
"venv\Scripts\python.exe" scripts\build_voice_cache.py
if errorlevel 1 echo [!] Could not prepare voice phrases now - they will be created on first use when online.

echo.
echo   Setup complete.  Start UPI Guardian with:  run.bat
echo   (for a phone: run_phone.bat)
echo.
endlocal
exit /b 0

:fail
echo.
echo [x] Setup stopped because of the error above. See docs\10_TROUBLESHOOTING.md
echo.
endlocal
exit /b 1
