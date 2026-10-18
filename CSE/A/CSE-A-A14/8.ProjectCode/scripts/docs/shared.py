"""Text shared by the chapter documents, the full report, the decks and the paper (objectives, problem statement, literature table)."""

from . import facts as F
from .refs import NUM

OBJECTIVES = [
    "Acquire a telecom customer dataset and perform exploratory analysis of churn behaviour.",
    "Clean the data, encode categorical fields and address class imbalance between churned and retained customers.",
    "Train and compare Logistic Regression, Decision Tree and Random Forest classifiers.",
    "Evaluate using accuracy, precision, recall, F1-score and ROC-AUC.",
    "Identify the features that contribute most strongly to churn risk.",
    "Present at-risk customers and their risk drivers through a retention dashboard.",
]

PROBLEM_POINTS = [
    "Churn is detected after the customer has left, when retention is no longer possible.",
    "Retention offers are applied uniformly rather than targeted at genuinely at-risk customers.",
    "A churn score without a reason gives the retention team nothing to act upon.",
    "Imbalanced data causes models to under-predict the minority churn class.",
]
NEED = "A churn prediction system that identifies at-risk customers early and explains the factors driving each prediction."

PROBLEM_STATEMENT = (
    "Given a table of telecom customer records (tenure, contract type, monthly charges, internet service, payment method and related fields), "
    "predict for each customer the probability of leaving, group customers into risk bands, show which attributes drive each prediction, "
    "and turn the result into a concrete retention action, all in an application that a retention analyst can run without writing code. "
    "The predictor must cope with the minority-class imbalance of churn data and must be evaluated with metrics that are not fooled by it."
)

INTRO_POINTS = [
    "Acquiring a new telecom customer costs several times more than retaining an existing one.",
    "Churn is usually noticed only after the customer has already left.",
    "Customer records contain early signals: tenure, contract type, monthly charges and service usage.",
    "Machine learning can learn these patterns and estimate churn risk before the customer leaves.",
    "Ensemble classifiers handle mixed categorical and numerical telecom data well.",
    "Explaining why a customer is at risk turns a prediction into an actionable retention step.",
]

# Literature table: Work | Approach | Data | Reported result | Limitation (only what was read on the paper's own page)
LIT_TABLE = [
    ["Oprea and Bara, 2026 [%d] (base paper)" % NUM["oprea"],
     "Unified perturbation-based explainer (RNP, FA, IM, AP) compared with SHAP and LIME; LR, SVC, RF, balanced RF, CatBoost, XGBoost, LightGBM",
     "Telco churn, 7,043 customers, 30% test (2,113)",
     "Recall up to 0.9077 (CatBoost); Spearman 0.8125 with SHAP; runtime 18.5 s vs SHAP 289.4 s",
     "One dataset; recall as the single objective; CRM integration proposed, not built"],
    ["Sikri et al., 2024 [%d]" % NUM["sikri"],
     "Ratio-based data balancing as a pre-processing step; single and ensemble classifiers",
     "Imbalanced telecom churn data (details not extracted)",
     "Ensembles beat single models; best XGBoost at a 75:25 ratio (accuracy, precision, recall, F-score)",
     "Abstract-level reading only; no per-customer explanation described"],
    ["El Attar and El-Hajj, 2026 [%d]" % NUM["elattar"],
     "Eight models incl. XGBoost, LightGBM, soft-voting ensemble; SHAP feature analysis",
     "IBM Telco, 7,043 customers, 80/20 split (1,409 test)",
     "XGBoost accuracy 0.84, AUC 0.932; Logistic Regression 0.78 and 0.864",
     "Single dataset; authors note SHAP is not causal"],
    ["Rasool et al., 2025 [%d]" % NUM["rasool"],
     "Stacking ensemble of tree models with SHAP",
     "Kaggle Churn in Telecoms, 3,333 customers",
     "Accuracy 94.75%, recall 73.20%, F1 80.23%",
     "No temporal modelling; telecom data only"],
    ["Lundberg and Lee, 2017 [%d]" % NUM["lundberg"],
     "SHAP: additive Shapley-value attributions for any model",
     "Method paper",
     "Unifies several attribution methods",
     "Costly on large data: 289.4 s in the experiment of [%d]" % NUM["oprea"]],
    ["Ribeiro et al., 2016 [%d]" % NUM["ribeiro"],
     "LIME: local surrogate model around one prediction",
     "Method paper",
     "Faithful local explanation of any classifier",
     "Moderate fidelity and lower consistency than SHAP in [%d]" % NUM["oprea"]],
    ["Slack et al., 2020 [%d]" % NUM["slack"],
     "Adversarial attacks on LIME and SHAP",
     "Method paper",
     "Shows perturbation-based explainers can be fooled",
     "Perturbation-based explanations need cautious reading"],
]
LIT_HEADER = ["Work", "Approach", "Data", "Reported result", "Limitation"]

GAP = ("The surveyed work compares classifiers on churn datasets and, in the base paper, concentrates on how to explain them quickly. "
       "The gap this project addresses is pairing accurate prediction with per-customer explanation so that retention action can be targeted rather than generic: "
       "a working application that scores every customer, shows the drivers of each score and maps them to concrete actions.")

NOT_LOCATED = [
    "Explainable Machine Learning for Telecom Customer Churn Prediction and Actionable Retention Strategies (listed as 2026, Applied Artificial Intelligence Research)",
    "A Novel SHAP-Guided Bayesian Optimization Method for Telecom Customer Churn Prediction and Retention (listed as 2025, IEEE EESPE)",
    "Enhanced Customer Retention: Deep Learning-Based Churn Prediction for Telecom Industry (listed as 2025, IJRASET)",
]
