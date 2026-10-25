# LITERATURE_FACTS - CipherGuard Shield (CSE-A-A5)

What is verified about the literature, and how. Reference numbers are those of `scripts/docs/refs.py` (`CITE['key']`). Verification used the Crossref REST API, the OpenAlex API (abstracts), DataCite (arXiv records), the base-paper PDF and the archived arXiv PDF. Anything marked **WEAK** must not be quoted for results.

## 1. Citation keys

Fixed contract, 1-30: 1 base, 2 s_fmdb, 3 s_ijsr, 4 s_blowfish, 5 s_hybrid_gmr, 6 arxiv, 7 unsw15, 8 unsw16, 9 xgboost, 10 lenet, 11 stacking, 12 gcm, 13 sp80056a, 14 hkdf, 15 aes, 16 oaep, 17 sklearn, 18 pytorch, 19 adam, 20 kadry, 21 nadeem, 22 bakro, 23 mbaya, 24 rahman, 25 alrayes, 26 lin, 27 alani, 28 qazi, 29 hdaib, 30 vengala.

Extras added (31-40), all with a checkable DOI or arXiv id:

| # | key | What it is | Use it for |
|---|---|---|---|
| 31 | kasongo | Kasongo & Sun, J. Big Data 2020, doi 10.1186/s40537-020-00379-6 | XGBoost-based feature reduction on UNSW-NB15; decision tree binary test accuracy 88.13% -> 90.85% (so ~0.88-0.91 is the normal range for classic ML on the official data) |
| 32 | vinayakumar | Vinayakumar et al., IEEE Access 2019, doi 10.1109/ACCESS.2019.2895334 | DNN-based IDS evaluated on several public datasets (deep-learning IDS background) |
| 33 | ahmad | Ahmad et al., Trans. Emerg. Telecommun. Technol. 2021, doi 10.1002/ett.4150 | Survey/taxonomy of ML and DL NIDS; IDS still struggle with accuracy, false alarms and novel attacks |
| 34 | ring | Ring et al., Comput. Secur. 2019, doi 10.1016/j.cose.2019.06.005 | Survey of network-based IDS data sets (dataset background) |
| 35 | zoghi | Zoghi & Serpen, arXiv:2101.05067 (2021) | UNSW-NB15 shows class imbalance and class overlap (read abstract) |
| 36 | goldschmidt | Goldschmidt & Chuda, arXiv:2502.06688 (2025) | Systematic review of 89 NIDS datasets; use only as "dataset survey" - its specific criticism of UNSW-NB15 was seen only in a search summary |
| 37 | mahalle | Mahalle & Shahade, INPAC 2014, doi 10.1109/INPAC.2014.6981152 | Classic hybrid RSA + AES for secure cloud upload / download (weak venue) |
| 38 | rao | Rao & Sujatha, Meas.: Sens. 2023, doi 10.1016/j.measen.2023.100870 | Hybrid ECC (Edwards curve + Diffie-Hellman) + AES for public cloud; key generation 0.000025 s, encryption 0.00349 s, 693.10 KB/s (author-reported) |
| 39 | sudha | Sudha & Arunachalaperumal, 2025, doi 10.1007/s40998-025-00816-3 | Optimised hybrid AES + ECC secure cloud storage. **WEAK**: title only, no abstract |
| 40 | hybrid_ijsea | IJSEA, Mar 2025, doi 10.7753/IJSEA1403.1013 | Hybrid AES-256 + RSA cloud scheme; authors report 35% lower encryption and 28% lower decryption time. **WEAK**: no authors in the records |

Not used and why: McGrew & Viega GCM paper (not a verifiable journal record); Vinayakumar author list and Ahmad / Ring author lists are abbreviated "et al." because the full lists were not retrieved.

## 2. The batch literature survey (5.LITERATURE SURVEY.docx)

