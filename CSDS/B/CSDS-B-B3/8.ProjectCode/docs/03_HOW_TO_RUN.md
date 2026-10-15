# How to run SkillVerse

SkillVerse has two front doors over the same Python code and the same SQLite database:

| | Command | URL |
|---|---|---|
| **New React app** (kit V3 "Depth Studio") | `run.bat` | http://localhost:5203 |
| Original Streamlit app (unchanged) | `streamlit run app.py` | http://localhost:8501 |

The React app talks to a thin FastAPI layer in `backend/` that calls the existing `services/`, `ai/` and `graph/`
modules. No business logic was rewritten.

## Requirements

- Python 3.10+ (tested on 3.11)
- Node.js 18+ (tested on 24) and npm

## One-click start (Windows)

Double-click `run.bat`, or run it from this folder. It will:

1. install the Python packages if they are missing (`pip install -r requirements.txt`),
2. run `npm install` in `frontend/` the first time,
3. start the API on **port 8203** and the UI on **port 5203** in two windows, and open the browser.

On first start the backend creates `knowledgex.db` and seeds the demo data automatically.

## Manual start

```bash
# 1. Python packages (once)
pip install -r requirements.txt

# 2. API  (from this folder; port 8203)
python -m uvicorn backend.main:app --port 8203

# 3. UI   (second terminal; port 5203)
cd frontend
npm install        # first time only
npm run dev
```

Open http://localhost:5203. API docs are at http://localhost:8203/docs.

Ports are read from `.env` (`BACKEND_PORT=8203`, `FRONTEND_PORT=5203`). The Vite dev server proxies `/api` to the backend,
so there is nothing else to configure.

## Demo accounts

Password for all three is `Demo@1234` (set `DEMO_PASSWORD` in `.env` *before the first run* to change it).

| Role | Email |
|---|---|
| Student | `student@example.com` |
| Mentor | `mentor@example.com` |
| Admin | `admin@example.com` |

The login page has a **Demo accounts** tab that signs you in with one click.

## Production build

```bash
cd frontend
npm run build      # outputs frontend/dist
npm run preview    # serves the build on port 5203 (still proxies /api to 8203)
```

## Checks

```bash
# with the API running:
python scripts/smoke_test.py
```

The smoke test walks the main flow for all three roles (login, assessment, roadmap, graph, career, marketplace purchase and
upload, mentors, mock interview, coding sandbox, profile, mentor panel, admin panel) and exits non-zero on any failure.
It creates a throw-away `smoke_*@example.com` student each run.

## Configuration (`.env`)

| Key | Purpose |
|---|---|
| `BACKEND_PORT` / `FRONTEND_PORT` | 8203 / 5203 |
| `APP_SECRET` | signs the web login tokens, change it outside a demo |
| `DEMO_PASSWORD` | password of the seeded demo accounts |
| `DATABASE_URL` | defaults to `sqlite:///knowledgex.db` in this folder |
| `AI_MODE` | `local` (default, fully offline) |

`.env` is git-ignored. Never commit it.

## Troubleshooting

- **"Cannot reach the SkillVerse server"** in the UI: the API is not running. Start it (step 2) and press *Try again*.
- **Port already in use**: change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` and restart both servers.
- **`npm run build` is killed with "memory allocation failed"**: the machine is out of memory/commit space. Close other
  programs and retry (or set `GOMAXPROCS=2` first).
- **Reset all data**: stop the API, delete `knowledgex.db`, start it again (it re-seeds).
- **The code editor rejects my solution**: it runs in an isolated process with a 5 s limit and a restricted set of
  built-ins; `import os`, `open(`, `eval(` and similar are refused on purpose.

## Project layout

```
backend/            FastAPI layer (routers: auth, student, market, mentors, practice, admin)
frontend/           Vite + React app; src/components/{ui,motion,charts,three} is the copied V3 kit
app.py, pages/      original Streamlit app (untouched)
services/ ai/ graph/ database/   shared business logic
scripts/smoke_test.py            API smoke test
run.bat                          launcher
docs/FRONTEND_PLAN.md            endpoint + feature inventory and sign-off checklist
```
