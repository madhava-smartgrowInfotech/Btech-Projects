@echo off
rem Starts the SkyCipher backend and frontend in their own windows and opens the browser.
cd /d "%~dp0"
if not exist venv call setup.bat
if not exist frontend\node_modules call setup.bat

set BACKEND_PORT=8210
set FRONTEND_PORT=5210
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
  if "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
  if "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
)

start "SkyCipher API :%BACKEND_PORT%" cmd /k "cd /d "%~dp0backend" && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "SkyCipher Web :%FRONTEND_PORT%" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo Waiting for the servers to start...
timeout /t 8 /nobreak >nul
start "" http://localhost:%FRONTEND_PORT%
