# HOW_TO_RUN — PeerScope

## 1. Prerequisites

- **Python 3.11 or 3.12** (Windows): download from the official site — https://www.python.org/downloads/
  During setup, tick **"Add python.exe to PATH"**.
- **Docker Desktop** (only if you use Method B): https://www.docker.com/products/docker-desktop/
- **Node.js 18 or newer** (for the web app): https://nodejs.org/
- A modern browser (Chrome / Edge / Firefox).
- Internet on first run (to install Python packages and download the local AI model on demand).

## 2. Method A — Automatic (recommended)

For someone with zero coding knowledge:

1. Open the PeerScope folder.
2. **Double-click `run.bat`**. (If Windows SmartScreen appears: click **“More info” → “Run anyway”**.)
3. A black command window opens and shows progress:
   - checks Python,
   - creates a virtual environment (first run only),
   - installs dependencies (first run takes several minutes — this is normal),
   - prepares the dataset and trains the decision model (first run only),
   - installs the web app packages (first run only),
   - starts the **API on port 8408** and the **web app on port 5408** in two windows.
4. Successful startup looks like this in the two windows:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8408
   VITE ... ready  ->  Local: http://127.0.0.1:5408/
   ```
5. Your browser opens automatically at **http://localhost:5408**. If it doesn't, type that address manually. (The API's own docs are at http://localhost:8408/docs.)
6. Upload a PDF on the **Analyze Paper** page and click **Analyze**.
7. To stop: close the two PeerScope windows (**PeerScope API** and **PeerScope Web**).

First-time downloads: the local language model (`Qwen2.5-1.5B-Instruct`, CPU) and the embedding model are fetched from Hugging Face on first analysis and cached locally. If the download fails, PeerScope keeps working with deterministic analysis and shows a clear “AI review unavailable” notice instead of fake content.

## 3. Method B — Docker

1. Install and start **Docker Desktop**.
2. Open a terminal in the PeerScope folder and run (copy-paste):
   ```
   docker build -t peerscope .
   ```
3. Then run:
   ```
   docker run --rm -p 8408:8408 peerscope
   ```
   Or simply double-click **`run-docker.bat`**, which does both steps.
4. The container runs the **API only** on http://localhost:8408 (docs at /docs). Start the web app from the project folder with `cd frontend`, `npm install`, `npm run dev`, then open http://localhost:5408.
5. To stop: press **Ctrl+C** in the terminal.

## 4. Method C — Manual

Windows (PowerShell / CMD) - two terminals.

Terminal 1, the API:

```
python -m venv .venv
.venv\Scriptsctivate
python -m pip install -r requirements.txt
python scripts\prepare_dataset.py
python scripts	rain_model.py
python scripts\make_demo_pdf.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8408
```

Terminal 2, the web app:

```
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5408**. Ports and the API address live in `.env` (`PEERSCOPE_PORT=8408`, `FRONTEND_PORT=5408`, `VITE_API_URL=http://127.0.0.1:8408`).

Linux / macOS: same commands with `python3` and `source .venv/bin/activate`.

To build the production bundle: `cd frontend && npm run build` (output in `frontend/dist`).

Optional checks (with both servers running): `python scripts/smoke_test.py` and, for fresh screenshots, `pip install playwright && playwright install chromium && python scripts/capture_screens.py`.

## 5. Troubleshooting

- **Python not found**: install from https://www.python.org/downloads/ and tick “Add python.exe to PATH”. Verify with `python --version`.
- **Python not on PATH**: reinstall with the PATH option, or run `py --version` to check the launcher.
- **Windows Defender / SmartScreen**: click **“More info” → “Run anyway”** for `run.bat`. This is a local script you downloaded yourself.
- **Dependency installation failure**: check internet, then delete the `.venv` folder and re-run `run.bat`. Read the red pip error — it names the failing package.
- **Model download failure**: analysis still works; the AI-review card shows “unavailable” with the reason. Retry later with internet.
- **Port 8408 or 5408 already in use**: close the other program using it, or change `PEERSCOPE_PORT` / `FRONTEND_PORT` in `.env` (keep `VITE_API_URL` pointing at the API port) and restart.
- **The web app shows "Cannot reach the PeerScope backend"**: the API window is not running or crashed - check the **PeerScope API** window, or run `python -m uvicorn app.main:app --port 8408`.
- **Broken `.venv` ("did not find executable")**: the folder was copied from another machine. `run.bat` detects this and rebuilds it; or delete `.venv` yourself.
- **`npm` not found**: install Node.js 18+ and reopen the terminal.
- **Browser did not open**: manually visit http://localhost:5408.
- **PDF cannot be parsed**: the file may be scanned images without text. PeerScope shows a “very little extractable text” warning in that case.
- **Docker unavailable**: install/start Docker Desktop; run `docker --version` to verify.
- **Docker build failure**: ensure Docker Desktop is running with internet access, then re-run the build and read the error output.
