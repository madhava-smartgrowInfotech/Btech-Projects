"""Chapters 9 and 10 (conclusion, future scope) and the text of the scope, novelty, contribution and implementation documents."""

import ast
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import cite
from .shared import OBJECTIVES


def func_src(rel, name):
    """Source text of a top-level function of a file under 8.ProjectCode (read from the real code)."""
    path = os.path.join(F.CODE, rel)
    text = open(path, encoding="utf8").read()
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node)
    raise KeyError((rel, name))


# --------------------------------------------------------------------------------------- conclusion
OUTCOMES = [
    ["1", "Acquire a dataset and explore churn behaviour", "Met, with a caveat", "A synthetic 1,000-customer data set with the Telco schema is generated (no real operator data); the Explore page and Section 8.2 show churn by contract, tenure, service and payment"],
    ["2", "Clean, encode and address class imbalance", "Met", "Duplicate removal, imputation, scaling, one-hot encoding; class weights and SMOTE; recall measured with and without handling (0.1887 against 0.6604 for Logistic Regression)"],
    ["3", "Train and compare Logistic Regression, Decision Tree and Random Forest", "Met", "All three trained and compared (plus Gradient Boosting and Histogram Gradient Boosting); Logistic Regression recommended on F1"],
    ["4", "Evaluate with accuracy, precision, recall, F1 and ROC-AUC", "Met", "All five metrics, confusion matrices, ROC and precision-recall curves, plus cross-validation and repeated splits"],
    ["5", "Identify the features that drive churn", "Met", "Coefficients and permutation importance: contract type, monthly charges, tenure and payment method lead. SHAP not exercised"],
    ["6", "Present at-risk customers and drivers through a dashboard", "Met", "Dashboard, risk bands, Customer 360, what-if, retention actions, batch scoring and monitoring pages"],
]


def conclusion_blocks():
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary of the Work"),
        P("This project set out to move customer-churn work from a table of classifier metrics to a tool a retention team can use. It built a complete pipeline and application: a data loader that profiles and validates a customer table, a preprocessing pipeline "
          "fitted on the training split only, three required and two optional classifiers with class-weight or SMOTE imbalance handling, an evaluation module with five metrics and the usual curves, a risk-banding scheme with editable thresholds, "
          "global and per-customer explanations, a what-if analysis, a transparent rule engine that turns drivers into retention suggestions, batch scoring and a drift check. These are delivered through two interfaces on one core: the original Streamlit application and the ChurnIQ "
          "web interface served by a FastAPI layer."),
        P(f"On the synthetic sample (1,000 customers, 26.4% churn) the best model by F1 is Logistic Regression: accuracy {F.LR['accuracy']:.3f}, precision {F.LR['precision']:.3f}, recall {F.LR['recall']:.3f}, F1 {F.LR['f1_score']:.3f} and ROC-AUC {F.LR['roc_auc']:.3f} on a 200-row test split. "
          f"Cross-validation and repeated splits show that Logistic Regression and Random Forest cannot be separated reliably (F1 {F.CV['Logistic Regression']['f1_score']['mean']:.3f} ± {F.CV['Logistic Regression']['f1_score']['std']:.3f} and {F.CV['Random Forest']['f1_score']['mean']:.3f} ± {F.CV['Random Forest']['f1_score']['std']:.3f} in 5-fold cross-validation). "
          "Ranking customers by predicted risk and contacting the top 20% reached 39.6% of the churners, a lift of about 2 over random contact."),
        H2("9.2 Objectives Revisited"),
        TAB("Outcome against the six objectives", ["No.", "Objective", "Outcome", "Evidence"], OUTCOMES, widths=[0.4, 1.8, 0.9, 2.9], align=["c", "l", "c", "l"], size=9),
        H2("9.3 Limitations"),
        P("The conclusions are limited in the following ways, which are discussed in full in the Scope and Limitations document:"),
        B("The data are synthetic. The metrics describe the pipeline on generated data and say nothing about accuracy on a real operator's customers.",
          "The test split has 200 rows and 53 churners. Cross-validation and repeated splits show spreads of 0.03 to 0.10 on several metrics, and a Random Forest result changes with the scikit-learn version.",
          "The ranking ability is moderate (ROC-AUC about 0.72, F1 about 0.46-0.51) and the probabilities are not calibrated (Brier score 0.213 against 0.195 for a constant predictor).",
          "SHAP was not installed, so no SHAP result is reported; the explanations are coefficient-times-value and permutation importance.",
          "The retention rules are heuristics written by the team. Their effect on real churn was not measured.",
          "There is no database, no multi-user support and no real authentication; the login is a demonstration.",
          "No user-acceptance study, load test or non-Chrome browser test was carried out."),
        H2("9.4 Concluding Remarks"),
        P(f"The project shows that an end-to-end churn workflow can be built from open-source parts, run on a desktop in seconds, and made inspectable at every step: the data are profiled, the model is chosen on a metric that is not fooled by imbalance, each score carries its drivers, and each suggestion carries its rule. "
          f"It follows the motivation of the base paper {cite('oprea')}, that churn predictions are most useful when they can be explained, and supplies the application layer the paper leaves open. "
          "Its numerical results are a demonstration on synthetic data; the next step, described in Chapter 10, is to repeat the evaluation on real customer records before any retention decision depends on it."),
    ]


