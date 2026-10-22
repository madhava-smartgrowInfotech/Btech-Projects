# How to Run VeriVision AI

## 1. Prerequisites

- **Windows 10/11** (64-bit) with **Python 3.10 or newer** (recommended: Python 3.11).
  Download Python from the official site: <https://www.python.org/downloads/>
  During installation, tick **"Add python.exe to PATH"**.
- **Node.js 20 or newer** for the web app: <https://nodejs.org/>. Without it `run.bat` still starts
  the API and the classic server-rendered pages on port 8414.
- **Optional — Docker Desktop** (only needed for Method B).
  Download from the official site: <https://www.docker.com/products/docker-desktop/>
- About 3 GB of free disk space (dependencies + model artifacts).
- No GPU required. The app uses CUDA automatically if available, otherwise CPU.

## 2. Method A — Automatic (Recommended)

For someone with zero coding knowledge:

1. Open the project folder `VeriVision-AI` in File Explorer.
2. Find the file **`run.bat`**.
3. **Double-click `run.bat`**. If Windows SmartScreen appears, click **"More info"**,
   then **"Run anyway"** (this file was created locally by this product).
4. A black command window opens. It will:
   - check Python,
   - create a `.venv` folder on first run,
   - install dependencies from `requirements.txt` (you will see download progress),
   - prepare data and train the models on first run (one-time, slower on CPU),
   - copy `.env.example` to `.env` (ports and demo login) if `.env` is missing,
   - install the web app packages (`frontend/node_modules`, one-time),
   - open two more windows: **VeriVision API** (port **8414**) and **VeriVision Web** (port **5414**).
5. Your browser opens **http://localhost:5414** (the web app).
6. Click **Sign in** and then **Use demo account** (`demo@verivision.ai` / `Demo@1234`),
   choose an image and click **Analyze image**.
7. To stop the app, close the **VeriVision API** and **VeriVision Web** windows (or press **Ctrl+C** in them).

The original server-rendered pages are still available on the API port:
**http://localhost:8414** (upload page) and **http://localhost:8414/insights**.

## 3. Method B — Docker

Recommended if Docker Desktop is already installed.

**Option 1 — helper script:** double-click **`run-docker.bat`**, then open
**http://localhost:5000** in your browser.

**Option 2 — copy-paste commands** (in Command Prompt from the project folder):

```text
docker build -t verivision-ai .
docker run --rm -p 127.0.0.1:5000:5000 --name verivision-ai verivision-ai
```

Then open **http://localhost:5000**. (Docker serves the classic pages only; use Method A or C for the React web app.) Stop with **Ctrl+C**.

## 4. Method C — Manual

Windows CMD commands (run from the project folder):

```text
cd /d D:\path\to\VeriVision-AI
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\prepare_dataset.py
python scripts\train_a1.py
python scripts\train_a2.py
python scripts\train_b.py
python scripts\train_c.py
python scripts\evaluate.py
python run.py
```

Then start the web app in a second terminal and open **http://localhost:5414**:

```text
cd frontend
npm install
npm run dev
```

The classic pages are on **http://localhost:8414**. Linux/macOS alternatives:

```bash
cd /path/to/VeriVision-AI
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python scripts/prepare_dataset.py
python scripts/train_a1.py
python scripts/train_a2.py
python scripts/train_b.py
python scripts/train_c.py
python scripts/evaluate.py
python run.py
```

Training knobs (optional environment variables):

```text
set VERIVISION_EPOCHS=5
set VERIVISION_BATCH=16
set VERIVISION_FORCE_FALLBACK=1
```

## 5. Troubleshooting

- **"Python was not found"** — reinstall Python from <https://www.python.org/downloads/>
  and tick "Add python.exe to PATH". Then close and reopen the command window.
- **Python version problem** — open a terminal and run `python --version`.
  VeriVision AI needs 3.10+. Install a newer Python if yours is older.
- **Windows Defender/SmartScreen warning on `run.bat`** — click **"More info"**,
  then **"Run anyway"**. The script only installs packages and starts the local server.
- **Port already in use** (`Address already in use: 8414` or `Port 5414 is already in use`) — another program
  uses the port. Stop it, or change `VERIVISION_PORT` / `FRONTEND_PORT` in `.env` and restart.
- **The web app says "Cannot reach the VeriVision API"** — the API window is not running. Start it with
  `.venv\Scripts\python.exe run.py` (port 8414) and press **Try again**.
- **Browser does not open automatically** — manually visit **http://localhost:5414**.
- **Node.js was not found** — install Node.js 20+; until then use the classic pages on **http://localhost:8414**.
- **Forgot the demo login** — it is `demo@verivision.ai` / `Demo@1234` (change it with
  `VERIVISION_DEMO_EMAIL` / `VERIVISION_DEMO_PASSWORD` in `.env`).
- **pip/dependency installation failure** — check your internet connection, then run
  `python -m pip install --upgrade pip setuptools wheel` and retry. Corporate proxies
  sometimes block PyPI; retry on another network if needed.
- **Model files missing** (`Model artifacts missing...`) — run the training workflow
  from Method C, or simply re-run `run.bat`, which trains automatically.
- **Dataset unavailable** — `prepare_dataset.py` first tries the public CIFAKE dataset
  via Kaggle, and falls back to clearly-labelled local demo data if download fails.
  Demo metrics are not representative of real-world performance.
- **Docker unavailable** — install Docker Desktop from
  <https://www.docker.com/products/docker-desktop/>, start it, and retry.
- **Insufficient memory** — close other apps, set `VERIVISION_BATCH=8` (or 16) and retrain.
- **Corrupted uploaded image** — the app shows "could not be decoded as an image".
  Try a different PNG/JPG/WEBP file under the size limit.
