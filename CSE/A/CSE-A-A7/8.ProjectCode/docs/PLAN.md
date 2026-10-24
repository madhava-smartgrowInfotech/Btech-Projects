# ATHENA - build plan

**Architecture:** FastAPI + SQLAlchemy/SQLite backend (port 8307), React + Vite JS frontend (port 5307, proxies `/api`).
Gemini multimodal reads scanned reports; XGBoost + SHAP triage model trained locally on CPU; ReportLab triage PDF.

**Endpoints (all under `/api`, JWT bearer except login/health)**
- `POST /auth/login`, `GET /auth/me`
- `POST /reports/extract` (PDF/image -> symptoms, findings, history, labs, page refs via Gemini)
- `POST /patients` (vitals + extracted fields -> fused record -> triage + SHAP, stored)
- `GET /patients` (queue, ordered by priority then arrival), `GET /patients/{id}`, `GET /patients/{id}/summary.pdf`
- `POST /patients/{id}/override` (accept/change priority + reason, stored as feedback)
- `GET /metrics` (accuracy vs recorded outcome, per-class recall, seconds per patient), `GET /health`

**Tables:** users, patients (vitals, extracted JSON, fused features, priority, risk, confidence, shap JSON, timings),
overrides (patient, user, old/new priority, reason, time).

**Screens:** Landing, Login, New patient, Result, Triage queue, Model performance.

**Data:** Kaggle "Hospital Triage and Patient History Data" (needs Kaggle token) -> committed sample in `data/sample/`;
5-10 generated sample report images via a seeded script, labelled as sample data.

**Model:** XGBoost on vitals + report-derived flags, isotonic-calibrated confidence, priority 1-5, metrics to `experiments/`.
