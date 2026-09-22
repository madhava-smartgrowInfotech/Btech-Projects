# CivicPulse

AI decision support for public grievance offices. CivicPulse understands complaints in **English, Hindi
and Hinglish**, predicts **priority** and **resolution time**, recommends the **responsible department**
and **explains every suggestion**. Officers make the final decision, and their overrides retrain the model.

## Features

- **Complaint intake** - text in any of the three languages, photo and map pin; tracking ID and a live status page.
- **Classification** - 15 categories and 8 departments (TF-IDF + Logistic Regression); Gemini extracts place,
  issue, affected people, hazards and duration as schema-validated fields.
- **Priority** - Low / Medium / High / Critical from the text, multilingual urgency cues and category (XGBoost).
- **Resolution time** - expected days learned from ~290k real NYC 311 service requests, with an SLA-breach flag.
- **Explanations** - LIME words behind the category, SHAP factors behind priority and time.
- **Officer workbench** - accept or override each suggestion with a reason; overrides become labels; one-click retrain with before / after metrics.
- **Hotspot map and analytics** - ward hotspots, recurring issues, SLA compliance by department, category trends, live refresh.
- **Draft reply** - Gemini drafts a reply in the citizen's language for the officer to edit and send.

Stack: React + Vite + Tailwind + Leaflet · FastAPI + SQLAlchemy + SQLite · scikit-learn, XGBoost, LIME, SHAP · Gemini.

## Quick start (Windows)

```bat
setup.bat          :: venv, Python + npm packages, .env
notepad .env       :: paste GEMINI_API_KEY (https://aistudio.google.com/apikey)
run.bat            :: API on :8201, web app on :5201, opens the browser
```

Needs Python 3.11, Node.js 20+ and Git. Full instructions: [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Demo logins

| Role | Email | Password |
|---|---|---|
| Citizen | citizen@civicpulse.local | Citizen@123 |
| Officer | officer@civicpulse.local | Officer@123 |
| Admin | admin@civicpulse.local | Admin@123 |

The demo database contains 700 **sample** complaints (real complaint texts from held-out data, generated
wards and timelines). They are marked with a "Sample" badge.

## Evaluation results

Held-out data, model v1 (`python ml/eval.py` -> [experiments/eval/metrics.json](experiments/eval/metrics.json)):

| Objective | Result |
|---|---|
| Category (9,459 complaints) | **82.9%** accuracy, macro-F1 0.786 (majority baseline 35.9%) |
| Category by language | English 82.7% · Hindi 82.8% · Hinglish 83.3% |
| Department recommendation | **84.9%** top-1 · **98.0%** top-3 |
| Priority (4 levels) | **79.7%** accuracy, macro-F1 0.681, 99.0% within one level |
| Resolution time (48,218 NYC 311 requests) | typical error **1.10 days** (per-category median: 1.24); SLA flag correct 76.8% |
| Explanation faithfulness | removing the top-3 LIME words drops confidence by **0.51** vs 0.02 for random words; SHAP additivity error 5e-6 |
| Human-in-the-loop | 100 simulated officer corrections -> agreement on them 0% -> **99%**, no drop elsewhere (85.8%) |
| Real-time intake | median **82 ms** per complaint including all explanations |

Details and limitations: [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md#evaluation).

## Checks

```bat
venv\Scripts\python scripts\smoke_test.py   :: end-to-end API flow, 25 checks (backend must be running)
cd frontend && npm run build                :: production build
```

## Documentation

| Document | Contents |
|---|---|
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | Problem, users, features, screens |
| [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) | Architecture, pipeline, models, explanations, retraining, data sources and licences, API, evaluation |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Setup, configuration, demo walkthrough, checks, troubleshooting |
| [docs/PLAN.md](docs/PLAN.md) | Build plan |

## Project layout

```
backend/app/      FastAPI app: main.py, db.py, auth.py, routes/, services/
frontend/src/     React screens (pages/), components/, api.js
ml/               train.py, eval.py
scripts/          download_data.py, smoke_test.py
data/raw/         datasets (see docs/02_HOW_IT_WORKS.md#data)
models/           trained models      experiments/  metrics per version + evaluation
```

## Data sources

CivicComp-HiEn (CC BY-SA 4.0), Citizen Grievance Dataset (CC0), Indian Citizen Complaint (MIT) from Kaggle,
and NYC 311 Service Requests (NYC Open Data). Map tiles © OpenStreetMap contributors.
