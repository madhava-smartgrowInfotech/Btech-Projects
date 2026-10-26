# SHEGUARD - REPORT FACTS

Single source of truth for every submission document. Every number below was measured on this machine in this run
(Oct 2026) by the scripts named in each section, or read from the product's own artefacts. Where something was not
measured, it says so.

## 1. Identity

- **Product:** SHEGUARD - *SHEGUARD: AI POWERED WOMEN'S SAFETY PLATFORM*. Batch CSDS-A-A7 (CSE - Data Science, Section A). Ports: API 8107, web 5107.
- **Students (batch file / Students.txt):** CH.AARTHI 23K91A6741 · D.PRANATHI 23K91A6748 · BALA VIGNESH 23K91A6717 · A.VISHAL 23K91A6704.
- **Guide:** "GUIDE NAME" is a placeholder in the batch file - kept as a placeholder. College, HOD, principal, academic year, designation: bracket placeholders.
- **Base paper (batch file):** K. Agrawal, A. Srivastava, K. Sharma, S. K. Satapathy, S.-B. Cho, S. Mishra, A. Chowdhury, A. Pal, "SafeRoutes: Charting a Secure Path - A Holistic Approach to Women's Safety Through Advanced Clustering and GPS Integration," IEEE Access, vol. 12, pp. 166368-166378, 2024, doi 10.1109/ACCESS.2024.3488784 (PDF: `Documentary/Base paper 2.pdf`, read in full).
- **Batch literature-survey list (5.LITERATURE SURVEY.docx):** [1] the base paper; [2] "The Role of IoT in Woman's Safety: A Systematic Literature Review", IEEE Access 2023 (PDF in `Documentary/Base paper_.pdf`: doi 10.1109/ACCESS.2023.3252903, read); [3] "A Mobile-Based Women Safety Application with Real-Time Emergency Alert and Location Tracking", Int. Scientific J. of Engineering and Management, 2026; [4] "Shake-to-Alert: An Automated Mobile Safety Application for Women with Emergency Notification via Motion Detection", ITIKD (2024 conference, listed 2025); [5] "Cross-Platform Women Safety Mobile Application with Real-Time Alert System and GPS Tracking", ICESIC 2026. Items 3-5 were not retrieved independently - cited as listed, never quoted for results.
- Also in `archived_base_papers/`: arXiv 2605.25806 (VAD models, 2026), an ESP32-camera women-safety paper, and the IRJMETS 2025 "SafeGuard Safe Route Recommendation System" (companion reference PDF, available to read).

## 2. What the abstract promises vs what the code does (state this plainly in the documents)

| Abstract / batch files say | The shipped code has |
|---|---|
| Flutter app | **React 19 + Vite + TypeScript + Tailwind 4 + Leaflet** web app, installable PWA (`vite-plugin-pwa`) |
| Supabase back end | **FastAPI 0.115 + SQLAlchemy 2 + SQLite** (`data/app.db`) |
| Role-based access with Postgres Row Level Security | **No RLS, no admin role.** One user role; every query filters on the JWT user id (`owner_id` / `user_id`); guardians have no account - they see a session only through an unguessable 32-hex `share_token` (read-only REST + WebSocket) |
| Safe Route guidance | OSRM route alternatives scored against a district-risk table (K-Means tiers) and a night multiplier. Real, with limits (section 6) |
| SafePhrase activation | Browser Web Speech API in continuous mode + a word-window matcher (`lib/safephrase.ts`); phrases are stored in the browser (localStorage) only, server just records `trigger = safephrase` |
| Smart SOS | **One-tap SOS button only.** No shake / power-button / fall detection, no automatic trigger; hold-3-seconds-to-cancel |
| Live location with guardians | `watchPosition` pushes to `POST /api/sos/{id}/location` about every 4 s; broadcast over `WS /ws/track/{share_token}` |
| Guardian alerts | Telegram Bot API + Gmail SMTP, **never exercised for real**: `TELEGRAM_BOT_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` are empty in `.env`, so every delivery reports "not sent" (see screenshot 12/13). Only the tracking link and the in-app status work end to end |
| Evidence: timestamps, location, audio, images | Photo (file input / camera) and audio (MediaRecorder) saved with timestamp, location, SHA-256 |
| AI assistant (Gemini API) | `POST /api/ai/ask` -> Gemini `generateContent`. **Could not be demonstrated returning an answer in this run**: the key hit its quota (HTTP 429), and earlier calls returned 503 / read timeouts (section 8) |

