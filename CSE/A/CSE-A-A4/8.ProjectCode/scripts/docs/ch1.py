"""Chapter 1: Introduction."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, N, P, TAB
from .refs import cite


def _full():
    ens, sas, qs, pcd = F.SAVED["ensemble"], F.SAVED["sa"], F.SAVED["qa"], F.SAVED["classical"]
    bb = F.BASE_BAL
    imb_none = F.imb_row("Logistic Regression", "none")
    imb_us = F.imb_row("Logistic Regression", "undersample")
    base = cite("base")
    sv_a, sv_s = F.SERVING["as_served_no_scaling"]["ensemble"], F.SERVING["with_scaling"]["ensemble"]
    lat = F.LATENCY["predict_single_fraud_example"]["median_ms"]
    n_total, n_fraud = F.DATASET["rows"], F.DATASET["fraud"]
    test_n = F.SPLIT["test"][0]
    train_n = F.SPLIT["train"][0]

    return [
        H1("1. INTRODUCTION"),
        P("This chapter introduces the domain of the project, the motivation for building SecurePay AI, the problem it addresses, the objectives set for it, the scope that was "
          "actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain and Background"),
        P("A credit card payment passes through several parties: the cardholder, the merchant, the acquiring bank and the issuing bank. Each of them can lose money when a card is used "
          "without the holder's consent, and each of them must decide, within the time of a single payment, whether to approve the transaction, ask the cardholder for extra proof "
          "or decline it. Card fraud is therefore both a financial problem and a real-time decision problem. The decision is taken for every payment, almost all payments are genuine, "
          "and a wrong decision in either direction has a price: a missed fraud is a direct loss, while a blocked genuine payment costs the bank a customer's goodwill and an analyst's time."),
        P("Two approaches have dominated practice. The first is the rule engine, in which analysts write conditions such as a high amount, a card that is not present, a country that "
          "differs from the holder's, or an unusual hour. Rules are transparent and fast, but they are written after a fraud pattern has been seen, they must be maintained by hand, "
          "and a fraudster who probes them can learn where the thresholds lie. The second approach is supervised machine learning, in which a classifier learns the pattern "
          f"from labelled history. Comparative studies on real card data generally find that nonlinear ensembles are stronger than linear models {cite('bhatt')}, and boosted trees "
          f"remain hard baselines on tabular transaction data {cite('xgb')}."),
        P("The central difficulty of the learning approach is class imbalance. Genuine transactions vastly outnumber fraudulent ones: the real dataset behind the base paper holds about "
          f"145 million transactions of which only about 19 thousand are fraud {base}, a fraud rate near 0.013 %. A classifier trained naively on such data can reach an accuracy above "
          f"99.9 % by predicting every transaction as genuine and still detect no fraud at all. For this reason accuracy is a poor yardstick, and the literature recommends precision, recall, "
          f"F1 and precision-recall analysis {cite('saito')}, {cite('hegarcia')}. Resampling methods such as SMOTE {cite('smote')}, Tomek links {cite('tomek')} and random undersampling "
          f"are used to rebalance the training data, but they have their own pitfalls, which the base paper reports from experience and which this project measures (Chapter 8)."),
        P(f"The base paper chosen for this batch, {F.BASE_SHORT} {base}, attacks the problem with a Gaussian-Bernoulli restricted Boltzmann machine classifier (GRBMC) trained in three ways: "
          "classical persistent contrastive divergence (PCD), simulated-annealing sampling (SAS) and quantum sampling (QS) on a D-Wave annealer. Its data is a private dataset of a Brazilian "
          "payment company, so the work cannot be reproduced directly. This project takes the same model family and the same three training ideas, runs them on an ordinary computer "
          "with a classical simulation of the quantum sampler, and wraps them in a screening application that an analyst can use."),
        P("Four terms are used throughout the report. A *transaction* is one row of the dataset with an amount, a merchant category, a channel, two binary indicators (card present, country "
          "matches the card) and 22 anonymised numeric features. A *fraud probability* is the number between 0 and 1 produced by a model for a transaction. A *risk band* is the action "
          f"attached to that probability: below {F.RISK_BANDS[0] * 100:.0f} % approve, from {F.RISK_BANDS[0] * 100:.0f} % to {F.RISK_BANDS[1] * 100:.0f} % challenge with an extra check, above "
          f"{F.RISK_BANDS[1] * 100:.0f} % decline and alert. The *ensemble* is the mean of the probabilities of the three trained models."),

        H2("1.2 Motivation"),
        P("Three observations motivate the project. First, published studies explore individual classifiers and sampling methods separately; what a team that wants to deploy a fraud "
          "model needs is a compared and tuned pipeline, measured on recall and F1 rather than accuracy. This is the gap recorded in the batch literature survey."),
        P(f"Second, the quantum-assisted result of the base paper is attractive but out of reach: it depends on a proprietary dataset and, for its best figures, on hours of simulator "
          f"or cloud quantum time {base}. The motivating question for this project is therefore practical: how much of the method survives when it is rebuilt on a laptop with a classical "
          "simulation of the sampler, and how does it compare with the plain classifiers that every data-science team already knows?"),
        P("Third, a model alone does not protect anybody. A trained classifier becomes useful only when a transaction can be submitted, a score and a decision come back immediately, "
          "and a file of many transactions can be screened at once. The team therefore decided to deliver the model behind an interface, and to measure the interface as carefully "
          "as the model; as Chapter 7 shows, that measurement found a defect that a model-only study would have missed."),

        H2("1.3 Problem Statement"),
        P("The problem statement approved for the batch is reproduced below."),
        B(*lit.PROBLEM_STATEMENT),
        P(f"Stated as one sentence: given a stream of card transactions in which fraud is rare, produce a probability of fraud for each transaction, map it to approve, challenge or decline, "
          "and do so quickly enough to sit inside a payment flow."),

        H2("1.4 Need for the System"),
        P(f"{lit.NEED} Four needs follow from the problem statement."),
        N("**Imbalance handling.** The training procedure must not let the majority class dominate, and the evaluation must report the metrics that matter for the minority class.",
          "**Recall first, precision second.** Missing a fraud costs more than reviewing a false alarm, so the operating point should favour recall while keeping false alarms tolerable. "
          "The threshold or the risk band must therefore be adjustable and its effect visible.",
          "**Adaptability.** Fraud patterns change, so the system must be retrainable on new data without code changes.",
          "**Usability.** The decision must be available to a non-programmer through an interface, with a risk score, a risk band and a per-model breakdown that make the decision explainable."),

        H2("1.5 Objectives"),
        P("The six objectives set in the batch proposal are listed below. They are quoted unchanged, and the table that follows states, in one line each, what was done about them. "
          "Chapter 8 measures the outcomes in detail and says plainly where an objective was only partly met."),
        N(*lit.OBJECTIVES),
        TAB("How each objective was addressed (details in Chapter 8)", ["No.", "Objective (short)", "Status", "What was done"],
            [["1", "Benchmark dataset and imbalance", "Partly met", f"A synthetic {n_total:,}-row file (50 % fraud) imitating the base paper's balanced set; a 1 % fraud variant for the imbalance study. No public benchmark was used."],
             ["2", "Preprocessing", "Met", "One-hot encoding, z-scoring, correlation filter, importance-based selection of 18 features and a stratified 80/20 split."],
             ["3", "SMOTE versus undersampling", "Met in scripts", "Compared with class weights and no resampling in `scripts/run_experiments.py`; the interface uses undersampling."],
             ["4", "LR, RF and XGBoost", "Met in scripts", "Trained on the same split in the experiment script; the product itself ships the three RBM classifiers."],
             ["5", "Precision, recall, F1, ROC-AUC", "Met", "Reported for every model, with confusion matrices, threshold sweeps and a five-seed study."],
             ["6", "Deploy behind an interface", "Met, with a defect", f"Flask API with {F.N_ENDPOINTS} routes and a React interface; scaling is skipped in the serving path (Chapter 7)."]],
            widths=[0.4, 1.7, 1.0, 3.2], align=["c", "l", "l", "l"], size=10),

        H2("1.6 Scope"),
        P("**Inside the scope.** Generation and exploration of a synthetic card-transaction dataset; the preprocessing pipeline; the GRBMC with its three training methods; an ensemble and a "
          "three-band decision rule; a REST API; a web interface with a dashboard, a single-transaction check, CSV bulk screening, analytics, a model comparison view and a retraining lab; "
          "scripts that measure accuracy, precision, recall, F1, ROC-AUC, latency and the effect of imbalance; and the documentation set."),
        P("**Outside the scope.** Real cardholder data, any quantum hardware, streaming ingestion from a payment switch, user accounts and authentication, a database, regulatory compliance "
          "(for example PCI DSS), model monitoring in production, and explanation of individual decisions beyond the per-model probabilities. These are listed again as limitations in Section 1.8 "
          "and as future work in Chapter 10."),

        H2("1.7 Contributions"),
        N("**A working end-to-end application.** SecurePay AI scores a single transaction in a median of "
          f"{lat:.0f} ms through the API, screens a CSV file in one request and lets the analyst retrain the models from the browser.",
          "**A classical reconstruction of the base paper's three-trainer comparison.** The GRBMC, the PCD gradient, an annealing sampler and a quantum-inspired sampler are implemented in "
          f"plain numpy, trained in seconds on {n_total:,} synthetic rows, and compared on a held-out split of {test_n:,} transactions. The ensemble reaches an F1 of {F.pct(ens['f1'])} "
          f"(SAS {F.pct(sas['f1'])}, QS {F.pct(qs['f1'])}).",
          "**An honest measurement of what the method does and does not do.** The PCD model scores a ROC-AUC of "
          f"{F.f3(pcd['roc_auc'])} but, at the default threshold, flags almost every transaction (accuracy {F.pct(pcd['accuracy'])}); its F1 over five seeds is {F.seed_cell('classical', 'f1')}, "
          f"against {F.seed_cell('sa', 'f1')} for SAS. Logistic regression, random forest and XGBoost reach an F1 of {F.pct(bb['Logistic Regression']['f1'])}, {F.pct(bb['Random Forest']['f1'])} "
          f"and {F.pct(bb['XGBoost']['f1'])} on the same split, so on this synthetic data the simple baselines are stronger.",
          "**An imbalance study.** With fraud reduced to 1 % of the stream, logistic regression without resampling reaches a precision of "
          f"{imb_none['precision']['mean']:.2f}, while random undersampling drops it to {imb_us['precision']['mean']:.2f} with {imb_us['mean_fp']:.0f} false alarms per {F.IMB['test_rows_per_seed']:,} transactions.",
          "**An audit of the serving path.** Feature scaling is silently skipped in the prediction routes; on a fresh balanced batch of "
          f"{F.SERVING['fresh_rows']:,} transactions the ensemble's accuracy falls from {F.pct(sv_s['accuracy'])} to {F.pct(sv_a['accuracy'])}. The defect is documented and quantified rather than hidden.",
          "**Reproducibility.** Every number in this documentation set is produced by scripts in the project (`scripts/run_experiments.py`, `scripts/measure_latency.py`, `scripts/smoke_test.py`) and written to `experiments/`."),

        H2("1.8 Limitations and Assumptions"),
        P("The following limitations apply to every result in this report. They are repeated, with their evidence, in Chapter 8 and in the separate scope and limitations document."),
        B(f"**Synthetic data.** The {n_total:,} transactions were generated by a script that shifts a handful of features for fraud. The classes are far easier to separate than real fraud, so "
          "the absolute figures say little about performance on real traffic, and they cannot be compared with the base paper's figures obtained on 145 million real transactions.",
          "**Quantum-inspired, not quantum.** The quantum sampler is a classical simulation of a transverse-field tunnelling step. No quantum annealer was used, and no quantum advantage is claimed.",
          f"**Small training scale.** The product trains on an {8000:,}-row sample ({train_n:,} training rows). The SAS and QS trainers use a 3,000-row subsample per epoch and a short annealing schedule, "
          "so they are heavily simplified relative to the base paper's hours-long runs.",
          "**Optimistic epoch selection.** The per-epoch history that the interface shows is evaluated on the test split, so its best epoch is chosen on test data. The primary numbers in this report use the final epoch.",
          "**Mild leakage.** Feature selection and undersampling are performed before the train-test split; with a balanced synthetic file the effect is small, but it is not zero.",
          "**No operational validation.** There is no authentication, no database, no monitoring, no pytest suite (only a 20-check smoke test) and no study with real analysts."),
        P("The assumptions are equally plain. We assume that the anonymised columns V1 to V22 stand for numeric behavioural features, that labels are correct, that the 50/50 balance of the "
          "training file is a deliberate design choice imitating the base paper and not a statement about real fraud rates, and that the application runs on a single local machine."),

        H2("1.9 Organisation of the Report"),
        P("The remaining chapters follow the order in which the project was carried out."),
        B("**Chapter 2, Literature Survey,** analyses the base paper in depth, groups the related work by theme and states the research gap.",
          "**Chapter 3, Feasibility Study,** judges the project technically, economically, operationally and against the schedule.",
          "**Chapter 4, System Requirements and Analysis,** describes the existing system, the proposed system and the functional, non-functional, hardware and software requirements.",
          "**Chapter 5, System Design,** gives the architecture, workflow, data-flow diagrams, UML diagrams, storage design, module design and user-interface design.",
          "**Chapter 6, Methodology and Software Implementation,** explains the dataset, preprocessing, the GRBMC and its training methods, the mathematics, the API and how to run the system.",
          "**Chapter 7, System Testing,** reports unit, integration, functional, security, performance and edge-case testing and the limits of what was tested.",
          "**Chapter 8, Results and Output Screens,** presents the measured results, the comparison with the base paper and baselines, the output screens, failure analysis and objectives against outcomes.",
          "**Chapters 9 and 10** give the conclusion and the future scope, followed by the references and three appendices (important code, installation and user guide, additional screens)."),
    ]


_DROP = (
    "This chapter introduces the domain",
    "Two approaches have dominated practice",
    "Four terms are used throughout",
    "Third, a model alone does not protect",
    "The base paper chosen for this batch",
    "The problem statement approved for the batch",
    "Stated as one sentence",
    "The six objectives set in the batch proposal",
    "The following limitations apply to every result",
    "The assumptions are equally plain",
)

_ORG = ("The remaining chapters follow the order of the work: Chapter 2 surveys the literature and the base paper; Chapter 3 judges feasibility; Chapter 4 sets out the requirements; "
        "Chapter 5 gives the design; Chapter 6 explains the methodology and implementation; Chapter 7 reports testing; Chapter 8 presents the results and output screens; Chapters 9 and 10 give the "
        "conclusion and future scope. References and three appendices (important code, installation and user guide, additional screens) follow.")


def _compact(out):
    """Report variant: drop the weakest prose, merge the chapter map into one paragraph, shrink the table."""
    res, skip_org = [], False
    for b in out:
        if b[0] == "p" and b[1].startswith(_DROP):
            if b[1].startswith("The assumptions are equally plain"):
                res.append(P("**Assumptions.** The anonymised columns V1 to V22 stand for numeric behavioural features, labels are correct, the 50/50 balance of the training file is a design choice imitating "
                             "the base paper (not a statement about real fraud rates), and the application runs on one local machine."))
            continue
        if b[0] == "h2" and b[1].startswith("1.9"):
            res += [b, P(_ORG)]
            skip_org = True
            continue
        if skip_org:
            continue
        if b[0] == "tab":
            b = ("tab", b[1], b[2], b[3], b[4], b[5], 9.5)
        res.append(b)
    return res


def blocks():
    out = _full()
    return _compact(out) if F.REPORT else out
