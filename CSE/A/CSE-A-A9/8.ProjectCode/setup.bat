@echo off
setlocal
cd /d "%~dp0"
echo.
echo === BotGraph setup ===

where python >nul 2>&1
if errorlevel 1 goto nopython
where node >nul 2>&1
if errorlevel 1 goto nonode

if not exist ".env" copy ".env.example" ".env" >nul

rem A virtual environment copied from another machine points at a Python that is not here - rebuild it.
if not exist ".venv\Scripts\python.exe" goto makevenv
".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if errorlevel 1 goto brokenvenv
goto installpy

:brokenvenv
echo The existing .venv does not work on this computer - rebuilding it.
rmdir /s /q ".venv"

:makevenv
echo Creating the Python environment...
python -m venv .venv
if errorlevel 1 goto fail

:installpy
echo Installing Python packages. The first run downloads PyTorch and can take several minutes...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 goto fail

echo Installing the web app packages...
pushd frontend
call npm install --no-audit --no-fund
if errorlevel 1 goto failpop
popd

echo.
echo Setup finished. Start the app with run.bat
exit /b 0

:nopython
echo Python 3.11 or newer was not found. Install it from https://www.python.org/downloads/ and tick Add python.exe to PATH.
exit /b 1

:nonode
echo Node.js was not found. Install the LTS version from https://nodejs.org/ and run setup.bat again.
exit /b 1

:failpop
popd

:fail
echo.
echo Setup did not finish. Read the message above, fix it, and run setup.bat again.
exit /b 1
