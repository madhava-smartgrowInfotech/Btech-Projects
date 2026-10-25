"""Chapters 9 and 10 (conclusion, future scope) and the text of the scope, novelty, contribution and implementation documents."""

import ast
import os
import textwrap

from . import facts as F
from .blocks import B, CODE, H1, H2, N, P, TAB
from .ch8 import cite
from .shared import OBJECTIVES, OBJECTIVE_STATUS

X, R = F.X, F.REAL
D = F.DISEASES
NAME = F.NAME


# --------------------------------------------------------------------------------------- real source text
def _read(rel):
    return open(os.path.join(F.CODE, rel), encoding="utf8").read()


def func_src(rel, name):
    """Source text of a top-level function of a file under 8.ProjectCode (read from the real code)."""
    text = _read(rel)
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            lines = text.splitlines()
            start = node.decorator_list[0].lineno - 1 if node.decorator_list else node.lineno - 1
            return "\n".join(lines[start:node.end_lineno])
    raise KeyError((rel, name))


def excerpt(rel, start, end=None, exact_end=False):
    """Lines of a real file from the first line containing `start` to the first later line containing `end` (inclusive)."""
    lines = _read(rel).splitlines()
    i = next(k for k, ln in enumerate(lines) if start in ln)
    if end is None:
        return "\n".join(lines[i:])
    j = next(k for k in range(i + 1, len(lines)) if (lines[k] == end if exact_end else end in lines[k]))
    return "\n".join(lines[i:j + 1])


# --------------------------------------------------------------------------------------- conclusion
def _hl(d):
    return F.HO[d][F.BEST[d]]


def conclusion_blocks():
    acc = {d: F.pct(_hl(d)["accuracy"]) for d in D}
    outcome_rows = [[str(i), o, s, e.split(". ")[0].rstrip(".") + "."] for i, (o, (s, e)) in enumerate(zip(OBJECTIVES, OBJECTIVE_STATUS), 1)]
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary of the Work"),
        P("This project set out to replace one-disease-at-a-time screening tools with a single system that estimates the risk of diabetes, heart disease, liver disease and kidney disease from routine clinical values. "
          "It built a data generator, a training script that fits and compares Logistic Regression, a Decision Tree, a Random Forest and an RBF Support Vector Machine for each disease on standardised inputs and saves the model with the highest F1, "
          "a Flask application that loads the saved models, a FastAPI service with seven routes that reuses the same prediction code, and a React web interface with a prediction form for each disease, a model-comparison page, a dataset page and a not-a-diagnosis notice. "
          "Around these, the project added the measurements that the training script does not make: ROC-AUC, confusion matrices, cross-validation, repeated splits, threshold sweeps, permutation importance, a real-data check and API tests."),
        P(f"On the 400-row test sets of the **synthetic** data, the served models reach accuracy {acc['diabetes']} (diabetes, SVM), {acc['heart']} (heart disease, Logistic Regression), {acc['liver']} (liver disease, Logistic Regression) and {acc['kidney']} (kidney disease, Logistic Regression), "
          "close to the 92% ceiling that the 8% label noise allows. Cross-validation and ten random splits show that Logistic Regression is the best model for every disease on every split, including diabetes, where the SVM was shipped on the strength of a single split; "
          "Random Forest and the Decision Tree fit the noisy labels and score lower. On real public data the same algorithms reach 76.5% (Pima diabetes), 84.3% (Cleveland heart), 71.8% (ILPD liver) and 98.8% (chronic kidney disease), "
          "and the shipped models transfer only partly: for liver disease their accuracy of 54.0% is below the 71.4% majority-class baseline."),
        H2("9.2 Objectives Revisited"),
        TAB("Outcome against the six objectives", ["No.", "Objective", "Outcome", "Evidence"], outcome_rows, widths=[0.4, 2.2, 0.8, 2.6], align=["c", "l", "c", "l"], size=9),
        P("Three objectives are met only in part, and the conclusions are written accordingly: the data are synthetic rather than benchmark data, there is no missing-value or outlier handling because the synthetic data contain none, "
          "ROC-AUC was not part of model selection, and the application does not show which parameters drove a prediction."),
        H2("9.3 Key Findings"),
        N("**One interface for four diseases works.** A single API and web application serve sixteen trained models; a prediction takes about 14 ms at the median on the project machine, and 41 of 41 API checks pass.",
          "**Synthetic accuracy measures the rule, not the patient.** The generator's label rule is linear with 8% flipped labels, so about 92% is the best any model can do; the models reach 88-92% and a linear model is the right family.",
          "**The simple model is the best model.** Logistic Regression has the best F1 on 10 of 10 splits for all four diseases, the highest cross-validated accuracy, and the smallest gap between training and test accuracy.",
          "**Model selection on one split can be wrong.** The shipped diabetes model (SVM, F1 0.8636) is not supported by cross-validation, where Logistic Regression is better.",
          "**Real data are harder.** Accuracy falls to 71.8-84.3% for three of the four diseases, and a model trained on synthetic data can fall below the majority-class baseline on real records.",
          "**A displayed confidence is not an accuracy.** The shown percentage is the probability of the predicted class, and a false positive can be displayed with 99.53%."),
        H2("9.4 Practical Applications"),
        P("The system is suitable as a **teaching and demonstration aid**: it shows how four classical classifiers are trained, compared and served behind one interface, how a model is wrapped in an API and a web form, and how much the numbers depend on the data. "
          "With real, validated training data and the additions in Chapter 10 it could become a screening aid in settings with few specialists, helping a health worker decide whom to refer for a confirmatory laboratory test. "
          "It is **not a diagnostic tool**, it has not been validated on patients, and the application says so on every result."),
        H2("9.5 Known Limitations"),
        P("The limitations are discussed in full in the Scope and Limitations document; the main ones are:"),
        B("The training data are synthetic; the metrics are not clinical performance and cannot be compared with published results on real data.",
          "Selection of the served model uses the same 400-row test set that reports its score, with fixed settings and no tuning.",
          "No missing-value or outlier handling, no calibration and no per-prediction explanation; the application's confidence is the probability of the predicted class.",
          "No range validation: impossible values such as a glucose of 100,000 mg/dL are classified.",
          "No sign-in, database, audit log or stored history; no pytest suite, usability study, fairness analysis or external validation."),
        H2("9.6 Concluding Remarks"),
        P(f"The project shows that a multi-disease screening pipeline can be built from open-source parts, run on a desktop in seconds, and audited honestly: every number in this report can be regenerated by a script, and the places where the evidence is weak are stated. "
          f"It follows the base paper {cite('base')} in comparing several classifiers by held-out evaluation and in treating interpretability as essential for clinical trust, but it does not reach the paper's rigour (nested cross-validation, real data, SHAP and counterfactual explanations). "
          "The next step, described in Chapter 10, is to repeat the evaluation on real patient data with proper validation before anyone relies on the output."),
    ]


