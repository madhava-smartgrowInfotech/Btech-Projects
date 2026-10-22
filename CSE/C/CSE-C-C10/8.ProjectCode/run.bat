@echo off
REM VenturePulse launcher - FastAPI backend (8410) + React frontend (5410). Keeps the window open on errors.
cd /d "%~dp0"
echo ============================================
echo  VenturePulse - starting local application
echo ============================================

set BACKEND_PORT=8410
set FRONTEND_PORT=5410
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found on PATH.
  echo Please install Python 3.10+ from https://www.python.org/downloads/
  echo During installation, enable "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found on PATH.
  echo Please install Node.js 18+ from https://nodejs.org/ and run this file again.
  echo.
  pause
  exit /b 1
)

echo [1/5] Python found:
python --version

REM A .venv copied from another PC points at a Python that does not exist here - rebuild it.
if exist ".venv" (
  ".venv\Scripts\python.exe" --version >nul 2>nul
  if errorlevel 1 (
    echo [2/5] The existing .venv is broken, rebuilding it...
    rmdir /s /q ".venv"
  )
)
if not exist ".venv" (
  echo [2/5] Creating virtual environment .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Virtual environment creation failed. See the error above.
    pause
    exit /b 1
  )
) else (
  echo [2/5] Virtual environment already exists, reusing it.
)

echo [3/5] Installing Python dependencies from requirements.txt (first run may take several minutes)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo [WARNING] pip upgrade failed, continuing...
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed. See the pip error above.
  echo Check your internet connection and retry.
  pause
  exit /b 1
)

echo [4/5] Installing frontend packages (first run only)...
if not exist "frontend\node_modules" (
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed. See the error above.
    pause
    exit /b 1
  )
  popd
) else (
  echo Frontend packages already installed.
)

echo [5/5] Starting VenturePulse...
echo   Backend  : http://localhost:%BACKEND_PORT%   (the original pages are still at /dashboard)
echo   Frontend : http://localhost:%FRONTEND_PORT%
echo The first start may train models (a few minutes). Later starts are fast.
echo Demo sign-in: demo@venturepulse.com / Demo@1234
echo Keep these windows open. Press Ctrl+C in each to stop.
start "VenturePulse backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
timeout /t 4 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
cd frontend
call npm run dev
echo.
echo Frontend stopped.
pause
