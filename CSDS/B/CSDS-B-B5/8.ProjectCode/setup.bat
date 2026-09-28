@echo off
REM SignBridge one-time setup: Python venv + packages, offline speech model, frontend packages.
cd /d "%~dp0"

where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)

if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example - put your GEMINI_API_KEY there for online sentence polishing.
)

if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || exit /b 1

echo Downloading the offline speech model (one time, needs internet)...
python -c "import os; from dotenv import load_dotenv; load_dotenv(); from faster_whisper import WhisperModel; WhisperModel(os.getenv('WHISPER_MODEL', 'small'), device='cpu', compute_type='int8'); print('speech model ready')" || exit /b 1

echo Installing frontend packages...
cd frontend
call npm install || exit /b 1
cd ..

echo.
echo Setup complete. Start SignBridge with run.bat