FUTURE = [
    ("Train and validate on real data", "Replace the synthetic CSVs by the public benchmark data (Pima, Cleveland, ILPD, chronic kidney disease) or, better, local clinical records, add median or model-based imputation and outlier handling inside the pipeline, "
     "and report the real-data results of Section 8.8 as the headline. This addresses the main weakness of the present work."),
    ("Nested cross-validation and tuning", "Follow the base paper: choose hyper-parameters and the algorithm in an inner loop and report an outer-loop estimate, so that model selection no longer uses the reported test set. This would also settle the diabetes choice."),
    ("Explain every prediction", "Add SHAP values and counterfactual \"what would change the result\" explanations, as in the base paper, and show the driving parameters on the result card; the offline permutation analysis of this report is a starting point."),
    ("Calibrate and expose the threshold", "Apply Platt scaling or isotonic regression on a validation split so that the percentage can be read as a risk, show a reliability curve, and let the user choose the decision threshold for a screening or a confirmatory use."),
    ("Validate inputs clinically", "Reject or flag physiologically impossible values on the server, not only in the form, and show units and reference ranges next to each field."),
    ("Recommendations and referral guidance", "Generate the \"healthcare recommendations\" promised in the abstract from reviewed clinical rules, with wording approved by a clinician, and link each to a confirmatory test."),
    ("More conditions and one-record scoring", "Add further diseases (for example thyroid, as in the base paper) and score one patient record against all conditions at once, with a combined summary and a missing-value policy for fields that were not measured."),
    ("Stronger models", "Try gradient-boosted trees and calibrated linear models, keep Logistic Regression as the interpretable baseline, and compare with fairness across sex and age groups."),
    ("Production foundations", "Add accounts with roles, an audit log, versioned model storage and a database; containerise the API and the web application; add a pytest suite, frontend tests and a load test."),
    ("Deployment and scalability", "The measured API handled about 415 requests per second on one desktop with four clients, which is ample for a clinic. Beyond that, run several stateless workers behind a reverse proxy; the models are small pickle files."),
    ("Further research", "Study how a screening aid changes referral behaviour in a rural health centre, how explanations affect trust, and whether models trained on one population transfer to another, which the liver result of this report shows to be the critical question."),
]


