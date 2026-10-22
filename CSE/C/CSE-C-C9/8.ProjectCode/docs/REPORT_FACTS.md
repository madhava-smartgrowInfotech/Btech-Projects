# REPORT FACTS - FinSight AI (Batch CSE-C-C9)

Single source of truth for every document. All numbers come from `artifacts/*.json`
(`metrics.json`, `model_comparison.json`, `validation_report.json`, `stats_report.json`,
`shap_global.json`, `forecast.json`, `training_summary.json`) and `artifacts/report_metrics.json`
(re-derived by `scripts/report_metrics.py`, which reproduces the stored metrics exactly), plus the
test and latency runs of 2026-10-22.

## 1. Identity
- Project: AI-Based Financial Identification Based On Demography and Financial Forecasting
- Product: **FinSight AI**; batch CSE-C-C9 (Batch C-09); TKR College of Engineering & Technology (Autonomous), Dept. of CSE
  (name taken from `Documentary/Batch_C09_...docx`). HOD / Principal / academic year: not stated anywhere -> placeholders.
- Students: Mohd Ahmed 23K91A05F7; Manne Upender 23K91A05E6; Padala Rajesh 23K91A05H7; Madagouni Harshavardhan Goud 23K91A05D5
- Guide: B Srikanth (designation unknown -> "Project Guide")
- Base paper: Y. Kim and E. J. Sun, "An Explainable Machine Learning Framework for Organizational Financial Distress Detection:
  Evidence From Korean Hospital Panel Data," IEEE Access, vol. 14, 2026, DOI 10.1109/ACCESS.2026.3709346 (PDF in `Documentary/`).
- Ports: API (Flask) 8409, frontend (React/Vite) 5409. Python 3.11.9, Node 24.19.

## 2. Dataset
- Classification: UCI Adult / Census Income, https://archive.ics.uci.edu/dataset/20/census+income (CC BY 4.0 per UCI page).
  `data/raw/adult.data` 32,561 rows + `adult.test` 16,281 rows = **48,842** rows, 15 columns.
- Target: income >50K (positive, 23.93 % of all rows) vs <=50K - adapted as a "financial-profile signal", NOT a credit score.
- Missing ("?") cells in raw data: workclass 2,799; occupation 2,809; native-country 857.
- Split: stratified 80/20, random_state 42 -> **train 39,073 / test 9,769** (test: 7,431 <=50K, 2,338 >50K); 5-fold stratified CV on train.
- Features: 12 user inputs (age, workclass, education, marital-status, occupation, relationship, race, sex, capital-gain,
  capital-loss, hours-per-week, native-country) + education-num + fnlwgt (median-imputed at prediction time) + engineered:
  net-capital, capital-intensity, log-capital-gain/loss, has-capital-gain/loss, capital-position, hours-band, age-band,
  education-tier, region, employment-stability -> 26 columns in `training_summary.features_used`.
- Forecasting data: **synthetic** monthly "Household Financial Conditions Index", Jan 2015-Dec 2025 (132 points; trend 100+0.35t,
  sinusoidal seasonality amplitude 4, Gaussian noise sd 1.6, mid-2020 shock -7 for Mar-Aug 2020; seed 42). Documented as
  illustrative in `data/README.md`. No real macroeconomic series is used. Real macro indicators (inflation, GDP) are NOT integrated.
- No database: the product has no RDBMS (batch doc mentions MySQL; not implemented). State = trained `.pkl` pipelines + JSON artifacts
  + browser sessionStorage (what-if baseline in the React app; Flask session cookie on the Jinja pages) + browser localStorage (theme, demo login).

## 3. Models and real metrics (held-out test set, threshold 0.5, n = 9,769)
| Model | Acc | Prec | Rec | F1 | ROC-AUC | CV AUC mean +/- sd | PR-AUC | Brier |
|---|---|---|---|---|---|---|---|---|
| Logistic Regression | 0.8599 | 0.7568 | 0.6108 | 0.6760 | 0.9140 | 0.9133 +/- 0.0013 | 0.7867 | 0.0976 |
| Random Forest | 0.8597 | 0.7402 | 0.6373 | 0.6849 | 0.9100 | 0.9079 +/- 0.0016 | 0.7955 | 0.0981 |
| Gradient Boosting | 0.8697 | 0.7915 | 0.6185 | 0.6944 | 0.9247 | 0.9204 +/- 0.0022 | 0.8228 | 0.0903 |
| **XGBoost (selected)** | **0.8782** | **0.7917** | **0.6664** | **0.7236** | **0.9319** | **0.9293 +/- 0.0011** | 0.8381 | 0.0857 |