| # | Work (as the batch lists it) | Verified record | What it does (from the abstract) | Quotable result |
|---|---|---|---|---|
| 1 | Base paper, IEEE Access 2026 | Kalyanasundaram, Raja, Kanthimathi; vol 14 pp 63767-63779; doi 10.1109/ACCESS.2026.3686106; PDF read | See section 3 | See section 3 |
| 2 | Strengthening cloud security through advanced encryption and anomaly detection ..., FMDB Trans. Sustain. Comput. Lett., 2024 | **Harikiran Boye**; vol 2 no 3 pp 153-163; doi 10.69888/FTSCL.2024.000241 | Combines homomorphic and quantum-resistant encryption with CNN/LSTM anomaly detection on access and activity logs; real-time encryption during transmission; evaluated by simulation on large cloud-activity datasets | "High accuracy ... minimal degradation in computational efficiency" - **no numbers in the abstract** |
| 3 | An automated data deletion: a secure method for multi-cloud security with IDS, IJSR, 2024 | **Jashanbir Singh, Gurjit Singh Bhathal**; vol 13 no 8 pp 213-217; doi 10.21275/SR24730194843 | Proposes an "Automated Data Deletion System with Integrated Intrusion Detection System" that deletes stored data as soon as an intrusion is detected | None: the abstract calls it a "brief idea"; no evaluation |
| 4 | Federated learning-based attack detection and secure data transmission in cloud using improved Blowfish encryption, Eng. Appl. Artif. Intell., 2026 | **Madhumati B. Shinde, Premanand P. Ghadekar**; vol 182, Art. 115975; doi 10.1016/j.engappai.2026.115975 | Title: federated-learning attack detection + improved Blowfish encryption for cloud transmission | **WEAK - no abstract retrievable; quote nothing beyond the title** |
| 5 | A cloud-based data privacy framework using hybrid encryption algorithms for secure data transmission, Genetics and Molecular Research, 2026 | **Nagaraju Pamarthi, Nagamalleswara Rao N**; doi 10.4238/mq5a9v31 | Three-layer hybrid: pre-obfuscated data, AES, XOR mask over the AES key, then RSA or MECC key exchange | Inputs 2-12 KB; encrypt 2.09 s, decrypt 2.45 s; throughput 0.0196 / 0.0167; power 5.56; security score 96 (vs OB-MECC 94, ECC 81, Base64 72). Author-reported simulation; no intrusion detection |

The survey's own gap statement (batch file): *"The surveyed work treats cryptography and intrusion detection as separate concerns. The gap is a single transmission path where both operate together and the combined overhead is measured."* Of the five, only [1] and [2] combine encryption with detection, and [2] gives no figures; [3] is a concept paper; [5] has no detection layer.

## 3. The base paper [1] (read in full from the PDF)

Title: *Intrusion Detection Model Using Fused Quantum NN-LeNet With Improved Elliptic Curve Cryptography Based Data Security*. V. Kalyanasundaram, Sivakami Raja, S. Kanthimathi (VIT Chennai). Received 23 Mar 2026, accepted 13 Apr 2026, published 21 Apr 2026. IEEE Access vol. 14, pp. 63767-63779, doi 10.1109/ACCESS.2026.3686106.

**Method.**
1. *Pre-processing:* min-max normalisation, N_n = (N - min N)/(max N - min N) (eq. 1).
2. *Detection:* two classifiers - (a) "FLPF with EVD-QNN": a quantum-inspired neural network (six conv layers, six batch-norm layers, sigmoid / tanh / swish / leaky-ReLU, max / average / mixed pooling, scaled dot product, flatten) whose flatten-layer feature map is concatenated with the eigenvalue/eigenvector decomposition (EVD) of that map; (b) LeNet (conv 6 -> avg-pool -> conv 16 -> avg-pool -> flatten -> FC 120 / 84 tanh -> softmax). The paper states plainly that the QNN is "quantum-inspired ... running on classical hardware", not a quantum computer.
3. *Fusion:* DSMMN-SLF - double-sigmoid median min-max normalisation based score-level fusion (eqs. 36-43): scores are normalised by tanh/double-sigmoid transforms and combined with weights proportional to each classifier's normalised score.
4. *Cryptography:* data judged non-intrusive is encrypted with Enhanced ECC (EECC), a modified ElGamal-style ECC with a re-defined secret key (eq. 50), encryption E(t1), E(t2) (eqs. 51-52) and a random integer kappa; claims "equivalent security with less key size than conventional ECC".

