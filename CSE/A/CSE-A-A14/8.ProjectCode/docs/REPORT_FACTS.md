# REPORT FACTS - CSE-A-A14 (single source of truth for every submission document)

Everything below was **measured or read from this project**. Nothing is copied from the base paper or the templates.
Regenerate with `python scripts/make_report_facts.py` after re-running `scripts/run_experiments.py`,
`scripts/measure_api_latency.py` and `scripts/smoke_test.py`.

## 1. Identity

| | |
|---|---|
| Title | Customer Churn Prediction in Telecom Industry (Machine Learning Based Customer Retention System) |
| Product name in the UI | ChurnIQ (React interface) on the original Streamlit core |
| Batch | CSE-A, Batch A14 - Department of Computer Science and Engineering |
| Students (from `1.A14_BATCH_DETAILS.docx` and `Students.txt`) | ANANTULA SAI NIKHILA SRAVANI - 23K91A0512; AVULA ANUDEEP - 23K91A0518; B SANDEEP - 24K915A0503; DARAGANI VINOD KUMAR - 23K91A0558 |
| Guide | B. SRIKANTH (Assistant Professor, Dept of CSE - per `Documentary/Batch_14...docx`) |
| College | TKR College of Engineering & Technology (Autonomous) - appears only in `Documentary/Batch_14...docx`, not in the batch-details file the prompt designates. HOD, Principal, academic year: **unknown** -> leave `[...]` placeholders |
| Base paper | S.-V. Oprea and A. Bara, "Explaining Customer Churn Through Unified Perturbation-Based XAI Soft Computing," IEEE Access, vol. 14, pp. 24460-24478, 2026, doi 10.1109/ACCESS.2026.3663648 |
| Ports | backend 8314, frontend 5314 (Streamlit original: 8501) |

Note: `Documentary/...docx` spells two names differently (Boda Sandeep, 24K95A0503). The prompt names `1.*_BATCH_DETAILS.docx` and `Students.txt` as the source, and both agree with each other, so those spellings are used.

## 2. What the product actually is (read from the code)

* A **Streamlit** app (`app.py` + 13 pages in `pages/`) over a pure-Python core in `src/` (12 modules, ~1,200 lines), **untouched**.
* A **FastAPI** layer in `backend/` (~1,050 lines): 31 route handlers that only import and call `src/` functions. One in-memory `AppState` mirrors `st.session_state`; the saved model is restored from `models/*.pkl` at start-up.
* A **React 19 + Vite 8** frontend (`frontend/`, 16 page components incl. landing, sign-in and 404, ~2,600 lines of page code) built on the V4 "Soft Pastel Calm" kit: landing page, demo sign-in, Dashboard, Data upload, Exploration, Model training, Evaluation, Customer risk, Customer 360, Explainable AI, What-if, Retention actions, Batch prediction, Monitoring, About.
* **No database.** Data = CSV files; model = joblib files (`models/model.pkl`, `preprocessor.pkl`, `model_metadata.pkl`); runtime state = in-memory. The ER diagram in the documents is therefore the **logical data model** of the entities the code manipulates, and must be labelled as such.
* **No LLM / external API.** Retention advice is a local rule engine (`src/retention_engine.py`, 10 IF/THEN rules + 2 fallbacks).
* **SHAP is optional and NOT installed** on the measurement machine (`import shap` fails). Explanations therefore use the built-in fallbacks (coefficient x value for local; model importance + permutation importance for global). The code path for SHAP exists but **was not exercised**; do not report SHAP results.
* Demo auth (added in the frontend rebuild): HMAC-SHA256 signed bearer token, 12 h expiry, credentials from `.env` (`demo@churniq.com` / `Demo@1234`).

