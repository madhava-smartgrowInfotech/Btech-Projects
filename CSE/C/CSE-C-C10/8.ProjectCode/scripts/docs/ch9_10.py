"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

from . import facts as F
from .blocks import B, CODE, H1, H2, N, P, TAB, renum
from .refs import cite

R = F.R
X = F.X
S = F.S
RM = R["models"]
RF, XGB, LR, DT, HGB = RM["Random Forest"], RM["XGBoost"], RM["Logistic Regression"], RM["Decision Tree"], RM["HistGradientBoosting"]
ALL = X["with_all_features"]
NOPH = X["without_posthoc_features"]
RET = X["retrieval_only_structured"]
LAT = F.LAT


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def m(blk, key="balanced_accuracy", d=3):
    return f"{blk[key]['mean']:.{d}f}"


def auc(model_blk):
    return m(model_blk, "roc_auc")


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    return [
        P("The project does not propose a new learning algorithm and does not claim one. Logistic regression, decision trees, random forests and gradient boosting are established methods "
          f"{cite('rf', 'xgb', 'gbm', 'sklearn')}, and so is retrieval of nearest neighbours by cosine similarity {cite('knn')}. What the project contributes is a particular combination of a classifier "
          "with retrieved comparable startups and feature-level reasons, the packaging of that combination as a local application, and a measurement of how well it works on a real public table. "
          "This document states first how the work differs from the declared base paper and the method anchor, then what is and is not new, and finally what the evidence supports."),
        H2("Difference from the base paper and the method anchor"),
        TAB("The base paper, the method anchor and this project compared", ["Dimension", "Base paper (Panjwani et al. 2026) [1]", "Method anchor (Maarouf et al. 2026) [2]", "This project"],
            [["Problem", "Startup success classification", "Startup success with an LLM and retrieved examples", "Startup outcome (SUCCESS / FAILURE) with comparable-startup evidence"],
             ["Data", "Crunchbase / Kaggle data; size not stated", "4,034 Crunchbase startups, 35.15 % successful", f"Real public table: {F.REAL_ROWS} rows (structured only); shipped app: {F.SYN_ROWS:,}-row synthetic fallback with text"],
             ["Features", "Funding, team size, industry, location", "Structured profile plus text description", "16 structured fields, state and industry (37 encoded features) plus a 384-d description embedding"],
             ["Learner", "LR, RF, SVM, Gradient Boosting", "kNN in-context learning with an LLM, against LR, RF, XGBoost", "LR, Decision Tree, RF, XGBoost (HistGradientBoosting in the study); balanced cosine retrieval beside the classifier"],
             ["Imbalance", "ADASYN oversampling", "Balanced accuracy as metric", "Balanced class weights; oversampling compared on real data; balanced accuracy as the selection metric"],
             ["Protocol", "Single 70:30 split", "5 repeated stratified 80/20 splits", "5 repeated stratified 80/20 splits (and a 70:30 x 5 seeds run for comparison)"],
             ["Explanation", "Feature importance chart", "LLM reasoning", "Signed top-5 feature terms, retrieval statistics and the retrieved startups themselves"],
             ["Delivery", "Flask page", "Experiment code", "FastAPI + React application, local only, no external model service"]],
            widths=[0.8, 1.8, 1.9, 2.4], align=["l", "l", "l", "l"], size=9),
        H2("What is new and what is not"),
        TAB("Elements of the work and their status", ["Element", "Status", "Note"],
            [["LR, Decision Tree, Random Forest, XGBoost and their metrics", "Standard", f"Used through scikit-learn and XGBoost {cite('sklearn', 'xgb')}; the ensemble ranking is the one the base paper reports"],
             ["Class weighting and oversampling for imbalance", "Standard", f"Established remedies {cite('imbalance', 'smote', 'adasyn')}; compared here on real data"],
             ["Retrieval of the most similar past startups as evidence", "Adapted idea", f"The retrieval-of-comparable-startups idea and the 5 x 80/20 protocol follow {cite('maarouf')}; here the LLM is replaced by a classifier and the retrieved cases are shown as evidence"],
             ["Fusion of scaled structured features with a sentence embedding by a weighted concatenation (alpha = 0.5) and L2 normalisation", "Design choice of this project", f"MiniLM embedding {cite('minilm', 'sbert')}; a single cosine similarity then covers both views"],
             ["Balanced half-success / half-failure retrieval quota from training rows only", "Design choice of this project", "Stops the neighbours of a rare outcome from being swamped, and cannot see test rows (no leakage)"],
             ["Application returning verdict, probabilities, drivers and comparable startups", "New in this project", "Six React screens, the original Jinja pages, eleven JSON routes, demo sign-in"],
             ["Ten-study real-data benchmark including a leakage-like-feature ablation and a retrieval-only classifier", "New in this project", "Separates what the models learn from what the table leaks and from what the text adds"],
             ["Observations: 85-92 % not reproduced; ROC-AUC falls by about 0.1 without post-hoc fields; retrieval alone equals LR; synthetic text leaks the label", "Findings of this project", "Reported with the data that supports them"]],
            widths=[2.7, 1.4, 2.6], align=["l", "l", "l"], size=9.5),
        H2("What the evidence supports"),
        P(f"The evidence supports the statement that the combination works end to end and that, on the real structured table, the tree ensembles rank above logistic regression, as the base paper claims: "
          f"balanced accuracy {m(RF)} (Random Forest) and {m(XGB)} (XGBoost) against {m(LR)} (Logistic Regression), ROC-AUC {auc(RF)}, {auc(XGB)} and {auc(LR)}. "
          f"It does not support the 85-92 % accuracy level of the base paper (best accuracy {m(XGB, 'accuracy')} on 80/20 splits and {R['split_70_30']['Random Forest']['accuracy']['mean']:.3f} on a 70:30 split). "
          f"It does not support a claim that the text embedding helps on real startups, because the real table has no descriptions; on the synthetic table the combined view scores {S['representations']['combined']['mean']:.3f} against {S['representations']['structured_only']['mean']:.3f} "
          "for the structured view, but that synthetic text was generated from class-specific templates and leaks the label. "
          f"A retrieval-only classifier on the real structured features reaches balanced accuracy {m(RET['10'])} to {m(RET['50'])}, equal to logistic regression. "
          "These are limits of the present experiment (one 922-row table, five splits, 185-row test folds) and are discussed under limitations."),
    ]


