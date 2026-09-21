# CipherGuard Shield — How to Run (Complete Guide)

## 1. Prerequisites — What you need on your machine

### For Method A and C (native Python run)

- **Python 3.10, 3.11, or 3.12** (64-bit). Check yours: open **Command Prompt** and type `python --version`. You need `Python 3.10.x` or newer.
  - Download: **https://www.python.org/downloads/** (click the yellow *Download Python* button). During setup, **check the box `Add Python to PATH`** at the bottom of the first installer screen.
  - Windows 10/11, 4 GB RAM free, ~1 GB disk for the virtual environment and models.
- No other installs required. All Python packages are listed in `requirements.txt` and installed automatically.

### For Method B (Docker — recommended if Docker Desktop is installed)

- **Docker Desktop for Windows** (includes Docker Engine + Compose)
  - Download: **https://www.docker.com/products/docker-desktop/**
  - After installing, open Docker Desktop and wait until it shows **Engine running** (green) in the bottom status bar.
- Python is **not required** for the Docker method.

> If you are unsure, use **Method A** — it is the simplest.

---

## 2. Method A — Automatic (Recommended): Double-Click `run.bat`

*Written for someone with zero coding knowledge.*

1. **Find the folder.** If you received a ZIP file, right-click it → **Extract All** → extract to your **Desktop** or **Documents**. You will get a folder containing `run.bat`.
2. **Start.** Double-click **`run.bat`** (gear icon, *Windows Batch File*). No other file needs to be clicked.
3. **What you will see:**
   - A black window opens and prints lines like `[OK] Python found`, `[1/4] Checking...`, `Installing dependencies` (first run: 1–2 minutes), `Training ThreatSense Engine` (30–60 seconds on first run only), then `[5/5] Starting CipherGuard Shield on http://localhost:8000`.
   - After about 5 seconds the window prints `[run.bat] Browser opened ...` and a **browser tab** opens automatically at **`http://localhost:8000`** showing the CipherGuard Shield dashboard. The black window **must stay open** while you use the app — this is expected; it shows server logs.
4. **How you know it worked:** The browser shows a clean white dashboard with *CipherGuard Shield* at the top, 4 tabs (Dashboard, Secure Transfer, Alerts, Model Performance), and under Model Performance you see accuracy ~97% and a confusion matrix. The black window says `Uvicorn running on http://127.0.0.1:8000`.
5. **Use the product:**
   - *Dashboard* → **Simulate Normal / Simulate Attack** or upload a CSV (≤10 MB, ≤10 000 rows).
   - *Secure Transfer* → type a message → **Encrypt & Transmit to Cloud** → **Decrypt & Verify at Cloud** (try the **Tamper** button to see tag verification fail).
   - *Alerts* → shows triggered detections; *Model Performance* → real held-out test metrics.
6. **How to stop:** Press **Ctrl+C** in the black window, or just **close the black window** (click the X). To start again, double-click `run.bat` — it reuses the existing virtual environment and skips reinstall/training.

> If the browser did not open automatically, open any browser and type **`http://localhost:8000`** manually. Leave the black window open.

---

## 3. Method B — Docker (Recommended if Docker Desktop is installed)

*Assumes you are comfortable copying and pasting one command. When using Docker, you should use `run-docker.bat`; manual commands are also shown.*

### Option B1 — One-click with `run-docker.bat`

1. Start **Docker Desktop** and wait for *Engine running*.
2. Double-click **`run-docker.bat`** in the CipherGuard Shield folder.
3. The script builds the image (`cipherguard-shield:latest`), starts a container mapped to `http://localhost:8000`, polls `/api/health`, and opens the browser automatically.
4. The window stays open and shows the container status. The product runs at **`http://localhost:8000`** even after you close this helper window (container stays in the background).

Useful follow-ups (paste in Command Prompt or PowerShell **from the project folder**):

```bat
docker logs -f cipherguard-shield
docker rm -f cipherguard-shield
docker compose down
```

### Option B2 — Exact copy-paste commands (no helper bat)

Open **Command Prompt** or **PowerShell** and paste these from the **project folder** (the folder that contains `Dockerfile`):

```powershell
# Build the image (first time: 2-4 minutes)
docker build -t cipherguard-shield:latest .

# Run the container (maps container 8000 -> host 8000)
docker run -d --name cipherguard-shield -p 8000:8000 cipherguard-shield:latest

# Optional: follow logs
docker logs -f cipherguard-shield
# Then open your browser at http://localhost:8000

# To stop/remove:
docker rm -f cipherguard-shield
```

**With Compose (alternative — same result):**

