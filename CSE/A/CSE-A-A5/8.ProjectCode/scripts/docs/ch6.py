"""Chapter 6: Methodology and Software Implementation.

methodology_blocks() feeds document 9 (and the first half of chapter 6); application_blocks() feeds document 12 (and the second half).
Every number is read from facts.py (experiments/**/metrics.json, reports/metrics.json); nothing is typed in by hand.
"""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB

try:
    from .refs import CITE as R
except Exception:  # refs.py is written by another module; fall back to the fixed numbering contract
    R = {}

_FIXED = {"base": 1, "arxiv": 6, "unsw15": 7, "unsw16": 8, "xgboost": 9, "lenet": 10, "stacking": 11, "gcm": 12, "sp80056a": 13,
          "hkdf": 14, "aes": 15, "oaep": 16, "sklearn": 17, "pytorch": 18, "adam": 19}


def c(*keys):
    return "[" + ", ".join(str(R.get(k, _FIXED[k])) for k in keys) + "]"


def _txt(blk):
    k = blk[0]
    if k in ("p", "eq", "h1", "h2", "h3", "code"):
        return blk[1]
    if k == "fig":
        return blk[2]
    if k == "tab":
        return blk[1]
    if k in ("b", "n"):
        return " ".join(blk[1])
    return ""


def _drop(b, *needles):
    """Report mode only: remove blocks whose text contains one of the needles (each must match something)."""
    out = list(b)
    for n in needles:
        hit = [x for x in out if n in _txt(x)]
        assert hit, f"ch6 trim needle not found: {n}"
        out = [x for x in out if n not in _txt(x)]
    return out


def _renumber_h3(b):
    import re
    out, sec, k = [], None, 0
    for x in b:
        if x[0] == "h2":
            sec, k = re.match(r"(\d+\.\d+)", x[1]).group(1), 0
        elif x[0] == "h3" and sec:
            k += 1
            x = ("h3", f"{sec}.{k} " + re.sub(r"^\d+\.\d+\.\d+\s+", "", x[1]))
        out.append(x)
    return out


