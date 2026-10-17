# How to run

The project has two front doors. Use the new React app; the original Flask pages still work.

## New app (React + FastAPI) - ports 8303 / 5303

Windows, one command:

```
run.bat
```

It creates `venv/` and installs `requirements.txt` on first run, installs `frontend/node_modules`, starts the API on
**http://127.0.0.1:8303** and the web app on **http://127.0.0.1:5303**, then opens the browser.
Ports are read from `.env` (copy `.env.example` if it is missing).

Manual start:

```
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m uvicorn backend.main:api --port 8303

cd frontend
npm install
npm run dev          # http://127.0.0.1:5303
npm run build        # production build into frontend/dist
```

The trained models were saved with scikit-learn 1.8.0, so use the pinned `requirements.txt`
(an older scikit-learn fails on `predict_proba`).

### API endpoints (`backend/main.py`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness |
| GET | `/api/diseases` | the four conditions with best model + accuracy |
| GET | `/api/diseases/{diabetes\|heart\|liver\|kidney}` | form fields, metrics, all algorithm scores |
| GET | `/api/diseases/{d}/sample?outcome=0\|1` | a real row from `data/` to pre-fill the form |
| POST | `/api/predict/{d}` | `{"values": {...}}` -> risk class, confidence, model, accuracy |
| GET | `/api/report` | full training report |
| GET | `/api/datasets` | row counts and class balance of `data/*.csv` |

`backend/main.py` imports the models and metadata from `app.py`; the prediction maths is identical to the Flask pages.

### Checks

```
venv\Scripts\python scripts\smoke_test.py       # API smoke test (backend must be running)
pip install playwright && playwright install chromium
python scripts\capture_screens.py               # walks every screen, fails on console errors, writes docs/screenshots/
```

## Original Flask app - port 5000

```
venv\Scripts\python app.py        # http://127.0.0.1:5000
```

## Retraining (optional)

```
venv\Scripts\python generate_data.py
venv\Scripts\python train_models.py
```
