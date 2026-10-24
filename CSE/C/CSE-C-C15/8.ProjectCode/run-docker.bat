@echo off
REM SentinelFlow Docker launcher.
setlocal EnableExtensions
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker was not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

echo Building SentinelFlow image ...
docker build -t sentinelflow .
if errorlevel 1 (
  echo [ERROR] Docker build failed. See the error above.
  pause
  exit /b 1
)

echo Starting SentinelFlow container on http://localhost:5000 ...
start "" "http://localhost:5000/"
docker run --rm -p 127.0.0.1:5000:5000 sentinelflow
set EXITCODE=%errorlevel%
echo.
echo Container stopped (exit code %EXITCODE%).
pause
exit /b %EXITCODE%
