# Frontend Plan - CSE-A-A14 Churn Intelligence (ChurnIQ)

**Project:** Explainable AI-Based Customer Churn Prediction and Intelligent Retention System
**Kit:** V4 - Soft Pastel Calm (JavaScript `.jsx`), copied into `frontend/src/` · **Ports:** backend `8314`, frontend `5314`
**Status:** built and verified (see section 6)

## 1. Starting point

The product is a **Streamlit app** (`app.py` + 13 modules in `pages/`) over a pure-Python core in `src/`.
It had no HTTP API, no `.env`, no `run.bat` and no `docs/`. The Streamlit app is untouched and still works
(`run.bat streamlit`). This job added:

- `backend/` - a thin FastAPI layer that imports the **existing** `src/` functions (no logic rewritten).
- `frontend/` - a new React + Vite app built on the V4 kit.
- `run.bat`, `.env` / `.env.example` (ports 8314 / 5314 and the demo login), `scripts/`, `docs/`.

Streamlit keeps all workflow state in `st.session_state`. The API mirrors that with one in-memory `AppState`
(single user, same as the Streamlit session). The saved model (`models/*.pkl`) is restored from disk at startup exactly
like `app.py` does; the dataset, the split and the trained-model comparison are session-only, as in Streamlit.

Two deliberate improvements over the Streamlit session logic, neither changing model behaviour:
- Training keeps its preprocessor in a *trial* object and only swaps it in on **Save**, so an older active model can never be scored with a newer preprocessor.
- After a restart (model restored, no held-out split) global importance is computed on the full dataset and labelled as such.

## 2. Backend endpoints (as built, all in `backend/main.py`)

Every route wraps an existing function. `/api/*` except `health` and `auth/login` require `Authorization: Bearer <token>`.

| # | Method + path | Request | Response | Source |
|---|---|---|---|---|
| 1 | `GET /api/health` | - | status, shap_available, model_loaded, dataset_loaded | - |
| 2 | `POST /api/auth/login` | `{email, password}` | `{token, user}` (demo account from `.env`) | `backend/auth.py` (new) |
| 3 | `GET /api/auth/me` | - | current user | `backend/auth.py` |
| 4 | `GET /api/state` | - | dataset flags, target/id, active model, thresholds, trained models | session state |
| 5 | `POST /api/data/sample` | - | dataset summary | `generate_sample_churn_data` |
| 6 | `POST /api/data/upload` | multipart `file` | dataset summary | `load_csv`, `coerce_numeric_looking_columns`, `profile_dataset` |
| 7 | `GET /api/data/preview` | `?rows=15` | columns + rows | raw_df |
| 8 | `GET` / `PUT /api/data/config` | `{target_col, id_col, numeric_cols, categorical_cols}` | columns + detected values | `detect_target_column`, `detect_id_column` |
| 9 | `GET /api/data/quality` | - | rows, cols, duplicates, missing, warnings, errors, ready | `profile_dataset`, `validate_dataset_for_training` |
| 10 | `POST /api/data/prepare` | - | duplicates removed, rows remaining | `clean_missing_and_duplicates` |
| 11 | `GET /api/eda` | `?filters=<json>&numeric=<col>` | KPIs, split, churn by attribute, tenure, histogram, correlation | `compute_kpis`, `make_tenure_group` |
| 12 | `GET /api/dashboard` | - | KPIs, split, risk summary, contract/tenure charts, drivers, top-20 at risk | `build_risk_table`, `risk_distribution_summary`, `global_importance` |
| 13 | `POST /api/models/train` | `{test_size, imbalance_strategy, models[], selection_metric}` | comparison rows + recommended | `train_test_split_data`, `build_preprocessor`, `train_selected_models`, `results_to_table`, `select_best_model` |
| 14 | `GET /api/models/results` | - | last comparison | session state |
| 15 | `POST /api/models/save` | `{name}` | active model info | `save_artifacts`, `get_shap_explainer` |
| 16 | `GET /api/evaluation` | - | per-model metrics, ROC/PR curves, confusion matrix | `evaluate_model` results |
| 17 | `GET` / `PUT /api/risk/thresholds` | `{low, medium, high}` | thresholds (validated) | `DEFAULT_RISK_THRESHOLDS` |
| 18 | `GET /api/risk` | - | summary + every scored customer | `build_risk_table` |
| 19 | `GET /api/customers` | `?search=&limit=` | ids with probability and band | `build_risk_table` |
| 20 | `GET /api/customers/{id}` | - | profile groups, probability, band, drivers, protective factors, actions | `score_customers`, `assign_risk_category`, `local_explanation`, `generate_recommendations` |
| 21 | `GET /api/xai/global` | - | importance tables (built-in / permutation / SHAP) | `global_importance` |
| 22 | `GET /api/xai/local/{id}` | - | probability, drivers, protective, method | `local_explanation` |
| 23 | `GET /api/whatif/schema` | `?customer_id=` | feature controls + current values | working_df |
| 24 | `POST /api/whatif` | `{customer_id, changes{}}` | original, scenario, change, bands, verdict | `score_customers` |
| 25 | `GET /api/retention` | `?risk=&limit=` | suggestion rows + counts | `recommendations_dataframe` |
| 26 | `GET /api/batch/template` | - | CSV of 25 customers in the right shape | working_df |
| 27 | `POST /api/batch/predict` | multipart `file`, `include_drivers` | scored rows + summary | `validate_columns_for_prediction`, `build_batch_predictions` |
| 28 | `GET /api/monitoring` | - | active model metadata and metrics | persistence metadata |
| 29 | `POST /api/monitoring/drift` | multipart `file` | missing columns, missing %, new categories, mean shift, churn rate | logic of `page_monitoring.py` |

