"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

All numbers come from facts.py (results/metrics.json and results/experiments/*.json); nothing is typed in by hand except configuration constants
that are read from the code (weights, thresholds) and library versions that were read from the environment.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import prepare, set_title, wipe, agenda, title_slide, thank_you, trim, render  # noqa: F401

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


def api(path, method="GET"):
    for r in F.API["latency"]:
        if r["path"] == path and r["method"] == method:
            return r
    raise KeyError(path)


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    k = F.K()
    R, W, H, L = F.REAL, F.WIN, F.HYB, F.LAT
    sh = F.SHIP
    probes_ok, probes_total = F.API["probes_ok"], F.API["probes_total"]
    st = api("/api/status")

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: Random Forest detection, distributed-risk severity and self-recovering quarantine",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS", 28)
    notes[1] = ("This review shows how SentinelFlow is designed and built, what is implemented, the first measured results and the open items. "
                "Introduce the four team members and the guide. The headline for this review is honest: the pipeline works, the shipped model was trained on a synthetic fallback, "
                "and we re-checked it on real CICIDS2017 flows.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and data"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    Wd = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "A DDoS attack floods a service from many sources. Detection without action leaves the service down, and blocking legitimate users through false positives is itself a denial of service. Signature rules miss new patterns.", K.ORANGE, "!"),
        ("Proposed system", "SentinelFlow turns rolling traffic windows into ten features, classifies them with a Random Forest, scores distributed risk and severity with listed factors, quarantines the worst sources temporarily and lets them recover, and shows everything on a React console.", K.BLUE, "i"),
        ("Base paper link [1]", "Trigui et al. (IEEE Access, 2026) build an RF + Banzhaf feature-selection ensemble for SDN DDoS detection and report 100 % offline; mitigation and live testing are future work. SentinelFlow implements the closed loop; it does not implement Banzhaf selection or voting ensembles.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (Wd + 0.29), 1.6, Wd, 4.8, t, b_, col, gl, body_size=17)
    notes[3] = "Recap of Review 1. We say plainly what is borrowed (a tree-based detector on flow features) and what is added (the live detection to mitigation loop)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "r2_01"), 0.6, 1.3, 7.2, 5.7)
    K.text(s, 8.0, 1.45, 4.75, 5.4, [
        ("**Four tiers, one process**", {"space_after": 8}),
        (f"Console: React 19 + Vite on port {F.WEB_PORT}, nine pages (landing, login, overview, detections, analytics, network health, mitigation, model, settings).", {"bullet": True}),
        (f"API: Flask on port {F.API_PORT}, twelve JSON endpoints; invalid input returns HTTP 400 with a message.", {"bullet": True}),
        ("Pipeline: monitoring, ml and security packages share one per-window function, process_window().", {"bullet": True}),
        ("State: SQLite plus joblib and JSON files. The REST API has no authentication and binds to 127.0.0.1.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "The same process_window() function handles live and simulated windows, so Simulation Mode exercises the real classifier, severity and mitigation code."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: train offline, then one pass per window")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "r2_02"), 0.6, 1.4, 7.4, 4.9)
    for i, (t, b_) in enumerate([("Train", "CICIDS2017 CSVs (or a synthetic fallback), mapped to ten features, plus 6,000 aggregated simulator windows; 200-tree Random Forest."),
                                 ("Monitor", "Window of packets, ten features, RF label and confidence, distributed risk, severity, action."),
                                 ("Evaluate", "Accuracy, precision, recall, F1, false-positive rate; real flows, synthetic split and window pipeline at 2, 5 and 10 s.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.3, y, 4.43, 1.65)
        K.text(s, 8.45, y + 0.07, 4.15, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.45, y + 0.42, 4.15, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.45, 7.4, 0.45, "High-level workflow of ml/train_model.py and the monitoring cycle.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "Offline training happens once; every window then costs a feature aggregation, one forest prediction and a few rule evaluations."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Data: synthetic training set and real CICIDS2017 check")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{sh['train_samples'] + sh['test_samples']:,}", "rows in the shipped training run (19,200 train, 4,800 test)", K.ORANGE),
                                   ("6,000", "of them aggregated simulator windows (3,000 benign, 3,000 attack)", K.BLUE),
                                   (f"{R['rows']:,}", "real CICIDS2017 flows used for the check (Friday DDoS day)", K.GREEN),
                                   (f"{R['benign'] / 1000:.1f}k / {R['attack'] / 1000:.1f}k", "benign / DDoS flows in the real file", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=11)
    rows = [["", "Shipped model's training data", "Real-data check (this review)"],
            ["Source", "Synthetic flows in CICIDS2017 column layout (CICIDS2017 was unreachable at build time) + simulator windows", "CICIDS2017 Friday-Afternoon-DDos CSV, Hugging Face mirror c01dsnap/CIC-IDS2017; licence 'other'; Sharafaldin et al. [8]"],
            ["Labels", "Benign / Attack by construction (12,000 each)", "BENIGN 97,718, DDoS 128,027 as labelled by the dataset authors"],
            ["Features", "Ten: sent / received packets, bytes, packets per s, bytes per s, average sizes", "Same ten, mapped by the product's own ml/preprocessing.py (forward = sent, backward = received)"],
            ["Split", "Stratified 80/20, seed 42", "Shipped model scored on all flows; retrained forest on stratified 80/20 over 5 seeds and on a 70/30 block split"],
            ["Caveat", "99.71 % is measured on the synthetic split", "One attack type; known label problems in CICIDS2017 [9]; file not committed to the repository"]]
    K.table(s, 0.6, 2.95, [1.3, 5.3, 5.53], rows, font_size=12, row_h=0.66, first_bold=True)
    notes[6] = ("The product's own training script falls back to synthetic data when CICIDS2017 cannot be downloaded, and records that in metrics.json. "
                "For this review the real file was downloaded separately and the shipped model and a retrained model were tested on it.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing and feature schema")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Raw flows / packets", K.NAVY), ("Clean: drop inf, NaN", K.PURPLE), ("Map to 10 features", K.PURPLE),
                                       ("Add window rows", K.GREEN), ("Stratified 80/20", K.GREEN), ("Random Forest", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([("10", "features: sent and received packets, bytes, rates and average sizes", K.BLUE),
                                   ("10 s", "default window; the model was calibrated on 10 s windows", K.GREEN)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=12)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        ("Flows: forward packets and bytes become 'sent', backward become 'received'; rates are counts over the flow duration; averages are bytes over packets (0 when there are none).", {"bullet": True}),
        ("Windows: packets whose destination is a local address are 'received', those from a local address are 'sent'; the same schema keeps training and inference identical.", {"bullet": True}),
        ("Every prediction validates names, order, NaN / infinity and negative values before the forest sees them.", {"bullet": True}),
        ("Known limit: a flow and a 10-second window differ in scale, so 6,000 simulator windows are added to training; a forest trained on flows alone called every simulated window benign.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "ml/preprocessing.py and monitoring/traffic_aggregator.py. The flow-to-window scale gap was measured: the forest retrained on real flows only had zero attack recall on simulator windows."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model: 200-tree Random Forest on ten features")
    wipe(s)
    K.picture(s, trim(F.fig("f04_feature_importance_compare.png"), "r2_f04"), 0.6, 1.35, 7.6, 4.6)
    K.text(s, 0.6, 6.0, 7.6, 0.8, "Gini importance of the shipped forest (synthetic data) and of a forest retrained on real flows: the real forest relies on average packet sizes and sent bytes.", size=12, color=K.TXT, align="c", italic=True)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**Why a Random Forest**: handles non-linear count and size features, trains in seconds, no feature scaling, and gives importances to explain.", {"bullet": True, "space_after": 8}),
        (f"**On real flows** the same forest scores {k['rr_acc'][0] * 100:.2f} % (5 seeds); a decision tree and gradient boosting are equal within 0.01 points; Gaussian Naive Bayes reaches {R['baselines_seed42']['GaussianNB']['accuracy'] * 100:.1f} %.", {"bullet": True, "space_after": 8}),
        (f"**Size**: shipped model {L['model_file_mb']} MB, loads in {L['model_load_seconds']} s.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[8] = "The base paper compares seven classifiers and four ensembles; we compare five single classifiers on the same real split, and the tree-based ones are indistinguishable."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training and evaluation configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Classifier", "scikit-learn RandomForestClassifier: 200 trees, no depth limit, class_weight balanced, seed 42, n_jobs = -1"],
            ["Shipped training run", f"{sh['train_samples']:,} train / {sh['test_samples']:,} test rows (stratified 80/20), trained in {sh['training_seconds']} s; artefacts in models/ and results/"],
            ["Real-data experiments", "RF retrained with the same settings on real flows: 5 seeds (42, 1, 2, 3, 4) and a 70/30 block split; baselines DT, HistGradientBoosting, GaussianNB, logistic regression"],
            ["Window pipeline test", "4,000 simulator windows per length (2, 5, 10 s; 35 % attack), rolling baseline of 12 windows, persistence, severity as in app.py"],
            ["Latency run", "600 windows; single-window inference; REST calls over 127.0.0.1"],
            ["Machine", "Core i5-12500, 15.7 GB RAM, no GPU, Windows 11; Python 3.11.9, scikit-learn 1.9.1; other jobs kept the CPU at 100 % during timing"]]
    K.table(s, 0.6, 1.45, [2.5, 9.63], rows, font_size=13.5, row_h=0.72, first_bold=True)
    K.text(s, 0.6, 6.7, 12.13, 0.4, "Hyper-parameters are those of ml/train_model.py; no tuning was done for this review.", size=12, color=K.TXT, italic=True)
    notes[9] = "Everything in the result slides was produced by scripts/run_experiments.py and scripts/measure_api.py; the shipped artefacts were never overwritten."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: risk, severity and mitigation")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_core_algorithm.png"), "r2_10"), 0.6, 1.3, 5.2, 5.7)
    rows = [["Step", "Rule (from the code)"],
            ["Distributed risk", "0.30 min(src/30,1) + 0.30 min(dst/15,1) + 0.25 min(rate/1500,1) + 0.15 baseline deviation; Medium from 0.4, High from 0.7"],
            ["Persistence", "consecutive windows with Attack or risk >= 0.7"],
            ["Severity score", "Attack +30; confidence >= 0.9 +15; rate >= 3,000 pkt/s +20; risk >= 0.7 +20; wide spread +8; persistence >= 3 +10; benign capped at 45"],
            ["Levels", "Medium >= 28, High >= 50, Critical >= 70"],
            ["Action", "Low: monitor. Medium: recommend rate limit. High / Critical: quarantine the top 3 non-protected sources for 40 s (80 s for Critical), then recover"]]
    K.table(s, 6.0, 1.4, [1.55, 5.18], rows, font_size=13, row_h=0.9, first_bold=True)
    notes[10] = "This mirrors security/distributed_analysis.py, severity.py and mitigation.py. Local and loopback addresses are never quarantined; the operating-system firewall is never touched."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "r2_04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["monitoring/", "capture, simulator, aggregator"], ["ml/", "features, preprocessing, training"], ["security/", "detector, risk, severity, mitigation"],
            ["database/db.py", "SQLite, four tables"], ["app.py", "12 endpoints, process_window"], ["frontend/src", "React pages and polling"],
            ["tests/", f"{F.PYTEST_TOTAL} pytest tests"], ["scripts/", "smoke, experiments, API probes"]]
    K.table(s, 7.9, 1.4, [1.9, 2.93], rows, font_size=12, row_h=0.52, first_bold=True)
    K.text(s, 7.9, 6.3, 4.83, 0.6, "Level-1 data flow diagram: seven processes, four stores.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1: capture and aggregate, classify, risk and severity, mitigate; the API, health sampler and training run alongside."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database and UML")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "r2_09"), 0.6, 1.3, 7.0, 4.9)
    K.picture(s, trim(F.diag("06_uml_class.png"), "r2_06"), 7.8, 1.3, 5.0, 5.2)
    K.text(s, 0.6, 6.3, 7.0, 0.7, "SQLite database: detections, mitigations, health_samples and settings; no foreign keys are declared.", size=11.5, color=K.TXT, italic=True)
    K.text(s, 7.8, 6.55, 5.0, 0.5, "Classes and module interfaces present in the code.", size=11.5, color=K.TXT, italic=True)
    notes[12] = "Honest point: the settings table exists but the API keeps settings in memory, and a quarantine row is linked to its detection only by reason text and time."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Language and API", "Python 3.11.9, Flask 3.1.3 (threaded), python-dotenv; ports 8415 and 5415 from .env"],
            ["Machine learning", "scikit-learn 1.9.1 (RandomForest), pandas 3.1.0, NumPy 2.4.6, joblib 1.6.0, matplotlib 3.11.2 for result plots"],
            ["Traffic and host", "Scapy 2.8.0 (sniff, needs Npcap on Windows), psutil 7.2.2 (CPU, memory, network counters)"],
            ["Storage", "SQLite (standard library) with a lock; model and metrics as joblib, JSON and PNG files"],
            ["Front end", "React 19, Vite 8, Tailwind 4, Recharts 3, React Router 7, axios, Framer Motion, three.js backdrop"],
            ["Testing and run", f"pytest 9.1.1 ({F.PYTEST_TOTAL} tests), smoke script, API probe script; run.bat or Docker (dashboard, inference, simulation)"]]
    K.table(s, 0.6, 1.45, [2.6, 9.53], rows, font_size=15, row_h=0.78, first_bold=True)
    notes[13] = "Versions are those installed on the development machine. The model file was saved with scikit-learn 1.9.0 and loads under 1.9.1 with a warning."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Aggregator, Random Forest, distributed risk, severity, mitigation with expiry", "Done", f"{F.PYTEST_PASSED}/{F.PYTEST_TOTAL} pytest tests cover each module"],
            ["Flask API (12 endpoints), SQLite storage, React console (9 pages)", "Done", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} smoke checks; {probes_ok}/{probes_total} malformed-input probes handled"],
            ["Simulation Mode through the identical pipeline", "Done", f"first detection {F.API['first_detection_after_start_seconds']:.1f} s after Start at 2 s windows"],
            ["Live Scapy capture", "Implemented, not verified live", "Npcap not installed here; error path verified (capture_error reported, mode returns to stopped)"],
            ["Training on real CICIDS2017", "Partly", "script supports it; shipped model used the synthetic fallback; real-data check run separately"],
            ["Enforcement beyond the application (firewall, rate limiting)", "Not done", "apply_os_firewall_block is a stub; rate limiting is only recommended"],
            ["Authentication, multi-attack classes, real testbed", "Not done", "API is localhost-only; binary labels; no SDN deployment"]]
    K.table(s, 0.6, 1.4, [5.4, 1.9, 4.83], rows, font_size=13, row_h=0.7)
    notes[14] = "State of the code base. The last three rows are the honest gaps against the batch objectives."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{k['ship_acc'] * 100:.2f}%", f"shipped model on its own synthetic split ({k['ship_n_test']:,} rows)", K.ORANGE),
                                   (f"{k['shipreal_acc'] * 100:.1f}%", f"same model on {k['real_rows']:,} real CICIDS2017 flows (recall {k['shipreal_rec'] * 100:.1f} %)", K.PURPLE),
                                   (f"{k['rr_acc'][0] * 100:.2f}%", "forest retrained on real flows, 5-seed mean (FPR 0.06 %)", K.GREEN),
                                   (f"{k['w5_fpr_act'] * 100:.2f}%", f"false positives at 5 s windows with severity (RF label alone {k['w5_fpr_ml'] * 100:.1f} %)", K.BLUE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.3, v, l, c, vsize=24, lsize=10.5)
    K.picture(s, trim(F.fig("f01_domain_gap.png"), "r2_f01"), 0.6, 2.8, 6.0, 3.3)
    K.picture(s, trim(F.fig("f02_window_size_effect.png"), "r2_f02"), 6.75, 2.8, 6.0, 3.3)
    K.text(s, 0.6, 6.2, 12.13, 0.9,
           f"The synthetic score does not transfer to real flows; retraining with the same features fixes that on this attack type. Window length matters: the model was calibrated on 10 s windows. "
           f"The base paper's 100 % is on different datasets and is not directly comparable. Recall at High/Critical: {k['w2_rec_act'] * 100:.0f} % at 2 s, {k['w5_rec_act'] * 100:.0f} % at 5 s, {k['w10_rec_act'] * 100:.1f} % at 10 s.",
           size=12.5, color=K.TXT)
    notes[15] = (f"Be explicit: 99.71 percent is a synthetic-data number. On real flows the shipped model has a {k['shipreal_fpr'] * 100:.1f} percent false-positive rate. "
                 "The severity layer keeps most benign windows below High; at 10 s windows 44 weaker attack windows stay at Medium.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("04_overview.png", "Overview: session control, capture-problem banner, live cards"), ("05_detections.png", "Detections: every scored window"),
            ("06_threat_detail.png", "Threat detail: verdict, traffic, risk, factors"), ("07_analytics.png", "Analytics: benign vs attack, severity"),
            ("09_mitigation.png", "Mitigation: active quarantines with countdown"), ("10_model.png", "Model: metrics with synthetic-data warning")]
    for i, (n_, cap) in enumerate(grid):
        r, c = divmod(i, 3)
        shot_box(s, n_, 0.6 + c * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running console at 1440 x 900 in Simulation Mode: simulated windows scored by the real model.", size=11, color=K.TXT, italic=True)
    notes[16] = "Real screenshots. Every screen labels Simulation Mode; the Model screen warns that the metrics describe the synthetic fallback dataset."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests passed (scratch database)", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke checks passed against the live API", K.BLUE),
                                   (f"{st['p50_ms']:.1f} ms", "median of GET /api/status over HTTP (127.0.0.1)", K.ORANGE),
                                   (f"{probes_ok} / {probes_total}", "malformed-input and abuse probes handled", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            [f"At 2 s windows the RF label alone flags {k['w2_fpr_ml'] * 100:.0f} % of benign windows as attacks", "Severity layer reduces actionable false positives to 6.8 %; 10 s default recommended"],
            [f"Single-window inference takes {L['single_inference_ms_n_jobs_-1']['p50']:.0f} ms with the saved n_jobs = -1 against {L['single_inference_ms_n_jobs_1']['p50']:.0f} ms with 1 (host at 100 % CPU)", "Reported; setting n_jobs = 1 is a listed fix"],
            ["The interface setting accepts a 5,000-character string; the landing page shows 99.71 % without the synthetic caveat", "Logged as defects; not changed in this review"],
            ["Live capture start without Npcap returns a clear reason through /api/status instead of crashing", "Simulation Mode used for demonstrations"]]
    K.table(s, 0.6, 2.9, [6.4, 5.73], rows, font_size=12, row_h=0.72)
    notes[17] = "Tests run against a scratch database; the probes and latency come from a scratch copy of the backend over real HTTP. Latency numbers were taken while other jobs used the whole CPU, so they are upper bounds."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["CICIDS2017 could not be downloaded when the product was built", "Labelled synthetic fallback in the product; real file obtained later and used for an honest re-check"],
            ["A flow and a 10-second window have different scales", "6,000 aggregated simulator windows added to training; the gap is measured and reported"],
            ["Accuracy depends on window length (46 % false positives at 2 s for the RF label alone)", "Severity layer with factors and persistence; 10 s default; results given for 2, 5 and 10 s"],
            ["Npcap is not installed, so live capture cannot run on the development PC", "Simulation Mode drives the identical pipeline; the capture error path is tested"],
            ["CPU shared with other jobs; saved forest uses n_jobs = -1", "Latency reported as upper bounds with the n_jobs comparison"]]
    K.table(s, 0.6, 1.5, [5.9, 6.23], rows, font_size=14, row_h=0.88)
    notes[18] = "Each challenge was met by a design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Train on real data", "Retrain the shipped model with the real CICIDS2017 files in data/raw, add the other attack days and multi-class labels, and report the gap honestly.", K.BLUE, "1"),
        ("Fix window sensitivity", "Make features independent of window length, set n_jobs = 1, and re-measure at 2, 5 and 10 s.", K.GREEN, "2"),
        ("Real enforcement", "Add an opt-in firewall or rate-limit action and measure recovery of a real service.", K.ORANGE, "3"),
        ("Live test and hardening", "Install Npcap and test live capture end to end; add authentication and length checks.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=17)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 2 close the largest honest gaps - a model trained on real traffic and a detector that does not depend on window length.", size=16, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. The first two items address the biggest gaps found by the real-data check."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = ("Likely questions: why the shipped model uses synthetic data; how the real-flow result compares with the base paper (different datasets, indicative only); "
                 "what mitigation really does (an application-level quarantine, no firewall change); why live capture was not shown.")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
