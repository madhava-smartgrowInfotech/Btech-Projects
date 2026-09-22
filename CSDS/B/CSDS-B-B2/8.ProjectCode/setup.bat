@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title SignalScout setup
echo.
echo  SignalScout setup - installs everything this folder needs. Safe to run again.
echo.

echo [1/8] Checking Python 3.11 ...
set "PY="
py -3.11 --version >nul 2>&1 && set "PY=py -3.11"
if not defined PY (
  python --version 2>nul | findstr /r /c:"Python 3\.11\." >nul && set "PY=python"
)
if not defined PY (
  echo   Python 3.11 was not found.
  echo   Install it with:  winget install -e --id Python.Python.3.11
  echo   or from https://www.python.org/downloads/ - tick "Add python.exe to PATH". Then run setup.bat again.
  goto :fail
)
echo   using: %PY%

echo [2/8] Checking Node.js ...
node --version >nul 2>&1
if errorlevel 1 (
  echo   Node.js was not found.
  echo   Install the LTS version with:  winget install -e --id OpenJS.NodeJS.LTS
  echo   or from https://nodejs.org/ - then open a new window and run setup.bat again.
  goto :fail
)
for /f %%v in ('node --version') do echo   found Node.js %%v

echo [3/8] Python environment (venv) ...
if not exist "venv\Scripts\python.exe" (
  %PY% -m venv venv || goto :fail
)
"venv\Scripts\python.exe" -m pip install --upgrade pip --quiet || goto :fail
echo   installing Python packages (first run downloads about 400 MB, including PyTorch CPU) ...
"venv\Scripts\python.exe" -m pip install -r backend\requirements.txt --quiet || goto :fail

echo [4/8] Configuration (.env) ...
"venv\Scripts\python.exe" scripts\sync_env.py || goto :fail

echo [5/8] Datasets ...
"venv\Scripts\python.exe" scripts\download_data.py || goto :fail

echo [6/8] Phone HTTPS link tool (cloudflared) ...
"venv\Scripts\python.exe" scripts\get_tools.py
if errorlevel 1 echo   continuing without it - the phone probe will not be reachable until it is installed

echo [7/8] Web app packages and build ...
pushd frontend
call npm install --no-fund --no-audit || (popd & goto :fail)
call npm run build || (popd & goto :fail)
popd

echo [8/8] Trained models ...
if exist "models\zone_classifier.joblib" if exist "models\radio_estimate.joblib" if exist "models\gp_signal.joblib" (
  echo   models present
  goto :done
)
echo   training models from the datasets (about 6 minutes) ...
"venv\Scripts\python.exe" ml\train_all.py || goto :fail

:done
echo.
echo  Setup complete. Start SignalScout with run.bat
echo  Check keys and connections any time with:  venv\Scripts\python.exe scripts\check_env.py
echo.
pause
exit /b 0

:fail
echo.
echo  Setup stopped because of the error above. See docs\10_TROUBLESHOOTING.md for fixes.
echo.
pause
exit /b 1
