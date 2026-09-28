# MediQueue

District-wide outpatient booking for Hyderabad that **prioritises by severity**, **spreads patients across
hospitals** and shows a **live queue position with waiting time**.

> Decision support only - MediQueue never gives a diagnosis. A qualified clinician confirms severity at the
> hospital. In an emergency call 108.

## Features

- **District hospital network** - 60 Hyderabad hospitals from OpenStreetMap with departments, daily OP limits and
  emergency quotas (editable in the console).
- **Patient booking** - pick symptoms or type them (mapped by Gemini) -> severity -> 3 ranked hospitals on a map -> token.
- **Severity triage** - mild / moderate / severe / critical from a trained symptom model, symptom severity weights
  and red-flag rules; critical cases get emergency advice and the emergency quota.
- **Limits, quotas and overflow** - an integer programme (PuLP) places each booking on the best day using calibrated
  no-show predictions for controlled overbooking; full days roll over to the next day automatically.
- **Live queue** - position and estimated wait pushed over WebSockets as patients are called or emergencies inserted.
- **Hospital console** - today's queue, call next, done / no-show, add emergency, limits and departments.
- **Referrals** - refer to another hospital with a summary shared only after patient consent; tracked to completion.
- **District dashboard** - live load map, per-hospital load and waits, severity mix, next-day moves, referrals.

## Quick start (Windows)

```bat
setup.bat        REM once: venv, Python + npm packages, .env
run.bat          REM API :8215 + web app :5215, opens the browser
run_phone.bat    REM same + Cloudflare quick tunnel -> https link for your phone
```

Optional: put a Gemini key in `.env` (`GEMINI_API_KEY`, from https://aistudio.google.com/apikey) for free-text
symptom mapping; without it a keyword matcher is used.

## Demo logins (password `demo1234`)

| Role | Email |
|---|---|
| Patient | `patient@mediqueue.app` |
| Hospital OP desk | `desk1@mediqueue.app` ... `desk60@mediqueue.app` |
| District admin | `admin@mediqueue.app` |

## Evaluation results

From `ml/eval.py` (seed 7) -> `experiments/eval/metrics.json`; model metrics in `experiments/`.

| Objective | Metric | Result |
|---|---|---|
| 1. Online booking across the district | Simulated requests booked (1,200 patients, 60 hospitals, demand > capacity) | **100%** |
| 2. OP limits and emergency quotas | Capacity / expected-attendance / emergency-quota violations | **0 / 0 / 0** |
| | Bookings moved automatically to a later day under overload | 16.1% |
| | Utilisation: fixed booking -> calibrated overbooking (limit 40, 300 days) | 79.4% -> **91.1%** (overflow on 4% of days) |
| | No-show model ROC-AUC / calibration error (ECE) | 0.728 / 0.003 |
| 3. Severity from symptoms | Condition model, held-out cases with only 3 symptoms: top-1 / top-3 accuracy | **91.2% / 99.3%** |
| | Red-flag cases graded critical | **100%** |
| | Under-triage vs reference acuity (graded below the condition's baseline) | 5.9% |
| 4. Hospital recommendation | Department match of the booked hospital | 97.8% |
| | Load spread across hospitals (coefficient of variation): MediQueue vs nearest-hospital | **0.14 vs 1.07** |
| | Busiest hospital's load: MediQueue vs nearest-hospital | **100% vs 587%** |
| | Mean travel distance: MediQueue vs nearest-hospital | 3.8 km vs 2.5 km |
| 5. Queue position and waiting time | Wait-estimate MAE (real no-show outcomes, 60-patient queues): naive -> no-show-aware -> live update | 24.8 -> **9.4** -> **6.7** min |
| 6. Referrals | Receiving hospital has the requested department (200 referrals) | **100%**, mean 2.5 km |

MediQueue trades about 1.2 km of extra travel for a far more even load: no hospital goes over its limit, while
sending everyone to the nearest hospital overloads some hospitals almost 6x.

## Tech

React + Vite + Tailwind + Leaflet/OpenStreetMap - FastAPI + SQLAlchemy + SQLite + WebSockets - scikit-learn -
PuLP (CBC) - Gemini - Cloudflare quick tunnel.

## Documentation

- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, users, features, objectives
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - architecture, models, allocation, queue, referrals, data sources and licences, evaluation method
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, run, phone access, demo walkthrough, checks
- [docs/PLAN.md](docs/PLAN.md) - build plan

## Project layout

```
backend/app/   main.py, db.py, auth.py, seed.py, routes/, services/
frontend/src/  pages/, components/, api.js
ml/            train_triage.py, train_noshow.py, eval.py
scripts/       smoke_test.py, fetch_hospitals.py, build_network.py, download_data.py, phone_tunnel.py
data/          datasets, hospitals_osm.csv, hospitals_network.csv, disease_acuity.csv
models/        trained models          experiments/   metrics
```

## Data and licences

Disease Symptom Prediction and Doctor's Specialty Recommendation (Kaggle, CC BY-SA 4.0), Medical Appointment No
Shows (Kaggle, CC BY-NC-SA 4.0), hospital locations (c) OpenStreetMap contributors (ODbL). Details in
[docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md).