def future_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        P("The work leaves several directions open. They are ordered by how much they would change the value of the system."),
        N(*[f"**{t}.** {d}" for t, d in FUTURE]),
        P("The first four are the most important: they address the main weakness of this report (synthetic data), the main weakness of the model choice (selection on the reported test set), the main gap against the base paper "
          "(explanations) and the main weakness of the output (an uncalibrated confidence)."),
    ]


def chapter9_blocks():
    return conclusion_blocks()


def chapter10_blocks():
    return future_blocks()


# --------------------------------------------------------------------------------------- novelty and contributions
def novelty_blocks():
    return [
        P(f"This section sets the project against the base paper {cite('base')} and separates what is new from what is standard. The paper is a **single-disease modelling study** (thyroid status, real data, nested cross-validation, SHAP and counterfactual explanations); "
          "this project is an **applied, multi-disease extension of its motivation** with a weaker evaluation protocol and no explanations. Its novelty is in the combination and in the audit of its own results, not in a new learning algorithm."),
        TAB("Novelty compared with the base paper", ["Element", "Base paper", "This project", "Status"],
            [["Scope", "One disease: thyroid, three classes", "Four diseases (diabetes, heart, liver, kidney) behind one API and one web application", "**New at application level**"],
             ["Algorithms", "SVC, Random Forest, Extra Trees, AdaBoost, CatBoost", "Logistic Regression, Decision Tree, Random Forest, SVM from scikit-learn", "Standard; no new learner"],
             ["Preprocessing", "Cleaning, feature engineering, consensus top-10 feature selection, scaling inside folds", "StandardScaler fitted on the training rows only; no feature selection, no imputation", "Standard, simpler"],
             ["Evaluation", "Nested cross-validation, grid search, ROC-AUC, SMOTE study", "One hold-out split with fixed settings; cross-validation and ten random splits added as an audit", "Weaker protocol, audited"],
             ["Explainability", "SHAP and counterfactual explanations", "None in the application; permutation importance offline only", "**Not achieved**; the main gap"],
             ["Data honesty", "Real public data, limits discussed", "Synthetic data with a quantified 92% noise ceiling, plus a supplementary real-data check of the shipped models", "**New in this project**"],
             ["Model-choice robustness", "Selection confined to the inner loop", "Shows the single-split choice for diabetes is not supported by 5-fold CV and ten splits", "**New finding**"],
             ["Reproducibility", "Fixed seeds, appendix tables", "Scripts regenerate every table, chart, screenshot and API test", "Good practice applied"]],
            widths=[1.1, 1.5, 2.2, 1.2], size=8.5),
        P("**What is not new.** The four classifiers, standardisation, an 80/20 split, selection by F1, pickled models, a Flask page, a FastAPI wrapper and a React front end are all standard techniques. "
          "The synthetic generator follows a familiar idea (a risk score through a sigmoid with label noise). No claim is made that the project improves on the state of the art; "
          "the contribution is a working, tested multi-disease interface and an honest account of what its numbers do and do not mean."),
    ]


def contribution_blocks():
    return [
        P("The project makes six contributions."),
        N("**A single multi-disease screening interface.** Sixteen models (four algorithms for each of four diseases) trained by one script and served by a seven-route FastAPI service and a React application with a prediction form per disease, a model-comparison page and a dataset page.",
          "**An audit of synthetic-data results.** The label rule of the generator is analysed to show that about 92% accuracy is the ceiling, and a supplementary run on the Pima, Cleveland, ILPD and chronic kidney disease data shows that the same algorithms score 71.8-98.8% on real data and that the shipped liver model falls below the majority-class baseline.",
          "**A robustness check of model selection.** Five-fold cross-validation and ten random splits show that Logistic Regression is the best model for every disease, and that the SVM shipped for diabetes rests on a single split.",
          "**A reproducible measurement record.** `run_experiments.py`, `real_data_check.py`, `api_tests.py`, `make_figures.py` and the capture scripts regenerate every number, chart and screenshot in the documents from the project's own files.",
          "**A tested API.** 41 functional, consistency, validation and sanity checks plus a 27-check smoke test pass; the API prediction equals a direct model call on all 40 sampled records, and the latency was measured.",
          "**An honest comparison with the base paper.** The differences in disease, data, protocol and explanations are stated, with no claim to match its metrics, and the gaps (no explanations, no imputation, no ROC-AUC in training, no recommendations) are listed rather than hidden."),
    ]


