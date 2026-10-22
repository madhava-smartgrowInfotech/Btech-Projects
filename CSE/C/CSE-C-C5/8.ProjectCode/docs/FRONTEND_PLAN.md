# Frontend Plan - Smart Campus Placement System (V5 Kinetic Mono)

Ports: backend **8405**, frontend **5405**. Existing Flask app (`app.py`, port 5000) stays untouched.
Because the Flask app renders server-side templates (only `POST /api/predict` is JSON), a thin **FastAPI layer in
`backend/main.py`** is added. It imports the existing `src.recommend` functions (`predict_for`, `recommend`,
`pre_comp_cache`) and reads the same `data/`, `models/`, `static/` files - no model/logic is rewritten.

## 1. Existing Flask endpoints (inventory)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | - | HTML: metrics table + first 12 companies |
| GET/POST | `/predict` | form: cgpa, tenth, twelfth, aptitude, technical, communication, dsa, projects, internships, certifications, backlogs, branch, degree, target_company, target_role | HTML: probability, label (>=0.5 ready), skill-gap tips |
| GET/POST | `/recommend` | form: cgpa, aptitude, technical, communication, dsa, projects, internships, certifications, backlogs, branch, target_company, target_role, location | HTML: base prob, avg gain, match rate, hybrid top-5 table |
| GET | `/dashboard` | - | HTML: model metrics table, 9-fold CV, Brier, residual rate, dataset stats, branch placed-rate, 3 plot images |
| GET/POST | `/recruiter` | form: min_cgpa, min_apt, branch (ALL/...) | HTML: up to 50 students sorted by CGPA, Technical |
| POST | `/api/predict` | JSON profile + target_company, target_role | `{placement_probability, eligible}` |
| GET | `/static/{pca,prob_hist,shap}.png`, `style.css` | - | files |

## 2. New FastAPI endpoints (backend/main.py, port 8405)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status}` |
| GET | `/api/meta` | - | branches, degrees, roles (predict), roles (recommend), locations, companies |
| GET | `/api/companies` | - | all companies (Company, Tier, cutoffs, Package_LPA, Location, Company_Type, Hiring_Rate) |
| GET | `/api/metrics` | - | `metrics.json` (results per model, cv_xgb_9fold, brier_platt, residual_rate, test_size) |
| GET | `/api/stats` | - | total, placed_rate, avg_cgpa, by_branch |
| GET | `/api/plots/{prob_hist\|pca\|shap}` | - | PNG |
| POST | `/api/predict` | profile + target_company, target_role | placement_probability, eligible, label, tips, company row (same maths as Flask `/predict`) |
| POST | `/api/recommend` | profile + target_company/role + optional location | `recommend()` result: base_prob, company_only, role_only, hybrid, avg_gain, match_rate |
| POST | `/api/recruiter/shortlist` | min_cgpa, min_apt, branch | `{total_matches, students[<=50]}` (total_matches is additive) |

## 3. Features / screens to carry over

| # | Existing feature | New screen (route) |
|---|---|---|
| 1 | Home: intro, 4 role cards, model performance table, companies list | Landing `/` (Kinetic Mono hero, live counters, terminal log, three.js grid, model table, company marquee) + companies board on `/companies` |
| 2 | Student eligibility prediction + tips + link to recommendations | `/predict` |
| 3 | Hybrid Company-Role top-5 recommendation (+ base prob, gain, match rate, location preference) | `/recommend` |
| 4 | Officer dashboard: model metrics, 9-fold CV, Brier, residual rate | `/dashboard` (tabs: Models, Explainability) |
| 5 | Dashboard dataset stats: total, placed rate, avg CGPA, branch-wise rate | `/dashboard` stat cards + bar chart |
| 6 | Dashboard plots: prob histogram, PCA, SHAP | `/dashboard` Explainability tab |
| 7 | Recruiter shortlist by CGPA / aptitude / branch | `/recruiter` |
| 8 | Companies list (12 on home, 30 in data) | `/companies` (all 30, searchable) |
| 9 | `POST /api/predict` JSON API | kept, also in FastAPI |

Cross-cutting: dark/light toggle (persisted), command palette, responsive drawer, all loading/empty/error/success states.

## 4. Verification checklist (ticked at the end)

- [x] 1 Landing / home metrics + companies
- [x] 2 Eligibility prediction + tips
- [x] 3 Company-Role recommendation (+location)
- [x] 4 Model metrics + CV/Brier/residual
- [x] 5 Dataset stats + branch chart
- [x] 6 Prob hist / PCA / SHAP plots
- [x] 7 Recruiter shortlist
- [x] 8 Companies board
- [x] 9 JSON predict API

## 5. Build notes

- Screens (React Router): `/` landing, `/predict`, `/recommend`, `/dashboard`, `/recruiter`, `/companies` (all but landing inside the kit `AppShell`).
- Kit V5 copied to `frontend/src`; product-specific parts adapted in the copy (AppShell nav/health, CommandPalette searches companies,
  ActivityLog branding, `display.jsx` probability badge). Added: `api.js`, `format.js`, `lib/{reduced,activity,data,useFetch,profile}`,
  `components/three/*` (wire-grid backdrop), `components/charts/Bars.jsx`.
- Backend additions (additive only): `backend/main.py` (FastAPI, port 8405). `pyarrow` added to requirements (pickled companies table needs it).
- Verified: `npm run build`, `scripts/smoke_test.py` (15 checks), browser walk of every screen at 360 / 768 / 1440 px in light + dark,
  reduced motion, keyboard (`g e/r/d/u/c/l`, `/`, `?`, Esc), clean console.