def contribution_blocks():
    return [
        N("An end-to-end startup-outcome application, VenturePulse: a FastAPI backend and a React interface that take 16 structured fields, a state, an industry and an optional description, and return a SUCCESS / FAILURE estimate with probabilities, a risk label, the main feature drivers and the comparable historical startups, all computed locally.",
          "A fused structured-plus-text representation (scaled features and a 384-dimensional MiniLM embedding, weight alpha = 0.5, L2 normalised) with a balanced, training-only cosine retrieval of k = 10, 20, 30 or 50 comparable startups, adapted from the retrieval idea of the method anchor without a language model.",
          "A comparison of Logistic Regression, Decision Tree, Random Forest and XGBoost under five repeated stratified 80/20 splits with balanced accuracy as the selection metric, plus HistGradientBoosting on real data, class-imbalance strategies, a threshold sweep, calibration bins and a Random Forest size study (scripts/run_experiments.py).",
          f"A set of honest findings on the real table: tree ensembles beat logistic regression (balanced accuracy {m(RF)} against {m(LR)}) but not to the 85-92 % level of the base paper; removing four post-hoc fields lowers ROC-AUC from about {auc(RF)} to {m(NOPH['Random Forest'], 'roc_auc')}; retrieval alone equals logistic regression; the shipped synthetic text leaks the label.",
          f"A test and measurement record: {F.N_TESTS} automated checks (7 unit tests, 15 smoke checks, 29 API edge cases) and a measured response time of {LAT['predict_k10']['median_ms']:.0f} ms (k = 10) to {LAT['predict_k50']['median_ms']:.0f} ms (k = 50) per prediction on a CPU-only machine."),
    ]


