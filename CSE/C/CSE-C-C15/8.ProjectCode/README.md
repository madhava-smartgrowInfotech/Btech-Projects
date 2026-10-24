# SentinelFlow — Real-Time DDoS Detection & Adaptive Mitigation

SentinelFlow is a standalone defensive network-security product. It monitors a selected
network interface (or a safe local simulator), aggregates traffic into rolling windows,
classifies each window with a trained **Random Forest** model, scores distributed-traffic
risk, assigns an explainable severity, and applies adaptive mitigation with automatic recovery.

## Core features

- Real-time DDoS detection with scikit-learn Random Forest
- 10-second rolling monitoring windows (configurable)
- Distributed / carpet-bombing-aware traffic risk scoring
- Explainable severity: Low / Medium / High / Critical with contributing factors
- Adaptive mitigation: application-level quarantine with ~40 s auto-recovery
- Network health monitoring via psutil (CPU, memory, throughput)
- Simulation Mode for permission-free, hardware-free demonstrations
- SQLite storage for detections, mitigations, health samples, and settings
- React console (Vite + design kit V5 "Kinetic Mono") in `frontend/`, plus the original Flask + vanilla JS + Chart.js dashboard

## Architecture

```text
Scapy sniff / Simulator
        -> traffic_aggregator (10 common features + context)
        -> Random Forest prediction (ml/model_loader)
        -> distributed risk (security/distributed_analysis)
        -> severity (security/severity)
        -> mitigation (security/mitigation) + SQLite + Flask dashboard
```

## Technology stack

Python 3.11/3.12, Flask, scikit-learn, pandas, numpy, joblib, Scapy, psutil,
matplotlib, SQLite, HTML5/CSS/vanilla JS, Chart.js (CDN with numeric fallback), Docker.

## ML pipeline

1. `ml/train_model.py` locates CICIDS2017 CSVs in `data/raw/` (or attempts documented
   public mirrors). If unreachable, it builds a schema-compatible synthetic fallback and
   labels the provenance as synthetic.
2. Columns are normalized, infinite/missing rows removed, labels mapped to Benign/Attack.
3. Raw flow fields map forward → sent, backward → received, rates from flow duration
   (documented in `ml/preprocessing.py` and `ml/features.py`).
4. A documented window-scale augmentation (6000 aggregated windows through the real
   monitoring pipeline) keeps the model calibrated across flow scale and window scale.
5. Stratified 80/20 split, RandomForestClassifier (200 trees, balanced weights, seed 42).
6. Artifacts in `models/` and `results/`: model, feature list, metadata, metrics JSON,
   classification report, confusion matrix, ROC curve, feature importance.

## Feature schema

`received_packets`, `received_bytes`, `received_packets_per_second`,
`received_bytes_per_second`, `average_received_packet_size`, `sent_packets`,
`sent_bytes`, `sent_packets_per_second`, `sent_bytes_per_second`,
`average_sent_packet_size` — plus runtime context (unique sources/destinations,
protocol distribution, baseline deviation). Training and inference share
`ml/features.py`, and every prediction validates names and ordering.

## Live monitoring

Scapy `sniff()` on the chosen interface, rolling windows (default 10 s), directional
aggregation using local interface addresses, real model inference, severity scoring,
SQLite event storage, and dashboard refresh. Capture failures show the actual reason
and offer Simulation Mode.

## Threat severity

Combines model confidence, packet-rate pressure, distributed-risk score,
source/destination spread, and cross-window persistence. The dashboard lists every
contributing factor next to the verdict — no black-box claims.

## Adaptive mitigation

High/Critical windows quarantine top suspicious sources inside SentinelFlow
(~40 s default, doubled for Critical) with automatic expiry and a full event history.
Medium recommends rate limiting; Low keeps monitoring. The OS firewall is never
touched automatically.

## Demo mode

Simulation Mode generates benign plus flood / carpet-bombing / slow-style windows
locally (no packets emitted), runs them through the identical inference pipeline, and
is always labelled **Simulation Mode** in the UI — never presented as live traffic.

## Evaluation process

`python ml/train_model.py` prints accuracy, precision, recall, F1, ROC-AUC, and the
classification report. `python ml/evaluate_model.py` reloads the persisted model and
re-scores the held-out test features. All dashboard numbers come from `results/`;
an untrained install shows a clear "Model not trained" state.

## Project structure

```text
SentinelFlow/
├── app.py                 # Flask app, REST API, pipeline orchestration
├── config/config.py       # host/port, windows, quarantine, paths
├── ml/                    # features, preprocessing, training, evaluation, loader
├── monitoring/            # interfaces, Scapy capture engine, aggregator, simulator
├── security/              # detector, distributed analysis, severity, mitigation
├── database/db.py         # SQLite storage
├── templates/ static/     # dashboard UI
├── data/ models/ results/ # dataset, artifacts, metrics, plots
├── screenshots/ docs/     # real captures, product report + generator
├── run.bat run-docker.bat Dockerfile docker-compose.yml
├── requirements.txt README.md HOW_TO_RUN.md
```

## Quick start

Double-click `run.bat`: it starts the API (port 8415) and the React console (port 5415) and opens
`http://127.0.0.1:5415`. Sign in with the demo account `demo@sentinelflow.com` / `Demo@1234`.
See `docs/03_HOW_TO_RUN.md`. The original server-rendered dashboard is still served at `http://127.0.0.1:8415/`.
Full instructions (automatic, Docker, manual, troubleshooting) are in `HOW_TO_RUN.md`.

## Limitations

- Live capture needs elevated privileges and Npcap on Windows; otherwise use Simulation Mode.
- Docker supports the dashboard, inference, database, and Simulation Mode; host packet
  capture inside a container is platform-limited and not promised.
- If CICIDS2017 downloads are unreachable, the build uses labelled synthetic fallback
  data plus window-scale augmentation; re-train on local labelled captures before any
  production use.

## Security / privacy considerations

Defensive monitoring only: no attack generation, no external scanning, no credential
handling, no automatic firewall changes, no persistence mechanisms. All servers bind to
`127.0.0.1`; the dashboard is localhost-only. Detections and quarantines stay on the
local machine in SQLite.

## Engineering assumptions

- CICIDS2017 forward direction maps to sent, backward to received.
- Local-interface addresses define inbound vs outbound orientation for live windows.
- Temporary quarantine default is 40 s (doubled for Critical severity).
- Default monitoring window is 10 s (Simulation Mode uses shorter windows for lively demos).
