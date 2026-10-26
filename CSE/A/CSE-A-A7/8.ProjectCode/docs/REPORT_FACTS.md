# ATHENA - report facts (single source for all documents)

Every number below was measured on this project. Source files are named next to each table.
Documents must agree with this file. **The triage model is trained and evaluated on seeded synthetic data**
(no real patient records); every results statement must say so.

## 1. Project and people
- Title: ATHENA - Autonomous Triage and Healthcare Electronic Neural Assistant (CSE-A, Batch A7)
- Domain: Artificial Intelligence in Healthcare and Medical Informatics
- Students: BADAVENI SRINATH 23K91A0523 · BASANI AVINASH 23K91A0532 · DEGALA PRANEETH 23K91A0561 · BONTHA SAISREE 23K91A0545
- Guide: K. SHALINI (designation not stated in the batch file)
- Institution: TKR College of Engineering & Technology (Autonomous), Department of Computer Science and Engineering (name appears in `Documentary/Batch_07_...docx`). Principal, HOD, academic year: not stated, leave placeholders.
- Base paper (batch file `3.BASE PAPER.docx`): M. Mlodawski, S. Deniziak, M. Plaza, A. Kwiatkowska, D. Jaszczyk, A. Gajda, K. Twardowski, "Multidimensional Analysis of the Diagnostic Performance of Machine Learning Models in Disease Classification: Implications for Clinical Decision Support Systems," IEEE Access, vol. 14, pp. 92149-92177, 2026, doi 10.1109/ACCESS.2026.3703248 (PDF in `Documentary/`, 29 pages, read in full).
- Machine used for every measurement: Intel Core i5-12500 (12 threads), 15.7 GB RAM, Windows 11 Pro, CPU only (no GPU), Python 3.11.9, Node 24.19.0.

## 2. What the product is (as built)
Decision-support tool for emergency departments. A nurse uploads a scanned report (PDF or PNG/JPG) and enters 8 vitals; the system reads the report, fuses report features with vitals into 36 model inputs, assigns triage priority 1 (Critical) to 5 (Non-urgent) with a calibrated confidence and risk level (High = P1-2, Moderate = P3, Low = P4-5), lists SHAP drivers, and a clinician accepts or changes the priority (reason required for a change). Live queue ordered by priority then arrival; performance page; triage-summary PDF.

### Architecture
React 19 + Vite SPA (port 5307) -> `/api` proxy -> FastAPI (port 8307) -> services: `extract.py` (report reading), `features.py` (fused record), `triage.py` (XGBoost + isotonic calibration + SHAP), `pdf.py` (ReportLab summary) -> SQLite via SQLAlchemy (`data/app.db`). Auth: bcrypt password hashes, HS256 JWT (12 h), roles clinician / admin (demo users seeded). Code size: about 4,100 lines (backend, ml, frontend pages/lib/components, tests).

### Report reading (`backend/app/services/extract.py`)
1. PDF: text layer via pypdf; a page without a text layer (<20 chars) falls back to OCR on its first embedded image.
2. Image: local OCR with RapidOCR (ONNX runtime, PaddleOCR-family models, no network); image upscaled x1.6 if its longer side < 2000 px; boxes sorted into reading order.
3. Parse: wrapped lines re-joined, sentences split, then a lexicon of 22 regex flags (11 symptoms, 5 findings, 6 history); spaces in phrases tolerate OCR run-ons; negation (`no, denies, denied, without, negative for, absence of, not, nil, free of, ruled out` within 45 characters before the match) drops the flag.
4. Labs: 6 labs parsed with value, unit and reference range (troponin >0.04 ng/mL, lactate >2.0 mmol/L, WBC >11, glucose <70 or >250 mg/dL, creatinine >1.3 mg/dL, haemoglobin <10 g/dL); an abnormal value sets the lab flag.
5. Every item keeps its page number. Upload limit 15 MB; empty file 400, unreadable 422.
- Not implemented from the original objectives: BioBERT (medical language model), PaddleOCR proper (RapidOCR used), RAG, multi-agent orchestration, MongoDB, Node.js frontend server, Flask (FastAPI used), LIME, the six-disease risk models (diabetes, heart, CKD, breast cancer, liver, sepsis), Gemini (dropped by choice, no API key). State these as gaps.