# --------------------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        P("**In scope.** The system covers the following, all of which are implemented and were run:"),
        B("Generation of four synthetic clinical data sets (diabetes, heart, liver, kidney; 2,000 rows each) with the column names of the public benchmark data.",
          "Training and comparison of Logistic Regression, a Decision Tree, a Random Forest and an RBF SVM for each disease on standardised inputs, with accuracy, precision, recall and F1 reported and the best model by F1 saved.",
          "A Flask application (original) and a FastAPI service with seven routes that load the saved models and return a risk class and a confidence for one record.",
          "A React web interface: landing page, overview, one prediction form per disease with real-record samples and input validation, a model-comparison page, a dataset page and an about page; dark and light themes; phone-width layout.",
          "Supplementary measurements for the documentation: ROC-AUC, confusion matrices, cross-validation, ten random splits, threshold and sensitivity sweeps, permutation importance, a real-data check and API tests."),
        P("**Out of scope.** The following were deliberately not built:"),
        B("Diagnosis, treatment advice or any clinical decision; the application is a demonstration of a screening pipeline.",
          "Other diseases and free-text or image input; every condition takes a fixed list of numeric laboratory and clinical fields.",
          "Scoring one record against all four diseases at once: each disease has its own form and its own required fields.",
          "Per-prediction explanations, healthcare recommendations, feature selection, missing-value imputation and outlier handling.",
          "User accounts, a database, storage of patient records, an audit log, deployment in a hospital or any integration with health-record systems.",
          "Hyper-parameter search, probability calibration and nested cross-validation."),
    ]


def assumption_blocks():
    return [
        B("The relationships between inputs and risk in the synthetic data are a stand-in for real clinical relationships; the risk rules were written by the team from general medical knowledge.",
          "Each condition is treated as a binary task: label 1 means high risk (Positive) and label 0 low risk (Negative).",
          "The user enters every value in the unit shown on the form (for example glucose in mg/dL); the system does not convert units.",
          "Categorical inputs (sex, chest-pain type, resting ECG, slope, vessels, thalassemia, albumin and sugar grades) are entered with the numeric codes shown on the form.",
          "A single stratified 80/20 split with seed 42 is representative enough to compare the algorithms; the cross-validation and ten-split checks test this assumption.",
          "The application is used by one person on a local machine; the demonstration needs no accounts."),
    ]


def limitation_blocks():
    return [
        B("**Synthetic data.** All four training sets are generated; the label is a known linear rule plus 8% flipped labels. Accuracy cannot exceed about 92% and says nothing about patients.",
          "**Weak transfer to real records.** The shipped models score 75.0%, 69.6%, 54.0% and 82.3% on real Pima, Cleveland, ILPD and chronic kidney disease records; for liver disease this is below the 71.4% majority baseline.",
          "**Model selection on the test set.** The served model is chosen on the 400 rows that report its score; for diabetes the chosen SVM is not supported by cross-validation.",
          "**Small test sets.** Each test set has 400 rows (112 to 292 high-risk), so single-split differences of one or two points are noise.",
          "**No tuning.** Hyper-parameters are fixed; the sensitivity sweep shows a point or two is available.",
          "**Uncalibrated confidence.** The percentage shown is the probability of the predicted class, not the chance of being right; a false positive is shown with 99.53%.",
          "**No explanations or recommendations.** The application does not show which inputs drove a prediction, and it gives no advice, so objective 6 and part of the abstract are not met.",
          "**No input range validation.** Values such as a glucose of 100,000 mg/dL or an age of -5 are accepted by the API and classified.",
          "**Hardware and environment.** Measured on one CPU-only desktop; the pickled models require scikit-learn 1.8.0 and fail with older versions.",
          "**Security and privacy.** There is no sign-in; no patient data are stored, but a deployed system would need both."),
    ]


def not_measured_blocks():
    return [
        P("The following were **not** measured, and no number for them appears in this work:"),
        B("Performance on real patients, on an external data set, or in a prospective setting.",
          "Probability calibration (no reliability curve or Brier score was computed).",
          "Nested cross-validation or a tuned model; the effect of a hyper-parameter search.",
          "Fairness or subgroup performance by sex or age.",
          "Agreement of the permutation importance with SHAP or with clinical knowledge beyond the generator's own rule.",
          "Usability with clinicians or patients, accessibility audits, and behaviour in browsers other than Chrome.",
          "Security, load beyond four concurrent clients, or latency on a deployed server.",
          "The effect of recommendations on health outcomes (none are produced)."),
    ]


