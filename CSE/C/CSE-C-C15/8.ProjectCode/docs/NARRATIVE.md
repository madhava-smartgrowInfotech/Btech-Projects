# SentinelFlow (CSE-C-C15) - the story every document tells

Read `docs/REPORT_FACTS.md` (numbers), `scripts/docs/facts.py` (`F.K()` returns the headline numbers - never hard-code a metric, read it from `F.K()`, `F.REAL`, `F.WIN`, `F.HYB`, `F.LAT`, `F.API`, `F.SHIP`),
`scripts/docs/refs.py` (`CITE['key']` gives the reference number), `scripts/docs/lit.py` and `scripts/docs/diagram_index.py`.

## One-paragraph story
Batch C15 asked for "a framework that detects DDoS traffic in real time and applies adaptive mitigation without blocking legitimate users". The base paper (Trigui et al., IEEE Access 2026, [1]) builds an RF + Banzhaf feature-selection ensemble
for SDN DDoS detection and reports 100 % on two offline datasets, with deployment, mitigation and live testing left as future work. SentinelFlow implements the closed loop on a commodity host: Scapy (or a built-in simulator) -> rolling windows ->
ten flow features -> 200-tree Random Forest -> explainable distributed-risk (carpet-bombing aware) and severity layer -> temporary application-level quarantine that recovers automatically -> SQLite history -> React console. The honest result is
mixed: the pipeline, API, UI and tests work (95 pytest tests, 25 smoke checks), the shipped model was trained on a synthetic fallback and does NOT transfer to real CICIDS2017 flows (71.8 % accuracy), retraining the same forest on real flows gives
99.94 % (5 seeds), the severity layer removes most false alarms, window length matters, "mitigation" never changes the OS firewall, and live capture could not be tested end to end because Npcap is absent.

## Things every document must say plainly (when relevant)
1. Shipped model = synthetic fallback + 6,000 window rows; 99.71 % accuracy / 99.46 % recall / 0.04 % FPR on its own held-out split (4,800 rows) is NOT a real-world figure.
2. Real data: CICIDS2017 Friday-Afternoon-DDoS file (225,745 flows: 97,718 benign, 128,027 DDoS) from the Hugging Face mirror `c01dsnap/CIC-IDS2017`; shipped model scores 71.79 % accuracy, 63.40 % recall, 17.21 % FPR, ROC-AUC 86.1 %.
3. Retrained RF (same 10 features, 200 trees, seed 42) on real flows: 99.94 +/- 0.01 % (5 seeds), FPR 0.058 %, block split 99.74 %. Caveats: one attack type (the DDoS day), random split of flows, known CICIDS2017 label problems [9], and the 10 features reduce to packet/byte counts and sizes.
4. Base-paper comparison: their 100 % is on a 104,345-row SDN dataset and a 1.75 M-row CIC-DDoS2023 subset with ensembles; ours is 99.94 % on CICIDS2017 DDoS-day flows - different data, different protocol, indicative only. Resource side: our RF trains in about 7 s (real flows), model 1.24 MB (real) / 2.74 MB (shipped); their SVM/kNN ensembles needed over 4,000 s / 150 s. Their mitigation is future work; ours is implemented (application-level).
5. Window length: calibrated on 10 s windows. At 2 s / 5 s the RF label alone gives 46.0 % / 13.6 % false positives on benign windows; High/Critical severity gives 6.77 % / 0.27 % FPR (recall 100 % at 2 s and 5 s, 96.96 % at 10 s where 44 weaker attack windows stay at Medium). Read exact values from `F.K()` / `F.WIN`.
   At 10 s the RF label is 100 % accurate on simulator windows only because the model was trained with rows from the same generator (tautological) - say so.
6. Distributed-risk score alone is a precise but weak detector (precision 100 %, recall 9-32 % at threshold 0.7); it works as a signal inside severity, not as a detector.
7. Mitigation = application-level denylist inside SentinelFlow (top 3 non-protected sources, 40 s, doubled for Critical, automatic recovery). `apply_os_firewall_block()` is a stub (`applied: false`). Nothing is dropped on the network. "Rate limiting" is only recommended.
8. Time from detection to mitigation: the decision is made within the same call that stores the detection; measured on a CPU-saturated host, median 217 ms from finished feature vector to decision (p95 489 ms), dominated by forest inference with the saved `n_jobs=-1` (single-window inference 313 ms median vs 33 ms with `n_jobs=1`). The real delay is the window length (default 10 s; 2-120 s). No real attack timeline was measured.
9. Live capture needs Npcap + Administrator; not installed here, so only the error path was exercised (HTTP 200 on start, capture_error reported by /api/status, mode returns to stopped). Simulation Mode drives the identical `process_window()` pipeline.
10. The React login is a browser-side demo gate (demo@sentinelflow.com / Demo@1234); the REST API has no authentication and binds to 127.0.0.1. The `settings` table exists but the API keeps settings in memory.
11. Landing page shows the 99.71 % figure without a synthetic caveat; the Model page has a "SYNTHETIC TRAINING DATA" warning.
12. Screenshots are Simulation Mode data scored by the real model (screens say "SIMULATION MODE"); the Overview screenshot shows the real "capture problem" banner (no Npcap). They were captured at 2 s windows.

