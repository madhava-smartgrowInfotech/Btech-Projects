@echo off
echo ============================================================
echo  QuantumFraudGuard - IEEE 2026 Prototype
echo  Fraud Detection using Quantum-Assisted RBM
echo ============================================================
echo.
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.
echo Starting backend on http://127.0.0.1:5000 ...
echo   - Frontend served at /
echo   - API at /api/health , /api/train , /api/predict_single etc.
echo   - Models pre-trained (classical / SA / QA) ready for demo
echo.
start http://127.0.0.1:5000
python backend/app.py
pause
