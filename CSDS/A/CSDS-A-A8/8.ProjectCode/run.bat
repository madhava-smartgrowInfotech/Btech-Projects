@echo off
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first & exit /b 1)
start "BioSight API" cmd /k "venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8108"
start "BioSight UI" cmd /k "cd frontend && npm run dev"
timeout /t 6 /nobreak >nul
start http://localhost:5108
