# REPORT_FACTS - single source of truth for the documentation of batch CSE-C-C6

Every number below is read from this project's own artefacts (`experiments/liar2/*.json`, `models/metrics.json`, the test scripts, the screenshot folder). The documents must agree with this file.

## 1. Identity

- Project: FAKE NEWS DETECTION SYSTEM USING FEATURE BASED OPTIMISED MSVM CLASSIFICATION (batch CSE-C-C6, product name in the UI: TruthGlow)
- Students: Neela Mojes (23K91A05H1), Noor Saniya (23K91A05H4), Malkajgiri Akshitha (23K91A05E2), Maravajhala Radha Sri Aashritha (23K91A05E7)
- Guide: K Rajasekhar Rao. College, HOD, principal, academic year, designation, e-mail: not in the batch files (placeholders kept)
- Base paper (batch files 1, 3, 5): M. Saad, S. Abdelrazek, I. R. Abdelmaksoud, "An algorithmic system for arabic fake news detection using neural networks and transformer embeddings with class weighting", Scientific Reports 16, 12226 (2026), doi 10.1038/s41598-026-45653-4. Binary Arabic task, 7,474 articles, CAMeLBERT embeddings + NN + class weighting, 80/20 split, reported F1 96.19 %, accuracy 95.52 %, precision 95.48 %, recall 96.90 % (Tesla T4 GPU).
- Companion papers in `archived_base_papers/`: Dell'Oglio et al., "An Experimental Comparison of the Most Popular Approaches to Fake News Detection" (arXiv 2603.25501, Information Sciences 2026): binary harmonised labels; on LIAR-PLUS (the most challenging dataset for nearly all models) LR F1 0.56, SVM F1 0.57. Huang et al., "A Hybrid Transformer Model for Fake News Detection: Leveraging Bayesian Optimization and Bidirectional Recurrent Unit" (arXiv 2502.09097): TF-IDF + Transformer/BiGRU + Bayesian optimisation, 99.73 % test accuracy on its own data.

## 2. Environment of every measurement

- CPU Intel Core i5-12500 (6 cores / 12 threads, 3.0 GHz base), 15.7 GB RAM, Windows 11 Pro, no discrete GPU used (Intel UHD 770 present, not used)
- Python 3.11.9; scikit-learn 1.9.1, NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.6, FastAPI 0.159.1, uvicorn 0.54.0 (project `.venv`); Node 24.19.0, npm 11.17.0
- Frontend: React 18.3, Vite 8, TypeScript 5.9, Tailwind CSS 4, TanStack Query 5, react-router 7, Recharts 3, GSAP 3, Framer Motion; ports backend 8406, frontend 5406

## 3. Datasets

### 3.1 Shipped demo corpus (synthetic, template based)

- `src/dataset.py::build_demo_dataset`: 5 sentence templates per class x 10 topics, light noise; the shipped `models/msvm_model.pkl` was trained on **750 documents** (250 per class), hold-out 20 % = 150 documents (50 per class). It reports accuracy 1.000, macro-F1 1.000, baseline accuracy 1.000: the classes are separable by the template words alone, so this score says nothing about real news.
- Shipped model structure: 571 TF-IDF + 25 stylometric = 596 features -> PCA 136 components (95.2 % variance) -> Firefly kept 57; C = 0.1842, gamma = 0.00264; training time 10.7 s; Firefly history 0.9901, 0.9906, 0.9909, 0.9910, 0.9915, 0.9916, 0.9916, 0.9916.

### 3.2 LIAR2 (real fact-checked statements) - the dataset of every real measurement

- Source: Hugging Face `chengxuphd/liar2` (Xu and Kechadi, IEEE Access 2024, doi 10.1109/ACCESS.2024.3418340), licence **Apache-2.0**; an extension of the LIAR benchmark (Wang, ACL 2017). PolitiFact statements labelled by professional fact-checkers.
- Official split (8:1:1): train 18,369, validation 2,297, test 2,296 statements; average statement length about 17.7 tokens. Only the `statement` text is used (no speaker, justification or counts - those leak the label).
- Original six labels: pants-on-fire 3,031 - false 6,605 - barely-true 3,603 - half-true 3,709 - mostly-true 3,429 - true 2,585 (whole dataset).
- Project mapping (`src/dataset.py`): true, mostly-true -> REAL; half-true -> PARTIALLY TRUE; barely-true, false, pants-on-fire -> FAKE.
- Test class counts (REAL / PARTIALLY TRUE / FAKE): [602, 371, 1323]; 3,000-document training subsample counts: [786, 484, 1730]. Majority class (FAKE) share of the test split = 0.576.
- Training subsample: 3000 statements drawn stratified from the 18,369 (compute limit: the Firefly search needs thousands of SVM fits); seeds [2024, 42, 7]. Scored on the full official validation and test splits.

