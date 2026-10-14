# Frontend Plan — Attendance Magic (CSDS-A-A2)

**Design variant:** V2 — Neo Brutal Grid · **Ports:** backend `8102`, frontend `5102`

The existing product is a **Streamlit** app (`app.py`, `ui/`) over a pure-Python service layer (`core/`).
It has **no HTTP API**. The Streamlit app stays untouched and runnable (`streamlit run app.py`).
A thin FastAPI layer (`backend/api.py`) imports and exposes the existing `core/` functions, and a new
React app (`frontend/`) is built on top of it.

---

## 1. Existing "endpoints" (service functions the Streamlit UI calls)

The product had no routes; these are the callable surfaces in `core/` that the UI uses, now exposed over HTTP.
`(new)` = additive endpoint, no existing behaviour changed.

| Method | Path | Wraps | Request | Response |
|---|---|---|---|---|
| GET | `/api/health` | `init_db`, `config` | — | `{status, app, tagline, db}` |
| GET | `/api/config` (new, read-only) | `config.*`, `liveness.CHALLENGES` | — | public settings: manual-location flag, radius/tolerance/accuracy, thresholds, enrolment rule, JWT expiry, timezone, max devices, challenge list |
| GET | `/api/models` | `liveness.get_detector`, `face_match.get_embedder` | — | `{landmarks, recognition, db}` (warms models) |
| GET | `/api/stats` (new, read-only) | counts over existing tables | — | `{sessions, live_sessions, records, attempts, blocked, students, enrolled}` |
| POST | `/api/auth/login` | `services.authenticate` | `{username, password, role?}` | `{token, user, expires_at}` · 401 bad creds · 403 wrong portal |
| POST | `/api/auth/register` | `liveness.check_neutral`, `services.register_user` | multipart `role, full_name, username?, roll_number?, password, face?` | `{user}` |
| GET | `/api/auth/me` | `auth.verify_token` (device-bound) | Bearer | `{user, device}` |
| GET | `/api/sessions` | `services.list_sessions` | Bearer (faculty) | `[session + present/blocked/attempt counts]` |
| POST | `/api/sessions` | `timeutil.to_utc`, `services.create_session` | `{course_code, course_name, section, start_local, duration_min, latitude, longitude, radius_m, allowed_rolls}` | `{session}` |
| GET | `/api/sessions/{id}` | `get_session_by_id`, `records_for`, `attempts_for`, `expected_rolls`, `export.records_dataframe` | Bearer (faculty) | `{session, metrics, rows, records, attempts}` |
| POST | `/api/sessions/{id}/close` | `services.close_session` | Bearer (faculty) | `{session}` |
| GET | `/api/sessions/{id}/export` | `export.to_excel_bytes` | Bearer (faculty) | `.xlsx` (Summary / Attendance / Verification Log) |
| GET | `/api/dashboard` (new, read-only) | `list_sessions`, `records_for`, `attempts_for` | Bearer (faculty) | totals, per-session series, blocks-by-stage, recent attempts |
| GET | `/api/qr?text=` | `qrcode` (same as `ui.common.qr_png`) | — | PNG |
| GET | `/api/students` | `services.list_students` | Bearer (faculty) | `[{id, roll, name, username, enrolled, registered, devices}]` |
| POST | `/api/students/{id}/reset-devices` | `services.reset_devices` | Bearer (faculty) | `{removed}` |
| POST | `/api/students/{id}/enroll` | `liveness.check_neutral`, `services.enroll_face` | multipart `face` | `{ok}` |
| GET | `/api/public/sessions/{token}` | `get_session_by_token` | — | course, section, window, status, faculty, centre, radius |
| GET | `/api/checkin/{token}/state` | wizard state (server-held, like `st.session_state`) | Bearer (student) | `{step, challenge, tries_left, …}` |
| POST | `/api/checkin/{token}/start` | `check_eligibility` + `log_attempt` | Bearer (student) | `{ok, reason, state}` |
| POST | `/api/checkin/{token}/location` | `geofence.check_geofence` + `log_attempt` | `{lat, lon, accuracy?}` | `{inside, distance_m, allowed_m, reason, state}` |
| POST | `/api/checkin/{token}/neutral` | `liveness.analyze` + `check_neutral` | multipart `image` | `{ok, message}` (photo-1 feedback) |
| POST | `/api/checkin/{token}/liveness` | `liveness.verify_challenge` + `log_attempt` | multipart `neutral, challenge` | `{passed, score, reason, state}` (new random challenge per retry, lock after 3) |
| POST | `/api/checkin/{token}/face` | `face_match.embed`, `verify_faces`, `session_embeddings`, re-`check_eligibility`, `record_attendance` | Bearer | `{passed, reason, record, state}` |
| POST | `/api/checkin/{token}/reset` | clears wizard state | Bearer | `{state}` |

