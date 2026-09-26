# PhishGuard

**A Dynamic Phishing URL Detection System Integrating Advanced Machine Learning and Crowdsourced Threat Intelligence**

Batch A3 · CSE (Data Science), Section A · Base paper: IEEE Access 2026, DOI 10.1109/access.2026.3700833

A pure-Python, end-to-end implementation of the three-stage design adopted from the base paper:

```
  URL ──► 1. Feature extraction ──► 2. ML classification ──► verdict
                                          ▲                      │
                                          │ retrain              ▼ report
                                    3. Crowdsourced threat intelligence
```

## Quick start

```bash
pip install -r requirements.txt
python run.py train          # trains & compares Random Forest, XGBoost, Logistic Regression (~30 s)
python run.py serve          # web interface at http://127.0.0.1:5000
```

Other commands:

```bash
python run.py check http://paypal-login.verify-account.tk/signin   # classify from the terminal
python run.py report <url> phishing --reporter alice               # submit a community report
python run.py retrain                                              # refine the model with confirmed reports
python run.py sync                                                 # pull OpenPhish / URLhaus feeds (needs internet)
python run.py download                                             # fetch the full 420k-URL dataset
python tests.py                                                    # run the smoke tests
```

## How each project objective is implemented

| Objective | Where |
|---|---|
| 1. Collect & preprocess a URL dataset | `data/urls_sample.csv` (40,000 balanced URLs sampled from a public 420k-row labelled dataset) · `phishguard/data.py` |
| 2. Lexical, structural, domain-based features | `phishguard/features.py` — 47 offline features in three groups, plus human-readable red flags |
| 3. Train & compare RF / XGBoost / LR | `phishguard/train.py` — same split, same features; accuracy, precision, recall, F1, ROC-AUC, confusion matrix; best F1 model is saved as `models/best_model.joblib` |
| 4. Crowdsourced threat intelligence | `phishguard/threat_intel.py` — SQLite store of reports; a URL is *confirmed* when net votes reach `CONSENSUS_THRESHOLD` (2) or it comes from a trusted feed; confirmed entries override the model instantly |
| 5. Continuous refinement | `phishguard/retrain.py` — merges base data with confirmed community URLs (weight ×3), retrains all models, bumps the model version and hot-reloads without restarting; auto-triggers after `AUTO_RETRAIN_EVERY` (25) new confirmations |
| 6. Real-time web interface | `phishguard/webapp.py` — Flask pages **Check URL / Report / Threat intelligence / Models** plus a JSON API |

## Results (held-out 20 % test set, 8,000 URLs)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| XGBoost (selected) | 92.9 % | 93.5 % | 92.2 % | 92.9 % | 0.981 |
| Random Forest | 92.5 % | 92.7 % | 92.3 % | 92.5 % | 0.978 |
| Logistic Regression | 82.8 % | 86.9 % | 77.2 % | 81.8 % | 0.922 |

The numbers are regenerated in `models/metrics.json` every time you train and shown on the **Models** page.

## Decision logic at check time (`phishguard/detector.py`)

1. Community/feed **confirmed phishing** → verdict *phishing* (zero-day coverage, no model needed).
2. Community **confirmed safe** → verdict *safe* (fixes false positives, problem statement point 4).
3. Otherwise the best model scores the URL; well-known registered domains get a reputation discount; pending (unconfirmed) reports nudge the score ±0.15 per net vote.
4. Probability ≥ 0.60 → **phishing**, ≥ 0.35 → **suspicious**, else **safe**.

## JSON API

```
GET  /api/check?url=<url>          → verdict, probability, red flags, features, community status
POST /api/report  {"url","verdict":"phishing|safe","reporter","note"}
GET  /api/stats                    → threat-intel counters + current model metrics
POST /api/retrain                  → retrain now (blocking) and return the new metrics
POST /api/sync                     → pull public feeds into the threat-intel store
```

## Project layout

```
run.py                     CLI entry point (train / check / report / sync / retrain / serve / download)
tests.py                   smoke tests
requirements.txt
phishguard/
  config.py                paths & thresholds
  features.py              stage 1 – feature extraction
  data.py                  dataset loading / preprocessing
  train.py                 stage 2 – train & compare the three classifiers
  threat_intel.py          stage 3 – crowdsourced reports, consensus, feed sync (SQLite)
  detector.py              real-time decision pipeline
  retrain.py               continuous refinement loop
  webapp.py                Flask web interface + API (templates are Python strings)
data/urls_sample.csv       training data (url,label; 1 = phishing)
data/threat_intel.db       created automatically on first report
models/                    trained models + metrics.json
```

## Notes

* Everything runs offline; `sync` and `download` are the only commands that need internet.
* Features are intentionally offline (no WHOIS/DNS) so training and real-time checking use identical code. A small built-in list of popular domains stands in for a Tranco-style reputation list.
* Thresholds, the auto-retrain trigger and feed URLs are all in `phishguard/config.py`.
