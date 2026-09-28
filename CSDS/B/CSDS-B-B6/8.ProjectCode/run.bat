@echo off
REM Starts the three hospital FHIR servers, the UniHealth API and the web app, then opens the browser.
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo Run setup.bat first. & exit /b 1)
if not exist frontend\node_modules (echo Run setup.bat first. & exit /b 1)
if not exist .env copy .env.example .env >nul
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8206
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=5206
if "%HOSPITAL_A_PORT%"=="" set HOSPITAL_A_PORT=12061
if "%HOSPITAL_B_PORT%"=="" set HOSPITAL_B_PORT=12062
if "%HOSPITAL_C_PORT%"=="" set HOSPITAL_C_PORT=12063
if not exist data\hospital_a.db venv\Scripts\python scripts\seed_hospitals.py

start "UniHealth - Northbridge General (FHIR)" /min cmd /c "set HOSPITAL_KEY=A&& venv\Scripts\python -m uvicorn hospitals.hospital_app:app --host 127.0.0.1 --port %HOSPITAL_A_PORT%"
start "UniHealth - Riverside Medical (FHIR)" /min cmd /c "set HOSPITAL_KEY=B&& venv\Scripts\python -m uvicorn hospitals.hospital_app:app --host 127.0.0.1 --port %HOSPITAL_B_PORT%"
start "UniHealth - Lakeview Clinic (FHIR)" /min cmd /c "set HOSPITAL_KEY=C&& venv\Scripts\python -m uvicorn hospitals.hospital_app:app --host 127.0.0.1 --port %HOSPITAL_C_PORT%"
start "UniHealth - API" /min cmd /c "venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "UniHealth - Web" /min cmd /c "cd frontend && npm run dev"

echo Waiting for UniHealth to start...
set /a tries=0
:wait
set /a tries+=1
if %tries% gtr 60 (echo The API did not start - check the "UniHealth - API" window. & exit /b 1)
curl -s -o nul http://127.0.0.1:%BACKEND_PORT%/api/health || (timeout /t 1 /nobreak >nul & goto wait)
curl -s -o nul http://127.0.0.1:%FRONTEND_PORT%/ || (timeout /t 1 /nobreak >nul & goto wait)
start http://localhost:%FRONTEND_PORT%
echo UniHealth is running at http://localhost:%FRONTEND_PORT%  (demo password: demo123)
echo Close the five "UniHealth" windows to stop it.
