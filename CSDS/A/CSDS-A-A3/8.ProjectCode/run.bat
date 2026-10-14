@echo off
rem PhishGuard - start the API (port 8103) and the React frontend (port 5103) together.
setlocal
cd /d "%~dp0"

if not exist "models\best_model.joblib" (
  echo No trained model found - training once ^(about 30 s^)...
  python run.py train || goto :error
)

if not exist "frontend\node_modules" (
  echo Installing frontend dependencies...
  pushd frontend
  call npm install || goto :error
  popd
)

start "PhishGuard API :8103" cmd /k python backend\server.py
start "PhishGuard UI :5103" cmd /k "cd /d frontend && npm run dev"

echo.
echo   API      http://127.0.0.1:8103/api/health
echo   Frontend http://127.0.0.1:5103
echo.
timeout /t 4 /nobreak >nul
start "" http://127.0.0.1:5103
exit /b 0

:error
echo Startup failed - see the messages above.
exit /b 1
