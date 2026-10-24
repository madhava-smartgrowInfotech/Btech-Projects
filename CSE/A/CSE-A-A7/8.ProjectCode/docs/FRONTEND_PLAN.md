# ATHENA - frontend plan (kit V2, Neo Brutal Grid)

Ports: backend 8307, frontend 5307 (confirmed in `.env`).

> Status: all features built and verified (see section 4). Two read-only endpoints were added for the UI and are
> not in the original spec: `GET /api/public/stats` (landing page numbers) and `GET /api/samples`, `/api/samples/{file}`
> (try-a-sample-report on the New patient screen).
>
> Starting point: `8.ProjectCode` had no backend, so the backend is built first from `MASTER_PROMPT_FAST.md`
> (see `docs/PLAN.md`). The endpoint list below is the contract that backend implements.

## 1. Endpoint inventory

| Method | Path | Request | Response |
|---|---|---|---|
| GET | /api/health | - | `{status}` |
| POST | /api/auth/login | `{email, password}` | `{access_token, user{id,name,email,role}}` |
| GET | /api/auth/me | - | `user` |
| POST | /api/reports/extract | multipart `file` (PDF/image) | `{symptoms[], findings[], history[], labs[], each {text/name,value,page}}` |
| POST | /api/patients | `{name?, vitals{age,heart_rate,sbp,dbp,spo2,temp_c,resp_rate,arrival_mode}, report}` | patient with fused features, priority 1-5, risk, confidence, SHAP list, seconds |
| GET | /api/patients | `?status` | queue ordered by priority then arrival |
| GET | /api/patients/{id} | - | full patient record |
| GET | /api/patients/{id}/summary.pdf | - | triage summary PDF |
| POST | /api/patients/{id}/override | `{priority, reason}` | updated patient + override entry |
| GET | /api/metrics | - | accuracy, per-class recall, seconds/patient, confusion matrix, override count |

## 2. Features
- [x] F1 Report intake (upload PDF/image, extracted fields with page)
- [x] F2 Vitals entry
- [x] F3 Fused patient record (report features and vitals side by side)
- [x] F4 Triage model (priority 1-5, risk level, calibrated confidence)
- [x] F5 Why this priority (SHAP, descending influence)
- [x] F6 Clinician override (accept/change with reason, stored as feedback)
- [x] F7 Triage queue and metrics page

## 3. Screen map
1. `/` Landing - loud type, hard edges, headline numbers from `/api/public/stats`
2. `/login` Login (clinician, admin)
3. `/app/new` New patient - FileDrop + vitals form -> F1, F2
4. `/app/patients/:id` Result - priority, fused record, SHAP chart, override modal, PDF download -> F3-F6
5. `/app/queue` Triage queue - ordered table/cards, filters -> F7
6. `/app/performance` Model performance - accuracy, per-class recall, seconds/patient -> F7

## 4. Verification

| Check | Result |
|---|---|
| `npm run build` | passes |
| `scripts/smoke_test.py` | passes (login, 12 report reads, create, SHAP order, override, queue, metrics, PDF) |
| `scripts/capture_screens.py` | 12 screenshots in `docs/screenshots/`, console clean, no failed requests |
| `scripts/check_responsive.py` | no horizontal scroll at 360 / 768 / 1440 in light and dark on every screen; theme persists; reduced motion honoured; Escape closes drawer and modal; focus ring visible |

Screens: Landing (light and dark), Login, Queue, New patient (empty and filled), Result (top and SHAP), Override modal, Queue after override, Performance.
