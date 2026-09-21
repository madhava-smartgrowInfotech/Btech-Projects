@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PolicyLens - setup
echo ==========================================================
echo   PolicyLens - one-time setup
echo ==========================================================
echo.

rem ---- 1. Python 3.11 --------------------------------------------------------
set "PY="
py -3.11 --version >nul 2>&1 && set "PY=py -3.11"
if not defined PY (
  python --version 2>nul | findstr /c:"Python 3.11" >nul && set "PY=python"
)
if not defined PY (
  echo [X] Python 3.11 was not found.
  echo     Install it from https://www.python.org/downloads/release/python-3119/
  echo     ^(Windows installer 64-bit, tick "Add python.exe to PATH"^), then run setup.bat again.
  goto :fail
)
for /f "delims=" %%v in ('%PY% --version') do echo [OK] %%v

rem ---- 2. Node.js -------------------------------------------------------------
where node >nul 2>&1
if errorlevel 1 (
  echo [X] Node.js was not found. Install the LTS version from https://nodejs.org and run setup.bat again.
  goto :fail
)
for /f "delims=" %%v in ('node --version') do echo [OK] Node.js %%v

rem ---- 3. Python environment and packages --------------------------------------
if not exist "venv\Scripts\python.exe" (
  echo.
  echo Creating the Python environment ^(venv^)...
  %PY% -m venv venv
  if errorlevel 1 goto :fail
)
echo.
echo Installing backend packages - the first time this downloads about 1 GB, please wait...
"venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 goto :fail
echo [OK] Backend packages installed

rem ---- 4. Configuration ---------------------------------------------------------
echo.
"venv\Scripts\python.exe" scripts\init_env.py
if errorlevel 1 goto :fail

rem ---- 5. Local AI models (embeddings, re-ranker, faithfulness) -----------------
echo.
echo Downloading the local AI models ^(about 480 MB, once^)...
"venv\Scripts\python.exe" scripts\download_models.py
if errorlevel 1 goto :fail

rem ---- 6. Frontend packages ------------------------------------------------------
echo.
echo Installing frontend packages...
pushd frontend
call npm ci --no-audit --no-fund
if errorlevel 1 (
  call npm install --no-audit --no-fund
  if errorlevel 1 ( popd & goto :fail )
)
popd
echo [OK] Frontend packages installed

rem ---- 7. Database, demo account, sample policies and search index -------------
echo.
"venv\Scripts\python.exe" scripts\init_app.py
if errorlevel 1 goto :fail

echo.
echo ==========================================================
echo   Setup complete. Start PolicyLens with run.bat
echo ==========================================================
if not "%~1"=="--no-pause" pause
exit /b 0

:fail
echo.
echo Setup did not finish - see the message above. docs\10_TROUBLESHOOTING.md has fixes for common problems.
if not "%~1"=="--no-pause" pause
exit /b 1
