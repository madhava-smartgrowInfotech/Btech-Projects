# MediQueue - build plan

**Architecture:** React + Vite (5215, Tailwind, Leaflet) -> `/api` + WebSocket proxy -> FastAPI (8215) -> SQLite (`data/app.db`).
Models loaded at start-up: symptom->condition classifier (`models/triage_model.joblib`) and calibrated no-show model
(`models/noshow_model.joblib`). PuLP (CBC) solves day allocation per booking. Gemini maps free text to symptoms.

**Tables:** `hospitals` (OSM location, specialties, op_limit, emergency_quota, avg_consult_min) - `users`
(patient / staff / admin) - `bookings` (token, date, severity, priority, no-show probability, status) - `referrals`
(from/to hospital, consented summary, status pending_consent -> sent -> accepted -> completed).

**Endpoints:** `POST /api/auth/login|register`, `GET /api/hospitals`, `PATCH /api/hospitals/{id}`, `GET /api/symptoms`,
`POST /api/triage/map-text`, `POST /api/triage`, `POST /api/recommend`, `POST /api/bookings`, `GET /api/bookings/mine|{id}`,
`GET /api/console/{hid}`, `POST /api/console/{hid}/call-next|emergency`, `POST /api/console/bookings/{id}/status`,
`GET|POST /api/referrals`, `GET /api/referrals/targets`, `POST /api/referrals/{id}/consent|accept|complete|decline`,
`GET /api/dashboard`, `WS /api/ws/hospital/{hid}` (0 = all hospitals).

**Screens:** Landing - Login - Book a visit - My token - Hospital console - Referrals - District dashboard.

**Data:** Disease Symptom Prediction (symptoms + Symptom-severity weights), Doctor's Specialty Recommendation
(condition -> specialty), Medical Appointment No Shows (no-show model), OpenStreetMap Hyderabad hospitals.
All small enough to commit in full.

**Severity:** max(symptom-weight band, likely-condition baseline, red-flag rules). Critical -> emergency advice + emergency quota.
**Allocation:** feasible day = expected attendance within OP limit and bookings within limit x (1 + 15 %);
ILP minimises urgency-weighted delay + overbooking penalty -> automatic next-day scheduling when full.
**Queue:** order by (priority, token); wait = sum over patients ahead of (1 - p_no-show) x consult minutes (learned live).