### Fused record (`features.py`)
36 inputs = 8 vitals (age, heart rate, systolic BP, diastolic BP, SpO2, temperature, respiratory rate, arrival mode coded walk-in 0 / transfer 1 / ambulance 2) + 28 report flags (11 symptom, 5 finding, 6 history, 6 lab).

### Model (`ml/train.py`, `services/triage.py`)
XGBoost multi:softprob, 220 trees, depth 4, learning rate 0.1, subsample 0.9, colsample 0.9, seed 7307; isotonic calibration (sklearn `CalibratedClassifierCV` on `FrozenEstimator`) fit on a separate calibration split; priority = argmax of calibrated probabilities; SHAP `TreeExplainer` on the same trees, contribution toward the chosen class sorted by absolute value, absent flags with |impact| < 0.15 hidden, top 8 shown. Training time 0.44 s; model inference about 0.012 ms per patient in batch (`model_seconds_per_patient` 1.2e-05).

### Data (synthetic - read this)
`ml/make_data.py`, seed 7307, 6,000 rows (`data/sample/triage_synthetic.csv`). Seven archetypes: minor 33.6 %, cardiac 14.6 %, respiratory 11.9 %, trauma 11.7 %, abdominal 10.3 %, infection 9.4 %, neuro 8.5 %. Vitals drawn from clipped normals shifted per archetype, flags from per-archetype probabilities; a hand-written severity score (vitals thresholds + flag weights + arrival bonus) plus Gaussian noise (sd 0.4) is cut at 1.2 / 3.0 / 5.2 / 8.0 into priorities. Priority share: P1 5.5 %, P2 19.9 %, P3 26.1 %, P4 26.7 %, P5 21.8 %. Split: 3,840 fit / 960 calibration / 1,200 test (80/20 stratified, then 80/20 of the training part). Kaggle "Hospital Triage and Patient History Data" (maalona; licence not stated) is the intended real-data source: `scripts/download_data.py` exists but was **never run or tested**; no real patient data was used.
Sample reports: 12 generated files (8 two-page PDFs, 4 PNG scans) in `data/sample_reports/` with `expected.json`.

## 3. Real metrics (shipped model, 1,200 held-out synthetic cases) - `experiments/metrics.json`, `experiments/eval/metrics.json`
| Metric | Value |
|---|---|
| Accuracy (exact priority) | 69.42 % |
| Within one priority level | 99.67 % |
| Macro F1 | 0.6696 |
| Quadratic weighted kappa | 0.8796 |
| Top-2 accuracy | 95.33 % |
| Mean confidence | 0.7321 |
| Recall P1 / P2 / P3 / P4 / P5 | 43.94 / 53.97 / 72.84 / 71.88 / 82.82 % |
| Support P1..P5 | 66 / 239 / 313 / 320 / 262 |
| Confusion matrix (rows = recorded, cols = model) | P1 [29,35,2,0,0] · P2 [9,129,101,0,0] · P3 [0,21,228,62,2] · P4 [0,0,36,230,54] · P5 [0,0,0,45,217] |
| Uncalibrated shipped base model | accuracy 68.25 %, macro F1 0.6532 |
| Report reading, 12 generated samples | precision 100 %, recall 100 %, 12/12 read exactly |
| End to end per patient (read report + model), 12 samples | mean 1.261 s, median 0.017 s, max 4.323 s (PDFs ~instant, image scans 2-5 s on CPU) |

