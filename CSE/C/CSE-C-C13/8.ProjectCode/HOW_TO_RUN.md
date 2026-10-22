# HOW_TO_RUN — CipherVault

Follow the sections in order. In development the app runs at **`http://localhost:5413`** (React frontend, Vite) and talks to the API at **`http://localhost:8413`**.

## 1. Prerequisites

- **Node.js 20 or newer (LTS)** for the frontend (Method A / C). Download: <https://nodejs.org/>
- **Python 3.11 or newer** (for Method A / C). Download: <https://www.python.org/downloads/>
  During install on Windows, tick **"Add python.exe to PATH"**.
- **A modern browser** (Chrome, Edge, or Firefox — needed for Web Crypto encryption).
  Download Chrome: <https://www.google.com/chrome/> · Firefox: <https://www.mozilla.org/firefox/new/>
- **Docker Desktop** (only for Method B). Download: <https://www.docker.com/products/docker-desktop/>
- **Disk**: ~500 MB free (Python packages + database + your encrypted files).

## 2. Method A — Automatic (recommended)

For someone with zero coding knowledge:

1. Open the `CipherVault` folder.
2. Double-click **`run.bat`**.
3. A black command window opens. You will see lines like:
   - `[OK] Found Python ...` and `[OK] Found Node ...`
   - `[*] Creating virtual environment ...` (first run only)
   - `[*] Installing/updating Python dependencies ...` and `[*] Installing frontend packages ...`
     (first run takes a few minutes - this is normal)
   - `[*] Starting backend on http://localhost:8413 ...` and `[*] Starting frontend on http://localhost:5413/ ...`
4. Two more windows open (backend and frontend) and your browser opens **`http://localhost:5413`**.
   If it does not, open that address manually.
5. Click **Try the demo** on the sign-in page for a ready-made vault (see "Demo accounts" below), or
   register an account and upload a file - it is encrypted in your browser before upload.
6. To stop the app, close the backend and frontend windows (or press **Ctrl+C** in each).

What success looks like: the backend window shows `Uvicorn running on http://127.0.0.1:8413`,
the frontend window shows `Local: http://127.0.0.1:5413/`, and the browser shows the CipherVault landing page.

## 3. Method B — Docker

**Recommended if Docker Desktop is installed.** Exact copy-paste commands
(run them in a terminal inside the `CipherVault` folder):

```
docker compose build
docker compose up
```

Then open **`http://localhost:8413`** in your browser (Docker serves the built frontend from the backend).
Stop with Ctrl+C, and optionally `docker compose down` to remove containers
(data in the `pgdata` volume and `./storage/encrypted` is preserved).

Or simply double-click **`run-docker.bat`**, which does the same thing with error checks.

## 4. Method C — Manual

Exact commands (from inside the `CipherVault` folder):

**Create a virtual environment:**
- Windows: `python -m venv .venv`
- Linux/macOS: `python3 -m venv .venv`

**Activate it:**
- Windows: `.venv\Scripts\activate`
- Linux/macOS: `source .venv/bin/activate`

**Install dependencies:**
```
pip install -r requirements.txt
```

**Configure environment variables:**
```
# Windows
copy .env.example .env
# Linux/macOS
cp .env.example .env
```
Edit `.env`: set a strong `JWT_SECRET`. For PostgreSQL, set e.g.
`DATABASE_URL=postgresql+psycopg://ciphervault:ciphervault@localhost:5432/ciphervault`
(the default SQLite `sqlite:///./ciphervault.db` needs no extra setup).

**PostgreSQL (only if you set a PostgreSQL DATABASE_URL):**
start PostgreSQL 16 and create database/user matching the URL, e.g.:
```
createdb ciphervault
```
With Docker Compose this is automatic (see Method B).

**Running migrations:** the app creates tables automatically on startup
(`init_db()` in `backend/app/db/database.py`); no manual migration step is needed.

**Start the backend:**
```
uvicorn backend.app.main:app --host 127.0.0.1 --port 8413
```

**Start the frontend (second terminal):**
```
cd frontend
npm install
npm run dev
```

**Manually open:** `http://localhost:5413`  (API docs: `http://localhost:8413/docs`)

**Single-server alternative:** run `npm run build` inside `frontend/`; the backend alone then
serves the built app at `http://localhost:8413` (no Vite server needed).

**Demo accounts:** the sign-in page has a **Try the demo** box (Owner / Editor / Viewer).
The first click creates three fictional accounts and fills the owner's vault with synthetic files
(5 files, shares, an editor update and a denied delete, so the audit log has real events).
You can also seed them from a terminal:
```
python scripts/seed_demo.py --url http://localhost:8413
```
Accounts: `owner@example.com` / `Demo-Owner-123`, `editor@example.com` / `Demo-Editor-123`,
`viewer@example.com` / `Demo-Viewer-123`. These are fictional, local-only accounts.

**Run the checks** (with the app running):
```
python scripts/smoke_test.py          # API end-to-end + a real-browser walk of every screen
python scripts/capture_screens.py     # refresh docs/screenshots/
pytest -q                             # backend unit tests
```
The smoke test needs Playwright once: `pip install playwright` (it drives your installed Chrome).

## 5. Troubleshooting

- **"Python not found"**: install Python from <https://www.python.org/downloads/> and
  tick "Add python.exe to PATH" during setup. Then close and reopen the terminal / double-click `run.bat` again.
- **Python version mismatch**: run `python --version`. CipherVault needs 3.11+.
  Install a newer Python side by side and retry.
- **Windows Defender/SmartScreen blocks `run.bat`**: Windows may show
  "Windows protected your PC". Select **More info → Run anyway**. The script is plain text —
  right-click → Edit to inspect it before running.
- **Port already in use** (`address already in use` / `WinError 10013`):
  another program uses port 8413 (backend) or 5413 (frontend). Close it, or change `APP_PORT` /
  `FRONTEND_PORT` in `.env` and restart (the frontend proxies `/api` to `APP_PORT`).
- **Browser not opening automatically**: manually open **`http://localhost:5413`**.
- **Blank page or "Cannot reach the server"**: the backend window must be running on port 8413.
- **"Vault locked" after a refresh**: by design. The decrypted private key lives only in memory; enter your password in the unlock dialog.
- **`npm install` fails**: check your internet connection and that Node 20+ is installed (`node --version`).
- **Dependency installation failures**: check internet access; update Python;
  try `pip install --upgrade pip` then `pip install -r requirements.txt`.
  Corporate proxies may need `pip --proxy ...` configuration.
- **PostgreSQL not available**: if you configured a PostgreSQL URL, verify the server is
  running and reachable (`pg_isready`). Or switch `.env` back to `DATABASE_URL=sqlite:///./ciphervault.db`
  for zero-setup local mode.
- **Docker Desktop not running**: start Docker Desktop and wait for the whale icon to say
  "running", then retry `docker compose up`.
- **Docker build failure**: run `docker compose build --no-cache` and read the error;
  common cause is no disk space (`docker system df`) or no network for pip.
- **Database migration failure**: tables auto-create on startup. If the DB file is corrupt,
  stop the server, delete `ciphervault.db`, and restart (local data will be reset).
- **File upload failure**: check the file is under the size limit (default 25 MB, see
  `MAX_UPLOAD_MB` in `.env`) and that storage has free disk space.
- **Encryption/decryption failure**: use Chrome/Edge/Firefox over `http://localhost`
  (Web Crypto requires a secure context — localhost qualifies). If download reports
  "Decryption failed" or "Integrity check failed", do not retry blindly: the ciphertext
  or key may be mismatched — re-upload the file and re-share it.
