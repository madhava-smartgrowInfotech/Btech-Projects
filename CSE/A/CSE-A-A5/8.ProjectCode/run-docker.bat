@echo off
setlocal
chcp 65001 >nul 2>&1
title CipherGuard Shield - Docker

REM Always run from the folder that contains this .bat
cd /d "%~dp0"
echo ============================================================
echo   CipherGuard Shield - Docker Run (recommended if Docker
echo   Desktop is installed)
echo ============================================================
echo Working directory: %CD%
echo.

REM --- Check Docker is available ---
docker --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker was not found.
  echo Install Docker Desktop from: https://www.docker.com/products/docker-desktop/
  echo After installing, start Docker Desktop and wait until it says "Engine running",
  echo then double-click run-docker.bat again.
  echo.
  pause
  exit /b 1
)
echo [OK] Docker found:
docker --version
echo.

REM Check Docker daemon running
docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker is installed but the Docker engine is not running.
  echo Open Docker Desktop and wait until it shows "Engine running" (green icon),
  echo then try again.
  echo.
  pause
  exit /b 1
)

echo [1/3] Building Docker image cipherguard-shield:latest ...
echo   (first build may take 2-4 minutes)
docker build -t cipherguard-shield:latest .
if errorlevel 1 (
  echo.
  echo [ERROR] Docker build failed. See the error above.
  echo Common fixes: ensure Docker Desktop is running, check internet connection,
  echo or try:  docker build --no-cache -t cipherguard-shield:latest .
  echo.
  pause
  exit /b 1
)
echo   Build complete.
echo.

echo [2/3] Starting container (port 8000)...
REM Stop/remove any previous container with same name (ignore errors)
docker rm -f cipherguard-shield >nul 2>&1

REM Prefer compose if available, else plain docker run
docker compose version >nul 2>&1
if %errorlevel%==0 (
  docker compose up -d
  if errorlevel 1 (
    echo [WARN] docker compose up failed, trying docker run...
    docker run -d --name cipherguard-shield -p 8000:8000 cipherguard-shield:latest
  )
) else (
  docker run -d --name cipherguard-shield -p 8000:8000 cipherguard-shield:latest
)
if errorlevel 1 (
  echo.
  echo [ERROR] Failed to start container.
  echo If you see "port is already allocated", close any program using 8000 or run:
  echo   docker rm -f cipherguard-shield
  echo and try again.
  echo.
  pause
  exit /b 1
)
echo   Container started.
echo.

echo [3/3] Waiting for server to be ready...
REM Poll health endpoint for up to ~30s
for /L %%i in (1,1,15) do (
  timeout /t 2 /nobreak >nul
  curl -s http://localhost:8000/api/health >nul 2>&1
  if !errorlevel!==0 goto :ready
  echo   still waiting... (%%i/15)
)
echo [WARN] Health check did not respond quickly. The container may still be starting.
:ready
echo   Server should be up.
echo.

echo Opening http://localhost:8000 in your browser...
start http://localhost:8000
echo.
echo CipherGuard Shield is running at:  http://localhost:8000
echo.
echo Useful commands:
echo   View logs:   docker logs -f cipherguard-shield
echo   Stop:        docker rm -f cipherguard-shield   (or: docker compose down)
echo.
echo This window will stay open - close it when you are done (container keeps running).
echo To stop the container, run:  docker rm -f cipherguard-shield
echo.
pause
