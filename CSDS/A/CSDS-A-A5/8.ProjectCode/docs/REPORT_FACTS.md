# TaxSentinel - Report Facts (single source of truth for the documentation set)

Every number in the batch documents (decks, chapter files, final report, IEEE paper) must agree with this file.
Sources: `experiments/metrics.json`, `experiments/eval/metrics.json`, `data/generated/meta.json`, `scripts/smoke_test.py`
output, live API timing on this machine, and the code itself.

## 1. Identity
- Project: **JEPA-LLM Tuning Framework for Combating GST and Sales Tax Input Tax Credit Fraud Pattern Detection**
- Product: **TaxSentinel** - backend FastAPI on port 8105, frontend React/Vite on port 5105
- Batch A5, CSE (Data Science), Section A. Guide: Dr. N. Ch. Ravi (Professor in CSE (D.S)).
- Students: B.ASHRITHA 23K91A6732 - B.DIVYA 23K91A6739 - A.KISHORE 23K91A6716 - A.YAGNESH 23K91A6711.
- College (from the Phase-I abstract form in `Documentary/`): TKR College of Engineering and Technology, Autonomous;
  Major Project Phase-I, A.Y. 2026-27, IV year I sem. City, principal, HOD names: **not in the batch files - placeholders**.
- Base paper (per `3.BASE PAPER.docx`): Datta, Thakkar, Dabhade, "Combating GST Input Tax Credit Fraud in India: Forensic Accounting,
  Data Analytics, and Legal Enforcement Strategies", Int. J. Management, Public Policy and Research, vol. 5 issue 1, Jan-Mar 2026,
  doi 10.55829/ykz3ea41. A qualitative, government-data paper: no model, no accuracy figures.
  Supporting references in `archived_base_papers/`: Xu et al., TED, arXiv:2605.26984 (2026; supervised heterogeneous-graph GNN, F1 76.35-94.96 %
  on two real tax datasets, varies with positive-sample ratio); Mehta et al., arXiv:2208.07660 (2022; node2vec + DBSCAN circular-trading
  communities on Telangana data, 77,837,538 invoices, 388,448 taxpayers, no accuracy metric).
- Base-paper statistics worth quoting (DGGI, from the paper): FY22-23 detected evasion 1.01 lakh crore, 4,872 cases, 97 arrests;
  FY23-24 2.01 lakh crore, 6,084 cases, 140 arrests; voluntary payments 20,713 -> 26,605 crore; fake-registration drives:
  21,791 fake GSTINs / 24,010 crore (May-Jul 2023), ~10,700 / 10,179 crore (Aug-Oct 2024, partial).

## 2. Honest framing (must be stated in every document)
- The data is **synthetic**: produced by a seeded generator with injected, labelled fraud. All accuracy figures are against those injected labels.
  Real GST returns were not available. Thresholds and weights were set on this generator and would need recalibration on real returns.
- The base paper has no model, so there is **no like-for-like accuracy comparison**. Comparison is (a) qualitative against the base paper's
  recommendations, (b) quantitative against a rule baseline built from standard scrutiny rules, and (c) context only against TED
  (different data, supervised, real).
- "Tuned LLM": the project **does not fine-tune** an LLM. Gemini is used through a constrained prompt (system prompt, evidence-only facts,
  `[E#]` citations, fixed three-section output) and each note is checked automatically. State this plainly.
- JEPA is used for **behaviour representation and deviation scoring**, not for generating text.
- Shell entities look self-consistent to the JEPA encoder (27 similar firms form their own "normal"); JEPA-only recall is 0.203. The
  network layer catches them. This is a stated finding, not a hidden one.
- Explanation quality was measured on 6 of the top-10 flagged cases only (Gemini free-tier quota ran out for the other 4).
- No pytest/unit-test suite exists. Testing = `scripts/smoke_test.py` (20 end-to-end API checks, all passed) + the evaluation harness
  `python -m ml.eval`. The report must say so and not claim unit-test counts.

