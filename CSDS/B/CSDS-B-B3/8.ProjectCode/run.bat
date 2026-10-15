@echo off
setlocal
cd /d "%~dp0"
title SkillVerse launcher

rem ---- ports (defaults match the batch assignment; override in .env) ----
set BACKEND_PORT=8203
set FRONTEND_PORT=5203
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"BACKEND_PORT=" /c:"FRONTEND_PORT=" ".env" 2^>nul`) do set %%A=%%B

where python >nul 2>nul || (echo Python was not found. Install Python 3.10+ and try again.& pause & exit /b 1)
where npm >nul 2>nul || (echo Node.js/npm was not found. Install Node 18+ and try again.& pause & exit /b 1)

if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul

echo [1/3] Checking Python packages...
python -c "import fastapi, uvicorn, sqlalchemy, bcrypt, sklearn, networkx, pandas" 2>nul || python -m pip install -r requirements.txt
if errorlevel 1 (echo pip install failed.& pause & exit /b 1)

echo [2/3] Checking frontend packages...
if not exist "frontend\node_modules" (
  pushd frontend
  call npm install
  popd
)

echo [3/3] Starting servers...
start "SkillVerse API  (port %BACKEND_PORT%)" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "SkillVerse UI   (port %FRONTEND_PORT%)" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 127.0.0.1"

timeout /t 6 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
echo.
echo   App:  http://localhost:%FRONTEND_PORT%
echo   API:  http://localhost:%BACKEND_PORT%/docs
echo   (The original Streamlit app still works:  streamlit run app.py)
echo.
echo Close the two server windows to stop.
endlocal
