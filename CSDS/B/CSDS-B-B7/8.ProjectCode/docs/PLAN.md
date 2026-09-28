# HospiSense - Build Plan

**Architecture:** React + Vite SPA (port 5207, proxies `/api`) -> FastAPI (port 8207) -> SQLite (`data/app.db`) + trained models in `models/`.
ML: XGBoost length-of-stay regressor + long-stay classifier with SHAP; XGBoost admissions model with lag features; probabilistic census
forecast (predicted stays + forecast arrivals, 90% bands); OR-Tools CP-SAT allocation optimiser.

**Data:** Microsoft Hospital LOS (100k EHR stays, 5 facilities A-E, 2012) = patients, stays and census history.
AV Healthcare Analytics II = paediatric share (age bands). Hospital Beds Management = ICU/surgical admission share and nurse attendance.
Wards (General, Surgical, Maternity, Paediatric, ICU) are assigned by a seeded rule in `ml/prepare_data.py`. Dates are shifted by a
fixed multiple of 7 days so the latest record falls on the operating date 2026-09-28.

**Endpoints:** `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/meta`, `GET /api/dashboard`,
`POST /api/admissions/predict`, `POST /api/admissions`, `GET /api/admissions`, `GET /api/forecast?facility=&days=`,
`GET /api/forecast/icu`, `GET /api/forecast/resources?facility=`, `POST /api/allocation/run`, `GET /api/allocation/plans`,
`GET /api/allocation/plans/{id}`, `POST /api/allocation/plans/{id}/accept` (with optional modified actions), `GET /api/metrics`.

**Tables:** users, admissions, ward_capacity, nurse_roster, equipment_inventory, allocation_plans.

**Screens:** Landing, Login, Dashboard, Admissions & predictions, Forecasts (occupancy + ICU), Allocation, Model performance.

**Evaluation (`ml/eval.py`):** LOS MAE/RMSE/R2 vs mean baseline; long-stay accuracy/F1/AUC; census forecast MAE vs persistence
over rolling back-tests; bed/nurse/equipment shortfall of static allocation vs optimised allocation on actual census.

**Demo logins:** admin@hospisense.app / Admin@123 (admin), doctor@hospisense.app / Doctor@123 (doctor).
