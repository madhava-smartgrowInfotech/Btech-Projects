"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) and 19.IEEE_Paper.pdf.

    python -m scripts.docs.build_paper            (from 8.ProjectCode; Word COM is used for the PDF)
"""

import os
import time
from decimal import ROUND_HALF_UP, Decimal

from . import facts as F
from .paper import Paper

X, R = F.X, F.REAL
DIS = F.DISEASES
BEST = F.BEST


def h(d, k):
    return X[d]["holdout"][BEST[d]][k]


def a4(x):
    return f"{x:.4f}"


def _r(x, q):
    return Decimal(str(round(x * 100, 6))).quantize(Decimal(q), ROUND_HALF_UP)


def p1(x):
    return f"{_r(x, '0.1')}%"


def p0(x):
    return f"{_r(x, '1')}%"


def sweep(d, t):
    return next(s for s in X[d]["threshold_sweep"] if abs(s["threshold"] - t) < 1e-9)


def realbest(d):
    m = max(F.MODEL_ORDER, key=lambda n: R[d]["real_cv"][n]["accuracy_mean"])
    return m, R[d]["real_cv"][m]["accuracy_mean"]


def build(path):
    cvlr = {d: X[d]["cv5"]["Logistic Regression"]["accuracy_mean"] for d in DIS}
    tr_rf = [X[d]["train_accuracy"]["Random Forest"] for d in DIS]
    te_rf = [X[d]["holdout"]["Random Forest"]["accuracy"] for d in DIS]
    sh = {d: R[d]["shipped_on_real"] for d in DIS}
    lat = F.API["latency"]
    lp = lat["POST /api/predict/diabetes"]
    conc = lat["POST /api/predict/diabetes (4 concurrent clients)"]
    realacc = {d: realbest(d)[1] for d in DIS}
    pi = {d: X[d]["perm_importance"][0] for d in DIS}
    posr = ", ".join(p0(X[d]["positive"] / X[d]["rows"]) for d in DIS)

    P = Paper()
    P.order = ["base"]   # the base paper is reference [1]
    names = [(n.title(), r) for n, r in F.STUDENTS]
    auth = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology (Autonomous)", "[City]", "[email]"] for n, r in names]
    auth.append(["B. Sruthi", "[Designation], Project Guide", "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology (Autonomous)", "[City]", "[email]"])
    P.title_block("Multi-Disease Prediction Using Machine Learning: An Intelligent Health Assistant for Diabetes, Heart, Liver and Kidney Risk", auth)
    P.begin_two_columns()

    P.abstract(
        "Chronic diseases are usually screened one at a time, and published systems rarely cover several conditions from routine laboratory values. "
        "This paper presents an Intelligent Health Assistant that screens diabetes, heart disease, liver disease and kidney disease through one web interface. "
        "For every condition, Logistic Regression, a Decision Tree, a Random Forest and an RBF Support Vector Machine are trained on standardised inputs, and the model with the highest F1-score "
        "on a stratified 80/20 hold-out is served by a FastAPI service and a React application. The four training sets are synthetic: 2,000 rows each, labelled by a linear risk rule with 8% of the labels flipped. "
        f"The served models therefore reach accuracies of {p1(h('diabetes','accuracy'))}, {p1(h('heart','accuracy'))}, {p1(h('liver','accuracy'))} and {p1(h('kidney','accuracy'))}, close to the 92% ceiling that the noise allows, "
        "and these numbers are not clinical results. Cross-validation shows Logistic Regression to be the most reliable model for every condition. "
        f"On real public data the same algorithms score {p0(min(realacc.values()))} to {p0(max(realacc.values()))}, and the served models transfer only partly. "
        "The application gives no explanations and is a demonstration, not a diagnostic tool.",
        ["healthcare analytics", "machine learning", "multi-disease prediction", "logistic regression", "support vector machine", "diabetes prediction", "risk assessment"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Diabetes, heart disease, liver disease and kidney disease are common chronic conditions whose early stages are often silent. Routine laboratory values and simple measurements such as glucose, blood pressure, "
           "cholesterol, bilirubin, creatinine and haemoglobin already carry early warning signals, and supervised learning can turn them into a risk estimate {r:salekin,islam}. "
           "Today a patient who wants these checks usually visits several specialists and takes a separate set of tests for each, and in rural centres there may be nobody to interpret the report. "
           "Late diagnosis then raises both treatment cost and mortality.")
    P.para("Published machine-learning systems mostly address one disease at a time: diabetes on the Pima data {r:sun}, kidney disease {r:islam}, liver disease {r:straw}. "
           "Multi-disease work tends to use reported symptoms instead of laboratory values {r:bangla,nahian}, and the one multi-disease web application we found covers stroke, depression and diabetes {r:multi25}. "
           "The base paper of this work studies a single condition, thyroid disease, with rigorous validation and explanations {r:base}. "
           "The gap is one pipeline that screens several conditions from routine clinical values, compares the same classical algorithms on each, and reports the evidence honestly.")
    P.para("The contributions of this paper are: (1) a web application that serves risk predictions for four conditions behind one interface; "
           "(2) a like-for-like comparison of four classical algorithms on each condition, selected by F1-score; "
           "(3) an audit of that comparison with ROC-AUC, cross-validation, ten random splits, threshold and sensitivity analysis, which changes one of the four model choices; and "
           "(4) a check on real public data that shows how far the synthetic-data results can be trusted. "
           "Section II reviews the literature, Section III gives the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All training and measurements ran on one Windows 11 desktop with an Intel Core i5-12500 processor (12 threads) and 16 GB of RAM. No GPU was used; training the 16 models takes a few seconds on the CPU.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9 with scikit-learn 1.8.0 {r:scikit}, pandas 3.0.2, NumPy 2.4.4 and joblib 1.5.3 for training; Flask 3.1.3 for the original pages; FastAPI 0.110.0 with Uvicorn 0.29.0 for the API; "
           "React 19 with Vite 8 on Node 24 for the interface; Playwright with Chrome for the screen captures.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Alam et al. {r:base} classify thyroid status (normal, hypothyroid, hyperthyroid) on the UCI thyroid data, 7,200 samples with 21 features. They train five classifiers (SVC, Random Forest, Extra Trees, AdaBoost, CatBoost) "
           "under nested cross-validation, with an outer stratified 5-fold loop for assessment and an inner 3-fold grid search for tuning, on the full feature set and on a ten-feature consensus subset. Random Forest and CatBoost reach 0.996 to 0.997 accuracy and "
           "an AUC of 0.999 to 1.000, and SVC 0.965 to 0.967. They add SHAP attributions and counterfactual what-if explanations, test SMOTE and reject it because minority recall rose by under 2%, "
           "and name class imbalance and the lack of external validation as limits. Our work borrows the idea of comparing several classical classifiers under held-out evaluation, but covers four diseases, uses a single split with fixed settings, "
           "and does not explain individual predictions.")
    P.para("**Single-disease systems.** On the Pima diabetes data, six classifiers were compared and gradient boosting was best at 81.8% accuracy, with the warning that results may hold only for that sub-population {r:sun}; the data set stems from a 1988 onset-forecasting study {r:pima}. "
           "For kidney disease, twelve classifiers gave XGBoost 0.983 accuracy {r:islam}, and an earlier study on 400 individuals reported an F1-measure of 0.993 while ranking the predictive attributes {r:salekin}. "
           "For liver disease, re-created models on the Indian Liver Patient Dataset reached about 71% to 79% accuracy and made more false-negative errors for women {r:straw}.")
    P.para("**Multi-disease systems.** A Bangla symptoms-disease set of 758 relations over 85 diseases gave 0.98 accuracy with voting ensembles and 0.97 with Random Forest {r:bangla}; a survey-based study predicted 11 common diseases from symptoms {r:nahian}. "
           "A 2025 Django application bundles separate models for stroke, student depression and diabetes and lowers the diabetes threshold to 0.2 to raise recall {r:multi25}. "
           "Selecting a model on the data used to report its error is optimistic {r:varma}, which is why the base paper nests its tuning; this project selected on one hold-out and carries that bias.")
    P.para("**Explanations, imbalance and data.** SHAP assigns each feature an additive contribution to one prediction {r:shap}, and a counterfactual explanation states the smallest change of the inputs that would alter a decision {r:wachter}; "
           "the base paper uses both and notes their computational overhead {r:base}. Oversampling with SMOTE {r:smote} was tried there and rejected. Four public benchmarks match our four conditions: Pima diabetes {r:pima} (768 patients, 8 features, physiologically impossible zeros that act as missing values), "
           "UCI Cleveland heart disease {r:cleveland} (303 instances, 13 features), the Indian Liver Patient Dataset {r:ilpd} (583 instances, 416 of them patients, 10 features) and UCI chronic kidney disease {r:ckd} (400 instances, 250 with the disease, 24 features, with missing values). "
           "They are small and incomplete, and published accuracies vary with preprocessing and split, from 81.8% on Pima {r:sun} to 0.983 on kidney data {r:islam}.")
    P.para("**Reading the base paper against this project.** Its strengths are real data, an unbiased protocol in which tuning never sees the assessment folds, class-wise reporting under imbalance and explanations that agree with endocrine physiology {r:base}. "
           "Its limits, which it states itself, are one disease, a skewed class distribution and no external validation. For a multi-disease screen the transferable lessons are the evaluation discipline and the explanation layer; "
           "this project adopts the first only in part (cross-validation and repeated splits are run afterwards, not used for selection) and not the second.")
    P.table("Summary of the reviewed work",
            ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["Alam et al. {r:base}", "5 classifiers, nested CV, SHAP", "UCI thyroid, 7,200", "Acc. 0.996-0.997", "One disease"],
             ["Zannat et al. {r:bangla}", "8 classifiers, voting", "Bangla symptoms, 85 diseases", "Acc. 0.98 (ensemble)", "Symptoms only"],
             ["Kamakshamma et al. {r:multi25}", "One model per disease, web app", "Kaggle: stroke, depression, diabetes", "Recall 94.73, 88.39, 91.02%", "Other diseases"],
             ["Sun and Sun {r:sun}", "6 classifiers", "Pima diabetes", "Boosting 81.8%", "One sub-population"],
             ["Islam et al. {r:islam}", "12 classifiers, feature reduction", "CKD, 25 variables", "XGBoost 0.983", "One disease"],
             ["Salekin, Stankovic {r:salekin}", "Attribute ranking, classifier", "400 people, 250 CKD", "F1 0.993", "Small cohort"],
             ["Straw, Wu {r:straw}", "Re-created liver models", "ILPD", "Acc. 71-79%", "Bias, no fix"]],
            [0.62, 0.78, 0.7, 0.8, 0.5], size=6.5)
    P.para("None of these combines diabetes, heart, liver and kidney risk from routine clinical values behind one interface and then audits its own model selection; that is the gap this work addresses.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Data")
    P.para("No clinical records were available when the system was built, so `generate_data.py` creates four data sets of 2,000 rows each with a fixed seed (42): diabetes (8 features), heart disease (13), liver disease (10) and kidney disease (12), "
           "8,000 rows in all. Features are drawn from clipped normal, exponential and uniform distributions with medically informed means. A hand-written linear risk score "
           "(for example 0.04 (glucose - 120) + 0.06 (BMI - 30) + 0.02 (age - 40) + 1.5 DPF + 0.03 (BP - 72) - 1.4 for diabetes) is passed through a sigmoid, thresholded at 0.5, "
           "and then **8% of the labels are flipped at random**. The label is therefore a known linear function of the inputs plus noise, and no classifier can exceed an expected accuracy of 1 - 0.08 = 92% on fresh draws. "
           f"Positive rates are {posr} for the four sets, with no missing values and no duplicates. "
           "Each set is split 80/20 with stratification (1,600 training rows, 400 test rows, seed 42). "
           "The heart rule weights age, sex, chest-pain type, blood pressure, cholesterol, exercise angina, ST depression and the number of vessels, and (negatively) maximum heart rate; the liver rule weights bilirubin, alkaline phosphatase, ALT, AST and age, and (negatively) albumin; "
           "the kidney rule weights age, blood pressure, albumin, sugar, glucose, urea and creatinine, and (negatively) specific gravity and haemoglobin. Other columns, such as insulin and skin thickness for diabetes, fasting sugar, ECG and slope for heart disease, "
           "or sodium and potassium for kidney disease, carry no weight and are noise by construction.")
    P.sub("B", "Preprocessing and models")
    P.para("The only preprocessing is a StandardScaler fitted on the training part; there is no imputation, outlier handling or feature selection, because the synthetic data needs none. "
           "Four algorithms are trained per disease with fixed settings and no tuning: Logistic Regression (maximum 1,000 iterations), a Decision Tree (depth 6), a Random Forest {r:rf} of 200 trees (depth 8) and an RBF Support Vector Machine {r:svm} (C = 1, probability outputs). "
           "Logistic Regression models p(y = 1 | x) = 1 / (1 + exp(-(w.x + b))) and minimises the log-loss; the SVM maximises a margin in the RBF feature space; the forest averages decorrelated trees.")
    P.sub("C", "Selection and evaluation")
    P.para("The model with the highest F1-score = 2PR / (P + R) on the 400-row test set is saved with its scaler and served; accuracy, precision and recall are recorded as well. "
           "The training script does not compute ROC-AUC, so we measured it afterwards, together with 5-fold cross-validation (scaler refitted inside each fold), ten different 80/20 splits, a decision-threshold sweep, "
           "permutation importance and hyper-parameter sensitivity. Permutation importance shuffles one feature of the test set 20 times and records the drop in accuracy of the served model; the threshold sweep moves the cut-off on the positive-class probability from 0.20 to 0.80 in steps of 0.05; the sensitivity runs re-train trees at depths 2 to 12, forests with 10 to 400 trees and the SVM with C from 0.1 to 100. These re-runs reproduce the served report exactly (all 16 model-disease cells match to four decimals).")
    P.sub("D", "Architecture and implementation")
    P.figure("docs/figures/paper_architecture.png", "System architecture: synthetic data and training scripts at the bottom, model files, the FastAPI service that imports the Flask module and the React interface.")
    P.para("`app.py` loads each disease's (model, scaler, feature list) bundle and the field metadata; `backend/main.py` imports it, so the API and the original Flask pages give identical predictions. "
           "Seven routes exist: health, disease list, disease detail, a real sample row, prediction, report and dataset summary. The React interface has a form for each disease with buttons that fill it from a real data row, "
           "a model-comparison page and a dataset page that warns that the data are synthetic. Nothing is stored: there is no database, no user account and no log of predictions.")
    P.figure("docs/figures/paper_flow.png", "Main flow of one prediction, from the form to the result card.")
    P.para("A request carrying every feature value is converted to numbers; a missing or non-finite value returns HTTP 422 with a message and an unknown disease returns 404. Otherwise the values are scaled, the model predicts the class, "
           "and the reported confidence is the larger class probability, which lies between 50% and 100%. It is a measure of how sure the model is of its own answer, not the probability of disease.")
    P.para("Four design decisions follow from the setting. The API imports the Flask module instead of copying it, so a model is trained and loaded in one place and the two front ends cannot disagree. "
           "The scaler is saved next to each model because a model is only valid on inputs scaled the same way. F1 rather than accuracy selects the model because the positive class is a minority in three of the four sets. "
           "The interface shows the confidence next to the model's hold-out accuracy so that a reader sees how much the figure is worth.")
    P.sub("E", "Reproducibility")
    P.para("Every number in this paper is produced by a script in the repository: `generate_data.py` (seed 42), `train_models.py`, `run_experiments.py` (ROC-AUC, confusion matrices, cross-validation, ten splits, thresholds, importance, sensitivity, timings), "
           "`real_data_check.py` (the real-data check), `api_tests.py` (the API checks and latency) and capture scripts that drive the real interface in Chrome to produce the screens. The results are written as JSON files and the documents read those files, "
           "so the text cannot drift from the measurements. The original build had no access to public data, and the Datasets page of the application says that its data are synthetic.")
    P.sub("F", "Supplementary check on real data")
    P.para("To test how far the synthetic results transfer, the same four algorithms were cross-validated (5 folds repeated 3 times, median imputation and scaling inside each fold) on Pima diabetes {r:pima} (768 rows), "
           "UCI Cleveland heart disease {r:cleveland} (303), the Indian Liver Patient Dataset {r:ilpd} (583) and UCI chronic kidney disease {r:ckd} (400, the 12 columns that match our schema), "
           "and the served models were applied to every real record after mapping the codes to ours. This check is not part of the application.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para("All numbers come from the 400-row test set of each disease (seed 42) unless stated. TABLE II lists the model that the application serves for each disease; the ranking of the other algorithms is shown in the repository's model-comparison page and in the report.")
    P.table("Hold-out metrics of the served model for each disease (synthetic data, 400 test rows)",
            ["Disease", "Model", "Acc.", "Prec.", "Rec.", "F1", "AUC"],
            [[F.NAME[d], F.SHORT[BEST[d]], a4(h(d, "accuracy")), a4(h(d, "precision")), a4(h(d, "recall")), a4(h(d, "f1")), a4(h(d, "roc_auc"))] for d in DIS],
            [0.8, 0.35, 0.45, 0.45, 0.45, 0.45, 0.45], size=7, align=["l", "c", "c", "c", "c", "c", "c"])
    P.para(f"Accuracy of {p1(min(h(d,'accuracy') for d in DIS))} to {p1(max(h(d,'accuracy') for d in DIS))} sits just under the 92% noise ceiling, so the pipeline recovers the generating rule almost as well as is possible; it says nothing yet about patients. "
           f"Logistic Regression is the served model for heart, liver and kidney disease and SVM for diabetes. The diabetes choice is fragile: SVM beats Logistic Regression by only {a4(X['diabetes']['holdout']['SVM']['f1'] - X['diabetes']['holdout']['Logistic Regression']['f1'])} in F1, "
           f"whereas 5-fold cross-validation gives accuracy {a4(cvlr['diabetes'])} for Logistic Regression and {a4(X['diabetes']['cv5']['SVM']['accuracy_mean'])} for SVM, and across ten random splits Logistic Regression has the best F1 in 10 of 10 splits for all four diseases. "
           f"Cross-validated Logistic Regression accuracy is {a4(cvlr['diabetes'])}, {a4(cvlr['heart'])}, {a4(cvlr['liver'])} and {a4(cvlr['kidney'])}. "
           f"The Random Forest fits the training part to {p1(min(tr_rf))}-{p1(max(tr_rf))} but scores {p1(min(te_rf))}-{p1(max(te_rf))} on the test part: with 8% random label noise a deeper model memorises noise. "
           "The linear model matches the linear generating rule, so this ranking is a property of the data and should not be taken to the clinic.")
    cm = {d: X[d]["confusion"][BEST[d]] for d in DIS}
    aucs = {d: [X[d]["holdout"][m]["roc_auc"] for m in ("Logistic Regression", "Random Forest", "SVM")] for d in DIS}
    spread = max(max(v) - min(v) for v in aucs.values())
    dtc = [X[d]["cv5"]["Decision Tree"]["accuracy_mean"] for d in DIS]
    cvm = lambda d, m: X[d]["cv5"][m]["accuracy_mean"]
    lr_rf = [cvm(d, "Logistic Regression") - cvm(d, "Random Forest") for d in DIS]
    lr_svm = [cvm(d, "Logistic Regression") - cvm(d, "SVM") for d in DIS]
    max_sd = max(X[d]["cv5"][m]["accuracy_std"] for d in DIS for m in F.MODEL_ORDER)
    P.para(f"Across algorithms the Decision Tree has the lowest ROC-AUC for every disease ({a4(min(X[d]['holdout']['Decision Tree']['roc_auc'] for d in DIS))} to {a4(max(X[d]['holdout']['Decision Tree']['roc_auc'] for d in DIS))}), "
           f"while Logistic Regression, Random Forest and SVM lie within {spread:.3f} of each other for each disease. In 5-fold cross-validation the Decision Tree is also the weakest on accuracy ({a4(min(dtc))} to {a4(max(dtc))}) and its depth-6 setting over-fits the label noise; "
           f"Logistic Regression leads the Random Forest by {min(lr_rf):.3f} to {max(lr_rf):.3f} and the SVM by {min(lr_svm):.3f} to {max(lr_svm):.3f} in cross-validated accuracy, "
           f"margins of about one to several fold-to-fold standard deviations (at most {max_sd:.3f}), so the linear model is ahead on this data, clearly over the forest and narrowly over the SVM.")
    P.para("The error profile differs by disease. Confusion counts of the served models (true negatives, false positives, false negatives, true positives) are "
           + "; ".join(f"{F.NAME[d].lower()} {cm[d][0][0]}, {cm[d][0][1]}, {cm[d][1][0]}, {cm[d][1][1]}" for d in DIS)
           + f". The heart model over-calls ({cm['heart'][0][1]} false positives against {cm['heart'][1][0]} false negatives), as {p0(X['heart']['positive']/X['heart']['rows'])} of its rows are positive; "
           f"the liver model under-calls ({cm['liver'][1][0]} false negatives against {cm['liver'][0][1]} false positives) with {p0(X['liver']['positive']/X['liver']['rows'])} positives. "
           "Tuning would change little: trees peak at depth 4 to 8 and degrade beyond it, forest accuracy is flat above 50 trees, and the SVM is best at C of 0.3 to 1 and drops to 77% to 83% at C = 100; "
           "the fixed settings lie on the plateau, but no grid search was run.")
    P.figure("docs/figures/paper_results.png", "Accuracy of the served model on the synthetic hold-out, of the best algorithm cross-validated on real public data, of the served model on the real records, and the majority-class rate.")
    P.para(f"**Threshold and drivers.** The application uses the 0.5 rule. A sweep from 0.20 to 0.80 changes little: the best F1 is at 0.5 for diabetes, liver and kidney disease and at 0.55 for heart disease ({a4(sweep('heart',0.55)['f1'])} against {a4(sweep('heart',0.5)['f1'])}). "
           f"Recall of 0.90 is reached for diabetes only at threshold 0.20 and a precision of {a4(sweep('diabetes',0.2)['precision'])}, and never for liver disease, whose recall is {a4(h('liver','recall'))}. "
           f"Permutation importance ranks {pi['diabetes']['feature']} first for diabetes ({pi['diabetes']['mean']:.3f} accuracy drop), {pi['heart']['feature']} for heart disease ({pi['heart']['mean']:.3f}), "
           f"{pi['liver']['feature']} for liver disease ({pi['liver']['mean']:.3f}) and {pi['kidney']['feature']} for kidney disease ({pi['kidney']['mean']:.3f}); these are the inputs that carry weight in the generating rule. "
           "This analysis was run offline: the application does not show it.")
    P.para(f"**Real data.** On the public data the best of the four algorithms scores {p1(realacc['diabetes'])} (diabetes, {realbest('diabetes')[0]}), {p1(realacc['heart'])} (heart, {realbest('heart')[0]}), {p1(realacc['liver'])} (liver, {realbest('liver')[0]}) and {p1(realacc['kidney'])} (kidney, {realbest('kidney')[0]}), "
           f"below the synthetic figures, markedly so for diabetes and liver disease. The served models, applied to the real records, reach accuracies of {p1(sh['diabetes']['accuracy'])}, {p1(sh['heart']['accuracy'])}, {p1(sh['liver']['accuracy'])} and {p1(sh['kidney']['accuracy'])} "
           f"with ROC-AUC {sh['diabetes']['roc_auc']:.2f}, {sh['heart']['roc_auc']:.2f}, {sh['liver']['roc_auc']:.2f} and {sh['kidney']['roc_auc']:.2f}. "
           f"The ranking of risk therefore carries over, but the 0.5 rule does not: for liver disease the accuracy of {p1(sh['liver']['accuracy'])} is below the {p1(R['liver']['majority_rate'])} obtained by always predicting the majority class. "
           "The kidney set is almost separable, and these real-data numbers are the better guide to how the method behaves on patients.")
    P.table("Real public data: cross-validated best algorithm and the served model applied to the real records",
            ["Disease", "Rows", "Best CV acc.", "Served acc.", "Served AUC", "Majority"],
            [[F.NAME[d], R[d]["rows"], p1(realacc[d]), p1(sh[d]["accuracy"]), f"{sh[d]['roc_auc']:.3f}", p1(R[d]["majority_rate"])] for d in DIS],
            [0.9, 0.4, 0.55, 0.5, 0.5, 0.5], size=7, align=["l", "c", "c", "c", "c", "c"])
    P.para("**Comparison with the base paper.** The base paper reports 0.996 to 0.997 accuracy on 7,200 real thyroid records with nested cross-validation and SHAP {r:base}. Our figures are not comparable: the disease, the data (real versus synthetic), "
           "the number of classes (three versus two), the protocol (nested cross-validation with tuning versus one split with fixed settings) and the explanation layer all differ. "
           "Our real-data cross-validated accuracies of 72% to 99% are the closest analogue, and they show how much lower results on noisy real clinical data can be than on a clean benchmark.")
    P.para("**Output screens.** Fig. 4 and Fig. 5 are captures of the running application. Each prediction page offers a button that fills the form from a real row of the training file, shows beside every field the training range of that feature, "
           "warns when a typed value falls outside it (a glucose of 900, for example), marks every empty required field when the form is submitted, and shows a result card with the class, the confidence bar, the model used and its hold-out accuracy together with a notice "
           "that the estimate is not a diagnosis. The layout also works on a 390-pixel phone screen. The comparison page lets a reader sort the four algorithms by any metric.")
    P.figure("docs/figures/paper_screen_predict.png", "Output screen: diabetes prediction for a real data row, showing the inputs with their training ranges and the result card (High Risk, 90.71% confidence, SVM, 89.5% hold-out accuracy).")
    P.figure("docs/figures/paper_screen_models.png", "Output screen: model-comparison page, with accuracy, precision, recall and F1 of the four algorithms for diabetes and the selected model marked.")
    P.figure("docs/figures/paper_stability.png", "Mean test accuracy of the four algorithms over ten random 80/20 splits (dots with one standard deviation) and on the seed-42 split (crosses); the dashed line is the 92% ceiling.")
    tm = {m: [X[d]["timing"][m] for d in DIS] for m in F.MODEL_ORDER}
    P.para(f"**Cost.** Fitting is cheap: Logistic Regression takes {min(t['fit_s'] for t in tm['Logistic Regression'])*1000:.0f} to {max(t['fit_s'] for t in tm['Logistic Regression'])*1000:.0f} ms per disease, the SVM {min(t['fit_s'] for t in tm['SVM']):.2f} to {max(t['fit_s'] for t in tm['SVM']):.2f} s "
           f"and the Random Forest {min(t['fit_s'] for t in tm['Random Forest']):.2f} to {max(t['fit_s'] for t in tm['Random Forest']):.2f} s on the CPU described in Section I-A. Scoring one row takes under {max(t['predict_ms_per_row'] for m in tm for t in tm[m]):.2f} ms in process, "
           "so the model is never the bottleneck of a request; the linear model is also the cheapest to store and the easiest to audit.")
    P.para("**Threats to validity.** The models were selected on the same 400 rows that report their accuracy, which biases the figures upward {r:varma}; the hold-out is small (one point of accuracy is four rows); "
           "the synthetic labels follow a linear rule, which favours linear models; the reported confidence is not calibrated; and nothing was validated externally or with clinicians. "
           "The ten-split and cross-validation figures in Fig. 6 reduce the first problem but not the others.")
    P.para(f"**Failure cases and tests.** For a heart record labelled low risk, the model returned High Risk with 99.53% confidence, a false positive that the confidence figure does not warn about. "
           f"The API accepts impossible values such as a glucose of 100,000 mg/dL (answered High Risk, 60.94%) because only the interface warns about values outside the training range, and nothing is imputed. "
           f"The {F.API_CHECKS[1]} API checks (functional, validation, consistency with direct model calls, sanity) passed, as did a {F.SMOKE_CHECKS}-check smoke test; there is no unit-test suite, no user study and no clinical validation. "
           f"Median latency of a prediction request on the local machine was {lp['p50_ms']:.1f} ms (95th percentile {lp['p95_ms']:.1f} ms), and {conc['throughput_rps']:.0f} requests per second with four concurrent clients, measured while the PC was busy and with coarse timer resolution, so they are upper bounds.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("The Intelligent Health Assistant delivers what the objectives ask for in its core: four algorithms were trained and compared for each of four diseases and one web interface serves the selected models. "
           "Several objectives are met only in part: the data are synthetic rather than benchmark data, no missing-value or outlier handling exists, ROC-AUC was not part of the selection, and the application does not show which parameters drove a prediction. "
           "The key finding is that on this data a plain Logistic Regression is the most reliable model for every disease, that the shipped diabetes choice rests on a difference inside the noise, "
           "and that accuracy near 90% on synthetic data falls to 72% to 84% on three of the four real sets and, for the served liver model, below the majority-class baseline.")
    P.para("Measured against the six stated objectives, two are achieved (training and comparing the four algorithms for each disease, and serving the selected models behind one interface) and four only in part (benchmark data, preprocessing, selection by ROC-AUC, and showing the parameters that drove each prediction). "
           "The abstract's promised health recommendations are not implemented. The system is therefore best described as a working demonstration of a multi-disease screening pipeline together with an honest audit of its own evidence.")
    P.para("Limitations are the synthetic data, model selection on the test set, uncalibrated confidence values, no range validation and no explanations. "
           "Future work: train on the real benchmark data with imputation and nested cross-validation as in the base paper {r:base}; add SHAP {r:shap} and counterfactual {r:wachter} explanations and show the driving parameters; "
           "calibrate the probabilities and tune thresholds per disease, testing SMOTE {r:smote} only if it helps; add range validation, authentication and an audit log; and validate with clinicians before any real use.")

    P.para("**Responsible use.** The application stores no patient data, shows a not-a-diagnosis notice on every result and states on its dataset page that the training data are synthetic. "
           "Even with real data, a screening aid of this kind should be introduced with clinical oversight, a stated intended use and monitoring of its errors for different groups of patients, since the liver study cited above found a higher false-negative rate in women {r:straw}.")

    P.references()
    P.save(path)
    return path, len(P.order)


def to_pdf(docx, pdf):
    """Convert with Word COM (under an exclusive lock shared with the other builders) and return the page count."""
    import pymupdf as fitz
    import win32com.client

    lock = r"C:\Users\Admin\AppData\Local\Temp\claude\D--abstracts-Madhav-CSE-A-CSE-A-A3\82ceb427-d353-4745-ad1c-1763a1ac520f\scratchpad\com.lock"
    for _ in range(60):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL)
            os.close(fd)
            break
        except FileExistsError:
            time.sleep(10)
    else:
        raise RuntimeError("could not get the Word COM lock")
    try:
        word = None
        for attempt in range(4):
            try:
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0
                doc = word.Documents.Open(os.path.abspath(docx), ReadOnly=True, AddToRecentFiles=False)
                doc.ExportAsFixedFormat(os.path.abspath(pdf), 17)
                doc.Close(False)
                break
            except Exception as e:
                print("retry", type(e).__name__, str(e)[:80])
                time.sleep(10)
            finally:
                if word is not None:
                    try:
                        word.Quit()
                    except Exception:
                        pass
                    word = None
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass
    with fitz.open(pdf) as d:
        return d.page_count


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    os.chdir(F.CODE)
    print(build(out))
    print("pages:", to_pdf(out, os.path.join(F.BATCH, "19.IEEE_Paper.pdf")))
