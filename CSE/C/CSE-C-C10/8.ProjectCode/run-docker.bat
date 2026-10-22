@echo off
REM VenturePulse Docker launcher (Recommended if Docker Desktop is installed)
cd /d "%~dp0"
echo ============================================
echo  VenturePulse - Docker startup
echo ============================================
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker was not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker is installed but not running. Please start Docker Desktop and retry.
  pause
  exit /b 1
)
echo Building image (first run may take a while)...
docker build -t venturepulse:latest .
if errorlevel 1 (
  echo [ERROR] Docker build failed. See the error above.
  pause
  exit /b 1
)
echo Starting application on http://localhost:8000 ...
docker run --rm -p 8000:8000 --name venturepulse-app venturepulse:latest
echo.
echo Container stopped.
pause
