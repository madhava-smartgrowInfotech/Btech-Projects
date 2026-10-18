@echo off
setlocal
cd /d "%~dp0"
set "BPORT=8311"
set "FPORT=5311"
for /f "tokens=1,2 delims==" %%a in ('findstr /b "BACKEND_PORT FRONTEND_PORT" .env 2^>nul') do (
  if "%%a"=="BACKEND_PORT" set "BPORT=%%b"
  if "%%a"=="FRONTEND_PORT" set "FPORT=%%b"
)

echo [1/3] Python dependencies
python -m pip install -q -r requirements.txt
if errorlevel 1 goto :fail

echo [2/3] Frontend dependencies
if not exist frontend\node_modules (
  pushd frontend
  call npm install --no-audit --no-fund
  popd
)
if not exist frontend\node_modules goto :fail

echo [3/3] Starting API on %BPORT% and web app on %FPORT%
start "AutoSecAI API" cmd /k "cd /d %~dp0 && python -m backend"
start "AutoSecAI Web" cmd /k "cd /d %~dp0frontend && npm run dev"
ping -n 7 127.0.0.1 >nul
start "" http://localhost:%FPORT%
echo.
echo Demo sign-in:  demo@autosecai.dev  /  Demo@1234
echo Close the two new windows to stop. The original Streamlit app is still available: run_streamlit.bat
exit /b 0

:fail
echo.
echo Setup failed - see the messages above.
exit /b 1