Confusion matrices (TN / FP / FN / TP): LR 6972/459/910/1428; RF 6908/523/848/1490; GB 7050/381/892/1446; **XGB 7021/410/780/1558**
(XGB specificity 0.9448). Per-fold CV AUC (XGB): 0.9295, 0.9275, 0.9310, 0.9295, 0.9290.
Hyperparameters: LR C=1, max_iter 2000 (scaled numerics); RF 300 trees; GB defaults; XGB 400 trees, depth 6, lr 0.05, subsample 0.9,
colsample 0.9, lambda 1. No hyper-parameter search was run; no class re-balancing. Selection by test ROC-AUC (best by test set,
a mild optimism the report notes; CV ranking agrees).

XGBoost threshold sweep (test): t=0.2 P .5825 R .8922 F1 .7048 | 0.3 P .6531 R .8221 F1 .7279 | 0.35 P .6901 R .7810 F1 .7327 |
0.4 P .7219 R .7417 F1 .7316 | 0.5 P .7917 R .6664 F1 .7236 | 0.6 P .8523 R .5851 F1 .6939 | 0.7 P .8996 R .4906 F1 .6349 | 0.8 P .9573 R .3832 F1 .5473.
Calibration (10 bins): predicted vs observed track closely (e.g. 0.0-0.1: 0.0212 vs 0.0221, n=5336; 0.9-1.0: 0.9843 vs 0.9871, n=698;
largest gap 0.4-0.5: 0.447 vs 0.4055).
Profile bands (app rule: p>=0.60 Established/Low risk, 0.35-0.60 Developing/Moderate, <0.35 Emerging/High) on test: Emerging 7,123
(actual >50K rate 7.19 %), Developing 1,041 (44.00 %), Established 1,605 (85.23 %).

Statistics (train set, `stats_report.json`): correlation with target: age 0.2293, education-num 0.3354, hours-per-week 0.2306,
net-capital 0.2124. Logit coefficients: const -8.445, age 0.0444, education-num 0.3374, hours 0.0418, net-capital 0.00024; all p < 0.001 (reported 0.0).

SHAP global top-15 (mean |SHAP|, XGB, 500-row sample): marital-status=Married-civ-spouse 1.0116; age 0.6653; education-num 0.4445;
capital-gain 0.4007; hours-per-week 0.3153; capital-loss 0.1385; sex=Female 0.1264; occupation=Exec-managerial 0.1256;
occupation=Prof-specialty 0.1204; fnlwgt 0.1007; marital=Never-married 0.0894; relationship=Own-child 0.0884;
occupation=Other-service 0.0877; relationship=Wife 0.0866; capital-intensity 0.0806.

Forecast (Holt-Winters additive trend + additive seasonality, period 12, 12-month horizon, +-1.96 sigma intervals, residual sd 1.659):
last observed 141.7 (Dec 2025) -> Dec 2026 forecast 146.55 (95 % band 143.30-149.80), +3.46 %, "upward". Back-test (fit 2015-2024, predict
2025 of the synthetic series): MAE 1.429, RMSE 1.600, MAPE 0.997 %, naive last-value MAE 4.504, 95 % interval coverage 100 % (12/12).
This evaluates the method against its own synthetic generator only - NOT real-world forecasting accuracy.

## 4. Comparison with base paper (different problem and data - not a like-for-like comparison)
Base paper: 165 Korean hospitals, 825 hospital-year rows (2019-2023), 236 line items -> 11 features, target deficit (net income < 0),
41.2 % positive. Hospital-level Group K-Fold AUC: XGBoost 0.842, GB 0.840, RF 0.831, LR 0.776, MLP 0.772; temporal (train 2019-22,
test 2023) 0.780; forward next-year 0.772; rolling-origin mean 0.800; Altman Z'' 0.680; SHAP top features material-cost ratio 0.777,
labor-cost ratio 0.729. This project: individuals, 48,842 rows, XGB test AUC 0.9319 / CV 0.9293; same ranking of model families
(XGB > GB > RF/LR; here LR 0.914 > RF 0.910 by AUC). Datasets, targets and validation protocols differ (one row per person here, so
no entity-grouped or temporal validation; no counterfactual/econometric analysis reproduced).

