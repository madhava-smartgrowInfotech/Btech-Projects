@echo off
setlocal
cd /d "%~dp0"
echo === ATHENA setup ===

rem 1. Python environment. A venv copied from another machine points at a missing Python, so rebuild it.
if exist venv\Scripts\python.exe (
  venv\Scripts\python.exe -c "import sys" >nul 2>&1
  if errorlevel 1 (
    echo Existing venv is broken, rebuilding it.
    rmdir /s /q venv
  )
)
if not exist venv\Scripts\python.exe (
  echo Creating Python environment.
  python -m venv venv
  if errorlevel 1 (
    echo Python 3.11 or newer is required and was not found on PATH.
    exit /b 1
  )
)
echo Installing Python packages. The first run takes a few minutes.
venv\Scripts\python.exe -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo Package install failed. Check your internet connection and run setup.bat again.
  exit /b 1
)

rem 2. Data and model, only when missing.
if not exist data\sample\triage_synthetic.csv venv\Scripts\python.exe ml\make_data.py
if not exist models\triage_model.joblib (
  echo Training the triage model.
  venv\Scripts\python.exe ml\train.py >nul
)
if not exist data\sample_reports\expected.json venv\Scripts\python.exe scripts\make_sample_reports.py

rem 3. Frontend packages.
if not exist frontend\node_modules (
  echo Installing frontend packages.
  pushd frontend
  call npm install --no-audit --no-fund
  if errorlevel 1 (
    popd
    echo npm install failed. Node.js 18 or newer is required.
    exit /b 1
  )
  popd
)
echo Setup finished.
exit /b 0
