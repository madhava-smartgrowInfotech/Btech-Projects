@echo off
setlocal
cd /d "%~dp0"
echo === CivicPulse setup ===

set "PY=python"
py -3.11 --version >nul 2>&1 && set "PY=py -3.11"

if not exist venv\Scripts\python.exe (
    echo Creating Python virtual environment...
    %PY% -m venv venv || goto :error
)
venv\Scripts\python -m pip install --upgrade pip -q
echo Installing backend packages (a few minutes the first time)...
venv\Scripts\python -m pip install -r backend\requirements.txt -q || goto :error

if not exist .env (
    copy .env.example .env >nul
    for /f %%s in ('venv\Scripts\python -c "import secrets;print(secrets.token_hex(32))"') do set "SECRET=%%s"
    powershell -NoProfile -Command "(Get-Content .env) -replace '^JWT_SECRET=.*','JWT_SECRET=%SECRET%' | Set-Content -Encoding ascii .env"
    echo Created .env - open it and paste your GEMINI_API_KEY.
)

if not exist data\raw\civiccomp_hien.csv.gz (
    echo Downloading datasets...
    venv\Scripts\python scripts\download_data.py || goto :error
)
if not exist models\text_models.joblib (
    echo Training models...
    venv\Scripts\python ml\train.py || goto :error
)

echo Installing frontend packages...
pushd frontend
call npm install || (popd & goto :error)
popd

echo.
echo Setup complete. Start CivicPulse with run.bat
exit /b 0

:error
echo.
echo Setup failed - see the message above.
exit /b 1
