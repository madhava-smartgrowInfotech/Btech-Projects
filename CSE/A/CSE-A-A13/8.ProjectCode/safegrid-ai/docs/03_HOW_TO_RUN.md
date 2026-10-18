# How to run SafeGrid-AI

Everything lives in this folder (`safegrid-ai/`). Ports: **API 8313**, **console 5313**.

## One click (Windows)

Double-click **`run.bat`**. It will:

1. check that Python 3.10+ and Node.js 18+ are installed,
2. create `backend\.venv` and install `backend\requirements.txt` (first run takes a few minutes - pandapower is large),
3. create `backend\.env` from the example file (mock LLM, no API key needed),
4. install the frontend packages (first run only),
5. start the API in its own window and the React console in the current one, and open http://localhost:5313.

Sign in with the demo account: **operator@safegrid.ai** / **SafeGrid@2026** (or press *Continue with the demo account*).
The demo sign-in only gates the browser session; the API itself has no user accounts.

To stop: press Ctrl+C in the console window and close the "SafeGrid-AI API" window.

## Changing ports

Edit `.env` in this folder (copy `.env.example` first if it is missing):

```
BACKEND_PORT=8313
FRONTEND_PORT=5313
```

`run.bat` and the Vite dev server both read it. The dev server proxies `/api` and `/ws` to the backend, so the browser only talks to one origin.

## Manual start

```bash
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate                 # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                 # macOS/Linux: cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8313

# frontend (second terminal)
cd frontend
npm install
npm run dev                            # http://localhost:5313
```

API docs: http://127.0.0.1:8313/docs · health check: http://127.0.0.1:8313/api/health

## Using the console

1. Pick a scenario (try **Malicious / invalid AI action**), an agent brain and a seed in the run controls at the top of every screen.
2. **Start** streams the run live (playback speed is adjustable), **Step** advances one step, **Reset** loads a fresh run.
3. Watch the **Dashboard**, **Grid view**, **Agent monitor**, **Safety shield**, **Power flow** and **Explainability** screens update.
4. On **Safety shield**, craft your own proposal (for example export 1000 kW) and see how the shield decides - nothing is applied to the grid.
5. On **Scenarios**, run any scenario to completion, or run the strategy comparison.

## Checks

```bash
python scripts/smoke_test.py          # end-to-end API check (backend must be running)
cd backend && pytest                  # backend unit tests
cd frontend && npm run build          # production build into frontend/dist
python scripts/capture_screens.py     # regenerate docs/screenshots (needs: pip install playwright && playwright install chromium)
```

## Troubleshooting

- **Port already in use**: `netstat -ano | findstr :5313` then `taskkill /PID <pid> /F`, or change the port in `.env`.
- **"The SafeGrid API is not reachable" banner**: the backend window is not running or still starting (pandapower takes ~10 s to import). Press *Retry*.
- **Real LLM**: set `LLM_PROVIDER=api`, `LLM_API_KEY` and `LLM_MODEL` in `backend\.env`, then pick *Real LLM (API)* as the agent brain. Without a key, agents use the labelled fallback policy.
