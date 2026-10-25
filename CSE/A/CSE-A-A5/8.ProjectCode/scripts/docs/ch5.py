"""Chapter 5: System Design for CipherGuard Shield.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
"""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

_W = F.SHIPPED["meta_coef"][0]
_B = F.SHIPPED["meta_intercept"][0]


def blocks():
    out = _full()
    return _report_trim(out) if F.REPORT else out


def _report_trim(bl):
    """Report mode: smaller figures, the two simplest diagrams side by side, and a few less essential tables dropped."""
    out, skipping, uc_h3 = [], False, False
    for b in bl:
        if b[0] in ("h1", "h2", "h3"):
            skipping = b[0] == "h3" and b[1].startswith("5.4.3")
            if skipping:
                continue
        if skipping:
            continue
        if b[0] == "fig":
            if b[1].endswith("03_dfd_level0.png"):
                out.append(("pair", [(b[1], "Data flow diagram, level 0 (context)."), (F.diag("08_use_case.png"), "Use-case diagram.")], 2.9))
                continue
            w = min(b[3], 4.6) if b[3] <= 5.2 else 4.8
            out.append(("fig", b[1], b[2], w))
            continue
        if b[0] == "tab" and (b[1].startswith("Console routes") or b[1].startswith("Controls and their limits")):
            continue
        if b[0] == "tab" and b[1].startswith("Modules, responsibilities"):
            rows = [r for r in b[3] if not (r[0].startswith("`app.py`") or r[0].startswith("`web/") or r[0].startswith("`scripts/"))]
            out.append(("tab", b[1], b[2], rows, b[4], b[5], b[6]))
            continue
        out.append(b)
    return out


