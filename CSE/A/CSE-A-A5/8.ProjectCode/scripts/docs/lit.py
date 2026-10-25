"""Literature and framing data for the decks (Review 1, Review 2, final) and the IEEE paper.

Every literature fact traces to docs/LITERATURE_FACTS.md; reference numbers match scripts/docs/refs.py (CITE keys).
Cells quote only what the abstracts / the base paper say; where a source gave no figure the cell says so.
"""
from .refs import CITE as R

BASE_PAPER_TITLE = "Intrusion Detection Model Using Fused Quantum NN-LeNet With Improved Elliptic Curve Cryptography Based Data Security"
BASE_PAPER_VENUE = "V. Kalyanasundaram, S. Raja, S. Kanthimathi - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Kalyanasundaram et al. [{R['base']}] (base paper)", "2026", "Quantum-inspired NN + LeNet fused by DSMMN-SLF; EECC encrypts non-intrusive data",
     "UNSW-NB15, 9,000 balanced rows: mean acc. 0.949; no ECDLP security proof"],
    [f"Kadry et al. [{R['kadry']}]", "2023", "WOA-selected features, quantum NN for attacks, optimised ECC for stored data",
     "Accuracy 98.5% (abstract); wireless-mesh setting; overhead not in abstract"],
    [f"Boye [{R['s_fmdb']}]", "2024", "Homomorphic + quantum-resistant encryption with CNN / LSTM anomaly detection",
     "Simulated cloud logs; abstract gives no numbers"],
    [f"Singh & Bhathal [{R['s_ijsr']}]", "2024", "Delete cloud data automatically when an intrusion is detected",
     "Idea paper: no implementation or evaluation reported"],
    [f"Shinde & Ghadekar [{R['s_blowfish']}]", "2026", "Federated attack detection with improved Blowfish encryption in the cloud",
     "Title only verified: no abstract retrievable, so no result quoted"],
    [f"Pamarthi & Rao [{R['s_hybrid_gmr']}]", "2026", "AES + RSA/MECC with XOR key masking for cloud transmission",
     "2-12 KB inputs; 2.09 s enc / 2.45 s dec; no attack detection"],
    [f"Mbaya et al. [{R['mbaya']}]", "2023", "Federated BiLSTM IDS with a Hyperledger signature store",
     "CIDDS data; precision 0.996, FPR 0.0009; no payload encryption"],
    [f"Bakro et al. [{R['bakro']}]", "2023", "SMOTE + IG/CS/PSO feature selection + random forest for cloud IDS",
     ">98% on UNSW-NB15 (multi-class); split protocol not in abstract"],
    [f"Kasongo & Sun [{R['kasongo']}]", "2020", "XGBoost feature reduction on UNSW-NB15 with SVM, kNN, LR, ANN, DT",
     "Decision tree binary accuracy 88.13% -> 90.85%"],
    [f"Rao & Sujatha [{R['rao']}]", "2023", "Edwards-curve ECC + Diffie-Hellman keys speed up AES for public cloud",
     "Key gen 0.000025 s, enc 0.00349 s, 693 KB/s; crypto only"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"Base paper [{R['base']}]", "Quantum-inspired NN + LeNet, DSMMN fusion, EECC", "UNSW-NB15, 9,000 balanced", "mean acc. 0.949; enc 0.39 s", "No ECDLP proof; one subset"],
    [f"Kadry et al. [{R['kadry']}]", "WOA + QNN IDS; optimised ECC", "network data (wireless mesh)", "accuracy 98.5%", "Overhead not reported in abstract"],
    [f"Boye [{R['s_fmdb']}]", "Homomorphic enc. + CNN/LSTM anomaly detection", "simulated cloud activity", "'high accuracy' (no figure)", "Simulation only; no figures"],
    [f"Singh, Bhathal [{R['s_ijsr']}]", "Delete data on intrusion", "none", "none", "Concept; not evaluated"],
    [f"Pamarthi, Rao [{R['s_hybrid_gmr']}]", "AES + RSA/MECC + XOR mask", "2-12 KB inputs", "2.09 s enc, 2.45 s dec", "No intrusion detection"],
    [f"Mbaya et al. [{R['mbaya']}]", "Federated BiLSTM + blockchain", "CIDDS", "precision 0.996, FPR 0.0009", "No payload encryption"],
    [f"Bakro et al. [{R['bakro']}]", "SMOTE, IG/CS/PSO, random forest", "UNSW-NB15, Kyoto", ">98% / >99% multi-class", "Split not in abstract"],
    [f"Kasongo, Sun [{R['kasongo']}]", "XGBoost feature reduction + ML", "UNSW-NB15", "DT 88.13 -> 90.85%", "Detection only"],
    [f"Rao, Sujatha [{R['rao']}]", "Edwards-curve ECC + AES", "synthetic inputs", "0.00349 s enc, 693 KB/s", "No detection layer"],
]

