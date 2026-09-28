@echo off
REM UniHealth one-time setup: Python venv + packages, hospital data, models, frontend packages.
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)
if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example - add your GEMINI_API_KEY to it.
)
if not exist venv python -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r backend\requirements.txt || exit /b 1
if not exist data\hospital_a.db venv\Scripts\python scripts\seed_hospitals.py || exit /b 1
if not exist models\heart_rf.joblib venv\Scripts\python ml\train.py || exit /b 1
pushd frontend
call npm install || (popd & exit /b 1)
popd
echo.
echo Setup complete. Start UniHealth with run.bat
