"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) and 19.IEEE_Paper.pdf.

    python -m scripts.docs.build_paper
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper

EX = F.EXTRA
CW, CV, SPL = F.CW, F.CV, F.SPL


def crop_shot(name, out, box):
    p = os.path.join(F.FIGS, out)
    Image.open(F.shot(name)).convert("RGB").crop(box).save(p)
    return p


def sw(t):
    return next(s for s in EX["threshold_sweep"] if abs(s["threshold"] - t) < 1e-9)


def lf(x):
    return next(s for s in EX["targeting_lift"] if abs(s["top_fraction"] - x) < 1e-9)


def build(path):
    lr, dt, rf, gb, hgb = (CW[n] for n in F.MODEL_ORDER)
    m15rf = F.M15["app_default_split"]["class_weight"]["models"]["Random Forest"]
    none, smo = F.NONE, F.SMOTE
    cvlr, cvrf, cvdt = CV["Logistic Regression"], CV["Random Forest"], CV["Decision Tree"]
    spl_lr, spl_rf = SPL["Logistic Regression"], SPL["Random Forest"]
    imp = F.M["importance"]["model_importance"]
    n_train_churn = F.DS["class_distribution"]["counts"]["1"] - F.SP["test_churners"]
    n_train_stay = F.SP["train_rows"] - n_train_churn
    w1, w0 = F.SP["train_rows"] / (2 * n_train_churn), F.SP["train_rows"] / (2 * n_train_stay)
    api = F.API["repeated_ms"]
    L = F.LAT
    rb = F.RISK["counts"]

    P = Paper()
    auth = [[n.title(), f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology (Autonomous)", "[City]", "[email]"] for n, r in F.STUDENTS]
    auth[2][0] = "B Sandeep"
    auth.append(["B. Srikanth", "Assistant Professor", "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology (Autonomous)", "[City]", "[email]"])
    P.title_block("Customer Churn Prediction in Telecom Industry: A Machine Learning Based Customer Retention System", auth)
    P.begin_two_columns()

    P.abstract(
        "Telecom operators lose revenue when customers leave, and a churn score without a reason gives a retention team nothing to act on. This paper presents ChurnIQ, "
        "an end-to-end customer retention system: a scikit-learn pipeline that imputes, scales and encodes customer records, handles class imbalance with class weights or SMOTE, "
        "trains and compares Logistic Regression, Decision Tree and Random Forest classifiers, groups customers into editable risk bands, explains each score through its largest drivers "
        "and turns them into rule-based retention actions, behind a FastAPI service and a React interface. No real operator data were available, so all experiments use 1,000 synthetic "
        f"customers with the public Telco schema and {F.DS['churn_rate_pct']} % churn. On a 200-row test split Logistic Regression reaches F1 {F.f3(lr['f1_score'])} and ROC-AUC {F.f3(lr['roc_auc'])}; "
        "cross-validation and repeated splits show spreads of 0.03 to 0.10, so the leading models are not separable. Probabilities are not calibrated, SHAP was not exercised and the "
        "retention rules were not evaluated on campaign data. The results are not comparable with the real-data results of the base paper.",
        ["churn prediction", "customer retention", "explainable AI", "imbalanced data", "machine learning", "random forest", "telecom analytics"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Customer churn, the loss of subscribers to a competitor, is the main way a telecom operator's customer base erodes {r:oprea}, and retaining a customer is generally treated as cheaper "
           "than acquiring a new one {r:ahmad,vafeiadis}. Operators already hold early signals of churn in their records: tenure, contract type, monthly charges, the services taken and the "
           "way the bill is paid. Machine learning turns these records into a churn probability, and comparisons of standard classifiers on this task are well established {r:vafeiadis,sikri,elattar}.")
    P.para("Two practical problems remain. A bare score gives a retention team nothing to act on: it does not say why a customer is at risk or what to offer, which is why recent work adds "
           "explanation methods such as SHAP {r:lundberg} and perturbation-based explainers {r:oprea}. And because churners are a minority (26.5 % of the public Telco data {r:telco}), a classifier can "
           "reach a high accuracy while missing most of them, so the metric and the handling of imbalance decide the outcome {r:hegarcia}. Most studies stop at a table of metrics; few deliver an "
           "application that scores every customer, shows the drivers of each score and maps them to actions.")
    P.para("The problem addressed is therefore: given a table of customer records, estimate for every customer the probability of leaving, group customers into risk bands, show which attributes drive each "
           "prediction and turn the result into a concrete retention action, in an application that an analyst can run without writing code and with metrics that are not fooled by class imbalance.")
    P.para("This paper describes ChurnIQ, an applied extension of the motivation of the base paper {r:oprea}, and makes four contributions: (1) a tested pipeline from a customer CSV to a ranked, "
           "banded customer list, with class weights or SMOTE {r:smote} for imbalance and model selection on F1; (2) per-customer explanation and a transparent rule-based retention engine; "
           "(3) a FastAPI service and a React interface over one shared core, with batch scoring and a drift check; and (4) a measured baseline that reports cross-validation spreads, "
           "calibration and decision-threshold behaviour beside the headline metrics, on clearly declared synthetic data. Section II reviews related work, Section III describes the method, "
           "Section IV reports the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All measurements were taken on one desktop: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11, no GPU.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11, scikit-learn 1.9.1 {r:sklearn}, pandas 3.0.6, imbalanced-learn, FastAPI 0.143.3 {r:fastapi}, React 19 with Vite 8 for the interface, and pytest for testing.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Oprea and Bara {r:oprea} ask which customer attributes matter most for retention and how to find them quickly. They run four perturbation-based explainers on a trained "
           "churn model (random noise perturbation, feature ablation, input marginalization and adversarial perturbation), combine them into one importance score and keep rows with a positive recall drop. "
           "On the Telco data (7,043 customers, 21 columns, 26.5 % churn; 70/30 split, 2,113 test rows) they compare Logistic Regression, SVC, Random Forest, Balanced Random Forest, CatBoost, XGBoost "
           "and LightGBM with recall as the primary objective; recall reaches 0.9077 for CatBoost at a precision of 0.4719. Their unified score agrees with SHAP (Spearman 0.8125, Kendall 0.7126, "
           "Jaccard 0.6885) and is much faster (18.5 s against 289.4 s for SHAP and 35.1 s for LIME in their setting). They find month-to-month contracts, monthly charges above about $90 and "
           "tenure below about 20 months to carry the highest risk, propose CRM integration as a decision-support layer, and state that their conclusions depend on recall as the objective "
           "and on a structured, moderate-dimensional data set.")
    P.para("**Churn prediction.** Comparisons of classifiers on churn data are the norm {r:vafeiadis} and have been extended to big-data platforms {r:ahmad}. Sikri et al. {r:sikri} add a ratio-based "
           "balancing step for imbalanced churn data and find ensembles better than single models, XGBoost at a 75:25 ratio being best on their measures. El Attar and El-Hajj {r:elattar} compare eight "
           "models on the Telco data (80/20 split) with SHAP feature analysis and report XGBoost at accuracy 0.84 and ROC-AUC 0.932 against 0.78 and 0.864 for Logistic Regression; Rasool et al. {r:rasool} "
           "report accuracy 94.75 %, recall 73.20 % and F1 80.23 % for a stacking ensemble with SHAP on a 3,333-customer data set. Explainable churn models have also been built with monotonic decision rules "
           "{r:szelag} and with leverage-point analysis {r:wang}. These figures are quoted as reported; the studies differ in data, split and balancing and cannot be ranked against one another or against this work.")
    P.para("**Explaining predictions.** SHAP {r:lundberg} attributes a prediction to features with Shapley values and has a fast exact form for trees {r:treeshap}; LIME {r:ribeiro} fits a local surrogate model. "
           "Both are perturbation-based, are costly or less consistent in the comparison of {r:oprea}, and can be fooled by adversarial models {r:slack}, so an explanation describes a model and not the customer's reasons.")
    P.table("Representative work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        ["{r:oprea}", "4 perturbation explainers vs SHAP, LIME; 7 classifiers", "Telco, 7,043 rows", "Recall up to 0.9077; Spearman 0.8125 with SHAP", "One data set; recall-only objective"],
        ["{r:sikri}", "Ratio-based balancing, ensembles", "Imbalanced telecom churn", "XGBoost best at 75:25 ratio", "Abstract-level reading; no explanation described"],
        ["{r:elattar}", "8 models, SHAP", "Telco, 80/20", "XGBoost acc. 0.84, AUC 0.932", "Single data set; SHAP not causal"],
        ["{r:rasool}", "Stacking, SHAP", "3,333 customers", "Acc. 94.75 %, recall 73.20 %", "No temporal model"],
        ["{r:lundberg}", "Shapley attributions", "Method paper", "Unifies attribution methods", "289.4 s in {r:oprea}"],
        ["{r:ribeiro}", "Local surrogate model", "Method paper", "Local explanations of any classifier", "Lower consistency than SHAP in {r:oprea}"],
        ["{r:slack}", "Adversarial attack on explainers", "Method paper", "Explainers can be fooled", "Read explanations with caution"],
    ], widths=[0.3, 0.8, 0.65, 0.85, 0.8], size=7, align=["c", "l", "l", "l", "l"])
    P.para("**Imbalance and classifier families.** Churners are a minority, and the usual remedies are cost-sensitive learning and resampling; He and Garcia {r:hegarcia} survey them, and SMOTE {r:smote} "
           "creates synthetic minority examples by interpolation. The classifier families in the churn literature are linear models, decision trees, random forests {r:breiman} and gradient boosting {r:friedman}, "
           "the last being the family behind the XGBoost, LightGBM and CatBoost models of the base paper. This work uses the first three as its required set because their behaviour can be read "
           "directly, and adds two scikit-learn boosting models as options.")
    P.para("**Positioning.** The base paper {r:oprea} answers how to explain a churn model quickly and recommends integration into a CRM as a decision-support layer; the studies of classifier performance "
           "{r:sikri,elattar,rasool} answer how accurate a model can be on one data set. This work takes the explanation motivation of the first and the comparison practice of the second and builds the "
           "missing layer between them: an application that scores, bands, explains and recommends, and whose evaluation states its own uncertainty.")
    P.para("**Gap.** The surveyed work compares classifiers or explainers on churn data. Few papers pair accurate prediction with a working application that scores every customer, explains each score and links "
           "the drivers to actions that can be audited, and the reported numbers depend so strongly on split, balancing and data set that a single-split metric can mislead. This paper addresses the application "
           "and reports the spreads.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Pipeline.** A customer CSV (or the generated sample) is validated and its target and identifier columns are detected; the data are split in a stratified 80/20 ratio, a preprocessor is fitted on "
           "the training split only, imbalance is handled, models are trained and compared, the best is saved, and every customer is scored and placed in a risk band with drivers and actions. "
           "Fig. 1 shows the architecture and Fig. 2 the main flow.")
    P.figure(F.fig("paper_architecture.png"), "Architecture of ChurnIQ: two interfaces, a FastAPI service, the pure-Python core src/ and the data and state.")
    P.figure(F.fig("paper_flow.png"), "Main flow from a customer table to explained, banded customers.")
    P.para(f"**Data.** The public Telco data {{r:telco}} were not used because no real operator data were available to the team; the generator in the project (src/sample_data.py, seed 42) produces {F.DS['rows']:,} customers with the same 21 columns "
           f"(4 numeric and 15 categorical features). Churn is drawn from a latent risk score that grows with month-to-month contracts, fibre-optic service, electronic-check payment, missing support add-ons and higher "
           f"charges and falls with tenure (55 % of customers are on month-to-month contracts, 44 % have fibre optic and 34 % pay by electronic check), plus Gaussian noise; the churn rate is {F.DS['churn_rate_pct']} %. Models trained on it can recover these effects, which checks the pipeline but says nothing about real customers.")
    P.para(f"**Preprocessing and imbalance.** Numeric fields get median imputation and standardisation; categorical fields get most-frequent imputation and one-hot encoding, giving {F.SP['encoded_feature_count']} inputs. "
           f"The split gives {F.SP['train_rows']} training and {F.SP['test_rows']} test rows ({F.SP['test_churners']} churners). Class weights set w_c = n / (2 n_c), i.e. {w1:.3f} for churners and {w0:.3f} for retained customers; "
           "SMOTE {r:smote} interpolates between minority neighbours on the transformed training split only; a third option applies no handling.")
    P.para("**Models.** Logistic Regression models P(churn | x) = 1 / (1 + exp(-(b0 + w.x))) and, with standardised inputs, w_j x_j is the contribution of feature j. A Decision Tree (depth 8, at least 10 customers "
           "per leaf) splits on Gini impurity. A Random Forest {r:breiman} averages 300 trees (depth 12, leaf 5). Gradient Boosting {r:friedman} (200 trees, depth 3, rate 0.08) and Histogram Gradient Boosting "
           "are optional. All come from scikit-learn {r:sklearn} with fixed settings and no hyper-parameter search. The model is chosen on F1 and not on accuracy, because with 26 % churners a model that never "
           "predicts churn is 74 % accurate. Metrics are accuracy, precision, recall, F1 and ROC-AUC on the held-out split.")
    P.para("**Evaluation protocol.** With TP, FP, TN and FN the counts of the confusion matrix and churn as the positive class, precision = TP / (TP + FP), recall = TP / (TP + FN) and "
           "F1 = 2 P R / (P + R); ROC-AUC is the probability that a random churner is scored above a random retained customer. Because one split of 200 rows is noisy, the three required models are also "
           "evaluated by stratified 5-fold cross-validation (200 held-out rows per fold) and on five random 80/20 splits (seeds 0 to 4), and the mean and standard deviation are reported. Imbalance handling "
           "is compared by repeating the single-split experiment with class weights, SMOTE and no handling. The decision threshold and the calibration of the scores are examined on the test "
           "predictions of the saved Logistic Regression model.")
    P.para("**Risk bands and actions.** The probability (predict_proba x 100) is placed in Low (below 30), Medium, High (60 to 80) or Critical (80 and above) with thresholds that the user can edit and the server validates. "
           "Nine of ten IF/THEN retention rules (for example a month-to-month contract, no tech support, monthly charges of 80 or more, electronic check, tenure of 6 months or less) fire only at a probability of 60 or more; "
           "the tenth fires in the Critical band, and each suggestion carries its reason.")
    P.para("**Explanation.** Global importance uses coefficients or tree importances and permutation importance (at most 300 test rows, 5 repeats). The local explanation multiplies each feature's weight by its "
           "standardised value and lists the five largest positive and negative contributions; an optional SHAP path exists but SHAP was not installed, so it was not exercised. A what-if page re-scores a customer "
           "after attribute changes; a batch page scores a CSV (predicted churn at 50 % or more) and a drift check compares new data with the training data.")
    P.para("**Design decisions.** All logic lives in the pure-Python core src/, which imports nothing from either interface, so the Streamlit pages and the FastAPI routes cannot disagree; the preprocessor is "
           "fitted on the training split only and SMOTE touches only the training split, so no test information leaks; settings and uploads are validated on the server and refused with 401, 404, 409 or 422 and a "
           "plain message; and nothing leaves the machine: no external service, no language model and no database server. The cost of this simplicity is a single-user, in-memory design.")
    P.para("**Batch scoring and monitoring.** A batch file must contain the feature columns the active model was trained on; otherwise the service answers 422 and names the missing columns. The output has the "
           "customer identifier, the probability, predicted churn (probability of 50 or more), the risk band and, optionally, the three largest risk factors; a 25-row template can be downloaded. "
           "The drift check compares a new file with the training data: missing columns, the percentage of missing values (flagged above 10 %), categories not seen in training, the shift of each numeric mean "
           "and the churn rate of the new file. It is a screening tool and computes no statistical drift test.")
    P.para("**Implementation.** The FastAPI layer has 31 route handlers, bearer-token authentication (HMAC-SHA256, 12 h), server-side validation and an in-memory state; only the active model "
           f"is saved (joblib) and restored. The React interface has {F.N_PAGES} pages. {F.TESTS['pytest']} unit tests and a {F.TESTS['smoke']}-check end-to-end API test pass.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** All numbers come from scripts that call the project's own functions: {F.DS['rows']:,} synthetic customers, stratified 80/20 split with seed 42, class weights, a {F.SP['test_rows']}-row "
           f"test set with {F.SP['test_churners']} churners, scikit-learn 1.9.1 and pandas 3.0.6. Table II gives the five models. Logistic Regression is the best on F1, ROC-AUC and recall and is the saved model; "
           f"Gradient Boosting has the highest accuracy ({F.f3(gb['accuracy'])}) and precision ({F.f3(gb['precision'])}) but a recall of only {F.f3(gb['recall'])}, and the Decision Tree is the weakest of the three required models.")
    P.table("Test-split metrics (80/20, seed 42, class weights)", ["Model", "Acc.", "Prec.", "Rec.", "F1", "AUC"],
            [[n, *[f"{CW[n][k]:.3f}" for k in ("accuracy", "precision", "recall", "f1_score", "roc_auc")]] for n in F.MODEL_ORDER],
            widths=[1.35, 0.4, 0.4, 0.4, 0.4, 0.4], size=7.5, align=["l", "c", "c", "c", "c", "c"])
    P.figure(F.fig("paper_model_comparison.png"), "Accuracy, precision, recall, F1 and ROC-AUC of the three required models on the test split.")
    P.para(f"**Portfolio and speed.** The saved model places the 1,000 customers in the four bands as {rb['Low Risk']}, {rb['Medium Risk']}, {rb['High Risk']} and {rb['Critical Risk']} (Figs. 4 and 5). "
           f"Training all five models takes {F.M['app_default_split']['class_weight']['wall_seconds']} s, scoring one customer a median {L['single_customer_median']} ms and all 1,000 customers {L['full_dataset_1000_rows_ms']} ms; "
           f"API responses over 127.0.0.1 have a median of {api['whatif']['median']:.0f} to {api['dashboard']['median']:.0f} ms for what-if, Customer 360 and the dashboard.")
    P.figure(crop_shot("10_customer360.png", "paper_cust360.png", (950, 520, 1415, 900)), "Output screen: retention actions of Customer 360 for the top-ranked customer, each with the reason that triggered it.")
    P.para(f"**Confusion matrices.** At the default 0.50 cut-off Logistic Regression finds {lr['confusion_matrix'][1][1]} of the 53 churners and raises {lr['confusion_matrix'][0][1]} false alarms; "
           f"Random Forest finds {rf['confusion_matrix'][1][1]} with {rf['confusion_matrix'][0][1]} false alarms, the Decision Tree {dt['confusion_matrix'][1][1]} with {dt['confusion_matrix'][0][1]}, "
           f"Gradient Boosting {gb['confusion_matrix'][1][1]} with {gb['confusion_matrix'][0][1]} and Histogram Gradient Boosting {hgb['confusion_matrix'][1][1]} with {hgb['confusion_matrix'][0][1]}. "
           "The choice between them is a trade-off between wasted offers and lost customers.")
    P.para(f"**Risk bands and a worked example.** Because class weights raise every score (mean {F.RISK['avg_probability']} % against {F.DS['churn_rate_pct']} % real churn), "
           f"{rb['High Risk'] + rb['Critical Risk']} customers ({(rb['High Risk'] + rb['Critical Risk']) / 10:.1f} %) fall in the High or Critical bands; the bands rank customers and are not chances of leaving. "
           "Fig. 4 shows the retention actions that Customer 360 gives the highest-ranked customer, scored 92.1 % (Critical, tenure 4 months, recorded outcome churned): the month-to-month contract, the missing tech-support "
           "add-on and the missing online-security add-on each trigger a rule, and each suggestion is shown with its reason so that an agent can accept or reject it.")
    P.figure(crop_shot("04_dashboard.png", "paper_dashboard.png", (862, 456, 1415, 868)), "Output screen: customers per risk band at the default 30/60/80 thresholds.")
    P.para(f"**Stability (Fig. 6).** A 200-row test split is noisy. In 5-fold cross-validation the F1 of Logistic Regression is {cvlr['f1_score']['mean']:.3f} ± {cvlr['f1_score']['std']:.3f} and of Random Forest "
           f"{cvrf['f1_score']['mean']:.3f} ± {cvrf['f1_score']['std']:.3f} (Decision Tree {cvdt['f1_score']['mean']:.3f} ± {cvdt['f1_score']['std']:.3f}); ROC-AUC is {cvlr['roc_auc']['mean']:.3f} ± {cvlr['roc_auc']['std']:.3f} "
           f"and {cvrf['roc_auc']['mean']:.3f} ± {cvrf['roc_auc']['std']:.3f}. Over five random splits the F1 is {spl_lr['f1_score']['mean']:.3f} ± {spl_lr['f1_score']['std']:.3f} and {spl_rf['f1_score']['mean']:.3f} ± {spl_rf['f1_score']['std']:.3f}. "
           "Logistic Regression and Random Forest are within one standard deviation of each other, so the data do not support calling either one better; ROC-AUC of about 0.70 to 0.72 is a moderate ranking ability, not a strong one.")
    P.figure(F.fig("paper_stability.png"), "F1-score of the three required models on the single split, in 5-fold cross-validation and on five random splits (bars: one standard deviation).")
    P.para(f"**Imbalance.** Without any handling, accuracy looks fine ({F.f3(none['Logistic Regression']['accuracy'])} for Logistic Regression, {F.f3(none['Random Forest']['accuracy'])} for Random Forest) but recall "
           f"collapses to {F.f3(none['Logistic Regression']['recall'])} and {F.f3(none['Random Forest']['recall'])}. SMOTE gives the best single-split F1 for Logistic Regression ({F.f3(smo['Logistic Regression']['f1_score'])}) "
           "but was tried on one split only and is not claimed to beat class weights.")
    P.para(f"**Drivers.** The largest Logistic Regression coefficients are contract type (month-to-month {imp[0]['importance']:.3f}, two-year {imp[1]['importance']:.3f}), monthly charges ({imp[2]['importance']:.3f}) "
           f"and tenure ({imp[4]['importance']:.3f}); permutation importance is led by monthly charges (0.042) and month-to-month contracts (0.028). These are the effects built into the generator, so they confirm the "
           "pipeline, and they match the drivers reported for real data in the base paper {r:oprea} only in the sense that both contain them.")
    P.para(f"**Threshold, calibration and targeting (Fig. 7).** At the 50 % cut-off of the batch table precision is {F.f3(sw(0.5)['precision'])}, recall {F.f3(sw(0.5)['recall'])} and F1 {F.f3(sw(0.5)['f1'])}; F1 stays between "
           f"{F.f3(sw(0.4)['f1'])} and {F.f3(sw(0.6)['f1'])} from 0.40 to 0.60, while at 0.30 recall is {F.f3(sw(0.3)['recall'])} but precision {F.f3(sw(0.3)['precision'])}. "
           f"The probabilities are not calibrated: the mean prediction is {EX['mean_predicted_probability']:.3f} against an observed rate of {EX['observed_churn_rate_test']:.3f} and the Brier score "
           f"is {EX['brier_score']:.3f}, no better than the {EX['brier_no_skill_constant_base_rate']:.3f} of a constant predictor, so scores are rankings. Contacting the top 20 % of customers (40) reaches "
           f"{lf(0.2)['churners_captured']} of the 53 churners ({lf(0.2)['capture_rate'] * 100:.1f} %, lift {lf(0.2)['lift']:.2f}); the top 10 % (20 customers) contain {lf(0.1)['churners_captured']} "
           f"(precision {lf(0.1)['precision']:.2f}) and the top 50 % contain {lf(0.5)['churners_captured']} ({lf(0.5)['capture_rate'] * 100:.1f} %). A lift of 1.5 to 2 is a moderate gain, and with 20 to 100 contacts the counts are small.")
    P.figure(F.fig("paper_threshold_calibration.png"), "Left: precision, recall and F1 of Logistic Regression against the decision threshold. Right: reliability of the predicted probabilities.")
    P.para(f"**Comparison with the base paper.** The data differ: the base paper {{r:oprea}} uses the real 7,043-row Telco data with a 2,113-row test set and boosted models tuned for recall, "
           f"whereas this work uses 1,000 synthetic customers, a 200-row test set and untuned scikit-learn models. Its accuracy of 0.699 to 0.793 and recall of 0.411 to 0.908 and this work's accuracy of "
           f"{F.f3(dt['accuracy'])} to {F.f3(gb['accuracy'])} and recall of {F.f3(hgb['recall'])} to {F.f3(lr['recall'])} are therefore not comparable, and no claim is made to match or beat them. "
           "The base paper's unified perturbation explainer and LIME were not implemented.")
    P.para(f"**Testing.** The {F.TESTS['pytest']} unit tests cover loading and target normalisation, the stratified split, SMOTE, the band boundaries (0, 29.99, 30, 59.9, 60, 79.9, 80, 100), batch validation, the retention "
           f"rules, model persistence and the token; the {F.TESTS['smoke']}-check end-to-end test also exercises the error paths (401, 404, 409, 422). Writing them exposed a real defect: the data loader tested "
           "the pandas dtype against object in three places, which is false for the string dtype of pandas 3, so blank TotalCharges strings were not converted and labels such as Churned and Retained were mishandled; "
           "it was fixed and both pandas versions now pass. Calls through the hostname localhost took 2.04 s longer than through 127.0.0.1 on this Windows machine because of IPv6 resolution, so latencies were measured on 127.0.0.1.")
    P.para("**Threats to validity.** The churn label is generated from the same features the model sees, so the relationships are cleaner than in real data and the scores would probably be lower on a real "
           "operator's customers. The test set holds 53 churners, so differences of a few points are not reliable; the spreads above, not the single-split figures, should guide any conclusion. Tree-ensemble "
           "results depend on the library version. The explanations come from coefficients and permutation importance and were not compared with SHAP.")
    P.para(f"**Failure cases and limits.** Logistic Regression flags {lr['confusion_matrix'][0][1]} of the 147 retained customers at 0.50 and misses {lr['confusion_matrix'][1][0]} of 53 churners; Gradient Boosting "
           f"and Histogram Gradient Boosting reach recall {F.f3(gb['recall'])} and {F.f3(hgb['recall'])} because they take no class weight. Random Forest is version-sensitive on this small split: F1 {F.f3(rf['f1_score'])} "
           f"here and {F.f3(m15rf['f1_score'])} under scikit-learn 1.5.0. The retention rules are heuristics whose business effect was not measured, the explanations are model attributions and not causes, "
           "and there was no user study.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"ChurnIQ delivers the path from a customer table to explained, banded customers and retention actions, with {F.TESTS['pytest']} unit tests and a {F.TESTS['smoke']}-check API test passing. "
           f"Against the project objectives, the three required classifiers were trained and compared on five metrics, imbalance was handled and measured, the main drivers were identified and at-risk customers "
           f"are presented through a dashboard. On synthetic data Logistic Regression and Random Forest are statistically indistinguishable (F1 about 0.46 to 0.51, ROC-AUC about 0.70 to 0.72), accuracy is a poor guide "
           "under imbalance, and the scores are rankings and not probabilities. Limits: synthetic data, a 200-row test set, uncalibrated scores, no SHAP, unmeasured business effect, a single shared demo login.")
    P.para("Objectives met: data acquisition and exploration (synthetic data), cleaning and imbalance handling, comparison of the three classifiers, evaluation on five metrics, identification of the main drivers, "
           "and a retention dashboard. Not met, because no real data existed: any claim about accuracy on real customers. The key finding is that the leading models are not separable on this data and that "
           "imbalance handling, not model choice, changes recall most (0.189 to 0.660 for Logistic Regression).")
    P.para("Future work: validate on real operator data; recalibrate the scores (Platt or isotonic) and tune the decision threshold to offer costs; add SHAP and the base paper's perturbation explainer; "
           "evaluate the retention rules in a controlled campaign; and add accounts, a database and drift tests for production use.")

    P.references()
    P.save(path)
    return path, len(P.order)


def to_pdf(docx, pdf):
    """Convert with Word (COM) and return the page count read from the PDF."""
    import subprocess
    import time

    import pymupdf as fitz
    import win32com.client

    subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], capture_output=True)
    time.sleep(1)
    for f in os.listdir(F.BATCH):
        if f.startswith("~$"):
            os.remove(os.path.join(F.BATCH, f))
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(os.path.abspath(docx), ReadOnly=True, AddToRecentFiles=False)
        doc.ExportAsFixedFormat(os.path.abspath(pdf), 17)
        doc.Close(False)
    finally:
        word.Quit()
    with fitz.open(pdf) as d:
        return d.page_count


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    print(build(out))
    print("pages:", to_pdf(out, os.path.join(F.BATCH, "19.IEEE_Paper.pdf")))
