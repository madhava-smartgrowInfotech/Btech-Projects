# PulmoVision - Frontend plan (Kit V2, Neo Brutal Grid)

Status: **Steps 1-4 complete.** Kit V2 is in `frontend/src`, every screen is wired to the API, and the checks in section 6 are verified.

Ports: backend **8212**, frontend **5212** (confirmed in `.env`, `run.bat`, `vite.config.js`).
Kit: `D:\abstracts\Frontend_Kits\V2` - 17 files + `MANIFEST.md`, JavaScript (.jsx).

---

## 1. Backend endpoints (inventory)

Auth: `Bearer <JWT>` from `POST /api/auth/login`. "doctor" = role-restricted (technicians get 403).
Patient/scan/metrics endpoints are open to any logged-in user.

| # | Method | Path | Auth | Request | Response |
|---|---|---|---|---|---|
| E1 | GET | `/api/health` | none | - | `{status, models_loaded, gemini_configured}` |
| E2 | POST | `/api/auth/login` | none | JSON `{email, password}` | `{token, user:{id,email,name,role}}` · 401 `"Wrong email or password"` |
| E3 | GET | `/api/auth/me` | any | - | `{id,email,name,role}` |
| E4 | GET | `/api/patients?q=` | any | query `q` (name or code, optional) | `[patient]` |
| E5 | POST | `/api/patients` | any | JSON `{name 1-120, phone ≤20, age 0-120, sex Male\|Female\|Other}` | `patient` |
| E6 | GET | `/api/patients/{id}` | any | - | `patient` + `scans: [scan_brief]` · 404 |
| E7 | POST | `/api/scans` | any | multipart `patient_id`, `file` (≤25 MB, PNG/JPG/DICOM) | `scan` · 400 empty · 404 patient · 413 too large · 422 rejected (colour photo / non-chest) |
| E8 | GET | `/api/scans` | any | - | `[scan]` (latest 50) |
| E9 | GET | `/api/scans/{id}` | any | - | `scan` · 404 |
| E10 | GET | `/api/scans/{id}/image/{kind}` | any | `kind` = original, resized, denoised, enhanced, mask, heatmap | `image/png` · 404 unknown kind |
| E11 | GET | `/api/scans/{id}/assistant` | doctor | - | `[{role, content, model}]` (chat history) |
| E12 | POST | `/api/scans/{id}/assistant` | doctor | JSON `{question 1-1000, lang en\|hi\|te}` | `{answer, model}` · 503 Gemini error |
| E13 | GET | `/api/scans/{id}/report?lang=en\|hi\|te` | doctor | - | `application/pdf` (header `X-AI-Status`) · 400 bad lang |
| E14 | GET | `/api/audit` | doctor | - | `[{id,user,action,target,at}]` (latest 200) |
| E15 | GET | `/api/metrics` | any | - | evaluation JSON + `training{xray,ct,unet}` · 404 until `ml/eval.py` has run |
| E16 | GET | `/api/metrics/figure/{name}.png` | any | e.g. `confusion_xray.png`, `confusion_ct.png` | `image/png` · 404 |

Shapes:
- `patient` = `{id, code, name, phone, age, sex, created_at, scan_count, last_scan?}`
- `scan` = `{id, patient_id, patient_code, patient_name, filename, modality (xray|ct), modality_score, prediction, confidence, probabilities, severity (none|mild|moderate|severe), affected_pct, details, created_at, disclaimer}`
  - `details` = preprocessing steps, mask method, lung area %, modality scores (no file ids)

---

## 2. Features and screens (inventory)

Features from `docs/01_OVERVIEW.md`:

| # | Feature | Where it lives today | Endpoints |
|---|---|---|---|
| F1 | Upload + modality check (PNG/JPG/DICOM, rejects colour photos and non-chest images) | New scan | E7 |
| F2 | Preprocessing steps shown (resize, denoise, CLAHE, normalise) | Result | E9, E10 |
| F3 | Lung segmentation mask overlay | Result | E9, E10 (`mask`) |
| F4 | Classification (X-ray: 5 classes; CT: 4 classes) + probabilities | Result | E9 |
| F5 | Grad-CAM heatmap, calibrated confidence, severity | Result, Patient detail | E9, E10 (`heatmap`) |
| F6a | Clinical assistant chat per scan (doctor, en/hi/te) | Result | E11, E12 |
| F6b | Multilingual PDF report (preview + download) | Report | E13 |
| F7a | JWT login, doctor / technician roles | Login, route guards | E2, E3 |
| F7b | Patient registry: list, search, create, detail with scan history | Patients, Patient detail, New scan | E4, E5, E6 |
| F7c | Audit log (doctor) | Audit log | E14 |
| F8 | Model evaluation: Dice/IoU, accuracy, macro-F1, per-class metrics, confusion matrices, modality routing | Model performance | E15, E16 |
| - | Landing page (public marketing entry) | Landing | none |

Existing screens (`frontend/src/pages/`, routes from `App.jsx`):