## 4. Extra experiments (`scripts/run_experiments.py` -> `experiments/extra/metrics.json`)
Same split, same 3,840 fit rows, test = the 1,200 held-out rows. Models trained uncalibrated.
| Model | Accuracy | Within 1 | Macro F1 | QWK | Top-2 | Fit s |
|---|---|---|---|---|---|---|
| Logistic regression | 72.42 | 99.67 | 0.7268 | 0.8966 | 96.42 | 0.07 |
| Decision tree (depth 8) | 54.67 | 94.67 | 0.5301 | 0.7610 | 80.50 | 0.02 |
| Random forest (300) | 67.17 | 99.67 | 0.6231 | 0.8708 | 95.08 | 0.52 |
| Extra trees (300) | 69.08 | 99.17 | 0.6534 | 0.8721 | 94.33 | 0.50 |
| k-NN (k=15) | 62.58 | 97.75 | 0.5642 | 0.8297 | 89.25 | 0.00 |
| MLP (64,32) | 70.92 | 99.33 | 0.7011 | 0.8880 | 97.25 | 6.07 |
| HistGradientBoosting | 70.33 | 99.58 | 0.6686 | 0.8843 | 95.58 | 0.94 |
| XGBoost (shipped config, uncalibrated) | 68.25 | 99.67 | 0.6532 | 0.8768 | 95.50 | 0.48 |

**Finding:** logistic regression beats XGBoost here. The synthetic labels come from an additive severity score, which a linear model recovers well. The model choice (XGBoost + SHAP TreeExplainer) was made for explanation and calibration, not because it won; say so.
5-fold CV accuracy on all 6,000 rows: logistic regression 71.58 % (sd 2.15), random forest 71.12 % (sd 0.91), XGBoost 72.37 % (sd 1.52). Five different split seeds for the shipped recipe: accuracy 71.57 % mean (sd 0.93), macro F1 0.6816; the shipped seed (7307) at 69.42 % is a below-average split.
**Label-noise ceiling:** knowing the clean severity score (no noise) reproduces the label for 86.25 % of rows, so about 86 % is the best exact accuracy any model can reach on this data; within-one 100 %.

### Modality ablation (XGBoost, same split) - the base paper's single-modality gap, measured
| Inputs | Accuracy | Within 1 | Macro F1 | QWK | Top-2 |
|---|---|---|---|---|---|
| Vitals only (8) | 40.58 | 82.25 | 0.3666 | 0.4888 | 70.33 |
| Report only (28) | 63.17 | 97.25 | 0.6146 | 0.8345 | 92.17 |
| Vitals + text flags (30) | 61.50 | 96.92 | 0.5767 | 0.8239 | 89.67 |
| Vitals + lab flags (14) | 46.92 | 87.92 | 0.4288 | 0.6081 | 77.75 |
| Fused (36) | 68.25 | 99.67 | 0.6532 | 0.8768 | 95.50 |
Fusing report and vitals adds 27.7 points of accuracy over vitals alone and 5.1 over the report alone (synthetic data; a property of how the data was generated as much as of the model).

### Calibration
ECE (10 bins, top label): uncalibrated 0.0466 -> isotonic 0.0412; Brier (multiclass, summed): 0.4187 -> 0.4104; mean confidence 0.6456 -> 0.7321 (accuracy 69.42 %). Isotonic calibration helps modestly. Reliability bins (isotonic): conf 0.54 -> acc 0.52 (n=189); 0.65 -> 0.66 (240); 0.75 -> 0.71 (325); 0.85 -> 0.66 (138, overconfident); 0.95 -> 0.94 (242).

### Confidence threshold and coverage (calibrated)
| Threshold | Coverage | Accuracy | Within 1 |
|---|---|---|---|
| 0.0 | 100 % | 69.42 | 99.67 |
| 0.5 | 94.7 % | 71.21 | 99.82 |
| 0.6 | 78.8 % | 75.03 | 99.79 |
| 0.7 | 58.8 % | 78.16 | 99.72 |
| 0.8 | 31.8 % | 84.03 | 100 |
| 0.85 | 25.5 % | 87.58 | 100 |
| 0.9 | 20.2 % | 94.21 | 100 |
| 0.95 | 9.7 % | 94.83 | 100 |

### Safety view (1,200 test cases)
Under-triage (model less urgent than recorded) 21.33 %, over-triage 9.25 %; two or more levels under 0.33 % (4 cases), over by two or more 0 %. Of 66 recorded P1 cases 2 were placed at P3 or lower urgency, none at P4/P5. Binary high-risk (P1-P2, 305 cases): recall 66.23 %, precision 90.58 % with argmax; flagging high risk when P(1)+P(2) >= 0.4 gives recall 84.26 %, precision 81.59 % (a threshold not implemented in the product; reported as a possible improvement).