Other facts: area-risk "model" = K-Means (k=3) on **one feature** (average crimes per reporting year) - equivalent to two cut-offs (section 5). Data are 2001-2012 district counts.

## 3. Architecture and code size

React/Vite SPA (port 5107, proxies `/api` and `/ws`) <-> FastAPI (port 8107) <-> SQLite. External: OSRM public demo server (routing), Nominatim (place search + one-off district geocoding), Gemini API, Telegram Bot API, Gmail SMTP. Leaflet + OpenStreetMap tiles in the browser.

- Python: backend (`backend/app`) + `ml/` + `scripts/` + `tests/` = about 2,300 lines before the documentation scripts; backend alone 18 modules (routes: auth, guardians, risk, routes_plan, sos, evidence, track, ai, places, ws; services: osrm, risk, gemini, telegram, email, hashing).
- Frontend: 26 TS/TSX files, about 2,950 lines; 9 screens + public Track page.
- `npm run build` (`tsc --noEmit && vite build`): passes in ~3 s of Vite time; JS 449.7 kB (135.7 kB gzip), CSS 41.2 kB (7.8 kB gzip), hero image 1,086 kB, PWA precache 6 entries 480.8 KiB.
- Machine: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro, Python 3.11.9, Node 24.19.0, no GPU used (none needed).
- Versions: fastapi 0.115.6, uvicorn 0.32.1, SQLAlchemy 2.0.36, scikit-learn 1.5.2, pandas 2.2.3, numpy 2.1.3, httpx 0.28.1, PyJWT 2.10.1, bcrypt 4.2.1, websockets 14.1, joblib 1.4.2, pytest 9.1.1; React 19.0.1, Vite 6, Tailwind 4.1, Leaflet 1.9.4, TypeScript 5.8.

### Endpoints (all JSON unless noted)
| Method + path | Auth | Purpose |
|---|---|---|
| GET `/api/health` | none | liveness |
| POST `/api/auth/register`, `/api/auth/login` | none | bcrypt password, JWT HS256, 7-day expiry |
| GET `/api/auth/me` | JWT | profile |
| GET/POST `/api/guardians`, PUT/DELETE `/api/guardians/{id}` | JWT, owner-scoped | guardian CRUD (name, phone, email, telegram_chat_id) |
| GET `/api/risk/areas` | **public** | 467 district rows (state, district, lat, lng, crime_rate, risk_score, risk_tier) |
| POST `/api/routes/plan` | JWT | OSRM alternatives + risk score, sorted ascending, first = recommended |
| GET `/api/places/search?q=` | JWT | Nominatim search, India only, 5 results |
| POST `/api/sos/start` | JWT | creates session + `share_token`, alerts guardians, returns tracking URL + delivery report |
| POST `/api/sos/{id}/location`, `/cancel`; GET `/api/sos/{id}` | JWT, owner-scoped | stream / end / read a session |
| POST/GET `/api/sos/{id}/evidence` | JWT, owner-scoped | multipart upload (kind photo\|audio), SHA-256, list |
| GET `/api/track/{share_token}` | **public** | read-only session view: name, status, path, last position |
| WS `/ws/track/{share_token}` | token only | location / cancelled push to viewers |
| POST `/api/ai/ask` | JWT | question (+ optional lat/lng) -> Gemini |
| GET `/evidence-files/...` | **public static mount** | stored evidence files |

### Database (SQLite, 6 tables)
`users(id, name, email unique, password_hash, created_at)` · `guardians(id, owner_id -> users, name, phone, email, telegram_chat_id, created_at)` · `emergency_sessions(id, user_id -> users, share_token unique, status active|cancelled, trigger manual|safephrase, started_at, ended_at, last_lat, last_lng, last_update_at)` · `location_pings(id, session_id, lat, lng, ts)` · `evidence(id, session_id, kind photo|audio, file_path, sha256, lat, lng, captured_at)` · `district_risk(id, state, district, lat, lng, crime_rate, risk_score, risk_tier)`.

