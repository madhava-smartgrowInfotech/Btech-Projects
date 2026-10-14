@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Attendance Magic - launcher

if not exist "venv\Scripts\python.exe" (
  echo Attendance Magic is not set up yet. Run setup.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Frontend packages are missing. Run setup.bat first.
  pause
  exit /b 1
)

rem Fixed ports for this batch; .env may override them.
set "BACKEND_PORT=8102"
set "FRONTEND_PORT=5102"
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
    if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
  )
)

netstat -ano | findstr /r /c:":%BACKEND_PORT% .*LISTENING" >nul && (
  echo Port %BACKEND_PORT% is already in use. Run stop.bat or close the other app first.
  pause
  exit /b 1
)
netstat -ano | findstr /r /c:":%FRONTEND_PORT% .*LISTENING" >nul && (
  echo Port %FRONTEND_PORT% is already in use. Run stop.bat or close the other app first.
  pause
  exit /b 1
)

echo Starting API on http://127.0.0.1:%BACKEND_PORT% ...
start "Attendance Magic API" cmd /k venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port %BACKEND_PORT%

echo Starting frontend on http://localhost:%FRONTEND_PORT% ...
start "Attendance Magic UI" cmd /k "cd /d frontend && npm run dev"

rem wait a few seconds for both servers before opening the browser
ping -n 7 127.0.0.1 >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo Attendance Magic is running:
echo   Frontend  http://localhost:%FRONTEND_PORT%
echo   API       http://127.0.0.1:%BACKEND_PORT%/docs
echo   Streamlit (original UI, optional):  venv\Scripts\streamlit run app.py
echo Close the two server windows (or run stop.bat) to stop.
exit /b 0
