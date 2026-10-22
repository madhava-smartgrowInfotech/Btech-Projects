@echo off
setlocal EnableExtensions
REM VeriVision AI - Docker launcher (API on 8414, web app on 5414, both on localhost only)
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker was not found.
  echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
  echo Then make sure Docker Desktop is running and try again.
  pause
  exit /b 1
)

echo Building and starting VeriVision AI ...
start "" "http://localhost:5414"
docker compose up --build
if errorlevel 1 (
  echo [ERROR] Docker Compose failed. See the error above.
  echo Make sure Docker Desktop is running.
  pause
  exit /b 1
)

pause