def scope_blocks():
    return [
        H2("In scope"),
        B("Binary classification of an early-stage startup as SUCCESS (acquired or IPO) or FAILURE (closed), with probabilities, a confidence and a risk label.",
          "Structured inputs: funding total and rounds, ages at first and last funding and milestone, relationships, milestones, average participants, seven flags (VC, angel, rounds A to D, top-500), state and industry; an optional description of up to 2,000 characters; k from {10, 20, 30, 50}.",
          "Preprocessing (median and most-frequent imputation, standardisation, one-hot encoding, log funding), a MiniLM text embedding, weighted fusion and balanced cosine retrieval of comparable startups.",
          "Four classifiers (Logistic Regression, Decision Tree, Random Forest, XGBoost) selected by balanced accuracy, with explanations from coefficients or importances.",
          "A local web application: landing page, demo sign-in, dashboard, analyse form and result, model performance and insights, plus the original server-rendered pages.",
          f"Evaluation on the real public table ({F.REAL_ROWS} rows) and on the shipped synthetic fallback: accuracy, balanced accuracy, precision, recall, F1, ROC-AUC, confusion matrices, class-imbalance, threshold, calibration, ablation and latency studies. Hardware used: {F.HARDWARE}."),
        H2("Out of scope"),
        B("Investment advice or any guarantee of a startup's future. The output is an analytical estimate.",
          "Founder background, team experience, market trends, patents and social-media signals; they are named in the abstract but exist in neither dataset.",
          "Temporal validation, because the public table carries no usable dates.",
          "Deep-learning classifiers, a language model, SHAP values and GPU training.",
          "Authentication beyond a demo token, multi-user operation, a SQL database, cloud deployment and load handling.",
          "Datasets other than the US-centred public table and the synthetic fallback."),
        H2("Users and environment"),
        P("The intended user is a student, teacher or analyst who runs the application locally (Windows, Python 3.11 and Node.js 20 or newer, started with run.bat) and uses it as a screening aid and as a teaching example of a classifier with retrieved evidence. "
          "The backend listens on 127.0.0.1:8410 and the React frontend on port 5410; no data leaves the computer and no external prediction service is called."),
    ]


def assumption_blocks():
    return [
        B("Historical startup records carry some signal about later outcomes through funding, milestones, relationships, sector and location. The experiments confirm a moderate signal; they do not show that these fields cause success.",
          "The outcome mapping is reasonable: acquired or IPO is SUCCESS, closed is FAILURE, and a startup that is still operating has no label and is outside the data.",
          f"The public 923-row table ({F.REAL_ROWS} rows after de-duplication) is representative enough of US startups of its period to compare models; it is not a sample of any other country.",
          "The fields age_last_milestone_year, milestones and relationships are usable as inputs, although part of them may be recorded after the outcome window (see limitation L2).",
          "Description text, when given, is the company's own summary, with the company name masked before embedding.",
          "The application runs on a trusted local machine and the user types their own inputs.",
          "The libraries match requirements.txt (scikit-learn 1.5.2, pandas 2.2.3); model files saved by newer versions may fail to load."),
    ]


