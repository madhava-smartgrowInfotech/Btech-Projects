@echo off
setlocal EnableExtensions
REM VeriVision AI - Docker launcher
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker was not found.
  echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
  echo Then make sure Docker Desktop is running and try again.
  pause
  exit /b 1
)

echo Building VeriVision AI image ...
docker build -t verivision-ai .
if errorlevel 1 (
  echo [ERROR] Docker build failed. See the error above.
  pause
  exit /b 1
)

echo Starting VeriVision AI on http://localhost:5000 ...
docker run --rm -p 127.0.0.1:5000:5000 --name verivision-ai verivision-ai
if errorlevel 1 (
  echo [ERROR] Docker run failed. See the error above.
  pause
  exit /b 1
)

pause
