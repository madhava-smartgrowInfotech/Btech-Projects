@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title UPI Guardian - phone mode

if not exist "venv\Scripts\python.exe" (
    echo [x] Please run setup.bat first.
    pause
    exit /b 1
)
if not exist ".env" "venv\Scripts\python.exe" scripts\init_env.py

set "API_PORT=8204"
set "FRONTEND_PORT=5204"
for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="API_PORT" set "API_PORT=%%B"
    if /i "%%A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%B"
)

echo.
echo   UPI Guardian - phone mode
echo   Builds the installable app, starts it and opens a secure HTTPS link for your phone.
echo.

echo [..] Building the web app (about a minute)
pushd frontend
call npm run build
if errorlevel 1 (
    popd
    echo [x] The web app build failed - see the messages above.
    pause
    exit /b 1
)
popd

start "UPI Guardian API (%API_PORT%)" cmd /k ""%~dp0venv\Scripts\python.exe" "%~dp0backend\run_api.py""
"venv\Scripts\python.exe" scripts\wait_for.py http://127.0.0.1:%API_PORT%/api/health 90

start "UPI Guardian Web (%FRONTEND_PORT%)" cmd /k "cd /d "%~dp0frontend" && npm run preview"
"venv\Scripts\python.exe" scripts\wait_for.py http://localhost:%FRONTEND_PORT%/ 60

echo [..] Opening the secure tunnel (Cloudflare quick tunnel, no account needed)
"venv\Scripts\python.exe" scripts\phone_link.py
endlocal
