Write-Host "QuantumFraudGuard - Starting..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet
Write-Host "Launching http://127.0.0.1:5000" -ForegroundColor Green
Start-Process "http://127.0.0.1:5000"
python backend/app.py
