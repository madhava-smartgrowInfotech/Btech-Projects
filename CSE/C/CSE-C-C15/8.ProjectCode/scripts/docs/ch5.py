"""Chapter 5: System Design for SentinelFlow.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
The diagram explanations in diagram_index.DIAGRAMS also appear in the Block Diagrams document; here they are adapted, not repeated.
"""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_IDX = {d[0]: d for d in DIAGRAMS}


def dg(key, width=5.4, extra=None):
    """Figure for one diagram plus the paragraphs written for this chapter."""
    _, _title, fname, caption, _text = _IDX[key]
    out = [FIG(F.diag(fname), caption, width)]
    for e in extra or []:
        out.append(P(e))
    return out


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    k = F.K()
    out = [
        H1("5. SYSTEM DESIGN"),
        P("This chapter describes how SentinelFlow is built: the architecture and workflow, the data flow, the class, sequence and use-case design, the data design, the core algorithm, "
          "the module and API design and the user interface. Every diagram was drawn from the code in `app.py`, `monitoring/`, `ml/`, `security/`, `database/` and `frontend/src/`; the complete set, each with a longer explanation, "
          "is also collected in the Block Diagrams document."),
        P("Three facts about the design are stated at the outset because they shape everything below. SentinelFlow is a **single Python process** with no message queue and no separate worker: the capture thread, the simulator thread, "
          "the health sampler and the Flask request threads share one set of in-memory objects. Its **mitigation is application-level**: a quarantine is an entry in a table inside the process, and the operating-system firewall is never touched. "
          f"And its **REST API has no authentication**; the product relies on binding to 127.0.0.1. The design follows the detection half of the base paper [{R['base']}] (a tree-based classifier on flow features) and adds the loop that paper "
          "lists as future work: severity assessment, mitigation, recovery and history."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. First, **close the loop** from a captured window to an action and back to a recovered state, so that detection is never the last step. Second, **be explainable**: every decision carries the factors that produced it, "
          "because a quarantined address must be justifiable to an administrator. Third, **be safe by default**: no attack traffic is generated, the firewall is not changed, local and loopback addresses are never quarantined, "
          "and quarantines expire by themselves. Fourth, **run on a laptop without special hardware**: the classifier is a Random Forest on ten numbers per window, and Simulation Mode needs neither Npcap nor Administrator rights. "
          "Fifth, **use one pipeline for live and simulated traffic**, so that the demonstration exercises the same code as a real capture."),
    ] + dg("arch", 5.4, extra=[
        f"The architecture has four tiers. The browser tier is a React 19 single-page application served by Vite on port {w}; it polls the API every two seconds and holds no business logic. "
        f"The Flask application listens on 127.0.0.1:{a}, exposes twelve JSON endpoints and owns `process_window()`, the one function through which every window passes. "
        "The pipeline modules are plain Python packages: `monitoring/` produces windows, `ml/` defines the feature schema and loads the model, and `security/` turns a prediction into a risk score, a severity and an action. "
        "State lives in a SQLite file and in the joblib, JSON and PNG artefacts written by training. Beyond the process boundary are the network interface (reached through Scapy), psutil for host counters and, at training time only, "
        "the CICIDS2017 files."]) + [

        H2("5.2 High-Level Workflow"),
    ] + dg("flow", 5.4, extra=[
        "The workflow has two time scales. Training is a command-line program, `python ml/train_model.py`, which took 22.2 seconds for the shipped model; it writes the model, the feature list, the metadata and the evaluation plots. "
        "Monitoring is a loop that repeats once per window. In live mode the window is the capture time of a Scapy `sniff()` call (ten seconds by default, two to 120 allowed); in Simulation Mode the simulator builds a packet list in memory and waits for the window length. "
        "Everything after the packet list is identical: aggregate, classify, assess, act, store."]) + [

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
    ] + dg("dfd0", 4.8, extra=[
        "At level 0 the system has four neighbours. The administrator controls sessions and reads results; the network interface or the simulator supplies packets; psutil supplies host counters for the health screen; "
        "the CICIDS2017 files supply labelled flow rows to the offline training script. A single store, D1, stands for the SQLite database and the model files."]) + [
        H3("5.3.2 Level 1: seven processes"),
    ] + dg("dfd1", 5.2, extra=[
        "Processes 1.0 to 4.0 run once per window. Process 2.0 loads the model files from D3 once and reuses them. Process 5.0, the API and dashboard, only reads: it answers the administrator's polls from D1 and D2. "
        "Process 6.0 is independent of traffic: a background thread samples CPU, memory and network counters every five seconds into D4. Process 7.0 is the offline trainer and is the only process that writes D3."]) + [
        H3("5.3.3 Level 2: risk, severity and mitigation"),
    ] + dg("dfd2", 5.2, extra=[
        "Process 3.0 combines four measurable components into a distributed-risk score and then adds the forest's label, its confidence, the packet rate, the spread and the persistence of suspicious windows into a severity score, "
        "keeping a list of the factors that contributed. Process 4.0 maps the severity to an action. Only High and Critical produce quarantines; the targets are the three busiest sources, minus the protected addresses. "
        "The rolling baseline D5 holds the packet rates of the last twelve windows and feeds the deviation component of the next window."]) + [

        H2("5.4 Class, Sequence and Use-Case Design"),
        H3("5.4.1 Class diagram"),
    ] + dg("uml", 5.4, extra=[
        "The design deliberately has few classes. `MonitorEngine` and `TrafficSimulator` are the two window producers and share one callback signature, `on_window(features, context, source, interface)`. "
        "`Database` serialises every SQLite call behind a lock because Flask runs threaded. `MitigationManager` keeps the active quarantines in a dictionary keyed by address and writes history through `Database`. "
        "Everything else is a module of functions, which keeps the risk, severity and aggregation rules easy to test: the test-suite calls them directly with hand-made inputs."]) + [
        H3("5.4.2 Sequence diagram"),
    ] + dg("seq", 5.3, extra=[
        "The sequence shows why the console never waits for a detection: the Start request returns as soon as the simulator thread exists, and the console learns about new windows by polling. "
        "The alternative flows listed under the diagram are the ones covered by tests: a failing live capture, a validation error, a second Start (HTTP 409) and quarantine expiry."]) + [
        H3("5.4.3 Use-case diagram"),
    ] + dg("uc", 4.6, extra=[
        "The administrator is the only human actor. Detection and mitigation are not use cases because nobody triggers them: they run on every window. Retraining the model is a developer use case performed from the command line, not from the console."]) + [

        H2("5.5 Data Design"),
    ] + dg("er", 5.4, extra=[
        "The database is one SQLite file, `data/sentinelflow.db`, created on first start by `Database.__init__`. Four tables are used; the data dictionary below describes them. "
        "There are no foreign keys: a quarantine row names the address, the reason text (which contains the window source and the severity) and the time, not the id of the detection that caused it. "
        "The full per-window detail (the ten features, the context, the risk components, the severity factors and the actions) is stored as one JSON text in `detections.detail_json`, so the Threat Detail screen can explain a past window exactly as it was scored."]) + [
        TAB("Data dictionary of the four tables", ["Table", "Columns", "Purpose and notes"],
            [["detections", "id (PK), timestamp, interface, source, prediction, confidence, severity, packet_rate, byte_rate, source_count, destination_count, distributed_risk, mitigation_status, detail_json",
              "One row per scored window. prediction is Benign or Attack; severity is Low, Medium, High or Critical; source is live or simulation."],
             ["mitigations", "id (PK), timestamp, ip, reason, duration, status", "One row per quarantine. status is active until expiry, then recovered (updated by address and reason)."],
             ["health_samples", "id (PK), timestamp, cpu_percent, memory_percent, bytes_sent, bytes_recv, packets_sent, packets_recv", "psutil sample every five seconds; the Network health screen reads the last 30."],
             ["settings", "key (PK), value", "Key-value table with get and set methods; the API currently keeps the window and quarantine settings in memory, so this table is unused."]],
            widths=[1.2, 3.0, 2.4], align=["l", "l", "l"], size=9.5),
        P("Three further stores are files: `models/sentinelflow_rf.joblib` with `feature_list.json` and `metadata.json` (written by training, read once by `model_loader`), and `results/` with `metrics.json`, `confusion_matrix.json`, "
          "`feature_importance.json`, `classification_report.txt` and three PNG plots (read by `/api/model/metrics` and `/static/results/<file>`). `data/processed/test_features.csv` keeps the held-out test rows."),

        H2("5.6 Core Algorithm Design"),
        H3("5.6.1 The per-window algorithm"),
    ] + dg("flowchart", 4.5, extra=[
        "`process_window()` is the heart of the application. It is deliberately a straight line with two early exits. The first exit handles a capture failure reported by the live engine (the context carries an `error` key); the second handles a missing model or invalid features, "
        "which `ml.features.validate_feature_dict` rejects when a value is missing, non-numeric, NaN, infinite or negative. After that the steps are fixed: distributed risk, baseline update, persistence update, severity, action, storage."]) + [
        H3("5.6.2 Distributed-risk and severity design"),
        P("The distributed-risk layer exists because of carpet-bombing: traffic spread over many destinations can look modest at every single destination while the aggregate is large. "
          "Its four components are source diversity (distinct sources divided by 30, capped at 1), destination diversity (distinct destinations divided by 15, capped at 1), rate pressure (packets per second divided by 1,500, capped at 1) "
          "and baseline deviation (how far the packet rate is above the mean of the last twelve windows, scaled to 0 to 1 over a fourfold rise). The weights are 0.30, 0.30, 0.25 and 0.15. "
          "Scores below 0.4 are Low, below 0.7 Medium and otherwise High, and the sentence that goes with the score names the pattern: concentrated, spread across many sources, spread across many destinations (possible carpet bombing) or both."),
        P("Severity adds up points from independent evidence, so that no single signal decides. The label contributes most, the others refine it, and a benign label is capped so that a benign window can never rise above Medium."),
        TAB("Severity points (security/severity.py)", ["Evidence", "Condition", "Points"],
            [["Forest label", "Attack / Benign", "+30 / +8 x confidence"],
             ["Model confidence", ">= 0.90 / >= 0.75", "+15 / +8"],
             ["Packet rate", ">= 3,000 / >= 1,200 / >= 400 packets per second", "+20 / +12 / +5"],
             ["Distributed risk", ">= 0.70 / >= 0.40", "+20 / +10"],
             ["Spread", ">= 25 sources or >= 12 destinations", "+8"],
             ["Persistence", ">= 3 consecutive suspicious windows / exactly 2", "+10 / +5"],
             ["Cap and levels", "Benign capped at 45; Critical >= 70, High >= 50, Medium >= 28, otherwise Low", "-"]],
            widths=[1.5, 3.6, 1.5], align=["l", "l", "l"], size=9.5),
        H3("5.6.3 Mitigation policy"),
        P("The policy is a table, not a model. **Low** keeps monitoring. **Medium** records a rate-limit recommendation for the interface. **High** quarantines the three busiest sources of the window for the configured time (40 seconds by default); "
          "**Critical** does the same for twice as long. Addresses that are `unknown`, loopback (127.0.0.1, ::1), the simulator's local host 192.168.1.20 or any address of a local interface are protected and never quarantined; when all top sources are protected the action degrades to a rate-limit recommendation. "
          "A source that is already quarantined is not quarantined again until the entry expires, and every call first expires due entries and marks them `recovered` in the history. "
          "The design choice that matters is what a quarantine is: an entry in `MitigationManager.active` and a row in `mitigations`. It is shown on the Mitigation screen and counted in the status, but no packet is dropped; "
          "an optional operating-system integration exists only as a stub, `apply_os_firewall_block()`, which returns `applied: false`."),

        H2("5.7 Module Design"),
        P("The table below lists every source module with its size and responsibility, so that the chapters that follow can refer to a module by name."),
        TAB("Modules of SentinelFlow (line counts measured)", ["Module", "Lines", "Responsibility and key functions"],
            [["app.py", "389", "Flask app; `process_window`, `_health_sampler`, 12 JSON routes, `/` page and `/static/results/<file>`; JSON 404 and 500 handlers"],
             ["config/config.py", "33", "Host and port from `.env` (defaults 127.0.0.1:5000, set to 8415), window 10 s, baseline 12, quarantine 40 s, paths, seed 42, test size 0.2"],
             ["ml/features.py", "62", "`FEATURE_COLUMNS` (ten names, fixed order), `validate_feature_dict`, `empty_feature_dict`"],
             ["ml/preprocessing.py", "144", "`normalize_columns`, `clean_dataframe`, `normalize_label_value`, `extract_label_series`, `map_to_common_schema` (forward to sent, backward to received)"],
             ["ml/train_model.py", "389", "Dataset lookup, synthetic fallback, window augmentation, 80/20 split, Random Forest, metrics, plots, artefacts"],
             ["ml/model_loader.py", "87", "`is_trained`, `load_model`, `get_metadata`, `predict_traffic` (label, confidence)"],
             ["ml/evaluate_model.py", "54", "Reloads the stored model and re-scores `data/processed/test_features.csv`"],
             ["monitoring/interface_manager.py", "60", "`list_interfaces` (psutil + Scapy), `local_ip_set`"],
             ["monitoring/packet_capture.py", "121", "`MonitorEngine`: rolling Scapy `sniff()` windows, error classification (permission, interface, Npcap)"],
             ["monitoring/simulator.py", "98", "`TrafficSimulator`: benign, flood, carpet and slow windows, no network I/O"],
             ["monitoring/traffic_aggregator.py", "83", "`aggregate_packets`: ten features plus context (sources, destinations, protocol shares, top sources)"],
             ["security/detector.py", "9", "`detect`: refuses to run without a trained model"],
             ["security/distributed_analysis.py", "73", "`compute_distributed_risk`"],
             ["security/severity.py", "78", "`assess_severity`"],
             ["security/mitigation.py", "115", "`MitigationManager`: `decide`, `quarantine`, `expire_due`, `get_active`, `set_duration`"],
             ["database/db.py", "204", "`Database`: four tables, locked SQLite access"]],
            widths=[2.0, 0.6, 4.0], align=["l", "c", "l"], size=9.0),
        P("The front end adds about 3,100 lines of JSX and JavaScript in `frontend/src/`: ten page components, a small UI kit (table, charts, controls, command palette, activity log), an `api.js` axios client, "
          "a polling provider (`lib/live.jsx`), a demo-login provider (`lib/auth.jsx`) and a theme provider."),

        H2("5.8 API Design"),
        P(f"The API is JSON over HTTP on 127.0.0.1:{a}. Errors are JSON objects with an `error` key and a meaningful status: 400 for invalid input, 404 for unknown routes, 409 when a session is already running, 500 for failures. "
          "The table below lists the twelve endpoints and the two additional routes."),
        TAB("Routes of app.py", ["Method", "Path", "Purpose", "Notable behaviour"],
            [["GET", "/api/status", "Mode, window, windows completed, latest detection, active mitigations", "mode is stopped, live or simulation; capture_error carries the last capture failure"],
             ["GET", "/api/health", "Current host sample, last 30 recent, last 30 from SQLite", "-"],
             ["GET", "/api/interfaces", "Interface names, addresses, up/down", "500 if discovery fails"],
             ["GET", "/api/detections?limit=", "Stored detections with counts by prediction and severity", "limit clamped to 1-500; non-integer gives 400"],
             ["GET", "/api/detections/latest", "Most recent detection", "Falls back to SQLite; message when none"],
             ["GET", "/api/mitigations", "Active quarantines with seconds left, history (100), quarantine length", "Expires due entries first"],
             ["GET / POST", "/api/settings", "Window (2-120 s), quarantine (5-3600 s), interface", "Out-of-range or non-numeric gives 400; malformed JSON is tolerated"],
             ["POST", "/api/monitor/start", "Start live capture on an interface", "409 if a session runs; capture failure is reported through status"],
             ["POST", "/api/monitor/stop", "Stop live capture", "Idempotent"],
             ["POST", "/api/demo/start", "Start Simulation Mode (window 2-120 s, default 5)", "409 if a session runs"],
             ["POST", "/api/demo/stop", "Stop simulation", "Idempotent"],
             ["GET", "/api/model/metrics", "metrics.json, feature importance, confusion matrix", "trained: false and a message when no model exists"],
             ["GET", "/", "Original server-rendered dashboard", "Jinja template"],
             ["GET", "/static/results/<file>", "Evaluation PNGs from results/", "send_from_directory; path traversal returns 404"]],
            widths=[0.8, 1.6, 2.4, 1.9], align=["c", "l", "l", "l"], size=9.0),

        H2("5.9 User Interface Design"),
        P("The console is a React single-page application in a dark, monospace-accented style with a light theme on a toggle. The landing page explains the pipeline and shows live counters from `/api/status`; "
          "the demo login gate leads to the console, which has a sidebar with seven screens (Overview, Detections, Analytics, Network health, Mitigation, Model, Settings), a top bar with a search box, a mode pill and a theme toggle, "
          "and a command palette (opened with `/`) with `g`-then-letter shortcuts."),
        TAB("Console screens and the data each reads", ["Screen", "Content", "Source"],
            [["Overview", "Session control (interface, window, Start live, Start simulation, Stop); six cards: threat status, severity with risk, model confidence, packets per second, sources and destinations, active mitigations; packet-rate sparkline; latest windows", "/api/status, /api/detections, /api/interfaces"],
             ["Detections", "Filterable, sortable table of every scored window; click opens the Threat Detail drawer with measured traffic, risk components, severity factors and the recommendation", "/api/detections"],
             ["Analytics", "Benign-versus-attack donut, severity distribution, packet-rate and confidence timeline", "/api/detections"],
             ["Network health", "CPU, memory, bytes and packets in and out with time series", "/api/health"],
             ["Mitigation", "Active quarantines with countdown bars, history, quarantine length", "/api/mitigations"],
             ["Model", "Accuracy, precision, recall, F1, ROC-AUC, confusion matrix, feature importance, plots, and a synthetic-data warning", "/api/model/metrics"],
             ["Settings", "Window and quarantine length, with server-side validation messages", "/api/settings"]],
            widths=[1.2, 4.2, 1.3], align=["l", "l", "l"], size=9.0),
        P("Three design choices are worth stating. **Simulation Mode is always labelled**: a pill in the top bar and a banner on the Overview screen say that nothing shown is live traffic. "
          "**Failures are shown, not hidden**: when live capture cannot start, the real reason from Scapy appears in a banner (the Overview capture in Chapter 8 shows the Npcap message). "
          "**The Model screen warns when the training data were synthetic**, which is the case for the shipped model. The output screens are shown and discussed in Chapter 8."),

        H2("5.10 Design Trade-offs and Known Weaknesses"),
        B("**One process, shared memory.** Simple and fast, but the quarantine table and the baseline are lost on restart (history survives in SQLite) and the design does not scale beyond one host.",
          "**Application-level mitigation.** Safe and demonstrable on any machine, but it does not stop a single packet; turning it into enforcement needs a firewall or SDN rule installer and a very careful allow-list.",
          "**Rules around a classifier.** The risk and severity weights are hand-set and not learned; they are transparent, and Chapter 8 measures what they achieve, but they were not tuned on real attack captures.",
          f"**Window length is a hidden parameter.** The forest was calibrated on 10-second windows; at 2 and 5 seconds its label alone raises {k['w2_fpr_ml'] * 100:.0f} % and {k['w5_fpr_ml'] * 100:.0f} % false alarms on benign windows, and the severity layer is what keeps the quarantine rate low ({k['w2_fpr_act'] * 100:.1f} % and {k['w5_fpr_act'] * 100:.2f} %).",
          "**No authentication on the API.** Acceptable for a localhost-only prototype; the demo login is a browser-side gate and protects nothing.",
          "**Saved forest uses all cores.** The model was stored with `n_jobs=-1`, which makes single-window inference about ten times slower than a single thread (Chapter 7)."),
    ]
    return out
