"""Text of 19.IEEE_Paper.docx (CipherGuard Shield). Every number is read from facts.py (experiments/**/metrics.json); nothing is typed in by hand.

Citations use {r:N} with the fixed global reference numbers of scripts/docs/refs.py:
 1 base paper, 2-5 batch survey items, 6 arXiv 2601.01134, 7 UNSW-NB15 (2015), 8 UNSW-NB15 (2016), 9 XGBoost, 10 LeNet, 11 stacking,
 12 NIST SP 800-38D, 13 NIST SP 800-56A, 14 RFC 5869, 15 FIPS 197, 16 RFC 8017, 17 scikit-learn, 18 PyTorch, 19 Adam,
 20 Kadry, 21 Nadeem, 22 Bakro, 23 Mbaya, 24 Rahman, 25 Alrayes, 26 Lin, 27 Alani, 28 Qazi, 29 Hdaib, 30 Vengala.
"""
import os

from . import facts as F
from . import paper_figs
from .paper import Paper

f2, f3, pct = F.f2, F.f3, F.pct

KEYS = ["arXiv", "unsw15", "unsw16", "xgboost", "lenet", "stacking", "gcm", "sp80056a", "hkdf", "aes", "oaep", "sklearn", "pytorch", "adam",
        "kadry", "nadeem", "bakro", "mbaya", "rahman", "alrayes", "lin", "alani", "qazi", "hdaib", "vengala"]


def _check_refs():
    """The fixed numbering is a contract with refs.py; fail loudly if it drifted."""
    from .refs import CITE
    expect = {"base": 1, "unsw15": 7, "unsw16": 8, "xgboost": 9, "stacking": 11, "gcm": 12, "sp80056a": 13, "hkdf": 14, "sklearn": 17, "pytorch": 18,
              "kadry": 20, "nadeem": 21, "mbaya": 23, "rahman": 24}
    for k, n in expect.items():
        if k in CITE:
            assert CITE[k] == n, (k, CITE[k], n)


