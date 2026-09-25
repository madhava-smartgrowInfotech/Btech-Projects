# SHEGUARD - Build Plan

## Architecture
React+Vite (JS) frontend (port 5107) <-> FastAPI backend (port 8107, SQLite via SQLAlchemy)
<-> external free services: OSRM (routing), Nominatim (geocoding, cached), Gemini API (assistant),
Telegram Bot API + Gmail SMTP (alerts). Live location via FastAPI WebSocket. Cloudflare quick
tunnel exposes both ports over HTTPS for phone testing.

## Data & ML
Kaggle "Crime in India" + "Crimes against women in India 2001-2021" (committed CSVs). Districts
geocoded once via Nominatim -> `data/districts_geocoded.csv` (committed, cached). `ml/train_risk_model.py`
builds per-district features (crime rate, trend) and runs K-Means (fallback DBSCAN) to assign
3 risk tiers (low/medium/high). Model + `experiments/metrics.json` committed. `ml/eval.py` scores
cluster quality (silhouette) into `experiments/eval/metrics.json`.

## Backend endpoints
- POST /api/auth/register, /api/auth/login -> JWT
- GET/POST /api/guardians (CRUD, owner-scoped)
- POST /api/routes/plan -> OSRM alternatives scored by district risk tier + time-of-day -> safest pick
- GET /api/risk/areas -> district risk tiers (heat layer)
- POST /api/sos/start, POST /api/sos/{id}/cancel, GET /api/sos/{id}
- POST /api/sos/{id}/evidence (multipart photo/audio) -> SHA-256 hash stored
- WS /ws/location/{session_id} (owner pushes), GET /api/track/{token} (public guardian view, read-only)
- POST /api/ai/ask -> Gemini
- Alerts service: Telegram sendMessage + Gmail SMTP on SOS start

## Tables
users, guardians, emergency_sessions, location_pings, evidence, districts_risk

## Screens (frontend/src/pages)
Landing, Login/Register, Home (SOS + SafePhrase), RoutePlanner, EmergencySession, GuardianTrack
(public, token-based), Guardians+Settings, Assistant

## Roles/RLS
Row-level checks in FastAPI (not Postgres RLS, SQLite): every query filters by `user_id`/guardian
share token; guardians only reach data via a per-session share token, never account login.

## Ports & secrets
Backend 8107, frontend 5107 (strictPort). Keys in `.env` (git-ignored): GEMINI_API_KEY,
TELEGRAM_BOT_TOKEN, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, JWT_SECRET. `.env.example` documents all.
