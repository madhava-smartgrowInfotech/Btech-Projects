# Frontend plan — HubOptima (V4 · Soft Pastel Calm)

Project: *Advanced Optimization in E-Commerce Logistics: Combining Matheuristics With Random Forests for Hub Location Efficiency* (batch CSDS-A-A4).

The existing interface is a **Flask app with templates stored as Python strings** (`hublocator/webapp.py`, served by `python run.py serve` on port 5000). It stays untouched and keeps working. A new React frontend is built in `frontend/` (port **5104**) and talks to a thin **FastAPI layer** in `backend/` (port **8104**) that imports the existing `hublocator` functions — no logic is rewritten.

---

## 1. Existing endpoints (Flask, `hublocator/webapp.py`)

### HTML routes
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | `?msg=` | Dashboard HTML: dataset summary, monthly-volume SVG chart, pipeline status, top 5 markets, latest comparison table |
| GET | `/forecast` | `?msg=` | RF metrics vs 2 baselines, feature importance (top 10), next-month forecast per region, back-test SVG + per-region table |
| POST | `/train` | form (none) | Retrains the RF forecaster → redirect `/forecast?msg=Forecaster retrained.` |
| GET/POST | `/optimize` | form: `period, n_hubs, capacity_factor, transport_rate, fixed_cost_per_hub, time_penalty, sla_hours, sla_hard (0/1), method (matheuristic/exact), time_limit` | KPIs, SVG network map, hub utilisation, cost split, search log, region allocation |
| GET/POST | `/compare` | form: `period, exact_limit, scal (optional)` | POST starts a background job (comparison **or** scalability benchmark) → redirect; GET shows comparison table, cost/fulfilment bar charts, scalability table, auto-refresh while running |
| GET/POST | `/rolling` | form: `n_months` (2–12) | POST starts background rolling-horizon job; GET shows 4 KPIs, fulfilment-by-month and realised-vs-forecast charts, monthly timeline with hub openings/closings |

