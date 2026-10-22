# Frontend plan - VeriVision AI (CSE-C-C14)

Design: **V4 Soft Pastel Calm** (kit copied into `frontend/src`). Ports: backend **8414**, frontend **5414**.
Stack: Vite + React (JavaScript), React Router, kit components. The Flask backend stays as it is.

> Layout note: `FRONTEND_PROMPT.md` says the code lives in `8.ProjectCode/VeriVision-AI/`. It does not - the
> backend (`app/`, `run.py`, `run.bat`) is directly in `8.ProjectCode/`. `frontend/` is created beside `app/`
> and `run.bat` is kept at the top.

## 1. Backend endpoint inventory (as found)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | - | HTML (upload page) |
| GET | `/health` | - | JSON `{status: "ok"\|"degraded", models_loaded, device, error}`; 200 / 503 |
| POST | `/predict` | multipart `image` | HTML result page (400 / 413 / 500 / 503 render `error.html`) |
| POST | `/api/predict` | multipart `image` | JSON `{predicted_label, prob_real, prob_fake, confidence, confidence_word, branch_labels{a1,a2,b,c}, agreement_count}`; errors `{error}` 400 / 500 / 503 |
| GET | `/insights` | - | HTML (metrics page, "unavailable" state when no evaluation artifacts) |
| GET | `/artifacts/confusion_matrix.png` | - | PNG, or 404 `{error}` |
| (static) | `/static/css/style.css`, `/static/js/main.js` | - | old server-rendered UI assets |

Data the old HTML pages receive but **no JSON endpoint returns** (so the React app cannot show it today):
branch table, Grad-CAM overlays, robustness outcomes, active weights, gate reasons, original image, device,
and the three metrics files (`ensemble_metrics.json`, `model_metrics.json`, `robustness_metrics.json`).

### Additive endpoints I will add (thin, no change to existing routes or logic)

| Method | Path | Returns |
|---|---|---|
| POST | `/api/analyze` | JSON of the exact dict `_run_analysis()` already builds for `/predict` (filename, original_image data-URL, verdict, confidence, branches, cams, robustness, gates, weights, device). Same validation + error mapping, but JSON errors `{error}`. |
| GET | `/api/insights` | `{available, ensemble, models, robustness, confusion_exists}` read from `artifacts/metrics/*.json` |
| GET | `/api/config` | `{max_mb, allowed_extensions, ensemble_weights, branches[{key,name,backbone,resolution,loss}], gates{tau_b,tau_c,correction}, confidence_thresholds, model_metadata}` read-only from `app/config.py` and `models/model_metadata.json` |

The Vite dev server proxies `/api`, `/health`, `/artifacts` to `127.0.0.1:8414`, so no CORS change is needed.

## 2. Feature inventory (everything the product already does)

README / templates / routes, each of these must still work in the new UI:

- [x] F1  Upload an image (drag & drop or browse), PNG / JPG / JPEG / WEBP, max size from config (10 MB), preview + file name/size
- [x] F2  Client + server validation messages (unsupported type, empty, too large, corrupt, models missing)
- [x] F3  Loading state while 4 models + Grad-CAM + robustness run (can take up to a minute on CPU)
- [x] F4  Verdict: REAL / AI-GENERATED with confidence % and word (High / Moderate / Low), REAL vs AI-GENERATED probability split, original image
- [x] F5  Ensemble facts: branches agreeing (n/4), device used
- [x] F6  Gate 1 "route adjustment" note and Gate 2 "consensus adjustment" note when they apply
- [x] F7  Branch votes table: model, prediction, confidence (EfficientNet A1, A2, ResNet50, MobileNetV3) + final fusion weights
- [x] F8  Robustness check: original / JPEG / resize / blur outcomes + consistency score + caution text
- [x] F9  Grad-CAM visual explanation with a branch selector (EfficientNet / ResNet50 / MobileNetV3) + "explanation aid, not proof" note
- [x] F10 "Analyze another image" flow
- [x] F11 Model Insights: ensemble accuracy / precision / recall / F1 / ROC-AUC / balanced accuracy / test samples
- [x] F12 Confusion matrix (image) and dataset + seed caption
- [x] F13 Per-model comparison table (Acc / F1 / AUC)
- [x] F14 Robustness table for the ensemble under JPEG / resize / blur / noise (clean vs degraded)
- [x] F15 "Evaluation unavailable until training is completed" state
- [x] F16 API health: status, models loaded, device, error
- [x] F17 Marketing copy: 4-model ensemble, Grad-CAM, runs locally, privacy note, limitations / disclaimer footer
- [x] F18 Error page ("We couldn't complete that request") with way back
- [x] F19 `POST /api/predict` JSON contract unchanged (smoke test checks it)
- [x] F20 Old server-rendered pages (`/`, `/predict`, `/insights`) still respond

## 3. Screen map (as built)

