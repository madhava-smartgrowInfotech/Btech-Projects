@echo off
setlocal EnableExtensions
REM FinSight AI - automatic launcher (localhost only)
REM API (Flask) on PORT, React frontend on FRONTEND_PORT. Defaults match .env.
cd /d "%~dp0"
set PORT=8409
set FRONTEND_PORT=5409
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="PORT" set PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found on PATH.
  echo Please install Python 3.11 or newer from https://www.python.org/downloads/
  echo Make sure to tick "Add python.exe to PATH" during installation.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found on PATH.
  echo Please install Node.js 18 or newer from https://nodejs.org/
  pause
  exit /b 1
)
echo [1/6] Python and Node found:
python --version
node --version

if not exist ".venv\Scripts\activate.bat" (
  echo [2/6] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create the virtual environment. See the error above.
    pause
    exit /b 1
  )
) else (
  echo [2/6] Virtual environment already exists. Skipping creation.
)

echo [3/6] Activating environment and installing Python dependencies...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
echo Installing requirements - first run may take several minutes...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed. See the error above.
  pause
  exit /b 1
)

if not exist "models\best_model.pkl" (
  echo [4/6] No trained model found. Running training pipeline - one-time, may take a few minutes...
  python scripts\train.py
  if errorlevel 1 (
    echo [ERROR] Training failed. See the error above.
    pause
    exit /b 1
  )
) else (
  echo [4/6] Trained model found.
)

echo [5/6] Preparing the React frontend...
pushd frontend
if not exist "node_modules" (
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed. See the error above.
    popd
    pause
    exit /b 1
  )
)
if not exist "dist\index.html" (
  call npm run build
  if errorlevel 1 (
    echo [ERROR] Frontend build failed. See the error above.
    popd
    pause
    exit /b 1
  )
)
popd

echo [6/6] Starting FinSight AI...
echo   API       http://localhost:%PORT%
echo   Frontend  http://localhost:%FRONTEND_PORT%
start "FinSight API" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && set PORT=%PORT%&& python run.py"
start "" "http://localhost:%FRONTEND_PORT%"
cd frontend
call npm run preview
echo.
echo Frontend stopped. Close the "FinSight API" window to stop the API. Press any key to close this window.
pause >nul