## 3. Dataset facts
**Synthetic GST ecosystem** (`scripts/generate_gst_data.py`, seed 42, Apr 2025 - Mar 2026, 12 months)
| Item | Value |
|---|---|
| Taxpayers | 600 (GSTIN-format ids with valid checksum; sectors raw material -> manufacturer -> wholesaler -> retailer, plus services) |
| Invoices | 64,474 B2B invoices (530 injected-fraud invoices) |
| Monthly returns | 6,977 taxpayer-month rows (GSTR-1/2B/3B figures, cash ledger, filing delay) |
| Fraud taxpayers | 79 = 27 shell entity + 21 circular trading + 19 fake-invoice buyers + 12 ITC spikes |
| Shell clusters injected | SC-01 5 members, SC-02 4 members, ... (see meta.json) |
| Circular rings injected | 5 |
| Hard negatives | festival seasonality, one-off capital purchases, new registrations, group companies sharing an address, late filers, prior-period credit catch-ups, naturally reciprocal trade |
| Size on disk | about 7 MB in `data/generated/` |
| Licence | part of this product |

**PaySim** (out-of-domain check): Kaggle `ealaxi/paysim1`, CC BY-SA 4.0, 100,000-row seeded random sample, 134 fraud rows; full 470 MB file git-ignored.

**Split**: the JEPA is trained **unsupervised** on all 6,977 taxpayer-months (no labels, no train/test split); labels are used only to
score. This is stated as a limitation (no held-out ecosystem for the headline numbers) - mitigated by the app regenerating other
seeds (smoke test: seed 7, 200 taxpayers gives 28 flagged) but no labelled metrics were recorded for those.

## 4. Model and training facts
- 19 features per taxpayer-month in 3 layers: invoice (6) purchase_invoices, sales_invoices, unmatched_share, no_eway_share, round_share,
  young_supplier_share; behaviour (7) outward_log, itc_claimed_log, itc_to_output, itc_mismatch, cash_ratio, filing_delay, age_log;
  network (6) suppliers, buyers, new_partner_share, reciprocal_share, top_buyer_share, value_add.
- Robust scaling (median / IQR, clip +-10). Context window = 3 previous months.
- JEPA: online encoder (Linear 19->64, LayerNorm, GELU, Linear 64->64, GELU, Linear 64->32), EMA target copy (momentum 0.99, no gradient),
  predictor MLP (input 3x(32+1)+32+4 -> 128 -> 128 -> 32). 4 mask variants (whole month hidden; invoice / behaviour / network block hidden).
  Loss = MSE(pred, target embedding) + variance term (hinge on embedding std, weight 1.0). AdamW lr 1e-3, wd 1e-4, batch 256, 100 epochs.
- **53,420 values in the saved state** (online encoder 7,648 + EMA target 7,648 + predictor 38,048 + 76-value mask buffer; trainable 45,696). Training on CPU: **11.7 s** (recorded run), final loss **0.1115**; loss peaks at 0.261 in epoch 11
  then falls and settles at 0.11-0.12 from about epoch 60. torch 2.14.0+cpu, python 3.11.9.
- Anomaly score: per-variant error / monthly median error; geometric mean over variants; taxpayer score = mean of top-2 months, robust-z, sigmoid.
  Behaviour-block variant gives a second score.
- Network: DiGraph seller->buyer; `simple_cycles` length <= 5 on recurring (>=2 months), above-median edges; cycle score =
  sqrt(balance) x recurrence x sqrt(concentration); overlapping cycles merge into rings (min score 0.25). Identity clusters from shared
  address / contact (connected components); cluster score = 0.4 mean JEPA + 0.2 young share + 0.2 intra-trade share + 0.2 vanished share,
  suspicious >= 0.4. Louvain communities.
- Invoice noisy-OR flags (weight): unreported 0.30, no_eway 0.30, round_value 0.15, young_supplier 0.20, shell_cluster 0.35, supplier_vanished 0.20,
  ring_edge 0.45, value_spike 0.15; anomalous at >= 0.5.
