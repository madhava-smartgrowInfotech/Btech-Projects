"""
Content shared by several documents (chapters, decks, paper). Written once so that every document
states the same objectives, scope, limitations, contributions and literature table.
Numbers come from facts.py (artifacts/*.json); never type a metric by hand elsewhere.
"""

from . import facts as F
from .refs import n

M = F.METRICS            # selected model (XGBoost), test split
BEST_LABEL = F.MODEL_LABEL[F.BEST]

# The six objectives exactly as recorded in 6.OBJECTIVES&PROBLEM STATEMENT.docx
OBJECTIVES = [
    "Collect a dataset combining demographic attributes with financial and transactional parameters.",
    "Preprocess the data, handle missing values and encode categorical demographic fields.",
    "Train models to classify financial profile and estimate credit or distress risk.",
    "Build a forecasting component that projects future financial position.",
    "Add an explainability layer showing which factors drove each assessment.",
    "Evaluate using accuracy, precision, recall and ROC-AUC, and deploy through a web interface.",
]

# Honest status of each objective (used in the results chapter, deck and paper)
OBJECTIVE_STATUS = [
    ("Met in part", f"UCI Adult / Census Income, {F.N_ROWS:,} individual records with age, education, occupation, location (native country), "
                    "and capital gains and losses. It has no transaction-level data, so the 'transactional parameters' part is not met."),
    ("Met", "'?' markers turned into missing values, median / 'Unknown' imputation and one-hot encoding inside each scikit-learn Pipeline, "
            "and 12 interpretable derived features."),
    ("Met in part", f"Four classifiers trained; {BEST_LABEL} selected. The target is income above 50K, mapped to Emerging / Developing / Established "
                    "profiles with Low / Moderate / High risk bands. It is not a credit-default or distress label."),
    ("Met in part", "Holt-Winters 12-month forecast with a 95% band is built and served, but on a documented synthetic Household Financial Conditions Index; "
                    "it does not forecast an individual's own finances."),
    ("Met", "SHAP global importance, live per-assessment SHAP contributions in plain language, and a labelled non-causal what-if comparison."),
    ("Met", f"Accuracy, precision, recall, F1 and ROC-AUC reported for all four models; the system is deployed as a Flask API with a React interface "
            f"on ports 8409 and 5409."),
]

SCOPE_IN = [
    "Classification of one individual's demographic and financial profile (12 inputs) into an Emerging, Developing or Established profile with a Low, Moderate or High risk band and a financial-strength score.",
    "The preprocessing and feature-engineering chain in `scripts/feature_engineering.py`, applied identically at training and prediction time through a scikit-learn Pipeline.",
    "Four candidate classifiers (Logistic Regression, Random Forest, Gradient Boosting, XGBoost) evaluated by stratified 80/20 split and 5-fold cross-validation, with the best selected by ROC-AUC.",
    "SHAP explainability: global importance charts at training time and live local contributions for every assessment, with plain-language sentences.",
    "A 12-month Holt-Winters forecast of an economic index with a 95% band, and a what-if comparison of a baseline and a changed scenario.",
    "A Flask JSON API (port 8409), the original server-rendered pages, a React front end (port 5409) with a sample login, a dashboard, performance views and a responsive light / dark interface.",
    "A reproducible training pipeline, an automated test suite (pytest), a smoke test and the documentation set.",
]

SCOPE_OUT = [
    "Credit decisions. The model predicts an income band from census-style attributes; it is not a credit score, a default or distress predictor, or a lending recommendation.",
    "Forecasting an individual's future finances. The forecast is of an aggregate economic index and is trained on a synthetic series.",
    "Real macroeconomic indicators (inflation, benchmark lending rates, GDP) named in the project abstract; they are not integrated.",
    "Transaction-level or bank data, income verification, identity checks and any personal-data storage.",
    "User accounts, real authentication, role management, audit logging and a relational database (the sample login is a browser-only demo gate).",
    "Fairness mitigation, causal inference, entity-grouped or temporal validation, and external validation on current data.",
    "Cloud deployment and horizontal scaling; the Docker files cover the original Flask pages only.",
]

ASSUMPTIONS = [
    "The 1994 US census extract (UCI Adult) is a usable stand-in for demographic and financial profiles; its income label is taken as ground truth.",
    "One row describes one person, so a random stratified split does not leak entities between training and test sets.",
    "Users enter values from the permitted option lists and ranges (age 16-100, hours 1-99, gains and losses 0-1,000,000).",
    "The census sampling weight `fnlwgt` has no meaning for a new user and is imputed with the training median at prediction time.",
    "The Household Financial Conditions Index used for forecasting is illustrative; its trend and seasonality are assumed to continue unchanged over the 12-month horizon.",
    "The system runs on a single local machine with Python 3.11 or newer and Node.js 18 or newer.",
]

