"""Build docs/REPORT_FACTS.md from the real experiment artefacts (single source of truth for the documents).

    python scripts/make_report_facts.py
Inputs : experiments/churn_synthetic/{metrics.json, api_latency.json, smoke_test_output.txt, pytest_output.txt}
Output : docs/REPORT_FACTS.md
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments", "churn_synthetic")
M = json.load(open(os.path.join(EXP, "metrics.json"), encoding="utf8"))
L = json.load(open(os.path.join(EXP, "api_latency.json"), encoding="utf8"))
M15 = json.load(open(os.path.join(EXP, "metrics_sklearn1.5.0.json"), encoding="utf8"))
smoke = open(os.path.join(EXP, "smoke_test_output.txt"), encoding="utf8").read()
n_pass = len(re.findall(r"^PASS", smoke, re.M))
n_fail = len(re.findall(r"^FAIL", smoke, re.M))
pyt_path = os.path.join(EXP, "pytest_output.txt")
pyt = open(pyt_path, encoding="utf8").read() if os.path.exists(pyt_path) else ""
_m = re.findall(r"(\d+) passed", pyt)
pyt_line = (f"**{_m[0]} passed** in the venv (pandas 3.0.6) and **{_m[1]} passed** on pandas 2.2.1" if len(_m) >= 2 else "not run")
_main = open(os.path.join(ROOT, "backend", "main.py"), encoding="utf8").read()
n_routes = len(re.findall(r"@(?:private|public|app)\.(?:get|post|put)", _main))

ex = json.load(open(os.path.join(EXP, "extra_analysis.json"), encoding="utf8"))
sw = {str(x["threshold"]): x for x in ex["threshold_sweep"]}
lf = {str(x["top_fraction"]): x for x in ex["targeting_lift"]}
rel_txt = "; ".join(f"{r['bin']}: predicted {r['mean_predicted']:.2f} vs observed {r['observed_churn']:.2f} (n={r['n']})" for r in ex["reliability"])

K = ("accuracy", "precision", "recall", "f1_score", "roc_auc")
H = "| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |\n|---|---|---|---|---|---|\n"


def table(rows):
    return H + "\n".join(f"| {n} | " + " | ".join(f"{r[k]:.4f}" for k in K) + " |" for n, r in rows.items())


def table_ms(d):
    return H + "\n".join(
        f"| {n} | " + " | ".join(f"{v[k]['mean']:.4f} ± {v[k]['std']:.4f}" for k in K) + " |" for n, v in d.items())


cw = M["app_default_split"]["class_weight"]["models"]
sm = M["app_default_split"]["smote"]["models"]
no = M["app_default_split"]["none"]["models"]
cm = "\n".join(f"| {n} | {r['confusion_matrix'][0][0]} | {r['confusion_matrix'][0][1]} | {r['confusion_matrix'][1][0]} | {r['confusion_matrix'][1][1]} |"
               for n, r in cw.items())
imp = M["importance"]
lat = L["repeated_ms"]
risk = M["risk_bands_default_thresholds"]
ds = M["dataset"]
sp = M["split"]
rf15, rf19 = M15["app_default_split"]["class_weight"]["models"]["Random Forest"], cw["Random Forest"]

shots = sorted(os.listdir(os.path.join(ROOT, "docs", "screenshots")))

doc = f"""# REPORT FACTS - CSE-A-A14 (single source of truth for every submission document)

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
* A **FastAPI** layer in `backend/` (~1,050 lines): {n_routes} route handlers that only import and call `src/` functions. One in-memory `AppState` mirrors `st.session_state`; the saved model is restored from `models/*.pkl` at start-up.
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
| File | `{ds['file']}` |
| Origin | **{ds['origin']}** - NOT the real Telco (IBM/Kaggle) data. Same column schema as the public Telco dataset. Churn is generated from a latent logistic risk score plus Gaussian noise (sd 0.55) |
| Licence | none needed - generated by this project's own code (`src/sample_data.py`) |
| Rows x columns | {ds['rows']} x {ds['columns']} |
| Duplicates / missing cells | {ds['duplicates_removed']} / {ds['missing_cells']} |
| Target / ID | `{ds['target']}` (Yes/No) / `{ds['id_col']}` |
| Features | {ds['n_features_raw']} raw (4 numeric: {', '.join(ds['numeric_features'])}; 15 categorical) -> {sp['encoded_feature_count']} after one-hot |
| Class balance | retained {ds['class_distribution']['counts']['0']} ({ds['class_distribution']['percentages']['0']}%), churned {ds['class_distribution']['counts']['1']} ({ds['class_distribution']['percentages']['1']}%), imbalance ratio {ds['class_distribution']['imbalance_ratio']}:1 |
| Split used for headline numbers | stratified {int(sp['test_size']*100)}% test, random_state {sp['random_state']}: {sp['train_rows']} train / {sp['test_rows']} test rows, **{sp['test_churners']} churners in the test set** |

