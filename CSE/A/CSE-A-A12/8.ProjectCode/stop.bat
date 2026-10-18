@echo off
rem Stops the windows started by run.bat
taskkill /FI "WINDOWTITLE eq PneumoDetect API*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq PneumoDetect UI*" /T /F >nul 2>nul
echo PneumoDetect stopped.
