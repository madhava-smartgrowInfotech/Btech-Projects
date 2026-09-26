@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SeatWise

if not exist "venv\Scripts\python.exe" goto :needsetup
if not exist "frontend\node_modules" goto :needsetup
if not exist ".env" goto :needsetup

rem ---- Read the ports from .env ---------------------------------------------
set "API_HOST=127.0.0.1"
set "API_PORT=8113"
set "WEB_PORT=5113"
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="API_HOST" set "API_HOST=%%b"
  if /i "%%a"=="API_PORT" set "API_PORT=%%b"
  if /i "%%a"=="WEB_PORT" set "WEB_PORT=%%b"
)

rem ---- Refuse to start on a port another program is using --------------------
netstat -ano | findstr /r /c:":%API_PORT% *[^ ]* *LISTENING" >nul
if not errorlevel 1 (
  echo Port %API_PORT% is already in use. SeatWise may already be running - run stop.bat first.
  goto :fail
)
netstat -ano | findstr /r /c:":%WEB_PORT% *[^ ]* *LISTENING" >nul
if not errorlevel 1 (
  echo Port %WEB_PORT% is already in use. SeatWise may already be running - run stop.bat first.
  goto :fail
)

echo Starting the SeatWise API on port %API_PORT% ...
start "SeatWise API - port %API_PORT%" /d "%~dp0backend" cmd /k ""%~dp0venv\Scripts\python.exe" -m uvicorn app.main:app --host %API_HOST% --port %API_PORT%"

echo Starting the SeatWise web app on port %WEB_PORT% ...
start "SeatWise web - port %WEB_PORT%" /d "%~dp0frontend" cmd /k "npm run dev"

echo Waiting for SeatWise to be ready ...
powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 90;$i++){ try { $a=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:%API_PORT%/api/health; $w=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:%WEB_PORT%/; if($a.StatusCode -eq 200 -and $w.StatusCode -eq 200){$ok=$true; break} } catch {}; Start-Sleep -Milliseconds 700 }; if(-not $ok){ exit 1 }"
if errorlevel 1 (
  echo SeatWise did not start in time. Check the two SeatWise windows for errors.
  goto :fail
)

start "" "http://localhost:%WEB_PORT%/"
echo.
echo  =====================================================
echo   SeatWise is running:  http://localhost:%WEB_PORT%
echo   API documentation:    http://localhost:%API_PORT%/docs
echo.
echo   Demo sign-in: admin@seatwise.local / SeatWise@2026
echo   To stop SeatWise, run stop.bat or close its two windows.
echo  =====================================================
echo.
pause
exit /b 0

:needsetup
echo SeatWise is not set up yet. Run setup.bat first.
:fail
pause
exit /b 1
