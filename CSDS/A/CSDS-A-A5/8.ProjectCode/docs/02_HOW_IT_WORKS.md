# TaxSentinel - How it works

```
generator ──> invoices, returns, taxpayers (CSV)
                   │
                   ▼
   feature layers (invoice | behaviour | network) per taxpayer-month
                   │
       ┌───────────┼──────────────────────────┐
       ▼           ▼                          ▼
 JEPA encoder   NetworkX: loops,          invoice anomaly
 (deviation)    shell clusters, exposure  signals
       └───────────┼──────────────────────────┘
                   ▼
   noisy-OR risk per taxpayer  +  invoice-chain scores
                   ▼
   evidence list E1..En ──> Gemini case note (cites E#)
                   ▼
   evaluation vs injected labels and a rule baseline
```

## 1. Data

### Synthetic GST ecosystem (`scripts/generate_gst_data.py`)
A seeded generator (default seed 42, 600 taxpayers, Apr 2025 - Mar 2026):
- **Taxpayers**: GSTIN-format IDs with a valid checksum, legal name, constitution, state, sector (raw material → manufacturer → wholesaler → retailer, plus services), registration date, address and masked contact.
- **Invoices**: B2B supplies along a tiered supply network, with value, rate, tax, e-way-bill flag and whether the seller reported the invoice in GSTR-1.
- **Monthly returns**: outward turnover, output tax, ITC available (GSTR-2B), ITC claimed (GSTR-3B), cash paid (with a credit carry-forward ledger) and filing delay.
- **Injected fraud with labels**: shell clusters with layered fake invoices, beneficiaries claiming ITC on them, circular-trading rings, and ITC spikes.
- **Legitimate hard negatives**: festival seasonality, one-off capital purchases, new registrations, group companies sharing an address, late filers, prior-period credit catch-ups, and naturally reciprocal services/manufacturer trade.

The committed dataset in `data/generated/` has 600 taxpayers, 64,474 invoices, 6,977 returns and 79 fraud taxpayers (27 shell, 21 circular, 19 fake-invoice buyers, 12 ITC spikes). *Generate & analyse* in the app writes new ecosystems to `data/workspace/` (not committed).

