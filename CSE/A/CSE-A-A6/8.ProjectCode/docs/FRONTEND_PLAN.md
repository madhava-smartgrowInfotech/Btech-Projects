# Frontend Plan - Smart Rider Impairment Warning System (CSE-A-A6)

Design kit: **V1 - Aurora Glass** (TypeScript `.tsx`) · Ports: backend **8306**, frontend **5306**

The existing product is a **Tkinter desktop app** (`python app.py`). It has **no HTTP API**, so the "existing
endpoints" below are the functions the GUI calls. The desktop app stays untouched and working. A thin FastAPI
layer in `backend/` imports and exposes those **existing functions** (`core`, `vision`, `storage`, `research`; no
logic rewritten), and a new React app in `frontend/` talks to it.

Because the browser, not the server, owns the webcam, the camera is read with `getUserMedia`; each frame is drawn to
a 640x480 canvas and posted to the API. The server runs the **same** `Vision.process -> RiskEngine.update` code and
returns the landmark-annotated frame, exactly like the Tk preview. Video frames stay in RAM and are never saved.

> Naming note: the prompt calls the product "Smart Alcohol Intoxication Detection and Prevention". The code, README
> and VERIFICATION.md call it **Smart Rider Impairment Warning System for Two-Wheelers** and state that a camera
> **cannot confirm alcohol use**. The UI uses the code's name and its honest wording (possible drowsiness /
> impairment, not intoxication).

---

## 1. Backend inventory

### 1a. Existing functions the GUI calls (the real "backend")

| Module | Function / class | Used by |
|--------|------------------|---------|
| `core` | `Settings` (+`validate`), `Observation`, `Decision`, `RiskEngine.update/reset`, `Calibration.add`, `simulate(scenario, elapsed, now)`, `NORMAL/WARNING/UNKNOWN` | Monitor, Thresholds |
| `vision` | `Vision.process(frame, now)` (quality gates, MediaPipe EAR, head roll, landmark dots), `CameraWorker` (replaced by browser camera) | Monitor |
| `storage` | `Store.add`, `recent(500)`, `export(path)`, `load_settings`, `save_settings` | History, Thresholds, Monitor |
| `research` | `evaluate(csv, out_dir, test_subjects)`, `extract_windows`, `metrics`; writes `report.json`, `confusion_matrix.png`, `window_features.csv`, `centroid_model.npz` | Research |
| `extract_video.py`, `setup_model.py`, `camera_check.py` | offline CLI tools (documented on the About screen, not GUI features) | - |
| `app.py` constants | `SCENARIOS`, disclaimers, status strings | all screens |

### 1b. New HTTP API (FastAPI, `backend/`, port 8306)

| # | Method | Path | Request | Response |
|---|--------|------|---------|----------|
| 1 | GET | `/api/health` | - | `{status, landmark_model, history_events, model_report}` |
| 2 | GET | `/api/config` | - | `{scenarios[], bounds{}, defaults{}, frame{w,h}, quality_gates[], disclaimers[], states{}}` |
| 3 | GET | `/api/about` | - | `{title, summary, pipeline[], formulas[], limitations[], reference{}, cli_tools[]}` |
| 4 | POST | `/api/session` | - | `{session_id, state}` (one engine + `Vision` per browser tab, like one `Application`) |
| 5 | DELETE | `/api/session/{id}` | - | `{closed}` (releases the landmarker; also logs the "Monitoring stopped" event) |
| 6 | GET | `/api/session/{id}` | - | full `state` (source, monitoring, calibration, decision, metrics, status text) |
| 7 | POST | `/api/session/{id}/source` | `{source: "camera"\|"simulation"\|"none", scenario?}` | `state` (= Start/Stop Camera, Simulation Mode, scenario change) |
| 8 | POST | `/api/session/{id}/monitoring` | `{active: bool}` | `state` (= Start/Stop Monitoring; 409 if no source / calibrating) |
| 9 | POST | `/api/session/{id}/calibration` | `{active: bool}` | `state` (= Calibrate; 409 in simulation / no camera) |
| 10 | POST | `/api/session/{id}/frame` | multipart `frame` (JPEG 640x480) | `{state, preview: data-URL JPEG with landmark dots}` (= `consume()`) |
| 11 | POST | `/api/session/{id}/tick` | - | `{state}` (advances the scripted simulation, = `simulate()` in `tick()`) |
| 12 | GET | `/api/settings` | - | `{settings{}, calibrated, note}` (`Store.load_settings`) |
| 13 | PUT | `/api/settings` | `{ear_threshold, closure_seconds, persistence_seconds, closed_fraction, tilt_degrees, cooldown_seconds}` | `{settings{}}`; 422 with the validator message; stops monitoring on open sessions |
| 14 | GET | `/api/history` | `?limit=500` | `{events[], total, summary{warnings, unknown, normal, live, simulation}}` (`Store.recent`) |
| 15 | GET | `/api/history/export` | - | CSV download (`Store.export`) |
| 16 | GET | `/api/research` | - | `{trained, report?, files[]}`; `{trained:false}` (200) when "Model not trained" |
| 17 | POST | `/api/research/evaluate` | multipart `file` (CSV), `test_subjects` | `report`; 422 with the `evaluate()` ValueError text |
| 18 | GET | `/api/research/confusion-matrix` | - | PNG written by `evaluate()` (**additive, read-only**) |
| 19 | GET | `/docs` | - | Swagger UI |

