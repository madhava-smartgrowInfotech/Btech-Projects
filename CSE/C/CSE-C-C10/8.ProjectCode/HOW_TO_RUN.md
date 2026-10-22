# HOW_TO_RUN — VenturePulse

Complete beginner-friendly guide. VenturePulse has two parts that run together:

| Part | URL | What it is |
|------|-----|-----------|
| **React app** (new) | **http://localhost:5410** | Landing page, demo sign-in, dashboard, analyze, model performance, insights |
| **FastAPI backend** | http://localhost:8410 | The prediction API and the original server-rendered pages (`/dashboard`, `/predict`, `/performance`, `/insights`) |

The ports are set in `.env` (`BACKEND_PORT=8410`, `FRONTEND_PORT=5410`; copy `.env.example` if `.env` is missing).

**Demo sign-in:** `demo@venturepulse.com` / `Demo@1234` (the sign-in page has a "click to fill" button). Change it with `DEMO_EMAIL` / `DEMO_PASSWORD` in `.env`.

## 1. Prerequisites

- **Python 3.10 or newer** (3.11 recommended). Download: https://www.python.org/downloads/
  - On Windows, during installation enable **"Add python.exe to PATH"**.
- **Node.js 18 or newer** (for the React app). Download: https://nodejs.org/
- **Docker Desktop** (only if you want Method B, which runs the backend and the original pages only). Download: https://www.docker.com/products/docker-desktop/
- **Internet** is required the first time (to install packages and download the text-embedding model `sentence-transformers/all-MiniLM-L6-v2`, ~90 MB). Later runs work offline from cached artifacts.
- Optional: the public dataset CSV "Startup Success Prediction" (https://www.kaggle.com/datasets/manishkc06/startup-success-prediction). If you have it, copy the CSV into the `data/raw/` folder before starting. If not, the app automatically uses a realistic synthetic dataset with the same schema — everything still works.

## 2. Method A — Automatic

For someone with zero coding knowledge:

1. Open the **VenturePulse** folder (`8.ProjectCode`) in File Explorer.
2. Double-click **`run.bat`**.
3. A command window shows progress:
   - `[1/5]` checks Python.
   - `[2/5]` creates the virtual environment (`.venv`) if it is missing, or rebuilds it if it is broken.
   - `[3/5]` installs/updates the Python dependencies from `requirements.txt` (first run takes several minutes — this is normal).
   - `[4/5]` runs `npm install` in `frontend/` (first run only).
   - `[5/5]` starts the backend in a second window and the React app in this one.
4. The first start may train the models (a few minutes); later starts load the saved models in seconds.
5. Your browser opens **http://localhost:5410**. If it does not, type that address yourself.
6. Click **Try the demo account**, then use **Dashboard → Analyze a startup → Model performance → Startup insights**.
7. To stop: press **Ctrl+C** in both windows, then close them.

## 3. Method B — Docker (backend + original pages only)

**Recommended if Docker Desktop is installed and you do not need the React app.** Run from the project folder:

```bat
docker build -t venturepulse:latest .
docker run --rm -p 8000:8000 --name venturepulse-app venturepulse:latest
```

Then open **http://localhost:8000**. Or double-click `run-docker.bat`. To stop: **Ctrl+C**, or `docker stop venturepulse-app`.

## 4. Method C — Manual

Windows (two terminals, from the project folder):

```bat
:: terminal 1 - backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8410

:: terminal 2 - frontend
cd frontend
npm install
npm run dev
```

Linux / macOS:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8410 &
cd frontend && npm install && npm run dev
```

Then open **http://localhost:5410**.

Checks and tools:

```bat
python -m pytest tests/ -q                 :: original backend tests
python scripts/smoke_test.py               :: end-to-end API smoke test (in-process)
python scripts/smoke_test.py --live        :: ... plus the running frontend proxy
python scripts/ui_checks.py                :: browser checks: 360/768/1440px, light/dark, keyboard, error states
python scripts/capture_screens.py          :: re-capture docs/screenshots (needs the app running and `pip install playwright`)
python scripts/train.py                    :: retrain the models (also rewrites the charts in app/static/img)
```

## 5. Troubleshooting

### Python or Node not found

You see `'python' is not recognized` / `'node' is not recognized`. Install them (links above), enable **"Add python.exe to PATH"**, close and reopen the terminal and try again.

### Windows Defender / SmartScreen

Windows may show "Windows protected your PC" for the local batch script. Click **More info → Run anyway**. This is your own local script starting local servers; nothing is uploaded anywhere.

### Port already in use

Change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` and start again (`run.bat` and the Vite proxy both read them), or stop the other program.

### The page says "Cannot reach the VenturePulse API"

The backend window is not running or crashed. Start it again with `run.bat` and read the red error in the backend window.

### "The model files may be missing or incompatible" (500 errors)

The saved models were created with different library versions than your install. Retrain them once: `.venv\Scripts\python scripts\train.py`, then restart.

### Browser does not open

Open **http://localhost:5410** manually and check both command windows are still running.

### Dependency installation fails

1. Check your internet connection (first install needs it).
2. Update pip: `python -m pip install --upgrade pip` and retry.
3. Read the red pip error in the window — it usually names the failing package.
4. Retry `run.bat`.

### Dataset download unavailable

No action needed. If the public dataset cannot be downloaded, the application automatically uses the built-in synthetic dataset with the same expected schema. The dashboard shows a data note, and `models/metadata.json` records `"synthetic_fallback": true`. All pages, predictions, and charts still work.