```powershell
docker compose up -d
docker compose logs -f
# open http://localhost:8000
docker compose down
```

Inside the Docker image the server listens on `0.0.0.0:8000` (required for host→container routing). On native runs without Docker it is bound strictly to `127.0.0.1` — see Method A/C and `run.bat`.

---

## 4. Method C — Manual (Troubleshooting or Non-Windows Users)

*For anyone comfortable copy-pasting terminal commands. Uses the same virtual environment and `127.0.0.1` binding as `run.bat`.*

Open **Command Prompt** (or PowerShell / macOS Terminal) **from the project folder** (the folder containing `requirements.txt`):

```bat
:: 1. Create a virtual environment (only once; skip if .venv already exists)
python -m venv .venv

:: 2. Activate it
:: Windows (Command Prompt):
.venv\Scripts\activate
:: Windows (PowerShell):
:: .venv\Scripts\Activate.ps1
:: macOS / Linux:
:: source .venv/bin/activate

:: 3. Install dependencies (progress will be printed; retry if internet hiccup)
pip install --upgrade pip
pip install -r requirements.txt

:: 4. Train models only if models\ is missing (first run)
python -m cipherguard.ids.train
:: (If you have real UNSW-NB15 CSVs, drop UNSW_NB15_training-set.csv and
::  UNSW_NB15_testing-set.csv into data\raw\ first, then run the command above)

:: 5. Start the backend (binds to 127.0.0.1 to avoid firewall prompts)
python -m uvicorn cipherguard.api.main:app --host 127.0.0.1 --port 8000 --log-level info
:: Or: python app.py

:: 6. Open your browser manually at:
:: http://localhost:8000
```

Keep the terminal open while using the product (Ctrl+C to stop).

---

## 5. Troubleshooting — Common Issues in Plain Language

**“Python was not found” / `python --version` says `not recognized`**
- Install Python from **https://www.python.org/downloads/**. On the first installer screen, **check `Add Python to PATH`** before clicking Install. Close and reopen Command Prompt, then try `python --version` again. If you use the Microsoft Store *Python* stub, uninstall it or ensure `python` points to the python.org install (check `where python`).

**Windows SmartScreen / Defender says “Windows protected your PC” or blocks `run.bat`**
- Click **`More info`** then **`Run anyway`**. If Defender quarantines it, open Windows Security → Protection history → Allow. `run.bat` and `run-docker.bat` are plain-text scripts — right-click → Edit to inspect them.

**“port already in use” / `Address already in use` / dashboard won’t load**
- Another program is using port **8000**. Close it or restart your PC. To identify it (Command Prompt, admin):
  ```
  netstat -ano | findstr :8000
  taskkill /PID <the_number> /F
  ```
  Then double-click `run.bat` again. You can also try changing the port: `python -m uvicorn cipherguard.api.main:app --host 127.0.0.1 --port 8001` and open `http://localhost:8001`.

**The black window / browser did not open automatically**
- Manually open any browser and type **`http://localhost:8000`** in the address bar. Check the black/terminal window — it shows `Uvicorn running on http://127.0.0.1:8000` if successful.

**Dependency install failed / `pip install` shows red errors**
- Check your internet connection. Retry `pip install -r requirements.txt`. If a specific package fails (e.g., `xgboost`), try: `pip install --upgrade pip setuptools wheel` then retry. Ensure you are on Python 3.10–3.12 (not 3.13). Delete `.venv` and run again if the environment is corrupted.

**Page shows “IDS engine not ready” or “Metrics not found”**
- The models are still training (first run takes ~60 seconds). Wait and **refresh the page (F5)**. If it persists, close the server, **delete the `models\` and `reports\` folders**, and run again — training regenerates them.

**Nothing happens when double-clicking `run.bat` or it closes instantly**
- Right-click `run.bat` → **Run as administrator** (and *More info → Run anyway* if SmartScreen appears). The new `run.bat` never closes silently — it prints the actual error and waits for a keypress, so you can read it.

**Need real UNSW-NB15 data? (optional)**
- You don’t need it — the demo includes high-quality synthetic data with the identical 42-feature schema that works out of the box (see `reports/metrics.json` → `data_mode: synthetic demo data`). For real data, download `UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv` from **https://research.unsw.edu.au/projects/unsw-nb15-dataset**, drop them into `data/raw/`, delete `models\` + `reports\`, then run `python -m cipherguard.ids.train` (or double-click `run.bat`).

**Docker helper says “Docker is not running”**
- Open **Docker Desktop** and wait until the bottom bar says *Engine running* (green whale). The command `docker info` should print without errors.

