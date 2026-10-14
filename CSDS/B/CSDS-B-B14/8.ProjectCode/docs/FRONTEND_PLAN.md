# AquaVision - Frontend Plan (Kit V4, Soft Pastel Calm)

Ports: backend **8214**, frontend **5214** (verified in `.env`; backend started and `GET /api/health` returned 200).
Rule: every row below is ticked `[x]` only after it was walked in the browser against the live API (Step 4).

---

## 1. Backend endpoints (21)

Base path `/api`. Everything except `/health` and `/auth/login` needs `Authorization: Bearer <token>`.
Role **engineer** is required where marked; **manager** gets read views and what-if.

| # | Method | Path | Request | Response (summary) | Used by today's UI |
|---|---|---|---|---|---|
| 1 | GET | `/health` | - | `{status, service}` | no |
| 2 | POST | `/auth/login` | `{email, password}` | `{token, user{email,name,role}}` | Login |
| 3 | GET | `/auth/me` | - | `{email,name,role}` | no |
| 4 | GET | `/dashboard` | - | `{kpis{nrw_pct, avg_pressure, min_pressure, equity_score, system_input_m3, billed_m3, quality_potable_pct, quality_checks, active_leaks, open_alerts, flagged_meters, forecast_week_m3, last_week_m3}, hourly_pressure, hourly_supply_lps, tank_level, zones[], forecast_week[], weather_source, alerts[]}` | Dashboard |
| 5 | GET | `/alerts` | - | open alerts list (syncs alerts first) | no |
| 6 | GET | `/network` | - | network geometry + `active_leaks[]`, `suspects[]`, `summary{}`, `zone_stats`, `snapshot` | Dashboard, Network, Leaks |
| 7 | GET | `/imbalance` | - | per-zone supply vs demand, equity score, rebalancing plan | Network |
| 8 | POST | `/imbalance/whatif` | `{pump_speed 0.7-1.3, throttle{pipe: factor}?}` | same shape as `/imbalance` for the what-if | Network |
| 9 | GET | `/leaks/pipes` | - | `[{pipe, zone}]` candidate pipes | Leaks |
| 10 | POST | `/leaks/inject` (engineer) | `{pipe, leak_lps 1-40}` | `{event, detected, leak_probability, ranking[], true_rank}` | Leaks |
| 11 | GET | `/leaks/events` | - | last 30 leak events | Leaks |
| 12 | POST | `/leaks/clear` (engineer) | - | `{repaired: n}` | Leaks |
| 13 | GET | `/forecast/zones` | - | zone list | Forecast |
| 14 | GET | `/forecast?zone=` | zone code (default `Z3`) | 7-day forecast for the zone | Forecast |
| 15 | GET | `/anomalies` | - | `{summary, meters[]}` flagged meters | Leaks |
| 16 | GET | `/anomalies/meter/{meter_id}` | - | meter series (404 if unknown) | Leaks |
| 17 | POST | `/quality/predict` | sample fields (`sample_name`, `ph`, `Hardness`, `Solids`, `Chloramines`, `Sulfate`, `Conductivity`, `Organic_carbon`, `Trihalomethanes`, `Turbidity`, all nullable) | `{id, potable, confidence, reasons[], limits[]}` | Quality |
| 18 | GET | `/quality/samples` | - | sample set to load into the form | Quality |
| 19 | GET | `/quality/history` | - | last 30 quality checks | Quality |
| 20 | GET | `/quality/limits` | - | guideline limits `[{parameter, label, min, max, unit, source}]` | no |
| 21 | GET | `/metrics` | - | `{quality, demand, leak, anomaly, eval}` from `experiments/` | no |

---

## 2. Features and screens the product has today

| Feature (README) | Where it lives today | Endpoints |
|---|---|---|
| F1 Water-quality prediction, SHAP reasons, limit checks | Quality | 17, 18, 19 |
| F2 Network digital twin on a map | Network, Leaks | 6 |
| F3 7-day demand forecast per zone | Forecast (+ Dashboard) | 4, 13, 14 |
| F4 Leak detection and localisation (inject / clear) | Leaks | 9-12, 6 |
| F5 Distribution imbalance, equity, rebalancing, what-if | Network | 7, 8 |
| F6 Abnormal consumption (IsolationForest meters) | Leaks | 15, 16 |
| F7 Operations dashboard (NRW, pressure, quality, equity, alerts) | Dashboard | 4 |
| F8 Evaluation of every model | **no screen today** (`/metrics` unused) | 21 |
| F9 Login with roles (engineer / manager) | Login | 2 |