**Consequences to state plainly:** the data are synthetic; the test set is only 200 rows (53 churners), so single-split metrics carry wide error bars (see section 4.2). The base paper used the real 7,043-row Telco data with a 30% test split (2,113 rows) - the two are **not comparable**.

## 4. Real model metrics

Measured by `scripts/run_experiments.py` (same src/ functions and split rule as the Model Training page).
Environment of record: Python {M['environment']['python']}, scikit-learn {M['environment']['sklearn']}, pandas {M['environment']['pandas']}, numpy {M['environment']['numpy']} (the `.venv` that `run.bat` builds; this is the environment of the screenshots and of the API). Raw output: `experiments/churn_synthetic/metrics.json`.

### 4.1 Headline - 80/20 stratified split, seed 42, class weights (the app default)

{table(cw)}

Recommended on F1 (default): **{M['app_default_split']['class_weight']['best_by_f1']}**; best ROC-AUC: **{M['app_default_split']['class_weight']['best_by_roc_auc']}**; best recall: **{M['app_default_split']['class_weight']['best_by_recall']}**. The saved active model in `models/` is Logistic Regression with exactly these LR numbers.

Confusion matrices (test set, 200 rows: 147 retained, 53 churners):

| Model | TN | FP | FN | TP |
|---|---|---|---|---|
{cm}

### 4.2 Stability - the 200-row split is noisy

Stratified 5-fold cross-validation (class weights, mean ± sd over folds, 200 held-out rows per fold):

{table_ms(M['cross_validation_5fold_class_weight'])}

Five random 80/20 splits (seeds 0-4, class weights, mean ± sd):

{table_ms(M['repeated_random_splits_5_seeds_class_weight'])}

Reading: Logistic Regression and Random Forest are within one standard deviation of each other on F1 and ROC-AUC; Logistic Regression has the higher recall, Random Forest the higher precision and accuracy; the Decision Tree is weakest on accuracy, precision, F1 and ROC-AUC (its recall is not the lowest). ROC-AUC is about 0.70-0.72, i.e. **moderate, not strong**.

### 4.3 Imbalance strategy (single split, seed 42)

SMOTE:

{table(sm)}

No handling:

{table(no)}

Findings: without imbalance handling recall collapses (LR 0.1887, RF 0.0943) while accuracy looks fine (0.745, 0.755) - the reason the app selects on F1 rather than accuracy. SMOTE gave the best single-split F1 for LR ({sm['Logistic Regression']['f1_score']:.4f}) but was not tested beyond one split.

### 4.4 Environment sensitivity (honest caveat)

The same script under scikit-learn {M15['environment']['sklearn']} / pandas {M15['environment']['pandas']} gives identical Logistic Regression results but a different Random Forest on the 200-row split (accuracy {rf15['accuracy']:.4f} vs {rf19['accuracy']:.4f}, F1 {rf15['f1_score']:.4f} vs {rf19['f1_score']:.4f}). Archived: `experiments/churn_synthetic/metrics_sklearn1.5.0.json`. Tree ensembles on 800 training rows are version-sensitive; the numbers above are specific to the environment of record.

### 4.5 Drivers (Logistic Regression, class weights)

Largest |coefficient| (model importance): {', '.join(f"{r['feature']} ({r['importance']:.3f})" for r in imp['model_importance'][:6])}.
Permutation importance (<= 300 test rows, 5 repeats, default scoring = accuracy): {', '.join(f"{r['feature']} ({r['importance']:.3f})" for r in imp['permutation_importance'][:4])}; the rest are <= 0.01 (noise-level).
Generator ground truth for comparison: month-to-month contract (+1.3), electronic check (+0.6), tenure (-1.6 over 72 months), no tech support (+0.45), no online security (+0.35), fibre (+0.35), monthly charges, senior citizen, no partner. The model recovers contract type, charges and tenure as top drivers - consistent with the generator, which is a check on the pipeline, **not** evidence about real telecom customers.

### 4.6 Risk segmentation of the 1,000 customers (active model, default thresholds 30/60/80)

Low {risk['counts']['Low Risk']} ({risk['percentages']['Low Risk']}%), Medium {risk['counts']['Medium Risk']} ({risk['percentages']['Medium Risk']}%), High {risk['counts']['High Risk']} ({risk['percentages']['High Risk']}%), Critical {risk['counts']['Critical Risk']} ({risk['percentages']['Critical Risk']}%); mean probability {risk['avg_probability']}%. (Scored on the training data too, so this describes the portfolio view the dashboard shows, not generalisation.) Class-weighted LR inflates probabilities (mean 45.9% vs 26.4% actual churn) - the scores are **rankings, not calibrated probabilities** (measured in 4.7).

