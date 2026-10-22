@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker CLI was not found.
  echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
echo Building LearnPathIQ image...
docker build -t learnpathiq .
if errorlevel 1 (
  echo [ERROR] Docker build failed. See error above.
  pause
  exit /b 1
)
echo Running LearnPathIQ at http://localhost:8000 ...
docker run --rm -p 8000:8000 learnpathiq
if errorlevel 1 (
  echo [ERROR] Container exited with an error.
  pause
  exit /b 1
)
pause
