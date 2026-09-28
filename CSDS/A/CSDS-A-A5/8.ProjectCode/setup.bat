@echo off
REM TaxSentinel one-time setup: Python venv + packages, .env, frontend packages.
setlocal
cd /d "%~dp0"

where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)

if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
echo Installing Python packages (PyTorch CPU build first)...
venv\Scripts\python -m pip install --upgrade pip -q
venv\Scripts\pip install -q torch --index-url https://download.pytorch.org/whl/cpu || exit /b 1
venv\Scripts\pip install -q -r requirements.txt || exit /b 1

if not exist .env (
  echo Creating .env from .env.example ...
  venv\Scripts\python -c "import secrets,re;t=open('.env.example',encoding='utf-8').read();open('.env','w',encoding='utf-8').write(re.sub(r'(?m)^JWT_SECRET=$','JWT_SECRET='+secrets.token_hex(32),t))"
  echo   Add your GEMINI_API_KEY to .env to enable written explanations.
)

if not exist models\jepa.pt (
  echo Training the JEPA encoder...
  venv\Scripts\python -m ml.train || exit /b 1
)

echo Installing frontend packages...
pushd frontend
call npm install --no-audit --no-fund || (popd & exit /b 1)
popd

echo.
echo Setup complete. Start TaxSentinel with run.bat
endlocal