FUTURE = [
    ("Validate on real data", "Repeat the experiments on real operator data or at least on the real public Telco file (7,043 rows), which the loader already supports after the pandas-3 fix. This would give metrics that can be compared with the base paper under a stated protocol, a much larger test set, and an honest answer to whether the synthetic-data conclusions hold."),
    ("Calibrate the probabilities", "Apply Platt scaling or isotonic regression on a validation split so that a score of 60 can be read as a chance of about 60%, and report reliability curves and the Brier score as part of the Evaluation page."),
    ("Add SHAP and the base paper's explainers", "Install and test the SHAP code path that already exists, compare it with the permutation and coefficient explanations, and implement LIME and a unified perturbation explainer in the manner of the base paper to compare fidelity, consistency and runtime on the same models."),
    ("Stronger models and tuning", "Add XGBoost, LightGBM and CatBoost, tune hyper-parameters by cross-validation, and keep Logistic Regression as the interpretable baseline. Evaluate on cross-validation first, given the noise of a single split."),
    ("Cost-sensitive decisions", "Let the analyst enter the cost of an offer and the value of a retained customer, choose the decision threshold that maximises expected profit, and show the expected return of contacting the top k%."),
    ("Measure the retention rules", "Run a controlled campaign (offer against no offer) on a sample of high-risk customers to estimate uplift, and refine or retire the rules according to measured effect."),
    ("Time and behaviour", "Use usage, complaint and billing histories over time (survival analysis or sequence features) so that churn can be predicted months ahead and not only from a snapshot."),
    ("Production foundations", "Replace the in-memory state by a database, add real accounts with roles and an audit log, store models with versions, and add scheduled batch scoring and statistical drift tests (population stability index, Kolmogorov-Smirnov)."),
    ("Integration", "Expose scores to a CRM through the API, and containerise the services for deployment."),
]


def future_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        P("The work leaves several directions open. They are ordered by how much they would change the value of the system."),
        N(*[f"**{t}.** {d}" for t, d in FUTURE]),
        P("The first three are the most important: they address the main weakness of this report (synthetic data), the main weakness of the scores (calibration) and the main gap against the base paper (explanation methods)."),
    ]


def chapter9_blocks():
    return conclusion_blocks()


def chapter10_blocks():
    return future_blocks()


# --------------------------------------------------------------------------------------- novelty and contributions
def novelty_blocks():
    return [
        P(f"This section sets the project against the base paper {cite('oprea')} and separates what is new from what is standard. The project is an **applied extension of the paper's motivation**, not a reproduction of its experiments."),
        TAB("Novelty compared with the base paper", ["Element", "Base paper", "This project", "Status"],
            [["Prediction models", "Seven classifiers incl. CatBoost, XGBoost, LightGBM", "LR, DT, RF + GB, HGB from scikit-learn", "Standard; no new learner"],
             ["Imbalance", "Class weights, scale_pos_weight", "Class weights, SMOTE on the training split only, none; recall measured with and without", "Standard methods, compared explicitly"],
             ["Model selection", "Recall as the objective", "Any of accuracy, precision, recall, F1, ROC-AUC; F1 by default", "Small variation"],
             ["Explanation method", "Unified perturbation explainer (RNP, FA, IM, AP), SHAP, LIME", "Coefficient x value (local), built-in and permutation importance (global); SHAP optional", "Simpler and cheaper; not a new explainer; **no unified explainer implemented**"],
             ["From score to action", "Business recommendations in the discussion", "Ten transparent IF/THEN rules with reasons, gated at 60%", "**New in this project** (heuristic, effect unmeasured)"],
             ["Per-customer view", "Global importance", "Customer 360: profile, score, band, drivers, actions", "**New in this project**"],
             ["Scenario analysis", "Not present", "What-if re-scoring of an edited customer", "**New in this project**"],
             ["Operations", "CRM integration proposed", "Batch scoring with schema check, drift screening, saved-model restore, API and web interface", "**New in this project** (single-user)"],
             ["Evaluation honesty", "Single split on real data", "Cross-validation, repeated splits, environment sensitivity, calibration and lift measured and reported", "Good practice applied; reported openly"]],
            widths=[1.1, 1.5, 2.0, 1.4], size=8.5),
        P("The novelty is therefore in the **combination and the application**: a complete, inspectable path from a customer table to a retention action, with the evaluation limits stated. There is no claim of a new algorithm and no claim of better prediction than the base paper."),
    ]