## 5. Application
Flask API + React 19/Vite frontend (41 source files, 11 pages). Frontend routes: `/` landing, `/login` (sample demo gate
demo@finsight.ai / finsight123, browser-only), `/app` dashboard, `/app/assess`, `/app/result`, `/app/explain`, `/app/forecast`,
`/app/whatif`, `/app/performance`, `/app/about`, 404. Original Jinja pages still at :8409.
Endpoints: GET /health; GET /; GET|POST /assess; GET /explain; GET /forecast; GET|POST /whatif; GET /performance; GET /about;
GET /artifacts/<png>; POST /api/predict; GET /api/forecast; GET /api/options; GET /api/dashboard; GET /api/explain;
GET /api/performance; POST /api/whatif.
Modules: app/__init__.py (factory), routes.py (228 lines), api.py (117), services/predictor.py (270), whatif.py (44), forecaster.py (12),
utils/validation.py (93); scripts/train.py (353), feature_engineering.py (288), forecast.py (94), models.py, evaluate.py,
smoke_test.py, capture_screens.py, capture_extra_screens.py, report_metrics.py.
Validation: required, allowed-set and numeric-range checks (age 16-100, hours 1-99, gains/losses 0-1,000,000), server side.
Security: demo login is client-side only (not real authentication); local-only binding 127.0.0.1; no PII stored; Flask secret key default
from env var FINSIGHT_SECRET_KEY.
Explainability: SHAP TreeExplainer (tree_path_dependent); global artifacts at train time; local SHAP live per request.
What-if: overrides gains/losses/hours/education; reports delta in score, profile and risk change. Labelled non-causal.

## 6. Testing and performance (run 2026-10-22)
- `pytest`: **9 passed** (7 in tests/test_app.py + 2 in tests/test_features.py) in ~9.4 s.
- `scripts/smoke_test.py`: **35/35 checks passed** (API on 8409 and proxy on 5409).
- API latency, 127.0.0.1, 40 calls each, median / p95 ms: POST /api/predict 68.9 / 116.9; POST /api/whatif 136.1 / 193.7;
  GET /api/forecast 7.3 / 27.1; GET /api/performance 9.1 / 26.1; GET /health 6.7 / 19.5; predict via 5409 proxy 71.8 / 165.8.
  In-process `predict_profile` (incl. SHAP): median 52.4 ms, p95 86.7 ms (30 calls).
- Measured on: Intel Core i5-12500, 15.7 GB RAM, Windows 11 Pro, CPU only; Python 3.11.9, scikit-learn 1.9.1, XGBoost 3.2.0, SHAP 0.51.0,
  statsmodels 0.15.0, Flask 3.1.3. (Persisted .pkl files were written by an older scikit-learn/XGBoost and emit version warnings on load; metrics reproduce exactly.)
- Not done: load/concurrency testing, browser-matrix testing, formal user-acceptance study, security audit, front-end unit tests.
- Example outputs: Adult row 1 (39, State-gov, Bachelors, Never-married, Adm-clerical, gains 2174, 40 h) -> score 1.1 % (p 0.0109), Emerging/High;
  what-if gains 80,000 + 50 h -> 99.5 %, Established/Low (+98.43 pp). 52-y Masters Exec-managerial married, gains 7,688, 50 h -> 99.9 % Established/Low.
  34-y Some-college Sales married Wife, 42 h -> 46.8 % Developing/Moderate. Invalid age (-5 / 7) -> HTTP 400 with message.

## 7. Known limitations (state plainly)
- Data are 1994 US census records; the target is income, not creditworthiness/distress; not a credit decision.
- Forecast series is synthetic; macro indicators from the abstract are not integrated; no individual-level forecast.
- Sex, race, marital status are model inputs (marital status and sex among top SHAP features) -> fairness/bias risk; no fairness audit performed.
- Extreme what-if values (gains 80,000) swing the score ~98 pp: model extrapolates from sparse capital-gain data (a spike in training data at
  99,999 is a known Adult quirk).
- Selection on test AUC, no hyper-parameter tuning, no external validation set, no DeLong significance tests.
- Demo login is cosmetic. No database, no user accounts, no audit log. Docker image targets Flask pages only (port 5000), not the React frontend.

## 8. Screenshot inventory (`docs/screenshots/`, 1440x900 unless full-page; real model output)
01_landing-light, 02_landing-dark, 03_login, 04_dashboard, 05_assessment (filled), 06_result (Emerging case), 07_explainability,
08_forecast, 09_whatif (baseline vs scenario), 10_performance, 11_about, 12_not-found, 13_validation-error (age 7),
14_result-established, 15_result-established-full (full page), 16_result-developing, 17_explainability-full, 18_forecast-full,
19_performance-full. Toast notifications ("Analysis complete") appear in some captures; they are part of the real UI.