Additive pieces (all read-only or thin glue): #2, #3, #14 `summary` aggregates, #18. No core/vision/storage/research
logic is edited. A fresh `Store` is opened per request because `sqlite3` connections are thread-bound.

## 2. Feature inventory (existing product) and where it lands

| ID | Feature (from `app.py` / README) | Screen | Status |
|----|----------------------------------|--------|--------|
| F1 | Start Camera / Stop Camera, camera index 0-9 (browser device picker) | Monitor | [x] |
| F2 | Live preview with eye landmark dots, "no video or face images are saved" note | Monitor | [x] |
| F3 | Signal quality + light level readout ("Good", "No face", "Poor lighting", ...) | Monitor | [x] |
| F4 | Calibrate: 8-15 s capture, progress bar, saves personal EAR threshold, failure keeps old one | Monitor | [x] |
| F5 | Start / Stop Monitoring, 2 s warm-up, three outputs Normal / Possible impairment or drowsiness / Unable to assess | Monitor | [x] |
| F6 | Simulation Mode + 4 scenarios (Normal, Prolonged eye closure, Missing face, Poor lighting), scenario switch keeps monitoring | Monitor | [x] |
| F7 | Live measurements: smoothed EAR, closure s, blink rate/min, closed fraction, head roll, threshold | Monitor | [x] |
| F8 | Reason text + alert message ("stop somewhere safe") + source banner (LIVE CAMERA / SIMULATION) | Monitor | [x] |
| F9 | Optional alert sound (browser beep replaces Tk bell, 15 s cooldown from the engine) | Monitor | [x] |
| F10 | Event logging to SQLite (state change, 5 s snapshots, alerts, final stop event) | Monitor -> History | [x] |
| F11 | History: up to 500 events, UTC timestamps, simulations labelled | History | [x] |
| F12 | History EAR chart, live vs simulation series | History | [x] |
| F13 | Export CSV of all events | History | [x] |
| F14 | Thresholds editor (6 values, validated bounds, saving stops monitoring) | Thresholds | [x] |
| F15 | Research / Evaluation: CSV format guide, held-out subject IDs, offline train + metrics | Research | [x] |
| F16 | "Model not trained" status, saved report viewer, confusion matrix | Research | [x] |
| F17 | Safety disclaimers (not alcohol test, Normal != fit to ride, stationary demo only) | Landing, Monitor footer, About | [x] |
| F18 | Formulas, quality gates, rule defaults, limitations, research reference, offline CLI tools | About | [x] |
| F19 | Graceful camera / permission / model-missing errors | Monitor | [x] |

## 3. Screen map

No login: the original is a single-user local tool with no accounts, so none is added.

