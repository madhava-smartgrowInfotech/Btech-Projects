@echo off
setlocal
cd /d "%~dp0"
if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example. Set JWT_SECRET in it before the first run.
)
if not exist venv (
  python -m venv venv || goto :fail
)
call venv\Scripts\python -m pip install --upgrade pip || goto :fail
call venv\Scripts\python -m pip install -r backend\requirements.txt || goto :fail
if not exist data\covers\NUL (
  call venv\Scripts\python scripts\make_samples.py || goto :fail
)
pushd frontend
call npm install || (popd & goto :fail)
popd
echo.
echo Setup complete. Start the app with run.bat
exit /b 0
:fail
echo Setup failed.
exit /b 1
