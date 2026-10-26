"""Chapter 5 content: architecture, workflow, DFDs, UML, database, modules, user interface; plus the diagram registry (ForgetSafe).

Diagrams are drawn by scripts/make_diagrams.py from the real engine, model, audit ledger and web handler; each paragraph below was
checked against the picture and against certified_unlearning/ and frontend/src/.
"""
from __future__ import annotations

from pathlib import Path

from doc_common import DIAG, ROOT, SHOTS

ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]


def _loc(rel: str) -> int:
    """Line count of a project file, so the module table cannot drift from the code."""
    return len((ROOT / rel).read_text(encoding="utf-8").splitlines())


DIAGRAMS = {
    "architecture": (
        "01_system_architecture.png", "System architecture of ForgetSafe",
        ["The diagram has five bands. At the top are the two kinds of person who use the system: the operator, who handles a deletion request by "
         "training, removing a client and reading the certificate, and the compliance auditor, who reads certificates and verifies the audit chain. "
         "Below them are four front doors that all call the same engine: the React web application on port 5109, which reaches the Python server "
         "through the Vite proxy with HTTP and JSON; the original single-page interface that the Python server returns at `/`; the Tkinter desktop "
         "window started with `python app.py --desktop`; and the terminal demonstration started with `--demo`. The last two call the engine directly "
         "(dashed arrows).",
         "The third band is the standard-library API on port 8109 (`ThreadingHTTPServer`, the request handler and `ApplicationState` with its "
         "re-entrant lock; JSON, no authentication), and the figure lists the nine routes it serves. The fourth band is the "
         "`FederatedUnlearningEngine`, one per session. Inside it the client datasets, the clipped-update step, the noisy aggregate and the character "
         "language model form a left-to-right chain, a note states that only clipped updates cross from client to aggregator, and the engine's "
         "operations (`train`, `unlearn`, `metrics`, `contributions`, `generate`, `export_certificate`) and tracked state (updates, noise, noisy sum, "
         "certificates) sit below the chain. The bottom band is storage: the hash-chained ledger file, the in-memory engine state, and an explicit "
         "'No SQL database' box."]),
    "workflow": (
        "02_high_level_workflow.png", "High-level workflow of a training and an unlearning request",
        ["The workflow has twelve steps in three bands. Band A is federated training (`POST /api/train`): clip each client's bigram-count vector at "
         "C = 25, sum the clipped updates and add Gaussian noise, divide by the client count to obtain the 1,089-parameter global model, and record "
         "the metrics and a training event in the ledger. Band B is the unlearning request (`POST /api/unlearn`): check the guards, subtract the "
         "client's stored update from the noisy sum, drop the client from the active list and rebuild the model with a new hash, and recompute the "
         "retained-only reference and its L2 distance to the model. Band C is verification, certificate and audit: the membership AUC of the "
         "client's records before and after, the perplexity, accuracy and retention of the utility score, the decision `CERTIFIED` when the distance is "
         "at most 1e-10 and the retention at least 70 percent (otherwise `REVIEW_REQUIRED`), and the certificate with its ledger record, which "
         "`POST /api/audit/verify` can re-walk at any time."]),
    "dfd0": (
        "03_dfd_level0.png", "Data-flow diagram, level 0 (context)",
        ["At the highest level ForgetSafe is one process, drawn as the circle labelled 0, with three external entities. The operator (a person using the "
         "web interface, the desktop window or the command-line demonstration) sends session and train requests, the client id to remove and a seed text, "
         "and receives the session id, the metrics (epsilon, perplexity, accuracy), the certificate as JSON, sample text and error messages. The "
         "compliance auditor sends verification and certificate requests and receives the chain status, the ledger records and the certificate JSON. "
         "The built-in client corpus in `dataset.py` (25 sentences) is the only data source and flows into the system. The note at the bottom "
         "states that every request is an HTTP call to port 8109 or a direct engine call from the desktop and command-line front doors; there is no "
         "database server, model hub or message queue."]),
    "dfd1": (
        "04_dfd_level1.png", "Data-flow diagram, level 1",
        ["Level 1 divides the system into six processes: manage session (1), federated training (2), unlearn client (3), verify and certify (4), "
         "generate sample text (5), and audit ledger and certificate export (6). Five data stores appear as open boxes: the client datasets (D1, "
         "drawn twice to keep the arrows short), the clipped updates with the stored noise (D2), the global model (D3), the certificates held in "
         "memory (D4) and the audit ledger file (D5). Training reads D1 and writes D2 and D3; unlearning reads and rewrites D2 and D3; verification "
         "reads D1, D2 and D3 and writes D4 and D5; sample generation reads D3; and process 6 reads and writes the ledger and reads the "
         "certificates. D5 is the only store that survives a restart."]),
    "dfd2": (
        "05_dfd_level2.png", "Data-flow diagram, level 2 (unlearning and verification)",
        ["Level 2 expands the two processes that carry the contribution of the project. Unlearning (3) has three sub-processes: 3.1 checks the "
         "guards (trained, known client, not yet removed, more than one client left) against the model and the active clients, 3.2 subtracts the tracked "
         "update held in D2 from the noisy sum, and 3.3 renormalises, rebuilds the model and stores it in D3. Verification (4) runs, drawn right to "
         "left in the lower band, as five sub-processes inside the same `unlearn()` call: 4.1 builds the retained-only reference from the updates "
         "and the same noise and measures its distance to the model, 4.2 measures the membership AUC from the client records (D1) before and after, "
         "4.3 computes the utility retention from the model, 4.4 decides the status, and 4.5 builds the certificate, stores it in D4 and appends the "
         "ledger record to D5. The operator receives the certificate."]),
    "usecase": (
        "08_use_case_diagram.png", "Use-case diagram",
        ["Two actors use the system, which the frame labels as the React UI, the legacy UI and the desktop and command-line front doors. The operator "
         "starts a new session, trains the federated model, generates sample text, views the dashboard and the client contributions, and requests the "
         "unlearning of a client. That last use case includes two others, drawn with dashed `include` arrows: running the verification checks (attack, "
         "reference, utility) and appending an audit record for both training and unlearning events. The compliance auditor browses the audit ledger "
         "and verifies the hash chain. Viewing a verification certificate and downloading it as JSON are shared by both actors. A note on the "
         "diagram records that the desktop and command-line interfaces expose the same use cases to the operator and that the auditor needs only "
         "read access (`GET /api/certificate/latest`, `POST /api/audit/verify`, the ledger in `/api/state`). The diagram contains no login or role "
         "use case because the application has no authentication; that absence is recorded as a limitation of the system."]),
    "sequence": (
        "09_sequence_diagram.png", "Sequence diagram of training, unlearning and audit verification",
        ["Six lifelines run left to right: the operator, the React UI (port 5109), the API in `web.py` (port 8109), the engine, the character language "
         "model and the audit ledger. The Train band shows the operator pressing Train, the UI calling `POST /api/train`, the API calling `train()`, "
         "the engine clipping, summing, adding noise and dividing by n, asking the model for perplexity and accuracy, appending the "
         "`FEDERATED_TRAINING` event and returning the metrics JSON. In the Unlearn band the operator picks a client and confirms, the UI calls "
         "`POST /api/unlearn` with the client id, and the engine asks the model for metrics and the membership AUC before, subtracts the update "
         "and rebuilds, asks again after, appends `CLIENT_UNLEARNING` and returns the certificate JSON. In the Verify band the Verify button calls "
         "`POST /api/audit/verify`, the API calls the ledger's `verify()` directly, and the pair `(valid, detail)` returns as `{valid, detail}`."]),
    "er": (
        "06_er_diagram.png", "Entity-relationship view of the data model (no SQL database)",
        ["ForgetSafe has no relational database, so the diagram shows the entities of its data model and how they relate; a note in the corner says "
         "so, and colour separates the in-memory entities (blue and green) from the persistent one (amber). A client dataset produces one client "
         "update per session, and a session has one update for each client, one global model (the noise, the noisy sum, the parameters and the "
         "model hash) and any number of certificates. Each certificate names the client dataset it removed and is linked one-to-one with an audit "
         "record through `audit_record_hash`. The audit record carries the session id inside its event fields but has no foreign key, and its "
         "`previous_hash` points to the record before it, the first record using 64 zeros, which is the self-link that forms the chain. Only the "
         "audit record is written to disk, as one JSON line of `data/audit_log.jsonl`."]),
    "uml": (
        "07_uml_class_diagram.png", "UML class diagram",
        ["The class diagram shows the engine at the centre. `FederatedUnlearningEngine` aggregates two or more `ClientDataset` objects, holds at most "
         "one `CharacterLanguageModel` (composition, 0..1, because the engine starts untrained) and exactly one `AuditLedger` (composition), keeps "
         "zero or more `UnlearningCertificate` objects, and creates `TrainingMetrics` and `ClientContribution` values through dashed `creates` "
         "dependencies; all four value classes are frozen dataclasses. `ApplicationState` holds one engine and a re-entrant lock for the web layer, "
         "and the request handler built by `make_handler` uses it. A grey note states that the Tkinter class `UnlearningApp` and `run_demo()` call "
         "the engine directly, with no HTTP and no `ApplicationState`. The module-level functions of `model.py` (`raw_update`, `clipped_update`, "
         "`membership_auc`) are noted beside the model class."]),
    "flowchart": (
        "10_algorithm_flowchart.png", "Flowchart of the unlearning algorithm (`FederatedUnlearningEngine.unlearn`)",
        ["The flowchart follows `unlearn()` from the start terminal. Four diamonds are the guards: the model is untrained (`RuntimeError`), the client id "
         "is unknown (`KeyError`), the client has already been unlearned (`ValueError`), or only one client is active (`ValueError`); each 'yes' "
         "leaves through a red box and `web.py` maps all of them to HTTP 400. A request that passes records the metrics and the membership AUC, "
         "subtracts the tracked update and removes the client, rebuilds the model and measures again, recomputes the reference and its L2 distance, and "
         "computes the retention. The last diamond tests the distance against 1e-10 and the retention against 70 percent: both true gives "
         "`CERTIFIED`, otherwise `REVIEW_REQUIRED`. Either way the certificate is built, appended to the ledger and returned with HTTP 200."]),
}


