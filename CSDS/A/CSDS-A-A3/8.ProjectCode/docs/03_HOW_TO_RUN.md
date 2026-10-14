# How to run PhishGuard

| Part | Port | Started by |
|---|---|---|
| API (Flask app + read-only additions) | **8103** | `python backend/server.py` |
| React frontend (Vite) | **5103** | `npm run dev` in `frontend/` |

Ports are read from `.env` (`BACKEND_PORT`, `FRONTEND_PORT`).

## Prerequisites

- Python 3.10+ with `pip install -r requirements.txt`
- Node.js 18+ (npm)

## One command (Windows)

```bat
run.bat
```

It trains the models once if `models/best_model.joblib` is missing, installs the frontend dependencies on first
run, opens the API and the UI in two windows and launches http://127.0.0.1:5103.

## Manually

```bash
pip install -r requirements.txt
python run.py train                 # only if models/ is empty (~30 s)

python backend/server.py            # terminal 1 -> http://127.0.0.1:8103/api/health

cd frontend
npm install                         # first time only
npm run dev                         # terminal 2 -> http://127.0.0.1:5103
```

The Vite dev server proxies `/api` and `/retrain` to the API, so the browser only talks to port 5103.

Production build: `cd frontend && npm run build && npm run preview` (serves `dist/` on 5103 with the same proxy).

## Screens

| URL | Screen |
|---|---|
| `/` | Landing page (3D hero, how it works, live numbers) |
| `/app/check` | Check a URL (single or batch file upload) |
| `/app/report` | Report a URL as phishing / safe |
| `/app/intel` | Crowdsourced threat intelligence, public feed sync |
| `/app/models` | Model comparison, confusion matrices, feature importance, retrain |
| `/app/activity` | Check log with probability trend and verdict mix |

## Tests

```bash
python tests.py                     # original unit + Flask tests
python scripts/smoke_test.py        # end-to-end API flow used by the React UI
```

## The original interface

The Flask pages are unchanged and still available: `python run.py serve` (port 5000), or directly on the API
port at http://127.0.0.1:8103/ while `backend/server.py` runs. The CLI commands in the README
(`check`, `report`, `sync`, `retrain`, `download`) work as before.

## Notes

- Retraining from the Models screen takes one to several minutes depending on the machine; the topbar shows
  a "Retraining" badge until the new model is hot-loaded.
- Feed sync needs internet access; a failed feed is reported per feed and the app keeps working offline.
- Runtime data (`data/threat_intel.db`) is created on first use and is not committed.
