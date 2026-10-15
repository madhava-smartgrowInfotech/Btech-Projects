# Report facts - PhishGuard (CSDS-A-A3)

Single source for every number in the submission documents. All values were measured on 15 Oct 2026 from this
folder's own artefacts: `models/metrics.json`, `docs/experiments/*.json` (written by `scripts/measure_results.py`,
`scripts/extra_tests.py`, `scripts/demo_scenario.py`) and the screenshots in `docs/screenshots/`.

**Naming.** The application is branded **PhishGuard** everywhere in code, UI and README (the master prompt
calls it PhishShield). The documents use **PhishGuard** so that text and screenshots agree.

## 1. Project

| Item | Value |
|---|---|
| Title | A Dynamic Phishing URL Detection System Integrating Advanced Machine Learning and Crowdsourced Threat Intelligence |
| Batch | A3 - CSE (Data Science), Section A |
| Students | D. Anish Meghan 23K91A6750 · B. Akshaya 23K91A6737 · B. Tanuja 23K91A6736 · Ch. Sai Chethan 23K91A6742 |
| Guide | Mr. G. Ravi (designation not given: placeholder kept) |
| College / principal / HOD / academic year | not given: placeholders kept |
| Base paper | L. Aldhuwayhi and A. Alromih, "A Dynamic Phishing URL Detection System Integrating Advanced Machine Learning and Crowdsourced Threat Intelligence," IEEE Access, vol. 14, pp. 88393-88404, 2026, doi 10.1109/ACCESS.2026.3700833 |
| Ports | backend 8103, frontend 5103 |

## 2. Base paper (read in full from `Documentary/`)

- Three phases: Extractor, Detection, Updating by crowdsourcing. Unknown / novel inputs are queued for **human (administrator) verification** before they join the training set.
- Dataset: PhiUSIIL, 235,804 URLs (134,850 legitimate, 100,945 phishing), 54 URL + page-content features; undersampled to 100,945 per class; ANOVA + chi-square selection to 34 features; stratified split.
- Model: hybrid deep network - Embedding(50) -> LSTM -> attention -> LSTM(64) for the URL text, Dense(64) for 34 numeric features, concatenate (128) -> sigmoid.
- Reported: accuracy 0.9980, F1 0.9988, test loss 0.0262; 5-fold cross-validation; learning-curve simulation of crowd data growth (plateau about 99.7% accuracy beyond 50% of the data); inference about 0.20 ms per URL (10 runs of 40,342 instances); "model size 48 bytes".
- Stated limits: needs real-world validation, crowd input may be noisy, adversarial misuse, scalability.
- Its literature table cites 27 references; related-work accuracies quoted in the paper: [4] Vajrobol 99.97 % (MI + LR, 5 features), [5] Etem 99.7 %, [9] Fan 99.16 %, [6] Butt 99.62 %, [7] Rathee 99.87 %, [11] Alnemari 97.3 %, [14] Taofeek 94.16 % (XGBoost), [10] Priya 97 %, [25] Assefa 91.24 % (autoencoder).

## 3. What this project built

Three-stage pipeline adopted from the base paper: feature extraction -> ML classification -> crowdsourced refinement.

| Component | File | Lines |
|---|---|---|
| Feature extraction (47 offline features) | `phishguard/features.py` | 333 |
| Dataset load / split | `phishguard/data.py` | 68 |
| Training and comparison | `phishguard/train.py` | 134 |
| Threat-intelligence store (SQLite) | `phishguard/threat_intel.py` | 250 |
| Real-time decision pipeline | `phishguard/detector.py` | 125 |
| Continuous retraining | `phishguard/retrain.py` | 76 |
| Flask app + JSON API (original UI) | `phishguard/webapp.py` | 373 |
| React-facing API layer | `backend/server.py` | 116 |
| CLI | `run.py` | 117 |
| Config | `phishguard/config.py` | 39 |
| React frontend (7 pages, Vite 5, React 18, three.js, recharts, framer-motion, gsap, lenis, lucide) | `frontend/src` | about 7,200 (JSX/JS/CSS) |

Python in `phishguard/` + `backend/` + `run.py`: 1,641 lines.

