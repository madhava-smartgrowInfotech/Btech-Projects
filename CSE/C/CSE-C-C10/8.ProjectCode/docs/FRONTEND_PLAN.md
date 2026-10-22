# FRONTEND PLAN - VenturePulse (CSE-C-C10)

**Project:** An Efficient Novel Approach for Predicting Startup Company Success Rates Using Advanced Machine Learning Paradigms
**Design:** V5 Kinetic Mono (kit copied into `frontend/src/`) · **Ports:** backend `8410`, frontend `5410`

The existing product is a FastAPI app with server-rendered Jinja2 pages (`app/templates/`). It stays untouched and
keeps working on the backend port (`http://localhost:8410/dashboard` etc.). The new React app lives in `frontend/` and
talks to the same FastAPI process over JSON.

> The prompt says the code lives in `8.ProjectCode/VenturePulse/`; in this repo the backend sits directly in
> `8.ProjectCode/` (there is no `VenturePulse/` subfolder), so `frontend/` is created beside `app/`.

---

## 1. Backend endpoint inventory (`app/main.py`)

| # | Method | Path | Request | Response | Used by |
|---|--------|------|---------|----------|---------|
| 1 | GET | `/api/health` | - | `{status, app, records, best_model}` (500 `{status:"error", detail}` on failure) | topbar status dot |
| 2 | GET | `/api/model-metrics` | - | `{models{name:{accuracy,balanced_accuracy,precision,recall,f1 -> {mean,std}, confusion_matrix_mean, confusion_matrix_last}}, best_model, representations{structured_only,text_only,combined -> {mean,std}}, retrieval_k{"k=10".."k=50" -> {mean,std}}, metadata{...}}` | Dashboard, Performance |
| 3 | GET | `/api/insights` | - | `{total, success, failure, success_rate, industries[{industry,success_rate,count}], states[{state,success_rate,count}], median_funding_success, median_funding_failure, correlations{signal:r}}` | Dashboard, Insights |
| 4 | POST | `/predict` | JSON `PredictPayload`: `funding_total_usd, funding_rounds, age_first_funding_year, age_last_funding_year, age_first_milestone_year, age_last_milestone_year, relationships, milestones, avg_participants` (numbers), `has_VC, has_angel, has_roundA, has_roundB, has_roundC, has_roundD, is_top500` (bool), `state, industry_type, description` (str, <= 2000 chars), `k` in {10,20,30,50} | `{outcome, probability_success, probability_failure, confidence, model, risk, similar[{similarity,outcome,industry,state,funding_total_usd,funding_rounds,relationships,milestones,description}], similar_counts{SUCCESS,FAILURE}, explanation[str], embedding_backend, k}` (422 on validation, 500 `{detail}`) | Predict, Result |
| 5 | GET | `/` , `/dashboard` | - | Jinja HTML (legacy) | legacy |
| 6 | GET | `/predict` | - | Jinja HTML form (legacy) | legacy |
| 7 | POST | `/predict-form` | form fields | Jinja HTML result (legacy) | legacy |
| 8 | GET | `/performance` , `/insights` | - | Jinja HTML (legacy) | legacy |
| 9 | GET | `/static/img/*.png` | - | matplotlib charts (10 PNGs) | legacy |

**Gaps the new UI needs (additive, read-only, no change to existing contracts)**

| New | Why |
|-----|-----|
| `GET /api/config` | The form's option lists (`STATES`, `INDUSTRIES`, `RETRIEVAL_KS`, `DEFAULT_K`, `MAX_DESC_LEN`) are only embedded in Jinja HTML today; also dataset metadata (synthetic-fallback note, embedding backend, alpha, class counts) |
| `GET /api/feature-importance` | The feature-importance chart is only a pre-rendered PNG; this returns the same numbers (model coefficients / importances + `feature_names_structured`) as JSON so the chart can be native |

## 2. Feature / screen inventory (README, HOW_TO_RUN, Jinja templates)

