@echo off
setlocal EnableExtensions

title FINJARVIS - Launcher
cd /d "%~dp0"

set BACKEND_PORT=8411
set FRONTEND_PORT=5411
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        if /i "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
        if /i "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
    )
)

echo.
echo ============================================================
echo        FINJARVIS - AI PERSONAL FINANCE MANAGER LAUNCHER
echo ============================================================
echo Backend  : http://127.0.0.1:%BACKEND_PORT%
echo Frontend : http://localhost:%FRONTEND_PORT%
echo.

echo [1/5] Checking Python and Node.js...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python 3.11 or newer from https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found. Install Node.js 20 or newer from https://nodejs.org/ and run this file again.
    pause
    exit /b 1
)
python --version
node --version

echo.
echo [2/5] Preparing the Python environment in .venv ...
rem A .venv copied from another computer points at a Python that is not here: rebuild it.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo       The existing .venv does not work on this PC. Rebuilding it.
        rmdir /s /q ".venv"
    )
)
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)
rem bcrypt 4.0.1 is required: passlib breaks with bcrypt 5 and rejects every password.
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, sklearn, pandas, multipart, passlib, reportlab, openpyxl, bcrypt; assert bcrypt.__version__ == '4.0.1'" >nul 2>&1
if errorlevel 1 (
    echo       Installing backend packages. The first run takes a few minutes.
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r backend\requirements.txt
    if errorlevel 1 (
        echo [ERROR] Installing the backend packages failed. Check your internet connection and run this file again.
        pause
        exit /b 1
    )
)

echo.
echo [3/5] Preparing the frontend...
if not exist "frontend\node_modules" (
    echo       Installing frontend packages. The first run takes a minute or two.
    pushd frontend
    call npm install --no-audit --no-fund
    if errorlevel 1 (
        popd
        echo [ERROR] npm install failed. Check your internet connection and run this file again.
        pause
        exit /b 1
    )
    popd
)

echo.
echo [4/5] Starting the backend on port %BACKEND_PORT% ...
start "FINJARVIS backend" /min cmd /c ""%~dp0.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

echo       Waiting for the server to start...
set /a TRIES=0
:waitloop
set /a TRIES+=1
curl -s -o nul http://127.0.0.1:%BACKEND_PORT%/api/health
if not errorlevel 1 goto backend_ready
if %TRIES% GEQ 90 (
    echo [ERROR] The backend did not start in time. Look at the "FINJARVIS backend" window for the reason.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto waitloop
:backend_ready
echo       Backend is ready.

echo.
echo [5/5] Starting the frontend on port %FRONTEND_PORT% ...
start "FINJARVIS frontend" /min cmd /c "cd /d "%~dp0frontend" && npm run dev"
timeout /t 4 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%

echo.
echo FINJARVIS is running. Two minimised windows hold the servers: close them to stop.
echo Demo login: username  demo   password  Demo@1234   (fictional data)
echo.
pause
endlocal
