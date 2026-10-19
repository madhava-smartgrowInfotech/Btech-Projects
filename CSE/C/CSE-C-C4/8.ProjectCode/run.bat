@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM QuantPulse - one-click Windows launcher
REM   API      http://localhost:8404   (FastAPI)
REM   Website  http://localhost:5404   (React, needs Node.js)
REM Ports and options are read from the .env file next to this script.
REM ============================================================

cd /d "%~dp0"
set "ROOT=%CD%"
set "BACKEND_PORT=8404"
set "FRONTEND_PORT=5404"

if exist "%ROOT%\.env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%ROOT%\.env") do (
    if not "%%B"=="" set "%%A=%%B"
  )
)
set "QUANTPULSE_PORT=%BACKEND_PORT%"

echo.
echo ============================================================
echo   QuantPulse - AI Stock Trend Forecasting
echo   Project folder: %ROOT%
echo   API port %BACKEND_PORT%, website port %FRONTEND_PORT%
echo ============================================================
echo.

REM ---- 1. Python ------------------------------------------------
echo [1/6] Checking Python...
where python >nul 2>&1
if errorlevel 1 goto :nopython
python --version
goto :venv

:nopython
echo.
echo [ERROR] Python was not found on PATH.
echo Install Python 3.11 from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
echo Then close this window and run run.bat again.
echo.
pause
exit /b 1

REM ---- 2. Virtual environment ----------------------------------
:venv
echo.
echo [2/6] Checking virtual environment...
set "PY=%ROOT%\.venv\Scripts\python.exe"
if not exist "%PY%" goto :makevenv
"%PY%" --version >nul 2>&1
if not errorlevel 1 goto :venvok
echo [..] The existing .venv is broken, so it will be recreated.
rmdir /s /q "%ROOT%\.venv"

:makevenv
echo [..] Creating virtual environment, this happens once...
python -m venv "%ROOT%\.venv"
if errorlevel 1 goto :venvfail
if not exist "%PY%" goto :venvfail

:venvok
echo [OK] Virtual environment ready.
goto :deps

:venvfail
echo.
echo [ERROR] Could not create the virtual environment. The Python error is shown above.
echo.
pause
exit /b 1

REM ---- 3. Python dependencies ----------------------------------
:deps
echo.
echo [3/6] Checking Python dependencies...
"%PY%" -c "import fastapi, uvicorn, pandas, numpy, tensorflow, transformers" >nul 2>&1
if not errorlevel 1 (
  echo [OK] Dependencies already installed.
  goto :train
)
echo [..] Installing dependencies. The first run downloads TensorFlow and PyTorch and takes several minutes.
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r "%ROOT%\backend\requirements.txt"
if errorlevel 1 (
  echo.
  echo [ERROR] Dependency installation failed. The pip error is shown above.
  echo Check your internet connection and run run.bat again.
  echo.
  pause
  exit /b 1
)
echo [OK] Dependencies installed.

REM ---- 4. Trained models ---------------------------------------
:train
echo.
echo [4/6] Checking trained models...
if exist "%ROOT%\artifacts\metrics.json" (
  echo [OK] Trained model artifacts found, training skipped.
  goto :front
)
echo [..] No trained models found, training now. This takes about 5 to 10 minutes on a CPU.
"%PY%" -m backend.train
if errorlevel 1 (
  echo.
  echo [ERROR] Model training failed. The error is shown above.
  echo.
  pause
  exit /b 1
)
echo [OK] Training finished.

REM ---- 5. Website dependencies ---------------------------------
:front
echo.
echo [5/6] Checking the website...
set "HAVE_NODE=0"
where node >nul 2>&1
if not errorlevel 1 set "HAVE_NODE=1"
if "%HAVE_NODE%"=="0" (
  echo [INFO] Node.js was not found, so the prebuilt website will be served by the API on port %BACKEND_PORT%.
  goto :start
)
if not exist "%ROOT%\frontend\node_modules" (
  echo [..] Installing website packages, this happens once...
  pushd "%ROOT%\frontend"
  call npm install
  set "NPM_EXIT=!ERRORLEVEL!"
  popd
  if not "!NPM_EXIT!"=="0" (
    echo.
    echo [ERROR] npm install failed. The error is shown above.
    echo.
    pause
    exit /b 1
  )
)
echo [OK] Website ready.

REM ---- 6. Start everything -------------------------------------
:start
echo.
echo [6/6] Starting QuantPulse...
start "QuantPulse API" /D "%ROOT%" cmd /k ""%PY%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

echo [..] Waiting for the API to answer...
set /a TRIES=0
:wait
set /a TRIES+=1
curl.exe -s -f "http://127.0.0.1:%BACKEND_PORT%/api/health" >nul 2>&1
if not errorlevel 1 goto :up
if %TRIES% GEQ 90 goto :slow
timeout /t 2 /nobreak >nul
goto :wait

:slow
echo [WARN] The API is slow to start. Check the "QuantPulse API" window for errors.
goto :open

:up
echo [OK] API is up.

:open
set "URL=http://localhost:%BACKEND_PORT%"
if "%HAVE_NODE%"=="1" (
  start "QuantPulse Website" /D "%ROOT%\frontend" cmd /k "npm run dev"
  set "URL=http://localhost:%FRONTEND_PORT%"
  timeout /t 6 /nobreak >nul
)
echo.
echo ============================================================
echo   QuantPulse is running: %URL%
echo   Close the "QuantPulse API" and "QuantPulse Website" windows to stop it.
echo ============================================================
start "" "%URL%"
echo.
pause
exit /b 0