| # | Existing feature | Where it is today |
|---|------------------|-------------------|
| F1 | Dashboard hero: best validated model, balanced accuracy +/- std, F1, "5 repeated stratified 80/20 splits - N startups" | `dashboard.html` |
| F2 | Dashboard KPI tiles: historical startups, successful, failed, success rate | `dashboard.html` |
| F3 | Class distribution chart; model comparison (balanced accuracy) chart | `dashboard.html` (PNG) |
| F4 | "How VenturePulse works" 4-step explainer | `dashboard.html` |
| F5 | Data note when the synthetic fallback dataset is in use | `dashboard.html` |
| F6 | Predict form: funding total, rounds, relationships, milestones, avg participants, 4 age fields, industry, state, k (10/20/30/50) | `predict.html` |
| F7 | Investor signals: Has VC, angel, Round A-D, Top-500 | `predict.html` |
| F8 | Startup description (required, max 2000 chars) + validation errors | `predict.html`, `/predict-form` |
| F9 | Result verdict: SUCCESS / FAILURE, confidence, model, risk label | `result.html` |
| F10 | Success / failure probability | `result.html` |
| F11 | "Not a guarantee" disclaimer | `result.html` |
| F12 | Key contributing features (explanation bullets) | `result.html` |
| F13 | Echo of the submitted inputs | `result.html` |
| F14 | Similar historical startups table (k, SUCCESS/FAILURE counts, similarity, outcome, industry, state, funding, rounds, summary) | `result.html` |
| F15 | "Analyze another startup" | `result.html` |
| F16 | Performance: 4-model metrics table (mean +/- std for balanced acc, acc, precision, recall, F1), best model highlighted | `performance.html` |
| F17 | Performance charts: balanced accuracy, F1, precision vs recall | `performance.html` (PNG) |
| F18 | Confusion matrix of the best model | `performance.html` (PNG) |
| F19 | Retrieval-size comparison (k) table + chart | `performance.html` |
| F20 | Structured vs text vs combined representation table + chart | `performance.html` |
| F21 | Feature importance chart | `performance.html` (PNG) |
| F22 | Insights: total / success / failure / median funding (S / F) tiles | `insights.html` |
| F23 | Success rate by industry (chart + table with n) | `insights.html` |
| F24 | Funding distribution by outcome | `insights.html` (PNG) |
| F25 | Correlation of each signal with SUCCESS | `insights.html` |
| F26 | Health check of the API | `/api/health` |
| F27 | Local-first / works offline, one-click `run.bat`, Docker, pytest suite | `run.bat`, `run-docker.bat`, `tests/` |

No login exists in the product, so the new app has none (nothing is invented).

## 3. Screen map (React, routes)

| Route | Screen | Covers | Data |
|-------|--------|--------|------|
| `/` | **Landing** - Kinetic Mono hero (three.js wire-grid background, live counters, terminal log), best-model card, live demo counters, CTA | F1, F2, F4, F5, F27 | `/api/model-metrics`, `/api/insights`, `/api/config` |
| `/app` | **Dashboard** | F1-F5, F26 | metrics, insights, config, health |
| `/app/analyze` | **Analyze a startup** (form) | F6, F7, F8 | `/api/config`, `POST /predict` |
| `/app/analyze/result` | **Estimated outcome** (result, in-page state) | F9-F15 | `POST /predict` response |
| `/app/performance` | **Model performance** | F16-F21 | `/api/model-metrics`, `/api/feature-importance` |
| `/app/insights` | **Startup insights** | F22-F25 | `/api/insights` |
| (overlay) | Activity log drawer (terminal log of API calls), command palette, shortcuts help | extras from the kit | in-memory |
| (backend) | Legacy Jinja app stays at `http://localhost:8410/dashboard` | all | untouched |

SPA routes avoid `/predict` so the Vite proxy can forward `POST /predict` to the backend unchanged.

## 4. Run / ports

* `.env`: `BACKEND_PORT=8410`, `FRONTEND_PORT=5410` (`.env.example` documents it).
* `run.bat`: builds `.venv`, installs `requirements.txt`, installs `frontend/node_modules`, starts uvicorn on 8410 and Vite on 5410.
* Vite proxies `/api`, `/predict` and `/static` to `127.0.0.1:8410`.

## 4b. Known blocker found in Step 1: shipped model artifacts (resolved)

`models/*.joblib|pkl` were saved with scikit-learn 1.9 / pandas 3, but `requirements.txt` pins scikit-learn 1.5.2 and
pandas 2.2.3, so `ensure_artifacts()` failed (`/api/health` 500, `/predict` 500) on a fresh `run.bat`. The models were
re-trained with `scripts/train.py` in the pinned `.venv` (the same thing the app does on first start when artifacts are
missing). Logistic Regression is identical (balanced acc 0.7493 +/- 0.0245, F1 0.7165); Decision Tree 0.614, Random Forest
0.641 (was 0.655), XGBoost 0.697 (was 0.694). README results table updated. `scripts/train.py` now adds the project root to
`sys.path` so `python scripts/train.py` works as documented.

## 5. What was built

* `app/api_extra.py` (additive, included with two lines in `app/main.py`): `GET /api/config`, `GET /api/feature-importance`,
  `POST /api/auth/login`, `GET /api/auth/me` (demo sign-in `demo@venturepulse.com` / `Demo@1234`, configurable in `.env`).
  No existing route or contract changed.
