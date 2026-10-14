# Frontend plan - PhishGuard (CSDS-A-A3)

**Design variant:** V3 - Depth Studio · **Ports:** backend 8103, frontend 5103

The existing interface is a Flask app with templates kept as Python strings (`phishguard/webapp.py`).
It stays untouched and still works (`python run.py serve`). The new React app lives in `frontend/`.
Because the Flask app already has a JSON API, the "thin layer" in `backend/server.py` simply calls the
existing `create_app()` factory and adds a few **additive, read-only** JSON endpoints plus CORS, then serves
on port 8103. No file in `phishguard/` changes.

---

## 1. Endpoint inventory (existing, `phishguard/webapp.py`)

### JSON API
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/check?url=<url>` | query `url` | `{url, normalized_url, verdict: phishing\|suspicious\|safe\|unknown, probability, ml_probability, decided_by: ml\|community\|none, reason, red_flags[], features{47}, model, model_version, community: null\|{status, phishing_votes, safe_votes, source, last_updated}}` · 400 `{error}` on empty/invalid URL. Logs the check. |
| POST | `/api/report` | JSON `{url, verdict: phishing\|safe, reporter?, note?}` | intel entry `{url_norm, url, phishing_votes, safe_votes, status, source, first_seen, last_updated, used_in_training}` · 400 `{error}`. May trigger auto-retrain. |
| GET | `/api/stats` | - | `{threat_intel: {reports, urls_tracked, confirmed_phishing, confirmed_safe, pending, checks, awaiting_training}, metrics: <metrics.json>, retraining: bool}` |
| POST | `/api/retrain` | - | blocking retrain; returns the new metrics summary (or `{skipped, reason}`) |
| POST | `/api/sync` | - | `{openphish: {ok, added}\|{ok:false, error}, urlhaus: {...}}` |

`metrics` shape: `{model_version, trained_at, best_model, n_features, train_rows, test_rows, crowd_rows?, crowd_weight?, models: {random_forest|xgboost|logistic_regression: {accuracy, precision, recall, f1, roc_auc, false_positive_rate, confusion_matrix{tn,fp,fn,tp}, train_seconds, top_features[{feature, importance}]}}}`

### HTML routes (old UI, kept)
| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/` | check a URL, KPIs, recent 12 checks |
| GET/POST | `/report` | report form; POST redirects to the check of that URL |
| GET | `/community` | threat-intel board (200 entries) |
| GET | `/models` | model comparison |
| POST | `/retrain` | starts a **background** retrain, sets `retraining` flag seen in `/api/stats` |
| POST | `/sync` | feed sync, then auto-retrain check, redirect with message |

### Added in `backend/server.py` (additive, read-only - marked NEW)
| Method | Path | Wraps |
|---|---|---|
| GET | `/api/checks?limit=` | `ThreatIntel.recent_checks()` - recent check log (old UI showed it server-rendered) |
| GET | `/api/intel?limit=&status=` | `ThreatIntel.recent()` - community board entries |
| GET | `/api/intel/lookup?url=` | `ThreatIntel.lookup()` - one entry with its last 10 reports |
| GET | `/api/config` | thresholds from `config.py` + feature names grouped lexical/structural/domain |
| GET | `/api/health` | `{ok, model_ready}` |

The React app reuses the existing `POST /retrain` (background) and polls `GET /api/stats` for the
`retraining` flag, exactly like the old Models page. Feed sync uses `POST /api/sync` (JSON outcome).

---

## 2. Feature inventory (existing UI) - all verified in the React UI on 2026-10-14

**Check URL (`/`)**
- [x] F1 URL input + Check; prefill from `?url=`
- [x] F2 Verdict card: Phishing / Suspicious / Looks safe / Unknown, normalized URL, reason
- [x] F3 Probability meter, decided-by tag, raw model score
- [x] F4 Red-flag list
- [x] F5 "Report as phishing" / "Report as safe" shortcuts (prefill report form)
- [x] F6 Extracted features table (47)
- [x] F7 KPIs: URLs checked, confirmed phishing, community reports, F1 of active model
- [x] F8 Recent checks table (click to re-check)
- [x] F9 Error message when a URL cannot be checked

