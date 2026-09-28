@echo off
setlocal
cd /d "%~dp0"
echo === TalentTrack setup ===
where python >nul 2>nul || (echo Python 3.11+ is required: https://www.python.org/downloads/ & exit /b 1)
where npm >nul 2>nul || (echo Node.js LTS is required: https://nodejs.org/ & exit /b 1)
if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || exit /b 1
)
call venv\Scripts\python -m pip install --upgrade pip -q
call venv\Scripts\pip install -r backend\requirements.txt || exit /b 1
if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example - add your GEMINI_API_KEY to enable AI interviews.
)
if not exist models\resume_clf.joblib (
  echo Training the resume role classifier...
  call venv\Scripts\python ml\train_resume.py || exit /b 1
)
echo Preparing the database and sample data...
pushd backend
call ..\venv\Scripts\python -m app.seed || (popd & exit /b 1)
popd
echo Installing frontend packages...
pushd frontend
call npm install --no-audit --no-fund || (popd & exit /b 1)
popd
where g++ >nul 2>nul || echo NOTE: g++ not on PATH - C++ submissions need it (winget install BrechtSanders.WinLibs.POSIX.UCRT).
where javac >nul 2>nul || echo NOTE: javac not on PATH - Java submissions need JDK 17.
echo.
echo Setup complete. Start the app with run.bat
endlocal