def diagram(d, key, width=None):
    fname, caption, paras = DIAGRAMS[key]
    path = DIAG / fname
    if path.exists():
        d.figure(path, caption, width=width, max_h=4.4 if getattr(d, "report", False) else 4.5)
    else:  # never fail a build because a picture is late; verify_docs checks figure counts
        d.p(f"[figure {fname} not yet generated]", italic=True)
    for p in paras:
        d.p(p)


# ---------------------------------------------------------------------------------------------------------------- architecture
def sec_arch(d):
    d.h2("System Architecture")
    d.p("ForgetSafe is a single-machine application in two parts: a Python back end that uses only the standard library, and a React front end "
        "built with Vite. The back end contains the whole domain logic (the federated aggregation, the unlearning, the verification and the audit "
        "ledger) and exposes it as a small JSON API; the front end is a client of that API and holds no domain logic. The original single-page "
        "interface and the Tkinter window of the first version were kept, so the same engine is reachable through four front doors. No external "
        "service is called and no network access is needed after the front-end dependencies are installed.")
    diagram(d, "architecture")
    d.p("Five design principles shaped the architecture.")
    d.numbered([
        "**Keep the guarantee in one place.** Everything that decides whether a removal is certified lives in `FederatedUnlearningEngine.unlearn()`; "
        "the web handler, the React pages and the Tkinter window only call it and display what it returns, so no front end can certify something "
        "the engine did not.",
        "**Separate the model from the orchestration.** The language model (`model.py`) knows only a flat parameter vector and four metrics. The "
        "engine treats the vector as the shared state, so the proxy can later be replaced by an adapter tensor of a real model without changing the "
        "orchestration, the certificate schema or the ledger. Reference [22] describes the low-rank adapter update that the proxy stands in for.",
        "**Make every deletion leave evidence.** Training and unlearning both end in a ledger append; there is no code path that changes the "
        "model without writing an audit record.",
        "**Dependency-free back end.** Using `http.server`, `dataclasses`, `hashlib` and `json` means the demonstration runs on any machine with "
        "Python 3.10 or newer, which matters for a project that is presented on a classroom computer.",
        "**Honest labelling.** The interface states that the model is a demonstrator (a note in the sidebar), and the certificate shows its method "
        "string, so nobody reading it can mistake the proxy for a formally erased LLM.",
    ])
    d.table([["Layer", "Technology", "Main files", "Responsibility"],
             ["Presentation (web)", "React 19, React Router 7, Recharts, Framer Motion, Vite 8", "`frontend/src/pages/*.jsx`, `components/ui/*`", "Landing page and five application pages; charts, tables, dialogs, toasts"],
             ["Presentation (legacy)", "HTML/JS string inside `web.py`; Tkinter", "`web.py` (`PAGE`), `gui.py`", "Original four-tab interface; desktop window"],
             ["API", "`http.server.ThreadingHTTPServer`", "`web.py`", "Routing, JSON encoding, input checks, status codes, one lock"],
             ["Domain", "Python dataclasses", "`engine.py`", "Training, unlearning, verification, certificate"],
             ["Model", "Pure Python lists", "`model.py`", "Bigram counts, clipping, probabilities, perplexity, accuracy, membership AUC"],
             ["Evidence", "SHA-256 over canonical JSON, JSONL file", "`audit.py`, `data/audit_log.jsonl`", "Append-only hash chain and its verification"],
             ["Data", "Python constants", "`dataset.py`", "Five client corpora, public evaluation set, non-member set"]],
            "Layers of the architecture", widths=[0.17, 0.25, 0.26, 0.32], font=9.5)
    d.p("**Trust boundary.** The federated learning rule is that raw data stays with the client and only an update crosses to the coordinator. In "
        "ForgetSafe the clients are `ClientDataset` objects and the coordinator is the engine, in one process. `train()` reads `client.records` "
        "to build each update, and the engine keeps every clipped update afterwards, because exact subtraction needs them. The boundary is "
        "therefore a convention of the code and not a separation of machines, and the stored updates are exactly the sensitive artefacts that a "
        "real deployment would have to encrypt and restrict, as `PROJECT_REPORT.md` itself notes.")


