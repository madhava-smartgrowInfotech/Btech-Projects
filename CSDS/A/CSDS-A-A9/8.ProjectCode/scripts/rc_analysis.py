"""Chapters 3 and 4 content: feasibility study, existing and proposed system, requirements, platform and roles (ForgetSafe)."""
from __future__ import annotations

from doc_common import CHARTS, PRODUCT, metrics

_api = metrics("api")["latency"]
_b = metrics("baseline")
_sc = metrics("scaling")["rows"]
TRAIN_P50 = _api["POST /api/train"]["p50_ms"]
UNL_P50 = _api["POST /api/unlearn"]["p50_ms"]
UNL_P95 = _api["POST /api/unlearn"]["p95_ms"]
STATE_P50 = _api["GET /api/state (trained)"]["p50_ms"]
HEALTH_P50 = _api["GET /api/health"]["p50_ms"]
TRAIN_MS = _b["training"]["train_ms"]
_nn = metrics("neural_adapter")
_tl = metrics("timeline")
_ld = metrics("load_test")
_sp = metrics("security_probe")
_ac = metrics("acceptance")
NN_RUN_S = _nn["runtime_seconds"]
NN_T = _nn["summary"]["timing"]
NN_PARAMS = _nn["base"]["base_parameters"]
NN_CLIENTS = _nn["config"]["n_clients"]
SP = _sp["classification_counts"]
_scen = _ld["scenarios"]
_levels = sorted({x["concurrency"] for v in _scen.values() for x in v["levels"]})
ZERO_ERR_MAX = max(c for c in _levels if all(x["errors_5xx_or_connection"] == 0 for v in _scen.values() for x in v["levels"] if x["concurrency"] <= c))
STATE_MAX_RPS = max(x["requests_per_s"] for x in _scen["GET /api/state"]["levels"])
RACE = _ld["races"]
SOAK = _ld["soak"]


def sec_feasibility_technical(d):
    d.h2("Technical Feasibility")
    d.p("Technical feasibility asks whether the required technology exists, whether the team could use it, and whether the result performs acceptably. For ForgetSafe the "
        "answer was settled by choosing a deliberately small technology set.")
    d.p("**Technology.** The back end uses only the Python standard library: `http.server` for the API, `dataclasses`, `hashlib`, `json`, `random` and `math` for "
        "the engine, and `tkinter` for the optional desktop interface. There is no dependency to install for the engine, the API or the tests. The front end uses "
        "React 19 with Vite 8, React Router, Recharts and a few presentation libraries, and is optional: the original single-page interface served at `/` needs no build. "
        "The neural adapter study adds PyTorch 2.14 (CPU build) and NumPy. All components are mature and freely available.")
    d.p("**Skills.** The mathematics needed (vector norms, Gaussian noise, the Gaussian mechanism, AUC) is undergraduate level and was implemented directly. The "
        "federated-learning and unlearning concepts were learned from the surveyed papers [9], [12], [13], [17]. Only the neural study uses a deep-learning framework, and no GPU programming was "
        "needed, which is why the whole project is feasible on a classroom computer.")
    d.p(f"**Performance.** On the measurement machine, training the five-client proxy takes about {TRAIN_MS:.0f} ms inside the engine and about {TRAIN_P50:.0f} ms through the API "
        f"(median); an unlearning request takes a median of {UNL_P50:.0f} ms through the API (95th percentile {UNL_P95:.0f} ms), including the attack, the metrics and the ledger write. "
        "These times are far inside what an interactive demonstration needs. The scaling experiment (Chapter 8) shows that the cost of a request does not grow with the amount "
        f"of client data in the way retraining does: from 100 to 500 synthetic clients, `unlearn()` rises from {_sc[2]['unlearn_ms_median']:.0f} ms to {_sc[4]['unlearn_ms_median']:.0f} ms "
        f"while re-running the proxy training rises from {_sc[2]['full_retrain_ms_median']:.0f} ms to {_sc[4]['full_retrain_ms_median']:.0f} ms. This applies to the proxy only.")
    if not getattr(d, "report", False):
        d.figure(CHARTS / "c08_scaling.png", "Median cost of a removal request and of retraining the proxy as the number of clients grows (5 repetitions per point)", width=4.4)
    d.p(f"**Technical risks and how they were retired.** Two risks were identified at the start: a real language model could not be trained on the available CPU-only machine, and "
        "a formal certificate for a non-linear model is a research problem. The design isolates the model behind `CharacterLanguageModel` and `clipped_update`, and the first risk "
        f"was retired at small scale by substituting low-rank adapters of a frozen {NN_PARAMS:,}-parameter recurrent network for {NN_CLIENTS} synthetic clients: the full experiment "
        f"(5 seeds, a sweep of 9 noise levels, retraining baselines) ran in {NN_RUN_S:.0f} s on the workstation. The second risk remains a research question; the project reports what "
        "its certificate establishes and what it does not. Pre-trained billion-parameter models are outside the hardware, so the project is feasible as a demonstrator and not as a production system.")


