@echo off
REM PeerScope Docker launcher.
cd /d "%~dp0"
where docker >nul 2>nul
if errorlevel 1 (
  echo [PeerScope] Docker was not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
echo [PeerScope] Building image...
docker build -t peerscope .
if errorlevel 1 (
  echo [PeerScope] Docker build FAILED. See the error above.
  pause
  exit /b 1
)
echo [PeerScope] API running on http://localhost:8408 ... the web app is started separately with run.bat
start "" "http://localhost:8408/docs"
docker run --rm -p 8408:8408 peerscope
pause