def limitation_blocks():
    lim = [
        ("L1. The shipped model is trained on synthetic data.", f"The Kaggle download needs a login, so the model in models/ was fitted to a {F.SYN_ROWS:,}-row synthetic fallback ({F.SYN_SUCCESS} success, {F.SYN_FAILURE} failure) generated from templates. "
         f"Its balanced accuracy of {syn_lr()} (Logistic Regression, fused features) is a pipeline check, not evidence of real-world skill, and its description text differs between classes by construction."),
        ("L2. Leakage-like fields.", f"relationships, milestones and the two milestone-age fields are recorded around or after the outcome window and the table has no time stamps to remove them. Dropping them lowers ROC-AUC from {auc(RF)} to {m(NOPH['Random Forest'], 'roc_auc')} (Random Forest) "
         f"and from {auc(XGB)} to {m(NOPH['XGBoost'], 'roc_auc')} (XGBoost). The real-data numbers are an upper bound for early-stage prediction {cite('leakage', 'zbikowski')}."),
        ("L3. No temporal split.", "Training and test rows are drawn at random, so look-ahead bias cannot be excluded, a problem that the base paper itself raises and that a time-based split would address."),
        ("L4. One small US dataset.", f"All real measurements use {F.REAL_ROWS} US startups; five 80/20 splits give test folds of 185 rows, so differences of about 0.03 in balanced accuracy are within the split-to-split spread. Small industries (Biotech, CleanTech: 6 test rows each) cannot be assessed."),
        ("L5. The text channel is untested on real startups.", "The public table has no descriptions. The benefit of the MiniLM embedding and of the fused retrieval is therefore measured only on synthetic text that leaks the label."),
        ("L6. No founder, team-experience or market data.", "The abstract and the objectives name these inputs; neither dataset contains them. Funding velocity is only approximated by the ages at first and last funding and the number of rounds."),
        ("L7. Class balance differs from the assumption.", f"In the real table SUCCESS is the majority ({F.pct(R['dataset']['success_share'])}). Class weights and oversampling did not raise ROC-AUC; they only trade recall of success for precision."),
        ("L8. Probabilities are not calibrated.", "A class-weighted logistic regression underestimates P(success) in the middle range on the real data (for example predicted 0.35, observed 0.65 in the 0.3-0.4 bin). The confidence shown is max(P) and is not a guarantee."),
        ("L9. Model selection rule versus data.", "The application picks the best model by balanced accuracy on its own training data; on the synthetic table that is Logistic Regression, on the real table XGBoost and Random Forest tie. A retrain on real data would therefore change the served model."),
        ("L10. Operational limits.", f"No database, no multi-user support, a demo HMAC token for sign-in, no load or security test; the sentence-transformers model is loaded on the first request and, if unavailable, a hashing fallback embedding is used. Hardware: {F.HARDWARE}."),
    ]
    out = [P("The following limitations apply to the system and to the conclusions of this report. They are numbered so that other chapters can refer to them.")]
    for t, body in lim:
        out.append(P(f"**{t}** {body}"))
    return out


def syn_lr():
    return f"{S['models']['Logistic Regression']['balanced_accuracy']['mean']:.3f}"


def not_measured_blocks():
    return [
        P("The following were not measured, and no figure for them appears in this report."),
        TAB("Items not measured", ["Item", "Why it matters", "Status"],
            [["Performance on a time-based (out-of-time) split", "Look-ahead bias cannot be excluded without it", "Not run: the table has no dates"],
             ["Effect of the text embedding and of fused retrieval on real startups", "The main novelty claim of the application", "Not run: the real table has no descriptions"],
             ["ROC-AUC of the shipped fused model", "Threshold-free ranking quality of the served model", "Not recorded by the application's own evaluation"],
             ["Founder experience, team size and market-trend features", "Named in the abstract and the objectives", "Not available in either dataset"],
             ["Statistical significance of differences between models", "Differences of 0.01 to 0.03 are within the spread of five splits", "Not tested"],
             ["SHAP values and other model-agnostic explanations", "The explanations shown are coefficient and importance terms", "Not computed"],
             ["Other datasets and other countries", "Generalisation beyond 922 US startups", "Not run"],
             ["Hyper-parameter search for each model", "Defaults and fixed settings may be far from the best", "Not run; Random Forest size varied only"],
             ["Concurrent users, memory under load, long-running behaviour", "Deployment readiness", "Not tested; only sequential requests were timed"],
             ["A user study of the interface", "Whether founders and investors understand the evidence", "Not carried out"],
             ["Security review and penetration test", "Input handling beyond localhost", "Only input validation and token checks were tested"]],
            widths=[2.7, 2.4, 1.6], align=["l", "l", "l"], size=9.5),
    ]


