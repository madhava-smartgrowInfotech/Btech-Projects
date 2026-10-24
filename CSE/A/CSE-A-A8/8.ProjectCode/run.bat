@echo off
rem LabLens - one-click start: FastAPI backend (port from .env, default 8308) + React frontend (default 5308).
setlocal
cd /d "%~dp0"

set BACKEND_PORT=8308
set FRONTEND_PORT=5308
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /I "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

where python >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 or newer was not found on PATH. Install it from https://www.python.org/downloads/ and run this file again.
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo Node.js was not found on PATH. Install the LTS version from https://nodejs.org/ and run this file again.
  pause
  exit /b 1
)

rem ---- backend virtual environment (rebuilt automatically if it is missing or broken)
set "VENV_PY=%~dp0backend\.venv\Scripts\python.exe"
set NEED_INSTALL=0
if not exist "%VENV_PY%" set NEED_INSTALL=1
if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import fastapi, uvicorn, multipart, cv2, pymupdf, sklearn, sqlalchemy, dotenv" >nul 2>&1
  if errorlevel 1 set NEED_INSTALL=1
)
if "%NEED_INSTALL%"=="1" (
  if exist "backend\.venv" (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if errorlevel 1 rmdir /s /q "backend\.venv"
  )
  if not exist "%VENV_PY%" (
    echo Creating the Python environment in backend\.venv ...
    python -m venv backend\.venv
    if errorlevel 1 (
      echo Could not create the virtual environment.
      pause
      exit /b 1
    )
  )
  echo Installing backend packages - this takes a few minutes the first time ...
  "%VENV_PY%" -m pip install --disable-pip-version-check -r backend\requirements.txt
  if errorlevel 1 (
    echo Package installation failed - check your internet connection and run this file again.
    pause
    exit /b 1
  )
)

rem ---- frontend packages
if not exist "frontend\node_modules" (
  echo Installing frontend packages ...
  pushd frontend
  call npm install --no-audit --no-fund
  popd
  if not exist "frontend\node_modules" (
    echo npm install failed - check your internet connection and run this file again.
    pause
    exit /b 1
  )
)

where tesseract >nul 2>&1
if errorlevel 1 echo Note: Tesseract OCR is not installed. Text PDFs work; scanned images and photos need it - see docs\03_HOW_TO_RUN.md.

echo Starting the API on port %BACKEND_PORT% and the web app on port %FRONTEND_PORT% ...
start "LabLens API" /D "%~dp0" "%VENV_PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%
start "LabLens UI" /D "%~dp0frontend" cmd /k npm run dev

ping -n 8 127.0.0.1 >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo LabLens is starting. Demo login: demo@lablens.com / Demo@1234
echo Close the two console windows to stop it.
endlocal
