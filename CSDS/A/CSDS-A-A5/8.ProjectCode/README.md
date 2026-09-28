# TaxSentinel

Self-supervised detection and plain-language explanation of GST input-tax-credit fraud: fake invoices,
circular trading, shell entities and abnormal ITC spikes.

TaxSentinel learns normal GST behaviour with a JEPA encoder, combines invoice, return-behaviour and
buyer-seller network evidence into one risk score per taxpayer and per invoice chain, draws fraud rings
as an interactive graph, and has Gemini write an investigator-style case note that cites every fact.

## Features
- **GST ecosystem generator**: seeded taxpayers, invoices and GSTR-1/2B/3B returns with injected fraud and labels (`scripts/generate_gst_data.py`).
- **Three feature layers**: invoice-level, taxpayer-behaviour and network features per taxpayer-month.
- **JEPA behaviour encoder**: a small PyTorch model, trained on CPU in ~15 s, whose embedding-prediction error is the anomaly score.
- **Fraud-ring detection**: circular-trading loops and shared-identity shell clusters (NetworkX), explored in an interactive graph.
- **Risk ranking**: ranked taxpayers and invoice chains, with drill-down to evidence, invoices, partners and monthly returns.
- **Written explanations**: Gemini case notes with `[E#]` citations and automatic grounding checks.
- **Evaluation**: precision@k, recall and F1 against injected labels, vs a rule-based baseline, plus ablations.

## Quick start (Windows)
```bat
setup.bat      :: venv + packages + .env + frontend packages (once)
:: put GEMINI_API_KEY=... in .env  (https://aistudio.google.com/apikey)
run.bat        :: starts API :8105 and web :5105, opens the browser
```
**Demo login:** `demo@taxsentinel.app` / `Demo@1234`

Details are in [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Evaluation results
Bundled ecosystem: seed 42, 600 taxpayers, 64,474 invoices, 79 injected-fraud taxpayers. Produced by
`python -m ml.eval` → [`experiments/eval/metrics.json`](experiments/eval/metrics.json).

**Taxpayer ranking and flags**

| Method | P@10 | P@25 | P@50 | P@79 | R@79 | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|
| **TaxSentinel** | 1.00 | 1.00 | 1.00 | **0.949** | **0.949** | **0.962** | 0.949 | **0.955** | **0.997** |
| Rule baseline (R1-R5) | 1.00 | 0.88 | 0.84 | 0.620 | 0.620 | 0.288 | 0.861 | 0.432 | 0.876 |
| JEPA only | 0.80 | 0.84 | 0.58 | 0.481 | 0.481 | 0.842 | 0.203 | 0.327 | 0.843 |
| Graph + invoice only | 1.00 | 1.00 | 1.00 | 0.848 | 0.848 | 1.000 | 0.797 | 0.887 | 0.940 |

The model flags 78 taxpayers (75 correct, 3 false alarms). The rule baseline flags 236, of which 168 are false alarms.

**Recall by pattern (at threshold)**

| Pattern | Count | TaxSentinel | Rule baseline |
|---|---|---|---|
| Circular trading | 21 | **1.00** | 0.86 |
| Shell entities | 27 | 1.00 | 1.00 |
| Fake-invoice buyers | 19 | **0.89** | 0.58 |
| ITC spikes | 12 | 0.83 | **1.00** |

**Invoices, rings, chains, transfer**
- Anomalous-invoice flags: precision 0.88, recall 0.97, F1 **0.92** (vs 0.16 for the "not in supplier's GSTR-1" check); ROC-AUC 0.9997.
- Circular-trading rings recovered: **5 / 5**. Top-10 invoice chains that are fraud: **100%**.
- PaySim transfer check (100k transactions, unlabelled training): JEPA ROC-AUC **0.935** vs 0.790 for ranking by amount; precision@100 0.31 vs 0.02.
- Explanation quality (citations, invalid citations, evidence coverage, numeric grounding) is measured by `python -m ml.eval` once `GEMINI_API_KEY` is set, and appears on the Model performance page.

The data is synthetic sample data. See the limits in [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md#9-limits).

## Tech stack
React + Vite + Tailwind, react-router, axios, lucide-react, react-force-graph · FastAPI, SQLAlchemy 2 + SQLite,
PyJWT + bcrypt · PyTorch (CPU), NetworkX, NumPy · Google Gemini (`google-genai`) · kagglehub.

## Project layout
```
backend/app/     main.py, db.py, auth.py, config.py, routes/, services/ (pipeline state, Gemini explainer)
frontend/src/    pages/, components/, api.js
ml/              features, JEPA, graph analysis, baseline, pipeline, train.py, eval.py
scripts/         generate_gst_data.py, download_data.py, smoke_test.py
data/            generated/ (GST ecosystem), sample/ (PaySim 100k), app.db + workspace/ (runtime, ignored)
models/          jepa.pt
experiments/     metrics.json (training), eval/metrics.json (evaluation)
docs/            overview, how it works, how to run
```

## Documentation
| Document | Contents |
|---|---|
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | Problem, users, capabilities, screens |
| [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) | Data and licences, features, JEPA, graph analysis, risk, explanations, evaluation, API |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Setup, start, demo walkthrough, command line, troubleshooting |
| [docs/PLAN.md](docs/PLAN.md) | Build plan |