- Risk = 1 - (1-0.75 JEPA)(1-0.6 behaviour)(1-0.7 network)(1-0.6 invoice); flagged at >= 0.5.
- Rule baseline R1-R5 (3B>2B by 20% and Rs 50k; <6 months & turnover > Rs 50 L; <1% cash on > Rs 1 L tax for 3+ months; ITC > 3x month on month;
  stopped filing).
- Explanations: Gemini (`GEMINI_MODEL`, fallbacks `gemini-3.5-flash-lite`, `gemini-flash-latest`), temperature 0.2, max 2048 tokens,
  < 320 words, 3 sections. Automatic checks: citations, invalid citations, evidence coverage, high-severity coverage, numeric grounding.

## 5. Results (bundled ecosystem, seed 42; `experiments/eval/metrics.json`)
**Taxpayer level (600 taxpayers, 79 fraud)**
| Method | P@10 | P@25 | P@50 | P@79 | R@79 | Precision | Recall | F1 | ROC-AUC | AP | Flagged (TP/FP/FN) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TaxSentinel (all layers) | 1.00 | 1.00 | 1.00 | 0.9494 | 0.9494 | 0.9615 | 0.9494 | 0.9554 | 0.9974 | 0.9860 | 78 (75/3/4) |
| Rule baseline R1-R5 | 1.00 | 0.88 | 0.84 | 0.6203 | 0.6203 | 0.2881 | 0.8608 | 0.4317 | 0.8762 | 0.7008 | 236 (68/168/11) |
| JEPA only (+behaviour) | 0.80 | 0.84 | 0.58 | 0.4810 | 0.4810 | 0.8421 | 0.2025 | 0.3265 | 0.8427 | 0.5305 | 19 (16/3/63) |
| Graph + invoice only | 1.00 | 1.00 | 1.00 | 0.8481 | 0.8481 | 1.0000 | 0.7975 | 0.8873 | 0.9403 | 0.9033 | 63 (63/0/16) |
| Without invoice layer | 1.00 | 1.00 | 0.98 | 0.9494 | 0.9494 | - | - | - | 0.9960 | 0.9771 | - |

**Recall by pattern (at flag threshold)**: circular trading 21 -> model 1.00 / baseline 0.857; shell entity 27 -> 1.00 / 1.00; fake-invoice buyers 19 -> 0.895 / 0.579;
ITC spikes 12 -> 0.833 / 1.00. Pattern correctly named for flagged members: 1.00 in all four.

**Invoice level (64,474 invoices, 530 fraud)**: model flags 581 -> precision 0.883, recall 0.9679, F1 0.9235 (tp 513, fp 68, fn 17), ROC-AUC 0.9997,
AP 0.969, P@100 1.00, P@500 0.936, P@530 0.9302. Baseline "not reported by supplier in GSTR-1" flags 1,071 -> precision 0.1195, recall 0.2415, F1 0.1599.

**Rings and chains**: injected rings 5, recovered 5 (>= 80 % of members in one detected ring); 9 rings detected (7 with fraud members, 2 without);
16 invoice chains, precision@top-10 = 1.00. Suspicious identity clusters 7 (12 clusters total). Cycles scanned 79.

**PaySim transfer** (100k rows, 134 fraud, 15 epochs, 6.2 s, unlabelled): ROC-AUC 0.9354 vs 0.7897 amount-only; AP 0.0895 vs 0.0128;
P@100 0.31 vs 0.02; P@500 0.082 vs 0.026; P@134 0.2612 vs 0.0373; R@500 0.306.

**Explanation quality** (Gemini, top-10 flagged cases, 6 completed): 0 invalid citations, ~10.8 citations per note, 100 % evidence coverage and 100 % high-severity coverage,
84 % numeric grounding, all three sections present, suspected pattern named in 100 %. 4 failed (503 / 429 / 504 errors).