def cnn_params(dim):
    flat = (dim // 4) * 64
    return 1 * 32 * 3 + 32 + 32 * 64 * 3 + 64 + flat * 64 + 64 + 64 + 1


def methodology_blocks():
    O, P_, S, SH = F.OFF, F.PAP, F.OFFS, F.SHIPPED
    sw = F.SHIFT
    fit, val, test = O["fit_rows"], O["val_rows"], O["test_rows"]
    st = O["seed42"]["stack"]
    spw_real = 56000 / 119341
    flat70, flat192 = (F.INPUT_DIM_SYNTH // 4) * 64, (F.INPUT_DIM_REAL // 4) * 64
    t90 = F.thr_row(0.9)
    b = []

    # ---------------------------------------------------------------- 6.1
    b += [H2("6.1 Overall methodology"),
          P("CipherGuard Shield protects one cloud data path in two independent ways. The first protection is cryptographic: the payload is encrypted before it leaves the sender with a fresh key that "
            "only the cloud can reconstruct, and any change to the ciphertext is detected on arrival. The second is statistical: network-flow records that describe the traffic are scored by a machine-learning "
            f"intrusion detector, and the flows judged to be attacks are logged with a severity. The idea of putting an intrusion detector and an elliptic-curve scheme in one framework comes from the base paper {c('base')}; "
            "the project replaces its quantum-inspired network and custom elliptic-curve scheme with components that are standard, available in open-source libraries and testable on a laptop (Section 6.4 gives the reasons). "
            "The method has six steps, and the first two belong to the cryptographic lane and the next three to the detection lane:"),
          N("**Key agreement.** For every message the sender generates a new P-256 key pair and combines its private key with the cloud's long-term public key (ECDH). The shared secret is passed through HKDF-SHA256 to give a 32-byte AES key.",
            "**Authenticated encryption.** The payload is encrypted with AES-256-GCM under a random 12-byte nonce. The result is a ciphertext of the same length as the plaintext and a 16-byte authentication tag. The sender transmits the *envelope*: ciphertext, nonce, tag and its ephemeral public key.",
            "**Flow preparation.** A flow record with 42 features is completed with defaults for missing fields and transformed by the fitted preprocessor: min-max scaling of the 39 numeric features and one-hot encoding of protocol, service and state.",
            "**Two classifiers.** XGBoost and a one-dimensional convolutional network each output the probability that the flow is an attack.",
            "**Stacking and decision.** A logistic-regression meta-model combines the two probabilities; a probability of at least 0.5 means *attack*, and the severity band (medium, high, critical) follows from the probability. Attacks are appended to an in-memory alert log.",
            "**Cloud verification.** The cloud re-derives the AES key from its private key and the envelope's ephemeral public key, decrypts, and accepts the message only if the authentication tag verifies."),
          FIG(F.diag("02_high_level_workflow.png"), "The two lanes of CipherGuard Shield: authenticated encryption of the payload and detection on the traffic.", 5.5),
          P("Two procedures sit outside the request path. The *training pipeline* (`cipherguard/ids/train.py`) builds the shipped bundle once from a labelled table and writes the model files and `reports/metrics.json`. "
            "The *experiment scripts* added during the documentation run (`scripts/run_experiments.py`, `benchmark_crypto.py`, `measure_pipeline.py`) re-use the same preprocessing and model code to evaluate it on real data, "
            "to benchmark the cryptography and to time the whole pipeline. Their JSON output is the single source of every figure reported in this document.")]

    # ---------------------------------------------------------------- 6.2
    b += [H2("6.2 Datasets"),
          P("Three datasets are involved, and keeping them apart is essential for reading the results. The shipped model was trained on a synthetic table generated by the project; the experiments use real traffic from "
            "UNSW-NB15; and one experiment imitates the evaluation protocol of the base paper."),
          H3("6.2.1 The synthetic demonstration dataset (shipped model)"),
          P(f"When `data/raw/` holds no UNSW-NB15 file, `train_pipeline` calls `generate_synthetic` (`cipherguard/ids/synthetic.py`) to create **{F.SYNTH_ROWS:,} rows**: 6,000 normal and 6,000 attack, with the 42-feature schema of UNSW-NB15. "
            "The generator draws every numeric feature from a simple distribution whose parameters differ between the two classes. Attack flows get a longer duration (exponential with mean 1.8 s against 0.8 s), "
            "more source packets (Poisson with mean 18 plus a uniform 0 to 7 against Poisson 8), larger byte counts (log-normal with log-mean 7.2 against 6.3), a higher rate (normal with mean 45,000 against 18,000), "
            "more connection counters (`ct_*`) and a different mix of protocols, services and states. A few features are drawn independently of the class (window sizes, TCP base numbers, `dttl`), and `ct_state_ttl` is never assigned and is therefore 0 in every row."),
          P(f"After generation 2.5 % of the labels (**300 of {F.SYNTH_ROWS:,} rows**) are flipped at random so that accuracy is not a perfect 1.0. The stratified 70/15/15 split gives {F.SYNTH_SPLIT[0]:,} training, {F.SYNTH_SPLIT[1]:,} validation "
            f"and {F.SYNTH_SPLIT[2]:,} test rows. The shipped metrics (accuracy {F.pct(F.SHIPPED['accuracy'], 2)}, F1 {F.f4(F.SHIPPED['f1'])}) are computed on that test split. Because the classes are separated by construction, the only thing that stops the model from reaching "
            f"100 % is the injected label noise, which caps accuracy at about 97.5 % if the clean classes were perfectly separable; the XGBoost model, the CNN and the stack all scored the same {F.pct(F.SHIPPED['xgb_accuracy'], 2)}, "
            "which is what a task this easy produces. A second consequence is that the `attack_cat` column of attack rows is drawn with an unseeded random call, so the file `data/raw/synthetic_demo.csv` is not reproducible bit for bit."),
          H3("6.2.2 UNSW-NB15 (real traffic)"),
          P(f"UNSW-NB15 {c('unsw15', 'unsw16')} was created at the Cyber Range Lab of UNSW Canberra by mixing real normal activity with synthetic contemporary attack behaviour generated by the IXIA PerfectStorm tool; "
            "100 GB of raw traffic was captured with tcpdump, and the Argus and Bro-IDS tools and twelve further algorithms extracted flow features. The data is free for academic research with citation. "
            f"This project uses the *official partition*: a training set of **175,341 flows** (56,000 normal and 119,341 attack) and a testing set of **{test:,} flows** (37,000 normal and 45,332 attack, {F.pct(O['test_attack_rate'], 2)} attack). "
            "The ten traffic categories are Normal, Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoor, Shellcode and Worms. The 42 features used by the application are exactly the "
            "flow features of the official files; the files were obtained as the `standard` configuration of the Hugging Face repackaging `lacg030175/UNSW-NB15` by `scripts/fetch_unsw_nb15.py`."),
          P("The two official files cover different capture periods, so a model trained on the first and tested on the second faces a *temporal shift*; accuracies obtained this way are lower than those from a random split of the same data, "
            "because near-duplicate flows cannot leak from the test set into training. The project reports the temporal protocol as its main real-data result for that reason."),
          H3("6.2.3 The base paper's protocol"),
          P(f"The base paper {c('base')} evaluates on 9,000 flows of UNSW-NB15, balanced to 4,500 per class, split 70/15/15 and repeated ten times with averaged metrics; it does not publish which flows were drawn. "
            f"The project imitates the protocol in `run_paper`: for each of ten seeds, 4,500 normal and 4,500 attack flows are sampled from the official training file and split into {P_['split_sizes']['train']:,} training, {P_['split_sizes']['val']:,} validation and "
            f"{P_['split_sizes']['test']:,} test flows. The sample is comparable in size and balance but not identical, so the comparison in Chapter 8 is indicative only."),
          TAB("Datasets and splits used in this project.",
              ["Dataset", "Rows", "Role", "Split"],
              [["Synthetic demo CSV (generated)", f"{F.SYNTH_ROWS:,}", "Trains the shipped models", f"{F.SYNTH_SPLIT[0]:,} / {F.SYNTH_SPLIT[1]:,} / {F.SYNTH_SPLIT[2]:,} (70/15/15)"],
               ["UNSW-NB15 official training set", "175,341", "Trains the real-trained bundle", f"{fit:,} fit / {val:,} validation (85/15)"],
               ["UNSW-NB15 official testing set", f"{test:,}", "Held-out test, never used for fitting", "whole file"],
               ["Paper-protocol sample", "9,000", "Imitates the base paper", f"{P_['split_sizes']['train']:,} / {P_['split_sizes']['val']:,} / {P_['split_sizes']['test']:,}, 10 repetitions"]],
              widths=[2.1, 0.8, 1.9, 2.0], align=["l", "r", "l", "l"], size=9.5)]

    # ---------------------------------------------------------------- 6.3
    b += [H2("6.3 Data preparation and feature encoding"),
          P("All three data paths use the same transformer, `build_preprocessor()` in `cipherguard/ids/preprocessing.py`. It is a scikit-learn `ColumnTransformer` " + c('sklearn') + " with two branches:"),
          B("a `MinMaxScaler` for the 39 numeric features (durations, packet and byte counts, rates, loads, jitter, TCP window and sequence fields, round-trip times, the `ct_*` connection counters and the three flag-like fields);",
            "a `OneHotEncoder(handle_unknown=\"ignore\")` for the three categorical features `proto`, `service` and `state`, so that a category never seen in training produces an all-zero block instead of an error."),
          P(f"The encoded vector has **{F.INPUT_DIM_SYNTH} inputs** for the synthetic bundle (39 numeric plus 31 one-hot columns: 6 protocols, 13 services, 12 states) and **{F.INPUT_DIM_REAL} inputs** for the real-trained bundle, because the real files contain many more protocol "
            "values (for example `unas`, `ospf`, `sctp`) and service and state values. The scaler and the encoder are fitted on the training portion only; validation and test rows are only transformed, so no information from them reaches the fit."),
          P("At scoring time the engine is forgiving about the input. Missing feature columns are filled with 0 (numeric) or `-` (categorical); column names are matched case-insensitively; categorical values are cast to text; "
            "and the API merges a single record with documented defaults (for example `proto` tcp, `service` http, `state` CON). The identifier, `label` and `attack_cat` columns of a CSV are ignored when scoring. "
            "No further cleaning is applied to the real data; the files are used as published."),
          P(f"Class imbalance is handled in two ways. XGBoost receives `scale_pos_weight = n_normal / n_attack` computed on the training portion (about {spw_real:.2f} for the real training file, close to 1 for the synthetic one). "
            "The README states that the CNN also uses balanced loss weighting; this is true only of the TensorFlow code path, which was not the one that ran. The PyTorch path, which produced every shipped and measured result, trains the CNN with plain, unweighted binary cross-entropy (Section 6.6).")]

    # ---------------------------------------------------------------- 6.4
    b += [H2("6.4 Algorithm choice and justification"),
          P("Each component was chosen for a reason that can be checked, and each rejected alternative has a reason too. Table 6.1 summarises the decisions and the paragraphs below discuss the three that matter most."),
          TAB("Algorithm choices and the alternatives that were not used.",
              ["Role", "Chosen", "Not chosen", "Reason"],
              [["Payload cipher", f"AES-256-GCM {c('gcm', 'aes')}", "AES-CBC + HMAC; ChaCha20-Poly1305", "One primitive gives confidentiality and integrity; hardware-accelerated in the library; tag failure is a single, clear error"],
               ["Key agreement", f"ECDH on P-256 {c('sp80056a')}", "RSA key transport (objective 1); finite-field DH", "Small public values (65 B), a fresh key per message at almost no cost, no padding oracle surface"],
               ["Key derivation", f"HKDF-SHA256 {c('hkdf')}", "Use the raw shared secret", "The ECDH output is not uniformly random; HKDF turns it into a uniform 256-bit key and binds a context string"],
               ["Detector A", f"XGBoost {c('xgboost')}", "Single decision tree; SVM", "Strong on tabular data, trains in seconds, gives calibrated-enough probabilities, handles mixed scales"],
               ["Detector B", f"1D CNN {c('lenet')}", "LSTM; quantum-inspired network", "Small (76 k parameters at 70 inputs), trains on CPU, offers a different inductive bias from trees"],
               ["Fusion", f"Logistic-regression stacking {c('stacking')}", "Plain average; DSMMN score-level fusion", "Two learned weights are easy to inspect and to report; the base paper's DSMMN needs parameters it does not publish"]],
              widths=[1.0, 1.4, 1.7, 2.7], align=["l", "l", "l", "l"], size=9),
          H3("6.4.1 ECDH in place of RSA"),
          P("The first batch objective asked for a hybrid scheme with AES for the payload and RSA for the key exchange. The project keeps the hybrid structure (an asymmetric step to establish a key, a symmetric cipher for the data) but uses elliptic-curve Diffie-Hellman for the asymmetric step. "
            f"Two properties decided it. First, because the sender creates a fresh key pair for every message, compromise of one session key reveals nothing about other messages, which RSA key transport under a long-term key does not give. Second, the public value in the envelope is 65 bytes instead of the 256 bytes of an RSA-2048 wrapped key. "
            f"The cost is that the cloud-side step is an ECDH computation (about {F.CRY['key_setup']['ecdh_exchange_plus_hkdf']['median_ms'] * 1000:.0f} microseconds including HKDF on the measurement machine). To make the substitution testable, the project benchmarks RSA-2048 and RSA-3072 with OAEP {c('oaep')} and AES-256-GCM on the same machine (Chapter 7): RSA encryption is cheaper "
            f"({F.crypto_row('rsa2048', '1 KB', 'encrypt'):.3f} ms against {F.crypto_row('sc', '1 KB', 'encrypt'):.3f} ms at 1 KB) but RSA decryption at the cloud is dearer ({F.crypto_row('rsa2048', '1 KB', 'decrypt'):.3f} ms for RSA-2048 and {F.crypto_row('rsa3072', '1 KB', 'decrypt'):.3f} ms for RSA-3072 against {F.crypto_row('sc', '1 KB', 'decrypt'):.3f} ms)."),
          H3("6.4.2 XGBoost and a CNN, stacked"),
          P("The detector is deliberately a modest ensemble of two different learners. XGBoost is the strongest standard method on tabular flow features, and it is the model that carries the result on real data. "
            "The 1D CNN treats the encoded feature vector as a short sequence; it is included because the base paper's detector is also a convolutional one and because the brief asked for a deep model. "
            f"The measurements in Chapter 8 show that on the official partition the CNN alone (accuracy {F.mstd(S, 'cnn', 'accuracy')}) is worse than XGBoost ({F.mstd(S, 'xgb', 'accuracy')}) and that stacking ({F.mstd(S, 'stack', 'accuracy')}) does not recover the difference. "
            "The project reports this rather than adjusting the design: stacking improves slightly on a plain average of the two probabilities and costs almost nothing, but it is not better than XGBoost alone on this data."),
          H3("6.4.3 What was not reproduced from the base paper"),
          P(f"The base paper {c('base')} proposes an eigenvalue-decomposition-augmented quantum-inspired network, a double-sigmoid median score-level fusion (DSMMN-SLF) and an *enhanced* elliptic-curve encryption (EECC) whose security the authors themselves say has not been proved against the ECDLP. "
            "None of these is implemented here. The quantum-inspired network is a research model without a maintained library, the fusion has parameters that are not published, and replacing a standard, reviewed cipher by a new scheme without a security proof would lower, not raise, the protection of real data. "
            "The project's contribution is therefore a clean, measured integration of standard parts, and Chapter 8 compares its numbers with the paper's with that difference stated.")]

    # ---------------------------------------------------------------- 6.5
    b += [H2("6.5 Mathematical formulation"),
          P("This section states the computations that the code performs, in the order of the pipeline. Symbols are defined where they first appear."),
          H3("6.5.1 Key agreement, key derivation and authenticated encryption"),
          P(f"Let G be the base point of NIST P-256 {c('sp80056a')} and C = c·G the cloud's long-term public key, with private scalar c. For each message the sender draws a new scalar e and sends E = e·G. Both parties can compute the same shared point:"),
          EQ("Z = x-coordinate of ( e · C ) = x-coordinate of ( c · E )"),
          P(f"HKDF {c('hkdf')} with SHA-256 first extracts a pseudo-random key from Z (no salt, so a string of zero bytes is used) and then expands it with the context string `cipherguard-shield-v1` to 32 bytes:"),
          EQ("PRK = HMAC-SHA256( salt = 0^32 , Z )          K = HKDF-Expand( PRK , info = \"cipherguard-shield-v1\" , L = 32 )"),
          P(f"AES-256-GCM {c('gcm')} encrypts the plaintext M under K and a random 96-bit nonce N, producing a ciphertext T of the same length and a 128-bit tag A that authenticates T (and any associated data, here none):"),
          EQ("( T , A ) = AES-256-GCM-Enc( K , N , M )        M = AES-256-GCM-Dec( K , N , T , A )  or  reject"),
          P("GCM computes A from a polynomial (GHASH) over the ciphertext in the field GF(2^128), masked by an AES block that depends on the nonce. Changing any bit of T, N or A, or using a different K, changes the recomputed tag and the decryption fails with an invalid-tag error, which the API turns into HTTP 400. "
            f"The envelope therefore adds {F.ENVELOPE_OVERHEAD_BYTES} bytes to every message: 12 (nonce) + 16 (tag) + 65 (uncompressed ephemeral point) bytes."),
          H3("6.5.2 Feature scaling and encoding"),
          EQ("x' = ( x - min_j ) / ( max_j - min_j )          for each numeric feature j, with min_j and max_j taken from the training portion"),
          EQ("one-hot( v ) = ( 1[v = v_1] , ... , 1[v = v_m] )          an unseen v gives the zero vector"),
          P(f"Values outside the training range give scaled values below 0 or above 1; the models are not clipped. The result is the vector x of {F.INPUT_DIM_SYNTH} (shipped) or {F.INPUT_DIM_REAL} (real-trained) inputs."),
          H3("6.5.3 The two classifiers"),
          P(f"XGBoost {c('xgboost')} builds an additive model of regression trees. With the logistic loss, the probability of attack is"),
          EQ("p_xgb( x ) = sigmoid( sum over t = 1..200 of f_t( x ) )          sigmoid( z ) = 1 / ( 1 + e^(-z) )"),
          P("and each tree f_t is chosen to minimise a second-order approximation of the regularised objective"),
          EQ("Obj = sum_i w_i · loss( y_i , yhat_i ) + sum_t ( gamma · T_t + 0.5 · lambda · ||leaf weights of tree t||^2 )          w_i = n_normal / n_attack for attack rows, else 1"),
          P(f"where w_i is the `scale_pos_weight` re-weighting of the positive class. The depth is limited to 6, the learning rate is 0.08, and each tree sees 85 % of the rows and 85 % of the columns."),
          P(f"The 1D CNN reads x as a one-channel sequence of length d. With ReLU activations, max pooling of width 2 and convolutions padded so that the length is preserved:"),
          EQ("h1 = ReLU( Conv1d_{1->32,k=3}( x ) ) ,  p1 = MaxPool2( h1 )          h2 = ReLU( Conv1d_{32->64,k=3}( p1 ) ) ,  p2 = MaxPool2( h2 )"),
          EQ("u = ReLU( W1 · flatten( p2 ) + b1 ) ,  u' = Dropout_0.3( u )          p_cnn( x ) = sigmoid( W2 · u' + b2 )"),
          P(f"The flattened vector has floor(d/4) × 64 elements: {flat70:,} for d = {F.INPUT_DIM_SYNTH} and {flat192:,} for d = {F.INPUT_DIM_REAL}. The number of trainable parameters is 128 + 6,208 + (floor(d/4)·64 + 1)·64 + 65, which is **{cnn_params(F.INPUT_DIM_SYNTH):,}** for the shipped bundle "
            f"(file size about 300 KB) and {cnn_params(F.INPUT_DIM_REAL):,} for the real-trained bundle. The network is trained by minimising the binary cross-entropy with the Adam optimiser {c('adam')}:"),
          EQ("L = -( 1 / n ) · sum_i [ y_i · ln p_i + ( 1 - y_i ) · ln( 1 - p_i ) ]"),
          H3("6.5.4 Stacking, decision rule and severity"),
          P(f"The meta-model is a logistic regression {c('stacking')} fitted on the validation split, whose inputs are the two base probabilities:"),
          EQ("p( x ) = sigmoid( w_1 · p_xgb( x ) + w_2 · p_cnn( x ) + b )"),
          P(f"The fitted values of the shipped bundle are w_1 = {F.SHIPPED['meta_coef'][0][0]:.3f}, w_2 = {F.SHIPPED['meta_coef'][0][1]:.3f} and b = {F.SHIPPED['meta_intercept'][0]:.3f}: both models contribute almost equally. The decision rule and the severity band are"),
          EQ("label = attack  if  p >= 0.5  else  normal          severity = critical if p >= 0.85 ,  high if p >= 0.70 ,  medium otherwise  (attacks only);  normal flows are low"),
          P("A threshold of 0.5 is the shipped value. Chapter 8 shows how precision, recall and the false-positive rate move when it changes, because for an operator the cost of a false alarm and the cost of a missed attack are not equal."),
          H3("6.5.5 Evaluation metrics"),
          P("With TP, TN, FP and FN the counts of the confusion matrix in which *attack* is the positive class, the reported metrics are"),
          EQ("accuracy = ( TP + TN ) / ( TP + TN + FP + FN )          precision = TP / ( TP + FP )          recall = TP / ( TP + FN )          F1 = 2 · precision · recall / ( precision + recall )"),
          EQ("FPR = FP / ( FP + TN )          FNR = FN / ( FN + TP )          MCC = ( TP·TN - FP·FN ) / sqrt( ( TP+FP )( TP+FN )( TN+FP )( TN+FN ) )"),
          P("ROC-AUC is the area under the curve of recall against FPR over all thresholds. When several seeds are run the tables report the mean and the sample standard deviation (n - 1 in the denominator).")]

    # ---------------------------------------------------------------- 6.6
    b += [H2("6.6 Model architecture and training"),
          FIG(F.diag("12_model_architecture.png"), "Architecture of the ThreatSense Engine: preprocessing, XGBoost, the 1D CNN and the stacking meta-model.", 5.6),
          H3("6.6.1 Training configuration"),
          TAB("Training configuration shared by the shipped bundle and the experiments.",
              ["Component", "Setting"],
              [["XGBoost", "200 trees, max depth 6, learning rate 0.08, subsample 0.85, column sample 0.85, scale_pos_weight = n_normal / n_attack, logloss, seed from the run"],
               ["1D CNN", f"Conv1d 1-32 (k 3) - MaxPool 2 - Conv1d 32-64 (k 3) - MaxPool 2 - Linear 64 - Dropout 0.3 - Linear 1 - sigmoid; {cnn_params(F.INPUT_DIM_SYNTH):,} parameters at 70 inputs"],
               ["CNN training", "Adam, learning rate 0.001, batch 256, at most 15 epochs, early stopping on validation loss (patience 5, minimum gain 0.0001), best weights restored, plain BCE loss (no class weights)"],
               ["Meta-model", "scikit-learn LogisticRegression with default regularisation, fitted on the validation split's [p_xgb, p_cnn]"],
               ["Split", "Stratified; shipped: 70/15/15 (seed 42); official partition: training file split 85/15 into fit and validation, testing file untouched"],
               ["Decision", "Threshold 0.5 on the stacked probability"],
               ["Hardware", "Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11, CPU only; Python 3.11.9, PyTorch 2.14.1 (CPU), XGBoost 2.0.3, scikit-learn 1.5.0"]],
              widths=[1.2, 5.6], align=["l", "l"], size=9.5),
          P(f"Training is cheap. On the official partition ({fit:,} fit rows) XGBoost trains in {O['train_seconds']['xgb']:.1f} s and the CNN in {O['train_seconds']['cnn']:.0f} s on the shared CPU used for the measurements; the meta-model takes milliseconds. "
            "The README gives 30 to 60 seconds for building the shipped bundle from the synthetic table, which is what `run.bat` does on first start when `models/` is empty."),
          H3("6.6.2 Experimental protocol"),
          P(f"The experiment script `scripts/run_experiments.py` imports the shipped code rather than re-implementing it: the preprocessor, the XGBoost settings, `train_cnn_torch` and the logistic meta-model are the same objects. "
            f"For the **official partition** it runs five seeds (42 to 46). A seed controls the stratified 85/15 split of the training file and the initialisation of the CNN and XGBoost; the official testing file ({test:,} flows) is scored once per seed and never used for fitting, early stopping or the meta-model. "
            "Besides the three project models the script trains four reference models on the same data, so that the ensemble can be judged against simpler alternatives: the plain mean of the two probabilities, a logistic regression, a decision tree (depth 12) and a random forest (100 trees, depth 16). "
            "For seed 42 it additionally records the threshold sweep, the detection rate per attack category, the ROC curves, the XGBoost feature importance (gain) and in-process inference times."),
          P(f"For the **paper protocol** it repeats the whole procedure for ten seeds on the balanced 9,000-flow samples described in Section 6.2.3. For the **domain-shift study** it scores the {sw['shipped_on_real_official_test']['rows']:,} real test flows with the shipped synthetic-trained bundle, "
            "scores fresh synthetic data (seed 7, 6,000 rows) with the same bundle, and scores the synthetic demo CSV with the real-trained models. The seed-42 models are also exported as a bundle that the API can serve "
            "(`scripts/make_real_bundle.py`, Section 6.10)."),
          P(f"The measured outcome of the protocol is summarised in one line here so that the design can be read against it. On the official partition the stacked model reaches accuracy {F.mstd(S, 'stack', 'accuracy')}, F1 {F.mstd(S, 'stack', 'f1')} and ROC-AUC {F.mstd(S, 'stack', 'roc_auc')} "
            f"(seed 42: {st['confusion_matrix'][0][0]:,} true negatives, {st['confusion_matrix'][0][1]:,} false positives, {st['confusion_matrix'][1][0]:,} false negatives, {st['confusion_matrix'][1][1]:,} true positives); at a threshold of 0.9 the accuracy rises to {t90['accuracy']:.3f} and the false-positive rate falls to {t90['fpr']:.3f}. "
            f"The shipped synthetic-trained bundle, by contrast, scores {F.f3(sw['shipped_on_real_official_test']['stack']['accuracy'])} on the same real flows. Chapter 8 discusses both."),
          H3("6.6.3 Two implementation details that affect interpretation"),
          B("**Unweighted CNN loss.** The README describes balanced loss weighting for the CNN. The PyTorch training function uses `nn.BCELoss()` with no weights; the weighted loss exists only in the TensorFlow function. "
            "On the real data this probably contributes to the CNN's high recall (0.99) and high false-positive rate, because the majority class in the training file is *attack*.",
            "**Stacking on the validation split.** The meta-model is fitted on 15 % of the training period. It therefore learns how well the two models agree with the labels in that period; on the later testing period the CNN is less reliable than the weights suggest, which is why the stack is not better than XGBoost alone on the official partition.")]
    if F.REPORT:  # compact variant for the full report (documents 9 and 12 render the full text)
        b = _drop(b, "The two lanes of CipherGuard Shield", "At scoring time the engine is forgiving", "6.5.2 Feature scaling", "x' = ( x - min_j )", "one-hot( v ) =",
                  "Values outside the training range", "and each tree f_t is chosen", "Obj = sum_i", "where w_i is the", "h1 = ReLU(", "The measured outcome of the protocol is summarised")
        b = _renumber_h3(b)
    return b


def application_blocks():
    b = []
    t = F.OFF["thresholds"]
    del t
    # ---------------------------------------------------------------- 6.7
    b += [H2("6.7 Application architecture"),
          P("CipherGuard Shield is a single Python process behind a web interface. The browser tier is a React 19 console built with Vite and Tailwind (screens: landing page, live scoring, secure transfer, alerts, model performance) that calls the API through axios and a Vite proxy; "
            "the original plain HTML and JavaScript dashboard in `web/` is still served by the API at `/`. The application tier is a FastAPI application (`cipherguard/api/main.py`, 382 lines) served by Uvicorn on 127.0.0.1:" + str(F.API_PORT) + ". "
            "It delegates to two packages: `cipherguard/crypto` with the `SecureChannel` and `KeyPair` classes, and `cipherguard/ids` with the preprocessing, the training code and the `ThreatSenseEngine` that loads the model files and scores records."),
          FIG(F.diag("01_system_architecture.png"), "Layered architecture of CipherGuard Shield.", 5.4),
          TAB("Modules and their responsibilities.",
              ["Module", "Responsibility"],
              [["cipherguard/crypto/secure_channel.py", "KeyPair (P-256 generation, X9.62 uncompressed encoding and decoding); SecureChannel (ECDH + HKDF key derivation, AES-256-GCM encrypt and decrypt, one-shot ephemeral encryption)"],
               ["cipherguard/ids/features.py", "The 42-feature schema, categorical feature names, and the allowed category values used by the generator"],
               ["cipherguard/ids/preprocessing.py", "ColumnTransformer with MinMax and one-hot branches; tolerant CSV loading; helper that fills missing columns"],
               ["cipherguard/ids/synthetic.py", "Seeded generator of the synthetic demonstration dataset"],
               ["cipherguard/ids/train.py", "Training pipeline: XGBoost, PyTorch (or TensorFlow) CNN, stacking meta-model; writes models/ and reports/"],
               ["cipherguard/ids/inference.py", "ThreatSenseEngine: loads the artefacts, predicts probabilities, derives label and severity"],
               ["cipherguard/api/main.py", "FastAPI routes, validation, in-memory alert log, session-key cache, mock cloud key pair, static file serving"],
               ["web/ and frontend/", "Legacy dashboard (HTML, CSS, JS) and the React console"],
               ["scripts/", "smoke_test, capture_screens, run_experiments, benchmark_crypto, measure_pipeline, make_real_bundle, fetch_unsw_nb15, serve"],
               ["tests/", "26 pytest tests for the crypto, the engine and the API"]],
              widths=[2.4, 4.4], align=["l", "l"], size=9.5),
          P("State is kept in three places and nowhere else. The model files in `models/` and the report in `reports/` are read at start-up. The alert log is a Python list of at most 500 entries, newest first, lost when the process stops. "
            "The cloud's key pair is generated on first use and lives for the lifetime of the process, as does a dictionary that caches session keys by ephemeral public key; this is a shortcut of the demonstration, and when the cache misses (for example for an envelope created before a restart of the cache) "
            "the API re-derives the key from the cloud private key and the envelope's ephemeral public key, which is the real protocol. There is no database.")]

    # ---------------------------------------------------------------- 6.8
    b += [H2("6.8 API design"),
          P("The API is JSON over HTTP, plus two multipart upload routes. Table 6.3 lists every route; the interactive Swagger page at `/docs` documents the same contract."),
          TAB("API routes of CipherGuard Shield.",
              ["Method and path", "Request", "Success response", "Errors"],
              [["GET /api/health", "-", "status, product, version, engine_loaded", "-"],
               ["GET /api/metrics", "-", "contents of reports/metrics.json", "404 not found, 503 engine"],
               ["POST /api/ids/score", "JSON object with any subset of the 42 features", "label, confidence, severity, xgb_score, cnn_score, alert (attacks only)", "400 invalid record, 503 / 500 engine"],
               ["POST /api/ids/score-batch", "multipart CSV, at most 10 MB and 10,000 rows", "total, attack_count, normal_count, results (first 1,000 rows)", "400 not CSV / empty / too large / unparsable"],
               ["GET /api/alerts?limit=", "limit 1 to 500 (default 100)", "alerts (newest first), total", "-"],
               ["DELETE /api/alerts", "-", "cleared: true", "-"],
               ["POST /api/crypto/encrypt", "plaintext (1 byte to 1 MB)", "ciphertext, nonce, tag, ephemeral_public (all base64), algorithm, key_exchange", "400 empty or too large"],
               ["POST /api/crypto/decrypt", "ciphertext, nonce, tag, ephemeral_public", "plaintext, verified: true", "400 bad base64, missing key, tag or key mismatch"],
               ["POST /api/crypto/encrypt-file", "multipart file, 1 byte to 5 MB", "filename, envelope fields, original_size, encrypted_size", "400 missing, empty or too large"]],
              widths=[1.7, 1.8, 2.2, 1.1], align=["l", "l", "l", "l"], size=8.8),
          P("The *score* route accepts any subset of the 42 features. The server fills the rest with defaults defined in the `IDSRecord` model, overlays the supplied values, and passes the 42-field record to the engine; if the verdict is *attack* the route builds an alert entry "
            "(timestamp, severity, confidence, the protocol, service, state, source and destination bytes, rate and `ct_srv_src`, and the two model scores), inserts it at the head of the list and returns it with the verdict. The *batch* route scores a CSV in one vectorised call and adds one alert per attack row."),
          P("The *encrypt* route performs the sender's side and the cloud's long-term public key is the only key it needs; it returns the envelope as base64 strings so that it can be pasted into a text field. The *decrypt* route is the cloud's side: it decodes the envelope, obtains the AES key, and returns the plaintext only if the tag verifies. "
            "The envelope fields are independent, so the console can alter the ciphertext between the two calls and demonstrate the rejection."),
          FIG(F.diag("07_sequence_flow.png"), "Sequence of a scoring request, an encryption request and a decryption request through the API.", 5.0)]

    # ---------------------------------------------------------------- 6.9
    b += [H2("6.9 Security and error handling"),
          H3("6.9.1 What the design protects"),
          B("**Confidentiality.** Each message is encrypted under its own 256-bit key. Nonces come from the operating system's random source (`os.urandom`); in 20,000 encryptions the benchmark observed 20,000 distinct nonces and 20,000 distinct ciphertexts for one repeated plaintext.",
            "**Integrity and authenticity of the ciphertext.** GCM's tag covers the ciphertext; flipping a single bit of the ciphertext, the tag or the nonce, truncating the ciphertext, or decrypting with another party's key was rejected in every one of 1,000 trials per case.",
            "**Fresh key per message.** The sender code creates a new ephemeral key pair for every message and does not store its private part, so the keys of different messages are independent. The demonstration API does keep each derived session key in an in-memory cache (see below), which weakens this property for the lifetime of the process.",
            "**Input limits.** Plaintext 1 MB, files 5 MB, CSV 10 MB and 10,000 rows, empty inputs refused, a CSV extension required; malformed base64 and wrong-length fields produce HTTP 400 with a message, never a stack trace."),
          H3("6.9.2 What it does not protect"),
          B("**The cloud is a mock.** The key pair is created inside the same process and is never written to disk, so there is no key storage, rotation or revocation, and the session-key cache holds every session key in memory for the lifetime of the process.",
            "**No authentication or authorisation.** Any client that can reach the port can encrypt, decrypt and clear alerts. CORS is set to `*`. The server binds to 127.0.0.1 by default, which is the only access control.",
            "**No transport security.** The service speaks plain HTTP on the loopback interface; a real deployment needs TLS, and the ECDH step does not authenticate the sender (an active attacker could substitute its own ephemeral key).",
            "**Detection is advisory.** The verdict does not block a transfer; the console runs the two lanes side by side and the operator decides.",
            "**The detector can be evaded.** No adversarial testing was done, and the model's strongest feature on real data (`sttl`) is an attribute of the testbed that an attacker can set freely."),
          TAB("Error handling in the API.",
              ["Situation", "Response", "Where"],
              [["Model files missing at start-up", "Training is started automatically; if loading still fails, routes return 503", "startup_event, ensure_engine"],
               ["Empty or non-JSON record, invalid field type", "400 \"Invalid record\"", "score route"],
               ["Upload is not a .csv file, is empty, unparsable, > 10 MB or > 10,000 rows", "400 with the reason", "score-batch route"],
               ["Empty plaintext, plaintext > 1 MB, file empty or > 5 MB", "400 with the reason", "encrypt routes"],
               ["Invalid base64, missing ephemeral key, malformed point", "400 \"Invalid base64 encoding\" or \"Invalid ephemeral_public\"", "decrypt route"],
               ["Tag mismatch or wrong key", "400 \"Decryption failed (tag verification or key mismatch)\"", "decrypt route"],
               ["Unexpected exception in scoring", "500 with the exception text", "score and batch routes"]],
              widths=[2.8, 2.9, 1.1], align=["l", "l", "l"], size=9.5)]

    # ---------------------------------------------------------------- 6.10
    sp = F.PIPE["in_process"]["engine_load_ms"]
    b += [H2("6.10 Installation and execution"),
          P("The product is run in one of three ways; the complete step-by-step guide is Appendix B and `HOW_TO_RUN.md`."),
          N("**run.bat (Windows).** Creates a virtual environment, installs `requirements.txt` (FastAPI, Uvicorn, cryptography, XGBoost, scikit-learn, PyTorch, pandas), trains the models if `models/` is empty, installs the React dependencies with `npm install`, starts the API on 8305 and the console on 5305 and opens the browser.",
            "**Manual.** `pip install -r requirements.txt`, then `python -m uvicorn cipherguard.api.main:app --host 127.0.0.1 --port 8305`, and in `frontend/` `npm install` and `npm run dev`.",
            "**Docker.** `run-docker.bat` builds the image from the Dockerfile and maps container port 8000; this path was not exercised in the documentation run."),
          P(f"Loading the shipped models takes about {sp:.0f} ms on the measurement machine, so the API is ready a second or two after start-up. Ports and host come from `.env` (`BACKEND_PORT`, `FRONTEND_PORT`)."),
          P("Three additions of the documentation run are part of the execution story. `python scripts/fetch_unsw_nb15.py` downloads the official training and testing files (about 19 MB) into `data/external/` (ignored by git). "
            "`python scripts/run_experiments.py [official] [paper] [shift]` reproduces the experiments (about 25 minutes on the measurement machine). `python scripts/make_real_bundle.py` turns the seed-42 models into a bundle the API can serve; the bundle is selected with two environment variables:"),
          CODE("set CIPHERGUARD_MODELS_DIR=experiments\\unsw_nb15\\official\\models\nset CIPHERGUARD_REPORTS_DIR=experiments\\unsw_nb15\\official\\reports\npython scripts\\serve.py", 9),
          P("With these variables unset, the API serves the shipped synthetic-trained bundle. `scripts/serve.py` imports PyTorch before anything else: on the Windows machine used here, PyTorch's DLLs fail to initialise (error 1114) when NumPy or pandas have already been imported, "
            "so the launcher and the test configuration (`tests/conftest.py`) import it first. The `run.bat` environment, which pins PyTorch 2.2.0, was not re-run."),
          P("Verification after installation is `python -m pytest tests` (26 tests) and `python scripts/smoke_test.py` (15 checks against the running API; `--frontend` repeats them through the Vite proxy), described in Chapter 7. "
            "`python scripts/capture_screens.py` and `capture_real_screens.py` regenerate the screenshots used in Chapters 7 and 8.")]
    if F.REPORT:
        b = _drop(b, "Layered architecture of CipherGuard Shield", "Modules and their responsibilities", "Sequence of a scoring request", "Error handling in the API",
                  "The *encrypt* route performs the sender", "Verification after installation is")
        b = _renumber_h3(b)
    return b


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