### Pipeline as implemented
1. `data_loader.load_csv` -> `detect_target_column` / `detect_id_column` -> `coerce_numeric_looking_columns` -> `profile_dataset`.
2. `preprocessing.clean_missing_and_duplicates` (drop exact duplicates; report missing).
3. `train_test_split_data`: stratified, `test_size` 0.10-0.40 (default 0.20), `random_state=42`.
4. `build_preprocessor`: numeric = median impute + StandardScaler; categorical = most-frequent impute + OneHotEncoder(handle_unknown="ignore"). Fit on the training split only.
5. Imbalance: `class_weight="balanced"` (default) | SMOTE on the transformed training split only (needs imbalanced-learn; falls back to class_weight if missing) | none.
6. `train_models.MODEL_REGISTRY`: Logistic Regression (max_iter 2000), Decision Tree (max_depth 8, min_samples_leaf 10), Random Forest (300 trees, max_depth 12, min_samples_leaf 5), Gradient Boosting (200 trees, depth 3, lr 0.08), Hist Gradient Boosting (depth 6, lr 0.08). Required three: LR, DT, RF. GB/HGB take no class_weight, so "class weights" does not rebalance them.
7. `evaluation.evaluate_model`: accuracy, precision, recall, F1, ROC-AUC, confusion matrix, ROC and PR curves. `select_best_model` picks by the chosen metric (default F1, never accuracy alone).
8. Save: `persistence.save_artifacts` -> `models/`. Probability = `predict_proba[:,1]*100`, rounded to 2 dp.
9. Risk bands (`utils.assign_risk_category`, defaults 30/60/80): Low <30, Medium 30-<60, High 60-<80, Critical >=80. Thresholds are user-editable and validated server-side (422 unless Low is 5-50, Medium is 5+ points above Low and at most 85, High is 5+ points above Medium and at most 95).
10. Explanations (`explainability`): global = built-in importance, permutation importance (<=300 test rows, 5 repeats), SHAP (if available); local = top-5 positive / top-5 negative contributors.
11. Retention engine: rules on contract, tech support, online security, monthly charges >= 80, electronic check, tenure <= 6, fibre optic, no streaming add-ons, paperless + e-check, Critical band; nine are gated on probability >= 60 and the tenth on the Critical band; two fallback messages cover low and moderate risk.
12. What-if: re-scores a customer with edited attributes (model-based scenario analysis, not causal). Batch: validates columns, scores, `predicted_churn` = probability >= 50, optional top-3 drivers (default on up to 300 rows).
13. Monitoring: active model metadata + drift check (missing columns, missingness, unseen categories, mean shift, churn rate).

## 3. Dataset facts

| | |
|---|---|
| File | `data/customer_churn.csv` |
| Origin | **synthetic, produced by src/sample_data.py (seed 42)** - NOT the real Telco (IBM/Kaggle) data. Same column schema as the public Telco dataset. Churn is generated from a latent logistic risk score plus Gaussian noise (sd 0.55) |
| Licence | none needed - generated by this project's own code (`src/sample_data.py`) |
| Rows x columns | 1000 x 21 |
| Duplicates / missing cells | 0 / 0 |
| Target / ID | `Churn` (Yes/No) / `customerID` |
| Features | 19 raw (4 numeric: SeniorCitizen, tenure, MonthlyCharges, TotalCharges; 15 categorical) -> 45 after one-hot |
| Class balance | retained 736 (73.6%), churned 264 (26.4%), imbalance ratio 2.79:1 |
| Split used for headline numbers | stratified 20% test, random_state 42: 800 train / 200 test rows, **53 churners in the test set** |

**Consequences to state plainly:** the data are synthetic; the test set is only 200 rows (53 churners), so single-split metrics carry wide error bars (see section 4.2). The base paper used the real 7,043-row Telco data with a 30% test split (2,113 rows) - the two are **not comparable**.

## 4. Real model metrics

Measured by `scripts/run_experiments.py` (same src/ functions and split rule as the Model Training page).
Environment of record: Python 3.11.9, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.4.6 (the `.venv` that `run.bat` builds; this is the environment of the screenshots and of the API). Raw output: `experiments/churn_synthetic/metrics.json`.

### 4.1 Headline - 80/20 stratified split, seed 42, class weights (the app default)

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.6300 | 0.3846 | 0.6604 | 0.4861 | 0.7224 |
| Decision Tree | 0.6150 | 0.3378 | 0.4717 | 0.3937 | 0.6081 |
| Random Forest | 0.6650 | 0.4054 | 0.5660 | 0.4724 | 0.7111 |
| Gradient Boosting | 0.7450 | 0.5357 | 0.2830 | 0.3704 | 0.6970 |
| Hist Gradient Boosting | 0.7100 | 0.4000 | 0.1887 | 0.2564 | 0.6855 |

Recommended on F1 (default): **Logistic Regression**; best ROC-AUC: **Logistic Regression**; best recall: **Logistic Regression**. The saved active model in `models/` is Logistic Regression with exactly these LR numbers.

