@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo  CareLens AI - Automatic Startup
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on PATH.
  echo Please install Python 3.11 from https://www.python.org/downloads/ and re-run run.bat
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found on PATH.
  echo Please install Node 18+ from https://nodejs.org/ and re-run run.bat
  pause
  exit /b 1
)
set BACKEND_PORT=8412
set FRONTEND_PORT=5412
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
)
if not exist ".venv" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create virtual environment. See the error above.
    pause
    exit /b 1
  )
)
call ".venv\Scripts\activate.bat"
echo Installing backend dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. See the error above.
  pause
  exit /b 1
)
if not exist "data\processed\knowledge_base.json" (
  echo Preparing medical knowledge base...
  python scripts\prepare_data.py
)
if not exist "data\index\faiss.index" (
  echo Building retrieval index...
  python scripts\build_index.py
)
if not exist "frontend\node_modules" (
  echo Installing frontend dependencies...
  pushd frontend
  call npm install
  popd
)
echo Seeding the demo account...
python scripts\seed_demo.py
echo Starting backend on http://127.0.0.1:%BACKEND_PORT% ...
start "CareLens API" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
echo Starting frontend on http://localhost:%FRONTEND_PORT% ...
start "CareLens Web" cmd /k "cd /d frontend && npm run dev"
timeout /t 6 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo  App:  http://localhost:%FRONTEND_PORT%   (demo login: demo@carelens.ai / Demo@1234)
echo  API:  http://127.0.0.1:%BACKEND_PORT%/docs
echo  Close the two server windows to stop.