# ---------------------------------------------------------------------------------------------------------------- workflow
def sec_workflow(d):
    d.h2("High-Level Workflow")
    d.p("The workflow of the lab has four user-visible steps, which the web application also shows as the numbered eyebrow of each page "
        "(Step 1 to Step 4) and as the three-step workflow card on the dashboard.")
    diagram(d, "workflow")
    d.table([["Step", "Trigger", "Engine call", "Result"],
             ["1. Train", "Train federated model button; `POST /api/train`", "`train()`", "Clipped updates and noise stored, global model built, metrics returned, `FEDERATED_TRAINING` appended"],
             ["2. Unlearn", "Execute and certify, then Remove and certify in the dialog; `POST /api/unlearn`", "`unlearn(client_id)`", "Update subtracted, model rebuilt, reference check, attack, retention, certificate, `CLIENT_UNLEARNING` appended"],
             ["3. Explore", "Generate sample; `POST /api/generate`", "`generate(seed_text, length)`", "180 characters sampled from the current model"],
             ["4. Audit", "Verify hash chain; `POST /api/audit/verify`", "`AuditLedger.verify()`", "Valid or the first broken record number"],
             ["Reset", "New session; `POST /api/session`", "new `FederatedUnlearningEngine`", "Untrained engine, new session id, ledger history kept"]],
            "Workflow steps and the code that runs them", widths=[0.12, 0.31, 0.2, 0.37], font=9.5)
    d.p("Two properties of the workflow are worth stating. First, retraining (pressing Train again) clears the certificates held in memory but not the "
        "ledger, so the ledger is a complete history across sessions while the certificate list describes only the current one. Second, the order is "
        "enforced by the engine and not only by the interface: `unlearn()` and `generate()` raise an error before training, and the API turns it into "
        "an HTTP 400 response.")