Confusion matrices (test set, 200 rows: 147 retained, 53 churners):

| Model | TN | FP | FN | TP |
|---|---|---|---|---|
| Logistic Regression | 91 | 56 | 18 | 35 |
| Decision Tree | 98 | 49 | 28 | 25 |
| Random Forest | 103 | 44 | 23 | 30 |
| Gradient Boosting | 134 | 13 | 38 | 15 |
| Hist Gradient Boosting | 132 | 15 | 43 | 10 |

### 4.2 Stability - the 200-row split is noisy

Stratified 5-fold cross-validation (class weights, mean ± sd over folds, 200 held-out rows per fold):

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.6480 ± 0.0396 | 0.3953 ± 0.0455 | 0.6246 ± 0.0844 | 0.4833 ± 0.0547 | 0.6945 ± 0.0463 |
| Decision Tree | 0.6070 ± 0.0236 | 0.3494 ± 0.0254 | 0.5643 ± 0.0390 | 0.4313 ± 0.0281 | 0.6226 ± 0.0201 |
| Random Forest | 0.6700 ± 0.0252 | 0.4070 ± 0.0341 | 0.5452 ± 0.0977 | 0.4634 ± 0.0506 | 0.6974 ± 0.0417 |

Five random 80/20 splits (seeds 0-4, class weights, mean ± sd):

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.6650 ± 0.0200 | 0.4155 ± 0.0248 | 0.6566 ± 0.1011 | 0.5075 ± 0.0443 | 0.7231 ± 0.0344 |
| Decision Tree | 0.6040 ± 0.0258 | 0.3593 ± 0.0260 | 0.6302 ± 0.0560 | 0.4573 ± 0.0332 | 0.6484 ± 0.0396 |
| Random Forest | 0.7040 ± 0.0284 | 0.4543 ± 0.0356 | 0.5509 ± 0.0524 | 0.4965 ± 0.0325 | 0.7102 ± 0.0171 |

Reading: Logistic Regression and Random Forest are within one standard deviation of each other on F1 and ROC-AUC; Logistic Regression has the higher recall, Random Forest the higher precision and accuracy; the Decision Tree is weakest on accuracy, precision, F1 and ROC-AUC (its recall is not the lowest). ROC-AUC is about 0.70-0.72, i.e. **moderate, not strong**.

### 4.3 Imbalance strategy (single split, seed 42)

SMOTE:

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.6850 | 0.4375 | 0.6604 | 0.5263 | 0.7283 |
| Decision Tree | 0.6350 | 0.3387 | 0.3962 | 0.3652 | 0.6430 |
| Random Forest | 0.7100 | 0.4359 | 0.3208 | 0.3696 | 0.7032 |
| Gradient Boosting | 0.7450 | 0.5278 | 0.3585 | 0.4270 | 0.7288 |
| Hist Gradient Boosting | 0.7200 | 0.4545 | 0.2830 | 0.3488 | 0.6994 |

No handling:

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.7450 | 0.5556 | 0.1887 | 0.2817 | 0.7202 |
| Decision Tree | 0.7050 | 0.4062 | 0.2453 | 0.3059 | 0.5745 |
| Random Forest | 0.7550 | 0.8333 | 0.0943 | 0.1695 | 0.7176 |
| Gradient Boosting | 0.7450 | 0.5357 | 0.2830 | 0.3704 | 0.6970 |
| Hist Gradient Boosting | 0.7100 | 0.4000 | 0.1887 | 0.2564 | 0.6855 |

Findings: without imbalance handling recall collapses (LR 0.1887, RF 0.0943) while accuracy looks fine (0.745, 0.755) - the reason the app selects on F1 rather than accuracy. SMOTE gave the best single-split F1 for LR (0.5263) but was not tested beyond one split.

### 4.4 Environment sensitivity (honest caveat)

The same script under scikit-learn 1.5.0 / pandas 2.2.1 gives identical Logistic Regression results but a different Random Forest on the 200-row split (accuracy 0.7200 vs 0.6650, F1 0.4815 vs 0.4724). Archived: `experiments/churn_synthetic/metrics_sklearn1.5.0.json`. Tree ensembles on 800 training rows are version-sensitive; the numbers above are specific to the environment of record.