## 4. Datasets

| Item | Facts |
|---|---|
| District crimes file | Kaggle "Crime in India" (rajanand), CC0: `district_wise_crimes_against_women_2001_2012.csv`; 9,017 rows, 8,597 after dropping `TOTAL` roll-ups; 35 states/UTs; years 2001-2012; 827 (state, district) pairs; 7 crime columns (Rape, Kidnapping and Abduction, Dowry Deaths, Assault on women with intent to outrage her modesty, Insult to modesty of Women, Cruelty by Husband or his Relatives, Importation of Girls) |
| State-year file | Kaggle "Crimes against women in India 2001-2021" (balajivaraprasad), CC0: 736 rows, 70 state labels, 2001-2021; **not used by any feature** (only mentioned as available) |
| District coordinates | Nominatim (OpenStreetMap, ODbL), `data/districts_geocoded.csv`: **467 of 827 pairs (56.5 %)** geocoded; the rest dropped, not guessed |
| Feature | `crime_rate` = (sum of the 7 columns over all years) / (years reported); districts reported 1-12 years (638 of 827 reported all 12; 34 reported 1 year); geocoded districts average 11.71 years |
| Train / test split | **None** - unsupervised clustering fitted on all 467 points; there is no labelled ground truth and no held-out set |
| Crime mix (counted crimes, all districts) | Cruelty by husband/relatives 40.0 %, assault on modesty 25.8 %, rape 13.0 %, kidnapping 11.7 %, insult to modesty 5.3 %, dowry deaths 4.2 % - so the "risk" is dominated by domestic-violence counts, which say little about street safety |
| Geocode sanity | 0 points outside India's bounding box; 2 districts share identical coordinates (466 distinct points) |
| Coverage gaps | **No geocoded district at all for Uttar Pradesh (77 districts), West Bengal (30), Delhi (24), Uttarakhand (13), Tripura (10), A&N Islands, Puducherry, Daman & Diu, Lakshadweep, Chandigarh, D&N Haveli** (11 of 35 states/UTs) |

## 5. Area-risk model (scripts: `ml/train_risk_model.py`, `ml/eval.py`, `scripts/run_experiments.py` -> `experiments/study/metrics.json`)

- StandardScaler + K-Means (k=3, `random_state=42`, `n_init=10`) on `crime_rate`; clusters named low/medium/high by mean crime rate; `risk_score` = min-max of crime_rate to 0-100.
- **Shipped metrics (re-run reproduced exactly):** silhouette 0.5798, Davies-Bouldin 0.531, Calinski-Harabasz 1155.4 (new); tiers low 278 / medium 148 / high 41; mean crimes/year 97.76 / 327.92 / 720.93. `district_risk.csv` agrees with the re-run on 100 % of districts; `risk_model.joblib` loads.
- **Tier ranges (crimes per year):** low 0-212.0, medium 215.5-522.0, high 537.67-1191.58. The tiers are exactly two thresholds on one number (cut-offs 213.75 and 529.83, 100 % agreement with K-Means): the "model" is a data-driven pair of cut-offs, not a multi-feature classifier.
- **k sweep (silhouette / Davies-Bouldin):** k=2 0.662 / 0.551; **k=3 0.580 / 0.531**; k=4 0.596 / 0.493; k=5 0.560 / 0.518; k=6 0.562 / 0.540; k=7 0.556 / 0.538; k=8 0.553 / 0.502. k=3 is a design choice (three tiers for the UI), not the metric optimum: k=2 has the highest silhouette, k=4 beats k=3 on both indices.
- **Stability (30 single-init K-Means runs):** adjusted Rand index vs shipped min 0.659, mean 0.790; silhouette 0.575-0.581. So assignments of districts near the cut-offs move with the initialisation.
- **Alternative tierings vs K-Means:** Ward agglomerative 83.3 % agreement (ARI 0.603; 231/164/72); Gaussian mixture 72.6 % (ARI 0.367; 181/214/72); equal-count terciles 49.3 %; fixed 100/300 cut-offs 54.6 %. The 41-district "high" tier is a method-dependent choice.
- **Who is "high risk":** West Godavari 1191.6, Vijayawada 1059.0 (5 reported years), Guntur 1032.5, Jaipur 1001.4 (5 yrs), Krishna 895.2, Khammam 876.5, Indore 866.0, Mumbai 850.2 (5 yrs), Nagaon 849.2, Kurnool 820.8. High tier by state: Andhra Pradesh 12, Rajasthan 11, Kerala 4, Madhya Pradesh 4, Assam 3, Maharashtra 3, Chhattisgarh 2, Haryana 1. The feature is a **raw count, not a rate per population**, so populous and well-reporting districts rank high (base paper uses population and per-capita data).
- Not measured: any correlation with real incidents on streets, population-normalised risk, or validation by users. Silhouette measures only cluster separation on one number.

