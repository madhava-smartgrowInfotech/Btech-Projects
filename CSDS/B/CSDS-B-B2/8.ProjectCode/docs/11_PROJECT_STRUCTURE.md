# Project structure

```
8.ProjectCode/
├── setup.bat               one-time install: Python venv, packages, .env, datasets, cloudflared, web build, models
├── run.bat                 starts everything (API, dashboard, HTTPS tunnel, ESP32 simulator)
├── .env.example            every setting with comments (copied to .env, which is git-ignored)
├── pytest.ini              test settings (tests in backend/tests)
├── backend/                FastAPI application
├── frontend/               React + Vite web app: dashboard and phone probe
├── ml/                     data preparation and training scripts
├── notebooks/              exploration, results and a Kaggle-ready notebook
├── experiments/            one folder per training run: model, metrics.json, plots, train.log
├── models/                 the model files the app loads (copied from the chosen runs)
├── data/                   datasets, sample field data, the SQLite database (created at runtime)
├── firmware/esp32_node/    Arduino firmware for the ESP32 sensor node
├── scripts/                launcher, simulator, downloads, checks and exports
└── docs/                   this documentation
```

Created at runtime and git-ignored: `venv/`, `frontend/node_modules/`, `frontend/dist/`, `.env`, `data/app.db*`, `data/runtime/` (tunnel address, simulator keys), `logs/` and `tools/` (cloudflared).

---

## backend/

```
backend/
├── requirements.txt
├── app/
│   ├── main.py             app factory: startup (database, seed, models, carrier table, simulator, sample data,
│   │                       background tasks), request logging, routers, serves frontend/dist for the tunnel
│   ├── seed.py             demo accounts
│   ├── core/
│   │   ├── config.py       Settings read from .env (one frozen dataclass)
│   │   ├── db.py           SQLAlchemy engine (SQLite, WAL mode), sessions, utcnow()
│   │   ├── security.py     password hashing, JWT, role checks, device keys (stored as SHA-256)
│   │   └── logging.py      structured key=value logs to the console and logs/
│   ├── models/             SQLAlchemy tables
│   │   ├── user.py         User (roles user / engineer / admin)
│   │   ├── device.py       Device (phone / esp32 / simulator / replay), key hash, fixed position
│   │   ├── reading.py      Reading: position, zone cell, operator, link, radio and service metrics, class
│   │   ├── zone.py         ZoneState: live state of one hexagon for one operator
│   │   ├── complaint.py    Complaint and ComplaintEvent (timeline)
│   │   └── misc.py         Notification (retry queue), SyncBatch, Setting, CellTower
│   ├── schemas/            Pydantic request and response models (UTC times on the wire)
│   ├── api/                HTTP routes, one file per area
│   │   ├── auth.py         register, login, profile
│   │   ├── system.py       health, public stats, phone connection info
│   │   ├── admin.py        users, settings and presets, notifications, sample data
│   │   ├── devices.py      phones and nodes, keys, sync history
│   │   ├── ingest.py       reading uploads (phones and ESP32 nodes)
│   │   ├── readings.py     reading list and CSV export
│   │   ├── coverage.py     map data (hexagons, heat, points, nodes) and the live event stream
│   │   ├── probe.py        ping, speed test and carrier endpoints for the phone probe
│   │   ├── suggest.py      better-signal suggestion, offline spot pack, predicted coverage
│   │   ├── complaints.py   complaint queue, lifecycle, notes, evidence exports, nearby towers
│   │   ├── analytics.py    dashboard and analytics figures
│   │   └── ml.py           model metrics, plots and field validation
│   ├── services/           the business logic behind the routes
│   │   ├── ingest.py       validates, labels and stores readings; idempotent by client UUID
│   │   ├── carrier.py      IP → network (ASN) → operator and link type (iptoasn table)
│   │   ├── zone_engine.py  judges zones, detects/registers/dismisses complaints, verifies fixes
│   │   ├── complaint_service.py  lifecycle rules and timeline events
│   │   ├── evidence.py     evidence bundle and summary text for a complaint
│   │   ├── notifier.py     Telegram and email, with a retry queue
│   │   ├── llm.py          optional plain-language summary (Gemini)
│   │   ├── suggest_service.py  gathers readings for the better-signal predictor
│   │   ├── opencellid.py   optional nearby-tower lookup with a weekly cache
│   │   ├── settings_service.py  admin-editable settings and presets
│   │   ├── sample_data.py  replays public-dataset traces as sample data
│   │   ├── simulator_setup.py  creates the simulated ESP32 nodes and their keys
│   │   ├── events.py       in-process event bus for the live stream
│   │   └── background.py   periodic zone sweep and notification sending
│   └── ml/                 inference code shared with training
│       ├── signal_ranges.py  3GPP-style ranges and labels
│       ├── features.py     feature building (30-second windows, availability flags, bands)
│       ├── mlp.py          PyTorch MLP with a scikit-learn style interface
│       ├── calibration.py  temperature scaling and calibration error
│       ├── service_quality.py  probe service-quality bands
│       ├── service.py      ModelService: classify radio, probe and Wi-Fi readings
│       ├── gp.py           two-scale Gaussian Process
│       ├── suggest.py      nearest strong spot and predicted grid
│       └── registry.py     loads models/ at startup
└── tests/                  pytest suite (see 09_TESTING.md)
```

