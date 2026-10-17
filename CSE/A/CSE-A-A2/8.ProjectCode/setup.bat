@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ResQAI - setup

if not exist ".env" copy /y ".env.example" ".env" >nul

if not exist "venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  python -m venv venv || (echo [X] Python 3.10+ is required. & pause & exit /b 1)
)
echo Installing Python packages...
"venv\Scripts\python.exe" -m pip install -q -r requirements.txt || (echo [X] pip install failed. & pause & exit /b 1)

echo Installing frontend packages...
pushd frontend
call npm install || (echo [X] npm install failed. Node.js 18+ is required. & popd & pause & exit /b 1)
popd

echo.
echo Setup complete. Run run.bat to start ResQAI.
pause
