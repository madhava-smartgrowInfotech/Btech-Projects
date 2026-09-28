@echo off
rem SkyCipher one-time setup: Python venv + backend packages + frontend packages + .env
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)

if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\pip install -r backend\requirements.txt || exit /b 1

if not exist .env (
  copy .env.example .env >nul
  venv\Scripts\python -c "import secrets;p='.env';s=open(p).read();open(p,'w').write(s.replace('JWT_SECRET=change-me-to-a-long-random-string','JWT_SECRET='+secrets.token_hex(32)))"
  echo Created .env with a random JWT secret.
)

pushd frontend
call npm install || (popd & exit /b 1)
popd
echo.
echo Setup complete. Start SkyCipher with run.bat