# ---------------------------------------------------------------------------------------------------------------- data flow
def sec_dfd(d):
    d.h2("Data-Flow Diagrams")
    d.p("Three levels of data-flow diagrams describe the movement of data. They follow the code: a data store is drawn only where the code keeps "
        "the data (an attribute of the engine or the ledger file), and a process only where a function transforms it.")
    d.h3("Level 0: context")
    diagram(d, "dfd0")
    d.h3("Level 1: main processes")
    diagram(d, "dfd1")
    d.table([["Process / store", "Implemented by", "Data in", "Data out"],
             ["1.0 Manage session", "`ApplicationState`, `FederatedUnlearningEngine.__init__`", "New-session command", "Fresh engine, session id (UUID)"],
             ["2.0 Federated training", "`train()`, `clipped_update()`", "Client records (D1)", "Clipped updates and noise (D2), model (D3), metrics, ledger event"],
             ["3.0 Unlearn a client", "`unlearn()`", "Client id, updates (D2)", "Reduced noisy sum, rebuilt model (D3)"],
             ["4.0 Verify and certify", "`_reference_parameters()`, `membership_auc()`, `_utility_retention()`", "Model, updates, noise, public and non-member sets", "Certificate (D4)"],
             ["5.0 Generate sample text", "`generate()`", "Seed text, model (D3)", "Text"],
             ["6.0 Audit ledger and certificate export", "`AuditLedger`, `export_certificate()`", "Events, certificates", "Records (D5), verification result, certificate JSON"],
             ["D1", "`dataset.py` tuples", "-", "Records"],
             ["D2", "`engine.updates`, `update_metadata`, `noise`, `noisy_sum`", "-", "Vectors of 1,089 floats"],
             ["D3", "`engine.model`", "-", "Parameter vector"],
             ["D4", "`engine.certificates`", "-", "Certificates of the current session"],
             ["D5", "`data/audit_log.jsonl`", "-", "One JSON line per event"]],
            "Processes and data stores of the level-1 diagram", widths=[0.18, 0.34, 0.22, 0.26], font=9)
    d.h3("Level 2: unlearning and verification")
    diagram(d, "dfd2")
    d.p("The level-2 view makes one design fact visible: no raw record is read during unlearning. Process 3.0 and the reference recomputation in "
        "4.0 use only the stored updates and the stored noise; the only place the client's raw sentences are touched again is the membership "
        "attack, which scores them against the model before and after the removal.")


