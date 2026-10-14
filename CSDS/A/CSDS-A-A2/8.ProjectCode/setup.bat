@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Attendance Magic - setup

rem mediapipe 0.10.21 (FaceMesh "solutions" API) has wheels for Python 3.9-3.12 only.
set "PY=py -3.11"
%PY% --version >nul 2>&1 || set "PY=python"

if not exist "venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  %PY% -m venv venv || goto :fail
)
echo Installing Python packages (first run downloads ~1 GB)...
venv\Scripts\python.exe -m pip install --upgrade pip >nul
rem requirements.txt pins protobuf 4.x for mediapipe while streamlit declares >=5;
rem install streamlit first, then the rest so the documented protobuf pin wins.
venv\Scripts\python.exe -m pip install "streamlit==1.64.0" || goto :fail
findstr /v /b /c:"streamlit==" requirements.txt > "%TEMP%\am_requirements.txt"
venv\Scripts\python.exe -m pip install -r "%TEMP%\am_requirements.txt" -r backend\requirements.txt || goto :fail
rem pip downgrades streamlit to satisfy protobuf 4.x; restore the pinned version on top (runs fine on 4.25).
venv\Scripts\python.exe -m pip install --no-deps "streamlit==1.64.0" || goto :fail

if not exist ".env" copy ".env.example" ".env" >nul

echo Seeding demo accounts...
venv\Scripts\python.exe scripts\seed_demo.py

echo Installing frontend packages...
pushd frontend
call npm install || (popd & goto :fail)
popd

echo.
echo Setup complete. Start everything with run.bat
pause
exit /b 0

:fail
echo.
echo Setup failed - see the messages above.
pause
exit /b 1
