@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title FlowSense launcher

rem ---- ports (from .env, same defaults) -------------------------------------
set "BACKEND_PORT=8310"
set "FRONTEND_PORT=5310"
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set "BACKEND_PORT=%%B"
    if /i "%%A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%B"
  )
)

rem ---- python -----------------------------------------------------------------
set "VPY=%~dp0.venv\Scripts\python.exe"
if exist "%VPY%" (
  "%VPY%" -c "import sys" >nul 2>&1
  if errorlevel 1 (
    echo The existing .venv points at a Python that is gone. Rebuilding it.
    rmdir /s /q ".venv"
  )
)
if not exist "%VPY%" (
  echo Creating the Python environment in .venv - first run only.
  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo ERROR: could not create a virtual environment. Install Python 3.10 or newer from python.org and tick "Add to PATH".
    pause
    exit /b 1
  )
)

"%VPY%" -c "import fastapi, uvicorn, numpy, pandas, sklearn, cv2, multipart" >nul 2>&1
if errorlevel 1 (
  echo Installing backend packages - a few minutes the first time.
  "%VPY%" -m pip install --upgrade pip >nul 2>&1
  "%VPY%" -m pip install -r backend\requirements.txt
  if errorlevel 1 (
    echo.
    echo ERROR: installing backend\requirements.txt failed - check your internet connection and run run.bat again.
    pause
    exit /b 1
  )
)

"%VPY%" -c "import ultralytics" >nul 2>&1
if errorlevel 1 (
  echo Installing YOLOv8 - ultralytics and PyTorch, a large download. The app still starts if this fails.
  "%VPY%" -m pip install -r backend\requirements-yolo.txt
  if errorlevel 1 echo WARNING: YOLOv8 was not installed. The Vision page will say so; every other screen works.
)

rem ---- node -------------------------------------------------------------------
where npm >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERROR: Node.js was not found. Install Node 20 or newer from nodejs.org and run run.bat again.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Installing frontend packages - first run only.
  pushd frontend
  call npm install
  popd
)

rem ---- start both servers -----------------------------------------------------
echo.
echo Starting FlowSense: API on port %BACKEND_PORT%, web app on port %FRONTEND_PORT%.
start "FlowSense API" /min cmd /c ""%VPY%" -m uvicorn backend.main:app --port %BACKEND_PORT%"
start "FlowSense Web" /min /d "%~dp0frontend" cmd /c "npm run dev"

if /i "%~1"=="nobrowser" goto :done
timeout /t 6 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"

:done
echo.
echo Open http://localhost:%FRONTEND_PORT%   (sign in with the demo account shown on the login page)
echo Close the two minimised windows named FlowSense to stop.
endlocal
