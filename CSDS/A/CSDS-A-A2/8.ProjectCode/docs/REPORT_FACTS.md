# REPORT FACTS - Attendance Magic (CSDS-A-A2)

Single source of truth for every submission document. Everything below was read from the code or measured on
this machine on 2026-10-15. Raw outputs: `docs/evaluation/*.json`. Re-run scripts are in `scripts/`.

## 1. Identity

| Item | Value |
|---|---|
| Product | Attendance Magic |
| Title | Attendance Magic: A Smart Geo-Fenced Attendance System with Live Challenge Verification |
| Batch / branch | A2 / CSE (Data Science) - Section A (CSDS-A) |
| Students | A.GREESHMA 23K91A6706 - B.VINAY 23K91A6740 - G.SRIRAM 23K91A6757 - B.SAI KUMAR 24K95A6704 |
| Guide | **not supplied** - batch file says literally "GUIDE NAME" -> keep placeholder `[GUIDE NAME]` |
| College / HOD / Principal / year | not supplied -> keep `[COLLEGE NAME]`, `[HOD NAME]`, `[PRINCIPAL NAME]`, `[ACADEMIC YEAR]` |
| Base paper | *Real-Time Student Face Recognition Attendance System Using AI*, IARJSET Vol. 12, Issue 5, 2025, DOI 10.17148/IARJSET.2025.125183 (PDF in `Documentary/`) |
| Literature survey (from `5.LITERATURE SURVEY.docx`) | [2] Comprehensive Review on Face Recognition, Anti-Spoofing Liveness Verification and Automated Dress Code Enforcement Techniques for Smart Attendance Framework (2026, Int. J. Research Publication and Reviews); [3] Smart Attendance Framework Using Face Recognition, Anti-Spoofing Liveness Verification and Automated Dress Code Enforcement (2026, IJISRT); [4] A Classroom Attendance System with Anti-Spoofing Based on ResNet101 and ArcFace for Face Recognition (2026, Journal of Intelligence and Knowledge Engineering); [5] Automatic Attendance System Using Silent Face Anti-Spoofing to Detect Spoof on Face Recognition (2025, SIML conference) |
| Ports | backend (FastAPI) 8102, frontend (React/Vite) 5102; original Streamlit UI 8501 |
| Objectives (from `6.OBJECTIVES...docx`) | 1 time-bound geo-fenced sessions; 2 JWT + device id + roll restrictions; 3 GPS vs session boundary; 4 liveness by random facial challenge (MediaPipe); 5 duplicate identity prevention (InsightFace embeddings); 6 summaries + Excel export |

**No guide name, college or year are known - leave the square-bracket placeholders; never invent them. No student e-mails are known.**

## 2. What the system is (and is not)

* Pure software system, **no model was trained in this project**. AI components are pre-trained and used as-is:
  MediaPipe Face Mesh (468-landmark, legacy `mp.solutions.face_mesh`, mediapipe 0.10.21) and InsightFace `buffalo_l`
  (SCRFD detector + ArcFace-R50 recogniser, 512-d embeddings, CPU ONNX Runtime 1.31). There is therefore **no training
  set, no training configuration, no loss curve**; documents must say so plainly. The project-specific contribution is the
  verification chain, thresholds, session/geo-fence logic, API and UI.
* Decision rules are deterministic thresholds on landmarks / cosine similarity (config.py, env-overridable).
* Check-in pipeline order (services.run_pipeline and backend/api.py wizard): **1 eligibility -> 2 geo-fence -> 3 liveness
  challenge -> 4 face match (frame consistency, identity, duplicate) -> record**. Every stage writes a `verification_attempts` row.
* Not implemented: depth/texture anti-spoofing, deepfake detection, GPS spoof detection (mock-location), live video
  stream challenge (two still photos are used), multi-faculty/admin roles, e-mail notifications, institutional LMS integration,
  PostgreSQL tested in production (supported via DATABASE_URL, only SQLite exercised).