**Dataset and protocol.** UNSW-NB15 (IXIA PerfectStorm, UNSW Canberra; 100 GB raw pcap; nine attack categories; 49 features). Only **9,000 samples, balanced (4,500 normal / 4,500 attack)**, two classes; stratified 70 % training / 15 % validation / 15 % testing; **10 repetitions, averages reported**; Adam, learning rate 0.0001-0.001 with early stopping; machine: 64-bit OS, 16 GB RAM (15.7 usable). Baselines were "re-implemented and fine-tuned": QNN+ECC [Kadry], QAE, PolyNet, LinkNet, Bi-LSTM, SqueezeNet, LeNet. The exact subset, test fraction and hyper-parameters are not published; unbalanced experiments are "proposed for future studies".

**Every reported number.**
- Abstract / text: precision of FLPF-EVD-QNN + LeNet "97 %"; precision 0.97 at training data (TD) 90 %; false-positive rate 0.03.
- Ablation (Table 1, TD = 80 %): proposed accuracy **0.95638**; LeNet with existing QNN 0.931662; with existing SLF 0.915825; with no SLF 0.902357; with no normalisation 0.90404; NPV of proposed 0.949652.
- Statistical analysis (Table 2), mean accuracy: **proposed 0.948696**; QNN+ECC 0.90492; QAE 0.904385; PolyNet 0.905035; LinkNet 0.912707; Bi-LSTM 0.899314; SqueezeNet 0.935426; LeNet 0.906939.
- Attack analysis (Fig. 7): brute-force key-breaking time of EECC **39 s** at 100 % data variation (longer than AES, ElGamal, Blowfish, ECC, RSA); chosen-plaintext correlation **0.135**; key-sensitivity correlation **0.16** (Fig. 9a).
- Time (Fig. 8): EECC encryption **0.39 s**, decryption **0.26 s**; latency (enc + dec) **0.645** (Fig. 9b) - lower than AES, ElGamal, Blowfish, ECC, RSA (data sizes and units are not given in the text).
- Parameter sensitivity (q, omega, delta) and ROC (TPR above all baselines at FPR 0.005) are described qualitatively.

**Stated limitations / caveats (in the paper itself).** "A rigorous cryptographic proof of security using standard hardness assumptions like ECDLP has not been fully developed" - the security analysis of EECC is empirical (brute force, CCA/KPA, MITM discussion); the QNN is quantum-*inspired*; the dataset is the 9,000-sample balanced subset ("to allow unbiased comparison"), real IDS data are naturally imbalanced; the encryption is applied *after* detection only to non-intrusive data (detection and encryption are chained, not measured as one path).

**What it is not.** It is a detector + a cipher design evaluated separately; it does not specify a transport protocol, an authenticated mode (no tag/nonce analysis) or a deployable service. CipherGuard Shield implements neither EECC nor the QNN; it uses standard ECDH P-256 / HKDF / AES-256-GCM and an XGBoost + 1D-CNN stack.

