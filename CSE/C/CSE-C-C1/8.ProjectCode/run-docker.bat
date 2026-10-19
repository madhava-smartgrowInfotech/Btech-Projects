@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================================
echo  AegisBallot - Docker Run
echo ========================================================

where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
echo [OK] Docker found
docker --version

echo [INFO] Building Docker image aegisballot ...
docker build -t aegisballot .
if errorlevel 1 (
  echo [ERROR] Docker build failed
  pause
  exit /b 1
)

REM Stop existing container if running (free port)
docker ps | findstr "aegisballot_app" >nul 2>&1
if not errorlevel 1 (
  echo [INFO] Existing container aegisballot_app is running - stopping ...
  docker stop aegisballot_app
  timeout /t 2 >nul
)

echo [INFO] Running container on http://localhost:8000 ...
docker run --rm -p 127.0.0.1:8000:8000 --name aegisballot_app aegisballot
if errorlevel 1 (
  echo [ERROR] Docker run failed.
  echo         If error is "port is already allocated" or 8000 in use:
  echo         Run: docker stop aegisballot_app
  echo         Or:  netstat -ano ^| findstr :8000  and kill the PID
  pause
  exit /b 1
)

pause
