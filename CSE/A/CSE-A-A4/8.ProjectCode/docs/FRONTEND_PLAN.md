# Frontend Plan - SecurePay AI (Credit Card Fraud Detection Using Machine Learning)

Design: **V4 - Soft Pastel Calm** (kit copied into `frontend/src`) · Backend **8304** · Frontend **5304**
Stack: React 18 + Vite (JavaScript) + the V4 kit. The old Flask template (`frontend/templates/index.html`) stays untouched and keeps working at `/` on the backend.

## 1. Backend inventory (Flask, `backend/app.py`)

| # | Method | Path | Request | Response |
|---|--------|------|---------|----------|
| 1 | GET | `/api/health` | - | `{status, models_trained[], data_rows}` |
| 2 | GET | `/api/dataset_info` | - | `{rows, columns[], fraud_count, legit_count, head[5], describe{}}` |
| 3 | POST | `/api/generate_dataset` | `{n_fraud, n_legit}` (500-50000 each) | `{rows, fraud, legit, message}` - **wipes loaded models/histories in memory** |
| 4 | POST | `/api/preprocess` | `{method: manual\|smote\|tomek, top_k}` | `{columns[], train_shape, test_shape, feature_importance{top 20}, dropped_corr[], scaler, balancing, message}` |
| 5 | POST | `/api/train` | `{modes[], epochs, n_hidden}` | `{<mode>: {history, metrics{accuracy,precision,recall,f1,confusion_matrix,roc_auc,report}, config}}` - slow, synchronous |
| 6 | GET | `/api/train_status` | - | `{<mode>: {epochs, best_f1, last_metrics}}` |
| 7 | GET | `/api/comparison` | - | `[{Method, mode, Accuracy, Precision, Recall, F1-Score, TotalTime, best_epoch}]` (best-F1 epoch) |
| 8 | GET | `/api/qubo?mode=` | `mode` classical\|sa\|qa | `{shape, display_size, Q[40x40], stats{min,max,mean}}` or 404 |
| 9 | POST | `/api/predict_single` | `{Amount, Time, Merchant_Category, Transaction_Type, Card_Present, Country_Match, V1..V22 (defaults = dataset mean), mode}` | `{prediction, fraud_probability, label, risk_level, individual_models{}}` |
| 10 | POST | `/api/predict_batch` | multipart `file` (CSV) | `{rows, preview[10], fraud_detected, metrics\|null}` |
| 11 | GET | `/api/export_predictions` | - | CSV download of last batch (404 if none) |
| - | GET | `/` | - | old Flask template (left as-is) |

### Additive read-only endpoints I will add (new file `backend/api_extra.py`, existing routes untouched)
The old UI faked its dashboard/analytics numbers. To show **real data only** the new UI needs:

| Path | Returns | Why |
|------|---------|-----|
| `GET /api/dataset_stats` | fraud rate by merchant category, by channel, by hour of day, amount buckets, card-present / country-match splits (computed from the loaded CSV) | Dashboard + Analytics charts (replaces the invented 7-day / hourly / merchant charts) |
| `GET /api/model_history` | per-epoch accuracy / precision / recall / F1 / loss for each model, `elapsed_sec`, `paper_time` | Training curves (only available today as a side effect of `POST /api/train`) |
| `GET /api/feature_importance` | feature importance of the loaded pipeline + selected columns + dropped-correlated columns | Feature chart without re-running `POST /api/preprocess` |
| `GET /api/sample_batch` | serves `data/sample_batch.csv` as a download | The old UI linked "sample_batch.csv" to the wrong URL |

## 2. Feature / screen inventory (existing UI + README + docs)

| Feature | Existing location | Endpoints |
|---------|-------------------|-----------|
| KPI cards, recent transactions, high-risk alerts, composition | Dashboard tab | 1, 2, new `dataset_stats` |
| "Live" monitoring chart | Dashboard tab (random numbers) | replaced by real class mix / amount distribution |
| Verify single transaction (risk score, decision, per-model scores, tip, risk bands) | Verify tab | 9 |
| Bulk CSV verification (upload, flagged count, metrics-if-labelled, preview, download) | Bulk tab | 10, 11 |
| Analytics (merchant risk, hour risk, trend, performance tiles) | Analytics tab | 7, new `dataset_stats` |
| Dataset generate / inspect | API only, README 13 | 2, 3 |
| Preprocess + feature importance | API only | 4, new `feature_importance` |
| Train classical / SA / QA, view curves, metrics, confusion matrix | API only | 5, 6, new `model_history` |
| Model comparison table (PCD / SAS / QS) | API only | 7 |
| QUBO heatmap | API only (README 12) | 8 |
| Light/dark, responsive | - | - |

