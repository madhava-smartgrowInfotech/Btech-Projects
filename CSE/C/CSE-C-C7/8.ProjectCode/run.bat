@echo off
setlocal
REM LearnPathIQ launcher - works from any directory
REM Starts the FastAPI backend and the React frontend. Ports come from .env.
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ============================================
echo  LearnPathIQ - starting local servers
echo ============================================

where python >nul 2>nul
if errorlevel 1 goto nopython

if not exist ".env" copy ".env.example" ".env" >nul
set "BACKEND_PORT=8407"
set "FRONTEND_PORT=5407"
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
  if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto venvfail
)

call ".venv\Scripts\activate.bat"
echo Installing Python dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto pipfail

if not exist "artifacts\metrics\model_metrics.json" (
  echo Training models first run, this takes 1 to 3 minutes...
  python scripts\train_pipeline.py
  if errorlevel 1 goto trainfail
)

where npm >nul 2>nul
if errorlevel 1 goto nonode

if not exist "frontend\node_modules" (
  echo Installing frontend packages...
  pushd frontend
  call npm install
  if errorlevel 1 goto npmfail
  popd
)

echo Starting API on http://localhost:%BACKEND_PORT% ...
start "LearnPathIQ API" cmd /k "cd /d "%SCRIPT_DIR%" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

echo Starting web app on http://localhost:%FRONTEND_PORT% ...
start "LearnPathIQ Web" cmd /k "cd /d "%SCRIPT_DIR%frontend" && npm run dev"

timeout /t 6 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo Open http://localhost:%FRONTEND_PORT%   (the original server-rendered UI is still at http://localhost:%BACKEND_PORT%)
echo Close the two server windows to stop.
pause
exit /b 0

:nopython
echo [ERROR] Python was not found on PATH.
echo Please install Python 3.11+ from https://www.python.org/downloads/
echo Make sure "Add python.exe to PATH" is checked during install.
pause
exit /b 1

:venvfail
echo [ERROR] Failed to create virtual environment. See error above.
pause
exit /b 1

:pipfail
echo [ERROR] Dependency installation failed. See error above.
pause
exit /b 1

:trainfail
echo [ERROR] Training failed. See error above.
pause
exit /b 1

:nonode
echo [ERROR] Node.js was not found on PATH.
echo Install Node.js 20+ from https://nodejs.org/ and run this file again.
pause
exit /b 1

:npmfail
echo [ERROR] npm install failed. See error above.
pause
exit /b 1
