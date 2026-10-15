# How to run ForgetSafe

## Requirements
- Python 3.10+ (no third-party packages)
- Node.js 18+ and npm (for the React frontend)

## One command (Windows)
```
run.bat
```
Starts the API on **http://127.0.0.1:8109** and the UI on **http://127.0.0.1:5109** (ports come from `.env`:
`BACKEND_PORT`, `FRONTEND_PORT`; copy `.env.example` to `.env` if it is missing). It installs `frontend/node_modules` on first run.

## Manually
```
python app.py --port 8109          # API (also serves the original single-page UI at /)
cd frontend
npm install
npm run dev                        # UI on 5109, proxies /api to 8109
```
Production build: `cd frontend && npm run build` (output in `frontend/dist`, preview with `npm run preview`).

## Original interfaces (unchanged)
- `python app.py` - original localhost UI on port 8000
- `python app.py --desktop` - Tkinter GUI
- `python app.py --demo` - terminal demonstration

## Tests
```
python -m unittest discover -s tests -v     # engine + API unit tests
python scripts/smoke_test.py                # end-to-end API flow on a temporary server
```

## Screens
`/` landing - `/app` dashboard - `/app/training` - `/app/unlearning` - `/app/explorer` - `/app/audit`

The runtime audit ledger is stored in `data/audit_log.jsonl` (git-ignored).
