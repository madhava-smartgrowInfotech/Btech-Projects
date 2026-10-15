# PulmoVision - How to run

## Requirements

- Windows 10/11, **Python 3.11+**, **Node.js LTS** (20 or newer), Git
- About 3 GB free disk space (CPU PyTorch + packages)
- Internet access for the first setup and for the AI assistant (Gemini)

## 1. Setup (once)

```bat
cd 8.ProjectCode
setup.bat
```

This creates `venv\`, installs the Python packages (CPU PyTorch) and the frontend packages.
`.env` is already in the repository with the Gemini key and security keys. If it is missing, `setup.bat` copies `.env.example` to `.env`; then fill in:

| Key | Meaning |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio key for the assistant and report text |
| `GEMINI_MODEL`, `GEMINI_FALLBACK_MODELS` | Main model and comma-separated fallbacks used when the main model's quota is exhausted |
| `JWT_SECRET` | Any long random string |
| `FERNET_KEY` | `venv\Scripts\python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"` |
| `BACKEND_PORT` / `FRONTEND_PORT` | 8212 / 5212 |

> Keep the same `FERNET_KEY` once you have data - patient records and images are encrypted with it.

## 2. Run

```bat
run.bat
```

Opens two windows (API on http://127.0.0.1:8212, web app on http://localhost:5212) and the browser.

| Role | Email | Password |
|---|---|---|
| Doctor | doctor@pulmovision.app | Doctor@123 |
| Technician | tech@pulmovision.app | Tech@123 |

The login page has one-click buttons for both accounts.

## 3. Try it

1. Sign in as the doctor -> **New scan** -> register a patient (right panel).
2. Upload `data\sample\xray\Tuberculosis\<any>.png` -> lung mask, heatmap, "Tuberculosis" with confidence and severity.
3. Upload a CT slice from `data\chest_ct\test\adenocarcinoma\` -> "Adenocarcinoma" with heatmap.
4. On the result page ask the assistant "What should happen next?" -> **Report** -> choose Telugu -> **Download PDF**.
5. Upload `data\sample\other\photo_1.jpg` -> rejected by the modality check.

## 4. Smoke test and build check

With the app running (`run.bat`):

```bat
venv\Scripts\python scripts\smoke_test.py
cd frontend && npm run build
```

## 5. Re-train and re-evaluate (optional)

```bat
venv\Scripts\python scripts\download_data.py      :: ~1.5 GB from Kaggle
cd ml
..\venv\Scripts\python prepare_data.py            :: splits + cached arrays (~2 min)
..\venv\Scripts\python train.py modality
..\venv\Scripts\python train.py xray              :: CPU, about 25-40 min
..\venv\Scripts\python train.py ct
..\venv\Scripts\python train.py unet
..\venv\Scripts\python eval.py                    :: writes experiments\eval\metrics.json
```

On a Kaggle GPU: `python scripts\make_notebook.py`, then on kaggle.com: New Notebook -> File -> Import Notebook (`notebooks\pulmovision_kaggle.ipynb`) -> Add Data (the three datasets in `docs\04_DATASET.md`) -> Settings -> Accelerator: GPU -> Run All -> download the output and copy `models\` and `experiments\` into this folder.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Port 5212 is already in use` | Another copy is running - close its window, or change `FRONTEND_PORT` in `.env` |
| Assistant says "AI assistant unavailable (... HTTP 429)" | The Gemini free-tier quota is used up; wait, or add another model to `GEMINI_FALLBACK_MODELS`. Reports are still produced, without the AI section |
| First analysis is slow | Models load on the first request (a few seconds) |
| `JWT_SECRET and FERNET_KEY must be set` | Fill them in `.env` (see the table above) |
