"""Chapter 6: Methodology and Software Implementation for SentinelFlow.

methodology_blocks()  - document 9 (H2/H3 only, renumbered by build_docs.renum)
application_blocks()  - document 12 (H2/H3 only)
blocks()              - the report chapter (H1 + both parts, numbered 6.1 ... by renum)
"""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import CITE as R


def _ref(*keys):
    return ", ".join(f"[{R[k]}]" for k in keys)


def _pc(x, d=2):
    return f"{x * 100:.{d}f} %"


def methodology_blocks():
    k = F.K()
    rl = F.REAL
    s = F.SHIP
    b = []
    b += [H2("Overall Methodology"),
          P("The method has an offline half and an online half that share one feature schema. Offline, labelled network flows are cleaned, mapped to ten window-style features, and used to train a Random Forest; the model, its feature list "
            "and its evaluation are written to disk. Online, a stream of packets is cut into fixed windows, each window is reduced to the same ten features plus some context, and the stored forest classifies it. "
            "A rule layer then measures how distributed the traffic is, a severity engine combines all evidence into one of four levels with a list of reasons, and a policy table turns the level into an action. "
            "The ten features are the contract between the halves: `ml/features.py` defines them once, training and inference import them from there, and every prediction validates names, order and value ranges."),
          N("**Acquire and map flows** (offline): read CICIDS2017-style CSV rows or build the synthetic fallback; normalise column names; drop infinite and missing values; map forward packets and bytes to *sent* and backward ones to *received*; derive rates and averages.",
            "**Add window-scale rows** (offline): generate 6,000 packet-level windows with the simulator generator and aggregate them through the real monitoring code, so that the forest also sees feature values of window size.",
            "**Train and evaluate** (offline): stratified 80/20 split, Random Forest with 200 trees, balanced class weights and seed 42; write metrics, confusion matrix, ROC curve and feature importance.",
            "**Capture and aggregate** (online): Scapy `sniff()` for one window (or simulator packets); count packets and bytes by direction; compute rates and averages; collect distinct sources, destinations, protocol shares and the top sources.",
            "**Classify**: validate the ten values, run the forest, return Attack or Benign with the probability of the predicted class.",
            "**Assess**: compute the distributed-risk score against a twelve-window baseline, update the persistence counter, compute the severity score and its factor list.",
            "**Act and record**: quarantine, recommend or monitor; store the detection with its full detail; let quarantines expire and mark them recovered."),
          ]
    b += [H2("Dataset"),
          H3("The shipped training data"),
          P("The product's training script looks for CICIDS2017 CSV files in `data/raw/` and, if it finds none and the download attempts fail, builds a labelled synthetic fallback and records that fact in the metadata. "
            f"That is what happened when the product was built, so the shipped model (trained on {s['train_samples'] + s['test_samples']:,} rows) is **synthetic-trained**: "
            "9,000 benign and 9,000 attack synthetic flows with the raw CICIDS2017 columns Flow Duration, Total Fwd Packets, Total Backward Packets and the two Total Length columns, plus 3,000 benign and 3,000 attack aggregated windows. "
            "Synthetic benign flows have a log-normal duration (median 0.4 s) and 1 to 39 packets per direction; synthetic attack flows are flood-like (200 to 2,499 forward packets, almost no reply), carpet-like (80 to 599) or slow (30 to 199 forward packets with longer duration). "
            f"The metrics the application displays ({_pc(s['accuracy'])} accuracy on {s['test_samples']:,} held-out rows) describe this synthetic mixture and are labelled so on the Model screen."),
          H3("The real data used for the real-data check"),
          P(f"To measure what the synthetic training cost, the real Friday-Afternoon-DDoS file of CICIDS2017 [{R['cicids']}] was obtained from a public Hugging Face mirror (`c01dsnap/CIC-IDS2017`, the MachineLearningCSV release; the dataset card carries the licence field *other* and asks users to cite the dataset paper). "
            f"It holds {rl['rows']:,} labelled flows: {rl['label_counts']['BENIGN']:,} benign and {rl['label_counts']['DDoS']:,} DDoS. It was mapped to the ten features with the product's own `map_to_common_schema`, so the experiment tests exactly the code path that a real training run would use. "
            "The file is 77 MB and is not stored in the repository. Two cautions apply: the file contains one attack family (the DDoS day), and CICIDS2017 is known to contain labelling and flow-construction problems"
            f" {_ref('engelen')}, so even a high score on it is a statement about this file, not about networks in general."),
          ]
    b += [H2("Preprocessing"),
          P("Preprocessing is in `ml/preprocessing.py`. Column names are lower-cased, trimmed and snake-cased so that ` Flow Duration` and `Flow Duration` match; infinite values become missing and rows that are entirely empty are dropped. "
            "Labels are normalised: *BENIGN*, *normal* and *0* mean benign, everything else attack. The mapping to the schema is: sent packets and bytes from the forward columns, received from the backward columns, rates as counts divided by the flow duration in seconds "
            "(duration floored at one microsecond and capped at 3,600 s), and averages as bytes divided by packets, zero when there are no packets. Remaining missing values become zero. "
            "The training script subsamples to 120,000 rows if a very large dataset is supplied. No scaling is applied: tree ensembles do not need it, and leaving the units alone keeps the features equal to what the live aggregator produces."),
          P("At run time the aggregator (`monitoring/traffic_aggregator.py`) does the same mapping from packets. A packet whose source is a local interface address and whose destination is not local counts as *sent*; every other packet counts as *received* "
            "(destined to this host, loopback, or merely observed in transit). Each window also yields context that the model does not see: distinct sources and destinations, packets per source and destination, protocol shares and the five busiest sources and destinations."),
          ]
    imp, rimp = F.IMP, rl["real_rf_importance"]
    meaning = {"received_packets": "packets in the *received* direction", "received_bytes": "bytes in the received direction",
               "received_packets_per_second": "received packets / window seconds", "received_bytes_per_second": "received bytes / window seconds",
               "average_received_packet_size": "received bytes / received packets (0 if none)", "sent_packets": "packets in the *sent* direction",
               "sent_bytes": "bytes in the sent direction", "sent_packets_per_second": "sent packets / window seconds",
               "sent_bytes_per_second": "sent bytes / window seconds", "average_sent_packet_size": "sent bytes / sent packets (0 if none)"}
    frows = [[c, meaning[c], f"{imp[c]:.3f}", f"{rimp[c]:.3f}"] for c in F.FEATURES]
    b += [TAB("The ten features, their definition and the importance each forest gives them", ["Feature", "Definition", "Shipped forest", "Forest on real flows"], frows,
              widths=[2.3, 2.5, 0.9, 0.9], align=["l", "l", "c", "c"], size=9.5),
          P("Two observations follow from the table. The shipped forest spreads its weight over packet counts, rates and sizes in both directions, which fits a synthetic world in which attacks are defined by volume. "
            "The forest trained on real flows leans on the average packet sizes and on the sent-direction counts: in the DDoS day, the attack flows differ from benign flows mostly in how many packets and bytes the initiator sends and how large they are, "
            "and received-direction rates add little. Both forests ignore any field that is not among the ten (flags, inter-arrival times, ports, flow duration beyond the rates), which is a deliberate simplification: the same ten numbers can be computed from a ten-second window of raw packets, and many CICIDS2017 fields cannot."),
          ]
    rows = []
    for n, d in rl["baselines_seed42"].items():
        rows.append([n, _pc(d["accuracy"]), _pc(d["f1"]), _pc(d["fpr"]), f"{d['train_seconds']:.2f}"])
    b += [H2("Algorithm Choice and Justification"),
          P(f"The base paper evaluates seven classifiers and four voting ensembles with a Banzhaf-index feature selection and reports 100 % on both of its datasets, with clear resource differences: its SVM-containing ensembles needed over 4,000 s to train on the SDN data and its kNN ensemble over 150 s to classify the SDN test set [{R['base']}]. "
            "SentinelFlow keeps one classifier, the Random Forest [" + str(R['breiman']) + "], for four reasons. (1) The base paper itself finds tree-based learners strongest and the lightest ensemble the best fit for real-time use. "
            "(2) A forest handles features of very different scales and heavy-tailed distributions (packet counts from 1 to thousands) without scaling. (3) It gives a probability and a feature-importance ranking, both of which the console shows. "
            "(4) It is quick to train and small enough to ship (2.74 MB). Feature selection was not implemented: with only ten features there is little to select, and the ablation below shows that the five *sent* features alone carry almost all the signal."),
          P("The choice was checked, not assumed. Five classifiers were trained on the same real split (seed 42, 20 % test) after the product was built; the comparison is Table below and Figure below."),
          TAB("Classifiers on the real CICIDS2017 DDoS-day flows (same split)", ["Classifier", "Accuracy", "F1", "False-positive rate", "Training time (s)"], rows,
              widths=[2.2, 1.0, 1.0, 1.3, 1.1], align=["l", "c", "c", "c", "c"], size=10),
          FIG(F.fig("f03_classifier_comparison.png"), "Classifier comparison on real flows: accuracy, F1 and false-positive rate (left) and training time (right).", 5.8),
          P("Three tree-based learners are indistinguishable at about 99.9 % on this file; Gaussian Naive Bayes fails (its independence assumption does not suit correlated counts) and scaled logistic regression is clearly worse. "
            f"The smaller 2025 study of Rahman reports the same ordering on a CIC sample, with SVM at 0.971, a decision tree at 0.827 and logistic regression at 0.593 {_ref('rahman')}; the absolute values differ because the data and features differ. "
            "A single decision tree or histogram gradient boosting would have done as well on this file and trained faster; the forest was kept because it was already integrated, because averaging 200 trees makes the confidence value smoother, and because nothing measured here argues against it. "
            "That is a judgement, and it is stated as one."),
          ]
    b += [H2("Mathematical Formulation"),
          H3("Random Forest"),
          P("The forest is an average of T = 200 decision trees, each grown on a bootstrap sample with random feature subsets at each split. Each tree splits to reduce Gini impurity; the forest's probability of the attack class is the mean of the trees' leaf probabilities and the label is the more probable class:"),
          EQ("G(S) = 1 − Σ_c p_c²,    ΔG = G(S) − (|S_L|/|S|)·G(S_L) − (|S_R|/|S|)·G(S_R)"),
          EQ("P(attack | x) = (1/T) Σ_t P_t(attack | x),    ŷ = Attack if P(attack | x) ≥ 0.5"),
          P("`class_weight=balanced` weights class c by n / (2·n_c), so that the rarer class is not under-fitted; the confidence shown for a window is the probability of the predicted class. "
            "Feature importance is the mean decrease in impurity attributed to each feature, normalised to sum to one."),
          H3("Window aggregation"),
          P("For a window of W seconds with packet set Π, local address set L, and packet length ℓ(p):"),
          EQ("sent = {p ∈ Π : src(p) ∈ L, dst(p) ∉ L},    received = Π \\ sent"),
          EQ("packets_x = |x|,   bytes_x = Σ_{p∈x} ℓ(p),   packets_per_second_x = packets_x / W,   bytes_per_second_x = bytes_x / W,   average_size_x = bytes_x / packets_x"),
          P("The same ten quantities (counts, bytes, rates, average sizes for each direction) are obtained from a CICIDS2017 flow by taking forward counts as *sent*, backward counts as *received* and the flow duration in place of W."),
          H3("Distributed-risk score"),
          P("With n_src and n_dst the numbers of distinct sources and destinations, r the total packet rate (received plus sent packets per second) and r̄ the mean rate of the previous windows in the baseline (up to twelve):"),
          EQ("R = 0.30·min(n_src/30, 1) + 0.30·min(n_dst/15, 1) + 0.25·min(r/1500, 1) + 0.15·b"),
          EQ("b = min( max(r/r̄ − 1, 0) / 4, 1 ) if r̄ > 1;   otherwise b = 0 for r < 300 and b = 0.4 for r ≥ 300"),
          P("R < 0.4 is Low, 0.4 ≤ R < 0.7 Medium and R ≥ 0.7 High. The weights are chosen by hand; they are a transparent rule, not a fitted model."),
          H3("Persistence and severity"),
          EQ("c_t = c_(t−1) + 1 if (ŷ_t = Attack or R_t ≥ 0.7), otherwise c_t = 0"),
          EQ("S = 30·[Attack] + 8·conf·[Benign] + pts(conf) + pts(r) + pts(R) + 8·[n_src ≥ 25 or n_dst ≥ 12] + pts(c);   S ← min(S, 45) if Benign"),
          P("where pts(conf) is 15 for conf ≥ 0.90 and 8 for conf ≥ 0.75, pts(r) is 20, 12 or 5 for r ≥ 3,000, 1,200 or 400, pts(R) is 20 for R ≥ 0.7 and 10 for R ≥ 0.4, and pts(c) is 10 for c ≥ 3 and 5 for c = 2. "
            "The level is Critical for S ≥ 70, High for S ≥ 50, Medium for S ≥ 28 and Low otherwise."),
          H3("Evaluation metrics"),
          P("With TP, FP, TN and FN counted on the attack class:"),
          EQ("Accuracy = (TP + TN)/(TP + TN + FP + FN),   Precision = TP/(TP + FP),   Recall = TP/(TP + FN),   F1 = 2·Precision·Recall/(Precision + Recall),   FPR = FP/(FP + TN)"),
          P("The false-positive rate gets special attention because a false positive is not a harmless count here: it can quarantine a legitimate source, which is the denial of service the system is meant to prevent. "
            "ROC-AUC is reported for the ranking quality of the probability, independently of the 0.5 threshold."),
          ]
    b += [H2("Model Architecture and Training"),
          TAB("Training configuration (ml/train_model.py, config/config.py)", ["Item", "Value"],
              [["Classifier", "scikit-learn RandomForestClassifier"], ["Trees", "200 (`n_estimators=200`)"], ["Depth and splits", "`max_depth=None`, `min_samples_split=2`"],
               ["Class weights", "balanced"], ["Parallelism when trained", "`n_jobs=-1` (stored in the saved model)"], ["Random seed", "42"], ["Split", "stratified 80 % train / 20 % test (`test_size=0.2`)"],
               ["Input", "ten features, fixed order, unscaled"], ["Rows of the shipped model", f"{s['train_samples']:,} train, {s['test_samples']:,} test (12,000 benign, 12,000 attack)"],
               ["Training time", f"{s['training_seconds']} s on the development machine"], ["Model file", f"{F.LAT['model_file_mb']} MB (joblib), loads in about {F.LAT['model_load_seconds']} s"],
               ["Artefacts", "model, feature_list.json, metadata.json, metrics.json, confusion_matrix.json/png, roc_curve.png, feature_importance.json/png, classification_report.txt, test_features.csv"]],
              widths=[2.2, 4.4], align=["l", "l"], size=10),
          P("There is no hyper-parameter search: the values are scikit-learn defaults except the number of trees and the class weights. Training also reports the held-out metrics and stores them next to the model, "
            "and `ml/evaluate_model.py` can reload the stored model and re-score the stored test rows, which is how the displayed figures can be reproduced."),
          H3("Evaluation protocol used for this report"),
          P("Because the shipped metrics describe synthetic data, the evaluation in Chapter 8 adds four checks, all produced by `scripts/run_experiments.py` from the product's own modules: (1) the shipped model scored on every real DDoS-day flow; "
            "(2) the same forest recipe retrained on real flows, five seeds of a stratified 80/20 split plus a chronological block split (first 70 % of the file to train, last 30 % to test); "
            "(3) the shipped model run through the window pipeline at 2, 5 and 10-second windows with 4,000 simulator windows each, comparing the forest's label alone with the High-or-Critical decision; "
            "(4) latency of each pipeline stage over 600 windows and of the REST API over real HTTP."),
          TAB("Experiments run for this report (scripts/run_experiments.py, scripts/measure_api.py)", ["Experiment", "Data", "Protocol", "Output file"],
              [["Shipped model on real flows", f"{rl['rows']:,} CICIDS2017 DDoS-day flows", "Score every flow with the stored model; also a 20 % stratified sample", "real_cicids2017.json"],
               ["Retrained forest on real flows", "same flows", "Same hyper-parameters; stratified 80/20; seeds 42, 1, 2, 3, 4; chronological 70/30 block split", "real_cicids2017.json"],
               ["Classifier comparison and ablation", "same flows, seed 42", "Five classifiers; six feature groups with the same forest", "real_cicids2017.json"],
               ["Product recipe on real flows", "real flows + 6,000 window rows, capped at 120,000", "Stratified 80/20; test on mixed rows, all real flows and fresh simulator windows at 2, 5, 10 s", "hybrid_recipe.json"],
               ["Window pipeline", "4,000 simulator windows per window length (35 % attack, seed 2026)", "Forest label alone, High/Critical severity, distributed risk alone; stateful baseline and persistence", "window_pipeline.json"],
               ["Stage latency", "600 simulator windows", "Aggregate, predict, risk and severity, mitigation decision, SQLite write; single-window inference with n_jobs -1 and 1", "latency.json"],
               ["REST API", "scratch copy of the backend on port 8915", "100 calls per GET endpoint on 127.0.0.1; 25 malformed-input probes; Start, run and Stop of the simulator", "api_measurements.json"]],
              widths=[1.6, 1.7, 2.4, 1.0], align=["l", "l", "l", "l"], size=9.0),
          P("All experiments use the product's own modules (`ml.preprocessing`, `monitoring.traffic_aggregator`, `security.*`) rather than re-implementations, so a defect in those modules would show up in the numbers. "
            "Seeds are fixed, the scripts write JSON, and `docs/REPORT_FACTS.md` is generated from the JSON, which keeps every document consistent with the measurements. "
            "The measurements were taken on an Intel Core i5-12500 machine with 15.7 GB of memory and no GPU; other jobs kept the CPU saturated during the latency runs, so timing figures are upper bounds."),
          ]
    return b


