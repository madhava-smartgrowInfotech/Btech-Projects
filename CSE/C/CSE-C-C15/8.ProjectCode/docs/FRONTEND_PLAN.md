# SentinelFlow - Frontend Plan (Kit V5 "Kinetic Mono")

Backend: Flask (`app.py`), port **8415** (set in `.env`). New React/Vite frontend in `frontend/`, port **5415**,
proxying `/api` and `/static/results` to the backend. The original Flask template dashboard (`templates/`,
`static/`) is left untouched and still served at `http://127.0.0.1:8415/`.

> The prompt says the code lives in `SentinelFlow/`; that folder is empty. The project sits at the `8.ProjectCode`
> root, so `frontend/` goes beside `app.py`.

## 1. Backend endpoint inventory

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | - | Legacy HTML dashboard (kept) |
| GET | `/api/status` | - | `{product, monitoring, mode: stopped\|live\|simulation, interface, window_seconds, windows_completed, model_trained, latest: Detection\|null, active_mitigations, capture_error}` |
| GET | `/api/health` | - | `{current: Sample\|null, recent: Sample[<=30], history: Sample[<=30]}`; Sample = `{timestamp, cpu_percent, memory_percent, bytes_sent, bytes_recv, packets_sent, packets_recv}` |
| GET | `/api/interfaces` | - | `{interfaces: [{name, display, ips[], up}]}` |
| GET | `/api/detections?limit=1..500` | query `limit` | `{detections: Detection[], by_prediction:{Benign,Attack}, by_severity:{Low,Medium,High,Critical}}` (400 on bad limit) |
| GET | `/api/detections/latest` | - | `{detection: Detection}` or `{detection:null, message}` |
| GET | `/api/mitigations` | - | `{active:[{ip,reason,quarantined_at,expires_at,remaining_seconds,duration,status}], history:[{id,timestamp,ip,reason,duration,status}], quarantine_seconds}` |
| GET | `/api/settings` | - | `{window_seconds, quarantine_seconds, interface}` |
| POST | `/api/settings` | `{window_seconds 2-120, quarantine_seconds 5-3600, interface?}` | `{ok, window_seconds, quarantine_seconds}` or 400 `{error}` |
| POST | `/api/monitor/start` | `{interface, window_seconds}` | `{ok, mode:"live", interface, window_seconds}`; 409 if a session runs; 500 with reason if capture fails |
| POST | `/api/monitor/stop` | - | `{ok}` |
| POST | `/api/demo/start` | `{window_seconds}` | `{ok, mode:"simulation", window_seconds}`; 409 if a session runs |
| POST | `/api/demo/stop` | - | `{ok}` |
| GET | `/api/model/metrics` | - | `{trained, metrics:{accuracy,precision,recall,f1,roc_auc,test_samples,train_samples,benign_total,attack_total,dataset_provenance,is_synthetic,model,training_seconds,...}, feature_importance:{name:value}, confusion_matrix:{labels,matrix}}` |
| GET | `/static/results/<file>` | - | `confusion_matrix.png`, `roc_curve.png`, `feature_importance.png` |

`Detection` = `{id, timestamp, interface, source, prediction: Benign\|Attack, confidence, severity, packet_rate, byte_rate, source_count, destination_count, distributed_risk, mitigation_status, detail:{features, context:{top_sources, top_destinations, protocol_distribution, ...}, distributed:{distributed_risk_score, distributed_risk_level, components, explanation, ...}, severity:{severity, severity_score, factors[], recommendation}, actions[]}}`.

No authentication exists (localhost-only product), so the frontend has no login.

## 2. Feature inventory (existing product)

