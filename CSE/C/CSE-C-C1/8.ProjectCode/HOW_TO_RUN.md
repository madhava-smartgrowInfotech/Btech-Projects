# How to Run — AegisBallot

> **New React frontend.** AegisBallot now has a React web app (`frontend/`) in front of the FastAPI backend.
> Backend: **http://localhost:8401** · Web app: **http://localhost:5401** (ports come from `.env`).
> Open the **web app (5401)**. The old server-rendered pages still exist on 8401 but are no longer the main UI.
> Also needed: **Node.js 20+** (https://nodejs.org/).

## Prerequisites
- **Python 3.12** (3.11 also compatible) — download from https://www.python.org/downloads/
- **Docker Desktop** (only if using Docker method) — https://www.docker.com/products/docker-desktop/
- No database server, blockchain wallet, public blockchain account, or government API credentials are required.
- All data is stored locally in SQLite (`data/aegisballot.db`) and the local permissioned ledger.
- Aadhaar verification is a **local synthetic/demo provider** (`DemoAadhaarProvider`). It validates 12-digit structure, Verhoeff checksum, and membership in the synthetic registry. It does NOT contact UIDAI.

---

## Method A — Automatic (Windows, zero coding knowledge)

1. Double-click **`run.bat`** in the project folder.
2. What happens:
   - The script checks for Python.
   - Creates `.venv` if missing.
   - Activates the venv, upgrades pip, installs `requirements.txt`.
   - Initializes the database and seeds demo data (`python -m app.seed`).
   - Installs the frontend (`npm install`, first run only).
   - Starts the FastAPI backend on **8401** and the web app on **5401**, each in its own console window.
   - Opens **http://localhost:5401** in your browser.
3. Successful startup looks like:
   ```
   INFO: Started server process
   INFO: Uvicorn running on http://127.0.0.1:8401
   ```
   plus a Vite window saying `Local: http://localhost:5401/`, and the browser shows the AegisBallot landing page.
4. Demo credentials (shown on login page too):
   - **Admin:** `admin` / `Admin@123`
   - **Auditor:** `auditor` / `Audit@123`
   - **Voters:** `voter1` / `Voter@01pass` through `voter20` / `Voter@20pass` (see `data/synthetic_identities.json` for mapped Aadhaar numbers)
5. To stop: close the two console windows (or press **Ctrl+C** in each).

---

## Smoke test and screenshots

With both servers running:
```bat
python scripts\smoke_test.py          :: 44 API and flow checks
pip install playwright && playwright install chromium
python scripts\capture_screens.py     :: saves every screen to docs\screenshots and checks the browser console
```
Both create a small "Smoke Test" / "Screenshot Demo Election" in the database. Wait a minute between the two (login rate limit: 10 per minute).

---

## Method B — Docker

> The Docker image runs the backend only, so it serves the original server-rendered pages on port 8000. Use Method A or C for the React web app.

Requirements: Docker Desktop running.

```bat
docker build -t aegisballot .
docker run --rm -p 127.0.0.1:8000:8000 --name aegisballot_app aegisballot
```

Or use the helper:

- Double-click **`run-docker.bat`** — it verifies Docker, builds, runs, and opens http://localhost:8000.

- Stop: `Ctrl+C` or `docker stop aegisballot_app`.

Visit **http://localhost:8000**.

Alternative with compose:
```bat
docker compose up --build
```

---

## Method C — Manual

### Windows (PowerShell/CMD)
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 8401
:: in a second window
cd frontend
npm install
npm run dev
```
Visit http://localhost:5401

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 8401
# second terminal: cd frontend && npm install && npm run dev
```

---

## Troubleshooting

- **Python not found:** Install Python 3.12, check “Add to PATH” during install, reopen terminal.
- **Docker not found:** Install Docker Desktop, ensure it is running.
- **Windows Defender / SmartScreen:** Click “More info” → “Run anyway” (run.bat is a local script).
- **Port already in use (8401 or 5401):** Close the other program, or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`.
- **Web app shows "Cannot reach the AegisBallot server":** the backend window is not running; start it with `run.bat`.
- **`npm run dev` fails with a memory error:** close other heavy programs, or run `npm run build` then `npm run preview` in `frontend/`.
- **Browser does not open automatically:** Manually visit http://localhost:5401
- **Dependency installation failure:** Delete `.venv` folder and re-run `run.bat`.
- **Corrupted virtual environment:** Delete `.venv` and `data/*.db`, then re-run.
- **Database initialization problems:** Delete `data/aegisballot.db` and `data/secrets.json`, then run `python -m app.seed` again.

---

## Demo Credentials & Data

- Admin: `admin` / `Admin@123`
- Auditor: `auditor` / `Audit@123`
- Voters: `voter1`..`voter20` with passwords `Voter@01pass`..`Voter@20pass`
- Synthetic Aadhaar numbers: `data/synthetic_identities.json` (masked display in UI, full value only for demo verification).
- To reset demo data: delete `data/aegisballot.db` and run `python -m app.seed`.

## Running Tests

```bat
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest -v
```

## Running the Benchmark

```bat
python -m app.benchmarks.run_benchmark --voters 1000
```
Output saved to `benchmark_results/latest.json` and `benchmark_results/benchmark_*.json`. The admin dashboard reads the latest result.

## Inspecting the Ledger

- As **Auditor** (Ledger audit page), click **Verify Ledger Integrity** (recomputes SHA-256 from genesis).
- Click a block number to see transactions (ballot IDs are anonymous, payloads encrypted).
- Check **Audit Log** for authentication, vote, and ledger events.

## Tamper-Detection Demonstration

- In the Auditor dashboard, click **Run Tamper-Detection Demo**.
- The system clones the ledger in memory, alters a block hash, validates, and shows detection without corrupting the production ledger.
- Alternatively, call the API: `GET /api/chain/verify`.

## Aadhaar Provider Note

The provider is `DemoAadhaarProvider` under `app/identity/provider.py`. It implements `IdentityVerificationProvider` and can be replaced by a real adapter. The UI always shows “Demo verification environment”.

