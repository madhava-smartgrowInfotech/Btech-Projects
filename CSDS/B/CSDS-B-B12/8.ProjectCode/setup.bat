@echo off
setlocal
cd /d "%~dp0"
echo === PulmoVision setup ===
where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)
if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example - put your GEMINI_API_KEY, JWT_SECRET and FERNET_KEY in it.
)
if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
call venv\Scripts\python -m pip install --upgrade pip -q
echo Installing Python packages (CPU PyTorch, about 1 GB the first time)...
call venv\Scripts\pip install -q torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu || exit /b 1
call venv\Scripts\pip install -q -r backend\requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu || exit /b 1
echo Installing frontend packages...
pushd frontend
call npm install --no-audit --no-fund || (popd & exit /b 1)
popd
echo.
echo Setup complete. Start the app with run.bat
endlocal
