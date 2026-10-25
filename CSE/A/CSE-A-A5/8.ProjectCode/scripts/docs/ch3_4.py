"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for CipherGuard Shield."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

_SC1 = F.crypto_row("sc", "1 KB", "encrypt")
_SC1D = F.crypto_row("sc", "1 KB", "decrypt")
_SC100 = F.crypto_row("sc", "100 KB", "encrypt")
_SC5 = F.crypto_row("sc", "5 MB", "encrypt")
_AES5 = F.crypto_row("aes", "5 MB", "encrypt")
_IDS1 = F.IP["ids_score_single"]["median_ms"]
_IDS1000 = F.IP["ids_batch_1000_rows"]["median_ms"]
_TRANSFER = F.IP["protected_transfer_100kb"]["median_ms"]
_XGB_S = F.OFF["train_seconds"]["xgb"]
_CNN_S = F.OFF["train_seconds"]["cnn"]
_STACK = F.OFFS["stack"]["accuracy"]["mean"]
_XGB = F.OFFS["xgb"]["accuracy"]["mean"]


def blocks():
    out = chapter3() + chapter4()
    return _report_trim(out) if F.REPORT else out


def _report_trim(bl):
    """Report mode: drop the least essential sections and one table so the full report stays within its page budget."""
    drop_h2 = ("3.6 Risk Assessment", "4.8 Usage Scenarios")
    out, skipping = [], False
    for b in bl:
        if b[0] in ("h1", "h2"):
            skipping = b[0] == "h2" and b[1] in drop_h2
        if skipping:
            continue
        if b[0] == "tab" and b[1].startswith("Work packages in the order"):
            continue
        out.append(b)
    return out