# ---------------------------------------------------------------------------------------------------------------- UML
def sec_uml(d):
    d.h2("UML Diagrams")
    d.p("The behaviour and structure of the application are described by a use-case diagram, a class diagram, a sequence diagram and a flowchart "
        "of the central algorithm. The ER view of the data model follows in the Data Design section.")
    d.h3("Use-case diagram")
    diagram(d, "usecase")
    d.h3("Class diagram")
    diagram(d, "uml")
    d.table([["Class / module", "Kind", "Key members (from the code)"],
             ["`ClientDataset`", "frozen dataclass", "`client_id`, `display_name`, `domain`, `records` (tuple of strings)"],
             ["`FederatedUnlearningEngine`", "class", "`clients`, `audit`, `clip_norm`, `noise_multiplier`, `delta`, `random_seed`, `session_id`, `updates`, `update_metadata`, `active_client_ids`, `noise`, `noisy_sum`, `model`, `certificates`; `train()`, `metrics()`, `contributions()`, `unlearn()`, `generate()`, `export_certificate()`; properties `trained`, `epsilon`"],
             ["`CharacterLanguageModel`", "dataclass", "`parameters`, `smoothing` (0.15); `negative_log_likelihood()`, `perplexity()`, `next_character_accuracy()`, `generate()`"],
             ["`TrainingMetrics`", "frozen dataclass", "`active_clients`, `epsilon`, `delta`, `perplexity`, `next_character_accuracy`, `utility_score`, `model_hash`"],
             ["`ClientContribution`", "frozen dataclass", "`client_id`, `display_name`, `domain`, `record_count`, `original_norm`, `clipped_norm`, `clip_scale`, `active`"],
             ["`UnlearningCertificate`", "frozen dataclass", "25 fields (see Data Design); `to_dict()`"],
             ["`AuditLedger`", "class", "`path`; `read_all()`, `append()`, `verify()`"],
             ["`ApplicationState`", "class", "`audit_path`, `engine`, `lock` (re-entrant); `snapshot()`"],
             ["`RequestHandler`", "class (inside `make_handler`)", "`do_GET()`, `do_POST()`, `_json()`, `_body()`, `log_message()`"],
             ["`UnlearningApp`", "Tkinter class", "four notebook tabs; `_train()`, `_unlearn()`, `_generate()`, `_verify_audit()`, `_export_certificate()`"]],
            "Classes of the back end", widths=[0.24, 0.17, 0.59], font=9)
    d.h3("Sequence diagram")
    diagram(d, "sequence")
    d.h3("Flowchart of the core algorithm")
    diagram(d, "flowchart")


