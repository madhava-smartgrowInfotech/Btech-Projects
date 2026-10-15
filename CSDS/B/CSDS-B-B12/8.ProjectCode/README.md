# PulmoVision

**Explainable screening of lung diseases from chest X-rays and CT scans** - lung segmentation, Grad-CAM heatmaps, calibrated confidence, severity, an AI clinical assistant and PDF reports in English, Hindi and Telugu.

> PulmoVision is a clinical decision-support tool. Every AI result is an aid for a qualified professional, not a final diagnosis.

## Features

- **Upload + modality check** - PNG / JPG / DICOM; recognises chest X-ray vs chest CT and rejects colour photos, non-images and non-chest images.
- **Preprocessing** - resize, non-local-means denoising, CLAHE and normalisation, shown step by step.
- **Lung segmentation** - U-Net (MobileNetV2 encoder) lung mask overlaid on X-rays.
- **Classification** - EfficientNet-B0 transfer learning. X-ray: COVID-19, viral pneumonia, lung opacity, tuberculosis, normal. CT: adenocarcinoma, large-cell carcinoma, squamous-cell carcinoma, normal.
- **Explanation + severity** - Grad-CAM heatmap, temperature-calibrated confidence, severity from the affected lung area.
- **AI assistant + multilingual reports** - Gemini answers follow-up questions per scan; PDF reports in English, Hindi or Telugu.
- **Secure records** - encrypted patient data and images at rest (Fernet), doctor / technician roles, audit log.
- **Evaluation** - Dice / IoU, accuracy, macro-F1, per-class sensitivity and confusion matrices, visible in the app.

## Quick start (Windows)

```bat
setup.bat      :: once - Python venv, CPU PyTorch, frontend packages
run.bat        :: starts the API (8212) and web app (5212) and opens http://localhost:5212
```

Requires Python 3.11+, Node.js LTS and Git. `.env` (Gemini key, JWT and encryption keys) is included; `.env.example` lists every setting.

### Demo login

| Role | Email | Password |
|---|---|---|
| Doctor | doctor@pulmovision.app | Doctor@123 |
| Technician | tech@pulmovision.app | Tech@123 |

Sample images: `data/sample/xray/<class>/`, CT slices in `data/chest_ct/test/`, non-chest photos in `data/sample/other/`.

## Evaluation results

RESULTS_TABLE

## Tech stack

React + Vite + Tailwind CSS, FastAPI, SQLAlchemy + SQLite, PyTorch, timm (EfficientNet-B0), segmentation-models-pytorch (U-Net), pytorch-grad-cam, pydicom, ReportLab (+ HarfBuzz shaping, Noto fonts), cryptography (Fernet), PyJWT + bcrypt, Google Gemini API.

## Project layout

```
backend/app/     FastAPI app: main.py, db.py, auth.py, routes/, services/ (pipeline, gemini, report, storage)
frontend/src/    React pages and components
ml/              prepare_data.py, train.py, eval.py
scripts/         smoke_test.py, download_data.py, make_notebook.py
notebooks/       Kaggle GPU training notebook
data/            chest_ct/ (full CT dataset), sample/ (X-ray, lung-mask and non-chest samples)
models/          trained weights       experiments/   training logs, splits, eval/metrics.json + plots
docs/            documentation
```

## Documentation

| Document | Contents |
|---|---|
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | Problem, users, features, screens |
| [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) | Architecture, pipeline, security, API, data, training |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Setup, run, smoke test, re-training, troubleshooting |
| [docs/04_DATASET.md](docs/04_DATASET.md) | Dataset sources, licences and credits |
| [docs/PLAN.md](docs/PLAN.md) | Build plan |
