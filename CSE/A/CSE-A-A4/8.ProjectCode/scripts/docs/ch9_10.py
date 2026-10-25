"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import cite as c


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def _v():
    """Frequently quoted measured values, read from the facts module (never typed)."""
    s = F.SAVED
    ens, sas, qs, pcd = s["ensemble"], s["sa"], s["qa"], s["classical"]
    bb = F.BASE_BAL
    sv = F.SERVING
    lat = F.LATENCY
    lr_n, rf_n, xg_n = (F.imb_row(m, "none") for m in ("Logistic Regression", "Random Forest", "XGBoost"))
    lr_u, rf_u, xg_u = (F.imb_row(m, "undersample") for m in ("Logistic Regression", "Random Forest", "XGBoost"))
    gr_u = F.imb_row("GRBMC (SA)", "undersample")
    lr_s = F.imb_row("Logistic Regression", "SMOTE")
    xg_s = F.imb_row("XGBoost", "SMOTE")
    rb = F.IMB["rule_based"]
    pe, pf = F.best_epoch("classical"), F.best_epoch("sa")
    return {
        "ens": ens, "sas": sas, "qs": qs, "pcd": pcd, "bb": bb, "sv": sv,
        "n_test": F.SPLIT["test"][0], "n_fraud_test": F.SPLIT["test_fraud"],
        "acc_e": F.pct(ens["accuracy"]), "p_e": F.pct(ens["precision"]), "r_e": F.pct(ens["recall"]), "f_e": F.pct(ens["f1"]), "auc": F.f3(ens["roc_auc"]),
        "f_sas": F.pct(sas["f1"]), "f_qs": F.pct(qs["f1"]), "f_pcd": F.pct(pcd["f1"]),
        "acc_pcd": F.pct(pcd["accuracy"]), "rec_pcd": F.pct(pcd["recall"]), "fp_pcd": pcd["fp"],
        "f_lr": F.pct(bb["Logistic Regression"]["f1"]), "f_rf": F.pct(bb["Random Forest"]["f1"]), "f_xg": F.pct(bb["XGBoost"]["f1"]),
        "seed_pcd": F.seed_cell("classical", "f1"), "seed_sas": F.seed_cell("sa", "f1"), "seed_qs": F.seed_cell("qa", "f1"),
        "acc_srv": F.pct(sv["as_served_no_scaling"]["ensemble"]["accuracy"]), "acc_scaled": F.pct(sv["with_scaling"]["ensemble"]["accuracy"]),
        "rec_srv": F.pct(sv["as_served_no_scaling"]["ensemble"]["recall"]), "fp_srv": sv["as_served_no_scaling"]["ensemble"]["fp"],
        "fp_scaled": sv["with_scaling"]["ensemble"]["fp"],
        "batch_flag": sv["sample_batch_as_served_flagged"], "batch_rows": sv["sample_batch_rows"], "batch_true": sv["sample_batch_true_fraud"], "batch_scaled": sv["sample_batch_scaled_flagged"],
        "lat": f"{lat['predict_single_fraud_example']['median_ms']:.0f}", "lat95": f"{lat['predict_single_fraud_example']['p95_ms']:.0f}",
        "lat_b": f"{lat['predict_batch_20_rows']['median_ms']:.0f}",
        "lr_n": lr_n, "rf_n": rf_n, "xg_n": xg_n, "lr_u": lr_u, "rf_u": rf_u, "xg_u": xg_u, "gr_u": gr_u, "lr_s": lr_s, "xg_s": xg_s, "rb": rb,
        "sweep": {r["threshold"]: r for r in F.SAVED["ensemble_threshold_sweep"]},
        "pe_ep": pe[0], "pe_f1": F.pct(pe[1]), "pf_ep": pf[0], "pf_f1": F.pct(pf[1]),
        "t_pcd": F.HIST["classical"]["elapsed_sec"], "t_sas": F.HIST["sa"]["elapsed_sec"], "t_qs": F.HIST["qa"]["elapsed_sec"],
        "n_rows": f"{F.DATASET['rows']:,}", "fr_rate": F.pct(F.IMB["fraud_rate"], 0),
        "smoke": f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL}",
    }


def _drop(blocks, starts=(), h2_drop=()):
    """Report mode: remove paragraphs/lists whose text starts with any prefix and whole H2 sections named in h2_drop."""
    if not F.REPORT:
        return blocks
    out, skipping = [], False
    for b in blocks:
        if b[0] == "h2":
            skipping = any(b[1].startswith(h) for h in h2_drop)
        if skipping:
            continue
        txt = b[1] if b[0] == "p" else (b[1][0] if b[0] in ("b", "n") and b[1] else "")
        if b[0] in ("p",) and any(txt.startswith(x) for x in starts):
            continue
        out.append(b)
    return out