| # | Route | Screen | Features | Data source |
|---|---|---|---|---|
| 1 | `/` | **Landing** (own header): pastel hero with the live ensemble card, capability marquee, how-it-works steps, feature cards, measured numbers (count-up), limitations, CTA | F17 | `/api/config`, `/api/insights` |
| 2 | `/login` | **Sign in** with a built-in **demo account** (`demo@verivision.ai` / `Demo@1234`, "Use demo account" button) - added because the product had no login | - | `POST /api/auth/login`, `GET /api/auth/me` |
| 3 | `/app` | **Analyze**: FileDrop + preview, client validation (type / size), indeterminate progress with elapsed timer + cancel, error state with retry | F1 F2 F3 F10 | `POST /api/analyze` |
| 4 | `/app` (result view) | **Result**: verdict hero, probability bar, agreement + device, gate notes, branch-vote table with final weights, robustness table + consistency, Grad-CAM tabs (EfficientNet / ResNet50 / MobileNetV3), fusion details | F4-F10 | response of `/api/analyze` |
| 5 | `/app/insights` | **Model insights**: 6 KPI cards, demo-data notice, confusion matrix (counts + rendered figure), clean-vs-degraded chart, per-model table + grouped bars, "unavailable" state | F11-F15 | `/api/insights`, `/artifacts/confusion_matrix.png` |
| 6 | `/app/models` | **How it works**: four route cards, fusion-weight chart, pixel-to-verdict timeline with the gate parameters, privacy, limitations | F17 | `/api/config` |
| 7 | `/app/status` | **System status**: API / models / device cards, raw health response, upload rules, re-check | F16 | `/health`, `/api/config` |
| 8 | `*` | **Not found** | F18 | - |

Shell: kit `AppShell` adapted (sidebar, topbar with status pill + theme toggle + sign-out, mobile bottom bar + drawer).
The Flask pages `/`, `/predict`, `/insights` on port 8414 are untouched (F20).

## 4. Ports / run (done)

- No `.env` exists today. Add `.env` + `.env.example` with `VERIVISION_PORT=8414`, `FRONTEND_PORT=5414`;
  `run.py` reads `.env`; `config.py` default port becomes 8414; `run.bat` also installs/starts the frontend.
- Old Flask pages keep working on 8414.

## 5. Verification (Step 4)

| Check | Result |
|---|---|
| `npm run build` | passes, no warnings except the kit's 570 kB main chunk (all screens lazy-loaded) |
| `python -m pytest tests` | 19 passed (11 original + 8 new for the JSON API) |
| `python scripts/smoke_test.py` | 29 checks passed: health, config, insights, wrong/valid login, 401 without token, analyze fake + real image (branches, weights, 3 Grad-CAMs, robustness), 3 validation errors, unchanged `/api/predict` + classic pages, Vite proxy |
| Walk every screen (`scripts/capture_screens.py`) | all screens reached with real data from a real analysis; **console clean, no failed requests** |
| UI state checks | protected route -> `/login`, garbage token, wrong password, unsupported + oversize file, offline API (error + retry), server 500 message, 401 mid-analysis -> sign-in, insights unavailable + insights API failure, degraded `/health`, skip link, 3px focus outline, reduced-motion, dark-mode persistence, sign-out - all pass |
| Responsive | 360 / 768 / 1440 px x light / dark on all 8 screens: no horizontal overflow, drawer opens and closes with Escape |
| `run.bat` | creates nothing new when `.venv` exists, copies `.env`, starts API (8414) + web app (5414), opens the browser; falls back to the classic page without Node |
| Screenshots | 16 PNGs in `docs/screenshots/` (landing light + dark, login, analyze empty/ready/running, result x4, insights light + dark, models, status, landing sections) |

Feature checklist above (F1-F20) is ticked: each one was exercised by the smoke test or the browser walk.

## 6. Decisions and things worth knowing

- **Demo login** (new): `POST /api/auth/login` issues a signed, 12-hour bearer token (itsdangerous, no new dependency).
  Only `/api/analyze` requires it; `/api/predict`, `/api/config`, `/api/insights` and the classic pages stay open.
  Credentials come from `.env` (`VERIVISION_DEMO_EMAIL` / `VERIVISION_DEMO_PASSWORD`); `/api/config` returns them so the
  login page can offer a one-click demo button - fine for a local demo, change it before any real deployment.
- **Backend changes** are additive only: `app/api.py` (new blueprint), three config constants, one JSON branch in the 413 handler,
  default port 5000 -> 8414, and `.env` support in `run.py`. No existing route, response or inference logic changed.
- **`requirements.txt`** pinned `numpy==2.5.2`, which does not exist, so `run.bat` could not install. Re-pinned to the versions
  that were installed and tested together (numpy 2.4.6, torch 2.14.1, ...).
- **Docker** keeps serving the classic pages on 5000 (`ENV VERIVISION_PORT=5000` added); it does not include the React app.
- **Metrics are demo-data metrics.** The shipped models were trained on synthetic fallback data (100% on clean test, 49.5% after
  a 2x resample). Insights and Landing say so; nothing in the UI is hard-coded - every number comes from the API.
- **Kit gaps filled in the copy** (kit untouched): `lib/api.js`, `lib/palette.js`, `lib/auth.jsx`, `components/reactbits/Blobs.jsx`;
  `Layout.jsx` rewritten for this product; one CSS selector fixed (`.stats-strip .s > span`) so count-up numbers keep their size.
- The API sorts JSON keys alphabetically, so the UI re-orders robustness variants (original, JPEG, resize, blur).
