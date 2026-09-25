# ClauseGuard - How to run

## Prerequisites

- Python 3.10+ on PATH
- Node.js LTS on PATH
- A free Gemini API key: https://aistudio.google.com/apikey

## First-time setup

```bat
setup.bat
```

This creates the Python virtual environment (`venv/`), installs backend dependencies, installs
frontend dependencies (`frontend/node_modules`), creates `.env` from `.env.example` if missing,
and downloads the CUAD dataset if `data/cuad/CUADv1.json` is not already present (it is committed,
so this normally does nothing).

Then open `.env` and set:

```
GEMINI_API_KEY=your-key-here
```

## Run

```bat
run.bat
```

This starts the backend (FastAPI/Uvicorn on port **8106**) and frontend (Vite dev server on port
**5106**) in two new windows and opens `http://localhost:5106` in your browser. Close the two
windows to stop the servers.

## Demo login

There is no pre-seeded account - click **Sign up** and register with any email/password (6+
characters). Everything after that uses the real pipeline; there is no fake/demo data path.

## Smoke test

With the backend running and `GEMINI_API_KEY` set in `.env`:

```bat
venv\Scripts\python.exe scripts\smoke_test.py
```

Drives register -> login -> upload -> report -> clause detail -> graph -> eval metrics against the
real API. Exits non-zero on failure. If `GEMINI_API_KEY` is not set, it prints a clear SKIP message
instead of failing, since the full pipeline needs the real API.

## Evaluation

```bat
venv\Scripts\python.exe ml\eval.py
```

Writes `experiments/eval/metrics.json`. The predatory-detection half runs with no API key; the
CUAD classification half needs `GEMINI_API_KEY` (it calls the embeddings API for each held-out
example, plus a one-time centroid build the first time it runs).

## Production build check

```bat
cd frontend
npm run build
```

## Ports

Fixed per this project's conventions: backend **8106**, frontend **5106**. Configurable via
`.env` (`BACKEND_PORT`, `FRONTEND_PORT`) if you need to change them.

## Troubleshooting

- **"GEMINI_API_KEY is not configured"** on upload: set the key in `.env` and restart `run.bat`.
- **Port already in use**: another process is bound to 8106 or 5106; stop it or change the port in
  `.env` (and re-run `setup.bat` is not required, just restart `run.bat`).
- **CUAD file missing**: run `venv\Scripts\python.exe scripts\download_data.py`.