### Features (47): lexical 23 · structural 9 · domain 15
- lexical: url_length, host_length, path_length, query_length, fragment_length, num_dots, num_hyphens, num_underscores, num_slashes, num_digits, digit_ratio, num_special_chars, has_at_symbol, num_query_params, num_equals, num_ampersands, num_percent, url_entropy, suspicious_word_count, longest_token_length, has_https_in_path_or_host, has_encoded_chars, letter_ratio
- structural: is_ip_host, has_port, nonstandard_port, num_subdomains, path_depth, has_double_slash_in_path, is_url_shortener, has_file_extension, has_executable_extension
- domain: domain_length, domain_entropy, domain_digit_count, domain_hyphen_count, domain_vowel_ratio, domain_max_consonant_run, tld_length, is_suspicious_tld, is_common_tld, brand_in_domain, brand_outside_domain, subdomain_length, subdomain_has_digit, tld_in_subdomain, is_popular_domain
- Reference lists in code: 42 suspicious words, 41 brand names, 41 suspicious TLDs, 7 common TLDs, 20 URL shorteners, 145 popular domains (hand-written stand-in for a Tranco list), 37 two-level public suffixes.
- Offline only: no DNS, WHOIS, HTTP or page content, so training and run time use identical code.

### Decision logic (`detector.py`)
1. community entry **confirmed_phishing** (URL, or same host) -> phishing, probability max(0.97, model), decided_by community
2. **confirmed_safe** -> safe, probability min(0.03, model)
3. otherwise model probability p; if registered domain is in the popular list and (TLD in com/org/net/edu/gov/mil/int or TLD length > 2) then p x 0.4; each net pending vote moves p by 0.15 (clipped 0..1)
4. p >= 0.60 phishing; >= 0.35 suspicious; else safe

### Threat intelligence (`threat_intel.py`)
- Tables: `reports` (id, url_norm, url, verdict phishing|safe, reporter, source, note, created_at; index on url_norm), `intel` (url_norm PK, url, phishing_votes, safe_votes, status pending|confirmed_phishing|confirmed_safe, source, first_seen, last_updated, used_in_training), `checks` (id, url, verdict, probability, decided_by, created_at).
- Consensus: net votes >= 2 -> confirmed_phishing; <= -2 -> confirmed_safe; trusted feed phishing report -> confirmed at once. CONSENSUS_THRESHOLD = 2, AUTO_RETRAIN_EVERY = 25, CROWD_SAMPLE_WEIGHT = 3.
- Feeds: OpenPhish (feed.txt) and URLhaus (text_online), up to 500 URLs per feed. Failures are reported, never raised.
- Retrain: base data (rows the crowd re-labelled removed) + confirmed URLs repeated x3, same 80/20 stratified split, all three models refit, version +1, detector hot-reloads. Auto-retrain runs only from the form route `/sync` and from `/report` and `/api/report`; **`/api/sync` does not trigger it** (observed).
- Design differences from the base paper: base paper queues novel URLs for administrator verification; this project uses vote consensus plus trusted feeds (no administrator step). Base paper uses an LSTM-attention network on 54 URL + content features; this project uses tree ensembles / logistic regression on 47 URL-only features.

### API (Flask app, port 8103 via `backend/server.py`)
| Method | Path | Purpose |
|---|---|---|
| GET | /api/check?url= | verdict, probability, ml_probability, decided_by, reason, red_flags, 47 features, model, version, community |
| POST | /api/report | {url, verdict, reporter, note} -> intel entry |
| GET | /api/stats | threat-intel counters, metrics.json, retraining flag |
| POST | /api/retrain | blocking retrain |
| POST | /api/sync | pull OpenPhish / URLhaus |
| GET | /api/health | ok, model_ready, model, model_version |
| GET | /api/config | thresholds, feature names by group |
| GET | /api/checks?limit= | recent checks |
| GET | /api/intel?limit=&status= | intel entries |
| GET | /api/intel/lookup?url= | one entry with last 10 reports |
| GET/POST | / , /report , /community , /models , POST /retrain , POST /sync | original Flask pages |
16 routes in total (6 original pages/actions, 5 original API routes, 5 added by `backend/server.py`).

### Screens (React, port 5103)
Landing `/` · Check URL `/app/check` (single and batch) · Report `/app/report` · Threat intelligence `/app/intel` · Models `/app/models` · Activity `/app/activity` · 404.

## 4. Dataset

