"""
Shared content for Review 1 and the literature chapters: survey table, existing system, limitations, gaps,
objectives (the six from 6.OBJECTIVES&PROBLEM STATEMENT.docx), problem statement, approach, expected outcomes.
Figures quoted from papers were read from those papers (the three PDFs in this batch) or from the publisher page.
"""

from .refs import cite

OBJECTIVES = [
    "Acquire a benchmark credit card transaction dataset and quantify the degree of class imbalance.",
    "Apply preprocessing including scaling, feature selection and stratified train-test splitting.",
    "Balance the training data using SMOTE and compare it against random undersampling.",
    "Train Logistic Regression, Random Forest and XGBoost classifiers on the balanced data.",
    "Evaluate using precision, recall, F1-score and ROC-AUC rather than accuracy alone.",
    "Deploy the best model behind an interface that flags a transaction as genuine or fraudulent.",
]

PROBLEM_STATEMENT = [
    "Fraudulent transactions are rare, so standard classifiers reach high accuracy by predicting everything as genuine.",
    "Rule-based systems raise many false alarms and block legitimate customers.",
    "Fraud patterns change continuously, so a fixed rule set becomes obsolete quickly.",
    "Missing a fraud costs far more than reviewing a false alarm, yet most models treat both errors equally.",
]
NEED = ("A machine learning system that handles severe class imbalance and maximises fraud recall while keeping false alarms acceptable.")

# (work, year, approach, data / reported result, limitation)
LIT_TABLE = [
    ("Neto et al. (base paper)", "2026", "Gaussian RBM classifier trained with classical PCD, simulated-annealing sampling and D-Wave quantum sampling",
     "Real Stone data, 145 M transactions, about 19 thousand fraud, balanced to 39 thousand; F1 83 / 88 / 84 % (PCD / SAS / QS)", "One proprietary dataset; no public baselines; hours of training; no deployable interface"),
    ("Aburbeian and Ashqar", "2023", "Random forest with SMOTE and hyper-parameter tuning",
     "94,682 online transactions; accuracy about 98 %, F1 about 98 %", "Resampled data scored; accuracy-led comparison on a small public set"),
    ("Han and Wu", "2026", "Combinatorial fusion of seven classifiers, validation-stage subset and rule selection",
     "IEEE-CIS, 590,540 transactions, 3.5 % fraud; AUC 0.9405, AUPRC 0.6699, F1 0.6373", "Gain over best single model is small; CTGAN augmentation hurt"),
    ("Shi", "2024", "ANN compared with XGBoost on imbalanced card data",
     "Both about 99.96 % accuracy; XGBoost higher F1 on the fraud class", "Accuracy is uninformative at this imbalance; no deployment"),
    ("Bhattacharyya et al.", "2011", "Logistic regression, SVM and random forest compared",
     "Nonlinear ensemble methods generally stronger than linear ones on card transactions (as summarised by Han and Wu)", "Older study; no deployment or imbalance-strategy comparison"),
    ("Dal Pozzolo et al.", "2018", "Realistic fraud modelling: delayed labels, concept drift, alert precision",
     "Discusses sampling bias, delayed labels and changing fraud patterns in real card streams", "Addresses data issues, not model training cost or a usable interface"),
    ("Carcillo et al.", "2021", "Unsupervised outlier scores added to supervised classifiers",
     "Unsupervised anomaly scores and supervised classifiers complement each other in large-scale systems", "Not a single compact model; no deployable interface"),
]

SURVEY_ITEMS = [
    "Fraud Detection in Credit Card Transactions Using Quantum-Assisted Restricted Boltzmann Machines (IEEE Access, 2026) - base paper",
    "Research on Credit Card Fraud Detection Based on Pyspark (2025)",
    "Enhancing E-Commerce Security: A Novel Approach to Credit Card Fraud Detection (2025)",
    "Credit Card Fraud Detection (IJRPR, 2025)",
    "Credit Card Fraud Detection Based on ANN and XGBoost (2024)",
]

