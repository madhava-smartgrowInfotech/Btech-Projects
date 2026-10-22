# LearnPathIQ — Personalized E-Learning Recommendations

LearnPathIQ is a locally-deployable, personalized e-learning recommendation platform. Learners create a profile (education, skill level, interests, topics, goals), and the system recommends suitable courses plus the most useful next learning action — with clear explanations. Recommendations adapt as interaction history accumulates.

## Key capabilities
- Account + learner profile (register/login/logout, profile create/update, recommendation history)
- 24-course local catalog with rich metadata (category, topic, level, duration, difficulty, prerequisites, outcomes, tags, rating)
- Hybrid recommender: TF-IDF content similarity + skill/topic compatibility + behavioral signals + predicted success probability + engagement + goal fit
- XGBoost / Random Forest / Logistic Regression success-risk models trained on OULAD-style learner-state features (80/10/10 learner-level split)
- Lightweight personalized action scoring (T-learner, one-vs-rest over `quiz, content, forum, homepage, continue_course`), described conservatively as "estimated benefit"
- Adaptive policy: `best_action = argmax estimated benefit`, workload-aware
- Offline evaluation on logged data: behavior-policy estimation, propensity clipping, IPS / SNIPS / Doubly Robust (no live A/B claims)
- Fairness audit by age band and gender (reporting only)
- Feedback loop: every view/open/start/quiz/content/forum/complete/dismiss/save event updates behavioral features
- Pages: landing, register, login, onboarding, dashboard, recommendations, course details, learning path, activity, insights, analytics
- JSON API + server-rendered light SaaS UI, SQLite persistence, binds to `127.0.0.1:8000`

## Architecture
```
Browser (Jinja2 + vanilla JS) <-> FastAPI (app/main.py, app/api_routes.py)
  -> SQLite (SQLAlchemy models) | recommender.py (hybrid ranking)
  -> models/*.joblib (scaler, selected predictor, uplift T-learner)
  -> artifacts/metrics/model_metrics.json + artifacts/plots/*.png
```

## Technology stack
Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic, pandas, NumPy, scikit-learn, XGBoost, joblib, matplotlib, Jinja2, passlib (pbkdf2_sha256).

## ML pipeline
`python scripts/train_pipeline.py`:
1. Attempts OULAD probe; uses reproducible synthetic OULAD-like fallback (`synthetic-oulad-like-fallback-v1`) with demographics, weekly VLE-style engagement, assessment scores, outcomes, observed actions.
2. Builds weekly learner-state features, learner-level 80/10/10 split.
3. Trains Logistic Regression / Random Forest / XGBoost; selects best by validation AUC; evaluates ROC-AUC, accuracy, precision, recall, F1, confusion matrix, Brier on held-out test.
4. Trains one-vs-rest T-learner action models where treatment variation suffices, else records the limitation and uses a predictive fallback.
5. Runs behavior-policy + IPS/SNIPS/DR offline evaluation with clipping; runs fairness audit; writes `artifacts/metrics/model_metrics.json`, plots, and `models/*.joblib`.

No metric is fabricated — every number comes from the local run. Unsupported metrics are stored as `null` with a reason.

## Dataset
Primary design target is the Open University Learning Analytics Dataset (demographics, VLE interactions, assessments). Because the full OULAD download requires manual access and is unreliable in sandboxed networks, this build probes availability and automatically falls back to a synthetic dataset with the same essential schema and statistical structure. The active source is recorded in `dataset_source` inside the metrics file.

## Frontend
A React frontend (Vite, kit V2 "Neo Brutal Grid") lives in `frontend/` and talks to the same JSON API. Ports come from `.env`:
React app on `http://localhost:5407`, FastAPI (and the original Jinja UI) on `http://localhost:8407`. See `docs/FRONTEND_PLAN.md`.

## Running
- Easiest: double-click `run.bat`, open `http://localhost:5407` (original UI: `http://localhost:8407`)
- Docker: `docker build -t learnpathiq .` then `docker run --rm -p 8000:8000 learnpathiq`
- Manual: see `HOW_TO_RUN.md`

## API overview
`POST /api/auth/register|login|logout`, `GET /api/me`, `GET|PUT /api/profile`, `GET /api/courses`, `GET /api/courses/{id}`, `GET /api/recommendations`, `POST /api/recommendations/refresh`, `POST /api/interactions`, `GET /api/activity|history|learning-path|insights|metrics|fairness|health`

## Evaluation methodology
Held-out learner-level test set; AUC/F1 primary, Brier for calibration; offline policy value via clipped IPS/SNIPS/DR with effective-sample-size reporting. Fairness is audit-only.

## Limitations
- Synthetic fallback data limits generalizability; replace with OULAD export for production studies.
- Uplift scores are observational "estimated benefits", not proven causal effects.
- Offline policy values are not live-experiment results.
- Single-node SQLite; demo auth (token cookie) — use a managed identity provider for production.

## Privacy / security
Passwords hashed with pbkdf2_sha256; token auth via HttpOnly cookie; parameterized ORM queries; Pydantic validation; no secrets committed (see `.env.example`); all data stays local in `learnpathiq.db`.