def _p(x, d=3):
    return f"{x:.{d}f}"


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    v = _v()
    base = c("base")
    bt = F.BASE_TABLE
    return [
        P(f"{F.PRODUCT} does not propose a new learning algorithm and we do not claim one. Its model, the Gaussian-Bernoulli restricted Boltzmann machine classifier, and its three training strategies come from the base paper {base}; "
          "the preprocessing steps (one-hot encoding, z-score scaling, a correlation filter, random undersampling, random-forest feature importance) are standard. What this project adds is a runnable, openly readable implementation of "
          "that setup on CPU, a complete screening application around it, and a set of measurements that the base paper does not contain: baselines, stability across seeds, threshold behaviour, behaviour at low fraud rates and "
          "an audit of the serving path. This section states the difference from the base paper first, then separates what is new from what is borrowed."),
        H2("2.1 Difference from the base paper"),
        TAB("Base paper and this project compared (the data differ, so the result columns are not comparable)",
            ["Aspect", "Base paper " + base, F.PRODUCT],
            [["Data", "Real fintech data, about 145 million transactions, about 19 thousand fraud, balanced by manual undersampling to 39 thousand", f"Synthetic file of {v['n_rows']} rows (50/50), generated by `backend/synthetic_data.py`; the pipeline works on an 8,000-row sample"],
             ["Model", "Gaussian RBM classifier (visible, hidden, label layers)", "Same structure, written in NumPy (`backend/rbm_classifier.py`)"],
             ["Training strategies", "PCD; simulated annealing through a D-Wave simulator; quantum sampling on D-Wave hardware", "PCD; a simplified annealing sampler; a classical simulation of a transverse-field sampler (no quantum hardware)"],
             ["Hyper-parameters", "Grid search over hidden units and learning-rate schedules; 200 / 65 / 65 hidden units, batch 512 / 32 / 32", "Taken from the paper (200 / 65 / 65 hidden, batch 512 / 32 / 32), not searched"],
             ["Epochs and time", "50 epochs; about 2 minutes, 4 hours, 1.8 hours", f"20 epochs; {v['t_pcd']:.1f} s, {v['t_sas']:.1f} s, {v['t_qs']:.1f} s measured on one CPU"],
             ["Reported F1 (PCD / SAS / QS)", f"{bt['PCD'][3]} % / {bt['SAS'][3]} % / {bt['QS'][3]} % at the best epoch on real data", f"{v['f_pcd']} / {v['f_sas']} / {v['f_qs']} at the final epoch on synthetic data (best-epoch values: {F.pct(F.best_epoch('classical')[1])} / {F.pct(F.best_epoch('sa')[1])} / {F.pct(F.best_epoch('qa')[1])})"],
             ["Baselines", "None reported", f"Logistic regression, random forest and XGBoost on the same split (F1 {v['f_lr']}, {v['f_rf']}, {v['f_xg']})"],
             ["Interface", "None", "Flask API with 16 routes and a React application with seven screens"]],
            widths=[1.3, 2.5, 2.5], align=["l", "l", "l"], size=9.5),
        H2("2.2 What is new here"),
        N(f"**An open, deployable implementation.** The base paper used a Julia package and cloud access to quantum hardware. Here the same model trains on a laptop CPU in seconds (about {v['t_sas']:.0f} s for 20 epochs) and sits behind an API and a browser interface, so the pipeline can be inspected, rerun and extended.",
          f"**Baselines on the same split.** Logistic regression, random forest and XGBoost reach F1 {v['f_lr']}, {v['f_rf']} and {v['f_xg']} on the split on which the ensemble reaches {v['f_e']}. On this data the simple models are better, which the base paper could not show because it reports no baselines.",
          f"**Stability and threshold analysis.** Five retrainings give F1 {v['seed_pcd']} for PCD but {v['seed_sas']} for SAS. A threshold sweep shows that the shipped PCD model ranks transactions well (ROC-AUC {F.f3(v['pcd']['roc_auc'])}) but is badly placed at 0.5 (accuracy {v['acc_pcd']}).",
          f"**Imbalance study.** With {v['fr_rate']} fraud, undersampling lowers the precision of logistic regression, random forest and XGBoost to {_p(v['lr_u']['precision']['mean'], 2)}, {_p(v['rf_u']['precision']['mean'], 2)} and {_p(v['xg_u']['precision']['mean'], 2)}, while training without resampling keeps it above {_p(min(v['lr_n']['precision']['mean'], v['rf_n']['precision']['mean'], v['xg_n']['precision']['mean']), 2)}. This extends the base paper's remark that SMOTE and Tomek links did poorly {base} with measured numbers.",
          f"**A serving-path audit.** Reading the code against the measurements exposed that the single and bulk routes skip feature scaling, so accuracy on a fresh batch drops from {v['acc_scaled']} to {v['acc_srv']}. The defect, its cause and its measured effect are documented rather than hidden (see the system-testing and results chapters of the report)."),
        H2("2.3 What is not new"),
        B(f"The restricted Boltzmann machine, contrastive-divergence training and the Gaussian-Bernoulli variant {c('hinton06', 'cd', 'pcd', 'guide', 'liao')}.",
          f"The idea of training an RBM with an annealing or quantum sampler {c('adachi', 'ajagekar')}; the samplers here are simplified approximations of it.",
          f"One-hot encoding, z-scoring, random undersampling and random-forest feature ranking {c('smote', 'tomek', 'breiman')}.",
          f"The evaluation metrics (precision, recall, F1, ROC-AUC) and the argument that accuracy is misleading on imbalanced data {c('saito', 'fawcett', 'hegarcia')}."),
        H2("2.4 A modest reading of the novelty"),
        P("The contribution is engineering and measurement, not a new method. No claim of quantum advantage is made or supported: the quantum-inspired sampler is a classical simulation, the data are synthetic, and the simple baselines outperform the RBM models on this split. "
          "The value of the work lies in showing, with reproducible scripts, what the base paper's approach does when it is rebuilt from its description and checked against ordinary baselines and against its own serving code."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The work makes the following contributions, each backed by code in the repository and by a measurement in Chapter 8."),
        N("A complete NumPy implementation of a Gaussian-Bernoulli RBM classifier with three trainers (persistent contrastive divergence, a simplified simulated-annealing sampler and a classical simulation of a quantum-inspired sampler), including the QUBO matrix view (`backend/rbm_classifier.py`, `samplers.py`, `train.py`).",
          f"A preprocessing and balancing pipeline that follows the base paper (one-hot, z-score, correlation filter, undersampling, importance-based selection of 18 features, stratified 80/20 split) with SMOTE and Tomek-link options (`backend/preprocessing.py`).",
          f"{F.PRODUCT}: a Flask API with {F.N_ENDPOINTS} routes and a React interface for single checks, CSV bulk screening, analytics, model comparison and a retraining lab, with risk bands at {F.pct(F.RISK_BANDS[0], 0)} and {F.pct(F.RISK_BANDS[1], 0)}.",
          f"A reproducible evaluation (`scripts/run_experiments.py`) covering the shipped models, three baselines, five seeds, a threshold sweep and a {v['fr_rate']}-fraud variant with four imbalance strategies, whose output feeds every table in this report.",
          f"An honest comparison with the base paper: the base paper's Table 1 is reproduced beside this project's results with an explicit statement that real and synthetic data are not comparable.",
          f"A serving-path audit that found and quantified a silent scaling failure (accuracy {v['acc_srv']} as served against {v['acc_scaled']} when scaled), together with a latency measurement (median {v['lat']} ms per check) and a read-only smoke test of the API ({v['smoke']} checks pass).",
          "Generated documentation: diagrams, result figures, screenshots and this report are produced by scripts from the code and the measured files, so they can be regenerated."),
    ]


def scope_blocks():
    v = _v()
    return [
        H2("1.1 What is in scope"),
        P(f"{F.PRODUCT} covers the path from a table of card transactions to a risk decision, together with the means of inspecting and retraining the models. In detail the scope includes:"),
        TAB("Features in scope and where they live",
            ["Area", "What the project provides", "Where"],
            [["Data", f"A synthetic, labelled file of {v['n_rows']} transactions (19,500 fraud, 19,500 legitimate); regeneration with chosen sizes from 500 to 50,000 per class", "`backend/synthetic_data.py`, Lab screen"],
             ["Preprocessing", "One-hot encoding, z-scoring of 24 numeric columns, correlation filter, undersampling (SMOTE and Tomek links optional), top-k feature selection, stratified split", "`backend/preprocessing.py`"],
             ["Models", "Three GRBM classifiers (PCD, SAS, QS) and their mean as an ensemble; per-epoch history; QUBO matrix", "`rbm_classifier.py`, `samplers.py`, `train.py`"],
             ["Single check", "One transaction in, fraud probability, per-model probabilities, risk band and recommended action out", "`/api/predict_single`, Verify screen"],
             ["Bulk screening", "A CSV in, a prediction and probability for every row, metrics when a Class column exists, a CSV out", "`/api/predict_batch`, Bulk screen"],
             ["Analytics", "Fraud rate by merchant, channel, hour, amount band, card presence and country match over the whole file", "`/api/dataset_stats`, Analytics screen"],
             ["Model views", "Comparison table, training curves, feature importance, QUBO heat-map", "Model comparison screen"],
             ["Evaluation", "Held-out metrics, baselines, seeds, thresholds, low-fraud variant, latency, smoke test", "`scripts/`"]],
            widths=[1.2, 3.6, 1.5], align=["l", "l", "l"], size=9.5),
        H2("1.2 What is out of scope"),
        B("Real transaction data. No bank or fintech data were available; every result is on synthetic data.",
          "Quantum hardware. The quantum sampler is a classical simulation and no D-Wave or other quantum service is called.",
          "Production concerns: authentication, authorisation, encryption in transit, audit logging, rate limiting, high availability and a production web server.",
          "Streaming scoring, card-holder history features, delayed labels and drift handling.",
          "Model governance: explainability reports for regulators, fairness analysis and human review workflows.",
          "A database. State is kept in memory, CSV, pickle and JSON files."),
        H2("1.3 Intended users and use"),
        P("The interface is written for two roles: a merchant or analyst who wants to check one payment, and a risk-operations user who screens CSV exports and reads analytics. The project is a prototype for study and demonstration. "
          "The landing page itself says that the models are trained on a synthetic dataset and are not for production payments, and the documentation repeats that limit."),
    ]


def assumption_blocks():
    v = _v()
    return [
        P("The results and the design rest on the following assumptions. They are stated so that a reader can judge how far the numbers travel."),
        B(f"The synthetic generator is an adequate stand-in for a balanced, undersampled card-fraud set. Fraud transactions are drawn with larger amounts (mean {F.DATASET['amount_mean_fraud']:.2f} against {F.DATASET['amount_mean_legit']:.2f}), more online and card-not-present use, more country mismatches and shifted values in five anonymised features. Real fraud is subtler.",
          "The 50/50 balance of the file reflects the base paper's manual undersampling and is not the balance of a live stream, where fraud is a small fraction of one percent.",
          f"A random 8,000-row sample of the file is large enough to train the three models, and a stratified 80/20 split of it ({F.SPLIT['train'][0]:,} training and {F.SPLIT['test'][0]:,} test rows) is a fair held-out set.",
          "The hyper-parameters reported in the base paper (hidden units, batch size, learning-rate shape) are reasonable for this data and are not re-tuned.",
          "Transactions arrive with the same columns, units and encodings as the training file. The API does not validate ranges.",
          "All timings were taken on one Windows PC with a CPU only, with the Flask development server and the API reached at 127.0.0.1.",
          "The 0.5 decision threshold and the 0.4 and 0.7 risk bands are product choices and were not tuned on validation data."),
    ]


def limitation_blocks():
    v = _v()
    return [
        P("This section lists the limitations that matter for reading the results. Each one was either measured or can be checked in the code."),
        H2("3.1 Synthetic data"),
        P(f"Every number in this report comes from a synthetic file. Its fraud and legitimate classes differ by construction: a logistic regression separates them with F1 {v['f_lr']}, almost as well as a random forest ({v['f_rf']}). "
          "Real transactions are expected to overlap far more, and published results on real data are much lower: the best fusion of tree models in a recent study reaches an AUPRC of about 0.67 on a public benchmark with 3.5 % fraud "
          f"{c('cfa')}. The results therefore show that the pipeline works end to end; they do not predict real-world detection rates. The anonymised features V1 to V22 are essentially noise apart from five shifted ones (and a small amount-linked offset in V1), and the interface labels V3, V14 and V17 as history, location variance and spending pattern only as friendly names."),
        H2("3.2 Quantum-inspired, not quantum"),
        P(f"The base paper's third trainer ran on quantum hardware {c('base')}. Here it is a classical simulation, and the annealing sampler is simplified: both samplers compute the hidden field from the mean visible vector of the batch and tile a single averaged model sample over the batch, "
          "and each epoch uses a 3,000-row subsample with 10 sweeps and 16 reads. Training times of a few seconds therefore do not reproduce, and say nothing about, the hours reported in the paper; the interface shows the paper's times in a separate column for that reason."),
        H2("3.3 Optimistic epoch selection"),
        P(f"The comparison view and the dashboard report each model at its best epoch, chosen on the same test split that scores it. That choice is optimistic. The best-epoch F1 of the shipped PCD model is {v['pe_f1']} (epoch {v['pe_ep']}), but the saved model is the final epoch, with F1 {v['f_pcd']}. "
          "This report uses final-epoch figures as the primary numbers and shows best-epoch values only where it says so."),
        H2("3.4 Pipeline order"),
        P("Undersampling and feature selection run on the whole sample before the train-test split, and the scaler is fitted on all rows. Test rows therefore influence which features are kept and how they are scaled. With a balanced synthetic file the effect is small, but it is a leak that a real study would remove."),
        H2("3.5 Unstable and badly placed classical model"),
        P(f"The PCD trainer is unstable: over five seeds its final-epoch F1 is {v['seed_pcd']}, and the shipped model flags nearly every transaction at the 0.5 threshold (accuracy {v['acc_pcd']}, recall {v['rec_pcd']}, {v['fp_pcd']} false positives among {v['n_test'] - v['n_fraud_test']} legitimate test rows) although its ROC-AUC is {F.f3(v['pcd']['roc_auc'])}. "
          "The ensemble averages it with the other two models, so a badly placed member still moves the mean."),
        H2("3.6 Bulk-route defect"),
        P(f"The bulk route (`predict_batch`) calls the fitted scaler on only the selected numeric columns ({F.SERVING['selected_numeric_features']} of the {F.SERVING['scaler_features']} it was fitted on). scikit-learn raises an error, a bare `except: pass` swallows it, and the models receive unscaled values. "
          f"On a fresh balanced batch of {F.SERVING['fresh_rows']:,} rows accuracy is {v['acc_srv']} as served against {v['acc_scaled']} when scaled ({v['fp_srv']} false positives against {v['fp_scaled']}). The bundled sample file of {v['batch_rows']} rows ({v['batch_true']} fraud) is flagged {v['batch_flag']} times as served and {v['batch_scaled']} times when scaled. "
          "The single-check route is not affected. The defect is documented and measured but was not fixed, so the bulk screenshot shows the behaviour of the code as shipped."),
        H2("3.7 Imbalance behaviour"),
        P(f"The models were trained and evaluated on balanced data. At {v['fr_rate']} fraud, an RBM trained on undersampled data keeps a precision of {_p(v['gr_u']['precision']['mean'], 2)} but finds only {_p(v['gr_u']['recall']['mean'], 2)} of the fraud, and the three baselines trained on undersampled data produce hundreds of false alarms per 7,800 transactions. "
          "A deployment would need cost-aware thresholds chosen on a realistic stream."),
        H2("3.8 Engineering limits"),
        B("No authentication, no HTTPS, open cross-origin access and the Flask development server (with debug mode on in `app.py`).",
          f"Only a read-only smoke test of the API ({v['smoke']} checks) exists; there is no unit-test suite and no regression test for the scaling defect.",
          "In-memory state: training from the Lab overwrites the shipped model files, and regenerating the dataset empties the in-memory models.",
          "The batch route rewrites `data/batch_predictions.csv` on every call, so concurrent users would overwrite each other's downloads.",
          "The risk label for a probability of exactly zero is undefined in the batch route because `pd.cut` excludes the lower edge."),
        H2("3.9 What the limitations mean for the reader"),
        P("The limitations do not affect all claims equally. The statements that hold regardless of the data are the structural ones: that the pipeline runs end to end, that the three trainers behave differently from each other and from ordinary baselines on the same split, "
          "that accuracy misleads at low fraud rates, and that a swallowed exception in the serving path changes the answers a user sees. The statements that depend on the data are the absolute values: an F1 near 94 % for the ensemble, near 96 to 97 % for the baselines, and precision near 0.95 at one percent fraud. "
          "These describe an easy synthetic problem and should not be quoted as expected performance on card transactions."),
        TAB("Which claims each limitation affects", ["Limitation", "Claims affected", "Claims not affected"],
            [["Synthetic data", "All absolute metrics; comparison with the base paper", "Relative behaviour of trainers; effect of resampling; the serving defect"],
             ["Quantum-inspired sampler", "Any statement about quantum training or its time", "PCD results; the structure of the classifier"],
             ["Best-epoch display", "Dashboard and comparison-screen F1 values", "Final-epoch figures used in this report"],
             ["Split after selection", "Small optimism in all test metrics", "Ordering of models; baseline comparison on the same split"],
             ["Scaling defect", "Everything shown on the Verify and Bulk screens", "Offline metrics, which use scaled inputs"],
             ["No real-world test", "Any claim of fitness for payments", "The engineering findings"]],
            widths=[1.6, 2.5, 2.2], align=["l", "l", "l"], size=9.5),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, so no figure is given for them:"),
        B("Precision and recall on real card transactions, and any result at the scale of the base paper (145 million transactions).",
          "Behaviour under concept drift, delayed labels or changing fraud tactics.",
          "Throughput and latency under concurrent load; latency was measured for one client at a time.",
          "Behaviour on hardware other than the single Windows PC used here, and on a production web server.",
          "Any run on quantum hardware or on a physical annealer; the training times reported in the base paper were not reproduced.",
          "Usability: no user study was run with analysts or merchants.",
          "Cost-weighted performance: the cost of a missed fraud against a false alarm is not known for this prototype.",
          "The effect of a scaling fix on the interface; the defect was measured offline and the product code was left unchanged."),
    ]


def walkthrough_blocks():
    v = _v()
    return [
        P("Four short walkthroughs show how the central pieces work. Excerpts are copied from the repository in the state in which the results were measured."),
        H2("3.1 Preprocessing: from raw rows to the 18-feature matrix"),
        P("`full_pipeline` encodes the two categorical columns, z-scores the 24 numeric columns, drops one column of any pair correlated above 0.95 (none were dropped here), undersamples to equal class sizes and keeps the top-k features of a random-forest ranking before the stratified split. "
          "The scaler is returned so that the API can reuse it, and that is where the later defect arises."),
        CODE(src("backend/preprocessing.py", 110, 150), 8),
        H2("3.2 The classifier: a training step and the prediction rule"),
        P("The visible units are the 18 standardised features, the label is a two-unit one-hot layer, and the hidden units are binary. A persistent-contrastive-divergence step compares the data statistics (positive phase) with the statistics of a persistent Gibbs chain (negative phase) and forms the gradients of the weight matrices `W` (visible-hidden) and `U` (label-hidden) and the three bias vectors."),
        CODE(src("backend/rbm_classifier.py", 82, 107), 8),
        P("Prediction does not sample. It computes the free energy of the input under each of the two label hypotheses and takes a softmax over their negatives, so the fraud probability is a smooth function of the weights. The visible bias term is the linear approximation noted in the comment, "
          "which is one reason the raw probabilities of the classical model are poorly calibrated."),
        CODE(src("backend/rbm_classifier.py", 148, 172), 8),
        H2("3.3 The simplified annealing sampler"),
        P("The annealing and quantum-inspired samplers replace the Gibbs chain in the negative phase. Both start from random hidden and label samples, run a short schedule and average the result. The listing shows the core of the annealing loop. Note that the hidden field is computed from `v_avg`, the mean of the mini-batch, "
          "not from each row, and that the model expectation is then tiled over the whole batch; this is a large simplification of the path-integral sampling the base paper describes."),
        CODE(src("backend/samplers.py", 41, 66), 8),
        P("The quantum-inspired variant uses the same structure but adds a tunnelling term: with probability proportional to a transverse-field strength that decays over the sweeps, a hidden unit is reset at random instead of following the Boltzmann probability."),
        CODE(src("backend/samplers.py", 107, 120), 8),
        H2("3.4 The bulk route and the swallowed scaler error"),
        P(f"Both prediction routes wrap the scaler call in a bare `except`. The single-check route builds one row with all 24 numeric columns, so the scaler works and the very first excerpt below is harmless. "
          f"The bulk route first narrows the frame to the 18 model columns and only then calls the scaler, which was fitted on all 24 numeric columns, so scikit-learn raises because the columns do not match and the bare `except` discards the error. "
          f"Because nothing is logged, the models silently receive unscaled amounts and times for every uploaded file. Measured effect on a fresh batch: accuracy {v['acc_srv']} as served against {v['acc_scaled']} when the scaler is applied correctly."),
        CODE(src("backend/app.py", 337, 345), 8),
        CODE(src("backend/app.py", 417, 423), 8),
        P("The repair is small: transform with all of `scaler.feature_names_in_` before selecting `columns`, and add a regression test that compares served probabilities with offline probabilities. That change was left out of this report's scope on purpose so that the measured behaviour matches the screenshots."),
    ]


def decision_blocks():
    return [
        P("The table lists the main implementation decisions with the reason for each and what it costs. Most follow the base paper; several were made for speed on a CPU."),
        TAB("Implementation decisions, reasons and trade-offs",
            ["Decision", "Reason", "Trade-off"],
            [["NumPy RBM instead of the Julia package", "Runs anywhere Python runs; code can be read and tested without Julia or cloud access", "Slower per step and written for clarity; fewer features than a research package"],
             ["Quantum sampler simulated classically", "No quantum hardware is available to the team", "The result is quantum-inspired only; no hardware effects are tested"],
             ["Annealing on batch mean and 3,000-row subsample", "Keeps an epoch under a few seconds on a CPU", "A crude approximation of the sampling in the paper; unstable QS and PCD results"],
             ["Manual undersampling by default", "The base paper found SMOTE and Tomek links worse on extreme imbalance; it keeps only real rows", "Throws away most legitimate rows when fraud is rare"],
             ["Eighteen features by random-forest importance", "The paper filters by CatBoost importance to keep the model small; CatBoost is optional here", "Selection before the split leaks a little test information"],
             ["Z-score scaling of numeric columns", "Gaussian visible units expect standardised inputs", "The serving path must repeat it exactly; it currently does not"],
             ["Mean of three probabilities as the ensemble", "Smooths the single-model instability and gives one risk score", "A poorly calibrated member (PCD) pulls the mean"],
             ["Risk bands at 0.4 and 0.7", "Gives three actions: approve, challenge with 3-D Secure, decline", "Not tuned on costs or validation data"],
             ["Flask with plain routes and in-memory store", "Smallest possible API for a prototype", "No auth, no persistence, development server"],
             ["React and Vite front end with a Vite proxy to port 8304", "Fast to iterate; one codebase for all screens", "Needs Node.js to build and run"],
             ["CSV, pickle and JSON files instead of a database", "Matches the offline, file-based workflow of the base paper", "No concurrent writers, no history of predictions"],
             ["Final-epoch metrics as the primary result", "Avoids choosing the epoch on the test split", "Lower than the best-epoch values shown in the interface"]],
            widths=[1.9, 2.4, 2.0], align=["l", "l", "l"], size=9.5),
    ]


# ------------------------------------------------------------------ chapter 9 / 10
def conclusion_blocks():
    v = _v()
    blocks = [
        H2("9.1 Summary of the work"),
        P(f"This project set out to build and measure a credit card fraud detector based on the quantum-assisted restricted Boltzmann machine of the base paper {c('base')}. We implemented the Gaussian-Bernoulli RBM classifier in NumPy with three trainers, built the preprocessing pipeline the paper describes, "
          f"wrapped the models in a Flask API with {F.N_ENDPOINTS} routes and a React interface, and measured everything on a synthetic, balanced file of {v['n_rows']} transactions. The quantum trainer is a classical simulation, so the system is quantum-inspired, not quantum."),
        P(f"On the {v['n_test']:,}-row held-out split the ensemble reaches accuracy {v['acc_e']}, precision {v['p_e']}, recall {v['r_e']}, F1 {v['f_e']} and ROC-AUC {v['auc']}. The annealing and quantum-inspired models reach F1 {v['f_sas']} and {v['f_qs']}. "
          f"The classical PCD model, at its shipped state, flags nearly every transaction (accuracy {v['acc_pcd']}, recall {v['rec_pcd']}). A single check takes a median {v['lat']} ms and a 20-row batch {v['lat_b']} ms."),
        P(f"Beyond the models, the project delivers the pieces that make them usable and checkable: preprocessing and training code that can be rerun, a retraining lab in the interface, bulk screening with an exportable result, analytics over the whole file, "
          f"an experiment script that regenerates every metric in this report, and a read-only smoke test of the API ({v['smoke']} checks pass). A full measurement run, including five seeds and a low-fraud variant, finishes in minutes on one CPU."),
        H2("9.2 Objectives against outcomes"),
        TAB("The six objectives and what was achieved",
            ["#", "Objective", "Outcome", "Status"],
            [["1", "Acquire a benchmark dataset and quantify the imbalance", f"No public benchmark was used. A synthetic file of {v['n_rows']} rows (50/50) was generated and a {v['fr_rate']}-fraud variant was built to quantify the effect of imbalance", "Partly met"],
             ["2", "Preprocessing: scaling, feature selection, stratified split", "One-hot, z-score, correlation filter, importance-based top-18 selection and a stratified 80/20 split", "Met (selection before the split)"],
             ["3", "Balance with SMOTE and compare with random undersampling", f"Compared in `scripts/run_experiments.py` on the {v['fr_rate']} variant (XGBoost precision is {_p(v['xg_s']['precision']['mean'], 2)} with SMOTE and {_p(v['xg_u']['precision']['mean'], 2)} with undersampling); the product supports SMOTE and Tomek links in the Lab", "Met in the experiment script"],
             ["4", "Train Logistic Regression, Random Forest and XGBoost", f"Trained on the same split (F1 {v['f_lr']}, {v['f_rf']}, {v['f_xg']}); they are not part of the shipped application, which serves the RBM models", "Met as baselines"],
             ["5", "Evaluate with precision, recall, F1 and ROC-AUC", "All four metrics, confusion matrices, a threshold sweep, five seeds and PR-AUC at low fraud", "Met"],
             ["6", "Deploy the best model behind an interface", f"The interface and API work ({v['smoke']} smoke checks pass), but the batch route skips scaling, and the deployed models are not the best models measured", "Met with a defect"]],
            widths=[0.3, 2.0, 3.0, 1.0], align=["c", "l", "l", "l"], size=9.5),
        H2("9.3 Key findings"),
        N(f"On this synthetic data, ordinary classifiers are better than the RBM. Logistic regression, random forest and XGBoost reach F1 {v['f_lr']}, {v['f_rf']} and {v['f_xg']}; the best RBM ensemble reaches {v['f_e']}. The data are easy, so this does not say what would happen on real data.",
          f"The three trainers differ in reliability more than in best score. SAS is stable (F1 {v['seed_sas']} over five seeds), QS is less so ({v['seed_qs']}), and PCD is unstable ({v['seed_pcd']}).",
          f"Ranking quality and decision quality are separate. All three models have ROC-AUC near {v['auc']}, but at 0.5 the PCD model is almost useless; the threshold, not the model, is the problem.",
          f"Imbalance strategy matters more than the model. At {v['fr_rate']} fraud, random undersampling drops the precision of all three baselines to between {_p(min(v['lr_u']['precision']['mean'], v['rf_u']['precision']['mean'], v['xg_u']['precision']['mean']), 2)} and {_p(max(v['lr_u']['precision']['mean'], v['rf_u']['precision']['mean'], v['xg_u']['precision']['mean']), 2)}, while no resampling keeps precision high and recall of {_p(min(v['lr_n']['recall']['mean'], v['rf_n']['recall']['mean'], v['xg_n']['recall']['mean']), 2)} to {_p(max(v['lr_n']['recall']['mean'], v['rf_n']['recall']['mean'], v['xg_n']['recall']['mean']), 2)}.",
          f"Silent failure is the main engineering risk. A swallowed exception in the batch route reduced accuracy from {v['acc_scaled']} to {v['acc_srv']} without any visible error.",
          f"The base paper's training times (hours) were not reproduced: with a simplified sampler an epoch takes well under a second."),
        P("Read together, the findings say that the base paper's recipe works as a classifier on easy data but does not, in this reimplementation, beat the standard tools, is fragile in its classical form, and is only as good as the code around it. "
          "None of this contradicts the base paper, which used real data, a far larger scale and quantum hardware. It does show that a student-scale rebuild must be checked against baselines and against its own serving code before any claim is made."),
        H2("9.4 Comparison with the base paper"),
        P(f"The base paper reports F1 of {F.BASE_TABLE['PCD'][3]} %, {F.BASE_TABLE['SAS'][3]} % and {F.BASE_TABLE['QS'][3]} % for PCD, SAS and QS on real data {c('base')}. Our final-epoch F1 values are {v['f_pcd']}, {v['f_sas']} and {v['f_qs']} on synthetic data. "
          f"The two sets of numbers cannot be compared directly: the data, the epoch count, the hyper-parameter search and the samplers all differ, and on our synthetic data even logistic regression reaches F1 {v['f_lr']}. What can be said is qualitative. In both studies simulated annealing is the strongest trainer and classical PCD the weakest. "
          f"Unlike the paper, our quantum-inspired sampler is about as good as the annealing sampler (F1 {v['f_qs']} against {v['f_sas']}), but it is less stable across seeds ({v['seed_qs']} against {v['seed_sas']}). "
          "We did not reproduce the paper's training times, because the samplers here are simplified and run on a CPU, and we make no claim about quantum hardware."),
        H2("9.5 Practical applications"),
        B("A teaching and demonstration tool for how restricted Boltzmann machines classify, how samplers change training, and why accuracy misleads on imbalanced data.",
          "A starting point for a risk-operations screening screen: single check, bulk file screening, analytics and model views are already wired to an API.",
          "A template for auditing a model service: the experiment script shows how to compare shipped behaviour with offline behaviour."),
        P("For a reader who wants to reuse the work, the most portable parts are the evaluation script and the audit method rather than the models. The script shows how to compare a served model with an offline one, how to vary the imbalance of a stream, and how to report spread over seeds. "
          "The interface is a reasonable skeleton for a screening tool once its data source, scaling and security are replaced with production-grade parts."),
        H2("9.6 Lessons learned"),
        B("Evaluate against ordinary baselines early. The RBM looked strong until logistic regression, random forest and XGBoost were trained on the same split and scored higher.",
          "Never swallow exceptions. A single bare `except` hid a feature-scaling error for the whole life of the batch route; it was found only because served predictions were compared with offline ones.",
          "Report final-epoch results. Picking the best epoch on the test split flatters every model, and the interface's dashboard figures show how large the effect is.",
          "Report the spread, not only the mean. Five seeds turned one apparently usable PCD model into an unstable trainer.",
          "State what the data are. Synthetic data allow a complete, repeatable study, but every conclusion must carry that caveat."),
        H2("9.7 Known limitations"),
        P("We chose to document the defects we found rather than hide them or silently repair them, because the screenshots, the latency figures and the test counts in this report all describe the code as shipped; a repair would change them and would need the measurements to be repeated. "
          "That decision keeps the report consistent with the repository and leaves the repair as the first item of future work."),
        P("The conclusions rest on synthetic data, one split, one machine and a simulated quantum sampler. The serving defect, the optimistic best-epoch display, the pre-split selection, the lack of authentication and the lack of a regression test are all documented in Chapter 8 and in the limitations document. "
          "Until the defect is fixed and the models are checked on real data, SecurePay AI should be treated as a prototype and not as a payment control."),
    ]
    blocks = _drop(blocks, starts=("Beyond the models", "Read together", "For a reader who wants", "We chose to document"), h2_drop=("9.6 Lessons",))
    if F.REPORT:
        blocks = [("h2", "9.6 Known limitations") if (b[0] == "h2" and b[1].startswith("9.7")) else b for b in blocks]
    return blocks


def future_blocks():
    v = _v()
    blocks = [
        H2("10.1 Improvements to the existing system"),
        N(f"**Fix the scaling defect and add a regression test.** Transform with all columns of `scaler.feature_names_in_` before selecting features, remove the bare `except`, and compare served probabilities with offline ones in a test that fails if they differ (served accuracy is {v['acc_srv']} today).",
          "**Choose the threshold on validation data.** Split the data three ways, pick the operating point on the validation part for the cost of a miss against a false alarm, and calibrate the PCD output (for example with isotonic regression).",
          "**Remove the evaluation leaks.** Split first, then scale, resample and select features on the training part only, and report final-epoch or validation-selected figures only.",
          "**Make the training reproducible and stable.** Search the hyper-parameters, average several seeds or use early stopping on a validation split, and report the spread."),
        P(f"Fixing the scaling defect is the single most valuable change, and its effect is already measured offline: with the scaler applied, ensemble accuracy on a fresh batch is {v['acc_scaled']} and false positives fall from {v['fp_srv']} to {v['fp_scaled']}. "
          "A regression test would send the bundled sample file through the running API and through the offline pipeline and assert that the two probability vectors agree within a tolerance; because it compares by column name, it would also catch a future change of feature order."),
        P(f"The threshold work needs care. In the sweep with steps of 0.05 the ensemble gives F1 {F.pct(v['sweep'][0.5]['f1'])} at 0.5 but precision {F.pct(v['sweep'][0.6]['precision'])} with recall only {F.pct(v['sweep'][0.6]['recall'])} at 0.6, and the PCD model flags everything up to 0.5 and nothing from 0.6, "
          "so its probabilities are bunched in a very narrow band. A finer search on a validation split, or a monotone calibration such as isotonic regression, is needed before any threshold can be called tuned."),
        P("These four items are listed in order of priority. The first removes a known defect, the second and third make the reported figures trustworthy, and the fourth makes them repeatable. Together they would turn the prototype into a system whose numbers can be defended."),
        H2("10.2 Additional features"),
        B("Real-data pilot with a partner's anonymised transactions, with a held-out time period instead of a random split.",
          f"A gradient-boosting champion model beside the RBMs: XGBoost reaches F1 {v['f_xg']} here and trains in a fraction of a second, so it is the obvious reference for any RBM claim.",
          "Cost-sensitive decisions and an alert budget, so the three actions reflect money and analyst capacity rather than fixed 0.4 and 0.7 cut-offs.",
          "Explanations for each decision (feature contributions for the single check), and storage of every prediction for audit.",
          "A model-monitoring screen with drift statistics and a scheduled retraining job."),
        P("Of these, the gradient-boosting champion and the cost-sensitive decision layer matter most. The first gives a fair yardstick for every other model; the second turns a probability into an action in a way a business can reason about, for example by flagging the highest-risk transactions up to a daily review budget of analysts' time."),
        P("Explanations deserve a concrete design. For an RBM classifier the free-energy difference between the fraud and legitimate hypotheses can be split into per-feature contributions, so the single-check screen could show which of the 18 inputs pushed the score up. "
          "Storing every prediction with its inputs, model version and later label is also the precondition for monitoring and retraining."),
        H2("10.3 Scalability and deployment"),
        B("Replace the Flask development server with a production server behind HTTPS, with authentication and role-based access (analyst and administrator).",
          "Containerise the API and the web build with Docker, read configuration from the environment and move model files to versioned storage.",
          "Keep predictions and model versions in a database instead of CSV and pickle files, and make the batch route write per-request files.",
          f"Vectorise scoring for batches (it already is) and load-test with concurrent clients; the measured median of {v['lat']} ms per check is for one client."),
        P("A realistic target deployment is a containerised API behind a reverse proxy with HTTPS, a managed relational database for predictions, labels and model versions, a scheduled job that retrains and evaluates a candidate model on the latest labelled period, and a promotion step that replaces the serving model only when the candidate beats it on a held-out later period. "
          "The present models are small matrix products, so a single process is plausibly enough for a prototype, but throughput under load was not measured and would depend on feature construction and I/O."),
        P(f"One open question in the present results can be tested cheaply. The classical trainer uses batches of 512 rows, so about 13 updates per epoch on 6,400 training rows, while the annealing trainers use batches of 32 over a 3,000-row subsample, about 94 updates per epoch. "
          f"The instability of PCD (F1 {v['seed_pcd']} over five seeds) may therefore come from too few updates under a decaying learning rate rather than from the sampler. We have not tested this; a sweep over batch size and learning rate would settle it."),
        P("An evaluation protocol for any later study should be fixed in advance: a time-ordered split so that the test period follows the training period, scaling and resampling fitted on the training part only, thresholds chosen on a validation period, "
          "and results reported as precision at a fixed alert budget, recall at a fixed false-positive rate and AUPRC, with the spread over several seeds. Such a protocol makes the numbers comparable with the base paper's successors and with the literature on real card data."),
        H2("10.4 Further research"),
        B("Replace the simplified samplers with a faithful path-integral simulated-annealing sampler, and obtain cloud access to a quantum annealer to test whether the effects reported in the base paper appear on real hardware.",
          "Study the Gaussian-Bernoulli RBM with learned variances and with a binary expansion of the visible units, as the paper's QUBO formulation requires.",
          "Compare the RBM classifier with a deep belief network, as the paper proposes as future work, and with tabular deep models.",
          f"Evaluate on public benchmarks with realistic imbalance, reporting AUPRC and cost curves as recommended for rare-event problems {c('saito', 'davis')}."),
        H2("10.5 Suggested roadmap"),
        TAB("Roadmap from prototype to pilot", ["Phase", "Work", "Evidence of success"],
            [["1. Repair", "Fix scaling, remove bare exceptions, add the regression test, split before selecting features", "Served and offline probabilities agree; test passes in continuous integration"],
             ["2. Re-measure", "Rerun `scripts/run_experiments.py` with validation-selected thresholds and final-epoch reporting; add the cost-sensitive layer", "Updated tables in the report; a stated cost assumption"],
             ["3. Harden", "Authentication, HTTPS, production server, containers, stored predictions", "Security checklist passed; deployment from a clean machine"],
             ["4. Pilot", "Score a partner's anonymised, time-ordered transactions; compare RBM, XGBoost and rules at a fixed alert budget", "Precision at the budget and recall measured on real data"]],
            widths=[1.0, 3.2, 2.1], align=["l", "l", "l"], size=9.5),
    ]
    return _drop(blocks, starts=("A regression test would send", "The threshold work needs care", "These four items", "Of these, the gradient-boosting", "Explanations deserve", "A realistic target deployment", "One open question", "An evaluation protocol"))


def chapter9_blocks():
    return [H1("9. CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("10. FUTURE SCOPE")] + future_blocks()
