# How to run

Two ways to run the product. They share the same SQLite database (`instance/app.db`).

## A. New React interface (recommended) - ports 8301 / 5301

Needs Python 3.11+ and Node 20+.

```bat
run.bat
```

`run.bat` creates the virtual environment and installs packages on first run, then opens two windows:

| Window | What | URL |
|---|---|---|
| backend | FastAPI JSON API (`backend/main.py`) | http://localhost:8301/api/health (docs at `/api/docs`) |
| frontend | Vite dev server (React) | http://localhost:5301 |

Manual start:

```bat
python -m venv venv
venv\Scripts\python -m pip install -r backend\requirements.txt
venv\Scripts\python -m uvicorn backend.main:app --port 8301

cd frontend
npm install
npm run dev
```

Ports and the cookie-signing secret live in `.env` (copy `.env.example`; `.env` is git-ignored). Set
`ANTHROPIC_API_KEY` there (and `pip install anthropic`) to get Claude-written answers; without it answers are the
offline extractive ones.

Try it: register, upload `sample_data/sample_notes_data_structures.txt`, ask "What is the LIFO principle?", take a
quiz from Documents, open the Roadmap.

Production build of the frontend: `cd frontend && npm run build` (output in `frontend/dist`, `npm run preview` serves it on 5301).

## B. Original Flask interface - port 5000 (unchanged)

```bat
venv\Scripts\python app.py
```

## Checks

```bat
venv\Scripts\python scripts\smoke_test.py          :: API checks (backend must be running)
pip install playwright                              :: once, system Python
python scripts\capture_screens.py                   :: walks every screen, saves docs/screenshots/*.png, reports console errors
python scripts\capture_screens.py --responsive      :: also checks 360 / 768 px for sideways scrolling
```
