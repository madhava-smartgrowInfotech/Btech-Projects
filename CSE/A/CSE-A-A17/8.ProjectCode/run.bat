@echo off
setlocal
rem TrendCast - starts the FastAPI backend (port 8317) and the React frontend (port 5317).
rem The original Streamlit app is untouched: run  streamlit run app.py  if you want it.
cd /d "%~dp0"

set "BACKEND_PORT=8317"
set "FRONTEND_PORT=5317"
for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
  if /i "%%A"=="BACKEND_PORT" set "BACKEND_PORT=%%B"
  if /i "%%A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%B"
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer is required and was not found on PATH.
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js 18 or newer is required and was not found on PATH.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 exit /b 1
)
set "PY=%~dp0.venv\Scripts\python.exe"

if not exist ".venv\.deps_installed" (
  echo Installing Python packages, this takes a few minutes the first time...
  "%PY%" -m pip install --upgrade pip
  "%PY%" -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
  echo ok> ".venv\.deps_installed"
)

if not exist "frontend\node_modules" (
  echo Installing frontend packages...
  pushd frontend
  call npm install
  if errorlevel 1 exit /b 1
  popd
)

if "%~1"=="test" (
  echo Starting the backend for the smoke test...
  start "TrendCast backend" /min "%PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%
  timeout /t 12 /nobreak >nul
  if not exist "data\sample_hm\transactions_train.csv" "%PY%" scripts\make_sample_data.py
  "%PY%" scripts\smoke_test.py --base http://localhost:%BACKEND_PORT%
  exit /b %errorlevel%
)

echo Starting backend on http://localhost:%BACKEND_PORT%
start "TrendCast backend" "%PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%

echo Starting frontend on http://localhost:%FRONTEND_PORT%
pushd frontend
start "TrendCast frontend" cmd /c "npm run dev"
popd

timeout /t 6 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo TrendCast is running. Close the two console windows to stop it.
endlocal
