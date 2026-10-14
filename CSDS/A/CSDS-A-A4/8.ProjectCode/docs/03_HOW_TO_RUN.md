# How to run HubOptima

HubOptima has two interfaces over the same `hublocator` package:

| Interface | Port | Start with |
|---|---|---|
| **React app** (V4 Soft Pastel Calm) + FastAPI layer | web **5104**, API **8104** | `run.bat` |
| Classic Flask app (original) | 5000 | `python run.py serve` |

## Requirements

- Python 3.10+ with `pip install -r backend/requirements.txt` (this includes the original `requirements.txt` plus FastAPI and uvicorn)
- Node.js 18+ (for the React app)

## One click (Windows)

Double-click `run.bat` in `8.ProjectCode`. It:

1. reads `BACKEND_PORT` / `FRONTEND_PORT` from `.env` (defaults 8104 / 5104),
2. installs the Python and npm packages if they are missing,
3. starts the API window (`python -m uvicorn backend.main:app --port 8104`) and waits for `/api/health`,
4. starts the web window (`npm run dev` in `frontend/`) and opens http://localhost:5104.

Stop it by closing the two windows.

## Manually

```bash
# terminal 1 - API (from 8.ProjectCode)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8104

# terminal 2 - web app
cd frontend
npm install
npm run dev            # http://localhost:5104  (proxies /api to :8104)
```

Production build: `cd frontend && npm run build` → `frontend/dist/` (serve with `npm run preview`, which also proxies `/api`).

API docs: http://localhost:8104/docs

## Screens

| Route | Screen |
|---|---|
| `/` | Landing page |
| `/app` | Dashboard |
| `/app/forecast` | Random Forest forecast (retrain, metrics, importance, next-month forecast, back-test) |
| `/app/plan` | Plan hubs (parameters, KPIs, network map, utilisation, search log, allocation) |
| `/app/compare` | Proposed vs traditional methods + scalability benchmark (background jobs) |
| `/app/rolling` | Rolling re-optimisation vs a static plan (background job) |
| `/app/regions` | The 90 demand regions (read-only) |

Dark mode is in the top bar (remembered per browser; follows the OS until you choose).

## Tests

```bash
python tests.py                                       # original smoke tests (data, forecast, optimisation, Flask app)
python scripts/smoke_test.py                          # API layer, in-process
python scripts/smoke_test.py --url http://127.0.0.1:8104 --frontend http://localhost:5104   # against running servers
```

## Notes

- Retraining the forecaster, running a comparison, the scalability benchmark or the rolling horizon overwrite `models/` and `results/` exactly as the CLI and the Flask app do.
- The CLI (`python run.py ...`) is unchanged; see the README.
