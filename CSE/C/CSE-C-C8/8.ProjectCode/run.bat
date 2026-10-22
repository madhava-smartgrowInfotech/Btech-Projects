@echo off
REM PeerScope launcher - double-click this file.
REM Starts the API on 8408 and the web app on 5408 (ports come from .env).
cd /d "%~dp0"
title PeerScope - starting...

set "API_PORT=8408"
set "WEB_PORT=5408"
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="PEERSCOPE_PORT" set "API_PORT=%%B"
    if /i "%%A"=="FRONTEND_PORT" set "WEB_PORT=%%B"
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [PeerScope] Python was not found on PATH.
  echo Please install Python 3.11 or 3.12 from https://www.python.org/downloads/
  echo During setup, tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo.
  echo [PeerScope] Node.js was not found on PATH.
  echo Please install Node.js 18 or newer from https://nodejs.org/
  echo.
  pause
  exit /b 1
)

REM A .venv copied from another machine points at a missing Python - detect and rebuild it.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
  if errorlevel 1 (
    echo [PeerScope] The existing virtual environment is broken. Rebuilding it...
    rmdir /s /q ".venv"
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [PeerScope] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo [PeerScope] Virtual environment creation FAILED. See the error above.
    echo.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
echo [PeerScope] Installing Python dependencies from requirements.txt ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [PeerScope] Dependency installation FAILED. See the pip error above.
  echo Check your internet connection, then re-run run.bat.
  echo.
  pause
  exit /b 1
)

if not exist "models\decision_model.joblib" (
  echo [PeerScope] First run: preparing dataset and training decision model...
  python scripts\prepare_dataset.py
  python scripts\train_model.py
  if errorlevel 1 (
    echo [PeerScope] Model training reported an error - see above. The app will still start.
  )
)
if not exist "data\demo\demo_paper.pdf" (
  python scripts\make_demo_pdf.py
)

if not exist "frontend\node_modules" (
  echo [PeerScope] Installing web app dependencies ...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo.
    echo [PeerScope] npm install FAILED. See the error above.
    echo.
    pause
    exit /b 1
  )
  popd
)

echo [PeerScope] Starting API on 127.0.0.1:%API_PORT% ...
start "PeerScope API" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %API_PORT%"

echo [PeerScope] Starting web app on 127.0.0.1:%WEB_PORT% ...
start "PeerScope Web" cmd /k "cd /d frontend && npm run dev"

timeout /t 6 /nobreak >nul
start "" "http://localhost:%WEB_PORT%"
echo.
echo [PeerScope] Running. Web app: http://localhost:%WEB_PORT%   API: http://localhost:%API_PORT%/docs
echo Close the two PeerScope windows to stop it.
pause
