# FRONTEND PLAN - FlowSense (kit V5 · Kinetic Mono)

Ports: backend **8310**, frontend **5310** (`.env`). The product today is a **Streamlit app** (`app.py`) over three
Python modules in `smart_traffic/`. It has **no HTTP API**, so `backend/` adds a thin FastAPI layer that imports and
exposes the existing functions (`Sim`, `QueuePredictor`, `vision.*`). `smart_traffic/` and `app.py` stay untouched.

## 1. Backend inventory

### 1.1 Existing functions (what the Streamlit page calls)

| Module | Function / class | Used by |
|---|---|---|
| `sim.py` | `Sim(rows, cols, controller, demand, seed, start_hour, predictor, emergencies, emg_rate, violations)` | Live, Benchmark, Violations, Prediction |
| `sim.py` | `Sim.run(s)`, `.step()`, `.summary()`, `.in_network()`, `.feature_matrix()`, `._new_vehicle(emg=True)` | all |
| `sim.py` | `Sim` state: `q, phase, timer, clear, pred, transit, qtot, viol_log, emg_log, active_emg, _preempt_active, entries` | map, KPIs, tables |
| `sim.py` | `CONTROLLERS`, `APPROACHES`, `PHASE_NAME`, `LINK_TIME`, `demand_profile()` | all |
| `predictor.py` | `QueuePredictor().fit()` (≈8 s), `.predict(X)`, `.metrics`, `.test`, `.importance`, `.n_samples` | Prediction, Live (ML forecast) |
| `vision.py` | `render_scene`, `detect_classical`, `detect_yolo`, `density_report`, `annotate`, `yolo_available`, `sample_image_path` | Vision |

### 1.2 HTTP API to add (`backend/`, FastAPI, prefix `/api`)

