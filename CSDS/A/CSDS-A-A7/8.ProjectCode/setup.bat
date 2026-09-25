@echo off
setlocal
cd /d "%~dp0"

echo === SHEGUARD setup ===

if not exist ".env" (
    echo Creating .env from .env.example - fill in your API keys before running.
    copy ".env.example" ".env" >nul
)

echo Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
)

echo Installing backend dependencies...
call venv\Scripts\pip.exe install -r backend\requirements.txt
if errorlevel 1 goto :error

echo Installing frontend dependencies...
pushd frontend
call npm install
if errorlevel 1 goto :frontend_error
popd

echo.
echo Setup complete. Run run.bat to start SHEGUARD.
goto :eof

:frontend_error
popd
:error
echo Setup failed - see the error above.
exit /b 1