# ---------------------------------------------------------------------------------------------------------------- database
def sec_database(d):
    d.h2("Data Design")
    d.p("ForgetSafe has no SQL or document database. This is a deliberate consequence of the problem it demonstrates: the evidence that must "
        "last is the audit ledger, and the working state of a session is cheap to recompute from a seed. The data model therefore has two parts: "
        "state held in memory by the engine, and one append-only file.")
    diagram(d, "er")
    d.h3("In-memory state of a session")
    d.table([["Attribute", "Type", "Set by", "Meaning"],
             ["`session_id`", "str (UUID4)", "`__init__`", "Identifies the session in events and certificates"],
             ["`clients`", "dict[str, ClientDataset]", "`__init__`", "Five clients; raw records (D1)"],
             ["`updates`", "dict[str, list[float]]", "`train()`", "Clipped bigram-count vector per client, 1,089 floats each"],
             ["`update_metadata`", "dict[str, (float, float)]", "`train()`", "Original L2 norm and clip scale per client"],
             ["`active_client_ids`", "list[str]", "`train()`, `unlearn()`", "Clients still contributing to the model"],
             ["`noise`", "list[float]", "`train()`", "One Gaussian draw, standard deviation sigma times C per coordinate; kept for the whole session"],
             ["`noisy_sum`", "list[float]", "`train()`, `unlearn()`", "Sum of active clipped updates plus the noise"],
             ["`model`", "CharacterLanguageModel or None", "`_rebuild_model()`", "`noisy_sum` divided by the active-client count"],
             ["`certificates`", "list[UnlearningCertificate]", "`unlearn()`; cleared by `train()`", "Certificates of the current session"]],
            "Engine state", widths=[0.2, 0.23, 0.2, 0.37], font=9.5)
    d.p("None of this state is written to disk. After a server restart the engine is untrained, and only the ledger shows what happened "
        "before. The random seed (2026 by default) makes the noise repeatable: the same seed gives the same noise and therefore the same model "
        "hash, which is what makes the experiments of the results chapter reproducible.")
    d.h3("Audit ledger records")
    d.p("The ledger is a JSON-lines file; each line is one record. The path is `data/audit_log.jsonl` relative to the directory from which the "
        "server is started, and the file is excluded from version control. Every record carries the three chain fields, and the remaining "
        "fields depend on the event type.")
    d.table([["Field", "Event types", "Description"],
             ["`sequence`", "both", "1-based position in the ledger"],
             ["`previous_hash`", "both", "`record_hash` of the preceding record; 64 zeros for the first"],
             ["`record_hash`", "both", "SHA-256 of `previous_hash`, a vertical bar and the canonical JSON of the record without this field"],
             ["`event_type`", "both", "`FEDERATED_TRAINING` or `CLIENT_UNLEARNING`"],
             ["`timestamp_utc`", "training", "ISO-8601 time, seconds precision"],
             ["`session_id`, `active_clients`, `epsilon`, `delta`, `clip_norm`, `noise_multiplier`, `model_hash`", "training", "Configuration and fingerprint of the trained model (epsilon rounded to 8 places)"],
             ["all 25 certificate fields", "unlearning", "The certificate, whose `issued_at_utc` serves as the time"]],
            "Ledger record schema", widths=[0.36, 0.14, 0.5], font=9.5)
    d.p("One detail follows from the order of operations. The certificate is appended to the ledger before its own record hash exists, so the "
        "ledger copy holds an empty `audit_record_hash`; the engine then stores the returned `record_hash` in the certificate object that is "
        "handed back to the caller. The certificate a user downloads therefore points to its ledger record, and the ledger record does not point "
        "back, which is acceptable because the record's position in the chain already identifies it.")
    d.h3("Certificate schema")
    d.table([["Group", "Fields"],
             ["Identity", "`certificate_id` (`CERT-` and 12 hex digits), `session_id`, `client_id`, `client_name`, `issued_at_utc`"],
             ["Decision", "`status` (`CERTIFIED` or `REVIEW_REQUIRED`), `method` (fixed string: tracked clipped-update subtraction with retained-client renormalization)"],
             ["Privacy parameters", "`epsilon`, `delta`, `clip_norm`, `noise_multiplier`"],
             ["Verification", "`residual_influence_l2`, `reference_retrain_l2` (the same number in this implementation), `membership_auc_before`, `membership_auc_after`"],
             ["Utility", "`perplexity_before`, `perplexity_after`, `accuracy_before`, `accuracy_after`, `utility_retention_percent`"],
             ["Population and integrity", "`clients_before`, `clients_after`, `model_hash_before`, `model_hash_after`, `audit_record_hash`"]],
            "The 25 fields of an unlearning certificate", widths=[0.22, 0.78], font=9.5)
    d.p("Two limits of this design are stated here because they affect how the evidence can be used. The ledger append reads the whole file to "
        "find the previous hash, so its cost grows with the ledger (the results chapter measures 0.44 ms at one record and 19.6 ms at 2,000). And two server "
        "processes started in the same directory would write to the same file without any file lock; the `RLock` in `ApplicationState` protects "
        "threads of one process only.")


