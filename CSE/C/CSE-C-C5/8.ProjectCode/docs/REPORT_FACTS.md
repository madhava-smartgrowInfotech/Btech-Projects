# REPORT FACTS - Smart Campus Placement System (CSE-C-C5)

Single source of truth for every document in the batch folder. Every number below was read from `models/metrics.json`,
`docs/experiments/experiments.json` (written by `scripts/run_experiments.py`), `docs/experiments/tests.json` (written by
`scripts/edge_tests.py`), the data files, or measured on this machine on 2026-10-22. Nothing is typed from memory.

## 1. Identity

| Item | Value |
|---|---|
| Product / project | Smart Campus Placement System |
| Batch | CSE-C, Batch C-05 (C5); domain Educational Data Mining and Machine Learning |
| College (from batch documents) | TKR College of Engineering & Technology (Autonomous) |
| Students | Mopidevi Bhagyasri 23K91A05F9; Pamulaparthi Harsha Vardan Reddy 23K91A05J0; Mohammad Faruk Baba 23K91A05F3; Prahalladh Terati 23K91A05J8 |
| Guide | S Usha Devi (designation not given -> placeholder) |
| Unknown -> keep square-bracket placeholders | academic year, HOD name, principal name, guide designation, place, date, department email |
| Ports | backend 8405, frontend 5405 (original Flask UI 5000) |
| Code | `8.ProjectCode` - src/ 508 lines, backend/main.py 221, app.py 140, frontend/src 15+ pages/components (pages 953 lines) |

## 2. Base papers (two sources, both are cited)

* **[Declared base paper, batch document 3]** M. Prasanna Kumari, B. Punith, M. Srinath, P. Koushik, Y. Gourav, "Student placement
  prediction system using machine learning," *International Journal of Engineering Technology and Management Sciences (IJETMS)*,
  vol. 10, no. 3, May-June 2026, pp. 47-51, DOI 10.46647/ijetms.2026.v10i03.008, ISSN 2581-4621. Vidya Jyothi Institute of Technology,
  Hyderabad. 5-page paper. Synthetic dataset; Logistic Regression, Random Forest, Gradient Boosting; 80:20 split; Streamlit app with
  batch CSV prediction, skill-gap analysis, PDF report and SMTP email. **It reports no accuracy/F1/AUC figure** (the results section
  only states the 80:20 split and the three models). Its reference list has 10 entries (Ambili and Abraham 2024; El Mrabet and Ait Moussa 2023; van den Berg et al. 2023; Baffa et al. 2023; Shinde et al. 2023; Shah 2023; Archana et al. 2023; Parida et al. 2022; Sah and Singh 2022; Tedre et al. 2021) - these were not read in full by us; cite only as "listed in [1]".
* **[Technique source, used by the code and README]** M. Heidari Fard and E. Tabrizi, "A Hybrid Machine Learning Approach for Graduate
  Admission Prediction and Combined University-Program Recommendation," arXiv:2603.29881 [cs.IR], 9 Feb 2026 (PDF in
  `8.ProjectCode/` and `archived_base_papers/`). Facts read from the PDF: 13,000 GradCafe records (2021-2025) enriched with QS data; 51%/49% accepted/rejected; 70/15/15 split (9,100/1,950/1,950); 9-fold CV; baselines LogReg 0.6944, DT 0.6944, RF 0.7344, SVM 0.6954, kNN 0.6774, XGBoost 0.7241 (LightGBM 0.7262) accuracy; XGBoost+kNN hybrid **0.8723** accuracy, XGBoost+SVM 0.8749; Platt Brier 0.1864 (isotonic 0.1867); XGBoost hyper-parameters n_estimators 100, max_depth 8, lr 0.1, subsample 0.8, colsample 0.8, reg_alpha 0.1, reg_lambda 1; kNN k=9 uniform; residual set R = misclassified OR p in [0.4, 0.6] (Eq. 1, uses true labels); GPA proximity and delta-max filters; recommendation raised mean acceptance probability by 65.1% (hybrid 0.704 average increase, 93% of 6,028 rejected applicants matched); SHAP and PCA.
