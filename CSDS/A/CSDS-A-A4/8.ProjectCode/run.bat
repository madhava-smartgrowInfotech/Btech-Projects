@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title HubOptima - launcher

rem Ports (overridable in .env)
set "BACKEND_PORT=8104"
set "FRONTEND_PORT=5104"
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
    if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
  )
)

set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=%~dp0venv\Scripts\python.exe"

"%PY%" -c "import fastapi, uvicorn, flask, sklearn, pulp" 2>nul
if errorlevel 1 (
  echo Installing Python packages...
  "%PY%" -m pip install -r backend\requirements.txt
)
if not exist "frontend\node_modules" (
  echo Installing frontend packages...
  pushd frontend
  call npm install
  popd
)

netstat -ano | findstr /r /c:":%BACKEND_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  echo [X] Port %BACKEND_PORT% is already in use - HubOptima may already be running.
  pause
  exit /b 1
)
netstat -ano | findstr /r /c:":%FRONTEND_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  echo [X] Port %FRONTEND_PORT% is already in use - HubOptima may already be running.
  pause
  exit /b 1
)

echo Starting the HubOptima API on port %BACKEND_PORT%...
start "HubOptima API (port %BACKEND_PORT%)" /D "%~dp0" cmd /k "%PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%
"%PY%" scripts\wait_for.py http://127.0.0.1:%BACKEND_PORT%/api/health 180
if errorlevel 1 (
  pause
  exit /b 1
)

echo Starting the HubOptima web app on port %FRONTEND_PORT%...
start "HubOptima Web (port %FRONTEND_PORT%)" /D "%~dp0frontend" cmd /k npm run dev
"%PY%" scripts\wait_for.py http://localhost:%FRONTEND_PORT%/ 120
start "" http://localhost:%FRONTEND_PORT%

echo.
echo ==========================================================
echo   HubOptima is running:  http://localhost:%FRONTEND_PORT%
echo   API docs:              http://localhost:%BACKEND_PORT%/docs
echo   Classic Flask UI:      python run.py serve  (port 5000)
echo   To stop: close the two HubOptima windows
echo ==========================================================
exit /b 0
