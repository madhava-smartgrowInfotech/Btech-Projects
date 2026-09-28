@echo off
REM HospiSense one-time setup: Python venv + packages, .env, frontend packages.
cd /d "%~dp0"

where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)

if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
call venv\Scripts\python -m pip install --upgrade pip
call venv\Scripts\pip install -r requirements.txt || exit /b 1

call venv\Scripts\python scripts\init_env.py

if not exist models\los_regressor.json (
  echo Preparing data and training models...
  call venv\Scripts\python ml\prepare_data.py || exit /b 1
  call venv\Scripts\python ml\train.py || exit /b 1
)

cd frontend
call npm install || exit /b 1
cd ..

echo.
echo Setup complete. Start HospiSense with run.bat