| Item | Value |
|---|---|
| File | `data/urls_sample.csv` (columns url,label; 1 = phishing), 2,181,263 bytes |
| Source | sample of the public "Using machine learning to detect malicious URLs" dataset (about 420k rows), as stated in `phishguard/data.py` |
| Rows | 40,000 (20,000 phishing, 20,000 legitimate), 40,000 unique URLs |
| Split | 80/20 stratified, random_state 42: 32,000 train / 8,000 test (4,000 + 4,000) |
| URL length | mean 51.5, median 40, max 1,383; phishing mean 55.9, legitimate mean 47.1 |
| Scheme | only 266 of 40,000 rows contain "://" - normalisation prepends http:// |
| Licence | not stated in the repository; the original dataset's licence was **not verified** |
| Not used | no page content, no WHOIS/DNS, no screenshots |
| Full dataset | `python run.py download` fetches it; not run, not evaluated |

## 5. Measured model results (held-out 8,000 URLs; `models/metrics.json`, reproduced)

Reproduction check (`measure_results.py`): saved Random Forest and XGBoost reload and match `metrics.json` exactly; the saved Logistic Regression file **cannot be loaded** with scikit-learn 1.4.2 here (it was written by a newer version) - it was refit in memory and matches `metrics.json` exactly. Loading the saved XGBoost file prints a serialisation-version warning.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | FPR | TN / FP / FN / TP | Train s |
|---|---|---|---|---|---|---|---|---|
| XGBoost (selected, 400 trees, depth 8, lr 0.08) | 0.9293 | 0.9353 | 0.9223 | 0.9288 | 0.9809 | 0.0638 | 3745 / 255 / 311 / 3689 | 2.7 |
| Random Forest (300 trees) | 0.9249 | 0.9269 | 0.9225 | 0.9247 | 0.9776 | 0.0727 | 3709 / 291 / 310 / 3690 | 12.2 |
| Logistic Regression (scaled, C=1) | 0.8281 | 0.8694 | 0.7722 | 0.8180 | 0.9218 | 0.1160 | 3536 / 464 / 911 / 3089 | 0.2 |

Model version 1, trained 2026-09-22T07:13:23+00:00, 47 features. Model files: RF 165,127,081 bytes; XGBoost 2,468,691; LR 2,849; best_model.joblib 2,469,577.

### 5-fold stratified cross-validation (all 40,000 URLs, mean +- std)
| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| XGBoost | 0.9259 +- 0.0019 | 0.9291 +- 0.0039 | 0.9221 +- 0.0028 | 0.9256 +- 0.0018 | 0.9792 +- 0.0010 |
| Random Forest | 0.9228 +- 0.0028 | 0.9228 +- 0.0051 | 0.9229 +- 0.0026 | 0.9228 +- 0.0026 | 0.9764 +- 0.0008 |
| Logistic Regression | 0.8264 +- 0.0035 | 0.8637 +- 0.0055 | 0.7751 +- 0.0046 | 0.8170 +- 0.0036 | 0.9190 +- 0.0031 |
XGBoost fold F1: 0.9238, 0.9268, 0.9231, 0.9278, 0.9263.

### Threshold sweep, XGBoost on the 8,000 test URLs
| Threshold | Precision | Recall | F1 | FPR | FP | FN |
|---|---|---|---|---|---|---|
| 0.20 | 0.8601 | 0.9698 | 0.9116 | 0.1578 | 631 | 121 |
| 0.30 | 0.8943 | 0.9523 | 0.9224 | 0.1125 | 450 | 191 |
| 0.35 | 0.9079 | 0.9443 | 0.9257 | 0.0958 | 383 | 223 |
| 0.40 | 0.9190 | 0.9385 | 0.9286 | 0.0828 | 331 | 246 |
| 0.50 | 0.9353 | 0.9223 | 0.9288 | 0.0638 | 255 | 311 |
| 0.60 | 0.9496 | 0.9000 | 0.9241 | 0.0478 | 191 | 400 |
| 0.70 | 0.9620 | 0.8738 | 0.9158 | 0.0345 | 138 | 505 |
| 0.80 | 0.9784 | 0.8283 | 0.8971 | 0.0182 | 73 | 687 |
| 0.90 | 0.9883 | 0.7575 | 0.8576 | 0.0090 | 36 | 970 |