def sec_feasibility_economic(d):
    d.h2("Economic Feasibility")
    d.p("Economic feasibility compares costs with benefits. No monetary figures were recorded for this project, so none are invented here; the analysis is qualitative and "
        "uses measured quantities where they exist.")
    d.table([["Item", "Demonstrator (this project)", "Production extension (not built)"],
             ["Software licences", "None: Python, Node.js, React, Vite and Recharts are open source", "Same, plus any managed services chosen"],
             ["Compute", f"One CPU-only workstation (i5-12500, 15.7 GB); the bigram product runs in milliseconds and the whole neural study in {NN_RUN_S:.0f} s", "GPU compute for LLM fine-tuning and for each retraining baseline"],
             ["Storage", "One tracked vector of 1,089 values per client (about 8.7 kB at 64-bit precision) and a JSONL ledger", "One adapter-sized tensor per client (per round if rounds are tracked), encrypted at rest, plus signed ledger storage"],
             ["Development effort", "Student project effort", "Engineering effort for secure aggregation, privacy accounting, signing and access control"],
             ["Operating cost per request", "Negligible (tens of milliseconds)", "Depends on the model; the aim is to be far below a full retrain"]],
            "Cost elements of the demonstrator and of a production extension", widths=[0.2, 0.4, 0.4], font=10)
    d.p(f"The benefit of the approach is the avoided cost of retraining for each deletion request and the reduced risk of being unable to show compliance. The avoided cost is measured on the neural "
        f"adapters: removing a client takes {NN_T['subtract_us_median']:.0f} microseconds ({NN_T['unlearn_with_metrics_ms_median']:.0f} ms with the attack and metrics) against "
        f"{NN_T['retrain_seven_adapters_s_median']:.1f} s for retraining the seven retained adapters, a factor of {NN_T['speedup_retrain_over_unlearn_with_metrics']:.0f} with metrics. The factor grows with the "
        "cost of one adapter fine-tune, and it is expressed in measured time on the workstation that was already available.")


def sec_feasibility_operational(d):
    d.h2("Operational Feasibility")
    d.p("Operational feasibility asks whether the intended users can work with the system. The intended users are the operator of a federated training service, who carries out "
        "a removal request on behalf of a data owner, and a compliance auditor, who inspects the record afterwards (Section on user roles below).")
    d.bullets([
        "**Ease of use.** The workflow is four steps shown in order in the interface: train, unlearn, explore, audit. Each screen explains its own empty state and offers the "
        "next action, and destructive actions (removal, retraining, a new session) ask for confirmation.",
        "**Installation.** `run.bat` starts the API on port 8109 and the web interface on port 5109 and installs front-end dependencies on first run; `python app.py` alone "
        "starts the original interface with no installation.",
        "**Maintenance.** The engine is under 300 lines and the model under 130; the API has nine routes; the tests run in under a second. A maintainer can read the whole back end in one sitting.",
        f"**Behaviour under load.** Up to {ZERO_ERR_MAX} concurrent clients produced no failed request in any scenario; at 64 clients `/api/state` reached {STATE_MAX_RPS:.0f} requests per second at most and some requests failed (Chapter 7). "
        f"The {_ac['journeys']} scripted acceptance journeys completed with a mean of {_ac['mean_duration_s']:.0f} s each.",
        "**Constraints on operation.** The system keeps one global session in memory, has no login, and loses the trained model when the server restarts (the ledger survives). It "
        "is suitable for a laboratory demonstration and not for shared or unattended operation.",
    ])