### Data sources and licences
| Source | Licence | What is committed |
|---|---|---|
| Synthetic GST ecosystem, produced by `scripts/generate_gst_data.py` (seeded) | Part of this product | Full dataset in `data/generated/` (~7 MB) |
| [PaySim - Synthetic Financial Datasets for Fraud Detection](https://www.kaggle.com/datasets/ealaxi/paysim1) (Kaggle) | CC BY-SA 4.0 | 100,000-row seeded random sample in `data/sample/paysim_sample.csv` (134 fraud rows). The full 470 MB file goes to `data/raw/` (git-ignored) via `scripts/download_data.py` (kagglehub) |

PaySim is used as an out-of-domain check: the same JEPA module is trained, unlabelled, on PaySim transactions (see Evaluation).

## 2. Feature layers (`ml/features.py`)
Each active taxpayer-month gets a 19-feature vector in three groups:

| Layer | Features |
|---|---|
| Invoice | purchase and sales invoice counts, share of purchase value not reported by suppliers, goods invoices ≥ ₹50k without an e-way bill, round-value share, share bought from suppliers under 6 months old |
| Behaviour | outward turnover, ITC claimed, ITC / output tax, ITC claimed above GSTR-2B, share of output tax paid in cash, filing delay, registration age |
| Network | number of suppliers and buyers, share of new trading partners, sales to parties that also supply it (reciprocity), largest buyer's share, value added |

Features are robust-scaled (median / IQR) and clipped.

## 3. JEPA behaviour encoder (`ml/jepa.py`)
A Joint-Embedding Predictive Architecture predicts **embeddings**, not raw values:
- **Context**: the previous 3 months (online encoder), plus the current month with one block hidden.
- **Target**: the embedding of the full current month from an EMA copy of the encoder (no gradient).
- **Mask variants**: hide the whole month (it must be predicted from history), or hide the invoice, behaviour or network block (it must be predicted from the other layers).
- **Loss**: MSE between predicted and target embeddings, plus a variance term that prevents collapse.
- **Size**: ~53k parameters (including the EMA target copy), 100 epochs, about 15 seconds on CPU (`python -m ml.train`).

Anomaly scoring: each variant's error is divided by the median error of that month. A taxpayer-month's deviation is the geometric mean across variants. The taxpayer score averages the top-2 months, robust-z-scored against all taxpayers and squashed to 0-1. The error of the behaviour-block variant alone gives a second score, which catches one-month ITC spikes.

## 4. Network analysis (`ml/graph.py`)
- **Trade graph**: a directed seller → buyer graph with aggregated value, tax, invoice count and months.
- **Circular trading**: `networkx.simple_cycles` (length ≤ 5) over recurring, above-median edges. Each cycle is scored as √balance × recurrence × √concentration: balance means values stay similar around the loop; recurrence means the whole loop trades in the same months; concentration means the loop is a large share of **every** member's purchases. Overlapping suspicious cycles merge into rings.
- **Shared-identity clusters**: registrations linked by the same address or contact number. The cluster score combines members' mean JEPA deviation, share registered within a year, share trading with each other, and share that stopped filing.
- **Exposure**: the share of a taxpayer's monthly purchases bought from suspicious clusters.
- **Communities**: Louvain communities on the value-weighted graph.

## 5. Invoice layer and risk
Each invoice gets a noisy-OR score from weighted signals: not reported by the supplier, no e-way bill, round value, young supplier, supplier in a suspicious cluster, supplier later stopped filing, edge of a detected loop, value far above the supplier's norm. Invoices scoring ≥ 0.5 count as anomalous. A taxpayer's invoice score is the peak monthly share of anomalous value.

**Taxpayer risk** = 1 − (1 − 0.75·JEPA)(1 − 0.6·behaviour)(1 − 0.7·network)(1 − 0.6·invoice). A taxpayer is flagged at risk ≥ 0.5. Noisy-OR means one strong layer is enough to raise risk, and agreeing layers raise it further.

**Invoice chains**: each detected loop and each suspicious shell cluster (with its buyers) becomes a chain, scored from the ring or cluster score plus the risk of its members or the anomalous share of its invoices.

**Patterns** (circular trading, shell entity, fake invoices, ITC spike, unusual behaviour) are named from the evidence, so the analyst sees *what kind* of fraud is suspected.

## 6. Evidence and written explanations
The pipeline builds an evidence list per taxpayer (E1..En), each item with a layer, severity and concrete numbers. Examples: JEPA deviation with the largest feature shifts, months where the GSTR-3B claim exceeds GSTR-2B, ITC spikes, low cash payment against the sector median, anomalous purchase and sales invoices, ring membership with the loop path, shared-identity cluster, exposure to shell suppliers, stopped filing.

`backend/app/services/explainer.py` sends the profile, scores and evidence to Gemini (`GEMINI_MODEL`, with fallbacks) under a system prompt that allows only evidence facts, requires an `[E#]` citation per claim, and fixes three sections (Summary / Why it was flagged / Suggested next steps). Each note is checked automatically: citation count, invalid citations, evidence coverage, high-severity coverage, and the share of numbers that appear in the evidence. Notes are stored per ecosystem in SQLite.

## 7. Evaluation (`ml/eval.py` → `experiments/eval/metrics.json`)
- **Taxpayer level**: precision@k and recall@k (k = 10, 25, 50 and the number of fraud taxpayers), precision/recall/F1 at the flag threshold, ROC-AUC and average precision, for the model, the rule baseline and three ablations.
- **Rule baseline**: R1 GSTR-3B ITC > GSTR-2B by 20% and ₹50k; R2 under 6 months old with monthly turnover > ₹50 L; R3 < 1% cash on > ₹1 L output tax for 3+ months; R4 ITC up more than 3× month over month; R5 stopped filing. Ranked by rules hit.
- **Per pattern**: recall of each injected pattern.
- **Invoices**: precision/recall/F1 of anomalous-invoice flags vs the classic "not in supplier's GSTR-1" check.
- **Rings and chains**: injected rings recovered (≥ 80% of members in one detected ring), and the fraud share of the top-10 chains.
- **PaySim transfer**: JEPA (no history window, 3 blocks) trained unlabelled on the 100k sample, scored by ROC-AUC and precision@k vs an amount-only ranking.
- **Explanation quality** (needs `GEMINI_API_KEY`): the automatic checks above, averaged over the top-10 flagged cases.

## 8. Application
- **Backend**: FastAPI + SQLAlchemy/SQLite (`users`, `pipeline_runs`, `explanations`), bcrypt + JWT. The pipeline result is kept in memory and pickled to `data/workspace/state.pkl`. New generations run in a background thread with progress polling.
- **Frontend**: React + Vite + Tailwind, react-force-graph for the network, axios; `/api` is proxied to the backend.

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/register`, `/login`, `GET /api/auth/me` | accounts |
| `POST /api/pipeline/run`, `GET /api/pipeline/status`, `/runs` | generate and analyse an ecosystem |
| `GET /api/overview` | dashboard |
| `GET /api/taxpayers`, `/api/taxpayers/{gstin}` | ranking, profile and evidence |
| `GET /api/chains`, `/api/chains/{id}` | invoice chains |
| `GET /api/structures`, `/api/graph?focus=|ring=|cluster=|chain=` | rings, clusters and graph data |
| `POST /api/explanations/{gstin}` | Gemini case note |
| `GET /api/metrics`, `/api/health` | evaluation and status |

## 9. Limits
- The data is synthetic. Thresholds and weights were set on this generator and would need recalibration on real returns.
- Shell entities look self-consistent to the JEPA encoder (27 similar firms form their own "normal"). The network layer is what catches them.
- The case notes are a risk indication for review, not a legal finding.
