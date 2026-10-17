@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "BACKEND_PORT=8302"
set "FRONTEND_PORT=5302"
if exist ".env" for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
  if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
)
for %%p in (%BACKEND_PORT% %FRONTEND_PORT%) do (
  for /f "tokens=5" %%i in ('netstat -ano ^| findstr /r /c:":%%p .*LISTENING"') do (
    echo Stopping process %%i on port %%p
    taskkill /f /t /pid %%i >nul 2>&1
  )
)
echo ResQAI stopped.
