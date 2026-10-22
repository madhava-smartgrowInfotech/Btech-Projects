"""Chapter 8: Results and output screens. Every number is read from artifacts/*.json at build time
(train.py, report_metrics.py, error_analysis.py, edge_cases.py) or from facts.py."""

import json
import os

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F
from . import shared as S

# Numbers reported in the base paper (Kim and Sun, IEEE Access 2026), copied from the PDF in Documentary/.
BASE_AUC = {"logistic_regression": 0.776, "random_forest": 0.831, "gradient_boosting": 0.840, "xgboost": 0.842}
BASE_OTHER = {"temporal_2023": 0.780, "mlp": 0.772, "altman_z2": 0.680, "forward": 0.772, "rolling_mean": 0.800}


def _json(name):
    p = os.path.join(F.ART, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def _shot(name, base=5.6, max_h=4.6):
    p = F.shot_view(name)
    return p, F.shot_w(p, base, max_h)


def analysis():
    """Small dict of derived numbers other builders (decks, paper) may reuse."""
    c = F.CM
    x = c[F.BEST]
    ea = _json("error_analysis.json") or {}
    g = ea.get("groups", {})
    out = {
        "xgb_vs_lr_auc_gain": round(c["xgboost"]["roc_auc"] - c["logistic_regression"]["roc_auc"], 4),
        "xgb_vs_gb_auc_gain": round(c["xgboost"]["roc_auc"] - c["gradient_boosting"]["roc_auc"], 4),
        "majority_baseline_accuracy": round(F.TEST_NEG / F.N_TEST, 4),
        "errors": x["fp"] + x["fn"],
        "xgb_cv_beats_gb_every_fold": all(a > b for a, b in zip(F.VALID["cv_roc_auc"]["xgboost"], F.VALID["cv_roc_auc"]["gradient_boosting"])),
    }
    if g:
        out["recall_female"] = g["Sex"]["Female"]["recall"]
        out["recall_male"] = g["Sex"]["Male"]["recall"]
        out["pred_pos_rate_female"] = g["Sex"]["Female"]["pred_pos_rate"]
        out["pred_pos_rate_male"] = g["Sex"]["Male"]["pred_pos_rate"]
        out["actual_pos_rate_female"] = g["Sex"]["Female"]["actual_pos_rate"]
        out["actual_pos_rate_male"] = g["Sex"]["Male"]["actual_pos_rate"]
    return out


def _fmt(v, d=4):
    return "-" if v is None else f"{v:.{d}f}"


def _row_text(r):
    return (f"{r['age']}, {r['workclass']}, {r['education']}, {r['marital-status']}, {r['occupation']}, {r['sex']}, "
            f"gains {int(r['capital-gain']):,}, losses {int(r['capital-loss']):,}, {r['hours-per-week']} h")


def blocks():
    M = F.METRICS
    C = F.CM
    X = C[F.BEST]
    A = analysis()
    RM = F.RM
    EA = _json("error_analysis.json") or {"groups": {}, "confident_false_positives": [], "confident_false_negatives": [], "summary": {}}
    SP = _json("sample_predictions.json") or []
    G = EA["groups"]
    SM = EA["summary"]
    bt = RM["forecast_backtest"]
    fc = F.FORECAST
    last_hist = fc["history"][-1]["value"]
    last_fc = fc["forecast"][-1]
    sweep = RM["threshold_sweep_xgboost"]
    best_f1 = max(sweep, key=lambda r: r["f1"])
    cv = F.VALID["cv_roc_auc"]
    st = F.STATS

    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1 screens
    out += [
        H2("8.1 Output screens"),
        P("The screens below are captures of the running application at 1440 x 900 pixels, taken in Chrome by `scripts/capture_screens.py` and `scripts/capture_extra_screens.py` against the live servers (API on port 8409, "
          "React front end on port 5409). Every screen shows real model output computed from the profile typed into the form; none is a mock-up. Some captures include the green 'Analysis complete' notification, "
          "which is part of the interface."),
    ]
    p, w = _shot("04_dashboard.png")
    out += [FIG(p, "Dashboard: serving model, test accuracy, ROC-AUC and F1 read from the artifacts, the five strongest SHAP drivers and the economic outlook", w),
            P(f"The dashboard is the first screen after sign-in. Its four tiles are filled from `/api/dashboard`: the serving model (XGBoost), accuracy {F.pct(M['accuracy'])} on the held-out test set, ROC-AUC {F.f3(M['roc_auc'])} "
              f"(cross-validated {F.f3(M['cv_roc_auc_mean'])} +/- {F.f3(M['cv_roc_auc_std'])}) and F1 {F.f3(M['f1'])} with precision {F.pct(M['precision'], 0)} and recall {F.pct(M['recall'], 0)}. Beneath them are a bar chart of the "
              "five largest mean absolute SHAP values and a short statement of the economic outlook, with buttons to start an assessment or open the forecast.")]
    p, w = _shot("05_assessment.png")
    out += [FIG(p, "Financial assessment form filled with the sample profile (age 39, State-gov, Bachelors, Never-married, Adm-clerical)", w),
            P("The form collects the twelve inputs, each with its allowed range or option list shown under the field. The values in the capture are the first record of the Adult data set. 'Use sample profile' fills them in one click and "
              "'Clear' empties them. Validation runs in the browser and again on the server; the next figure shows a rejected entry.")]
    p, w = _shot("13_validation-error.png")
    out += [FIG(p, "Validation error: age 7 is outside the permitted range of 16 to 100, so the field is outlined and the analysis is refused", w),
            P("When the server returns HTTP 400 the page shows a pink banner and marks the offending field with its allowed range ('Must be between 16 and 100.'). No model is run and no result is shown. "
              "This is the behaviour the edge-case tests of Chapter 7 checked at the API level.")]
    p, w = _shot("06_result.png")
    out += [FIG(p, "Result for the sample profile: Emerging profile, High risk band, financial-strength score 1.1%, with the SHAP factors that shaped it", w),
            P("The result screen shows the predicted profile, the risk band, the financial-strength score (the model's probability of income above 50K, here 0.0109) and the live SHAP contributions for this one person, "
              "split into strengthening and weakening factors with a plain-language sentence for each. For this record years of education (+0.545) and age (+0.184) strengthen the prediction, while its investment-gains value of 2,174 "
              "is the largest weakening factor (-1.626) presumably because larger gains accompany high incomes in the training data. The text below the score states the risk-band rule: strength of at least 60% is Low risk, "
              "35% to 60% Moderate and below 35% High.")]
    p, w = _shot("16_result-developing.png")
    out += [FIG(p, "Result for a dual-income profile (age 34, Local-gov, Some-college, married, Sales, 42 hours): Developing profile, Moderate risk, score 46.8%", w),
            P("A profile between the two thresholds. Being married to a civilian spouse (+0.836) and the household role 'Wife' (+0.553) are the strongest strengthening factors; the screen makes clear that the score of 46.8% sits "
              "inside the Developing band, which in the test split corresponds to a population in which 44.0% actually earn more than 50K (Section 8.2).")]
    p, w = _shot("14_result-established.png")
    out += [FIG(p, "Result for a mid-career manager (age 52, Private, Masters, married, Exec-managerial, gains 7,688, 50 hours): Established profile, Low risk, score 99.9%", w),
            P("The third band. Investment gains (+4.678) dominate, followed by marital status (+1.004), age (+0.550) and years of education (+0.527). The full page continues with the actionable insights, an echo of the inputs and a "
              "miniature of the forecast; the full-page capture is stored as `docs/screenshots/15_result-established-full.png`.")]
    p, w = _shot("07_explainability.png")
    out += [FIG(p, "Explainability screen: global SHAP importance (left) and the SHAP summary of per-row effects (right)", w),
            P(f"The explainability screen shows the global picture computed at training time. 'marital status = Married-civ-spouse' has the largest mean absolute SHAP value ({F.SHAP['features'][0]['mean_abs_shap']:.3f}), followed by age "
              f"({F.SHAP['features'][1]['mean_abs_shap']:.3f}), years of education ({F.SHAP['features'][2]['mean_abs_shap']:.3f}), investment gains ({F.SHAP['features'][3]['mean_abs_shap']:.3f}) and hours per week "
              f"({F.SHAP['features'][4]['mean_abs_shap']:.3f}). In the beeswarm on the right each dot is one row; the colour is the feature value, so red capital-gain dots far to the right show that large gains push the prediction up. "
              "A banner states that SHAP explains learned associations, never causation.")]
    p, w = _shot("08_forecast.png")
    out += [FIG(p, "Forecast screen: 12-month Holt-Winters projection of the Household Financial Conditions Index with its 95% interval", w),
            P(f"Four tiles give the horizon (12 months, January to December 2026), the trend direction (upward), the projected change ({fc['forecast_pct_change']:+.2f}%, from {last_hist:.1f} to {last_fc['value']:.1f}) and the residual standard "
              f"deviation ({fc['residual_std']}), from which the interval of plus or minus 1.96 standard deviations is drawn. The chart can be switched between the full history, the last five years and the last two years. "
              "The subtitle says the projection 'extrapolates past patterns and cannot predict personal outcomes'; the series it extrapolates is synthetic, as Section 8.2 explains.")]
    p, w = _shot("09_whatif.png")
    out += [FIG(p, "What-if screen: scenario gains of 80,000 and 50 weekly hours compared with the baseline profile", w),
            P("The what-if screen keeps the baseline from the last assessment and lets the user change gains, losses, hours or education. In the capture, raising gains to 80,000 and hours to 50 moves the same person from "
              "Emerging (1.1%) to Established (99.5%), a change of +98.43 percentage points, and the comparison lists the two changed fields. Every result is captioned as a model simulation, not a causal prediction, "
              "because a jump of this size is the model extrapolating into a region where the training data are sparse (Section 8.5).")]
    p, w = _shot("10_performance.png")
    out += [FIG(p, "Performance screen: model comparison table with the selected model highlighted, followed by the metrics, ROC and confusion-matrix views", w),
            P("The performance screen lists the four models with accuracy, precision, recall, F1, ROC-AUC and the mean and standard deviation of cross-validated AUC, with the best model marked. Below the fold it shows the "
              "ROC curves, the confusion matrix, the validation protocol with the per-fold AUCs, and the correlation and logistic-regression statistics. The numbers on this screen are the numbers in Section 8.2.")]

    # ------------------------------------------------------------------ 8.2 model performance
    rows = []
    for m in F.MODELS:
        c = F.COMPARE[m]
        rows.append([F.MODEL_LABEL[m] + (" (selected)" if m == F.BEST else ""), F.f4(c["accuracy"]), F.f4(c["precision"]), F.f4(c["recall"]), F.f4(c["f1"]), F.f4(c["roc_auc"]),
                     f"{c['cv_roc_auc_mean']:.4f} +/- {c['cv_roc_auc_std']:.4f}"])
    out += [
        H2("8.2 Model performance"),
        P(f"All numbers in this section are measured on the {F.N_TEST:,} records of the stratified test split ({F.TEST_POS:,} with income above 50K and {F.TEST_NEG:,} at or below), produced by training on the other {F.N_TRAIN:,} records. "
          f"Classification uses the default threshold of 0.5 unless stated. A classifier that always answered 'at most 50K' would score {F.pct(A['majority_baseline_accuracy'])} accuracy on this split, which is the bar the accuracy figures should be read against; "
          "ROC-AUC, which does not depend on the class ratio, is the primary metric."),
        TAB("Test-set metrics of the four classifiers", ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "5-fold CV AUC"], rows,
            widths=[1.6, 0.75, 0.75, 0.7, 0.7, 0.75, 1.3], size=9, align=["l", "c", "c", "c", "c", "c", "c"]),
        FIG(F.fig("model_comparison.png"), "The four classifiers compared on the held-out test split", 5.6),
        P(f"XGBoost is best on every metric, with Gradient Boosting essentially tied on precision ({F.f3(F.COMPARE['gradient_boosting']['precision'])} against {F.f3(F.COMPARE['xgboost']['precision'])}). "
          f"Its ROC-AUC of {F.f4(M['roc_auc'])} is {A['xgb_vs_lr_auc_gain']:.4f} above Logistic Regression and {A['xgb_vs_gb_auc_gain']:.4f} above Gradient Boosting. The size of the gain over the linear baseline is modest: Logistic Regression "
          f"already reaches {F.f3(F.COMPARE['logistic_regression']['roc_auc'])}, and it is slightly ahead of Random Forest ({F.f3(F.COMPARE['random_forest']['roc_auc'])}) on AUC. "
          "With 48,842 rows and mostly categorical inputs, much of the signal is linear in the engineered features, which is why interpretable regression remains a strong comparator."),
        P(f"The ranking is stable. The cross-validated AUC, computed on the training split only, gives the same order (XGBoost {F.f4(F.COMPARE['xgboost']['cv_roc_auc_mean'])}, Gradient Boosting {F.f4(F.COMPARE['gradient_boosting']['cv_roc_auc_mean'])}, "
          f"Logistic Regression {F.f4(F.COMPARE['logistic_regression']['cv_roc_auc_mean'])}, Random Forest {F.f4(F.COMPARE['random_forest']['cv_roc_auc_mean'])}), the fold-to-fold standard deviation is at most 0.0022, and XGBoost beats Gradient Boosting in "
          f"{'every one' if A['xgb_cv_beats_gb_every_fold'] else 'not every one'} of the five folds. No formal significance test (such as the DeLong test used by the base paper) was run, and the model was chosen using the test split, "
          "so the headline figure is slightly optimistic; the cross-validated figure is the cleaner estimate."),
        FIG(F.fig("cv_folds.png"), "Per-fold ROC-AUC of the five-fold stratified cross-validation for each model", 4.8),
    ]
    cmrows = []
    for m in F.MODELS:
        c = C[m]
        cmrows.append([F.MODEL_LABEL[m], f"{c['tn']:,}", f"{c['fp']:,}", f"{c['fn']:,}", f"{c['tp']:,}", F.f4(c["specificity"]), F.f4(c["pr_auc"]), F.f4(c["brier"])])
    out += [
        TAB("Confusion-matrix counts, specificity, PR-AUC and Brier score on the test split", ["Model", "TN", "FP", "FN", "TP", "Specificity", "PR-AUC", "Brier"], cmrows,
            widths=[1.5, 0.7, 0.6, 0.6, 0.7, 0.9, 0.75, 0.7], size=9, align=["l", "c", "c", "c", "c", "c", "c", "c"]),
        FIG(F.fig("confusion_matrices.png"), "Confusion matrices of the four models on the test split (rows: actual, columns: predicted)", 6.2),
        P(f"For the selected model, {X['tn']:,} of the {F.TEST_NEG:,} people at or below 50K are classified correctly (specificity {F.pct(X['specificity'])}) and {X['tp']:,} of the {F.TEST_POS:,} above 50K are found (recall {F.pct(X['recall'])}). "
          f"The {A['errors']:,} errors split into {X['fp']:,} false positives and {X['fn']:,} false negatives: the model errs more often by missing a high-income person than by promoting a low-income one. "
          f"It also has the best Brier score ({F.f4(X['brier'])}) and PR-AUC ({F.f4(X['pr_auc'])}), so its probabilities as well as its labels are better than the alternatives'."),
        FIG(F.fig("artifact_roc_curve.png"), "ROC curves of the four models on the test split (generated by the training script)", 4.6),
        P(f"The ROC curves of the four models lie close together and well above the diagonal; the ordering by area matches the table. A threshold of 0.5 is a convention, not an optimum for this application, so the threshold analysis below is more informative than any single operating point."),
    ]
    swrows = [[f"{r['threshold']:.2f}", F.f4(r["accuracy"]), F.f4(r["precision"]), F.f4(r["recall"]), F.f4(r["f1"])] for r in sweep]
    out += [
        TAB("Threshold analysis of the selected model (test split)", ["Threshold", "Accuracy", "Precision", "Recall", "F1"], swrows, widths=[1.1, 1.1, 1.1, 1.1, 1.1], size=10, align=["c"] * 5),
        FIG(F.fig("threshold_sweep.png"), "Precision, recall, F1 and accuracy of the selected model as the decision threshold moves", 5.0),
        P(f"Lowering the threshold from 0.5 to 0.3 raises recall from {F.pct(X['recall'])} to {F.pct(sweep[1]['recall'])} while precision falls from {F.pct(X['precision'])} to {F.pct(sweep[1]['precision'])}. F1 peaks at a threshold of {best_f1['threshold']:.2f} "
          f"({F.f4(best_f1['f1'])}), slightly above its value at 0.5 ({F.f4(X['f1'])}), and accuracy is highest near 0.5 ({F.f4(X['accuracy'])}). At 0.8 precision reaches {F.pct(sweep[-1]['precision'])} but only {F.pct(sweep[-1]['recall'])} of high-income people are found. "
          "An institution that wants to avoid missing strong profiles would choose a lower threshold; one that wants few false alarms, a higher one. The application does not use a single threshold for its output: it uses the probability itself, "
          "mapped to three bands, as described next."),
    ]
    cal = [c for c in RM["calibration"] if c["n"]]
    calrows = [[c["bin"], f"{c['n']:,}", _fmt(c["mean_pred"]), _fmt(c["observed"])] for c in cal]
    bc, ba = RM["profile_band_counts_test"], RM["profile_band_actual_positive_rate"]
    out += [
        TAB("Calibration of the selected model: predicted probability against observed share above 50K (test split)", ["Probability bin", "Rows", "Mean predicted", "Observed share"], calrows, widths=[1.5, 1.0, 1.5, 1.5], size=9.5, align=["c"] * 4),
        FIG(F.fig("calibration.png"), "Reliability diagram of the selected model on the test split", 3.9),
        P("The model is well calibrated: in every bin the mean predicted probability is close to the observed share, with the largest gap in the 0.4 to 0.5 bin (0.447 predicted, 0.406 observed). "
          "This matters for the application because the financial-strength score shown to the user is this probability; a score of 47% really does correspond to roughly four to five in ten comparable people earning above 50K in this data. "
          "Calibration was measured but not corrected; the raw XGBoost probabilities were used."),
        TAB("Profile bands on the test split", ["Profile band", "Rule on probability p", "Test rows", "Actually earn above 50K"],
            [["Emerging (High risk)", "p < 0.35", f"{bc['Emerging']:,}", F.pct(ba["Emerging"])], ["Developing (Moderate risk)", "0.35 <= p < 0.60", f"{bc['Developing']:,}", F.pct(ba["Developing"])],
             ["Established (Low risk)", "p >= 0.60", f"{bc['Established']:,}", F.pct(ba["Established"])]], widths=[1.9, 1.5, 1.0, 1.9], size=9.5, align=["l", "l", "c", "c"]),
        FIG(F.fig("profile_bands.png"), "Number of test rows per profile band and the share of each band that actually earns above 50K", 5.2),
        P(f"The bands separate the population usefully: only {F.pct(ba['Emerging'])} of the {bc['Emerging']:,} rows in the Emerging band actually earn above 50K, against {F.pct(ba['Developing'], 0)} in Developing and {F.pct(ba['Established'])} in Established. "
          "The band thresholds (0.35 and 0.60) are fixed in the application code (`profile_from_proba`). The labels are descriptive names for ranges of a probability; they are not credit grades."),
        FIG(F.fig("shap_top.png"), "Twelve largest global SHAP importances of the selected model", 5.2),
    ]
    shrows = [[str(i + 1), f["label"], f"{f['mean_abs_shap']:.4f}"] for i, f in enumerate(F.SHAP["features"][:10])]
    out += [
        TAB("Top ten global SHAP importances (XGBoost, 500-row sample, log-odds scale)", ["Rank", "Feature", "Mean |SHAP|"], shrows, widths=[0.6, 3.6, 1.3], size=10, align=["c", "l", "c"]),
        P("Marital status (being a civilian-spouse household), age, education, investment gains and weekly hours account for most of the model's behaviour. Sex appears in the top ten (rank 7). "
          "The logistic-regression statistics computed on the training split point the same way: correlations with income above 50K are "
          f"{st['correlations_with_target']['education-num']:.3f} for years of education, {st['correlations_with_target']['hours-per-week']:.3f} for weekly hours, {st['correlations_with_target']['age']:.3f} for age and {st['correlations_with_target']['net-capital']:.3f} for net capital, "
          f"and the four logit coefficients are all positive with p-values reported as 0.0. As the base paper also stresses {n('base')}, these are associations learned from historical data, not causal effects."),
        FIG(F.fig("artifact_shap_beeswarm.png"), "SHAP beeswarm plot: effect of each feature value on the prediction (generated by the training script)", 5.2),
    ]
    out += [
        H3("Forecast"),
        P("**The forecast series is synthetic.** The Adult data have no time dimension, so the 12-month forecast uses a Household Financial Conditions Index generated by `scripts/forecast.py` (132 monthly values from January 2015 to December 2025: "
          "a linear trend, a yearly sinusoid, Gaussian noise and a mild downturn in March to August 2020). It is documented as illustrative in `data/README.md`. The numbers below therefore measure how well the Holt-Winters method recovers "
          "its own generating pattern; they are not evidence of accuracy on real economic data."),
        FIG(F.fig("forecast_plot.png"), "Holt-Winters forecast of the synthetic index with its 95% band", 5.6),
        TAB("Back-test of the forecasting method on the synthetic series", ["Quantity", "Value"],
            [["Fitting window", f"{bt['train_months']} months (2015-01 to 2024-12)"], ["Held-out window", f"{bt['test_months']} months (2025)"], ["Mean absolute error", f"{bt['mae']:.3f} index points"],
             ["Root mean squared error", f"{bt['rmse']:.3f}"], ["Mean absolute percentage error", f"{bt['mape_pct']:.3f}%"], ["Naive last-value forecast, MAE", f"{bt['naive_last_value_mae']:.3f}"],
             ["Share of held-out months inside the 95% band", f"{bt['interval_coverage_95'] * 100:.0f}% (12 of 12)"]], widths=[3.4, 2.6], size=10, align=["l", "c"]),
        P(f"Fitted to 2015-2024, the model predicts the 12 months of 2025 with a mean absolute error of {bt['mae']:.2f} index points ({bt['mape_pct']:.2f}%), about a third of the {bt['naive_last_value_mae']:.2f} of a naive forecast that repeats the last value, "
          f"and all 12 held-out values fall inside the 95% band. Because the series is generated from a trend plus seasonality plus noise, a trend-and-seasonality smoother is almost guaranteed to do well; the result confirms that the code is correct, nothing more. "
          f"The live forecast (fitted to all 132 months) moves from {last_hist:.1f} in December 2025 to {last_fc['value']:.1f} in December 2026 ({fc['forecast_pct_change']:+.2f}%), with a final-month band of {last_fc['lower']:.1f} to {last_fc['upper']:.1f}."),
    ]

    # ------------------------------------------------------------------ 8.3 base paper
    cmp_rows = []
    for m in F.MODELS:
        cmp_rows.append([F.MODEL_LABEL[m], f"{BASE_AUC[m]:.3f}", f"{F.COMPARE[m]['roc_auc']:.3f}", f"{F.COMPARE[m]['cv_roc_auc_mean']:.3f}"])
    out += [
        H2("8.3 Comparison with the base paper"),
        P(f"The base paper {n('base')} is the only quantitative reference for this project, and the comparison has to be read with care because almost everything differs. The table below sets the numbers side by side and the figure that follows plots them. "
          "**This is context, not a ranking.**"),
        TAB("Base paper and this project compared (ROC-AUC)", ["Model", "Base paper (hospital-level Group K-Fold)", "This project, test split", "This project, 5-fold CV"], cmp_rows,
            widths=[1.6, 2.0, 1.4, 1.4], size=9.5, align=["l", "c", "c", "c"]),
        FIG(F.fig("base_paper_comparison.png"), "ROC-AUC of the same four model families in the base paper and in this project (different data and protocols)", 5.6),
        TAB("What differs between the two studies", ["Aspect", "Base paper", "This project"], [
            ["Unit of analysis", "Hospitals (organisations)", "Individual people"],
            ["Data", "165 Korean hospitals, 825 hospital-year rows, 2019-2023, 236 line items reduced to 11 features", f"UCI Adult / Census Income, {F.N_ROWS:,} rows from 1994, 14 raw fields expanded to 26 columns"],
            ["Target", "Annual deficit (net income below zero), 41.2% positive", "Income above 50K, 23.9% positive; mapped to a profile band, not a distress label"],
            ["Validation", "Hospital-level Group K-Fold (primary), temporal hold-out 2019-22 to 2023, stratified K-Fold for reference", "Stratified 80/20 split and stratified 5-fold CV; one row per person, so no entity grouping and no temporal split"],
            ["Further analyses", "Counterfactual subsidy analysis, panel fixed-effects regression, DeLong tests, Altman Z'' baseline", "Not reproduced; SHAP, a logistic-regression table, a what-if screen, calibration and threshold analysis instead"],
            ["Deliverable", "A framework and findings", "A working web application around the same framework"],
        ], widths=[1.3, 2.6, 2.6], size=9, align=["l", "l", "l"]),
        P(f"Three observations can be drawn. First, the ordering of the families is similar: gradient-boosted trees lead and the linear model trails, although in this project Random Forest falls below Logistic Regression while in the base paper it sits between boosting and the linear baseline. "
          f"Second, the gap between boosting and the linear baseline is much smaller here ({A['xgb_vs_lr_auc_gain']:.3f} AUC) than in the base paper (0.066), consistent with a large, mostly categorical person-level data set in which main effects explain most of the signal. "
          f"Third, the absolute AUCs ({F.f3(M['roc_auc'])} against 0.842) must not be compared as a measure of skill: they are computed on different populations and different targets, with a much larger sample and a less demanding protocol here. "
          f"The base paper's own contrast between random and entity-grouped validation (0.860 to 0.831 for Random Forest) shows how much the protocol alone can move AUC. What this project adds to the base paper is not a better number but the extension of the "
          "approach to individuals and its delivery as an explainable application."),
    ]

    # ------------------------------------------------------------------ 8.4 sample inputs/outputs
    srows = []
    for s in SP:
        i = s["inputs"]
        srows.append([s["id"], f"{i['age']}, {i['workclass']}, {i['education']}, {i['marital-status']}, {i['occupation']}, {i['sex']}, gains {i['capital-gain']:,}, losses {i['capital-loss']:,}, {i['hours-per-week']} h",
                      f"{s['strength_pct']}%", f"{s['profile']} / {s['risk']}"])
    drows = []
    for s in SP:
        drows.append([s["id"], "; ".join(f"{d['label']} ({d['shap']:+.3f})" for d in s["top_drivers"])])
    out += [
        H2("8.4 Sample inputs and outputs"),
        P("Five profiles were sent to the running API (`POST /api/predict`) by `scripts/error_analysis.py`; the table lists the inputs and the output of the system, copied from `artifacts/sample_predictions.json`. "
          "Profile A is the first record of the Adult data set; the others were written to span the range of outputs."),
        TAB("Sample profiles and the system's output", ["ID", "Inputs", "Strength", "Profile / risk"], srows, widths=[0.4, 3.9, 0.8, 1.4], size=9, align=["c", "l", "c", "l"]),
        TAB("Strongest drivers reported for each sample (two strengthening, one weakening)", ["ID", "SHAP contributions (log-odds)"], drows, widths=[0.4, 6.1], size=9, align=["c", "l"]),
        P("The five outputs behave sensibly. Profile B (52, Masters, married, executive, gains 7,688) is near certain to be Established because the capital gain contributes +4.678 on the log-odds scale; Profile D (22, part-time, high-school graduate) is "
          "far below the Emerging threshold, with age the main weakening factor; Profile E combines a doctorate and long hours with a divorced status and investment losses and lands in Established with a mixed explanation (education +1.813, "
          "losses +1.125, a pattern learned from the training data and not advice to incur losses, against marital status -1.466). Profile C falls in the Developing band. "
          "The what-if comparison shown in Section 8.1, applied to Profile A, with gains of 80,000 and 50 weekly hours, moved the score from 1.1% to 99.5% (+98.43 percentage points)."),
    ]

    # ------------------------------------------------------------------ 8.5 success/failure
    fp, fn_ = EA["confident_false_positives"], EA["confident_false_negatives"]
    frows = [[f"FP{i + 1}", _row_text(r), f"{r['p']:.4f}"] for i, r in enumerate(fp[:3])] + [[f"FN{i + 1}", _row_text(r), f"{r['p']:.4f}"] for i, r in enumerate(fn_[:3])]

    def g(group, key, field):
        return G[group][key][field]

    grows = []
    for grp, keys in (("Sex", ["Female", "Male"]), ("Marital status", ["Married-civ-spouse", "All other statuses"]),
                      ("Education tier", ["Secondary-or-below", "Higher-secondary", "Tertiary"]), ("Age band", ["18-25", "26-35", "36-50", "51-65", "65+"])):
        for k in keys:
            d = G[grp][k]
            grows.append([grp, k, f"{d['n']:,}", F.pct(d["actual_pos_rate"]), F.pct(d["pred_pos_rate"]), F.pct(d["recall"]), F.pct(d["fpr"]), F.pct(d["precision"])])
    out += [
        H2("8.5 Success and failure analysis"),
        H3("Where the model succeeds"),
        P(f"The model is right on {SM['n_right']:,} of {F.N_TEST:,} test records and is confident when it is right: its mean confidence (the probability it assigns to the class it predicts) is {SM['mean_confidence_right']:.3f} on correct predictions against "
          f"{SM['mean_confidence_wrong']:.3f} on errors. {SM['right_with_conf_ge_0.9']:,} correct predictions have confidence of at least 0.9 while only {SM['wrong_with_conf_ge_0.9']} errors do, so a very confident prediction is wrong about once in "
          f"{(SM['right_with_conf_ge_0.9'] + SM['wrong_with_conf_ge_0.9']) // SM['wrong_with_conf_ge_0.9']} cases. The Emerging band is the strongest: {bc['Emerging']:,} rows, of which {F.pct(ba['Emerging'])} are actually above 50K. "
          f"The Adult data also contain an awkward spike at an investment gain of 99,999 (a value that appears to be a censoring code): all {SM['rows_gain_99999_in_test']} test rows with that value are above 50K, which is consistent with the model treating a very large gain as a strong positive signal."),
        H3("Where the model fails"),
        P(f"Of the {SM['n_wrong']:,} errors, {SM['wrong_with_conf_lt_0.6']} are low-confidence (below 0.6) and {SM['borderline_0.35_0.65']:,} test rows lie in the borderline probability range of 0.35 to 0.65, which is where most mistakes concentrate. "
          "The most confident mistakes are listed below. They are mostly cases where a single dominant attribute, usually capital gain, contradicts the label: the model sees a large capital gain (or, in the third case, a reported investment loss, which it also associates with higher incomes) and says 'above 50K', while the person's recorded income is below; "
          "the false negatives are young, unmarried or part-time workers whose recorded income is nonetheless high. Both kinds are individually plausible and show a limit of an eleven-attribute census profile: it cannot see the factors that "
          "actually separate such people."),
        TAB("Most confident errors on the test split (FP: predicted above 50K, actually at most 50K; FN: the reverse)", ["Case", "Record", "P(above 50K)"], frows, widths=[0.6, 5.0, 0.9], size=9, align=["c", "l", "c"]),
        H3("Error rates by group"),
        P("Because the model uses sex, marital status and age, the error rates were broken down by these groups on the test split. The table gives, for each group, the share who actually earn above 50K, the share the model predicts to, "
          "and the recall, false-positive rate and precision of the model. This is a descriptive check, not a fairness audit: no fairness criterion was set in advance and no mitigation was tried."),
        TAB("Test-split outcomes by group (threshold 0.5)", ["Attribute", "Group", "Rows", "Actually >50K", "Predicted >50K", "Recall", "False-positive rate", "Precision"], grows,
            widths=[0.9, 1.4, 0.55, 0.75, 0.75, 0.6, 0.8, 0.7], size=8.5, align=["l", "l", "c", "c", "c", "c", "c", "c"]),
        P(f"The disparities are large and they follow the data. In the test split {F.pct(g('Sex', 'Female', 'actual_pos_rate'))} of women and {F.pct(g('Sex', 'Male', 'actual_pos_rate'))} of men earn above 50K; the model predicts {F.pct(g('Sex', 'Female', 'pred_pos_rate'))} and "
          f"{F.pct(g('Sex', 'Male', 'pred_pos_rate'))}. Its precision is almost identical for the two groups ({F.pct(g('Sex', 'Female', 'precision'))} and {F.pct(g('Sex', 'Male', 'precision'))}), but recall is lower for women ({F.pct(g('Sex', 'Female', 'recall'))} against {F.pct(g('Sex', 'Male', 'recall'))}), "
          f"so high-earning women are missed more often than high-earning men. Married civilian-spouse households have a recall of {F.pct(g('Marital status', 'Married-civ-spouse', 'recall'))} but also a false-positive rate of {F.pct(g('Marital status', 'Married-civ-spouse', 'fpr'))}, "
          f"while every other marital status has a recall of only {F.pct(g('Marital status', 'All other statuses', 'recall'))} and a false-positive rate of {F.pct(g('Marital status', 'All other statuses', 'fpr'))}: the model leans heavily on being married. "
          f"Recall also rises steeply with education tier ({F.pct(g('Education tier', 'Secondary-or-below', 'recall'))} for secondary or below, {F.pct(g('Education tier', 'Tertiary', 'recall'))} for tertiary) and with age band (from {F.pct(g('Age band', '18-25', 'recall'))} at 18-25 to {F.pct(g('Age band', '36-50', 'recall'))} at 36-50). "
          "In plain terms, the model reproduces a historical income pattern in which men, married people, graduates and the middle-aged more often earn above 50K, and it is least able to recognise a high earner who is young, unmarried, a woman or has little formal education. "
          "That is a property of the 1994 data and of the model's reliance on it, and it is the main reason the application is described throughout as informational and not as a basis for decisions about individuals."),
        H3("Extrapolation and the what-if screen"),
        P("The what-if results (+98.43 and +98.26 points in the examples above and in Chapter 7) are a different kind of failure. Raising investment gains from a few thousand to tens of thousands or a million moves the score to the top of the scale "
          "because in the training data almost everyone with large gains earns above 50K. The model has not learned that a person can raise their own gains; it has learned a correlation, and the what-if screen applies it as if it were an intervention. "
          "The interface labels the result as a simulation; the numbers should be read as 'people with such gains in this data are almost all high earners', never as 'what you would earn if you changed this'."),
    ]

    # ------------------------------------------------------------------ 8.6 limitations
    out += [
        H2("8.6 Limitations of the results"),
        B("**Different target from the objective.** The model predicts income above 50K. It is a financial-profile signal built from census attributes, not a credit-default or distress model, and the report makes no claim about repayment.",
          "**Dated, single-source data.** The training data are 1994 US census records. Accuracy figures say how well the model reproduces that data, not how it would perform on a current or non-US population.",
          "**Synthetic forecast.** The forecast component was validated only against its own generator. Real economic indicators were not used.",
          "**Selection on the test split and no tuning.** The best model was chosen by test ROC-AUC, hyperparameters were fixed, and no significance test was run; the cross-validated AUC (0.929) is the safer estimate.",
          "**Single random split.** One stratified split and one cross-validation were run with one random seed (42). The variability across splits was not measured beyond the fold standard deviations.",
          "**No fairness audit.** Section 8.5 shows large group differences in recall and in predicted positive rate. They were measured but not corrected.",
          "**Modest recall.** About one in three high-income people is missed at the default threshold; the threshold can be lowered at the cost of precision.",
          "**Uncertain generalisation of scenarios.** What-if scores far from the bulk of the training data are extrapolations."),

        # ------------------------------------------------------------------ 8.7 objectives
        H2("8.7 Objectives versus outcomes"),
        P("The six objectives are those recorded in the project's objectives document. The table states plainly what was achieved against each."),
        TAB("Objectives versus outcomes", ["No.", "Objective", "Status", "Outcome"],
            [[str(i + 1), S.OBJECTIVES[i], S.OBJECTIVE_STATUS[i][0], S.OBJECTIVE_STATUS[i][1]] for i in range(6)], widths=[0.4, 1.9, 0.8, 3.4], size=9, align=["c", "l", "c", "l"]),
        P("Three of the six objectives are met in full and three in part. The parts that were not met share one cause: the project used a public census data set instead of a data set that combines demographic and transactional or credit-history variables, "
          "and no such data set was available openly. The consequences are that the classifier answers 'how does this profile compare with higher-earning profiles' instead of 'how likely is distress or default', and that forecasting is demonstrated on an aggregate index, not on a person's finances. "
          "Within those limits, the system delivers what was promised: a working, explainable, evaluated and deployed pipeline from demographic input to profile, explanation and forecast."),
    ]
    return out
