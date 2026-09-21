@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SeatWise setup

echo.
echo  =====================================================
echo   SeatWise - one-time setup
echo  =====================================================
echo.

rem ---- 1. Python 3.11 --------------------------------------------------
set "PYTHON="
py -3.11 --version >nul 2>nul && set "PYTHON=py -3.11"
if not defined PYTHON (
  for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYV=%%v"
  if "!PYV:~0,5!"=="3.11." set "PYTHON=python"
)
if not defined PYTHON (
  echo [X] Python 3.11 was not found.
  echo     Install it from https://www.python.org/downloads/release/python-3119/
  echo     ^(Windows installer 64-bit^) and tick "Add python.exe to PATH".
  goto :fail
)
echo [1/6] Python 3.11 found

rem ---- 2. Node.js --------------------------------------------------------
where node >nul 2>nul
if errorlevel 1 (
  echo [X] Node.js was not found. Install the LTS version from https://nodejs.org
  goto :fail
)
for /f %%v in ('node --version') do echo [2/6] Node.js %%v found

rem ---- 3. Python environment --------------------------------------------
if not exist "venv\Scripts\python.exe" (
  echo [3/6] Creating the Python environment...
  %PYTHON% -m venv venv || goto :fail
) else (
  echo [3/6] Python environment exists
)
echo       Installing Python packages ^(first time: a few minutes^)...
"venv\Scripts\python.exe" -m pip install --upgrade pip --quiet --disable-pip-version-check
"venv\Scripts\python.exe" -m pip install -r backend\requirements.txt --quiet --disable-pip-version-check || goto :fail

rem ---- 4. Configuration --------------------------------------------------
echo [4/6] Preparing .env
"venv\Scripts\python.exe" scripts\ensure_env.py || goto :fail

rem ---- 5. Web app packages -----------------------------------------------
echo [5/6] Installing web app packages ^(first time: a few minutes^)...
pushd frontend
call npm install --no-audit --no-fund --loglevel=error
if errorlevel 1 (
  popd
  goto :fail
)
popd

rem ---- 6. Database ----------------------------------------------------------
echo [6/6] Creating the database
"venv\Scripts\python.exe" scripts\init_db.py || goto :fail

echo.
"venv\Scripts\python.exe" scripts\check_env.py
echo.
echo  =====================================================
echo   Setup complete. Start SeatWise with run.bat
echo  =====================================================
echo.
pause
exit /b 0

:fail
echo.
echo  Setup did not finish. Read the message above, fix it, then run setup.bat again.
echo  See docs\10_TROUBLESHOOTING.md for common problems.
echo.
pause
exit /b 1
