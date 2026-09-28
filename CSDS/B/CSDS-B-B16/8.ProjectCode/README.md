# RetinaGuard

RetinaGuard screens retinal fundus images for **hypertensive retinopathy** using Haar wavelet features and a LeNet CNN.
It scores the patient's **heart-disease risk** from clinical parameters, then combines both into one explained
**risk stage** with recommendations and a PDF report.

> Clinical decision support: every AI result is an aid for a qualified professional, not a final diagnosis.

## Features

- **Fundus preprocessing** - green channel, CLAHE, resize and normalisation shown step by step, with a
  blur / illumination quality check
- **Haar wavelet features** - 2-level LL / LH / HL / HH sub-bands highlighting vessels and lesions
- **Retinopathy detection** - a LeNet CNN on the 8 wavelet sub-bands (PyTorch, trains on CPU)
- **Explanation** - Grad-CAM heatmap and Frangi vessel map, with vessel density and width
- **Heart-disease risk** - a Random Forest on 13 clinical parameters, with SHAP top factors
- **Combined risk stage** - Low / Moderate / High / Very high, with follow-up recommendations
- **Screening report** - a one-page PDF with the images, findings, stage and recommendations
- **Patients and history** - screenings stored per patient in SQLite
- **Model performance** - accuracy, sensitivity, specificity, F1, ROC-AUC, confusion matrices and ROC curves

## Quick start (Windows)

```bat
setup.bat    :: venv + pip + npm install + .env
run.bat      :: starts API (8216) and web app (5216) and opens the browser
```

Requirements: Python 3.11+, Node.js LTS. No GPU and no API keys. Full steps: [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Demo login

| Role | Email | Password |
|------|-------|----------|
| Clinician | clinician@retinaguard.local | RetinaGuard@123 |
| Technician | technician@retinaguard.local | RetinaGuard@123 |

Labelled sample fundus images (sample data from the held-out test split) can be picked directly on the
New screening page.

## Evaluation results

Held-out test sets (`python ml/eval.py` -> `experiments/eval/metrics.json`):

| Model | Test cases | Accuracy | Sensitivity | Specificity | F1 | ROC-AUC |
|-------|-----------:|---------:|------------:|------------:|---:|--------:|
| LeNet on Haar wavelets - hypertensive retinopathy | 107 | 64.5% | 65.9% | 63.5% | 60.4% | 0.725 |
| Random Forest - heart disease | 76 | 81.6% | 80.0% | 82.9% | 80.0% | 0.885 |

| Confusion matrix | TN | FP | FN | TP |
|------------------|---:|---:|---:|---:|
| Retinopathy | 40 | 23 | 15 | 29 |
| Heart disease | 34 | 7 | 7 | 28 |

The heart-disease model has a 5-fold cross-validated ROC-AUC of 0.918. The heart data is de-duplicated
(302 unique patients) and its label is aligned with the UCI source. The retinopathy model is a small CPU model trained on 712
images; treat its output as a screening signal. Details are in [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md).

## Tech stack

React + Vite + Tailwind (JavaScript) | FastAPI + SQLAlchemy + SQLite | JWT + bcrypt | PyTorch (CPU) | PyWavelets |
OpenCV | scikit-image | scikit-learn | SHAP | ReportLab

## Project layout

```
backend/app/     FastAPI app: main.py, db.py, auth.py, routes/, services/ (preprocess, wavelet, lenet, retina, heart, staging, report)
frontend/src/    React screens (pages/), shared components, api.js
ml/              train_retina.py, train_heart.py, eval.py
scripts/         smoke_test.py, download_data.py, make_sample.py
data/            heart/heart.csv, sample/fundus/ (labelled sample), raw/ (full data, git-ignored)
models/          lenet_hr.pt, lenet_hr.json, heart_rf.joblib
experiments/     training metrics, splits and eval/metrics.json
docs/            documentation
```

## Documentation

- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, users, features, screens, architecture
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - pipeline, models, staging rules, evaluation, data sources and licences, API
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, run, demo walk-through, retraining, troubleshooting
- [docs/PLAN.md](docs/PLAN.md) - build plan

## Data

- Hypertension & Hypertensive Retinopathy Dataset (Kaggle, CC BY-NC 4.0): a sample is committed and the full set comes from `scripts/download_data.py`
- Heart Disease Dataset (Kaggle / UCI Cleveland): committed in full