### JSON API
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/forecast` | – | `{period, total, regions:[{region_id, city, period, forecast}], metrics:{mae,rmse,mape,r2}}` |
| POST | `/api/optimize` | JSON `{n_hubs, capacity_factor, transport_rate, fixed_cost_per_hub, time_penalty, sla_hours, sla_hard, time_limit, period, method}` (all optional) | `{sol:{status, seconds, objective, hubs, log[], …}, kpi:{n_hubs, hubs, hub_cities, total_cost, fixed_cost, transport_cost, time_cost, cost_per_order, avg_delivery_hours, max_delivery_hours, avg_distance_km, fulfilment_rate, reliability_sla, overloaded_hubs, utilisation{}, assignment[]}, realized}` or `{error}` |
| GET | `/api/compare` | – | `results/comparison.json`: `{params, realized_total_demand, forecast_total_demand, methods:{proposed, exact_mip, greedy, kmeans, largest, fixed_avg}}` |
| GET | `/api/rolling` | – | `results/rolling.json`: `{periods, static_hubs, timeline[], adaptive_avg, static_avg, hub_changes, params}` |

### New thin FastAPI layer — `backend/main.py` (port 8104)
Imports `hublocator.*` and exposes the same operations as JSON. Response shapes of the four existing API calls are kept identical. **(+)** = added; none of them change `hublocator/` logic.

| Method | Path | Wraps |
|---|---|---|
| GET | `/api/health` **(+)** | liveness, solver availability |
| GET | `/api/summary` **(+)** | `dataset_summary` + pipeline status (forecaster trained, comparison/rolling present, PuLP available) — the dashboard page |
| GET | `/api/regions` **(+)** | `regions.csv` (id, city, state, lat, lon, population, tier) — for the network map |
| GET | `/api/options` **(+)** | planning months (next + 18 historical), evaluation months, `config.DEFAULTS` |
| GET | `/api/forecast` | same as Flask |
| GET | `/api/forecast/metrics` **(+)** | full `forecast_metrics.json` (baselines, feature importance, back-test detail) |
| POST | `/api/train` **(+)** | `train_forecaster` (same as Flask `POST /train`) |
| POST | `/api/optimize` | same as Flask (map SVG dropped — drawn client-side from `/api/regions`) |
| GET | `/api/compare` | same as Flask |
| GET | `/api/scalability` **(+)** | `load_scalability` |
| POST | `/api/compare/run` **(+)** | background `run_comparison` or `scalability_benchmark` (same as Flask `POST /compare`) |
| GET | `/api/rolling` | same as Flask |
| POST | `/api/rolling/run` **(+)** | background `rolling_reoptimisation` (same as Flask `POST /rolling`) |
| GET | `/api/jobs` **(+)** | `{compare: bool, rolling: bool}` — replaces the HTML meta-refresh with polling |

---

## 2. Existing features (from README, webapp and CLI)

| # | Feature | Original screen | Status in new UI |
|---|---|---|---|
| F1 | Dataset overview: regions, months, total orders, RF MAPE | Dashboard | ✅ |
| F2 | Monthly order-volume chart | Dashboard | ✅ |
| F3 | Pipeline status (data / forecaster / matheuristic / rolling / comparison) | Dashboard | ✅ |
| F4 | Largest markets (top 5 avg monthly orders) | Dashboard | ✅ |
| F5 | Latest comparison summary table | Dashboard | ✅ |
| F6 | RF vs naive forecasters (MAE, RMSE, MAPE, R²) + training info | Forecast | ✅ |
| F7 | Train / retrain forecaster | Forecast | ✅ |
| F8 | Feature importance (top 10) | Forecast | ✅ |
| F9 | Next-month forecast per region + network total | Forecast | ✅ |
| F10 | Back-test chart actual vs predicted + per-region error table | Forecast | ✅ |
| F11 | Plan hubs: month + 9 parameters (p, capacity, transport, fixed cost, time penalty, SLA, hard/soft, method, time limit) | Plan hubs | ✅ |
| F12 | Plan KPIs (hubs, cost, cost/order, avg/max delivery, fulfilment, SLA reliability, solve time/status/sub-MIPs) | Plan hubs | ✅ |
| F13 | Network map (hubs + regions sized by demand + allocation lines) | Plan hubs | ✅ |
| F14 | Hub utilisation with ok / tight / overloaded tags + cost split | Plan hubs | ✅ |
| F15 | Matheuristic search log | Plan hubs | ✅ |
| F16 | Region allocation table (region, hub, demand, distance, hours) | Plan hubs | ✅ |
| F17 | Infeasible-plan error message | Plan hubs | ✅ |
| F18 | Run method comparison (month, exact time limit) in background | Compare | ✅ |
| F19 | Comparison table (6 methods, hubs, cost, vs proposed, delivery, fulfilment, SLA, overloaded, time) | Compare | ✅ |
| F20 | Operating-cost and fulfilment bar charts | Compare | ✅ |
| F21 | Run scalability benchmark in background + results table | Compare | ✅ |
| F22 | Run rolling re-optimisation (2–12 months) in background | Re-optimise | ✅ |
| F23 | Adaptive vs static KPIs (fulfilment, SLA, cost delta, hub openings, static hubs) | Re-optimise | ✅ |
| F24 | Fulfilment-by-month and realised-vs-forecast charts | Re-optimise | ✅ |
| F25 | Monthly timeline with hub openings/closings | Re-optimise | ✅ |
| F26 | Running-job indicator / auto refresh | Compare, Re-optimise | ✅ |
| F27 | Solver indicator (CBC via PuLP vs greedy fallback) | Footer | ✅ |
| F28 | Original Flask UI + CLI (`run.py`) still work | – | ✅ |

---

## 3. Screen map (new React app)

| Route | Screen | Features | Notes |
|---|---|---|---|
| `/` | **Landing** **(+)** | – | hero with drifting SVG blobs, how-it-works (5 pipeline steps), feature grid, live stats strip (count-up from `/api/summary`), CTA, footer |
| `/app` | **Dashboard** | F1–F5, F27 | StatCards with sparkline, area chart, pipeline Timeline, markets list, comparison table |
| `/app/forecast` | **Forecast** | F6–F10 | metrics table, retrain button (confetti on success), importance bars, forecast table (search + sort + paginate), back-test chart + error table |
| `/app/plan` | **Plan hubs** | F11–F17 | parameter form (Selects, Switch for hard SLA, segmented method), KPIs, SVG network map, utilisation bars, search log Timeline, allocation Table; confetti on first successful plan |
| `/app/compare` | **Compare methods** | F18–F21, F26 | run panel (Tabs: comparison / scalability), job polling with progress, table, rounded bar charts, scalability table + chart |
| `/app/rolling` | **Re-optimise** | F22–F26 | run panel, KPI strip, two line charts, monthly Timeline of hub changes |
| `/app/regions` | **Regions** **(+)** | – | browse the 90 demand regions (from `/api/regions`) with tier/state filter — new, read-only |
| `*` | 404 | – | EmptyState with link home |

Global: AppShell (sidebar → bottom bar under 768px), topbar with dark-mode toggle (persisted, honours `prefers-color-scheme`), backend-status pill, toasts, route-level code splitting.

**Variant:** V4 Soft Pastel Calm — Plus Jakarta Sans / Inter, cream `#FDFCFA`, lavender / mint / peach / sky pastels, warm-slate dark mode, 20–28px radii, spring micro-interactions, drifting blobs, one-shot confetti, shimmer skeletons, count-up figures.

---

## 4. Verification (2026-10-14)

| Check | Result |
|---|---|
| `npm run build` | passes, route-level chunks (charts, motion, gsap split out) |
| `scripts/smoke_test.py --url http://127.0.0.1:8104 --frontend http://localhost:5104` | all checks pass (every endpoint, matheuristic + exact MIP plans, validation, proxy) |
| Original `python tests.py` | all tests passed (data, forecast, optimisation, Flask web app + API). One run made in parallel with a long build failed the "matheuristic within 2 % of exact" check because of CPU contention under the solver time limits; it passes when run on its own |
| Every route at 1440 / 768 / 360 px, light + dark (48 page loads, headless Chrome) | no console errors, no page errors, no failed requests or asset 404s, no horizontal overflow |
| Feature walkthrough | theme toggle persisted; plan with defaults (map, KPIs, allocation); exact MIP on Oct 2025 scored on realised demand; field validation; retrain modal (Escape closes, focus trapped) + retrain toast; back-test search; comparison job; scalability job; rolling job (3 months); region filters; mobile drawer (Escape closes) and bottom bar; reduced-motion page renders with plain fades; keyboard skip link + focus ring |

F1–F28 above were each exercised against the live API. F28: the Flask UI (`python run.py serve`) and `run.py` CLI are untouched - `hublocator/`, `run.py`, `tests.py` and `requirements.txt` have no changes.

Notes
- The API layer maps non-finite floats (e.g. an infinite objective in a matheuristic log entry under an impossible hard SLA) to `null`, and reports a plan whose objective is infinite as "no feasible solution". The Flask app would emit non-standard `Infinity` JSON for the same input.
- Test runs that retrain or re-run jobs overwrite `models/` and `results/`; those files were restored to their pre-test state afterwards.
