@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PolicyLens - launcher

if not exist "venv\Scripts\python.exe" (
  echo PolicyLens is not set up yet. Run setup.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Frontend packages are missing. Run setup.bat first.
  pause
  exit /b 1
)
if not exist ".env" (
  echo .env is missing. Run setup.bat first.
  pause
  exit /b 1
)

rem Ports are fixed for PolicyLens; read overrides from .env if present.
set "BACKEND_PORT=8101"
set "FRONTEND_PORT=5101"
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
  if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
)

netstat -ano | findstr /r /c:":%BACKEND_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  echo [X] Port %BACKEND_PORT% is already in use. PolicyLens may already be running - run stop.bat, or close the other program.
  pause
  exit /b 1
)
netstat -ano | findstr /r /c:":%FRONTEND_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  echo [X] Port %FRONTEND_PORT% is already in use. PolicyLens may already be running - run stop.bat, or close the other program.
  pause
  exit /b 1
)

echo Starting the PolicyLens API on port %BACKEND_PORT%...
start "PolicyLens API (port %BACKEND_PORT%)" /D "%~dp0backend" cmd /k ..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%

"venv\Scripts\python.exe" scripts\wait_for.py http://127.0.0.1:%BACKEND_PORT%/api/health 240
if errorlevel 1 (
  pause
  exit /b 1
)

echo Starting the PolicyLens web app on port %FRONTEND_PORT%...
start "PolicyLens Web (port %FRONTEND_PORT%)" /D "%~dp0frontend" cmd /k npm run dev

"venv\Scripts\python.exe" scripts\wait_for.py http://127.0.0.1:%FRONTEND_PORT%/ 120
start "" http://localhost:%FRONTEND_PORT%

echo.
echo ==========================================================
echo   PolicyLens is running:  http://localhost:%FRONTEND_PORT%
echo   API docs:               http://localhost:%BACKEND_PORT%/docs
echo   Demo login:             demo@policylens.app / Demo@12345
echo   To stop: close the two PolicyLens windows or run stop.bat
echo ==========================================================
exit /b 0
