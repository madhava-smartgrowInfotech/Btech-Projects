@echo off
setlocal EnableExtensions
REM StoryVox automatic launcher (recommended for Windows, no coding knowledge required).
REM Starts the API on port 8402 and the web app on port 5402.
cd /d "%~dp0"
set PORT=8402
set FRONTEND_PORT=5402
if defined PORT_OVERRIDE set PORT=%PORT_OVERRIDE%

echo ============================================================
echo  StoryVox - starting the storytelling app
echo ============================================================
echo  Two windows will open: the StoryVox API and the web app.
echo  Keep both open while you use the app. First run may take a
echo  while because story and voice models are downloaded once.
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found on PATH.
  echo Please install Python 3.11 or newer from https://www.python.org/downloads/
  echo Then double-click run.bat again.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found on PATH.
  echo Please install Node.js 20 or newer from https://nodejs.org/
  echo Then double-click run.bat again.
  pause
  exit /b 1
)

REM A virtual environment copied from another computer points at a Python that does not exist here. Rebuild it.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
  if errorlevel 1 (
    echo The existing .venv is broken, recreating it...
    rmdir /s /q ".venv"
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating the StoryVox virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment. See the error above.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Could not activate the virtual environment.
  pause
  exit /b 1
)

echo Installing StoryVox dependencies, this may take several minutes...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [WARNING] pip upgrade failed, continuing with dependency install...
)
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed. See the error above.
  echo Try: pip install -r requirements.txt
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo Installing web app packages...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed. See the error above.
    pause
    exit /b 1
  )
  popd
)

echo.
echo Starting the StoryVox API on http://localhost:%PORT% ...
start "StoryVox API" cmd /k ""%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%"

echo Starting the web app on http://localhost:%FRONTEND_PORT% ...
start "" "http://localhost:%FRONTEND_PORT%"
pushd frontend
call npm run dev
popd
echo.
echo StoryVox web app stopped. You can close this window and the StoryVox API window.
pause
exit /b 0