def contribution_blocks():
    return [
        P("The project makes six contributions."),
        N("**An end-to-end, explainable churn workflow.** One tested code path from CSV to risk bands, drivers and retention actions, usable through a Streamlit application and a React web interface (31 API routes, 13 working pages).",
          "**An evaluation that does not hide its uncertainty.** Besides the headline split, results are reported by 5-fold cross-validation and five random splits, under three imbalance strategies and two software environments, with calibration, threshold and targeting analyses.",
          "**A reproducible experiment record.** `scripts/run_experiments.py`, `make_figures.py` and `measure_api_latency.py` regenerate every number and figure in the documents from the project's own code.",
          "**A transparent retention engine.** Ten named rules plus two fallbacks, each returning a reason with its suggestion, so every action can be audited and changed.",
          "**A tested core.** 44 unit tests and a 63-check end-to-end API test; the tests found and fixed a real compatibility defect (pandas 3 string dtype) in the data loader.",
          "**An honest comparison with the base paper.** The differences in data, split, models and goals are stated, with no claim to match or beat its metrics."),
    ]


# --------------------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        P("**In scope.** The system covers the following, all of which are implemented and tested:"),
        B("Loading a customer CSV or generating a sample; detection of the target and ID columns; data-quality report; cleaning.",
          "Exploratory analysis of churn by attribute, with filters.",
          "Training and comparison of Logistic Regression, Decision Tree and Random Forest (and optionally Gradient Boosting and Histogram Gradient Boosting) with class weights, SMOTE or no handling.",
          "Evaluation on five metrics, confusion matrices and ROC and precision-recall curves; model selection on a chosen metric; saving and restoring the active model.",
          "Scoring of every customer, four risk bands with validated, editable thresholds, and a dashboard.",
          "Global and local explanation, what-if analysis, rule-based retention actions.",
          "Batch scoring of a new CSV with a schema check, and a drift screen.",
          "Two interfaces (Streamlit and a React web interface over a FastAPI service) with a demo login."),
        P("**Out of scope.**"),
        B("Collection or purchase of real operator data; the project's results rest on a synthetic sample.",
          "Real-time scoring from live billing or network events.",
          "A production database, multi-user operation, roles, auditing, and production-grade authentication.",
          "Integration with a CRM or campaign system.",
          "Measurement of the financial effect of retention campaigns.",
          "Deep-learning and external gradient-boosting libraries, LIME, and the unified perturbation explainer of the base paper."),
    ]


def assumption_blocks():
    return [
        B("The customer table has one row per customer and a binary churn label for training.",
          "Column names follow the 21-column Telco schema; other schemas run through the generic pipeline but the retention rules use only the Telco field names.",
          "One analyst uses the system at a time; state is held in memory.",
          "A churn probability is a model score used to rank customers, not a calibrated chance of leaving.",
          "The synthetic data stand in for an operator's data so that the pipeline can be demonstrated and tested."),
    ]


def limitation_blocks():
    return [
        TAB("Limitations and their consequences", ["Limitation", "Consequence", "Evidence"],
            [["Synthetic data", "No claim about real-world accuracy", "Generated by `src/sample_data.py`; churn follows a latent score plus noise"],
             ["Small test set", "Single-split metrics are noisy", f"200 rows, 53 churners; sd 0.03-0.10 across folds and splits"],
             ["Moderate ranking ability", "Predictions are useful for prioritising, not for certainty", f"ROC-AUC {F.LR['roc_auc']:.3f}; F1 {F.LR['f1_score']:.3f}; lift about 2 in the top 20%"],
             ["Uncalibrated probabilities", "Risk bands are rankings, not chances", f"Brier {F.EXTRA['brier_score']:.3f} against {F.EXTRA['brier_no_skill_constant_base_rate']:.3f} for a constant predictor"],
             ["Version-sensitive tree ensembles", "The Random Forest number depends on the scikit-learn version", "F1 0.4724 (scikit-learn 1.9.1) against 0.4815 (1.5.0)"],
             ["No SHAP result", "Explanations are approximations", "`import shap` fails in the environment; fallbacks used"],
             ["Rule-based advice", "Effect on churn unknown", "Rules written by the team; no campaign data"],
             ["In-memory state", "Dataset and comparison are lost on restart; one user", "AppState design; only the active model is persisted"],
             ["Demo login", "Not suitable for real customer data", "One shared account in `.env`"],
             ["Limited testing", "No load, security, usability or multi-browser evidence", "Section 7.7"]],
            widths=[1.5, 2.1, 2.4], size=9),
    ]