# ---------------------------------------------------------------------------------------------------------------- modules
def sec_modules(d):
    d.h2("Module Design")
    d.p("The code base is small enough to describe module by module. Line counts below were taken from the files when this report was built.")
    rows = [["Module", "Lines", "Responsibility", "Key functions and classes"]]
    mods = [
        ("certified_unlearning/engine.py", "Lifecycle of a session: train, unlearn, verify, certify, export", "`FederatedUnlearningEngine`, `TrainingMetrics`, `ClientContribution`, `UnlearningCertificate`, `_vector_hash()`"),
        ("certified_unlearning/model.py", "Character-bigram model and its numerical helpers", "`normalize_text()`, `raw_update()`, `clipped_update()`, `l2_norm()`, `CharacterLanguageModel`, `membership_auc()`"),
        ("certified_unlearning/audit.py", "Append-only hash-chained ledger", "`AuditLedger.append()`, `verify()`, `read_all()`, `GENESIS_HASH`"),
        ("certified_unlearning/dataset.py", "Built-in corpora", "`CLIENTS`, `PUBLIC_EVALUATION`, `NON_MEMBER_TEXTS`, `ClientDataset`"),
        ("certified_unlearning/web.py", "HTTP server, JSON API and the legacy page", "`PAGE`, `ApplicationState`, `make_handler()`, `run_web()`"),
        ("certified_unlearning/gui.py", "Tkinter desktop interface", "`UnlearningApp`, `run_gui()`"),
        ("app.py", "Entry point with three modes", "`run_demo()`, `main()` (`--demo`, `--desktop`, `--port`, `--host`, `--open-browser`)"),
        ("tests/test_end_to_end.py", "Unit and endpoint tests (5 tests)", "`FederatedUnlearningTests`"),
        ("scripts/smoke_test.py", "End-to-end API check (14 checks)", "`run()`, `call()`, `check()`"),
        ("scripts/run_experiments.py", "Default-configuration measurements (11 experiments)", "`exp_baseline()`, `exp_seeds()`, `exp_sweep()`, `exp_gold()`, `exp_audit()`, `exp_api()`"),
        ("scripts/run_synthetic_corpus.py", "Synthetic-grammar corpus study with the real engine; git timeline", "`Corpus`, `section_sweep()`, `section_n_sweep()`, `section_timeline()`"),
        ("scripts/run_neural_experiment.py", "GRU with LoRA-style adapters on synthetic text (torch)", "`Base`, `Adapter`, `train_adapter()`, `main()`"),
        ("scripts/run_testing_experiments.py", "Load, concurrency, security probes, scripted acceptance", "load levels, races, probe groups, Playwright journeys"),
    ]
    for rel, resp, keys in mods:
        rows.append([f"`{rel}`", str(_loc(rel)), resp, keys])
    d.table(rows, "Back-end, test and measurement modules", widths=[0.3, 0.07, 0.28, 0.35], font=9)
    d.p("`web.py` holds the single largest block of text, but most of it is the embedded legacy page (about 90 lines of HTML, CSS and JavaScript); "
        "its Python logic is about 140 lines from `ApplicationState` to `run_web()`.")
    d.h3("Engine module")
    d.p("`engine.py` is the module that carries the project's claim. `train()` builds one clipped update per client, draws the noise with "
        "`random.Random(seed).gauss`, forms the noisy sum and builds the model. `unlearn()` guards the request, subtracts, rebuilds, measures and "
        "certifies. `metrics()` computes perplexity, accuracy, the composite utility score and the SHA-256 fingerprint of the parameter vector "
        "(the vector rounded to 12 decimals and serialised as compact JSON). `contributions()` exposes the per-client norms that the training "
        "page charts, and `_reference_parameters()` builds the retained-only recomputation that the certificate compares against.")
    d.h3("Model module")
    d.p("`model.py` defines the 33-symbol alphabet (the start marker `^`, the end marker `$`, space, the 26 lower-case letters and four punctuation "
        "marks), and keeps the 1,089-element parameter vector as a flat list in row-major order, so that the entry for the transition from "
        "character `a` to character `b` is at `index(a) * 33 + index(b)`. Probabilities are computed row by row: the parameter is clamped at zero, "
        "the smoothing constant 0.15 is added, the entry for the start marker is zeroed so that the model never emits it, and the row is "
        "normalised. This clamping is what lets a noisy, partly negative parameter vector still define a valid distribution.")
    d.h3("Audit module and web module")
    d.p("`audit.py` has no dependency on the rest of the package. It hashes with `hashlib.sha256` and writes with an explicit `\\n` newline so that "
        "the file is byte-identical across operating systems. `web.py` builds the handler class inside `make_handler(application)` so that the "
        "handler closes over one `ApplicationState`; the tests exploit this by starting a server on an spare port with their own temporary "
        "ledger.")
    d.h3("Front-end modules")
    rows = [["Path", "Lines", "Role"]]
    fe = [
        ("frontend/src/main.jsx", "Mounts theme, toast and lab providers and the router"),
        ("frontend/src/App.jsx", "Route table; lazy-loads each page"),
        ("frontend/src/lib/api.js", "Thin fetch client for the eight JSON endpoints; turns `{error}` bodies into `ApiError`"),
        ("frontend/src/lib/lab.jsx", "`LabProvider` and `useLab()`: the single copy of `GET /api/state`"),
        ("frontend/src/lib/theme.jsx", "Light and dark theme, persisted in `localStorage`"),
        ("frontend/src/pages/Dashboard.jsx", "Workflow stepper, four metric tiles, client-norm chart, latest certificate"),
        ("frontend/src/pages/Training.jsx", "Train, retrain and new-session actions with confirmation dialogs; clients table and norm chart"),
        ("frontend/src/pages/Unlearning.jsx", "Client selector, confirmation dialog, certificate view, before and after charts"),
        ("frontend/src/pages/Explorer.jsx", "Seed field, sample list tagged with client count and model hash"),
        ("frontend/src/pages/Audit.jsx", "Chain status, searchable ledger table, record viewer"),
        ("frontend/src/pages/Landing.jsx", "Public landing page with live counters from `/api/state`"),
        ("frontend/src/pages/shared.jsx", "`CertificateView`, `AuditTable`, `ClientsTable`, status badges"),
        ("frontend/src/pages/useAction.js", "Runs an API call, refreshes state, shows a success or error toast"),
        ("frontend/src/components/ui/*", "Button, Card, Table, Modal, Toast, Layout, Skeleton and other building blocks"),
        ("frontend/src/components/charts/index.jsx", "Recharts wrappers: bar, grouped bar, line, area"),
    ]
    for rel, role in fe:
        if rel.endswith("/*"):
            n = sum(len((p).read_text(encoding="utf-8").splitlines()) for p in (ROOT / rel[:-2]).glob("*"))
        else:
            n = _loc(rel)
        rows.append([f"`{rel}`", str(n), role])
    d.table(rows, "Front-end modules", widths=[0.36, 0.08, 0.56], font=9)