### 4.5 Drivers (Logistic Regression, class weights)

Largest |coefficient| (model importance): Contract: Month-to-month (0.825), Contract: Two year (0.791), MonthlyCharges (0.558), PaymentMethod: Bank transfer (automatic) (0.408), tenure (0.400), PaymentMethod: Electronic check (0.388).
Permutation importance (<= 300 test rows, 5 repeats, default scoring = accuracy): MonthlyCharges (0.042), Contract: Month-to-month (0.028), DeviceProtection: Yes (0.008), OnlineBackup: Yes (0.006); the rest are <= 0.01 (noise-level).
Generator ground truth for comparison: month-to-month contract (+1.3), electronic check (+0.6), tenure (-1.6 over 72 months), no tech support (+0.45), no online security (+0.35), fibre (+0.35), monthly charges, senior citizen, no partner. The model recovers contract type, charges and tenure as top drivers - consistent with the generator, which is a check on the pipeline, **not** evidence about real telecom customers.

### 4.6 Risk segmentation of the 1,000 customers (active model, default thresholds 30/60/80)

Low 253 (25.3%), Medium 481 (48.1%), High 213 (21.3%), Critical 53 (5.3%); mean probability 45.89%. (Scored on the training data too, so this describes the portfolio view the dashboard shows, not generalisation.) Class-weighted LR inflates probabilities (mean 45.9% vs 26.4% actual churn) - the scores are **rankings, not calibrated probabilities** (measured in 4.7).

### 4.7 Extra analyses on the Logistic Regression test predictions (`scripts/make_figures.py` -> `experiments/churn_synthetic/extra_analysis.json`)

* **Calibration:** Brier score 0.2131 (a constant base-rate predictor scores 0.1948, so the model is **not better than no-skill on Brier**); mean predicted probability 0.4608 vs observed churn 0.265. Every reliability bin over-predicts: 0.0-0.2: predicted 0.13 vs observed 0.04 (n=27); 0.2-0.4: predicted 0.32 vs observed 0.15 (n=47); 0.4-0.6: predicted 0.50 vs observed 0.25 (n=73); 0.6-0.8: predicted 0.69 vs observed 0.49 (n=47); 0.8-1.0: predicted 0.82 vs observed 0.67 (n=6).
* **Decision threshold (test split):** at 0.50 (the batch-scoring cut-off) precision 0.3846, recall 0.6604, F1 0.4861; F1 is flat between 0.40 and 0.60 (best 0.5124 at 0.55 and 0.5122 at 0.45); at 0.30 recall 0.9623 but precision 0.3248; at 0.70 recall 0.1887, precision 0.4545.
* **Targeting value (ranking by predicted probability, 200 test customers, 53 churners):** contacting the top 10% (20 customers) captures 9 churners (precision 0.45, lift 1.698x); top 20% (40) captures 21 = 0.3962 of churners (precision 0.525, lift 1.981x); top 30% (60) captures 28 = 0.5283; top 50% (100) captures 41 = 0.7736. Lift is moderate (about 1.5-2x); with 20-60 contacts the counts are small.
* **Churn rate by segment (all 1,000 rows):** month-to-month 34.1%, one year 19.2%, two year 12.5%; tenure 0-12 months 36.6% vs 49+ months 18.7%; fibre optic 32.7%, DSL 25.1%, no internet 14.7%; electronic check 33.4% vs bank transfer 18.3%. These follow the relationships built into the generator (section 4.5).

## 5. Performance (measured)

Machine: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro 10.0.26200, Python 3.11.9, Node v24.19.0, no GPU used.

| Measurement | Result |
|---|---|
| Single-customer scoring (preprocess + LR predict_proba), 200 runs | median 19.07 ms, p95 33.66 ms (venv: pandas 3.0.6 / scikit-learn 1.9.1; the same measurement under pandas 2.2.1 / scikit-learn 1.5.0 gave median 2.85 ms, p95 3.51 ms) |
| Score all 1,000 customers | 35.4 ms |
| Train 5 models, class weights (wall time, incl. evaluation) | 2.96 s ; RF alone 1.117 s |
| API (127.0.0.1), median of 10: dashboard / customer 360 / local explanation / what-if / retention / EDA | 93.8 / 79.7 / 68.3 / 64.6 / 77.2 / 84.8 ms |
| API: batch predict 25 rows (no drivers), median of 5 | 70.3 ms |
| API one-off: load sample / prepare / train 3 models / save model | 181.6 / 38.0 / 1515.3 / 89.1 ms |

