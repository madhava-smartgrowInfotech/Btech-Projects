@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem Stops only the processes listening on PolicyLens's own ports.
set "BACKEND_PORT=8101"
set "FRONTEND_PORT=5101"
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="BACKEND_PORT" set "BACKEND_PORT=%%b"
    if /i "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%b"
  )
)
set "FOUND="
for %%P in (%BACKEND_PORT% %FRONTEND_PORT%) do (
  for /f "tokens=5" %%i in ('netstat -ano ^| findstr /r /c:":%%P .*LISTENING"') do (
    taskkill /F /T /PID %%i >nul 2>&1 && echo Stopped the process on port %%P ^(PID %%i^)
    set "FOUND=1"
  )
)
if not defined FOUND echo PolicyLens was not running.
exit /b 0
