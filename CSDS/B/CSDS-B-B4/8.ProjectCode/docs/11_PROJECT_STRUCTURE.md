# 11 · Project structure

```
8.ProjectCode/
├─ setup.bat · run.bat · run_phone.bat · stop.bat   one-command setup / start / phone mode / stop
├─ .env.example                                     every configuration key (copied to .env)
├─ .gitignore · .gitattributes                      what stays out of git · CRLF for .bat files
├─ README.md
├─ backend/                FastAPI application
├─ frontend/               React + Vite web app (installable PWA)
├─ ml/                     training, evaluation and the scenario simulator
├─ notebooks/              exploration, Kaggle-ready training, explainability
├─ experiments/            one folder per training run: model, metrics.json, plots, log
├─ models/                 the model files the app loads
├─ data/                   raw datasets, sample data, processed files, app.db
├─ scripts/                data download, generators, helpers used by the .bat files
└─ docs/                   this documentation
```

## backend/

| Path | What it contains |
|---|---|
| `run_api.py` | Starts Uvicorn on `API_HOST:API_PORT` (checks the port first) |
| `requirements.txt` | Pinned runtime packages |
| `app/main.py` | FastAPI app, lifespan (create tables, load models, seed sample data, start the hold scheduler), error handlers, CORS |
| `app/core/` | `config.py` (settings from `.env`), `db.py` (SQLite engine/session), `security.py` (bcrypt, JWT), `deps.py` (current user, admin guard, `api_error`), `logging.py` (JSON logs) |
| `app/models/entities.py` | All SQLAlchemy tables (see [02_ARCHITECTURE.md](02_ARCHITECTURE.md) §4) |
| `app/schemas/` | Pydantic request/response models for auth |
| `app/api/` | Routers: `auth, wallet, payments, qr, collect, holds (and approvals), trusted, trust (and reports), sms, voice, settings, notifications (and WebSocket), admin, models_info, sandbox, public, health` |
| `app/services/risk.py` | **Risk engine** — builds features from the ledger, runs M1 → M3, SHAP, policy |
| `app/services/explain.py` | SHAP → reason codes → sentences |
| `app/services/trust.py` | Payee trust score from the ledger and reports |
| `app/services/guard.py` | Collect-request and QR guard, `upi://pay` parsing/building |
| `app/services/intent.py` | Safety-question tree and scam-script matching |
| `app/services/payments.py` | Assess → intent → confirm → pay / hold → cancel |
| `app/services/holds.py` · `scheduler.py` | Delayed Protection, trusted-contact approval, the background release loop |
| `app/services/ledger.py` | Sandbox money movement (paise), references |
| `app/services/sms_rules.py` · `sms_service.py` | Scam-pattern rules (EN/HI/TE, native + romanised), language detection, entity extraction; storing SMS checks |
| `app/services/voice.py` | gTTS synthesis with the MP3 cache |
| `app/services/notifier.py` | Stored notifications + live WebSocket push after commit |
| `app/services/policy.py` | Thresholds (tuned defaults + admin overrides), level → action |
| `app/services/views.py` | One place that turns rows into API payloads |
| `app/services/sample_activity.py` · `app/seed.py` | Labelled sample accounts and six months of sample history, scored by the real models |
| `app/ml/features.py` | **Shared feature definitions** for M1, M3 and the trust score (used by training too) |
| `app/ml/sms.py` · `registry.py` | SMS analysis (model + rules + highlights); loading models and SHAP explainers |
| `app/i18n/messages.py` | Server-side texts in 3 languages: reasons, scam names, advice, spoken templates, screen guides |
| `app/assets/voice/` | 75 pre-recorded MP3 phrases (guides + advice, 3 languages) |
| `tests/` | pytest suite (see [09_TESTING.md](09_TESTING.md)) |

## frontend/