def sec_feasibility_schedule(d):
    d.h2("Schedule Feasibility")
    d.p("The dates below are those recoverable from the project's git history and file modification times (`experiments/timeline/metrics.json`); each row names its evidence.")
    rows = [["Date", "Phase", "Evidence"]]
    for ph in _tl["phases"]:
        rows.append([ph["date"].replace(" to ", " - "), ph["phase"], ph["evidence"].split(";")[0]])
    d.table(rows, "Phases of the work with dates taken from git", widths=[0.17, 0.45, 0.38], font=9)
    d.p("The backend arrives in a single commit (2026-09-25), the React front end three weeks later on top of the unchanged API, and the measurement and documentation work in the final "
        "week. The schedule was feasible because the scope was fixed to models that run in milliseconds or minutes on one workstation; a version built on a pre-trained LLM would add data preparation, "
        "training time and hardware procurement.")


def sec_feasibility_summary(d):
    d.h2("Advantages and Constraints Summary")
    d.table([["Dimension", "Verdict", "Basis", "Main constraint"],
             ["Technical", "Feasible as a demonstrator", f"Standard-library back end; 5 unit tests and 14 smoke checks pass; neural adapter study in {NN_RUN_S:.0f} s on the CPU", "Scale: pre-trained billion-parameter LLMs are outside the hardware"],
             ["Economic", "Feasible; benefit not quantified", "No licences; one workstation", "Production costs (compute, secure storage) not estimated"],
             ["Operational", "Feasible for a laboratory demonstration", "Four-step workflow, confirmations, one-command start", "No authentication, one shared session, model not persisted"],
             ["Schedule", "Feasible at this scope", "Small code base and fast tests; dated phases from git", "A pre-trained-LLM version would need much longer"]],
            "Feasibility summary", widths=[0.15, 0.2, 0.35, 0.3], font=10)
    d.p("The advantages are low cost, transparency (every number can be reproduced by the scripts in `scripts/`) and an architecture that separates the model from the "
        "verification and audit logic. The constraints are the scale of the models, the lack of access control and the conditions under which the evidence is informative, which are stated once "
        "in the scope document and Chapter 9.")


def sec_existing(d):
    d.h2("Existing System and Its Limitations")
    d.p("The batch's literature survey lists four existing practices for handling a deletion request in a federated or machine-learning pipeline:")
    d.numbered([
        "Full retraining of the model without the deleted client's data.",
        "Approximate unlearning through gradient ascent or heuristic weight adjustment.",
        "SISA-style sharded training that retrains only the affected shards [12].",
        "Differential privacy during training to limit the influence of individual data [10], [11].",
    ])
    d.p("Their limitations, again from the batch survey and confirmed by the papers read, are:")
    d.table([["Limitation", "Where it bites", "Which practices"],
             ["Too expensive for large federated LLMs", "Every deletion triggers a repeat of fine-tuning", "Full retraining"],
             ["No formal guarantee that data is forgotten", "A regulator cannot be shown more than the operator's assertion", "Gradient ascent and heuristic edits"],
             ["Not verifiable or auditable", "No record that outlives the session and exposes edits", "All four"],
             ["Aggressive unlearning degrades utility", "The model forgets more than the target data", "Approximate methods"],
             ["Mostly designed for centralised models", "Client updates, aggregation and stored history are not used", "Sharding, gradient methods"]],
            "Limitations of existing practice", widths=[0.34, 0.4, 0.26], font=10)


def sec_proposed(d):
    d.h2("Proposed System and Its Advantages")
    d.p(f"{PRODUCT} implements a federated unlearning workflow with five parts. Clients hold their own records inside the engine; each contributes only an L2-clipped "
        "update. The coordinator aggregates the updates with Gaussian noise into a global model. When a client asks to be forgotten, the coordinator subtracts that client's stored "
        "update and renormalises over the remaining clients; no record of the client is read again. The result is verified against a recomputation, measured with a membership-inference "
        "attack and a utility check, written as a certificate, and chained into the audit ledger.")
    d.table([["Advantage", "How it arises", "Qualification"],
             ["No retraining step", "Removal is a vector subtraction over a fixed-size parameter vector", "Exact only because the aggregate is a one-shot sum of independent updates"],
             ["Inspectable evidence", "Each request yields a certificate and a ledger record", "Strength of the evidence depends on the noise setting"],
             ["Bounded release", "Clipping bounds each client's influence; noise gives an (epsilon, delta) statement", "Classical bound valid only for epsilon below 1; not re-accounted after removal"],
             ["Tamper evidence", "SHA-256 chain verified on demand", "No signature or anchor; truncation and re-hashing undetected"],
             ["Separation of concerns", "Model, engine, ledger and interface are separate modules", "Demonstrated with neural adapters (Chapter 8); larger models are outside the project's scope"]],
            "Advantages of the proposed system and their qualifications", widths=[0.2, 0.42, 0.38], font=10)