Screens that exist today: Landing, Login, Dashboard, Quality, Network, Forecast, Leaks.
Gaps found: **F8 has no screen**; endpoints 3, 5, 20, 21 and 1 are not called by the UI.

---

## 3. Screen map (build target)

| Route | Screen | Endpoints | Notes |
|---|---|---|---|
| `/` | Landing | none | Kit landing and motion pieces. Text only, no numbers that are not from the API. |
| `/login` | Login | 2 | Demo accounts from README shown as a hint. Error text from the server. |
| `/dashboard` | Operations dashboard | 4 (KPIs, charts, tank, zones), 5 (alerts panel) | Skeleton, empty ("no alerts"), error with retry. |
| `/quality` | Water-quality check | 18 (samples), 19 (history), 20 (limits reference), 17 (predict) | Form labelled; result shows potable, confidence, SHAP reasons, limit status. |
| `/network` | Network and imbalance | 6 (map), 7 (imbalance), 8 (what-if) | What-if available to engineer and manager. |
| `/forecast` | Demand forecast | 13 (zones), 14 (forecast) | Zone picker. |
| `/leaks` | Leaks and anomalies | 6, 9 (pipes), 11 (events), 10 (inject), 12 (clear), 15, 16 | Inject and clear are engineer-only: disabled for manager with a reason. |
| `/evaluation` | Model evaluation (**new**) | 21 | Covers F8. Metrics tables per model. |
| session | Auth provider | 3 | Validates the stored token on load. |
| topbar | Dark mode toggle, sidebar / drawer | none | Persisted. |

---

## 4. Decisions made in Step 1 (defaults, to confirm)

1. Add `/evaluation` so F8 has a screen (no existing screen covers it).
2. Dashboard KPIs from `/dashboard`; alerts panel from `/alerts`.
3. `/quality/limits` shown as a reference table on the quality page.
4. `/auth/me` used on load to check the stored session.
5. Keep **leaflet** for the network map. It is used today and is not in the prompt's dependency list.
6. Kit stylesheet is `styles/index.css` (the manifest says `tokens.css`; the file is `index.css`). Imported once in `main.jsx`.
7. The kit has no Tailwind or PostCSS config files at its top level, so nothing to copy in Step 2.2.

---

## 5. Feature checklist (ticked in Step 4)

- [x] F1 Water-quality prediction (`/quality`)
- [x] F2 Network digital twin map (`/network`, `/leaks`)
- [x] F3 7-day demand forecast (`/forecast`, dashboard)
- [x] F4 Leak inject / localise / clear (`/leaks`)
- [x] F5 Imbalance, equity, what-if (`/network`)
- [x] F6 Abnormal consumption (`/leaks`)
- [x] F7 Operations dashboard (`/dashboard`)
- [x] F8 Model evaluation (`/evaluation`)
- [x] F9 Login and roles (`/login`)
- [x] Landing page (`/`)

---

## 6. Verification (Step 4)

- `npm run build` passes (Vite 6, no errors). Recharts and Leaflet load in lazy page chunks.
- `scripts/smoke_test.py` passes all 10 checks against the running API on 8214.
- Browser walk-through in Chrome (Playwright) as engineer and as manager:
  - Landing, sign-in redirect, every screen loads with no error states and no failed requests.
  - Water quality: sample loaded, check run, result and history shown.
  - Network: map renders; imbalance tab and what-if scenario run.
  - Forecast: zone switch loads the new forecast.
  - Leaks: inject detects the leak and ranks pipes; repair closes it; meter detail opens.
  - Evaluation: metrics render from `/api/metrics`.
  - Manager: inject and repair are disabled.
  - Dark mode choice survives a reload.
  - Console: no errors; no page errors; no 4xx/5xx responses during the walk.
- Widths: no horizontal page scroll at 360px and 768px (checked by `scrollWidth`, 360 and 768).
- Not separately tested in the browser: reduced motion (wired through `MotionConfig reducedMotion="user"` and the kit CSS media query), keyboard focus order, light mode at 360px and 768px (the widths walk ran in dark mode).