OBJECTIVES = [
    "Hybrid encryption: AES for the payload, an asymmetric scheme for key exchange",
    "Secure key generation, distribution and storage between sender and receiver",
    "Transmission module: encrypt before upload, decrypt after download",
    "Train an ML classifier on a benchmark intrusion dataset to detect anomalous access",
    "Integrate detection so suspicious sessions are flagged and logged during transfer",
    "Evaluate encryption / decryption time, throughput overhead and detection accuracy",
]

PROBLEM_STATEMENT = [
    "Data in a public cloud is readable by the provider unless it is encrypted before upload",
    "Symmetric encryption alone leaves the key exchange open to interception",
    "Encryption cannot detect an attacker who already holds valid credentials",
    "Most academic systems address either cryptography or intrusion detection, rarely both",
    "Need: one transmission path that encrypts the data and watches the traffic with ML",
]

EXISTING_SYSTEM = [
    "Cryptography-only schemes: hybrid AES + RSA or AES + ECC protect confidentiality but see no attacks",
    "IDS-only schemes: ML or deep-learning detectors on UNSW-NB15, CICIDS and similar flows, with no payload protection",
    "Two-part frameworks (e.g. QNN + ECC) report detection accuracy and encryption separately",
    "Key exchange and detection are evaluated on different data, so no per-transfer cost is known",
    "Results quoted on random or balanced subsets of UNSW-NB15 are hard to compare with the official split",
]

LIMITATIONS_OF_EXISTING = [
    "Encryption-only systems cannot flag a compromised session or an attacker with valid keys",
    "IDS-only systems leave the data readable in transit and at the provider",
    "Combined overhead of encrypting and detecting on one path is rarely measured",
    "Many abstracts report accuracy without the split, so numbers are not comparable",
    "Several surveyed cloud-security papers are concept papers or give no figures (e.g. [" + str(R['s_ijsr']) + "], [" + str(R['s_fmdb']) + "])",
    "UNSW-NB15 has known class overlap and imbalance [" + str(R['zoghi']) + "]; our own runs score about 5 points lower on the official split than on balanced random subsets",
]

GAPS = [
    "The surveyed work treats cryptography and intrusion detection as separate concerns: no single transmission path where both operate and the combined overhead is measured",
    "Reported intrusion-detection accuracy depends on the split protocol; the official UNSW-NB15 partition is harder than balanced random subsets [" + str(R['unsw15']) + "], [" + str(R['kasongo']) + "]",
    "The base paper's EECC and quantum-inspired network are not accompanied by a standard-library implementation or a security proof [" + str(R['base']) + "]",
    "Standardised primitives (ECDH P-256, HKDF, AES-256-GCM) are rarely benchmarked against the RSA hybrid that cloud tutorials still recommend [" + str(R['mahalle']) + "], [" + str(R['hybrid_ijsea']) + "]",
    "Demo systems often ship synthetic training data without testing that the model transfers to real traffic",
]
