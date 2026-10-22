# Fake News Detection System Using Feature-Based Optimised MSVM Classification

Lightweight text-classification pipeline: TF-IDF + stylometric features →
PCA extraction → Firefly feature-selection & hyperparameter tuning → MSVM (RBF, OvR,
balanced class weights) with an explicit **PARTIALLY TRUE** class.

## Quickstart
```bash
pip install -r requirements.txt
python train.py                 # demo corpus (900 docs, 3 classes)
python train.py --csv data/my.csv
python predict.py --text "Official report confirmed by experts with verified data"
streamlit run app.py
```

## CSV format
Columns `text` (+ optional `title`) and `label` ∈ {REAL, PARTIALLY TRUE, FAKE} or {0,1,2}.
LIAR 6-way labels and ISOT layouts are auto-mapped (see `src/dataset.py`).

## Structure
```
app.py  train.py  predict.py  requirements.txt
src/preprocessing.py  src/dataset.py  src/firefly.py  src/pipeline.py
models/  data/
```

## Classes
0 = REAL · 1 = PARTIALLY TRUE · 2 = FAKE

## React frontend (TruthGlow, kit V1 Aurora Glass)
A web UI over the same model lives in `frontend/` (React + Vite + Tailwind) with a thin FastAPI layer in `backend/`.
The Streamlit app (`streamlit run app.py`) and the CLI still work unchanged.

Double-click `run.bat` (backend on 8406, frontend on 5406). Details: `docs/03_HOW_TO_RUN.md`, plan and checklist: `docs/FRONTEND_PLAN.md`.