def walkthrough_blocks():
    return [
        P("This section walks through the code that matters most, quoting the repository as it was when the results of this report were measured."),
        H2("Fusing the structured and text representations"),
        P("`fuse` L2-normalises the scaled structured vector and the text embedding separately, scales them by alpha and 1 - alpha, concatenates them and normalises again, so that the dot product of two fused vectors is their cosine similarity. "
          "`retrieve_similar` then ranks all training rows by that similarity and fills a half-success, half-failure quota, topping up from the nearest remaining rows if one class runs short. Only training rows are searched."),
        CODE(src("app/ml/retrieval.py", 11, 55), 8),
        H2("The prediction path"),
        P("`predict_one` builds one input row (adding the log of the funding total), transforms it with the fitted preprocessor, embeds the description (or, if it is empty, a short sentence made of the industry) and fuses both parts. "
          "The model gives P(failure) and P(success); the outcome is the larger one and the confidence is its value. The same fused vector is used for the retrieval of comparable startups."),
        CODE(src("app/services/predictor.py", 38, 61), 8.5),
        H2("Risk label"),
        P("The risk label is a fixed rule on the predicted class and the confidence, not a separate model. It reads the confidence of the winning class only, so a FAILURE prediction with high confidence is labelled Moderate risk rather than Lower risk."),
        CODE(src("app/services/predictor.py", 104, 104), 8.5),
        H2("The evaluation loop"),
        P("The evaluation fits the preprocessor on the training part of each of the five stratified 80/20 splits only, fuses the features, trains every model, scores it with accuracy, balanced accuracy, precision, recall and F1, repeats the comparison for the structured-only, text-only and combined views, "
          "and runs the retrieval vote for each k. The best model by mean balanced accuracy is the one the application serves."),
        CODE(src("app/ml/evaluation.py", 50, 72), 8),
        H2("Signed demo token"),
        P("The demo sign-in returns an HMAC-signed token containing the e-mail address and an expiry time. `read_token` decodes it, rejects an expired token and compares the signature in constant time. A token whose signature has been altered is refused (checked by the edge tests)."),
        CODE(src("app/api_extra.py", 64, 83), 8.5),
        H2("The real-data experiment"),
        P("The real-data script re-uses the application's own preprocessing and model definitions, so that the real numbers describe the same pipeline that is served. It loads the 923-row table, maps its columns to the application's schema, and runs the studies of Chapter 8."),
        CODE(src("scripts/run_experiments.py", 53, 82), 8),
    ]


def decision_blocks():
    return [
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "What was observed"],
            [["Select the served model by balanced accuracy", "With unequal classes, plain accuracy rewards predicting the majority; balanced accuracy averages the recall of both classes " + cite("maarouf"), f"On the synthetic table Logistic Regression wins ({syn_lr()}); on the real table XGBoost and Random Forest tie at {m(XGB)}"],
             ["class_weight = balanced for LR, tree and forest", "Cheap algorithm-level remedy for imbalance that does not alter the data " + cite("imbalance"), "On real data it did not raise ROC-AUC; it trades recall of the majority class for precision (L7)"],
             ["Embed the description with all-MiniLM-L6-v2 on the CPU", "384-d sentence embeddings, small enough to run locally without a GPU or an external service " + cite("minilm", "sbert"), f"First request loads the model; later predictions take a median of {LAT['predict_k10']['median_ms']:.0f} ms at k = 10"],
             ["Hashing fallback embedding if the transformer cannot load", "The application must still start without the model download", "Reported in the response as embedding_backend; not used in the measurements"],
             ["Fuse with alpha = 0.5 and normalise twice", "Gives both views equal weight and turns cosine similarity into a dot product", "Alpha was not tuned (not measured)"],
             ["Balanced half/half retrieval quota", "A plain top-k would mostly return the majority outcome", f"On the synthetic table k = 50 gave {S['retrieval_k']['k=50']['mean']:.3f} balanced accuracy against {S['retrieval_k']['k=10']['mean']:.3f} for k = 10; on real structured data k hardly matters"],
             ["Search training rows only", "Prevents a test startup from retrieving itself or its siblings (leakage)", "Retrieval accuracy is therefore an honest out-of-sample figure"],
             ["Mask the company name in the description", "Prevents a language model or embedding from using a known brand " + cite("maarouf"), "Done in clean_text before embedding"],
             ["Store models and data as files, keep state in memory", "A local single-user teaching application needs no database", "Fast start; cannot serve several users (L10)"],
             ["Demo HMAC token for the React screens", "Gives the interface a sign-in without user management", "Tampered token rejected in the edge tests; not a security design"],
             ["Pydantic ranges and a k whitelist {10, 20, 30, 50}", "Reject nonsense and oversized input before it reaches the model", "29 of 29 edge cases behave as expected (422 for out-of-range values)"],
             ["Separate real-data script instead of changing the shipped model", "The model files were trained before the real table was found; changing them was not required to measure", "Real and synthetic numbers kept apart in every table"]],
            widths=[2.0, 2.4, 2.3], align=["l", "l", "l"], size=9),
    ]