## 6. Safe-route scoring (code: `backend/app/services/risk.py`; experiment: 16 real OSRM city pairs, cached `experiments/study/osrm_cache.json`)

- Every 8th polyline point -> nearest district by haversine over all 467 -> tier weight low 1.0 / medium 2.5 / high 5.0 -> mean; night (UTC hour >= 15, i.e. about 20:30-05:30 IST) multiplies by 1.6.
- Unit sanity (ml/eval.py): route entirely in high-risk districts 5.0 vs low-risk 1.0 - passes. Day score 2.5 -> night 4.0 for the same route (ratio 1.6).
- **Night multiplier never changes the ranking**: it scales every route by the same 1.6 - 16 of 16 pairs have identical day/night order. It changes the displayed number and label only.
- 16 pairs routed: 10 returned 2 alternatives, 6 returned 1 (so for 37.5 % of trips there is nothing to choose between). Recommended route = the OSRM fastest in 11 of 16; when there were alternatives the safest pick cost on average +3.7 min.
- Sensitivity: alternative tier weights (1/2/3, 1/3/9) changed the recommended route in 0 of 10 multi-route pairs; changing the sampling step (1, 4, 16, 32) changed it in 1 of 10.
- **Coverage problem:** nearest-district distance from 40 Indian city centres: median 8.1 km but max 231.3 km; 7 cities are >100 km from any district - **Hyderabad 149.0 km, Secunderabad 147.3, Warangal 195.0, Kolkata 190.7, Lucknow 231.3, Kanpur 164.3, Varanasi 113.4**; Delhi 24.1, Dehradun 70.4, Madurai 63.0, Agra 54.0. Along the 16 test routes the mean nearest-district distance was 61.9 km (max 231.3). `nearest_district` has no distance limit, so a route through Lucknow is scored with a district hundreds of km away.
- Route-level labels in the UI (LOW / MODERATE / HIGH) come from the share of sampled points per tier (HIGH if >= 20 % of samples are high-tier). Delhi -> Jaipur shows both alternatives as HIGH risk (33/25/42 % and 19/5/76 % low/medium/high); Hyderabad -> Vijayawada one route, HIGH (20/0/80 %).
- Cost: scoring one route ≈ 305 ms (pure-Python loop 467 x ~N samples); live `POST /api/routes/plan` 1.6 s mean (1.6 s median, 5 calls) including the OSRM call.
- Demo-server dependence: OSRM public demo and Nominatim are rate-limited free services with no SLA.

## 7. API measurements (script `scripts/measure_api.py` -> `experiments/study/api_metrics.json`; 127.0.0.1, one client, sequential)

