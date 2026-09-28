@echo off
setlocal
cd /d "%~dp0"
if not exist venv ( echo Run setup.bat first. & exit /b 1 )
if not exist frontend\node_modules ( echo Run setup.bat first. & exit /b 1 )
echo Starting TalentTrack API on http://localhost:8209 ...
start "TalentTrack API" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8209"
echo Starting TalentTrack web app on http://localhost:5209 ...
start "TalentTrack Web" cmd /k "cd /d %~dp0frontend && npm run dev"
echo Waiting for the API to come up...
for /l %%i in (1,1,60) do (
  powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8209/api/health -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" && goto ready
  timeout /t 1 /nobreak >nul
)
:ready
timeout /t 3 /nobreak >nul
start "" http://localhost:5209
echo TalentTrack is running. Close the two console windows to stop it.
endlocal