## Objectives (6.OBJECTIVES&PROBLEM STATEMENT.docx) against outcomes
| # | Objective | Outcome |
|---|---|---|
| 1 | Acquire a benchmark dataset and extract flow features | Partly: training script looks for CICIDS2017 CSVs in data/raw and otherwise builds a synthetic fallback (what shipped). In this documentation run the real Friday-DDoS file (225,745 flows) was obtained and mapped with the product's own preprocessing; the shipped model was not retrained on it. |
| 2 | Capture live traffic and compute the same features in real time | Implemented (Scapy sniff, `traffic_aggregator`, same schema as training); not verified live (no Npcap) - verified through the simulator and unit tests of the aggregator. |
| 3 | Train a classifier to separate DDoS from legitimate traffic | Achieved as code and as a result on real flows after retraining (99.94 %); the shipped artefact is synthetic-trained (71.8 % on real flows). |
| 4 | Adaptive mitigation that rate-limits or blocks sources | Partly: temporary quarantine with automatic recovery inside the application; rate limiting only recommended; no OS/network enforcement. |
| 5 | Dashboard of live traffic, detections and mitigation | Achieved: React console (8 screens) plus legacy dashboard; polling every 2 s. |
| 6 | Evaluate accuracy, false positives and detection-to-mitigation time | Achieved for accuracy and FPR (synthetic split, real flows, window pipeline at three window lengths) and for decision latency; not measured against a real attack timeline. |

## Novelty against the base paper (state it modestly)
(a) closes the loop the base paper leaves open (severity -> mitigation -> recovery -> history) on a commodity host and measures its latency; (b) a transparent distributed-risk layer for carpet-bombing patterns (source diversity, destination diversity, rate pressure, baseline deviation), with a measured finding that it is weak alone but useful inside severity; (c) an explainable severity score that lists its factors and removes most false alarms; (d) a safe Simulation Mode that runs the identical pipeline; (e) a shared feature schema for flow rows and window rows, with a measured flow-to-window scale gap; (f) an evaluation protocol that separates synthetic and real data and reports the gap. NOT new: Random Forest, CICIDS2017, Scapy, Flask. Not implemented from the base paper: Banzhaf feature selection, voting ensembles (a comparison of single classifiers on real flows is included instead).

## Source-of-truth quirks
- Product name SentinelFlow; ports API 8415, web 5415 (`.env`). Project title is the batch title; DOCX/PPTX titles use the full batch title.
- Batch details say base paper = IEEE Access 2026 (Trigui et al.). The folder also holds arXiv 2605.26307 (Swileh et al., carpet-bombing, RAG + LLM) and arXiv 2502.00975 (Rahman): cite them as related work [6], [7].
- Students and guide: use `F.STUDENTS`, `F.GUIDE`; placeholders `[COLLEGE NAME]`, `[ACADEMIC YEAR]`, `[HOD NAME]`, `[PRINCIPAL NAME]`, `[DESIGNATION]` stay.
- Hardware: i5-12500, 15.7 GB, Windows 11, CPU only; other sessions kept the CPU at 100 % during measurements (say so next to latency numbers).

## Assets
Diagrams `docs/diagrams/01..10` (see `diagram_index.DIAGRAMS`); result charts `docs/figures/f01_domain_gap`, `f02_window_size_effect`, `f03_classifier_comparison`, `f04_feature_importance_compare`, `f05_feature_ablation`,
`f06_confusion_matrices`, `f07_severity_by_style`, `f08_latency_breakdown`, `f09_api_latency`, `f10_flow_vs_window_scale`; shipped plots `results/confusion_matrix.png`, `roc_curve.png`, `feature_importance.png`;
screenshots `docs/screenshots/01_landing_light` ... `12_command_palette` (12) and the older dashboard in `screenshots/` (8, appendix only). Code to quote: `app.py` (process_window), `security/*.py`, `monitoring/traffic_aggregator.py`, `ml/train_model.py`, `ml/preprocessing.py`, `database/db.py`.

## Style
Times New Roman, no marketing language, no "robust/seamless/state-of-the-art" filler, no invented numbers, first person plural for the team's own work is fine, past tense for measurements. Every figure and table referenced in the text.
Full report 80-95 pages; chapter documents each over 40 KB (include figures).
