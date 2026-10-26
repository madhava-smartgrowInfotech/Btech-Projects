"""Chapter 8: Results and Output Screens (also document 14). Every number is built from facts.py (evaluation/*.json)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, PAIR, TAB
from .refs import cite

R, X, S = F.R, F.X, F.S
M = R["models"]
ORDER = F.MODEL_ORDER_REAL


def pair(left, right, cap_l, cap_r, width=3.0):
    return PAIR([(F.shot(left), cap_l), (F.shot(right), cap_r)], width)


def screen(name, caption, base=5.6, max_h=5.6):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def row6(model, blk, keys=("accuracy", "balanced_accuracy", "precision", "recall", "f1", "roc_auc")):
    return [model] + [F.pm(blk, k) for k in keys]


def comparison_rows():
    return [row6(m, M[m]) for m in ORDER]


def split_rows():
    return [row6(m, R["split_70_30"][m]) for m in ("Logistic Regression", "Random Forest", "HistGradientBoosting")]


def imbalance_rows():
    names = {"none": "none", "class_weight": "class weights", "oversample": "random oversampling"}
    rows = []
    for m in ("Logistic Regression", "Random Forest"):
        for k, label in names.items():
            r = R["imbalance"][m][k]
            rows.append([m, label, F.pm(r, "balanced_accuracy"), F.pm(r, "recall"), F.pm(r, "f1"), F.pm(r, "roc_auc")])
    return rows


def threshold_rows():
    return [[f"{t['threshold']:.2f}", f"{t['precision']:.3f}", f"{t['recall']:.3f}", f"{t['f1']:.3f}", f"{t['balanced_accuracy']:.3f}"] for t in R["threshold_sweep_logreg"]]


def calib_rows():
    return [[c["bin"], str(c["n"]), f"{c['mean_pred']:.3f}", f"{c['observed']:.3f}", f"{c['observed'] - c['mean_pred']:+.3f}"] for c in R["calibration_logreg"]]


def rf_rows():
    return [[k, F.pm(v, "balanced_accuracy"), F.pm(v, "roc_auc")] for k, v in R["rf_n_estimators"].items()]


def importance_rows():
    fi = R["feature_importance"]
    g, p, c = fi["random_forest_gini"][:8], fi["random_forest_permutation_auc"][:8], fi["logistic_abs_coef"][:8]
    return [[str(i + 1), f"{p[i]['feature']} ({p[i]['value']:.3f})", f"{g[i]['feature']} ({g[i]['value']:.3f})", f"{c[i]['feature']} ({c[i]['value']:.3f})"] for i in range(8)]


def ablation_rows():
    rows = []
    for m in ("Logistic Regression", "Random Forest", "XGBoost"):
        a, w = X["with_all_features"][m], X["without_posthoc_features"][m]
        rows.append([m, F.pm(a, "balanced_accuracy"), F.pm(w, "balanced_accuracy"), F.pm(a, "roc_auc"), F.pm(w, "roc_auc")])
    return rows


def retrieval_rows():
    return [[k] + [F.pm(v, key) for key in ("accuracy", "balanced_accuracy", "recall", "f1", "roc_auc")] for k, v in X["retrieval_only_structured"].items()]


def shipped_rows():
    rows = []
    for m in F.MODEL_ORDER_APP:
        r = S["models"][m]
        rows.append([m + (" (selected)" if m == S["best_model"] else "")] + [F.pm(r, k) for k in ("accuracy", "balanced_accuracy", "precision", "recall", "f1")])
    return rows


def syn_vs_real_rows():
    rows = []
    for m in ("Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"):
        a, r = R["synthetic_structured_only"][m], M[m]
        rows.append([m, F.pm(a, "balanced_accuracy"), F.pm(r, "balanced_accuracy"), F.pm(a, "roc_auc"), F.pm(r, "roc_auc")])
    return rows


def transfer_rows():
    res = R["synthetic_to_real"]["results"]
    return [[m, f"{res[m]['accuracy']:.3f}", f"{res[m]['balanced_accuracy']:.3f}", f"{res[m]['f1']:.3f}", f"{res[m]['roc_auc']:.3f}"] for m in res]


def industry_rows():
    return [[g, str(v["n"]), f"{v['success_share']:.2f}", f"{v['accuracy']:.2f}"] for g, v in X["per_industry_rf_seed42_split"].items()]


def blocks():
    rf, lr, xg = M["Random Forest"], M["Logistic Regression"], M["XGBoost"]
    n_test = round(F.REAL_ROWS * 0.2 + 0.4)
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1
    b += [H2("8.1 What was measured, and on which data"),
          P("Two tables of start-ups are involved and the numbers of this chapter must never be read without knowing which one they come from. "
            f"The **shipped application** runs on a synthetic fallback of {F.SYN_ROWS:,} generated start-ups ({F.SYN_SUCCESS} SUCCESS, {F.SYN_FAILURE} FAILURE) that has the schema of the public table and a template-generated business description for each row, because the Kaggle download "
            "needed a login. The descriptions of the two classes are written from different templates, so the text channel leaks the label by construction. Scores on this table are a check that the pipeline works, not evidence of real-world skill. "
            f"The **real table** is the public \"Startup Success Prediction\" data {cite('kaggle')}: {F.REAL_ROWS} start-ups after de-duplication ({F.REAL_SUCCESS} acquired = SUCCESS, {F.REAL_FAILURE} closed = FAILURE), "
            "all United States, 16 structured columns plus state and industry, and no description text. Every real measurement below uses it with the structured features only."),
          TAB("The two tables", ["", "Shipped synthetic table", "Real public table"],
              [["Rows", f"{F.SYN_ROWS:,}", f"{F.REAL_ROWS}"], ["SUCCESS / FAILURE", f"{F.SYN_SUCCESS} / {F.SYN_FAILURE} (42.5 % / 57.5 %)", f"{F.REAL_SUCCESS} / {F.REAL_FAILURE} (64.6 % / 35.4 %)"],
               ["Description text", "Yes (templates; leaks the label)", "None"], ["Used for", "What the application serves and its dashboards", "All real-data experiments (`scripts/run_experiments.py`, `scripts/extra_experiments.py`)"],
               ["Test fold size (20 %)", "280", f"{n_test}"]],
              widths=[1.5, 2.6, 2.4], align=["l", "l", "l"], size=9.5),
          FIG(F.fig("f13_class_balance.png"), "Class balance of the two tables: success is the minority class in the synthetic table and the majority in the real table.", 3.8),
          P(f"Protocol: five repeated stratified 80/20 splits with seed 42 (the protocol of {cite('maarouf')}), preprocessing fitted on the training part only, mean ± standard deviation over the five splits. Balanced accuracy is the primary metric because the classes are unequal; "
            "accuracy, precision, recall and F1 refer to the SUCCESS class, and ROC-AUC is added for the real-data studies. With about 185 test start-ups per split, a standard deviation of 0.02 to 0.03 is expected, and differences smaller than that should not be read as a ranking. "
            f"The real-data study ran in {R['runtime_seconds']:.0f} s and the extra studies in {X['runtime_seconds']:.0f} s on {F.HARDWARE}.")]

    # ------------------------------------------------------------------ 8.2
    b += [H2("8.2 Output screens"),
          P("All screens were captured from the running application with a real browser session (Google Chrome driven by Playwright, 1440 pixels wide, dark theme, demo account). The data behind them is the synthetic fallback the application serves, "
            "so the dashboard, performance and insight figures describe that table; the prediction was made for one real submission typed into the form. Longer screens are shown scaled to fit the page; Appendix C shows enlarged parts of them."),
          H3("8.2.1 Landing page, sign-in and the empty form"),
          pair("01_landing_dark.png", "02_landing_light.png", "Landing page in the dark theme: headline \"Will this startup succeed?\", a live terminal card, the four-pass explanation and the six capabilities.",
               "The same landing page in the light theme; the numbers (1,400 start-ups, 42.5 % success, 0.749) are read live from the API.", 2.2),
          P("The landing page (first pair) explains the product in four passes: enter the signals, fuse and embed, retrieve comparable start-ups, predict and explain. The terminal card is filled by two live calls (`/api/health` and `/api/insights`) and the strip of counters near the bottom shows "
            "1,400 historical start-ups, a 42.5 % success rate, the best balanced accuracy 0.749 and four classifiers compared. Both themes are supported and the choice is remembered."),
          pair("03_login.png", "05_analyze_form_empty.png", "Sign-in screen with the demo account prefilled: API online, model Logistic Regression, 1,400 records.",
               "Analyze screen before anything is typed: funding and traction, company profile, investor signals and the description box.", 2.9),
          P("Sign-in (left) uses the demo account; the left panel confirms that the API is online, which model is serving and how many historical records it holds, and the footer says the data is a synthetic sample. "
            "The analyze form (right) groups the inputs of Chapter 6: nine numeric fields, an industry and state selector, the number of comparable cases k (10, 20, 30 or 50), seven investor flags and a description of up to 2,000 characters with a live counter."),
          H3("8.2.2 Dashboard"),
          screen("04_dashboard.png", "Dashboard: dataset counters, the selected model with its five validation scores, the class distribution, the model comparison chart and the pipeline configuration.", 4.6, 3.6),
          P("The dashboard opens after sign-in. It shows 1,400 historical start-ups (595 successful, 805 failed, a 42.5 % success rate), the best validated model Logistic Regression with balanced accuracy 0.749 ± 0.025, accuracy 0.751, precision 0.696, recall 0.739 and F1 0.716, "
            "a doughnut of the class distribution and a bar chart comparing the four models. An amber data note states that the public download was unavailable and the synthetic dataset is in use, so a reader cannot mistake these figures for real-world performance. "
            "The configuration card lists the 384-dimensional embedding, the structured weight 0.5, the default of 50 comparable cases and the class balance."),
          H3("8.2.3 Analyze: the filled form and the result"),
          screen("06_analyze_form_filled.png", "Analyze screen filled with the submission used throughout this chapter (a software start-up in California with USD 2.5 million raised in two rounds).", 4.4, 3.3),
          P("The submission is the one described in Section 8.5. The form validates before sending: an empty description or a number outside its range is refused with a message, and all processing happens on the local server."),
          screen("07_result.png", "Result screen: SUCCESS with confidence 83.3 % (Lower risk), the five key contributing features, the 25 / 25 evidence split and the table of comparable historical start-ups.", 4.6, 5.4),
          P("The result screen answers in four blocks. The headline shows the estimated outcome SUCCESS, the confidence 83.3 % (the larger of the two probabilities, success 0.83 and failure 0.17), the model, a risk label (Lower risk, because the outcome is SUCCESS and the confidence is at least 0.70) and the disclaimer that the estimate is not a guarantee. "
            "The explanation lists five feature contributions of the Logistic Regression and two retrieval statistics. The doughnut shows the evidence split of the k = 50 comparable start-ups, 25 SUCCESS and 25 FAILURE, and the table lists them with similarity (best 0.580), outcome, industry, state, funding, rounds and summary, sortable and paged (5 pages of 10). "
            "The last block repeats the submitted inputs."),
          H3("8.2.4 Model performance and insights"),
          screen("08_performance.png", "Model performance screen: comparison table of four models, bar charts, precision-recall scatter, the confusion matrix of Logistic Regression, retrieval-size and representation studies, and the top-15 coefficients.", 4.4, 6.0),
          P("The performance screen reproduces the evaluation of the shipped application on the synthetic table. The table ranks the models by balanced accuracy (Logistic Regression 0.749, XGBoost 0.697, Random Forest 0.641, Decision Tree 0.614); the confusion matrix gives the mean per test fold of 280 start-ups "
            "(122.2 true failures, 38.8 false successes, 31.0 missed successes, 88.0 true successes); the retrieval-size panel shows the weighted vote improving from 0.654 at k = 10 to 0.698 at k = 50; the representation panel shows structured only 0.714, text only 0.599 and combined 0.749; "
            "and the coefficient chart is led by round C, funding rounds, relationships and venture-capital backing. On the real table the order of the models is different (Section 8.3.1)."),
          screen("09_insights.png", "Startup insights screen: totals, success rate by industry, median funding by outcome, correlations with success and success rate by state, all computed from the 1,400 loaded records.", 4.4, 4.4),
          P("The insights screen is descriptive. Median funding is USD 993 K for successful and USD 592 K for failed start-ups; relationships (r = 0.261), funding rounds (0.240) and milestones (0.236) correlate most with success; industry success rates range from 36.4 % (Mobile) to 49.3 % (E-Commerce) and state rates from 38.2 % to 49.7 %. "
            "These are properties of the synthetic generator, not findings about real start-ups.")]

    # ------------------------------------------------------------------ 8.3
    b += [H2("8.3 Model performance"),
          H3("8.3.1 Comparison of the models on the real table"),
          P("The four classifiers of the application and HistGradientBoosting (a second boosting ensemble added for the study) were trained with the application's own preprocessing and hyper-parameters, class-weighted where the model supports it, on the structured features of the real table."),
          TAB("Real table, 5 x 80/20 splits, structured features (mean ± std)", ["Model", "Accuracy", "Balanced acc.", "Precision", "Recall", "F1", "ROC-AUC"], comparison_rows(),
              widths=[1.45, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85], align=["l"] + ["c"] * 6, size=8.5),
          FIG(F.fig("f01_model_comparison_real.png"), "Balanced accuracy, ROC-AUC and F1 of the five models on the real table (error bars: standard deviation over five splits).", 4.4),
          P(f"The tree ensembles lead: Random Forest and XGBoost reach balanced accuracy {F.pm(rf)} and {F.pm(xg)}, accuracy {F.pm(rf, 'accuracy')} and {F.pm(xg, 'accuracy')}, F1 {F.pm(rf, 'f1')} and {F.pm(xg, 'f1')}, with the best ROC-AUC for Random Forest ({F.pm(rf, 'roc_auc')}). "
            f"Logistic Regression is clearly behind on accuracy ({F.pm(lr, 'accuracy')}) but close on ROC-AUC ({F.pm(lr, 'roc_auc')}); the single Decision Tree has the worst ranking quality ({F.pm(M['Decision Tree'], 'roc_auc')}). "
            "Random Forest, XGBoost and HistGradientBoosting are within one standard deviation of each other on every metric, so no ranking among the three should be claimed. The ensemble advantage over Logistic Regression is real but modest: about 0.04 in balanced accuracy and 0.02 to 0.03 in ROC-AUC."),
          FIG(F.fig("f02_confusion_matrix_rf.png"), "Random Forest, mean confusion matrix per test fold (rows: actual class, columns: predicted class).", 2.2),
          P("For Random Forest the mean test fold of 185 start-ups holds 42.6 true failures, 22.4 false successes, 19.6 missed successes and 100.4 true successes: 84 % of the successes are found (recall 0.837) but only 66 % of the failures are recognised (42.6 of 65). "
            "Logistic Regression has the opposite balance, finding 74 % of the failures (48.4 of 65) but only 67 % of the successes (80.8 of 120)."),
          H3("8.3.2 The base-paper protocol: a single 70:30 split"),
          P(f"The declared base paper {cite('base')} uses a 70:30 split. The same models were also run with a stratified 70:30 split repeated over five seeds."),
          TAB("Real table, 70:30 split x 5 seeds (mean ± std)", ["Model", "Accuracy", "Balanced acc.", "Precision", "Recall", "F1", "ROC-AUC"], split_rows(),
              widths=[1.45, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85], align=["l"] + ["c"] * 6, size=8.5),
          P(f"Under this protocol Random Forest reaches accuracy {F.pm(R['split_70_30']['Random Forest'], 'accuracy')} and F1 {F.pm(R['split_70_30']['Random Forest'], 'f1')}, HistGradientBoosting {F.pm(R['split_70_30']['HistGradientBoosting'], 'accuracy')}, and Logistic Regression {F.pm(R['split_70_30']['Logistic Regression'], 'accuracy')}. "
            "The ensemble-over-linear ranking reported by the base paper is reproduced; its 85 to 92 % accuracy level is not (Section 8.4)."),
          H3("8.3.3 Handling the class imbalance"),
          P("Objective 3 assumes that success is rare. In the real table the opposite is true: 64.6 % of the start-ups are successes, so failure is the minority class. Class weights and random oversampling of the minority were compared with no correction."),
          TAB("Imbalance strategies on the real table (mean ± std)", ["Model", "Strategy", "Balanced acc.", "Recall (success)", "F1", "ROC-AUC"], imbalance_rows(),
              widths=[1.4, 1.4, 0.95, 0.95, 0.9, 0.9], align=["l", "l", "c", "c", "c", "c"], size=8.5),
          FIG(F.fig("f06_imbalance_strategies.png"), "Effect of class weights and oversampling on balanced accuracy and on the recall of the success class.", 4.4),
          P("Neither correction changes balanced accuracy or ROC-AUC beyond the noise. They move the operating point: removing the correction gives the highest recall of the (majority) success class (0.815 for Logistic Regression, 0.878 for Random Forest) and the correction trades part of it for better recognition of failures. "
            "The correction is therefore a choice of error balance, not a gain in discrimination; the application keeps balanced class weights."),
          H3("8.3.4 Decision threshold"),
          TAB("Logistic Regression: threshold sweep on the real table (pooled test predictions of the five splits)", ["Threshold on P(success)", "Precision", "Recall (success)", "F1", "Balanced acc."], threshold_rows(),
              widths=[1.7, 1.1, 1.3, 1.0, 1.2], align=["c"] * 5, size=9),
          FIG(F.fig("f03_threshold_sweep.png"), "Precision, recall, F1 and balanced accuracy of Logistic Regression as the decision threshold moves.", 4.0),
          P("Balanced accuracy is flat (0.71) between thresholds 0.30 and 0.50 and falls beyond 0.55. Raising the threshold buys precision (0.83 at 0.50, 0.91 at 0.75) at the price of recall (0.67 and 0.32). An investor who wants few false successes would choose a high threshold and accept that most successes are missed; "
            "one who wants a broad shortlist would choose 0.30 (recall 0.875, precision 0.781). The application uses 0.5."),
          H3("8.3.5 Size of the Random Forest"),
          TAB("Random Forest, number of trees (class-weighted, real table)", ["Trees", "Balanced acc.", "ROC-AUC"], rf_rows(), widths=[1.2, 1.8, 1.8], align=["c"] * 3, size=9.5),
          P("Going from 50 to 300 trees raises ROC-AUC from 0.803 to 0.816; 600 trees give no further gain. The application's 300 trees are therefore a sensible size."),
          H3("8.3.6 How far the probability can be trusted"),
          TAB("Logistic Regression (class-weighted), reliability of the predicted P(success) on the real table", ["Predicted bin", "Start-ups", "Mean predicted", "Observed success rate", "Observed - predicted"], calib_rows(),
              widths=[1.2, 0.9, 1.3, 1.5, 1.4], align=["c"] * 5, size=9),
          FIG(F.fig("f10_calibration.png"), "Reliability diagram: observed success rate against mean predicted probability (pooled test predictions).", 3.0),
          P("The curve lies above the diagonal in every bin: balanced class weights pull the probabilities towards 0.5 whereas the real success share is 64.6 %, so a start-up scored 0.25 actually succeeded 44 % of the time. The ranking is informative (observed success rises from 8 % to 93 % across the bins) "
            "but the number shown as confidence is a score, not a frequency. Isotonic or Platt re-calibration was not applied."),
          H3("8.3.7 Which features separate success from failure"),
          TAB("Top eight features on the real table", ["Rank", "Random Forest permutation (drop in ROC-AUC)", "Random Forest Gini", "Logistic Regression |coefficient|"], importance_rows(),
              widths=[0.5, 2.3, 2.0, 2.2], align=["c", "l", "l", "l"], size=8.5),
          FIG(F.fig("f04_feature_importance.png"), "Three rankings of the most informative features on the real table.", 5.6),
          P("Number of relationships comes first in both Random Forest rankings (Gini 0.162, permutation 0.060, four times the next feature). Milestones, the ages at the first and last milestone, total funding and the age at first funding follow. "
            "The linear model ranks differently: its largest coefficients belong to the state of Oregon, the top-500 flag, relationships and industry dummies, because a linear model spreads weight over many correlated and one-hot columns. "
            "Reading only one ranking would mislead; relationships and funding appear in all three. Objective 5 is met, with the caveat of Section 8.3.8."),
          H3("8.3.8 Fields recorded after the outcome"),
          P("Relationships, milestones and the two milestone-age fields are recorded around or after the outcome window in part, and the table has no dates that would allow them to be removed by time. The studies were repeated without these four fields."),
          TAB("Effect of removing the four post-hoc fields (real table, 5 x 80/20)", ["Model", "Balanced acc., all fields", "Balanced acc., without", "ROC-AUC, all fields", "ROC-AUC, without"], ablation_rows(),
              widths=[1.5, 1.3, 1.3, 1.2, 1.2], align=["l", "c", "c", "c", "c"], size=9),
          FIG(F.fig("f07_leakage_ablation.png"), "Balanced accuracy and ROC-AUC with and without relationships, milestones and the two milestone-age fields.", 4.4),
          P("ROC-AUC drops from 0.789 to 0.724 for Logistic Regression, from 0.816 to 0.719 for Random Forest and from 0.806 to 0.699 for XGBoost, and the ensembles lose their advantage over the linear model. "
            f"The headline real-data scores of Section 8.3.1 are therefore an upper bound for a true early-stage prediction. This is the look-ahead problem that the base paper itself cites {cite('zbikowski')} and that {cite('mashhadi')} avoids with temporal splits; this project could not, because the table has no dates {cite('leakage')}."),
          H3("8.3.9 Retrieval of comparable start-ups used as a classifier"),
          P("The application retrieves a balanced set of k comparable start-ups from the training rows and shows them with their outcomes. To test whether that evidence is also predictive, the retrieved set was used on its own, with no trained model: the similarity-weighted vote of the k neighbours decides the outcome. "
            "On the real table only the structured half of the fused vector exists."),
          TAB("Retrieval-only classifier on the real table (structured features, mean ± std)", ["k", "Accuracy", "Balanced acc.", "Recall", "F1", "ROC-AUC"], retrieval_rows(),
              widths=[0.6, 1.2, 1.25, 1.2, 1.2, 1.2], align=["c"] * 6, size=9),
          FIG(F.fig("f08_retrieval_k.png"), "Retrieval vote by number of neighbours: synthetic table with the fused vector (left) and real table with structured features only (right).", 4.6),
          P("Retrieval alone reaches balanced accuracy 0.70 to 0.71 and ROC-AUC 0.77 to 0.79: the same as Logistic Regression (0.709, 0.789) and below Random Forest and XGBoost (0.746). The comparable start-ups shown on the result screen are therefore not decoration; they carry about as much signal as the linear model. "
            "On the synthetic table the vote improves with k (0.654 at k = 10 to 0.698 at k = 50); on the real table k hardly matters, which is why the default of 50 is kept. The text half of the fusion could not be tested on real data."),
          H3("8.3.10 The shipped application on its synthetic table"),
          TAB("Shipped application, synthetic table, fused features, 5 x 80/20 (mean ± std)", ["Model", "Accuracy", "Balanced acc.", "Precision", "Recall", "F1"], shipped_rows(),
              widths=[1.8, 0.95, 0.95, 0.95, 0.95, 0.95], align=["l"] + ["c"] * 5, size=9),
          FIG(F.fig("f09_representation_study.png"), "Representation study on the synthetic table: structured only, text only, and the fused vector (Logistic Regression).", 3.2),
          P("On this table Logistic Regression is selected with balanced accuracy 0.749 ± 0.025 and the trees are worse, the opposite of the real-table order. The text-only model reaches 0.599 and the fused vector 0.749, a gain of 0.035 over structured features alone. "
            "Because the generated descriptions differ by class, this gain shows that the text channel can carry a label that was put there; it is not evidence that business descriptions help on real start-ups, where this was not tested. The ROC-AUC of the shipped fused model was not recorded by the application's own evaluation."),
          H3("8.3.11 Synthetic table against real table, and transfer between them"),
          TAB("Same models, structured features only, on each table (5 x 80/20)", ["Model", "Balanced acc., synthetic", "Balanced acc., real", "ROC-AUC, synthetic", "ROC-AUC, real"], syn_vs_real_rows(),
              widths=[1.5, 1.3, 1.3, 1.2, 1.2], align=["l", "c", "c", "c", "c"], size=9),
          FIG(F.fig("f05_synthetic_vs_real.png"), "The same four models on the synthetic and on the real table (structured features only).", 4.6),
          TAB(f"Trained on all {R['synthetic_to_real']['train_rows']:,} synthetic rows, tested on all {R['synthetic_to_real']['test_rows']} real rows", ["Model", "Accuracy", "Balanced acc.", "F1", "ROC-AUC"], transfer_rows(),
              widths=[1.8, 1.1, 1.2, 1.0, 1.1], align=["l"] + ["c"] * 4, size=9.5),
          P("The synthetic generator is not a poor imitation of the real structured data: a model trained only on the synthetic rows ranks the real start-ups with ROC-AUC 0.745 to 0.749 and balanced accuracy 0.67, a little below models trained on real rows. "
            "That makes the synthetic fallback a usable stand-in for a demonstration, but not a substitute for the real table: the tree models behave differently on the two, and the synthetic table contains the label-leaking text.")]

    # ------------------------------------------------------------------ 8.4
    b += [H2("8.4 Comparison with the base papers"),
          P(f"The declared base paper {cite('base')} reports \"85 to 92 %\" accuracy for Random Forest and Gradient Boosting on a 70:30 split with ADASYN oversampling, but gives no dataset size, no table of per-model results and no ROC-AUC. "
            f"The method on which the retrieval design builds, {cite('maarouf')}, uses 4,034 Crunchbase start-ups (1,418 successful, 35.15 %) with the same 5 x 80/20 protocol as this project, and reports balanced accuracy. "
            f"{cite('mashhadi')} uses a Crunchbase firm-quarter panel for 2010 to 2023 with temporal splits and reports ROC-AUC. The datasets, labels and protocols differ, so the numbers below are placed side by side for orientation only."),
          TAB("Reported results of the papers and of this project", ["Work", "Data and protocol", "Reported result", "Note"],
              [["Panjwani et al. [1]", "Crunchbase / Kaggle data, size not stated; 70:30; ADASYN", "Accuracy 85 to 92 % for the best ensembles", "No table, no ROC-AUC; not reproducible from the paper"],
               ["Maarouf et al. [2]", "4,034 Crunchbase start-ups, 35.15 % successful; 5 x 80/20; text and structured data", "Balanced accuracy: kNN-ICL (k = 50) 0.713, Logistic Regression 0.631, Random Forest 0.634, XGBoost 0.618; fused LLM trained on 20,172 start-ups 0.743", "Needs an LLM; descriptions are available"],
               ["Mashhadi et al. [3]", "Crunchbase panel 2010-2023, temporal splits, SMOTE-NC and inverse weights", "AUROC 0.872 (exit, 36 months, Random Forest), 0.817 (next funding), 0.921 (patents)", "Different target and horizon; temporal validation"],
               ["This project, real table", f"{F.REAL_ROWS} US start-ups, 64.6 % successful; 5 x 80/20; structured only", f"Balanced accuracy 0.746 (RF, XGBoost); ROC-AUC 0.816 (RF); accuracy 0.775 (XGBoost); retrieval-only 0.70 to 0.71", "No dates, no text; four post-hoc fields included"],
               ["This project, real table, base-paper protocol", "70:30 x 5 seeds", f"Random Forest accuracy {F.pm(R['split_70_30']['Random Forest'], 'accuracy')}, Logistic Regression {F.pm(R['split_70_30']['Logistic Regression'], 'accuracy')}", "Closest like-for-like with [1]"],
               ["This project, shipped application", "1,400 synthetic rows, fused features", "Balanced accuracy 0.749 (Logistic Regression)", "Synthetic; text leaks the label"]],
              widths=[1.3, 1.9, 2.1, 1.2], align=["l", "l", "l", "l"], size=8.5),
          FIG(F.fig("f11_vs_base_papers.png"), "Reported figures of the papers and of this project; datasets and protocols differ, so the bars are not comparable one to one.", 5.4),
          P("What can be said: (1) the base paper's qualitative finding, that ensembles beat Logistic Regression, is reproduced on the real table, by 0.06 to 0.08 in accuracy depending on the protocol and the model; (2) its 85 to 92 % level is not reproduced by any real-data run here (best 0.775 on 80/20 and 0.796 on 70:30), "
            "and because the paper does not state its dataset or list its results the gap cannot be explained, though look-ahead fields and a different table are possible reasons; (3) the balanced accuracy of 0.746 is above the 0.62 to 0.63 that the supervised baselines of the method paper reach and just above its retrieval-augmented language model (0.713), but that paper uses a different, text-based and larger dataset and the comparison is only indicative; "
            "(4) the temporal-split study reaches higher AUROC for patents but a similar level for exits (0.87 against 0.82 here), on much larger panel data with a leakage-safe design. This project's contribution lies in the end-to-end application with evidence and drivers, and in the honest benchmark of Sections 8.3.1 to 8.3.11, not in a higher score.")]

    # ------------------------------------------------------------------ 8.5
    b += [H2("8.5 Sample input and output"),
          P("One real submission was used for the screens. The inputs below are those of the filled form in Section 8.2.3."),
          TAB("Sample input", ["Field", "Value"],
              [["Industry, state", "Software, CA"], ["Total funding, rounds", "USD 2,500,000 across 2 rounds"], ["Age at first / last funding (years)", "1.5 / 2.5"],
               ["Age at first / last milestone (years)", "1 / 2"], ["Relationships, milestones, average participants", "6, 3, 3"], ["Investor flags", "Has VC, Round A"],
               ["Comparable cases k", "50"], ["Description", "A subscription analytics platform for small retailers using demand forecasting, with 40 paying stores and growing monthly revenue. (130 characters)"]],
              widths=[2.6, 3.9], align=["l", "l"], size=9.5),
          TAB("Sample output (JSON fields of `POST /predict`, as shown on the result screen)", ["Field", "Value"],
              [["outcome", "SUCCESS"], ["probability_success / probability_failure", "0.83 / 0.17"], ["confidence", "0.833 (83.3 %)"], ["model", "Logistic Regression"], ["risk", "Lower risk"],
               ["similar_counts", "25 SUCCESS, 25 FAILURE (k = 50)"], ["explanation", "has_roundC (0.00): weight 2.495, supports FAILURE; funding_rounds (-0.07): 2.401, supports FAILURE; relationships (0.72): 2.380, supports SUCCESS; has_VC (1.00): 2.348, supports SUCCESS; milestones (0.58): 2.243, supports SUCCESS; retrieval statistics (top similarity 0.580; mean similarity to SUCCESS 0.492, to FAILURE 0.456)"]],
              widths=[2.2, 4.3], align=["l", "l"], size=9),
          TAB("The five most similar historical start-ups returned for this input (from the result screen)", ["Similarity", "Outcome", "Industry", "State", "Funding", "Rounds"],
              [["0.580", "SUCCESS", "Software", "CO", "USD 1.07 M", "1"], ["0.553", "SUCCESS", "Software", "CA", "USD 4.06 M", "4"], ["0.537", "FAILURE", "Media", "FL", "USD 862 K", "1"],
               ["0.534", "SUCCESS", "Software", "CA", "USD 1.34 M", "0"], ["0.530", "FAILURE", "Software", "CA", "USD 1.29 M", "0"]],
              widths=[0.9, 1.0, 1.1, 0.7, 1.3, 0.8], align=["c"] * 6, size=9.5),
          P("Two properties of this output are worth noting. First, the evidence split is 25 / 25 by construction, because retrieval draws half of the cases from each class; the split itself says nothing about the likely outcome, and the informative statistics are the similarities (0.492 to SUCCESS cases against 0.456 to FAILURE cases, a small margin). "
            "Second, the explanation ranks features by the size of the coefficient, not by its contribution for this input: a flag that is absent (has_roundC = 0) is listed first and labelled as supporting FAILURE, although its contribution is zero. The retrieved start-ups and the estimate agree here, but the list of drivers is a description of the model, not of this case.")]

    # ------------------------------------------------------------------ 8.6
    b += [H2("8.6 Success and failure analysis"),
          H3("8.6.1 Where the system works"),
          B("It ranks start-ups usefully: ROC-AUC 0.82 for Random Forest and 0.79 for Logistic Regression on the real table, and the observed success rate rises from 8 % to 93 % across the probability bins of Section 8.3.6.",
            "It finds most of the successes with the ensemble models (recall 0.84 to 0.88) at precision about 0.82.",
            "The whole path, from the form to the explained result, takes about 0.15 to 0.2 s at the median on a CPU-only PC (Chapter 7), and comparable start-ups give a second, independent view of the estimate that matches a linear model in accuracy.",
            "Success and failure rates of the larger industry groups are predicted well: on one test split Media is right for 31 of 35 start-ups (0.89) and Software for 77 of 106 (0.73)."),
          H3("8.6.2 Where it fails"),
          TAB("Random Forest accuracy by industry, one test split (seed 42, 185 start-ups)", ["Industry", "Start-ups", "Share successful", "Accuracy"], industry_rows(), widths=[1.6, 1.2, 1.6, 1.2], align=["l", "c", "c", "c"], size=9.5),
          B("Failures are the harder class for the ensembles: only 66 % of the closed start-ups are recognised by Random Forest (42.6 of 65 per fold), so about one verdict in five that says SUCCESS is wrong (precision 0.82).",
            "Small segments are unreliable: Biotech (6 start-ups, accuracy 0.33) and CleanTech (6, 0.50) are too few to read, and the model has seen only a few of them.",
            "Without the four post-hoc fields the ensembles drop to balanced accuracy 0.64 to 0.68, so genuinely early-stage predictions are weaker than the headline numbers.",
            "The displayed confidence is conservative on the real table (Section 8.3.6): a score of 0.25 corresponds to a 44 % success rate.",
            "The explanation lists features by coefficient size, not by contribution, and an absent flag can appear as a driver (Section 8.5).",
            "Founder experience, team size and market conditions, named in the abstract, are not in either dataset and cannot influence any estimate.")]

    # ------------------------------------------------------------------ 8.7
    b += [H2("8.7 Limitations of the results"),
          B("The application serves a model trained on synthetic data; its dashboard scores (balanced accuracy 0.749) are not real-world performance.",
            f"The real table has {F.REAL_ROWS} start-ups, one country, a 185-row test fold and a single family of random splits; the standard deviations over splits understate the true uncertainty and no significance test was run.",
            "No temporal split is possible, so look-ahead bias cannot be excluded; Section 8.3.8 shows that it matters.",
            "The text channel and the fused representation could not be evaluated on real data; the synthetic text leaks the label.",
            "Base-paper figures cannot be compared like for like because the declared paper states neither its dataset nor its per-model results.",
            "HistGradientBoosting appears only in the study, not in the application; ROC-AUC was not recorded for the shipped fused model; no SHAP analysis was made."),
          P("The 29 edge cases and 51 automated checks of Chapter 7 show that the software behaves as specified; they say nothing about whether the estimates are right. The latency of 148 to 199 ms per prediction (median) was measured with a warm model on one machine.")]

    # ------------------------------------------------------------------ 8.8
    b += [H2("8.8 Objectives against outcomes"),
          TAB("Objectives of the project and what was achieved", ["#", "Objective", "Outcome", "Status"],
              [["1", "Collect a startup dataset covering funding history, team background, sector, location and outcome", f"The public table ({F.REAL_ROWS} start-ups) was obtained and analysed; the application ships a synthetic fallback with the same schema. Team background and market data are not in either dataset", "Partly met"],
               ["2", "Clean the data and engineer features capturing funding velocity, team experience and market context", "Cleaning, imputation, scaling, one-hot coding and log funding done; funding velocity only approximated by the ages at first and last funding and the number of rounds; no team-experience or market feature exists", "Partly met"],
               ["3", "Address class imbalance between successful and failed startups", "Balanced class weights in the application; oversampling compared on real data (Section 8.3.3). On the real table failure, not success, is the minority and neither correction improves ROC-AUC", "Met"],
               ["4", "Train and compare Logistic Regression, Decision Tree, Random Forest and boosting ensembles", "All four plus HistGradientBoosting compared with 5 x 80/20 and 5 x 70:30 splits (Sections 8.3.1 and 8.3.2)", "Met"],
               ["5", "Identify the features that most strongly separate successful from failed startups", "Three rankings (Section 8.3.7): relationships, milestones and funding stand out; four fields may be recorded after the outcome (Section 8.3.8)", "Met, with a caveat"],
               ["6", "Evaluate using accuracy, precision, recall, F1-score and ROC-AUC", "All five measured on the real table; the shipped fused model's own evaluation records balanced accuracy, accuracy, precision, recall and F1 but not ROC-AUC", "Met"]],
              widths=[0.35, 2.3, 3.0, 0.85], align=["c", "l", "l", "c"], size=9),
          P("In summary, the system is built and works end to end, the ensemble ranking of the base paper is reproduced on a real table, and the benchmark shows how much of the real-data score depends on fields that may not be available early. "
            "The application's estimates should be read as a transparent, evidence-backed screening aid and not as a prediction that has been validated on future start-ups.")]
    return b
