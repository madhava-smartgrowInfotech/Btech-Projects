@echo off
REM AquaVision one-time setup: Python venv + packages, frontend packages, .env
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)
if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
call venv\Scripts\python -m pip install --upgrade pip
call venv\Scripts\pip install -r requirements.txt || exit /b 1
if not exist .env (
  copy .env.example .env >nul
  for /f %%i in ('venv\Scripts\python -c "import secrets;print(secrets.token_hex(32))"') do set SECRET=%%i
  call venv\Scripts\python -c "import re,os;p='.env';s=open(p).read().replace('change-me-to-a-long-random-string',os.environ['SECRET']);open(p,'w').write(s)"
  echo Created .env with a fresh JWT secret.
)
cd frontend
call npm install || exit /b 1
cd ..
echo.
echo Setup complete. Start AquaVision with run.bat