**Pipeline output on the seed-42 ecosystem** (live API): 78 flagged taxpayers, 9 rings, 7 suspicious clusters, 16 chains, 581 anomalous invoices,
ITC claimed Rs 187.59 Cr (1,875,947,115), ITC at risk (flagged) Rs 25.62 Cr (256,151,048); flagged-pattern counts: circular trading 24, fake invoices 17,
ITC spike 17, behaviour anomaly 2, shell entity 27. Top taxpayer: Lotus Manufacturing Pvt Ltd, risk 0.9651, in ring R01 (5 parties, Rs 44.65 Cr,
9 common months, balance 0.87; chain CH-R01 98 invoices, ITC passed Rs 9.78 Cr, score 0.8334).

## 6. Performance and testing (measured 15 Oct 2026 on this machine)
- Machine: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Intel UHD 770 (no discrete GPU; training on CPU), Windows 11 Pro,
  Node v24.19.0, Python 3.11.9, torch 2.14.0+cpu, FastAPI 0.115.6, SQLAlchemy 2.0.36, NetworkX 3.4.2, NumPy 2.4.6; frontend React 18.3, Vite 6, Tailwind 4,
  recharts 3, react-force-graph-2d, framer-motion, three.
- Full generate + features + JEPA training + analysis for 600 taxpayers: **16.0 s** analysis (pipeline `seconds`), **18.6-29.0 s** end-to-end per 600-taxpayer run in the run history (generation included; the five latest runs 19.4, 27.8, 29.0, 24.5, 23.6 s;
  three early development runs took 20.2, 52.6-54.9 and 274.5 s while other work was loading the machine) and 5.8-9.9 s for 200 taxpayers. JEPA training alone 11.7 s.
- API latency, 20 calls each, median / max ms: health 1.7/3.5; overview 4.6/13.2; taxpayers (50) 8.4/12.5; taxpayer profile 8.5/20.2; chains 5.2/6.8;
  structures 5.3/6.8; graph (overview) 12.1/13.9; graph (ring) 4.3/5.0; metrics 6.9/11.4; monthly 3.5/36.6; login (bcrypt) ~261 ms (single call).
- Edge and security checks (`scripts/docs_build/edge_tests.py` -> `experiments/edge_tests.json`): **41 / 41 passed** (authentication, authorisation incl. altered-signature JWT and 401 on every protected route without a token, validation 422/409/404 cases, SQL-injection-style and script-tag search text inert, one-run-at-a-time 409, small run seed 5 / 150 taxpayers completes, bundled ecosystem restored with 78 flagged).
- `scripts/smoke_test.py`: **20 / 20 checks PASSED**, total 39.4 s, including two full regenerations (seed 7 / 200 taxpayers; seed 42 / 600), registration, login, 401 on
  protected route, ranking order, profile + 12-month series, graph with loop, rings and clusters, chain drill-down, a Gemini explanation (model gemini-3.5-flash-lite,
  14 citations, coverage 1.0), saved explanation, and metrics.
- Run history (database): the 12 most recent runs all finished with status `done`.

## 7. Architecture summary
Browser (React SPA, axios, JWT in storage) -> FastAPI (`backend/app/main.py`, routers auth, pipeline, investigate, explanations, series; CORS limited to the
frontend origin) -> in-memory pipeline state (`services/state.py`, pickled to `data/workspace/state.pkl`) produced by `ml/pipeline.py`
(features -> JEPA -> graph -> invoice scoring -> risk -> evidence -> chains -> evaluation) and SQLite (`users`, `pipeline_runs`, `explanations`) via SQLAlchemy;
Gemini via `services/explainer.py`. New generations run in a background thread with progress polling (`/api/pipeline/status`).
Security: bcrypt password hashing, HS256 JWT (720 min expiry), bearer guard on every route except register/login/health, input validation with pydantic
(seed 0-10,000,000; taxpayers 150-1500; password >= 8 chars; email pattern), one run at a time (409), 503 while loading, 502 on Gemini failure, 404 unknown GSTIN.

### Endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | /api/auth/register, /api/auth/login | create account / sign in (returns JWT) |
| GET | /api/auth/me | current user |
| POST | /api/pipeline/run | start generate + analyse (seed, taxpayers) |
| GET | /api/pipeline/status, /api/pipeline/runs | progress / last ten runs |
| GET | /api/overview, /api/overview/monthly | dashboard / monthly ITC series |
| GET | /api/taxpayers, /api/taxpayers/{gstin} | ranking (q, pattern, flagged, sector, sort, limit, offset) / profile with evidence, partners, invoices |
| GET | /api/chains, /api/chains/{id} | invoice chains / drill-down |
| GET | /api/structures, /api/graph (focus, ring, cluster, chain) | rings, clusters / graph data |
| POST | /api/explanations/{gstin} | Gemini case note, stored with quality checks |
| GET | /api/metrics, /api/health | evaluation + training info / status |

### Database (SQLite)
- `users(id PK, email unique, name, password_hash, created_at)`
- `pipeline_runs(id PK, seed, n_taxpayers, status, message, stats JSON, user_id FK->users, started_at, finished_at)`
- `explanations(id PK, run_key idx, gstin idx, model, text, evidence JSON, quality JSON, user_id FK->users, created_at)`
- Analytical data (taxpayers, invoices, returns) lives in CSV files + the pickled state, not in SQL.