Finding: via the hostname `localhost` every request costs an extra ~2.04 s on this Windows machine (IPv6 `::1` is tried first; uvicorn listens on 127.0.0.1 only). Over `127.0.0.1`, which the Vite proxy uses, the numbers above hold. The smoke test's default base URL is `localhost`, so it takes ~95 s instead of a few seconds. Not fixed (out of scope); mention as a known quirk.

## 6. Testing (real)

| Test | Result |
|---|---|
| `scripts/smoke_test.py` - end-to-end API walk, stdlib only | **63 PASS, 0 FAIL** (output archived in `experiments/churn_synthetic/smoke_test_output.txt`); covers health, auth (401 / bad password), load sample, preview, config, quality, prepare, EDA + filter, train (incl. 422 on empty selection), results, evaluation, save, dashboard, risk + threshold validation, customers, Customer 360, 404, XAI global/local, what-if, retention, batch template + predict + 422 on missing columns, monitoring + drift, CSV upload, non-CSV rejection |
| `tests/` pytest unit tests of the `src/` core | **44 passed** in the venv (pandas 3.0.6) and **44 passed** on pandas 2.2.1 (output: `experiments/churn_synthetic/pytest_output.txt`) |
| Defect found by the tests and fixed | `src/data_loader.py` tested `dtype == object` in three places, which is False for the pandas 3 string dtype: blank `TotalCharges` strings were not coerced to numbers and labels such as Churned/Retained were mishandled (Yes/No and the synthetic sample were unaffected). Fixed with a helper `_is_text()` that accepts object and string dtypes; the two regression tests now pass on both pandas versions |
| `npm run build` (frontend) | passes (Vite 8) |
| Browser check (Playwright, Chrome) `scripts/capture_screens.py` | all 16 screens captured with real data; console clean; no failed requests |
| Responsive / theme / accessibility | 360, 768, 1440 px in light and dark: no horizontal overflow; reduced-motion; keyboard (skip link, focus ring, Esc closes overlays) - checked manually via Playwright during the build, **not** with an automated accessibility tool |
| `run.bat` from scratch | creates `.venv`, installs, starts API (8314) and web (5314) |

**Not done:** no load / concurrency test (single-user in-memory design), no penetration test, no user-acceptance study with real users, no cross-browser test beyond Chrome, no test of the SHAP code path (shap not installed), no cost-sensitive (monetary) evaluation.

## 7. Endpoints (29 behaviours; `backend/main.py`)

Public: `GET /api/health`, `POST /api/auth/login`. Bearer-protected: `GET /api/auth/me`, `GET /api/state`, `POST /api/data/sample`, `POST /api/data/upload`, `GET /api/data/preview`, `GET|PUT /api/data/config`, `GET /api/data/quality`, `POST /api/data/prepare`, `GET /api/eda`, `GET /api/dashboard`, `POST /api/models/train`, `GET /api/models/results`, `POST /api/models/save`, `GET /api/evaluation`, `GET|PUT /api/risk/thresholds`, `GET /api/risk`, `GET /api/customers`, `GET /api/customers/{id}`, `GET /api/xai/global`, `GET /api/xai/local/{id}`, `GET /api/whatif/schema`, `POST /api/whatif`, `GET /api/retention`, `GET /api/batch/template`, `POST /api/batch/predict`, `GET /api/monitoring`, `POST /api/monitoring/drift`. Interactive docs at `/docs`. Errors: 401 (token), 404 (unknown customer), 409 (data/model not ready), 422 (validation) with a plain-language `detail`.

## 8. Technology stack (versions measured)

Python 3.11.9; scikit-learn 1.9.1 (venv) / 1.5.0 (system); pandas 3.0.6 / 2.2.1; numpy 2.4.6 / 1.26.4; imbalanced-learn; joblib; plotly (Streamlit charts); Streamlit (original UI); FastAPI 0.143.3; uvicorn 0.54.0; React 19.3, Vite 8.3, react-router 7, Recharts 3, framer-motion 14, GSAP 3, Lenis, canvas-confetti, lucide-react; git.

## 9. Screenshot inventory (`docs/screenshots/`, all 1440x900, real data: 1,000 synthetic customers, three models trained, Logistic Regression active)