def _full():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how CipherGuard Shield is built: the architecture and workflow, the data flow, the class and sequence design, the data design, the two core algorithms, "
          "the module and API design and the user interface. Every diagram was drawn from the code (`cipherguard/api/main.py`, `cipherguard/crypto/secure_channel.py` and "
          "`cipherguard/ids/`) and is reproduced with an explanation; the full set is also collected in the Block Diagrams document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. First, **confidentiality and integrity by construction**: use one authenticated-encryption primitive from a maintained library rather than "
          "combining a cipher and a separate integrity check. Second, **a fresh key for every message**, so that the loss of one key exposes one message. Third, **detection that "
          "can be measured**: the detector must run on the real UNSW-NB15 schema, report held-out metrics and expose its scores. Fourth, **both protections on one data path**, so that the "
          "combined overhead named as a gap by the literature survey can be timed. Fifth, **small and runnable**: one API, one console, no database and no external service."),
        FIG(F.diag("01_system_architecture.png"), "Figure: four-tier architecture of CipherGuard Shield (console, FastAPI application, core packages and in-memory state, file stores).", 5.2),
        P("The presentation tier is a React 19 and Vite console on port 5305, which calls the API through a Vite proxy, together with the original HTML and JavaScript dashboard that "
          f"the API serves at its root path. The application tier is FastAPI on 127.0.0.1:{F.API_PORT}, with route groups for health and metrics, ThreatSense scoring and alerts, and "
          "SecureChannel encryption and decryption. Below it sit two Python packages: `cipherguard/crypto` with SecureChannel and KeyPair, and `cipherguard/ids` with the preprocessing, "
          "training and inference code of the ThreatSense Engine. Three structures live only in process memory: the alert list, the session-key cache and the mock cloud key pair. "
          "The data tier consists of files: the model bundle in `models/`, the metrics report in `reports/`, the synthetic CSV in `data/raw/`, and the experiment outputs in `experiments/`."),
        P("The two packages do not import each other. The only place where they meet is `main.py`, which is a deliberate choice: the console and the tests can exercise each module alone, "
          "and the experiments in Chapter 8 time them separately and together."),

        H2("5.2 High-Level Workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "Figure: the two protection lanes around one transfer.", 5.6),
        P("Lane A is the confidentiality path. A payload of up to 1 MB of text or 5 MB of file is encrypted with a key that only the sender and the cloud can derive, and the cloud "
          "returns the plaintext only if the 16-byte tag verifies. Lane B is the behaviour path. A flow record, or each row of a CSV, is preprocessed, scored by two models and "
          "fused into a verdict; attacks are appended to the alert log with a severity."),
        P("The two lanes are drawn side by side because that is how the console uses them. A verdict does not hold back or cancel a transfer: the API treats scoring and encryption as "
          "independent requests. Coupling a flagged session to a blocked transfer is the first item of future work. What the design does allow is measuring the cost of both lanes "
          f"for one transfer, which is {F.IP['protected_transfer_100kb']['median_ms']:.2f} ms for a 100 KB payload in process (Chapter 8)."),

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0"),
        FIG(F.diag("03_dfd_level0.png"), "Figure: data flow diagram, level 0 (context).", 5.6),
        P("At the context level CipherGuard Shield is one process with four neighbours. The operator provides flow records, CSV files, text, files and ciphertext and receives verdicts, alerts, "
          "envelopes, plaintext and metrics. The developer provides a retrain command and receives models and the metrics file. The cloud endpoint receives envelopes and answers with verified plaintext "
          "or a tag failure. The labelled-flow source, UNSW-NB15 or the synthetic CSV, is used only when training."),
        H3("5.3.2 Level 1"),
        FIG(F.diag("04_dfd_level1.png"), "Figure: data flow diagram, level 1.", 5.4),
        P("Level 1 shows seven processes and five stores. Validation (1.0) routes a request either to scoring (2.0) or to encryption (4.0). Scoring reads the stored models (D4) and hands scores to "
          "reporting (3.0), which owns the alert log (D1). Encryption writes the session key to the cache (D2); decryption (5.0) reads the cache, falls back to deriving the key with the "
          "cloud private key, and answers the operator. The metrics process (6.0) reads `metrics.json` (D3). Training (7.0) is offline: it reads the training CSV (D5) and writes the "
          "models and the metrics file."),
        H3("5.3.3 Level 2"),
        FIG(F.diag("05_dfd_level2.png"), "Figure: data flow diagram, level 2, of the scoring process.", 5.4),
        P("The scoring process has six steps. Defaults and name alignment (2.1) make any subset of the 42 features acceptable; the preprocessor (2.2) turns the record into a vector of "
          f"{F.INPUT_DIM_SYNTH} numbers for the shipped bundle or {F.INPUT_DIM_REAL} for the real-data bundle; XGBoost (2.3) and the CNN (2.4) each give an attack probability; the "
          "meta-model (2.5) fuses them; and the threshold and severity step (2.6) produces the label returned to the reporting process."),

        H2("5.4 UML Design"),
        H3("5.4.1 Class Diagram"),
        FIG(F.diag("06_uml_class.png"), "Figure: UML class diagram.", 5.2),
        P("The FastAPI application is the only class that knows both modules. It holds a ThreatSenseEngine, the alert list and the session-key cache. ThreatSenseEngine holds the "
          "preprocessor, the XGBoost model, the CNN and the meta-model, and its `score_single` and `predict_proba` methods are the whole scoring interface. The CNN layer stack is defined "
          "twice, in `train.py` and in `inference.py`, with identical layers; this duplication keeps inference from importing the training code and its optional TensorFlow probe. "
          "SecureChannel is a set of static methods, so a key pair is the only object it creates. The Pydantic schemas validate input, and the alert is a plain dictionary."),
        H3("5.4.2 Sequence Diagram"),
        FIG(F.diag("07_sequence_flow.png"), "Figure: sequence diagram of scoring, encryption and verified decryption.", 5.2),
        P("The sequence follows three requests. Scoring ends by inserting an alert only for an attack. Encryption derives the key against the cloud public key and caches it under the "
          "ephemeral public key, a shortcut that lets the demo decrypt without the cloud's private key. Decryption uses the cache if it can; if the entry is missing, which the "
          "test suite forces by clearing the cache, it derives the key with the cloud private key, so the verification does not depend on the shortcut."),
        H3("5.4.3 Use-Case Diagram"),
        FIG(F.diag("08_use_case.png"), "Figure: use-case diagram.", 5.2),
        P("There are seven operator use cases, one of which (decrypt and verify) involves the cloud endpoint, and one developer use case, retraining, which is a command-line action "
          "and not a screen of the console."),

        H2("5.5 Data Design"),
        P("CipherGuard Shield has no database. This is a design decision, not an omission: the demonstration needs short-lived alerts and per-process keys, and a database would add a "
          "dependency without adding a capability the experiments use. The consequence, stated in the limitations, is that alerts and keys are lost on restart. The entity-relationship "
          "diagram therefore shows logical entities and their call-time relations."),
        FIG(F.diag("09_er_diagram.png"), "Figure: logical entity-relationship diagram (no database).", 5.6),
        TAB("Data structures and where they live", ["Structure", "Fields", "Lives in"], [
            ["Flow record", "42 features: `proto`, `service`, `state` (text) and 39 numeric; optional `label`, `attack_cat` in CSV", "request body or CSV"],
            ["Verdict", "`label`, `confidence`, `severity`, `xgb_score`, `cnn_score` (+ `alert` for attacks)", "response"],
            ["Alert entry", "`timestamp`, `severity`, `confidence`, `label`, `features` (proto, service, state, sbytes, dbytes, rate, ct_srv_src), `scores` (xgb, cnn)", "in-memory list, newest first, at most 500"],
            ["Envelope", "`ciphertext` (base64), `nonce` (12 B), `tag` (16 B), `ephemeral_public` (65 B), `algorithm`, `key_exchange`", "response and request"],
            ["Session-key cache", "ephemeral public key (base64) to 32-byte AES key", "in-memory dict"],
            ["Cloud key pair", "P-256 private and public key, created on first use", "in-memory, one per process"],
            ["Model bundle", "`xgb_model.joblib`, `cnn_model.pt`, `stacking_meta.joblib`, `preprocessor.joblib`, `feature_info.json`", "`models/`"],
            ["Metrics report", "data mode, split sizes, accuracy, precision, recall, F1, ROC-AUC, confusion matrix, per-model accuracy, meta weights, class balance", "`reports/metrics.json`"],
        ], widths=[1.2, 3.8, 1.3], size=9.5, align=["l", "l", "l"]),
        P(f"The feature schema (`cipherguard/ids/features.py`) fixes 42 features in a stated order. Three are categorical: `proto` (six values listed for the synthetic generator), `service` "
          "(thirteen) and `state` (twelve); the real dataset has more values, which is why its encoded vector has 192 inputs instead of 70. The preprocessor's one-hot encoder is configured "
          "to ignore unseen categories, so a value that was not in the training data produces an all-zero block instead of an error."),

        H2("5.6 Algorithm Design"),
        H3("5.6.1 SecureChannel"),
        FIG(F.diag("11_flowchart_securechannel.png"), "Figure: flowchart of SecureChannel encryption and verified decryption.", 5.6),
        P("The channel follows the standard hybrid pattern: an asymmetric step agrees a key and a symmetric authenticated cipher protects the data. With the cloud's long-term public key Q_c and "
          "the sender's fresh private key d_e, the design is:"),
        EQ("Z = d_e · Q_c  (ECDH on NIST P-256);   K = HKDF-SHA256(Z, salt = none, info = \"cipherguard-shield-v1\", L = 32 bytes)"),
        EQ("(C, T) = AES-256-GCM-Enc_K(N, P),  N = 96 random bits;   P = AES-256-GCM-Dec_K(N, C, T)  or  reject"),
        P(f"The primitives are those specified in NIST SP 800-56A [{R['sp80056a']}], RFC 5869 [{R['hkdf']}], FIPS 197 [{R['aes']}] and NIST SP 800-38D [{R['gcm']}]. The cloud computes the same Z with its private "
          "key and the sender's ephemeral public key, so the sender never needs to know a secret that the cloud holds. Because every message also gets a new key, a repeated nonce would not by itself break the scheme, but the implementation "
          f"still draws a random 96-bit nonce for every message; the benchmark saw {F.CRY['uniqueness']['distinct_nonces']:,} distinct nonces in "
          f"{F.CRY['uniqueness']['encryptions']:,} encryptions. The envelope's fixed overhead is {F.ENVELOPE_OVERHEAD_BYTES} bytes."),
        P("The deviation from the batch objective is a design choice recorded here: the key agreement uses elliptic curves instead of RSA. The RSA-OAEP alternative "
          f"[{R['oaep']}] wraps a random AES key with the cloud's RSA public key; its wrapped key is 256 bytes for a 2048-bit modulus against the 65-byte ephemeral point, and the cloud pays "
          "an RSA private-key operation per message. The benchmark in Chapter 8 compares the two."),
        H3("5.6.2 ThreatSense scoring"),
        FIG(F.diag("10_flowchart_scoring.png"), "Figure: flowchart of the scoring algorithm.", 5.0),
        FIG(F.diag("12_model_architecture.png"), "Figure: architecture of the stacked detector.", 5.6),
        P(f"Preprocessing scales each numeric feature to the range 0 to 1 with min-max normalisation, x' = (x - min) / (max - min), the same first step as the base paper [{R['base']}], and "
          "one-hot encodes the three categorical features. The first model is XGBoost [" + str(R['xgboost']) + "] with 200 trees, depth 6, learning rate 0.08, row and column subsampling of 0.85 and "
          "scale_pos_weight equal to the ratio of normal to attack rows. The second is a one-dimensional CNN written in PyTorch [" + str(R['pytorch']) + f"], trained with Adam [{R['adam']}] at 0.001, "
          f"batch size 256, at most 15 epochs and early stopping with patience 5; it has {F.CNN_PARAMS_70:,} parameters at 70 inputs. Its loss is plain binary cross-entropy: the TensorFlow code path "
          "applies balanced class weights, the PyTorch path that actually ran does not."),
        P(f"The two probabilities are fused by stacking [{R['stacking']}]: a logistic regression is fitted on the validation split and applied to the test split."),
        EQ("p = σ(w1 · p_xgb + w2 · p_cnn + b);   label = attack if p ≥ 0.5, otherwise normal"),
        P(f"For the shipped bundle the fitted weights are w1 = {_W[0]:.2f} and w2 = {_W[1]:.2f} with b = {_B:.2f}. Severity depends only on p: critical for p ≥ {F.SEVERITY['critical']:.2f}, "
          f"high for p ≥ {F.SEVERITY['high']:.2f}, medium for any other attack, and low for normal traffic. The base paper fuses its two classifiers with a double-sigmoid median min-max "
          f"normalisation (DSMMN-SLF); stacking is a simpler analogue, and the documents never call it by that name."),

        H2("5.7 Module Design"),
        TAB("Modules, responsibilities and size", ["Module / file", "Responsibility", "Lines"], [
            ["`cipherguard/crypto/secure_channel.py`", "KeyPair (P-256 generation, X9.62 encode/decode); SecureChannel: derive_session_key (ECDH + HKDF), encrypt, decrypt (length checks), encrypt_with_ephemeral, base64 helpers; module-level mock cloud key pair", "160"],
            ["`cipherguard/ids/features.py`", "42-feature schema, categorical list, label and attack-category column names, allowed category values", "32"],
            ["`cipherguard/ids/preprocessing.py`", "ColumnTransformer (MinMaxScaler + OneHotEncoder with unknown ignored); tolerant CSV loader; label coercion", "110"],
            ["`cipherguard/ids/synthetic.py`", "synthetic UNSW-NB15-schema generator with 2.5% label noise", "127"],
            ["`cipherguard/ids/train.py`", "backend probe, XGBoost, CNN (TensorFlow or PyTorch), stacking, evaluation, artefact and report writing", "462"],
            ["`cipherguard/ids/inference.py`", "ThreatSenseEngine: load artefacts, prepare features, XGBoost + CNN + meta prediction, severity, metrics read", "186"],
            ["`cipherguard/api/main.py`", "FastAPI routes, validation, in-memory alert and key caches, static files, model and report directory settings", "382"],
            ["`app.py`", "entry point; reads `BACKEND_PORT` from the environment or `.env`", "23"],
            ["`web/` (legacy dashboard)", "HTML, JavaScript and CSS dashboard served by the API", "566"],
            ["`frontend/src/` (React console)", "pages, components, hooks and libraries of the console", "3,210"],
            ["`scripts/` and `tests/`", "capture and smoke scripts, experiments, benchmarks, fetch, serve, bundle builder; 26 tests", "see Chapter 7"],
        ], widths=[2.2, 3.5, 0.6], size=9.5, align=["l", "l", "c"]),
        P("The modules are small and have one reason to change each. `features.py` is the single source of the column order that `preprocessing.py`, `train.py`, `inference.py` and `main.py` "
          "all import, so the schema cannot drift between training and serving. `main.py` is the only module that touches HTTP."),

        H2("5.8 API Design"),
        TAB("HTTP interface", ["Method and path", "Request", "Response", "Errors"], [
            ["GET /api/health", "none", "status, product, version, engine_loaded", "-"],
            ["GET /api/metrics", "none", "contents of `reports/metrics.json`", "404, 503, 500"],
            ["POST /api/ids/score", "JSON object with any subset of the 42 features", "label, confidence, severity, xgb_score, cnn_score, alert (attacks)", "400 invalid, 503 / 500 engine"],
            ["POST /api/ids/score-batch", "multipart CSV, at most 10 MB and 10,000 rows", "total, attack_count, normal_count, results (first 1,000 rows)", "400 non-CSV / empty / too large, 500, 503"],
            ["GET /api/alerts?limit=", "limit 1 to 500", "alerts (newest first), total", "-"],
            ["DELETE /api/alerts", "none", "cleared: true", "-"],
            ["POST /api/crypto/encrypt", "JSON `plaintext`, non-empty, at most 1 MB", "ciphertext, nonce, tag, ephemeral_public, algorithm, key_exchange, note", "400"],
            ["POST /api/crypto/decrypt", "ciphertext, nonce, tag, ephemeral_public", "plaintext, verified", "400 bad base64, missing key, tag or key mismatch"],
            ["POST /api/crypto/encrypt-file", "multipart file, non-empty, at most 5 MB", "filename, envelope fields, original_size, encrypted_size", "400"],
            ["GET /docs, /openapi.json", "none", "interactive API documentation", "-"],
            ["GET /, /static/*", "none", "legacy dashboard", "404 for unknown API paths"],
        ], widths=[1.5, 1.7, 2.0, 1.1], size=9, align=["l", "l", "l", "l"]),
        P("Validation is strict and returns a meaningful status instead of a stack trace: an empty plaintext, a file of the wrong type, malformed base64 and a mismatched tag all return 400 with a "
          "message. A model that is not loaded returns 503. Request bodies are plain JSON; CORS is open to any origin because the server is bound to localhost, a setting that "
          "would have to change with any real deployment."),
        P("The two directory settings, `CIPHERGUARD_MODELS_DIR` and `CIPHERGUARD_REPORTS_DIR`, let the same API serve a different model bundle. They were added during the documentation "
          "run so that the bundle trained on real UNSW-NB15 flows could be shown in the console without replacing the shipped files."),

        H2("5.9 User Interface Design"),
        P("The console is a React single-page application built on a dark, monospaced design kit with a light theme as an alternative (the choice is remembered in the browser). A sidebar "
          "lists the four working screens with keyboard shortcuts, a command palette opened with the slash key jumps to any screen, and an engine badge polls the health route every "
          "five seconds. Screenshots of every screen appear in Chapter 8; this section describes their purpose."),
        TAB("Console routes", ["Route", "Screen", "What the operator does"], [
            ["`/`", "Landing page", "sees live counters and a terminal that calls the real API"],
            ["`/app`", "Live scoring", "fills or presets a flow record, scores it, uploads a CSV, watches the session log and charts"],
            ["`/app/secure`", "Secure transfer", "encrypts text or a file, decrypts and verifies at the cloud, tampers with the ciphertext"],
            ["`/app/alerts`", "Alerts", "filters by severity, refreshes, clears all"],
            ["`/app/performance`", "Model performance", "reads the held-out metrics, confusion matrix and model comparison"],
        ], widths=[1.3, 1.5, 3.5], size=10, align=["l", "l", "l"]),
        B("The scoring form exposes three selectors and twelve numeric fields and keeps the remaining 27 features in an advanced section, so that any of the 42 features can be set.",
          "Presets for a normal flow and an attack flow fill the form and score it, which makes the demonstration repeatable.",
          "The performance screen states the data mode in a banner, so a reader sees that the shipped numbers come from synthetic data.",
          "Errors from the API (400, 503, 500) are shown as messages and never as blank screens."),

        H2("5.10 Key Design Decisions"),
        TAB("Decisions and their reasons", ["Decision", "Reason", "Consequence"], [
            ["ECDH P-256 + HKDF + AES-256-GCM, not RSA + AES", "short keys, fresh key per message, one authenticated primitive", "differs from objective 1; RSA hybrid benchmarked as baseline"],
            ["Random 96-bit nonce per message", "simple, and safe with a fresh key per message", "nonce uniqueness verified over 20,000 messages"],
            ["Library cryptography only", "avoids implementation errors in primitives", "security rests on reviewed standards, not on a new scheme"],
            ["XGBoost + 1D CNN + stacking", "strong tabular model, a neural model for diversity, a cheap fusion", "stacking did not beat XGBoost alone on real data (Chapter 8)"],
            ["Schema of 42 UNSW-NB15 features", "same features for synthetic and real data", "retraining on real data is a file drop"],
            ["In-memory alerts and keys", "no database dependency for a demonstration", "state is lost on restart"],
            ["Mock cloud in the same process", "lets the whole channel be tested without infrastructure", "no real upload; cloud key not persisted"],
            ["Scoring independent of transfer", "each lane testable alone", "no automatic blocking of flagged sessions"],
        ], widths=[1.8, 2.3, 2.2], size=9.5, align=["l", "l", "l"]),

        H2("5.11 Security and Error-Handling Design"),
        P("The security design is described against a simple threat model, and the limits of that model are stated. The attacker considered is a party who can read and modify messages "
          "between the sender and the cloud endpoint, but who does not hold the cloud's private key. Against that attacker the channel provides confidentiality of the payload and "
          "detection of any change to the ciphertext, the nonce, the tag or the key material, because the GCM tag covers them. Replay of an old envelope is not prevented: the "
          "service has no message counter or timestamp, so a replayed envelope decrypts again. Traffic analysis is not hidden: message length equals plaintext length."),
        TAB("Controls and their limits", ["Control", "What it does", "Limit"], [
            ["Authenticated encryption (AES-256-GCM)", "rejects modified ciphertext, tag or nonce", "no replay protection"],
            ["Ephemeral ECDH per message", "a new key for each message; compromise of one key exposes one message", "the cloud's long-term key, if stolen, lets an attacker who recorded envelopes derive their keys, so there is no forward secrecy against that key"],
            ["Length and type checks", "nonce 12 B, tag 16 B, key 32 B; base64 validation", "-"],
            ["Size limits", "1 MB text, 5 MB file, 10 MB CSV, 10,000 rows", "no rate limiting"],
            ["Localhost binding", "the server listens on 127.0.0.1", "no authentication or TLS if exposed"],
            ["No secrets in logs", "plaintext and keys are not written to logs", "the session-key cache keeps keys in memory"],
        ], widths=[1.8, 2.4, 2.1], size=9.5, align=["l", "l", "l"]),
        P("The row on forward secrecy deserves a precise reading. Each message uses a fresh sender key, so the sender's ephemeral secrets are discarded; but the cloud's long-term key pair "
          "is the other half of every ECDH exchange, so a party who later obtains it can recompute the session keys of recorded envelopes. The design therefore gives per-message key "
          "independence, not full forward secrecy; achieving the latter would need an interactive handshake with ephemeral keys on both sides, which is future work."),
        P("Errors follow one rule: a failure is reported with a status code and a short message, and the server keeps running. The decrypt route returns the same 400 status for a wrong tag and a "
          "wrong key, and its message names both causes, so a client cannot tell which one failed."),
    ]
