"""Chapter 7: System Testing for SentinelFlow. Counts come from the recorded test runs (docs/metrics/*.txt); timings from F.LAT and F.API."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB

# pytest cases collected per file (parametrised cases counted separately); they add up to F.PYTEST_TOTAL
N_API, N_FEAT, N_MODEL, N_PIPE = 32, 24, 13, 26
assert N_API + N_FEAT + N_MODEL + N_PIPE == F.PYTEST_TOTAL

_PROBE_NOTE = {
    "demo/start twice -> 409": "first start (200); the second start is the next row",
    "array JSON body": "accepted and ignored (a list has no keys)",
    "very long interface name accepted but not echoed unsafely": "stored without a length check",
    "live capture start without Npcap": "start returns 200, then status.capture_error names Npcap",
}


def _probe_rows():
    rows = []
    for p in F.API["probes"]:
        exp = p["expected"]
        exp = "/".join(str(e) for e in exp) if isinstance(exp, list) else str(exp)
        rows.append([f"{p['method']} {p['path']}".replace("%2f", "/"), p["name"], exp, str(p["status"]), "pass" if p["ok"] else "FAIL"])
    return rows


def _lat_rows():
    seen, rows = set(), []
    for d in F.API["latency"]:
        key = (d["method"], d["path"], d["n"])
        if key in seen:
            continue
        seen.add(key)
        rows.append([d["method"], d["path"], str(d["status"]), str(d["n"]), f"{d['p50_ms']:.1f}", f"{d['p95_ms']:.1f}", f"{d['max_ms']:.0f}"])
    return rows


def blocks():
    L, A = F.LAT, F.API
    comp = [("Aggregate packets into features", "aggregate_ms"), ("Random Forest prediction (`n_jobs=-1` as saved)", "predict_ms"), ("Distributed risk + severity", "risk_severity_ms"),
            ("Mitigation decision (includes SQLite writes)", "mitigate_ms"), ("Store the detection row (SQLite)", "db_ms"), ("Whole window, aggregate to stored", "total_ms"),
            ("Detection to mitigation decision", "detect_to_mitigation_ms")]
    lat_rows = [[n, f"{L[k]['mean']:.1f}", f"{L[k]['p50']:.1f}", f"{L[k]['p95']:.1f}", f"{L[k]['max']:.0f}"] for n, k in comp]
    n1, n_1 = L["single_inference_ms_n_jobs_1"], L["single_inference_ms_n_jobs_-1"]
    b = [H1("7. SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("SentinelFlow was delivered with one end-to-end script, `scripts/smoke_test.py`, and a screenshot script. The documentation run added an automated pytest suite in `tests/`, a probe script for malformed input and API timing "
            "(`scripts/measure_api.py`), and the experiment script that measures model quality (`scripts/run_experiments.py`). The pipeline modules are mostly plain functions (feature validation, CICIDS2017 mapping, packet aggregation, "
            "distributed risk, severity), so they are tested at unit level on small constructed inputs with exact or tolerance assertions. The Flask application is tested through its test client, and the live behaviour through the "
            "smoke script and the probe script against a running server. Whether the model separates real attacks from real traffic is a different question from whether the software is correct; no unit test can settle it, so it is measured "
            "separately in Chapter 8."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest: tests/test_features_preprocessing.py, test_pipeline_modules.py, test_model_db.py (schema, preprocessing, aggregator, risk, severity, mitigation, simulator, model loader, database)", f"{N_FEAT + N_PIPE + N_MODEL} cases", "All passed"],
               ["API / integration", "pytest with the Flask test client: tests/test_api.py (every endpoint, validation, the shared `process_window()` pipeline, simulation end to end)", f"{N_API} cases", "All passed"],
               ["Functional (live backend)", f"scripts/smoke_test.py against a running backend (127.0.0.1:8915, a scratch copy)", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Security / robustness", "scripts/measure_api.py malformed-input probes", f"{A['probes_total']} probes", f"{A['probes_ok']} of {A['probes_total']} behaved as intended"],
               ["Performance", "scripts/run_experiments.py latency (600 windows), scripts/measure_api.py (100 calls per endpoint)", "600 windows; 15 endpoint rows", "Section 7.7"],
               ["Screens", "scripts/capture_screens.py (Playwright, Chrome, 1440 x 900)", "12 captures", "Chapter 8"]],
              widths=[1.2, 3.3, 1.1, 1.1], align=["l", "l", "l", "l"], size=9.5),
          P("All tests ran on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, Python 3.11.9, scikit-learn 1.9.1, Flask 3.1, no GPU, no Npcap. Other programs kept the CPU near 100 % during the runs, "
            f"so the full pytest run took 114 s instead of the few seconds it needs on an idle machine, and every timing in Section 7.7 is an upper bound. The tests use a scratch SQLite file; none writes to `data/sentinelflow.db`.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The suite has **{F.PYTEST_TOTAL} test cases in four files, and all {F.PYTEST_PASSED} passed** (`docs/metrics/pytest.txt`). `tests/conftest.py` gives every test a scratch database and resets the module-level state of `app.py` "
            "(active quarantines, rolling baseline, persistence counter, quarantine length) so tests do not influence one another; it also supplies one flood-like and one benign feature vector."),
          TAB("Unit and component tests, by file.",
              ["File (cases)", "What is asserted"],
              [[f"test_features_preprocessing.py ({N_FEAT})",
                "The schema has ten unique features; `validate_feature_dict` returns values in schema order and rejects a missing feature, non-numeric values (text, `None`, a list), NaN, positive and negative infinity and negative numbers; "
                "column names are normalised to snake case; label strings (`BENIGN`, `Normal`, `0`, `DDoS`, `PortScan`, `1`) map to Benign or Attack; the CICIDS2017 mapping sends forward to sent and backward to received, divides by the duration, "
                "gives an average of zero (not NaN) when a direction has no packets and survives a zero duration; infinities become NaN"],
               [f"test_pipeline_modules.py ({N_PIPE})",
                "Aggregator: orientation of sent versus received, external transit counted as received, empty window all zero, malformed packet skipped, top sources ranked, protocol shares. Distributed risk: low for concentrated benign traffic, "
                "High for wide spread at a high rate, components add up to the score, carpet-bombing wording for many destinations. Severity: a benign window never exceeds Medium, a confident wide attack is Critical with at least five listed factors, "
                "persistence adds exactly ten points. Mitigation: High quarantines the top three sources, Critical doubles the duration, Medium recommends a rate limit and Low only monitors, protected addresses (127.0.0.1, 192.168.1.20, unknown) "
                "are never quarantined, a duplicate quarantine is ignored, a quarantine expires and its history row becomes `recovered`, the countdown is correct, the duration has a floor of 5 s, the firewall stub reports `applied: False`. "
                "Simulator: packet lengths stay within 40-1,500 bytes, attack windows are more than twice as large as benign ones, start/callback/stop and a refused second start"],
               [f"test_model_db.py ({N_MODEL})",
                "The model artefacts exist and load; a prediction has the shape `{prediction, label, confidence}` with confidence in [0.5, 1]; a volumetric flood window is classified Attack; a bad feature dictionary raises; an untrained state raises "
                "`FileNotFoundError`; the stored `metrics.json` agrees with `confusion_matrix.json` (4,800 rows, accuracy, precision and recall recomputed). Database: detection round trip and newest-first order, counts by prediction and severity, limit, "
                "mitigation recovery, chronological health history, setting overwrite, exactly four tables"],
               [f"test_api.py ({N_API})",
                "See Section 7.3"]],
              widths=[1.7, 4.8], align=["l", "l"], size=9.0),
          P("Two tests are worth singling out because they guard numbers quoted elsewhere in this report. The metrics-consistency test recomputes accuracy, precision and recall from the stored confusion matrix, so the figures the Model page "
            "displays cannot drift from the matrix. The benign-cap test confirms that a window the forest calls Benign can never be scored above Medium, which is what prevents a benign window from triggering a quarantine.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration testing"),
          P(f"The {N_API} cases of `tests/test_api.py` drive the Flask application through its test client against the shipped model. They cover the idle status shape, a JSON 404 for an unknown route, the interface list, six out-of-range or non-numeric "
            "settings values (all 400), the accepted and persisted settings, malformed JSON tolerated, an invalid `limit` (400) and a clamped one, the empty-state message of `/api/detections/latest`, the model-metrics endpoint "
            "(it reports the synthetic provenance and ten importances), the PNG result images, the dashboard page and the health endpoint."),
          P("The central integration tests call `process_window()` directly, the function that both the live engine and the simulator use. A flood-like window returns Attack, High or Critical severity, the action `quarantine`, a stored row id and three "
            "active quarantines; a benign window returns Low or Medium and no quarantine; a capture error is passed through as `{error}`; a feature-validation error is reported as `Feature validation failed`. After processing, the detection is visible through "
            "`/api/detections` with its factor list, through `/api/detections/latest`, and through `/api/mitigations` (three active rows, three history rows, a 40 s quarantine length)."),
          P("The simulation tests start the simulator through `/api/demo/start`, check that a second start and a live start are refused with 409, wait until the first scored window appears in `/api/detections` (source `simulation`), and stop it. "
            "Six further cases try the bad `window_seconds` values 1, 500 and text on both start endpoints (all 400).")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing"),
          P(f"`scripts/smoke_test.py` was run against a running backend (a scratch copy of the code on port 8915 so the shipped database was untouched). **All {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks passed** (`docs/metrics/smoke_test.txt`): status, interfaces, settings "
            "(two rejections, one save, persistence), start of the simulation, refusal of a second start and of a live start while simulating, the simulation reporting its mode, at least four newly scored windows, every field the console reads in a detection row, "
            "the detail keys (features, distributed, severity, actions), valid severity keys, `/api/detections/latest`, a 400 for a bad limit, the mitigation and health shapes, the model metrics and the three result images, stop and the return to `stopped`. "
            "The script has three further checks (the React server, its proxy of `/api` and of `/static/results`); they were skipped because the Vite server was not running during this measurement, and the console pages themselves were exercised "
            "by the screenshot run described in Chapter 8."),
          P(f"In the same session the probe script started the simulator at 2 s windows: the first scored detection appeared {A['first_detection_after_start_seconds']:.1f} s after pressing Start, and {A['live_sim_windows_scored']} windows were scored in the observation period "
            f"({A['live_sim_by_prediction'].get('Attack', 0)} Attack, {A['live_sim_by_prediction'].get('Benign', 0)} Benign) with {A['live_sim_quarantines_recorded']} quarantine rows recorded.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("SentinelFlow is a localhost tool: the servers bind to 127.0.0.1, the React login is a browser-side demo gate and the REST API has no authentication. Security testing therefore concentrated on what a hostile or careless client could do through the API: "
            f"malformed numbers, injection-looking strings, path traversal on the file route, wrong HTTP methods, state-machine abuse and oversized values. **{A['probes_ok']} of {A['probes_total']} probes behaved as intended and the backend answered normally afterwards.**"),
          TAB("Malformed-input and abuse probes (scripts/measure_api.py).",
              ["Request", "Probe", "Expected", "Got", "Result"], _probe_rows(), widths=[2.2, 2.4, 0.7, 0.5, 0.6], align=["l", "l", "c", "c", "c"], size=8.5),
          P("Three observations qualify the clean result. First, the probe named `array JSON body` shows that a JSON list posted to `/api/settings` is accepted and ignored (status 200) instead of being rejected; it is harmless but sloppy. "
            "Second, the `interface` setting accepts a 5,000-character string; the value is stored in memory and is only used as an interface name for a capture that would then fail, but there is no length or character check. "
            "Third, the API has no authentication, authorisation or rate limiting at all: anyone who can reach port 8415 can start and stop monitoring or change the quarantine length. That is acceptable for a service bound to the loopback address and "
            "would not be acceptable beyond it. The SQL-looking `limit` value is rejected by integer parsing, and all queries use bound parameters, so injection through the API was not possible in the probes tried."),
          P("Path traversal on `/static/results/<path>` returned 404 for both the encoded and the plain `..` forms because the route uses Flask's `send_from_directory`. The mitigation module never executes a command: the operating-system firewall hook is a stub that returns "
            "`applied: False`, so a forged address cannot make SentinelFlow run a shell command. The one input that reaches Scapy is the interface name; it is passed as a function argument, not to a shell.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          TAB("Edge cases and how SentinelFlow behaved.",
              ["Case", "How tested", "Observed behaviour"],
              [["Window with no packets", "aggregator unit test", "All ten features are zero, `top_sources` empty, no division by zero"],
               ["Direction with zero packets (average size)", "preprocessing and aggregator tests", "Average size is 0.0, not NaN"],
               ["Flow with zero duration", "preprocessing test", "Duration is clipped to 1e-6 s; rates stay finite"],
               ["NaN, infinity, negative or non-numeric feature", "validation tests (8 cases)", "`ValueError`; `process_window` returns `{error: 'Feature validation failed: ...'}`"],
               ["Missing feature", "validation and API tests", "Names the missing features"],
               ["Model file missing", "detector test with `is_trained` patched", "`FileNotFoundError` with the instruction to run `python ml/train_model.py`; the status endpoint reports `model_trained: false`"],
               ["Capture without Npcap", "probe run on this machine", "Start returns 200; the capture thread reports 'Packet capture driver unavailable ... Install Npcap or use Simulation Mode'; status shows `capture_error` and returns to `stopped`; no stored row"],
               ["Second start while a session runs", "API and smoke tests", "HTTP 409 for both start endpoints"],
               ["Window length outside 2-120 s, quarantine outside 5-3600 s", "API tests and probes", "HTTP 400 with an explanatory message"],
               ["Attack sources that are the host itself or loopback", "mitigation tests", "Never quarantined; the action becomes `rate_limit_recommended`"],
               ["Same source flagged in consecutive windows", "mitigation test", "The second quarantine is ignored while the first is active (one history row)"],
               ["Quarantine reaches its end", "mitigation test with patched clock", "Removed from the active list; history row marked `recovered`"],
               ["Benign window with high model confidence", "severity test", "Capped at 45 points, so never High or Critical"]],
              widths=[2.0, 1.7, 2.8], align=["l", "l", "l"], size=9.0),
          P("One edge case could not be tested end to end: live capture of real traffic. Npcap is not installed on the test machine, so the capture engine's success path, its handling of IPv6 packets and its orientation rule on a real interface "
            "were reviewed in the source and exercised only through the aggregator tests and the simulator.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P(f"Two kinds of timing were measured. The first is the cost of processing one monitoring window, measured over {L['windows']} simulated windows of 10 s with {L['mean_packets_per_window']:.0f} packets on average (up to {L['max_packets_per_window']}), "
            "using the product's own aggregator, detector, risk and severity code, mitigation manager and SQLite writes. The second is the latency of the REST endpoints over real HTTP on 127.0.0.1 (the name `localhost` adds about two seconds per call on this machine because of an IPv6 fallback)."),
          TAB("Per-window processing time in milliseconds (600 windows; host CPU at 100 % from other jobs).",
              ["Step", "Mean", "Median", "95th pct", "Max"], lat_rows, widths=[3.1, 0.8, 0.8, 0.9, 0.8], align=["l", "r", "r", "r", "r"], size=9.5),
          FIG(F.fig("f08_latency_breakdown.png"), "Where the time goes in one window, and the cost of the saved `n_jobs=-1`.", 6.0),
          P(f"The forest dominates: its median is {L['predict_ms']['p50']:.0f} ms of a {L['total_ms']['p50']:.0f} ms window, while aggregation takes about {L['aggregate_ms']['p50']:.0f} ms and the rule layer well under a millisecond. The cause is a configuration detail, not the model: the saved forest has "
            f"`n_jobs=-1`, so even a single-row prediction pays for a thread pool. With `n_jobs=1` the median single-window inference drops from {n_1['p50']:.0f} ms to {n1['p50']:.0f} ms ({n_1['mean']:.0f} ms and {n1['mean']:.0f} ms means). "
            f"The decision from the finished feature vector to the mitigation decision took a median of {L['detect_to_mitigation_ms']['p50']:.0f} ms (95th percentile {L['detect_to_mitigation_ms']['p95']:.0f} ms, maximum {L['detect_to_mitigation_ms']['max']:.0f} ms) on this loaded machine. "
            "Both numbers are far smaller than the monitoring window itself, which is the real delay of the design: a window must close (10 s by default, 2 s at the shortest setting of the demo) before it can be classified. "
            f"Loading the model takes {L['model_load_seconds']} s and the file is {L['model_file_mb']} MB."),
          TAB("REST API latency over HTTP on 127.0.0.1 (milliseconds).",
              ["Method", "Endpoint", "Status", "Calls", "Median", "95th pct", "Max"], _lat_rows(), widths=[0.6, 2.6, 0.6, 0.5, 0.7, 0.8, 0.6], align=["l", "l", "c", "c", "r", "r", "r"], size=9.0),
          FIG(F.fig("f09_api_latency.png"), "Median and 95th-percentile latency of the GET endpoints.", 5.4),
          P("Every endpoint answers in a median of 36 ms or less, including the 500-row detection list, which is dominated by JSON encoding. The slowest is the interface listing (Scapy and psutil are queried on every call); the maxima of 134-214 ms are single outliers on the loaded host. "
            "No load test was run: the API was exercised by one client at a time, so nothing is known about concurrent users, and the throughput of live capture under a real flood (Scapy's `sniff()` is a pure-Python capture loop) was not measured.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance"),
          P("No user study was run: the project team and its guide used the console, but there were no external users and no structured feedback, so nothing here is a measured acceptance result. What can be said is how the verified behaviour maps to the six objectives of the batch "
            "and to the user stories listed in the batch's `19.USER_STORIES.xlsx` (which describe an administrator who registers, submits flows, runs detection and mitigation, views results and exports reports)."),
          TAB("Objectives against what was verified by testing.",
              ["#", "Objective", "Verified by", "Status"],
              [["1", "Acquire a benchmark dataset and extract flow features", "Preprocessing tests; real CICIDS2017 DDoS-day file mapped and scored (Chapter 8)", "Partly: shipped model not trained on it"],
               ["2", "Capture live traffic and compute the same features", "Aggregator tests; simulator; capture error path", "Implemented; not run live"],
               ["3", "Train a classifier for DDoS versus legitimate traffic", "Model tests; experiments of Chapter 8", "Done; shipped model synthetic-trained"],
               ["4", "Adaptive mitigation that rate-limits or blocks sources", "Mitigation tests (quarantine, expiry, protection)", "Partly: application-level only"],
               ["5", "Dashboard of traffic, detections and mitigation", "Smoke test; 12 screenshots", "Done"],
               ["6", "Evaluate accuracy, false positives, detection-to-mitigation time", "Experiments and timings of Chapters 7-8", "Done; no real attack timeline"]],
              widths=[0.3, 2.5, 2.4, 1.3], align=["c", "l", "l", "l"], size=9.0),
          P("Several user stories describe features that the product does not have: registration and password reset (the console has a demo gate only), roles, file submission of flows, notifications and export of reports. They were not tested because they do not exist. "
            "The stories that match built functionality (a results dashboard, a view of detections and their history with filtering, an explanation of why a window was flagged, an API for detection and mitigation) pass the checks above.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing done"),
          B("**No live capture.** Npcap is not installed, so no real packet was captured and the capture engine's success path was never executed; the simulator drives the same downstream code.",
            "**No real attack.** No attack traffic was generated or captured; the attack windows come from the product's simulator, and the real-data evidence is offline flow data (Chapter 8). Time from the first attack packet to a quarantine was therefore not measured.",
            "**No load or concurrency test.** One client at a time; no long soak run (the longest simulation observed was a few hundred windows); no memory-growth measurement of the in-memory baseline and detection buffers beyond what the screenshots show.",
            "**One machine, a loaded one.** All timings were taken with other jobs holding the CPU at 100 %; they are upper bounds and shift from run to run.",
            "**Scratch data.** Tests and probes ran on scratch databases; the 12 screenshots were captured earlier from the product's own database.",
            "**Front end.** There are no automated front-end tests; the React pages were checked through the Playwright screenshot run and by eye. The three proxy checks of the smoke script were not executed in the final run.",
            "**Statistical validity.** Model quality was measured on one real attack day of one dataset with a random flow split and a block split; both splits share capture conditions with the training data.")]
    return b
