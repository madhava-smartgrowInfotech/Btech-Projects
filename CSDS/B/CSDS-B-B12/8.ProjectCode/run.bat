@echo off
setlocal
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first. & exit /b 1)
if not exist frontend\node_modules (echo Run setup.bat first. & exit /b 1)
set BACKEND_PORT=8212
set FRONTEND_PORT=5212
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
  if "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
  if "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
)
echo Starting PulmoVision API on port %BACKEND_PORT% ...
start "PulmoVision API" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
echo Starting PulmoVision web app on port %FRONTEND_PORT% ...
start "PulmoVision Web" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 8 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%
echo.
echo PulmoVision is running:  http://localhost:%FRONTEND_PORT%
echo Demo logins: doctor@pulmovision.app / Doctor@123   and   tech@pulmovision.app / Tech@123
echo Close the two server windows to stop.
endlocal
