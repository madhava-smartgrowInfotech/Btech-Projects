@echo off
REM Starts the MediQueue backend (8215) and frontend (5215) and opens the browser
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first & exit /b 1)
start "MediQueue API :8215" cmd /k "cd backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8215"
start "MediQueue Web :5215" cmd /k "cd frontend && npm run dev"
timeout /t 6 /nobreak >nul
start http://localhost:5215
echo MediQueue is starting: http://localhost:5215  (API http://localhost:8215/docs)