# ------------------------------------------------------------------ conclusion and future scope
def _conclusion_body():
    return [
        H2("Summary"),
        P("The project set out to predict, from historical startup data, whether an early-stage company is more likely to succeed or fail, to compare the standard classifiers on that task and to name the factors behind each prediction. "
          "The system was built and works end to end as VenturePulse: it accepts structured inputs and an optional description, returns a SUCCESS or FAILURE estimate with probabilities and a risk label, lists the main feature terms and shows the comparable historical startups that support the estimate."),
        P(f"The report measured the system honestly. The model that the application serves was trained on a {F.SYN_ROWS:,}-row synthetic fallback and scores {syn_lr()} balanced accuracy on it; that number is a pipeline check. "
          f"On the real public table of {F.REAL_ROWS} startups, under five repeated 80/20 splits, Random Forest reaches a balanced accuracy of {F.real('Random Forest')} and a ROC-AUC of {F.real('Random Forest', 'roc_auc')}, XGBoost {F.real('XGBoost')} and {F.real('XGBoost', 'roc_auc')}, "
          f"and Logistic Regression {F.real('Logistic Regression')} and {F.real('Logistic Regression', 'roc_auc')}."),
        H2("Objectives achieved"),
        TAB("The six objectives and what was achieved", ["No.", "Objective", "Outcome"],
            [["1", "Collect a startup dataset", f"Partly: the real {F.REAL_ROWS}-row public table was obtained and analysed (funding, sector, location, outcome); team background is missing; the shipped app runs on a synthetic fallback of the same schema"],
             ["2", "Clean the data and engineer features", "Partly: cleaning, imputation, scaling, one-hot encoding and log funding done; funding velocity only approximated by ages and rounds; no team-experience or market-context feature exists"],
             ["3", "Address class imbalance", f"Achieved: balanced class weights in the application and a comparison with oversampling on real data; no ROC-AUC gain, success is the majority class here"],
             ["4", "Train and compare LR, DT, RF and boosting", "Achieved: four models in the application and HistGradientBoosting in the study, under 5 x 80/20 splits"],
             ["5", "Identify separating features", "Achieved: Random Forest Gini and permutation importance and logistic-regression weights; relationships ranks first in both tree measures"],
             ["6", "Evaluate with accuracy, precision, recall, F1, ROC-AUC", "Achieved on real data; ROC-AUC of the shipped fused model was not recorded"]],
            widths=[0.5, 2.2, 4.0], align=["c", "l", "l"], size=9.5),
        H2("Key findings"),
        N(f"On real startups the tree ensembles rank above logistic regression (balanced accuracy {m(RF)} and {m(XGB)} against {m(LR)}), as the base paper claims, but at an accuracy of {m(XGB, 'accuracy')} and not at the 85-92 % it reports; Random Forest, XGBoost and HistGradientBoosting lie within one standard deviation of one another.",
          f"The table leaks: removing relationships, milestones and the two milestone-age fields lowers ROC-AUC from {auc(RF)} to {m(NOPH['Random Forest'], 'roc_auc')} for Random Forest and from {auc(XGB)} to {m(NOPH['XGBoost'], 'roc_auc')} for XGBoost, and the ensembles lose their lead.",
          f"Retrieval alone is competitive: balanced top-k voting with no trained model reaches balanced accuracy {m(RET['10'])} to {m(RET['50'])} and ROC-AUC {m(RET['10'], 'roc_auc')} to {m(RET['50'], 'roc_auc')}, equal to logistic regression, and the retrieved startups give a user something to inspect.",
          f"Imbalance handling changes recall, not ranking: class weights or oversampling leave ROC-AUC at about {auc(RF)} and balanced accuracy at 0.75 for Random Forest; the logistic-regression balanced accuracy is flat between thresholds 0.30 and 0.50 (0.71) while recall of success falls from 0.88 to 0.67.",
          "The text channel is untested on real startups: the real table has no descriptions, and the synthetic descriptions leak the class, so the 0.749 of the shipped fused model must not be read as real-world performance.",
          f"The software is sound: {F.N_TESTS} automated checks pass and a prediction takes a median of {LAT['predict_k10']['median_ms']:.0f} to {LAT['predict_k50']['median_ms']:.0f} ms on a CPU."),
        H2("Practical applications"),
        B("A screening aid that gives a first, evidence-backed view of a startup profile and shows which comparable companies and features drive it.",
          "A teaching and demonstration tool for a complete tabular machine-learning workflow: imbalance, model comparison, threshold choice, calibration and leakage checks.",
          "A starting point for a team with its own labelled startup data and time stamps, where the same pipeline can be retrained and validated out of time.",
          "It is not investment advice and not a replacement for due diligence."),
        H2("Known limitations"),
        P("The main limitations are the synthetic training data of the served model (L1), the leakage-like fields (L2), the lack of a temporal split (L3), the small single-country table with 185-row test folds (L4), the untested text channel (L5), the missing founder and market data (L6) and uncalibrated probabilities (L8). "
          "The full list L1 to L10 is given in the document on scope and limitations."),
    ]


