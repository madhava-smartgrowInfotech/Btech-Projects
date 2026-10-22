@echo off
setlocal EnableExtensions
REM FinSight AI - Docker launcher
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker CLI was not found.
  echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

echo Building FinSight AI image...
docker build -t finsight-ai .
if errorlevel 1 (
  echo [ERROR] Docker build failed. See the error above.
  pause
  exit /b 1
)

echo Starting FinSight AI on http://localhost:5000 ...
docker run --rm -p 5000:5000 --name finsight-ai finsight-ai
if errorlevel 1 (
  echo [ERROR] Docker run failed. Is Docker Desktop running?
  pause
  exit /b 1
)
pause
