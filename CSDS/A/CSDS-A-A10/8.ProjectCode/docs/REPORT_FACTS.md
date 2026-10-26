# CareFlow / MedFlow Documentation Facts

This file is the factual source of truth for every submission document in batch **CSDS-A-A10**. It was compiled on 26 October 2026 from the batch documents, the running application, the SQLite database, the saved model artefacts, and direct measurements. Do not introduce a number in a report, paper, diagram, or slide unless it appears here or is subsequently added with its measurement method.

## 1. Project and academic identity

- Batch: **CSDS-A-A10**, CSE (Data Science), Section A.
- Submission title: **AI Powered Intelligent Hospital Patient Flow Management System**.
- Product name used in the code and user interface: **MedFlow**. The documentation prompt calls the product **CareFlow**; use the academic project title on covers and introduce MedFlow as the implemented prototype.
- Students:
  1. **A. RAMU** — **23K91A6715**
  2. **B. RUSHI** — **23K91A6720**
  3. **B. RAJ KUMAR** — **23K91A6725**
  4. **A. PRABHAS** — **23K91A6703**
- Guide: the two supplied sources contain only **GUIDE NAME**. Preserve the square-bracket placeholder **[GUIDE NAME]** in generated documents until the real name is supplied.
- College, principal, HOD, city, student emails, guide designation, and academic year were not supplied. Preserve explicit square-bracket placeholders and never invent these details.

## 2. Sources audited

- Batch documents: `1.A10_BATCH_DETAILS.docx`, `Students.txt`, `2.ABSTRACT.docx`, `3.BASE PAPER.docx`, `4.INTRODUCTION.docx`, `5.LITERATURE SURVEY.docx`, and `6.OBJECTIVES&PROBLEM STATEMENT.docx`.
- Base paper: Saritha A. N. et al., “Alleviate: An AI-Powered Mobile Application for Personalized Healthcare Management and Doctor Recommendation,” *IEEE Access*, vol. 13, 2025, DOI `10.1109/ACCESS.2025.3647089`, 11 pages. The supplied paper states a **CC BY-NC-ND 4.0** licence.
- Code: root and frontend READMEs, all backend routes, configuration, security, models, schemas, services, ML training/prediction code, seed code, frontend routes, API client, role dashboards, and package manifests.
- Repository evidence gaps: there is no `experiments/` directory, no `metrics.json`, no repository test suite, no `run.bat`, and there was no `docs/screenshots/` directory before this audit.

## 3. Implemented system architecture

### 3.1 Runtime layers

1. **React 19 + TypeScript + Vite frontend** with Tailwind CSS, Framer Motion, GSAP, React Three Fiber, Recharts, Radix primitives, Axios, and Zustand.
2. **FastAPI backend** exposing REST endpoints and a WebSocket broadcast channel.
3. **SQLAlchemy data layer** backed by the local `backend/medflow.db` SQLite database. The configured database URL can be replaced through `MEDFLOW_DATABASE_URL`.
4. **Machine-learning layer** using scikit-learn models saved with Joblib: a Random Forest wait-time regressor and a Gradient Boosting triage classifier.
5. **JWT authentication and role checks** for administrator, doctor, nurse, laboratory technician, and reception users. The public waiting board and health endpoint do not require authentication.

### 3.2 Implemented flow

- Reception creates a patient/visit, obtains a department token, predicts triage priority from supplied or default vitals, and predicts waiting time from department type, queue position, UTC hour, priority, average service time, and a default two-server assumption.
- Queue order is priority rank (`critical`, `urgent`, `normal`) followed by token number.
- Doctors view their department queue, assign a visit to themselves, order a laboratory test, admit to an available ward/ICU bed, or discharge.
- Laboratory staff view ordered/scheduled/in-progress/completed columns and advance test status.
- Nurses view ward and ICU capacity, update bed state, and release beds.
- Administrators view calculated KPIs, department load, and bed/ICU occupancy.
- WebSocket `/ws/live` broadcasts visit, bed, and laboratory changes to connected dashboards.

### 3.3 Persisted entities

