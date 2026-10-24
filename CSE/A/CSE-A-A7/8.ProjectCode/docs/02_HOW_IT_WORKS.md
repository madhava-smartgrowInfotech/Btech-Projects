# How ATHENA works

## Architecture
```
Browser (React + Vite, port 5307)  --/api proxy-->  FastAPI (port 8307)
                                                     |-- services/extract.py   report reading
                                                     |-- services/features.py  fused record definition
                                                     |-- services/triage.py    XGBoost + calibration + SHAP
                                                     |-- services/pdf.py       triage summary PDF
                                                     '-- SQLite (data/app.db)  users, patients, overrides
```

## Report reading (`extract.py`)
1. **PDF**: the text layer of each page is read with pypdf. A page with no text layer falls back to OCR on its embedded image.
2. **Image (PNG/JPG)**: local OCR with RapidOCR (ONNX, no network, no separate install). The image is upscaled for small print, and text boxes are put in reading order.
3. **Parsing**: wrapped lines are rejoined, then each sentence is matched against a clinical lexicon of 22 symptom, finding and history flags. Matches preceded by a negation ("no", "denies", "without", "negative for") in the same clause are dropped. Spaces in phrases tolerate OCR run-ons ("ofbreath").
4. **Labs**: troponin, lactate, WBC, glucose, creatinine and haemoglobin values are parsed with units and compared with reference ranges; abnormal ones set a flag.
5. Every item keeps the **page number** it was found on.

Gemini is not used. The original spec called for a multimodal LLM for this step; the local reader was chosen so the product runs offline with no API key.

## Fused record (`features.py`)
36 model inputs: 8 vitals (arrival mode coded walk-in 0, transfer 1, ambulance 2) and 28 report flags (22 from text, 6 from lab values).

## Triage model (`ml/train.py`, `triage.py`)
- XGBoost multiclass (220 trees, depth 4) on the 36 inputs, predicting priority 1 to 5.
- **Calibration**: isotonic calibration on a separate 20% calibration split, so the reported confidence is a probability, not a raw score.
- **Risk level**: priority 1-2 High, 3 Moderate, 4-5 Low.
- **SHAP**: TreeExplainer on the same trees; the contribution toward the chosen priority is listed in descending absolute value. Absent flags with negligible effect are hidden.
- Priority is the arg-max of the calibrated probabilities.

## Data (read this)
**The model is trained on synthetic data.** `ml/make_data.py` (seed 7307) simulates 6,000 patients from seven clinical archetypes (minor, cardiac, respiratory, neuro, trauma, infection, abdominal), draws vitals and report flags per archetype, then computes a severity score from clinical rules and adds noise. That score is cut into priorities 1 to 5 and plays the role of the clinician-recorded outcome.

Consequences:
- Reported accuracy measures recovery of a known rule, not agreement with real clinicians.
- Priority 1 is rare (about 5%) and has the lowest recall.
- Real triage records would give different numbers. `scripts/download_data.py` is the entry point for the Kaggle dataset **Hospital Triage and Patient History Data** (https://www.kaggle.com/datasets/maalona/hospital-triage-and-patient-history-data, licence not stated). It is **not used** in this build and is untested.

Committed data: `data/sample/triage_synthetic.csv` (the 6,000 rows), `data/sample/holdout_sample.csv` (hold-out rows used to seed the demo queue), and `data/sample_reports/` (12 generated report files with `expected.json`). Sample reports and cases are labelled as sample data in the UI.

## Evaluation (`experiments/metrics.json`, `experiments/eval/metrics.json`)
Hold-out split: 1,200 cases the model never saw.

| Metric | Value |
|---|---|
| Accuracy (exact priority) | 69.4% |
| Within one priority level | 99.7% |
| Macro F1 | 0.670 |
| Recall P1 / P2 / P3 / P4 / P5 | 43.9% / 54.0% / 72.8% / 71.9% / 82.8% |
| Model time per patient | about 0.01 ms |
| End to end per patient (read report + model) | mean 1.3 s, median 0.02 s (PDFs instant, image scans 4-6 s on CPU) |
| Report reading on the 12 sample reports | precision 100%, recall 100% |

Seconds per patient is also measured live: the performance page averages the processing time of patients entered through the app.

## Clinician override
`POST /api/patients/{id}/override` stores who, the old and new priority, `accept` or `change`, and the reason (required for a change). The patient's current priority updates, the model's original suggestion is kept, and the queue reorders. The performance page reports the share of reviews that kept the model's priority.

## API
All routes are under `/api`; everything except `health`, `public/stats` and `auth/login` needs a bearer token.

| Method | Path | Purpose |
|---|---|---|
| GET | /health | liveness, model present |
| GET | /public/stats | headline model numbers for the landing page |
| POST | /auth/login | sign in, returns token |
| GET | /auth/me | current user |
| GET | /samples, /samples/{file} | list and fetch the generated sample reports |
| POST | /reports/extract | upload PDF or image, get structured findings |
| POST | /patients | vitals + report, returns priority, confidence, SHAP |
| GET | /patients | queue, ordered by priority then arrival |
| GET | /patients/{id} | full record |
| GET | /patients/{id}/summary.pdf | triage summary |
| POST | /patients/{id}/override | accept or change the priority |
| GET | /metrics | offline evaluation and live counts |

## Frontend
React 19 + Vite, JavaScript. The design is the shared "Neo Brutal Grid" kit (hard edges, flat colour, no gradients), copied into `frontend/src` so the folder is self-contained. Dark mode, reduced motion, a drawer navigation on small screens and keyboard focus are supported. Chart code and motion libraries are split into lazy chunks.
