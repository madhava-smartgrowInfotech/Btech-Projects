# Smart Campus Placement System — Advanced Hybrid Version
Batch C-05 | CSE-C

**Idea:** Your abstract (placement eligibility + company recommendation + Flask) **×** base paper
`arXiv:2603.29881` (Hybrid XGBoost + kNN residual refinement, Platt calibration, SHAP, dual-axis recommendation).

## Mapping: base paper → placement
| Base paper (admission) | This project (placement) |
|---|---|
| XGBoost + kNN residual on borderline probs [0.4,0.6] | Same, for placement borderline students |
| Platt scaling, Brier score | Same |
| SHAP, PCA, 70/15/15 split, 9-fold CV | Same |
| University-only / Program-only / Hybrid Univ–Prog | Company-only / Role-only / Hybrid Company–Role |
| QS rank, GPA proximity Δmax, country/budget filters | Company Tier, CGPA proximity Δmax, location/package filters |
| Program_Admission_Rate, Program×QS interaction | Company_Hiring_Rate, CGPA×Tier interaction |

## Run
```bash
pip install -r requirements.txt
python src/generate_dataset.py
python src/preprocess.py
python src/hybrid_model.py
python app.py
# open http://127.0.0.1:5000
```

## Pages
- `/` Home + metrics + companies
- `/predict` Student eligibility + skill-gap tips + `POST /api/predict`
- `/recommend` Hybrid top-5 Company–Role alternatives
- `/dashboard` Officer: metrics, prob histogram, PCA, SHAP, branch stats
- `/recruiter` Filter students by CGPA/aptitude/branch

## Results (regenerated on run → `models/metrics.json`, plots in `static/`)
Expected: Hybrid XGBoost+kNN beats single XGBoost; recommendation raises acceptance prob for rejected students.

## Viva points
1. Why hybrid? Global XGBoost fails on borderline similar profiles → local kNN fixes residuals.
2. Why calibration? Recommendation ranking needs reliable probabilities.
3. Why SHAP? Placement officer needs explainable decisions (CGPA, Tier, Skill_Index…).

## New React frontend (kit V5 - Kinetic Mono)
`run.bat` starts a FastAPI layer (`backend/`, port 8405) over the same `src/` code plus a React/Vite UI (`frontend/`, port 5405).
The Flask app above still works unchanged. See `docs/03_HOW_TO_RUN.md` and `docs/FRONTEND_PLAN.md`.