`User`, `Department`, `Patient`, `Visit`, `Bed`, `LabTest`, and `MovementLog`. A visit stores token, complaint, vitals JSON, status, priority, current department, assigned doctor, predicted wait, classifier confidence in the field named `triage_score`, optional bed, and timestamps.

## 4. Dataset and model facts

Both datasets are generated inside `backend/app/ml/train.py`. They are **synthetic**, are not saved as source datasets, contain no real patient records, and have no external dataset licence. The generator seed is NumPy RNG seed **42**. The measurements below evaluate the existing saved model artefacts against the deterministic 15% test partitions produced by the same generator and split code. They are development results, not independent clinical validation.

### 4.1 Wait-time regression

- Generator size: **12,000 rows**.
- Split: **10,200 training / 1,800 test** (85% / 15%, `random_state=42`).
- Features: department type, queue ahead, UTC hour, priority, average service minutes, and server count.
- Target: simulated wait in minutes based on `(queue ahead / servers) × average service time`, a rush-hour multiplier, a priority factor, Gaussian noise, and clipping to 0–240 minutes.
- Model: `RandomForestRegressor`, **200 estimators**, maximum depth **10**, `random_state=42`, `n_jobs=-1`.
- Saved artefact: `wait_time_model.joblib`, **21,064,417 bytes**.
- Test R-squared: **0.951041**.
- Test MAE: **5.982 minutes**.
- Test RMSE: **8.580 minutes**.
- Batch inference measurement: **0.0268 ms per test sample** on the machine in Section 8. This is model-only batch timing, not API latency.

### 4.2 Triage classification

- Generator size: **15,000 rows**.
- Split: **12,750 training / 2,250 test** (85% / 15%, stratified, `random_state=42`).
- Features: age, heart rate, systolic blood pressure, SpO2, temperature, and respiratory rate.
- Labels: a simplified NEWS2-style rule produces an early-warning score; scores 0–3 map to normal, 4–6 to urgent, and 7 or above to critical.
- Model: `GradientBoostingClassifier`, **150 estimators**, maximum depth **3**, `random_state=42`.
- Saved artefact: `triage_model.joblib`, **830,879 bytes**.
- Test accuracy: **0.9680** (96.80%).
- Macro precision: **0.962435**.
- Macro recall: **0.858574**.
- Macro F1: **0.898475**.
- Confusion matrix, rows = actual and columns = predicted, label order `[critical, normal, urgent]`:

  | Actual \\ Predicted | Critical | Normal | Urgent |
  |---|---:|---:|---:|
  | Critical | 63 | 0 | 37 |
  | Normal | 0 | 1,525 | 2 |
  | Urgent | 2 | 31 | 590 |

- Critical-class recall on this test partition is **63/100 = 63%**; this limitation must accompany the overall accuracy.
- Batch inference measurement: **0.0186 ms per test sample** on the machine in Section 8. This is model-only batch timing, not API latency.

### 4.3 Claims that must not be made

- No real hospital deployment, real patient dataset, clinical trial, clinician validation, or independent external test was performed.
- No measured reduction in patient waiting time exists. The landing-page claim of **42% average wait-time reduction** is hard-coded marketing copy and must not be cited as a result.
- The landing-page claims of **214 live patients** and **6 unified departments** are hard-coded and do not describe the measured database snapshot below.
- The base paper’s reported **97.24% precision** concerns a different symptom-to-specialist task and dataset. It is not directly comparable with this project’s triage accuracy.

## 5. Demonstration database snapshot

The database was initially empty. On 26 October 2026 it was populated additively for documentation and screenshot verification; no existing records or files were deleted. The demonstration records are synthetic and must be labelled as such.

- Users: **7**; departments: **7**; patients: **23**; visits: **23**; beds: **18**; lab tests: **5**; movement logs: **18**.
- Visit statuses: **10 waiting**, **3 in consultation**, **3 lab pending**, **2 lab in progress**, **5 discharged**.
- Priorities: **2 critical**, **21 normal**, **0 urgent**.
- Bed states: **11 occupied**, **7 available**.
- Ward capacity: **12 beds** (7 occupied, 5 available).
- ICU capacity: **6 beds** (4 occupied, 2 available).
- Seeded dashboard snapshot: **23 patients today**, **18 active visits**, **11.1 minutes average predicted wait**, **2 active critical cases**, **61% hospital-wide bed occupancy**, and **67% ICU occupancy**. These values describe the synthetic demonstration snapshot, not a hospital study.