* `frontend/` - React 18 + Vite 6 + Tailwind 4, kit V5 copied into `frontend/src` (`components/ui`, `components/motion`,
  `lib/theme`, `index.css` tokens). Kit files that were product-coupled (AppShell, CommandPalette, display badges, Logo) were
  adapted in the copy; missing helpers (`lib/reduced`, `lib/activity`, `reactbits/Backdrop|WireGrid`) were added; the kit folder
  was not touched. New: `api.js`, `format.js`, `lib/auth.jsx`, `components/charts/Charts.jsx`, and the pages below.
* Vite proxies `/api` and `/predict` to the backend, so `POST /predict` is used exactly as the Jinja app uses it.
* `run.bat` rebuilt: reads ports from `.env`, rebuilds a broken `.venv`, installs Python + npm deps, starts both servers.
* `scripts/smoke_test.py`, `scripts/ui_checks.py`, `scripts/capture_screens.py`; screenshots in `docs/screenshots/`.

| Route | Screen |
|-------|--------|
| `/` | Landing (three.js wire grid, typewriter, live API terminal, scroll reveals, live counters) |
| `/login` | Sign in (demo account button) |
| `/app` | Dashboard |
| `/app/analyze` | Analyze form -> estimated outcome (in-page result) |
| `/app/performance` | Model performance |
| `/app/insights` | Startup insights |

## 6. Feature checklist - verified working in the new UI

Verified by `scripts/capture_screens.py --check` (full walk, clean console, no failed requests), `scripts/smoke_test.py --live`
(16/16), `scripts/ui_checks.py` (53/53) and the original `pytest tests` (7/7).

- [x] F1 Dashboard hero: best model, balanced accuracy +/- std, F1, 5 splits / N startups
- [x] F2 KPI tiles: historical, successful, failed, success rate
- [x] F3 Class distribution (donut) + model comparison chart (native recharts instead of PNG)
- [x] F4 "How VenturePulse works" 4 steps
- [x] F5 Synthetic-fallback data note (dashboard)
- [x] F6 Predict form: funding, rounds, relationships, milestones, avg participants, 4 age fields, industry, state, k
- [x] F7 Investor signals: VC, angel, Round A-D, Top-500
- [x] F8 Description (required, max 2000) + client and server validation messages
- [x] F9 Verdict SUCCESS / FAILURE, confidence, model, risk label
- [x] F10 Success / failure probability (LED score bars)
- [x] F11 "Not a guarantee" disclaimer
- [x] F12 Key contributing features (explanation bullets)
- [x] F13 Echo of submitted inputs
- [x] F14 Similar historical startups table (k, S/F counts, similarity, outcome, industry, state, funding, rounds, summary; sortable, paged, cards on mobile)
- [x] F15 "Analyze another startup"
- [x] F16 4-model metrics table (mean +/- std), best highlighted
- [x] F17 Balanced accuracy, F1, precision-vs-recall charts
- [x] F18 Confusion matrix of the best model
- [x] F19 Retrieval-size comparison (chart + table)
- [x] F20 Structured vs text vs combined (chart + table)
- [x] F21 Feature importance chart (from the new `/api/feature-importance`)
- [x] F22 Insights tiles incl. median funding S / F
- [x] F23 Success rate by industry (chart + table with n)
- [x] F24 Funding by outcome (median funding chart; the API exposes medians, not the full distribution)
- [x] F25 Correlation of each signal with SUCCESS
- [x] F26 API health indicator (topbar / sidebar / login / landing)
- [x] F27 Local-first run: `run.bat` (tested), Docker files untouched, pytest suite passing
- [x] Legacy Jinja pages still render at `http://localhost:8410/dashboard` (smoke test)

## 7. Non-negotiables

- [x] Every state: skeletons, empty-state component (table), error states with what failed + what to do + Retry, toasts for success
- [x] Dark mode default + light, toggle in the topbar, persisted (`vp_theme`)
- [x] `prefers-reduced-motion` respected (headline instant, CSS grid replaces WebGL, motion collapses to fades); three.js is a lazy chunk
- [x] Responsive from 360px: sidebar becomes a drawer, wide tables scroll or become cards, no horizontal overflow at 360/768/1440 in both themes
- [x] Keyboard: visible focus rings, Escape closes drawers/palette, `/` palette, `g d/a/p/i/l` navigation, `?` help, labelled inputs
- [x] Real data only: every number comes from the API; the only canned text is the optional "Fill an example" input