# --------------------------------------------------------------------------------------- code walk-through
def walkthrough_blocks():
    return [
        P("The excerpts below are taken unchanged from the code base and explain how the central steps are implemented."),
        H2("3.1 Generating labelled data (`generate_data.py`)"),
        P("Each data set is built from feature distributions, a linear risk score and a sigmoid. `add_noise_labels` thresholds the probability at 0.5 and then flips 8% of the labels at random; "
          "this noise is why about 92% accuracy is the ceiling. The diabetes risk score is shown as an example."),
        CODE(func_src("generate_data.py", "add_noise_labels"), 8.5),
        CODE(excerpt("generate_data.py", "    risk = (", "outcome = add_noise_labels(risk)"), 8.5),
        H2("3.2 Training, comparing and saving models (`train_models.py`)"),
        P("For each disease the script splits the rows 80/20 with stratification, fits the scaler on the training rows only, trains the four algorithms, computes four metrics on the test rows and keeps the model with the highest F1. "
          "The selection and the reported score use the same test rows, which is the weakness discussed in Section 8.4."),
        CODE(excerpt("train_models.py", "    X_train, X_test, y_train, y_test = train_test_split(", '    joblib.dump(cfg["features"]'), 8),
        H2("3.3 Loading the models and predicting (`app.py`)"),
        P("`load_bundle` loads the model, scaler and feature list of a disease, and `BUNDLES` holds all four. The prediction step scales the submitted values with the saved scaler and calls `predict`; "
          "the confidence is the larger of the two class probabilities."),
        CODE(func_src("app.py", "load_bundle") + "\n\n" + textwrap.dedent(excerpt("app.py", "            X = np.array(values)", '            result = "Positive (High Risk)"')), 8.5),
        H2("3.4 The prediction route (`backend/main.py`)"),
        P("The FastAPI service imports `app.py`, so its predictions are identical to the Flask pages. The route rejects an unknown disease with 404 and any missing or non-finite value with 422 and a message naming the fields, then repeats the same three steps."),
        CODE(func_src("backend/main.py", "predict"), 8),
        H2("3.5 Input validation in the web form (`frontend/src/pages/Predict.jsx`)"),
        P("The form checks that every field is present and numeric before calling the API, and marks the first missing field. A separate check in the field component warns when a value is outside the range seen in the training data."),
        CODE(excerpt("frontend/src/pages/Predict.jsx", "function validate(", "}", exact_end=True), 8.5),
    ]


def decision_blocks():
    return [
        TAB("Implementation decisions and their reasons", ["Decision", "Reason"],
            [["Keep the original Flask app and import it from the FastAPI service", "One set of model bundles and prediction code, so the React interface and the Flask pages give identical results and nothing was re-implemented"],
             ["StandardScaler fitted on the training rows only, saved beside the model", "Prevents information from the test rows reaching the model; the same scaling is applied at prediction time"],
             ["Four classical algorithms with fixed settings", "Matches the objectives and keeps the comparison reproducible; a search on 1,600 rows would also need a separate validation split"],
             ["Select the served model on F1", "Accuracy alone favours the majority class in the unbalanced heart and liver sets; F1 balances precision and recall"],
             ["Stratified split", "Keeps the class balance equal in training and test rows"],
             ["Save models as joblib pickles with a JSON report", "Simple, loads in milliseconds and needs no database; the cost is a pinned scikit-learn version"],
             ["Return the predicted-class probability as the confidence", "Available for all four algorithms (the SVM uses `probability=True`); the cost is that it is not calibrated"],
             ["Synthetic data with the public column names", "The build environment had no internet access, and matching names let real data be dropped in later (as the real-data check does)"],
             ["React with Vite, dark and light themes", "Fast development, a responsive interface down to phone width, and a clear separation from the API"],
             ["Real-record sample buttons in the form", "Lets a user try the models with valid values and see agreement and disagreement with the stored label"],
             ["Warn, but do not block, values outside the training range", "The user may enter a legitimate extreme value; the cost is that impossible values are not rejected (a limitation)"],
             ["Measure extra things in separate scripts", "Cross-validation, ROC-AUC, the real-data check and API tests were added without changing the shipped models or the application"]],
            widths=[2.5, 3.5], size=9.5),
    ]
