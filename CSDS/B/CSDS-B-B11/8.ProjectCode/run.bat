@echo off
setlocal
cd /d "%~dp0"
if not exist venv (
  echo Please run setup.bat first.
  pause & exit /b 1
)
if not exist frontend\node_modules (
  echo Please run setup.bat first.
  pause & exit /b 1
)

set "BACKEND_PORT=8211"
set "FRONTEND_PORT=5211"
if exist .env (
  for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
    if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
  )
)

echo Starting NutriSense API on port %BACKEND_PORT% ...
start "NutriSense API" cmd /k "cd /d "%~dp0backend" && "%~dp0venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
echo Starting NutriSense web app on port %FRONTEND_PORT% ...
start "NutriSense Web" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 7 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo NutriSense is running. Close the two server windows to stop it.
echo Sample login: demo@nutrisense.app / Demo@1234
