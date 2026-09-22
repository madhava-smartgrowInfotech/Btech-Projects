# CivicPulse - Build Plan

**Architecture:** React + Vite SPA (5201, proxies `/api`) -> FastAPI (8201) -> SQLite (`data/app.db`) + ML services (`models/`) + Gemini API.
Intake pipeline: text -> language detect -> TF-IDF+LR (category, department) -> XGBoost (priority) -> XGBoost (resolution days, SLA flag) -> LIME words + SHAP factors -> Gemini structured extraction -> officer queue.

**Data:** CivicComp-HiEn (16k real Bengaluru complaints x EN/HI/Hinglish, severity labels, ~32 MB CSVs, committed - model weights skipped) + Citizen Grievance Dataset (3.7k Hindi/Hinglish/EN, committed) + Indian Citizen Complaint (2k EN, committed) -> ~14 unified categories -> 8 departments. NYC 311 extract (~200k closed requests, created/closed dates, gzipped) -> resolution-time model. Seeded generator -> wards (Bengaluru sample city), officers, ~600 labelled sample complaint histories. Kaggle downloads work anonymously (no token needed).

**ML (CPU, < 1 min each):** category + department = TF-IDF (word 1-2 + char 2-5) + LogisticRegression; priority = XGBoost on text-urgency probability + multilingual urgency cues + category (Low/Med/High from CivicComp severity, Critical = top severity score); resolution days = XGBoost regressor on NYC 311 (category, priority, weekday, month). Metrics -> `experiments/*.json`.

**Tables:** users, departments (SLA days), wards, complaints (AI suggestion + final decision JSON), events (status timeline + replies), feedback (officer overrides = new labels), model_runs (metrics history).

**Endpoints (`/api`):**
- auth: `POST /auth/login`, `POST /auth/register`, `GET /auth/me`
- citizen: `POST /complaints` (text, photo, lat/lng), `GET /complaints/mine`, `GET /complaints/track/{tracking_id}`
- officer: `GET /officer/queue`, `GET /complaints/{id}`, `POST /complaints/{id}/decision` (accept/override + reason), `POST /complaints/{id}/status`, `POST /complaints/{id}/draft-reply`, `POST /complaints/{id}/reply`
- model: `POST /model/retrain`, `GET /model/metrics`
- analytics: `GET /analytics/summary`, `/analytics/hotspots`, `/analytics/sla`, `/analytics/trends`
- admin: `GET /departments`, `PUT /departments/{id}` (SLA days)

**Screens:** Landing, Login, File complaint (text + photo + Leaflet pin), Track my complaints, Officer triage queue, Complaint detail (LIME/SHAP, Gemini fields, override, draft reply, retrain), Hotspot map + analytics (admin SLA editor).

**Roles:** citizen, officer, admin (field-staff app deferred; officers update status). Defaults: departments Roads 7d, Water Supply 3d, Sanitation 3d, Electricity 2d, Health 3d, Revenue 15d, Public Safety 1d, Town Planning 21d; languages EN/HI/Hinglish.

**Verification:** `scripts/smoke_test.py` drives the live API end-to-end; `npm run build`; `ml/eval.py` -> `experiments/eval/metrics.json`.
