@echo off
setlocal
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first. & exit /b 1)
if not exist .env (echo .env is missing - run setup.bat first. & exit /b 1)

set BACKEND_PORT=8217
set FRONTEND_PORT=5217
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
  if "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
  if "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
)

echo Starting CallSense API on http://localhost:%BACKEND_PORT% ...
start "CallSense API" cmd /k "venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port %BACKEND_PORT%"
echo Starting CallSense web app on http://localhost:%FRONTEND_PORT% ...
start "CallSense Web" cmd /k "cd frontend && npm run dev"

timeout /t 6 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%
echo CallSense is running. Close the two console windows to stop it.
endlocal
