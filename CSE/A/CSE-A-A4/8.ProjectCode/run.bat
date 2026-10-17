@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo  SecurePay AI - Credit Card Fraud Detection
echo  Backend (Flask) + React frontend
echo ============================================================

set BACKEND_PORT=8304
set FRONTEND_PORT=5304
if exist .env (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

echo Installing Python dependencies...
pip install -r requirements.txt --quiet

if not exist frontend\node_modules (
  echo Installing frontend packages...
  pushd frontend
  call npm install
  popd
)

echo Starting backend on http://127.0.0.1:%BACKEND_PORT% ...
start "SecurePay backend" cmd /k "set BACKEND_PORT=%BACKEND_PORT%&& python backend\app.py"

echo Starting frontend on http://127.0.0.1:%FRONTEND_PORT% ...
start "SecurePay frontend" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1"

timeout /t 6 /nobreak >nul
start http://127.0.0.1:%FRONTEND_PORT%
echo.
echo The old Flask page is still available at http://127.0.0.1:%BACKEND_PORT%/
endlocal
