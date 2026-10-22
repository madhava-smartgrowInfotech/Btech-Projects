@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem ---- ports (project .env, defaults 8405 / 5405) ----
set BACKEND_PORT=8405
set FRONTEND_PORT=5405
if not exist ".env" copy /y ".env.example" ".env" >nul 2>nul
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

rem ---- python environment ----
set PY=.venv\Scripts\python.exe
if exist "%PY%" (
  "%PY%" -c "import fastapi, uvicorn, xgboost, pyarrow, sklearn, pandas" >nul 2>nul
  if errorlevel 1 set NEED_DEPS=1
) else (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :nopython
  set NEED_DEPS=1
)
if defined NEED_DEPS (
  echo Installing Python packages - this can take several minutes the first time...
  "%PY%" -m pip install --upgrade pip
  "%PY%" -m pip install -r requirements.txt
  if errorlevel 1 goto :pipfail
)

rem ---- trained models (only built when missing) ----
if not exist "models\xgb_calibrated.pkl" (
  echo Training models...
  "%PY%" src\generate_dataset.py
  "%PY%" src\preprocess.py
  "%PY%" src\hybrid_model.py
)

rem ---- frontend dependencies ----
if not exist "frontend\node_modules" (
  echo Installing frontend packages...
  pushd frontend
  call npm install
  popd
)

echo.
echo Starting backend  on http://localhost:%BACKEND_PORT%
echo Starting frontend on http://localhost:%FRONTEND_PORT%
start "SCPS backend" cmd /k ""%~dp0%PY%" -m uvicorn backend.main:app --port %BACKEND_PORT%"
start "SCPS frontend" /d "%~dp0frontend" cmd /k "npm run dev"

timeout /t 6 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo Both servers run in their own windows - close them to stop the app.
goto :eof

:nopython
echo Python 3.10+ was not found on PATH. Install it from python.org and run again.
pause
exit /b 1

:pipfail
echo Installing Python packages failed - see the messages above.
pause
exit /b 1
