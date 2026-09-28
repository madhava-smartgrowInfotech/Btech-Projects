# RetinaGuard - How to run

## Requirements

- Windows 10/11
- Python 3.11 or newer - https://www.python.org/downloads/ (tick "Add Python to PATH")
- Node.js LTS - https://nodejs.org/
- Git (optional, to clone)
- About 3 GB of free disk space (PyTorch CPU and packages). No GPU and no API keys are needed.

## First-time setup

1. Open the `8.ProjectCode` folder.
2. Double-click **`setup.bat`** (or run it in a terminal). It will:
   - create `venv/` and install the Python packages (CPU PyTorch, FastAPI, OpenCV, scikit-image, SHAP, ReportLab, ...),
   - create `.env` from `.env.example` with a random `JWT_SECRET`,
   - run `npm install` in `frontend/`.
   The trained models are already in `models/`, so no training is needed.

## Start

Double-click **`run.bat`**. It opens two console windows (API and web app) and then the browser at
http://localhost:5216. Close both console windows to stop.

- Web app: http://localhost:5216
- API: http://localhost:8216 (docs at http://localhost:8216/docs)

Ports are set in `.env` (`BACKEND_PORT=8216`, `FRONTEND_PORT=5216`).

## Sign in

| Role | Email | Password |
|------|-------|----------|
| Clinician | clinician@retinaguard.local | RetinaGuard@123 |
| Technician | technician@retinaguard.local | RetinaGuard@123 |

The demo password comes from `DEMO_PASSWORD` in `.env` and is applied when the accounts are first created.

## Demo walk-through

1. **New screening** -> *New patient*: enter a name, age and sex.
2. Upload a fundus photo, or click one of the labelled sample thumbnails (red tag = retinopathy in the ground truth).
3. Fill the clinical form (age and sex are pre-filled) and click **Run screening**.
4. The **Result** page shows the quality check, the preprocessing steps, the wavelet sub-bands (level 1 / level 2),
   the retinopathy probability with the Grad-CAM heatmap and Frangi vessel map, the heart-disease risk with its SHAP
   factors, and the overall stage with recommendations.
5. **Screening report** opens the PDF; **Download PDF** saves it.
6. **Patients & history** lists every patient and screening; **Model performance** shows the evaluation.

## Checks

With the API running (`run.bat`):

```bat
venv\Scripts\python scripts\smoke_test.py
cd frontend && npm run build
```

## Retrain and re-evaluate (optional)

```bat
venv\Scripts\python scripts\download_data.py   :: full datasets into data\raw (about 1 GB, no Kaggle token needed)
venv\Scripts\python ml\train_heart.py          :: seconds
venv\Scripts\python ml\train_retina.py         :: about 5 minutes on CPU
venv\Scripts\python ml\eval.py                 :: writes experiments\eval\metrics.json
venv\Scripts\python scripts\make_sample.py     :: rebuilds data\sample\fundus from the test split
```

If Kaggle ever asks for credentials, create a token at https://www.kaggle.com/settings -> API and put
`KAGGLE_USERNAME` / `KAGGLE_KEY` in `.env`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Port 5216 is already in use` | Another app is using the port: close it, or change `FRONTEND_PORT` in `.env` |
| Web app says it cannot reach the server | The API window must be running; check it for errors |
| `JWT_SECRET is not set` | Run `setup.bat`, or copy `.env.example` to `.env` and set `JWT_SECRET` |
| `Retina model not trained yet` | `models/lenet_hr.pt` is missing: run the retrain steps above |
| Start again with an empty database | Stop the app and delete `data\app.db` and `data\uploads\` |