def not_measured_blocks():
    return [
        P("The following were **not measured** and are therefore not claimed anywhere in the project documents:"),
        B("Performance on real customer data or on the real public Telco file.",
          "The business value or uplift of any retention action.",
          "Calibration after recalibration, and cost-sensitive (profit) performance.",
          "SHAP-based explanations and any comparison of the built-in explanations with SHAP or LIME.",
          "Behaviour with several simultaneous users or very large files.",
          "Usability with real retention analysts."),
    ]


# --------------------------------------------------------------------------------------- implementation document
def walkthrough_blocks():
    return [
        P("The excerpts below are taken unchanged from the code base and explain how the central steps are implemented."),
        H2("3.1 Building the preprocessor (`src/preprocessing.py`)"),
        P("A single ColumnTransformer treats numeric and categorical fields differently. Because it is fitted on the training split only and reused unchanged for scoring, the same transformation is applied at training and in the application."),
        CODE(func_src("src/preprocessing.py", "build_preprocessor"), 8.5),
        H2("3.2 Training and comparing models (`src/train_models.py`)"),
        P("`train_selected_models` fits each requested model under the chosen imbalance strategy and evaluates it on the same test split. SMOTE is applied to the training matrix only; class weights are passed only to the models that accept them."),
        CODE(func_src("src/train_models.py", "train_selected_models"), 8),
        CODE(func_src("src/train_models.py", "select_best_model"), 8.5),
        H2("3.3 Risk bands (`src/utils.py`)"),
        CODE(func_src("src/utils.py", "assign_risk_category"), 8.5),
        H2("3.4 Local explanation with a fallback (`src/explainability.py`)"),
        P("When SHAP is unavailable (the case in this report) the explanation multiplies each feature's weight by the customer's standardised value; the third returned item tells the interface which method was used."),
        CODE(func_src("src/explainability.py", "local_explanation"), 7.5),
        H2("3.5 Scoring (`src/prediction.py`)"),
        CODE(func_src("src/prediction.py", "score_customers") + "\n\n" + func_src("src/prediction.py", "validate_columns_for_prediction"), 8.5),
        H2("3.6 Token check (`backend/auth.py`)"),
        CODE(func_src("backend/auth.py", "make_token") + "\n\n" + func_src("backend/auth.py", "read_token"), 8.5),
    ]


def decision_blocks():
    return [
        TAB("Implementation decisions and their reasons", ["Decision", "Reason"],
            [["All logic in `src/`, interfaces as thin callers", "Both interfaces give identical results; the core can be tested without a server"],
             ["Fit the preprocessor on the training split only; SMOTE on the training split only", "Prevents information from the test split reaching the model"],
             ["Select the model on F1 by default", "On 26% churn accuracy rewards a model that never predicts churn; the experiment shows recall of 0.19 with 0.745 accuracy"],
             ["Class weights as the default imbalance strategy", "Simple, no synthetic rows, works with all three required models"],
             ["Fixed hyper-parameters, no search", "Keeps the comparison reproducible and fast; a search on 800 rows would overfit the validation noise"],
             ["Coefficient-times-value as the local fallback", "Exact contribution to the log-odds for Logistic Regression; cheap; works without SHAP"],
             ["Rules gated at 60%", "Avoids sending offers to customers the model considers unlikely to leave"],
             ["Server-side validation of thresholds and files", "The interface cannot create an impossible state; errors are plain-language"],
             ["HMAC bearer token instead of sessions", "Stateless and dependency-free; suitable for a demonstration login"],
             ["Single in-memory `AppState` with a lock", "Mirrors Streamlit's session state; adequate for one user"],
             ["Report cross-validation and repeated splits", "A 200-row test set is too small to rank similar models"]],
            widths=[2.5, 3.5], size=9.5),
    ]