* `01_landing_light.png`
* `02_landing_dark.png`
* `03_login.png`
* `04_dashboard.png`
* `05_data.png`
* `06_explore.png`
* `07_train.png`
* `08_evaluation.png`
* `09_risk.png`
* `10_customer360.png`
* `11_explain.png`
* `12_whatif.png`
* `13_retention.png`
* `14_batch.png`
* `15_monitoring.png`
* `16_about.png`
* `17_dashboard_dark.png`
* `18_risk_tablet.png`
* `19_customer360_phone.png`
* `20_dashboard_phone.png`

Screens 01-16 are 1440x900 and were re-captured with the API on its default risk thresholds (30 / 60 / 80), so the dashboard and risk counts (253 / 481 / 213 / 53) match section 4.6; screens 17-20 (dark theme, 768 px and 360 px layouts) come from `scripts/capture_extra.py`. An earlier capture had been taken after the smoke test left the thresholds at 25 / 55 / 75; the smoke test now restores the defaults.

## 10. Base paper vs this project (use for "comparison with the base paper")

| | Base paper (Oprea & Bara, IEEE Access 2026) | This project |
|---|---|---|
| Data | Real Telco churn, 7,043 rows, 21 columns, 26.5% churn (1,869 churners), Kaggle/IBM | **Synthetic**, 1,000 rows, same schema, 26.4% churn |
| Split | 70/30, test = 2,113 rows | 80/20 stratified, test = 200 rows |
| Classifiers | LR, SVC, RF, Balanced RF, CatBoost, XGBoost, LightGBM | LR, Decision Tree, RF (required) + GB, HistGB (optional) |
| Imbalance | class_weight, scale_pos_weight | class_weight, SMOTE (train only), none |
| Objective metric | Recall (primary) | F1 by default, user-selectable (accuracy/precision/recall/F1/ROC-AUC) |
| Reported (Table 2, accuracy / recall / precision) | LR 0.7120/0.4112/0.6210; SVC 0.7419/0.5369/0.6319; RF 0.7932/0.5634/0.6734; BRF 0.7558/0.8223/0.6327; CatBoost 0.6990/0.9077/0.4719; XGB 0.7596/0.7300/0.5427; LGBM 0.7317/0.8293/0.5037. ROC-AUC (Fig. 5): CB 0.86, XGB 0.83, LGBM 0.85 | See section 4 |
| Explainability | SHAP, LIME and a unified perturbation-based explainer (RNP, FA, IM, AP); recall-drop ranking; Spearman 0.8125, Kendall 0.7126, Jaccard 0.6885 vs SHAP; runtime SHAP 289.4 s, LIME 35.1 s, PBE 18.5 s | Built-in importance, permutation importance (one perturbation mechanism), local coefficient-weighted contributions; SHAP code path present but unmeasured. **No unified PBE, no LIME, no SHAP-vs-PBE statistics** |
| Beyond the paper | - | Per-customer risk bands, Customer 360, what-if, rule-based retention actions, batch scoring, drift check, saved-model restore, web UI |
| Driver findings | Month-to-month contracts, high monthly charges, tenure < 20 months | Same three drivers recovered, but on data that was *generated* with those relationships |

The project is an **applied extension of the base paper's motivation**, not a reproduction (README states this). It must not claim to match or beat the paper's metrics.

## 11. Gaps to state plainly in every document

1. Data are synthetic; no real operator data were available. No claim about real-world accuracy.
2. Test set 200 rows / 53 churners; cross-validation and five splits show sd of 0.03-0.10 on several metrics.
3. ROC-AUC about 0.70-0.72; F1 about 0.46-0.51 for the best models. Probabilities are not calibrated (Brier 0.213 vs 0.195 for a constant base-rate predictor; every reliability bin over-predicts).
4. SHAP not installed -> SHAP explanations not demonstrated; fallbacks are approximations.
5. No database, no multi-user support, no persistence of the dataset or training comparison across restarts; demo login only (shared account, no roles).
6. Retention rules are heuristics written by the team; their business effect was **not** measured (no campaign data).
7. No user-acceptance study; no load test; browser coverage = Chrome.
8. No LIME, no unified perturbation explainer, no gradient-boosting libraries (XGBoost/LightGBM/CatBoost) - only scikit-learn models.
