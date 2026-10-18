"""Chapter 8: Results and output screens. Every number is read from experiments/churn_synthetic/*.json."""

from . import facts as F
from .blocks import B, FIG, H1, H2, P, TAB
from .refs import cite

K5 = ("accuracy", "precision", "recall", "f1_score", "roc_auc")
HDR = ["Model", "Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC"]
AL = ["l", "c", "c", "c", "c", "c"]
EX = F.EXTRA
API = F.API["repeated_ms"]
L = F.LAT


def row(name, m):
    return [name] + [f"{m[k]:.4f}" for k in K5]


def row_ms(name, m):
    return [name] + [f"{m[k]['mean']:.4f} ± {m[k]['std']:.4f}" for k in K5]


def shot(name):
    return F.shot(name)


def sw(x):
    return next(s for s in EX["threshold_sweep"] if abs(s["threshold"] - x) < 1e-9)


def lf(x):
    return next(s for s in EX["targeting_lift"] if abs(s["top_fraction"] - x) < 1e-9)


def blocks():
    cw, sm, no = F.CW, F.SMOTE, F.NONE
    m15 = F.M15["app_default_split"]["class_weight"]["models"]
    out = [
        H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
        H2("8.1 Experimental Setup"),
        P("All results come from `scripts/run_experiments.py`, `scripts/make_figures.py` and `scripts/measure_api_latency.py`, which call the same `src/` functions as the application and write their raw output to `experiments/churn_synthetic/`. "
          "Re-running them reproduces the numbers below on the same software versions."),
        TAB("Experimental setup", ["Item", "Value"],
            [["Data", f"`data/customer_churn.csv`: {F.DS['rows']:,} synthetic customers, 21 columns, churn rate {F.DS['churn_rate_pct']}% (264 churners)"],
             ["Split", f"Stratified 80/20, random_state 42: {F.SP['train_rows']} training rows and {F.SP['test_rows']} test rows ({F.SP['test_churners']} churners)"],
             ["Models", "Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, Histogram Gradient Boosting (settings in Section 6.5)"],
             ["Imbalance handling", "Class weights (headline), SMOTE and none (Section 8.6)"],
             ["Extra protocols", "Stratified 5-fold cross-validation and five random 80/20 splits (seeds 0-4) for the three required models"],
             ["Environment of record", f"Python {F.M['environment']['python']}, scikit-learn {F.M['environment']['sklearn']}, pandas {F.M['environment']['pandas']}, numpy {F.M['environment']['numpy']}; Windows 11, Intel Core i5-12500, CPU only"]],
            widths=[1.5, 4.5], size=9.5),
        P("**Reading the numbers.** The data are synthetic and the test split is small, so every figure below is evidence about the pipeline on this data, not about real customers. "
          "Where a result could change by several points from split to split, the spread is shown next to it."),
        H2("8.2 Exploratory Findings"),
        P("The exploration of the data (Section 4.7) shows the relationships on which the models later rely: churn is 34.1% for month-to-month contracts against 12.5% for two-year contracts, 36.6% in the first year of tenure against 18.7% after four years, "
          "32.7% for fibre optic against 14.7% for customers without internet, and 33.4% for electronic check against 18.3% for automatic bank transfer. The base paper reports the same three drivers for the real Telco data "
          f"(month-to-month contracts, high monthly charges and short tenure) {cite('oprea')}; here they appear because the generator was built with them."),
        H2("8.3 Model Comparison"),
        P("Table below shows the five models on the held-out test split with class weights, the default of the Train page. Logistic Regression is recommended on F1 (0.4861), ROC-AUC (0.7224) and recall (0.6604); it is the saved active model."),
        TAB("Test-split metrics, 80/20 split, seed 42, class weights", HDR, [row(n, cw[n]) for n in F.MODEL_ORDER], widths=[1.7, 0.8, 0.8, 0.7, 0.8, 0.8], align=AL, size=9.5),
        FIG(F.fig("model_comparison.png"), "Test-split metrics of the five models (class weights, seed 42)", 6.0),
        P("Three points stand out. **First**, Gradient Boosting has the highest accuracy (0.7450) and precision (0.5357) but a recall of only 0.2830 (Hist Gradient Boosting is lower still at 0.1887), because boosting in this implementation takes no class weight and therefore favours the majority class; "
          "for a retention team that must find churners, its accuracy is misleading. **Second**, the three required models are close: Logistic Regression and Random Forest have F1 of 0.4861 and 0.4724, and the Decision Tree is lower at 0.3937. "
          "**Third**, ROC-AUC is about 0.72 for the best models, a moderate ability to rank churners above stayers, not a strong one."),
        P(f"**Sensitivity to the software environment.** The same script under scikit-learn 1.5.0 and pandas 2.2.1 gives identical Logistic Regression results but a different Random Forest on this 200-row split "
          f"(accuracy {m15['Random Forest']['accuracy']:.4f} against {cw['Random Forest']['accuracy']:.4f}; F1 {m15['Random Forest']['f1_score']:.4f} against {cw['Random Forest']['f1_score']:.4f}). "
          "Tree ensembles on 800 training rows are version-sensitive, which is another reason to treat single-split differences between the two best models as noise. The archived output is `metrics_sklearn1.5.0.json`."),
        H2("8.4 Confusion Matrices and Curves"),
        TAB("Confusion matrices on the test split (200 rows: 147 retained, 53 churners)", ["Model", "True negative", "False positive", "False negative", "True positive"],
            [[n] + [str(cw[n]["confusion_matrix"][0][0]), str(cw[n]["confusion_matrix"][0][1]), str(cw[n]["confusion_matrix"][1][0]), str(cw[n]["confusion_matrix"][1][1])] for n in F.MODEL_ORDER],
            widths=[1.9, 1.0, 1.0, 1.1, 1.0], align=["l", "c", "c", "c", "c"], size=10),
        P("Logistic Regression finds 35 of the 53 churners but flags 56 retained customers by mistake; Random Forest finds 30 and flags 44; Gradient Boosting finds only 15 and flags 13. "
          "The choice between them is a trade-off between wasted offers and lost customers, which the threshold analysis in Section 8.8 makes explicit."),
        FIG(F.fig("confusion_matrices.png"), "Confusion matrices of the three required models", 6.0),
        FIG(F.fig("roc_pr_curves.png"), "ROC and precision-recall curves of the three required models on the test split", 6.0),
        H2("8.5 Stability of the Results"),
        P("A 200-row test set with 53 churners is small. To see how much the numbers move, the three required models were re-evaluated by stratified 5-fold cross-validation (200 held-out rows per fold) and on five random 80/20 splits."),
        TAB("Stratified 5-fold cross-validation, class weights (mean ± sd over folds)", HDR, [row_ms(n, F.CV[n]) for n in F.MODEL_ORDER[:3]], widths=[1.4, 0.95, 0.95, 0.95, 0.95, 0.95], align=AL, size=8.5),
        TAB("Five random 80/20 splits, seeds 0-4, class weights (mean ± sd)", HDR, [row_ms(n, F.SPL[n]) for n in F.MODEL_ORDER[:3]], widths=[1.4, 0.95, 0.95, 0.95, 0.95, 0.95], align=AL, size=8.5),
        FIG(F.fig("stability.png"), "F1-score and ROC-AUC on the single split, in cross-validation and on five splits (error bars: one standard deviation)", 6.0),
        P("Logistic Regression and Random Forest are within one standard deviation of each other on F1 and ROC-AUC in both protocols, so **the data do not support calling either one better**. Logistic Regression has the higher recall and Random Forest the higher precision and accuracy. "
          "The Decision Tree is the weakest on accuracy, precision, F1 and ROC-AUC (its recall is not the lowest). The spread on F1 is 0.03-0.05 and on recall 0.04-0.10, so differences of a few points on a single split should not be over-read."),
        H2("8.6 Effect of Imbalance Handling"),
        TAB("Logistic Regression and Random Forest under the three strategies (single split)", ["Model", "Strategy", "Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC"],
            [[n, s, *[f"{src[n][k]:.4f}" for k in K5]] for n in ("Logistic Regression", "Random Forest") for s, src in (("None", no), ("Class weights", cw), ("SMOTE", sm))],
            widths=[1.4, 1.1, 0.75, 0.75, 0.7, 0.7, 0.7], align=["l", "l", "c", "c", "c", "c", "c"], size=9),
        FIG(F.fig("imbalance_strategy.png"), "Accuracy, recall and F1 of Logistic Regression and Random Forest under the three imbalance strategies", 6.0),
        P("Without any handling the models look good on accuracy (0.7450 for Logistic Regression, 0.7550 for Random Forest) but recall collapses to 0.1887 and 0.0943: they miss most churners. Class weights and SMOTE restore recall at the cost of precision. "
          "SMOTE gave the best single-split F1 for Logistic Regression (0.5263) but was tested on one split only, so it is not claimed to be better than class weights. This is the reason the application selects on F1 and not on accuracy."),
        H2("8.7 Drivers of Churn"),
        FIG(F.fig("feature_importance.png"), "Largest Logistic Regression coefficients and permutation importance", 6.0),
        P("For Logistic Regression the largest absolute coefficients belong to contract type (Month-to-month 0.825 and Two year 0.791), monthly charges (0.558), automatic bank-transfer payment (0.408), tenure (0.400) and electronic-check payment (0.388). "
          "Permutation importance, which measures the fall in accuracy when one feature is shuffled, is led by MonthlyCharges (0.042) and Contract: Month-to-month (0.028); the others are 0.01 or less, which is noise-level on 200 rows. "
          "The generator used contract type, electronic check, tenure, support and security add-ons, fibre optic and monthly charges as drivers, so the model recovers the main ones. This confirms the pipeline works; it is not evidence about real customers."),
        H2("8.8 Threshold, Calibration and Targeting"),
        P("**Decision threshold.** The batch table calls a customer a predicted churner at 50% or more. Moving the threshold trades precision for recall:"),
        TAB("Logistic Regression: effect of the decision threshold on the test split", ["Threshold", "Flagged of 200", "Precision", "Recall", "F1"],
            [[f"{t:.2f}", str(sw(t)["flagged"]), f"{sw(t)['precision']:.3f}", f"{sw(t)['recall']:.3f}", f"{sw(t)['f1']:.3f}"] for t in (0.30, 0.40, 0.50, 0.60, 0.70)],
            widths=[1.2, 1.3, 1.2, 1.1, 1.1], align=["c"] * 5, size=10),
        FIG(F.fig("threshold_sweep.png"), "Precision, recall and F1 against the decision threshold (Logistic Regression)", 4.6),
        P("F1 is almost flat between 0.40 and 0.60 (0.503 to 0.512), so the 50% cut-off is a reasonable default; a retention team with cheap offers would lower it (at 0.30 recall is 0.962 but only 32% of those flagged are churners), and a team with costly offers would raise it."),
        P(f"**Calibration.** The predicted probabilities are not calibrated. The mean predicted probability on the test split is {EX['mean_predicted_probability']:.3f} against an observed churn rate of {EX['observed_churn_rate_test']:.3f}, every reliability bin over-predicts, "
          f"and the Brier score is {EX['brier_score']:.3f}, no better than the {EX['brier_no_skill_constant_base_rate']:.3f} of a constant predictor that always outputs the base rate. Class weights are the likely cause of the over-prediction: they shift the scores upward on purpose. "
          "The scores are therefore a **ranking**, and the risk bands should not be read as chances of leaving. Recalibration (for example Platt scaling or isotonic regression) is listed as future work."),
        FIG(F.fig("calibration.png"), "Reliability of the predicted probabilities (Logistic Regression, test split)", 4.2),
        P(f"**Targeting value.** If the retention team contacts customers in order of predicted risk, the top 10% (20 customers) contain {lf(0.1)['churners_captured']} churners (precision {lf(0.1)['precision']:.2f}, lift {lf(0.1)['lift']:.2f}); the top 20% (40 customers) contain {lf(0.2)['churners_captured']} "
          f"of the 53 churners ({lf(0.2)['capture_rate'] * 100:.1f}%, precision {lf(0.2)['precision']:.3f}, lift {lf(0.2)['lift']:.2f}); the top 30% contain {lf(0.3)['churners_captured']} ({lf(0.3)['capture_rate'] * 100:.1f}%); and the top 50% contain {lf(0.5)['churners_captured']} ({lf(0.5)['capture_rate'] * 100:.1f}%). "
          "The lift of 1.5 to 2 over random contact is a moderate gain, and with 20 to 60 contacts the counts are small."),
        FIG(F.fig("targeting_lift.png"), "Churners captured when contacting the highest-scored customers first (test split)", 4.4),
        H2("8.9 Comparison with the Base Paper"),
        P(f"The comparison is for context only. The base paper {cite('oprea')} and this project use different data, splits, models and goals, and **the metrics are not comparable**: "
          "the paper's real 7,043-row data with a 2,113-row test set against this project's 1,000 synthetic rows with a 200-row test set."),
        TAB("Base paper compared with this project", ["Aspect", "Base paper (Oprea and Bara, 2026)", "This project"],
            [["Data", "Real Telco churn, 7,043 rows, 21 columns, 26.5% churn", "Synthetic, 1,000 rows, same schema, 26.4% churn"],
             ["Split", "70/30, test 2,113 rows", "80/20 stratified, test 200 rows (53 churners)"],
             ["Classifiers", "LR, SVC, RF, balanced RF, CatBoost, XGBoost, LightGBM", "LR, DT, RF (required); GB, HGB (optional); scikit-learn only"],
             ["Imbalance", "class weights, scale_pos_weight", "class weights, SMOTE (train only), none"],
             ["Objective", "Recall", "F1 by default; any of five metrics selectable"],
             ["Reported metrics", "Accuracy 0.6990-0.7932; recall 0.4112-0.9077; ROC-AUC 0.83-0.86 for CatBoost, XGBoost, LightGBM", f"Accuracy 0.6150-0.7450; recall 0.1887-0.6604; ROC-AUC 0.6081-0.7224 (single split)"],
             ["Explainability", "SHAP, LIME and a unified perturbation explainer; Spearman 0.8125 with SHAP; SHAP 289.4 s, LIME 35.1 s, PBE 18.5 s", "Built-in and permutation importance, coefficient-times-value local explanation; SHAP path present but not exercised; no LIME, no unified perturbation explainer"],
             ["Beyond the paper", "Framework only", "Risk bands, Customer 360, what-if, retention rules, batch scoring, drift check, web interface"],
             ["Drivers found", "Month-to-month contracts, high monthly charges, tenure below 20 months", "The same three, on data generated with those relationships"]],
            widths=[1.1, 2.5, 2.4], size=8.5),
        P("The project's metrics are lower than the paper's boosted models, as expected: it uses simpler models, no hyper-parameter search, a much smaller training set and synthetic data in which churn contains deliberate noise. "
          "No claim is made that the project matches or beats the paper; its contribution is the application around a churn model, not a better churn model."),
        H2("8.10 Risk Segmentation of the Customer Base"),
        TAB("Customers per risk band (1,000 customers, saved Logistic Regression model, thresholds 30 / 60 / 80)", ["Band", "Customers", "Share"],
            [[b, str(F.RISK["counts"][b]), f"{F.RISK['percentages'][b]}%"] for b in ("Low Risk", "Medium Risk", "High Risk", "Critical Risk")],
            widths=[2.0, 1.5, 1.5], align=["l", "c", "c"], size=10),
        FIG(F.fig("risk_bands.png"), "Customers per risk band at the default thresholds", 4.2),
        P(f"The mean score is {F.RISK['avg_probability']}%. These customers include the training rows, so the table shows the portfolio view that the dashboard presents and not generalisation. Because the scores are inflated by class weighting, "
          "the 266 customers in the High and Critical bands (26.6%) are the ones the rules treat as candidates for action; their share happens to be close to the 26.4% real churn rate, which should not be read as a calibration."),
        H2("8.11 Performance"),
        TAB("Measured response times", ["Measurement", "Result"],
            [["Train the five models, class weights (wall time, incl. evaluation)", f"{F.M['app_default_split']['class_weight']['wall_seconds']} s; Random Forest alone {F.CW['Random Forest']['fit_and_eval_seconds']} s"],
             ["Score one customer (preprocess + predict), 200 runs", f"median {L['single_customer_median']} ms, 95th percentile {L['single_customer_p95']} ms (pandas 3 / scikit-learn 1.9); {F.M15['inference_latency_ms']['single_customer_median']} ms median under pandas 2 / scikit-learn 1.5"],
             ["Score all 1,000 customers", f"{L['full_dataset_1000_rows_ms']} ms"],
             ["API median over 127.0.0.1: dashboard / Customer 360 / local explanation / what-if / retention / EDA", f"{API['dashboard']['median']} / {API['customer_360']['median']} / {API['xai_local']['median']} / {API['whatif']['median']} / {API['retention']['median']} / {API['eda']['median']} ms"],
             ["API: global explanation / evaluation / health", f"{API['xai_global']['median']} / {API['evaluation']['median']} / {API['health']['median']} ms"],
             ["API: batch predict 25 rows (no drivers)", f"median {API['batch_predict_25_rows_no_drivers']['median']} ms"],
             ["API one-off: load sample / prepare / train 3 models / save model", f"{F.API['once_ms']['load_sample']} / {F.API['once_ms']['prepare']} / {F.API['once_ms']['train_3_models']} / {F.API['once_ms']['save_model']} ms"]],
            widths=[3.0, 3.0], size=9),
        P("Every call is well under a second. Two measurement notes: single-customer scoring is about 6.7 times slower under the newer pandas and scikit-learn (19 ms against 2.9 ms), and a request through the hostname `localhost` carries an extra 2.04 s on this Windows machine because of IPv6 name resolution, "
          "which is why the figures were taken against 127.0.0.1, the address the web interface proxy uses. Timings vary between runs and depend on whether other programs are using the machine."),
        H2("8.12 Output Screens"),
        P("The screenshots were captured from the running application at 1440 x 900 with the sample data loaded, three models trained and the Logistic Regression model saved. They show real values, not mock-ups."),
        FIG(shot("04_dashboard.png"), "Retention dashboard: portfolio KPIs, churn split and risk distribution", 5.6),
        FIG(shot("05_data.png"), "Data upload page: data quality report and preparation of the working copy", 5.6),
        FIG(shot("06_explore.png"), "Exploration page: churn rate by customer attribute", 5.6),
        FIG(shot("07_train.png"), "Model training page: metric choice, model comparison and saving the active model", 5.6),
        FIG(shot("08_evaluation.png"), "Model evaluation page: ROC and precision-recall curves of the models trained in the session", 5.6),
        FIG(shot("09_risk.png"), "Customer risk segmentation: editable thresholds and customers per band (default 30 / 60 / 80)", 5.6),
        FIG(shot("10_customer360.png"), "Customer 360: profile, score, band, drivers and retention actions", 5.6),
        FIG(shot("11_explain.png"), "Explainable AI page: permutation importance, with the notice that SHAP is not installed", 5.6),
        FIG(shot("12_whatif.png"), "What-if page: original and scenario score for an edited customer", 5.6),
        FIG(shot("13_retention.png"), "Retention page: rule-based actions for High and Critical customers", 5.6),
        FIG(shot("14_batch.png"), "Batch prediction page: scoring a CSV with risk bands and top factors", 5.6),
        FIG(shot("15_monitoring.png"), "Monitoring page: active model details and the drift check", 5.6),
        H2("8.13 Discussion and Threats to Validity"),
        B("**What the results support.** The pipeline works end to end, recovers the contract, charge and tenure effects built into the synthetic data, ranks customers moderately well (ROC-AUC about 0.72, lift about 2 in the top 20%), and shows why accuracy is a poor guide on imbalanced data.",
          "**What they do not support.** Any claim about accuracy on real customers; a ranking of Logistic Regression against Random Forest; calibrated probabilities; the business value of the retention rules.",
          "**Data validity.** The data are synthetic and the churn label is generated from the same features the model sees, so the relationships are cleaner than in real data.",
          "**Statistical validity.** The test set has 53 churners; standard deviations of 0.03-0.10 on several metrics mean that differences of a few points are not reliable.",
          "**Environment validity.** Tree-ensemble scores differ between scikit-learn versions on this small split.",
          "**Explanation validity.** The explanations come from coefficients and permutation importance. They describe the model, not the customers' reasons, and they were not compared with SHAP."),
    ]
    return out
