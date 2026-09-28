@echo off
REM MediQueue one-time setup: Python venv + backend packages + frontend packages
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)
if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
call venv\Scripts\python -m pip install --upgrade pip
call venv\Scripts\pip install -r backend\requirements.txt || exit /b 1
if not exist .env (
  copy .env.example .env >nul
  for /f %%s in ('venv\Scripts\python -c "import secrets;print(secrets.token_hex(32))"') do (
    venv\Scripts\python -c "import pathlib,sys;p=pathlib.Path('.env');p.write_text(p.read_text().replace('change-me-to-a-long-random-string','%%s'))"
  )
  echo Created .env - add your GEMINI_API_KEY to enable free-text symptom mapping with Gemini.
)
cd frontend
call npm install --no-audit --no-fund || exit /b 1
cd ..
echo.
echo Setup complete. Start the app with run.bat
