@echo off
setlocal
cd /d "%~dp0"
echo === RetinaGuard setup ===

where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)

if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
echo Installing Python packages (PyTorch CPU wheel, first run takes a few minutes)...
venv\Scripts\python -m pip install --upgrade pip >nul
venv\Scripts\pip install -r backend\requirements.txt || exit /b 1

if not exist .env (
  echo Creating .env from .env.example with a random JWT secret...
  venv\Scripts\python -c "import secrets,pathlib;t=pathlib.Path('.env.example').read_text();pathlib.Path('.env').write_text(t.replace('change-me-to-a-long-random-string',secrets.token_hex(32)))"
)

echo Installing frontend packages...
pushd frontend
call npm install || (popd & exit /b 1)
popd

if not exist models\lenet_hr.pt (
  echo Trained models are missing. Downloading data and training ^(about 5 minutes on CPU^)...
  venv\Scripts\python scripts\download_data.py || exit /b 1
  venv\Scripts\python ml\train_heart.py || exit /b 1
  venv\Scripts\python ml\train_retina.py || exit /b 1
)

echo.
echo Setup complete. Start RetinaGuard with run.bat
endlocal