| Endpoint | n | mean ms | median ms | p95 ms |
|---|---|---|---|---|
| GET /api/health | 30 | 2.3 | 2.1 | 4.1 |
| GET /api/risk/areas (467 rows) | 30 | 36.2 | 31.1 | 81.3 |
| POST /api/auth/login (bcrypt) | 15 | 285.2 | 279.0 | 314.6 |
| GET /api/auth/me | 30 | 5.1 | 4.9 | 6.7 |
| POST /api/guardians | 30 | 11.0 | 10.9 | 13.3 |
| GET /api/guardians | 30 | 7.3 | 6.9 | 10.8 |
| POST /api/sos/start (30 guardians, no channel configured) | 15 | 50.7 | 34.2 | 137.4 |
| POST /api/sos/{id}/location | 30 | 15.3 | 14.7 | 20.4 |
| GET /api/track/{token} | 30 | 9.4 | 8.3 | 15.3 |
| POST evidence 100 KB / 1 MB / 5 MB | 10 each | 15.0 / 19.1 / 68.2 | 13.3 / 18.4 / 61.0 | 24.0 / 23.8 / 117.9 |
| GET /api/sos/{id}/evidence | 30 | 9.6 | 8.7 | 15.3 |
| POST /api/routes/plan (live OSRM) | 5 | 1628.6 | 1591.1 | 2001.5 |

- **WebSocket push delay** (POST location -> guardian receives frame): 1 viewer mean 15.4 ms (median 13.2, p95 17.2, max 77.1), 5 viewers mean 14.6 ms (p95 18.8), 30 trials each.
- **Alert delivery to guardians was never measured** (no Telegram / Gmail credentials); `sos/start` latency above excludes any real network send. With real channels the request waits for each guardian's Telegram call and SMTP send in sequence (10 s timeout each) before replying, and `send_email` is a blocking `smtplib` call inside an `async` route, so it stalls the whole server's event loop while it runs - read from the code, not measured.
- SHA-256 of 1 MB: about 1.05 ms.

## 8. Tests and security probes

- **pytest (`tests/`, new this run): 51 passed, 6 xfailed (strict), 0 failed in ~18 s** (57 tests; offline, throw-away SQLite, OSRM / Gemini / Telegram / Gmail stubbed). Covers: auth (register, duplicate, validation, bcrypt hash, expired/forged token), guardian CRUD and isolation, 467-district table and tier counts, route planning (sort, 404, 502), SOS lifecycle and alert fan-out, location trail, cancel, WebSocket push, evidence hashing and tamper, AI endpoint, scorer unit tests (haversine, tier weights, night factor, window boundaries, empty route, no-district fallback, no distance limit), model artefact checks.
- The 6 **expected failures document real defects**: (1) Gemini timeout (`httpx.ReadTimeout`) is uncaught -> HTTP 500 instead of 502 (seen live: first two assistant calls returned 500 after 20 s); (2) latitude 999 accepted; (3) `trigger` accepts any string; (4) WebSocket accepts any token including one matching no session; (5) no upload size limit (20 MB "audio" accepted in 0.24 s); (6) an `.html` upload labelled photo is served back as `text/html` from the API origin.
- Earlier `scripts/smoke_test.py`: 12 live steps pass; Gemini step warns (500 on this run).
- **Live access-control probes (`measure_api.py`):** no token -> 401 on guardians / sos / ai / routes; forged or tampered JWT -> 401; user B on user A's session: read, location push, cancel, evidence list, evidence upload -> all 404; B editing/deleting A's guardian -> 404, B's own guardian list stays empty; wrong tracking token 404, right token 200; `/api/risk/areas` public 200.
- **Findings:** stored evidence is retrievable **without any token** at `/evidence-files/{session_id}/{sha-prefix}.{ext}` (200); file name needs the 16-hex hash prefix so it is unguessable by session id alone (404 for a guessed name) but anyone with a link has it; no login lockout (25 consecutive wrong passwords all return 401, none 429); password rule is only min 6 chars ("aaaaaa" accepted); track page keeps showing the full location trail after the session is cancelled (no expiry, although the 404 text says "expired"); `location push after cancel` -> 400 (correct); CORS is `*`; JWT secret is **not** the default (set in `.env`); `.env` is tracked by git in this repo (do not commit).
- **Evidence integrity:** hash is computed server-side at upload; recomputing from the stored file matches; flipping one bit changes the hash. There is **no verify endpoint** and the hash sits in the same database as the file path - it detects tampering only if someone recomputes and compares.
- Not tested: real alert delivery, real device GPS / battery / camera / speech accuracy, load / concurrency beyond 5 WebSocket viewers, iOS Safari, a screen reader, a real phone over the tunnel, penetration testing.