| Route | Screen | Kit pieces |
|-------|--------|-----------|
| `/` | **Landing** - Aurora hero, live-verdict card (real simulated run), how it works, honesty/limits, CTA | `AuroraBackground`, `Reveal`, `Stagger`, `MagneticButton`, `CountUp`, landing pieces |
| `/monitor` | **Monitor** - source, preview, calibration, state card, metrics, reason/alert, sound | `AppShell`, `Card`, `Button`, `Tabs`/`Select`, `Badge`, progress, `Toast`, `Skeleton` |
| `/history` | **History** - stat cards, EAR chart (live vs simulation), table, export | `StatCard`, `Chart`, `Table`, `EmptyState`, `Skeleton` |
| `/thresholds` | **Thresholds** - six validated fields, reset to defaults, calibrated badge | `Field`, `Button`, `Card`, `Toast` |
| `/research` | **Research** - status, CSV guide, upload + held-out IDs, metrics, confusion matrix | `FileDrop`, `Field`, `Card`, `Table`, `Chart` |
| `/about` | **How it works** - pipeline, formulas, gates, limitations, reference, CLI tools | `Card`, `Tabs`, `Reveal` |

Cross-cutting: dark mode toggle in the topbar (persisted), drawer sidebar under 1024px, `prefers-reduced-motion`,
lazy-loaded routes, skeleton / empty / error / success states on every data screen.

## 4. Environment findings

- `.venv` shipped with the repo pointed at a missing `C:\Users\kavya\...` Python; it is rebuilt with Python 3.14 from
  `requirements.txt` (+ `backend/requirements.txt`). `run.bat` will rebuild a dead venv.
- `.env` created with `BACKEND_PORT=8306`, `FRONTEND_PORT=5306`.
- Baseline before any change: `unittest` 20/20 pass, `smoke_test.py` passes, `Vision()` initialises with
  `models/face_landmarker.task`, `Store` reads `data/events.sqlite3` (14 existing events).

## 5. Verification record (Step 4)

Walked with Playwright against the running app (`scripts/capture_screens.py`, `scripts/check_layout.py`) and the API
smoke test (`scripts/smoke_test.py`, 34 checks). All 19 features above are ticked as working.

| Check | Result |
|-------|--------|
| `npm run build` (`tsc -b && vite build`) | passes, no errors |
| API smoke test, temp storage | 34 / 34 pass |
| Original unit tests / Tk smoke test (desktop app untouched) | 20 / 20 and PASS |
| Simulation: Prolonged eye closure -> *Possible impairment or drowsiness* with "stop somewhere safe" | pass |
| Scenario switch keeps monitoring; Missing face -> *Unable to assess*; Normal -> *Normal* | pass |
| Camera path (fake webcam, real face photo): landmarks drawn, quality Good, calibration saved (threshold 0.183), verdict Normal | pass |
| History: stats, EAR chart (live vs simulation), filter, search, CSV export | pass |
| Thresholds: client validation, server validation, save, reset to defaults | pass |
| Research: "Model not trained" empty state, synthetic sample trains and is flagged, bad CSV rejected with the reason | pass |
| Demo login, protected routes, sign out, 401 handling | pass |
| Alert sound (3 oscillator beeps on a warning) | pass |
| 360 / 768 / 1440 px x light / dark x every route: no horizontal overflow | pass |
| Console clean (no errors, no unhandled rejections, no failed requests) | pass |
| `prefers-reduced-motion`, Escape closes select and drawer, hidden file input labelled | pass |

Screenshots: `docs/screenshots/`.

## 6. Decisions and additions

* **Demo login added** (`demo@smartrider.app` / `Demo@1234`), HMAC-signed 12 h token, because the desktop app had none and the brief asked for one.
* **Additive endpoints** (read-only or glue): `/api/config`, `/api/about`, `/api/history` summary, `/api/research/confusion-matrix`, `/api/research/sample-csv`, `/api/auth/*`, `/api/session/*`.
* **Synthetic data**: `backend/synthetic.py` generates the demo research CSV from a seeded RNG; reports built from it are flagged.
* **Browser Alert sound** replaces the Tk bell (Web Audio, three beeps) and still follows the engine's 15 s cooldown.
* **Product name**: the code and README say "Smart Rider Impairment Warning System for Two-Wheelers" and that a camera cannot confirm alcohol use, so the UI follows them rather than the prompt's "Alcohol Intoxication Detection".
