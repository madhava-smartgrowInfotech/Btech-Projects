@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ChurnIQ launcher

rem ---------------------------------------------------------------------------
rem  run.bat           start the API and the React app (installs on first run)
rem  run.bat smoke     run the API smoke test against a running backend
rem  run.bat streamlit start the original Streamlit app instead
rem  run.bat build     production build of the frontend
rem ---------------------------------------------------------------------------

set BACKEND_PORT=8314
set FRONTEND_PORT=5314
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT" set BACKEND_PORT=%%B
    if /i "%%A"=="FRONTEND_PORT" set FRONTEND_PORT=%%B
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer was not found on PATH. Install it from python.org and run this again.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python virtual environment .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo Could not create the virtual environment.
    exit /b 1
  )
)
set VENV_PY=%~dp0.venv\Scripts\python.exe

if /i "%~1"=="streamlit" goto streamlit
if /i "%~1"=="smoke" goto smoke
if /i "%~1"=="build" goto build

:deps
if not exist ".venv\.deps-ok" (
  echo Installing Python packages, first run only ...
  "%VENV_PY%" -m pip install --upgrade pip
  "%VENV_PY%" -m pip install -r backend\requirements.txt
  if errorlevel 1 (
    echo Python package install failed. Check your internet connection and try again.
    exit /b 1
  )
  echo ok> ".venv\.deps-ok"
)

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 18 or newer was not found on PATH. Install it from nodejs.org and run this again.
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Installing frontend packages, first run only ...
  pushd frontend
  call npm install
  if errorlevel 1 (
    popd
    echo npm install failed. Check your internet connection and try again.
    exit /b 1
  )
  popd
)

echo Starting the API on port %BACKEND_PORT% ...
start "ChurnIQ API" /D "%CD%" cmd /k ""%VENV_PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
echo Starting the web app on port %FRONTEND_PORT% ...
start "ChurnIQ Web" /D "%CD%\frontend" cmd /k "npm run dev"

echo Waiting for the web app ...
set /a TRIES=0
:wait
set /a TRIES+=1
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing http://localhost:%FRONTEND_PORT%/ -TimeoutSec 2).StatusCode } catch { exit 1 }" >nul 2>nul
if not errorlevel 1 goto ready
if %TRIES% GEQ 40 goto ready
timeout /t 1 /nobreak >nul
goto wait

:ready
echo.
echo   App:  http://localhost:%FRONTEND_PORT%
echo   API:  http://localhost:%BACKEND_PORT%/docs
echo   Demo sign in: demo@churniq.com / Demo@1234
echo.
start "" "http://localhost:%FRONTEND_PORT%"
exit /b 0

:smoke
if not exist ".venv\.deps-ok" (
  echo Start the app once with run.bat first, so the packages are installed.
  exit /b 1
)
"%VENV_PY%" scripts\smoke_test.py http://localhost:%BACKEND_PORT%
exit /b %errorlevel%

:build
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found on PATH.
  exit /b 1
)
pushd frontend
if not exist "node_modules" call npm install
call npm run build
set BUILD_RC=%errorlevel%
popd
exit /b %BUILD_RC%

:streamlit
echo Installing the Streamlit requirements, first run only ...
"%VENV_PY%" -m pip install -r requirements.txt
"%VENV_PY%" -m streamlit run app.py
exit /b %errorlevel%