LIMITATIONS = [
    "**Old, US-specific data.** The Adult extract describes 1994 US adults. Its income distribution, occupations and wage levels do not describe current populations, and the countries in the form map to a handful of census categories.",
    "**Income is not creditworthiness.** The target is income above 50K. The report therefore claims a financial-profile signal only; it makes no claim about repayment behaviour or distress.",
    "**Synthetic forecast series.** The forecast component is validated only against its own generator (back-test MAPE below 1%), which says nothing about accuracy on real economic data.",
    "**Sensitive attributes in the model.** Sex, race and marital status are inputs and marital status is the most important SHAP feature. No fairness audit or mitigation was performed, so the model may reproduce historical bias.",
    "**Recall of the positive class is modest.** At the default 0.5 threshold the selected model finds about two thirds of the people with income above 50K; the threshold analysis shows how this trades against precision.",
    "**Model selected on the test split.** The best model was chosen by test ROC-AUC, with no separate validation set, no hyperparameter search and no significance test; the cross-validation ranking agrees with the test ranking.",
    "**Extrapolation in what-if scenarios.** Large changes (for example investment gains of 80,000) move the score by close to 100 points because the training data are sparse there; scenario output is a model simulation, not a causal prediction.",
    "**Demo-grade security and storage.** The login is client-side only, no data is persisted, the session secret has a development default, and the Docker image serves the Flask pages only.",
    "**Not financial advice.** Outputs are informational and must not be used as the sole basis for any financial decision.",
]

CONTRIBUTIONS = [
    f"**From organisations to individuals.** The explainable machine-learning framework of the base paper {n('base')} (feature engineering, multi-model comparison, SHAP, validation) is carried over from hospital panel data to individual demographic and financial profiling on {F.N_ROWS:,} census records.",
    "**An end-to-end system, not only a model.** Validated form input, feature engineering, XGBoost prediction, profile and risk band, live SHAP explanation, what-if comparison, forecast and performance views are served through a Flask API and a React interface.",
    "**Leakage-safe, reproducible evaluation.** Imputation, encoding and scaling live inside each Pipeline; four models are compared on one stratified split plus 5-fold CV; every metric is written to JSON and re-derived by a script.",
    "**Explanations in plain language.** Per-assessment SHAP values become sentences, including a correct reading of one-hot features (the absence of a category), and the what-if screen is labelled as simulation, not causation.",
    "**A forecasting component with honest provenance.** A Holt-Winters 12-month forecast with a 95% band is built on a documented synthetic index and its limits are stated wherever it appears.",
    "**Evaluation beyond a single score.** Confusion matrices, a threshold sweep, calibration bins, observed income rates per profile band, API latency and automated test results are reported.",
]

# Rows: Work, Approach, Data, Reported result, Limitation   (only facts verified from the sources; see docs/lit_notes.md)
LIT_TABLE = [
    [f"Kim and Sun {n('base')} (base paper)", "Four-stage explainable ML: feature engineering, LR / RF / GB / XGBoost / MLP, SHAP, domain validation",
     "165 Korean hospitals, 825 hospital-year rows, 2019-2023", "XGBoost AUC 0.842 (hospital-level Group K-Fold); 0.780 on 2023 hold-out; Altman Z'' 0.680",
     "Organisations, not individuals; small panel; SHAP is associational"],
    [f"Abid {n('abid')}", "Five ML and four deep models forecasting CDS-implied default probability",
     "Sovereign credit data for Egypt, Morocco and Saudi Arabia", "Linear regression best; RNN and GRU competitive",
     "Three countries; sovereign risk, not individual profiles"],
    [f"Maurino {n('maurino')}", "Effect of missing values, noise, outliers and label errors on 10 credit-risk models (Pucktrick library)",
     "One open-source credit-risk dataset", "Some errors can raise F1 (up to 17% for specific models); noise and mislabelling generally hurt",
     "Binary task, one dataset; fairness not studied"],
    [f"Zhang et al. {n('zhang')}", "PrivacyCredit: privacy-preserving credit-risk learning with alternative data (vertical federated learning)",
     "Real credit data linked with alternative data", "Same performance as the insecure plaintext combination",
     "Needs partner data; no demographic explanation layer"],
    [f"Barboza et al. {n('barboza')}", "Comparison of ensembles with statistical models for bankruptcy prediction",
     "Listed firms", "Ensembles outperform traditional statistical models (as summarised in the base paper)",
     "Corporate setting"],
    [f"Bussmann et al. {n('bussmann')}", "Shapley values to explain credit-risk models", "SME lending data",
     "Explanations for credit decisions", "SME-level, not demographic profiling"],
    [f"Gramegna and Giudici {n('gramegna')}", "SHAP and LIME compared for discriminative power in credit risk", "Credit-risk data",
     "Evaluates explanation methods", "No end-to-end application"],
    [f"Grinsztajn et al. {n('grinsztajn')}", "Benchmark of tree-based models against deep learning on tabular data", "Many tabular datasets",
     "Tree-based models still outperform deep models on typical tabular data", "General benchmark, not finance-specific"],
]

RESEARCH_GAP = (
    "Explainable machine learning for financial distress has been developed for organisations and sovereigns, while work on individuals concentrates on accuracy "
    "and uses a narrow set of financial parameters. None of the surveyed works combines individual demographic profiling, a per-person explanation, a forecast "
    "of economic conditions and a usable web interface in one reproducible system. This project fills that gap on public data."
)
