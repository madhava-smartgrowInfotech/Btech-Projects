$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "SecurePay AI - starting..." -ForegroundColor Cyan

$backend = "8304"; $frontend = "5304"
if (Test-Path .env) {
  foreach ($line in Get-Content .env) {
    if ($line -match '^BACKEND_PORT=(\d+)') { $backend = $Matches[1] }
    if ($line -match '^FRONTEND_PORT=(\d+)') { $frontend = $Matches[1] }
  }
}

pip install -r requirements.txt --quiet
if (-not (Test-Path frontend\node_modules)) { Push-Location frontend; npm install; Pop-Location }

$env:BACKEND_PORT = $backend
Start-Process powershell -ArgumentList "-NoExit","-Command","`$env:BACKEND_PORT='$backend'; python backend\app.py"
Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location frontend; npm run dev -- --host 127.0.0.1"
Start-Sleep -Seconds 6
Write-Host "Frontend  http://127.0.0.1:$frontend" -ForegroundColor Green
Write-Host "Backend   http://127.0.0.1:$backend  (old Flask page at /)" -ForegroundColor Green
Start-Process "http://127.0.0.1:$frontend"
