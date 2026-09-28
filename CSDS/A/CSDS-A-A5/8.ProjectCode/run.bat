@echo off
REM Start the TaxSentinel backend (8105) and frontend (5105) and open the browser.
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo Run setup.bat first. & exit /b 1)
if not exist frontend\node_modules (echo Run setup.bat first. & exit /b 1)
if not exist .env copy .env.example .env >nul

set BACKEND_PORT=8105
set FRONTEND_PORT=5105
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
  if "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
  if "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
)

start "TaxSentinel API" cmd /k "venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "TaxSentinel Web" cmd /k "cd frontend && npm run dev"

echo Waiting for the API on port %BACKEND_PORT% ...
powershell -NoProfile -Command "$u='http://127.0.0.1:%BACKEND_PORT%/api/health'; for($i=0;$i -lt 90;$i++){ try { if((Invoke-RestMethod $u -TimeoutSec 2).pipeline_ready){ exit 0 } } catch {}; Start-Sleep 1 }; exit 0"
start "" http://localhost:%FRONTEND_PORT%
echo TaxSentinel is running: http://localhost:%FRONTEND_PORT%  (demo: demo@taxsentinel.app / Demo@1234)
echo Close the two server windows to stop it.
endlocal
