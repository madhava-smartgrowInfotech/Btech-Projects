@echo off
setlocal
cd /d "%~dp0"

where cloudflared >nul 2>nul
if errorlevel 1 (
    echo cloudflared not found. Install it first with:
    echo   winget install --id Cloudflare.cloudflared
    exit /b 1
)

echo Starting SHEGUARD backend on port 8107...
start "SHEGUARD backend" cmd /k "cd /d "%~dp0" && venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8107 --reload"

timeout /t 3 /nobreak >nul

echo Starting SHEGUARD frontend on port 5107...
start "SHEGUARD frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 /nobreak >nul

echo Starting Cloudflare quick tunnel to the frontend (this proxies /api and /ws too)...
echo Look for a line like "https://xxxx.trycloudflare.com" below - open that on your phone.
start "SHEGUARD tunnel" cmd /k "cloudflared tunnel --url http://localhost:5107"

echo.
echo Once the tunnel window shows your https://...trycloudflare.com link, open it on
echo your phone's Chrome browser, then use the browser menu to "Add to Home screen".