Auth: the JWT from `core/auth.py` is sent as `Authorization: Bearer`; it is verified on every request
against the device hash (`core/device.fingerprint` over the request headers + a per-browser id sent as
`X-Device-Id`), exactly like the Streamlit app verifies it on every rerun.

## 2. Existing features & screens (from README, `app.py`, `ui/`)

| # | Feature | Where today | Status in React |
|---|---|---|---|
| F1 | Faculty sign in (username/email, wrong-portal guard) | `ui/common.login_form` | [x] |
| F2 | Faculty register | `ui/common.register_form` | [x] |
| F3 | Student sign in (roll no. or username) | `ui/common.login_form` | [x] |
| F4 | Student register with reference-face photo (neutral-face check, enrolment required) | `ui/common.register_form` | [x] |
| F5 | JWT bound to device; expiry shown; sign out | `common.current_claims`, sidebar | [x] |
| F6 | Create time-bound session: code, name, section, date, start, duration | `faculty._create_session` | [x] |
| F7 | Geo-fence centre via browser GPS or manual lat/lon (when allowed) + radius slider 10–500 m | `common.location_picker` | [x] |
| F8 | Allowed roll patterns (`*`, prefixes, explicit list) | `faculty._create_session` | [x] |
| F9 | Map preview of centre + radius | `st.map` | [x] |
| F10 | Share link + QR code + window summary | `faculty._create_session` | [x] |
| F11 | Session list with status badge (live/upcoming/expired/closed) | `faculty._sessions` | [x] |
| F12 | Session metrics: status, present, expected, blocked | `faculty._sessions` | [x] |
| F13 | Export Excel (Summary, Attendance incl. absentees, Verification Log) | `export.to_excel_bytes` | [x] |
| F14 | Close session now | `services.close_session` | [x] |
| F15 | Refresh | button | [x] |
| F16 | Attendance records table (with absentees for explicit lists) | `export.records_dataframe` | [x] |
| F17 | Records map (centre + student points) | `st.map` | [x] |
| F18 | Verification log (time, roll, stage, pass/blocked, reason, device) | expander | [x] |
| F19 | Students list (roll, name, username, face enrolled, registered) | `faculty._students` | [x] |
| F20 | Reset a student's device bindings | `services.reset_devices` | [x] |
| F21 | Re-enrol a student's reference face (camera, neutral check) | `faculty._students` | [x] |
| F22 | Student portal: paste session link/token | `student.render(None)` | [x] |
| F23 | Session link `?session=TOKEN` opens check-in with course header, status, window, faculty | `app.py`, `student.render` | [x] |
| F24 | 6-step progress (Sign in → Eligibility → Location → Live challenge → Face match → Done) | `student._progress` | [x] |
| F25 | Eligibility: live window, roll allowed, not already marked, one roll per device, device binding | `check_eligibility` | [x] |
| F26 | Location verification vs geo-fence (GPS or manual) | `geofence.check_geofence` | [x] |
| F27 | Random live challenge: neutral photo + pose photo, neutral feedback, 3 tries, new challenge per retry, lock + start over | `student` step 3 | [x] |
| F28 | Face verification: frame consistency, identity vs enrolled, duplicate vs session; retake on face error | `student` step 4 | [x] |
| F29 | Success screen: distance, liveness score + challenge, identity, max duplicate sim, thresholds, celebration | `student` step 5 | [x] |
| F30 | Every attempt logged with stage + reason | `log_attempt` | [x] |
| F31 | "How it works" explainer + model/DB info | `app.py` about tab | [x] |

## 3. Screen map (React)

