# Frontend Plan - FinSight AI (Kit V4, Soft Pastel Calm)

Ports: backend **8409**, frontend **5409**. The existing Flask app (server-rendered Jinja templates) stays untouched
and working; a new React (Vite, JavaScript) frontend is built in `frontend/`.

> Layout note: the prompt says the code lives in `8.ProjectCode/FinSight/`. In this checkout it lives directly in
> `8.ProjectCode/` (`app/`, `scripts/`, `run.bat`, ...). `frontend/` is created beside `app/`.

## 1. Backend inventory (existing endpoints)

Flask app, blueprint `main` in `app/routes.py`, model + SHAP services in `app/services/`.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/health` | - | JSON `{status, product, model, model_loaded, forecast_available}` |
| GET | `/` | - | HTML dashboard (metrics, model name, top-5 SHAP, forecast interpretation) |
| GET / POST | `/assess` | form: age, workclass, education, marital-status, occupation, relationship, race, sex, native-country, capital-gain, capital-loss, hours-per-week | GET: HTML form (+ session baseline prefill). POST: HTML result (400 with error list on invalid, 500 on failure); stores baseline in session |
| GET | `/explain` | - | HTML: global SHAP (`shap_global.json`) |
| GET | `/forecast` | - | HTML: Holt-Winters forecast chart + table |
| GET / POST | `/whatif` | form: the 12 baseline fields + `scenario_capital_gain`, `scenario_capital_loss`, `scenario_hours`, `scenario_education` (at least one required) | HTML comparison (400 on invalid) |
| GET | `/performance` | - | HTML: model comparison, ROC/confusion images, validation protocol, stats |
| GET | `/about` | - | HTML about page |
| GET | `/artifacts/<name>` | name in `confusion_matrix.png`, `roc_curve.png`, `shap_bar.png`, `shap_beeswarm.png` | PNG (404 otherwise) |
| POST | `/api/predict` | JSON, the 12 assessment fields | `{ok, result:{proba, strength_pct, risk_pct, profile, risk, model, inputs, shap:{positives[], negatives[], expected_value, available, note}, insights[]}}` or `{ok:false, errors[]}` 400/500 |
| GET | `/api/forecast` | - | `{available, method, source_note, history[{date,value}], forecast[{date,value,lower,upper}], interpretation, trend_direction, forecast_pct_change, horizon_months, residual_std}` |

### Gaps the SPA needs (thin, additive, read-only wrappers - no logic changes)

New blueprint `app/api.py` (registered in `create_app`), every route just calls the existing functions/artifact loaders:

| Method | Path | Wraps |
|---|---|---|
| GET | `/api/options` | the option lists + numeric limits from `app/utils/validation.py` |
| GET | `/api/dashboard` | `metrics.json`, `get_model_name()`, top-5 of `shap_global.json`, forecast interpretation |
| GET | `/api/explain` | `shap_global.json` |
| GET | `/api/performance` | `model_comparison.json`, `validation_report.json`, `stats_report.json`, `training_summary.json` |
| POST | `/api/whatif` | the same validation + override rules as the `/whatif` route, then `run_whatif()` |

`/api/predict`, `/api/forecast`, `/health`, `/artifacts/<name>` are reused as they are. CORS is avoided by a Vite dev
proxy (`/api`, `/artifacts`, `/health` -> 8409); the built SPA is also servable from Flask (see run notes).

## 2. Feature inventory (everything the product does today)

1. Dashboard: model snapshot (model name, accuracy, ROC-AUC, F1), six capability cards, top SHAP drivers, economic outlook text.
2. Financial assessment form: 12 validated inputs, server-side validation errors, prefill from last baseline.
3. Result: profile (Emerging / Developing / Established), risk band, strength score + bar, model name, risk-band mapping.
4. Local SHAP: strengthening and weakening factors with values and plain-language sentences.
5. Actionable insights list (informational) and the echo of the user's inputs.
6. Mini 12-month economic forecast chart on the result page.
7. Explainability: global SHAP bar + beeswarm images, ranked feature table, "how to read this", note banner.
8. Forecast: history + 12-month forecast + 95% interval chart, method / horizon / trend / % change, interpretation, residual std, forecast table.
9. What-if: baseline + 4 scenario overrides, baseline vs scenario cards, delta (pp), verdict, changed fields, profile/risk change callouts, validation errors.
10. Performance: 4-model comparison table (best starred), confusion matrix + ROC images, validation protocol + per-model fold AUCs, statistics table (correlation, logit coef, p-value) + note.
11. About: how it works, technology, responsible-use text.
12. Error page (404 / 500), health endpoint, responsible-use disclaimers on every analysis, `/artifacts` images.

## 3. Screen map (new SPA)

| Route | Screen | Covers features | API |
|---|---|---|---|
| `/` | **Landing** (no shell) - hero, how-it-works, capability cards, live model stats, CTA | 1, 12 | `/api/dashboard` |
| `/login` | **Sample login** (added on request; the product had no login) - demo account, validation, wrong-password error, show password | - | none (client-side demo gate) |
| `/app` | Dashboard | 1 | `/api/dashboard` |
| `/app/assess` | Assessment form | 2 | `/api/options`, `/api/predict` |
| `/app/result` | Result (profile, risk, score, SHAP factors, insights, inputs, mini forecast) | 3, 4, 5, 6 | `/api/predict` (state kept in sessionStorage), `/api/forecast` |
| `/app/explain` | Explainability | 7 | `/api/explain`, `/artifacts/*` |
| `/app/forecast` | Forecast | 8 | `/api/forecast` |
| `/app/whatif` | What-if | 9 | `/api/options`, `/api/whatif` |
| `/app/performance` | Performance | 10 | `/api/performance`, `/artifacts/*` |
| `/app/about` | About + responsible use | 11 | static copy from the original page |
| `*` | Not found | 12 | - |

Cross-cutting: skeleton / empty / error / success states, dark-mode toggle (persisted), reduced motion, drawer sidebar
under 900px, tables that scroll or collapse to cards at 360px, keyboard focus + Escape, labelled inputs.

## 4. Feature checklist (verified in Step 4)

- [x] 1 Dashboard snapshot, cards, top drivers, outlook
- [x] 2 Assessment form + validation + prefill
- [x] 3 Result profile / risk / score
- [x] 4 Local SHAP factors
- [x] 5 Insights + inputs echo
- [x] 6 Mini forecast on result
- [x] 7 Explainability
- [x] 8 Forecast
- [x] 9 What-if
- [x] 10 Performance
- [x] 11 About / responsible use
- [x] 12 Error page, health, disclaimers

## 5. Verification record

- `npm run build` passes; `python -m pytest tests` 9/9 (Flask app untouched, old pages still served on 8409).
- `scripts/smoke_test.py`: 35/35 checks (API on 8409 and through the 5409 proxy, deep links, bad input, what-if).
- `scripts/capture_screens.py` walks every screen with real model output, saves `docs/screenshots/01..11_*.png`
  (landing in light and dark) and reports console errors, page errors and failed/404 requests - none.
- Checked at 360 / 768 / 1440 px in light and dark: no horizontal overflow, drawer navigation at <900px,
  Escape closes the drawer, validation and API-offline error states with retry, empty result state,
  `prefers-reduced-motion` (content visible, marquee static).
- Additive backend change only: `app/api.py` (5 thin read-only/wrapper routes) registered in `app/__init__.py`;
  `run.py` now also reads `.env` for the port.

## 6. Sample login

The product has no accounts, so a **sample login** was added at `/login` (frontend only, no backend change):
`demo@finsight.ai` / `finsight123`. All `/app/*` routes are guarded and return the visitor to the page they asked
for; the session persists across reloads (`localStorage`), and Sign out in the topbar clears it. It is a demo gate
that runs in the browser and protects nothing. Verified: redirect when signed out, empty / invalid / wrong-password
errors, show-password, return-to-page, reload persistence, sign out, 360px layout.
