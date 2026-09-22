@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "API_PORT=8204"
set "FRONTEND_PORT=5204"
if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        if /i "%%A"=="API_PORT" set "API_PORT=%%B"
        if /i "%%A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%B"
    )
)

echo Stopping UPI Guardian (ports %API_PORT% and %FRONTEND_PORT% only)...
powershell -NoProfile -Command ^
  "$ports = @(%API_PORT%, %FRONTEND_PORT%);" ^
  "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort } | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('  stopped process on port ' + $_.LocalPort) };" ^
  "Get-CimInstance Win32_Process -Filter \"Name='cloudflared.exe'\" | Where-Object { $_.CommandLine -match 'localhost:%FRONTEND_PORT%' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host '  stopped phone tunnel' }"
echo Done.
endlocal
