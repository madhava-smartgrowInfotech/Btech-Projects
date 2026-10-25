"""Chapter 2: Literature Survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import KEYS, REFS, UNVERIFIED, cite


def _base_table():
    names = {"PCD": "Classical PCD", "SAS": "Simulated-annealing sampling", "QS": "Quantum sampling (D-Wave)"}
    rows = []
    for k, (a, p, r, f1, t) in F.BASE_TABLE.items():
        rows.append([names[k], f"{a} %", f"{p} %", f"{r} %", f"{f1} %", t])
    return rows


def _full():
    base = cite("base")
    ens, sas, qs, pcd = F.SAVED["ensemble"], F.SAVED["sa"], F.SAVED["qa"], F.SAVED["classical"]
    bb = F.BASE_BAL
    unv = ", ".join(f"[{KEYS[k]}]" for k in sorted(UNVERIFIED, key=lambda k: KEYS[k]))

    lit_rows = [[w, y, a, d, l] for (w, y, a, d, l) in lit.LIT_TABLE]
    mine = ["This project", "2026", "GRBMC with PCD, SAS and a quantum-inspired sampler, ensembled; Flask and React interface",
            f"Synthetic 39,000 rows; ensemble F1 {F.pct(ens['f1'])}, SAS {F.pct(sas['f1'])}, QS {F.pct(qs['f1'])}, PCD {F.pct(pcd['f1'])} (accuracy {F.pct(pcd['accuracy'])})",
            "Synthetic data; simulated sampler; baselines are stronger; batch route skips scaling"]
    lit_rows.append(mine)

    return [
        H1("2. LITERATURE SURVEY"),
        P("This chapter surveys the work on which the project rests. It starts with the base paper, which is analysed in detail, and then groups related work by theme: rule-based and machine-learning "
          "detection, ensembles and boosting, imbalance handling, evaluation, and restricted Boltzmann machines with annealing and quantum-assisted training. It ends with the datasets and algorithms "
          "used in the literature, the strengths and limitations of that work, and the research gap that SecurePay AI addresses."),

        H2("2.1 Overview"),
        P("The batch literature survey lists five works. The first is the base paper " + base + ". The second to fourth are a 2025 paper on credit card fraud detection with PySpark, a 2025 paper "
          "on e-commerce security and card fraud, and a 2025 article titled simply *Credit Card Fraud Detection*; the fifth is a 2024 study that compares an artificial neural network with XGBoost " + cite("shi") + ". "
          "The batch survey gives only titles, years and sources for them. We were able to verify the base paper (read in full) and the ANN and XGBoost study (publisher page), but not the other three items "
          f"(references {unv}); they are therefore listed in the reference list with a note and are not used as evidence anywhere in this report."),
        P(f"To make the survey stronger than a list of titles, we added papers that were read in full or whose citation details are standard: the earlier random-forest paper that the batch had used as its first base paper {cite('rfpaper')}, "
          f"a 2026 study on fusing tree models for imbalanced card data {cite('cfa')}, and the established literature on fraud modelling {cite('dp18')}, {cite('carcillo')}, {cite('bhatt')}, "
          f"imbalanced learning {cite('hegarcia')}, {cite('smote')}, {cite('dp15')} and restricted Boltzmann machines {cite('hinton06')}, {cite('cd')}, {cite('pcd')}."),

        H2("2.2 Base Paper Analysis"),
        H3("2.2.1 Problem and data"),
        P(f"The base paper {base}, published in IEEE Access in 2026, asks whether restricted Boltzmann machines (RBMs) whose training is assisted by quantum annealing can detect fraud better than "
          "their classically trained counterparts. Its dataset was provided by a Brazilian payment company and covers about 145 million transactions collected over three months, of which about 19 thousand "
          "are fraud. The data is anonymised under Brazilian data-protection law, so neither cardholder information nor balances are disclosed."),
        H3("2.2.2 Method"),
        P(f"The model is a Gaussian-Bernoulli RBM classifier (GRBMC): a visible layer of continuous features, a layer of binary hidden units and a label layer that is attached to the hidden units like an extension of the "
          f"visible layer {cite('larochelle')}, {cite('liao')}. Training minimises the negative log-likelihood by stochastic gradient descent; the gradient has a data term that is easy to compute and a model term "
          f"that requires samples from the model's own distribution. Three ways of obtaining those samples are compared: (i) classical persistent contrastive divergence (PCD) with Gibbs sampling {cite('pcd')}, {cite('cd')}; "
          f"(ii) simulated-annealing-assisted training (SAS), in which the energy function is written as a quadratic unconstrained binary optimisation (QUBO) problem and sampled with D-Wave's path-integral simulator {cite('anneal')}; and "
          f"(iii) quantum sampling (QS) on real D-Wave hardware, where repeated anneals give samples of the Boltzmann distribution {cite('adachi')}, {cite('ajagekar')}. Because the visible units are Gaussian, a binary expansion "
          "is needed to write the model as a QUBO, which increases the number of variables and is the reason the authors restrict the number of features."),
        P(f"The preprocessing follows advice from the payment company's anti-fraud team: one-hot encoding of categorical fields (the best of several encodings tried), z-score normalisation of numeric fields, removal of the most "
          f"correlated features and removal of the least important features according to a CatBoost model {cite('catboost')}. Four balancing strategies were tried. SMOTE {cite('smote')} made the model learn mostly from synthetic "
          f"points, Tomek links {cite('tomek')} reduced the data to a few hundred rows, and the two combinations suffered the same problems, so the authors used manual random undersampling: all fraud rows plus an equal number of random genuine rows, "
          "giving a shuffled 39-thousand-row set with a 50/50 split and an 80/20 train-test split."),
        P("A grid search found 200 hidden units and batches of 512 best for classical training, with an exponentially decaying learning rate; 65 hidden units and batches of 32 for the annealing methods; and a smooth "
          "decay with a floor, LR = eta0 exp(-lambda (t - 1)) + eta_f, for the quantum method, whose learning rates had to be much smaller to avoid divergence. All models were trained for 50 epochs."),
        H3("2.2.3 Reported results"),
        P("Table 2.1 reproduces the base paper's Table 1, which gives the metrics at the optimum epoch of each 50-epoch training run, selected by F1 and measured on the test split."),
        TAB("Base paper results (its Table 1, read from the paper)", ["Method", "Accuracy", "Precision", "Recall", "F1", "Training time"], _base_table(),
            widths=[2.1, 0.8, 0.85, 0.7, 0.6, 1.2], align=["l", "c", "c", "c", "c", "c"], size=10),
        P("The authors conclude that the annealing-assisted models, which use only 65 hidden units and small batches, match or slightly exceed the classical model, which needs 200 hidden units and large batches, and that "
          "performance and run time are in a trade-off: the classical model trained in two to three minutes, the simulated-annealing model in about four hours (a figure the authors attribute partly to Python-from-Julia overhead on "
          "Windows) and the quantum model in about 1 hour 50 minutes. They state that whether the advantage is universal or specific to their data is an open question, and name quantum kernels for support vector machines, "
          "the quantum approximate optimisation algorithm and deep belief networks as future work."),
        H3("2.2.4 Strengths"),
        B("A real, very large dataset provided by a payment company, with preprocessing agreed with its fraud team.",
          "A clear comparison of three training procedures on identical data, epochs and metrics, with the hyper-parameters tuned separately for each.",
          "An honest account of what failed: SMOTE, Tomek links and their combinations, oscillating annealing curves, diverging learning rates on quantum samples.",
          "The first-class use of F1, precision and recall instead of accuracy alone."),
        H3("2.2.5 Weaknesses and open points"),
        B("The data is private, so the work cannot be repeated by others and no public baseline is available.",
          "No non-RBM classifier is trained on the same data, so the paper cannot say whether an RBM is a good choice for fraud at all; the strongest baselines for tabular data are boosted trees " + cite("xgb") + ".",
          "Each result is a single training run and the reported epoch is the best one on the test split, which favours the models whose curves oscillate most.",
          "The differences between methods are small (F1 of 83, 88 and 84 %), and no confidence interval or seed study is given.",
          "The quantum runs were limited by access to the hardware, and some epochs of the quantum run could not be evaluated."),
        H3("2.2.6 What this project adopts and what it changes"),
        TAB("Base paper compared with this project", ["Aspect", "Base paper", "This project"],
            [["Data", "Real, 145 M transactions, 19 k fraud, balanced to 39 k", f"Synthetic, {F.DATASET['rows']:,} rows generated by `synthetic_data.py`, 50/50"],
             ["Model", "GRBMC", "GRBMC (same layers, same 200/65 hidden units, same batch sizes)"],
             ["Trainers", "PCD, simulated annealing, real quantum annealer", "PCD, a simplified annealing sampler, a quantum-inspired classical simulation"],
             ["Preprocessing", "One-hot, z-score, correlation filter, CatBoost importance, manual undersampling", "Same steps; random-forest importance is used when CatBoost is not installed"],
             ["Epochs and time", "50 epochs; 2 min to 4 h", f"20 epochs; {min(h['elapsed_sec'] for h in F.HIST.values()):.1f} to {max(h['elapsed_sec'] for h in F.HIST.values()):.1f} s per trainer on the shipped models"],
             ["Baselines", "None", "Logistic regression, random forest, XGBoost, a hand-written rule"],
             ["Seeds and imbalance", "Single run; 50/50 only", "Five seeds; a 1 % fraud variant"],
             ["Delivery", "Notebook-level study", "Flask API (16 routes) and React interface with bulk screening"]],
            widths=[1.2, 2.5, 2.6], align=["l", "l", "l"], size=10),
        P("The project therefore adopts the model, the preprocessing recipe and the hyper-parameters of the base paper, and changes the data, the sampling hardware, the scale and the evaluation. Because the data "
          "and the hardware differ, the numbers of the two works are never compared as if they measured the same thing."),

        H2("2.3 Related Work"),
        H3("2.3.1 Rule-based and learning-based detection"),
        P(f"Early card-fraud systems relied on expert rules. Learning-based detection replaced them as labelled data became available. Bhattacharyya et al. compared logistic regression, support vector machines and random forests "
          f"on real card data and found that nonlinear ensemble methods were generally stronger {cite('bhatt')}. Dal Pozzolo et al. describe the practical issues that separate fraud modelling from ordinary classification: "
          f"sampling bias, delayed labels and changing fraud patterns {cite('dp18')}. Carcillo et al. show that unsupervised outlier scores and supervised classifiers complement each other in large-scale systems {cite('carcillo')}. "
          "These studies agree that how a model fails matters as much as its overall accuracy, which is the stance taken in this project."),
        H3("2.3.2 Ensembles and boosting"),
        P(f"Tree ensembles are the usual strong baselines on tabular data. Random forests average many decorrelated trees {cite('breiman')}, and XGBoost fits trees sequentially to the residual errors with regularisation {cite('xgb')}. "
          f"Aburbeian and Ashqar combine SMOTE with a tuned random forest on a Kaggle set of 94,682 online transactions and report an accuracy of about 98 % and an F1 of about 98 % {cite('rfpaper')}; they note that earlier studies "
          f"often reported only accuracy. Shi compares an ANN with XGBoost on imbalanced card data and finds that both reach an accuracy of about 99.96 %, so that only the F1 on the fraud class separates them, in favour of XGBoost {cite('shi')}. "
          f"Han and Wu study 480 fusion configurations of seven classifiers on the IEEE-CIS benchmark (590,540 transactions, 3.5 % fraud) under a leakage-free 60/20/20 protocol; the best fusion of random forest, XGBoost and LightGBM "
          f"reaches an AUC-ROC of 0.9405, an AUPRC of 0.6699 and an F1 of 0.6373, with a gain over the best single model that is small but whose bootstrap interval excludes zero {cite('cfa')}. "
          "Their experiment with synthetic fraud generated by a GAN is a negative result: the augmentation degraded both the single models and the fusion. The practical message for this project is that the plain tree and linear baselines are "
          "strong and must be part of any fair comparison, which the base paper does not provide."),
        H3("2.3.3 Handling class imbalance"),
        P(f"He and Garcia survey learning from imbalanced data {cite('hegarcia')}, and Fernandez et al. give a book-length treatment {cite('fernandez')}. The main families are data-level methods (oversampling, undersampling and "
          f"their combinations), algorithm-level methods (class weights, cost-sensitive learning) and threshold moving. SMOTE interpolates between minority-class neighbours to create synthetic examples {cite('smote')}; "
          f"Tomek links remove majority points that form a pair with a minority point across the class boundary {cite('tomek')}; random undersampling discards majority points. Dal Pozzolo et al. show that undersampling "
          f"biases the posterior probabilities of a classifier and that the probabilities must be recalibrated if they are used as probabilities {cite('dp15')}. This explains, in hindsight, a result of our own imbalance study "
          f"(Chapter 8): after undersampling, every classifier's recall rises but its precision collapses on a stream with 1 % fraud. The imbalanced-learn library provides the resamplers used here {cite('imblearn')}."),
        H3("2.3.4 Evaluation metrics"),
        P(f"With a rare positive class, accuracy and ROC curves can look excellent while the model is of little use. Saito and Rehmsmeier show that the precision-recall plot is more informative than the ROC plot on imbalanced "
          f"data {cite('saito')}, and Davis and Goadrich relate the two curves formally {cite('davis')}. Fawcett's introduction to ROC analysis remains the standard reference for the ROC side {cite('fawcett')}, and Powers "
          f"discusses precision, recall, F-measure and their relatives, including their biases {cite('powers')}. This project reports precision, recall, F1 and ROC-AUC for every model, adds PR-AUC for the imbalance study "
          "and shows confusion matrices so that the two kinds of error can be counted."),
        H3("2.3.5 Restricted Boltzmann machines, annealing and quantum-assisted training"),
        P(f"An RBM is a two-layer energy-based model that learns a probability distribution over its inputs {cite('hinton06')}. Training needs samples from the model, which are obtained by Gibbs sampling; contrastive divergence runs "
          f"a short chain starting at the data {cite('cd')}, and persistent contrastive divergence keeps the chain alive between updates {cite('pcd')}. Hinton's practical guide collects the tricks that make RBM training work {cite('guide')}, "
          f"Fischer and Igel give a tutorial introduction {cite('fischer')}, and Larochelle et al. show how to turn an RBM into a classifier by adding a label layer {cite('larochelle')}. Gaussian-Bernoulli RBMs, which accept "
          f"continuous inputs, are known to be hard to train, and Liao et al. propose remedies {cite('liao')}."),
        P(f"Simulated annealing {cite('anneal')} explores an energy landscape by accepting uphill moves with a probability that falls as a temperature is lowered. Quantum annealing replaces thermal jumps by quantum tunnelling "
          f"through a transverse field. Adachi and Henderson applied a quantum annealer to the training of deep networks built from RBMs {cite('adachi')}, and Ajagekar and You used quantum-assisted deep learning for fault detection "
          f"in industrial processes {cite('ajagekar')}; the base paper follows the latter framework. All of this work needs either annealing hardware or a simulator, and the sampler quality is the weak point: the base paper reports "
          "oscillating metrics because the number of sweeps had to be limited. These observations motivate the project's choice to study a cheap classical stand-in, state plainly that it is only quantum-inspired, and measure how "
          "stable it is."),

        H3("2.3.6 From study to deployment"),
        P("Most of the work above ends with a table of metrics. Dal Pozzolo et al. are an exception in that they model the conditions of a live system: labels arrive late because a cardholder reports fraud days after the "
          f"event, fraud behaviour drifts, and analysts can examine only a limited number of alerts per day {cite('dp18')}. These conditions change what a good model is: a score that ranks transactions well is useful even when "
          "its probabilities are not calibrated, because the alert budget fixes the operating point. We keep this lesson in view when interpreting our own results. The classical RBM trained by PCD, for example, "
          f"ranks transactions well (ROC-AUC {F.f3(F.SAVED['classical']['roc_auc'])}) but, at the default threshold of 0.5, flags almost everything; a threshold chosen on a held-out set would repair it, which is why Chapter 8 includes a "
          "threshold sweep. The surveyed papers do not describe an interface, a serving path or its tests, which is where SecurePay AI adds the most practical content and also where it found its most serious defect (Chapter 7)."),

        H2("2.4 Datasets and Algorithms Used in the Literature"),
        TAB("Datasets in the surveyed work", ["Dataset", "Size and fraud rate", "Used by"],
            [["Private payment-company data (Brazil)", "145 M transactions, about 19 thousand fraud (about 0.013 %); balanced to 39 thousand", "Base paper " + base],
             ["Kaggle online-transaction set", "94,682 transactions; 20 features, partly PCA-masked", "Aburbeian and Ashqar " + cite("rfpaper")],
             ["IEEE-CIS Fraud Detection (Kaggle, 2019)", "590,540 transactions; 3.5 % fraud; 434 columns after merging", "Han and Wu " + cite("cfa")],
             ["Imbalanced card data (publisher page)", "Not stated in the abstract", "Shi " + cite("shi")],
             ["Synthetic file generated by this project", f"{F.DATASET['rows']:,} transactions, 50 % fraud; plus a 1 % fraud variant", "This project"]],
            widths=[2.0, 2.6, 1.7], align=["l", "l", "l"], size=10),
        TAB("Algorithms used in the surveyed work and in this project", ["Algorithm", "Role", "Where it appears"],
            [["Gaussian-Bernoulli RBM classifier", "Probabilistic classifier trained by sampling", "Base paper; this project's product"],
             ["PCD, simulated annealing, quantum sampling", "Ways to obtain the model-term samples", "Base paper; this project (simplified, classical)"],
             ["Logistic regression", "Linear baseline", "Bhattacharyya et al.; this project's experiments"],
             ["Random forest", "Bagged trees; importance ranking", "Aburbeian and Ashqar; Han and Wu; this project (importance filter and baseline)"],
             ["XGBoost", "Boosted trees", "Shi; Han and Wu; this project's experiments"],
             ["SMOTE, Tomek links, random undersampling", "Rebalancing", "Base paper; this project's experiments and pipeline"],
             ["CatBoost importance", "Feature selection", "Base paper; replaced by random-forest importance when CatBoost is absent"]],
            widths=[2.2, 2.0, 2.1], align=["l", "l", "l"], size=10),

        H2("2.5 Summary of the Surveyed Work"),
        TAB("Literature survey table", ["Work", "Year", "Approach", "Data and reported result", "Limitation"], lit_rows,
            widths=[1.2, 0.45, 1.6, 1.8, 1.45], align=["l", "c", "l", "l", "l"], size=9),
        P("The last row is this project, shown for orientation only: its figures come from synthetic data and are not comparable with the rows above it. "
          "The three unverified titles of the batch survey (Section 2.1) are not summarised."),

        H2("2.6 Strengths and Limitations of the Surveyed Work"),
        P("**Strengths.** The literature agrees on the correct problem framing (imbalance, cost asymmetry, drift), supplies strong and cheap baselines, and gives a toolbox of resampling and evaluation methods. "
          "The base paper adds a distinctive model family and an unusually candid account of failed balancing strategies."),
        P("**Limitations.** Accuracy-led reporting persists in the smaller studies; resampled data is sometimes scored; the strongest published RBM results rest on private data and on hardware or simulators that "
          "few teams can use; comparisons with plain baselines are missing in the base paper; and almost no study delivers a deployable interface. Reported differences between methods are often a few percentage points "
          "from a single run, so conclusions about their ranking are fragile."),

        H2("2.7 Research Gap"),
        P("From the survey we identify the following gaps, listed in the batch proposal and extended after reading the papers in full."),
        N(*lit.GAPS),
        TAB("How SecurePay AI addresses the gaps", ["Gap", "Response in this project"],
            [["1 Separate classifiers and samplers", "Single pipeline in which the RBM trainers, three baselines and four imbalance strategies are compared on the same split (Chapter 8)"],
             ["2 Accuracy-led evaluation", "Precision, recall, F1, ROC-AUC, confusion matrices, threshold sweeps and PR-AUC; recall is the headline for fraud"],
             ["3 Base-paper RBM only on private data", "Same model and hyper-parameters rebuilt on a public-code synthetic dataset so that anyone can repeat the experiments"],
             ["4 Quantum hardware out of reach", "Quantum-inspired classical sampler, with its instability measured over five seeds"],
             ["5 Behaviour at low fraud rates", "A 1 % fraud variant with no resampling, class weights, SMOTE and undersampling"],
             ["6 No deployable live scoring", f"Flask API and React interface with a risk band; median {F.LATENCY['predict_single_fraud_example']['median_ms']:.0f} ms per check; its defects are reported"]],
            widths=[2.1, 4.2], align=["l", "l"], size=10),
        P(f"In short, the research gap is a compared, tuned pipeline, evaluated on recall and F1 rather than accuracy and deployable for live scoring. The project fills it with an honest finding that is not the one "
          f"the base paper's direction suggests: on this synthetic data the three simple baselines (F1 {F.pct(bb['Logistic Regression']['f1'])}, {F.pct(bb['Random Forest']['f1'])} and {F.pct(bb['XGBoost']['f1'])}) are "
          f"stronger than the RBM ensemble (F1 {F.pct(ens['f1'])}), and the RBM's practical interest lies in its probabilistic structure and in the study of its training methods rather than in raw accuracy."),
    ]


_DROP = (
    "This chapter surveys the work on which the project rests",
    "To make the survey stronger than a list of titles",
    "A grid search found 200 hidden units",
    "Most of the work above ends with a table of metrics",
    "The last row is this project, shown for orientation only",
    "From the survey we identify the following gaps",
    "Simulated annealing [",
)
_DROP_H3 = ("2.3.6",)


def _compact(out):
    """Report variant: drop the weakest prose, the duplicated gap list and the 'study to deployment' subsection."""
    res, skipping = [], False
    for b in out:
        if b[0] in ("h2", "h3"):
            skipping = b[0] == "h3" and b[1].startswith(_DROP_H3)
        if skipping:
            continue
        if b[0] == "p" and b[1].startswith(_DROP):
            continue
        if b[0] == "p" and b[1].startswith("With a rare positive class, accuracy and ROC curves"):
            b = P(f"With a rare positive class, accuracy and ROC curves can look excellent while the model is of little use; the precision-recall plot is more informative {cite('saito')}, {cite('davis')}, "
                  f"ROC analysis is standard {cite('fawcett')}, and Powers discusses the biases of precision, recall and F-measure {cite('powers')}. This project reports precision, recall, F1 and ROC-AUC for every model, "
                  "PR-AUC for the imbalance study and confusion matrices.")
        if b[0] == "n" and b[1] and b[1][0] == lit.GAPS[0]:
            continue
        if b[0] == "tab":
            b = ("tab", b[1], b[2], b[3], b[4], b[5], min(b[6], 9.5) if b[6] > 9 else b[6])
        res.append(b)
    return res


def blocks():
    out = _full()
    return _compact(out) if F.REPORT else out