# ---------------------------------------------------------------------------------------------------------------- UI
def sec_ui(d):
    d.h2("User Interface Design")
    d.paras(
        "The web application has one public landing page and a sidebar application with five pages: Dashboard (`/app`), Federated training "
        "(`/app/training`), Certified unlearning (`/app/unlearning`), Model explorer (`/app/explorer`) and Compliance audit (`/app/audit`). "
        "The pages are numbered Step 1 to Step 4 in their headers so that the order of the workflow is visible. A top bar shows an API-online "
        "indicator that polls `/api/health` every 30 seconds and a light and dark theme toggle; on screens narrower than 900 pixels the sidebar is replaced by a "
        "bottom navigation bar and a drawer.",
        "All pages read one shared copy of the server state through `useLab()`, which calls `GET /api/state` once and again after every action. "
        "The shared `useAction()` hook wraps every mutating call: it marks the button busy, refreshes the state, and raises a success toast or an "
        "error toast that stays for eight seconds. Because the engine lives on the server, a browser reload does not lose the session.",
        "Four interface states are handled on every page. While the first state request is in flight a skeleton is shown; when no model has been "
        "trained an empty state explains what to do and offers a button; when the API cannot be reached an error state offers a retry; and "
        "destructive actions (retraining, a new session, removing a client) ask for confirmation in a modal dialog that states the consequence in "
        "one sentence. The removal dialog reads, for example, that the client will be erased from the global model and that this cannot be "
        "undone in the session.",
        "Several design decisions come from the nature of the content. Numbers a regulator would read (epsilon, delta, residual influence, "
        "reference distance, hashes) are shown in a monospaced style and in full on the certificate, with a Download JSON button that fetches "
        "`/api/certificate/latest`. Status is never colour alone: a certified result carries a shield icon and the word Certified, a failed chain "
        "carries a broken-shield icon and the word Broken. The landing page contains no invented statistics; its counters (registered clients, "
        "domains, ledger records) are read from the live API. The sidebar carries a standing note, Demonstrator, which says that the model is a "
        "character-level proxy for an LLM adapter update and that the product is not a legal compliance product.")
    if getattr(d, "report", False):
        d.p("Two of the screens are shown below to illustrate the design; the complete set of output screens, including the dark theme and the phone layout, is in the results chapter and Appendix C.")
        d.figure_pair([(SHOTS / "05_dashboard_trained.png", "Dashboard: workflow stepper, four metric tiles, client norms and certificate slot"),
                       (SHOTS / "09_unlearning_certificate.png", "Certified unlearning: confirmation result, certificate and before-and-after chart")])
    else:
        d.p("The screens below were captured from the running application with real data in it (seed 2026, a model trained through the "
            "interface, then Client 01 and Client 02 removed).")
        d.figure_pair([(SHOTS / "01_landing.png", "Landing page with live lab status"),
                       (SHOTS / "05_dashboard_trained.png", "Dashboard after training: workflow, metrics, client norms")])
        d.figure_pair([(SHOTS / "04_training_trained.png", "Federated training page with the clients table and norm chart"),
                       (SHOTS / "07_unlearning_request.png", "Right-to-be-forgotten request form")])
        d.figure_pair([(SHOTS / "09_unlearning_certificate.png", "Verification certificate and before-and-after chart"),
                       (SHOTS / "10_explorer_after_unlearning.png", "Model explorer: a sample from the 4-client model")])
        d.figure_pair([(SHOTS / "13_audit_ledger.png", "Compliance audit: chain status and ledger table"),
                       (SHOTS / "15_dashboard_dark.png", "Dark theme after two removals")])
        d.figure_pair([(SHOTS / "16_unlearning_mobile.png", "Unlearning page at 390 px width"),
                       (SHOTS / "17_legacy_ui.png", "Original single-page interface, still served at `/` of the API")])
    d.p("One limitation of the interface should be recorded. The explorer shows what the model generates, and at the default noise level the text "
        "is a string of letters with little structure (the capture in the results chapter shows a sample beginning `privacybsov`), because the model is noise-"
        "dominated. The interface presents the sample honestly as the model's output rather than polishing it, but it also offers no warning "
        "that the quality is low; the metric tiles (perplexity 130.22, accuracy 5.1 percent) are the only indication.")
