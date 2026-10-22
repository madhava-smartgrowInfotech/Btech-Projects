# How to run FINJARVIS

FINJARVIS now ships two front ends over the same Python code:

| | Command | Address |
|---|---|---|
| **New web app** (React + FastAPI, "Aurora Glass" design) | `run.bat` | http://localhost:5411 |
| Original Streamlit app (unchanged) | `streamlit run app.py` | http://localhost:8501 |

Both use the same SQLite file (`finjarvis.db`), so accounts and data are shared.

## Quick start (Windows)

1. Install **Python 3.11+** (tick "Add python.exe to PATH") and **Node.js 20+**.
2. Double-click **`run.bat`** in this folder.
   - It builds `.venv`, installs `backend\requirements.txt` and `npm install`s the frontend the first time (a few minutes).
   - It starts the API on port **8411** and the web app on port **5411** in two minimised windows, then opens the browser.
3. Log in with the built-in demo account, or create your own:

   | Username | Password |
   |---|---|
   | `demo` | `Demo@1234` |

   The demo account is created automatically on first start and holds fictional data for the current month and five months before it
   (transactions, budgets, goals, investments), so every screen has something to show. The login page also has a **Try the demo account** button.

To stop, close the two minimised "FINJARVIS backend" / "FINJARVIS frontend" windows.

## Configuration (`.env`)

Copy `.env.example` to `.env`. Everything is optional:

| Variable | Meaning |
|---|---|
| `BACKEND_PORT` / `FRONTEND_PORT` | Ports used by `run.bat` (default 8411 / 5411) |
| `APP_SECRET_KEY` | Signs login tokens. Set any long random string |
| `AI_API_KEY` | Optional Anthropic key; enables free-form answers in the AI Assistant |
| `DEFAULT_CURRENCY` | Display default |
| `FINJARVIS_DB` | Optional path to a different SQLite file (used by the test scripts so your real data is never touched) |

`.env` is git-ignored; never commit it.

## Run the pieces by hand

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8411

cd frontend
npm install
npm run dev          :: http://localhost:5411 (proxies /api to 8411)
npm run build        :: production build into frontend\dist
```

API documentation (Swagger) is at http://127.0.0.1:8411/docs while the backend runs.

## Checks

```bat
.venv\Scripts\python.exe -m pytest                      :: original service/ML unit tests (38)
.venv\Scripts\python.exe scripts\smoke_test.py          :: end-to-end API test on a throw-away database (49 checks)
pip install playwright && playwright install chromium
python scripts\capture_screens.py                       :: refreshes docs\screenshots (starts the app itself if needed)
```

## What changed for the new front end

- `backend/` is a thin FastAPI layer. Every route calls the existing functions in `services/`, `ml/`, `auth/` and `utils/`; none of them were edited.
  It adds only what a browser needs: signed bearer tokens, `/api/health`, `/api/meta`, a combined `/api/dashboard` read, an unread count,
  and a public `/api/public/showcase` (the landing page's numbers, computed from the demo account).
- `backend/requirements.txt` pins **bcrypt 4.0.1**. With bcrypt 5.x, `passlib` raises "password cannot be longer than 72 bytes" and
  every sign-up or login fails. (The original `requirements.txt` asks for `bcrypt>=4.1.2`, which resolves to 5.x today.)
- `backend/demo_seed.py` loads `data/sample_transactions.csv` with its dates shifted so the newest sample month is the current month,
  plus a few earlier synthetic months. The original loader keeps the file's June-August 2026 dates, so the current month stays empty.
- The Analytics "Type" filter, which the Streamlit page showed but ignored, now switches the category chart between spending and income.
- `tests/conftest.py` now disposes the temp database engine before deleting it (Windows could not delete the open file).

## Troubleshooting

- **"Server offline - start run.bat"** in the top bar: the API is not running. Start `run.bat`, or check the "FINJARVIS backend" window for the error.
- **Port already in use**: change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`, or close the program using it.
- **Sign-up says "password cannot be longer than 72 bytes"**: the wrong bcrypt is installed. Delete `.venv` and run `run.bat` again.
- **`.venv` copied from another PC does not start**: `run.bat` detects this and rebuilds it.
- **Live investment prices fail**: they need internet and a ticker symbol (for example `NIFTYBEES.NS`). The app keeps your last known price and says so.
- **AI Assistant says free-form chat is unavailable**: set `AI_API_KEY` in `.env` and restart. The built-in analytics answers work without it.
