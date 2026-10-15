@echo off
setlocal
cd /d "%~dp0"

set BACKEND_PORT=8109
set FRONTEND_PORT=5109
if exist .env (
  for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b /c:"BACKEND_PORT=" /c:"FRONTEND_PORT=" .env`) do set %%a=%%b
)

echo Starting ForgetSafe API on http://127.0.0.1:%BACKEND_PORT% ...
start "ForgetSafe API" cmd /k python app.py --port %BACKEND_PORT%

if not exist frontend\node_modules (
  echo Installing frontend dependencies ...
  pushd frontend
  call npm install
  popd
)

echo Starting ForgetSafe UI on http://127.0.0.1:%FRONTEND_PORT% ...
start "ForgetSafe UI" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 4 /nobreak >nul
start "" http://127.0.0.1:%FRONTEND_PORT%
endlocal
