# Frontend plan - AgriVision (AI Powered Crop Disease Detection and Recommendation)

Batch CSE-C-C16 | Design V1 Aurora Glass | backend port 8416 | frontend port 5416

## 1. What exists today

`agrivision/` is a **Flask** app (server-rendered Jinja templates, cookie session, SQLite `agrivision.db`,
uploads in `agrivision/static/uploads`). It stays untouched and still runs on its own (`python app.py`, port 5000).

Core modules the new API layer will import (not rewrite):

| Module | What it gives |
|---|---|
| `config.py` | DB path, upload dir, 10 MB limit, allowed extensions (jpg, jpeg, png, webp) |
| `disease_db.py` | `CLASSES` (38 PlantVillage / PD36-C labels), `display_name()`, `get_disease_info()` |
| `inference.py` | `predict(bytes, crop_hint)` -> top-3, confidence, latency, engine name |

Honest note on the model: `agrivision/models/` is **empty**, so `predict()` runs its colour/texture
**heuristic** engine ("pd36c-heuristic"), not a trained CNN. `train.py` + `datasets/plantdoc-images` can produce
`models/plantdoc_cnn.h5`, which `inference.py` auto-loads. The new UI shows the engine name on every result so
nobody mistakes heuristic output for CNN output.

### 1.1 Existing Flask routes

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/` | - | - | landing page |
| GET/POST | `/login` | - | form `email`, `password` | redirect to dashboard, or flash "Invalid email or password." |
| GET/POST | `/register` | - | form `full_name,email,phone,password(min 6),role,region,crop` | redirect to login; flash on duplicate email |
| GET | `/logout` | - | - | clears session |
| GET | `/dashboard` | yes | - | totals (scans, healthy, high severity, disease rate), 6 recent detections |
| GET/POST | `/detect` | yes | multipart `image`, `crop_type` | stores image + row, redirect to `/result/<id>` |
| GET | `/result/<rid>` | yes | - | result with top-3, disease info, treatments |
| GET | `/history` | yes | query `q, crop, disease(healthy/diseased)` | up to 200 rows, filtered in Python |
| POST | `/history/<rid>/delete` | yes | - | deletes row + image |
| GET | `/history/<rid>/export` | yes | `format=csv|pdf` | one-record CSV or PDF download |
| GET | `/history/export` | yes | - | all-history CSV download |
| GET | `/analytics` | yes | - | distribution by disease, severity counts, scans per day |
| GET | `/encyclopedia` | - | `q` | 38 disease cards, crop chips, text search |
| GET | `/disease/<name>` | - | - | full disease card (404 if unknown) |
| GET/POST | `/profile` | yes | form `full_name, region, language(en/hi/mr), crops[]` | profile edit |
| POST | `/api/v1/auth/register` | - | JSON `email,password,...` | 201 `{user_id,email,message}` / 409 `EMAIL_EXISTS` |
| POST | `/api/v1/detect/upload` | yes | multipart `image`, `crop_type` | `{result_id,predicted_disease,confidence,top_3_predictions[],severity,processing_time_ms,recommendations}` |
| GET | `/api/v1/history` | yes | `limit<=100, offset` | `{total_count, results[]}` |
| GET | `/api/v1/history/<rid>` | yes | - | `{result_id,predicted_disease,disease_details,image_url,created_at}` |
| GET | `/api/v1/analytics/dashboard` | yes | - | `{total_detections, disease_distribution}` |
| GET | `/api/v1/diseases` | - | - | list of 38 disease cards |
| GET | `/health` | - | - | `{status:"ok", classes:38}` |

Flask uses a **cookie session** and has **no JSON login**, so a browser SPA cannot sign in through `/api/v1`.

### 1.2 Existing features (every one must survive)

1. Landing page: hero, live-demo card, how it works, 14 crops covered, personas (farmers / officers / dealers), CTA
2. Register (name, email, phone, password, role, region, main crop) and login, with the demo account
   `demo@agrivision.ai` / `demo1234`; logout
3. Dashboard: totals (scans, healthy, high severity, disease rate), quick-scan per crop (tomato, potato, maize),
   season alert, field tips, recent detections
4. Detect: crop type (18 options), drag-and-drop / browse / mobile camera capture, image preview, file name and size,
   progress while analysing, photo tips, extension/size validation (JPG/PNG/JPEG/WEBP, 10 MB)
5. Result: image, date, crop, latency, severity badge, urgent-action flag, confidence bar, top-3 predictions,
   symptoms, lifecycle, prevention, chemical / organic / cultural treatments with cost, safety notice,
   export CSV, export PDF, print, copy share link
6. History: search, crop filter, healthy/diseased filter, view, per-record PDF, delete with confirmation,
   export all as CSV, "new scan"
7. Analytics: disease distribution, severity breakdown, detection timeline, total scans
8. Disease encyclopedia: 38 entries, text search, crop chips, severity badge
9. Disease detail: description, symptoms, lifecycle, prevention, treatments, "scan for this disease"
10. Profile: name, region, language, monitored crops (multi-select), CSV of my data, logout
11. Dark mode toggle (persisted), EN / HI / MR language switch (existing dictionary is only four phrases)
12. Footer links to the API and health endpoint

## 2. New API layer (`backend/`, FastAPI, port 8416)

Thin wrapper that imports `agrivision.config`, `agrivision.disease_db`, `agrivision.inference` and reads/writes
the **same SQLite file and `users` / `results` tables** as Flask. No logic is rewritten. Differences from Flask:

- Auth is a signed **bearer token** (`POST /api/v1/auth/login`) instead of a cookie, because the SPA is a separate origin in dev.
- The existing `/api/v1/*` paths are mirrored with the **same response shapes**; extra fields are only added.
- Additive read-only or thin endpoints (listed below) cover what the templates computed server-side.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | status, class count, engine name, DB ok |
| POST | `/api/v1/auth/login` | NEW - email + password -> token + user |
| POST | `/api/v1/auth/register` | mirrors Flask API, accepts the same fields as the register form |
| GET | `/api/v1/auth/me` | NEW - current user |
| PUT | `/api/v1/profile` | NEW - name, region, language, crops (same SQL as `/profile`) |
| GET | `/api/v1/dashboard` | NEW - the numbers the dashboard template computes + 6 recent |
| POST | `/api/v1/detect/upload` | mirrors Flask; adds `engine`, returns `result_id` |
| GET | `/api/v1/history` | mirrors Flask `limit/offset`; adds `q, crop, disease` filters + severity, image_url |
| GET | `/api/v1/history/{id}` | mirrors Flask; adds top-3, confidence, engine-neutral fields the result page needs |
| DELETE | `/api/v1/history/{id}` | same as Flask delete (row + image) |
| GET | `/api/v1/history/{id}/export?format=csv|pdf` | same content as Flask export |
| GET | `/api/v1/history/export` | all-history CSV |
| GET | `/api/v1/analytics/dashboard` | mirrors Flask; adds severity counts + timeline (what `/analytics` renders) |
| GET | `/api/v1/diseases`, `/api/v1/diseases/{class}` | list (with `q`) and one card |
| GET | `/uploads/{file}` | leaf images (auth-checked by ownership via result id) |

## 3. Screen map (React, kit V1)

| Route | Screen | Replaces | Data |
|---|---|---|---|
| `/` | Landing (aurora hero, live result card, how it works, crops marquee, personas, CTA) | `/` | `/api/health`, `/api/v1/diseases` |
| `/login` | Sign in + "use demo account" | `/login` | auth/login |
| `/register` | Create account | `/register` | auth/register |
| `/encyclopedia` | Disease guide (search, crop chips) | `/encyclopedia` | diseases |
| `/disease/:cls` | Disease detail | `/disease/<name>` | diseases/{cls} |
| `/dashboard` | Stats, quick scan, alert, tips, recent | `/dashboard` | dashboard |
| `/detect` | Upload + crop + progress | `/detect` | detect/upload |
| `/result/:id` | Result with top-3, treatments, exports, share | `/result/<rid>` | history/{id}, export |
| `/history` | Filterable list, delete, export | `/history` | history, delete, export |
| `/analytics` | Three charts + totals | `/analytics` | analytics/dashboard |
| `/profile` | Edit profile, my data CSV, logout | `/profile` | auth/me, profile |
| `*` | Not found | - | - |

Shell: kit `AppShell` (sidebar -> drawer under 1024px), topbar with language switch + theme toggle + user menu.

## 4. Ports and run

`.env` (git-ignored, ports only): `BACKEND_PORT=8416`, `FRONTEND_PORT=5416`. `.env.example` is committed.
`run.bat` creates `.venv`, installs `backend/requirements.txt` and `frontend` packages, starts both servers.

## 5. Feature checklist (verified in Step 4)

How each was verified: `scripts/smoke_test.py` (API, 39 checks), `scripts/capture_screens.py` (every screen with real PlantDoc
leaves, console clean) and `scripts/ui_checks.py` (360 / 768 / 1440 px, keyboard, theme, language, delete, profile).

- [x] 1 Landing page (hero, real knowledge-base card, counts from the API, crops ticker, how it works, features, personas, CTA, footer)
- [x] 2 Register / login / demo account (`demo@agrivision.ai` / `demo1234`) / logout, return-to-page after sign-in
- [x] 3 Dashboard (totals, disease rate, quick scan for tomato / potato / maize, season alert, field tips, 6 recent)
- [x] 4 Detect (18 crops, drop / browse / camera, preview, upload progress, 10 MB + extension validation, error state)
- [x] 5 Result (confidence, top-3, symptoms, lifecycle, prevention, treatments with cost, safety note, CSV, PDF, print, share link)
- [x] 6 History (search, crop filter, healthy/diseased filter, pagination, PDF per record, delete with confirmation, export all CSV)
- [x] 7 Analytics (disease distribution, severity breakdown, timeline, totals, "show as table" for each chart)
- [x] 8 Encyclopedia (38 entries, search, crop chips)
- [x] 9 Disease detail (+ "Scan for this disease" pre-selects the crop)
- [x] 10 Profile (name, region, language, multi-crop, my data CSV, sign out)
- [x] 11 Dark mode (persisted) + EN / HI / MR switch (key interface text only; knowledge-base text stays English)
- [x] 12 API / health links (landing footer)

## 6. Differences from the Flask app (deliberate)

- The analytics bar chart is keyed by full diagnosis name (crop + disease); Flask merged same-named diseases across crops.
- Engine honesty: the sidebar, landing, detect screen and every result say the engine is the colour/texture heuristic
  until a trained model exists. The heuristic's score is almost always 97.2%, so it is labelled "not a calibrated probability".
- Landing page numbers (38 classes, 14 crops, ...) are counted from the API; the old "99%+ accuracy target" and
  "<2s" claims were not carried over because nothing measures them.
- Register signs the user in directly instead of redirecting to the login page.
