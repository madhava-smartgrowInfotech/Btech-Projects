# How to Run FinSight AI

> **New React frontend:** `run.bat` now starts the API on port 8409 and the React app on 5409 - see the
> section at the end of this file and `docs/03_HOW_TO_RUN.md`. Ports below refer to the original Flask-only mode.

## 1. Prerequisites

- **Python 3.11 or newer** (3.11 / 3.12 recommended; any recent 3.x works).
  Download: https://www.python.org/downloads/
  During installation on Windows, tick **"Add python.exe to PATH"**.
- **Docker Desktop** (only required for the Docker method).
  Download: https://www.docker.com/products/docker-desktop/
- A modern web browser (Chrome / Edge / Firefox).
- Internet access on first run (to install Python packages and download the
  public dataset; the app itself then runs fully offline on localhost).

## 2. Method A — Automatic (Recommended)

For someone with zero coding knowledge:

1. Open the `FinSight` project folder.
2. Double-click **`run.bat`**.
3. The command window will:
   - Check Python is installed,
   - Create a `.venv` virtual environment (first run only),
   - Install/update dependencies from `requirements.txt` (first run takes
     several minutes — progress is printed),
   - Train the models automatically if `models/best_model.pkl` is missing,
   - Start the Flask server bound to `127.0.0.1`.
4. You will see something like `Running on http://127.0.0.1:5000`.
5. Your browser should open automatically at:

   ```text
   http://localhost:5000
   ```

6. If the browser does not open, open the URL above manually.
7. To stop the application, press **Ctrl+C** in the command window or close
   the window.

## 3. Method B — Docker

**Recommended if Docker Desktop is installed.**

Make sure Docker Desktop is running, then in a terminal inside the project
folder run:

```text
docker build -t finsight-ai .
docker run --rm -p 5000:5000 --name finsight-ai finsight-ai
```

Or with Docker Compose:

```text
docker compose up --build
```

Then open:

```text
http://localhost:5000
```

Alternatively, just double-click **`run-docker.bat`** — it checks Docker,
builds the image, and starts the app, keeping the window open with clear
errors if anything fails.

## 4. Method C — Manual

Windows (PowerShell / CMD):

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\train.py
python run.py
```

Unix-like (macOS / Linux):

```text
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/train.py
python run.py
```

Then open manually:

```text
http://localhost:5000
```

## 5. Troubleshooting

- **Python not found:** install Python 3.11+ from
  https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  Verify with `python --version`.
- **Windows Defender / SmartScreen blocks `run.bat`:** click **More info**
  → **Run anyway**. The script only creates a virtualenv, installs
  packages, and starts a local server.
- **Port already in use:** another app is using port 5000. Stop it, or run
  with a different port: `set PORT=5001` (Windows) then `python run.py`,
  and open `http://localhost:5001`.
- **Browser not opening automatically:** manually open
  `http://localhost:5000` (or your configured port).
- **Dependency installation failures:** check your internet connection,
  then re-run. For the full error, run
  `.venv\Scripts\activate` + `pip install -r requirements.txt` manually.
- **Docker not running:** start Docker Desktop and wait until it shows
  "running", then retry.
- **Model/data artifact missing:** run `python scripts\train.py` from the
  project folder (downloads the public dataset and regenerates
  `models/` + `artifacts/`). The app shows a friendly message instead of a
  stack trace if artifacts are absent.
- **Permission problems:** move the project to a folder you own
  (e.g. Documents), right-click `run.bat` → Run as administrator only if
  needed, and ensure antivirus is not quarantining `.venv`.


## Running the React frontend (ports 8409 / 5409)

`.env` holds the ports: `PORT=8409` (Flask API) and `FRONTEND_PORT=5409` (React app). Defaults apply if it is missing.

**Automatic:** double-click `run.bat`. It creates `.venv`, installs requirements, trains the model if missing,
runs `npm install` and `npm run build` in `frontend/` (first run only), starts the API in a second window and
serves the frontend, then opens http://localhost:5409. Needs Python 3.11+ and Node.js 18+.

**Manual:**

```text
python -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
python scripts	rain.py          :: only if modelsest_model.pkl is missing
python run.py                    :: API on http://localhost:8409

cd frontend
npm install
npm run dev                      :: http://localhost:5409 (proxies /api to 8409)
```

For a production-style run use `npm run build` then `npm run preview` (also port 5409).
The original server-rendered Flask pages are unchanged and still available at http://localhost:8409.

**Checks** (with both servers running): `python scripts\smoke_test.py` and `python scripts\capture_screens.py`
(the latter needs `pip install playwright`; it uses installed Chrome, else run `playwright install chromium`).
