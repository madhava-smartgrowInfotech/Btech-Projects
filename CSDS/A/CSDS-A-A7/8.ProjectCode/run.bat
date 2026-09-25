@echo off
setlocal
cd /d "%~dp0"

echo Starting SHEGUARD backend on port 8107...
start "SHEGUARD backend" cmd /k "cd /d "%~dp0" && venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8107 --reload"

timeout /t 3 /nobreak >nul

echo Starting SHEGUARD frontend on port 5107...
start "SHEGUARD frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 /nobreak >nul

start "" "http://localhost:5107"

echo.
echo Backend:  http://localhost:8107
echo Frontend: http://localhost:5107
echo Close the two opened terminal windows to stop SHEGUARD.
