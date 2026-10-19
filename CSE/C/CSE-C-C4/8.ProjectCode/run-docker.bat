@echo off
REM ============================================================
REM  QuantPulse - Docker one-click runner (recommended if
REM  Docker Desktop is installed). Builds and starts backend
REM  (+ dev frontend profile optionally) via Docker.
REM ============================================================
setlocal EnableExtensions
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo  [ERROR] Docker was not found.
  echo  Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  echo  then double-click run-docker.bat again.
  echo.
  pause
  exit /b 1
)

echo  [..] Building + starting QuantPulse with Docker ...
docker compose up --build
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo  [ERROR] docker compose failed with code %EXITCODE% (see above).
  echo.
  pause
  exit /b %EXITCODE%
)
pause
