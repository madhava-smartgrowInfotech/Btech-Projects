"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for SentinelFlow (CSE-C-C15)."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def feasibility_blocks():
    k = F.K()
    L, A = F.LAT, F.API
    api_p50 = sorted(d["p50_ms"] for d in A["latency"] if d["method"] == "GET")
    return [
        H1("3. FEASIBILITY STUDY"),
        H2("3.1 Introduction"),
        P(f"Before the design was fixed, the project was examined for technical, economic, operational and schedule feasibility. This chapter records that examination with the evidence gathered while building and measuring {F.PRODUCT}: "
          "what was available, what it cost, who would run it and how the work was planned."),
        H2("3.2 Technical Feasibility"),
        P("The product needs five capabilities: packet capture or a substitute, feature computation, a trained classifier, a web service with storage, and a browser interface. Each is available in free, widely used libraries, "
          "and each was shown to work on the development machine (an Intel Core i5-12500 with 6 cores and 12 threads, 15.7 GB of memory, Windows 11 Pro, no GPU)."),
        TAB("Technology choices and the evidence that they are feasible", ["Capability", "Choice (version used)", "Evidence"],
            [["Packet capture", f"Scapy 2.8.0 [{R['scapy']}], Npcap on Windows", "Capture code written; Npcap absent on the test machine, so only the error path ran. Simulator substitutes."],
             ["Host health", f"psutil 7.2.2 [{R['psutil']}]", "CPU, memory and network counters sampled every 5 s and stored."],
             ["Classifier", f"scikit-learn 1.9.1 [{R['sklearn']}], Random Forest [{R['breiman']}]", f"Shipped forest trained in {F.SHIP['training_seconds']} s; real-flow forest in about {F.REAL['real_rf_per_seed'][0]['train_seconds']:.0f} s; model file {L['model_file_mb']} MB."],
             ["Data handling", "pandas 3.1.0, NumPy 2.4.6, joblib 1.6.0", f"{k['real_rows']:,} real flows read, cleaned and mapped in a single pass."],
             ["Web service", f"Python 3.11.9, Flask 3.1.3 [{R['flask']}]", f"Twelve JSON endpoints; median response {api_p50[0]:.1f} to {api_p50[-1]:.1f} ms over HTTP on 127.0.0.1."],
             ["Storage", "SQLite (Python standard library)", "Four tables; no server to install."],
             ["Interface", "React 19, Vite 8, Tailwind 4, Recharts 3", "Nine pages built; twelve screens captured with data."],
             ["Tests", "pytest 9.1.1, requests", f"{F.PYTEST_PASSED} automated tests and {F.SMOKE_PASSED} smoke checks pass."]],
            widths=[1.2, 2.1, 3.2], align=["l", "l", "l"], size=9.5),
        P(f"Capacity was checked against the simulator, whose windows are the heaviest the pipeline sees in this project: over {L['windows']} windows the mean was {L['mean_packets_per_window']:,.0f} packets and the largest {L['max_packets_per_window']:,}; aggregating such a window took a median of {L['aggregate_ms']['p50']:.1f} ms. "
          "Real traffic on a busy link would contain far more packets per window, so the capture path is the part whose capacity could not be established without a live test."),
        P("The main technical risk was data: CICIDS2017 could not be downloaded when the product was first built, so the training script falls back to a labelled synthetic dataset and says so in the metadata, the API and the console. "
          f"The documentation run later obtained one real CICIDS2017 file (the Friday-afternoon DDoS capture, {k['real_rows']:,} flows) from a public mirror, which showed that the fallback is *feasible to run but not representative* (Chapter 8). "
          "The second risk was packet capture on Windows, which needs Npcap and Administrator rights; the Simulation Mode removes the dependency for demonstration. The feasibility of the core idea, a classifier on ten flow features, is supported by the real-data result "
          f"of {k['rr_acc'][0] * 100:.2f} % accuracy after retraining."),
        H2("3.3 Economic Feasibility"),
        P("The project was carried out with no expenditure on licences, cloud services or special hardware. Every library is open source: Flask, scikit-learn, pandas, psutil and Vite are under permissive licences, React is under the MIT licence and Scapy under the GNU GPL version 2. "
          "CICIDS2017 is distributed for research by the Canadian Institute for Cybersecurity (its licence field on the mirror used reads simply 'other', and the dataset paper has to be cited [" + f"{R['cicids']}" + "]). "
          "The computer used was an ordinary desktop; the heaviest job, training the 200-tree forest on the real flows, took seconds. No GPU, database server or message broker is needed."),
        TAB("Cost items", ["Item", "Cost", "Note"],
            [["Software licences", "None", "All libraries open source"], ["Cloud or hosting", "None", "Runs on localhost; optional Docker image"],
             ["Hardware", "Existing computer", "No GPU; model file 2.74 MB"], ["Dataset", "None", "Public CICIDS2017 files; paper must be cited"],
             ["Human effort", "Team time", "The only real cost; not priced here because no timesheet exists"]],
            widths=[1.8, 1.5, 3.2], align=["l", "l", "l"], size=10.5),
        P("For an organisation that wanted to adopt a product like this, the recurring costs would be administrator time to retrain the model on its own traffic and, for live capture, a machine placed where it can see the traffic. "
          "Those costs were not measured and are not estimated here."),
        H2("3.4 Operational Feasibility"),
        P("The intended operator is a network administrator or analyst, not a developer. Starting the product is one step: `run.bat` creates a virtual environment, installs the dependencies, trains the model if none exists and starts the API on port "
          f"{F.API_PORT} and the console on port {F.WEB_PORT}. The console explains itself: a coloured banner says whether the data is live or simulated, every detection lists the factors behind its severity, and the Model page warns when the training data was synthetic. "
          "Quarantines are temporary (40 seconds by default, 80 for Critical) and expire without intervention, so a wrong decision corrects itself and no firewall rule has to be cleaned up afterwards, because none is ever written."),
        P("Operating the product live requires Administrator rights and Npcap on Windows, which a small organisation can supply but a student laboratory sometimes cannot; Simulation Mode covers that case. "
          "Maintenance consists of retraining when the traffic profile changes: copying CICIDS2017 or locally labelled captures into `data/raw` and running `python ml/train_model.py`."),
        H2("3.5 Schedule Feasibility"),
        P("The batch backlog (19.USER_STORIES.xlsx) divides the work into 23 user stories of 116 story points in five sprints. The file is an import sheet and carries every story with the status 'To Do'; it is a plan, not a record of what was done. "
          "Table 3.3 shows the plan; Chapter 8 reports which objectives were reached."),
        TAB("Planned sprints from the batch backlog", ["Sprint", "Stories", "Points", "Content"],
            [["1", "US-101 to US-106", "26", "Login, password reset, roles, flow submission and validation, repository setup"],
             ["2", "US-107 to US-110, US-114", "32", "Approach evaluation, benchmark dataset, live capture with the same features, classifier training, output review"],
             ["3", "US-111 to US-113, US-115 to US-117", "39", "Adaptive mitigation, live-traffic dashboard, accuracy evaluation, retry and logging, tuning, API"],
             ["4", "US-118 to US-121", "14", "Results dashboard, report export, history and search, notifications"],
             ["5", "US-122, US-123", "5", "Evaluation metrics, deployment and user documentation"]],
            widths=[0.6, 1.9, 0.7, 3.3], align=["c", "l", "c", "l"], size=10),
        P("The schedule was feasible for the core of the project (sprints 2 and 3: data, capture, classifier, mitigation, dashboard, API) and for the history, search and documentation items. "
          "The items of sprint 1 that concern accounts (registration, password reset, role-based access) and the export and notification items of sprint 4 were not built; the console has a demonstration login only. This is stated again in Section 4.7."),
        H2("3.6 Risk Analysis"),
        TAB("Risks, their handling and what actually happened", ["Risk", "Handling in the design", "Outcome"],
            [["Benchmark dataset unavailable", "Labelled synthetic fallback, provenance recorded in metadata", "Happened: the shipped model is synthetic-trained; real-data check added in documentation"],
             ["Packet capture not permitted or Npcap missing", "Capture errors surfaced in the UI; Simulation Mode", "Happened on the test machine; error path tested, simulator used"],
             ["Legitimate source quarantined by mistake", "Protected local addresses, short expiring quarantine, severity layer before action", f"False-positive rate at acting level {k['w5_fpr_act'] * 100:.2f} % (5 s windows) in simulation"],
             ["Detector too slow for the window", "Per-window decision in one call; measure latency", f"Median {L['detect_to_mitigation_ms']['p50']:.0f} ms on a CPU-saturated host; forest saved with n_jobs=-1 costs about ten times more per window"],
             ["Optimistic metrics", "Report held-out, real and pipeline-level numbers separately", "Gap found and reported (Chapter 8)"],
             ["Scope growth (accounts, export, notifications)", "Backlog prioritised; core loop first", "Accounts, export and notifications left out"]],
            widths=[1.7, 2.5, 2.3], align=["l", "l", "l"], size=9.5),
        H2("3.7 Advantages and Constraints"),
        P("**Advantages.** The product is self-contained (one process, one SQLite file), explainable (every severity lists its factors), safe to demonstrate (Simulation Mode), cheap to run, and reversible in its action (temporary quarantine, no firewall changes). "
          "Its model is small and quick to retrain, and its behaviour is covered by automated tests."),
        P("**Constraints.** The result depends on the quality and representativeness of the training data; the monitoring window must match the one the model was calibrated on; live capture needs privileges; and the mitigation is advisory at the network level because nothing outside the application is changed. "
          "These constraints shape the requirements in Chapter 4."),
    ]


