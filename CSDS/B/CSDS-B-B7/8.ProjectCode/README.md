# HospiSense

HospiSense predicts length of stay, forecasts bed and ICU demand, and recommends how to allocate beds, staff and equipment - with
the reasons behind every number.

> Decision support only: every prediction and recommendation supports, and does not replace, qualified clinical and
> operational judgement.

## Features

- **Length-of-stay prediction** - expected days, an 80% range and a short/long-stay class at admission, with SHAP reasons in days (XGBoost).
- **Occupancy forecast** - 14-day census per facility and ward from current patients' predicted stays plus forecast admissions, with 90% bands.
- **ICU demand forecast** - expected ICU beds per facility and an early warning on the first day demand can pass capacity.
- **Staff and equipment demand** - nurses per shift at safe ratios; ventilators, monitors, infusion pumps and dialysis machines.
- **Allocation recommendations** - OR-Tools integer programmes recommend bed conversions, diversions, nurse floats, extra shifts and equipment transfers, and explain the trade-off.
- **Decision dashboard** - KPIs, alerts and forecasts; administrators accept a plan as is or edit it first, and accepted plans update capacity, rosters and stock.
- **Evaluation** - held-out accuracy, forecast error against naive baselines, and the gain over the static allocation.

## Quick start (Windows)

```bat
setup.bat    :: once - Python venv, packages, .env, npm install
run.bat      :: starts the API (8207) and web app (5207) and opens http://localhost:5207
```

Requires Python 3.11+ and Node.js LTS. No API keys are needed; datasets and trained models are included.

## Demo login

| Role | Email | Password |
|---|---|---|
| Administrator | admin@hospisense.app | Admin@123 |
| Doctor | doctor@hospisense.app | Doctor@123 |

## Evaluation results

Held-out data (October-December admissions, never used in training). Produced by `ml/eval.py` -> `experiments/eval/metrics.json`.

| Measure | HospiSense | Baseline |
|---|---|---|
| Length-of-stay MAE | **0.31 days** (R2 0.968, 97.4% within 1 day) | 1.91 days (predict the average) |
| Long-stay class (> 5 days) | accuracy 96.6%, F1 0.934, AUC 0.996 | - |
| Census forecast MAE (beds per ward, 1-14 days) | **4.48** | 5.91 persistence (-24.1%), 5.01 28-day mean (-10.5%) |
| 90% band coverage | 89.2% | - |
| ICU early warning, next 7 days | recall 80%, precision 27% | - |
| Patient-days without a bed | **919** | 1,083 static allocation (-15.1%) |
| Nurse shifts short of safe ratio | **2,446** | 4,610 (-46.9%) |
| Equipment unit-days short | **165** | 239 (-31.0%) |
| Nurse shifts rostered | 116,655 | 110,740 (+5.3%, the cost of covering peaks) |

## Project layout

```
backend/app/     FastAPI app: main.py, db.py, auth.py, routes/, services/ (engine, planning, optimizer)
frontend/src/    React screens (pages/), components/, api.js
ml/              prepare_data.py, train.py, eval.py
scripts/         smoke_test.py, download_data.py, init_env.py
data/            raw datasets (committed), processed history, app.db (created on first run)
models/          trained models and hospital_config.json
experiments/     metrics.json (training), eval/metrics.json (evaluation)
docs/            documentation
```

## Documentation

- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, users, features, screens, default hospital structure
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - data sources and licences, models, forecast, optimiser, evaluation, API
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, running, demo walk-through, checks, troubleshooting
- [docs/PLAN.md](docs/PLAN.md) - build plan