1. Start live capture on a chosen interface, start Simulation Mode, stop either (header controls)
2. Status pill: Stopped / Live Capture / Simulation Mode, with mode note and capture error
3. Six summary cards: threat status, severity (+distributed risk), ML confidence, packets/sec (+bytes/sec), sources/destinations, active mitigations (+mode)
4. Network Health: CPU %, memory %, bytes in/out numbers + CPU/memory and bytes in/out time-series
5. Detection Analytics: Benign-vs-Attack split, severity distribution (with numeric fallback)
6. Live Detection Table (time, interface, source, prediction, confidence, severity, srcs, dsts, pkt/s, mitigation), auto-refresh every 3 s
7. Threat Detail for a selected detection: prediction/confidence/severity score, measured traffic, distributed-traffic explanation, severity factors, recommended mitigation, mitigation status, model features
8. Mitigation Center: active quarantines with seconds remaining (auto-recover), mitigation history
9. Model Performance: accuracy/precision/recall/F1/ROC-AUC/test samples, dataset provenance + synthetic warning, confusion matrix / ROC / feature-importance images, "model not trained" state
10. Settings: monitoring window, quarantine duration, save with validation messages
11. Simulation Mode always labelled as simulated, never as live traffic
12. Interface list with up/down state and addresses

## 3. Screen map (React, routes)

| Route | Screen | Covers features |
|---|---|---|
| `/` | Landing - Kinetic Mono hero, three.js grid, live counters from the API, terminal typewriter, feature grid, CTA | brand, 2, 11 |
| `/app` | **Overview** - session control bar (interface select, Start Live, Start Simulation, Stop, status pill), 6 stat cards, packet-rate sparkline, terminal log of latest detections | 1, 2, 3, 11, 12 |
| `/app/detections` | **Detections** - filterable/sortable table (cards on mobile), click row -> Threat Detail drawer | 6, 7 |
| `/app/analytics` | **Analytics** - prediction donut, severity bars, packet-rate / confidence timeline, protocol mix of latest window | 5 |
| `/app/health` | **Network Health** - CPU/memory/bytes in/out/packets tiles and charts | 4 |
| `/app/mitigation` | **Mitigation** - live quarantine countdowns, history table, quarantine duration shown | 8 |
| `/app/model` | **Model** - metrics, provenance, confusion matrix, feature importance chart, ROC image | 9 |
| `/app/settings` | **Settings** - window/quarantine form, interface choice, theme | 10 |
| Global | Command palette (Ctrl/Cmd+K), toasts, dark-mode toggle, mobile drawer nav, 404 | - |

## 4. Changes outside `frontend/`

- `config/config.py`: `HOST`/`PORT` now read `BACKEND_HOST`/`BACKEND_PORT` from `.env` (default unchanged, 5000). No logic change.
- New `.env` (8415 / 5415), `run.bat` updated to start backend + frontend, `scripts/smoke_test.py`, `scripts/capture_screens.py`, `docs/03_HOW_TO_RUN.md`.
- No new API endpoints are planned; if one proves necessary it will be additive and read-only and called out here.

## 5. Verification checklist (ticked in Step 4)

- [x] 1 Start live / simulation / stop
- [x] 2 Status pill + mode note
- [x] 3 Six summary cards
- [x] 4 Network health numbers + charts
- [x] 5 Detection analytics charts
- [x] 6 Detection table
- [x] 7 Threat detail
- [x] 8 Mitigation center
- [x] 9 Model performance
- [x] 10 Settings save
- [x] 11 Simulation labelling
- [x] 12 Interface list

Verified on 2026-10-25 (Chromium via Playwright, backend 8415 + UI 5415):

- `npm run build` passes; `scripts/smoke_test.py` passes 27/27 (API contracts, validation 400/409, simulation scoring, proxy).
- Every screen walked with a running simulation; `scripts/capture_screens.py` finished with a clean console (no errors, no 404s)
  and wrote 12 screenshots to `docs/screenshots/`.
- Layout checked at 360, 768 and 1440 px in light and dark: no horizontal page overflow on any screen.
- Keyboard: focus rings, `g <key>` navigation, `/` palette, Escape closes drawer / palette / detail. Reduced motion: no WebGL canvas,
  content shown at once. Backend-down state shows what failed and how to fix it. Live capture failure (no Npcap) is reported in a toast and an error panel.
- Added beyond the original product: demo sign-in gate (`demo@sentinelflow.com` / `Demo@1234`), command palette, activity log, keyboard shortcuts.
