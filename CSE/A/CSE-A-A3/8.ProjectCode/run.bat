@echo off
setlocal
cd /d "%~dp0"

rem Ports come from .env (ports only); defaults match .env.example
set BACKEND_PORT=8303
set FRONTEND_PORT=5303
if exist .env (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

if not exist venv\Scripts\python.exe (
  echo Creating Python environment...
  python -m venv venv || goto :fail
  venv\Scripts\python -m pip install -q -r requirements.txt || goto :fail
)
if not exist frontend\node_modules (
  echo Installing frontend packages...
  pushd frontend
  call npm install || goto :fail
  popd
)

echo Starting API on http://127.0.0.1:%BACKEND_PORT% ...
start "Health API" cmd /k "venv\Scripts\python -m uvicorn backend.main:api --host 127.0.0.1 --port %BACKEND_PORT%"
echo Starting app on http://127.0.0.1:%FRONTEND_PORT% ...
start "Health Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 6 >nul
start "" http://127.0.0.1:%FRONTEND_PORT%
exit /b 0

:fail
echo Setup failed - see the messages above.
exit /b 1
