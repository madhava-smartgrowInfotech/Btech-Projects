# 08 · Configuration

All settings live in **`.env`** in the project folder. `setup.bat` creates it from
**`.env.example`** (with a new random `JWT_SECRET`) and never overwrites an existing file.
`.env` is git-ignored — never commit it. Restart UPI Guardian after changing it.

| Key | Default | What it does | How to get / choose it |
|---|---|---|---|
| `API_HOST` | `127.0.0.1` | Address the API listens on | Keep `127.0.0.1`; the web app (and the phone tunnel) reach the API through the Vite proxy |
| `API_PORT` | `8204` | API port | Fixed so UPI Guardian can run next to other products; change only if 8204 is taken (also update `CORS_ORIGINS` if needed) |
| `FRONTEND_PORT` | `5204` | Web app port (dev and preview) | Fixed, `strictPort` — the web server refuses to start on another port |
| `CORS_ORIGINS` | `http://localhost:5204,http://127.0.0.1:5204` | Browser origins allowed to call the API directly | Comma separated |
| `JWT_SECRET` | *(random, from setup.bat)* | Secret that signs login tokens | Generate your own: `venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"`. Changing it signs everyone out |
| `JWT_EXPIRE_MINUTES` | `720` | How long a login stays valid | Minutes (720 = 12 h) |
| `DATABASE_PATH` | `data/app.db` | SQLite file (created automatically) | Relative paths are resolved from the project folder |
| `SEED_SAMPLE_DATA` | `true` | Load the sample accounts, history, reports and requests into an empty database | `false` gives an empty sandbox |
| `SANDBOX_START_BALANCE` | `50000` | Starting balance (₹) of every new wallet | Any whole number |
| `RISK_MEDIUM_THRESHOLD` | `35` | Fallback Medium threshold (score 0–100) | Used only if `models/risk_policy.json` is missing; admins can change the live policy in *Fraud analytics* |
| `RISK_HIGH_THRESHOLD` | `70` | Fallback High threshold | As above |
| `HOLD_MINUTES_DEFAULT` | `30` | Default Delayed Protection hold for new accounts | Users can change their own hold time in Settings |
| `HOLD_CHECK_SECONDS` | `5` | How often the scheduler releases or expires holds | 1–60 |
| `TTS_ENABLED` | `true` | Allow new spoken phrases via gTTS (needs internet) | `false` = only pre-recorded phrases; the app falls back to the browser's voice |
| `VOICE_CACHE_DIR` | `data/voice_cache` | Where newly spoken phrases are cached as MP3 | Pre-recorded guides are in `backend/app/assets/voice/` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` | Logs are JSON lines in the API window |
| `KAGGLE_API_TOKEN` | *(empty)* | Only for `scripts/download_data.py` | Kaggle → profile → *Settings* → *API* → *Generate New Token*; see [04_DATASET.md](04_DATASET.md). Not needed normally — the datasets are committed |
| `CLOUDFLARED_PATH` | *(empty)* | Full path to `cloudflared.exe` for `run_phone.bat` | Leave empty to use PATH or `C:\Program Files (x86)\cloudflared\` |

## Other configuration files

| File | What it controls |
|---|---|
| `models/risk_policy.json` | Tuned score thresholds (Medium 35, High 70), block threshold 2.5, probability anchors — written by `ml/train_risk.py` |
| `models/behaviour_profile.json` | Hour-of-day and amount profiles from UPI Transactions 2024 |
| `frontend/vite.config.ts` | Ports (read from `.env`), `/api` + WebSocket + `/docs` proxy, allowed tunnel hosts (`.trycloudflare.com`), PWA manifest and caching |
| `backend/pytest.ini` | Test settings |

## Changing the policy without editing files

Sign in as admin → **Fraud analytics** → **Risk policy**. The values are stored in the database
(`app_settings`) and override `risk_policy.json` until you press **Back to tuned defaults**.
