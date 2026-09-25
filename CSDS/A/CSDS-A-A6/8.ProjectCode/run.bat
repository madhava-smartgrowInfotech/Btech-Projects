@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
    echo .env not found - run setup.bat first.
    exit /b 1
)
if not exist "venv\Scripts\python.exe" (
    echo Python venv not found - run setup.bat first.
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo Frontend dependencies not installed - run setup.bat first.
    exit /b 1
)

echo Starting ClauseGuard backend on port 8106...
start "ClauseGuard Backend" cmd /k ""%~dp0venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8106 --app-dir "%~dp0backend""

echo Starting ClauseGuard frontend on port 5106...
start "ClauseGuard Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 5 /nobreak >nul
start "" "http://localhost:5106"

echo.
echo ClauseGuard is starting in two new windows (backend + frontend).
echo Close those windows to stop the servers.
endlocal