CSV downloads (risk table, recommendations, batch results) are generated in the browser from the rows the user is viewing.
Additive helpers beyond the Streamlit features: demo login (2, 3), sample batch file (26).

## 3. Feature inventory (every existing Streamlit feature)

| # | Streamlit page | Features that survive |
|---|---|---|
| F1 | **Dashboard** | KPI cards (total, churn rate, high-risk, critical-risk, avg probability) and the pre-model fallback (total/churn/avg tenure); churn donut; risk distribution; churn by contract; by tenure; top drivers; top-20 at-risk table; welcome empty state |
| F2 | **Data Upload** | CSV upload; sample dataset; 15-row preview; target + ID selection; advanced numeric/categorical override; quality report (rows, cols, duplicates, missing by column, warnings); training-readiness checks; prepare data |
| F3 | **Exploratory Analysis** | 7 KPIs; attribute filters; churn distribution; churn by attribute tabs; tenure group; numeric distribution by churn with feature picker; correlation heatmap |
| F4 | **Model Training** | dataset summary tiles; class distribution and imbalance ratio; test-size; imbalance strategy (class weights / SMOTE / none, with SMOTE fallback); model selection (3 required + 2 optional); recommend-by metric; train; comparison table; recommended model; save best model |
| F5 | **Model Evaluation** | ROC curves; PR curves; per-model confusion matrix; five metrics; active-model badge; accuracy caveat |
| F6 | **Customer Risk** | three threshold sliders; band counts and %; risk chart; filterable, searchable table; CSV download; "application-defined bands" note |
| F7 | **Customer 360** | customer search/select; ID, probability, risk badge; customer / service / billing groups; tenure; churn drivers; protective factors; retention actions with reasons and disclaimer |
| F8 | **Explainable AI** | global tabs (built-in, permutation, SHAP); SHAP-unavailable notice; local explanation per customer; method label; drivers and protective factors |
| F9 | **What-If Analysis** | customer picker; sliders (numeric) and selects (categorical); original vs scenario probability; change in points; verdict message; "model-based scenario analysis" label |
| F10 | **Retention Recommendations** | band filter (default High + Critical); max customers (5-500); recommendation table; counts; CSV download; rule reference |
| F11 | **Batch Prediction** | expected-columns notice; CSV upload; missing-column errors; missing-value warning; top-factors toggle (default on up to 300 rows); results table; CSV download |
| F12 | **Model Monitoring** | active model metadata and metrics; feature columns; drift check (missing columns, high missingness, unseen categories, mean comparison, new churn rate, imbalance warning) |
| F13 | **About Project** | problem statement, architecture, stack, XAI approach, risk scoring, what-if, dataset, base paper, privacy, future work |
| F14 | **Shell** | 13-page navigation; dataset and model status; base-paper citation; model restored from disk on start |

