@echo off
REM Start HospiSense: API on 8207, web app on 5207, then open the browser.
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo Run setup.bat first. & exit /b 1)
if not exist frontend\node_modules (echo Run setup.bat first. & exit /b 1)
if not exist .env call venv\Scripts\python scripts\init_env.py

start "HospiSense API" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8207"
start "HospiSense Web" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Waiting for the API to start...
:wait
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8207/api/health -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 goto wait
start "" http://localhost:5207
echo HospiSense is running at http://localhost:5207  (API http://127.0.0.1:8207/docs)