### 4.7 Extra analyses on the Logistic Regression test predictions (`scripts/make_figures.py` -> `experiments/churn_synthetic/extra_analysis.json`)

* **Calibration:** Brier score {ex['brier_score']} (a constant base-rate predictor scores {ex['brier_no_skill_constant_base_rate']}, so the model is **not better than no-skill on Brier**); mean predicted probability {ex['mean_predicted_probability']} vs observed churn {ex['observed_churn_rate_test']}. Every reliability bin over-predicts: {rel_txt}.
* **Decision threshold (test split):** at 0.50 (the batch-scoring cut-off) precision {sw['0.5']['precision']}, recall {sw['0.5']['recall']}, F1 {sw['0.5']['f1']}; F1 is flat between 0.40 and 0.60 (best 0.5124 at 0.55 and 0.5122 at 0.45); at 0.30 recall {sw['0.3']['recall']} but precision {sw['0.3']['precision']}; at 0.70 recall {sw['0.7']['recall']}, precision {sw['0.7']['precision']}.
* **Targeting value (ranking by predicted probability, 200 test customers, 53 churners):** contacting the top 10% (20 customers) captures {lf['0.1']['churners_captured']} churners (precision {lf['0.1']['precision']}, lift {lf['0.1']['lift']}x); top 20% (40) captures {lf['0.2']['churners_captured']} = {lf['0.2']['capture_rate']} of churners (precision {lf['0.2']['precision']}, lift {lf['0.2']['lift']}x); top 30% (60) captures {lf['0.3']['churners_captured']} = {lf['0.3']['capture_rate']}; top 50% (100) captures {lf['0.5']['churners_captured']} = {lf['0.5']['capture_rate']}. Lift is moderate (about 1.5-2x); with 20-60 contacts the counts are small.
* **Churn rate by segment (all 1,000 rows):** month-to-month 34.1%, one year 19.2%, two year 12.5%; tenure 0-12 months 36.6% vs 49+ months 18.7%; fibre optic 32.7%, DSL 25.1%, no internet 14.7%; electronic check 33.4% vs bank transfer 18.3%. These follow the relationships built into the generator (section 4.5).

## 5. Performance (measured)

Machine: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro 10.0.26200, Python 3.11.9, Node v24.19.0, no GPU used.

| Measurement | Result |
|---|---|
| Single-customer scoring (preprocess + LR predict_proba), 200 runs | median {M['inference_latency_ms']['single_customer_median']} ms, p95 {M['inference_latency_ms']['single_customer_p95']} ms (venv: pandas 3.0.6 / scikit-learn 1.9.1; the same measurement under pandas 2.2.1 / scikit-learn 1.5.0 gave median {M15['inference_latency_ms']['single_customer_median']} ms, p95 {M15['inference_latency_ms']['single_customer_p95']} ms) |
| Score all 1,000 customers | {M['inference_latency_ms']['full_dataset_1000_rows_ms']} ms |
| Train 5 models, class weights (wall time, incl. evaluation) | {M['app_default_split']['class_weight']['wall_seconds']} s ; RF alone {cw['Random Forest']['fit_and_eval_seconds']} s |
| API (127.0.0.1), median of 10: dashboard / customer 360 / local explanation / what-if / retention / EDA | {lat['dashboard']['median']} / {lat['customer_360']['median']} / {lat['xai_local']['median']} / {lat['whatif']['median']} / {lat['retention']['median']} / {lat['eda']['median']} ms |
| API: batch predict 25 rows (no drivers), median of 5 | {lat['batch_predict_25_rows_no_drivers']['median']} ms |
| API one-off: load sample / prepare / train 3 models / save model | {L['once_ms']['load_sample']} / {L['once_ms']['prepare']} / {L['once_ms']['train_3_models']} / {L['once_ms']['save_model']} ms |

Finding: via the hostname `localhost` every request costs an extra ~2.04 s on this Windows machine (IPv6 `::1` is tried first; uvicorn listens on 127.0.0.1 only). Over `127.0.0.1`, which the Vite proxy uses, the numbers above hold. The smoke test's default base URL is `localhost`, so it takes ~95 s instead of a few seconds. Not fixed (out of scope); mention as a known quirk.

## 6. Testing (real)

