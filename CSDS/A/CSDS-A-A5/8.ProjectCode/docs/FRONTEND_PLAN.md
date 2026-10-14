# TaxSentinel - Frontend rebuild plan (V5 Kinetic Mono)

Backend `:8105`, frontend `:5105` (from `.env`). The backend is not changed; every call below is kept.

## 1. API inventory

All routes are under `/api`. Every route except `health`, `auth/register` and `auth/login` needs
`Authorization: Bearer <token>`.

| # | Method | Path | Request | Response | Used by (old UI) |
|---|---|---|---|---|---|
| A1 | GET | `/health` | - | `{status, pipeline_ready, gemini_configured}` | run.bat only |
| A2 | POST | `/auth/register` | `{name, email, password(>=8)}` | `{token, user{id,name,email}}` | Login |
| A3 | POST | `/auth/login` | `{email, password}` | `{token, user}` | Login |
| A4 | GET | `/auth/me` | - | `{id, name, email}` | (unused) |
| A5 | POST | `/pipeline/run` | `{seed 0-10M, taxpayers 150-1500}` | `{run_id, status}`; 409 if one is running | Overview generator |
| A6 | GET | `/pipeline/status` | - | `{running, stage, progress, message, run_id, error, current{run_key, seed, taxpayers, dataset, generated_at}}` | Overview generator (1 s poll) |
| A7 | GET | `/pipeline/runs` | - | last 10 `[{id, seed, taxpayers, status, message, started_at, finished_at, flagged}]` | (unused) |
| A8 | GET | `/overview` | - | `{stats, seed, run_key, generated_at, dataset, risk_histogram[10], pattern_labels, top_taxpayers[8], top_chains[5], headline{k, model/baseline precision_at_k, model/baseline f1}}` | Overview |
| A9 | GET | `/metrics` | - | `{current{run_key, seed, evaluation, train_info}, config, training, eval_report}` | Performance |
| A10 | GET | `/taxpayers` | `q, pattern, flagged, sector, sort(risk/jepa/network/invoice/itc/name), limit<=500, offset` | `{total, items[brief + rules + rings]}` | Taxpayers |
| A11 | GET | `/taxpayers/{gstin}` | - | `{taxpayer, evidence, monthly, rules, partners, flagged_invoices, rings, cluster, invoice_counts, pattern_labels, explanation}` | Profile, Case |
| A12 | GET | `/chains` | - | `[chain brief + label_fraud_share]` | Fraud rings |
| A13 | GET | `/chains/{id}` | - | chain brief + `parties, invoices(<=150), invoices_total` | Chain detail |
| A14 | GET | `/structures` | - | `{rings[], clusters[]}` | Fraud rings |
| A15 | GET | `/graph` | one of `focus, ring, cluster, chain` (or none = whole fraud network) | `{nodes[], links[]}` | Profile, Case, Chain, Fraud rings |
| A16 | POST | `/explanations/{gstin}` | - | `{text, model, quality, created_at}`; 400 no evidence, 502 Gemini error | Case |

## 2. Existing features and screens

| # | Screen / feature | Route |
|---|---|---|
| F1 | Landing page: pitch, features, how it works, demo link | `/` |
| F2 | Sign in, create account, demo-account fill (`?demo=1` prefill) | `/login` |
| F3 | Auth guard, token in localStorage, auto sign-out on 401, sign out | all `/app` |
| F4 | Generate & analyse a new ecosystem (seed, taxpayers), live progress, current ecosystem line, auto-refresh on finish | `/app` |
| F5 | KPI stats: taxpayers, invoices, flagged, ITC at risk | `/app` |
| F6 | Top-8 highest-risk taxpayers | `/app` |
| F7 | Flagged-by-pattern counts (link to filtered ranking), loops / shell-cluster counts | `/app` |
| F8 | Risk distribution histogram | `/app` |
| F9 | Top-5 invoice chains | `/app` |
| F10 | Detection vs rule baseline headline (P@k, F1) | `/app` |
| F11 | Taxpayer ranking: search, pattern / sector / flagged filters, 6 sort keys, pagination, URL-synced | `/app/taxpayers` |
| F12 | Taxpayer profile: header, risk layers, rules triggered, injected label, monthly ITC chart, evidence list, focus graph + loops, partners, shared-identity cluster, anomalous invoices | `/app/taxpayers/:gstin` |
| F13 | Case & explanation: write / regenerate Gemini note, `[E#]` citations jump to evidence, quality metrics, evidence list, network graph | `/app/cases/:gstin` |
| F14 | Fraud rings: whole-network graph, ring / cluster selection, chains table | `/app/graph` |
| F15 | Interactive force graph: risk colours, animated loop edges, hover card, click to open profile | shared |
| F16 | Chain detail: stats, chain graph, parties, invoices | `/app/chains/:id` |
| F17 | Model performance: P@k, R@k bars, method table + ablations, per-pattern recall, invoice / ring / chain metrics, JEPA loss curve, explanation-quality report, PaySim transfer | `/app/performance` |

