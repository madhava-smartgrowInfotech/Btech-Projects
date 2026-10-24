@echo off
setlocal
cd /d "%~dp0"
echo === ATHENA ===

rem Run setup on a fresh checkout or when the environment is incomplete.
set NEEDS_SETUP=0
if not exist venv\Scripts\python.exe set NEEDS_SETUP=1
if not exist frontend\node_modules set NEEDS_SETUP=1
if not exist models\triage_model.joblib set NEEDS_SETUP=1
if "%NEEDS_SETUP%"=="0" (
  venv\Scripts\python.exe -c "import fastapi, xgboost, shap, rapidocr_onnxruntime" >nul 2>&1
  if errorlevel 1 set NEEDS_SETUP=1
)
if "%NEEDS_SETUP%"=="1" (
  call setup.bat
  if errorlevel 1 (
    echo Setup failed, see the messages above.
    pause
    exit /b 1
  )
)

echo Starting the API on http://localhost:8307
start "ATHENA API" /min cmd /c "venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8307"
echo Starting the web app on http://localhost:5307
start "ATHENA Web" /min cmd /c "cd frontend && npm run dev"

echo Waiting for the web app.
set /a TRIES=0
:wait
set /a TRIES+=1
powershell -NoProfile -Command "try { (Invoke-WebRequest http://localhost:5307 -UseBasicParsing -TimeoutSec 2).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  if %TRIES% GEQ 40 (
    echo The web app did not start. Close this window and run run.bat again.
    pause
    exit /b 1
  )
  timeout /t 1 /nobreak >nul
  goto wait
)
start "" http://localhost:5307
echo.
echo ATHENA is running. Sign in with clinician@athena.health and Athena@123.
echo Close the two minimised ATHENA windows to stop it.
endlocal