def requirements_blocks():
    k = F.K()
    L, A = F.LAT, F.API
    return [
        H1("4. SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System and its Limitations"),
        P("In practice an administrator has three kinds of tools. Signature-based intrusion detection systems compare traffic with known patterns; they are precise for known attacks but, as the batch problem statement says, cannot detect novel or modified patterns. "
          "Threshold rules on packet rate or connection count are cheap but need manual tuning and miss attacks that spread over many destinations. Research prototypes, including the base paper, train a classifier on stored flows and report accuracy, but stop at detection."),
        TAB("Limitations of the existing approaches", ["Approach", "What it does", "Limitation for this problem"],
            [["Signature IDS", "Matches known patterns", "Misses new or modified attacks"],
             ["Threshold rules", "Alarm when rate or count exceeds a limit", "Manual tuning; blind to spread-out traffic; many false alarms in busy periods"],
             ["Offline classifier (base paper and similar)", "Labels stored flows with high accuracy", "No live loop, no mitigation, no severity, no latency measurement"],
             ["Retrieval + LLM", "Classifies traffic by retrieving similar cases", "About two seconds per request and an external model service"]],
            widths=[1.8, 2.1, 2.6], align=["l", "l", "l"], size=10),
        H2("4.2 Proposed System and its Advantages"),
        P(f"{F.PRODUCT} aggregates traffic into rolling windows, classifies each window, grades its severity with a visible explanation, acts on High and Critical windows with a temporary quarantine, lets the quarantine lapse, and stores everything for review. "
          "Its advantages over the existing approaches are the closed loop, the explanation attached to every decision, the carpet-bombing-aware distributed-risk signal, a safe simulation mode and a measured false-positive rate at the point of action."),
        H2("4.3 Functional Requirements"),
        P("Table 4.3 lists the functional requirements, the code that implements each and how it was verified. 'Tests' refers to the pytest suite in `tests/` (95 tests) and 'smoke' to `scripts/smoke_test.py` (25 backend checks); both pass."),
        TAB("Functional requirements and their verification", ["ID", "Requirement", "Implemented in", "Verification"],
            [["FR-1", "Capture packets on a chosen interface in rolling windows", "monitoring/packet_capture.py", "Error path tested (no Npcap); live capture not verified here"],
             ["FR-2", "Run a safe simulator through the same pipeline", "monitoring/simulator.py", "Tests (bounds, callback, start/stop); smoke; 25 probes"],
             ["FR-3", "Aggregate packets into ten features plus context", "monitoring/traffic_aggregator.py", "5 aggregator tests"],
             ["FR-4", "Validate every feature vector before prediction", "ml/features.py", "Tests for missing, non-numeric, NaN, infinite, negative values"],
             ["FR-5", "Classify a window as Benign or Attack with a confidence", "ml/model_loader.py, security/detector.py", "Tests: output shape, flood window is Attack, missing model reported"],
             ["FR-6", "Score distributed-traffic risk from 0 to 1", "security/distributed_analysis.py", "4 tests (levels, component sum, carpet-bombing wording)"],
             ["FR-7", "Grade severity Low to Critical and list the factors", "security/severity.py", "4 tests (cap, Critical case, persistence)"],
             ["FR-8", "Quarantine the top three non-protected sources on High or Critical; recommend rate limiting on Medium", "security/mitigation.py", "Tests for durations, doubling, protected addresses, duplicates"],
             ["FR-9", "Expire quarantines automatically and mark them recovered", "security/mitigation.py, database/db.py", "Expiry test with a controlled clock"],
             ["FR-10", "Store detections, mitigations, host health and settings", "database/db.py", "7 database tests; schema test"],
             ["FR-11", "Expose status, history, settings, control and model metrics through a REST API", "app.py", "32 API tests; smoke; 25 probes"],
             ["FR-12", "Validate settings (window 2 to 120 s, quarantine 5 to 3600 s)", "app.py", "Out-of-range and malformed-value tests and probes"],
             ["FR-13", "Show overview, detections, analytics, health, mitigation, model and settings in a console", "frontend/src/pages", "Console pages captured with data (Chapter 8)"],
             ["FR-14", "Show model metrics together with the data provenance", "app.py, Model page", "API test for provenance; screenshot of the warning"],
             ["FR-15", "Train and persist the model from CICIDS2017 CSV files or the fallback", "ml/train_model.py", "Run when the product was built; real-flow experiments reuse its pieces"]],
            widths=[0.55, 2.45, 1.7, 1.8], align=["c", "l", "l", "l"], size=9),
        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and measured status", ["Quality", "Requirement", "Status"],
            [["Responsiveness", "The API answers dashboard polling without visible delay", f"Median {min(d['p50_ms'] for d in A['latency']):.1f} to {max(d['p50_ms'] for d in A['latency']):.1f} ms per endpoint over HTTP (127.0.0.1)"],
             ["Decision latency", "The decision for a window is made within a fraction of the window", f"Median {L['detect_to_mitigation_ms']['p50']:.0f} ms, 95th percentile {L['detect_to_mitigation_ms']['p95']:.0f} ms from finished features to decision, on a host kept at 100 % CPU by other jobs"],
             ["Accuracy", "High accuracy and a low false-positive rate on real traffic", f"Not met by the shipped model on real flows ({k['shipreal_acc'] * 100:.1f} %); met after retraining ({k['rr_acc'][0] * 100:.2f} %)"],
             ["Explainability", "Every severity shows its contributing factors", "Met (factor list stored with each detection)"],
             ["Safety", "No change to the operating-system firewall; reversible actions", "Met by design: firewall function is a stub; quarantines expire"],
             ["Reliability", "Errors reported, not hidden; invalid input rejected", f"{A['probes_ok']} of {A['probes_total']} malformed-input probes behaved as intended; backend healthy afterwards"],
             ["Security", "Local-only service", "Servers bind to 127.0.0.1; no API authentication; interface name not length-checked"],
             ["Portability", "Windows and Linux; optional Docker", "Windows 11 tested; Docker files present but not run for this report"],
             ["Maintainability", "Tests and a single feature schema shared by training and inference", f"{F.PYTEST_PASSED} tests; `ml/features.py` is the single schema"]],
            widths=[1.2, 2.4, 2.9], align=["l", "l", "l"], size=9.5),
        H2("4.5 Hardware Requirements"),
        P("The product was developed and measured on an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory and Windows 11 Pro. No GPU is used. The shipped model is 2.74 MB and loads in a fraction of a second. "
          "A network interface is needed only for live capture; Simulation Mode needs none. Minimum hardware was not determined by experiment and no lower bound is claimed; peak memory use was not measured."),
        H2("4.6 Software Requirements"),
        TAB("Software used", ["Component", "Version used", "Role"],
            [["Python", "3.11.9 (3.11 or 3.12 recommended)", "Back end, training, tests"], ["Flask", "3.1.3", "REST API and legacy dashboard"],
             ["scikit-learn / joblib", "1.9.1 / 1.6.0", "Random Forest and model persistence"], ["pandas / NumPy / SciPy", "3.1.0 / 2.4.6 / 1.17.1", "Data handling"],
             ["Scapy / Npcap", "2.8.0 / required on Windows for live capture", "Packet capture"], ["psutil", "7.2.2", "Host health and local addresses"],
             ["matplotlib", "3.11.2", "Result plots"], ["pytest / requests", "9.1.1 / 2.34.2", "Tests and smoke checks"],
             ["Node.js with React / Vite / Tailwind / Recharts", "React 19.3, Vite 8.3, Tailwind 4.3, Recharts 3.10", "Console"],
             ["SQLite", "Bundled with Python", "Storage"], ["Browser", "Chrome, Edge or Firefox", "Console"]],
            widths=[2.2, 2.4, 1.9], align=["l", "l", "l"], size=10),
        P("A note on versions: the model was pickled with scikit-learn 1.9.0 and loaded with 1.9.1, which produces a warning but works; pinning the library version would remove it."),
        H2("4.7 User Roles"),
        P("The product has a single role, the administrator or analyst, who can start and stop sessions, change settings and read everything. The batch backlog also asks for registration, password reset and a separate privileged "
          "role for a security-operations analyst (US-101 to US-103). These were **not implemented**: the React console has a browser-side demonstration login (a fixed demo account stored in the browser) that only gates the pages, and the REST API has no authentication. "
          "Because both servers listen on 127.0.0.1 only, the exposure is limited to the local machine, but the product should not be put on a network interface as it stands."),
        H2("4.8 Data Requirements"),
        P(f"For training the product needs labelled flow records with, at least, forward and backward packet counts, forward and backward byte totals and the flow duration, which is what CICIDS2017 CSV files provide. "
          f"The documentation run used one such file with {k['real_rows']:,} rows. For operation it needs no external data: windows are built from packets, and the store is created on first start. "
          "The persistent data are the four SQLite tables (detections, mitigations, health samples, settings), the model files and the result files written by training."),
        TAB("The ten-feature schema shared by training and inference", ["Feature", "Meaning", "From a CICIDS2017 flow", "From a live window"],
            [["received_packets, received_bytes", "Count and bytes of received traffic", "Backward packets and bytes", "Packets whose destination is a local address (or neither end is local)"],
             ["received_packets_per_second, received_bytes_per_second", "Received rates", "Counts divided by flow duration", "Counts divided by window length"],
             ["average_received_packet_size", "Bytes per received packet (0 if none)", "Bytes / packets", "Bytes / packets"],
             ["sent_packets, sent_bytes", "Count and bytes of sent traffic", "Forward packets and bytes", "Packets whose source is local and destination is not"],
             ["sent_packets_per_second, sent_bytes_per_second", "Sent rates", "Counts divided by flow duration", "Counts divided by window length"],
             ["average_sent_packet_size", "Bytes per sent packet (0 if none)", "Bytes / packets", "Bytes / packets"]],
            widths=[1.9, 1.5, 1.5, 1.6], align=["l", "l", "l", "l"], size=9),
        P("The schema is the single contract between training and inference. Alongside the ten features the aggregator computes context that the classifier never sees (distinct sources and destinations, protocol shares, the busiest addresses), which the distributed-risk and mitigation steps use."),
        H2("4.9 Interface Requirements"),
        TAB("REST interface", ["Method", "Path", "Purpose"],
            [["GET", "/api/status", "Mode, interface, window, windows completed, latest detection, active quarantines, capture error"],
             ["GET", "/api/health", "Current and recent CPU, memory and network counters"], ["GET", "/api/interfaces", "Capture interfaces with addresses and state"],
             ["GET", "/api/detections?limit=n", "Stored detections (1 to 500) with counts by prediction and severity"], ["GET", "/api/detections/latest", "Most recent detection"],
             ["GET", "/api/mitigations", "Active quarantines and history"], ["GET, POST", "/api/settings", "Read or change window and quarantine length"],
             ["POST", "/api/monitor/start, /api/monitor/stop", "Start or stop live capture"], ["POST", "/api/demo/start, /api/demo/stop", "Start or stop Simulation Mode"],
             ["GET", "/api/model/metrics", "Metrics, feature importance, confusion matrix and provenance"]],
            widths=[0.9, 2.3, 3.3], align=["l", "l", "l"], size=9.5),
        P("The human interface is the React console on port 5415 (the original server-rendered dashboard remains on 8415). The packet interface is Scapy on the chosen network adapter. The only external file interface is the CSV reader of the training script."),
        H2("4.10 Use Cases"),
        TAB("Principal use cases", ["No.", "Use case", "Actor", "Main flow"],
            [["UC-1", "Start Simulation Mode", "Administrator", "Press Start simulation; windows are scored and shown"],
             ["UC-2", "Start live capture", "Administrator", "Choose interface and window, press Start live; the session reports a capture error if the driver is missing"],
             ["UC-3", "Investigate a detection", "Administrator", "Open Detections, select a row, read the factors and the recommendation"],
             ["UC-4", "Watch quarantines", "Administrator", "Open Mitigation, see countdowns and history"],
             ["UC-5", "Adjust settings", "Administrator", "Change window or quarantine length; invalid values are refused"],
             ["UC-6", "Check the model", "Administrator", "Open Model; read metrics and the synthetic-data warning"],
             ["UC-7", "Retrain the model", "Developer", "Place CSV files in data/raw and run the training script"]],
            widths=[0.6, 1.7, 1.2, 3.0], align=["c", "l", "l", "l"], size=10),
        P("The use-case diagram in Chapter 5 shows these cases with their actors."),
        H2("4.11 Existing and Proposed Systems Compared"),
        TAB("Existing approaches and SentinelFlow", ["Aspect", "Existing (offline classifier, base paper)", "SentinelFlow"],
            [["Input", "Stored flow datasets", "Live packets or simulated windows, plus offline flow files for training"],
             ["Decision", "Label per flow", "Label per window plus distributed risk and severity"],
             ["Action", "None (future work)", "Temporary quarantine with automatic recovery, rate-limit advice"],
             ["Explanation", "Feature importance", "Per-decision factor list"],
             ["Resource profile", "Training time, inference time, memory, model size", f"Model size, decision latency (median {L['detect_to_mitigation_ms']['p50']:.0f} ms under load), API latency"],
             ["Reported accuracy", "100 % on SDN and CIC-DDoS2023", f"{k['ship_acc'] * 100:.2f} % synthetic (shipped); {k['shipreal_acc'] * 100:.1f} % shipped on real flows; {k['rr_acc'][0] * 100:.2f} % retrained on real flows"]],
            widths=[1.3, 2.4, 2.8], align=["l", "l", "l"], size=9.5),
        H2("4.12 Constraints and Assumptions"),
        B("Window length: the model assumes ten-second windows; other lengths change the rates the model sees.",
          "Orientation: forward flow direction is treated as sent and backward as received; live orientation follows local interface addresses.",
          "Privilege: live capture needs Administrator rights and Npcap on Windows.",
          "Safety: no operating-system firewall rule is ever written; the quarantine is a decision inside the application.",
          "Data: the real-data evaluation covers one attack type (the DDoS day of CICIDS2017) and a random split of flows; the dataset has known labelling problems.",
          "Scope: a single administrator role, local access only, binary classification."),
    ]


def blocks():
    return feasibility_blocks() + requirements_blocks()
