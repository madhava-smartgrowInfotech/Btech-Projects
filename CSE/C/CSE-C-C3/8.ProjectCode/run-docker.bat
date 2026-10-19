@echo off
REM ParkSure Docker launcher (recommended if Docker Desktop is installed).
setlocal
cd /d "%~dp0"
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker was not found on PATH.
  echo Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  echo Then run this file again.
  pause
  exit /b 1
)
echo Building ParkSure image...
docker compose build
if errorlevel 1 (
  echo [ERROR] docker compose build failed. See the error above.
  pause
  exit /b 1
)
echo Starting ParkSure at http://localhost:8000 ...
start "" "http://localhost:8000"
docker compose up
echo.
echo ParkSure container stopped.
pause