# =====================================================================================================================
def chapter3():
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether a project can be built, run and maintained with the resources at hand. For CipherGuard Shield the question was answered partly by "
          "analysis and partly by building the system and measuring it on the development machine, so most entries below carry a measured value rather than an estimate. "
          "Where a question could not be settled with the data available to the team, the entry says so."),

        H2("3.1 Technical Feasibility"),
        P("The technical risk lay in four places: whether authenticated public-key encryption could be implemented correctly with a maintained library instead of hand-written "
          "arithmetic; whether a tabular intrusion detector combining gradient-boosted trees and a one-dimensional convolutional network could be trained and served on an "
          "ordinary processor; whether the real UNSW-NB15 benchmark could be obtained and used with the same 42-feature schema as the application; and whether the pieces "
          "could be combined behind one API and one console. The development machine is a desktop with an Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of RAM and "
          "no graphics processor in use, running Windows 11. It was shared with other jobs during every measurement, so the figures are indicative."),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can ECDH, HKDF and AES-256-GCM be used without writing cryptographic primitives?",
             f"Yes: the `cryptography` package (version {F.CRY['machine']['cryptography']}) supplies P-256 ECDH, HKDF-SHA256 and AESGCM; SecureChannel is 163 lines of glue", "Feasible"],
            ["Is encryption fast enough for interactive use?",
             f"SecureChannel encrypts 1 KB in {_SC1:.2f} ms and 100 KB in {_SC100:.2f} ms; 5 MB in {_SC5:.1f} ms (raw AES-GCM {_AES5:.1f} ms); decrypting 1 KB takes {_SC1D:.2f} ms", "Feasible"],
            ["Can the detector be trained on a CPU?",
             f"XGBoost trains on 149,039 real flows in {_XGB_S:.1f} s; the 1D CNN needs {_CNN_S:.0f} s on the loaded machine (15 epochs at most)", "Feasible"],
            ["Is scoring fast enough?",
             f"one flow scores in a median of {_IDS1:.2f} ms in process and {F.API['score_single']['median_ms']:.1f} ms over HTTP; 1,000 flows in {_IDS1000:.1f} ms", "Feasible"],
            ["Is the detector accurate on real traffic?",
             f"official UNSW-NB15 partition, 5 seeds: stacked ensemble {_STACK:.3f}, XGBoost alone {_XGB:.3f} accuracy; the shipped synthetic-trained model reaches only "
             f"{F.SHIFT['shipped_on_real_official_test']['stack']['accuracy']:.3f} on the same test flows", "Feasible, with a caveat"],
            ["Can the real benchmark be obtained?",
             f"yes: the official training ({F.OFF['train_rows']:,} flows) and testing ({F.OFF['test_rows']:,} flows) sets were downloaded as 19 MB of parquet and have the 42 features the application uses", "Feasible"],
            ["Can everything run behind one local API?",
             "FastAPI, ten routes, in-memory alert log, no external service; 26 automated tests and 15 smoke checks pass", "Feasible"],
        ], widths=[1.9, 3.3, 1.1], size=10, align=["l", "l", "l"]),
        P("Where the checks are weakest is the data behind the shipped model. The application was delivered with a model trained on a synthetic dataset generated in "
          f"the project (`cipherguard/ids/synthetic.py`, {F.SYNTH_ROWS:,} rows) because the real CSV files were not placed in `data/raw/`. Chapter 8 shows that this model "
          "does not transfer to real traffic. The technical feasibility of intrusion detection on UNSW-NB15 was therefore established by a separate set of experiments "
          "run on the real data with the same pipeline; the shipped default was left unchanged."),
        P("A second, smaller risk is the dependency chain. On the Windows host used here, importing `numpy` or `pandas` before `torch` made the PyTorch libraries fail to "
          "initialise (WinError 1114). The experiment scripts, the test configuration and the helper `scripts/serve.py` therefore import `torch` first. The risk is real "
          "but cheap to remove, and `run.bat` creates its own virtual environment with the pinned versions."),

        H2("3.2 Economic Feasibility"),
        P("Every component of the system is free and open source, and the work ran on a computer the team already had, so no money was spent on software, licences or cloud "
          "services. The table lists what was used. Cash costs for a real deployment, such as a cloud account, TLS certificates or a managed key store, were not part of the "
          "project and were not estimated, because the cloud endpoint is a mock inside the same process."),
        TAB("Components, licences and cost to the project", ["Item", "Role", "Licence", "Cost"], [
            ["Python 3.11, FastAPI, Uvicorn", "language and web API", "PSF / MIT / BSD", "none"],
            ["`cryptography`", "P-256 ECDH, HKDF, AES-GCM, RSA (benchmark)", "Apache-2.0 / BSD", "none"],
            ["XGBoost, scikit-learn, PyTorch", "detector, preprocessing, CNN", "Apache-2.0 / BSD", "none"],
            ["React 19, Vite, Tailwind, Recharts", "console", "MIT", "none"],
            ["UNSW-NB15 dataset", "real benchmark flows", "free for academic use, cite the authors", "none"],
            ["Development computer (i5-12500, 15.7 GB)", "all builds and measurements", "owned", "not purchased for the project"],
            ["pytest, Playwright", "tests and screenshots", "MIT / Apache-2.0", "none"],
        ], widths=[1.9, 2.1, 1.5, 0.9], size=10, align=["l", "l", "l", "l"]),
        P("The only recurring cost the project can name is electricity for the machine, which was not measured. The one-time compute cost of the experiments was small: the "
          f"complete study (five official-partition runs, ten paper-protocol runs and the shift tests) finished in about 25 minutes of wall-clock time, and the cryptography "
          f"benchmark in a few minutes. The economic case for the design is that both protections run on commodity hardware: one protected 100 KB transfer costs {_TRANSFER:.1f} ms in process."),

        H2("3.3 Operational Feasibility"),
        P("The system is meant to be used by a security analyst or a student demonstrator, not by a developer. The operator starts the application with `run.bat`, which creates a "
          "virtual environment, installs the pinned packages, trains the model if the artefacts are missing, starts the API on port "
          f"{F.API_PORT} and the console on port {F.WEB_PORT}, and opens the browser. From the console the operator can score one traffic record or a CSV, read and clear alerts, "
          "encrypt text or a file, decrypt and verify it at the mock cloud, tamper with a ciphertext to see the integrity check fail, and read the model's held-out metrics."),
        B("**Skills needed:** none beyond using a browser; installing Python 3.10 or newer and Node.js 18 or newer on first use.",
          "**Resources:** HOW_TO_RUN.md asks for about 4 GB of free RAM and 1 GB of disk; the model files occupy about 0.8 MB.",
          "**Maintenance:** retraining is one command (`python -m cipherguard.ids.train`); replacing the data needs only dropping CSV files into `data/raw/`.",
          "**What operations would still need:** authentication, TLS, persistent storage for alerts and keys, and a real cloud endpoint. None of these exist yet (Chapter 10)."),
        P("Docker packaging exists (`Dockerfile`, `docker-compose.yml`, `run-docker.bat`) but was not built or run during this project, so operational feasibility through Docker is "
          "untested."),

        H2("3.4 Schedule Feasibility"),
        P("The repository does not record a calendar plan, and inventing one would be misleading, so the schedule is described by the order in which the work was done, as the "
          "version-control history and the artefacts show. The batch documents for the abstract, introduction, literature survey and objectives were written first; the "
          "backend, the cryptographic channel, the detector and the first dashboard were delivered as the initial project files; the run script was then corrected; the React "
          "console was rebuilt on the Kinetic Mono design kit; and the documentation run added the real-data experiments, the tests, the benchmarks and the documents."),
        TAB("Work packages in the order they were completed", ["Phase", "Work", "Outcome"], [
            ["1", "Problem identification, survey and objectives (batch documents 2 to 6)", "abstract, base paper, introduction, five-paper survey, six objectives"],
            ["2", "Backend, SecureChannel, ThreatSense Engine, legacy dashboard", "FastAPI app, 42-feature pipeline, shipped synthetic-trained bundle"],
            ["3", "Run script and Docker packaging", "`run.bat`, `Dockerfile`, `docker-compose.yml`"],
            ["4", "React console on the V5 kit", "landing, live scoring, secure transfer, alerts, performance"],
            ["5", "Documentation run: real-data experiments, crypto benchmarks, tests, diagrams, documents", "26 tests, 15 smoke checks, `experiments/**/metrics.json`, eleven documents"],
        ], widths=[0.6, 3.4, 2.3], size=10, align=["c", "l", "l"]),
        P("The schedule held because the design is small: two cooperating modules, ten routes and one trained model family. The part that would have been hardest to schedule, "
          "obtaining and using real benchmark data, turned out to be a download plus one script."),

        H2("3.5 Advantages and Constraints"),
        H3("3.5.1 Advantages"),
        B("Both protections sit on one data path and one code base, so their combined cost can be measured rather than assumed.",
          "Fresh ephemeral keys for every message mean that compromise of one session key does not expose other messages.",
          "In 5,000 tamper trials (five kinds of modification, 1,000 each) every modified message was rejected, 1,000 untouched messages were all accepted, and no nonce repeated in 20,000 encryptions.",
          "The same pipeline trains on synthetic or real flows without code changes, so moving to real data is a file drop.",
          "Everything is open source and runs on one ordinary machine."),
        H3("3.5.2 Constraints"),
        B("The cloud endpoint is a mock in the same process; no data is uploaded anywhere.",
          "Detection is run on flow records or CSV rows; the system does not capture packets.",
          "The default model is trained on synthetic data and is not a credible detector for real traffic.",
          "Alerts and the cloud key pair live in memory and are lost when the server restarts.",
          "There is no authentication, TLS or rate limiting, so the server is bound to 127.0.0.1."),
        P(f"The base paper [{R['base']}] reports an intrusion detector together with an enhanced elliptic-curve scheme and states that a formal security proof is left for future work; "
          "the feasibility judgement here is the same in spirit: the engineering is feasible and measured, the security argument rests on standard, reviewed primitives rather than on a new scheme."),

        H2("3.6 Risk Assessment"),
        P("The risks that could have stopped the project, and what happened to each, are listed below. Two of them materialised, and both are documented as findings instead of being hidden."),
        TAB("Risks and outcomes", ["Risk", "Likelihood and impact", "What happened"], [
            ["Real benchmark data unavailable", "medium; the detector would have no credible evaluation", "materialised for the shipped model (synthetic fallback was used); resolved for the experiments by downloading the official partition"],
            ["Synthetic data misleads the reader", "high; headline accuracy would be meaningless", "materialised: the shipped model scores " + f"{F.SHIFT['shipped_on_real_official_test']['stack']['accuracy']:.3f}" + " on real flows; stated in every results section"],
            ["Cryptographic misuse (nonce reuse, key reuse, unauthenticated mode)", "low with a library; impact severe", "avoided by using AES-GCM with a random nonce and a fresh key; 20,000-message uniqueness test"],
            ["Library incompatibility between training and serving", "medium", "model files load because scikit-learn and XGBoost match the pins; PyTorch import order handled in the scripts"],
            ["Stacking brings no benefit", "unknown at design time", "materialised on real data: XGBoost alone is better on the official partition (Chapter 8)"],
            ["Over-claiming against the base paper", "medium", "avoided: the comparison states that subsets and protocols differ and that EECC and the quantum-inspired network are not reproduced"],
        ], widths=[1.9, 1.7, 2.7], size=9.5, align=["l", "l", "l"]),
        P("The conclusion of the feasibility study is that the project was feasible as a measured engineering study: the channel, the detector and the console were built and tested with free "
          "tools on one machine. It was not shown feasible, and the project does not claim it, to deploy the system against live cloud traffic."),
    ]