- UI wording: the emergency screen's call button reads "Call 911 (emergency services)" while other screens say "112 / 911"; India's national emergency number is 112 (a small localisation defect, visible in screenshots 12/13/15).

## 9. SafePhrase matcher (script `scripts/safephrase_eval.mjs` -> `experiments/study/safephrase.json`)

The product's own TypeScript (`frontend/src/lib/safephrase.ts`) is transpiled and run unchanged on **written** transcripts - 24 positives (2 phrases x exact / embedded in sentence / one word dropped / one word misheard / reordered) and 40 ordinary sentences checked against both phrases (80 negative checks). **No audio, no recogniser** - recogniser accuracy was not measured.

| Sensitivity (word share needed) | Recall on 24 positives | False triggers on 80 negative checks |
|---|---|---|
| Low (100 %) | 13/24 = 54.2 % | 0 |
| Medium (85 %, the default) | 13/24 = 54.2 % | 0 |
| High (75 %) | 18/24 = 75.0 % | 0 |
| Ultra (60 %) | 24/24 = 100 % | 8/80 = 10.0 % (e.g. "can you help me with my homework", "tell me about sheguard") |

- Exact and embedded phrases always trigger (10/10 at every level); words in any order inside the window also trigger. For the three-word default phrase, Medium behaves exactly like Low (2 of 3 words = 0.67 < 0.85), so a single misrecognised word blocks the alert. Match cost 1.5 microseconds.
- The matcher is the only part of SafePhrase tested; whether Chrome's recogniser hears "sheguard" correctly is unknown. The Web Speech API streams audio to the browser vendor's service and needs a Chrome/Edge tab open in the foreground; the page cannot listen with the screen off.

## 10. AI assistant (script `scripts/assistant_eval.py` -> `experiments/study/assistant.json`)

- Design: one fixed system prompt (safety scope, "if an active emergency, first line must tell the user to use SOS or call local emergency services", under 150 words), temperature 0.4, max 400 output tokens, model from `GEMINI_MODEL` (default `gemini-flash-latest`), location passed as text if granted. No conversation memory (each question is a separate call), no output filtering, no logging.
- **Result of this run: 0 of 10 probe prompts answered.** All 10 returned HTTP 502 with Google error 429 "You exceeded your current quota"; earlier in the same run calls returned 500 (20.3 s read timeout, uncaught) and 502 with Google 503 "This model is currently experiencing high demand". So the claim "emergency first line", answer length and quality were **not measured**. The UI shows the friendly message "The AI assistant is unavailable right now" (screenshots 07, 08, 09). The `/api/ai/ask` plumbing is covered by stubbed tests only.

## 11. Screenshots (`docs/screenshots/`, 1440x900, Chrome via Playwright, `scripts/capture_screenshots.py`)

Real captures of the running app with real data: a freshly registered account (through the UI), three guardians added through the form, real OSRM routes and Nominatim search, real SOS session with live position updates (Playwright sets the browser's geolocation: Delhi then Hyderabad city centres), an evidence photo (one of the app's own screenshots) and a 3-second audio clip from Chrome's fake microphone (a test tone), the guardian's page in a second logged-out browser context, hold-to-cancel. Limits: the position is injected, not a phone's GPS; the audio is a test tone; alert channels are unconfigured; AI assistant answered with the unavailable message.

