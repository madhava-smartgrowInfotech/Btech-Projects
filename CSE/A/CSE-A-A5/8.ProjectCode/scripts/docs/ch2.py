"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def blocks():
    b = _full()
    if not F.REPORT:
        return b
    from .ch1 import trim
    keep_rel = lambda r: not any(n in r[0] for n in ("Alrayes", "Nadeem", "Bakro", "Mbaya"))
    return trim(
        b,
        drop=("Two surveys frame the field", "Older and adjacent work shows the same pattern", "Taken together, the surveyed detectors"),
        drop_sections=("2.2.5", "2.3.5"),
        table_rows={"Related work compared": keep_rel},
    )


def _full():
    bp = F.BASE_PAPER_RESULTS
    base, arx = R["base"], R["arxiv"]
    surv = [R["s_fmdb"], R["s_ijsr"], R["s_blowfish"], R["s_hybrid_gmr"]]
    off, pap = F.OFFS, F.PAPS
    bl = bp["baselines"]
    base_rows = [
        ["Data", f"UNSW-NB15 [{R['unsw15']}], {bp['samples']:,} samples, balanced (4,500 attack, 4,500 non-attack), 2 classes"],
        ["Split and repetitions", f"Stratified {bp['split']} train / validation / test; every experiment run {bp['runs']} times and averaged"],
        ["Preprocessing", "Min-max normalisation of every feature to [0, 1]"],
        ["Detector", "FLPF with EVD-QNN (a quantum-inspired network run on classical hardware) fused with a LeNet CNN by double-sigmoid median min-max score-level fusion (DSMMN-SLF)"],
        ["Cryptography", "Enhanced Elliptic Curve Cryptography (EECC), applied to the data that the detector declares non-intrusive"],
        ["Hardware", "64-bit OS, x64 processor, 16 GB RAM (15.7 GB usable)"],
        ["Headline accuracy", f"Mean accuracy {bp['proposed_mean_accuracy']:.4f} over repetitions (Table 2 of the paper); {bp['proposed_ablation_accuracy']:.5f} in the ablation at 80 % training data"],
        ["Precision and FPR", f"Precision {bp['precision_at_90']:.2f} at 90 % training data; false-positive rate {bp['fpr']:.2f}"],
        ["Baselines (mean accuracy)", "; ".join(f"{k} {v:.4f}" for k, v in bl.items())],
        ["Encryption cost", f"Encryption {bp['enc_time_s']:.2f} s, decryption {bp['dec_time_s']:.2f} s, latency {bp['latency']:.3f} (units and payload size as printed in the paper)"],
    ]
    rel_rows = [
        [f"Lin et al. [{R['lin']}]", "ResNet-50, VGG19, XceptionNet, EfficientNet for security-grade evaluation", "EfficientNet 99.9 % detection rate (as described in [1])", "Evaluation system, not a transmission framework"],
        [f"Alrayes et al. [{R['alrayes']}]", "Deep-neural-network IDS", "Real-time monitoring benefit (as described in [1])", "No encryption of the data path"],
        [f"Nadeem et al. [{R['nadeem']}]", "SMOTE, cuckoo-search / information-gain / PSO feature selection, random forest", "Better than compared methods (as described in [1])", "Cloud IDS only"],
        [f"Bakro et al. [{R['bakro']}]", "Hybrid feature selection with an ML classifier for a cloud IDS", "Improved over compared work (as described in [1])", "Detection only"],
        [f"Rahman et al. [{R['rahman']}]", "GAN-generated synthetic data to train NIDS models", "100 % on BoT-IoT (as described in [1])", "Perfect scores on synthetic-derived data warrant caution"],
        [f"Mbaya et al. [{R['mbaya']}]", "SecFedIDM-V1: blockchain with BiLSTM-RNN, federated", "Web application on CIDDS (as described in [1])", "Heavy architecture; separate from payload encryption"],
        [f"Kadry et al. [{R['kadry']}]", "Optimised quantum neural network plus elliptic-curve cryptography", "98.5 % accuracy (as described in [1])", "Combines detection and ECC but not measured as one path"],
        [f"Alhusseini et al. [{arx}]", "HyIDS: Energy Valley Optimizer feature selection with SVM, RF, decision tree, KNN", "D_TreeEVO 99.13 % (CIC-DDoS2019), 99.78 % (CSE-CIC-IDS2018)", "Different datasets; detection only, no encryption"],
        [f"Kalyanasundaram et al. [{base}]", "Quantum-inspired QNN + LeNet fusion, EECC", f"Mean accuracy {bp['proposed_mean_accuracy']:.4f}, precision {bp['precision_at_90']:.2f}", "Balanced 9,000-sample subset; no formal EECC security proof"],
    ]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey covers four strands of work that meet in this project: machine-learning detectors for network and cloud intrusion, encryption schemes used for data in the cloud, "
          "designs that combine the two, and the datasets and evaluation protocols on which the detectors are judged. The batch literature survey lists five works, led by the base paper "
          f"[{base}]; the other four [{surv[0]}]-[{surv[3]}] are an encryption-and-anomaly-detection study of cloud storage and transmission, a multi-cloud intrusion-detection method "
          "with automated data deletion, a federated attack-detection scheme with an improved Blowfish cipher, and a hybrid-encryption privacy framework. Their abstracts were read where "
          "they could be retrieved; results quoted below are the authors' own claims and were not reproduced. The base paper's own reference list supplies much of the detector literature, "
          "and each claim taken from it is marked as described in the base paper."),

        H2("2.2 Base Paper Analysis"),
        H3("2.2.1 Problem and approach"),
        P(f"Kalyanasundaram, Raja and Kanthimathi [{base}] observe that once an attacker has access to a network the attacker can collect information quickly, so a detector is needed, "
          "and that the data must also be protected. They propose a deep-learning intrusion detector followed by an enhanced elliptic-curve encryption of the data judged "
          "non-intrusive. The detector has three stages. Inputs are first normalised with min-max scaling. Two classifiers then score each sample: a quantum-inspired network "
          "(FLPF with EVD-QNN) that adds an eigenvalue-decomposition block to its flatten-layer feature map, and a LeNet CNN [" + str(R['lenet']) + "]. Their scores are fused by "
          "a double-sigmoid, median min-max normalisation (DSMMN-SLF) followed by a weighted sum. The paper stresses that the QNN is quantum-inspired and runs on classical "
          "hardware, with the quantum circuit simulated by differentiable classical transformations."),
        P("The cryptographic part, EECC, modifies the key relations and the encryption and decryption equations of elliptic-curve cryptography so that, the authors claim, equivalent "
          "security is obtained with a smaller key and lower computation. Security is discussed against brute-force, chosen-ciphertext, known-plaintext and man-in-the-middle attacks "
          "by empirical comparison with AES, ElGamal, Blowfish, ECC and RSA."),
        H3("2.2.2 Evaluation protocol and reported numbers"),
        TAB("The base paper at a glance", ["Item", "As reported in the paper"], base_rows, widths=[1.6, 4.7], align=["l", "l"], size=10),
        H3("2.2.3 Strengths"),
        B("It addresses detection and encryption in one framework, which is the gap this project also targets.",
          "It uses a public benchmark (UNSW-NB15), repeats each experiment ten times, fixes seeds and keeps hyper-parameters constant across models.",
          "It includes an ablation (removing the QNN, the fusion, or the normalisation lowers accuracy) and a parameter-sensitivity analysis of the fusion.",
          "It is candid that the network is quantum-inspired and that a formal proof of EECC security is future work."),
        H3("2.2.4 Limitations"),
        B(f"The evaluation uses a 9,000-sample balanced subset of a dataset whose official training and testing sets hold {F.OFF['train_rows']:,} and {F.OFF['test_rows']:,} flows; the paper itself notes that "
          "unbalanced classes are left to future work, and the selection of the subset is not published.",
          "The ablation and the headline accuracy are reported at different training fractions (80 % and 90 %), so figures from different tables cannot be mixed.",
          "EECC lacks a proof under standard hardness assumptions such as the elliptic-curve discrete-logarithm problem; its timing figures are quoted without a stated payload size in bytes or key length, so they cannot be compared directly with a production cipher.",
          "The detector and the cipher are connected in sequence (only data judged non-intrusive is encrypted); detection metrics and encryption timings are reported separately, and the cost of running both on one path is not reported."),
        P(f"This project follows the paper's idea of one framework with both protections and its 70/15/15 protocol, but replaces the quantum-inspired network by XGBoost and a one-dimensional CNN, "
          f"replaces EECC by a standard ECDH + HKDF + AES-GCM construction [{R['gcm']}], [{R['sp80056a']}], [{R['hkdf']}] and fuses the two detector outputs with a logistic-regression stack."),

        H3("2.2.5 What this project keeps from the base paper and what it changes"),
        TAB("Base paper compared with this project", ["Aspect", "Base paper", "This project"],
            [["Detector", "Quantum-inspired QNN + LeNet", "XGBoost + 1D CNN (PyTorch)"],
             ["Fusion", "DSMMN-SLF score-level fusion", "Logistic-regression stacking on the two probabilities"],
             ["Preprocessing", "Min-max normalisation", "Min-max on numeric features plus one-hot on proto, service, state"],
             ["Cipher", "EECC (modified elliptic-curve scheme)", "ECDH P-256 + HKDF-SHA256 + AES-256-GCM (standard)"],
             ["Link between the parts", "Detector first; only non-intrusive data is encrypted", "Two lanes side by side; the API does not gate a transfer on the verdict"],
             ["Data protocol", f"{bp['samples']:,} balanced samples, {bp['split']}, {bp['runs']} runs", f"Official partition ({F.OFF['train_rows']:,} / {F.OFF['test_rows']:,}), 5 seeds; and the paper's protocol, {F.PAP['split_sizes']['test']:,}-flow test sets, 10 runs"],
             ["Security evidence", "Empirical comparison of key-breaking time and correlation", "Tamper tests (1,000 trials per case), nonce-uniqueness test, standard primitives"]],
            widths=[1.4, 2.4, 2.5], align=["l", "l", "l"], size=9.5),

        H2("2.3 Related Work"),
        H3("2.3.1 Machine-learning and deep-learning intrusion detection"),
        P(f"Detectors for network and cloud intrusion form the largest body of work. As described in the base paper, Lin et al. [{R['lin']}] compared ResNet-50, VGG19, XceptionNet and EfficientNet for "
          f"a network security-grade evaluation and report a 99.9 % detection rate for EfficientNet; Alrayes et al. [{R['alrayes']}] built a deep-neural-network IDS; Nadeem et al. [{R['nadeem']}] combined SMOTE "
          f"oversampling with cuckoo-search, information-gain and particle-swarm feature selection and a random forest for a cloud IDS; and Bakro et al. [{R['bakro']}] proposed a hybrid feature-selection design for cloud intrusion "
          f"detection. Rahman et al. [{R['rahman']}] trained detectors on GAN-generated data and report perfect scores on BoT-IoT, a result that should be read with caution because synthetic "
          f"training and evaluation data can make a task easier than real traffic. Alani et al. [{R['alani']}] study a hybrid ensemble IDS for the Internet of Things, and Qazi et al. [{R['qazi']}] a deep-learning network IDS called zero-touch "
          f"network security. Mbaya et al. [{R['mbaya']}] combine blockchain with a BiLSTM-RNN in a federated IDS (SecFedIDM-V1)."),
        P(f"Alhusseini et al. [{arx}], archived with this batch, address cloud intrusion detection from the feature side: the Energy Valley Optimizer reduces the CIC-DDoS2019 features from 88 to 38 and the "
          "CSE-CIC-IDS2018 features from 80 to 43, and four classifiers (SVM, random forest, decision tree, KNN) are evaluated after down-sampling; the best model, a decision tree with the optimiser, "
          "reaches 99.13 % accuracy (F1 98.94 %) on the first dataset and 99.78 % accuracy (F1 99.70 %) on the second. These numbers are on different datasets and cannot be compared with UNSW-NB15 results."),
        P(f"Two surveys frame the field. Ahmad et al. [{R['ahmad']}] review machine-learning and deep-learning network IDS and conclude that accuracy, false alarms and novel attacks remain open problems, and "
          f"Vinayakumar et al. [{R['vinayakumar']}] evaluate a deep-neural-network IDS on several public datasets. On UNSW-NB15 itself, Kasongo and Sun [{R['kasongo']}] use XGBoost-based feature reduction and report a "
          "decision-tree binary test accuracy that rises from 88.13 % to 90.85 %, which places accuracies of roughly 0.88 to 0.91 in the normal range for classical models on the official partition."),
        P("Across this strand, tree ensembles and small neural networks perform similarly on tabular flow features, and the reported accuracies depend heavily on dataset, subset and split. "
          "The ensemble idea used here, a stacking of a tree model and a network, follows Wolpert's stacked generalisation [" + str(R['stacking']) + "] with gradient-boosted trees [" + str(R['xgboost']) + "]."),
        H3("2.3.2 Encryption for data in the cloud"),
        P(f"The batch survey items add four recent studies of protecting data in the cloud. Boye [{surv[0]}] combines homomorphic and quantum-resistant encryption with CNN and LSTM anomaly detection on "
          "access and activity logs, with encryption applied during transmission, and evaluates the idea by simulation. Singh and Bhathal "
          f"[{surv[1]}] propose an automated data-deletion system with an integrated intrusion detector that removes stored data as soon as an intrusion is detected; the abstract presents it as a brief idea and "
          f"gives no evaluation. Shinde and Ghadekar [{surv[2]}] pair federated-learning attack detection with an improved Blowfish cipher for secure transmission; only the title, venue and year could be "
          f"verified, so no result from it is quoted. Pamarthi and Rao [{surv[3]}] describe a three-layer hybrid in which the data is obfuscated, encrypted with AES, the AES key is masked with XOR, and the key is "
          "exchanged with RSA or a modified elliptic-curve scheme; for inputs of 2 to 12 KB they report encryption in 2.09 s and decryption in 2.45 s (author-reported, different hardware, so not comparable with the "
          "timings of this report)."),
        P(f"Older and adjacent work shows the same pattern. Mahalle and Shahade [{R['mahalle']}] present the classic hybrid in which RSA protects an AES key for cloud upload and download, and Rao and Sujatha [{R['rao']}] "
          "combine an Edwards-curve Diffie-Hellman exchange with AES for public clouds and report key generation in 0.000025 s and encryption in 0.00349 s (author-reported). Vengala et al. use a modified "
          f"elliptic-curve scheme inside a three-factor authentication protocol [{R['vengala']}]. Common to all of them is a symmetric cipher for the payload, an asymmetric step for the key, and elliptic-curve "
          "primitives increasingly preferred for their small keys; none of them measures an intrusion detector on the same path."),
        P(f"The building blocks of this project are standards rather than novel schemes: AES [{R['aes']}] in Galois/Counter Mode [{R['gcm']}], elliptic-curve Diffie-Hellman key establishment on the NIST P-256 curve "
          f"[{R['sp80056a']}], HKDF [{R['hkdf']}] for key derivation, and, as the comparison baseline, RSA with OAEP padding [{R['oaep']}]. Authenticated encryption is preferred to a bare cipher "
          "because it detects modification, which matters for data in transit."),
        H3("2.3.3 Joint intrusion detection and cryptography"),
        P(f"Few designs put the two protections in one framework. Kadry et al. [{R['kadry']}] combine an optimised quantum neural network with elliptic-curve cryptography and report 98.5 % accuracy, as described in "
          f"the base paper; the base paper [{base}] extends the idea with a fused detector and EECC; Boye [{surv[0]}] pairs encryption with anomaly detection on logs but, as far as the abstract shows, gives no "
          f"figures; and Shinde and Ghadekar [{surv[2]}] pair federated attack detection with an improved Blowfish cipher by their title. Of the five works in the batch survey only the base paper and Boye "
          "combine detection and encryption at all. In these works the two parts are evaluated separately: detection accuracy on one side, encryption strength or timing on the other. The cost "
          "of running both on one data path, and the way the cost splits between them, is not reported."),
        H3("2.3.4 Datasets and evaluation protocol"),
        P(f"UNSW-NB15 was created at the UNSW Canberra Cyber Range Lab with the IXIA PerfectStorm tool, which mixes real modern normal activity with synthetic contemporary attack behaviour; the "
          f"authors captured 100 GB of raw traffic with tcpdump and derived 49 features with the Argus and Bro-IDS tools [{R['unsw15']}], [{R['unsw16']}]. It has nine attack categories (Fuzzers, Analysis, Backdoors, DoS, Exploits, Generic, "
          f"Reconnaissance, Shellcode, Worms). The official partition has {F.OFF['train_rows']:,} training and {F.OFF['test_rows']:,} testing flows. Because the two sets come from different capture periods, a "
          "model trained on one is tested under a mild distribution shift, whereas random splits of the pooled data are easier. This project therefore reports both the official partition "
          f"and the base paper's balanced 9,000-sample protocol. Zoghi and Serpen [{R['zoghi']}] describe class imbalance and class overlap in UNSW-NB15, and Ring et al. [{R['ring']}] survey network-based "
          "IDS datasets in general; both are reasons for stating the split and the class balance next to every accuracy figure."),

        H3("2.3.5 What the survey implies for the design"),
        P("Four practical lessons were taken from the reading and shaped the design chapters that follow."),
        N("**Use standard, authenticated primitives.** The strongest claim a student project can make about cryptography is that it uses a well-reviewed construction correctly. AES-GCM "
          "gives confidentiality and integrity in one pass, so a separate integrity check is unnecessary, and a fresh nonce per message is the one rule that must not be broken.",
          f"**Give every message its own key.** An elliptic-curve exchange with an ephemeral sender key costs about {F.CRY['key_setup']['ecdh_exchange_plus_hkdf']['median_ms']:.2f} ms (ECDH plus HKDF, median) on the measurement machine and means that a leaked session key exposes one message only.",
          "**State the protocol before the number.** The surveyed accuracies cannot be ranked because subsets and splits differ, so this project reports the official partition, the base paper's protocol "
          "and the synthetic-data result side by side and says which is which.",
          "**Measure the combination.** Because the gap is the missing cost of running both protections, the benchmark and latency scripts time detection and encryption separately and together."),
        H2("2.4 Datasets and Algorithms Used in This Project"),
        TAB("Datasets and algorithms of this project", ["Element", "Choice", "Why"],
            [["Real data", f"UNSW-NB15 official partition: {F.OFF['train_rows']:,} train, {F.OFF['test_rows']:,} test flows, 42 features used", "Same benchmark as the base paper; official split gives a realistic, harder test"],
             ["Demo data", f"Generated synthetic set: {F.SYNTH_ROWS:,} rows, same 42-feature schema", "Lets the product run with no download; carries no claim about real traffic"],
             ["Preprocessing", "Min-max scaling of 39 numeric features, one-hot encoding of proto, service and state", "Min-max as in the base paper; one-hot for the three categorical features"],
             ["Tree model", f"XGBoost [{R['xgboost']}], 200 trees, depth 6", "Strong on tabular flow data, trains in seconds"],
             ["Neural model", f"1D CNN in PyTorch [{R['pytorch']}], two conv layers, Adam [{R['adam']}]", "Counterpart of the base paper's convolutional LeNet branch"],
             ["Fusion", f"Logistic-regression stacking [{R['stacking']}] on the two probabilities", "Simple, trainable analogue of score-level fusion"],
             ["Key agreement", f"ECDH on P-256 [{R['sp80056a']}], fresh ephemeral key per message", "Small public values, per-message keys"],
             ["Key derivation", f"HKDF-SHA256 [{R['hkdf']}]", "Standard extract-and-expand KDF"],
             ["Payload cipher", f"AES-256-GCM [{R['gcm']}], 12-byte nonce, 16-byte tag", "Authenticated encryption; tampering is detected"],
             ["Baseline", f"RSA-2048 / 3072 OAEP [{R['oaep']}] + AES-GCM", "The objective's RSA design, benchmarked"],
             ["Tooling", f"scikit-learn [{R['sklearn']}], PyTorch, FastAPI, React", "Reproducible, open-source stack"]],
            widths=[1.2, 2.8, 2.3], align=["l", "l", "l"], size=9.5),

        H2("2.5 Strengths and Limitations of the Surveyed Work"),
        TAB("Related work compared", ["Work", "Approach", "Reported result", "Limitation for this project"], rel_rows, widths=[1.3, 2.0, 1.6, 1.4], align=["l", "l", "l", "l"], size=9),
        P("Taken together, the surveyed detectors are strong on accuracy but are evaluated on different datasets, subsets and splits, so their numbers are not interchangeable; the encryption "
          "studies concentrate on the cipher; and the few joint designs evaluate the two halves separately."),

        H2("2.6 Research Gap"),
        P("The batch survey identified the gap in one sentence: the surveyed work treats cryptography and intrusion detection as separate concerns, and a single transmission path where both "
          "operate together, with the combined overhead measured, is missing. The reading above supports and sharpens it:"),
        N("**No measured combined path.** The joint designs report detection metrics and encryption timings independently; no source separates the per-transfer cost of detection from that of encryption.",
          "**Evaluation protocol is rarely stated or comparable.** Subset, balance and split differ between papers, and perfect or near-perfect scores appear on synthetic or heavily down-sampled data.",
          "**Integrity is seldom tested.** Few works show, with repeated trials, that a modified ciphertext is rejected, although authenticated encryption exists to provide exactly that.",
          "**Reproducibility.** Implementations are seldom released, so the numbers cannot be checked against real traffic by a student team."),
        P(f"This project responds with a runnable platform and its measurements: authenticated encryption and a stacked detector on one path, a per-transfer cost of "
          f"{F.f2(F.IP['protected_transfer_100kb']['median_ms'])} ms for a 100 KB payload with the detector's share stated, 5,000 tamper trials (plus 1,000 untouched controls), and a detector evaluated on the real official partition "
          f"({F.mstd(off, 'stack', 'accuracy')} accuracy stacked, {F.mstd(off, 'xgb', 'accuracy')} XGBoost alone) and under the base paper's protocol ({F.f3(pap['stack']['accuracy']['mean'])})."),
    ]