# =====================================================================================================================
def chapter4():
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter describes the situation the project starts from, the system that was built in response, the functional and non-functional requirements it was built "
          "to meet, and the hardware, software, users and constraints involved. Requirement identifiers (FR-n and NFR-n) are used again in Chapter 7 where each is tested."),

        H2("4.1 Existing System and Its Limitations"),
        P("Data that is stored or processed in a public cloud is readable by the provider unless it is encrypted before upload, and data in transit is exposed to anyone on the "
          f"path. The introduction of the base paper [{R['base']}] makes the same point and reviews the alternatives: firewalls, antivirus software and intrusion detection systems "
          "for network protection, and public-key schemes such as Diffie-Hellman, ECC and RSA for confidentiality. In practice the two kinds of protection are separate products "
          "run by separate teams."),
        P(f"The literature survey of this batch lists four further works besides the base paper: a study of encryption and anomaly detection for secure storage and transmission [{R['s_fmdb']}], "
          f"a multi-cloud data-deletion method with intrusion detection [{R['s_ijsr']}], a federated-learning attack detector with improved Blowfish encryption [{R['s_blowfish']}] and a hybrid-encryption "
          f"privacy framework for cloud transmission [{R['s_hybrid_gmr']}]. The survey's own conclusion is that cryptography and intrusion detection are mostly treated as separate concerns "
          "and that few systems show a single transmission path where both operate and the combined overhead is measured."),
        TAB("Limitations of the existing approach", ["Limitation", "Consequence"], [
            ["Symmetric encryption alone leaves key exchange exposed", "an interceptor who obtains the key reads everything"],
            ["Public-key encryption of whole payloads is slow", "unsuitable for files and bulk data; hybrid schemes are needed"],
            ["Encryption does not detect an attacker holding valid credentials", "a second, behaviour-based layer is needed"],
            ["Detection and encryption are built and evaluated separately", "their combined overhead and their interaction are unknown"],
            ["Intrusion detectors are reported on subsets, often balanced and randomly split", "published accuracy may not describe deployment (Chapter 8)"],
            ["New cryptographic schemes are proposed without a formal proof", f"[{R['base']}] states this for its own scheme; standard reviewed primitives avoid the issue"],
        ], widths=[3.0, 3.3], size=10.5, align=["l", "l"]),

        H2("4.2 Proposed System and Its Advantages"),
        P("CipherGuard Shield is a web application with two cooperating modules. **SecureChannel** protects a payload before transmission: the sender generates an ephemeral "
          "P-256 key pair, performs ECDH against the cloud's long-term public key, derives a 256-bit key with HKDF-SHA256 and encrypts with AES-256-GCM using a random 12-byte "
          "nonce. The cloud derives the same key and refuses any message whose 16-byte tag does not verify. **ThreatSense Engine** classifies network flow records as normal or "
          "attack with XGBoost and a one-dimensional CNN whose outputs are combined by a logistic-regression meta-model, assigns a severity and appends attacks to an alert log. "
          "A React console and the original HTML dashboard sit on top of a FastAPI service."),
        P("A deliberate difference from the batch objectives must be stated. Objective 1 asked for AES with RSA for key exchange. The product uses ECDH on P-256 instead, because "
          "the keys are shorter and every message gets a fresh key. RSA-OAEP with AES-GCM was implemented only as a benchmark baseline, so that the choice is backed by "
          f"measurement: at 1 KB the cloud-side decrypt takes {_SC1D:.2f} ms with SecureChannel against {F.crypto_row('rsa2048', '1 KB', 'decrypt'):.2f} ms for RSA-2048 and "
          f"{F.crypto_row('rsa3072', '1 KB', 'decrypt'):.2f} ms for RSA-3072, while RSA encryption is cheaper at {F.crypto_row('rsa2048', '1 KB', 'encrypt'):.3f} ms against {_SC1:.2f} ms."),
        TAB("Advantages of the proposed system over the existing practice", ["Advantage", "Evidence"], [
            ["Confidentiality and integrity in one primitive", "AES-256-GCM tag; 5 tamper kinds x 1,000 trials all rejected"],
            ["Fresh key per message", f"20,000 encryptions, {F.CRY['uniqueness']['distinct_nonces']:,} distinct nonces; new ephemeral key each time"],
            ["Low fixed overhead", f"{F.ENVELOPE_OVERHEAD_BYTES} bytes per message (12 nonce + 16 tag + 65 ephemeral key)"],
            ["Detection and encryption measured together", f"protected 100 KB transfer {_TRANSFER:.2f} ms; detection is {F.IP['share_of_transfer_median']['ids'] * 100:.0f}% of it"],
            ["Operator-visible alerts with severity", "alert log, severity bands low / medium / high / critical, console table"],
            ["Reproducible with real data", "one script downloads UNSW-NB15; experiments write JSON that the documents read"],
        ], widths=[2.4, 3.9], size=10.5, align=["l", "l"]),

        H2("4.3 Functional Requirements"),
        P("The functional requirements were derived from the six batch objectives and from the features of the original dashboard. The last column states what the evidence "
          "for each requirement is in this project."),
        TAB("Functional requirements", ["ID", "Requirement", "Status and evidence"], [
            ["FR-1", "Encrypt a text payload (non-empty, at most 1 MB) with a fresh ephemeral key", "Met; tests `test_round_trip`, `test_encrypt_decrypt_round_trip`"],
            ["FR-2", "Encrypt a file of at most 5 MB", "Met; `encrypt-file` tests including the 5 MB limit"],
            ["FR-3", "Decrypt and verify at the cloud, rejecting a bad tag with HTTP 400", "Met; 1,000/1,000 tamper trials per case"],
            ["FR-4", "Derive the key from the cloud private key when the session cache is empty", "Met; test `test_decrypt_uses_cloud_private_key_when_cache_is_empty`"],
            ["FR-5", "Score one flow record (any subset of the 42 features; defaults fill the rest)", "Met; smoke check and API tests"],
            ["FR-6", "Score a CSV of up to 10,000 rows and 10 MB, rejecting non-CSV and empty files", "Met; API tests"],
            ["FR-7", "Return label, confidence, severity and the two model scores", "Met"],
            ["FR-8", "Log attacks with timestamp, severity, confidence, features and scores (newest 500)", "Met in memory only"],
            ["FR-9", "List alerts (limit 1 to 500) and clear them", "Met"],
            ["FR-10", "Show held-out metrics from `reports/metrics.json`", "Met; shows the synthetic bundle unless another bundle is configured"],
            ["FR-11", "Serve a different model bundle through environment variables", "Added in this run (`CIPHERGUARD_MODELS_DIR`, `CIPHERGUARD_REPORTS_DIR`)"],
            ["FR-12", "Provide a console with live scoring, secure transfer, alerts and performance screens", "Met; screens in Chapter 8"],
            ["FR-13", "Report engine health", "Met; `GET /api/health`"],
            ["FR-14", "Retrain from CSV files placed in `data/raw/`", "Met by code; exercised on real data by the experiment scripts"],
        ], widths=[0.6, 3.5, 2.2], size=9.5, align=["c", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and the evidence", ["ID", "Requirement", "Measured evidence"], [
            ["NFR-1", "Interactive scoring latency", f"{_IDS1:.2f} ms in process, {F.API['score_single']['median_ms']:.1f} ms over HTTP (median)"],
            ["NFR-2", "Interactive encryption latency for text", f"{F.API['encrypt_1kb_text']['median_ms']:.1f} ms encrypt, {F.API['decrypt_1kb_text']['median_ms']:.1f} ms decrypt over HTTP (1 KB)"],
            ["NFR-3", "File encryption within seconds", f"1 MB file over HTTP {F.API['encrypt_file_1mb']['median_ms']:.1f} ms (median)"],
            ["NFR-4", "Integrity: any modification must be rejected", "5,000 tamper trials all rejected; 1,000 untouched controls all accepted"],
            ["NFR-5", "Key and nonce freshness", "20,000 distinct nonces; ephemeral key per message"],
            ["NFR-6", "Input validation", "size, type, base64 and length checks; tests for each"],
            ["NFR-7", "Detection quality on real traffic", f"stacked accuracy {_STACK:.3f}, ROC-AUC {F.OFFS['stack']['roc_auc']['mean']:.3f}; false-positive rate {F.OFFS['stack']['fpr']['mean']:.3f} (a weakness)"],
            ["NFR-8", "Reproducibility", "seeds fixed, five-seed and ten-repetition studies, all results in JSON"],
            ["NFR-9", "Portability", "Windows tested; the code has no Windows-specific calls; Docker untested"],
            ["NFR-10", "Security of deployment", "Not met: no authentication, TLS or rate limiting; bound to localhost"],
            ["NFR-11", "Persistence of alerts and keys", "Not met: memory only"],
        ], widths=[0.7, 2.4, 3.2], size=9.5, align=["c", "l", "l"]),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum stated by the project", "Machine used for all measurements"], [
            ["Processor", "any 64-bit CPU; no GPU needed", "Intel Core i5-12500, 6 cores / 12 threads"],
            ["Memory", "about 4 GB free (HOW_TO_RUN.md)", "15.7 GB, shared with other running jobs"],
            ["Disk", "about 1 GB for the environment and models", "models 0.8 MB; real dataset 19 MB as parquet"],
            ["Network", "none for scoring and encryption; internet only to install packages and fetch the dataset", "local loopback"],
        ], widths=[1.2, 2.6, 2.5], size=10.5, align=["l", "l", "l"]),

        H2("4.6 Software Requirements"),
        TAB("Software: pinned versions and what actually ran", ["Component", "Pinned in requirements.txt", "Used for the measurements"], [
            ["Python", "3.10 to 3.12", F.CRY["machine"]["python"]],
            ["FastAPI / Uvicorn / Pydantic", "0.110.0 / 0.29.1 / 2.6.3", "0.143.3 / 0.54.0 / 2.14.1"],
            ["cryptography", "42.0.5", F.CRY["machine"]["cryptography"]],
            ["XGBoost / scikit-learn", "2.0.3 / 1.5.0", "2.0.3 / 1.5.0"],
            ["PyTorch", "2.2.0", "2.14.1 (CPU)"],
            ["NumPy / pandas / joblib", "1.26.4 / 2.2.1 / 1.3.2", "1.26.4 / 2.2.1 / 1.3.2"],
            ["Node.js", "18 or newer", "24.19"],
            ["Browser for screenshots", "-", "Chromium driven by Playwright 1.44"],
        ], widths=[2.1, 2.1, 2.1], size=10.5, align=["l", "l", "l"]),
        P("The measurements therefore ran on newer web-framework and PyTorch versions than the pins; the pinned versions are the ones `run.bat` installs. The test suite passed on "
          "the newer versions, and the model files load because scikit-learn and XGBoost match the pins."),

        H2("4.7 User Roles and Constraints"),
        TAB("User roles", ["Role", "What the role does", "Interface"], [
            ["Operator / security analyst", "scores flows, reads alerts, encrypts and verifies transfers, reads metrics", "console and legacy dashboard"],
            ["Developer / administrator", "retrains models, runs experiments and tests, configures ports and bundles", "command line, `.env`"],
            ["Cloud endpoint (mock)", "holds the long-term key pair, derives keys, verifies tags", "inside the API process"],
        ], widths=[1.8, 3.0, 1.5], size=10.5, align=["l", "l", "l"]),
        P("The constraints that bound the design are the following. The server listens on 127.0.0.1 only. Uploads are limited as stated in FR-1, FR-2 and FR-6. The detector expects "
          "the 42 UNSW-NB15 features; missing columns are filled with defaults, which silently weakens a score. The default models were trained on synthetic data. All state is in "
          "process memory. These constraints are repeated as limitations in Chapter 10 and in the Scope and Limitations document."),

        H2("4.8 Usage Scenarios"),
        P("Three scenarios were used to check that the requirements describe something an operator would actually do, and Chapter 8 reproduces each of them with screenshots."),
        N("**Screen a batch of flows.** The analyst uploads a CSV of flow records (FR-6). The console shows the number of rows scored, the attacks and normal flows found, and, when the CSV "
          "carries a `label` column, how many verdicts agree with it. Attacks appear in the alert table with a severity (FR-7, FR-8, FR-9).",
          "**Send a protected message.** The operator types a message and chooses encrypt (FR-1). The console shows the ciphertext, nonce, tag and ephemeral public key. Decrypting at the cloud "
          "returns the plaintext and the word verified (FR-3). Pressing the tamper button changes one ciphertext byte, and the next decryption is refused with an error.",
          "**Check how far to trust the numbers.** The analyst opens the performance screen (FR-10), reads the data-mode banner and the confusion matrix, and compares them with the real-data bundle "
          "served through the directory settings (FR-11)."),
        H2("4.9 Data Requirements"),
        P(f"The detector needs labelled network flows with the 42 features in `features.py`. The shipped bundle uses {F.SYNTH_ROWS:,} generated rows. The experiments use the official UNSW-NB15 training "
          f"set ({F.OFF['train_rows']:,} flows: 56,000 normal, 119,341 attack) and testing set ({F.OFF['test_rows']:,} flows: 37,000 normal, 45,332 attack, {F.OFF['test_attack_rate'] * 100:.2f}% attack). "
          f"UNSW-NB15 [{R['unsw15']}] was created in the Cyber Range Lab of UNSW Canberra and contains nine attack categories besides normal traffic; the dataset's distributors ask users to cite the original papers "
          f"[{R['unsw15']}], [{R['unsw16']}]. The data are downloaded by `scripts/fetch_unsw_nb15.py` into a git-ignored folder, so the repository does not redistribute them."),
        P("The encryption module needs no dataset; its inputs are user text and files within the stated size limits."),
    ]
