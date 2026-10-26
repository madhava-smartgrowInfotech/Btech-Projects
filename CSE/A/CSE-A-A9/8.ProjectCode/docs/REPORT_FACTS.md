# REPORT_FACTS - BotGraph (CSE-A-A9)

Single source of truth for every document in the batch folder. Numbers come from `experiments/metrics.json`,
`experiments/scalability.json`, `experiments/eval/metrics.json`, `scripts/smoke_test.py` and the latency run on 2026-10-26.

## 1. Identity

- Product **BotGraph**; project *Graph Neural Network Analysis for Scalable Fake Profile Detection and Botnets*; batch CSE-A-A9 (CSE-A, Batch 09).
- Students (from `1.A9_BATCH_DETAILS.docx` / `Students.txt`): BIJJA NAGA LAKSHMI 23K91A0538 - DIVVELA SRIVATSHAV 23K91A0564 - ADUMULLA DURGA 23K91A0504 - BURUGULA KOUSHIK 23K91A0550.
- Guide: NEELIMA (designation not given - placeholder). College / principal / HOD / academic year are not in the batch files - keep template placeholders.
- Ports: API 8309, web 5309. Demo logins `moderator@botgraph.app`, `analyst@botgraph.app`, password `Demo@1234`.

## 2. Base paper and literature (verified)

