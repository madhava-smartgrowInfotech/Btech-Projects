@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title UPI Guardian

if not exist "venv\Scripts\python.exe" (
    echo [x] Please run setup.bat first.
    pause
    exit /b 1
)
if not exist "frontend\node_modules" (
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
echo   Starting UPI Guardian
echo     API      http://127.0.0.1:%API_PORT%   (docs: /docs)
echo     Web app  http://localhost:%FRONTEND_PORT%
echo.

start "UPI Guardian API (%API_PORT%)" cmd /k ""%~dp0venv\Scripts\python.exe" "%~dp0backend\run_api.py""
"venv\Scripts\python.exe" scripts\wait_for.py http://127.0.0.1:%API_PORT%/api/health 90

start "UPI Guardian Web (%FRONTEND_PORT%)" cmd /k "cd /d "%~dp0frontend" && npm run dev"
"venv\Scripts\python.exe" scripts\wait_for.py http://localhost:%FRONTEND_PORT%/ 90

start "" "http://localhost:%FRONTEND_PORT%/"
echo   UPI Guardian is running. Close the two server windows (or run stop.bat) to stop it.
echo.
endlocal
