"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared block lists used by documents 9, 10, 12 and 15.

Every number is read from scripts/docs/facts.py (results/metrics.json and results/experiments/*.json) when the blocks are built.
Code listings are read from the repository files at build time, so they are exact copies of what is in 8.ProjectCode.
"""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, TAB
from .refs import CITE as R

K = F.K()
RE, W, L, A, HY = F.REAL, F.WIN, F.LAT, F.API, F.HYB


def pc(x, d=1):
    return f"{x * 100:.{d}f} %"


def src(rel, start, end=None, include_end=False):
    """Text of a repository file from the first line containing `start` up to (not including) the first later line containing `end`."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    a = next(i for i, ln in enumerate(lines) if start in ln)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i]) + (1 if include_end else 0)
    return "\n".join(lines[a:b]).rstrip()


def _w(key, name="ml_only"):
    return W[key][name]


# ---------------------------------------------------------------------------- shared lists
def _objective_rows():
    return [
        ["1. Acquire a benchmark dataset and extract flow features", "Partly",
         f"The training script reads CICIDS2017 CSVs from data/raw and otherwise builds a labelled synthetic fallback, which is what shipped. During documentation the real Friday-DDoS file ({K['real_rows']:,} flows) was obtained and mapped with the product's own preprocessing; the shipped model was not retrained on it."],
        ["2. Capture live traffic and compute the same features in real time", "Implemented, not verified live",
         "Scapy capture, rolling windows and the aggregator use the training schema. Npcap is not installed on the test machine, so only the error path was exercised; the simulator drives the identical pipeline."],
        ["3. Train a classifier to separate DDoS from legitimate traffic", "Achieved after retraining",
         f"Shipped synthetic-trained forest: {pc(K['ship_acc'], 2)} on its own split but {pc(K['shipreal_acc'])} on real flows. Same forest retrained on real flows: {F.mstd(*K['rr_acc'])} % over five seeds."],
        ["4. Adaptive mitigation that rate-limits or blocks sources", "Partly",
         "High and Critical windows quarantine the top three non-protected sources for 40 s (80 s for Critical) with automatic recovery, inside the application. Rate limiting is only recommended; the OS firewall is never touched."],
        ["5. Dashboard of live traffic, detections and mitigation", "Achieved",
         "Nine-page React console plus the original Flask dashboard; polling every 2 s; every screen captured with data."],
        ["6. Evaluate accuracy, false-positive rate and time from detection to mitigation", "Achieved for offline evaluation",
         f"Accuracy and false-positive rate on a synthetic split, on real flows and through the window pipeline at three window lengths; decision latency median {L['detect_to_mitigation_ms']['p50']:.0f} ms on a saturated host. No real attack timeline was measured."],
    ]


def _findings():
    sh, rr = RE["shipped_on_real_all"], RE["real_rf_seed42"]
    b = RE["baselines_seed42"]
    ab = RE["ablation_seed42"]
    return [
        f"**The synthetic-trained model does not transfer.** The shipped forest scores {pc(K['ship_acc'], 2)} accuracy and {pc(K['ship_fpr'], 2)} false positives on its own 4,800-row split, but on the {K['real_rows']:,} real CICIDS2017 DDoS-day flows it scores {pc(K['shipreal_acc'])} accuracy, {pc(K['shipreal_rec'])} recall and {pc(K['shipreal_fpr'])} false positives (ROC-AUC {pc(K['shipreal_auc'])}: the ranking is informative, the 0.5 threshold is not).",
        f"**The same forest trained on real flows is accurate.** With identical features and hyper-parameters, five seeds give {F.mstd(*K['rr_acc'])} % accuracy and {F.mstd(*K['rr_fpr'], d=3)} % false positives; a chronological block split (first 70 % train, last 30 % test) gives {pc(K['blk_acc'], 2)}. This is the same order as the 100 % reported by the base paper [{R['base']}], on different data and with a different protocol.",
        f"**Simple tree models are enough on this data.** On the same real split a decision tree ({pc(b['DecisionTree']['accuracy'], 2)}), the 200-tree forest ({pc(b['RandomForest(200)']['accuracy'], 2)}) and histogram gradient boosting ({pc(b['HistGradientBoosting']['accuracy'], 2)}) are indistinguishable; logistic regression reaches {pc(b['LogisticRegression(scaled)']['accuracy'], 2)} and Gaussian Naive Bayes only {pc(b['GaussianNB']['accuracy'])}. The forest takes {RE['real_rf_per_seed'][0]['train_seconds']:.1f} s to train and its file is {RE['real_rf_model_mb']} MB.",
        f"**Packet and byte counts carry the signal.** Four count-and-byte features alone give {pc(ab['counts_and_bytes_only']['accuracy'], 2)}; sent-direction features alone {pc(ab['sent_only']['accuracy'], 2)}; received-direction features alone fall to {pc(ab['received_only']['accuracy'])} with {pc(ab['received_only']['fpr'])} false positives. The rate features add nothing on flows.",
        f"**Window length decides the false-alarm rate.** The model was calibrated on 10-second windows. On 4,000 simulator windows the forest label alone raises false positives on benign windows of {pc(K['w2_fpr_ml'])} at 2 s, {pc(K['w5_fpr_ml'])} at 5 s and {pc(K['w10_fpr_ml'])} at 10 s (the last figure is flattering, because the simulator generated the training windows).",
        f"**The severity layer removes most false alarms.** Acting only on High or Critical severity cuts those false positives to {pc(K['w2_fpr_act'], 2)} at 2 s and {pc(K['w5_fpr_act'], 2)} at 5 s while 100 % of attack windows still reach High or Critical at both lengths; at 10 s recall is {pc(K['w10_rec_act'], 2)} because 44 weaker attack windows stay at Medium. The distributed-risk score alone is precise but weak: at threshold 0.7 it has 100 % precision and only {pc(W['window_2s']['distributed_risk_ge_0.7_only']['recall'])}, {pc(W['window_5s']['distributed_risk_ge_0.7_only']['recall'])} and {pc(W['window_10s']['distributed_risk_ge_0.7_only']['recall'])} recall at 2, 5 and 10 s.",
        f"**Flow-scale and window-scale rows are different populations.** A forest trained on real flows only labels every simulator window Benign (recall 0 at all three window lengths) although its ROC-AUC on those windows is {pc(RE['real_rf_on_sim_windows']['window_10s']['roc_auc'])}. The product's recipe of adding 6,000 window rows fixes this on windows ({pc(HY['hybrid_on_sim_windows']['window_10s']['accuracy'])} on fresh windows from the same generator) while keeping {pc(HY['mixed_test']['accuracy'], 2)} on the mixed test split.",
        f"**Decision latency is small next to the window.** On a host whose CPU was saturated by other jobs, the time from the finished feature vector to the mitigation decision had a median of {L['detect_to_mitigation_ms']['p50']:.0f} ms (95th percentile {L['detect_to_mitigation_ms']['p95']:.0f} ms), dominated by forest inference: the saved forest has `n_jobs=-1`, which costs {L['single_inference_ms_n_jobs_-1']['p50']:.0f} ms per single window against {L['single_inference_ms_n_jobs_1']['p50']:.0f} ms with `n_jobs=1`. The real delay to a decision is the window length, 10 s by default.",
        f"**The software is tested.** {F.PYTEST_PASSED} pytest tests and {F.SMOKE_PASSED} smoke checks pass; {A['probes_ok']} of {A['probes_total']} malformed-input probes were handled as intended; the REST endpoints answer in a median of {min(r['p50_ms'] for r in A['latency'] if r['method'] == 'GET'):.0f} to {max(r['p50_ms'] for r in A['latency'] if r['method'] == 'GET'):.0f} ms on 127.0.0.1.",
    ]


def _limitations():
    return [
        ("Synthetic training data in the shipped model", f"CICIDS2017 was unreachable when the product was built, so the shipped forest was trained on {F.SHIP['benign_total'] + F.SHIP['attack_total']:,} rows of a labelled synthetic fallback (flows) plus simulator windows. Its {pc(K['ship_acc'], 2)} is a figure about that data, not about real traffic; on real flows it scores {pc(K['shipreal_acc'])}."),
        ("Real-data result covers one attack day", f"The retrained forest was tested on one CICIDS2017 file (Friday afternoon, {K['real_rows']:,} flows). Random 80/20 splits of flows from one capture overlap in time, the block split ({pc(K['blk_acc'], 2)}) is the stricter figure, and CICIDS2017 labels are known to contain errors [{R['engelen']}]. Other attack types and other datasets were not tested."),
        ("Ten features describe a flow, not an attack", "The schema is five counters per direction. On the real flows the model leans on packet and byte counts and sizes; it has no TCP-flag, port, inter-arrival or entropy information, so attacks that look like ordinary volume are out of reach."),
        ("Window length sensitivity", f"The calibration is for 10 s windows. The Simulation Mode default is 5 s and the screenshots were captured at 2 s, where the forest label alone has {pc(K['w2_fpr_ml'])} false positives on benign windows; only the severity layer keeps the acted-on rate at {pc(K['w2_fpr_act'], 2)}."),
        ("Mitigation is an application-level denylist", "Quarantine adds an address to a list inside SentinelFlow for 40 s (80 s for Critical). `apply_os_firewall_block()` is a stub that returns `applied: false`; no packet is dropped anywhere. Rate limiting is only recommended."),
        ("Live capture was not run end to end", "Scapy capture needs Npcap and administrator rights. Neither is available on the test machine; the start request returns 200, the status endpoint reports the real driver error and the mode returns to stopped. All performance numbers come from real flow files and from the simulator."),
        ("Simulator windows are not real attacks", "Flood, carpet-bombing and slow-style windows are generated in software with fixed address pools and sizes. The forest was trained on windows from the same generator, so near-perfect scores on fresh simulator windows say little."),
        ("Landing page headline", f"The landing page shows {pc(K['ship_f1'], 2)} F1 without a caveat; only the Model page carries the 'synthetic training data' warning."),
        ("Inference cost of the saved forest", f"The forest was saved with `n_jobs=-1`, so classifying one window costs a median of {L['single_inference_ms_n_jobs_-1']['p50']:.0f} ms on the loaded test host against {L['single_inference_ms_n_jobs_1']['p50']:.0f} ms with one worker."),
        ("No authentication on the REST API; unvalidated interface name", f"The API binds to 127.0.0.1 only and the React login is a browser-side demo gate. The `interface` setting accepts a 5,000-character string. {A['probes_ok']} of {A['probes_total']} other probes behaved as intended."),
    ]


def _not_measured():
    return [
        ["Live packet capture on a real interface", "Npcap and administrator rights are missing; only the error path was exercised."],
        ["Time from the first attack packet to the first quarantine", "Needs a real attack against a live interface; only the decision latency after a window closes was measured."],
        ["Recovery time of a real service", "Quarantine does not drop traffic, so there is no service to recover."],
        ["Real carpet-bombing traffic", "Only the simulator's carpet style (many destinations, 10-45 attacker addresses) was scored."],
        ["Other CICIDS2017 attack days, CIC-DDoS2023, SDN datasets", "Only the Friday-afternoon DDoS file was obtained."],
        ["Multi-class attack typing, online learning, ensembles", "The product is binary and trained once; the base paper's four voting ensembles and Banzhaf selection were not implemented."],
        ["Behaviour under sustained packet load", "Largest simulator window was 8,966 packets; capture throughput of Scapy at line rate was not measured."],
        ["Usability with real administrators", "No user study; the console was exercised by the team only."],
        ["Security review of the API", "Malformed-input probes only; no authentication, rate limiting or penetration test."],
    ]


# ---------------------------------------------------------------------------- novelty and contributions
def novelty_blocks():
    bp = F.BP
    return [
        H2("What the base paper does"),
        P(f"The base paper [{R['base']}] proposes a resource-aware ensemble framework for DDoS detection in software-defined networks. Its feature selection combines Random Forest importance with the Banzhaf Power Index; it benchmarks seven classifiers (XGBoost, Random Forest, Gradient Boosting, SVM, kNN, AdaBoost, Naive Bayes) and builds four hard-voting ensembles. "
          f"It is evaluated on {bp['datasets']}. {bp['result'].capitalize()}, and it profiles training time, inference time, memory and model size: {bp['resource']}."),
        P(f"The paper names its own next steps: {bp['future']}. Detection, not mitigation, is what it delivers; mitigation actions such as throttling or blackholing are described as what a deployed sidecar could trigger."),
        H2("What SentinelFlow adds"),
        TAB("SentinelFlow against the base paper", ["Aspect", "Base paper", "SentinelFlow"],
            [["Goal", "Offline detection accuracy and resource cost", "Closed loop: detect, assess, act, recover, record"],
             ["Setting", "SDN controller-adjacent sidecar (proposed)", "Commodity host: Scapy or simulator -> Flask -> SQLite -> React"],
             ["Data", "SDN flows (104,345 rows), CIC-DDoS2023 (1.75 M rows)", f"Synthetic fallback (shipped); CICIDS2017 DDoS-day flows ({K['real_rows']:,}) for the real-data evaluation"],
             ["Features", "Banzhaf-selected subset of 23 / 47 columns", "Ten fixed counters shared by flow rows and window rows"],
             ["Classifier", "Four voting ensembles of seven learners", "One 200-tree Random Forest; five classifiers compared on real flows"],
             ["Reported result", "100 % accuracy, precision, recall, F1 on both datasets", f"{F.mstd(*K['rr_acc'])} % on real flows (retrained); {pc(K['shipreal_acc'])} for the shipped synthetic-trained model"],
             ["Resource profile", "Training time, inference time, memory, model size", f"Training {RE['real_rf_per_seed'][0]['train_seconds']:.1f} s, model {RE['real_rf_model_mb']} MB, decision latency median {L['detect_to_mitigation_ms']['p50']:.0f} ms (loaded host)"],
             ["Mitigation", "Future work", "Temporary application-level quarantine with automatic recovery; rate limiting recommended"],
             ["Distributed attacks", "Not modelled separately", "Distributed-risk score (sources, destinations, rate, baseline) for carpet-bombing patterns"],
             ["Explainability", "Feature selection only", "Severity score with the list of contributing factors shown beside every verdict"]],
            widths=[1.1, 2.4, 2.9], align=["l", "l", "l"], size=9.5),
        P("The datasets, protocols and hardware differ, so the table compares designs, not scores."),
        H2("What is new here and what is not"),
        B("**New in this project (relative to the base paper):** the closed loop from detection to quarantine to recovery with measured decision latency; a transparent distributed-risk layer aimed at carpet-bombing patterns; an explainable severity score that, in the measurements, removes most false alarms; a Simulation Mode that drives the identical pipeline without sending traffic; one feature schema shared by flow rows and window rows, with a measured flow-to-window scale gap; and an evaluation that separates synthetic from real data and reports the difference.",
          f"**Not new:** the Random Forest [{R['breiman']}], the CICIDS2017 dataset [{R['cicids']}], Scapy, Flask and SQLite, and the use of ensembles for DDoS detection.",
          "**Not carried over from the base paper:** Banzhaf-index feature selection and the voting ensembles. A comparison of single classifiers on real flows is reported instead, and the ten-feature schema is too small for feature selection to matter."),
        P(f"Related work points the same way. The carpet-bombing paper of Swileh et al. [{R['carpet']}] replaces supervised training by retrieval and a large language model (about 2 s per request), which avoids the retraining and flow-to-window calibration problems measured here but needs an external model service. "
          f"Engelen et al. [{R['engelen']}] warn that CICIDS2017 results need care, which is why the real-data figures here are stated with their limits."),
    ]


def _contributions():
    return [
        ("A closed detection-to-recovery loop on one machine.", f"Windows from Scapy or the simulator pass through classification, risk, severity and an action that is stored, shown and, for quarantines, reversed automatically after 40 s (80 s for Critical). The loop was exercised end to end through the REST API and the simulator ({F.PYTEST_PASSED} tests, {F.SMOKE_PASSED} smoke checks)."),
        ("A transparent distributed-risk layer.", f"A 0-1 score from source diversity, destination diversity, packet-rate pressure and deviation from a 12-window baseline (weights 0.30, 0.30, 0.25, 0.15). Measured alone it is precise but weak (recall {pc(W['window_5s']['distributed_risk_ge_0.7_only']['recall'])} at 5 s windows), so it is used as one input of the severity score."),
        ("An explainable severity score.", f"Four levels with the list of contributing factors. Acting only on High or Critical cuts false positives on benign windows from {pc(K['w5_fpr_ml'])} to {pc(K['w5_fpr_act'], 2)} at 5 s windows with 100 % attack recall."),
        ("A safe Simulation Mode and a shared feature schema.", "Flood, carpet-bombing and slow-style windows are generated in software and scored by the same code as live windows. Flow rows and window rows share ten features, which also exposes the flow-to-window scale gap."),
        ("A real-data evaluation that exposes the synthetic-data gap.", f"On {K['real_rows']:,} real CICIDS2017 flows the shipped model scores {pc(K['shipreal_acc'])}, a retrained forest {F.mstd(*K['rr_acc'])} %; five classifiers, a feature-group ablation and a chronological split are reported."),
        ("A tested, documented product.", f"A Flask API with twelve endpoints, a nine-page React console, a four-table SQLite history, {F.PYTEST_PASSED} automated tests and a malformed-input probe battery ({A['probes_ok']} of {A['probes_total']} handled as intended)."),
    ]


def contribution_blocks():
    out = [P("The project makes six contributions. Each is stated with the measurement that supports it; none claims more than the measurements show.")]
    out.append(N(*[f"**{t}** {d}" for t, d in _contributions()]))
    out.append(P("What the contributions do not include: a new learning algorithm, a new dataset, enforcement outside the application, or evidence of detection quality on live attacks."))
    return out


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        H2("In scope"),
        B("Detection of volumetric and distributed DDoS traffic as a binary decision (Benign or Attack) on rolling windows of 2 to 120 s (default 10 s).",
          "Live capture with Scapy on a chosen interface, and a Simulation Mode that generates flood, carpet-bombing and slow-style windows in software.",
          "Ten shared flow features per window, a 200-tree Random Forest, a distributed-risk score, an explainable four-level severity score and persistence across consecutive windows.",
          "Temporary application-level quarantine of the top three non-protected sources (40 s, doubled for Critical) with automatic recovery, and rate-limit recommendations for Medium severity.",
          "SQLite history of detections, quarantines, health samples and settings; host health from psutil; twelve JSON endpoints; a nine-page React console and the original Flask dashboard.",
          "Offline training and evaluation with CICIDS2017-style flow CSVs, including the real-data evaluation reported in Chapter 8."),
        H2("Out of scope"),
        B("Enforcement outside the application: no operating-system firewall rule, router, switch or SDN controller is changed.",
          "Attack generation of any kind: Simulation Mode builds packet records in memory and sends nothing.",
          "Multi-class attack typing, online learning, ensembles, Banzhaf feature selection and deep models.",
          "Encrypted-payload inspection, application-layer (HTTP) analysis and per-protocol rate limiting.",
          "User accounts, roles and multi-tenant operation: the React login is a browser-side demo gate and the API is localhost-only.",
          "Distributed deployment, high-availability storage and capture at data-centre line rates."),
        H2("Deployment boundary"),
        TAB("Where the system is meant to run", ["Item", "Boundary"],
            [["Host", "One Windows or Linux machine, Python 3.11 or 3.12, CPU only (measured on an Intel Core i5-12500, 15.7 GB RAM)"],
             ["Network access", "Passive sniffing of one interface; needs Npcap and administrator rights on Windows"],
             ["Servers", "Flask on 127.0.0.1:8415, Vite development server on 5415"],
             ["Storage", "One SQLite file, joblib model, JSON and PNG results"],
             ["Users", "One administrator or analyst at a time"]],
            widths=[1.4, 5.0], align=["l", "l"], size=10),
    ]


def assumption_blocks():
    return [
        P("The design and the measurements rest on the following assumptions. Where an assumption could not be checked it is marked."),
        B("CICIDS2017 forward direction maps to the sent features and backward direction to the received features; rates are counts divided by flow duration.",
          "For live windows, a packet whose destination is a local interface address counts as received, one whose source is local counts as sent, and packets between two non-local addresses count as received (the sensor sees them arrive).",
          "The default window of 10 s and the default quarantine of 40 s are engineering choices, not values derived from data; both are configurable (2-120 s and 5-3600 s).",
          "Loopback, the machine's own addresses and 192.168.1.20 (the simulator's local host) are protected and never quarantined.",
          "An address that is quarantined is not blocked on the network, so later windows can still contain its packets and re-quarantine it after expiry.",
          "The simulator's traffic styles are a reasonable stand-in for the three behaviours it names (unchecked against real captures).",
          f"The real-data evaluation assumes that the labels of the CICIDS2017 Friday-afternoon file are correct enough to score against, although errors in the dataset are documented [{R['engelen']}].",
          "Latency figures assume the load of the test host (other jobs kept the CPU at 100 %), so they are upper bounds."),
    ]


def limitation_blocks():
    out = [P("Each limitation below was found while building or measuring the system, and each is stated with the number that shows it."),
           N(*[f"**{t}.** {d}" for t, d in _limitations()]),
           P(f"The first two figures show the limitation that matters most. Figure 1 compares the shipped model on its own synthetic split with the same model on real flows and with the forest retrained on real flows. "
             f"Figure 2 shows how the false-positive rate depends on the window length, with and without the severity layer."),
           FIG(F.fig("f01_domain_gap.png"), "Accuracy, recall and false-positive rate: shipped model on synthetic data and on real flows, and the forest retrained on real flows.", 5.8),
           FIG(F.fig("f02_window_size_effect.png"), "False-positive rate on benign windows and attack recall at 2, 5 and 10 s windows, forest label alone against High or Critical severity.", 5.8)]
    return out


def not_measured_blocks():
    return [P("Gaps are listed instead of being filled with plausible numbers. Each row says why the quantity is missing."),
            TAB("Quantities that were not measured", ["Quantity", "Reason"], _not_measured(), widths=[2.6, 3.8], align=["l", "l"], size=10)]


# ---------------------------------------------------------------------------- code walk-throughs
def walkthrough_blocks():
    return [
        H2("The shared pipeline: process_window()"),
        P("`process_window()` in `app.py` is the one function every window passes through, whether it came from Scapy or from the simulator. It returns an error record early if the capture engine reported a failure or if the feature vector is invalid, "
          "then computes the distributed risk against the rolling baseline, updates the persistence counter, asks `severity.assess_severity()` for a level, lets the mitigation manager decide, builds the record and stores it."),
        CODE(src("app.py", "def process_window", "    return record", True), 7.6),
        P("Three details matter. The baseline is updated after the risk is computed, so a window is never compared with itself. The persistence counter counts consecutive windows that the forest calls Attack or whose risk is at least 0.7, and it resets to zero otherwise. "
          "A failure to store the row does not lose the verdict: the record is returned with `id` set to `None`."),
        H2("Aggregating packets into the schema"),
        P("`aggregate_packets()` turns a list of packet summaries into the ten features and a context dictionary. The orientation rule decides which direction a packet counts in: outbound from a local address is sent, everything else is received."),
        CODE(src("monitoring/traffic_aggregator.py", "    for pkt in packets:", "    features = {"), 7.6),
        P("Malformed packet summaries are skipped, so one bad packet cannot abort a window. The same function serves live capture and the simulator, which is why both paths produce identical features for the same traffic."),
        H2("Distributed-risk score"),
        P("The score combines four components, each capped at 1: unique sources (30 saturates), unique destinations (15 saturates), packet rate (1,500 packets/s saturates) and the deviation of the packet rate from the rolling baseline. The weights are 0.30, 0.30, 0.25 and 0.15, "
          "and the explanation string names the pattern, including 'possible carpet-bombing pattern' when many destinations are seen."),
        CODE(src("security/distributed_analysis.py", "    # Component 1", "    spread = ", False), 7.6),
        H2("Severity score"),
        P("Severity is an additive score with a reason attached to every addition. A Benign window can add at most a small residual and is capped at 45, so it can never be High or Critical. The thresholds are 28 (Medium), 50 (High) and 70 (Critical)."),
        CODE(src("security/severity.py", "    score = 0.0", "    return {", False), 7.6),
        H2("Mitigation decision and quarantine"),
        P("`decide()` chooses an action from the severity. High and Critical windows quarantine up to three of the most active sources that are not protected addresses; Critical doubles the duration. Medium returns a rate-limit recommendation and Low returns monitor. "
          "`quarantine()` ignores an address that is already quarantined, and `expire_due()` runs on every decision and every status query, marking expired entries as recovered in SQLite."),
        CODE(src("security/mitigation.py", "    def decide", "    def get_active", False), 7.6),
        H2("Training the forest and the window augmentation"),
        P("`train_model.py` generates window-scale rows with the same generator that Simulation Mode uses and aggregates them through the real aggregator, so that the forest sees both flow-scale and window-scale values. The held-out split mixes both kinds of rows."),
        CODE(src("ml/train_model.py", "    sim = TrafficSimulator", "    X_aug = ", False), 7.6),
        CODE(src("ml/train_model.py", "    X_train, X_test, y_train, y_test", "    clf.fit(X_train, y_train)", True), 7.6),
        P(f"The measurements in Chapter 8 show the consequence of this design: the augmentation makes the forest accurate on windows from the simulator's own generator and, when real flows are added, keeps it accurate on both ({pc(HY['mixed_test']['accuracy'], 2)} on the mixed split of {HY['rows_after_cap']:,} rows)."),
    ]


# ---------------------------------------------------------------------------- decisions
def decision_blocks():
    return [
        P("Each decision is given with the reason it was taken and what the measurements say about it."),
        H2("4.1 Random Forest as the classifier"),
        P(f"The batch abstract names a Random Forest. On the real flows it is as accurate as a decision tree and histogram gradient boosting ({pc(RE['baselines_seed42']['RandomForest(200)']['accuracy'], 2)}, {pc(RE['baselines_seed42']['DecisionTree']['accuracy'], 2)} and {pc(RE['baselines_seed42']['HistGradientBoosting']['accuracy'], 2)}), trains in {RE['baselines_seed42']['RandomForest(200)']['train_seconds']:.1f} s on {int(K['real_rows'] * 0.8):,} rows and exposes feature importances; "
          f"Gaussian Naive Bayes ({pc(RE['baselines_seed42']['GaussianNB']['accuracy'])}) and logistic regression ({pc(RE['baselines_seed42']['LogisticRegression(scaled)']['accuracy'], 2)}) are worse. The cost is size: the forest file is {RE['real_rf_model_mb']} MB for the real-data model, and a single tree would be smaller and faster for the same accuracy on this data."),
        H2("4.2 Ten counters as the feature schema"),
        P("CICIDS2017 flow rows and live packet windows must produce the same features. Packet and byte counts per direction, their rates and their averages can be computed from both with no loss. "
          f"The ablation shows that four count-and-byte features give {pc(RE['ablation_seed42']['counts_and_bytes_only']['accuracy'], 2)} on real flows, so the schema is sufficient for this dataset; it is also why the schema cannot describe attacks that look like ordinary volume."),
        H2("4.3 Rolling windows instead of single flows"),
        P("A live sensor sees packets, not completed flows, and a flood is visible as a rate over time. Windows (default 10 s) give a stable rate and a count of distinct sources and destinations. "
          f"The price is the flow-to-window scale gap: a forest trained on real flows alone labels every simulator window Benign, and the product's answer is to add 6,000 window rows to training. Window length then becomes a calibration parameter: {pc(K['w2_fpr_ml'])} false positives at 2 s against {pc(K['w10_fpr_ml'])} at 10 s for the forest label alone."),
        H2("4.4 A rule layer on top of the forest"),
        P(f"The forest says Attack or Benign; the rule layer says how distributed the traffic is and how severe the situation is, with reasons. Rules were chosen because every verdict can be explained to an administrator and every threshold can be read in the code. "
          f"The measurements justify the layer: acting on High or Critical severity instead of the forest label cut benign-window false positives from {pc(K['w5_fpr_ml'])} to {pc(K['w5_fpr_act'], 2)} at 5 s. The thresholds are hand-set, not learned, and were not tuned on real data."),
        H2("4.5 Application-level quarantine instead of firewall rules"),
        P("A mistaken firewall rule can cut off the administrator or a legitimate service, and changing it needs elevated rights. Quarantine inside the application is reversible by design: it expires by itself and is never applied to loopback or local addresses. "
          "The trade-off is that nothing is actually blocked, which the documents state wherever mitigation is mentioned. The stub `apply_os_firewall_block()` marks where an explicit opt-in could be added."),
        H2("4.6 A Simulation Mode"),
        P("Live capture needs Npcap, administrator rights and real traffic. The simulator builds packet records in memory, so the pipeline can be demonstrated, tested and screenshotted anywhere, and it never sends traffic. "
          "Its disadvantage is that it generates the same kinds of windows the model was trained on, so scores on simulator windows are flattering and are reported as such."),
        H2("4.7 SQLite for history"),
        P(f"One file, no server, and enough for a single administrator: the API reads 500 detections in a median of {next(r['p50_ms'] for r in A['latency'] if r['path'] == '/api/detections?limit=500'):.0f} ms. Each write opens its own connection under a lock, which is simple and safe but adds latency on a busy disk (the mitigation step, which writes the quarantine rows, was the second-largest part of the decision time in the measurements). A server database would be needed for several writers."),
        H2("4.8 Flask on a host instead of an SDN controller"),
        P(f"The base paper [{R['base']}] targets SDN, where a controller can install rules. A student machine has no SDN switch, so SentinelFlow runs beside the traffic it watches. This keeps it runnable anywhere and testable, and it is why mitigation is limited to the application; the same pipeline could be fed by flow statistics from a controller."),
        H2("4.9 A React console with polling"),
        P("The console polls `/api/status` every two seconds and the detection endpoints on the pages that need them. Polling is simple and stateless; the measured endpoint latencies (single-digit to low double-digit milliseconds) leave room for it. Server-sent events or WebSockets would remove the delay of up to two seconds."),
        H2("4.10 Settings kept in memory"),
        P("Window length and quarantine duration are validated (2-120 s and 5-3600 s) and held in memory; the `settings` table exists but is not used by the API, so a restart returns the defaults. Persisting the two values is a small change that was not made."),
    ]


# ---------------------------------------------------------------------------- conclusion
def _chapter9_core():
    return [
        H2("9.1 Summary of the work"),
        P(f"The batch asked for a framework that detects DDoS traffic in real time and applies adaptive mitigation without blocking legitimate users. The project delivered {F.PRODUCT}: Scapy or simulated traffic windows, ten flow features, a 200-tree Random Forest, an explainable distributed-risk and severity layer, "
          f"temporary quarantine with automatic recovery, a SQLite history, twelve REST endpoints and a nine-page React console, backed by {F.PYTEST_PASSED} passing tests and {F.SMOKE_PASSED} passing smoke checks. It follows the base paper [{R['base']}] and adds the closed detection-to-mitigation loop that the paper leaves as future work."),
        P(f"In the documentation phase the product was evaluated more strictly than it had been built. The shipped model, trained on a synthetic fallback, scores {pc(K['ship_acc'], 2)} on its own split but {pc(K['shipreal_acc'])} on {K['real_rows']:,} real CICIDS2017 DDoS-day flows; the same forest retrained on real flows reaches {F.mstd(*K['rr_acc'])} %. "
          "The two layers must be read separately: the engineering (pipeline, API, console, tests) works as designed; the shipped model's headline figure does not describe real traffic."),
        H2("9.2 Objectives achieved and not achieved"),
        TAB("Batch objectives against the outcome", ["Objective", "Status", "Evidence"], _objective_rows(), widths=[1.9, 1.0, 3.7], align=["l", "c", "l"], size=9.5),
        P("The statuses are strict. 'Partly' means a simpler version of the step exists; 'Implemented, not verified live' means the code exists and its failure path was tested but live capture was not possible; nothing is claimed beyond the table."),
        H2("9.3 Key findings"),
        N(*_findings()),
        P("Figure 9.1 and Figure 9.2 summarise the two findings that most change how the system should be read: the gap between synthetic and real data, and the effect of window length with and without the severity layer."),
        FIG(F.fig("f01_domain_gap.png"), "Accuracy, recall and false-positive rate: shipped model on synthetic data and on real flows, and the forest retrained on real flows.", 5.6),
        FIG(F.fig("f02_window_size_effect.png"), "False-positive rate on benign windows and attack recall at 2, 5 and 10 s windows.", 5.6),
        H2("9.4 Practical applications"),
        P("SentinelFlow is a teaching and prototyping tool for network-security courses and small labs: it shows the whole path from packets to a verdict, an explanation and a reversible action; it provides a safe simulator for demonstrations; and it is a test bed for the evaluation mistakes the report exposes "
          "(synthetic data, window-length calibration, forests saved with a parallel setting). It is not a replacement for a firewall, a scrubbing service or a commercial intrusion-prevention system, and it must be retrained on real captures before any operational use."),
        H2("9.5 Known limitations"),
        P("The limitations are listed in full in Chapter 1, Chapter 8 and the Scope and Limitations document. The ones that matter most for reading the results are:"),
        B(*[f"**{t}.**" for t, _ in _limitations()[:6]]),
    ]


def _strip(blocks, drop_prefix=None):
    """Chapter blocks without their chapter numbers on H2 headings (for the shared chapter-document text)."""
    out = []
    for b in blocks:
        if b[0] == "h2":
            if drop_prefix and b[1].startswith(drop_prefix):
                continue
            out.append(("h2", b[1].split(" ", 1)[1]))
        else:
            out.append(b)
    return out


def conclusion_blocks():
    core = _strip(_chapter9_core(), None)
    # in the chapter document the limitations are written out in full
    i = next(n for n, b in enumerate(core) if b[0] == "h2" and b[1] == "Known limitations")
    return core[:i] + [core[i], N(*[f"**{t}.** {d}" for t, d in _limitations()])]


def chapter9_blocks():
    core = _chapter9_core()
    out = []
    for b in core:
        if b[0] == "p" and b[1].startswith("Figure 9.1"):
            out.append(P("The two figures below summarise the findings that most change how the system should be read: the gap between synthetic and real data, and the effect of window length with and without the severity layer."))
        else:
            out.append(b)
    return [H1("9. CONCLUSION")] + out


# ---------------------------------------------------------------------------- chapter 10
def _future_improvements():
    return [
        f"**Retrain on real data and ship that model.** Place the CICIDS2017 CSVs in `data/raw` (the training script already uses them) and add CIC-DDoS2023 and an SDN flow dataset as the base paper does, so that the shipped forest is not synthetic. The real-flow result ({F.mstd(*K['rr_acc'])} %) shows the pipeline is ready; what is missing is the artefact and a split that respects time.",
        f"**Calibrate for the window length.** Train with window rows built at the configured length (or at several lengths), store the length in the model metadata and refuse or warn when the console runs with a different one; at 2 s the forest label alone gave {pc(K['w2_fpr_ml'])} false positives on benign windows.",
        f"**Fix the inference setting.** Save the forest with `n_jobs=1` (or set it at load time): single-window inference falls from {L['single_inference_ms_n_jobs_-1']['p50']:.0f} ms to {L['single_inference_ms_n_jobs_1']['p50']:.0f} ms on the loaded test host, which removes the largest part of the decision time.",
        "**Make the landing page honest.** Show the synthetic warning wherever the headline metric appears, and show the real-data figures once the model is retrained.",
        "**Persist settings and validate every field.** Use the existing `settings` table for window length and quarantine duration, and reject over-long `interface` values.",
        "**Learn the severity thresholds.** Replace the hand-set weights and cut-offs by values tuned on labelled windows, keeping the factor list so that every verdict stays explainable.",
    ]


def _future_features():
    return [
        "**Richer features:** entropy of destination and source addresses per window, TCP flag rates (SYN, ACK, RST), protocol shares, inter-arrival statistics and per-destination packet counts for a sharper carpet-bombing signal. The aggregator already collects protocol and top-destination context that the model does not yet use.",
        "**Multi-class typing:** classify SYN flood, UDP flood, HTTP flood and carpet bombing so that the recommended action can differ (the base paper lists multi-class detection as future work as well).",
        f"**Ensembles and feature selection from the base paper [{R['base']}]:** voting ensembles and Banzhaf-index selection become useful once the feature set is larger than ten.",
        "**Online learning:** update the model from confirmed windows, with a guard against an attacker poisoning the training stream.",
        "**Notifications and export:** e-mail or chat alerts on High and Critical windows and a CSV or PDF export of the detection history.",
        "**Authentication and roles:** replace the browser-side demo gate by server-side accounts and protect the REST API before it is bound to anything other than 127.0.0.1.",
    ]


def _future_scale():
    return [
        "**Live testing:** install Npcap, run SentinelFlow as administrator against a lab network with a traffic generator under the supervision of the department, and measure time from the first attack packet to the first quarantine.",
        "**OS-level enforcement with explicit opt-in:** implement `apply_os_firewall_block()` for Windows Firewall or iptables behind a confirmation setting, a protected-address list and an automatic rollback, so that the safe default stays unchanged.",
        f"**SDN integration:** feed flow statistics from an SDN controller instead of Scapy windows and install throttling or blackhole rules through the controller, as the base paper [{R['base']}] proposes for a sidecar.",
        "**Deployment:** package the API and the console in the existing Docker image with a production server, add rotation of the SQLite history or a server database, and move polling to server-sent events.",
        "**Scale:** measure capture throughput at line rate, move aggregation to a compiled or kernel-assisted capture path, and run several sensors that report to one console.",
    ]


def _future_research():
    return [
        f"**Transfer between datasets and window lengths:** the flow-to-window gap measured here suggests studying domain adaptation between flow-level training data and window-level sensors, and testing on CIC-DDoS2023 and SDN data as in the base paper.",
        f"**Retrieval and language-model detection:** the carpet-bombing paper [{R['carpet']}] avoids retraining by retrieval; comparing its accuracy, cost (about 2 s per request) and robustness with a calibrated forest on the same traffic is an open question.",
        f"**Dataset quality:** repeat the evaluation on a relabelled CICIDS2017 [{R['engelen']}] and on captures made by the team.",
        "**False-positive cost:** quantify the harm of quarantining a legitimate source, for example by replaying benign traffic with known senders and counting wrongly quarantined addresses.",
        f"**Adversarial behaviour:** test evasion by low-rate or slowly ramping floods and by spoofed sources, against which a source-based quarantine is weak (see the taxonomy of Mirkovic and Reiher [{R['mirkovic']}]).",
    ]


def _chapter10_core():
    return [
        H2("10.1 Improvements to the existing system"),
        P("The improvements below follow directly from the measurements; the first three would change the headline results."),
        N(*_future_improvements()),
        H2("10.2 Additional features"),
        B(*_future_features()),
        H2("10.3 Scalability and deployment"),
        B(*_future_scale()),
        H2("10.4 Further research"),
        B(*_future_research()),
    ]


def future_blocks():
    return _strip(_chapter10_core())


def chapter10_blocks():
    return [H1("10. FUTURE SCOPE")] + _chapter10_core()