### Robustness: report flags dropped at inference (each positive flag removed with probability p)
| p | Accuracy | Within 1 | Macro F1 |
|---|---|---|---|
| 0 | 69.42 | 99.67 | 0.6696 |
| 0.1 | 66.17 | 98.08 | 0.6331 |
| 0.2 | 62.08 | 96.33 | 0.5941 |
| 0.3 | 59.50 | 95.00 | 0.5645 |
| 0.5 | 50.92 | 89.50 | 0.4647 |
| 1.0 (no report) | 33.92 | 70.42 | 0.2459 |
The model degrades gracefully but a missed report finding is costly: a reader recall of 84 % (section 5) puts the product near the p = 0.1-0.2 rows.

### Global SHAP importance (mean |SHAP| over test set, all classes)
SpO2 0.422, arrival mode 0.325, shortness of breath 0.271, systolic BP 0.237, respiratory rate 0.235, ST elevation 0.228, focal weakness/speech 0.220, troponin raised 0.213, chest pain 0.200, lactate raised 0.177, altered mental state 0.172, heart rate 0.132, trauma 0.130, age 0.124, intracranial haemorrhage 0.106. Matches the severity weights used to build the labels, which is a sanity check on the explainer, not clinical validation.

## 5. Report-reader stress test (`scripts/extract_stress.py` -> `experiments/extra/extract_stress.json`)
40 short fragments written by the developers (not independent clinical text), 70 expected flags: precision 95.16 %, recall 84.29 %, 27/40 read exactly.
| Category | Cases | Precision | Recall |
|---|---|---|---|
| plain statements | 10 | 0.950 | 1.000 |
| negation | 6 | 0.500 | 0.667 |
| abbreviations | 4 | 1.000 | 1.000 |
| OCR run-ons/split words | 4 | 1.000 | 0.571 |
| lab values | 5 | 1.000 | 1.000 |
| history | 3 | 1.000 | 1.000 |
| paraphrases outside the lexicon | 5 | 1.000 | 0.143 |
| mixed narrative | 3 | 1.000 | 0.909 |
Known defects found: "Afebrile" matches "febrile" (negating prefix not handled); "Chest pain: absent" (post-positioned negation) still flags; "denies X but reports Y" negates Y too (45-character window ignores "but"); "haematemesis" also triggers vomiting (the "emesis" pattern); split OCR words ("vomit ing", "elevat ion") are missed; "fall at home" is not "trauma"; paraphrases ("cannot catch his breath", "crushing pain in the centre of the chest") are missed. The generated sample reports score 100 % because they were written with the lexicon in view; the 84 % recall is the more honest figure.

Defect found while writing Chapter 7: the API field `direction` ("raises urgency" / "lowers urgency") is derived from the sign of the SHAP value toward the *predicted* class, so it reads the wrong way round when the predicted priority is 4 or 5 (a positive contribution raises the score of a low-urgency class). The on-screen bars are unaffected. Not fixed (documentation run); documented in Chapter 7.
Cold starts measured in a fresh process: first SHAP call 11.7 s, first OCR scan 7.6 s (the server warms both at start-up).

## 6. Testing
- `tests/` (pytest, scratch SQLite): 47 tests - 46 pass, 1 expected failure (negation-scope limitation above, marked xfail), 0 fail. test_extract 20 (19 pass + 1 xfail), test_triage 11, test_api 16. Run time about 15 s.
- `scripts/smoke_test.py` against the running API: all 17 checks pass (re-run in this session against a scratch database) (login, bad password, auth required, 12 report reads, create patient, SHAP order, override rules, queue order, metrics, PDF, 404).
- `scripts/check_responsive.py` (360 / 768 / 1440 px, light and dark, keyboard, reduced motion) and `scripts/capture_screens.py` (12 screens): passed when the frontend was built (`docs/FRONTEND_PLAN.md`); `npm run build` passes. Not re-run in the documentation session.
- Not tested: fresh-venv `setup.bat`, `scripts/download_data.py`, any multi-user concurrency, any real scan other than the 4 generated PNGs, any clinician usability study. No security testing beyond: JWT required on every patient route, bcrypt hashes, path-traversal check on the samples route, 15 MB upload cap, input range validation (pydantic), SQL via ORM.
- Known security gaps: default JWT secret `dev-secret-change-me` when `JWT_SECRET` unset (PyJWT warns the key is 22 bytes), CORS fixed to localhost origins, no rate limiting, no HTTPS, no audit log beyond overrides, demo passwords seeded.

