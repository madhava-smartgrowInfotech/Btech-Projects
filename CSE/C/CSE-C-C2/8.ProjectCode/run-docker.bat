@echo off
setlocal EnableExtensions
REM StoryVox Docker launcher. Recommended if Docker Desktop is installed.
cd /d "%~dp0"
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker was not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
echo Building the StoryVox image...
docker build -t storyvox:latest .
if errorlevel 1 (
  echo [ERROR] Docker build failed. See the error above.
  pause
  exit /b 1
)
echo Starting StoryVox at http://localhost:8402 ...
docker run --rm -p 127.0.0.1:8402:8402 -v "%cd%\data:/app/data" storyvox:latest
set EXITCODE=%errorlevel%
echo.
echo Container stopped (exit code %EXITCODE%).
pause
exit /b %EXITCODE%
