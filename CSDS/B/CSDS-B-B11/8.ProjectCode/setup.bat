@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo   NutriSense - one-time setup
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.11+ is required. Install it from https://www.python.org/downloads/ and tick "Add to PATH".
  pause & exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js LTS is required. Install it from https://nodejs.org/
  pause & exit /b 1
)

if not exist venv (
  echo [1/5] Creating Python virtual environment...
  python -m venv venv || goto :fail
)
echo [2/5] Installing backend packages...
call venv\Scripts\python -m pip install --upgrade pip >nul
call venv\Scripts\pip install -r backend\requirements.txt || goto :fail

if not exist .env (
  echo [3/5] Creating .env from .env.example...
  copy .env.example .env >nul
  venv\Scripts\python -c "import secrets,pathlib;p=pathlib.Path('.env');p.write_text(p.read_text().replace('change-me-to-a-long-random-string',secrets.token_hex(32)))"
  echo       Add your GEMINI_API_KEY to .env ^(https://aistudio.google.com/apikey^)
) else (
  echo [3/5] .env already exists - keeping it.
)

echo [4/5] Preparing food database and swap model...
if not exist data\processed\foods.csv venv\Scripts\python ml\build_foods.py || goto :fail
if not exist models\swap_kmeans.joblib venv\Scripts\python ml\train_swaps.py || goto :fail

echo [5/5] Installing frontend packages...
pushd frontend
call npm install || (popd & goto :fail)
popd

echo.
echo Setup complete. Start NutriSense with run.bat
pause
exit /b 0

:fail
echo.
echo Setup failed - see the messages above.
pause
exit /b 1
