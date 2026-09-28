@echo off
REM Starts MediQueue and a Cloudflare quick tunnel so it can be opened on a phone over HTTPS
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first & exit /b 1)
where cloudflared >nul 2>nul || if not exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
  echo Installing cloudflared...
  winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
)
start "MediQueue API :8215" cmd /k "cd backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8215"
start "MediQueue Web :5215" cmd /k "cd frontend && set MEDIQUEUE_TUNNEL=1&& npm run dev"
timeout /t 6 /nobreak >nul
echo Starting the tunnel - the phone link appears below in a few seconds...
venv\Scripts\python scripts\phone_tunnel.py