| Route | Screen | Roles | Existing file |
|---|---|---|---|
| `/` | Landing | public | `Landing.jsx` |
| `/login` | Login | public | `Login.jsx` |
| `/scan` | New scan (pick/create patient, upload) | any | `NewScan.jsx` |
| `/scans/:id` | Result (mask, heatmap, severity, preprocessing, assistant) | any (assistant: doctor) | `Result.jsx` |
| `/scans/:id/report` | Report preview / download | doctor | `Report.jsx` |
| `/patients` | Patients list + search | any | `Patients.jsx` |
| `/patients/:id` | Patient detail + history | any | `PatientDetail.jsx` |
| `/performance` | Model performance | any | `Performance.jsx` |
| `/audit` | Audit log | doctor | `Audit.jsx` |

Shell: `Layout.jsx` (sidebar nav: New scan, Patients, Model performance, Audit log for doctors; topbar with logout), `ui.jsx` (AuthImage, badges, Spinner, ErrorBox), `Logo.jsx`.

---

## 3. Screen map (what Step 3 builds)

Same routes, same API calls, rebuilt with kit components. Kit names come from the prompt; the exact kit exports are confirmed in Step 2.

| Route | Kit pieces | API | States to design |
|---|---|---|---|
| `/` Landing | landing + motion pieces (FadeIn, SlideUp, Stagger, Reveal, CountUp, MagneticButton) | none (static product copy, no invented numbers) | - |
| `/login` | Card, Button, form inputs, Toast | E2 | wrong credentials error, loading |
| `/scan` | AppShell, Card, FileDrop, Button, Modal (new patient), Toast | E4, E5, E7 | empty patient list (action: create), 422 rejection message, 413, upload progress |
| `/scans/:id` | AppShell, StatCard, Card, Tabs, Charts (probability bars), Table, Button, Toast | E9, E10, E11, E12 | skeleton, 404, technician sees "doctor-only" assistant notice, assistant 503 |
| `/scans/:id/report` | AppShell, Tabs (en/hi/te), Button (download), PDF frame | E13 | generating (AI wait), AI-unavailable notice from `X-AI-Status` |
| `/patients` | AppShell, Table (wide → cards on mobile), Button, Modal, EmptyState | E4, E5 | empty state with "Add patient" action |
| `/patients/:id` | AppShell, Card, Table (scan history), Button | E6, E10 (heatmap thumbnail) | 404 |
| `/performance` | AppShell, StatCard, Charts, Card, Table | E15, E16 | "no evaluation yet" 404 state |
| `/audit` | AppShell, Table, EmptyState | E14 | empty, 403 for technician (redirect) |

Cross-cutting: dark mode toggle in topbar (kit `theme.jsx`), `prefers-reduced-motion`, 360 px drawer nav, focus rings, Escape closes overlays, lazy-load Leaflet/recharts-heavy pages.

---

## 4. Known gaps (found in Step 1)

| # | Gap | Effect | Needs |
|---|---|---|---|
| G1 | `models/xray_classifier.pt`, `models/ct_classifier.pt`, `models/lung_unet.pt` are **missing** (only `modality_backbone.pt` and `modality_bank.npz` exist) | `GET /api/health` shows `models_loaded: false`; **E7 POST /api/scans returns 500** (FileNotFoundError), so the core flow cannot run | Weights restored from training (`ml/train.py` or `notebooks/pulmovision_kaggle.ipynb`) - user decision |
| G2 | `experiments/eval/metrics.json` and `experiments/*_training.json` are missing | E15 returns 404; Performance screen must show its "no evaluation" state | `python ml/eval.py` after G1 is fixed |
| G3 | `scripts/smoke_test.py` exists but depends on the upload flow in G1 | smoke test will fail on scan upload until G1 is fixed | same as G1 |

Backend endpoints were **not** changed in Step 1. No additive read-only endpoint has been proposed yet.

---

## 5. Step 1 checks

- [x] Backend starts (`uvicorn app.main:app` on 8212) - `/api/health` returns 200.
- [x] Ports in `.env` are 8212 / 5212.
- [x] Every endpoint in section 1 listed (E1-E16).
- [x] Every existing screen and feature listed (section 2).
- [x] Screen map written (section 3).
- [x] Step 2 (kit copy) - kit copied into `frontend/src`; the kit's missing `lib/auth`, `lib/storage` and `lib/gsap` modules and its navigation were adapted in this copy.

---

## 6. Step 4 tick-list (verified 2026-10-15)

Each feature from section 2 is ticked only after it is walked end-to-end in the browser.

- [x] F1 Upload + modality check (real X-ray and CT uploads; colour photo rejected)
- [x] F2 Preprocessing steps (result page)
- [x] F3 Lung mask (result and scan thumbnails)
- [x] F4 Classification (probability chart)
- [x] F5 Heatmap, confidence, severity
- [x] F6a Assistant (doctor; answered by Gemini)
- [x] F6b Report preview/download (en and te verified in the browser; hi returned by the API)
- [x] F7a Login + roles (technician has no Audit log and is redirected)
- [x] F7b Patients: list, search, create, detail
- [x] F7c Audit log
- [x] F8 Model performance (measured values, including the weak CT result)
- [x] Landing page (Neo Brutal Grid)
