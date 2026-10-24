@echo off
setlocal
cd /d "%~dp0"
echo.
echo === BotGraph ===

if not exist ".env" copy ".env.example" ".env" >nul
set "BACKEND_PORT="
set "FRONTEND_PORT="
for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b /c:"BACKEND_PORT=" /c:"FRONTEND_PORT=" ".env"`) do set "%%a=%%b"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8309"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=5309"

rem First run, or a broken environment: run setup.
if not exist ".venv\Scripts\python.exe" goto dosetup
".venv\Scripts\python.exe" -c "import fastapi, torch, networkx, bcrypt, jwt" >nul 2>&1
if errorlevel 1 goto dosetup
if not exist "frontend\node_modules" goto dosetup
goto start

:dosetup
call "%~dp0setup.bat"
if errorlevel 1 exit /b 1

:start
echo Starting the API on port %BACKEND_PORT% and the web app on port %FRONTEND_PORT%...
start "BotGraph API" /min cmd /c ".venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "BotGraph web app" /min cmd /c "cd /d frontend && npm run dev"

set /a tries=0
:wait
set /a tries+=1
powershell -NoProfile -Command "try { $null = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:%BACKEND_PORT%/api/health -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto ready
if %tries% GEQ 45 goto ready
ping -n 3 127.0.0.1 >nul
goto wait

:ready
ping -n 3 127.0.0.1 >nul
echo.
echo BotGraph is running:  http://localhost:%FRONTEND_PORT%
echo Demo logins (password Demo@1234):  moderator@botgraph.app   analyst@botgraph.app
echo Close the two minimised windows named BotGraph to stop it.
start "" "http://localhost:%FRONTEND_PORT%"
exit /b 0