| Test | Result |
|---|---|
| `scripts/smoke_test.py` - end-to-end API walk, stdlib only | **{n_pass} PASS, {n_fail} FAIL** (output archived in `experiments/churn_synthetic/smoke_test_output.txt`); covers health, auth (401 / bad password), load sample, preview, config, quality, prepare, EDA + filter, train (incl. 422 on empty selection), results, evaluation, save, dashboard, risk + threshold validation, customers, Customer 360, 404, XAI global/local, what-if, retention, batch template + predict + 422 on missing columns, monitoring + drift, CSV upload, non-CSV rejection |
| `tests/` pytest unit tests of the `src/` core | {pyt_line} (output: `experiments/churn_synthetic/pytest_output.txt`) |
| Defect found by the tests and fixed | `src/data_loader.py` tested `dtype == object` in three places, which is False for the pandas 3 string dtype: blank `TotalCharges` strings were not coerced to numbers and labels such as Churned/Retained were mishandled (Yes/No and the synthetic sample were unaffected). Fixed with a helper `_is_text()` that accepts object and string dtypes; the two regression tests now pass on both pandas versions |
| `npm run build` (frontend) | passes (Vite 8) |
| Browser check (Playwright, Chrome) `scripts/capture_screens.py` | all 16 screens captured with real data; console clean; no failed requests |
| Responsive / theme / accessibility | 360, 768, 1440 px in light and dark: no horizontal overflow; reduced-motion; keyboard (skip link, focus ring, Esc closes overlays) - checked manually via Playwright during the build, **not** with an automated accessibility tool |
| `run.bat` from scratch | creates `.venv`, installs, starts API (8314) and web (5314) |

**Not done:** no load / concurrency test (single-user in-memory design), no penetration test, no user-acceptance study with real users, no cross-browser test beyond Chrome, no test of the SHAP code path (shap not installed), no cost-sensitive (monetary) evaluation.

## 7. Endpoints (29 behaviours; `backend/main.py`)

Public: `GET /api/health`, `POST /api/auth/login`. Bearer-protected: `GET /api/auth/me`, `GET /api/state`, `POST /api/data/sample`, `POST /api/data/upload`, `GET /api/data/preview`, `GET|PUT /api/data/config`, `GET /api/data/quality`, `POST /api/data/prepare`, `GET /api/eda`, `GET /api/dashboard`, `POST /api/models/train`, `GET /api/models/results`, `POST /api/models/save`, `GET /api/evaluation`, `GET|PUT /api/risk/thresholds`, `GET /api/risk`, `GET /api/customers`, `GET /api/customers/{{id}}`, `GET /api/xai/global`, `GET /api/xai/local/{{id}}`, `GET /api/whatif/schema`, `POST /api/whatif`, `GET /api/retention`, `GET /api/batch/template`, `POST /api/batch/predict`, `GET /api/monitoring`, `POST /api/monitoring/drift`. Interactive docs at `/docs`. Errors: 401 (token), 404 (unknown customer), 409 (data/model not ready), 422 (validation) with a plain-language `detail`.

## 8. Technology stack (versions measured)

Python 3.11.9; scikit-learn 1.9.1 (venv) / 1.5.0 (system); pandas 3.0.6 / 2.2.1; numpy 2.4.6 / 1.26.4; imbalanced-learn; joblib; plotly (Streamlit charts); Streamlit (original UI); FastAPI 0.143.3; uvicorn 0.54.0; React 19.3, Vite 8.3, react-router 7, Recharts 3, framer-motion 14, GSAP 3, Lenis, canvas-confetti, lucide-react; git.

## 9. Screenshot inventory (`docs/screenshots/`, all 1440x900, real data: 1,000 synthetic customers, three models trained, Logistic Regression active)

{chr(10).join(f"* `{s}`" for s in shots)}

Screens 01-16 are 1440x900 and were re-captured with the API on its default risk thresholds (30 / 60 / 80), so the dashboard and risk counts (253 / 481 / 213 / 53) match section 4.6; screens 17-20 (dark theme, 768 px and 360 px layouts) come from `scripts/capture_extra.py`. An earlier capture had been taken after the smoke test left the thresholds at 25 / 55 / 75; the smoke test now restores the defaults.

## 10. Base paper vs this project (use for "comparison with the base paper")

| | Base paper (Oprea & Bara, IEEE Access 2026) | This project |
|---|---|---|
| Data | Real Telco churn, 7,043 rows, 21 columns, 26.5% churn (1,869 churners), Kaggle/IBM | **Synthetic**, 1,000 rows, same schema, {ds['class_distribution']['percentages']['1']}% churn |
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
"""
with open(os.path.join(ROOT, "docs", "REPORT_FACTS.md"), "w", encoding="utf8") as fh:
    fh.write(doc)
print("wrote docs/REPORT_FACTS.md", len(doc), "chars")