Reference list of the base paper (32 entries) is in the scratchpad text `base.txt`; entries [14], [19]-[25], [29], [30] feed refs 20-30 above. Mappings used: base [22] Kadry -> 20; [25] Nadeem -> 21; [24] Bakro -> 22; [23] Mbaya -> 23; [21] Rahman -> 24; [19] Alrayes -> 25; [14] Lin -> 26; [20] Alani -> 27; [1] Qazi -> 28; [30] Hdaib -> 29; [29] Vengala -> 30. Note: in the base paper's *text* the Lin et al. work is cited as [18] and the Alani et al. work as [20] ("Ibrahim et al." in the text is a mis-attribution of the same slot); the reference list is authoritative.

## 4. Archived arXiv paper [6] (read)

Alhusseini, Rouhi, Feizi-Derakhshi, *AI-powered hybrid intrusion detection framework for cloud security using novel metaheuristic optimization*, arXiv:2601.01134 (3 Jan 2026), 18 pages. Covers the **ML half only**.
- **HyIDS:** Energy Valley Optimizer (EVO) feature selection followed by four ML models: SVM, Random Forest, Decision Tree (D_Tree) and KNN; 24 experiments.
- **Data:** CIC-DDoS2019 (88 -> 38 features) and CSE-CIC-IDS2018 (80 -> 43 features), both heavily imbalanced; balanced by downsampling.
- **Results (abstract):** D_TreeEVO accuracy **99.13 %**, F1 **98.94 %** on CIC-DDoS2019; accuracy **99.78 %**, F1 **99.70 %** on CSE-CIC-IDS2018.
- **Literature tables** quote other works (e.g. Gebremariam et al. RF-XGB on UNSW-NB15 / CICIDS2017 / NSL-KDD up to 100 % / 99.80 %; Zhou et al. HHO-DNN 81.92 % on UNSW-NB15; Aljamal et al. detection rate 94.7 %).
- It has no encryption component, so it is background for the IDS half only and is not the batch's base paper.

## 5. Facts for deck and paper claims

- UNSW-NB15 [7], [8]: created at the UNSW Canberra Cyber Range Lab with IXIA PerfectStorm; official partition 175,341 training and 82,332 testing records, 42 flow features plus label and attack category (verified in this run from the data itself: 56,000/119,341 and 37,000/45,332 normal/attack).
- Typical numbers on UNSW-NB15: decision tree 88.13 % -> 90.85 % binary accuracy with XGBoost feature reduction [31]; ">98 %" multi-class for a SMOTE + IG/CS/PSO + RF design with unspecified split [22]; the base paper's 0.949 on a 9,000-row balanced subset [1]. Our measured values: 0.890 stacked / 0.910 XGBoost (official split), 0.938 (paper-style protocol) - consistent with the ranges above once the protocol is accounted for.
- Known dataset issues: class imbalance and overlap [35]; temporally shifted official train/test sets (our own results: shipped synthetic model 0.660 on the real test set; protocol gap about 5 points).
- Crypto positioning: AES-GCM per NIST SP 800-38D [12], ECDH per SP 800-56A [13], HKDF per RFC 5869 [14], AES per FIPS 197 [15], RSA-OAEP per RFC 8017 [16]. Literature on hybrid cloud schemes [5], [37], [38], [40] reports seconds-scale or percent-scale gains in author-run simulations; none measures an IDS on the same path.

## 6. Unverifiable or weak items (read before quoting)

1. Ref 4 (Shinde & Ghadekar, 2026): abstract not retrievable; only title/authors/venue/DOI verified.
2. Ref 36: UNSW-NB15 criticism attributed to it in a search summary was not read in the source.
3. Ref 39 and 40: no abstract / no author list respectively.
4. Refs 12-16 (NIST, IETF) and 17-19: bibliographic details written from knowledge of the standard records and not re-fetched this run (Crossref returned only secondary books for scikit-learn and PyTorch). Low risk, but they are the only entries without a fetched record.
5. Refs 24-29 (Rahman, Alrayes, Lin, Alani, Qazi, Hdaib): existence, title, venue and pages checked against Crossref; only Qazi's abstract was read. Results of these works must not be quoted beyond what the base paper says about them.