All additive. Request/response are JSON unless stated.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{ok, predictor_ready, predictor_error, yolo_available, sim_clock}` |
| GET | `/api/meta` | - | `{controllers:{key:label}, approaches, grids:["2x2","3x3"], vehicle_types, version}` |
| GET | `/api/live` | - | live snapshot: `config, clock, kpis, banner, map{roads,signals,vehicles,labels,bounds}, queue_series, junctions[], t` |
| PUT | `/api/live/config` | `{grid, controller, demand, emergencies, use_ml}` | live snapshot (a grid change restarts the sim, as in `get_live`) |
| POST | `/api/live/step` | `{seconds}` (1-900) | live snapshot - "Run live" = repeated 2 s steps, "Skip 5 min" = 300 |
| POST | `/api/live/ambulance` | - | live snapshot + `{entry:{junction,approach}}` |
| POST | `/api/live/reset` | - | live snapshot |
| POST | `/api/benchmark` | `{grid, seconds, demand, seeds, start_hour, use_ml}` | `{kpis, controllers:{key:{label,summary_runs,mean,queue_series,emergency_delays[]}}, table}` (cached per request key, like `st.cache_data`) |
| POST | `/api/benchmark/sweep` | `{grid, use_ml}` | `{levels, series:{controller:[delay…]}}` |
| GET | `/api/benchmark/last` | - | last benchmark violation rows (feeds Violations page) |
| GET | `/api/vision/synthetic` | `?vehicles&ambulance&flash&seed` | `{frame_png, annotated_png (base64), detections[], report, truth_count}` |
| GET | `/api/vision/sample` | `?conf` | same shape, YOLOv8 on the bundled sample photo (503-style error if `ultralytics` missing) |
| POST | `/api/vision/analyze` | multipart `file`, `conf` | same shape, YOLOv8 on the uploaded image |
| GET | `/api/prediction` | - | `{kpis, metrics_table, scatter[≤1500], importance[], n_samples}` (202 + `{training:true}` while the model trains) |
| GET | `/api/prediction/live` | - | `{available, clock, labels[], queue_now[], forecast[], worst{junction,approach,from,to}}` |
| POST | `/api/prediction/simulate` | `{seconds:180}` | same as `/api/live` snapshot |
| GET | `/api/violations` | - | `{kpis, by_junction[], per_minute[], log[], last_benchmark[]}` |

Predictor trains once in a background thread on startup; `/api/health` reports `predictor_ready`.

## 2. Feature inventory (every Streamlit feature → must appear)

**Global**
- G1 Navigation between the 6 pages
- G2 Network settings: road network 2×2 / 3×3
- G3 "Use ML queue forecast" toggle
- G4 Hero strip: product name, tagline, capability chips (YOLOv8 · ML · CV · Emergency Priority · Inter-Junction Communication · Violation Detection)
- G5 First-run model-training notice

**Live Control Center**
- L1 Signal controller select (4 controllers)
- L2 Traffic demand slider 0.4-2.0 step 0.1
- L3 Emergency vehicles toggle
- L4 ▶ Run live (60 s, 30 ticks × 2 s with redraw)
- L5 ⏭ Skip 5 min
- L6 🚑 Send ambulance
- L7 ↺ Reset
- L8 KPI row: Sim clock + demand multiplier · Vehicles in network + queued · Avg delay/veh · Emergency delay (+served/active) · Violations caught
- L9 Emergency banner (pre-empting / green wave / "controller ignores it")
- L10 Road-network map: roads, vehicle squares by type, ambulance star, signal heads (green / clearing / red), junction labels with ⚡ pre-empt + phase + timer, legend
- L11 "Vehicles queued (network total)" area chart (last 400 s)
- L12 Junction status table: Junction, Green (+clearing), Timer, Queue N/E/S/W, Forecast +30 s, Pre-empt
- L13 Legend caption

**Controller Benchmark**
- B1 Settings: Duration (10/15/20/30/45/60 min), Demand 0.5-1.8, Random seeds 1-5, Start hour 0-23
- B2 ▶ Run benchmark (4 controllers on identical traffic)
- B3 KPIs: Delay vs fixed-time · Delay vs base paper · Emergency delay · Fuel saved (+ kg CO₂)
- B4 Bar chart Avg delay / vehicle (mean ± std per controller)
- B5 Bar chart Emergency delay
- B6 Line chart: queued vehicles over time per controller
- B7 Box plot: emergency-vehicle delay distribution
- B8 Full results table (mean over seeds)
- B9 Demand sweep (0.6-1.8) line chart with progress
- B10 Empty state before the first run

**Vision (YOLOv8)**
- V1 Input mode: Synthetic overhead scene · YOLOv8 sample photo · YOLOv8 upload
- V2 Synthetic controls: vehicles 2-16, ambulance present, flash frame A/B, scene seed
- V3 YOLO confidence threshold 0.1-0.9
- V4 Image upload (jpg/jpeg/png)
- V5 Camera frame + annotated detections side by side (magenta ring = light-bar cluster)
- V6 KPIs: vehicles detected (by class) · Density PCU + % capacity · Congestion level · Emergency vehicle yes/no · Recommended green (s)
- V7 Ground-truth vs detected caption (synthetic)
- V8 "How it works" panel
- V9 Error state when `ultralytics` is missing

**Traffic Prediction**
- P1 KPIs: training samples · MAE (GBM) · R² (GBM) · error vs persistence
- P2 Predicted-vs-actual scatter (held-out test, ≤1500 pts) with ideal line
- P3 Feature-importance bars
- P4 Model-comparison table (Persistence / Random Forest / Gradient Boosting)
- P5 Live forecast: queue now vs +30 s per approach (grouped bars)
- P6 Highest predicted build-up callout
- P7 "Simulate 3 minutes now" when the live sim is < 40 s old

**Violation Detection**
- Vi1 Simulate 10 more minutes
- Vi2 KPIs: total · red-light · wrong-way · avg confidence
- Vi3 Violations by junction (stacked bars)
- Vi4 Violations per simulated minute
- Vi5 Evidence log table (time, junction, approach, kind, plate, vehicle, confidence), newest first
- Vi6 Empty state before any violation
- Vi7 "Violations by controller (last benchmark)" table
- Vi8 Explanatory caption

**About & Paper**
- A1 Base paper citation + DOI link + gap statement
- A2 Adopted-vs-advanced table (7 rows)
- A3 System pipeline diagram (Camera → YOLOv8 / light-bar → density → ML forecast → controller ↔ neighbours; violation detector)
- A4 Controller list
- A5 How to run + model-assumption note (saturation flow, link time, clearance, start-up loss)

## 3. Screen map (what gets built)

| Route | Screen | Covers |
|---|---|---|
| `/` | **Landing** - three.js wire-grid hero, live terminal feed, counters from the real simulator, capability strip | G4 |
| `/app` | **Live control center** | G1-G3, L1-L13 |
| `/app/benchmark` | **Controller benchmark** | B1-B10 |
| `/app/vision` | **Vision** | V1-V9 |
| `/app/prediction` | **Traffic prediction** | P1-P7, G5 |
| `/app/violations` | **Violations** | Vi1-Vi8 |
| `/app/about` | **About & paper** | A1-A5 |

Shared: AppShell (sidebar → drawer < 1024 px), topbar (network grid select, ML toggle, API/pipeline status dot,
activity log, shortcuts, theme toggle), command palette (jump to screen), activity log drawer (real API events),
toasts, keyboard `g`+letter navigation.

## 4. Decisions / defaults

- **Demo login added** (`/login`, one operator account from `.env`, signed token): protects every `/api` route except health, login and the landing-page preview. The Streamlit app has none, so this is purely additive.
- Live sim is **one shared server-side `Sim`** (same as Streamlit's `st.session_state.sim`); Prediction and Violations read it.
- Map is drawn client-side in SVG from server-computed positions (same geometry as `draw_map`).
- "Run live" calls `/api/live/step` with 2 s ticks 30 times so the map animates from real state.
- Kit files are product-neutral only partly (tax-fraud coupling in `AppShell`, `CommandPalette`, `display.jsx`, `ActivityLog`):
  those *copies* are adapted; missing `lib/reduced`, `lib/activity`, `api`, `format`, `reactbits/Backdrop` are written.
- `ultralytics` was not installed on this machine: installed (it also upgraded the system PyTorch 2.2.0 -> 2.14.1), so the YOLO modes are verified end-to-end. `run.bat` installs it into the project `.venv` from `backend/requirements-yolo.txt` and keeps going if that fails.
- Extra endpoints beyond the table in section 1.2: `POST /api/auth/login`, `GET /api/auth/demo`, `GET /api/auth/me`, `GET /api/public/pulse` (public preview simulation for the landing page; also returns the headline fixed-time vs advanced numbers).

## 5. Tick-off (Step 4)

Verified in the running app by `scripts/smoke_test.py` (API, 31 checks), `scripts/capture_screens.py` (every screen with real data, console clean)
and `scripts/check_ui.py` (360 / 768 / 1440 px x light / dark, keyboard, drawer, reduced motion). Screenshots: `docs/screenshots/`.

| ID | Feature | Status | Where it lives |
|---|---|---|---|
| G1 | Navigation between the 6 pages | ✅ | sidebar / drawer, `g`+key, `/` switcher |
| G2 | Road network 2×2 / 3×3 | ✅ | sidebar "Network settings" (restarts the live sim, as before) |
| G3 | ML queue forecast toggle | ✅ | sidebar "Network settings" |
| G4 | Hero + capability chips | ✅ | landing page (headline, marquee of the six capabilities) |
| G5 | Model-training notice | ✅ | Prediction page progress bar, sidebar status "model training" |
| L1 | Controller select (4) | ✅ | Live control > Scenario |
| L2 | Demand slider 0.4-2.0 | ✅ | Live control > Scenario |
| L3 | Emergency vehicles toggle | ✅ | Live control > Scenario |
| L4 | Run live (60 s, 30 × 2 s) | ✅ | button + progress, Stop button added |
| L5 | Skip 5 min | ✅ | Live control |
| L6 | Send ambulance | ✅ | Live control (toast names the entry road) |
| L7 | Reset | ✅ | Live control |
| L8 | 5 KPI tiles | ✅ | Live control |
| L9 | Emergency banner (3 variants) | ✅ | Live control |
| L10 | Road-network map (roads, vehicles, ambulance star, signals, ⚡ labels, legend) | ✅ | SVG `TrafficMap` |
| L11 | Queued-vehicles area chart | ✅ | Live control (empty state before any traffic) |
| L12 | Junction status table | ✅ | Live control (cards below 640 px) |
| L13 | Legend caption | ✅ | Live control |
| B1 | Duration / demand / seeds / start hour | ✅ | Benchmark > Settings |
| B2 | Run benchmark | ✅ | Benchmark |
| B3 | 4 KPIs | ✅ | Benchmark |
| B4 | Avg-delay bars (mean ± std) | ✅ | Benchmark |
| B5 | Emergency-delay bars | ✅ | Benchmark |
| B6 | Queued vehicles over time | ✅ | Benchmark |
| B7 | Emergency-delay box plot | ✅ | Benchmark |
| B8 | Full results table | ✅ | Benchmark |
| B9 | Demand sweep | ✅ | Benchmark |
| B10 | Empty state before first run | ✅ | Benchmark |
| V1 | Input mode (synthetic / sample / upload) | ✅ | Vision tabs |
| V2 | Synthetic controls (vehicles, ambulance, flash A/B, seed) | ✅ | Vision |
| V3 | YOLO confidence threshold | ✅ | Vision |
| V4 | Image upload (jpg / jpeg / png) | ✅ | Vision (drag and drop or browse) |
| V5 | Frame + annotated detections | ✅ | Vision |
| V6 | 5 KPIs | ✅ | Vision |
| V7 | Ground-truth vs detected caption | ✅ | Vision (synthetic) |
| V8 | "How it works" | ✅ | Vision |
| V9 | `ultralytics` missing error | ✅ | error state with the install command (API returns 503 + hint) |
| P1 | 4 model KPIs | ✅ | Prediction |
| P2 | Predicted-vs-actual scatter | ✅ | Prediction |
| P3 | Feature importance | ✅ | Prediction |
| P4 | Model-comparison table | ✅ | Prediction |
| P5 | Live forecast bars | ✅ | Prediction |
| P6 | Highest build-up callout | ✅ | Prediction |
| P7 | Simulate 3 minutes now | ✅ | Prediction empty state |
| Vi1 | Simulate 10 more minutes | ✅ | Violations |
| Vi2 | 4 KPIs | ✅ | Violations |
| Vi3 | By-junction stacked bars | ✅ | Violations |
| Vi4 | Per-minute bars | ✅ | Violations |
| Vi5 | Evidence log (newest first, sortable, paged) | ✅ | Violations |
| Vi6 | Empty state | ✅ | Violations |
| Vi7 | Violations by controller (last benchmark) | ✅ | Violations |
| Vi8 | Explanatory caption | ✅ | Violations |
| A1 | Base paper + DOI link | ✅ | About |
| A2 | Adopted-vs-advanced table | ✅ | About |
| A3 | System pipeline diagram | ✅ | About (SVG) |
| A4 | Controller list | ✅ | About (from `/api/meta`) |
| A5 | How to run + model note | ✅ | About |
