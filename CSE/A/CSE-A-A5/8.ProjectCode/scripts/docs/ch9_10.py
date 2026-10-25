"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""
import os

from . import facts as F
from .blocks import B, CODE, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def c(*keys):
    """Citation string such as [1], [6] from CITE keys."""
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _v():
    """Frequently quoted measured values."""
    sc, xg = F.OFFS["stack"], F.OFFS["xgb"]
    r = F.SHIFT["shipped_on_real_official_test"]["stack"]
    pc = F.OFF["per_category"]
    return {
        "st_acc": F.mstd(F.OFFS, "stack", "accuracy"), "xg_acc": F.mstd(F.OFFS, "xgb", "accuracy"), "cn_acc": F.mstd(F.OFFS, "cnn", "accuracy"),
        "st_f1": F.mstd(F.OFFS, "stack", "f1"), "st_auc": F.mstd(F.OFFS, "stack", "roc_auc"), "st_fpr": F.mstd(F.OFFS, "stack", "fpr"), "xg_fpr": F.mstd(F.OFFS, "xgb", "fpr"),
        "pap_st": F.mstd(F.PAPS, "stack", "accuracy"), "pap_xg": F.mstd(F.PAPS, "xgb", "accuracy"), "pap_pr": F.mstd(F.PAPS, "stack", "precision"),
        "sh_acc": F.f4(F.SHIPPED["accuracy"]), "real_acc": F.f3(r["accuracy"]), "real_auc": F.f3(r["roc_auc"]),
        "fa": F.pct(1 - pc["Normal"]["rate"]), "fz": F.pct(1 - pc["Fuzzers"]["rate"]), "t9_acc": F.f3(F.thr_row(0.9)["accuracy"]), "t9_fpr": F.f3(F.thr_row(0.9)["fpr"]),
        "xfer": f"{F.IP['protected_transfer_100kb']['median_ms']:.1f}", "ids_share": f"{F.IP['share_of_transfer_median']['ids'] * 100:.0f}",
        "enc_share": f"{F.IP['share_of_transfer_median']['encrypt'] * 100:.0f}", "dec_share": f"{F.IP['share_of_transfer_median']['decrypt'] * 100:.0f}",
        "api3": f"{F.API['protected_transfer_via_api_1kb']['median_ms']:.1f}",
        "sc1k_dec": f"{F.crypto_row('sc', '1 KB', 'decrypt'):.2f}", "r2048_dec": f"{F.crypto_row('rsa2048', '1 KB', 'decrypt'):.2f}", "r3072_dec": f"{F.crypto_row('rsa3072', '1 KB', 'decrypt'):.2f}",
        "sc1k_enc": f"{F.crypto_row('sc', '1 KB', 'encrypt'):.2f}", "r2048_enc": f"{F.crypto_row('rsa2048', '1 KB', 'encrypt'):.2f}",
    }


