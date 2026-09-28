@echo off
REM APISentry one-time setup: Python venv + backend deps + frontend deps.
setlocal
cd /d "%~dp0"

echo ============================================
echo  APISentry setup
echo ============================================

if not exist ".env" (
  echo Creating .env from .env.example ...
  copy /y ".env.example" ".env" >nul
  echo   -^> Edit .env to add your GEMINI_API_KEY ^(optional; a built-in generator is used otherwise^).
)

echo.
echo [1/3] Creating Python virtual environment ...
if not exist "venv" (
  python -m venv venv
)

echo.
echo [2/3] Installing backend dependencies ...
call "venv\Scripts\python.exe" -m pip install --upgrade pip
call "venv\Scripts\python.exe" -m pip install -r backend\requirements.txt

echo.
echo [3/3] Installing frontend dependencies ...
pushd frontend
call npm install
popd

echo.
echo ============================================
echo  Setup complete. Run run.bat to start APISentry.
echo ============================================
endlocal
