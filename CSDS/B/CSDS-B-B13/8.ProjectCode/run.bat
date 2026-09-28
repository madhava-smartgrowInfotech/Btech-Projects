@echo off
REM Start APISentry: two practice targets + backend + frontend, then open the browser.
setlocal
cd /d "%~dp0"

REM --- load ports from .env (fallback to defaults) ---
set "BACKEND_PORT=8213"
set "FRONTEND_PORT=5213"
set "DEMOPAY_PORT=12130"
set "VULNBANK_PORT=12131"
if exist ".env" (
  for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
    if /i "%%A"=="BACKEND_PORT"  set "BACKEND_PORT=%%B"
    if /i "%%A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%B"
    if /i "%%A"=="DEMOPAY_PORT"  set "DEMOPAY_PORT=%%B"
    if /i "%%A"=="VULNBANK_PORT" set "VULNBANK_PORT=%%B"
  )
)

if not exist "venv\Scripts\python.exe" (
  echo venv not found. Run setup.bat first.
  exit /b 1
)

echo Starting DemoPay practice target on port %DEMOPAY_PORT% ...
start "APISentry DemoPay" cmd /c "venv\Scripts\python.exe targets\demopay.py"

echo Starting VulnBank practice target on port %VULNBANK_PORT% ...
start "APISentry VulnBank" cmd /c "venv\Scripts\python.exe targets\vulnbank.py"

echo Starting backend on port %BACKEND_PORT% ...
start "APISentry Backend" cmd /c "cd backend && ..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"

echo Starting frontend on port %FRONTEND_PORT% ...
start "APISentry Frontend" cmd /c "cd frontend && npm run dev"

echo Waiting for the frontend to come up ...
timeout /t 6 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"

echo.
echo APISentry is starting. Open http://localhost:%FRONTEND_PORT%
echo Demo login: demo@apisentry.local / demo12345
echo Close the four opened windows to stop the services.
endlocal
