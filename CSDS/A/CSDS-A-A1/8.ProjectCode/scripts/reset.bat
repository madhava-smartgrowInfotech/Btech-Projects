@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
echo This deletes all accounts, uploaded policies, conversations and claim checks on this computer,
echo then recreates the demo account and the sample policies. Your .env and AI response cache are kept.
set /p CONFIRM=Type RESET to continue:
if defined CONFIRM set "CONFIRM=%CONFIRM: =%"
if /i not "%CONFIRM%"=="RESET" (
  echo Cancelled.
  exit /b 0
)
call stop.bat
if exist "data\app.db" del /q "data\app.db"
if exist "data\app.db-wal" del /q "data\app.db-wal"
if exist "data\app.db-shm" del /q "data\app.db-shm"
if exist "data\chroma" rmdir /s /q "data\chroma"
if exist "data\uploads" rmdir /s /q "data\uploads"
if exist "data\pages" rmdir /s /q "data\pages"
"venv\Scripts\python.exe" scripts\init_app.py
echo Reset complete. Start PolicyLens with run.bat
pause
