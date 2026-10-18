@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PneumoDetect launcher

rem ---------------------------------------------------------------
rem  PneumoDetect - one-click start
rem    run.bat          FastAPI backend + React frontend (new UI)
rem    run.bat flask    the original Flask app on port 5000
rem ---------------------------------------------------------------

set "BACKEND_PORT=8312"
set "FRONTEND_PORT=5312"
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set "BACKEND_PORT=%%B"
    if /i "%%A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%B"
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or 3.11 was not found on PATH. Install it from python.org and tick "Add to PATH".
  goto :fail
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating virtual environment .venv ...
  python -m venv .venv
  if errorlevel 1 goto :fail
)

if not exist ".venv\deps.ok" (
  echo [2/4] Installing Python packages. The first run downloads TensorFlow and takes a while ...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-api.txt
  if errorlevel 1 goto :fail
  echo ok> ".venv\deps.ok"
) else (
  echo [2/4] Python packages already installed.
)

if /i "%~1"=="flask" goto :flask

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 18 or newer was not found on PATH. Install it from nodejs.org.
  goto :fail
)

if not exist "frontend\node_modules" (
  echo [3/4] Installing frontend packages ...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    goto :fail
  )
  popd
) else (
  echo [3/4] Frontend packages already installed.
)

echo [4/4] Starting API on port %BACKEND_PORT% and UI on port %FRONTEND_PORT% ...
start "PneumoDetect API" /D "%~dp0" cmd /k .venv\Scripts\python.exe -m uvicorn backend.main:api --port %BACKEND_PORT%
start "PneumoDetect UI" /D "%~dp0frontend" cmd /k npm run dev
timeout /t 8 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo   UI   : http://localhost:%FRONTEND_PORT%
echo   API  : http://localhost:%BACKEND_PORT%/docs
echo   Demo login: demo@pneumodetect.ai / Pneumo@123
echo   Close the two new windows, or run stop.bat, to stop everything.
goto :eof

:flask
echo Starting the original Flask app on http://localhost:5000 ...
".venv\Scripts\python.exe" app.py
goto :eof

:fail
echo.
echo Setup failed. Fix the message above and run run.bat again.
pause
exit /b 1
