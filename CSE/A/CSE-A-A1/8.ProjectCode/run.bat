@echo off
REM Starts the FastAPI backend (8301) and the React frontend (5301).
setlocal
cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
  echo Creating virtual environment...
  python -m venv venv
  venv\Scripts\python.exe -m pip install -r backend\requirements.txt
)
if not exist frontend\node_modules (
  echo Installing frontend packages...
  pushd frontend
  call npm install
  popd
)

start "ALIP backend :8301" cmd /k "venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8301"
start "ALIP frontend :5301" cmd /k "cd frontend && npm run dev"
echo.
echo Backend : http://localhost:8301/api/health
echo Frontend: http://localhost:5301
endlocal
