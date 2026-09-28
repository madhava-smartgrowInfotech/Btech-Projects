# BioSight - How to run

## Requirements
- Windows 10/11, **Python 3.11+**, **Node.js 18+ (LTS)**, Git
- Internet access, used for Gemini reports and for the first `pip` / `npm` install
- No GPU is needed. The trained models are committed and run on the CPU.

## 1. Set up (once)
Double-click **`setup.bat`** in the `8.ProjectCode` folder. It does three things:
- creates `venv/` and installs PyTorch (CPU) plus `requirements.txt`
- copies `.env.example` to `.env` if `.env` is missing (the committed `.env` already holds the Gemini key)
- runs `npm install` in `frontend/`

## 2. Start
Double-click **`run.bat`**. It opens two windows:
- the API on **http://127.0.0.1:8108** (docs at http://127.0.0.1:8108/docs)
- the web app on **http://localhost:5108**, which also opens in your browser

Sign in with the demo account **demo@biosight.app / Demo@1234**, or register a new one.

## 3. Try the demo
1. **MRI analysis:** pick a sample slice with a red dot and click **Analyse slice**. You get the tumour overlay, area, Dice against the expert mask, and a structured report. You can also upload your own PNG/JPG/TIF slice.
2. **Label efficiency:** the chart compares 10% and 100% of masks, with the JEPA model against the U-Net, MAE and scratch baselines.
3. **DNA analysis:** click a sample sequence (for example *trinucleotide repeat*), then **Classify sequence**.
4. **STR matching:** click **Sample query**, then **Search database**. You get ranked references with likelihood ratios and a report.
5. **Model performance:** shows every evaluation number.

## 4. Smoke test (with the app running)
```
venv\Scripts\python scripts\smoke_test.py
```
It drives the real API end to end: login, MRI segmentation, DNA classification, STR matching, reports and history. It prints `SMOKE TEST PASSED` when everything works.

## 5. Re-train (optional)
```
venv\Scripts\python scripts\download_data.py       # full LGG MRI + DNA datasets from Kaggle (~1 GB)
venv\Scripts\python ml\prepare_data.py             # 128x128 arrays + committed sample
venv\Scripts\python ml\train_mri.py --stage all    # F1-F3 (about 2-3 h on CPU)
venv\Scripts\python scripts\gen_repeat_sequences.py
venv\Scripts\python ml\train_dna.py                # F4 (about 30 min on CPU)
venv\Scripts\python scripts\gen_str_db.py          # F5 database
venv\Scripts\python ml\eval.py                     # experiments/eval/metrics.json
```
To train on a GPU, import `notebooks/biosight_kaggle_training.ipynb` into Kaggle. Add the dataset *mateuszbuda/lgg-mri-segmentation*, set the accelerator to GPU, then Run All. Copy the output `models/*.pt` into `models/` and `experiments/*` into `experiments/`.

## Troubleshooting
| Problem | Fix |
|---------|-----|
| `Port 5108 is already in use` | Close the other window running BioSight, or find the process with `netstat -ano \| findstr 5108`. |
| "Cannot reach the BioSight API" | Check that the API window is open and shows `Uvicorn running on http://127.0.0.1:8108`. |
| Report says "AI report service unavailable" | Gemini was busy or unreachable. The model results are still real. Retry later, or check `GEMINI_API_KEY` in `.env`. |
| `ModuleNotFoundError` | Run `setup.bat` again. |