## 6. API and WebSocket inventory

Framework-provided `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, and `/redoc` routes are present in addition to these application routes:

| Method | Path | Access / purpose |
|---|---|---|
| POST | `/api/auth/login` | Public credential login; returns JWT and user |
| GET | `/api/auth/me` | Authenticated current user |
| GET | `/api/departments` | Authenticated department list |
| GET | `/api/departments/public` | Public department list |
| GET | `/api/departments/staff/doctors` | Authenticated doctor list |
| POST | `/api/visits` | Reception/admin/nurse creates visit |
| GET | `/api/visits` | Authenticated filtered visit list |
| GET | `/api/visits/{visit_id}` | Authenticated visit detail |
| PATCH | `/api/visits/{visit_id}/status` | Staff status/department transition |
| PATCH | `/api/visits/{visit_id}/assign-doctor` | Doctor/admin/nurse/reception assignment |
| GET | `/api/visits/{visit_id}/movements` | Authenticated movement history |
| GET | `/api/beds` | Authenticated bed list |
| PATCH | `/api/beds/{bed_id}/status` | Nurse/admin bed state update |
| POST | `/api/beds/visits/{visit_id}/admit` | Doctor/nurse/admin admission |
| POST | `/api/beds/visits/{visit_id}/release` | Doctor/nurse/admin release |
| POST | `/api/labs` | Doctor/admin orders test |
| GET | `/api/labs` | Authenticated laboratory list |
| PATCH | `/api/labs/{lab_test_id}/status` | Lab/admin test update |
| GET | `/api/dashboard/kpis` | Authenticated KPI calculation |
| GET | `/api/dashboard/department-load` | Authenticated department load |
| GET | `/api/dashboard/queue-board` | Public waiting board |
| GET | `/api/health` | Public service health |
| WebSocket | `/ws/live` | Public live-update channel |

## 7. Verification and measured API response times

### 7.1 Repository checks

- No automated unit, integration, security, or end-to-end test files were present.
- Frontend lint: `npm run lint` exited **0** with **14 warnings** and no errors. Warnings cover ref access during render, synchronous state changes inside effects, missing hook dependencies, and three `Math.random` purity warnings in the landing animation.
- Frontend production build: `npm run build` exited **0**; TypeScript and Vite transformed **3,573 modules** and completed the Vite build in **1.73 s**. Vite warned that two JavaScript chunks exceed 500 kB after minification (`895.93 kB` and `1,084.51 kB`; gzip `237.16 kB` and `344.51 kB`).
- The application was exercised in system Chrome through Playwright at **1440 × 900**. The capture run reported no browser console errors.

### 7.2 Local API smoke and latency measurement

Conditions: running FastAPI/Uvicorn on loopback port **8010**, SQLite database, one local client, 15 sequential read requests per endpoint. Login returned HTTP 200. All **150** measured read requests returned HTTP 200. Times include loopback HTTP and endpoint/database work but are not concurrent-load benchmarks.

| Endpoint | Mean ms | Median ms | P95 ms |
|---|---:|---:|---:|
| `/api/health` | 4.496 | 2.074 | 17.136 |
| `/api/dashboard/queue-board` | 10.056 | 7.569 | 21.053 |
| `/api/auth/me` | 3.985 | 4.031 | 4.878 |
| `/api/departments` | 9.124 | 4.822 | 23.228 |
| `/api/departments/staff/doctors` | 7.101 | 4.856 | 19.872 |
| `/api/visits` | 10.629 | 7.657 | 29.632 |
| `/api/beds` | 10.862 | 6.763 | 26.326 |
| `/api/labs` | 8.528 | 4.511 | 17.924 |
| `/api/dashboard/kpis` | 12.321 | 8.523 | 25.590 |
| `/api/dashboard/department-load` | 14.231 | 14.024 | 16.274 |

- One local WebSocket connection to `/ws/live` completed in **46.657 ms**.

## 8. Measurement machine

- Operating system: **Microsoft Windows 11 Pro**, version **10.0.26300**, 64-bit.
- Processor: **12th Gen Intel Core i5-12500**, 6 physical cores, 12 logical processors, reported maximum clock 3,000 MHz.
- Installed RAM: **15.7 GB**.
- Python: **3.11.9** in the project virtual environment for model evaluation.
- Browser capture: installed Google Chrome controlled by Python Playwright.

## 9. Screenshot inventory

All files are real 1440 × 900 captures from the running application with the populated synthetic demonstration database. Use dashboard and workflow captures in academic outputs; do not cite unsupported marketing numbers visible on the landing page.

| File | Screen / evidence |
|---|---|
| `01_landing.png` | Public landing page; visual only, unsupported marketing numbers excluded from results |
| `02_login.png` | Staff sign-in and seeded role accounts |
| `03_waiting_board.png` | Public board with current tokens, queues, and predicted waits |
| `04_admin_dashboard.png` | Populated KPIs, department load, ward and ICU occupancy |
| `05_reception_dashboard.png` | Registered visits with token, priority, status, and time |
| `06_patient_registration.png` | Real registration form populated with vitals; form was not submitted |
| `07_doctor_dashboard.png` | General Medicine waiting and active-patient queues |
| `08_patient_detail.png` | Visit vitals, predicted wait, movement, and consultation action |
| `09_order_lab_test.png` | Laboratory-order workflow modal |
| `10_admit_patient.png` | Ward/ICU bed-selection workflow with real bed availability |
| `11_nurse_bed_board.png` | Populated General Ward bed board |
| `12_icu_bed_board.png` | Populated ICU bed board |
| `13_laboratory_dashboard.png` | Scheduled and in-progress laboratory work queues |

## 10. Known gaps and honest limitations

- Missing academic identity: guide, college, city, HOD, principal, guide designation, academic year, and email addresses.
- No real patient-flow dataset; both ML datasets are synthetic and generated from hand-designed rules/distributions.
- No independent clinical validation, prospective study, clinician assessment, deployment study, user-acceptance test, security test, concurrency/load test, accessibility audit, or measured effect on actual waiting time.
- The triage model’s overall 96.80% accuracy masks **63% critical-class recall** on the deterministic test partition.
- The database is SQLite and the default development secret is unsafe for production unless `MEDFLOW_SECRET_KEY` is set.
- The WebSocket endpoint has no authentication, and broadcasts are held in process memory; this is not a multi-instance production design.
- The nurse dashboard initially shows no bed panel until a ward/ICU tab is clicked because the uncontrolled default tab is computed before departments load. The populated screenshots were taken after explicit tab selection.
- Bed occupancy seeded for display is not linked to admitted visit records. It validates occupancy visualisation, not an end-to-end historical admission chain.
- The laboratory status update route records test progression, but moving a test into `in_progress` does not itself update its visit to `lab_in_progress`; only completion can move a matching visit from `lab_in_progress` to `pharmacy`.
- The documentation prompt header mentions backend/frontend ports 8110/5110, while the checked-in README and Vite proxy actually configure **8010/5173**. Measurements and screenshots use the implemented ports.
- There is no `run.bat`; the application was started using the README commands.
- The landing animation contributes very large production chunks and uses render-time randomness; the build and lint warnings above must not be hidden.

## 11. Base-paper comparison boundary

The supplied Alleviate paper implements a mobile personalized-healthcare system using Flutter/Dart, Flask, Firebase, location services, prescription management, doctor verification, diet/exercise features, and symptom-based recommendations. It reports 97.24% precision for its logistic-regression specialist recommendation and 84.76% precision for a diet-plan Random Forest. This project instead implements in-hospital queue, movement, laboratory, and bed-flow coordination with a React/FastAPI/SQLite stack and two synthetic-data models. Any comparison must be qualitative or explicitly state that tasks, datasets, splits, and conditions differ.