SUPPORT_EVIDENCE = [
    f"The base paper's real dataset holds 145 million transactions of which about 19 thousand are fraud, roughly 0.013 % {cite('base')}.",
    f"Random forest with SMOTE reaches about 98 % accuracy on a 94,682-transaction set, but accuracy alone hides minority-class errors {cite('rfpaper')}.",
    f"On IEEE-CIS (3.5 % fraud) the best fusion of tree models gives AUPRC 0.6699 and F1 0.6373, far below accuracy figures {cite('cfa')}.",
    f"ANN and XGBoost both score about 99.96 % accuracy, so only fraud-class F1 separates them {cite('shi')}.",
    f"SMOTE and Tomek links performed poorly when the minority class was extremely small, so the base paper fell back to manual undersampling {cite('base')}.",
]

EXISTING_SYSTEM = [
    "Rule engines flag a transaction when fixed conditions fire: high amount, card not present, foreign country, odd hour.",
    "Rules are written by analysts, so they lag behind new fraud patterns and are learned and bypassed by fraudsters.",
    "Every rule hit goes to manual review or an automatic decline, which blocks genuine customers and costs analyst time.",
    "Standard classifiers trained on raw data score high accuracy by predicting nearly everything as genuine.",
    "Published machine-learning studies compare individual classifiers or sampling methods separately and rarely deliver a deployable scoring interface.",
]

LIMITATIONS_EXISTING = [
    "Static rules: they cannot adapt to shifting fraud behaviour and are easy to probe.",
    "Accuracy-led evaluation: at 0.013 % to 3.5 % fraud a model that never flags anything looks excellent.",
    "Resampling pitfalls: SMOTE trains on synthetic minority points and undersampling can leave very little data.",
    "Hard-to-reproduce results: the base paper's data is proprietary and its best training took hours on a simulator or quantum cloud.",
    "No operational layer: most studies stop at a notebook, with no interface that flags a live transaction.",
]

GAPS = [
    "Individual classifiers and sampling methods are studied separately; a compared, tuned pipeline is missing.",
    "Evaluation is often accuracy-led; recall, precision and F1 on the fraud class are what an analyst needs.",
    "The base paper's quantum-assisted RBM is shown only on private data and without a usable interface.",
    "Quantum hardware is out of reach for most teams; whether a classical simulation of the sampler is enough is unanswered.",
    "Few works measure how the same pipeline behaves when fraud falls from 50 % to about 1 % of the stream.",
    "Deployable live scoring with a risk band and an explanation of the decision is rarely provided.",
]

PROPOSED_APPROACH = [
    "Prepare: one-hot encode merchant and channel, z-score the numeric columns, drop highly correlated columns, undersample to 50/50 and keep the 18 most important features.",
    "Model: a Gaussian-Bernoulli RBM classifier with visible, hidden and label layers, trained three ways - classical PCD, simulated-annealing sampling and a quantum-inspired sampler that simulates a transverse field.",
    "Decide: average the three fraud probabilities; below 40 % approve, 40 to 70 % challenge, above 70 % decline and alert.",
    "Serve: a Flask API with 16 routes and a React interface for single checks, CSV bulk screening, analytics, model comparison and a retraining lab.",
    "Measure: precision, recall, F1 and ROC-AUC on a held-out split, against Logistic Regression, Random Forest and XGBoost, across seeds, thresholds and a 1 % fraud variant.",
]

EXPECTED_OUTCOMES = [
    "A working screening application that returns a risk score and a decision for one transaction in well under a second.",
    "An honest comparison of the three RBM trainers on one dataset, including their instability and training cost.",
    "Evidence on imbalance: what SMOTE, class weights and undersampling do when fraud is 1 % of the stream.",
    "Measured results with stated limits: synthetic data, a quantum-inspired simulator and no real-world validation.",
    "Reusable scripts that regenerate every number in the documentation.",
]
