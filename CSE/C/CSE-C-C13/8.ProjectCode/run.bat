@echo off
setlocal EnableDelayedExpansion
REM ============================================================
REM  CipherVault - one-click local launcher (Windows)
REM  - Runs from its own folder no matter where launched from
REM  - Checks Python + Node, creates venv, installs deps
REM  - Backend (FastAPI)  : http://localhost:8413   (API + docs at /docs)
REM  - Frontend (Vite)    : http://localhost:5413   <- open this one
REM ============================================================
cd /d "%~dp0"

set BACKEND_PORT=8413
set FRONTEND_PORT=5413
set URL=http://localhost:%FRONTEND_PORT%/

echo ============================================================
echo  CipherVault - starting local secure file storage
echo ============================================================

REM ---- 1. Check Python ----
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] Python was not found on PATH.
  echo   Install Python 3.11 or newer from https://www.python.org/downloads/
  echo   and tick "Add python.exe to PATH", then run this file again.
  echo.
  pause
  exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Found Python %PYVER%

REM ---- 2. Check Node.js (needed for the frontend) ----
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] Node.js was not found on PATH.
  echo   Install the LTS version from https://nodejs.org/ then run this file again.
  echo.
  pause
  exit /b 1
)
for /f %%v in ('node --version') do set NODEVER=%%v
echo [OK] Found Node %NODEVER%

REM ---- 3. Create venv if missing ----
if not exist ".venv\Scripts\python.exe" (
  echo [*] Creating virtual environment ^(.venv^)...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create the virtual environment.
    pause
    exit /b 1
  )
) else (
  echo [OK] Virtual environment already exists.
)

REM ---- 4. Install backend dependencies ----
echo [*] Installing/updating Python dependencies ^(first run may take a few minutes^)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed ^(see pip error above^).
  pause
  exit /b 1
)
echo [OK] Python dependencies ready.

REM ---- 5. Install frontend dependencies ----
if not exist "frontend\node_modules" (
  echo [*] Installing frontend packages ^(first run only^)...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed. Check your internet connection.
    pause
    exit /b 1
  )
  popd
)
echo [OK] Frontend packages ready.

REM ---- 6. Ensure storage dir + env ----
if not exist "storage\encrypted" mkdir "storage\encrypted"
if not exist ".env" (
  if exist ".env.example" (
    copy ".env.example" ".env" >nul
    echo [*] Created .env from .env.example - edit it to set a strong JWT_SECRET.
  )
)

REM ---- 7. Start both servers ----
echo.
echo [*] Starting backend on http://localhost:%BACKEND_PORT% ...
start "CipherVault backend" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
echo [*] Starting frontend on %URL% ...
start "CipherVault frontend" cmd /k "cd /d frontend && npm run dev"

timeout /t 6 /nobreak >nul
start "" "%URL%"
echo.
echo  CipherVault is running:
echo    App (open this)   %URL%
echo    API docs          http://localhost:%BACKEND_PORT%/docs
echo.
echo  Two windows were opened (backend, frontend). Close them to stop the app.
echo  Tip: on the sign-in page, "Try the demo" creates fictional accounts with sample files.
pause
