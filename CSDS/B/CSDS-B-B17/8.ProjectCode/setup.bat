@echo off
setlocal
cd /d "%~dp0"
echo === CallSense setup ===

where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)

if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
echo Installing Python packages ^(PyTorch CPU, faster-whisper; first run takes a few minutes^)...
venv\Scripts\python -m pip install --upgrade pip >nul
venv\Scripts\pip install -r backend\requirements.txt || exit /b 1

if not exist .env (
  echo Creating .env from .env.example with a random JWT secret - add your GEMINI_API_KEY to it.
  venv\Scripts\python -c "import secrets,pathlib;t=pathlib.Path('.env.example').read_text();pathlib.Path('.env').write_text(t.replace('change-me-to-a-long-random-string',secrets.token_hex(32)))"
)

echo Installing frontend packages...
pushd frontend
call npm install || (popd & exit /b 1)
popd

if not exist models\intent.joblib (
  echo Training the intent and sentiment models ^(about a minute^)...
  venv\Scripts\python ml\train.py || exit /b 1
)
if not exist data\sample\calls\refund_request.flac (
  echo Generating the sample call recordings...
  venv\Scripts\python scripts\generate_sample_calls.py || exit /b 1
)

echo Downloading the speech models ^(faster-whisper small + wav2vec2 emotion, about 850 MB, once^)...
venv\Scripts\python -c "import sys;sys.path.insert(0,'backend');from app.services import speech;speech.whisper();speech.emotion_model();print('Speech models ready')" || exit /b 1

echo.
echo Setup complete. Start CallSense with run.bat
endlocal