**Base paper (batch documents, `Documentary/` PDF read in full):** A. Saha, N. K. Sarkar, S. Pratihar, "PruferNET: An Augmented Graph Neural Network for
Influential Node Detection in Social Networks," *IEEE Access*, vol. 14, 2026, pp. 79940-, DOI 10.1109/ACCESS.2026.3695637 (published 21 May 2026).
- Task: three-class node classification by depth in a minimum spanning tree (Very Shallow / Shallow / Deep) - **influence**, not bot detection, no fake labels.
- Data: SNAP Facebook social circles, 4,039 nodes / 88,234 edges (paper's figure); extra check on Email-Eu-core (986 nodes, 16,064 edges).
- Method: edge weight 1/(deg u + deg v) -> MST -> Prufer sequence -> features (label frequency, entropy, unique-label ratio, transition influence, subtree depth)
  + degree, closeness, PageRank, trust score (mean neighbour PageRank) -> GraphSAGE (64 hidden, dropout 0.5, AdamW lr 0.003, 300 epochs), split 60/20/20.
- Reported: test accuracy **99.63 %** with Prufer features vs **96.54 %** with traditional features; 5-fold CV on Facebook "stable". Hardware in paper: T4 GPU, 16 GB RAM.
- Stated gaps relevant to this project: no bot/fake labels, no coordinated-group detection, no moderator loop, no scalability measurement.

Companions in `archived_base_papers/` (cite as supporting): RABot, arXiv 2602.21749 (Zhang et al., 2026, reinforcement-guided graph augmentation for imbalanced, noisy social bot detection);
HW-GNN, arXiv 2511.22493 (Liu et al., 2025, homophily-aware Gaussian-window spectral network for bot detection). `BASEPAPER_REFERENCES.md` there names RABot as base - the batch documents name PruferNET; **batch documents win**.

Batch literature survey (`5.LITERATURE SURVEY.docx`, titles/years only):
| # | Title | Verification |
|---|---|---|
| 1 | PruferNET (base) | verified from PDF |
| 2 | AdapTGN: adaptive temporal-relational GNN for bot detection (2026) | **not found** by web search - listed with "not verified", never cited for numbers |
| 3 | Novel GNN approach for social network fake news identification in Arabic (ICAART 2026 proceedings) | **not verified** - listed only |
| 4 | Social media bot detection using account metadata, advanced feature selection and stacking (IJSR 2026) | exact title not found; nearest match: Sharma & Borah, "Stacking of machine learning classifiers for bot detection using account level data," IJ-ICT vol 15 no 2, June 2026, pp. 477-487, DOI 10.11591/ijict.v15i2.pp477-487 (RF 89 %, stacked 90 %). Listed as "not verified", nearest match mentioned. |
| 5 | LGB: language model and GNN-driven social bot detection | exists: arXiv 2406.08762 (Tsinghua / Beijing Jiaotong); up to 10.95 % over baselines on two real datasets; venue in batch file (Research Digest...) not verified |

Other real works safe to cite (from arXiv records seen): BotDGT arXiv 2404.15070; BotTGCL ICCS 2025 (temporal-aware, graph contrastive); MSGS arXiv 2307.01968.
Classic references to add from knowledge with care (title/venue only, no invented numbers): Kipf & Welling GCN (ICLR 2017), Velickovic et al. GAT (ICLR 2018),
Hamilton et al. GraphSAGE (NeurIPS 2017), Blondel et al. Louvain (J. Stat. Mech. 2008), Leskovec & Mcauley SNAP ego networks (NeurIPS 2012), Kingma & Ba Adam (ICLR 2015), Paszke et al. PyTorch (NeurIPS 2019).

## 3. Data (from `docs/02_HOW_IT_WORKS.md`)

| Source | Licence | Used for |
|---|---|---|
| SNAP Facebook social circles (Kaggle mirror `dhruvb2028/social-circles-facebook`), ten `.edges` files | public research data | **real topology: 3,963 accounts, 88,156 ties** |
| Instagram fake/spammer/genuine accounts (`free4ever1/instagram-fake-spammer-genuine-accounts`), 696 labelled rows | CC BY 3.0 | profile attributes (resampled, jittered) |
| Twitter Bot Detection Dataset (`goyaladi/twitter-bot-detection-dataset`), 50,000 rows | CC0 | posting-behaviour rows (label carries almost no signal - acts as realistic noise) |
| Injected botnets (`ml/data.py`, seed 7) | generated | 8 botnets, 150 lone spammers, timing and interaction features, handles - **synthetic** |

- Final graph: **4,533 nodes (3,963 real + 570 injected), 94,456 ties (88,156 real + 6,300 injected), 570 fake (12.6 %)**.
- Botnet sizes (truth): 62, 50, 52, 60, 48, 56, 58, 34 = 420 bot accounts; + 150 lone spammers = 570.
- Camouflage: 40 % of botnet accounts and 25 % of lone spammers get genuine-looking profiles; 6 % of genuine accounts get fake-looking ones.
- Split: stratified 60/20/20 -> 2,719 train / 906 val / 908 test (114 fake in test); identical for every model.
- 23 features in four groups: profile metadata 12, posting behaviour 4, temporal 6, interaction frequency 1. Standardised before training.
- Honest limits: botnets are injected (measures recovery of this kind of coordination); profile and posting rows come from different people (no real correlation); no live-platform data; no text/NLP features (the abstract mentions linguistic cues - **not implemented**); no TwiBot-22-scale data.
- Not comparable with PruferNET: different task (bot vs. depth class), different labels, partly synthetic data.

## 4. Models and training

- Plain PyTorch sparse ops (no torch-geometric). Baseline MLP (2 dense layers, no graph); GCN `A_hat X W`; GraphSAGE `W_self x + W_neigh mean(N)`; GAT 4 heads then single head (edge softmax via scatter_reduce/index_add).
- 2 layers, 64 hidden, dropout 0.3, Adam lr 0.01, weight decay 5e-4, class-weighted cross-entropy (positive weight = sqrt of imbalance), <=160 epochs, patience 40 on validation F1, threshold tuned on validation; seeds 0, 1, 2.
- Trained 2026-10-24 13:16 UTC. Served model: GraphSAGE (best validation F1 0.9587).
- Clustering: candidates p >= 0.30; each linked to 5 most cosine-similar candidates + weight 1.0 per real tie; Louvain (`networkx`, seed 0); groups < 5 dropped; coordinated if tie density >= 5 %.
- Explanations: gradient x input attribution of the fake-vs-genuine margin (first-order approximation).

## 5. Metrics (test split, 908 accounts, 114 fake, mean +- std over 3 seeds)

| Model | Acc | Prec | Recall | F1 | ROC-AUC | PR-AUC | threshold(s) | train s (3 seeds mean per run) |
|---|---|---|---|---|---|---|---|---|
| Feature-only baseline (MLP) | 0.9585 +-0.0026 | 0.8683 +-0.0149 | 0.7895 +-0.0072 | **0.8270 +-0.0101** | 0.9668 | 0.9070 | 0.5 | 3.0 |
| GCN | 0.9637 +-0.0018 | 0.9585 +-0.0056 | 0.7427 +-0.0109 | **0.8369 +-0.0088** | 0.9880 | 0.9392 | 0.625-0.75 | 10.4 |
| GAT | 0.9765 +-0.0041 | 0.9632 +-0.0101 | 0.8450 +-0.0252 | **0.9001 +-0.0181** | 0.9776 | 0.9465 | 0.425-0.5 | 40.6 |
| **GraphSAGE (served)** | **0.9853 +-0.0014** | **0.9749 +-0.0040** | **0.9064 +-0.0149** | **0.9393 +-0.0063** | **0.9901** | **0.9736** | 0.5-0.525 | 11.7 |

- F1 lift over baseline: GCN +0.0099 (+1.0 pt), GAT +0.0731 (+7.3 pt), GraphSAGE +0.1123 (+11.2 pt).
- Observations: GCN has the best precision/recall trade towards precision (0.958) but lowest recall (0.743 < baseline 0.789); GAT has the highest seed variance (F1 0.877-0.922); GAT can drift +-0.01 between runs (non-deterministic index_add).
- Per-seed F1 GraphSAGE 0.9459 / 0.9412 / 0.9309; GAT 0.9014 / 0.8774 / 0.9217; GCN 0.8473 / 0.8374 / 0.8259; baseline 0.8333 / 0.8349 / 0.8128.
- Confusion matrices (stored for **seed 0** only; test 908): baseline TN 782 FP 12 FN 24 TP 90; GCN TN 791 FP 3 FN 28 TP 86; GAT TN 791 FP 3 FN 18 TP 96; **GraphSAGE TN 791 FP 3 FN 9 TP 105**.
- ROC points stored per model in metrics.json (`roc.fpr`, `roc.tpr`).
- **Not measured:** threshold sweep curves beyond the validation-tuned threshold, ablation of individual feature groups, cross-dataset or real-botnet evaluation, comparison with a numerical result from PruferNET (different task), significance tests, GPU timings.

### Botnet recovery (served GraphSAGE)
- 9 clusters found: **8 of 8 injected botnets recovered as single communities**, mean recall 1.000, mean precision 0.9883, fake purity 0.913 (of members flagged), plus one diffuse "loose" group of 160 accounts (density 0.0014, 18 internal ties; mean score 0.746) of lone spammers and look-alikes.
- Per botnet precision: 1.0, 1.0, 1.0, 0.923, 1.0, 1.0, 0.983, 1.0.
- Served clusters (app): BN-00112 size 65 (density 0.262, 95 % flagged, peak hour 22 holds 94 %); BN-03963 size 62 (density 0.312); BN-03936 size 59; BN-04235 size 56 (peak hour 21 holds 100 %); BN-04075 size 52; ... ; BN-00055 diffuse size 160.
- Flagged accounts at threshold 0.5: **548** of 4,533.
- Recall is on injected, seeded botnets - this is a known-answer test, not evidence about real-world botnets.

### Scalability (CPU, disjoint copies of the graph, 10 epochs timed)
| Nodes | Ties | Build s | GCN train/inf | GAT train/inf | SAGE train/inf | MLP train/inf |
|---|---|---|---|---|---|---|
| 4,533 | 94,456 | 0.046 | 0.142 / 0.036 | 0.255 / 0.051 | 0.060 / 0.027 | 0.073 / 0.011 |
| 9,066 | 188,912 | 0.106 | 0.152 / 0.065 | 0.597 / 0.129 | 0.115 / 0.054 | 0.022 / 0.002 |
| 18,132 | 377,824 | 0.266 | 0.307 / 0.143 | 1.103 / 0.259 | 0.203 / 0.099 | 0.041 / 0.003 |
| 36,264 | 755,648 | 0.513 | 0.577 / 0.235 | 2.022 / 0.584 | 0.392 / 0.186 | 0.085 / 0.008 |
(seconds; train = per epoch). Roughly linear in ties. Largest graph is 36 k accounts - far below platform scale; scale claim is limited to this range. First timing row of the baseline is slower than its second (warm-up).

## 6. Architecture, endpoints, storage

- `ml/` (data.py 345 lines, gnn.py 188, train.py 138, clustering.py 100, eval.py 90, config.py 39) -> `data/processed/{graph.npz, accounts.csv, graph_meta.json}`, `models/{baseline,gcn,gat,sage}.pt, scores.npz, clusters.json, meta.json`, `experiments/*.json`.
- `backend/app/` FastAPI: main.py, auth.py (JWT HS256 12 h, bcrypt), db.py (SQLAlchemy 2, SQLite), settings.py, routes/{core,accounts,clusters,queue,models}.py, services/store.py (loads artefacts once at start-up).
- `frontend/` React 18 + Vite 5 (JS), V4 Soft Pastel Calm kit; pages: Landing, Login, Overview, GraphData, Accounts, AccountDetail, Clusters, ClusterDetail, Queue, Models, NotFound.
- Code size: ml 900 lines, backend app ~850, scripts 533 (Python).
- Endpoints (18): GET /api/health; POST /api/auth/login; GET /api/auth/me; GET /api/graph/summary; GET /api/overview; GET /api/accounts; GET /api/accounts/{id}; GET /api/accounts/{id}/neighbourhood;
  GET /api/clusters; GET /api/clusters/{id}; GET /api/queue; POST /api/queue/decisions (moderator); DELETE /api/queue/decisions/{id} (moderator); GET /api/decisions; GET /api/models; GET /api/models/scalability;
  POST /api/models/retrain (moderator); GET /api/models/retrain/status. All but health and login need a bearer token; analyst gets 403 on moderator routes; CORS limited to the web origin.
- SQLite tables: `users(id,email,name,role,password_hash)`, `reviews(id,target_type,target_id,decision,note,score,members JSON,user_id FK,created_at,used_in_run)`, `training_runs(id,started_at,finished_at,status,feedback_labels,best,f1_before JSON,f1_after JSON,message,user_id FK)`.
- Retraining: decisions become labels (confirm -> fake, dismiss -> genuine); reviewed accounts move into training; **test split never touched**; one seed, four models; F1 before/after logged; used decisions can no longer be undone.
- No third-party calls at run time (Gemini entries in `.env.example` unused).

## 7. Testing (real runs)

- `scripts/smoke_test.py`: **36 checks pass** (2026-10-26, system Python 3.11.9, torch 2.14.1+cpu): health, auth (anonymous 401, wrong password 401, both roles), graph counts, 3 models beat baseline, scalability, ranking, account detail, neighbourhood, search, 404, botnets found and recovered, analyst blocked from decisions, cluster decision clears members from queue, undo, retrain run recorded with before/after F1, decisions marked used, used decision not undoable, API serves full graph afterwards. Scratch DB and model copies - the shipped files are untouched.
- There is **no pytest unit-test suite**; the smoke test is the automated suite. `scripts/ui_checks.py` (360/768/1440 px light + dark, keyboard, reduced motion) and `scripts/capture_screens.py` (console errors) were run when the UI was built (recorded as ticked in `docs/FRONTEND_PLAN.md`); not re-run on 2026-10-26.
- Environment note: `import torch` after `fastapi` fails here with WinError 1114 on the machine's system Python; the project `.venv` (made by `setup.bat`) does not have this problem. The 2026-10-26 runs preloaded torch through a scratch `sitecustomize`; product code unchanged. The `.venv` folder is no longer in the working tree.

## 8. API latency (measured 2026-10-26, 127.0.0.1, 20 requests each, scratch DB, warm server)

| Endpoint | median ms | p95 ms |
|---|---|---|
| /api/health | 11.1 | 20.1 |
| /api/overview | 12.6 | 26.9 |
| /api/graph/summary | 8.3 | 22.8 |
| /api/accounts?page_size=25 | 8.9 | 23.1 |
| /api/accounts/{id} | 10.6 | 27.5 |
| /api/accounts/{id}/neighbourhood | 13.8 | 28.4 |
| /api/clusters | 15.0 | 23.2 |
| /api/queue?kind=accounts | 6.7 | 22.4 |
| /api/models | 16.0 | 24.3 |
| /api/models/scalability | 3.0 | 27.7 |
| POST /api/auth/login (5 requests, bcrypt) | 233 | - |
- API start-up (load graph, scores, clusters): 5.1 s to first healthy response. Machine was shared with another session's CPU job - treat as upper bounds.

## 9. Measurement machine

12th Gen Intel Core i5-12500 (6 cores / 12 threads), 16 GB RAM (16,073 MB), Windows 11 Pro, CPU only (no GPU), Python 3.11.9, PyTorch 2.14.1+cpu on the system interpreter (project pins `torch>=2.2,<2.6`; the shipped models were trained 2026-10-24), Node v24.19.0.
Software: FastAPI, Uvicorn, SQLAlchemy 2, PyJWT, bcrypt, NumPy 1.x, pandas 2, scikit-learn, networkx 3.x (Louvain), React 18, Vite 5.

## 10. Screenshot inventory (`docs/screenshots/`, all 1440x900, real data, captured by `scripts/capture_screens.py`)

01_landing_light, 02_landing_dark, 03_login, 04_overview, 05_graph_and_features, 06_accounts, 07_account_detail, 07b_account_reasons_and_neighbourhood (checked: real account 4286, score, reasons, neighbourhood),
08_clusters, 09_cluster_detail, 09b_cluster_graph_and_members, 10_queue_accounts, 11_queue_clusters, 12_decision_log, 13_models_comparison, 14_models_scalability, 15_models_retraining, 16_overview_dark. (18 images)

## 11. Objectives vs outcome

1. Graph representation - done (4,533 nodes, 94,456 ties, documented schema).
2. Node features - done (23 in four groups); **no text/linguistic features** though the abstract mentions them.
3. Compare GCN/GAT/GraphSAGE - done on one split, 3 seeds, plus no-graph baseline. GraphSAGE best (F1 0.939).
4. Botnet clusters from embeddings - done; 8/8 injected botnets recovered (synthetic ground truth).
5. Evaluation - accuracy, precision, recall, F1, ROC-AUC, PR-AUC measured.
6. Scalability - measured to 36 k accounts / 756 k ties on CPU, roughly linear; platform-scale not tested.
Not done / honest gaps: real-world botnet evaluation, text NLP features, temporal/dynamic graph, live ingestion, comparison with RABot/HW-GNN reproduced on our data, pytest suite.

## 12. Items needing a decision / flagged

- Base paper conflict: batch documents say PruferNET, the archive record says RABot. Docs use PruferNET as base, RABot and HW-GNN as supporting references.
- Literature survey items 2-4 cannot be verified (see section 2).

## 13. Extra experiments (scripts/run_extra_experiments.py, 2026-10-26, experiments/extra/metrics.json; 324.8 s on the shared CPU)

Threshold sweep and error analysis use the shipped scores (seed-0 models, test split 908 accounts, 114 fake). Ablation retrains in memory with seeds 0, 1, 2 and a validation-tuned threshold; its "all 23 features" row (baseline 0.822, GraphSAGE 0.942) differs from the main table (0.827, 0.939) in the third decimal because it is a separate run.

### 13.1 Threshold sweep (served GraphSAGE, seed 0)
| Threshold | Precision | Recall | F1 | FP | FN |
|---|---|---|---|---|---|
| 0.20 | 0.838 | 0.956 | 0.893 | 21 | 5 |
| 0.30 | 0.908 | 0.947 | 0.927 | 11 | 6 |
| 0.40 (F1 peak) | 0.956 | 0.947 | **0.952** | 5 | 6 |
| 0.50 (served) | 0.972 | 0.921 | 0.946 | 3 | 9 |
| 0.60 | 0.981 | 0.904 | 0.941 | 2 | 11 |
| 0.70 | 0.980 | 0.877 | 0.926 | 2 | 14 |
| 0.80 | 0.990 | 0.851 | 0.915 | 1 | 17 |
| 0.90 | 0.989 | 0.798 | 0.883 | 1 | 23 |
- F1 stays between 0.927 and 0.952 for every threshold from 0.30 to 0.60: the result does not hinge on the tuned threshold. The sweep's F1 maximum (0.952 at 0.40) is on the test split itself, so it is shown for analysis only; the served threshold (0.5) was chosen on validation.
- Baseline MLP, same sweep: best F1 0.834 (thresholds 0.50, 0.55, 0.65); at 0.30 precision 0.692 / recall 0.886 (45 FP); recall above 0.9 only with precision below 0.62 (threshold 0.25: P 0.612, R 0.912). The graph model keeps precision 0.87 at recall 0.947.

### 13.2 Error analysis (served GraphSAGE at 0.5, seed 0; 114 fake accounts in test)
- Botnet members in the test split: 82 - GraphSAGE caught **82**, baseline caught 64.
- Lone spammers in the test split: 32 - GraphSAGE caught **23**, baseline caught 26 (the graph does not help against lone spammers).
- Rescued by the graph (missed by baseline, caught by GraphSAGE): 18; lost (caught by baseline, missed by GraphSAGE): 3; missed by both: 6.
- All 9 missed fakes are lone spammers with degree 4-8 (median degree of missed fakes 7 versus 20 for caught fakes). Their scores: 0.02-0.50.
- The 3 false positives are genuine accounts of the real topology (degrees 4, 10 and 41).

### 13.3 Feature-group ablation (test F1, mean +- std over 3 seeds; precision / recall in brackets for GraphSAGE)
| Variant | Features | Baseline MLP | GraphSAGE |
|---|---|---|---|
| All features | 23 | 0.822 +- 0.009 | 0.942 +- 0.001 (0.966 / 0.918) |
| Without profile metadata | 11 | 0.803 +- 0.013 | 0.887 +- 0.004 |
| Without posting behaviour | 19 | 0.822 +- 0.016 | 0.946 +- 0.005 |
| Without temporal pattern | 17 | 0.515 +- 0.003 | 0.840 +- 0.003 |
| Without interaction frequency | 22 | 0.825 +- 0.010 | 0.919 +- 0.022 |
| Profile metadata only | 12 | 0.512 +- 0.011 | 0.831 +- 0.012 |
| Behaviour only (posting, temporal, interaction) | 11 | 0.803 +- 0.013 | 0.887 +- 0.004 |
| **Degree only (log degree, no attributes)** | 1 | 0.338 +- 0.003 | **0.965 +- 0.003 (0.962 / 0.968)** |

Findings (state exactly like this):
1. The temporal pattern group (synthetic: botnet members share a creation window and a peak hour) is the most valuable attribute group: removing it drops the baseline from 0.822 to 0.515 and GraphSAGE from 0.942 to 0.840. It is synthetic, so it is where the benchmark is most generous.
2. Posting behaviour adds nothing (GraphSAGE 0.946 without it): consistent with the Twitter bot label carrying almost no signal.
3. Profile metadata alone gives the baseline only 0.512, while GraphSAGE on the same 12 features reaches 0.831: the neighbourhood supplies what the profile lacks.
4. **GraphSAGE on a single structural feature (log node degree) scores F1 0.965, above the model with all 23 features (0.942).** In this benchmark the injected botnets and lone spammers have a distinctive local degree pattern (dense internal ties, 2-7 or 3-10 ties to real accounts), so message passing over degrees alone nearly solves the task. The benchmark therefore rewards structure more than a real platform would; the F1 of 0.939 must not be read as real-world accuracy. The no-graph MLP on degree gets precision 0.205 / recall 0.953 (F1 0.338): a node's own degree is not enough, its neighbours' degrees are what separate the classes.
5. The reported "graph lift" (+11.2 F1 points) is genuine for this data but is partly produced by how the botnets were injected.

## 14. Retraining runs and defects found while documenting (2026-10-26, scratch API and scratch database; shipped files untouched)

Two retraining runs on a scratch copy of the application (details and exact numbers: Chapter 8 section 8.9 of the report, `docs/metrics/sample_io.json`):
- Run A (all decisions correct): F1 change GraphSAGE +0.1 point, baseline +0.2, GAT -0.9, GCN -2.1 (one training seed each).
- Run B (two deliberate wrong decisions: one fake account dismissed, one 62-account botnet dismissed): GraphSAGE -4.1 points, GCN -8.2, GAT -1.5, baseline -0.3; clusters shown fell from 8 to 7.
Defects found (not fixed - the product code was not changed in the documentation run):
1. After run A the served model switched from GraphSAGE to GAT: the best architecture is chosen on one seed's validation F1 after reviewed accounts left the validation set; GraphSAGE still had the higher test F1 (0.947 vs 0.892) and `/api/health` then reports GAT's full-run F1 of 0.900.
2. Any invalid token returns "session has expired".
3. The default JWT secret is a fixed public development string when `.env` keeps the placeholder.
4. A wrong moderator decision, especially on a whole cluster, corrupts the retraining labels (no review or second approval step).
Other: no pytest suite; `scripts/ui_checks.py` not re-run on 2026-10-26; the project `.venv` is created by `setup.bat` and is not in the working tree.