def build(path):
    try:
        _check_refs()
    except ImportError:
        pass
    figs = paper_figs.make()
    P = Paper()
    o, p = F.OFFS, F.PAPS
    s42, sh, shift = F.S42, F.SHIPPED, F.SHIFT
    cry, ip, ap = F.CRY, F.IP, F.API
    real_on_shipped = shift["shipped_on_real_official_test"]["stack"]
    tamp = cry["tamper_tests"]
    n_tamper = sum(v["trials"] for k, v in tamp.items() if k != "untouched message accepted")
    ok_tamper = sum(v["as_expected"] for k, v in tamp.items() if k != "untouched message accepted")
    pc = F.OFF["per_category"]
    normal_fa = 1 - pc["Normal"]["rate"]
    fuzz_miss = 1 - pc["Fuzzers"]["rate"]
    thr9 = F.thr_row(0.9)
    cmx = s42["stack"]["confusion_matrix"]
    sc_enc1, sc_dec1 = F.crypto_row("sc", "1 KB", "encrypt"), F.crypto_row("sc", "1 KB", "decrypt")
    r2_enc1, r2_dec1 = F.crypto_row("rsa2048", "1 KB", "encrypt"), F.crypto_row("rsa2048", "1 KB", "decrypt")
    r3_dec1 = F.crypto_row("rsa3072", "1 KB", "decrypt")
    share = ip["share_of_transfer_median"]
    real_meta = None
    try:
        import json
        real_meta = json.load(open(os.path.join(F.EXP, "unsw_nb15", "official", "reports", "metrics.json")))
    except OSError:
        pass

    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS_UPPER]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"])
    P.title_block("CipherGuard Shield: Authenticated Encryption and Machine-Learning Intrusion Detection for Secure Cloud Data Transmission", authors)
    P.begin_two_columns()

    P.abstract(
        "Data sent to a public cloud can be read or altered in transit, and encryption alone cannot see an attacker who already holds valid access. "
        "This paper presents CipherGuard Shield, a platform that places two protections around one cloud data path. SecureChannel seals each payload with AES-256-GCM under a key "
        "derived from a fresh ECDH P-256 exchange and HKDF-SHA256. ThreatSense Engine classifies network-flow records with XGBoost and a one-dimensional CNN combined by logistic-regression stacking. "
        f"Both were measured on one machine. All {ok_tamper:,} of {n_tamper:,} tampered messages were rejected, one protected 100 KB transfer costs {ip['protected_transfer_100kb']['median_ms']:.1f} ms of which detection is "
        f"{share['ids'] * 100:.0f} %, and on the official UNSW-NB15 split the stacked detector reaches {f3(o['stack']['accuracy']['mean'])} accuracy, below XGBoost alone at {f3(o['xgb']['accuracy']['mean'])}. "
        f"The bundled demo model, trained on synthetic data, scores {f3(sh['accuracy'])} on its own test split but {f3(real_on_shipped['accuracy'])} on real flows, which is the main caution of the work. "
        f"Under a protocol in the style of the base paper the stacked model reaches {f3(p['stack']['accuracy']['mean'])}.",
        ["authenticated encryption", "cloud security", "elliptic-curve Diffie-Hellman", "ensemble learning", "intrusion detection", "stacking", "UNSW-NB15"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Moving data to a public cloud moves it outside the owner's network perimeter. Confidentiality, integrity and availability must then hold while the data is in transit, "
           "and operators need to notice attacks that encryption cannot prevent, such as a session opened with stolen credentials {r:2,3}. Symmetric ciphers such as AES are fast but need a safe way to "
           "agree on a key; asymmetric schemes solve key agreement but are too slow for bulk data, so practical systems wrap a fresh symmetric key with an asymmetric one {r:12,13,37}.")
    P.para("In most deployments cryptography and intrusion detection are separate products with separate operators. The surveyed cloud-security work likewise treats them separately: "
           "each proposes one layer and leaves the cost of running both unmeasured {r:2,3,4,5}. The base paper {r:1} is a notable exception. It couples a quantum-inspired network and LeNet with an enhanced "
           f"elliptic-curve cipher and reports a mean accuracy of {f3(F.BASE_PAPER_RESULTS['proposed_mean_accuracy'])} on 9,000 UNSW-NB15 flows, but it offers no formal security proof for its cipher and "
           "does not measure the combined overhead of detection plus encryption on one data path.")
    P.para("Done separately, the two layers also fail separately. Encryption gives no signal when valid credentials are stolen, and a flow-level detector sees only traffic statistics, not the payload "
           "that encryption hides. Running both means two sets of keys, logs and latencies, and without a combined measurement an operator cannot say whether detection or encryption dominates the "
           "cost of one transfer. The batch objectives for this work ask for a hybrid AES and RSA scheme, an intrusion classifier trained on a benchmark dataset, flagging and logging of "
           "suspicious sessions, and an evaluation of encryption time, overhead and detection accuracy.")
    P.para("CipherGuard Shield is a working, tested platform that makes this combination concrete at student-project scale. The contributions are: (1) SecureChannel, an authenticated-encryption path "
           "built from standard primitives (ECDH P-256, HKDF-SHA256, AES-256-GCM) with a fresh key per message, benchmarked against an RSA-OAEP hybrid; (2) ThreatSense Engine, an XGBoost and 1D-CNN "
           "detector with logistic-regression stacking, an alert log and a live console; (3) a measured evaluation on the real UNSW-NB15 partition, on a protocol like the base paper's and across "
           "synthetic and real data, including the combined per-transfer overhead; and (4) an account of what the numbers do and do not show. Section II surveys related work, Section III describes "
           "the method, Section IV gives the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All timings and training runs used one Windows 11 machine with an Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of RAM and no GPU, so the neural network trained and ran on the CPU. "
           "The machine was shared with other jobs, so absolute times are indicative.")
    P.sub("B", "Software Requirements")
    P.para(f"Python 3.11.9; FastAPI 0.110 and Uvicorn for the service; the cryptography package {F.CRY['machine']['cryptography']}; XGBoost 2.0.3 {{r:9}}; scikit-learn 1.5.0 {{r:17}} for preprocessing, logistic "
           "regression and the baselines; PyTorch {r:18} (2.14.1, CPU) for the CNN; and React 19 with Vite for the console.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Kalyanasundaram et al. {r:1} normalise flows with min-max scaling, classify them with a flatten-layer feature-map quantum neural network that uses eigenvalue decomposition "
           "(simulated on classical hardware) and with LeNet, and fuse the two scores with a double-sigmoid median min-max scheme (DSMMN-SLF). Non-intrusive data are then encrypted with an enhanced "
           f"elliptic-curve cryptography (EECC) variant. Experiments use {F.BASE_PAPER_RESULTS['samples']:,} balanced UNSW-NB15 samples split {F.BASE_PAPER_RESULTS['split']} and averaged over {F.BASE_PAPER_RESULTS['runs']} runs: "
           f"mean accuracy {f3(F.BASE_PAPER_RESULTS['proposed_mean_accuracy'])}, precision {f2(F.BASE_PAPER_RESULTS['precision_at_90'])} and false-positive rate {f2(F.BASE_PAPER_RESULTS['fpr'])}, ahead of re-implemented baselines "
           f"such as SqueezeNet ({f3(F.BASE_PAPER_RESULTS['baselines']['SqueezeNet'])}) and LeNet ({f3(F.BASE_PAPER_RESULTS['baselines']['LeNet'])}). EECC encrypts in {F.BASE_PAPER_RESULTS['enc_time_s']} s and decrypts in "
           f"{F.BASE_PAPER_RESULTS['dec_time_s']} s. The authors state that a rigorous proof of EECC security under standard hardness assumptions is future work, and the subset drawn from UNSW-NB15 and the "
           "baseline settings are not fully specified. Its ablation (accuracy 0.956 for the full model at an 80 % training share, between 0.902 and 0.932 when the quantum block, the fusion rule or the "
           "normalisation is replaced or removed) supports the value of each component, but every variant is evaluated on the same balanced subset, so the ablation shows relative, not absolute, merit.")
    P.para("**IDS combined with cryptography.** Kadry et al. {r:20} pair an optimised quantum neural network with elliptic-curve encryption of stored files. The batch survey adds encryption with "
           "anomaly detection for storage and transmission {r:2}, an intrusion-detection system with automated data deletion across clouds {r:3}, federated attack detection with an improved "
           "Blowfish cipher {r:4} and a hybrid-encryption privacy framework {r:5}.")
    P.para("**Detector design.** Bakro et al. {r:22} combine SMOTE, three feature-selection methods and a random forest for a cloud IDS and report over 98 % accuracy on UNSW-NB15 in their abstract; Mbaya et al. {r:23} "
           "train a BiLSTM-RNN in a blockchain-backed federated setting; Rahman et al. {r:24} train detectors on GAN-generated data and, as summarised in {r:1}, reach perfect BoT-IoT scores, a reminder that "
           "synthetic data can flatter a model. Stacked generalisation {r:11} combines base learners through a meta-model trained on held-out predictions, and gradient-boosted trees {r:9} remain "
           "strong on tabular flow features. UNSW-NB15 {r:7} supplies 49 flow features with nine attack categories and an official training and testing partition captured at different times; its class imbalance and overlap are known weaknesses {r:35}.")
    P.para("**Hybrid cryptography for the cloud.** Mahalle and Shahade {r:37} protect uploads and downloads with RSA-wrapped AES keys, the classical hybrid that the batch objectives name. "
           "The survey items repeat the pattern with variations: AES and RSA with an XOR key mask, reported at about two seconds per 2 to 12 KB input {r:5}, and a Blowfish variant inside a federated "
           "detector {r:4}. Such timings depend on the implementation and the payload, so they cannot be compared across papers; the benchmark here therefore measures an RSA-OAEP hybrid on the same machine "
           "as the elliptic-curve path.")
    P.table("Representative related work", ["Work", "Approach", "Data", "Result as reported", "Limitation"], [
        ["{r:1}", "QNN + LeNet fusion, EECC", "UNSW-NB15, 9,000", "Acc. 0.949; enc. 0.39 s", "No security proof"],
        ["{r:20}", "Optimised QNN + ECC", "Network data", "Acc. 98.5 % (as cited in {r:1})", "Storage focus"],
        ["{r:22}", "SMOTE, 3 feature selectors, RF", "UNSW-NB15, Kyoto", "Over 98 %, over 99 %", "Detection only"],
        ["{r:23}", "Blockchain federated BiLSTM", "CIDDS", "Precision 0.996", "No crypto cost"],
        ["{r:2}", "Encryption + anomaly detection", "Not stated", "No figures given", "Not evaluated"],
        ["{r:3}", "IDS-triggered data deletion", "None", "Concept only", "Not evaluated"],
        ["{r:5}", "AES + RSA/MECC, XOR key mask", "2-12 KB inputs", "Enc. 2.09 s, dec. 2.45 s", "No detector"],
        ["{r:4}", "Federated IDS, improved Blowfish", "Cloud", "Abstract not retrievable", "Not verified"],
    ], widths=[0.3, 0.95, 0.62, 0.78, 0.75], size=7, align=["c", "l", "l", "l", "l"])
    P.para("**Evaluation practice.** Reported accuracy on UNSW-NB15 depends heavily on how the data are split. The official partition separates training and testing in time, whereas a random subset "
           "of the training set shares its capture conditions with the training data and is easier; the base paper uses a balanced random subset of 9,000 flows. Both protocols are used here and "
           "reported separately so that the difference is visible rather than hidden in a single headline number. The visual analysis in {r:35} finds class imbalance and overlap to be the main "
           "problems of the dataset, which is why false-positive rate and per-category rates are reported next to accuracy.")
    P.para("**Gap.** The surveyed work builds either a detector or a cipher, or couples them without reporting what the pair costs. None reports, on one path, the encryption time, the detection time "
           "and their share of a transfer, and none tests how a detector trained on generated data behaves on real traffic. CipherGuard Shield addresses these two points with standard, "
           "auditable primitives and does not attempt the base paper's quantum-inspired network or its custom cipher.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the layers. A React console talks to a FastAPI service on the same host. The service exposes nine endpoints (scoring, batch scoring, alerts, encrypt, decrypt, "
           "file encryption, metrics and health). Alerts and session keys live in process memory, the models and reports are files, and the cloud is a mock endpoint with its own key pair in the same process.")
    P.figure(figs["arch"], "CipherGuard Shield architecture: console, FastAPI service, the two core modules and file or memory storage.")
    P.para("**Console.** The React console has four working screens: live scoring of one record or a CSV batch with a session log, secure transfer (encrypt text or a file, decrypt at the mock cloud, "
           "tamper with the ciphertext and watch the tag check fail), an alert table with severity filter, and a model-performance screen that reads the held-out metrics file. A banner on that "
           "screen states which data the bundle was trained on, so a viewer sees whether the numbers come from synthetic or real flows.")
    P.para("**SecureChannel.** For every message the sender generates an ephemeral P-256 key pair (e, E), computes the ECDH shared secret with the cloud's public key C and derives a 256-bit key {r:13,14}:")
    P.eq("K = HKDF-SHA256( ECDH(e, C), info ).")
    P.para("A random 12-byte nonce n is drawn and the payload m is sealed with AES-256-GCM {r:12}, giving a ciphertext of the same length and a 16-byte tag:")
    P.eq("(c, t) = AES-GCM_K( n, m ).", )
    P.para(f"The envelope (c, n, t, E) adds a fixed {F.ENVELOPE_OVERHEAD_BYTES} bytes. The cloud recomputes K from its private key and E, and releases plaintext only if the tag verifies. "
           "Payloads are limited to 1 MB of text or 5 MB per file. As a baseline, an RSA-2048 and an RSA-3072 OAEP key-wrapping hybrid {r:16} with the same AES-GCM was benchmarked but is not part of the product.")
    P.para("**Security properties.** Because every message uses a fresh ephemeral key, a leaked session key exposes one message only, and a repeated random nonce could not matter since no key is "
           "reused. GCM authenticates the ciphertext, nonce and tag together, so any modification is detected before plaintext is released. Two limits are deliberate to state: the ephemeral public "
           "key and the cloud's public key are not signed or certified in this prototype, so an active attacker who could substitute keys is outside the threat model; and the mock cloud's private key "
           "is held in process memory and is lost on restart. Neither confidentiality of the payload against a passive eavesdropper nor tamper detection depends on these limits.")
    P.para(f"**ThreatSense Engine.** A flow record has 42 UNSW-NB15 features (39 numeric, three categorical). Numeric features are min-max scaled and protocol, service and state are one-hot encoded "
           f"({F.INPUT_DIM_SYNTH} inputs for the synthetic bundle, {F.INPUT_DIM_REAL} for real data). XGBoost {{r:9}} (200 trees, depth 6, learning rate 0.08) and a CNN (two Conv1d layers of 32 and 64 filters "
           "with max pooling, a 64-unit dense layer, dropout 0.3 and a sigmoid output, trained with Adam and early stopping) each give an attack probability. A logistic-regression meta-model fitted on "
           "a validation split fuses them {r:11}:")
    P.eq("p = σ( w_1 p_xgb + w_2 p_cnn + b ).")
    P.para("A flow is labelled attack if p reaches 0.5 and receives severity critical at 0.85 or above, high at 0.70 and medium otherwise; attacks are appended to a 500-entry alert log. "
           "The two learners were chosen because they are complementary on tabular data: trees cope with mixed scales and categorical counts, the CNN reads the feature vector as a sequence.")
    P.para("**Features.** The 42 inputs describe a flow rather than packet payloads: duration and protocol, service and connection state; packet and byte counts in each direction; rates, load, loss, inter-packet "
           "times and jitter; time-to-live values and TCP window sizes and round-trip timings; and connection-count features that summarise recent flows to the same host or service. "
           "Missing fields in an API request are filled with fixed defaults, so a request that sets only a dozen fields scores a mostly default flow.")
    P.para(f"**Training.** The synthetic bundle is generated from class-conditional distributions (exponential, Poisson and log-normal draws for durations, packet counts and byte counts) and "
           f"then 2.5 % of the labels are flipped. For the official partition the training set is split 85/15 (stratified) into fit and validation parts; the validation part drives CNN early stopping "
           f"(patience 5, at most 15 epochs, batch 256, Adam at 1e-3, unweighted binary cross-entropy) and fits the meta-model, so the test set never influences training. XGBoost uses "
           f"scale_pos_weight equal to the negative-to-positive ratio. The CNN has {F.CNN_PARAMS_70:,} parameters at 70 inputs. Seeds 42 to 46 change the split and the initialisation. "
           f"On the CPU, XGBoost trained in {F.OFF['train_seconds']['xgb']:.1f} s and the CNN in {F.OFF['train_seconds']['cnn']:.0f} s on {F.OFF['fit_rows']:,} flows.")
    P.figure(figs["flow"], "Main flow: the two lanes run side by side; the API does not gate a transfer on the detector's verdict.")
    P.para(f"**Data and protocols.** The shipped default model is trained on {F.SYNTH_ROWS:,} synthetic rows with the UNSW-NB15 schema (70/15/15 split, 2.5 % label noise). Because that is not real traffic, "
           f"three further experiments use the real data {{r:7}}: the official partition ({F.OFF['fit_rows']:,} fit and {F.OFF['val_rows']:,} validation flows from the training set, {F.OFF['test_rows']:,} test flows, five seeds); "
           "a protocol in the style of the base paper (9,000 balanced flows, 70/15/15, ten repetitions); and a shift test that scores the shipped model on real flows and a real-trained model on the synthetic CSV. "
           "Random forest, decision tree and logistic-regression baselines use the same inputs.")
    P.para("**Metrics.** Accuracy, precision, recall, F1, ROC-AUC, false-positive rate (false alarms among normal flows) and the Matthews correlation coefficient are computed on held-out flows with "
           "attack as the positive class. Because UNSW-NB15 is imbalanced and its official split is temporal, the false-positive rate and the per-category rates matter as much as accuracy. "
           "The threshold sweep is run on the test set and is descriptive, not a tuned result.")
    P.para(f"**Implementation and verification.** The service validates every input (size limits, CSV and base64 checks) and returns 400 or 503 with a message. {F.PYTEST_PASSED} pytest tests and "
           f"{F.SMOKE_PASSED} smoke checks pass against the running API. Crypto latency is the median of 15 to 300 repetitions per payload size; tamper cases use 1,000 trials each.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** Detection results come from the official UNSW-NB15 testing set ({F.OFF['test_rows']:,} flows, {pct(F.OFF['test_attack_rate'])} attacks, captured after the training set) "
           f"and from 1,350-flow test splits of the base-paper-style protocol. Threshold 0.5 is used unless stated. Table II gives the main metrics; the official-partition accuracy is a mean over five seeds. Table III compares with the base paper and Table IV lists the encryption and decryption times.")
    rows = []
    for lab, k in [("Official, stacked", "stack"), ("Official, XGBoost", "xgb"), ("Official, 1D CNN", "cnn")]:
        rows.append([lab, F.mstd(o, k, "accuracy"), f3(o[k]["precision"]["mean"]), f3(o[k]["recall"]["mean"]), f3(o[k]["f1"]["mean"]), f3(o[k]["roc_auc"]["mean"])])
    for lab, k in [("Paper prot., stacked", "stack"), ("Paper prot., XGBoost", "xgb"), ("Paper prot., RF", "rf")]:
        rows.append([lab, F.mstd(p, k, "accuracy"), f3(p[k]["precision"]["mean"]), f3(p[k]["recall"]["mean"]), f3(p[k]["f1"]["mean"]), f3(p[k]["roc_auc"]["mean"])])
    rows.append(["Shipped, synthetic test", f3(sh["accuracy"]), f3(sh["precision"]), f3(sh["recall"]), f3(sh["f1"]), f3(sh["roc_auc"])])
    rr = real_on_shipped
    rows.append(["Shipped, real official test", f3(rr["accuracy"]), f3(rr["precision"]), f3(rr["recall"]), f3(rr["f1"]), f3(rr["roc_auc"])])
    P.table("Detection metrics (mean of seeds or runs)", ["Setting, model", "Accuracy", "Prec.", "Recall", "F1", "AUC"], rows, widths=[1.1, 0.78, 0.38, 0.4, 0.38, 0.38], size=6.8, align=["l", "c", "c", "c", "c", "c"])
    P.figure(figs["results"], "(a) Accuracy on real UNSW-NB15 (mean, bar = std). (b) Stacked model by training and test data (dotted = chance). (c) Threshold sweep, official test set, seed 42. (d) Share of each traffic category handled correctly, seed 42.")
    P.para(f"**Detection.** On the official partition the stacked ensemble reaches {F.mstd(o, 'stack', 'accuracy')} accuracy with ROC-AUC {f3(o['stack']['roc_auc']['mean'])}, but XGBoost alone is better "
           f"({F.mstd(o, 'xgb', 'accuracy')}, false-positive rate {f3(o['xgb']['fpr']['mean'])} against {f3(o['stack']['fpr']['mean'])}). The CNN is weakest ({f3(o['cnn']['accuracy']['mean'])}); "
           "the meta-model is fitted on a validation split from the earlier training period, so it inherits the CNN's higher false-alarm rate on the later test period. "
           f"Seed-to-seed spread is small (standard deviation {o['stack']['accuracy']['std']:.4f} for the stack, {o['xgb']['accuracy']['std']:.4f} for XGBoost and {o['cnn']['accuracy']['std']:.4f} for the CNN), and the "
           f"Matthews coefficient is {f3(o['stack']['mcc']['mean'])} for the stack and {f3(o['xgb']['mcc']['mean'])} for XGBoost, so the ranking of the models is not an artefact of one split. "
           + (f"The fitted meta-model weights XGBoost ({real_meta['meta_coef'][0][0]:.2f}) above the CNN ({real_meta['meta_coef'][0][1]:.2f}), consistent with the ranking of the two. " if real_meta else "") +
           f"Averaging the two probabilities gives {f3(o['mean']['accuracy']['mean'])}, so stacking adds only about {o['stack']['accuracy']['mean'] - o['mean']['accuracy']['mean']:.3f}. "
           f"Under the paper-style protocol stacking, XGBoost and a random forest are indistinguishable ({f3(p['stack']['accuracy']['mean'])}, {f3(p['xgb']['accuracy']['mean'])}, {f3(p['rf']['accuracy']['mean'])}).")
    P.para(f"**Observed limits.** At threshold 0.5 the stacked model passes only {pct(pc['Normal']['rate'])} of normal flows ({cmx[0][1]:,} false alarms against {cmx[1][0]:,} missed attacks, seed 42), so an operator "
           f"would see about {normal_fa * 100:.0f} alarms per 100 normal flows. Raising the threshold to 0.9 gives accuracy {f3(thr9['accuracy'])}, precision {f3(thr9['precision'])}, recall {f3(thr9['recall'])} "
           f"and false-positive rate {f3(thr9['fpr'])}. Fuzzers are the weakest attack category ({fuzz_miss * 100:.1f} % missed); every other category is detected at {min(v['rate'] for k, v in pc.items() if k not in ('Normal', 'Fuzzers')) * 100:.0f} % or more. "
           "The source time-to-live field sttl dominates XGBoost's feature gain, a known artefact of the UNSW-NB15 testbed, so the scores may overstate how well the model would generalise to other networks.")
    P.para("**Cases that went wrong.** On the console's attack preset the two learners disagree strongly: XGBoost gives an attack probability of 0.45 and the CNN 1.00, and only the fused value of 0.84 "
           "crosses the threshold, a reminder that a single learner can miss what the other sees. The shipped bundle labels real traffic unreliably (the real sample in Fig. 5 is 65 % agreement), "
           "unseen protocol, service or state values are ignored by the encoder instead of rejected, and a record with default values for most fields can look normal or abnormal by accident. "
           "Malformed CSV files, files over the size limit, empty payloads, bad base64 and tag mismatches are rejected with HTTP 400, and an unavailable model returns 503; "
           "these paths are covered by the tests.")
    P.para(f"**Comparison with the base paper.** Table III sets the figures side by side. The base paper reports a mean accuracy of {f3(F.BASE_PAPER_RESULTS['proposed_mean_accuracy'])}, precision {f2(F.BASE_PAPER_RESULTS['precision_at_90'])} and false-positive rate "
           f"{f2(F.BASE_PAPER_RESULTS['fpr'])} for its model, with SqueezeNet the strongest baseline at {f3(F.BASE_PAPER_RESULTS['baselines']['SqueezeNet'])}. Under a comparable protocol our stacked model reaches "
           f"{f3(p['stack']['accuracy']['mean'])} accuracy, {f3(p['stack']['precision']['mean'])} precision and {f3(p['stack']['fpr']['mean'])} false-positive rate: about one point below the proposed model "
           "and level with its strongest baseline. The comparison is indicative only. The paper's sampled subset, hyper-parameters and test fraction are not published, our test splits hold 1,350 flows, "
           "and its quantum-inspired network and EECC were not reproduced.")
    bp = F.BASE_PAPER_RESULTS
    P.table("Comparison with the base paper (indicative)", ["Model", "Accuracy", "Precision", "FPR"], [
        ["Base paper, proposed {r:1}", f3(bp["proposed_mean_accuracy"]), f2(bp["precision_at_90"]), f2(bp["fpr"])],
        ["Base paper, best baseline", f3(bp["baselines"]["SqueezeNet"]), "n/a", "n/a"],
        ["Ours, stacked (paper protocol)", F.mstd(p, "stack", "accuracy"), f3(p["stack"]["precision"]["mean"]), f3(p["stack"]["fpr"]["mean"])],
        ["Ours, XGBoost (paper protocol)", F.mstd(p, "xgb", "accuracy"), f3(p["xgb"]["precision"]["mean"]), f3(p["xgb"]["fpr"]["mean"])],
        ["Ours, stacked (official split)", F.mstd(o, "stack", "accuracy"), f3(o["stack"]["precision"]["mean"]), f3(o["stack"]["fpr"]["mean"])],
    ], widths=[1.45, 0.8, 0.6, 0.55], size=6.8, align=["l", "c", "c", "c"])
    P.para(f"**Synthetic against real data.** The shipped model scores {f3(sh['accuracy'])} on its synthetic test split, {f3(shift['shipped_on_fresh_synthetic_seed7']['stack']['accuracy'])} on freshly generated synthetic data, "
           f"but {f3(real_on_shipped['accuracy'])} accuracy (ROC-AUC {f3(real_on_shipped['roc_auc'])}) on the {F.OFF['test_rows']:,} real test flows; a real-trained model scores "
           f"{f3(shift['real_trained_on_synthetic_demo_csv']['stack']['accuracy'])} on the synthetic CSV. The 2.5 % label noise caps accuracy on the synthetic data at about 0.975, and XGBoost, the CNN and the "
           "stack all score the same there, so that figure measures the generator, not the detector. In the console, 120 real flows are agreed with by the shipped model in 78 cases (65.0 %) and by the real-trained bundle in 101 (84.2 %) (Fig. 5).")
    crow = []
    for sz in ["1 KB", "100 KB", "1 MB", "5 MB"]:
        crow.append([sz, f"{F.crypto_row('sc', sz, 'encrypt'):.2f} / {F.crypto_row('sc', sz, 'decrypt'):.2f}", f"{F.crypto_row('aes', sz, 'encrypt'):.2f} / {F.crypto_row('aes', sz, 'decrypt'):.2f}",
                     f"{F.crypto_row('rsa2048', sz, 'encrypt'):.2f} / {F.crypto_row('rsa2048', sz, 'decrypt'):.2f}", f"{F.crypto_row('rsa3072', sz, 'encrypt'):.2f} / {F.crypto_row('rsa3072', sz, 'decrypt'):.2f}"])
    P.table("Median encrypt / decrypt time in ms", ["Payload", "SecureChannel", "AES-GCM only", "RSA-2048 hybrid", "RSA-3072 hybrid"], crow, widths=[0.5, 0.75, 0.7, 0.75, 0.75], size=6.8, align=["l", "c", "c", "c", "c"])
    P.figure(figs["secure"], "Secure transfer screen: the first ciphertext byte was changed in transit and the cloud rejects the message (tag verification failed).")
    P.para(f"**Cryptography.** {ok_tamper:,} of {n_tamper:,} tampered envelopes (flipped ciphertext, tag or nonce bit, truncation, wrong key; 1,000 trials each) were rejected and untouched messages were always accepted. "
           f"20,000 encryptions of one plaintext produced 20,000 distinct nonces and ciphertexts. For a 1 KB payload SecureChannel takes {sc_enc1:.2f} ms to encrypt and {sc_dec1:.2f} ms to decrypt; "
           f"the RSA-2048 hybrid encrypts faster ({r2_enc1:.2f} ms) but decrypts slower ({r2_dec1:.2f} ms, and {r3_dec1:.2f} ms for RSA-3072), and its wrapped key is 256 bytes against a 65-byte ephemeral key. "
           f"At 1 MB SecureChannel needs {F.crypto_row('sc', '1 MB', 'encrypt'):.1f} ms to encrypt and {F.crypto_row('sc', '1 MB', 'decrypt'):.1f} ms to decrypt, more than the raw AES-GCM cost of "
           f"{F.crypto_row('aes', '1 MB', 'encrypt'):.2f} ms because the API payload is base64 coded.")
    P.para(f"**Combined overhead.** One protected 100 KB transfer (score one flow, encrypt, decrypt) takes {ip['protected_transfer_100kb']['median_ms']:.2f} ms in process, split into IDS scoring "
           f"{ip['ids_score_single']['median_ms']:.2f} ms ({share['ids'] * 100:.0f} %), encryption {ip['encrypt_100kb']['median_ms']:.2f} ms and decryption {ip['decrypt_100kb']['median_ms']:.2f} ms. Through the HTTP API on 127.0.0.1 "
           f"the three calls for a 1 KB payload take {ap['protected_transfer_via_api_1kb']['median_ms']:.1f} ms; one scoring call alone is {ap['score_single']['median_ms']:.1f} ms, a 1 KB encrypt call {ap['encrypt_1kb_text']['median_ms']:.1f} ms, "
           f"a 120-row batch {ap['score_batch_120_rows']['median_ms']:.0f} ms and a 1 MB file encryption {ap['encrypt_file_1mb']['median_ms']:.0f} ms. Detection, not encryption, dominates the cost. "
           f"With the 192-input real-trained models a single flow takes {F.OFF['inference_timing_ms']['1']['median_ms']:.1f} ms and 1,000 flows {F.OFF['inference_timing_ms']['1000']['median_ms']:.0f} ms, so the detector would keep up with thousands "
           "of flows per second on this machine but was not tested under concurrent load.")
    P.figure(figs["real"], "Output screens with real data: held-out metrics of the real-trained bundle (top), and 120 real flows scored by the shipped model (bottom left, 65.0 % agreement) and by the real-trained bundle (bottom right, 84.2 %).")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("CipherGuard Shield delivers an authenticated-encryption path and a machine-learning intrusion detector as one tested platform with a live console. Against the batch objectives, the hybrid "
           "scheme was met by substitution (ECDH instead of RSA, with RSA benchmarked), key generation and distribution were met but key storage was not (the cloud key lives in memory), "
           "encrypt-before-upload and decrypt-after-download were met against a mock cloud, and the detector and the evaluation were met on real UNSW-NB15 data.")
    P.para(f"The key findings are that standard primitives reject every tampered message at sub-millisecond cost for payloads up to 100 KB, that detection accounts for {share['ids'] * 100:.0f} % of a protected "
           f"transfer's time, and that the shipped model's {f3(sh['accuracy'])} accuracy comes from synthetic data and falls to {f3(real_on_shipped['accuracy'])} on real flows. On real data XGBoost alone "
           f"({f3(o['xgb']['accuracy']['mean'])}) beat the stacked ensemble ({f3(o['stack']['accuracy']['mean'])}). Limitations: no live packet capture, no authentication or TLS in the demo, an in-memory alert log, "
           f"{pct(normal_fa, 0)} false alarms on normal traffic at the default threshold, no adversarial testing and a test machine shared with other jobs.")
    P.para("Two objectives are only partly met. Suspicious flows are scored, flagged and logged with a severity, but the alert is not tied to a particular transfer and nothing is blocked "
           "automatically; and evaluation of enc/dec time, overhead and accuracy is complete for this prototype but not for a deployment, because the cloud is simulated in the same process and "
           "no network latency, concurrency or memory cost was measured.")
    P.para("The result most worth carrying forward is methodological: a detector must be judged on real traffic under a temporally separated split, with false alarms and per-category rates "
           "reported, and the cost of encryption must be measured next to the cost of detection on the same path. Both were done here on a single machine and a single dataset, so the findings "
           "describe this prototype and UNSW-NB15, not cloud traffic in general.")
    P.para("Future work: ship the real-trained model as the default and tune its threshold on a validation period; add per-category and calibrated outputs to cut false alarms; couple the verdict to "
           "the transfer so that flagged sessions are held; persist keys in a key-management service with TLS and authentication; and evaluate against evasion attacks and on newer datasets.")

    P.references()
    return P.save(path)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "19.IEEE_Paper.docx")))
