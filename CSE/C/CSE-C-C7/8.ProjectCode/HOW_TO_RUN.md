# HOW_TO_RUN — LearnPathIQ

## 0. What runs where (React frontend)
| What | URL | Port (set in `.env`) |
|---|---|---|
| New React app (Neo Brutal Grid UI, kit V2) | http://localhost:5407 | `FRONTEND_PORT=5407` |
| FastAPI backend + original server-rendered UI | http://localhost:8407 | `BACKEND_PORT=8407` |

`run.bat` starts both (two windows: "LearnPathIQ API" and "LearnPathIQ Web") and opens the React app.
The React dev server proxies `/api` and `/static` to the backend, so no CORS setup is needed.

Manual start, from this folder, in two terminals:
```
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8407
cd frontend && npm install && npm run dev
```
Extra requirement for the React app: Node.js 20 or newer (https://nodejs.org/).

Checks (with both servers running): `python scripts/smoke_test.py` (API flow through the proxy),
`python scripts/capture_screens.py` (walks every screen, refreshes `docs/screenshots/`, fails on console errors),
`python scripts/check_responsive.py` (360/768/1440 px, light and dark). The last two need `pip install playwright`.

The older sections below describe the original single-server flow; replace `8000` with `8407` wherever it appears
(the port now comes from `.env`; Docker still publishes 8000).

## 1. Prerequisites
- Python 3.11 or newer (tested on 3.11+). Download: https://www.python.org/downloads/
- 4 GB RAM minimum, 8 GB recommended; ~500 MB free disk.
- Docker Desktop (only for Method B). Download: https://www.docker.com/products/docker-desktop/
- Windows 10/11, macOS, or Linux. No paid APIs, no cloud, no external database.

## 2. Method A — Automatic (recommended for most users)
1. Open the `LearnPathIQ` folder.
2. Double-click `run.bat`.
3. The command window will: check Python → create `.venv` (first time) → install packages from `requirements.txt` → train models on first run (1–3 minutes) → start the server.
4. "Installing dependencies" means downloading the Python libraries listed in `requirements.txt` — progress bars are normal.
5. Success looks like: `Uvicorn running on http://127.0.0.1:8000` and your browser opening automatically.
6. Use exactly: `http://localhost:8000`
7. To stop: press `Ctrl+C` in the command window, then close it.

## 3. Method B — Docker (recommended when Docker Desktop is installed)
Copy-paste these commands in a terminal from the `LearnPathIQ` folder:
```
docker build -t learnpathiq .
docker run --rm -p 8000:8000 learnpathiq
```
Then open `http://localhost:8000`. Stop with `Ctrl+C`.

## 4. Method C — Manual
Windows CMD (from the `LearnPathIQ` folder):
```
cd /d D:\path\to\LearnPathIQ
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python scripts\train_pipeline.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Then open `http://localhost:8000`.

Non-Windows (macOS/Linux):
```
cd LearnPathIQ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/train_pipeline.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 5. Troubleshooting
- **Python not found**: install from https://www.python.org/downloads/ and tick "Add python.exe to PATH"; reopen CMD and run `python --version`.
- **Windows Defender/SmartScreen blocks run.bat**: click "More info" → "Run anyway". The file is a plain text launcher; right-click → Edit to inspect it.
- **Port 8000 already in use**: close the other app, or start with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8001` and open `http://localhost:8001`.
- **Browser does not open automatically**: manually open `http://localhost:8000`.
- **Dependency installation failure**: check internet access, then delete `.venv` and re-run `run.bat`. Ensure Python 3.11+.
- **Dataset download failure**: no action needed — the trainer automatically uses the built-in synthetic OULAD-like fallback and records it in the metrics file.
- **Model artifact missing** (`503 Model artifacts not ready`): run `python scripts\train_pipeline.py` from the project folder, then restart the server.
- **Docker unavailable**: use Method A or C; Docker is optional.