## 3. Screen map (new UI)

| Route | Screen | Covers | Notes |
|---|---|---|---|
| `/` | Landing - typewriter hero, how-it-works, feature grid, live stats strip (from A1 + A8 when signed in), CTA, footer | F1 | three.js wireframe grid background |
| `/login` | Sign in / Create account (Tabs), demo fill | F2, F3 | |
| `/app` | Control room - generator (Stepper-style stage readout + ProgressBar), 4 KPI StatCards with CountUp + sparkline, top taxpayers Table, pattern counts, risk histogram (Recharts), top chains, headline, **activity log** | F4-F10 | **NEW:** terminal activity log streams real events (pipeline status polls, run history from A7, API calls) |
| `/app/taxpayers` | Ranking - SearchField, Selects, sortable/paginated Table (cards < 640px) | F11 | |
| `/app/taxpayers/:gstin` | Profile - Tabs (Signals / Evidence / Network / Invoices) | F12 | |
| `/app/cases/:gstin` | Case file - explanation with citations, quality KeyValueList, evidence Timeline, graph | F13 | |
| `/app/graph` | Fraud rings - graph, ring and cluster lists, chains Table | F14, F15 | |
| `/app/chains/:id` | Chain - StatCards, graph, parties, invoices | F16 | |
| `/app/performance` | Model performance - Recharts bars, tables, loss curve | F17 | |
| `/app/runs` | **NEW** Run history - Table + Timeline of the last 10 pipeline runs (A7) | - | uses an existing, previously unused endpoint |

Shell additions (**NEW**): command palette on `/` (search taxpayers via A10 + jump to screens), `g` then
`o/t/r/p/h` to jump, dark/light toggle (persisted, follows `prefers-color-scheme`), API status dot (A1),
toasts for success / failure.

## 4. Verification checklist

Walked end to end on 2026-10-14 in headless Chromium (Playwright) against the running API, on the dev server and on
the production build (`npm run build` + `vite preview`): 48/48 feature checks and 58/58 layout checks (360 / 768 /
1440 px x dark / light, every screen, no horizontal page scroll, 360 px run with reduced motion). Production console:
no errors, no failed requests, no 404s. `scripts/smoke_test.py`: 20/20.

- [x] F1 Landing - typewriter hero, live `/api/health` readout (+ `/api/overview` when signed in), three.js grid, how-it-works, features, stats strip, CTA, footer
- [x] F2 Sign in / register (new account created) / demo fill (`?demo=1` prefill)
- [x] F3 Guard redirects to /login, invalid token -> 401 -> signed out to /login, sign out
- [x] F4 Generate & analyse (seed 42, 600): stepper + progress, stage events in the activity log, toast, dashboard refresh to `run-N`
- [x] F5 KPI stats with count-up + sparklines
- [x] F6 Top-8 taxpayers
- [x] F7 Pattern counts link to the filtered ranking; loops / shell-cluster counts
- [x] F8 Risk distribution histogram
- [x] F9 Top-5 chains
- [x] F10 Headline P@k / F1 vs rule baseline
- [x] F11 Ranking: search, pattern / sector / flagged filters, header + select sort, pagination, empty state, clear filters
- [x] F12 Taxpayer profile: header, risk layers, rules, label, monthly ITC chart, evidence, focus graph + loops, partners, cluster, anomalous invoices
- [x] F13 Case: Gemini note written, `[E#]` citation highlights the evidence item, grounding metrics, regenerate
- [x] F14 Fraud rings: whole-network graph, ring / cluster selection, reset, chains table
- [x] F15 Interactive graph: risk colours, animated loop edges, hover card, click to profile, zoom / fit controls
- [x] F16 Chain detail: stats, graph, parties, invoices
- [x] F17 Model performance: P@k / R@k, method + ablation table, per-pattern recall, invoice / ring / chain metrics, loss curve, explanation report, PaySim
- [x] NEW Run history (`/api/pipeline/runs` + `/api/pipeline/status`)
- [x] NEW Keyboard: `/` palette (live taxpayer search, focus trapped, Esc closes), `g o/t/r/p/h/l`, `?` help
- [x] NEW Activity log drawer, theme toggle persisted across reloads

## 5. Backend change (additive, read-only)

`GET /api/overview/monthly` in `backend/app/routes/series.py` (registered in `main.py`): per-month ecosystem series
(invoices, flagged invoices, returns filed, ITC claimed / available, ITC claimed by flagged taxpayers, flagged filers)
computed from the in-memory state and cached per `run_key`. It feeds the Overview KPI sparklines and the
"Ecosystem pulse" chart. No existing route or behaviour changed.
