# SHEGUARD - How it works

## Data

| Source | Licence | What's committed |
|---|---|---|
| [Crime in India](https://www.kaggle.com/datasets/rajanand/crime-in-india) (Kaggle, rajanand) | CC0 Public Domain (per dataset page) | `data/raw/district_wise_crimes_against_women_2001_2012.csv` - the district-wise crimes-against-women table (the file the risk model trains on). The rest of that Kaggle dataset (police strength, arrests, etc.) is not used by any SHEGUARD feature and isn't committed; re-download all of it with `scripts/download_data.py`. |
| [Crimes against women in India 2001-2021](https://www.kaggle.com/datasets/balajivaraprasad/crimes-against-women-in-india-2001-2021) (Kaggle, balajivaraprasad) | CC0 Public Domain (per dataset page) | `data/raw/crimes_against_women_2001_2021.csv` - state-year crime totals, committed in full (32 KB). Referenced by the AI assistant's context and available for the longer-range trend a future version could show. |
| District coordinates | Derived from OpenStreetMap via Nominatim (ODbL) | `data/districts_geocoded.csv` - 467 of the 827 (state, district) pairs geocoded successfully (the rest are sub-district entries like railway divisions that don't resolve to a single Nominatim result, and are dropped rather than guessed); cached so it never needs to run again. Produced by `scripts/geocode_districts.py`, respecting Nominatim's 1 request/second policy. |

Both datasets are well under the 200 MB commit threshold, so the actual CSVs are checked in
rather than a sample. `scripts/download_data.py` re-downloads them via `kagglehub` (anonymous,
no Kaggle account needed) if you ever delete `data/raw/`.

## F2 - Area risk model (ML)

`ml/train_risk_model.py`:
1. Loads the district-wise crimes-against-women CSV, drops `TOTAL` rollup rows, and sums the
   7 crime columns (Rape, Kidnapping & Abduction, Dowry Deaths, Assault, Insult to Modesty,
   Cruelty by Husband/Relatives, Importation of Girls) per district, averaged per reporting year
   to get one `crime_rate` feature per district.
2. Joins each district to its geocoded (lat, lng).
3. Standard-scales `crime_rate` and runs **K-Means (k=3)** on CPU (fits in well under a second
   for the 467 successfully-geocoded districts) to assign each district to a cluster.
4. Clusters are labelled `low` / `medium` / `high` by sorted mean crime rate, and a 0-100
   `risk_score` is min-max scaled from `crime_rate`.
5. Saves the fitted scaler + KMeans model to `models/risk_model.joblib`, the per-district table
   to `data/district_risk.csv` (loaded into the `district_risk` DB table on backend startup by
   `backend/app/seed.py`), and metrics to `experiments/metrics.json`.

`ml/eval.py` reloads the trained output and reports: silhouette score and Davies-Bouldin score
for the 3-tier clustering, per-tier crime-rate stats, and a sanity check that the route scorer
(`backend/app/services/risk.py`) always ranks an all-high-risk-district route above an
all-low-risk-district route. Numbers land in `experiments/eval/metrics.json` (see README for the
latest run).

## F1 - Safe Route

`POST /api/routes/plan` asks the free public **OSRM** demo server for alternative driving routes
between two points, then for each alternative samples points along the polyline, maps each
sampled point to its nearest district (haversine distance) and that district's risk tier, and
combines tier weights with a **night-time multiplier** (higher weight 21:00-05:30 IST-ish) into
a single risk score. Routes are sorted by that score; the lowest is marked `recommended`. The
frontend map draws every alternative plus a translucent circle per district coloured by risk
tier as a heat layer.

## F3 - Emergency triggers

- **Smart SOS**: one tap on the Home screen gets the browser's current geolocation and calls
  `POST /api/sos/start`.
- **SafePhrase**: the Home screen uses the browser's **Web Speech API**
  (`SpeechRecognition`/`webkitSpeechRecognition`) in continuous mode; when the live transcript
  contains the user's configured phrase, it stops listening and starts the same SOS flow with
  `trigger: "safephrase"`.

## F4 - Live location session

Starting an SOS creates an `emergency_sessions` row with a random `share_token`. While the
session is active, the owner's browser calls `navigator.geolocation.watchPosition` and pushes
updates (throttled to ~1 per 4s) to `POST /api/sos/{id}/location`. That endpoint stores the ping
and **broadcasts it over a FastAPI WebSocket** (`/ws/track/{share_token}`) to every guardian
currently viewing that session's tracking page - no polling.

## F5 - Free alerts

On SOS start, the backend loops over the user's guardians and best-effort sends:
- a **Telegram** message via the Bot API (`services/telegram.py`) if the guardian has a
  `telegram_chat_id`, and
- an **email** via Gmail SMTP with an App Password (`services/email.py`) if they have an email,

both containing the live tracking URL. In-app, the emergency screen itself shows the same link
and status. Delivery is best-effort and reported back in the start-SOS response so the UI can
show what succeeded.

## F6 - Evidence capture (NEW)

The emergency screen can capture a photo (`<input type="file" capture="environment">`) or a
short audio clip (`MediaRecorder`). Each file is uploaded as multipart form data to
`POST /api/sos/{id}/evidence`, hashed server-side with **SHA-256**, saved under
`data/evidence/{session_id}/`, and recorded with its hash, kind, capture location and timestamp
- so tampering after the fact is detectable.

## F7 - AI safety assistant

`POST /api/ai/ask` forwards the question (plus the user's approximate location, if granted) to
the **Gemini API** (`gemini-2.0-flash`) with a safety-focused system prompt, and returns the
answer. Requires `GEMINI_API_KEY` in `.env`.

## F8 - Roles and access

There's no separate guardian login: every authenticated endpoint filters by the JWT's
`user_id` (guardians, sessions, evidence all carry an `owner_id`/`user_id` foreign key and every
query checks it), so one user can never see another's data. Guardians reach a session only
through its unguessable per-session `share_token` - a read-only endpoint and a read-only
WebSocket, nothing else - which is this project's SQLite-compatible equivalent of the reference
system's Postgres Row Level Security.

## F9 - Installable PWA

`vite-plugin-pwa` generates a manifest (name, theme colour, standalone display, icons) and a
service worker, so a phone's Chrome "Add to Home screen" produces a full-screen, offline-capable
app shell.
