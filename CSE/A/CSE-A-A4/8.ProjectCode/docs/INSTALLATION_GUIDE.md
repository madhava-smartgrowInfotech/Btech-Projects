# Installation Guide — SecurePay AI

## 1. Prerequisites Check

Open PowerShell and run:

```powershell
python --version   # expect 3.11.x
pip --version      # expect 24+
```

If `python` not found, install from https://www.python.org/downloads/ (tick "Add to PATH").

## 2. Get the Project

The folder is `D:\abstracts\Madhav\CSE\A\CSE-A-A4\8.ProjectCode\`.

If you received a ZIP, extract it so that `backend/app.py` exists at that path.

## 3. Install Dependencies

```powershell
cd D:\abstracts\Madhav\CSE\A\CSE-A-A4\8.ProjectCode
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Verify:

```powershell
pip list | Select-String "Flask|pandas|scikit"
```

## 4. Verify Data & Models

```powershell
dir data       # should show creditcard_synthetic.csv (18 MB)
dir models     # should show grbmc_*.pkl + pipeline.pkl
```

If missing:

```powershell
python backend/synthetic_data.py
python seed_models.py   # ~45 sec, trains on 8K subset, 10 epochs x3
```

## 5. Run

Double-click `run.bat` OR:

```powershell
python backend/app.py
```

Open `http://127.0.0.1:5000` in Chrome.

## 6. Test

*   Health: `http://127.0.0.1:5000/api/health` → `{"status":"ok"}`
*   Verify: Go to *Verify Transaction* → `Run Fraud Check` → see `Fraud Detected` / `Approved`
*   Bulk: Upload `data/sample_batch.csv` → see 20 rows, 8 flagged, Download button

Done.



## 5. React frontend (new UI)

The original Flask page still works at `http://127.0.0.1:8304/`. The new React UI (Soft Pastel Calm design) lives in `frontend/` and needs Node.js 20+.

```powershell
cd D:\abstracts\Madhav\CSE\A\CSE-A-A4\8.ProjectCode
run.bat          # installs deps, starts backend (8304) and frontend (5304), opens the browser
```

Manual start:

```powershell
$env:BACKEND_PORT = "8304"; python backend\app.py     # terminal 1
cd frontend; npm install; npm run dev                   # terminal 2 -> http://127.0.0.1:5304
```

Ports are read from `.env` (`BACKEND_PORT=8304`, `FRONTEND_PORT=5304`; copy `.env.example`). Vite proxies `/api` to the backend, so no CORS setup is needed.

Checks (backend + frontend running):

```powershell
python scripts\smoke_test.py            # API smoke test (read-only; add --full to retrain)
python scripts\capture_screens.py       # walks every screen, saves docs\screenshots\*.png
python scripts\responsive_check.py      # 360/768/1440 px, dark mode, keyboard, reduced motion
cd frontend; npm run build               # production build into frontend\dist
```

Screenshots use Playwright: `pip install playwright` and either `playwright install chromium` or an installed Chrome.
