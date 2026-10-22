@echo off
setlocal EnableExtensions
REM VeriVision AI - one-click launcher: API on 127.0.0.1:8414, React frontend on http://localhost:5414
cd /d "%~dp0"

echo ============================================================
echo  VeriVision AI - starting
echo ============================================================

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found on PATH.
  echo Please install Python 3.10 or newer from https://www.python.org/downloads/
  echo During installation, tick "Add python.exe to PATH".
  pause
  exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Found %%v

if not exist ".venv" (
  echo Creating virtual environment in .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment. See the error above.
    pause
    exit /b 1
  )
) else (
  echo Virtual environment already exists, reusing it.
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate the virtual environment.
  pause
  exit /b 1
)

echo Installing dependencies from requirements.txt ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed. See the error above.
  echo Try: python -m pip install --upgrade pip setuptools wheel
  pause
  exit /b 1
)

if not exist "models\efficientnet_a1.pt" (
  echo Model artifacts not found. Preparing data and training models...
  echo This is a one-time step and can take a while on CPU.
  python scripts\prepare_dataset.py
  if errorlevel 1 (
    echo [ERROR] Dataset preparation failed. See the error above.
    pause
    exit /b 1
  )
  python scripts\train_a1.py
  python scripts\train_a2.py
  python scripts\train_b.py
  python scripts\train_c.py
  python scripts\evaluate.py
  if not exist "models\efficientnet_a1.pt" (
    echo [ERROR] Training did not produce model artifacts.
    echo Run the commands in HOW_TO_RUN.md Method C manually to see details.
    pause
    exit /b 1
  )
) else (
  echo Model artifacts found, skipping training.
)

if not exist ".env" (
  if exist ".env.example" copy /y ".env.example" ".env" >nul
)

where node >nul 2>nul
if errorlevel 1 goto :noNode

if not exist "frontend\node_modules" (
  echo Installing frontend packages, one-time step ...
  pushd frontend
  call npm install
  popd
)

echo Starting the API on http://localhost:8414 in its own window ...
start "VeriVision API" cmd /k ".venv\Scripts\python.exe run.py"
echo Starting the web app on http://localhost:5414 ...
start "VeriVision Web" cmd /k "cd /d frontend && npm run dev"
ping -n 9 127.0.0.1 >nul
start "" "http://localhost:5414"
echo.
echo Both servers are running in their own windows. Close those windows to stop them.
echo Demo login: demo@verivision.ai  /  Demo@1234
pause
exit /b 0

:noNode
echo [WARNING] Node.js was not found, so the new web app cannot start.
echo Install Node.js 20 or newer from https://nodejs.org/ and run this file again.
echo Starting the built-in classic page on http://localhost:8414 instead ...
start "" "http://localhost:8414"
python run.py
echo.
echo Server stopped.
pause
