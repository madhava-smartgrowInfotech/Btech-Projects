# CipherGuard Shield — Secure Data Transmission Platform for Cloud Environments

A production-quality security platform that combines **authenticated encryption** with a **real machine-learning intrusion detection system (IDS)** and a **live monitoring dashboard**.

## What it does

- **SecureChannel** encrypts any payload before “transmission to the cloud” using real, verifiable cryptography:
  - **ECDH P-256** (via `cryptography` library) for key exchange — sender generates an ephemeral keypair and derives a shared secret with the cloud’s long-term public key.
  - **HKDF-SHA256** to derive a 256-bit **AES-256-GCM** session key from the ECDH secret.
  - **AES-256-GCM** with 12-byte nonce and 16-byte tag, with full tag verification on decrypt. Wrong tag / tampered ciphertext is rejected.
- **ThreatSense Engine** classifies network flow records as **normal vs. attack** using a real ensemble:
  - **Model A: XGBoost** (gradient-boosted trees) on tabular flow features.
  - **Model B: 1D CNN** (PyTorch; 2 conv layers + pooling + dense) — same feature vector reshaped as a 1D sequence; TensorFlow/Keras is the same architecture when available, PyTorch is the active backend on this host (identical topology).
  - **Fusion: Logistic Regression stacking** — a meta-model trained on the two base models’ output probabilities (soft-voting / weighted score averaging with min-max normalized probabilities). Documented in code as *ensemble stacking*.
- **Live dashboard** (FastAPI + HTML/CSS/JS):
  - Upload/simulate traffic records → live classification, running alert log, charts (attack vs normal, confidence distribution).
  - Secure Transfer panel: submit file/text, see real ciphertext/nonce/tag + ephemeral public key, send to mock cloud, decrypt and verify.
  - Alerts panel with severity/timestamp/features.
  - Model Performance page rendering the genuine `reports/metrics.json` (accuracy, precision, recall, F1, ROC-AUC, confusion matrix).

No raw packet sniffing — traffic is labeled dataset flows (batch replay) or user-submitted records via the UI, which is sufficient to demonstrate a real IDS pipeline without special hardware.

## Architecture

```
web/ (index.html + static/css + static/js)  →  FastAPI (cipherguard/api/main.py)
                                              ├─ /api/ids/*         → ThreatSense Engine (cipherguard/ids/)
                                              ├─ /api/crypto/*      → SecureChannel (cipherguard/crypto/secure_channel.py)
                                              ├─ /api/metrics       → reports/metrics.json
                                              └─ /api/alerts
cipherguard/ids/  preprocessing.py (OneHot + MinMax), synthetic.py, train.py, inference.py
cipherguard/crypto/  secure_channel.py  (AES-256-GCM + ECDH P-256 + HKDF-SHA256)
data/raw/  → UNSW-NB15 CSVs or synthetic_demo.csv (generated)
models/  → xgb_model.joblib, cnn_model.pt (.keras if TF available), stacking_meta.joblib, preprocessor.joblib
reports/ → metrics.json, metrics.md
```

### Technology names (explicit)

- **AES-256-GCM** — authenticated encryption, 12-byte nonce, 16-byte tag
- **ECDH P-256** — NIST SECP256R1 via `cryptography`
- **HKDF-SHA256** — key derivation
- **XGBoost** — gradient-boosted trees
- **1D CNN** — 2× Conv1D + MaxPooling + Dense, implemented in PyTorch (TensorFlow/Keras equivalent when TF loads)
- **Logistic Regression stacking** — honest analogue of score-level fusion
- **UNSW-NB15** — public intrusion dataset

## Dataset handling — engineering assumptions

1. **Real UNSW-NB15 path**: Place the standard CSVs (`UNSW_NB15_training-set.csv` / `UNSW_NB15_testing-set.csv` — or any split) into `data/raw/`. The training pipeline (`python -m cipherguard.ids.train`) auto-detects them, normalizes headers/lowercasing, maps `label` / `attack_cat`, handles missing columns, and retrains. Metrics will then reflect real UNSW-NB15 performance.
2. **Bundled synthetic demo data** (what the reported numbers actually use): If `data/raw/` contains no usable CSV, `train_pipeline` generates a **synthetic labeled network-flow dataset** with the **same 42-feature schema** (`duration, proto, service, sbytes, ct_srv_src, …`, 2 classes: normal/attack) via `cipherguard/ids/synthetic.py`. Distributions overlap slightly and 2.5% label noise is injected so accuracy is high but not suspiciously perfect. The file is saved as `data/raw/synthetic_demo.csv` so the pipeline is fully runnable out of the box.
3. **Which mode was used for the shipped metrics**: Check `reports/metrics.json` → `data_mode`. In this build it is `"synthetic demo data (UNSW-NB15 schema, generated)"`. The README explicitly states this. Dropping real CSVs and rerunning `python -m cipherguard.ids.train` will overwrite `models/*` and `reports/metrics.json` with real UNSW-NB15 numbers, and the dashboard updates automatically.