# ---------------------------------------------------------------- document 9: novelty and contributions
def novelty_blocks():
    v = _v()
    b = F.BASE_PAPER_RESULTS
    return [
        H2("2.1 What the base paper contributes"),
        P(f"The base paper {c('base')} proposes a detection model that fuses a quantum-inspired convolutional network with a flatten-layer feature map and an eigenvalue-decomposition block (FLPF with EVD-QNN) and a LeNet classifier through a double-sigmoid, "
          f"median-normalised score-level fusion (DSMMN-SLF), and an enhanced elliptic-curve scheme (EECC) that encrypts data judged free of intrusion. It evaluates on {b['samples']:,} balanced UNSW-NB15 samples and reports a mean accuracy of {b['proposed_mean_accuracy']:.4f}, "
          f"a precision of {b['precision_at_90']:.2f} and an encryption time of {b['enc_time_s']} s. Its own text admits the limits: the quantum network is quantum-inspired and runs on classical hardware, the EECC has no proof of security under the elliptic-curve discrete-logarithm assumption, and the data set is balanced and small."),
        H2("2.2 What is new in this project and what is not"),
        TAB("Novelty against the base paper", ["Aspect", "Base paper", "This project", "New?"],
            [["Detection algorithm", "FLPF-EVD-QNN + LeNet, DSMMN-SLF fusion", "XGBoost + 1D CNN, logistic-regression stacking", "No - standard methods, chosen for transparency and low cost"],
             ["Encryption algorithm", "EECC (non-standard, unproven)", "ECDH P-256 + HKDF-SHA256 + AES-256-GCM, standard primitives from a maintained library", "No - but a deliberate, defensible substitution"],
             ["Key handling", "Static key relations in the scheme", "Fresh ephemeral key pair per message, forward secrecy per message, 93-byte fixed envelope", "Design choice that differs"],
             ["Running system", "Offline simulation", "Working service: REST API, React console, alert log, tamper test, file mode", "Yes"],
             ["Combined overhead", "Detection and encryption timed separately", f"One protected transfer measured end to end: {v['xfer']} ms in process, {v['api3']} ms over HTTP", "Yes"],
             ["Baseline for the key exchange", "AES, ElGamal, Blowfish, ECC, RSA compared on abstract timing", f"RSA-2048/3072-OAEP + AES-GCM benchmarked on the same machine, by payload size", "Yes, as a measurement"],
             ["Training-data audit", "Balanced 9,000-sample subset", f"Synthetic bundle exposed: {v['sh_acc']} on synthetic data against {v['real_acc']} on real flows; real-data experiments on the official partition", "Yes"],
             ["Evaluation protocol", "10 runs on a random balanced subset", "Both that protocol and the official temporally split partition, 5 seeds, thresholds, categories", "Yes"]],
            widths=[1.2, 1.6, 2.4, 1.3], align=["l", "l", "l", "l"], size=9.0),
        H2("2.3 Why the integration counts"),
        P("The literature survey of this batch found one gap: cryptography and intrusion detection are treated as separate concerns, and nobody measures what the pair costs on one transmission path. "
          f"CipherGuard Shield places both behind one API and one console and measures the pair. The result is not what one would assume: detection accounts for {v['ids_share']}% of the per-transfer cost and encryption plus decryption for {int(v['enc_share']) + int(v['dec_share'])}%, "
          "so the cheap, standard cipher can be switched on for every message and the budget question is the detector."),
        P("A second contribution is negative and therefore easy to overlook: the project shows, with the same code, that a model can score 97.33% on the data it was built for and 66% on real traffic, and that a stacked ensemble can be no better than its strongest member. "
          "Reporting these results is part of the method, not an afterthought."),
        H2("2.4 Where this work is weaker than the base paper"),
        B("No quantum-inspired network, no DSMMN fusion and no EECC were reproduced; the comparison with the paper is therefore a comparison of outcomes under a similar protocol, not of methods.",
          f"On the comparable protocol the stacked model reaches {v['pap_st']} accuracy against the paper's {b['proposed_mean_accuracy']:.4f}, and {v['pap_pr']} precision against {b['precision_at_90']:.2f}.",
          "The paper reports attack analyses (brute force, chosen-ciphertext, man-in-the-middle) for its scheme; here only integrity and uniqueness tests were run, and the strength of AES-GCM and P-256 rests on the standards."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The work makes the following contributions."),
        N(f"**A working secure-transmission platform.** SecureChannel encrypts text or files up to 5 MB with ECDH P-256, HKDF-SHA256 and AES-256-GCM using a fresh ephemeral key per message, with tag verification at the cloud and a one-click tamper test.",
          "**An intrusion detector with an alert log and a live console.** The ThreatSense Engine stacks XGBoost and a 1D CNN, returns a label, a confidence and a severity, and appends attacks to an alert list shown in a React console.",
          f"**A measured combined overhead.** One protected 100 KB transfer costs {v['xfer']} ms in process ({v['ids_share']}% detection, {v['enc_share']}% encryption, {v['dec_share']}% decryption) and {v['api3']} ms as three HTTP calls, closing the gap named by the literature survey.",
          f"**A cryptographic baseline comparison.** RSA-2048 and RSA-3072 OAEP hybrids were benchmarked against SecureChannel: RSA wraps a key faster ({v['r2048_enc']} ms against {v['sc1k_enc']} ms at 1 KB) but unwraps it slower ({v['r2048_dec']} and {v['r3072_dec']} ms against {v['sc1k_dec']} ms), and 1,000 trials of each of six tamper cases were all handled correctly.",
          f"**Detection results on real data with an honest protocol.** On the official UNSW-NB15 partition the stacked model reaches {v['st_acc']} accuracy and XGBoost alone {v['xg_acc']}; the base paper's protocol gives {v['pap_st']}; thresholds, categories and seeds are reported.",
          f"**An audit of the synthetic default.** The shipped {v['sh_acc']} accuracy is explained (2.5% label noise cap, three models identical) and contrasted with {v['real_acc']} on real flows; a real-trained bundle can be served with two environment variables.",
          "**Reproducible tooling.** Scripts for data fetching, experiments, crypto benchmarks, pipeline latency, screenshots, 26 automated tests and 15 smoke checks, with every figure in the documents generated from stored JSON."),
        P("None of these contributions is a new algorithm; they are engineering, measurement and honest reporting around standard components."),
    ]


# ---------------------------------------------------------------- document 10: scope and limitations
def scope_blocks():
    return [
        H2("1.1 What is in scope"),
        B("Encrypting text (up to 1 MB) and files (up to 5 MB) before they reach a mock cloud endpoint, and decrypting and verifying them there.",
          "Scoring single flow records and CSV batches (up to 10 MB and 10,000 rows) in the 42-feature UNSW-NB15 schema as normal or attack, with confidence and severity.",
          "An in-memory alert log of up to 500 attack verdicts, an API, a React console and the original HTML dashboard.",
          "Offline training of the detector on synthetic data (shipped default) or on real UNSW-NB15 CSV/parquet files, and serving of a chosen model bundle.",
          "Measurements of detection quality, cryptographic cost and combined overhead on one machine."),
        H2("1.2 What is out of scope"),
        TAB("Items deliberately not covered", ["Item", "Why it is out", "Where it appears"],
            [["Live packet capture and flow export", "Needs privileged network access and a flow exporter; flows are supplied as records or CSV rows", "Future scope"],
             ["Blocking or quarantining a flagged session", "The API does not gate a transfer on the verdict; the operator decides", "Future scope"],
             ["A real cloud provider, upload and download", "The cloud is a mock endpoint with a process-lifetime key pair", "Future scope"],
             ["Key custody (KMS, HSM), certificates, key rotation", "Keys exist only in memory", "Future scope"],
             ["Authentication, TLS, rate limiting", "Local demonstration service bound to 127.0.0.1", "Future scope"],
             ["Persistent storage of alerts", "The alert list is lost on restart", "Future scope"],
             ["The base paper's EECC and quantum-inspired network", "Not reproduced; standard primitives and models were used", "Chapter 8, Section 8.8"],
             ["Adversarial and evasion testing of the detector", "Not attempted", "Limitations"],
             ["Load, concurrency and multi-tenant testing", "Single-user measurements only", "Limitations"]],
            widths=[2.3, 3.0, 1.2], align=["l", "l", "l"], size=9.5),
    ]


def assumption_blocks():
    return [
        P("The results and the design rest on the following assumptions."),
        B("The 42 UNSW-NB15 flow features describe the traffic well enough to separate attacks from normal flows; this holds on the benchmark but is not established for other networks.",
          "Labels in UNSW-NB15 are correct and its official training and testing sets are a fair stand-in for 'the past' and 'the future'.",
          "The mock cloud's key pair, which lives in process memory, stands for a long-term cloud key held securely elsewhere.",
          "The `cryptography` library and the operating system's random number generator are trustworthy; no side-channel or implementation attack is considered.",
          "Operators accept a threshold of 0.5 unless they choose another; the product does not tune it.",
          "The service is run locally (127.0.0.1) by a trusted operator; there is no hostile client."),
    ]


def limitation_blocks():
    v = _v()
    return [
        H2("Data and model limitations"),
        B(f"**The default model is trained on synthetic data.** Its {v['sh_acc']} accuracy is a property of the generator (2.5% label noise, near-perfect separability) and drops to {v['real_acc']} on real flows (ROC-AUC {v['real_auc']}).",
          f"**The official UNSW-NB15 test set is temporally shifted and harder than a random split.** The stacked model reaches {v['st_acc']} there, but a {v['fa']} false-alarm rate on normal flows at threshold 0.5.",
          f"**Stacking did not beat XGBoost.** XGBoost alone scores {v['xg_acc']}; the CNN adds false alarms and 246 s of CPU training time.".replace("246 s", f"{F.OFF['train_seconds']['cnn']:.0f} s"),
          f"**Fuzzers are missed {v['fz']} of the time**, and a single feature, `sttl`, dominates the importance ranking, a known artefact of the UNSW-NB15 testbed.",
          "**The CNN is trained with an unweighted binary cross-entropy loss** in the PyTorch branch that ran, although the README describes balanced weighting (which exists only in the TensorFlow branch).",
          "**Missing features default silently** to average values at the API, so a partial record can look benign."),
        H2("Security and system limitations"),
        B("**Mock cloud with an in-memory key pair.** There is no key storage, rotation or certificate, so objective 2 (key storage) is not met.",
          "**Demo shortcut in decryption.** The API caches session keys by ephemeral public key; any caller who knows an ephemeral public key can ask for decryption. The real ECDH path (cloud private key) is used when the cache misses and is tested, but the cache is not a production design.",
          "**No authentication, TLS or rate limiting**; CORS allows every origin.",
          "**The alert list is in memory** (at most 500 entries) and is lost on restart; there is no database.",
          "**No live traffic.** The system scores supplied records; it does not capture packets and does not tie a verdict to a particular transfer.",
          "**Resource limits are fixed in code**: 1 MB text, 5 MB file, 10 MB or 10,000-row CSV."),
        H2("Evaluation limitations"),
        B("One public data set from one laboratory; one machine; no significance tests; timings on a shared desktop CPU.",
          "The comparison with the base paper is indicative: its subset, hyper-parameters and test fraction are not published.",
          "The Docker image, the TensorFlow code path and browsers other than Chrome were not tested."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured and are therefore stated as gaps, not as results."),
        B("Network latency to a real cloud provider, TLS overhead and behaviour under concurrent users.",
          "Memory footprint and energy use of the detector and of SecureChannel.",
          "Robustness of the detector against adversarial or evasive traffic, and its behaviour on traffic from another network or another benchmark.",
          "Security of the base paper's EECC and the accuracy of its quantum-inspired network (neither implemented).",
          "Detection accuracy on live captured traffic; the system has only scored supplied records.",
          "A statistical significance test between the stacked model and XGBoost; the seed spread suggests the gap on the official partition is stable, but no test was run.",
          "RSA hybrid encryption inside the product; it exists only in the benchmark script.",
          "The Docker deployment and the original `run.bat` installation path on a clean machine."),
    ]


# ---------------------------------------------------------------- document 12: walkthroughs and decisions
def walkthrough_blocks():
    return [
        P("This section walks through the code that carries the design. The listings are copied from the repository at the state in which the results were measured."),
        H2("3.1 Key derivation"),
        CODE(src("cipherguard/crypto/secure_channel.py", 46, 56), 8.5),
        CODE(src("cipherguard/crypto/secure_channel.py", 69, 77), 8.5),
        P("`derive_session_key` performs the elliptic-curve Diffie-Hellman exchange on P-256 and passes the shared secret through HKDF with SHA-256, no salt and the context string `cipherguard-shield-v1`, giving a 32-byte AES-256 key. "
          "Both sides compute the same key because ECDH is symmetric: the sender uses its ephemeral private key and the cloud's public key, the cloud uses its private key and the sender's ephemeral public key. "
          "The raw shared secret is never used as a key, which is the reason for HKDF [%d]. The same function serves both directions, which keeps the encrypt and decrypt paths short and testable." % R["hkdf"]),
        H2("3.2 Authenticated encryption"),
        CODE(src("cipherguard/crypto/secure_channel.py", 79, 101), 8.5),
        P("`AESGCM.encrypt` returns the ciphertext with the 16-byte tag appended; the code splits them so that the interface can show the nonce, the ciphertext and the tag separately. "
          "The nonce is 12 random bytes from the operating system for every message, the size recommended for GCM [%d], and because the key itself is fresh for every message a nonce repeat is not a realistic risk (20,000 trials produced 20,000 distinct nonces). "
          "Decryption re-joins ciphertext and tag and `AESGCM.decrypt` raises `InvalidTag` on any modification, which is what produces the 400 response." % R["gcm"]),
        H2("3.3 One-shot encryption to the cloud"),
        CODE(src("cipherguard/crypto/secure_channel.py", 131, 147), 8.5),
        P("`encrypt_with_ephemeral` generates a new P-256 key pair, derives the key against the recipient's public key and returns the envelope fields, including the 65-byte uncompressed ephemeral public key. "
          "It also returns the ephemeral private key and the session key under underscore-prefixed names for in-process use; the API does not serialise them. The benchmark in Chapter 8 times exactly this function, which is why its figures include the key generation and the base64 conversion."),
        H2("3.4 Decryption at the cloud with a fall-back"),
        CODE(src("cipherguard/api/main.py", 314, 335), 8.5),
        P("The decrypt route first looks for a cached key, a demo shortcut kept so that the console can decrypt without holding the cloud's private key; if the cache has no entry it performs the real exchange with the cloud key pair. "
          "Malformed base64 and an unparsable ephemeral key give 400 with a message; a tag or key mismatch also gives 400 and releases no plaintext. A test clears the cache and checks that decryption still works."),
        H2("3.5 Scoring a record"),
        CODE(src("cipherguard/ids/inference.py", 139, 153), 8.5),
        P("`predict_proba` transforms the frame with the stored preprocessor (min-max scaling of 39 numeric features and one-hot encoding of protocol, service and state, ignoring unseen categories), gets the XGBoost probability and the CNN probability, "
          "stacks them as two columns and lets the logistic-regression meta-model produce the final probability. The label is attack when that probability is at least 0.5. `score_single` adds the severity bands of 0.70 (high) and 0.85 (critical). "
          "The CNN input is reshaped to (rows, 1, features), the 1D-sequence view of the flow vector used by the shipped architecture."),
        H2("3.6 Training the stack"),
        CODE(src("cipherguard/ids/train.py", 348, 352), 8.5),
        P("The meta-model is trained on the validation split's probabilities, not on the training split's, so that it sees predictions of models that did not fit those rows. "
          "That is the textbook way to stack %s, but it also explains a result of Chapter 8: when the test period differs from the validation period, the meta-model's weights, which favour the CNN's confident outputs, no longer fit." % c("stacking")),
    ]


def decision_blocks():
    v = _v()
    rows = [["Key agreement", "ECDH P-256 with an ephemeral key per message", "RSA-OAEP key wrapping; static key pair", f"Smaller keys (65 B against 256 B wrapped), cheaper unwrap at the cloud ({v['sc1k_dec']} ms against {v['r2048_dec']} ms), forward secrecy per message. RSA-2048 and 3072 were kept as measured baselines."],
            ["Key derivation", "HKDF-SHA256 with a context string", "Using the ECDH output directly as a key", "The raw shared secret is not uniformly random; HKDF is the standard remedy."],
            ["Payload cipher", "AES-256-GCM", "AES-CBC with HMAC; ChaCha20-Poly1305", "Authenticated encryption in one primitive; hardware-accelerated; maintained implementation. No custom cryptography."],
            ["Nonce", "12 random bytes per message", "Counter", "Fresh key per message makes random nonces safe and stateless."],
            ["Detector", "XGBoost + 1D CNN + logistic-regression stack", "Single model; deep fusion as in the base paper", "Cheap on a CPU, transparent, and a direct analogue of score-level fusion. Chapter 8 shows XGBoost alone is at least as good."],
            ["CNN framework", "PyTorch (TensorFlow code path kept)", "TensorFlow only", "TensorFlow failed to load on the development host; the PyTorch path has the same layer stack."],
            ["Training data default", "Synthetic generator in the same 42-feature schema", "Bundling the real dataset", "Runs out of the box with no download or licence step; the cost is the synthetic-data trap documented in Chapter 8. Real data are one script away."],
            ["Alert store", "In-memory list capped at 500", "Database", "Smallest thing that works for a demonstration; the cost is loss on restart."],
            ["Cloud", "Mock endpoint with a process key pair", "Real provider", "Lets the whole path be tested offline; key custody is therefore not demonstrated."],
            ["Interfaces", "REST API, React console, legacy HTML page", "Console only", "The legacy page needs no build step and remains a fall-back."],
            ["Model switching", "`CIPHERGUARD_MODELS_DIR` / `CIPHERGUARD_REPORTS_DIR`", "Overwriting models/", "Lets a real-trained bundle be served without touching the shipped one."]]
    return [
        P("Each design decision below was taken for a reason and has a cost; the table states both."),
        TAB("Implementation decisions and their reasons", ["Decision", "Chosen", "Alternative", "Reason and consequence"], rows, widths=[1.0, 1.5, 1.4, 2.6], align=["l", "l", "l", "l"], size=8.5),
        P("Two decisions were forced by the environment rather than chosen. On the measurement host `import torch` fails if numpy or pandas are imported first, so the experiment scripts, the test suite and `scripts/serve.py` import torch first; "
          "the shipped `run.bat` creates its own virtual environment and was not re-run here. The experiments also run on a shared CPU, which is why absolute timings are reported as indicative."),
    ]


# ---------------------------------------------------------------- chapter 9 and 10
def conclusion_blocks():
    v = _v()
    b = [
        H2("9.1 Summary of the work"),
        P("This project built CipherGuard Shield, a platform that puts two protections around one cloud data path: SecureChannel, which encrypts a payload with a fresh ECDH P-256 key, HKDF-SHA256 and AES-256-GCM and verifies it at the cloud, "
          "and the ThreatSense Engine, which classifies network flows with XGBoost, a 1D CNN and logistic-regression stacking and logs attacks with a severity. A REST API, a React console and the original dashboard expose both. "
          f"The work was then measured: on real UNSW-NB15 flows, in cryptographic benchmarks and in a combined pipeline test, and verified with {F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} smoke checks."),
        H2("9.2 Objectives achieved"),
        TAB("The six objectives of the batch against the outcome", ["#", "Objective", "Outcome"],
            [["1", "Hybrid AES + RSA scheme", "Partly met by substitution: ECDH + HKDF + AES-256-GCM; RSA hybrids benchmarked only"],
             ["2", "Key generation, distribution, storage", "Generation and distribution met; storage not met (in-memory mock cloud key)"],
             ["3", "Encrypt before upload, decrypt after download", "Met against a mock cloud, text and files, with tamper rejection"],
             ["4", "Classifier on a benchmark dataset", f"Met in experiments on real UNSW-NB15 ({v['st_acc']} stacked, {v['xg_acc']} XGBoost); default model synthetic"],
             ["5", "Flag and log suspicious sessions", "Partly met: flows scored and logged in memory; not tied to a transfer; nothing blocked"],
             ["6", "Evaluate times, overhead and accuracy", f"Met: sub-millisecond crypto up to 100 KB, {v['xfer']} ms combined transfer, detection metrics with seeds"]],
            widths=[0.35, 2.1, 4.1], align=["c", "l", "l"], size=9.5),
        H2("9.3 Key findings"),
        N(f"**Authenticated encryption is cheap and behaved exactly as specified.** 1,000 of 1,000 trials of each of six tamper cases were correct; a protected 100 KB transfer costs {v['xfer']} ms, of which {v['ids_share']}% is detection.",
          f"**The synthetic default says nothing about real traffic.** {v['sh_acc']} on synthetic data against {v['real_acc']} (ROC-AUC {v['real_auc']}) on the {F.OFF['test_rows']:,} real test flows.",
          f"**On real data the detector ranks well but alarms too often.** Stacked accuracy {v['st_acc']}, ROC-AUC {v['st_auc']}, false-positive rate {v['st_fpr']}; a threshold of 0.9 gives accuracy {v['t9_acc']} and a false-positive rate of {v['t9_fpr']}.",
          f"**Stacking gave no gain over XGBoost.** XGBoost alone: {v['xg_acc']} on the official partition and {v['pap_xg']} against {v['pap_st']} under the base paper's protocol.",
          f"**Against the base paper** the stacked model is about one point lower under a comparable protocol ({v['pap_st']} against {F.BASE_PAPER_RESULTS['proposed_mean_accuracy']:.4f}); the comparison is indicative only because the datasets differ in their subsets."),
        H2("9.4 Practical applications"),
        B("A teaching and prototyping platform for encrypting data before upload and watching network flows in one place.",
          "A reference implementation of ephemeral-key hybrid encryption with tamper tests and a measured RSA baseline.",
          "A starting point for a flow-based alerting service once live flow export, authentication and persistent storage are added (Chapter 10).",
          "A template for reporting an intrusion-detection result honestly: real data, official split, seeds, thresholds, categories and a synthetic-versus-real audit."),
        H2("9.5 Known limitations"),
        P(f"The default model is synthetic; the official test set is harder than a random split and produces {v['fa']} false alarms on normal traffic at threshold 0.5; Fuzzers are missed {v['fz']} of the time; the cloud is a mock with in-memory keys; "
          "there is no authentication, TLS or persistent store; live traffic and adversarial inputs were not tested; and the base paper's EECC and quantum-inspired network were not reproduced. Chapter 8 and the Scope and Limitations document give the full list."),
        H2("9.6 Lessons learned"),
        B("Report the data a number was measured on in the same sentence as the number; a synthetic 97% and a real 89% are different claims.",
          "Run the simple baseline first. XGBoost alone matched or beat a three-model stack, a result that would have stayed hidden without a baseline table.",
          "Prefer standard, maintained primitives and measure them against the alternative that was asked for (RSA) rather than adopting a non-standard scheme.",
          f"Make the evaluation protocol part of the result: the same stacked design scored {v['pap_st']} on a random balanced subset and {v['st_acc']} on the temporally split official partition.",
          "Keep experiments scripted and their output stored as JSON, so every number in the documents can be traced and regenerated."),
    ]
    if F.REPORT:   # the objectives table already stands in Section 8.12 of the report; keep three lessons
        out = []
        i = 0
        while i < len(b):
            x = b[i]
            if x[0] == "tab" and x[1].startswith("The six objectives"):
                out.append(P("Section 8.12 sets the six objectives of the batch against the outcomes. Objectives 3 (encrypt before upload, decrypt after download) and 6 (evaluate times, overhead and accuracy) are met; "
                             "objective 4 (classifier on a benchmark dataset) is met in the experiments on real UNSW-NB15, while the shipped default model is synthetic; objectives 1 (hybrid scheme, met by substitution of ECDH for RSA) "
                             "and 5 (flag and log suspicious sessions) are met in part; objective 2 is met for key generation and distribution but not for key storage."))
            elif x[0] == "b" and x[1][0].startswith("Report the data a number was measured on"):
                out.append(("b", x[1][:3]))
            else:
                out.append(x)
            i += 1
        b = out
    return b


def future_blocks():
    return [
        H2("10.1 Improvements to the existing system"),
        B("**Make the real-trained bundle the default** and ship the data-fetch script, so the console shows real-data metrics from the first start; keep the synthetic generator only as a test fixture.",
          "**Choose the decision threshold on a validation set** and expose it in the console; a threshold of 0.9 already cuts the false-positive rate on the official partition from " + F.f3(F.thr_row(0.5)["fpr"]) + " to " + F.f3(F.thr_row(0.9)["fpr"]) + ".",
          "**Train the CNN with class weights** (the TensorFlow branch already does) and compare with XGBoost alone; drop the CNN if it still adds nothing.",
          "**Fit the stacking meta-model on data from a period later than the training data**, or replace it by simple averaging with a calibrated XGBoost.",
          "**Replace the session-key cache** by a strict ECDH-only decrypt path and remove the demo shortcut."),
        H2("10.2 Additional features"),
        B("**Flow export instead of CSV rows:** read flows from a tap or a flow exporter (for example Zeek or NetFlow) and score them continuously.",
          "**Gate transfers on verdicts:** hold, quarantine or require approval for a transfer whose session is flagged, and tie alerts to sessions.",
          "**Persistent alert store** (a database), search, acknowledgement and export.",
          "**Authentication, authorisation and TLS** for the API and the console, with audit logging.",
          "**Key management:** a KMS or HSM for the cloud key, key rotation and certificates for the cloud's public key.",
          "**Multi-class detection** (attack category, not only attack or normal) and explanations of verdicts."),
        H2("10.3 Scalability and deployment"),
        B(f"Containerise and test the existing Docker files, run the API behind a reverse proxy and several workers; scoring 1,000 rows takes about {F.IP['ids_batch_1000_rows']['median_ms']:.0f} ms in process, so one core can serve thousands of flows a second, while the CNN's {F.OFF['train_seconds']['cnn'] / 60:.0f}-minute training and XGBoost's {F.OFF['train_seconds']['xgb']:.0f} seconds make regular retraining jobs practical.",
          "Move the cloud endpoint into a separate service with its own key custody and a real object store, then measure real network latency and concurrency.",
          "Add drift monitoring: track the distribution of the 42 features and the alert rate, and retrain when they move."),
        H2("10.4 Further research"),
        B("Evaluate on more recent and more varied data sets and on traffic captured in a real network; test whether the `sttl` dependence disappears.",
          "Test adversarial robustness: evasive flows, poisoned training data, and the effect of attackers who know the model.",
          "Reproduce the base paper's EECC and quantum-inspired network, and compare them with the standard primitives and models used here on the same data.",
          "Study federated or privacy-preserving training so that several clouds can share a detector without sharing flows.",
          "Provide a significance analysis and confidence intervals for the comparison between stacked and single models."),
        H2("10.5 Suggested order of work"),
        TAB("Future work ranked by value and effort", ["Priority", "Item", "Effort", "Why first"],
            [["1", "Real-trained model as default, threshold chosen on validation data", "Small", "Removes the synthetic-data trap and halves the false-alarm rate"],
             ["2", "Authentication, TLS, ECDH-only decrypt path", "Small to medium", "Closes the demo shortcuts that block any real use"],
             ["3", "Persistent alert store and session-linked verdicts", "Medium", "Makes alerts durable and attributable to a transfer"],
             ["4", "Flow export and continuous scoring", "Medium to large", "Moves from supplied records to live traffic"],
             ["5", "KMS or HSM key custody, rotation, certificates", "Medium", "Meets the key-storage objective that is not met today"],
             ["6", "Adversarial testing, drift monitoring, other data sets", "Large", "Shows whether the results survive outside UNSW-NB15"]],
            widths=[0.7, 2.7, 1.1, 2.1], align=["c", "l", "l", "l"], size=9.5),
    ]


def _future_trim(bl):
    if not F.REPORT:
        return bl
    out, skip = [], False
    for x in bl:
        if x[0] == "h2" and x[1].startswith("10.5"):
            skip = True
            continue
        if not skip:
            out.append(x)
    return out


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + _future_trim(future_blocks())