## 3. Screen map to build

| Route | Screen | Kit pieces | API |
|-------|--------|------------|-----|
| `/` | **Landing** (hero, how it works, live model numbers, CTA) | motion helpers, Card, Button | 1, 7 |
| `/app` | **Dashboard** - stat cards (rows, fraud, legit, best F1), class balance, risk by channel, recent transactions, high-risk sample alerts | AppShell, StatCard, charts, Table | 1, 2, stats |
| `/app/verify` | **Verify Transaction** - form, risk meter, decision, per-model bars, risk-band guide, demo presets | Form, Card, Badge, ProgressBar | 9 |
| `/app/bulk` | **Bulk Verification** - FileDrop, sample download, summary, metrics + confusion matrix, preview table, export | FileDrop, Table, Stepper | 10, 11 |
| `/app/analytics` | **Analytics** - fraud by merchant, by channel, by hour, amount distribution, card-present / country-match | charts, Tabs | stats |
| `/app/models` | **Model Comparison** - PCD / SAS / QS table, training curves, QUBO heatmap, feature importance | Tabs, charts, Table | 6, 7, 8, history, importance |
| `/app/lab` | **Model Lab** - dataset generate, preprocess, train (confirm modal, progress state) | Modal, Stepper, Form | 2, 3, 4, 5 |
| `*` | 404 page | EmptyState | - |

Shared: topbar theme toggle (persisted), backend health pill, toasts, drawer sidebar < 1024px.

## 4. Verification checklist (ticked in Step 4)

- [x] Dashboard KPIs / recent transactions / alerts from real data
- [x] Verify single transaction (all 10 inputs + preset demos, ensemble result, per-model scores)
- [x] Bulk CSV upload, metrics, preview, export download, sample download
- [x] Analytics charts from real data
- [x] Dataset generate / inspect
- [x] Preprocess + feature importance
- [x] Train (classical / SA / QA) + curves
- [x] Model comparison table
- [x] QUBO heatmap
- [x] Dark mode, 360 / 768 / 1440, reduced motion, keyboard
- [x] `npm run build`, `scripts/smoke_test.py`, console clean

## 5. Verification record
- `npm run build` passes; `scripts/smoke_test.py` 20/20 against the Vite proxy and against Flask directly.
- `scripts/capture_screens.py` walks every screen with real data (16 screenshots in `docs/screenshots/`, landing in light + dark) and exits clean: no console errors, rejections or 4xx/5xx.
- `scripts/responsive_check.py`: all 8 routes at 360 / 768 / 1440 px in light and dark have no horizontal scroll; drawer opens and Escape closes it; skip link, focus outline, input labels, theme persistence and reduced-motion all pass.
- Error / empty / success states exercised (API offline, 500 from train, bad CSV, invalid form, mocked training result): screenshots 20-22.
- Retraining (`/api/train`) and dataset regeneration were **not** run against the real models (they overwrite `models/` and the CSV); the Lab screen's training result view was verified with a mocked API response of the real shape. `python scripts/smoke_test.py --full` runs the real flow.

## 6. Notes / findings
- No `.env` existed; created `.env` (`BACKEND_PORT=8304`, `FRONTEND_PORT=5304`, git-ignored) and `.env.example`. `backend/app.py` now reads `BACKEND_PORT` (default 8304) instead of the hard-coded 5000 - a config-only change.
- Pre-existing backend behaviour (not changed): `POST /api/predict_batch` swallows a scaler error, so un-scaled values go to the models; the bundled `sample_batch.csv` comes back with all 20 rows flagged (docs say 8). The UI renders whatever the API returns.
- `POST /api/generate_dataset` clears in-memory models; `/api/train` is synchronous and slow, so the Lab screen guards both behind a confirm dialog.