## frontend/

```
frontend/
├── package.json, vite.config.ts   Vite (port 5202, strict), PWA plugin, API proxy to 8202
├── tailwind.config.ts             design tokens (colours, fonts, radii)
├── index.html, public/            favicon, app icons
└── src/
    ├── main.tsx            providers: query cache persisted to IndexedDB, theme, motion, router, auth
    ├── App.tsx             routes (pages are loaded on demand)
    ├── sw.ts               service worker: offline app shell, background sync for the probe queue
    ├── index.css           colour tokens for light and dark themes, map styles
    ├── lib/
    │   ├── api.ts, auth.tsx, theme.tsx, utils.ts
    │   ├── zones.ts, coverage.ts, complaints.ts, analytics.ts, devices.ts   data hooks and labels
    │   └── probe/          the phone probe engine
    │       ├── measure.ts  round trips, adaptive download and upload tests
    │       ├── classify.ts provisional Strong / Weak / Dead on the phone
    │       ├── store.ts    IndexedDB queue, settings, strong-spot pack
    │       ├── sync-core.ts  batch upload of queued readings (shared with the service worker)
    │       ├── spots.ts    nearest strong spot, distances, bearings
    │       └── useProbe.ts measurement loop, GPS, wake lock, sync
    ├── components/
    │   ├── ui/             buttons, dialogs, selects, tabs and other accessible primitives (Radix based)
    │   ├── layout/         sidebar layout, navigation, theme toggle, user menu
    │   ├── common/         route guards, loading / empty / error states, zone badges
    │   ├── map/            Leaflet layers (hexagons, heat, points, nodes, complaints, prediction), filters
    │   ├── complaints/     list, status badges and stepper, report dialog, evidence chart
    │   ├── charts/         stat tiles, class-share chart, complaint chart, time-of-day heatmap
    │   ├── landing/        animated coverage preview for the landing page
    │   └── reactbits/      RotatingText, CountUp, SpotlightCard, Radar (from React Bits, with licence)
    └── pages/
        ├── Landing.tsx, auth/ (Login, Register)
        ├── Dashboard.tsx, CoverageMap.tsx, MyComplaints.tsx, ComplaintDetail.tsx
        ├── Analytics.tsx, ModelPerformance.tsx
        ├── Connect.tsx, Devices.tsx, Profile.tsx
        ├── desk/OperatorDesk.tsx
        ├── admin/ (Settings, Users)
        └── probe/          the phone app: ProbeApp, Pair, LiveTab, SignalTab, OtherTabs (readings, sync, settings)
```

## ml/, notebooks/, experiments/, models/

| Path | Contents |
|---|---|
| `ml/prepare_data.py` | Cleans `data/raw/` into `data/processed/` and writes `prep_report.json` |
| `ml/train_classifier.py` | Zone classifier: 3 candidates, 2 baselines, cross-validation, calibration, plots |
| `ml/train_throughput_model.py` | Radio-condition estimate from speed tests |
| `ml/train_gp.py` | Better-signal predictor with spatial block cross-validation |
| `ml/train_all.py` | Runs the four steps in order |
| `ml/_common.py`, `ml/_plots.py` | Paths, seeding, run folders, the shared plot style |
| `notebooks/` | `01_data_exploration`, `02_model_results`, `03_kaggle_zone_classifier` |
| `experiments/<run>/` | `model.joblib`, `metrics.json`, `train.log`, PNG plots |
| `models/` | `zone_classifier`, `radio_estimate` and `gp_signal`, each as a `.joblib` file plus a short `.json` summary |

## data/

| Path | Contents |
|---|---|
| `data/raw/` | Both public datasets, complete, with `MANIFEST.json` (hashes, licences) |
| `data/processed/` | Cleaned datasets and the preparation report |
| `data/asn/` | iptoasn IP-to-network table, used to tell the operator from a phone's address |
| `data/field/` | Anonymised sample of your own readings (created by `scripts/export_field_sample.py`) |
| `data/app.db` | The SQLite database (runtime, not committed) |

## scripts/

| Script | Purpose |
|---|---|
| `launcher.py` | Used by `run.bat`: starts and supervises the API, dashboard, tunnel and simulator; `--stop` ends a running launcher |
| `sync_env.py` | Creates or updates `.env` from `.env.example` and generates the JWT secret |
| `download_data.py` | Verifies or downloads the datasets |
| `get_tools.py` | Downloads `cloudflared.exe` into `tools/` |
| `check_env.py` | Checks every setting and connection; can send test notifications |
| `esp32_simulator.py` | Simulated ESP32 nodes (seeded, same format as the firmware) |
| `export_field_sample.py` | Anonymised export of your own readings to `data/field/` |

## firmware/esp32_node/

| File | Purpose |
|---|---|
| `esp32_node.ino` | Measures Wi-Fi and BLE signal, latency, loss, GPS and an optional modem; buffers readings in LittleFS; uploads in batches |
| `config.example.h` | Settings template. Copy it to `config.h`, which is git-ignored. |
| `README.md` | Parts, wiring, libraries, flashing and troubleshooting |
