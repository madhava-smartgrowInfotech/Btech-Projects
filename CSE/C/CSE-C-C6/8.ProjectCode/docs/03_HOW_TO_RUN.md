# How to run

The product has two ways to run. Both use the same trained model (`models/msvm_model.pkl`).

## A. The new web app (recommended)

| Part | Folder | Port |
|---|---|---|
| API (FastAPI, wraps `src/`) | `backend/` | **8406** |
| Web UI (React + Vite) | `frontend/` | **5406** |

Ports live in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`; copy `.env.example` if the file is missing).

### One click
Double-click **`run.bat`**. It checks Python (3.11+) and Node.js (20+), builds `.venv` and installs the backend
packages (first run only, a few minutes), runs `npm install` in `frontend/` (first run only), starts both servers
in two minimised windows and opens http://localhost:5406. Close those two windows to stop.

If a `.venv` copied from another computer does not work here, `run.bat` rebuilds it.

### By hand
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
.venv\Scripts\python -m uvicorn backend.main:app --port 8406

cd frontend
npm install
npm run dev            # http://localhost:5406
```
Open http://localhost:5406 (use `localhost`, not `127.0.0.1`).

### Screens
Landing `/` · Detect `/app` · Batch check `/app/batch` · Model analytics `/app/analytics` · Retrain `/app/retrain` · About `/app/about`.

### API
`GET /api/health` · `GET /api/model` · `GET /api/samples` · `POST /api/predict` · `POST /api/batch/preview` ·
`POST /api/batch/run` · `POST /api/retrain` + `GET /api/retrain/{job_id}`. Interactive docs: http://127.0.0.1:8406/docs.

### Checks
```bash
python scripts/smoke_test.py          # starts its own server on port 8496 with a COPY of the model
cd frontend && npm run build          # type-check + production build
python scripts/capture_screens.py     # screenshots into docs/screenshots/ (needs the app running)
```

### Notes
* **Retraining replaces `models/msvm_model.pkl`** (same as the Streamlit tab). Keep a copy if you want to return to the shipped model.
* The shipped model was pickled with scikit-learn 1.9, so use the packages `run.bat` installs; an older scikit-learn (for example 1.5) may not load it.
* If no model file exists, the backend trains a small demo model on first start (about a minute).

## B. The original Streamlit app (unchanged)
```bash
pip install -r requirements.txt
python train.py
streamlit run app.py
```
