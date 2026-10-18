# How to run AutoSecAI

## One command (Windows)

    run.bat

It installs the Python and npm dependencies on first run, starts the API on **8311** and the web app on **5311**
(both from `.env`), and opens http://localhost:5311.

**Demo sign-in:** `demo@autosecai.dev` / `Demo@1234` (or press "Use the demo account" on the sign-in page). You can also
create your own account; accounts are stored locally in `data/app.db`.

## Manual

    pip install -r requirements.txt
    python -m backend                  # API  -> http://127.0.0.1:8311  (docs at /docs)
    cd frontend && npm install && npm run dev   # UI -> http://localhost:5311

The first launch trains the models (about 30 s) if `autosecai/artifacts/` is missing.

## Checks

    python -m pytest tests -q          # 17 tests: engine + API
    python scripts/smoke_test.py       # API smoke test (API running)
    pip install playwright && playwright install chromium
    python scripts/ui_flows.py         # drives the real UI through every feature
    python scripts/capture_screens.py  # rewrites docs/screenshots/*.png
    cd frontend && npm run build       # production build

## Optional

- **LLM explanations:** Settings > Anthropic API key (or set `ANTHROPIC_API_KEY` for the API process). Off by default; without it everything runs offline.
- **GitHub token:** Settings > GitHub token, for private repositories and higher rate limits.
- **Original Streamlit UI:** `run_streamlit.bat` (needs `streamlit` and `plotly`; the new app does not).

## Ports

Fixed in `.env`: `BACKEND_PORT=8311`, `FRONTEND_PORT=5311`. Vite proxies `/api` to the backend, so the browser only talks to 5311.