def _future_body():
    return [
        H2("Improvements to the model"),
        N("Validate out of time: obtain founding and event dates, train on earlier cohorts and test on later ones, and drop fields recorded after the outcome window, as the reference study does with a leakage-safe temporal panel " + cite("mashhadi") + " (untested here).",
          "Add the missing inputs: founder and team experience, team size and composition, and market context, which the abstract names and the base paper's features include " + cite("base") + " (no data yet).",
          "Test the text channel on real startups: collect genuine company descriptions (for example from a public company directory under its licence) and measure the fused representation and retrieval against the structured baseline.",
          "Calibrate the probabilities (Platt or isotonic scaling with class priors) and report Brier score and reliability curves, because the class-weighted logistic regression is visibly miscalibrated on real data (L8).",
          "Add SHAP-based explanations for the tree ensembles " + cite("shap") + " in place of coefficient and importance terms, and compare them with the Gini and permutation rankings.",
          "Tune each model (grid or Bayesian search), tune alpha and k, and compare the served model choice with the study's best model; add significance tests over many more splits or repeated cross-validation.",
          "Report PR-AUC next to ROC-AUC, as the reference study does " + cite("pr", "mashhadi") + ", and evaluate cost-sensitive decision thresholds chosen by an investor's own costs."),
        H2("Improvements to the application"),
        B("Let the application select the served model from the real-data results and show its ROC-AUC on the Performance screen (L9).",
          "Warn the user when the inputs lie outside the range of the training data or when the confidence is low, and show the calibrated confidence.",
          "Accept a CSV of many startups and return a ranked list with downloadable results.",
          "Save each analysis (inputs, outcome, comparable startups) for later review, with a proper user store replacing the demo token.",
          "Show the retrieval evidence as a chart of outcomes among the nearest startups, per industry and funding stage."),
        H2("Scalability and deployment"),
        B("Serve the backend with several worker processes behind a reverse proxy, add real authentication and rate limits, and store models and analyses in a database (L10).",
          "Cache the embedding of repeated descriptions and pre-compute the training-matrix similarity index (for example approximate nearest neighbours) so that retrieval stays fast with hundreds of thousands of startups.",
          "Run a load test and a memory profile; only sequential requests were timed here.",
          "Package the application as a container image (a Dockerfile exists but was not exercised in this report) for one-command deployment."),
        H2("Further research"),
        B("Compare the retrieval-based approach with a language model that reads the retrieved startups, as in the method anchor " + cite("maarouf") + ", on the same data and protocol.",
          "Extend to richer outcome horizons (next funding, patenting, exit) as in the reference study, and to survival analysis for time-to-exit.",
          "Study fairness and bias across regions, sectors and founder groups, since a model trained on a US table may disadvantage other ecosystems.",
          "Run a user study with founders and investors on whether comparable-startup evidence and feature drivers change their decisions."),
    ]


def conclusion_blocks():
    return _conclusion_body()


def future_blocks():
    return _future_body()


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + renum(_conclusion_body(), "9")


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(_future_body(), "10")