**Report (`/report`)**
- [x] F10 Form: URL, verdict (phishing / safe-false-positive), reporter, note; prefill from query
- [x] F11 Consensus threshold explained
- [x] F12 After submit, go to the check result for that URL; validation errors shown
- [x] F13 Auto-retrain after N new confirmations (backend)

**Threat intelligence (`/community`)**
- [x] F14 KPIs: tracked, confirmed phishing, confirmed safe, pending; awaiting-training + auto-retrain count
- [x] F15 Sync public feeds (OpenPhish, URLhaus) with per-feed outcome message
- [x] F16 Entries table: URL, status, phishing votes, safe votes, source, updated; empty state
- [x] F17 Row actions: check URL, +phish, +safe (prefilled report)

**Models (`/models`)**
- [x] F18 Comparison table: accuracy, precision, recall, F1, ROC-AUC, FPR, train time; best highlighted
- [x] F19 Training meta: features, train/test rows, crowd rows x weight, best model, version, trained-at
- [x] F20 Per-model confusion matrix + top-10 feature importances
- [x] F21 Retrain now (background) with confirmed / not-yet-used counts; message
- [x] F22 Not-trained empty state

**Global**
- [x] F23 Navigation between the four screens
- [x] F24 Footer: active model + version

---

## 3. Screen map (React, `frontend/`)

| Route | Screen | Covers | Notes |
|---|---|---|---|
| `/` | **Landing** | - | NEW: 3D hero, pinned how-it-works (3 stages), feature grid, live stats strip from `/api/stats`, CTA, footer |
| `/app` | redirect → `/app/check` | | |
| `/app/check` | **Check URL** | F1-F9, F7, F8 | gauge, red flags, community panel, feature table grouped by lexical / structural / domain (NEW grouping), quick sample URLs from the README |
| `/app/report` | **Report** | F10-F13 | Stepper (URL → verdict → details), shows current community tally for the URL via `/api/intel/lookup` (NEW) |
| `/app/intel` | **Threat intelligence** | F14-F17 | sortable/paginated table, status filter + search (NEW), detail drawer with report history (NEW), sync modal |
| `/app/models` | **Models** | F18-F22 | metric chart (NEW), confusion matrices, feature importance bars, retrain with live status polling |
| `/app/activity` | **Activity** | F8 (expanded) | NEW: full recent-check log (200), verdict mix chart, decided-by split |
| `*` | Not found | | NEW |

App shell: sidebar (drawer below 900px) + topbar (theme toggle, model badge, retraining indicator) - F23, F24.

**Defaults chosen:** product name stays **PhishGuard** (the backend's name); dark theme is the default identity,
light theme available and persisted; old Flask UI untouched on its own port when run with `run.py serve`.

---

## 4. Verification log (2026-10-14)

Automated browser walks (Playwright/Chromium) against the real API on 8103:

| Run | Result |
|---|---|
| 1440px dark, dev server | 31/31 checks pass, console + network clean |
| 768px light, dev server | all checks pass, console clean |
| 360px dark, dev server | all checks pass (mobile drawer nav, table → cards), no horizontal scroll |
| 1440px dark, production build (`vite preview`) | 31/31 pass, no 404s on assets |
| `prefers-reduced-motion` | static gradient image instead of the WebGL canvas, Lenis off, pinned section becomes CSS sticky |
| WebGL disabled | static gradient image, no page errors |
| Retrain (real) | started from Models → topbar "Retraining" badge → backend finished, model version bumped; completion toast verified with a mocked stats sequence (the real run took 4-12 min on this machine) |
| Feed sync (real) | OpenPhish +300, URLhaus +500 shown per feed |
| `python tests.py` | all tests passed (original Flask UI untouched) |
| `python scripts/smoke_test.py` | passed |

Flows covered: single check (+ deep link), red flags, feature groups, report ×2 → community verdict overrides the
model, report validation, threat-intel table / filter / search / drawer with report history, Escape closes
overlays, modal focus trap, models charts + confusion matrices, activity log, batch check from an uploaded file,
theme toggle persisted across reload, 404.

After testing, the trained models were restored from a backup and the test `data/threat_intel.db` was deleted.