def application_blocks():
    a, w = F.API_PORT, F.WEB_PORT
    k = F.K()
    b = []
    b += [H2("Application Architecture"),
          P(f"The application is Flask 3 serving on 127.0.0.1:{a} with `threaded=True`, `debug=False` and no reloader. `app.py` creates one `Database`, one `MitigationManager`, one `MonitorEngine` and one `TrafficSimulator` at import time and wires both producers to `process_window`. "
            "A daemon thread, `_health_sampler`, appends a psutil sample to a 120-entry in-memory deque and to SQLite every five seconds; failures are printed and the next sample is attempted. "
            "Shared mutable state (the latest detection, the persistence counter, the health buffer) is guarded by `state_lock`; the rolling baseline is a `deque(maxlen=12)` of packet rates. "
            f"The React console is a separate Vite project in `frontend/` (React 19, React Router 7, axios, Recharts, Tailwind 4, three.js for the landing background) served on port {w}, whose dev server proxies `/api` and `/static/results` to the API so that the browser makes only same-origin calls."),
          P("`process_window(features, context, source, interface)` is the single entry point for both producers. It returns an error record when the context carries a capture error, when the model is missing or when feature validation fails; "
            "otherwise it computes the distributed risk, updates the baseline and persistence, assesses severity, asks the mitigation manager for actions and stores a detection record. "
            "If the database write fails the record is still kept in memory with `id = None`, so the console keeps working. Appendix A quotes the function."),
          H3("Window producers"),
          P("`MonitorEngine._live_loop` repeats `sniff(iface, prn=callback, timeout=window, store=False)`; the callback extracts source, destination, protocol and length from IPv4 or IPv6 packets and skips malformed ones. "
            "A `PermissionError` produces a message about Administrator rights and Npcap; messages mentioning an unknown device or interface produce an invalid-interface message; Npcap or WinPcap problems produce the driver message; anything else is reported with the interface name. "
            "After an error the engine posts one error window (so the status can show it), stops itself and leaves it to the user to retry or switch to Simulation Mode. "
            "`TrafficSimulator` chooses benign or attack windows with attack probability 0.35 and builds packet lists in memory: benign windows of 60 to 600 packets between 192.168.1.20 and three external hosts; flood windows of 2,500 to 9,000 packets from 8 to 40 sources to one victim; "
            "carpet windows of 1,800 to 6,000 packets from 10 to 45 sources to 6 to 20 destinations; slow windows of 300 to 1,200 TCP packets from many sources to one victim. No packet is sent anywhere."),
          ]
    b += [TAB("Traffic styles produced by the simulator (monitoring/simulator.py)", ["Style", "Packets per window", "Sources", "Destinations", "Protocols and sizes"],
              [["Benign", "60-600", "2 external hosts and 1 local host", "3 external hosts and the local host", "TCP 62 %, UDP 28 %, ICMP 4 %, other 6 %; mixed sizes up to 1,200 bytes; both directions"],
               ["Flood", "2,500-9,000", "8-40 sources", "1 victim", "TCP 55 %, UDP 35 %, ICMP 10 %; 60-320 bytes; one direction"],
               ["Carpet bombing", "1,800-6,000", "10-45 sources", "6-20 victims", "TCP 50 %, UDP 50 %; 60-520 bytes"],
               ["Slow", "300-1,200", "up to ~4,000 possible addresses, many distinct", "1 victim", "TCP only; 200-1,400 bytes"]],
              widths=[1.1, 1.0, 1.5, 1.2, 1.9], align=["l", "c", "l", "l", "l"], size=9.0),
          P("The styles are the pattern classes the product aims at: a volumetric flood from many sources to one victim, carpet bombing from many sources across many victims, and a slow attack with modest volume. "
            "They are **generated by the same code that produced the 6,000 window rows used in training**, which means that high accuracy on simulator windows at the training window length is expected and proves nothing about real attacks; Chapter 8 says so wherever those numbers appear."),
          H3("Pseudocode of the two loops"),
          CODE("TRAINING  (ml/train_model.py)\n"
               "  rows   <- CICIDS2017 CSVs in data/raw, else synthetic fallback (9,000 + 9,000 flows)\n"
               "  X, y   <- map_to_common_schema(clean(rows)), label BENIGN -> 0, anything else -> 1\n"
               "  X, y   <- X + 3,000 benign windows + 3,000 attack windows (simulator generator, 10 s)\n"
               "  split  <- stratified 80 / 20, seed 42\n"
               "  forest <- RandomForest(200 trees, balanced).fit(train);  write metrics, plots, model\n\n"
               "MONITORING  (one iteration per window)\n"
               "  packets            <- sniff(window) or simulator.make_window()\n"
               "  features, context  <- aggregate_packets(packets, window, local_ips)\n"
               "  label, conf        <- forest(features)                      # validate first\n"
               "  risk               <- distributed_risk(features, context, baseline)\n"
               "  persistence        <- persistence + 1 if label == Attack or risk >= 0.7 else 0\n"
               "  level, factors     <- severity(label, conf, features, risk, persistence)\n"
               "  actions            <- policy(level, context.top_sources)    # quarantine / recommend / monitor\n"
               "  store(detection, actions);  expire due quarantines", 8.5),
          ]
    b += [H2("API Design"),
          P(f"Twelve JSON endpoints, the legacy page and the results route are described in Chapter 5. The conventions are uniform: GET endpoints are read-only and cheap (median 3 to 13 ms over real HTTP except `/api/interfaces` at {F.API['latency'][2]['p50_ms']:.0f} ms, which asks the operating system for adapters); "
            "POST endpoints take a JSON body and tolerate a malformed or missing body by treating it as empty; every input is validated before use and rejected with HTTP 400 and an `error` message, and conflicts return 409. "
            "A global handler turns unknown routes into a JSON 404 and unhandled exceptions into a JSON 500."),
          ]
    b += [H2("Front-End Implementation"),
          P("The front end has ten page components and a small kit of shared components. `lib/live.jsx` polls `/api/status` every two seconds and fetches detections and mitigations on a slower cadence, then shares the result through a React context, so every screen sees the same data; "
            "`lib/auth.jsx` implements the demo gate (credentials checked in the browser and a flag kept in `localStorage`); `lib/theme.jsx` keeps the light or dark choice; `components/ui/CommandPalette.jsx` and `nav.jsx` implement the keyboard shortcuts. "
            "Charts use Recharts; the landing page draws a three.js grid and a typewriter terminal, and respects the reduced-motion setting. The Threat Detail drawer renders the stored `detail_json` of a detection."),
          ]
    b += [H2("Security and Error Handling"),
          TAB("Security and error-handling measures, with what each was checked by", ["Concern", "Measure in the code", "Checked by"],
              [["Network exposure", "Flask binds to 127.0.0.1 only (config HOST); Docker image pins 0.0.0.0 inside the container only", "Configuration review"],
               ["Input validation", "window 2-120, quarantine 5-3600, limit clamped 1-500; integers parsed with try/except; features validated for presence, numeric type, NaN, inf and negatives", f"Unit and API tests; {F.API['probes_ok']} of {F.API['probes_total']} HTTP probes behaved as intended"],
               ["Injection", "All SQL uses parameter placeholders; a `limit=1;DROP TABLE detections` probe returns 400", "HTTP probe"],
               ["Path traversal", "Results files are served by `send_from_directory`; `..` paths return 404", "HTTP probe"],
               ["Safe mitigation", "Quarantine is application-level; protected addresses (unknown, loopback, simulator host, local interface addresses) are never targeted; entries expire; OS firewall stub returns applied: false", "Unit tests"],
               ["Failure of capture", "Real reason shown (permission, interface, Npcap); engine stops instead of looping", "HTTP probe: HTTP 200 on start, then `capture_error` in status"],
               ["Failure of storage or model", "Corrupt or missing model gives a clear message; a failed detection write is caught; health-sampler errors are printed and skipped", "Unit tests (model missing)"],
               ["Concurrency", "One lock in `Database`, one in `MitigationManager`, `state_lock` in the app; a second Start returns 409", "API tests"]],
              widths=[1.3, 3.6, 1.7], align=["l", "l", "l"], size=9.0),
          P("Three gaps are stated plainly. The REST API has **no authentication**; protection rests on the localhost binding and the demo login is a browser-side gate that protects nothing. "
            "The `interface` field of the settings call is not length-checked (a 5,000-character value was accepted and stored in memory). "
            "And the `settings` table is never used: settings are kept in memory and return to their defaults on restart."),
          ]
    b += [TAB("Error paths of live capture and what the user sees", ["Condition", "Message shown (status.capture_error / banner)", "State afterwards"],
              [["Scapy cannot be imported", "Scapy is unavailable: <reason>", "Engine stopped"],
               ["Permission denied", "Packet capture permission denied ... Run as Administrator/root, install Npcap on Windows, or use Simulation Mode", "Engine stopped after one error window"],
               ["Unknown interface", "Invalid network interface '<name>': <reason>", "Engine stopped"],
               ["Npcap or WinPcap missing (this machine)", "Packet capture driver unavailable ... Install Npcap (https://npcap.com) or use Simulation Mode", "Start returns HTTP 200, mode returns to stopped within seconds"],
               ["Any other capture error", "Capture failed on '<interface>': <reason>", "Engine stopped"],
               ["Aggregation or callback failure", "Aggregation failed: <reason> / Detection callback failed: <reason>", "Loop continues with the next window"]],
              widths=[1.7, 3.3, 1.6], align=["l", "l", "l"], size=9.0),
          ]
    b += [H2("Installation and Execution"),
          P("Requirements are Windows 10 or 11 (or a modern Linux), Python 3.11 or 3.12, Node.js 20 or newer for the console and, for live capture only, Npcap and an Administrator terminal. "
            "`run.bat` creates `.env` with the default ports, creates `.venv`, installs `requirements.txt`, trains the model if it is missing, runs `npm install` on the first start, starts the API and the console and opens the browser. "
            f"The demonstration login is `{F.DEMO_EMAIL}` / `{F.DEMO_PASSWORD}`; Simulation Mode needs no privileges. Appendix B gives the steps."),
          ]
    return b


def blocks():
    return [H1("6. METHODOLOGY AND SOFTWARE IMPLEMENTATION"),
            P("This chapter explains how SentinelFlow is built and how it was evaluated: the overall method, the data, the preprocessing, the choice of algorithm, the formulas, the training configuration, the application, its security and its installation. "
              "Every number in it comes from `results/metrics.json` or from the experiments in `results/experiments/`, run on the product's own modules.")
            ] + renum(methodology_blocks() + application_blocks(), "6")
