@echo off
setlocal EnableExtensions EnableDelayedExpansion

title ParkSure - Launcher

cd /d "%~dp0"

set BACKEND_PORT=8403
set FRONTEND_PORT=5403

echo.
echo ============================================================
echo                 PARKSURE PROJECT LAUNCHER
echo ============================================================
echo.
echo Project folder: %CD%
echo Backend  : http://127.0.0.1:%BACKEND_PORT%
echo Frontend : http://127.0.0.1:%FRONTEND_PORT%
echo.

REM ============================================================
REM 1. CHECK PYTHON AND NODE
REM ============================================================

echo [1/7] Checking Python and Node.js...
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python 3.11 or newer from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)
python --version

where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found.
    echo Install Node.js 20 or newer from https://nodejs.org/ then run this file again.
    echo.
    pause
    exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm was not found. Reinstall Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
node --version
echo.

REM ============================================================
REM 2. CHECK PROJECT FILES
REM ============================================================

echo [2/7] Checking project files...

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt was not found in %CD%
    pause
    exit /b 1
)
if not exist "app\main.py" (
    echo [ERROR] app\main.py was not found. Run this file from the ParkSure project folder.
    pause
    exit /b 1
)
if not exist "frontend\package.json" (
    echo [ERROR] frontend\package.json was not found.
    pause
    exit /b 1
)
echo Project files found.
echo.

REM ============================================================
REM 3. VIRTUAL ENVIRONMENT
REM ============================================================

echo [3/7] Checking virtual environment...

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
)
".venv\Scripts\python.exe" --version
if errorlevel 1 (
    echo [ERROR] The virtual environment Python is not working.
    echo Delete the .venv folder and run this file again.
    pause
    exit /b 1
)
echo.

REM ============================================================
REM 4. PYTHON DEPENDENCIES
REM ============================================================

echo [4/7] Installing Python dependencies. This may take several minutes...
echo.

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Python dependency installation failed. The error is shown above.
    echo Delete the .venv folder and run this file again.
    pause
    exit /b 1
)
echo.

REM ============================================================
REM 5. FRONTEND DEPENDENCIES
REM ============================================================

echo [5/7] Installing frontend dependencies...
echo.

if not exist "frontend\node_modules" (
    pushd frontend
    call npm install
    set NPM_RESULT=!errorlevel!
    popd
    if not "!NPM_RESULT!"=="0" (
        echo [ERROR] npm install failed. The error is shown above.
        pause
        exit /b 1
    )
) else (
    echo frontend\node_modules already present.
)
echo.

REM ============================================================
REM 6. START BACKEND AND FRONTEND
REM ============================================================

echo [6/7] Starting ParkSure...
echo.
echo Keep the two server windows open while you use ParkSure.
echo.

set PARKSURE_PORT=%BACKEND_PORT%
set PARKSURE_BASE_URL=http://127.0.0.1:%FRONTEND_PORT%
start "ParkSure Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "ParkSure Frontend" /D "%CD%\frontend" cmd /k "npm run dev"

REM ============================================================
REM 7. WAIT FOR BOTH SERVERS
REM ============================================================

echo [7/7] Waiting for the servers...

set READY=0
for /L %%i in (1,1,60) do (
    if "!READY!"=="0" (
        timeout /t 1 /nobreak >nul
        powershell -NoProfile -Command "try { $a=Invoke-WebRequest -Uri 'http://127.0.0.1:%BACKEND_PORT%/api/locations' -UseBasicParsing -TimeoutSec 1; $b=Invoke-WebRequest -Uri 'http://127.0.0.1:%FRONTEND_PORT%' -UseBasicParsing -TimeoutSec 1; if ($a.StatusCode -eq 200 -and $b.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
        if not errorlevel 1 set READY=1
        if "!READY!"=="0" echo Waiting... %%i/60
    )
)

if "!READY!"=="1" (
    echo.
    echo ============================================================
    echo             PARKSURE STARTED SUCCESSFULLY
    echo ============================================================
    echo.
    echo Open http://127.0.0.1:%FRONTEND_PORT%
    echo.
    echo Demo logins:
    echo   admin  - admin@parksure.app / admin123
    echo   driver - driver1@parksure.app / driver123
    echo.
    start "" "http://127.0.0.1:%FRONTEND_PORT%"
    echo Close the ParkSure Backend and ParkSure Frontend windows to stop.
    echo.
    pause
) else (
    echo.
    echo [ERROR] ParkSure did not start within 60 seconds.
    echo Check the ParkSure Backend and ParkSure Frontend windows for the error.
    echo.
    pause
)

endlocal
