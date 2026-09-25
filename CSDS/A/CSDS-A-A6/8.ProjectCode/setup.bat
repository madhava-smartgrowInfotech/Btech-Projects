@echo off
setlocal
cd /d "%~dp0"

echo === ClauseGuard setup ===

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH. Install Python 3.10+ and re-run this script.
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js was not found on PATH. Install Node.js LTS and re-run this script.
    exit /b 1
)

if not exist ".env" (
    echo Creating .env from .env.example - fill in GEMINI_API_KEY before running.
    copy ".env.example" ".env" >nul
)

echo.
echo Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
)

echo Installing backend dependencies...
call "venv\Scripts\python.exe" -m pip install --upgrade pip
call "venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo Backend dependency install failed.
    exit /b 1
)

echo.
echo Installing frontend dependencies...
pushd frontend
call npm install
if errorlevel 1 (
    echo Frontend dependency install failed.
    popd
    exit /b 1
)
popd

echo.
if not exist "data\cuad\CUADv1.json" (
    echo CUAD dataset missing - downloading...
    call "venv\Scripts\python.exe" scripts\download_data.py
)

echo.
echo === Setup complete ===
echo 1. Open .env and set GEMINI_API_KEY (get one at https://aistudio.google.com/apikey)
echo 2. Run run.bat to start ClauseGuard
endlocal