def sec_requirements_functional(d):
    d.h2("Functional Requirements")
    d.p("Each functional requirement is traced to the endpoint and screen that implement it and to the test that exercises it. Tests are the five unit tests in "
        "`tests/test_end_to_end.py` (U1 workflow, U2 repeat rejection, U3 tamper detection, U4 certificate export, U5 health and state) and the 14 checks of `scripts/smoke_test.py` (S).")
    d.table([["ID", "Requirement", "Endpoint / screen", "Verified by"],
             ["FR1", "Train the global model across the five clients and report epsilon, delta, perplexity, accuracy and a model hash", "POST /api/train; Federated training", "U1, S"],
             ["FR2", "Show each client's record count, original and clipped norm, clip scale and state", "GET /api/state; Training, Dashboard", "U5, S"],
             ["FR3", "Start a new session while preserving audit history", "POST /api/session; Federated training", "S"],
             ["FR4", "Remove a chosen active client by subtracting its tracked update and renormalising", "POST /api/unlearn; Certified unlearning", "U1, S"],
             ["FR5", "Issue a certificate with status, privacy parameters, reference and residual distance, AUC and perplexity before and after, retention, model hashes and ledger hash", "POST /api/unlearn response; certificate card", "U1, S"],
             ["FR6", "Download the latest certificate as JSON together with the ledger verification result", "GET /api/certificate/latest", "U4, S"],
             ["FR7", "Reject invalid requests: untrained model, unknown client, client already removed, removal of the last client, missing client id", "POST /api/unlearn error responses", "U2, S, edge-case study"],
             ["FR8", "Generate a text sample from the current model for a seed text", "POST /api/generate; Model explorer", "S"],
             ["FR9", "List training and unlearning events in an append-only, hash-chained ledger", "GET /api/state (audit); Compliance audit", "U1, S"],
             ["FR10", "Verify the hash chain on demand and report the first broken record", "POST /api/audit/verify; Compliance audit", "U3, S"],
             ["FR11", "Provide the original single-page interface, a Tkinter desktop interface and a command-line demonstration", "GET /; `app.py --desktop`, `--demo`", "Manual; S for `/api` only"]],
            "Functional requirements and traceability", widths=[0.07, 0.45, 0.3, 0.18], font=9)