* Alternates listed in `archived_base_papers/BASEPAPER_REFERENCES.md`: EduPredict (ICICAT 2025); Springer doi:10.1007/978-3-031-72747-4_38; Foundry Journal 2025 (not verified here).
* Batch literature survey (`5.LITERATURE SURVEY.docx`): 5 titles with year/source only (no authors, no numbers) - Excelling through Placement Process (2025, Campus to Corporate); Campus Placement Prediction And Analysis Using Machine Learning (2025, IJRPR); Student Placement Package Prediction By Regression Analysis (2024, IJRPR); Predictive Analysis of Campus Placement of Student Using Machine Learning Algorithms (2024, Journal of IoT and Machine Learning). Gap stated in batch docs: "extending prediction into company recommendation and actionable skill-gap feedback".
* Batch abstract/objectives: 6 objectives (collect data; clean/encode and address imbalance; train and compare classifiers; recommend companies; identify skill gaps; dashboards evaluated with accuracy, precision, recall). The batch details name MySQL and HTML/CSS/JS; **the code uses no database** (CSV + pickle).

## 3. What the system is (verified from code)

Three layers: (1) offline training scripts `src/generate_dataset.py`, `src/preprocess.py`, `src/hybrid_model.py`; (2) serving core `src/recommend.py` (`predict_for`, `recommend`, `delta_max_cgpa`, `load_artifacts`); (3) interfaces: original Flask app (`app.py`, templates/, 5 pages + `POST /api/predict`) and a FastAPI layer (`backend/main.py`, 9 routes) with a React 19 / Vite 8 / Tailwind 4 / three.js / Recharts / framer-motion / GSAP front end (kit V5 "Kinetic Mono"; pages Landing, Eligibility `/predict`, Recommendations `/recommend`, Officer dashboard `/dashboard`, Recruiter `/recruiter`, Companies `/companies`; command palette, activity log, dark/light theme). No authentication, no database, no user accounts.

### FastAPI endpoints (backend/main.py)
| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | status, models_ready |
| GET | /api/meta | branches, degrees, roles, locations, company names |
| GET | /api/companies | 30 company rows |
| GET | /api/metrics | models/metrics.json |
| GET | /api/stats | total, placed_rate, avg_cgpa, by_branch |
| GET | /api/plots/{prob_hist,pca,shap} | PNG; 404 for any other name |
| POST | /api/predict | profile + target_company + target_role -> probability, eligible, label, company_detail, tips |
| POST | /api/recommend | profile + optional target/role/location -> base_prob, company_only, role_only, hybrid (top 5), avg_gain, match_rate |
| POST | /api/recruiter/shortlist | min_cgpa, min_apt, branch -> total_matches, up to 50 students sorted by CGPA then Technical |
Validation: Pydantic ranges (cgpa 0-10, scores 0-100, counts 0-20) -> 422; unknown company -> 404; missing artefacts -> 503; CORS only for http://localhost:5405 and http://127.0.0.1:5405.

### Data (synthetic - stated plainly)
* `data/placement_dataset.csv`: **3,000 students x 19 columns**, generated by `src/generate_dataset.py` (numpy seed 42). **No real student data**; labels are drawn from a logistic score of CGPA gap, aptitude gap, technical gap, skill index, internships, projects, certifications, backlogs, CSE/IT bonus and tier penalty plus Gaussian noise (sd 0.8). Student-level scores are generated from CGPA with noise.
* `data/companies.csv`: **30 companies** (7 Tier-1 dream, 15 Tier-2 core, 8 Tier-3 mass) with CGPA/aptitude/technical cutoffs, package (4.0-28.0 LPA), location (Bangalore, Hyderabad, Chennai, Pune, Mumbai, Noida, Mysore), type (MNC, Startup, Core) and hiring rate (0.12-0.55). Invented plausible values, not real recruiter requirements.
* Placed 1,791 (59.7%), not placed 1,209 (40.3%); no missing values. CGPA mean 7.833 (sd 0.704, min 5.80, max 9.35). Branch counts CSE 981, ECE 516, IT 432, MECH 397, CIVIL 368, EEE 306; placed rate by branch 58.5%-60.8% (CSE 60.8%, ECE 58.5%, IT 59.5%, CIVIL 59.5%, EEE 59.8%, MECH 58.9%). BTech 2,444 / MTech 556; Regular 2,150 / Lateral 850; years 2023 534, 2024 780, 2025 904, 2026 782 (placed 57.9%, 56.7%, 61.9%, 61.4%). Eight roles, 344-401 students each. Placed rate by target tier: Tier 1 9.6% (324 students), Tier 2 49.5% (1,320), Tier 3 81.6% (1,356). Backlogs 0..4 -> placed 72.2, 61.1, 52.6, 38.3, 33.7 %; internships 0..4 -> 56.8, 59.2, 63.2, 69.2, 78.6 %.
* Split: stratified 70/15/15, seed 42 -> **train 2,100 / validation 450 / test 450** (test placed 59.56%).

