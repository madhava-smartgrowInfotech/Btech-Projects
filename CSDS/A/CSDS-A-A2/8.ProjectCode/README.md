# 🪄 Attendance Magic

**A Smart Geo-Fenced Attendance System with Live Challenge Verification**
CSE (Data Science) · Batch A2 · Base paper: *Real-Time Student Face Recognition Attendance System Using AI* (IARJSET Vol. 12 Issue 5, 2025, DOI 10.17148/IARJSET.2025.125183)

The base paper automates attendance with CNN face recognition on a classroom camera. This project keeps
face-based identity verification and strengthens it with **geo-fencing**, a **random live facial
challenge** (liveness) and **per-session duplicate-face checks**, all inside a **time-bound session**.

Everything is Python: Streamlit for the UI, SQLAlchemy for storage, MediaPipe + InsightFace for the AI.

---

## Features (mapped to the project objectives)

| # | Objective | Implementation |
|---|-----------|----------------|
| 1 | Faculty create time-bound sessions with configurable geo-fences | `ui/faculty.py` → `services.create_session()`; unique link `?session=<token>` + QR code |
| 2 | JWT auth, device identification, roll-number restrictions | `core/auth.py` (PBKDF2 passwords, PyJWT tokens bound to a device hash), `core/device.py` (browser fingerprint), device bindings + roll patterns in `core/services.py` |
| 3 | GPS location vs. session boundary | `core/geofence.py` (haversine), browser GPS via `streamlit-js-eval` |
| 4 | Liveness via random facial challenge with MediaPipe | `core/liveness.py` – 8 challenges (turn/tilt/look up-down/open mouth/close eyes) verified from Face Mesh landmarks |
| 5 | Prevent duplicate identities with InsightFace embeddings | `core/face_match.py` – ArcFace (buffalo_l) cosine similarity vs. enrolled face and vs. all faces already recorded in the session |
| 6 | Attendance summaries and Excel export | `core/export.py` – Summary, Attendance and Verification-Log sheets |

Extra: every attempt (pass or block, with the reason) is logged in `verification_attempts` for evaluation.

---

## Quick start

```bash
cd attendance_magic
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_demo.py        # demo faculty + 4 students
streamlit run app.py               # http://localhost:8501
```
or simply `./run.sh`.

The first run downloads the InsightFace `buffalo_l` model (~280 MB) to `~/.insightface/models`.

**Demo accounts** (from `seed_demo.py`)

| Role | Login | Password |
|------|-------|----------|
| Faculty | `faculty@college.edu` | `faculty123` |
| Students | `23K91A6706`, `23K91A6740`, `23K91A6757`, `24K95A6704` | `student123` |

Seeded students have **no enrolled face**; either register a new student (the form takes a reference
photo) or let faculty re-enrol them in the *Students* tab. For a quick trial set `AM_REQUIRE_ENROLLMENT=false`.

### Headless demo (no camera needed)

```bash
python scripts/demo_pipeline.py
```
Runs the exact service-layer pipeline used by the web app on a bundled sample photo and prints every
proxy-prevention check (already-marked, outside fence, static photo vs. challenge, identity mismatch,
duplicate face, disallowed roll, unregistered device) and writes `demo_attendance.xlsx`.

### Tests

```bash
pytest -q            # 23 tests: auth, geofence, liveness maths, face-match logic, services,
                     # model-backed tests, and two Streamlit AppTest end-to-end flows
```

---

## How a check-in works

```
Faculty                                   Student (phone browser)
────────                                  ───────────────────────
create session ─► link + QR ───────────►  open link  ?session=TOKEN
(course, window, lat/lon, radius,             │
 allowed rolls)                               ▼
                                          1. Sign in → JWT (bound to device hash)
                                          2. Eligibility: session live? roll allowed?
                                             not already marked? device registered?
                                          3. GPS → haversine distance ≤ radius + tolerance
                                          4. Random challenge (e.g. "turn head LEFT")
                                             photo 1 = neutral, photo 2 = pose
                                             MediaPipe landmarks → yaw/pitch/roll/MAR/EAR deltas
                                          5. InsightFace embedding:
                                               • photo 1 ≈ photo 2   (same person)
                                               • ≈ enrolled face     (identity)
                                               • ≉ any face already in session (duplicate)
                                          6. Record saved (UTC) + attempt log
view records / map / log ◄──────────────  ✅ marked
export Excel
```