### Deployed three-band verdict (reputation discount applied to 772 test URLs)
| True class | phishing | suspicious | safe |
|---|---|---|---|
| phishing (4,000) | 3,583 | 187 | 230 |
| legitimate (4,000) | 188 | 191 | 3,621 |
"phishing" only counted positive: precision 0.9501, recall 0.8958, F1 0.9221, accuracy 0.9244. "suspicious" counted positive: precision 0.9087, recall 0.9425, F1 0.9253, accuracy 0.9239.

### Feature ablation (XGBoost refit, threshold 0.5)
| Features | n | Accuracy | F1 | ROC-AUC |
|---|---|---|---|---|
| lexical only | 23 | 0.8928 | 0.8917 | 0.9605 |
| structural only | 9 | 0.6491 | 0.6601 | 0.7065 |
| domain only | 15 | 0.7871 | 0.7773 | 0.8834 |
| lexical + structural | 32 | 0.9035 | 0.9020 | 0.9672 |
| lexical + domain | 38 | 0.9246 | 0.9242 | 0.9787 |
| all 47 | 47 | 0.9283 | 0.9276 | 0.9811 |
| without is_popular_domain | 46 | 0.9270 | 0.9263 | 0.9804 |
| without is_common_tld | 46 | 0.9289 | 0.9284 | 0.9812 |
| without both | 45 | 0.9266 | 0.9259 | 0.9806 |
(Refit "all 47" differs from the saved model by 0.001 accuracy: XGBoost run-to-run variation.) Top XGBoost importances (saved model): is_common_tld 0.195, is_popular_domain 0.165, suspicious_word_count 0.121, brand_outside_domain 0.056, has_executable_extension 0.048, is_suspicious_tld 0.038, num_hyphens 0.025, subdomain_has_digit 0.025, domain_hyphen_count 0.021, has_at_symbol 0.020.

### Learning curve (XGBoost, fixed 8,000-URL test set; training rows permuted)
Training rows -> F1: 3,200 0.8946 · 6,400 0.9060 · 9,600 0.9118 · 12,800 0.9181 · 16,000 0.9206 · 19,200 0.9215 · 22,400 0.9239 · 25,600 0.9243 · 28,800 0.9290 · 32,000 0.9316 (accuracy 0.8948 -> 0.9321). The 32,000-row point differs from the saved model (0.9288) because of row order: roughly +-0.003 variation.

### Crowd-feedback experiment (retraining effect on unseen URLs)
k confirmed test URLs added x3 to training, scored on the remaining test URLs, mean of 3 seeds:
| k | held-out | F1 before | F1 after | missed phishing before | after |
|---|---|---|---|---|---|
| 250 | 7,750 | 0.9282 | 0.9276 | 305.0 | 305.3 |
| 500 | 7,500 | 0.9285 | 0.9281 | 295.0 | 297.0 |
| 1,000 | 7,000 | 0.9279 | 0.9272 | 277.3 | 277.7 |
| 2,000 | 6,000 | 0.9283 | 0.9290 | 238.0 | 235.3 |
**Finding:** adding random, correctly labelled in-distribution URLs does not measurably change F1 (changes within +-0.001, seed std 0.0002-0.0011). The benefit of the loop on this data is the immediate community override and the reversal of known mistakes, not a better average score; improvement on a *shifted* (new-campaign) distribution could not be measured with this static dataset.

### Latency (this PC; Flask test client = in-process, no network; final measurement run)
- feature extraction: 0.077 ms per URL (2,000 URLs); 4.0 s to featurise 40,000 URLs
- one URL, feature extraction + XGBoost predict_proba: 0.407 ms
- batch scoring of 8,000 feature rows: 0.0014 ms per URL (about 11 ms for the batch)
- `GET /api/check` (full pipeline incl. SQLite log write): mean 8.04 ms, median 7.88, p95 9.70, max 16.16 ms (300 requests)
- Timings vary between runs on this PC (earlier runs: mean 9.7 to 11.3 ms, p95 13.9 to 20.0 ms); all accuracy-type measurements were identical across runs. The extra test suite measured a mean of about 9 ms.
- base paper: about 0.20 ms per URL (different measurement, different model)