## 3. Architecture

Layers: **React 19 + Vite 8 SPA (`frontend/`)** -> HTTP/JSON+multipart -> **FastAPI app (`backend/api.py`, thin)** -> **service layer `core/`** -> SQLAlchemy -> SQLite (`attendance_magic.db`).
A second, original **Streamlit UI (`app.py`, `ui/`)** calls the same `core/` (kept; 23 pytest tests include two Streamlit AppTest flows).

| Module | File | Lines | Role |
|---|---|---|---|
| config | `config.py` | 105 | all settings, env-overridable |
| db | `core/db.py` | 40 | engine, `Base`, `get_session`, `init_db` |
| models | `core/models.py` | 148 | 5 ORM tables |
| auth | `core/auth.py` | 93 | PBKDF2-HMAC-SHA256 (200,000 iter, 16-byte salt); JWT HS256 (120 min) bound to device hash |
| device | `core/device.py` | 37 | SHA-256 over user-agent, accept-language, sec-ch-ua(+platform,+mobile) + `X-Device-Id` |
| geofence | `core/geofence.py` | 60 | haversine, tolerance, GPS-accuracy gate |
| liveness | `core/liveness.py` | 268 | Face Mesh metrics, 8 challenges, neutral-frame check, image decode (<=1280 px) |
| face_match | `core/face_match.py` | 158 | ArcFace embedding, cosine, frame-consistency/identity/duplicate decision |
| services | `core/services.py` | 314 | users, sessions, eligibility, roll patterns, device binding, `run_pipeline` |
| export | `core/export.py` | 79 | 3-sheet .xlsx (Summary, Attendance, Verification Log) |
| timeutil | `core/timeutil.py` | 32 | UTC storage, Asia/Kolkata display |
| api | `backend/api.py` | 625 | 27 REST endpoints, per-student wizard state |
| Streamlit UI | `app.py`, `ui/*.py` | 74 + 581 | original interface |
| React app | `frontend/src` | pages 2,105 + components/lib 2,367 lines | 12 routes (below) |
| tests | `tests/test_core.py` | 353 | 23 tests (13 functions; test_verify_challenge has 11 cases) |
| scripts | seed_demo, demo_pipeline, smoke_test | 450 | demo/test tooling |

Totals: `core/` 1,229 lines; backend 626; Streamlit UI 581; tests 353; React src ~4,470 (JSX/JS).