---

## Project layout

```
attendance_magic/
├── app.py                 Streamlit entry (routes faculty portal / student check-in)
├── config.py              all settings (env-overridable)
├── core/
│   ├── db.py, models.py   SQLAlchemy (SQLite default, PostgreSQL/Supabase via DATABASE_URL)
│   ├── auth.py            PBKDF2 password hashing + JWT
│   ├── device.py          device fingerprint from request headers
│   ├── geofence.py        haversine + boundary check
│   ├── liveness.py        MediaPipe challenge verification
│   ├── face_match.py      InsightFace embeddings, identity + duplicate checks
│   ├── services.py        business logic / headless pipeline
│   ├── export.py          Excel export
│   └── timeutil.py        UTC storage, local display
├── ui/
│   ├── common.py          login/register forms, camera + GPS widgets
│   ├── faculty.py         create session, records, map, export, students
│   └── student.py         6-step check-in wizard
├── scripts/seed_demo.py   demo accounts
├── scripts/demo_pipeline.py  headless end-to-end demo
└── tests/test_core.py
```

---

## Configuration (environment variables)

See `.env.example`. Most important:

| Variable | Default | Meaning |
|----------|---------|---------|
| `AM_BASE_URL` | `http://localhost:8501` | Public URL used in session links |
| `AM_JWT_SECRET` | *(change it!)* | JWT signing secret |
| `DATABASE_URL` | `sqlite:///attendance_magic.db` | `postgresql+psycopg2://…` for Supabase (install `psycopg2-binary`) |
| `AM_ALLOW_MANUAL_LOCATION` | `true` | Show a manual lat/lon tab (turn **off** in production) |
| `AM_MAX_DEVICES_PER_STUDENT` | `1` | Device-binding strictness |
| `AM_DEFAULT_RADIUS_M`, `AM_GEOFENCE_TOLERANCE_M`, `AM_MAX_GPS_ACCURACY_M` | 60 / 15 / 150 | Geo-fence tuning |
| `AM_IDENTITY_THRESHOLD`, `AM_DUPLICATE_THRESHOLD` | 0.40 / 0.45 | Cosine-similarity thresholds |
| `AM_LIVENESS_*` | see `config.py` | Movement thresholds for each challenge |
| `AM_CAMERA_MIRRORED` | `true` | Streamlit's camera returns a selfie-mirrored image |
| `AM_REQUIRE_ENROLLMENT` | `true` | Students must enrol a reference face |
| `AM_TIMEZONE` | `Asia/Kolkata` | Display timezone (DB stores UTC) |

---

## Deployment notes

* **HTTPS is required** for browser camera and GPS on phones (except `localhost`). Put Streamlit behind
  nginx/Caddy with TLS, or use Streamlit Community Cloud / a VM with a domain, then set `AM_BASE_URL`.
* **Supabase/PostgreSQL:** `pip install psycopg2-binary`, set `DATABASE_URL` to the Supabase connection
  string; tables are created automatically on first start.
* **MediaPipe versions:** `mediapipe==0.10.21` bundles the Face Mesh model. If you must use a newer
  MediaPipe (≥ 0.10.30, no `solutions` API), download `face_landmarker.task` from Google's MediaPipe
  model page into `assets/` (or set `AM_FACE_LANDMARKER_MODEL`); `core/liveness.py` switches to the
  Tasks API automatically.
* CPU-only inference is fine: MediaPipe ≈ 20 ms and InsightFace ≈ 150 ms per image on a laptop.

---

## Evaluation ideas for the report

* **Proxy prevention** – re-run `scripts/demo_pipeline.py`; every block appears in the *Verification Log*
  sheet with the stage and reason.
* **Verification accuracy** – vary `AM_IDENTITY_THRESHOLD` / `AM_DUPLICATE_THRESHOLD` and record
  false-accept / false-reject counts from the log.
* **Response time** – time each stage with `time.perf_counter()` around the calls in `services.run_pipeline`.