| Path | What it contains |
|---|---|
| `vite.config.ts` | Fixed ports with `strictPort`, `/api` (+ WebSocket) and `/docs` proxy, tunnel hosts, PWA manifest and caching |
| `tailwind.config.js` · `src/index.css` | Design tokens (light/dark), brand colours, chart palette, status colours |
| `public/` | Favicon, PWA icons (made by `scripts/make_icons.py`) |
| `src/main.tsx` · `src/App.tsx` | Providers (theme, i18n, TanStack Query, auth, motion) and routes |
| `src/lib/` | `api.ts` (Axios + error codes), `auth.tsx`, `i18n.tsx`, `theme.tsx`, `voice.ts` (playback + browser fallback), `live.ts` (WebSocket), `pwa.ts` (install prompt, online state), `types.ts`, `format.ts` |
| `src/locales/` | `en.ts`, `hi.ts`, `te.ts` — 756 UI strings each (type-checked for completeness) |
| `src/components/ui/` | shadcn/ui components (Radix-based) |
| `src/components/reactbits/` | React Bits components copied in as source (Aurora, BlurText, RotatingText, ShinyText, CountUp, SpotlightCard) with their licence |
| `src/components/risk/` | Risk gauge, level/status badges, trust badge, reason list, SHAP bars, highlighted text |
| `src/components/charts/` | Chart card (legend + table view), horizontal bar chart |
| `src/components/layout/` | App shell (sidebar, top bar, mobile tabs, notifications), route guards |
| `src/pages/` | `landing/`, `auth/`, `Home`, `Send`, `Scan`, `Collect`, `pay/` (risk check, intent, PIN, hold, outcomes), `SmsCheck`, `History`, `HistoryDetail`, `TrustedContacts`, `Approvals`, `Settings`, `ModelPerformance`, `Sandbox`, `admin/Analytics` |

## ml/

| File | Purpose |
|---|---|
| `train_all.py` | Runs every step in order and writes `models/model_cards.json` |
| `profile_upi2024.py` | UPI 2024 label check + behaviour profiles |
| `train_behaviour.py` · `contrastive.py` | M1 (LR, RF, XGBoost, contrastive + attention network) |
| `train_sms.py` · `train_sms_transformer.py` | M2 and the small-transformer comparison |
| `simulator.py` · `train_risk.py` | Scenario simulator and M3 (LR, RF, XGBoost), policy tuning, ablation |
| `common.py` | Experiment folders, metrics, plots |
| `requirements-train.txt` | Extra packages for training (PyTorch CPU, sentence-transformers) |

## data/

| Path | Contents | In git |
|---|---|---|
| `raw/payment_fraud_benchmark/` · `raw/upi_transactions_2024/` · `raw/sms_spam_collection/` | Full public datasets | yes |
| `raw/upi_scam_sms/` | Indian UPI-scam SMS set | yes |
| `sample/upi_scenarios_sample.csv` | 5,000-row sample of the simulation | yes |
| `processed/sms_heldout_for_simulation.csv` | Held-out SMS texts reused by the simulator | yes |
| `processed/upi_scenarios.csv.gz` | Full simulation (re-created by `ml/train_risk.py --regenerate`) | no |
| `app.db` | The sandbox database (created on first start) | no |
| `voice_cache/` | Newly spoken phrases | no |

## scripts/

`init_env.py` (creates `.env`), `wait_for.py` (used by `run.bat`), `phone_link.py` (Cloudflare
tunnel + link/QR), `download_data.py`, `generate_scam_sms.py`, `build_voice_cache.py`,
`build_notebooks.py`, `make_icons.py`.

## notebooks/

`01_data_exploration.ipynb` (all datasets), `02_kaggle_behaviour_model.ipynb` (Kaggle-ready M1
training; its output `behaviour_model_kaggle.joblib` is kept next to it),
`03_risk_explainability.ipynb` (SHAP waterfall and reasons for one payment). All are committed
with their outputs.
