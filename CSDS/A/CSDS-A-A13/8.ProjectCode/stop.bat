@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "API_PORT=8113"
set "WEB_PORT=5113"
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="API_PORT" set "API_PORT=%%b"
    if /i "%%a"=="WEB_PORT" set "WEB_PORT=%%b"
  )
)

rem Stop only the programs listening on SeatWise's own ports.
set "STOPPED="
for %%p in (%API_PORT% %WEB_PORT%) do (
  for /f "tokens=5" %%i in ('netstat -ano ^| findstr /r /c:":%%p *[^ ]* *LISTENING"') do (
    taskkill /pid %%i /t /f >nul 2>nul && set "STOPPED=1" && echo Stopped the process on port %%p ^(PID %%i^)
  )
)
if not defined STOPPED echo SeatWise was not running.
timeout /t 2 >nul
