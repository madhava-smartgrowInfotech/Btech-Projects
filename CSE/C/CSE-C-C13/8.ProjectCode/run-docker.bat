@echo off
setlocal
REM ============================================================
REM  CipherVault - Docker launcher (Windows)
REM  Recommended if Docker Desktop is installed.
REM ============================================================
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] Docker CLI was not found.
  echo.
  echo Please install Docker Desktop from:
  echo   https://www.docker.com/products/docker-desktop/
  echo Then start Docker Desktop and double-click run-docker.bat again.
  echo.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERROR] Docker is installed but not running.
  echo Please start Docker Desktop and wait until it says "running",
  echo then double-click run-docker.bat again.
  echo.
  pause
  exit /b 1
)

echo [*] Building and starting CipherVault with Docker...
echo     App: http://localhost:8413
echo.
docker compose up --build
set EXITCODE=%ERRORLEVEL%
echo.
if not "%EXITCODE%"=="0" (
  echo [ERROR] Docker Compose exited with code %EXITCODE%. See the error above.
  pause
  exit /b %EXITCODE%
)
pause