### Pre-processing (src/preprocess.py)
Frequency encoding of 5 categoricals (Branch, Target_Company, Target_Role, Degree_Type, Student_Type); z-score of 13 numeric columns (CGPA, Tenth, Twelfth, Aptitude, Technical, Communication, DSA, Projects, Internships, Certifications, Backlogs, Placement_Year, Target_Tier) and 6 engineered columns (Skill_Index = 0.4 Tech + 0.3 Apt + 0.15 Comm + 0.15 DSA over 100; Company_Hiring_Rate; CGPA_x_Tier; CGPA_Gap, Apt_Gap, Tech_Gap against the target company's cutoffs) = **24 features**. Maps and scaler fitted on the training split only (saved in `preprocess.pkl`). "Address imbalance" (objective 2): classes are 59.7/40.3 and no resampling is applied; stratified splitting keeps the ratio.

### Models and training (src/hybrid_model.py)
LogisticRegression(max_iter 1000), DecisionTree, RandomForest(200), SVC(rbf, probability), kNN(k=9), XGBoost(n_estimators 100, max_depth 8, lr 0.1, subsample 0.8, colsample 0.8, reg_alpha 0.1, reg_lambda 1, logloss); LightGBM branch skipped (not installed). 9-fold CV of XGBoost on the training split: **0.8147** accuracy. XGBoost calibrated by `CalibratedClassifierCV(method="sigmoid", cv=3)` (Platt); Brier **0.1352**. Hybrid: residual set R = (calibrated prediction wrong) OR (p in [0.4, 0.6]) - the first term uses the **true test labels** (as in the base paper's Eq. 1), so reported hybrid numbers are **not reproducible at serving time** (see 5.3). Local models kNN(k=9) and SVC(rbf) are fitted on all training rows and applied only to residual rows. Serving rule (`src/recommend.predict_for`): `p = xgb_calibrated(x)`; if 0.4 <= p <= 0.6: `p = 0.5 p + 0.5 kNN_proba(x)`. Decision threshold 0.5. Artefacts: `xgb_calibrated.pkl` 1.49 MB, `knn_residual.pkl` 0.42 MB, `svm_residual.pkl` 0.20 MB, `preprocess.pkl` 2.7 KB, `companies.pkl` 4.3 KB (all dated 2026-09-09). Re-training one full seed (6 baselines + calibration + 2 local models) took about 3 s on this machine; the shipped pickles reproduce `metrics.json` exactly (verified: `shipped_pickles_reproduce_metrics_json = true`); a fresh retrain with the installed library versions drifts by at most 0.011 in any metric.

### Recommendation (src/recommend.py)
For each of 30 companies: skip if |CGPA - cutoff| > delta_max(tier) (0.6 / 1.0 / 1.5 for tiers 1/2/3), or aptitude < cutoff - 15, or (backlogs > 2 and Tier 1), or package < minimum; proximity = max(0, 1 - gap/delta_max); for roles {target role, SDE, Data Analyst, QA Engineer} compute p = predict_for; score = p + 0.05 proximity + 0.02 location bonus. Three lists: company-only (best role per company), role-only (target company only), hybrid (top 5 pairs). avg_gain = mean(p - base_p) over hybrid items with p > base_p; match_rate = share of hybrid items beating base. Skill-gap tips are rules on cutoffs (`_tips`): CGPA below cutoff, aptitude below cutoff, technical below cutoff, no internship; otherwise "Strong profile".

## 4. Environment (measured)
Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro 10.0.26200, **no GPU (CPU only)**. Python 3.14.7 (project `.venv`), scikit-learn 1.9.0, xgboost 3.4.1, pandas 3.0.5, numpy 2.5.3, shap 0.52.0, matplotlib 3.11.1, FastAPI 0.159.1, uvicorn 0.54.0, pydantic 2.14.1, Flask 3.1.3; Node 24.19.0; React 19.3, Vite 8.3, Tailwind 4.3, three 0.186, Recharts 3.10, framer-motion 14.5, GSAP 3.15, react-router 7.18, axios 1.20. Browser: Chrome via Playwright.

## 5. Results (all from this project)

### 5.1 Test-set metrics, seed 42 (450 students) - `models/metrics.json`, reproduced exactly from the shipped pickles
| Model | Accuracy | ROC-AUC | F1 | Precision | Recall |
|---|---|---|---|---|---|
| Logistic Regression | 0.8289 | 0.9106 | 0.8577 | 0.8498 | 0.8657 |
| Decision Tree | 0.7533 | 0.7506 | 0.7869 | 0.8103 | 0.7649 |
| Random Forest | 0.8067 | 0.8918 | 0.8404 | 0.8267 | 0.8545 |
| SVM (RBF) | 0.8289 | 0.8855 | 0.8597 | 0.8399 | 0.8806 |
| kNN (k=9) | 0.7978 | 0.8638 | 0.8378 | 0.8020 | 0.8769 |
| XGBoost | 0.8089 | 0.8888 | 0.8396 | 0.8396 | 0.8396 |
| XGBoost + Platt | 0.8067 | 0.8928 | 0.8404 | 0.8267 | 0.8545 |
| Hybrid XGB+kNN (paper rule, uses true labels) | 0.8400 | 0.8968 | 0.8710 | 0.8379 | 0.9067 |
| Hybrid XGB+SVM (paper rule) | 0.8356 | 0.8810 | 0.8650 | 0.8464 | 0.8843 |
| Hybrid kNN, label-free (borderline 0.4-0.6 only, hard replace) | 0.8089 | 0.8954 | 0.8442 | 0.8204 | 0.8694 |
| Hybrid kNN, serving rule (0.5p + 0.5 kNN in band) | 0.8089 | 0.8939 | 0.8436 | 0.8227 | 0.8657 |
9-fold CV (XGB, training split) 0.8147; Brier (Platt) 0.1352; residual rate of the paper rule 0.2289 (103 of 450); borderline-only rate 0.0689 (31 of 450).

### 5.2 Confusion matrices (test, n=450; rows true 0/1, columns predicted 0/1)
| Model | TN | FP | FN | TP |
|---|---|---|---|---|
| XGBoost + Platt | 134 | 48 | 39 | 229 |
| Hybrid, paper rule (labels used) | 135 | 47 | 25 | 243 |
| Hybrid, label-free | 131 | 51 | 35 | 233 |
| Hybrid, serving rule | 132 | 50 | 36 | 232 |
| Logistic Regression | 141 | 41 | 36 | 232 |

### 5.3 The key honest finding
The hybrid's headline gain (accuracy 0.8067 -> 0.8400, +3.3 points; recall 0.8545 -> 0.9067) exists only because Eq. 1 chooses the residual set using the true labels: XGBoost is wrong on 87 of the 450 test rows; 72 of those lie outside the borderline band and enter the 103-row residual set only because their true label shows they are wrong (15 wrong rows are also borderline; 31 rows are borderline in total; 87 + 31 - 15 = 103). kNN is right on 30.1% of the 103 oracle residual rows versus XGBoost 15.5% - a selection effect, not a real skill. On the label-free rule that can run at serving time (only the 31 borderline rows) the hybrid scores **0.8089** accuracy (vs 0.8067 for calibrated XGBoost): +0.2 point = 1 student of 450; kNN is right on 54.8% of the borderline rows vs XGBoost 51.6%. The base paper's 87.23% has the same caveat (its Eq. 1 is also label-driven; we did not re-derive its data). **Five-seed study** (seeds 42,1,2,3,4; mean ± sd, retrained in memory): Hybrid paper rule 0.8391 ± 0.0154; label-free 0.8142 ± 0.0180; serving rule 0.8151 ± 0.0149; XGBoost+Platt 0.8138 ± 0.0115; Logistic Regression 0.8231 ± 0.0194 (highest AUC 0.9031 ± 0.0109).

### 5.4 Five-seed study (accuracy / F1 / ROC-AUC, mean ± sd, n=450 test rows per seed; seed-42 retrain differs from 5.1 by <= 0.011)
| Model | Accuracy | F1 | ROC-AUC |
|---|---|---|---|
| Logistic Regression | 0.8231 ± 0.0194 | 0.8547 ± 0.0157 | 0.9031 ± 0.0109 |
| Decision Tree | 0.7369 ± 0.0205 | 0.7778 ± 0.0172 | 0.7284 ± 0.0220 |
| Random Forest | 0.8004 ± 0.0216 | 0.8376 ± 0.0170 | 0.8825 ± 0.0120 |
| SVM | 0.8129 ± 0.0169 | 0.8483 ± 0.0139 | 0.8863 ± 0.0133 |
| kNN | 0.7960 ± 0.0208 | 0.8363 ± 0.0179 | 0.8614 ± 0.0171 |
| XGBoost | 0.8156 ± 0.0178 | 0.8487 ± 0.0159 | 0.8863 ± 0.0121 |
| XGBoost + Platt | 0.8138 ± 0.0115 | 0.8474 ± 0.0118 | 0.8899 ± 0.0127 |
| Hybrid XGB+kNN (labels used) | 0.8391 ± 0.0154 | 0.8699 ± 0.0132 | 0.8958 ± 0.0100 |
| Hybrid XGB+SVM (labels used) | 0.8258 ± 0.0170 | 0.8583 ± 0.0144 | 0.8815 ± 0.0168 |
| Hybrid kNN, label-free | 0.8142 ± 0.0180 | 0.8489 ± 0.0159 | 0.8883 ± 0.0137 |
| Hybrid kNN, serving rule | 0.8151 ± 0.0149 | 0.8498 ± 0.0139 | 0.8896 ± 0.0132 |
Per-seed accuracy (seeds 42,1,2,3,4): XGB+Platt 0.8111, 0.8222, 0.8022, 0.8044, 0.8289; Hybrid paper rule 0.8444, 0.8467, 0.8333, 0.8156, 0.8556; label-free 0.8111, 0.8200, 0.8000, 0.7978, 0.8422; LogReg 0.8289, 0.8467, 0.8133, 0.7956, 0.8311. (Seed-42 retrain values; the shipped model's seed-42 numbers are in 5.1.) Differences between models of 1-2 points are within one standard deviation.

### 5.5 Borderline band sweep (calibrated XGBoost p in [lo, hi] replaced by kNN label; seed 42, shipped models)
| Band | Rows replaced | Accuracy | F1 | ROC-AUC |
|---|---|---|---|---|
| none (p>=0.5) | 0 | 0.8067 | 0.8404 | 0.8928 |
| 0.45-0.55 | 13 | 0.8022 | 0.8379 | 0.8935 |
| 0.40-0.60 (served) | 31 | 0.8089 | 0.8442 | 0.8954 |
| 0.35-0.65 | 45 | 0.8067 | 0.8444 | 0.8967 |
| 0.30-0.70 | 73 | 0.8067 | 0.8455 | 0.8941 |
| 0.20-0.80 | 133 | 0.8067 | 0.8449 | 0.8886 |
Across bands accuracy stays within 0.7 points (0.8022 to 0.8089): the local model adds no measurable value on this data.

### 5.6 Decision-threshold sweep (calibrated XGBoost, seed 42)
| Threshold | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| 0.30 | 0.7933 | 0.7760 | 0.9179 | 0.8410 |
| 0.35 | 0.8044 | 0.7980 | 0.8993 | 0.8456 |
| 0.40 | 0.8044 | 0.8061 | 0.8843 | 0.8434 |
| 0.45 | 0.8022 | 0.8140 | 0.8657 | 0.8391 |
| 0.50 | 0.8067 | 0.8267 | 0.8545 | 0.8404 |
| 0.55 | 0.8044 | 0.8309 | 0.8433 | 0.8370 |
| 0.60 | 0.8067 | 0.8441 | 0.8284 | 0.8362 |
| 0.65 | 0.8022 | 0.8482 | 0.8134 | 0.8305 |
| 0.70 | 0.8044 | 0.8689 | 0.7910 | 0.8281 |
Accuracy is flat (0.793-0.807) across thresholds; threshold trades precision (0.776 -> 0.869) against recall (0.918 -> 0.791). The served threshold 0.5 is a reasonable middle.

### 5.7 Calibration
Brier: raw XGBoost 0.1379, Platt 0.1352 (a 2% improvement), Logistic Regression 0.1180 (better than both). Mean predicted probability on test 0.5923 vs observed 0.5956. Base paper Brier 0.1864 (Platt) - different data, not comparable. Figure: `docs/figures/calibration.png`.

### 5.8 Explainability (SHAP, mean |SHAP| over the 450 test rows, retrained XGBoost; the shipped `static/shap.png` ranks the same top five)
CGPA_Gap 1.1239, Backlogs 0.8833, Tech_Gap 0.5036, Apt_Gap 0.3958, CGPA_x_Tier 0.3878, Tenth_Percent 0.1707, Internships 0.1619, Projects 0.1554, DSA_Score 0.1474, Company_Hiring_Rate 0.1381, Target_Company (freq) 0.1338, Communication_Score 0.1188. The gap features measured against the target company's cutoffs dominate - consistent with how the labels were generated (this is a property of the synthetic data, not a discovery about real placements).

### 5.9 Recommender (60 test students whom the model rates below 0.5 for their own target; shipped models)
Mean base probability 0.2219; 52 of 60 (86.7%) receive at least one hybrid alternative that beats the base; mean top-1 probability 0.6434; mean average gain over improved items 0.4371 (43.7 percentage points); the top-1 alternative reaches >= 0.5 for 39 of 60 (65%). These are **model-estimated** probabilities, never checked against real outcomes. In the screenshot (CGPA 7.5, target Google SDE) the base is 10.8%, average gain +78.8 pt, match rate 100%, top pick ValueLabs QA Engineer 89.9%; picks are Tier-3 companies (ValueLabs, Infosys) - the algorithm maximises probability, not package or fit. When the target company fails the feasibility filter (Google at CGPA 7.2) the role-only list is empty (0 items). Base paper: +65.1% mean over all rejected applicants (different definition and data).

### 5.10 Testing (46 checks, all pass; `scripts/edge_tests.py` + `scripts/smoke_test.py` 15 checks all pass)
Unit 10/10, integration 8/8, functional 6/6, validation 13/13, security 9/9 = 46/46. `scripts/smoke_test.py` (live server): 15 of 15 checks pass. Notable observed behaviours: an unknown branch value (e.g. ROBOTICS) or unknown role (Astronaut) is accepted (HTTP 200; unseen categories get frequency 0); an all-zero profile scores 0.1394, an all-maximum profile at Google 0.7993; strong profile at Infosys 0.9032, weak profile at Google 0.1212; raising CGPA 6.0 -> 9.0 at Infosys raises p 0.883 -> 0.905, backlogs 0 -> 4 lowers 0.905 -> 0.892 (small because the profile is otherwise strong). SQL-injection-like, script-tag, path-traversal and 100 kB inputs all return 404 and nothing is executed (there is no database); CORS allows only the frontend origin. **No authentication, no rate limiting** (documented limitation). The project had no automated tests before this run; `scripts/smoke_test.py` pre-existed.
Failures/limits of testing: no browser-based automated UI test suite (screenshots were captured with Playwright, 10 screens); no load test beyond sequential calls; no test on real student data.

### 5.11 Performance (localhost 127.0.0.1, sequential calls, this machine; the default `localhost` adds ~2 s IPv6 fallback and was not used)
| Endpoint | n | mean ms | p50 ms | p95 ms | max ms |
|---|---|---|---|---|---|
| GET /api/health | 50 | 5.4 | 3.0 | 4.7 | 104.6 |
| GET /api/metrics | 50 | 6.1 | 3.5 | 21.3 | 27.2 |
| GET /api/stats | 30 | 21.2 | 19.0 | 31.6 | 38.7 |
| POST /api/predict | 50 | 65.7 | 55.7 | 109.5 | 147.4 |
| POST /api/recruiter/shortlist | 30 | 28.1 | 25.8 | 38.7 | 46.8 |
| POST /api/recommend | 8 | 5,381.6 | 5,062.0 | 5,708.2 | 8,073.9 |
In-process: `predict_for` 66.0 ms mean (p50 55.6, p95 116.7, n=100); `recommend()` 3.49 s mean over 60 students (p50 3.61, p95 6.41, max 13.87). **Recommendation takes 3-8 s** because `predict_for` reloads four pickle files on every call and is called up to 4 x (feasible companies) times per request - the main performance weakness; caching the artefacts would be the obvious fix (not done).

## 6. Objectives vs outcome (batch objectives)
1. Collect records - **partially**: no real data exists; a 3,000-record synthetic dataset was generated (documented limitation).
2. Clean/encode, handle imbalance - **done for encoding**; no missing values, classes 59.7/40.3, no resampling applied.
3. Train and compare classifiers - **done**: 6 baselines + calibrated XGBoost + 2 hybrids, 5-seed study.
4. Recommend companies - **done** (hybrid top-5, three strategies), gains are model-estimated only.
5. Skill gaps - **done as rules** (`_tips`: below-cutoff on CGPA, aptitude, technical; no internship), plus SHAP global ranking; no per-student SHAP explanation.
6. Dashboards and evaluation - **done**: officer dashboard (metrics, SHAP, PCA, probability histogram, branch placed rates), recruiter shortlist; accuracy, precision, recall, F1, ROC-AUC, Brier reported.
Not implemented from the batch description: MySQL storage, login for students/recruiters/officers, PDF/email reports, batch CSV prediction (the IJETMS paper has it), job-description requirement vectors, real placement data.

## 7. Comparison with the base papers (state datasets differ)
| | IJETMS placement paper [declared base] | arXiv:2603.29881 [technique base] | This project |
|---|---|---|---|
| Task | placement prediction | admission prediction + university-program recommendation | placement prediction + company-role recommendation |
| Data | synthetic (size not stated) | 13,000 real GradCafe records | 3,000 synthetic students, 30 invented companies |
| Split | 80:20 | 70/15/15 (9,100/1,950/1,950) | 70/15/15 (2,100/450/450) |
| Models | LR, RF, Gradient Boosting | 7 baselines, XGBoost+kNN/SVM hybrid | 6 baselines, calibrated XGBoost, kNN/SVM hybrids |
| Reported result | none numeric | XGBoost 0.7241; hybrid 0.8723 | XGBoost 0.8089; hybrid 0.8400 (label-driven) / 0.8089 (label-free) |
| Calibration | none | Platt, Brier 0.1864 | Platt, Brier 0.1352 |
| Explainability | feature importance / skill gap | SHAP | SHAP ranking + rule-based tips |
| Recommendation | skill gap only | university, program, hybrid | company, role, hybrid |
| Deployment | Streamlit, PDF, email | none | Flask + FastAPI + React |
Numbers are **not comparable**: our data is synthetic and generated by a logistic rule, so even Logistic Regression reaches 0.829; the paper's real data is noisier (0.69-0.73 baseline accuracy).

## 8. Novelty / contributions (honest)
Adaptation of the arXiv hybrid framework from admissions to placement (company = university, role = program, company tier = QS rank, CGPA proximity = GPA proximity, company hiring rate = program admission rate, CGPA x tier = program x QS interaction, company cutoffs as gap features); skill-gap tips; three-strategy company-role recommender with feasibility filters; officer dashboard and recruiter shortlist; FastAPI + React interface over unchanged ML code; an evaluation that exposes the label-dependence of the residual rule (new measurement); reproducible scripts. **Not new**: XGBoost, Platt scaling, kNN, SHAP, PCA (standard); the residual idea comes from the base paper.

## 9. Limitations (honest, for documents)
Synthetic data and invented company table (no real generalisation claim); labels generated by a logistic rule so models recover the rule; hybrid gain depends on test labels; no real-time retraining or data upload; no authentication; no database; unknown categories silently accepted; recommender latency 3-8 s and steers weak profiles to Tier-3 companies; role-only list can be empty; 3-fold calibration on 2,100 rows; single dataset, single machine, CPU only; recommender gains unverified against outcomes; Python 3.14 / sklearn 1.9 pickles are version-sensitive (pyarrow needed for the pandas 3 company pickle); tips are fixed rules; React UI sends no auth token and trusts localhost CORS.

## 10. Screenshot inventory (`docs/screenshots/`, 1440x900, real running app, 3,000-student data, captured 2026-10-22 by `scripts/capture_screens.py`)
| File | What it shows |
|---|---|
| 01_landing_dark.png / 01_landing_light.png | Landing page: hero, live counters (3,000 students, 30 companies), model table, company marquee (dark and light theme) |
| 02_predict.png | Eligibility: Microsoft, SDE, CGPA 8.4, aptitude 84, technical 79, 1 internship, 3 projects -> **22.2%**, NEEDS IMPROVEMENT, cutoffs panel (CGPA 8.4/8.2 pass, Aptitude 84/82 pass, Technical 79/82 fail), Tier 1, 24.0 LPA, Hyderabad, hiring rate 15%, tip "Strengthen DSA + core subjects; build 2+ projects." |
| 03_recommend.png | Recommendations: base 10.8% (Google SDE), avg gain +78.8 pt, match rate 100%, top pick ValueLabs QA Engineer 89.9%; bar chart of top-5 vs base; tabs hybrid 5 / company-only 5 / role-only 0 |
| 04_dashboard.png | Officer dashboard: 3,000 students, placed rate 59.7%, avg CGPA 7.83, hybrid XGB+kNN AUC 0.8968 (accuracy 84.0%), 9-fold CV 0.8147, Brier 0.1352, residual 22.9%; model comparison chart; placed rate by branch; model table |
| 05_dashboard_shap.png | SHAP importance tab: mean-abs-SHAP bar chart of all 24 features |
| 06_recruiter.png | Recruiter shortlist: min CGPA 7.5, min aptitude 65, all branches -> 1,394 matches, top 50 by CGPA, placed / not placed tags |
| 07_companies.png | Companies board (30 companies, searchable) |
| 08_command_palette.png | Command palette search ("hyd") |
| 09_activity_log.png | Activity log of the session's real API calls |

## 11. Diagram and figure inventory
Diagrams (`docs/diagrams/`, matplotlib 150 dpi, drawn from the code): 01_system_architecture, 02_high_level_workflow, 03_dfd_level0, 04_dfd_level1, 05_dfd_level2 (process 4 recommendation), 06_class_diagram, 07_sequence_prediction, 08_use_case, 09_er_diagram, 10_core_algorithm_flowchart, 11_training_pipeline, 12_recommendation_flowchart.
Figures (`docs/figures/`, from `scripts/run_experiments.py`): model_comparison, confusion_matrices (three panels: XGB+Platt, hybrid with labels used, hybrid serving rule: TN 132 FP 50 FN 36 TP 232), threshold_sweep, calibration, multi_seed, shap_top10, reco_gain. Shipped plots: `static/shap.png`, `static/pca.png`, `static/prob_hist.png`.

## 12. How to reproduce
`run.bat` (venv, pip, train if models missing, npm install, both servers); `.venv\Scripts\python.exe scripts\run_experiments.py` (about 5 min, mostly the recommender timing); `scripts\edge_tests.py` and `scripts\smoke_test.py` against `uvicorn backend.main:app --port 8405`; `scripts\make_diagrams.py`; `scripts\capture_screens.py`.
