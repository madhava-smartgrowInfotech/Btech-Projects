# SHEGUARD

A women's safety companion: safer route guidance, hands-free emergency triggers, live
guardian tracking, secure evidence capture and an AI safety assistant - built end-to-end with
real data, a real trained model and real external APIs.

## Features
- **Safe Route** - OSRM route alternatives scored by area risk and time of day; safest highlighted on a map with a risk heat layer.
- **Area risk model** - K-Means clustering of district-level crimes-against-women data into low/medium/high risk tiers.
- **SafePhrase + Smart SOS** - a spoken phrase (Web Speech API) or one tap starts an emergency.
- **Live location session** - position streams to guardians over a WebSocket; they watch it move on a read-only tracking page, no login needed.
- **Free alerts** - Telegram message + email to every guardian with the live tracking link, plus in-app status.
- **Evidence capture** - photo or audio clip saved with timestamp, location and a SHA-256 hash.
- **AI safety assistant** - Gemini answers safety questions with location-aware context.
- **Roles & access** - every query scoped to the logged-in user; guardians only ever see a per-session share link.
- **Installable PWA** - add-to-home-screen, full-screen app on a phone.

## Quick start
```
setup.bat
venv\Scripts\python.exe ml\train_risk_model.py
run.bat
```
Fill in `.env` (copied from `.env.example` by `setup.bat`) with your free Gemini/Telegram/Gmail
keys before testing alerts and the assistant - see `docs/03_HOW_TO_RUN.md` for the full guide,
including phone testing via a Cloudflare tunnel.

**Demo login:** `demo@sheguard.app` / `Demo@1234` (run `venv\Scripts\python.exe scripts\seed_demo.py`
once the backend is up), or just register your own account.

## Evaluation results
See `experiments/metrics.json` (training) and `experiments/eval/metrics.json` (evaluation) -
summarised below and reproduced with `ml/train_risk_model.py` then `ml/eval.py`.

**Area risk model** (467 of 827 districts geocoded successfully via Nominatim; the rest are
odd sub-entries like railway divisions Nominatim can't resolve to a single point, and are
excluded rather than guessed):
- K-Means (k=3) silhouette score: **0.58**, Davies-Bouldin score: **0.53** (lower is better) - a
  clean 3-way split.
- Tiers: **low** 278 districts (mean 97.8 crimes/year), **medium** 148 (327.9/year), **high**
  41 (720.9/year).

**Route scoring sanity check** (`ml/eval.py`): a route sampled entirely from high-risk
districts scores **5.0** vs **1.0** for one sampled entirely from low-risk districts - the
scorer reliably ranks the safer route first.

**End-to-end smoke test** (`scripts/smoke_test.py`): all 12 steps pass against the live API -
register, login, add guardian, load 467 risk areas, plan a real OSRM route, start an SOS
(with best-effort Telegram/email delivery), push a location update, upload evidence with a
verified 64-char SHA-256 hash, read the public tracking page, cancel, and confirm the
cancellation propagates. The Gemini step is skipped with a warning (not a failure) until you
add `GEMINI_API_KEY`.

## Documentation
- [`docs/01_OVERVIEW.md`](docs/01_OVERVIEW.md) - what it does and who it's for
- [`docs/02_HOW_IT_WORKS.md`](docs/02_HOW_IT_WORKS.md) - data sources, ML pipeline, how each feature is implemented
- [`docs/03_HOW_TO_RUN.md`](docs/03_HOW_TO_RUN.md) - setup, running, phone testing, smoke test
- [`docs/PLAN.md`](docs/PLAN.md) - original architecture plan

## Tech stack
React + Vite (JS) + Tailwind + Leaflet frontend - FastAPI + SQLAlchemy + SQLite backend -
scikit-learn (K-Means) - OSRM + Nominatim + Gemini + Telegram Bot API + Gmail SMTP - installable
PWA - Cloudflare quick tunnel for phone testing.

## Defaults chosen during the build
- Python 3.10 (3.11+ wasn't available on the build machine; everything used is 3.10-compatible).
- Gemini model: `gemini-2.0-flash`.
- SafePhrase default text: "help me sheguard" (user-editable on the Home screen).
- Night-time risk weighting: approximated as 21:00-05:30 IST using the server's UTC clock (no
  per-user timezone lookup, to keep the build simple).
- Guardian delivery is best-effort per channel (Telegram/email) - the SOS-start response reports
  what succeeded so the UI can show it.
