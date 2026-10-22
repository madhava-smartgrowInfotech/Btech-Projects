# How to run - Smart Campus Placement System

Two ways to run it. Both use the same trained models in `models/` and data in `data/`.

## A. New React app (recommended)

Requirements: Python 3.10+, Node.js 20+.

```
run.bat
```

`run.bat` creates `.venv`, installs `requirements.txt`, trains the models if `models/` is empty, runs `npm install` in `frontend/`,
then opens two windows and the browser:

| Part | URL | Port source |
|---|---|---|
| FastAPI backend (`backend/main.py`) | http://localhost:8405 (docs at `/docs`) | `BACKEND_PORT` in `.env` |
| React frontend (Vite, `frontend/`) | http://localhost:5405 | `FRONTEND_PORT` in `.env` |

Manual start (two terminals):

```
.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8405
cd frontend
npm install        # first time only
npm run dev
```

Production build of the UI: `cd frontend && npm run build` (output in `frontend/dist`; `npm run preview` serves it on 5405 with the `/api` proxy).

## B. Original Flask app (unchanged)

```
python app.py      # http://127.0.0.1:5000
```

## Retraining the models (optional)

```
python src/generate_dataset.py
python src/preprocess.py
python src/hybrid_model.py
```

## Tests and screenshots

```
python scripts/smoke_test.py             # needs the backend running; add --inprocess to run without a server
python scripts/capture_screens.py        # needs both servers; writes docs/screenshots/*.png (pip install playwright)
```

## Screens

`/` landing · `/predict` eligibility · `/recommend` company-role recommendations · `/dashboard` officer dashboard ·
`/recruiter` shortlisting · `/companies` company board. Keyboard: `/` search, `g e|r|d|u|c` jump to a screen, `g l` activity log, `?` help.

## Troubleshooting

- **"Could not reach the placement API"** - the backend is not running on 8405; start it as above.
- **`ModuleNotFoundError: pyarrow`** - the pickled company table needs it: `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **Port already in use** - change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` (copy of `.env.example`) and restart.