## 7. Latency over HTTP (`scripts/measure_api.py` -> `experiments/extra/api_latency.json`, 127.0.0.1, scratch DB)
| Endpoint | n | Median ms | p95 ms |
|---|---|---|---|
| GET /health | 50 | 2.7 | 3.3 |
| POST /auth/login (bcrypt) | 10 | 216.1 | 225.4 |
| GET /patients (queue) | 30 | 9.4 | 10.7 |
| POST /reports/extract, PDF | 30 | 9.3 | 10.6 |
| POST /reports/extract, PNG scan (OCR) | 10 | 2,232.9 | 2,706.8 |
| POST /patients (model + SHAP) | 30 | 21.7 | 27.8 |
| GET summary.pdf | 20 | 9.0 | 10.7 |
| GET /metrics | 20 | 16.2 | 18.6 |
| Flow: PDF extract + triage | 20 | 30.2 | 43.0 |
| Flow: scan extract + triage | 10 | 2,149.7 | 2,290.7 |
(The live performance page showed 0.30 s average per patient in the screenshot session; that mixes PDF and scan cases.)

## 8. API (all under `/api`)
GET /health · GET /public/stats · POST /auth/login · GET /auth/me · GET /samples · GET /samples/{file} · POST /reports/extract · POST /patients · GET /patients · GET /patients/{id} · GET /patients/{id}/summary.pdf · POST /patients/{id}/override · GET /metrics (13 endpoints). Everything except health, public/stats and login needs a bearer token.

## 9. Database (SQLAlchemy, SQLite)
- users(id, name, email unique, password_hash, role)
- patients(id, name, created_at, created_by FK users, source live|sample, vitals JSON, report JSON, fused JSON, model_priority, priority, risk_level, confidence, probabilities JSON, shap JSON, ocr_seconds, model_seconds, total_seconds, recorded_outcome)
- overrides(id, patient_id FK, user_id FK, user_name, old_priority, new_priority, action accept|change, reason, created_at)
Relations: user 1-N patients (created_by), patient 1-N overrides, user 1-N overrides. Seeds: 2 demo users, 12 sample cases (from `holdout_sample.csv`, `source = sample`, with `recorded_outcome`).

## 10. Frontend
React 19.3, Vite 8, react-router 7, recharts 3, framer-motion, gsap, lucide-react; "Neo Brutal Grid" design kit. 31 source files. Screens: Landing, Login, New patient, Result, Triage queue, Performance. Dark mode, drawer nav below tablet width, keyboard focus.

