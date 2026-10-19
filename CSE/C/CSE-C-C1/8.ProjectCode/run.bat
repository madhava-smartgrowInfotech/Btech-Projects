@echo off
setlocal EnableDelayedExpansion
REM AegisBallot run.bat - backend (FastAPI) + frontend (Vite/React)

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Ports come from .env (defaults match the batch assignment)
set "BACKEND_PORT=8401"
set "FRONTEND_PORT=5401"
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
    if "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
  )
)

echo ========================================================
echo  AegisBallot - Secure Voting Platform
echo  Backend  : http://localhost:%BACKEND_PORT%
echo  Frontend : http://localhost:%FRONTEND_PORT%
echo ========================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found on PATH. Install Python 3.11 or 3.12 from https://www.python.org/downloads/
  pause
  exit /b 1
)
where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js not found on PATH. Install Node 20 or newer from https://nodejs.org/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
  )
)

echo [INFO] Installing backend dependencies ...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed.
  pause
  exit /b 1
)

echo [INFO] Preparing database and demo data ...
".venv\Scripts\python.exe" -m app.seed

if not exist "frontend\node_modules" (
  echo [INFO] Installing frontend dependencies - first run only ...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
  popd
)

netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [ERROR] Port %BACKEND_PORT% is already in use. Close the other program or change BACKEND_PORT in .env.
  pause
  exit /b 1
)
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [ERROR] Port %FRONTEND_PORT% is already in use. Close the other program or change FRONTEND_PORT in .env.
  pause
  exit /b 1
)

echo [INFO] Starting backend on port %BACKEND_PORT% ...
start "AegisBallot API" /d "%SCRIPT_DIR%" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

echo [INFO] Starting frontend on port %FRONTEND_PORT% ...
start "AegisBallot Web" /d "%SCRIPT_DIR%frontend" cmd /k "npm run dev"

echo [INFO] Opening the browser in a few seconds ...
timeout /t 6 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%

echo.
echo AegisBallot is running in two console windows. Close them to stop it.
echo Demo logins: admin / Admin@123 , auditor / Audit@123 , voter1 / Voter@01pass
endlocal