## 4. Architecture summary (agrees with the diagrams)

- Three tiers: React/Vite UI (6 screens) -> FastAPI `backend/main.py` (339 lines) -> library `src/` (preprocessing 91, dataset 110, firefly 106, pipeline 181 lines) -> `models/msvm_model.pkl` (joblib bundle). No SQL database; no login. Also kept: CLI (`train.py`, `predict.py`) and a Streamlit app (`app.py`, 230 lines).
- Pipeline: `clean_text` (lower-case, drop URLs, @/# tokens, non-letters, stop words, tokens <= 2 chars) -> TF-IDF (1-2 grams, sublinear tf, min_df 2, max_df 0.9, max_features 4000 default) + 25 stylometric features -> StandardScaler -> PCA (95 % variance, at most 300 components) -> 80/20 stratified split -> Firefly (population 10, 12 generations, mask over PCA components + log10 C in [-1,3] + log10 gamma in [-4,1], fitness = 3-fold CV macro-F1 - 0.02 x selected share; alpha 0.2 decayed 0.97 per generation, beta0 1, gamma 1) -> SVC (RBF, one-vs-rest shape, class_weight balanced, probability=True).
- Endpoints: GET /api/health, GET /api/model, GET /api/samples, POST /api/predict (min 5 words, else 422), POST /api/batch/preview, POST /api/batch/run (<= 20,000 rows, <= 25 MB), POST /api/retrain (202; fireflies 4-20, generations 3-30, max_tfidf 1000-8000; 409 if a job runs; < 30 rows -> 400), GET /api/retrain/{job_id}.
- Screens: Landing `/`, Detect `/app`, Batch check `/app/batch`, Model analytics `/app/analytics`, Retrain `/app/retrain`, About `/app/about`, 404.
- Code size (wc -l): src 488 + backend 339 + app/train/predict 320; frontend TypeScript/TSX 4,865 lines (pages 1,303); scripts: smoke_test 127, unit_edge_tests, run_experiments, etc.

## 5. Results on real data (LIAR2, 3 classes) - test split, mean ± std over seeds

Seeds run: [2024, 42, 7] (3 runs). Training subsample 3000; Firefly 10 fireflies x 12 generations; 550 ± 34 fitness evaluations per search.

| Model | Accuracy | Macro-F1 | Weighted-F1 |
|---|---|---|---|
| Majority class (always FAKE) | 0.576 ± 0.000 | 0.244 ± 0.000 | 0.421 ± 0.000 |
| Complement NB, TF-IDF, 3,000 docs | 0.584 ± 0.003 | 0.426 ± 0.010 | 0.551 ± 0.004 |
| Logistic regression, TF-IDF, 3,000 docs | 0.554 ± 0.010 | 0.470 ± 0.011 | 0.563 ± 0.008 |
| Linear SVM, TF-IDF, 3,000 docs | 0.560 ± 0.009 | 0.444 ± 0.009 | 0.551 ± 0.006 |
| Complement NB, TF-IDF, all 18,369 docs | 0.599 ± 0.000 | 0.481 ± 0.000 | 0.588 ± 0.000 |
| Logistic regression, TF-IDF, all 18,369 docs | 0.573 ± 0.000 | 0.500 ± 0.000 | 0.588 ± 0.000 |
| Linear SVM, TF-IDF, all 18,369 docs | 0.575 ± 0.000 | 0.475 ± 0.000 | 0.575 ± 0.000 |
| PCA + default RBF SVM (baseline of the product) | 0.505 ± 0.011 | 0.441 ± 0.010 | 0.522 ± 0.010 |
| PCA + Firefly mask only (default C, gamma) | 0.481 ± 0.015 | 0.425 ± 0.014 | 0.502 ± 0.016 |
| PCA + random search (same budget and fitness) | 0.494 ± 0.019 | 0.436 ± 0.009 | 0.514 ± 0.011 |
| **PCA + Firefly + MSVM (proposed)** | 0.494 ± 0.008 | 0.429 ± 0.010 | 0.511 ± 0.007 |

Validation split (proposed): accuracy 0.501 ± 0.007, macro-F1 0.439 ± 0.010. Internal 20 % hold-out of the training subsample (what the app's Analytics screen shows): accuracy 0.495 ± 0.017, macro-F1 0.413 ± 0.003.

Per-class test results (proposed, mean ± std):

| Class | Precision | Recall | F1 |
|---|---|---|---|
| REAL | 0.374 ± 0.009 | 0.474 ± 0.028 | 0.418 ± 0.011 |
| PARTIALLY TRUE | 0.211 ± 0.011 | 0.276 ± 0.054 | 0.238 ± 0.023 |
| FAKE | 0.714 ± 0.024 | 0.565 ± 0.026 | 0.630 ± 0.010 |

Confusion matrix, seed 42 (rows true REAL / PARTIALLY TRUE / FAKE; columns predicted): [[272, 117, 213], [142, 84, 145], [324, 218, 781]]. Sum over seeds: [[856, 390, 560], [461, 307, 345], [971, 755, 2243]].

### 5.1 Optimisation and cost

- PCA: 4,025 features -> 300 components (cap 300 reached; variance kept 29.3 % ± 0.2) -> Firefly kept 148 ± 12 components; best C 8.47, best gamma 0.00102.
- Firefly best fitness 0.4334 ± 0.0102 vs random search 0.4256 ± 0.0051 (random kept 154 components on average).
- Training time (whole pipeline fit incl. Firefly): 504 ± 75 s; random search alone 480 s; default SVM fit 1.20 s; linear SVM on 3,000 docs 0.63 s, on 18,369 docs 0.34 s.
- Scoring times measured inside the experiment runs are not quoted (other jobs were running); use the idle API measurement in section 7.

### 5.2 The shipped synthetic-demo model on real LIAR2 test statements

Accuracy 0.192, macro-F1 0.155; predicted counts (REAL / PARTIALLY TRUE / FAKE) [172, 2044, 80]; confusion matrix [[36, 555, 11], [24, 341, 6], [112, 1148, 63]].

### 5.3 Error analysis (seed 42, test split)

Accuracy by confidence (highest class probability):

| Confidence bin | n | Accuracy |
|---|---|---|
| [0.0, 0.4) | 7 | 0.286 |
| [0.4, 0.5) | 462 | 0.368 |
| [0.5, 0.6) | 1070 | 0.407 |
| [0.6, 0.7) | 643 | 0.681 |
| [0.7, 0.8) | 109 | 0.789 |
| [0.8, 1.01) | 5 | 1.000 |

Accuracy by statement length (words):

| Words | n | Accuracy |
|---|---|---|
| 0-9 | 275 | 0.560 |
| 10-14 | 665 | 0.525 |
| 15-19 | 584 | 0.483 |
| 20-29 | 564 | 0.466 |
| 30+ | 208 | 0.428 |

Predicted counts {'FAKE': 1139, 'REAL': 738, 'PARTIALLY TRUE': 419} vs true counts {'FAKE': 1323, 'REAL': 602, 'PARTIALLY TRUE': 371}. Misclassification pairs: {'FAKE -> PARTIALLY TRUE': 218, 'FAKE -> REAL': 324, 'PARTIALLY TRUE -> FAKE': 145, 'PARTIALLY TRUE -> REAL': 142, 'REAL -> FAKE': 213, 'REAL -> PARTIALLY TRUE': 117}.

**Verdict vs probabilities (a product finding):** the verdict is `SVC.predict` (class-weighted decision function); the class probabilities come from Platt scaling (`probability=True`). On 1120 of 2296 test statements (48.8 %) the verdict is not the class with the highest probability. Verdict counts [738, 419, 1139] vs argmax-probability counts [44, 0, 2252] (REAL / PARTIALLY TRUE / FAKE); PARTIALLY TRUE is the top-probability class for 0 statements. Taking the argmax probability as the verdict would give accuracy 0.578 but macro-F1 0.264 (it almost always says FAKE). The confidence shown in the UI is the maximum probability, so it can belong to a different class than the verdict. Cross-tab (rows verdict, columns argmax): {'REAL': {'REAL': 37, 'PARTIALLY TRUE': 0, 'FAKE': 701}, 'PARTIALLY TRUE': {'REAL': 7, 'PARTIALLY TRUE': 0, 'FAKE': 412}, 'FAKE': {'REAL': 0, 'PARTIALLY TRUE': 0, 'FAKE': 1139}}.

Prediction by original six-way label (counts):

| Original label | n | REAL | PARTIALLY TRUE | FAKE |
|---|---|---|---|---|
| pants-on-fire | 303 | 63 | 31 | 209 |
| false | 660 | 141 | 113 | 406 |
| barely-true | 360 | 120 | 74 | 166 |
| half-true | 371 | 142 | 84 | 145 |
| mostly-true | 343 | 137 | 77 | 129 |
| true | 259 | 135 | 40 | 84 |

## 6. Comparison with the base paper (datasets differ - state this wherever compared)

| | Base paper (Saad et al. 2026) | This project |
|---|---|---|
| Language / data | Arabic, 7,474 articles (multi-source, part translated from LIAR/WELFake) | English, LIAR2 statements (18,369 / 2,297 / 2,296) |
| Task | binary real / fake | three-class REAL / PARTIALLY TRUE / FAKE |
| Features | CAMeLBERT contextual embeddings | TF-IDF (1-2 grams) + 25 stylometric, PCA |
| Classifier | neural network + class weights | RBF multi-class SVM + balanced class weights, Firefly tuned |
| Compute | Tesla T4 GPU | CPU only (i5-12500) |
| Reported | accuracy 95.52 %, F1 96.19 % | accuracy 49.4 %, macro-F1 42.9 % (not comparable: harder task and data) |

## 7. API latency and throughput (127.0.0.1, sequential requests, CPU idle)

- `liar2_msvm_model.pkl`: start-up 6.09 s; POST /api/predict client round trip mean 12.6 ms, p50 6.5, p95 29.8, max 76.7 (n=300); server-reported latency mean 3.7 ms, p95 5.3; batch 100 rows 0.13 s, 1,000 rows 0.55 s, 2,296 rows 1.2 s (server time)
- `msvm_model.pkl`: start-up 2.79 s; POST /api/predict client round trip mean 9.7 ms, p50 5.0, p95 27.7, max 31.8 (n=300); server-reported latency mean 2.2 ms, p95 3.8; batch 100 rows 0.02 s, 1,000 rows 0.2 s, 2,296 rows 0.66 s (server time)

## 8. Tests

- `scripts/smoke_test.py`: 16 checks, all passed (API end to end on a copy of the model).
- `scripts/unit_edge_tests.py`: 34 library checks + 33 API edge checks = 67, all passed.
- Total: 83 automated checks. `npm run build` (tsc -b + vite build): passes (tsc -b && vite build, 6.7 s).
- KNOWN ISSUE: load_csv: a label column containing only the words true/false is read by pandas as booleans and mapped true -> PARTIALLY TRUE, false -> REAL instead of REAL / FAKE

## 9. Screenshot inventory (`docs/screenshots/`, 1440x900, real data)

- `01_landing_dark.png` (289 KB)
- `01_landing_light.png` (256 KB)
- `02_landing_how_it_works.png` (193 KB)
- `03_detect_result.png` (326 KB)
- `04_batch_results.png` (291 KB)
- `05_analytics.png` (250 KB)
- `05b_analytics_charts.png` (263 KB)
- `06_retrain.png` (215 KB)
- `07_retrain_running.png` (250 KB)
- `08_retrain_done.png` (232 KB)
- `09_about.png` (246 KB)
- `10_liar2_landing.png` (290 KB)
- `11_liar2_detect_fake.png` (331 KB)
- `11_liar2_detect_fake_input.png` (283 KB)
- `12_liar2_detect_real.png` (331 KB)
- `12_liar2_detect_real_input.png` (286 KB)
- `13_liar2_detect_partial.png` (333 KB)
- `13_liar2_detect_partial_input.png` (286 KB)
- `14_liar2_detect_miss.png` (331 KB)
- `14_liar2_detect_miss_input.png` (285 KB)
- `15_liar2_batch_preview.png` (183 KB)
- `16_liar2_batch_results.png` (293 KB)
- `17_liar2_analytics.png` (252 KB)
- `18_liar2_analytics_charts.png` (273 KB)
- `19_liar2_about.png` (247 KB)
- `20_liar2_retrain.png` (215 KB)
- `21_liar2_retrain_running.png` (162 KB)
- `22_liar2_retrain_done.png` (235 KB)
- Files 01-09 were captured by the frontend build on the shipped synthetic-demo model (100 % analytics, disclaimer visible); files 10-22 were captured for the documentation on the model trained on real LIAR2 data.

## 10. Honest gaps and deviations (state plainly in every document)

- The shipped model and its 100 % figures come from a synthetic template corpus; the real-data results are those of section 5.
- LIAR2 results use a 3,000-statement training subsample (compute); a linear SVM trained on all 18,369 statements is reported beside it as an upper reference. Only three seeds were run, no significance test.
- Objective 2 lists stemming; the code does not stem (cleaning, stop-word removal, TF-IDF only). The Documentary file lists five veracity categories; the product uses three (mapped from LIAR's six).
- Firefly hyper-parameters (alpha, beta0, gamma, penalty 0.02, population 10, 12 generations) were not tuned. PCA is capped at 300 components, so it keeps well under 95 % of the variance on real text.
- No ISOT, no other dataset, no cross-dataset test other than demo-model-on-LIAR2; no user study; no concurrency/load test; no GPU; no security audit beyond input validation.
- Verdict and displayed probabilities/confidence come from two different mechanisms and disagree on about half of the real test statements (section 5.3); the demo model never showed this because its classes are perfectly separable.
- Some fixed UI wording assumes the demo model (landing metric strip: 'Scored on a held-out 20% test split of its demo corpus'; Analytics note about the synthetic corpus; example chips 'from the demo corpus'). It stays visible when a model trained on real data is loaded.
- Known library issue: `load_csv` on a label column containing only the words true/false (pandas parses them as booleans) maps true -> PARTIALLY TRUE and false -> REAL.
