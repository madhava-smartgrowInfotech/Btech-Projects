@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
    echo Run setup.bat first.
    exit /b 1
)
if not exist .env (
    echo .env is missing - run setup.bat first.
    exit /b 1
)

set "BACKEND_PORT=8201"
set "FRONTEND_PORT=5201"
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
    if "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
)

echo Starting CivicPulse API on port %BACKEND_PORT% ...
start "CivicPulse API" /D "%~dp0backend" cmd /k "..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
echo Starting CivicPulse web app on port %FRONTEND_PORT% ...
start "CivicPulse Web" /D "%~dp0frontend" cmd /k "npm run dev"

echo Waiting for the API (the first start builds sample data, ~30 s)...
powershell -NoProfile -Command "for($i=0;$i -lt 180;$i++){try{Invoke-WebRequest -UseBasicParsing http://127.0.0.1:%BACKEND_PORT%/api/health -TimeoutSec 2 | Out-Null; exit 0}catch{Start-Sleep 1}}; exit 1"
if errorlevel 1 echo The API did not answer yet - check the "CivicPulse API" window.
start "" http://localhost:%FRONTEND_PORT%
echo CivicPulse is running. Close the two console windows to stop it.