## 4. Screen map (as built)

New: **Landing** (`/`) and **Sign in** (`/login`, with the demo account). App routes sit inside the kit `AppShell`
(sidebar becomes a drawer plus bottom bar under 900px; topbar has API status, theme toggle, sign out).

| Route | Screen | Covers |
|---|---|---|
| `/` | Landing (Soft Pastel Calm hero, features, steps, facts, CTA, light and dark) | new |
| `/login` | Sign in with one-click demo | new |
| `/app` | Dashboard | F1 |
| `/app/data` | Data upload | F2 |
| `/app/eda` | Exploration | F3 |
| `/app/train` | Model training | F4 |
| `/app/evaluation` | Evaluation | F5 |
| `/app/risk` | Customer risk | F6 |
| `/app/customer` | Customer 360 (`?id=`) | F7 |
| `/app/explain` | Explainable AI (`?id=`) | F8 |
| `/app/whatif` | What-if (`?id=`) | F9 |
| `/app/retention` | Retention actions | F10 |
| `/app/batch` | Batch prediction | F11 |
| `/app/monitoring` | Monitoring | F12 |
| `/app/about` | About project | F13 |

Every data screen has a skeleton while loading, an empty state with an action (Quick start, Load sample, Train), an error
state naming what failed and what to do, and toast feedback on success. Extras: one-click **Quick start** (sample -> prepare
-> train -> save), confetti on save (skipped for reduced motion), downloadable sample batch file.

## 5. Checklist - every original feature still works

- [x] F1 Dashboard
- [x] F2 Data Upload
- [x] F3 Exploratory Analysis
- [x] F4 Model Training
- [x] F5 Model Evaluation
- [x] F6 Customer Risk
- [x] F7 Customer 360
- [x] F8 Explainable AI
- [x] F9 What-If Analysis
- [x] F10 Retention Recommendations
- [x] F11 Batch Prediction
- [x] F12 Model Monitoring
- [x] F13 About Project
- [x] F14 Shell status + model restore from disk
- [x] Landing page (new)
- [x] Demo login (new)

## 6. Verification record

| Check | Result |
|---|---|
| `npm run build` | passes |
| `scripts/smoke_test.py` (API, ~60 checks) | passes on the dev machine (pandas 2.2 / scikit-learn 1.5) and in a fresh `.venv` from `run.bat` (pandas 3.0 / scikit-learn 1.9) |
| `scripts/capture_screens.py` | all 16 screens captured with real data, console clean, no failed requests |
| 360 / 768 / 1440 px, light and dark | every `/app` screen: no horizontal overflow, no console errors |
| Reduced motion | all screens render; animations collapse (MotionConfig + CSS) |
| Keyboard | skip link, visible 3px focus ring, Escape closes drawer and dialogs, tabs use arrow keys |
| Auth | protected routes redirect to `/login`, bad password rejected, session cleared on sign out |
| Empty / error states | gates for no data, no model, no trained models; bad upload; CSV without a churn column |
| `run.bat` from scratch | creates `.venv`, installs, starts both servers on 8314 / 5314 |