### Sample verdicts (live detector, empty community DB)
| URL | verdict | probability |
|---|---|---|
| http://secure-paypal-login.account-verify.tk/signin?user=a | phishing | 0.9989 |
| http://192.168.1.5/wp-admin/bank/update.php | phishing | 0.9999 |
| http://paypal.com.verify-login.tk/signin?user=a&pwd=b | phishing | 0.9999 |
| http://bit.ly/3xYz9Ab | phishing | 0.9999 |
| http://apple-id-locked.support-center.xyz/unlock/account.html | phishing | 0.9998 |
| http://netflix-billing-update.com/payment/verify | phishing | 0.9939 |
| http://free-prize-winner-lucky.top/claim.exe | phishing | 0.9994 |
| http://example-bank-secure.info/login.php?session=9f3a | phishing | 0.9083 |
| https://github.com/anthropics | safe | 0.0207 |
| https://www.wikipedia.org/wiki/Phishing | safe | 0.0008 |
| https://www.irctc.co.in/nget/train-search | safe | 0.0868 |
| https://stackoverflow.com/questions/11227809 | safe | 0.0020 |
| https://docs.python.org/3/library/urllib.html | phishing (**false positive**) | 0.6009 |
| https://www.amazon.in/gp/cart/view.html | phishing (**false positive**) | 0.7869 |
Cause of the two false positives (from code): `python` is not in the popular-domain list; `amazon.in` is popular but its TLD is two letters and not in the common list, so the reputation discount is not applied.

### Error analysis (XGBoost, threshold 0.5): 255 false positives, 311 false negatives
Most confident false positives: namewiki.info/firstname/Dorion (0.998), usaippon.us/racquetballfriendsplayerannc12006 (0.994), twitter.com/mikeruiz1 (0.990), abebooks.com/book-search/author/mavis-gallant/... (0.990), bouchercon.info/nominees.html (0.989). Most confident false negatives (look like ordinary blogs / file pages): travelhoneymoon.wordpress.com/2016/03/30/tips-to-how-to-feel-happy (0.002), formget.com/app/form/share/eP2Y-202367 (0.002), cece.pixub.com/antispam-protector/antispam-protector/ (0.006), veganvet.net/animal-issues-05-20-2014/ (0.007), panopticlick.eff.org/browser-uniqueness.pdf (0.011).

## 6. Live demonstration run (real app, scratch copy so shipped models are untouched)

`scripts/demo_scenario.py` + `scripts/capture_screenshots.py` against the running API (8103) and UI (5103).
- Before: zero-day lookalike `https://docs-share.cloudhost-files.com/drive/view?id=44` scored 0.0953 -> **safe**; after two community phishing reports -> **phishing, decided by community, 97.0 %** (raw model score still 9.5 %).
- `docs.python.org/3/library/urllib.html` (0.6009 phishing) and `www.amazon.in/gp/cart/view.html` (0.7869) corrected to **safe** by two safe reports each.
- 19 reports filed: 5 URLs confirmed phishing (2-3 reports each), 2 confirmed safe, 3 pending (one with disagreeing reports). 42 checks logged by the scenario.
- Feed sync from the Threat intelligence screen: OpenPhish +300 URLs, URLhaus +500 URLs (real public feeds, internet available) -> 810 URLs tracked, 805 confirmed phishing, 2 confirmed safe, 3 pending, 819 reports, 807 awaiting training.
- Retrain from the Models screen: model version 1 -> **2**. Base 40,000 + 807 community rows x3 (train 33,953 / **test 8,162** - a different test set from v1 because the crowd rows are split too). XGBoost v2: accuracy 0.9291, precision 0.9364, recall 0.9236, F1 0.9299, ROC-AUC 0.9816, FPR 0.0652, confusion 3740 / 261 / 318 / 3843; Random Forest v2 F1 0.9286 (acc 0.9272); Logistic Regression v2 F1 0.8198 (acc 0.8287). XGBoost training took 203.8 s in that run (3.6 s for RF) - it ran while a browser was polling and is not a clean timing. v1 -> v2 numbers are **not directly comparable** (different test sets, 807 phishing-heavy feed rows).
- Files: `docs/experiments/demo_scenario.json`, `demo_retrain_metrics_v2.json`, `demo_stats_after.json`.

## 7. Tests (all run 15 Oct 2026, 0 failures)

