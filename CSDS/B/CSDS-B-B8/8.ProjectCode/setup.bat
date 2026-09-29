@echo off
REM CareWatch one-time setup: Python venv + packages, frontend packages.
cd /d "%~dp0"
where py >nul 2>nul && (py -3.11 -m venv venv || python -m venv venv) || python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cd frontend
call npm install
cd ..
if not exist .env copy .env.example .env
echo.
echo Setup complete. Start CareWatch with run.bat
pause