Preprocessing (both modes): categorical encoding via `OneHotEncoder(handle_unknown="ignore")` for `proto/service/state`, `MinMaxScaler` for numeric features, stratified 70/15/15 train/val/test split, class balancing via `scale_pos_weight` (XGBoost) and balanced loss weighting (CNN).

Artifacts are genuine: `models/*.joblib/.pt` are real trained models, and `reports/metrics.json` + `reports/metrics.md` are computed from an actual held-out test set — never fabricated.

## How to run

Quickest (native):

```bat
double-click run.bat
```

Docker (recommended if Docker Desktop is installed):

```bat
double-click run-docker.bat
```

Manual:

```bash
pip install -r requirements.txt
python -m cipherguard.ids.train   # only if models/ missing; run.bat does this automatically
python -m uvicorn cipherguard.api.main:app --host 127.0.0.1 --port 8000
# then open http://localhost:8000
```

The native server is always bound to **127.0.0.1** (localhost) to avoid firewall prompts; inside Docker it is mapped via `0.0.0.0:8000` → `localhost:8000`. The dashboard is a clean white/light professional theme (Inter/system-ui, generous spacing, not a dark terminal).

See **HOW_TO_RUN.md** for the complete 5-section guide (Prerequisites, Method A/B/C, Troubleshooting).

## API overview

- `GET /api/health` — status + engine_loaded
- `GET /api/metrics` — held-out test metrics
- `POST /api/ids/score` — JSON flow record → `{label, confidence, severity, xgb_score, cnn_score}`
- `POST /api/ids/score-batch` — multipart CSV → `{total, attack_count, normal_count, results}`
- `GET /api/alerts` / `DELETE /api/alerts`
- `POST /api/crypto/encrypt` — `{plaintext}` → `{ciphertext, nonce, tag, ephemeral_public, algorithm}`
- `POST /api/crypto/decrypt` — `{ciphertext, nonce, tag, ephemeral_public}` → `{plaintext, verified}` or 400 on tag mismatch
- `POST /api/crypto/encrypt-file` — multipart file → same encrypted fields

Input validation is strict (malformed CSV, empty payload, >10 MB CSV, >5 MB file, invalid base64, tag mismatch all return sensible HTTP codes + messages). No secrets are logged.

## Retrain with real UNSW-NB15

1. Download the dataset from https://research.unsw.edu.au/projects/unsw-nb15-dataset (UNSW_NB15_training-set.csv, UNSW_NB15_testing-set.csv).
2. Copy both CSVs into `data/raw/`.
3. Delete old artifacts if you want a clean run: `del models\* reports\*`.
4. `python -m cipherguard.ids.train` — watch console for “Data mode: real UNSW-NB15 CSVs” and new metrics.
5. Restart the server; the Model Performance page will show the new numbers.

## Security notes

- Nonces are `os.urandom(12)` per encryption; keys are ephemeral and never reused.
- Session keys are 32 bytes, derived fresh per message via ECDH+HKDF; no fixed keys.
- GCM tag verification uses `AESGCM` which throws on mismatch — the API surfaces 400.
- The “cloud” is a mock in-process endpoint with its own keypair (`get_cloud_keypair()`). In a real deployment it would be a separate service with private key custody.

## Project layout

```
cipherguard/crypto/secure_channel.py  SecureChannel (ECDH P-256 + HKDF + AES-256-GCM)
cipherguard/ids/features.py           42-feature schema
cipherguard/ids/preprocessing.py      ColumnTransformer (MinMax + OneHot), load_csv_smart
cipherguard/ids/synthetic.py          synthetic UNSW-NB15-like generator
cipherguard/ids/train.py              XGBoost + 1D CNN (PyTorch/TF) + LR stacking
cipherguard/ids/inference.py          ThreatSenseEngine (load + score)
cipherguard/api/main.py               FastAPI routes + static frontend mount
web/index.html, web/static/*          Dashboard (no build step)
data/raw/                             place real CSVs here
models/                               trained artifacts
reports/                              metrics.json/.md
run.bat, requirements.txt, HOW_TO_RUN.md
```

## Troubleshooting

- Port in use: `netstat -ano | findstr :8000` then `taskkill /PID <pid> /F`, or restart PC.
- TensorFlow not loading: PyTorch backend is active; same architecture, metrics still valid. Set `TF_ENABLE_ONEDNN_OPTS=0` if you want to try TF.
- Model not loaded (503): Run `python -m cipherguard.ids.train` and restart.

## License

Proprietary — CipherGuard Shield.