Frontend routes: `/` landing, `/about`, `/login`, `/register`, `/checkin` (paste link), `/checkin/:token` (6-step wizard),
`/app` dashboard, `/app/sessions`, `/app/sessions/new`, `/app/sessions/:id` (tabs: records, map, verification log, analytics), `/app/students`, `*` 404.
Frontend libraries: framer-motion, gsap, lenis, leaflet (OpenStreetMap tiles), lucide-react, react-router-dom 7, recharts. Production build succeeds (vite, 23 s; largest chunk 581 kB / 194 kB gzip).
Design: "Neo Brutal Grid" (lime #C8FF2E, coral #FF5C39, sky #7CC6FF, black borders, light/dark theme).

### Software versions (venv, Python 3.11.9)
streamlit 1.64.0, mediapipe 0.10.21, insightface 2.0, onnxruntime 1.31.0, opencv-python-headless 4.10.0.84, numpy 1.26.4, SQLAlchemy 2.1.4, PyJWT 2.15.1, pandas 3.0.6, openpyxl 3.1.5, qrcode 8.2, fastapi 0.143.0, uvicorn 0.54.0, pydantic 2.14.1, pytest 9.1.1; Node v24.19.0.

### Hardware (measurement machine)
Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Intel UHD 770 (not used - CPU-only inference), Windows 11 Pro 10.0.26200. Other desktop apps were running (see variance note in §7).

## 4. Database (SQLAlchemy 2, SQLite default)

| Table | Columns (type) | Keys/constraints |
|---|---|---|
| `users` | id, role('faculty'/'student'), username (unique), full_name, roll_number (unique, nullable), password_hash, face_embedding (BLOB 512xfloat32), created_at | PK id |
| `attendance_sessions` | id, token (unique, indexed, `secrets.token_urlsafe(24)`), faculty_id FK users, course_code, course_name, section, starts_at, ends_at (UTC), latitude, longitude, radius_m, allowed_rolls (comma patterns, fnmatch), is_closed, created_at | status derived: upcoming / live / expired / closed |
| `attendance_records` | id, session_id FK, student_id FK, roll_number, student_name, marked_at, latitude, longitude, gps_accuracy_m, distance_m, device_hash, challenge, liveness_score, identity_similarity, max_duplicate_similarity, face_embedding | **UNIQUE(session_id, student_id)** |
| `device_bindings` | id, user_id FK, device_hash, device_label, first_seen, last_seen | **UNIQUE(user_id, device_hash)** |
| `verification_attempts` | id, session_id FK, roll_number, stage (eligibility/location/liveness/face/success), passed, reason, device_hash, created_at | audit log of every attempt |

Relationships: User 1-N sessions; Session 1-N records; Session 1-N attempts; User 1-N device_bindings; Record N-1 User.

## 5. Algorithms and exact parameters

**Geo-fence** - haversine, R = 6,371,000 m: `d = 2R asin(sqrt(sin^2(dphi/2) + cos(phi1)cos(phi2) sin^2(dlambda/2)))`. Accept iff `d <= radius + tolerance`
(defaults radius 60 m, tolerance 15 m -> **75 m**); reject if reported GPS accuracy > **150 m**. Radius range in UI 10-500 m.

**Liveness (landmarks 1, 10, 33, 61, 133, 145, 152, 159, 234, 263, 291, 362, 374, 386, 454 of Face Mesh)**
* yaw = (nose_x - x_left)/(x_right - x_left) - 0.5; pitch = (nose_y - eyes_mid_y)/(chin_y - eyes_mid_y); roll = atan2 of eye line (deg);
  MAR = |lip_top-lip_bottom| / |mouth_left-mouth_right|; EAR = mean over eyes of |top-bottom| / |outer-inner|.
* 8 random challenges (`random.choice`): TURN_LEFT/RIGHT (|delta yaw| >= **0.12**), LOOK_UP/DOWN (delta pitch >= **0.08**), TILT_LEFT/RIGHT (delta roll >= **12 deg**), OPEN_MOUTH (MAR >= **0.35**), CLOSE_EYES (EAR <= **0.18**). Direction sign flips with `AM_CAMERA_MIRRORED` (default true).
* Neutral frame must have exactly 1 face, |yaw| <= **0.10**, MAR <= **0.25**.
* Score = clamp(measured/threshold, 0, 1). **3 failed liveness tries lock the wizard** (a new random challenge after each failure).

**Face match (InsightFace buffalo_l, det_size 640x640, CPU)** - cosine similarity of L2-normalised 512-d embeddings:
1. frame consistency (neutral vs challenge photo) >= **0.45**;
2. identity (live vs enrolled reference) >= **0.40**; no enrolment -> reject when `AM_REQUIRE_ENROLLMENT` (default true);
3. duplicate: max similarity to any other record in the session must be < **0.45**.
Exactly one face is required; a second face is tolerated only if its width < 50 % of the largest.

**Eligibility** - session live; student role; roll matches an `allowed_rolls` pattern; not already marked; the device has not marked another roll in this session; device binding <= `AM_MAX_DEVICES_PER_STUDENT` (default 1).

**Security** - PBKDF2-HMAC-SHA256 200,000 iterations; JWT HS256 with claims sub, role, username, name, roll, dev, iat, exp; token rejected if presented from a different device hash; role guards (faculty vs student, 403) on every endpoint; session ownership check (404 for another faculty's session); CORS limited to localhost origins; wizard state is server-side; re-check of eligibility before writing the record. Known weakness: default `AM_JWT_SECRET` is a placeholder (PyJWT warns the 30-byte key is below the 32-byte recommendation).

## 6. REST API (FastAPI, `http://127.0.0.1:8102/docs`)

Meta: `GET /api/health`, `/api/config`, `/api/models`, `/api/stats`, `/api/qr?text=`
Auth: `POST /api/auth/login`, `/api/auth/register` (multipart + face), `GET /api/auth/me`, `POST /api/auth/logout`
Faculty: `GET|POST /api/sessions`, `GET /api/sessions/{id}`, `POST /api/sessions/{id}/close`, `GET /api/sessions/{id}/export`, `GET /api/dashboard`, `GET /api/students`, `POST /api/students/{id}/reset-devices`, `POST /api/students/{id}/enroll`
Student / public: `GET /api/public/sessions/{token}`, `GET /api/checkin/{token}/state`, `POST /api/checkin/{token}/start`, `/location`, `/neutral`, `/liveness`, `/face`, `/retake`, `/reset`
(27 route handlers in total, plus the FastAPI /docs page.)

## 7. MEASURED RESULTS (all real; scripts + JSON in `docs/evaluation/`)

### 7.1 Tests
| Suite | Result |
|---|---|
| `pytest -q` (23 tests: auth/JWT, haversine, geofence, liveness maths 11 parametrised cases, neutral check, face-match logic, roll patterns, session lifecycle, model-backed sample-image test, 2 Streamlit AppTest flows) | **23 passed**, 17.8 s |
| `scripts/smoke_test.py` (API end-to-end with real models, 41 checks) | **41 / 41 PASS**, 9.9 s |
| `scripts/demo_pipeline.py` (9 scenarios) | 2 genuine passes, **8 blocked attempts** at the right stage (see 7.6) |

### 7.2 Identity / duplicate thresholds - LFW verification protocol (`eval_face_verification.py`)
Dataset: **LFW** (Labeled Faces in the Wild; 13,233 images, 5,749 identities; public research benchmark; no licence grant beyond research use; 250x250 JPEG; downloaded from figshare, not redistributed). Protocol file `pairs.txt`: 10 folds x (300 matched + 300 mismatched) = 6,000 pairs, 7,701 unique images. Model: buffalo_l through the product's own `face_match.embed()`.

* 1,208 of 7,701 images (**15.7 %**) are rejected by `embed()` (1,197 "more than one face", 11 "no face"); 1,693 pairs therefore have no score. **Scored: 4,307 pairs = 2,141 genuine + 2,166 impostor.** (LFW are tightly cropped, up-scaled press photos, not selfies - the retake rate on real selfies was NOT measured.)
* Genuine cosine: mean 0.673, SD 0.107, 5th percentile 0.494. Impostor: mean 0.004, SD 0.058, 95th pct 0.099, 99th pct 0.144, **max 0.246**.
* **AUC 0.9992, EER 0.30 % (at threshold 0.19), best accuracy 99.84 % at 0.25, 10-fold accuracy 99.82 % +/- 0.22 %.**

| Threshold | TAR (genuine accepted) | FRR | FAR (impostor accepted) | Accuracy |
|---|---|---|---|---|
| 0.20 | 99.67 % | 0.33 % | 0.18 % | 99.74 % |
| 0.30 | 99.53 % | 0.47 % | 0.00 % | 99.77 % |
| 0.35 | 99.30 % | 0.70 % | 0.00 % | 99.65 % |
| **0.40 (identity, deployed)** | **98.69 %** | **1.31 %** | **0.00 %** | 99.35 % |
| **0.45 (duplicate / consistency, deployed)** | **97.15 %** | **2.85 %** | **0.00 %** | 98.58 % |
| 0.50 | 94.72 % | 5.28 % | 0.00 % | 97.38 % |
| 0.60 | 78.47 % | 21.53 % | 0.00 % | 89.30 % |

Interpretation: at 0.40 no impostor pair of 2,166 reached the threshold (max impostor 0.246) so a wrong person is not accepted on this data; 1.3 % of genuine pairs would need a retake. At 0.45 a second person with the same face as a recorded one is detected 97.2 % of the time (the remaining 2.8 % pass undetected - same-photo/near-identical captures score ~1.0). The deployed thresholds are conservative relative to the EER point (0.19). Base-paper accuracy is on a different (own classroom) dataset - not comparable.

### 7.3 Liveness (`eval_liveness.py`, still LFW images - **no live person, no camera**)
* A. Neutral frame acceptance on a random 1,000 LFW images (seed 7): **329 / 1,000 = 32.9 %** accepted; rejected: not frontal (|yaw|>0.10) 499, multiple faces 92, mouth open 79, no face 1. (Press photos are not instructed "look straight"; user-posed selfies were not measured.)
* B. Metric distribution on accepted neutral frames (mean / SD): yaw 0.001 / 0.053; pitch 0.354 / 0.055; roll -0.9 deg / 6.9 deg; MAR 0.095 / 0.086; EAR 0.283 / 0.069.
* C. **Static replay (same photo as neutral and challenge, 329 frames): 0 % pass for TURN, LOOK, TILT, OPEN_MOUTH; 8.2 % (27/329) pass CLOSE_EYES** because the single photo already shows closed eyes (EAR <= 0.18).
* D. **Rotated-photo attack on TILT challenges** (300 neutral photos rotated by a signed angle, tilt-left / tilt-right pass rate): angles within +/-10 deg pass **0 %**; at 12 deg 51 % (equals threshold); at >= 15 deg **98-99 %**. Measured roll delta equals the rotation angle. => **A photo merely rotated on screen defeats both tilt challenges.**
* E. **Photo-bank attack, liveness only** (157 LFW identities with >= 10 photos, attacker picks the best pair): TURN_LEFT 93.6 %, TURN_RIGHT 94.3 %, LOOK_UP 59.2 %, LOOK_DOWN 45.2 %, TILT_LEFT 47.1 %, TILT_RIGHT 46.5 %, OPEN_MOUTH 51.0 %, CLOSE_EYES 56.7 % (`liveness.json`, first photo = first neutral candidate only).
* **E2. Photo-bank attack against the FULL chain** (`eval_photo_bank_attack.py`: liveness + frame consistency >= 0.45 + identity >= 0.40 vs a held-out enrolled photo; 154 victims; attacker tries up to 5 neutral photos): pass rate per challenge - TURN_LEFT **95.5 %**, TURN_RIGHT **94.2 %**, LOOK_UP 79.9 %, LOOK_DOWN 72.7 %, TILT_LEFT 70.1 %, TILT_RIGHT 69.5 %, OPEN_MOUTH 48.7 %, CLOSE_EYES 52.6 % (liveness-only for the same set: 98.7 / 97.4 / 83.1 / 77.9 / 73.4 / 73.4 / 50.6 / 56.5 %). Caveat: LFW identities with >= 10 photos are public figures with rich photo banks; an ordinary student has fewer photos. **Conclusion: the random challenge stops a single stolen photo (7/8 challenges: 0 % success) but NOT an attacker who owns several photos of the victim in different poses; with 3 tries and a random challenge an attacker has about a 1-in-8 chance per draw of getting the easiest challenge.** Genuine-user pass rate was NOT measured (no volunteers/camera).

### 7.4 Geo-fence (`eval_geofence.py`)
* Haversine vs Vincenty (WGS-84) at lat 17.385: constant relative error **0.469 %** -> 0.35 m at 75 m, 4.7 m at 1 km, 23 m at 5 km.
* Boundary sweep (radius 60 m + 15 m tolerance, centre 17.3850, 78.4867, accuracy 10 m): **inside up to and including 75 m, rejected from 80 m** (sweep step 5 m). Accuracy gate: 150 m accepted, 151 m rejected ("GPS accuracy too low").
* **Simulation (not field data)** - isotropic Gaussian GPS error sigma per axis, 20,000 trials: P(accept) for a student truly at 40 / 60 / 100 / 150 m = sigma 3 m: 100 / 100 / 0 / 0 %; 5 m: 100 / 99.9 / 0 / 0 %; 10 m: 99.98 / 92.3 / 0.5 / 0 %; 20 m: 94.2 / 72.3 / 8.5 / 0.015 %; 30 m: 80.8 / 60.0 / 15.7 / 0.34 %. Real phone GPS error was NOT measured; no GPS-spoofing detection exists.

### 7.5 Latency (CPU, `eval_latency.py`, 40 repetitions, p50 / p95 ms)
* Cold start: MediaPipe Face Mesh load **0.81 s**, InsightFace buffalo_l load **1.55 s** (first-run model download ~280 MB not counted).
* Per stage (face crops ~250-320 px): JPEG decode+resize of a 1280x886 photo 4.8 / 8.5; MediaPipe landmarks 6.8 / 8.8; challenge maths 0.004 / 0.006; **InsightFace embedding 175.6 / 244.3**; face-match decision with 30 session faces 0.38 / 0.56; **AI work for one check-in (2 landmark + 2 embedding passes) 368 / 525**.
* HTTP, in-process TestClient (network excluded), 40 complete check-ins: login 105.5 / 123; eligibility 12.6 / 14.8; location 8.0 / 9.8; liveness (2 uploads) 23.1 / 26.6; face match + record **521 / 759**; **check-in total after login 564 / 806 ms**.
* Duplicate-scan cost vs session size (verify_faces, p50): 10 faces 0.14 ms; 100: 1.15; 500: 5.7; 1,000: 11.9; 5,000: 41 ms (linear scan, numpy).
* Variance: an earlier run with the CPU at ~100 % from other processes gave InsightFace p50 277 ms; the figures above are from a lightly loaded run (load ~20-30 %).
* LFW embedding throughput (loaded machine, concurrent jobs): mean 281 ms, p50 250, p95 547 per image.

### 7.6 Proxy-attack scenario matrix (demo_pipeline / smoke_test / UI run) - all real
| # | Scenario | Result |
|---|---|---|
| 1 | genuine student inside fence, right challenge | PASS (distance 7.7 m, liveness 1.00) |
| 2 | same student again | blocked - eligibility "already marked" |
| 3 | student 556 m away | blocked - location "Outside geo-fence: 556 m, limit 75 m" |
| 4 | static photo for OPEN_MOUTH | blocked - liveness (MAR 0.073, need 0.35) |
| 5 | another person's face under this roll | blocked - face identity (similarity 0.02, need 0.40) |
| 6 | same face under a second roll | blocked - duplicate (similarity 1.00) |
| 7 | roll not on the list | blocked - eligibility |
| 8 | second device for the same student | blocked - device binding |
| 9 | JWT used from another device | HTTP 401 |
| 10 | 3 failed challenges | wizard locked (step 99) |
Caveat for demos: in `demo_pipeline.py` the same image is used for enrolment and check-in, so identity = 1.00 there; with different photographs of one person (UI run, LFW) identity similarities were 0.59-0.86.

### 7.7 UI demonstration run (real app, 2026-10-15; documentation database)
Two sessions in the faculty account: **CS601 Machine Learning** (closed; 4 present of 4 students; 4 blocked attempts: out-of-fence, static photo, duplicate-face proxy, roll not allowed) and **CS604 Data Visualization** (live, explicit list of 5 rolls: 3 present, 7 blocked attempts, 30 checks logged; identity similarities 0.856, 0.628, 0.593). Face photographs are **LFW stand-ins** (one identity per demo student; file names anonymised) because the product holds no student photos and no camera was attached; challenge photos are real second photographs satisfying the issued challenge (TILT via rotated copy where no real photo existed). Camera capture was replaced by the app's own "Upload photo" tab. Demo accounts: faculty `faculty@college.edu`; students = the 4 team roll numbers (password student123), plus two extra demo accounts (Proxy Demo 23K91A6799 enrolled with the same face as 23K91A6706; Visitor Demo 24K95A6710).

## 8. NOT MEASURED / honest gaps (state plainly in every document)
1. No model training; no training/validation/test split of our own; no loss/accuracy curves. Results are the evaluation of pre-trained components on LFW.
2. No live camera or human-subject trial: genuine pass rate of the 8 challenges, selfie single-face retake rate, usability and user-acceptance testing were not done.
3. No comparison number against the base paper on identical data (base paper uses its own classroom dataset; this project's numbers are LFW verification pairs).
4. Real phone GPS accuracy and indoor drift not measured (only a simulation).
5. No load / concurrency test (single-process uvicorn, SQLite); per-session scale only measured for the duplicate scan.
6. No HTTPS/mobile-browser field test (camera and GPS on phones need HTTPS; localhost used).
7. Liveness is defeated by a rotated photo (tilt) and by a bank of victim photos (§7.3). No texture/depth anti-spoofing.
8. Face photographs in screenshots are LFW stand-ins, not the team's faces.
9. The guide name, college, HOD, principal, academic year and e-mail addresses are unknown (placeholders).

## 9. Screenshot inventory (`docs/screenshots/`, 1440 px wide; tall pages captured full length)
| File | Screen |
|---|---|
| 01_landing | landing page hero + live statistics |
| 02_landing_how_it_works | landing, how-it-works section |
| 03_about | about / how it works page |
| 04_login_faculty, 05_login_student | sign-in (faculty / student portal) |
| 06_register_student | student registration with reference-face upload |
| 07_checkin_portal | paste-session-link portal |
| 09_create_session | new session form with geo-fence preview map |
| 10_session_share_qr | share link + QR after creation |
| 11_faculty_dashboard | dashboard: KPIs, check-ins per session, checks by stage, latest attempts |
| 12_sessions_list | sessions list |
| 13_session_records | live session: KPIs, share link, attendance records (present/absent) |
| 14_session_map | geo-fence map with check-ins |
| 15_session_log | verification log (live session) |
| 16_session_analytics | checks by stage, distance from centre |
| 17_session_closed_records, 18_session_closed_log | closed session records / log |
| 19_students, 19b_students_manage | student list; manage drawer (enrolment, device reset) |
| 20_checkin_signin | student check-in, sign-in step |
| 21_checkin_location_step | step 2 location |
| 22_checkin_challenge | step 3 random challenge ("Turn your head to your LEFT") |
| 23_checkin_photos_ready | two photos loaded (TILT RIGHT challenge) |
| 24_checkin_marked | step 5 "Marked. Present." with distance 7.7 m, liveness 1.00, identity 0.86 |
| 25_checkin_outside_geofence | blocked: outside geo-fence |
| 26_checkin_static_photo_rejected | blocked: static photo fails challenge |
| 27_checkin_locked | locked after 3 failed challenges |
| 28_checkin_identity_mismatch | blocked: face does not match reference |
| 29_checkin_duplicate_face_blocked | blocked: duplicate face (proxy) |
| 31_checkin_roll_not_allowed | blocked: roll number not allowed |
| 30_api_docs | FastAPI OpenAPI page |
| 32_excel_summary, 33_excel_attendance, 34_excel_verification_log | the 3 sheets of the real Excel export (opened in Excel) |

## 10. Reproduction
`scripts/docs_personas.py`, `scripts/capture_screenshots.py`, `scripts/capture_excel.py` (screens); `scripts/eval_face_verification.py`, `eval_face_failures.py`, `eval_liveness.py`, `eval_photo_bank_attack.py`, `eval_geofence.py`, `eval_latency.py` (metrics, outputs in `docs/evaluation/`). LFW is downloaded separately (https://ndownloader.figshare.com/files/5976018 and pairs file 5976006) and is not part of the repository.
