# How to Run FinSight AI (React frontend)

## Running the React frontend (ports 8409 / 5409)

`.env` holds the ports: `PORT=8409` (Flask API) and `FRONTEND_PORT=5409` (React app). Defaults apply if it is missing.

**Automatic:** double-click `run.bat`. It creates `.venv`, installs requirements, trains the model if missing,
runs `npm install` and `npm run build` in `frontend/` (first run only), starts the API in a second window and
serves the frontend, then opens http://localhost:5409. Needs Python 3.11+ and Node.js 18+.

**Manual:**

```text
python -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
python scripts	rain.py          :: only if modelsest_model.pkl is missing
python run.py                    :: API on http://localhost:8409

cd frontend
npm install
npm run dev                      :: http://localhost:5409 (proxies /api to 8409)
```

For a production-style run use `npm run build` then `npm run preview` (also port 5409).
The original server-rendered Flask pages are unchanged and still available at http://localhost:8409.

**Checks** (with both servers running): `python scripts\smoke_test.py` and `python scripts\capture_screens.py`
(the latter needs `pip install playwright`; it uses installed Chrome, else run `playwright install chromium`).

See `HOW_TO_RUN.md` for the Docker method and troubleshooting.
