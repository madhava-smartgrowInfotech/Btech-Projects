@echo off
cd /d "%~dp0"
echo === BioSight setup ===
if not exist venv (
  python -m venv venv || (echo Python 3.11+ is required & exit /b 1)
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
if not exist .env copy .env.example .env
cd frontend
call npm install
cd ..
echo === Setup complete. Start the app with run.bat ===
