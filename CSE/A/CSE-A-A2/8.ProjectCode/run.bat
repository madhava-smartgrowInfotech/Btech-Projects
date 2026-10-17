@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ResQAI - launcher

if not exist ".env" copy /y ".env.example" ".env" >nul
if not exist "venv\Scripts\python.exe" (
  echo ResQAI is not set up yet. Run setup.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Frontend packages are missing. Run setup.bat first.
  pause
  exit /b 1
)

rem Ports are fixed for ResQAI; overrides may be set in .env.
set "BACKEND_PORT=8302"
set "FRONTEND_PORT=5302"
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
  if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
)

netstat -ano | findstr /r /c:":%BACKEND_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  echo [X] Port %BACKEND_PORT% is already in use. ResQAI may already be running - run stop.bat first.
  pause
  exit /b 1
)
netstat -ano | findstr /r /c:":%FRONTEND_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  echo [X] Port %FRONTEND_PORT% is already in use. ResQAI may already be running - run stop.bat first.
  pause
  exit /b 1
)

echo Starting ResQAI API on port %BACKEND_PORT%...
start "ResQAI API" cmd /k "set PORT=%BACKEND_PORT%&& venv\Scripts\python.exe app.py"

echo Starting ResQAI web app on port %FRONTEND_PORT%...
start "ResQAI Web" cmd /k "cd /d frontend && npm run dev"

echo Waiting for the web app...
for /l %%i in (1,1,30) do (
  netstat -ano | findstr /r /c:":%FRONTEND_PORT% .*LISTENING" >nul && goto ready
  timeout /t 1 /nobreak >nul
)
:ready
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo ResQAI is running:  web http://localhost:%FRONTEND_PORT%   api http://localhost:%BACKEND_PORT%
echo Close the two ResQAI windows (or run stop.bat) to stop it.
