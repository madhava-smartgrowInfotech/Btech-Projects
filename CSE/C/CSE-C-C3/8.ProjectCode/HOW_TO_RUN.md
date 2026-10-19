# ParkSure — How to Run (non-coder friendly)

ParkSure has two parts that run together: a **backend** (Python, port **8403**) and a **frontend** (React, port **5403**). `run.bat` starts both.

## 1. Prerequisites
- **Python 3.11 or newer** (tested with 3.11–3.14): https://www.python.org/downloads/
  - During install, tick **"Add python.exe to PATH"**.
- **Node.js 20 or newer** (includes npm): https://nodejs.org/
- A modern browser (Chrome / Edge / Firefox).
- Optional (Method B only): **Docker Desktop**: https://www.docker.com/products/docker-desktop/
- Stripe keys are **optional**. Without them ParkSure uses a built-in demo checkout so every flow still works. To take real test payments, set `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` and run with Stripe test mode.

Demo logins (created automatically on first run):
- Admin: `admin@parksure.app` / `admin123`
- Driver: `driver1@parksure.app` / `driver123`

## 2. Method A — Automatic (recommended): double-click `run.bat`
1. Open this project folder in File Explorer.
2. Double-click **`run.bat`**.
3. What appears: a launcher window that checks Python and Node, installs the Python and npm packages (the first run takes a few minutes), then opens two more windows: **ParkSure Backend** and **ParkSure Frontend**.
4. Your browser opens automatically to **http://127.0.0.1:5403**. If it doesn't, type that address manually.
5. How to know it worked: you see the ParkSure landing page with a rotating 3D shape and a search box.
6. How to stop: close the **ParkSure Backend** and **ParkSure Frontend** windows.

## 3. Method B — Docker (backend only)
```powershell
docker compose build
docker compose up
```
Docker runs the backend and its original built-in pages on **http://localhost:8000**. It does not include the new React frontend; use Method A or C for that.

## 4. Method C — Manual (copy-paste, two terminals)
Terminal 1, the backend:
```powershell
cd "D:\abstracts\Madhav\CSE\C\CSE-C-C3\8.ProjectCode"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8403
```
Terminal 2, the frontend:
```powershell
cd "D:\abstracts\Madhav\CSE\C\CSE-C-C3\8.ProjectCode\frontend"
npm install
npm run dev
```
Open **http://127.0.0.1:5403**. The frontend forwards every `/api` call to the backend on 8403, so you never open 8403 yourself.

Strategy Insights can also be computed from the command line:
```powershell
python scripts/compute_buffer_strategy_metrics.py --window-days 60
```

## 5. Checking it works
- `python scripts/smoke_test.py` runs the whole booking flow against a throwaway database and prints `SMOKE-OK`.
- `python scripts/capture_screens.py` (needs `pip install playwright` and `playwright install chromium`, with the app running) saves a PNG of every screen to `docs/screenshots/`.
- `cd frontend && npm run build` produces a production build in `frontend/dist`.

## 6. Troubleshooting
- **"Python was not found" / "Node.js was not found"**: install it from the link above (tick "Add to PATH" for Python), then reopen the terminal / double-click run.bat again.
- **Windows Defender / SmartScreen blocks run.bat** ("Unknown publisher"): click **More info → Run anyway**. The file is a plain text launcher; right-click → Edit to inspect it.
- **Port already in use** (`address already in use :8403` or `Port 5403 is already in use`): another program uses that port. Close it. The frontend is set to refuse a different port on purpose, because the backend address is fixed.
- **The page loads but says "Cannot reach the ParkSure server"**: the backend window is closed or crashed. Check the **ParkSure Backend** window for the error and run.bat again.
- **Browser doesn't open automatically**: manually open http://127.0.0.1:5403.
- **Dependency install fails**: check internet access, then delete the `.venv` folder (or `frontend\node_modules`) and run `run.bat` again. If a specific package errors, copy the red error text — it names the exact cause.
- **Start fresh data**: stop the backend, delete `parksure.db`, start again. It is re-created and re-seeded with the demo data.
