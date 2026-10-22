"""Builds 19.IEEE_Paper.docx (two-column, ~6 pages) from facts.py, shared.py and the figures already produced.

    python -m scripts.docs.build_paper
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper

pct, f3, f4 = F.pct, F.f3, F.f4


def crop_shot(name, out, box):
    os.makedirs(F.FIGS, exist_ok=True)
    p = os.path.join(F.FIGS, out)
    Image.open(F.shot(name)).convert("RGB").crop(box).save(p)
    return p


def confusion_fig(x):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    cm = np.array([[x["tn"], x["fp"]], [x["fn"], x["tp"]]])
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=7500)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", fontsize=11, fontweight="bold", color="white" if cm[i, j] > 3750 else "#1B2A41")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["<=50K", ">50K"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["<=50K", ">50K"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    for sp in ax.spines.values():
        sp.set_visible(False)
    p = os.path.join(F.FIGS, "paper_confusion.png")
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def build(path):
    M = F.METRICS
    C = F.CM
    X = C[F.BEST]
    cmp_ = F.COMPARE
    RM = F.RM
    MEAS = F.MEAS
    env = MEAS["environment"]
    lat = MEAS["api_latency_ms_127_0_0_1"]
    py = MEAS["pytest"]["passed"]
    smoke = MEAS["smoke_test"]
    fc = F.FORECAST
    bt = RM["forecast_backtest"]
    sw = {r["threshold"]: r for r in RM["threshold_sweep_xgboost"]}
    cal = RM["calibration"]
    bands = RM["profile_band_counts_test"]
    brate = RM["profile_band_actual_positive_rate"]
    shap = F.SHAP["features"]
    miss = RM["missing_cells_raw"]
    st = F.STATS
    pos_rate = pct(RM["positive_rate_all"], 2)

    P = Paper()
    P.order = ["base"]
    authors = [[n.title(), "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology (Autonomous)", "Hyderabad, India", "[EMAIL]"] for n, _ in F.STUDENTS]
    authors.append([F.GUIDE.title().replace("B Srikanth", "B Srikanth"), "[DESIGNATION], Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology (Autonomous)", "Hyderabad, India", "[EMAIL]"])
    P.title_block("FinSight AI: Explainable Financial Profiling from Demographic Data with XGBoost, SHAP and Holt-Winters Forecasting", authors)
    P.begin_two_columns()

    P.abstract(
        "Assessing an individual's financial position usually relies on a narrow set of financial parameters, a static score and no explanation, so non-linear interactions "
        "between demographic and financial factors are missed and decisions are hard to justify. This paper presents FinSight AI, a web application that converts twelve "
        "demographic and financial inputs into a financial profile, a risk band, a strength score, a per-person SHAP explanation and a twelve-month economic forecast. "
        f"Four classifiers were trained on the public UCI Adult data ({F.N_ROWS:,} records) inside leakage-safe pipelines. On {F.N_TEST:,} held-out records the selected XGBoost model reaches "
        f"accuracy {pct(M['accuracy'])}, recall {pct(M['recall'])} and ROC-AUC {f3(M['roc_auc'])} (cross-validated AUC {f3(M['cv_roc_auc_mean'])}). The target is income above 50K, not creditworthiness, "
        "and the forecast uses a documented synthetic index, so results are reported with these limits; the comparison with the base paper, which studies hospitals, is given as context only.",
        ["demographic analytics", "economic forecasting", "explainable AI", "financial profiling", "Holt-Winters", "SHAP", "XGBoost"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Financial decisions depend on an accurate picture of a person's economic position. Classical scoring starts from a few financial ratios and a linear or logistic "
           "model {r:altman,ohlson}; it ignores the demographic context in which people earn, spend and save, such as age, education, occupation and household. The cost is twofold: "
           "non-linear interactions are missed, which makes assessments inaccurate for people whose profile does not fit the average, and a bare score cannot be explained to the "
           "customer or a regulator. Ensemble learners such as random forests, gradient boosting and XGBoost capture these interactions {r:breiman,friedman,xgboost} and post-hoc "
           "attribution with SHAP {r:shap,treeshap} makes their output inspectable, but most published systems stop at a trained model and a metric.")
    P.para("The base paper {r:base} builds an explainable framework for organisational financial distress using Korean hospital panel data. The gap addressed here is "
           "to extend the same approach to individuals, where demographic attributes carry much of the signal, and to deliver it as a usable system. The contributions are:")
    P.para("1) an end-to-end application that validates a twelve-field profile, engineers features, predicts a financial-strength score, maps it to a profile and risk band, and explains "
           "it with live SHAP contributions; 2) a leakage-safe comparison of four classifiers with stratified cross-validation and results beyond a single score (confusion matrices, "
           "threshold, calibration, band-level rates); 3) a twelve-month Holt-Winters forecast and a what-if comparison, both labelled as non-causal; and 4) an honest account of limits, "
           "including a synthetic forecasting series and the absence of a fairness audit.", indent=0.2)
    P.para("Section II surveys related work, Section III describes the method and system, Section IV reports measurements and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All training, evaluation and timing ran on one desktop: {env['cpu']}, {env['ram_gb']} GB RAM, {env['os']}, CPU only (no GPU was used).")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}, scikit-learn {env['scikit-learn']} {{r:sklearn}}, XGBoost {env['xgboost']}, SHAP {env['shap']}, statsmodels {env['statsmodels']}, Flask {env['flask']}, "
           f"and a React 19 / Vite front end on Node.js {env['node']}. Tests use pytest.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.sub("A", "Base paper")
    P.para("Kim and Sun {r:base} present a four-stage explainable framework: domain-adaptive feature engineering, multi-model training, SHAP interpretation and domain-specific validation. "
           "They instantiate it on a balanced panel of 165 Korean hospitals (825 hospital-year rows, 2019-2023) built from 236 disclosed line items, reduced to 11 engineered features, "
           "with net-income deficit as target (41.2 % positive). Under hospital-level Group K-Fold, XGBoost reaches AUC 0.842, Gradient Boosting 0.840, Random Forest 0.831, "
           "Logistic Regression 0.776 and an MLP 0.772; training on 2019-2022 and testing on 2023 gives 0.780, and a modified Altman Z''-score only 0.680. SHAP ranks material-cost "
           "(0.777) and labour-cost (0.729) ratios first. Pairwise DeLong tests show the three ensembles are not significantly different, hyperparameters are left at defaults, and the "
           "authors stress that SHAP explains associations, not causes. Their framework is organisational; individual profiling is left open.")
    P.sub("B", "Related work")
    P.para("Distress and bankruptcy prediction moved from Altman's discriminant function {r:altman} and Ohlson's logit {r:ohlson} to ensembles, which Barboza et al. {r:barboza} "
           "report to outperform traditional statistical models. Abid {r:abid} forecasts CDS-implied sovereign default probabilities with five machine-learning and four deep models for "
           "Egypt, Morocco and Saudi Arabia, and finds linear regression best with RNN and GRU competitive. Maurino {r:maurino} shows on an open credit-risk dataset that missing values, "
           "noise, outliers and label errors affect ten models differently, with some corruptions even helping specific models. Zhang et al. {r:zhang} propose PrivacyCredit, a vertical "
           "federated method that adds alternative data to credit-risk models without exposing it, matching the plaintext combination.")
    P.para("On explainability, Bussmann et al. {r:bussmann} use Shapley values to explain SME credit-risk models and Gramegna and Giudici {r:gramegna} compare SHAP with LIME in credit risk. "
           "For tabular data, Grinsztajn et al. {r:grinsztajn} find that tree-based models still outperform deep learning, which supports using boosted trees here.")
    P.para("Positioning. Compared with these works, this project keeps the base paper's recipe of boosted trees, SHAP and default hyperparameters but changes the unit of analysis from the "
           "organisation to the person, drops the panel structure (one row is one person, so a stratified split is appropriate), and adds what the surveyed studies leave out: a per-assessment "
           "explanation in plain language, a forecast component and a working interface. It does not reproduce the base paper's counterfactual or econometric analyses.")
    P.table("Summary of the surveyed work",
            ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["Kim, Sun {r:base}", "Explainable ML, SHAP", "165 hospitals", "XGB AUC 0.842", "Organisations only"],
             ["Abid {r:abid}", "5 ML + 4 DL models", "3 sovereigns", "Linear reg. best", "Not individuals"],
             ["Maurino {r:maurino}", "Data-quality robustness", "1 open dataset", "Errors affect models unevenly", "Binary, one dataset"],
             ["Zhang {r:zhang}", "Federated credit risk", "Credit + alt. data", "Equals plaintext", "Needs partner data"],
             ["Barboza {r:barboza}", "Ensembles vs statistics", "Listed firms", "Ensembles better", "Corporate"],
             ["Bussmann {r:bussmann}", "Shapley explanations", "SME lending", "Explains credit risk", "SME level"],
             ["Grinsztajn {r:grinsztajn}", "Trees vs deep learning", "Tabular sets", "Trees still win", "Not finance"]],
            [0.62, 0.72, 0.6, 0.78, 0.68], size=6.5)
    P.para("Research gap: explainable machine learning for financial risk has been developed for organisations and sovereigns, while work on individuals centres on accuracy with few "
           "parameters. None of the surveyed works joins individual demographic profiling, a per-person explanation, an economic forecast and a usable web interface in one "
           "reproducible system; this project does so on public data.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Data")
    P.para(f"Classification uses the UCI Adult / Census Income data {{r:uci}}: {F.N_ROWS:,} records (32,561 + 16,281), 15 columns, of which "
           f"{pos_rate} earn above 50K. Missing values are marked '?' in workclass ({miss['workclass']:,}), occupation ({miss['occupation']:,}) and native country ({miss['native-country']:,}). "
           f"The label (income above 50K) is adapted as a financial-profile signal; it is not a credit score. A stratified 80/20 split with seed 42 gives {F.N_TRAIN:,} training and "
           f"{F.N_TEST:,} test records ({F.TEST_NEG:,} and {F.TEST_POS:,} of the two classes). One row is one person, so entity-grouped validation is unnecessary. "
           "Because the census records have no time axis, forecasting uses a separate monthly Household Financial Conditions Index, January 2015 to December 2025 (132 points), "
           "which is synthetic (trend, yearly seasonality, noise and a mid-2020 dip, seed 42) and documented as such.")
    P.sub("B", "Preprocessing and features")
    P.para("'?' becomes missing; numeric gaps take the training median and categorical gaps the constant 'Unknown', followed by one-hot encoding and, for logistic regression only, "
           "standard scaling, all inside a scikit-learn ColumnTransformer within each Pipeline {r:sklearn} so that nothing is fitted on test data. Twelve interpretable features are derived "
           "from the 14 raw fields (26 columns): net capital, capital intensity, log gains and losses, gain and loss flags, capital position, hours band, age band, education tier, "
           "region from country and employment stability. The census weight is meaningless for a new user and is imputed with the training median at prediction time.")
    P.sub("C", "Models and formulation")
    P.para("Four classifiers are compared: logistic regression (C = 1, 2000 iterations), random forest (300 trees) {r:breiman}, scikit-learn gradient boosting {r:friedman} and XGBoost "
           "(400 trees, depth 6, learning rate 0.05, subsample and column sample 0.9, L2 weight 1) {r:xgboost}. No hyperparameter search or class re-balancing was used, in line with the "
           "base paper's default-parameter practice. XGBoost adds regularised trees; its score is")
    P.equation("p(x) = σ( Σₖ fₖ(x) ),   L = Σᵢ ℓ(yᵢ, ŷᵢ) + Σₖ ( γTₖ + ½λ‖wₖ‖² )", 1)
    P.para("and p(x) is read as the financial-strength score. It is mapped to a profile by fixed bands: p ≥ 0.60 Established (Low risk), 0.35 ≤ p < 0.60 Developing (Moderate), otherwise "
           "Emerging (High). The model is selected by ROC-AUC. Explanations use TreeExplainer {r:treeshap}, which decomposes each prediction exactly into")
    P.equation("f(x) = φ₀ + Σⱼ φⱼ(x)", 2)
    P.para("where φⱼ is the contribution of feature j in log-odds; the five largest positive and negative terms are shown with plain-language sentences, and one-hot features with value 0 are "
           "worded as the absence of a category. The forecast is an additive Holt-Winters model {r:winters} with period 12:")
    P.equation("ŷₜ₊ₕ = ℓₜ + h·bₜ + sₜ₊ₕ₋ₘ(k+1)", 3)
    P.para(f"fitted with statsmodels {{r:statsmodels}}; the 95 % band is ±1.96 times the residual standard deviation ({fc['residual_std']:.3f}). The what-if screen re-predicts the same person "
           "after changing gains, losses, weekly hours or education and reports the change in score, profile and risk; it is a model simulation, not a causal estimate.")
    P.figure(F.diag("01_system_architecture.png"), "Architecture of FinSight AI: React interface, Flask API, services, persisted model and artifacts.", 3.4)
    P.para(f"Evaluation protocol. Each candidate is cross-validated on the training split with five stratified folds (shuffled, seed 42), refitted on the whole training split and scored once on "
           f"the held-out {F.N_TEST:,} records with accuracy, precision, recall, F1 and ROC-AUC {{r:sklearn}}; the threshold is 0.5. The best model by ROC-AUC is persisted as the serving "
           "pipeline together with the confusion matrix, ROC curves, SHAP importance, a validation report and a statistics report (correlations and a logistic regression on age, "
           "education, hours and net capital), all as JSON or image artifacts that the interface reads.")
    P.para("Measures. With true and false positives and negatives written TP, FP, TN and FN, precision is TP/(TP+FP), recall is TP/(TP+FN), specificity is TN/(TN+FP) and")
    P.equation("F1 = 2·precision·recall / (precision + recall)", 4)
    P.equation("AUC = P( p(x⁺) > p(x⁻) )", 5)
    P.para("where x⁺ and x⁻ are a randomly drawn positive and negative record. ROC-AUC does not depend on the threshold and is the selection criterion; the other measures are reported at 0.5 and, for "
           "XGBoost, across thresholds. Calibration is checked with ten equal-width reliability bins and the Brier score.")
    P.sub("D", "Architecture and implementation")
    P.para("A Flask API on port 8409 exposes /api/predict, /api/whatif, /api/forecast, /api/explain, /api/performance and /health; the same application still serves the original "
           "Jinja pages. Server-side validation checks required fields, allowed values and ranges (age 16-100, hours 1-99, gains and losses 0-1,000,000) and answers HTTP 400 with messages "
           "otherwise. The pipeline and explainer are loaded once at start-up. A React 19 interface on port 5409 proxies the API and provides a sample login (a browser-only demo gate), "
           "dashboard, assessment form, result, explainability, forecast, what-if and performance screens in light and dark themes. No personal data is stored: the trained pipeline is a "
           "pickle file, evaluation output is JSON and the what-if baseline lives in browser session storage.")
    P.para("Reproducibility. One command (run.bat) creates the virtual environment, installs the requirements, trains the models if no persisted pipeline exists, builds the front end and starts "
           "both servers; scripts/train.py regenerates every artifact from the raw Adult files with a fixed seed, and a separate script re-derives the confusion matrices, threshold sweep, "
           "calibration bins and forecast back-test from the persisted models. The Docker files cover the original Flask pages only, not the React front end.")
    P.figure(F.diag("02_high_level_workflow.png"), "Main flow of one assessment, from sign-in to explained result.", 3.4)

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"Conditions: the {F.N_TEST:,}-record stratified test split, decision threshold 0.5, positive class income above 50K, seed 42; cross-validation uses five stratified folds on the training "
           f"split. Metrics were reproduced by a separate script and match the training output exactly.")
    rows = []
    for m in F.MODELS:
        c = cmp_[m]
        rows.append([F.MODEL_LABEL[m] + (" *" if m == F.BEST else ""), f3(c["accuracy"]), f3(c["precision"]), f3(c["recall"]), f3(c["f1"]), f3(c["roc_auc"]), f"{c['cv_roc_auc_mean']:.3f}±{c['cv_roc_auc_std']:.3f}"])
    P.table("Test-set metrics of the four classifiers (* selected)", ["Model", "Acc.", "Prec.", "Rec.", "F1", "AUC", "CV AUC"], rows, [0.95, 0.38, 0.38, 0.38, 0.35, 0.38, 0.58], size=7, align=["l", "c", "c", "c", "c", "c", "c"])
    P.para(f"XGBoost is best on every metric; its confusion matrix is {X['tn']:,} true negatives, {X['fp']:,} false "
           f"positives, {X['fn']:,} false negatives and {X['tp']:,} true positives (specificity {pct(X['specificity'])}, PR-AUC {f3(X['pr_auc'])}, Brier score {f4(X['brier'])}). "
           f"Cross-validated AUC is stable (standard deviation {M['cv_roc_auc_std']:.4f}), and the ranking by cross-validation agrees with the test ranking.")
    P.figure(confusion_fig(X), "Confusion matrix of the selected XGBoost model on the test split (threshold 0.5).", 3.0)
    prec_neg = X["tn"] / (X["tn"] + X["fn"])
    f1_neg = 2 * prec_neg * X["specificity"] / (prec_neg + X["specificity"])
    P.table("Per-class results of XGBoost", ["Class", "Precision", "Recall", "F1", "Support"],
            [["Income <=50K", f3(prec_neg), f3(X["specificity"]), f3(f1_neg), f"{F.TEST_NEG:,}"],
             ["Income >50K", f3(X["precision"]), f3(X["recall"]), f3(X["f1"]), f"{F.TEST_POS:,}"]],
            [0.9, 0.55, 0.5, 0.45, 0.5], size=7, align=["l", "c", "c", "c", "c"])
    P.para(f"The majority class is easy (recall {f3(X['specificity'])}), the minority class is where the model errs. Logistic regression is a strong baseline here: XGBoost improves its AUC by only "
           f"{cmp_['xgboost']['roc_auc'] - cmp_['logistic_regression']['roc_auc']:.3f}, whereas the base paper's gap between XGBoost and logistic regression is 0.066 (0.842 against 0.776). "
           "Random Forest has the lowest AUC of the four. Interaction effects therefore matter, but less than in the hospital panel.")
    P.figure(F.fig("model_comparison.png"), "Accuracy, precision, recall, F1 and ROC-AUC of the four classifiers on the same test split.", 3.4)
    P.para(f"Threshold. Lowering the threshold to 0.35 raises recall from {f3(sw[0.5]['recall'])} to {f3(sw[0.35]['recall'])} at precision {f3(sw[0.35]['precision'])} (F1 {f3(sw[0.35]['f1'])}); "
           f"raising it to 0.60 gives precision {f3(sw[0.6]['precision'])} and recall {f3(sw[0.6]['recall'])}. The default 0.5 is therefore a choice, not an optimum for recall. "
           f"Calibration is close: in the lowest bin mean prediction is {f3(cal[0]['mean_pred'])} against an observed rate {f3(cal[0]['observed'])}, and the largest gap is in the 0.4-0.5 bin "
           f"({f3(cal[4]['mean_pred'])} against {f3(cal[4]['observed'])}).")
    P.figure(F.fig("threshold_sweep.png"), "Precision, recall, F1 and accuracy of XGBoost as the decision threshold moves from 0.2 to 0.8.", 3.4)
    P.para(f"Profiles. The application's bands separate the groups well: of {bands['Emerging']:,} test records called Emerging, {pct(brate['Emerging'])} actually earn above 50K; of {bands['Developing']:,} "
           f"Developing, {pct(brate['Developing'])}; of {bands['Established']:,} Established, {pct(brate['Established'])}.")
    P.para(f"Explanation. The mean absolute SHAP values rank married-civilian-spouse status first ({shap[0]['mean_abs_shap']:.3f}), then age ({shap[1]['mean_abs_shap']:.3f}), years of education "
           f"({shap[2]['mean_abs_shap']:.3f}), capital gains ({shap[3]['mean_abs_shap']:.3f}) and weekly hours ({shap[4]['mean_abs_shap']:.3f}); a logistic regression on four numeric variables "
           f"gives positive coefficients, all with p < 0.001, and the strongest correlation with the target is education ({st['correlations_with_target']['education-num']:.3f}). These are associations, not causes.")
    P.figure(F.fig("shap_top.png"), "Global feature importance: mean absolute SHAP value of the twelve strongest features.", 3.4)
    P.para(f"Significance. XGBoost leads Gradient Boosting by {cmp_['xgboost']['roc_auc'] - cmp_['gradient_boosting']['roc_auc']:.3f} AUC, about three times the largest fold-to-fold standard deviation "
           f"({max(c['cv_roc_auc_std'] for c in cmp_.values()):.4f}), but no formal significance test such as DeLong's was run, and the model was chosen on the test split, so the margin should be read as indicative.")
    P.para("Local explanation. For a 52-year-old married executive with a Master's degree, 50 weekly hours and investment gains of 7,688 the application returns an Established profile at "
           "Low risk with a score of 99.9 %; the largest strengthening contributions are investment gains (+4.678 log-odds), married-civilian-spouse status (+1.004), age (+0.550), years of education "
           "(+0.527) and net investment position (+0.424), and the largest weakening one is overall investment activity (-0.243). A 34-year-old sales employee with some college, 42 hours and no gains "
           "is scored 46.8 %, Developing at Moderate risk.")
    P.para(f"Interface. The dashboard shows the serving model, accuracy {pct(M['accuracy'])}, ROC-AUC {f3(M['roc_auc'])} and F1 {f3(M['f1'])} read from the artifacts, the five strongest SHAP drivers and the "
           "forecast outlook; the performance screen lists the four-model comparison, the confusion matrix, ROC curves, per-fold AUCs and the statistics table. Invalid input is rejected with field-level "
           "messages (for example an age of 7 is refused with 'must be between 16 and 100'), and every analysis screen carries the disclaimer that the output is informational, not financial advice.")
    P.figure(crop_shot("14_result-established.png", "paper_result.png", (264, 100, 1440, 900)), "Output screen: an Established profile with live SHAP factors.", 3.4)
    P.figure(crop_shot("09_whatif.png", "paper_whatif.png", (264, 100, 1440, 830)), "Output screen: what-if comparison of a baseline and a scenario.", 3.4)
    P.table("Profile bands on the test split and measured response times", ["Item", "Value"],
            [["Emerging: rows / observed >50K", f"{bands['Emerging']:,} / {pct(brate['Emerging'])}"],
             ["Developing: rows / observed >50K", f"{bands['Developing']:,} / {pct(brate['Developing'])}"],
             ["Established: rows / observed >50K", f"{bands['Established']:,} / {pct(brate['Established'])}"],
             ["POST /api/predict, median / p95", f"{lat['POST /api/predict']['median']:.1f} / {lat['POST /api/predict']['p95']:.1f} ms"],
             ["POST /api/whatif, median / p95", f"{lat['POST /api/whatif']['median']:.1f} / {lat['POST /api/whatif']['p95']:.1f} ms"],
             ["GET /api/forecast, median / p95", f"{lat['GET /api/forecast']['median']:.1f} / {lat['GET /api/forecast']['p95']:.1f} ms"]],
            [2.2, 1.1], size=7, align=["l", "c"])
    P.figure(F.fig("forecast_plot.png"), "Twelve-month Holt-Winters forecast with a 95 % band on the synthetic Household Financial Conditions Index.", 3.4)
    P.para(f"Testing. The {py} pytest cases (seven on the application, two on feature engineering) check that every page loads, that a valid assessment gives different output for different inputs (nothing is hard-coded), that invalid or missing "
           "input returns HTTP 400, that the JSON prediction and forecast endpoints return a probability, SHAP contributions and twelve forecast points, that a what-if request changes the score, "
           f"and that the persisted artifacts are complete, that derived features are computed and that missing values are handled. The smoke test adds {smoke['total']} checks of the live servers. "
           "Load, browser-matrix and user-acceptance testing were not carried out.")
    P.para(f"System. All {py} automated tests and {smoke['passed']} of {smoke['total']} smoke checks pass. On 127.0.0.1 a prediction with SHAP takes a median {lat['POST /api/predict']['median']:.0f} ms "
           f"(95th percentile {lat['POST /api/predict']['p95']:.0f} ms) and a what-if comparison {lat['POST /api/whatif']['median']:.0f} ms on the CPU above. "
           f"Forecast. The index is projected from {fc['history'][-1]['value']:.1f} to {fc['forecast'][-1]['value']:.2f} ({fc['forecast_pct_change']:+.2f} %). Back-tested on the held-out final year of the "
           f"synthetic series, MAE is {bt['mae']:.3f} against {bt['naive_last_value_mae']:.3f} for a last-value forecast and MAPE {bt['mape_pct']:.2f} %; this only shows that the method recovers its own "
           "generator and says nothing about real-world forecasting accuracy.")
    P.para(f"Comparison with the base paper. The base paper reports AUC 0.842 for XGBoost on 165 hospitals under hospital-level Group K-Fold and 0.780 on a temporal hold-out; here XGBoost reaches "
           f"{f3(M['roc_auc'])} on individual census records. The two numbers must not be ranked against each other: the entities, the target (income above 50K versus a hospital deficit), the sample size "
           "(48,842 versus 825), the validation protocol (random stratified versus entity-grouped and temporal) and the features all differ. What carries over is the ordering of model families, "
           "with boosted trees ahead of linear models, and the use of SHAP.")
    P.para("Threats to validity. Selection on the test split, the single data source from 1994, the lack of an external or temporal validation set, the use of a target that is not a credit outcome "
           "and the synthetic forecasting series all limit how far the numbers generalise; the cross-validation and the reproduction script reduce, but do not remove, the first of these.")
    P.para(f"Failure cases and limits. Recall is {pct(M['recall'])}: {X['fn']:,} higher earners in the test split are missed at threshold 0.5. Large scenario changes (investment gains of 80,000 for a "
           "39-year-old clerk scored 1.1 %) swing the score by about 98 points because training data are sparse there. Sex, race and marital status are inputs and marital status is the top SHAP feature, yet no fairness audit was done {r:mehrabi}. The data are 1994 US "
           "records, income is not creditworthiness, no hyperparameters were tuned and the model was selected on the test split.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"The objectives were met as follows: a demographic and financial dataset was collected and preprocessed (in part: no transaction data); four models were trained and XGBoost selected; "
           f"a forecast and an explanation layer were built; and accuracy, precision, recall and ROC-AUC were evaluated and the system deployed through a web interface. The key finding is that "
           f"boosted trees with SHAP reach {f3(M['roc_auc'])} AUC on census-style demographic data and can be explained per person, but the approach inherits the age, bias and target limits listed above. "
           "The forecast is illustrative and the output is informational, not financial advice.")
    P.para("Future work: replace the synthetic index with real macroeconomic series (inflation, lending rates, GDP) and validate the forecast out of time; evaluate on current, non-US and credit-"
           "outcome data with entity-grouped and temporal splits; audit and mitigate bias in sensitive attributes; tune and calibrate the model and choose the threshold by cost; and add real "
           "authentication, persistence and container deployment of the full stack. Showing a per-person confidence interval for the score, and "
           "comparing SHAP with an alternative explainer on the same assessments, would further support the explanation layer.")
    P.references()
    P.save(path)
    return P


def main():
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    P = build(out)
    print("wrote", out, "references:", len(P.order))


if __name__ == "__main__":
    main()