def sec_requirements_nonfunctional(d):
    d.h2("Non-Functional Requirements")
    d.table([["ID", "Requirement", "Target and how it was checked", "Status"],
             ["NFR1", "Responsiveness", f"Interactive latencies; median {TRAIN_P50:.0f} ms to train, {UNL_P50:.0f} ms to unlearn, {STATE_P50:.0f} ms to read the state, {HEALTH_P50:.0f} ms health (live server, 127.0.0.1)", "Met"],
             ["NFR2", "Reproducibility", "Fixed random seed (2026) and deterministic corpus; every reported number regenerated by `scripts/run_experiments.py`", "Met"],
             ["NFR3", "Data boundary", "Raw records live in client objects; only clipped updates reach the aggregate", "Met by design in the simulation"],
             ["NFR4", "Integrity of records", "SHA-256 chain with sequence checks; edits, deletions and swaps detected in the tamper study", "Partly met: truncation, re-hashing and an emptied file undetected"],
             ["NFR5", "Portability", "Back end runs on Python 3.10 or newer with no packages; front end on Node.js 18 or newer", "Met (measured on Python 3.11.9 and Node 24.19)"],
             ["NFR6", "Usability", "Empty and error states on every screen, confirmations, dark mode, layout checked at 1440 px and 390 px", "Met (manual review)"],
             ["NFR7", "Robustness", "Errors returned as JSON with 400/404 codes; invalid input never crashes the server", f"Partly met: {_sp['n_probes']} probes, {SP['defect']} defects (e.g. no read timeout, a 2 MB body aborts the connection, unsupported methods return HTML)"],
             ["NFR8", "Security", "Authentication, authorisation and encrypted storage of tracked updates", "Not met: none implemented; probes show unauthenticated erase and CSRF (Chapter 7)"],
             ["NFR9", "Maintainability", "Small modules with a model interface that can be swapped; the neural study reuses the method unchanged", "Met"],
             ["NFR10", "Concurrency", f"Races and load measured on 127.0.0.1: 32 simultaneous removals of one client gave {RACE['32 simultaneous unlearn requests for the same client']['status_counts']['200']} success and the rest rejected; 16 simultaneous trainings left a valid chain; {SOAK['requests']:,}-request soak with {SOAK['errors_5xx_or_connection']} errors", f"Met up to {ZERO_ERR_MAX} concurrent clients; failures appear at 32 to 64"],
             ["NFR11", "Acceptance", f"{_ac['journeys']} scripted synthetic-user journeys (desktop and phone, light and dark): train, sample, remove, verify", f"Met: {_ac['journeys_passed_all_steps']} of {_ac['journeys']} passed"]],
            "Non-functional requirements and their status", widths=[0.08, 0.2, 0.5, 0.22], font=9)


def sec_requirements_platform(d):
    d.h2("Hardware and Software Requirements")
    d.p("The first table lists the machine on which every measurement in this report was taken.")
    d.table([["Component", "Used for the measurements"],
             ["Processor", "Intel Core i5-12500, 6 cores / 12 threads"],
             ["Memory", "15.7 GB RAM"],
             ["Graphics processor", "None used"],
             ["Operating system", "Windows 11 Pro"],
             ["Display for captures", "1440 x 900 viewport (a 390 x 844 viewport for the mobile capture)"]],
            "Hardware", widths=[0.3, 0.7], font=10)
    d.table([["Software", "Version / role"],
             ["Python", "3.11.9; the README states 3.10 or newer; standard library only for the engine, API, tests and Tkinter interface"],
             ["Node.js / npm", "24.19.0 / 11.17.0 (the run guide states 18 or newer) for the React interface"],
             ["React, React Router", "React 19; React Router 7"],
             ["Vite", "8.3 (development server on 5109 with a proxy of `/api` to 8109)"],
             ["Recharts and presentation libraries", "Recharts 3 for charts; framer-motion, GSAP, Lenis, lucide-react and canvas-confetti for motion and icons"],
             ["Browser", "Google Chrome (used for all screenshots)"],
             ["PyTorch 2.14 (CPU), NumPy 1.26", "Neural adapter study only; the engine, API and tests do not need them"],
             ["Playwright (Python)", "Used to capture the screenshots and to run the scripted acceptance journeys"],
             ["matplotlib, python-docx, python-pptx", "Used only to produce the diagrams, charts and submission documents"]],
            "Software", widths=[0.3, 0.7], font=10)


def sec_roles(d):
    d.h2("User Roles and Constraints")
    d.p("The software distinguishes no users: it has no login and no permission checks, so the roles below are roles of use, not roles enforced by the system.")
    d.table([["Role", "Does", "Uses"],
             ["Operator", "Trains the global model, carries out a removal request, samples the model, starts a new session", "Federated training, Certified unlearning, Model explorer"],
             ["Compliance auditor", "Reads the certificate, downloads its JSON, verifies the ledger", "Certified unlearning (certificate), Compliance audit"],
             ["Data owner (client)", "Asks to be forgotten; the request is made outside the system and the operator acts on it", "None directly"],
             ["Maintainer", "Runs the tests and the measurement suite; replaces the model", "Command line"]],
            "Roles of use", widths=[0.2, 0.5, 0.3], font=10)
    d.p("**Constraints.** The API listens on localhost by default and should not be exposed to a network in its present form, because any caller could erase a client or reset the "
        "session; only one engine exists for all callers; at least one client must always remain, and a client can be removed once per session; the ledger is a local file that is read in full on "
        "every append; and the corpus is fixed.")