| Route | Screen | Features | |
|---|---|---|---|
| `/` | **Landing** — oversized masked headline, live-stats marquee, how-it-works, feature grid, stats strip (`/api/stats`), CTA, footer. `/?session=TOKEN` redirects to check-in | F31, F23 | |
| `/login` | Sign in — Faculty / Student tabs | F1, F3, F5 | |
| `/register` | Register — Faculty / Student (student: `Stepper` + camera/`FileDrop` reference face) | F2, F4 | |
| `/about` | How it works — the 7 checks, pipeline timeline, models + DB, live thresholds from `/api/config` | F31 | |
| `/app` | **Faculty dashboard** — marquee ticker of live stats, `StatCard`s, charts (check-ins per session, blocks by stage), recent sessions, recent attempts | — **(added)** | ✚ |
| `/app/sessions/new` | Create session — form, GPS/manual location, radius, roll patterns, Leaflet map preview, then link + QR panel | F6–F10 | |
| `/app/sessions` | Sessions — sortable/paginated table with status badges, search | F11 | |
| `/app/sessions/:id` | Session detail — metrics, link/QR, export, close (confirm modal), refresh/auto-refresh, records table, records map, verification log, attempts chart | F12–F18, F30 | |
| `/app/students` | Students — table, search, drawer to reset devices / re-enrol face | F19–F21 | |
| `/checkin` | Student portal — paste link or token | F22 | |
| `/checkin/:token` | Check-in wizard — Stepper over the 6 steps, camera capture (mirrored like Streamlit), GPS, challenge, face match, success | F23–F29 | |
| `*` | 404 | — | ✚ |

✚ = added. The Streamlit app keeps working on its own port (8501).

## 4. Decisions / defaults

- **Backend**: `backend/api.py` (FastAPI) imports `config`, `core.*` directly. No changes in `core/`, `ui/`, `app.py`.
- **Check-in state** is held server-side per (student, session, device), as Streamlit held it in `session_state`, so
  the random challenge is always chosen by the server and the order of checks cannot be skipped.
- **Session links** produced by the React UI are `http://<frontend>/?session=TOKEN` — same shape as the Streamlit link.
- **Camera** frames are captured mirrored (selfie), matching `AM_CAMERA_MIRRORED=true` / Streamlit's camera widget.
- **Python**: `venv/` on Python 3.11 (mediapipe 0.10.21 has no 3.14 wheel; the old `.venv` is 3.14 and empty).
- **Maps**: Leaflet + OpenStreetMap tiles, lazy-loaded.

---

## 5. Verification (Step 3) — all 31 features ticked above

| Check | Result |
|---|---|
| `npm run build` | ✅ passes, no errors; every route is its own chunk, Leaflet + Recharts lazy-loaded |
| `scripts/smoke_test.py` (new, in-process HTTP, real MediaPipe + InsightFace) | ✅ 41/41 checks: register (face required), wrong-portal + bad password, device-bound JWT, session create, full 6-step check-in, outside fence, static photo vs challenge, duplicate face, identity mismatch, records/log/Excel/dashboard/students, reset devices, re-enrol, close session |
| `pytest -q` (original 23 tests incl. Streamlit AppTest) | ✅ 23 passed — Streamlit app untouched and working |
| Browser walk (Chrome via Playwright, `run.bat` servers) | ✅ landing → login → create session (manual + GPS) → QR/link → enrol face → student check-in via link (GPS, challenge fail → new challenge, tilt pass, face match, success) → records / map / log / analytics → Excel download → close session → closed-session block, invalid link |
| Console | ✅ no errors, no unhandled rejections, no asset 404s (only deliberate API 401/404 in negative tests) |
| 360 / 768 / 1440 px × light / dark | ✅ every route, no horizontal page scroll; sidebar → drawer + bottom bar, tables → cards at ≤ 640 px |
| Dark mode | ✅ topbar toggle, persisted (`am.theme`), honours `prefers-color-scheme` |
| Reduced motion | ✅ headline masks / reveals collapse to fades, marquee static, Lenis off |
| Keyboard | ✅ skip link, visible focus rings, labelled inputs, modal focus trap, Escape closes only the top overlay |

Bugs found and fixed during the walk: buttons inside forms defaulted to `submit`; Leaflet bounds before first view;
mobile table cards lost their class; hidden tooltip caused 7 px overflow at 360 px; menu button visible on desktop.
