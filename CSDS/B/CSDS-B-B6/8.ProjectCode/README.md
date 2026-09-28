# UniHealth

**One patient-controlled health record across hospitals.** UniHealth provides:
- HL7 FHIR R4 exchange between independent hospital servers
- a Master Patient Index with fuzzy record linkage
- consent the patient can see and revoke, backed by a hash-chained audit ledger
- Random Forest risk prediction
- an AI assistant that explains records in plain language, in the patient's own language

> Clinical decision support only. AI and risk outputs assist qualified professionals and are never a final diagnosis.
> All patient data is synthetic sample data (Synthea).

## Features
- **F1 Three hospitals** - independent FHIR R4 servers (Northbridge General, Riverside Medical Center, Lakeview Clinic), each with its own database and patient IDs, loaded with overlapping Synthea patients.
- **F2 Master Patient Index** - fuzzy matching on name, birth date, gender and phone links one person's records across hospitals, with a confidence score.
- **F3 Consent management** - grant or revoke access per hospital and data category. Each consent is stored as a FHIR `Consent` and written to a hash-chained, tamper-evident ledger.
- **F4 Secure retrieval** - a doctor's request passes a consent check. Parallel FHIR REST calls then fetch the records and merge them into one timeline. Every access is audited.
- **F5 Post-treatment sync** - a hospital records a visit and pushes a FHIR summary Bundle to the platform. The original stays at the hospital.
- **F6 Unified record** - encounters, conditions, medications, labs and allergies in one timeline, downloadable as a FHIR Bundle.
- **F7 Health-risk prediction** - heart-disease and diabetes Random Forests read values from the record and show the top factors behind each score.
- **F8 Assistant and reminders** - Gemini explains lab reports and summarises treatment in the patient's language. Medication and follow-up reminders appear in the app.

## Quick start (Windows)
```
setup.bat        # once: venv, packages, hospital databases, models, npm install
                 # then put your GEMINI_API_KEY in .env  (https://aistudio.google.com/apikey)
run.bat          # starts 3 hospital FHIR servers, the API and the web app, opens http://localhost:5206
```
Ports: web **5206**, API **8206**, hospitals **12061-12063**.

## Demo login (password `demo123`)
| Username | Role |
|---|---|
| `patient` | Patient with records at all three hospitals (`patient2`, `patient3`: two / one hospital) |
| `dr.riverside` | Doctor at Riverside Medical Center (also `dr.northbridge`, `dr.lakeview`) |
| `staff.lakeview` | Hospital records staff (also `staff.northbridge`, `staff.riverside`) |
| `admin` | Platform administrator |

## Evaluation results
From `ml/eval.py` -> [`experiments/eval/metrics.json`](experiments/eval/metrics.json).

**Record linkage (MPI)** - 92 hospital records, 60 real people, 40 true cross-hospital links, threshold 0.80:

| Precision | Recall | F1 | Persons found |
|---|---|---|---|
| 1.000 | 1.000 | 1.000 | 60 / 60 |

At a stricter threshold of 0.90, recall drops to 0.85. The typo-tolerant scoring is what recovers those links.

**Consent enforcement** (3 patients x 3 hospitals, through the live API):

| Check | Correct |
|---|---|
| Denied without consent | 9 / 9 |
| Allowed with consent | 9 / 9 |
| Only consented categories returned | 9 / 9 |
| Denied after revocation | 9 / 9 |

**Tamper-evident ledger** - 50 trials each of editing a detail, editing the actor, deleting an entry and swapping entries: detection rate **100%** for all four, and no false alarms. The live ledger verified intact after every test run.

**Standards and unification** - **11,728 of 11,728** hospital resources pass FHIR R4 validation. The unified record contains 100% of the resources held at each linked hospital (865 items from three hospitals for the main demo patient). Median record retrieval is **75 ms**.

**Risk models** (5-fold cross-validation, CPU, trained in seconds):

| Model | Rows | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| Heart disease (5 record features) | 303 | 0.677 | 0.668 | 0.619 | 0.634 | 0.731 |
| Diabetes (5 record features) | 768 | 0.771 | 0.699 | 0.619 | 0.654 | 0.834 |

The models use only values that exist in a FHIR record, such as blood pressure, cholesterol, glucose, BMI, age and sex. They do not use exercise-test fields. This keeps the heart model usable on real records at a moderate AUC.

**AI assistant** - verified live: the smoke test's "explain the lipid panel in Telugu" check passed with a real Gemini response. Free-tier keys allow about 5 requests per minute per model and a small daily allowance, and Google sometimes returns "high demand". UniHealth then tries the fallback models in `GEMINI_FALLBACK_MODEL` and, if all are busy, shows a clear error within seconds. It never shows a made-up answer.

## Tests
```
venv\Scripts\python scripts\smoke_test.py    # drives the running API through F1-F8
cd frontend && npm run build                 # production build
```

## Tech stack
React + Vite + Tailwind (JavaScript) - FastAPI + SQLAlchemy 2 + SQLite - PyJWT + bcrypt - fhir.resources (R4) - rapidfuzz - scikit-learn - Google Gemini (google-genai).

## Documentation
- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, users, features, screens
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - architecture, linkage, consent ledger, retrieval, sync, models, data sources and licences
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, keys, demo walkthrough, tests, troubleshooting
- [docs/PLAN.md](docs/PLAN.md) - build plan

## Folder layout
```
backend/app/     FastAPI platform: main.py, db.py, auth.py, routes/, services/
hospitals/       FHIR R4 hospital server (run 3x) and its SQLite store
frontend/src/    React screens (pages/), shared components, api.js
ml/              train.py (risk models), eval.py (all evaluation numbers)
scripts/         seed_hospitals.py (seeded split of Synthea), smoke_test.py
data/            Synthea zip, heart and diabetes CSVs, sample/ (MPI ground truth, demo patients)
models/          heart_rf.joblib, diabetes_rf.joblib
experiments/     metrics.json (training), eval/metrics.json (evaluation)
```