### Code size (counted with wc -l on 15 Oct 2026)
ml/*.py 1,233 lines (pipeline 530, features 169, jepa 149, eval 133, graph 110, metrics 60, baseline 45, train 37); backend/app 787; scripts 690
(generate_gst_data 483, smoke_test 153, download_data 54); Python total 2,710. Frontend pages 1,415 lines in 10 pages; frontend src 3,774 lines in 36 files.
API process working set 503 MB (measured with the 600-taxpayer state loaded).

## 8. Screenshot inventory (`docs/screenshots/`, 1440x900, real data, run-14 = seed 42, 600 taxpayers)
01 landing - 02 login - 03 login with demo account filled - 04 overview before run - 05 overview while generating (JEPA training epoch 10/100, 25 %) -
06 overview results (+ 06b full page) - 07 taxpayer ranking - 08 profile signals (Lotus Manufacturing) - 09 profile evidence - 10 profile network with ring loop -
11 profile anomalous invoices - 12 profile ITC-spike taxpayer (Ganga Wholesale) - 13 profile shell cluster (Pioneer Services) - 14 fraud graph -
15 fraud rings and clusters list (full page) - 16 chain CH-R01 circular - 17 chain CH-S37 shell supply - 18 case before explanation -
19 case with Gemini explanation (+ 19b full page) - 20 model performance (+ 20b full page) - 21 run history - 22 overview dark mode - 23 command palette.

## 9. Known gaps (state as gaps, never as results)
- No real GST data; no external validation of the headline numbers; no held-out ecosystem labelled metrics.
- LLM is prompted, not fine-tuned; explanation quality only on 6 / 10 cases.
- No unit-test suite or coverage figure; no load test beyond single-user latency; no user-acceptance study.
- No SUS / usability score, no GPU measurement, no cross-seed variance.
- ITC-spike recall (0.833) is below the rule baseline (1.00); fake-invoice-buyer recall 0.895.
- TED (supervised GNN, real data) F1 76-95 % is a different task setting and data; not comparable.


## 10. Cross-seed study, threshold sweep and error analysis (added 15 Oct 2026; `scripts/docs_build/seed_study.py`)
Re-running the whole pipeline (generate, train JEPA, analyse, evaluate) on five other generated ecosystems of 600 taxpayers with the SAME weights and threshold
(`experiments/seed_study.json`):

| Seed | Fraud taxpayers | Flagged | P@k | Precision | Recall | F1 | ROC-AUC | Baseline F1 | Rings found |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 82 | 70 | 0.7805 | 0.8571 | 0.7317 | 0.7895 | 0.9695 | 0.4983 | 5/5 |
| 2 | 79 | 70 | 0.9241 | 0.9714 | 0.8608 | 0.9128 | 0.9953 | 0.4718 | 5/5 |
| 3 | 76 | 77 | 0.8816 | 0.8831 | 0.8947 | 0.8889 | 0.9928 | 0.4194 | 5/5 |
| 7 | 88 | 82 | 0.9205 | 0.9512 | 0.8864 | 0.9176 | 0.9921 | 0.4815 | 5/5 |
| 11 | 77 | 73 | 0.9351 | 0.9589 | 0.9091 | 0.9333 | 0.9920 | 0.4120 | 5/5 |
| **mean (std)** | | | 0.8884 (0.0569) | 0.9243 (0.0455) | 0.8565 (0.0644) | **0.8884 (0.0515)** | **0.9883 (0.0095)** | **0.4566 (0.0345)** | |

Range of model F1 0.7895-0.9333; baseline P@k mean 0.6249; invoice F1 mean 0.8997. Per-pattern recall across the five seeds: circular trading 1.00 on all;
shell entity 0.963-1.00; fake-invoice buyers 0.333-0.810; ITC spikes 0.417-0.917 (seed 42: 0.895 and 0.833). Conclusion: ranking quality is stable, the F1 at the fixed 0.5
threshold is lower and more variable than the seed-42 headline (0.955), and the advantage over the rule baseline holds on every seed. The seed-42 figures are a best case.

**Threshold sweep on seed 42** (flagged / TP / FP / FN / precision / recall / F1): 0.2: 174/79/95/0/0.454/1.000/0.625; 0.3: 113/78/35/1/0.690/0.987/0.813;
0.4: 85/77/8/2/0.906/0.975/0.939; **0.5: 78/75/3/4/0.962/0.949/0.955**; 0.6: 71/70/1/9/0.986/0.886/0.933; 0.7: 57/57/0/22/1.0/0.722/0.838; 0.8: 47/47/0/32/1.0/0.595/0.746;
0.9: 19/19/0/60/1.0/0.240/0.388.

**Mean layer scores seed 42 (fraud vs legitimate)**: JEPA 0.303 vs 0.067; behaviour 0.165 vs 0.085; network 0.684 vs 0.010; invoice 0.704 vs 0.014.

**Error analysis seed 42** (`experiments/error_analysis.json`): false positives (3, all legitimate, none from network or invoice evidence): Apex Distributors (wholesaler, risk 0.56, JEPA 0.68,
behaviour 0.16, network 0, invoice 0, rank 74, pattern behaviour_anomaly), Vertex Enterprises LLP (0.69; JEPA 0.80; rank 59; behaviour_anomaly), Orbit Industries Pvt Ltd (0.57; JEPA 0.37,
behaviour 0.51, invoice 0.22; rank 73). False negatives (4): Eastern Enterprises Pvt Ltd (ITC spike, risk 0.41, rank 84), Global Logistics & Co (ITC spike, 0.47, rank 80),
Metro Manufacturing (fake-invoice buyer, 0.29, rank 122), Zenith Enterprises (fake-invoice buyer, 0.32, rank 106). Detected rings: 9 (R01-R09; 7 with fraud members; R08 score 0.298 size 5 and
R09 score 0.266 size 2 contain no fraud; R07 merges 11 members; R05 has 2 members). Invoice level: 68 false positives (most common flag sets: no_eway+unreported 22, ring_edge+value_spike 18,
ring_edge+unreported 12) and 17 missed fraud invoices (shell_cluster+supplier_vanished 8 - noisy-OR 1-0.65x0.80 = 0.48 < 0.50; shell_cluster+young_supplier 3; ring_edge 3; round_value+shell_cluster 3).

**Explanation notes** (`experiments/samples.json`): the same case (Lotus Manufacturing, rank 1) was written 4 times during the project (stored notes): citations 13-14, 0 invalid, evidence coverage 1.0,
numeric grounding 0.870-0.900 across the four generations (0.889, 0.900, 0.870, 0.885); another case (rank 2-ish, 09GPRC...) twice at 0.75 with 10 citations. Mean over the 6 evaluated notes: 10.83 citations, numeric grounding 0.843, mean words 311.3.