| Suite | Count | Result |
|---|---|---|
| `python tests.py` (shipped) | 3 test functions (features, threat intel, web app + API) | all passed |
| `python scripts/smoke_test.py` (shipped) | 20 checks over the API the React UI uses | all passed |
| `python scripts/extra_tests.py` (added in this run) | 72 checks: unit 23, integration 8, functional 14, validation 17, security 8, performance 2 | 72 / 72 passed |
Total: 95 automated checks. Security checks: SQL-injection text stored as data, tables survive; script tags in reported / checked URLs and reporter names are HTML-escaped on `/` and `/community`; CORS header `*` present; no cookies set; 100 kB note does not crash the server. Edge cases handled with HTTP 200/400: bare domain, no scheme, malformed port, unmatched bracket, 5,000-char URL, unicode host, percent-encoded traversal, `javascript:` and `data:` URLs.
Frontend: production build present (`frontend/dist`); no frontend unit tests exist; interaction walkthrough was done with Playwright captures only.
**Not done:** load / concurrency testing, authentication (the application has no login), user-acceptance testing, tests on live (non-dataset) URLs at scale, cross-browser testing (Chrome only).

## 8. Environment

| Item | Value |
|---|---|
| CPU | Intel Core i5-12500, 6 cores / 12 threads |
| RAM | 15.7 GB |
| GPU | Intel UHD Graphics 770 (not used) |
| OS | Windows 11 Pro 10.0.26200 |
| Python | 3.11.9 |
| scikit-learn 1.4.2 · xgboost 2.0.3 · Flask 3.1.0 · pandas 2.2.1 · numpy 1.26.4 · joblib 1.3.2 | |
| Node.js | v24.19.0; React 18.3, Vite 5.4, react-router 6.28, recharts 2.13, three 0.169, framer-motion 11.11 |
| Capture | Playwright 1.44 with installed Google Chrome, 1440 x 900 |
| requirements.txt | flask>=3.0, scikit-learn>=1.4, xgboost>=2.0, pandas>=2.0, numpy>=1.26, joblib>=1.3 |

## 9. Honest limitations (for the Limitations and Conclusion text)
1. 40,000-URL sample, one source; base paper used 235,804 URLs, different dataset, so 92.9 % vs 99.8 % is **not** a like-for-like comparison.
2. URL-only features; no page content, WHOIS, DNS or certificate data. Lexical features give most of the signal (lexical-only F1 0.892).
3. The dataset URLs are mostly scheme-less and the legitimate class looks like ordinary web pages: some features (is_common_tld, is_popular_domain) are dataset-shaped; removing both costs only 0.002 F1, so the model is not dependent on them alone, but results on live traffic were not measured.
4. Popular-domain reputation list is hand-written (145 names): ccTLD forms of big brands and uncommon legitimate sites are false-positive prone (docs.python.org, amazon.in).
5. Crowd verdicts are votes with a threshold of 2, no reporter identity, rate limit or reputation, and no administrator review (base paper requires verification): one actor can create two reports. Host-level override means one confirmed phishing URL marks every page on that host phishing.
6. No authentication on the API; CORS `*`.
7. Retraining averages are unchanged on in-distribution URLs; benefit on new campaigns not measured.
8. Saved `logistic_regression.joblib` is not loadable under the installed scikit-learn (version drift) - affects only reproducibility checks; the app loads only `best_model.joblib`.
9. Retraining a new model re-splits the data, so version-to-version metrics are not strictly comparable.
10. Feed URLs (URLhaus, OpenPhish) are accepted as phishing without verification; URLhaus lists malware-distribution URLs, not only phishing.

## 10. Screenshot inventory (`docs/screenshots/`, 1440 x 900 unless full page)
01_landing · 02_check_home · 03_check_phishing · 03b_check_phishing_full (full page) · 04_check_safe · 05_check_community_override · 06_check_false_positive_corrected · 07_batch_results (full) · 08_report_form · 09_intel · 10_intel_detail · 11_models · 12_models_full (full) · 13_activity · 14_activity_full (full) · 15_intel_sync_dialog · 16_intel_sync_result · 17_intel_after_sync · 18_retrain_confirm · 19_retrain_running · 20_models_after_retrain · 21_models_after_retrain_full (full) · 22_intel_after_retrain · 23_check_dark. 24 files, all real captures with data loaded.

## 11. Diagrams and charts
Diagrams in `docs/diagrams/` (01-10, generated by `scripts/make_diagrams.py`); charts in `docs/charts/` (generated by `scripts/make_result_charts.py` from `docs/experiments/measured.json` and `models/metrics.json`); IEEE figures in `docs/paper/`.
