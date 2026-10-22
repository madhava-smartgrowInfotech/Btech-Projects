# FinSight AI — AI-Based Financial Identification & Forecasting

**FinSight AI** is a standalone web application that analyzes an individual's
demographic and financial information and produces a financial profile,
a risk assessment, a future economic forecast, and explainable ML insights
with clear visualizations.

## Problem being solved

Individuals rarely get a clear, data-driven picture of where they stand
financially or which factors matter most. FinSight AI turns factors such as
**age, occupation, education, income signals, and location** — plus economic
indicators — into an interpretable profile with honest, model-based guidance.

## Key features

- **Financial assessment form** with full server-side validation.
- **Financial profile classification** — Emerging / Developing / Established,
  with confidence score and Low / Moderate / High risk band.
- **4-model comparison** — Logistic Regression, Random Forest, Gradient
  Boosting, XGBoost; best selected by real ROC-AUC.
- **SHAP explainability** — global importance charts + live per-person
  positive/negative contributors in plain language.
- **Economic forecasting** — Holt-Winters 12-month forecast with history,
  intervals, and trend interpretation (Plotly.js charts).
- **What-if scenarios** — change gains, losses, hours, or education and
  compare baseline vs scenario side-by-side.
- **Validation & stats** — stratified 5-fold CV, leakage-safe pipelines,
  correlation + logistic-regression statistics.
- **Polished light-theme UI** — dashboard, assessment, results, explainability,
  forecast, what-if, performance, and about screens.

## How the system works

```text
User input → validation → feature engineering → trained classifier
→ profile + risk → SHAP explanation → economic forecast
→ optional what-if → integrated dashboard
```

Architecture: `data ingestion → preprocessing → feature engineering →
model training → evaluation → persisted artifacts → Flask API → dashboard`.

## ML models used

| Model | Role |
|---|---|
| Logistic Regression | Interpretable linear baseline (scaled features) |
| Random Forest | Bagged-tree comparator |
| Gradient Boosting | Boosted-tree comparator |
| XGBoost | Primary nonlinear classifier (selected on merit — currently best by ROC-AUC) |

Preprocessing lives inside each `Pipeline` (`ColumnTransformer` +
median/`"Unknown"` imputation + one-hot encoding; scaling only for the
linear model) with `random_state=42` throughout.

## Dataset / source

- **Classification:** UCI Adult / Census Income —
  https://archive.ics.uci.edu/dataset/20/census+income
  (48,842 individual records; target `income >50K vs <=50K`, adapted as a
  financial-profile signal — not a credit score or approval).
- **Forecasting:** the Adult data is cross-sectional, so a separate monthly
  Household Financial Conditions Index series is used (synthetic illustrative
  series with documented schema — see `data/README.md`), modelled with
  Holt-Winters Exponential Smoothing.
- Full provenance, schema, sizes, and rationale: `data/README.md`.

## Feature engineering

Interpretable, reproducible transforms only: net investment position,
log-scaled gains/losses, capital-intensity/position flags, hours bands,
age bands, education tiers, regional categories from country,
employment-stability categories. Implemented in
`scripts/feature_engineering.py`.

## Explainability

SHAP `TreeExplainer` (tree-path-dependent, no expensive per-request
resampling). Global artifacts (`shap_global.json`, `shap_bar.png`,
`shap_beeswarm.png`) are precomputed at train time; local contributions are
computed live per prediction. The UI states clearly that SHAP shows
associations, not causation.

## Forecasting

`statsmodels` Holt-Winters (additive trend + seasonality), 12-month horizon
with ±1.96σ intervals, history + forecast + interpretation served from
`artifacts/forecast.json`.

## What-if analysis

`app/services/whatif.py` re-runs the persisted model on baseline and
scenario inputs, reports score deltas, profile/risk changes, and changed
fields. Labelled everywhere as a **scenario simulation, not causal**.

## Validation strategy

Stratified 80/20 split + 5-fold stratified CV (`n_splits=5`,
`random_state=42`); preprocessing inside pipelines; no GroupKFold needed
(one row per person — documented); no temporal split for classification
(no time dimension); see `artifacts/validation_report.json`.

## Installation

```text
python -m venv .venv
.venv\Scripts\activate        :: Windows
pip install -r requirements.txt
python scripts\train.py
python run.py
```

Or just double-click **`run.bat`**. Docker: `docker build -t finsight-ai .`
+ `docker run --rm -p 5000:5000 finsight-ai` (see `HOW_TO_RUN.md`).

## Running instructions

Open `http://localhost:5000` → **Start Financial Assessment** → fill the
form → review profile, SHAP drivers, insights, and forecast → optionally
run a **What-If** scenario → inspect **Performance** for real metrics.

## API / endpoints

| Route | Purpose |
|---|---|
| `/` | Dashboard |
| `/assess` | Assessment form + result |
| `/explain` | Global SHAP |
| `/forecast` | Forecast + intervals |
| `/whatif` | Scenario comparison |
| `/performance` | Model comparison, ROC, confusion matrix, validation, stats |
| `/about` | Product info |
| `/health` | JSON status |
| `/api/predict` | JSON prediction |
| `/api/forecast` | JSON forecast |

## Project structure

```text
FinSight/
  app/ (routes, services, templates, static)
  scripts/ (train, evaluate, feature_engineering, models, forecast)
  data/ (raw, processed, README.md)
  models/ (persisted pipelines)
  artifacts/ (metrics, plots, SHAP, forecast JSON)
  tests/  screenshots/
  requirements.txt  run.py  run.bat  run-docker.bat
  Dockerfile  docker-compose.yml  HOW_TO_RUN.md  README.md
```

## Limitations

- Predictions are model-based estimates from historical census patterns;
  they are not personal advice, credit decisions, or guarantees.
- The model reflects biases present in 1990s census data; treat results as
  informational patterns, not judgments about individuals.
- The economic index is illustrative; its forecast extrapolates past
  patterns and cannot predict personal outcomes.

## Responsible-use disclaimer

FinSight AI provides informational financial insights only. It does not
offer professional financial advice and never guarantees investment
returns, income, credit, or loan approval. Consult a qualified professional
for decisions about your finances.