| File | Shows |
|---|---|
| 01_landing | landing page, signed out |
| 02_register | registration form filled in |
| 03_profile_guardians | profile with three guardians |
| 04_dashboard | dashboard: SOS button, status tiles (3 guardians, area risk "Medium - GURGAON" at the Delhi position), SafePhrase tile |
| 05_route_search | destination search suggestions (Nominatim) |
| 06_route_delhi_jaipur | Delhi -> Jaipur: two OSRM alternatives, both HIGH risk, 274.1 km / 204 min and 299.5 km / 205 min, risk heat circles |
| 07_route_details | route cards and the (unavailable) AI tips panel |
| 08_route_hyderabad_vijayawada | Hyderabad -> Vijayawada, 269.1 km / 213 min, HIGH risk (20 / 0 / 80 %) |
| 09_ai_assistant | assistant chat: question sent, "unavailable" reply |
| 10_safephrase / 11_safephrase_added | SafePhrase settings, fingerprint, sensitivity; second phrase added |
| 12_emergency_started | emergency screen: tracking link, 0 of 3 guardians reached (no channel configured), live map |
| 13_emergency_evidence | photo and audio saved with SHA-256, path so far |
| 14_guardian_tracking | guardian's live page, no login |
| 15_hold_to_cancel | hold-to-cancel ring at about half |
| 16_dashboard_after_sos | dashboard after cancelling, recent activity logged |
| 17_guardian_cancelled | guardian's page after the user confirmed safe |
| 18_profile_activity | profile with guardians and activity |

## 12. Comparison with the base paper (state plainly: not like for like)

- Base paper (read in full): multi-source data from data.gov.in (2001 and 2011 district population, IPC 2013 crimes against women, literacy, per-capita expenditure, police strength 2013, forest cover) -> imputation, scaling, correlation (Pearson, Spearman), K-Means and Gaussian mixture, 3-4 clusters, "dummy data from globally safest cities" as a scoring reference; cab-service integration with a 1.96x safety buffer and deviation alerts (designed, **not implemented or evaluated**; the paper's results are "anticipated" and contain correlation matrices and cluster-selection tables, no accuracy figures).
- Its cluster-selection tables (multi-feature data; number of districts not stated): silhouette 0.440 (k=2), 0.416 (k=3); Calinski-Harabasz 264.7 (k=2), 221.0 (k=3), 222.7 (k=4); Davies-Bouldin 1.021 (k=2), **0.970 (k=3)**, 1.011 (k=4); explained variance column falls with k. (Its Fig. 11 plots silhouette values near 0.25-0.31, which differ from Table 3; the paper's own tables are quoted here as printed.)
- SHEGUARD at k=3: silhouette 0.580, Davies-Bouldin 0.531, Calinski-Harabasz 1155.4 on **one** feature and 467 points - **not comparable** (different data, feature count and size; indices on a 1-D count are inherently higher); no claim of being better.
- What SHEGUARD adds beyond the base paper: SafePhrase, one-tap SOS, live guardian tracking by link, SHA-256 evidence, assistant, PWA, and a running implementation. What it lacks versus the base paper: population/per-capita normalisation, police-presence and socio-economic features, GMM comparison and cluster-selection analysis in the product, cab-vendor deviation alerts.

## 13. Objectives vs outcomes (from `6.OBJECTIVES&PROBLEM STATEMENT.docx`)

1. Safe route guidance - **partly achieved**: working, but built on 2001-2012 district counts with 56 % geocoding, no coverage for several big cities, and a night factor that never reorders routes.
2. Quick activation (SafePhrase + Smart SOS) - **partly**: one-tap SOS and hold-to-cancel work; SafePhrase matcher tested on written transcripts only; no shake/automatic trigger.
3. Live location to guardians - **achieved** (WebSocket push ~15 ms locally; no login for guardians); delivery of the link by Telegram/email unverified.
4. Evidence preserved securely - **partly**: timestamped, located, SHA-256 hashed; but files are publicly retrievable by URL, no size cap, no verification endpoint.
5. AI assistance with Gemini - **implemented, not demonstrated** in this run (quota 429).
6. Protect data with role-based access and RLS - **partly**: owner-scoped queries (probes pass), bcrypt + JWT; no RLS (SQLite) and no roles beyond user.

## 14. Honest limitations to repeat in the documents

Synthetic-free but old and coarse data (2001-2012, district level, counts not rates, 56 % geocoded); one-feature clustering without ground truth, validation or a held-out set; no field trial, no real-device test; delivery channels and Gemini unverified live; SQLite single-file database, no migrations, no rate limiting; demo OSRM / Nominatim servers; browser-only (no native Flutter app); SafePhrase needs an open Chrome/Edge tab and online speech recognition.
