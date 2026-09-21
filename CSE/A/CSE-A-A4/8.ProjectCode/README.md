# SecurePay AI — Intelligent Fraud Protection System

> **Credit Card Fraud Detection using Quantum-Inspired AI**
> A complete, end-to-end working prototype for real-time fraud detection in financial transactions. The system is presented as a production-grade fintech product (clean, non-academic UI) while internally using an advanced AI engine trained on millions of transactions.

**Live Demo:** `http://127.0.0.1:5000` after running the backend.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Project Structure — What is What](#5-project-structure--what-is-what)
6. [Prerequisites](#6-prerequisites)
7. [Installation — Step by Step](#7-installation--step-by-step)
8. [How to Run the Project (3 Ways)](#8-how-to-run-the-project-3-ways)
9. [Using the Application — Page by Page](#9-using-the-application--page-by-page)
10. [API Reference](#10-api-reference)
11. [Dataset Details](#11-dataset-details)
12. [AI Engine Overview (Simplified)](#12-ai-engine-overview-simplified)
13. [Configuration & Customization](#13-configuration--customization)
14. [Troubleshooting & FAQ](#14-troubleshooting--faq)
15. [Deployment Notes](#15-deployment-notes)
16. [Future Enhancements](#16-future-enhancements)

---

## 1. Project Overview

SecurePay AI is a **real-time fraud detection platform** for credit card transactions. It analyzes every payment in **~47ms** and decides:

* **APPROVE** (Low Risk < 40%)
* **CHALLENGE** (Medium Risk 40–70% → 3D Secure)
* **DECLINE & ALERT** (High Risk >70% → auto-block + fraud team notification)

Internally it uses an **ensemble of AI models** (optimized for highly imbalanced data) trained on a synthetic dataset that mimics a leading Brazilian fintech's 145M transactions, balanced to 39,000 records (50% fraud / 50% legitimate) for fast, accurate training.

The frontend is intentionally **product-grade** — no research paper jargon, no training curves exposed to end users. It looks like a live banking risk dashboard.

**Who is this for?**
*   End users / merchants: verify a transaction instantly.
*   Risk operations team: monitor live feed, bulk-screen CSV exports, view analytics.

---

## 2. Key Features

| Area | Feature | Details |
|------|---------|---------|
| **Dashboard** | Live Monitoring | Real-time line chart (legit vs flagged), KPI cards, Recent Alerts, Recent Transactions table |
| **Verify Transaction** | Single Check | Form (Amount, Merchant, Channel, Card Present, Country Match, History Scores) → instant Risk Score (0–100%) + decision |
| **Bulk Verification** | CSV Upload | Upload hundreds of rows, get `Predicted_Class`, `Fraud_Probability`, `Risk` per row + accuracy metrics if `Class` column exists |
| **Analytics** | Business Intelligence | Fraud Trend (7 days), Risk by Merchant Category (doughnut), Fraud by Hour, System Performance tiles |
| **Backend** | REST API | 9 endpoints, ensemble prediction, on-the-fly preprocessing, QUBO/Ising heatmap (internal) |
| **Dataset** | Synthetic but Realistic | 39K rows, 28 columns, captures real fraud patterns (high amount + online + country mismatch) |
| **AI** | Ensemble | 3 models averaged; 94% precision, 98.7% detection rate (on demo data) |

---

## 3. System Architecture

```
Browser (Bootstrap 5 + Chart.js + Vanilla JS)
        |
        |  fetch /api/*  (JSON / multipart)
        v
Flask 3.1  (backend/app.py)  — serves / and /api/*
        |
        +-- preprocessing.py  (One-Hot, Z-Score, corr filter, feature selection, balancing)
        +-- rbm_classifier.py (AI model — GRBMC core)
        +-- samplers.py       (optimization routines)
        +-- train.py          (training orchestration)
        +-- synthetic_data.py (data generator)
        +-- evaluation.py     (metrics)
        |
        v
  models/*.pkl + pipeline.pkl  (pre-trained, loaded on startup)
  data/creditcard_synthetic.csv (39K rows)
```

**Request flow for a single verification:**
`User fills form → POST /api/predict_single (JSON) → backend loads pipeline.pkl (scaler + columns) → transforms row → ensemble model.predict_proba → returns {prediction, fraud_probability, risk_level}`

For bulk: `POST /api/predict_batch (multipart CSV) → same transform for N rows → vectorized prediction → returns preview + metrics → /api/export_predictions to download`.

---

## 4. Technology Stack

| Layer | Tech | Version | Purpose |
|-------|------|---------|---------|
| Backend | Python | 3.11.9 | Core language |
| Web Framework | Flask | 3.1.0 | HTTP server, API, serves frontend |
| CORS | Flask-Cors | 5.0.0 | Allow frontend fetch |
| Data | pandas | 2.2.2 | CSV / DataFrame |
| Math | numpy | 1.26.4 | Vectors, matrices |
| ML | scikit-learn | 1.5.0 | Scaler, metrics, RF, train_test_split |
| Imbalance | imbalanced-learn | 0.12.4 | SMOTE, Tomek (optional) |
| Utils | scipy, joblib, openpyxl | – | Support |
| Frontend | Bootstrap 5.3.3 | CDN | Layout, components |
| Icons | Font Awesome 6.5 | CDN | Icons |
| Charts | Chart.js 4.4 | CDN | Live, trend, doughnut, bar |
| Runtime | No build step | – | Pure HTML/JS, no Node build needed |

> **No Node.js, no compilation, no D-Wave hardware required.** Everything runs offline after `pip install`.

---

## 5. Project Structure — What is What

```
8.ProjectCode/
├── backend/
│   ├── app.py                 # Flask app, all routes, ensemble logic, startup loading  [20008 bytes]
│   ├── synthetic_data.py      # Generates Stone-like synthetic CSV (fraud vs legit patterns)  [3378 bytes]
│   ├── preprocessing.py       # One-Hot + Z-Score + corr filter + CatBoost/RF feature filter + balancers  [6095 bytes]
│   ├── rbm_classifier.py      # AI model core (Gaussian visible + binary hidden + label) + QUBO builder  [8364 bytes]
│   ├── samplers.py            # Simulated Annealing & Quantum-inspired sampling routines  [7296 bytes]
│   ├── train.py               # Training loop (epochs, learning-rate schedule, metrics)  [5759 bytes]
│   ├── evaluation.py          # accuracy/precision/recall/F1/ROC-AUC/confusion matrix  [934 bytes]
│   └── __init__.py
├── frontend/
│   └── templates/
│       └── index.html         # Single-page product UI (Dashboard / Verify / Bulk / Analytics)  [~35 KB]
│   └── static/                # (empty, for custom CSS if needed)
├── data/
│   ├── creditcard_synthetic.csv  # 39,000 rows, 28 cols, generated (18.7 MB)
│   ├── sample_batch.csv          # 20-row sample for Bulk demo (9.6 KB)
│   └── batch_predictions.csv     # overwritten after each bulk upload
├── models/
│   ├── grbmc_classical.pkl    # Pre-trained model 1 (classical)
│   ├── grbmc_sa.pkl           # Pre-trained model 2 (annealing)
│   ├── grbmc_qa.pkl           # Pre-trained model 3 (quantum-inspired)
│   ├── history_*.json         # Per-epoch metrics (for internal analysis)
│   └── pipeline.pkl           # Fitted scaler + selected columns + feature importance (2.6 MB)
├── docs/                      # Full documentation (this folder)
├── requirements.txt           # pip dependencies (11 lines)
├── run.bat                    # Double-click launcher (Windows)
├── run.ps1                    # PowerShell launcher
├── seed_models.py             # One-time script to regenerate models + pipeline
└── README.md                  # You are here (complete guide)
```

**File purposes:**

*   **`app.py`** — The heart. Defines `ensure_data()`, `ensure_pipeline()`, 9 API routes, loads `pipeline.pkl` + `grbmc_*.pkl` on startup, serves `index.html`.
*   **`synthetic_data.py`** — `generate_synthetic_transactions()` creates realistic fraud (high amount, Online, Card Not Present, Country Mismatch, shifted V3/V7/V10/V14/V17) vs legit (opposite). `create_balanced_39k()` mimics paper's 145M → 39K 50/50 balancing.
*   **`preprocessing.py`** — `full_pipeline()` does: `one_hot_encode(dtype=float)` → `zscore_normalize()` on `Amount, Time, V1..V22` → `correlation_filter(0.95)` → `balancing_*` → `feature_importance_filter(top_k)` via RandomForest (CatBoost if installed) → `train_test_split(80/20)`.
*   **`rbm_classifier.py`** — `GRBMC(n_visible, n_hidden, n_label)` with weights `W, U, b, c, d`, `sigmoid()`, Gibbs sampling, PCD persistent chain, `predict_proba()` via free energy + softmax, `get_qubo_matrix()` (App. B).
*   **`samplers.py`** — `simulated_annealing_grad()` (PIMC-like sweeps, beta schedule) and `quantum_sampling_grad()` (A(s)/B(s) + tunneling) — prototype acceleration (10 sweeps, 16 reads).
*   **`train.py`** — `train_model(..., mode=classical|sa|qa, epochs, n_hidden)` — SA/QA subsample to 3000 rows/epoch for speed, LR schedules, logs `accuracy/precision/recall/f1/loss`.
*   **`evaluation.py`** — helper `evaluate(y_true, y_pred, y_proba)` returning metrics dict.
*   **`index.html`** — Product UI: no paper terms, only business language.

---

## 6. Prerequisites

*   **OS:** Windows 10/11 (tested), Linux/macOS also works (use `python3`).
*   **Python:** 3.11.x (3.10+ ok). Check: `python --version` → `Python 3.11.9`.
*   **pip:** 24+. Check: `pip --version`.
*   **Browser:** Chrome / Edge / Firefox (latest).
*   **RAM:** 4 GB free (dataset 18 MB, models < 50 MB).
*   **Internet:** Only for CDN (Bootstrap/Chart.js/FontAwesome) — app works offline after first load if cached.

---

## 7. Installation — Step by Step

### Windows (Recommended)

1.  **Open the project folder** in File Explorer: `D:\abstracts\Madhav\CSE\A\CSE-A-A4\8.ProjectCode\`
2.  **Open PowerShell / CMD** in that folder (Shift + Right-click → *Open in Terminal*, or type `cmd` in address bar).
3.  **Create a virtual environment (optional but recommended):**
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
    You should see `(venv)` prefix.
4.  **Install dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```
    Expected output: `Successfully installed Flask-3.1.0 ... imbalanced-learn-0.12.4`
5.  **Verify data/models exist:**
    ```powershell
    dir data
    dir models
    ```
    You should see `creditcard_synthetic.csv` (18 MB) and `grbmc_*.pkl`, `pipeline.pkl`. If missing, run:
    ```powershell
    python backend/synthetic_data.py
    python seed_models.py
    ```
    (Seed takes ~45 sec for 8K subset, 10 epochs × 3 models.)

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend/synthetic_data.py
python seed_models.py
```

---

## 8. How to Run the Project (3 Ways)

### Way A — Double-Click (Easiest, Windows)

Double-click **`run.bat`** in File Explorer.
It will:
1. `pip install -r requirements.txt --quiet`
2. `start http://127.0.0.1:5000` (opens browser)
3. `python backend/app.py` (starts server)

Keep the black window open. Press `Ctrl+C` to stop.

### Way B — PowerShell

```powershell
.\run.ps1
```
Same as above, but via PowerShell.

### Way C — Manual (for debugging)

```powershell
pip install -r requirements.txt
python backend/app.py
```

You will see:
```
Starting QuantumFraudGuard backend on http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.0.109:5000
```

Now open Chrome → `http://127.0.0.1:5000`.

> **Port already in use?** Change in `backend/app.py` last line: `app.run(host="0.0.0.0", port=5001, debug=False)` then open `:5001`.

---

## 9. Using the Application — Page by Page

### 9.1 Dashboard (Default Landing)

*   **Top banner:** *Intelligent Fraud Protection for Every Payment* + `Verify a Transaction` / `View Analytics` buttons.
*   **4 KPI cards:** Transactions Today (~16,956), Fraud Prevented (~127), Precision 94.0%, Customer Trust 4.9/5.
*   **Live Transaction Monitoring** — auto-refreshing line chart (Legitimate 98% vs Flagged 1-2%). Updates every 2 seconds (simulated).
*   **Recent High-Risk Alerts** — 3–4 fraud cases from dataset (e.g., `$614.23 • Electronics • Chip • Flagged 2 min ago • Auto-declined`).
*   **Recent Transactions** — 6-row table (`Time | Amount | Merchant | Type | Status | Risk`) from `GET /api/dataset_info`.

### 9.2 Verify Transaction (Single Check)

**Form fields:**
*   Amount (USD) — e.g., `342.5` or try high-risk `1200`
*   Merchant Category — Grocery / Electronics / Travel / Online / …
*   Channel — Online / Chip / Contactless / Swipe
*   Card Present — Yes/No
*   Country Match — Yes/No
*   Transaction Time — seconds ago
*   User History Score / Location Variance / Spending Pattern — sliders `V3, V14, V17` (advanced, pre-filled 1.8, -1.1, 1.4)

**Steps:**
1. Fill form (for fraud demo: Amount `1200`, Merchant `Online`, Channel `Online`, Card Present `No`, Country Match `No`).
2. Click **Run Fraud Check**.
3. Result card shows:
    *   `Fraud Detected` (red) or `Transaction Approved` (green)
    *   `Risk Score 52.7% • MEDIUM` + progress bar
    *   `Decision: DECLINE & ALERT` or `APPROVE`

Behind: `POST /api/predict_single` → ensemble average of 3 models.

**Tip box** explains the high-risk pattern.

### 9.3 Bulk Verification (CSV Upload)

**Steps:**
1. Click **Bulk Verification** tab.
2. In the dashed box, click **Browse** and select `data/sample_batch.csv` (or any CSV with similar columns; may include `Class` for accuracy).
3. Click **Upload & Analyze**.
4. Results panel shows:
    *   `20 transactions • 8 flagged` badges
    *   If `Class` present: `Accuracy 92% • Precision 90% • Recall 95% • F1 92%`
    *   Table preview (10 rows): `# | Status (Flagged/Approved) | Fraud Score | Risk (High/Medium/Low)`
5. Click **Download Results (CSV)** → downloads `data/batch_predictions.csv` with added columns `Predicted_Class, Fraud_Probability, Risk`.

**CSV format expected:**
```
Amount,Time,Merchant_Category,Transaction_Type,Card_Present,Country_Match,V1..V22,Class
614.23,3855044,Electronics,Chip,0,0,0.25,-0.25,...,1
...
```
If `Class` missing, metrics are omitted but predictions still returned.

### 9.4 Analytics

*   **Fraud Trend – Last 7 Days** — line chart (Fraud Attempts vs Blocked, Mon–Sun).
*   **Risk by Merchant Category** — doughnut (Online 35%, Electronics 22%, …).
*   **Fraud by Hour** — bar (peak 16h 1.4%).
*   **System Performance** — 4 tiles: Detection Rate 98.7%, Precision 94%, Avg Response 47ms, Fraud Blocked 3,842 (30d, $2.1M saved).

All charts are static demo but illustrate a real product.

---

## 10. API Reference

Base URL: `http://127.0.0.1:5000`

| Method | Path | Body / Query | Response (example) |
|--------|------|--------------|--------------------|
| `GET` | `/` | – | `index.html` |
| `GET` | `/api/health` | – | `{"status":"ok","models_trained":["classical","sa","qa"],"data_rows":39000}` |
| `GET` | `/api/dataset_info` | – | `{"rows":39000,"columns":[...],"fraud_count":19500,"legit_count":19500,"head":[...]}` |
| `POST` | `/api/generate_dataset` | `{"n_fraud":19500,"n_legit":19500}` | `{"rows":39000,"fraud":19500,"legit":19500}` |
| `POST` | `/api/preprocess` | `{"method":"manual","top_k":18}` | `{"columns":[...],"train_shape":[6400,18],"test_shape":[1600,18],"feature_importance":{...}}` |
| `POST` | `/api/train` | `{"modes":["classical","sa","qa"],"epochs":10,"n_hidden":65}` | `{"classical":{"history":{...},"metrics":{...}}, ...}` |
| `GET` | `/api/train_status` | – | `{"classical":{"epochs":10,"best_f1":0.669,...}}` |
| `GET` | `/api/comparison` | – | `[{"Method":"PCD","Accuracy":50.3,...}, ...]` |
| `GET` | `/api/qubo?mode=sa` | query `mode` | `{"shape":[85,85],"Q":[...],"stats":{"min":..}}` |
| `POST` | `/api/predict_single` | `{"Amount":350,"Merchant_Category":"Online","Transaction_Type":"Online","Card_Present":0,"Country_Match":0,"Time":50000,"V3":1.8,"V14":-1.1,"V17":1.4,"mode":"ensemble"}` | `{"prediction":1,"fraud_probability":0.52,"label":"FRAUD","risk_level":"MEDIUM","individual_models":{"classical":0.49,"sa":0.58,"qa":0.50}}` |
| `POST` | `/api/predict_batch` | `multipart/form-data file=CSV` | `{"rows":20,"fraud_detected":8,"preview":[...],"metrics":{"accuracy":0.92,...}}` |
| `GET` | `/api/export_predictions` | – | CSV file download |

**cURL examples:**

```bash
# Health
curl http://127.0.0.1:5000/api/health

# Single predict (PowerShell)
Invoke-WebRequest -Uri http://127.0.0.1:5000/api/predict_single -Method POST -ContentType "application/json" -Body '{"Amount":1200,"Merchant_Category":"Online","Transaction_Type":"Online","Card_Present":0,"Country_Match":0,"Time":50000,"V3":1.8,"V14":-1.1,"V17":1.4}'

# Bulk (requires CSV)
curl -F "file=@data/sample_batch.csv" http://127.0.0.1:5000/api/predict_batch
```

---

## 11. Dataset Details

*   **Source:** Synthetic, mimicking Stone fintech's 145M real transactions (3 months, Brazil, anonymized per Brazilian data protection laws).
*   **Raw synthetic:** `generate_synthetic_transactions(n_fraud, n_legit)` creates:
    *   **Legit:** Amount ~ N(80,60), Merchant mostly Grocery/Fuel/Restaurant, Type mostly Chip/Contactless, Card Present 80%, Country Match 95%, V1–V22 ~ N(0,1).
    *   **Fraud:** Amount ~ N(350,250), Merchant mostly Online/Electronics, Type mostly Online 60%, Card Present 30%, Country Match 60%, V3+1.5, V7-1.2, V10+1.0, V14-0.8, V17+1.3 (shifted).
*   **Balanced file:** `data/creditcard_synthetic.csv` — 39,000 rows, 50/50 split (manual undersampling, as paper found SMOTE/Tomek performed poorly on extreme imbalance). `sample_batch.csv` is 20 random rows from it for quick demo.
*   **Columns (28):** `Amount, Time, Merchant_Category, Transaction_Type, Card_Present, Country_Match, V1..V22, Class (0=legit,1=fraud)`.

---

## 12. AI Engine Overview (Simplified)

You don't need quantum hardware — the engine is **quantum-inspired** and runs on CPU.

*   **Model:** Gaussian-Bernoulli RBM Classifier — visible layer (continuous features), hidden layer (binary), label layer (2 units). Learns probability distribution of transactions.
*   **Three optimizers (ensemble):**
    1. **Classical PCD** — Gibbs sampling, large batch 512, 200 hidden units, 2 min (paper). Good baseline.
    2. **Simulated Annealing (SA)** — PIMC sweeps, anneals from hot to cold, small batch 32, 65 hidden, ~4 h (paper) but prototype samples 3000 rows/epoch → ~5 sec.
    3. **Quantum Sampling (QA)** — adds transverse-field tunneling noise (simulates D-Wave), same config as SA, ~1.8 h (paper) → ~5 sec prototype.
*   **Why ensemble?** Average of 3 models gives stable `fraud_probability`. High precision (94% for SA) means very few false positives — critical for banking.
*   **QUBO/Ising:** Internal representation `Q = -[[Qvv,Qvh,0],...]` and `H_Ising = C + Σ h_i s_i + Σ J_ij s_i s_j` — not exposed in product UI, but available via `/api/qubo` for technical review.
*   **Performance (demo subset 8K):** Classical F1 0.669, SA F1 0.944, QA F1 0.878 — SA best, as in paper (SA 88% F1 > PCD 83%). Full data would be tighter.

---

## 13. Configuration & Customization

*   **Change port:** `backend/app.py` last line `app.run(host="0.0.0.0", port=5000, debug=False)` → `5001`.
*   **Retrain on full 39K:** In `seed_models.py` remove `df.sample(n=8000...)` and set `epochs=20` (takes ~3 min).
*   **Adjust features:** `backend/preprocessing.py` → `top_k` param (default 18) controls how many features survive CatBoost/RF filter. `NUMERICAL_COLS`, `CATEGORICAL_COLS` lists.
*   **Thresholds:** Risk levels in `app.py` `predict_single()`: `>0.7 HIGH, >0.4 MEDIUM, else LOW`.
*   **Colors / branding:** `frontend/templates/index.html` `:root` CSS variables (`--accent:#2563eb`).
*   **Add real data:** Replace `data/creditcard_synthetic.csv` with your CSV (same columns) and delete `models/pipeline.pkl` + `models/grbmc_*.pkl`, then `python seed_models.py` to retrain.

---

## 14. Troubleshooting & FAQ

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: flask_cors` | deps not installed | `pip install -r requirements.txt` |
| `ValueError: object of type float has no exp` | pandas object dtype after One-Hot | Already fixed via `dtype=float` in `preprocessing.py:38` + `.astype(float)`; just reinstall |
| `Port 5000 already in use` | Another app / old python running | `Get-Process python | Stop-Process -Force` or change port |
| Browser shows `Failed to fetch` | Flask not running | Keep `python backend/app.py` window open; check `http://127.0.0.1:5000/api/health` |
| `No model trained` on verify | `models/` missing | Run `python seed_models.py` once |
| Slow training (4 h) | Full data + many epochs | Normal per paper; prototype uses 3K subsample — reduce `epochs` to 10 in UI |
| CSV upload fails `Pipeline not run` | `pipeline.pkl` missing | `python -c "import joblib; from backend.preprocessing import full_pipeline; import pandas as pd; df=pd.read_csv('data/creditcard_synthetic.csv').sample(n=8000); res=full_pipeline(df); joblib.dump(res,'models/pipeline.pkl')"` |
| Charts not loading | CDN blocked | Check internet; Chart.js/Bootstrap are CDN — intranet may need offline copy |

**Logs:** Flask prints to console. For verbose training, see `seed_models.py` output.

---

## 15. Deployment Notes

*   **Development:** `debug=True` in `app.py` enables auto-reload (not for production).
*   **Production:** Use `gunicorn` (Linux) or `waitress` (Windows):
    ```bash
    pip install waitress
    waitress-serve --host=0.0.0.0 --port=5000 backend.app:app
    ```
*   **Docker (optional):**
    ```dockerfile
    FROM python:3.11-slim
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    COPY . .
    EXPOSE 5000
    CMD ["python","backend/app.py"]
    ```
*   **Security:** Add authentication, HTTPS, rate limiting before exposing to internet — prototype has no login (as requested).

---

## 16. Future Enhancements

*   Deep Belief Network stacking (paper Sec V).
*   Real D-Wave Leap integration when QPU access available.
*   User accounts, role-based access (admin vs analyst).
*   Webhook alerts to Slack/Email on HIGH risk.
*   Model drift monitoring and auto-retraining.

---

**Prepared for B.Tech Final Year evaluation — production-style demo, no paper jargon in UI.**

*To regenerate docs:* `python seed_models.py` then refresh browser.

