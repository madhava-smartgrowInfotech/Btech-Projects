# RetinaGuard - Build Plan

**Architecture:** React + Vite (5216) -> `/api` proxy -> FastAPI (8216) -> SQLite (`data/app.db`).
Backend services: `preprocess` (green channel, CLAHE, resize 128, normalise, blur/illumination check) ->
`wavelet` (2-level Haar, PyWavelets) -> `retina_model` (LeNet, PyTorch CPU, input = stacked sub-bands) ->
`explain` (Grad-CAM + Frangi vessel map) ; `heart_model` (Random Forest + SHAP TreeExplainer) ;
`staging` (retina prob + heart prob -> Low / Moderate / High / Very high + recommendations) ; `report` (ReportLab PDF).

**Endpoints:** `POST /api/auth/login`, `GET /api/auth/me`, `GET|POST /api/patients`, `GET /api/patients/{id}`,
`POST /api/screenings/image` (upload -> quality, steps, sub-bands, retina prob, heatmap, vessel map),
`POST /api/screenings/{id}/clinical` (form -> heart risk + SHAP + combined stage), `GET /api/screenings`,
`GET /api/screenings/{id}`, `GET /api/screenings/{id}/report` (PDF), `GET /api/metrics`, `GET /api/samples`, `GET /api/health`.

**Tables:** `users` (email, name, role clinician|technician, password hash), `patients` (code, name, age, sex),
`screenings` (patient, user, image paths, quality, retina prob, clinical json, heart prob, shap json, stage, created).

**Screens:** Landing, Login, New screening (fundus + clinical form), Result (steps, wavelet view, heatmap, vessel map,
risk stage), Report (PDF preview/download), Patients & history, Model performance.

**Data:**
- Hypertension & Hypertensive Retinopathy Dataset (Kaggle, CC BY-NC 4.0, ~1 GB) -> `data/raw/` (git-ignored),
  small labelled sample in `data/sample/`, `scripts/download_data.py` (kagglehub).
- Heart Disease Dataset (Kaggle johnsmith88 / UCI Cleveland, 1025 rows) -> committed in `data/heart/`.

**Training (CPU):** LeNet ~15 epochs on 128x128 wavelet stacks; RF 300 trees. Models in `models/`,
metrics in `experiments/`; `ml/eval.py` -> `experiments/eval/metrics.json` (acc, sens, spec, F1, ROC-AUC, confusion matrices).

**Demo logins:** clinician@retinaguard.local / technician@retinaguard.local (password in README, seeded on first run).