## 11. Literature facts verified for this run
- Base paper (read in full): 1,655 real clinical cases (internal medicine 616, pediatrics 1,039), 19 algorithms, ICD-10, 87 diagnostic classes (32 pediatrics, 55 internal medicine), 479 clinical parameters; internal medicine best = Gradient Boosting 84.74 % TOP-1; pediatrics best = MLP 87.20 %; TOP-3 mean 77.43 % (internal) / 81.99 % (pediatrics); TOP-3 best 91.72 % / 94.71 %; external validation on 120 cases: TOP-1 73.33 % / 78.33 %, TOP-3 86.67 % / 90.00 %; Optuna TPE tuning, 100 trials per model; SHAP + LIME; 0.85 confidence threshold; McNemar tests and bootstrap CIs; no imputation, absent symptom = 0; rule-based augmentation of rare diseases.
- Batch survey (`5.LITERATURE SURVEY.docx`) items: [2] Identifying the High-Risk Obstetric Patient at Triage, J. Emerg. Nurs., 2026 - **could not be located by web search; listed but not cited**. [3] Anatolian Current Medical Journal 2025 (vol. 7, no. 1): prospective comparison of ESI vs Manchester triage, 6,000 patients each, Esenyurt Necmi Kadioglu State Hospital, Turkey (dergipark.org.tr/tr/pub/acmj/article/1579702). [4] "Emergency Diagnostic Assessment During Triage" is chapter 6 of the Wiley book *Emergency Triage of the Horse* (2025) - veterinary, out of domain; listed with that note. [5] Assessment of knowledge of triage among patient attendants, single-centre cross-sectional study, 284 participants, BPKIHS Dharan, Nepal (nepjol.info/index.php/jgpemn/article/view/87619); 2024 date from batch file, not confirmed.
- Companion paper (`archived_base_papers/`): Cheng et al., "Collaborative Medical Triage under Uncertainty: A Multi-Agent Dynamic Matching Approach," arXiv:2507.22504, 2025. Archived record also names Jang et al., "TRIAGE: Dialectical Reasoning for Explainable Risk Prediction on Irregularly Sampled Medical Time Series with LLMs," arXiv:2606.09030, 2026 as a base paper; the batch documents (authoritative) name the IEEE Access paper. Use IEEE Access as the base paper; cite the two arXiv papers as related work, from their titles only.
- Verified by web search this run: Fernandes et al., Artif. Intell. Med. 102:101762 (2020); Hinson et al., Ann. Emerg. Med. 74(1):140-152 (2019); Hong, Haimovich, Taylor, PLoS ONE 13(7):e0201016 (2018; 560,486 visits, triage-only AUC ~0.87, full ~0.91-0.92); Levin et al., Ann. Emerg. Med. 71(5):565-574 (2018; 172,726 visits, AUC 0.73-0.92); Raita et al., Crit. Care 23:64 (2019; 135,470 visits, DNN AUC 0.86 vs ESI 0.74 for critical care); Xie et al., Sci. Data 9:658 (2022, MIMIC-IV-ED benchmark).
- Method references from the authors' knowledge (stable, well-known): Chen & Guestrin XGBoost KDD 2016; Lundberg & Lee SHAP NeurIPS 2017; Lundberg et al. TreeExplainer Nat. Mach. Intell. 2020; Zadrozny & Elkan 2002; Niculescu-Mizil & Caruana 2005; Guo et al. 2017; Grinsztajn et al. NeurIPS 2022; Lee et al. BioBERT Bioinformatics 2020; Du et al. PP-OCR arXiv:2009.09941; Breiman 2001; Pedregosa 2011.

## 12. Screenshot inventory (`docs/screenshots/`, 1440x900, real running app, demo login, seeded queue + one live patient)
01_landing_light.png · 02_landing_dark.png · 03_login.png · 04_queue.png (queue before new patient) · 05_new_patient_empty.png · 06_new_patient_filled.png (sample report 01 read, vitals filled) · 07_result.png (priority 1 Critical) · 08_result_why.png (SHAP "why this priority", extracted findings with pages) · 09_override_modal.png · 10_result_decision.png (after change) · 11_queue_updated.png (13 cases, override shown as CHANGED) · 12_performance.png (accuracy 69.4, within-one 99.7, macro F1 0.670, 0.30 s live average, confusion matrix).

## 13. Diagrams (generated in `docs/diagrams/`, step 2)
system architecture · high-level workflow · DFD 0/1/2 · UML class diagram · sequence diagram (new patient to override) · use-case diagram · ER diagram · core-algorithm flowchart.

## 14. Honest gaps (state plainly in every document)
1. No real patient data: accuracy measures recovery of a known synthetic rule, not agreement with clinicians. Objective 6 (accuracy against clinician-assigned priority) is only met against the synthetic recorded priority.
2. No medical language model (BioBERT) - rule-based lexicon; no RAG, no multi-agent orchestration, no six-disease risk models, no MongoDB, no LIME.
3. Report reader: 100 % on generated samples, 84.3 % recall on the hand-written stress set; real scans untested.
4. P1 recall 43.9 % and high-risk (P1-P2) recall 66.2 % at argmax: the model under-triages the sickest patients most often; a clinician must review every priority.
5. Calibration only modestly improved (ECE 0.047 -> 0.041); confidence 0.8-0.9 bin is over-confident (66 % observed).
6. Linear baseline beats the shipped model on the synthetic data.
7. Security is demo-grade (default JWT secret, no HTTPS, no rate limiting).
8. No clinician user study, no prospective evaluation, no regulatory review.
