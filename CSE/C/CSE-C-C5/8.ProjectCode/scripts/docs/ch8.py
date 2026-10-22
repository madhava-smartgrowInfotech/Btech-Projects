"""Chapter 8: Results and Output Screens (also document 14)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB
from .lit import OBJECTIVES

ORDER = ["logreg", "tree", "rf", "svm", "knn", "xgb", "xgb_calibrated", "hybrid_xgb_knn", "hybrid_xgb_svm", "hybrid_knn_labelfree", "hybrid_knn_serving"]


def screen(name, caption, base=5.0, max_h=3.0):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def pair(a, ca, b_, cb, w=3.0):
    return ("pair", [(F.shot(a), ca), (F.shot(b_), cb)], w)


def screens_blocks():
    """Every working screen with real data (light-theme landing page included)."""
    return [
        H2("8.2 Output screens"),
        P("All screens below are real captures (1440 x 900) of the application running on the development PC with the trained models loaded and the 3,000-student dataset in `data/`. The data are synthetic "
          "(Chapter 4 and Chapter 6), so every student row, probability and chart describes the generated campus, not a real one. `scripts/capture_screens.py` enters the values shown and presses the buttons, so each result is a live answer of the API."),
        H3("8.2.1 Landing page"),
        pair("01_landing_dark.png", "Landing page, dark theme: headline, terminal status panel and counters strip.",
             "01_landing_light.png", "Landing page, light theme (same content)."),
        P("The page announces the system (\"Predict the placement. Recommend the next offer.\") and names the base paper (arXiv:2603.29881). The terminal panel prints what the API reports: the models `xgb_calibrated`, `knn_residual` and "
          "`preprocess` are ready, the dataset has 3,000 students (59.7 % placed, average CGPA 7.83), 30 companies are loaded across three tiers, and `hybrid_xgb_knn` scores AUC 0.8968, F1 0.8710 and recall 0.9067 on the test set. "
          "These are the figures of the paper rule that uses the true labels (Section 8.5); the page does not say so."),
        H3("8.2.2 Placement eligibility"),
        screen("02_predict.png", "Eligibility screen: Microsoft, SDE, CGPA 8.4, aptitude 84, technical 79, one internship, three projects give 22.2 % and NEEDS IMPROVEMENT.", base=4.6, max_h=2.8),
        P("The form on the left holds the student profile; the panel on the right shows the result. At Microsoft (Tier 1, 24.0 LPA, Hyderabad, hiring rate 15 %) the estimated probability is **22.2 %**, labelled NEEDS IMPROVEMENT. "
          "The cutoff panel shows CGPA 8.4 against 8.2 and aptitude 84 against 82 passing and technical 79 against 82 failing; the model also applies the strong Tier-1 penalty built into the data. The tip \"Strengthen DSA + core subjects; build 2+ projects\" comes from the technical shortfall."),
        H3("8.2.3 Company-role recommendations"),
        screen("03_recommend.png", "Recommendation screen: base probability 10.8 % (Google, SDE), average gain +78.8 pt, match rate 100 %, top pick ValueLabs QA Engineer 89.9 %.", base=4.6, max_h=2.8),
        P("For a student with CGPA 7.5, aptitude 65 and technical 65 targeting Google as an SDE, the base probability is 10.8 %. The tiles show the base probability, the average gain over improved alternatives (+78.8 percentage points), the match "
          "rate (100 %) and the top pick; the chart pairs each of the five hybrid picks with the base. The tabs show the hybrid list (5 items), the company-only list (5) and the role-only list (0). Every pick is a Tier-3 company (ValueLabs, Infosys), a property of the algorithm discussed in Section 8.13."),
        H3("8.2.4 Officer dashboard"),
        pair("04_dashboard.png", "Officer dashboard: counters, model comparison chart, placed rate by branch.",
             "05_dashboard_shap.png", "Dashboard SHAP tab: mean absolute SHAP value of all 24 features."),
        P("The tiles show 3,000 students, a placed rate of 59.7 % (average CGPA 7.83), the hybrid AUC of 0.8968 with accuracy 84.0 %, and the 9-fold cross-validation accuracy of 0.8147 with Brier score 0.1352 and residual rate 22.9 %. "
          "The grouped bars compare ROC-AUC and F1 of the nine shipped models; the placed rate by branch is between 58 % and 61 % because the generator gives branches almost the same chance. The model table marks Logistic Regression as best by AUC (0.9106). "
          "The SHAP tab ranks CGPA_Gap, Backlogs, Tech_Gap, Apt_Gap and CGPA_x_Tier first; other tabs show the PCA scatter and the probability histogram."),
        H3("8.2.5 Recruiter shortlist and companies board"),
        pair("06_recruiter.png", "Recruiter screen: CGPA >= 7.5, aptitude >= 65, all branches; 1,394 matches, top 50 shown.",
             "07_companies.png", "Companies screen: 30 companies with tier, type, cutoffs, package, location, hiring rate (page 1 of 3)."),
        P("The recruiter sets a minimum CGPA, a minimum aptitude score and a branch; the API returns the number of matches (1,394) and the top 50 by CGPA then technical score, each with the company and role targeted and the historical PLACED or NOT PLACED tag, "
          "and an Export CSV button. It is a database-style filter and does not use the model. The companies board lists every company the model knows, searchable by name, city or type and filterable by tier; the cutoffs and packages are invented values that resemble real campus recruiters (Chapter 4)."),
        H3("8.2.6 Command palette and activity log"),
        pair("08_command_palette.png", "Command palette opened with the slash key and the query \"hyd\".",
             "09_activity_log.png", "Activity log drawer: UI events and API calls with status and latency."),
        P("The palette searches the company list from any screen. The activity log records the real calls of the session (`GET /meta 200 19 ms`, `GET /companies 200 36 ms`, `GET /stats 200 61 ms`), which confirms that the screens are driven by the API."),
    ]


def _rows_models():
    return [F.model_row(n) for n in ORDER]


def blocks():
    R, C, S42 = F.R, F.CONF, F.EXP["seed42"]
    x, xc, hk, hl, hs = R["xgb"], R["xgb_calibrated"], R["hybrid_xgb_knn"], R["hybrid_knn_labelfree"], R["hybrid_knn_serving"]
    rs = F.RES
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    b += [H2("8.1 Experimental setup and protocol"),
          P(f"All figures in this chapter come from `models/metrics.json` (the shipped models), `docs/experiments/experiments.json` (written by `scripts/run_experiments.py`) and `docs/experiments/tests.json`, on "
            f"{F.ENV['cpu']} with {F.ENV['ram']} RAM and no GPU (Python {F.ENV['python']}, scikit-learn {F.ENV['sklearn']}, XGBoost {F.ENV['xgboost']}). The headline protocol is the **held-out test split**: of the 3,000 synthetic students, "
            f"15 % (**{F.TEST_N} students**) were set aside by a stratified split with seed 42 and were not used to fit the models or the encoders; the models were fitted on {F.TRAIN_N:,} students and {F.VAL_N} were held for validation. "
            "We loaded the shipped model files and re-evaluated them on the same split: the results reproduce `metrics.json` exactly. A fresh retrain with the installed library versions differs by at most 0.011 in any metric "
            "and takes about three seconds."),
          P("**What this protocol does and does not show.** The students, the companies and the placement labels are synthetic. The label of each student is drawn from a logistic function of the CGPA, aptitude and "
            "technical gaps against the target company's cutoffs, internships, projects, certifications, backlogs and tier, plus noise. Models can therefore recover the rule that generated the data, and a linear model does "
            "very well. The numbers show how well each algorithm learns this generated rule; they do not show how well it would predict real placements, which was not measured. Every number below states its protocol."),
          P("**Key finding in one paragraph.** The hybrid XGBoost + kNN model reaches 0.8400 accuracy against 0.8067 for calibrated XGBoost, but only because the residual set that it refines is chosen with the true test labels "
            f"(the rule of the base paper [2]). A rule that can run at serving time, using only the probability band 0.4 to 0.6, scores {hl['accuracy']:.4f}, which is {hl['accuracy'] - xc['accuracy']:+.4f} against XGBoost, "
            f"one student of {F.TEST_N}. Logistic Regression has the best ROC-AUC ({R['logreg']['roc_auc']:.4f}), and over five random splits the leading label-free models differ by less than one standard deviation.")]
    b += screens_blocks()

    b += [H2("8.3 Model performance"),
          P("The table gives all models on the 450 test students (seed 42). The first nine rows are the contents of `models/metrics.json`; the last two rows evaluate the hybrid under rules that do not use the labels."),
          TAB("Test-set metrics, seed 42 (n = 450)", ["Model", "Accuracy", "ROC-AUC", "F1", "Precision", "Recall"], _rows_models(),
              widths=[2.5, 0.8, 0.8, 0.7, 0.9, 0.7], align=["l", "c", "c", "c", "c", "c"], size=9.5),
          FIG(F.fig("model_comparison.png"), "Accuracy, F1 and ROC-AUC of the models on the held-out test set (seed 42).", 5.0),
          P(f"The Decision Tree is clearly the weakest ({R['tree']['accuracy']:.4f}). The other classifiers lie within about three points of each other: Random Forest {R['rf']['accuracy']:.4f}, kNN {R['knn']['accuracy']:.4f}, XGBoost {x['accuracy']:.4f}, "
            f"SVM and Logistic Regression {R['svm']['accuracy']:.4f}. Logistic Regression ties the SVM for accuracy and leads every model on ROC-AUC ({R['logreg']['roc_auc']:.4f}); this is the expected result when the labels come "
            "from a logistic score. Other measures: the 9-fold cross-validation accuracy of XGBoost on the training split is "
            f"{F.CV9:.4f}; the Brier score of the calibrated XGBoost is {F.BRIER:.4f}; the paper-rule residual set contains {F.RESIDUAL_RATE * 100:.2f} % of the test rows (103 of 450)."),
          H3("8.3.1 Probability and PCA views"),
          ("pair", [(F.static("prob_hist.png"), "Histogram of predicted placement probabilities on the test set."), (F.static("pca.png"), "PCA of the test set: correct placed, correct not placed, misclassified.")], 3.1),
          P("The histogram is bimodal, with most students near 0 or near 1 and a thin middle: the borderline band 0.4 to 0.6 holds only 31 of the 450 students (6.9 %). In the PCA view the misclassified students lie along the "
            "boundary between the two classes, not in a separate cluster, as the base paper also observed for its data.")]

    cm = lambda k: [str(C[k]["tn"]), str(C[k]["fp"]), str(C[k]["fn"]), str(C[k]["tp"])]
    b += [H2("8.4 Confusion matrices"),
          TAB("Confusion matrices on the test set (seed 42; rows are the truth, 0 = not placed, 1 = placed)", ["Model", "TN", "FP", "FN", "TP"],
              [["XGBoost + Platt"] + cm("xgb_calibrated"), ["Hybrid, paper rule (true labels used)"] + cm("hybrid_oracle"), ["Hybrid, label-free (borderline band only)"] + cm("hybrid_labelfree"),
               ["Hybrid, serving rule"] + cm("hybrid_serving"), ["Logistic Regression"] + cm("logreg")],
              widths=[3.4, 0.7, 0.7, 0.7, 0.7], align=["l", "c", "c", "c", "c"], size=10),
          FIG(F.fig("confusion_matrices.png"), "Confusion matrices of calibrated XGBoost, the hybrid with the paper rule, and the hybrid with the serving rule.", 5.0),
          P(f"Calibrated XGBoost makes {C['xgb_calibrated']['fp']} false positives (students predicted placed who were not) and {C['xgb_calibrated']['fn']} false negatives. The paper-rule hybrid removes 14 false negatives and one false positive; "
            f"the label-free and serving versions change the counts by only a few students ({C['hybrid_serving']['fp']} false positives and {C['hybrid_serving']['fn']} false negatives for the serving rule). For a placement cell, "
            "a false negative (a student wrongly told they are not ready) hides an opportunity, and a false positive gives false comfort; the threshold analysis below shows how to trade one for the other.")]

    b += [H2("8.5 The hybrid model: what the gain really is"),
          P("The hybrid takes the predictions of calibrated XGBoost and replaces those of a *residual set* R by the predictions of a local model. The base paper [2] defines R as the rows that XGBoost misclassifies **or** whose "
            "probability lies in [0.4, 0.6] (its Equation 1). The first condition needs the true label, so the rule can be evaluated on a test set but cannot be applied to a new student. `src/hybrid_model.py` follows the paper, and "
            "`models/metrics.json`, the dashboard and the landing page report that version."),
          TAB("Why the paper rule cannot be used at serving time (seed 42)", ["Quantity", "Value"],
              [["Test students", str(rs["n_test"])], ["Students XGBoost classifies wrongly", f"{rs['xgb_errors']}"], ["... of which inside the 0.4 to 0.6 band", f"{rs['xgb_errors_inside_band']}"],
               ["Students inside the band (all)", f"{rs['borderline_only']}"], ["Residual set of the paper rule", f"{rs['oracle_residual']}  (87 + 31 - 15)"],
               ["kNN accuracy on the paper-rule residual set", f"{rs['knn_acc_on_oracle'] * 100:.1f} %  (XGBoost: {rs['xgb_acc_on_oracle'] * 100:.1f} %)"],
               ["kNN accuracy on the band rows only", f"{rs['knn_acc_on_borderline'] * 100:.1f} %  (XGBoost: {rs['xgb_acc_on_borderline'] * 100:.1f} %)"]],
              widths=[3.6, 3.0], align=["l", "l"], size=10),
          P(f"Of the 103 residual rows, 72 are in the set only because XGBoost got them wrong, and a local model that is asked to re-decide rows that are known to be wrong will do better than chance simply because the "
            "global model's answer is excluded. kNN is right on 30.1 % of the 103 rows against 15.5 % for XGBoost, but on the 31 rows that a deployed system could actually select the two are close (54.8 % against 51.6 %). "
            f"The hybrid's accuracy therefore falls from {hk['accuracy']:.4f} (labels used) to **{hl['accuracy']:.4f}** (label-free) and {hs['accuracy']:.4f} (the serving rule of `src/recommend.py`: 0.5 p + 0.5 p_kNN inside the band), "
            f"against {xc['accuracy']:.4f} for calibrated XGBoost: a difference of one student."),
          TAB("Effect of the width of the borderline band (kNN label replaces the XGBoost label; seed 42)", ["Band", "Rows replaced", "Accuracy", "F1", "ROC-AUC"],
              [[("none (p >= 0.5)" if r["lo"] == r["hi"] else f"{r['lo']:.2f} to {r['hi']:.2f}" + (" (served)" if (r['lo'], r['hi']) == (0.4, 0.6) else "")), str(r["replaced"]), f"{r['accuracy']:.4f}", f"{r['f1']:.4f}", f"{r['roc_auc']:.4f}"] for r in F.BAND],
              widths=[2.0, 1.2, 1.0, 1.0, 1.0], align=["l", "c", "c", "c", "c"], size=10),
          P("Widening the band from 0 to 133 replaced rows changes accuracy by at most 0.7 percentage points (0.8022 to 0.8089) and moves ROC-AUC by under 0.01. On this data the local model adds no measurable value. "
            "The base paper's accuracy of 0.8723 for its hybrid is built on the same label-driven definition; we did not re-derive its data, so we cannot say how much of it would remain."),
          FIG(F.fig("threshold_sweep.png"), "Precision, recall, F1 and accuracy of calibrated XGBoost as the decision threshold moves from 0.30 to 0.70.", 3.8)]

    b += [H2("8.6 Decision-threshold analysis"),
          P("The threshold sweep figure at the end of Section 8.5 shows the sweep from 0.30 to 0.70. Accuracy is flat between 0.793 and 0.807 for every threshold, so the threshold does not change how often the system is right. It changes the kind of error: raising the threshold from 0.30 to 0.70 "
            "raises precision from 0.776 to 0.869 and lowers recall from 0.918 to 0.791. A placement cell that wants to avoid missing students who could be placed should lower the threshold (0.35 gives recall 0.899 "
            "with precision 0.798, F1 0.846); a cell that wants a short, reliable list of ready students should raise it. The served threshold of 0.5 is a reasonable middle and is not tuned.")]

    cal = F.CAL
    b += [H2("8.7 Calibration"),
          P(f"Platt scaling [4] was applied to XGBoost with three-fold cross-validation. The Brier score [8] improves from {cal['brier_raw_xgb']:.4f} (raw) to {cal['brier_platt']:.4f} (calibrated), a gain of about 2 %; Logistic Regression, "
            f"whose probabilities are calibrated by construction, scores {cal['brier_logreg']:.4f}, better than both. The mean predicted probability on the test set is {cal['mean_prob_test']:.4f} against an observed placed fraction of "
            f"{cal['base_rate_test']:.4f}. The base paper reports a Brier score of 0.1864 for Platt scaling [2]; the data differ, so the two numbers are not comparable. Calibration matters because the recommendation module ranks "
            "alternatives by probability and the user interface shows the probability as a percentage."),
          FIG(F.fig("calibration.png"), "Reliability diagram of raw and Platt-calibrated XGBoost on the test set.", 3.4)]

    b += [H2("8.8 Stability over five random splits"),
          P("To see whether the ranking of models depends on one lucky split, the whole pipeline was retrained in memory on five stratified splits (seeds 42, 1, 2, 3 and 4), each with 450 test students. The seed-42 retrain differs "
            "from the shipped model by at most 0.011. Values are mean ± standard deviation."),
          TAB("Five-seed study (test accuracy, F1, ROC-AUC)", ["Model", "Accuracy", "F1", "ROC-AUC"],
              [[F.MODEL_LABELS[n], F.ms(n), F.ms(n, "f1"), F.ms(n, "roc_auc")] for n in ORDER],
              widths=[2.7, 1.3, 1.3, 1.3], align=["l", "c", "c", "c"], size=9.5),
          FIG(F.fig("multi_seed.png"), "Test accuracy of four models on each of the five random splits.", 3.8),
          P(f"Four results follow. First, the split-to-split standard deviation is 1.2 to 2.2 points, larger than the gaps between Logistic Regression ({F.ms('logreg')}), SVM, XGBoost ({F.ms('xgb')}), XGBoost + Platt "
            f"({F.ms('xgb_calibrated')}) and the label-free hybrids ({F.ms('hybrid_knn_labelfree')}, {F.ms('hybrid_knn_serving')}); these cannot be ranked reliably. Second, the paper-rule hybrid ({F.ms('hybrid_xgb_knn')}) is ahead in all five seeds, "
            "by 1 to 3 points over calibrated XGBoost, which is what the label dependence predicts. Third, the label-free hybrid is equal to or lower than XGBoost + Platt in four of five seeds and the means differ by 0.0004. "
            f"Fourth, Logistic Regression has the best mean ROC-AUC ({F.ms('logreg', 'roc_auc')}) and the Decision Tree remains clearly last ({F.ms('tree')}). The shipped numbers of Section 8.3 are one draw from this spread.")]

    b += [H2("8.9 Explainability: which features matter"),
          TAB("Mean absolute SHAP value of the eight most influential features (XGBoost, 450 test students)", ["Rank", "Feature", "Mean |SHAP|"],
              [[str(i), s["feature"], f"{s['mean_abs_shap']:.4f}"] for i, s in enumerate(F.SHAP[:8], 1)],
              widths=[0.7, 3.4, 1.4], align=["c", "l", "c"], size=10),
          FIG(F.fig("shap_top10.png"), "Mean absolute SHAP value of the ten most influential features (retrained XGBoost, test set).", 3.8),
          P("The three gap features (CGPA, technical and aptitude score against the target company's cutoff), the number of backlogs and the CGPA x tier interaction dominate; the raw scores, internships, projects and "
            "communication matter much less. This agrees with the dashboard's SHAP chart of the shipped model (Figure in Section 8.2.4), which ranks the same five features first. It is also exactly how the synthetic labels "
            "were generated, so it confirms that the model learned the generator and says nothing about what drives real placements. The engineered gap features are the main useful idea of the feature set: they turn a company-independent "
            "score into a company-specific distance from the cutoff.")]

    r = F.REC
    b += [H2("8.10 Recommendation results"),
          P(f"The recommendation module was run for {r['students']} test students whom the model rates below 0.5 for their own target company. Table values are model-estimated probabilities; they were not checked against real "
            "placements, so they measure how the module redistributes the *model's* probability, not how many students would be placed."),
          TAB("Recommendation results for 60 students rated below 0.5 for their own target", ["Quantity", "Value"],
              [["Mean base probability (own target)", f"{r['mean_base_prob']:.4f}"], ["Students with at least one better alternative in the top 5", f"{r['with_at_least_one_better_alt']} of {r['students']} ({r['with_at_least_one_better_alt'] / r['students'] * 100:.1f} %)"],
               ["Mean probability of the top-1 alternative", f"{r['mean_top1_prob']:.4f}"], ["Mean average gain over the improved alternatives", f"{r['mean_avg_gain_over_improved']:.4f} (43.7 percentage points)"],
               ["Students whose top-1 alternative reaches 0.5", f"{r['top1_reaches_ready']} of {r['students']} (65 %)"],
               ["Time per recommendation (in process)", f"mean {r['recommend_latency_s']['mean']:.2f} s, p95 {r['recommend_latency_s']['p95']:.2f} s, max {r['recommend_latency_s']['max']:.2f} s"]],
              widths=[3.6, 3.0], align=["l", "l"], size=10),
          FIG(F.fig("reco_gain.png"), "Estimated gain (top-1 alternative minus original target) for the 60 students.", 3.6),
          P("Most students gain a large estimated probability, because a student who is far below a Tier-1 cutoff has a probability near 0.1 there and a probability near 0.9 at an easy Tier-3 company. The base paper reports "
            "a mean increase of 65.1 % over all rejected applicants and 0.704 for its hybrid strategy [2]; the definitions and data differ, so the comparison is indicative only. Two features of the module matter in practice: "
            "(i) it ranks by probability and so prefers easy companies; (ii) it takes several seconds, as the latency row shows.")]

    b += [H2("8.11 Comparison with the base papers"),
          P("Two papers are involved. The batch document names the IJETMS paper [1] as the base paper; the code and README are built on the hybrid framework of [2]. The comparison below is stated plainly: **the data, the "
            "task and the evaluation differ, so no accuracy figure can be called better or worse than a published one.**"),
          TAB("Comparison with the base papers", ["Aspect", "IJETMS placement paper [1]", "Hybrid admission paper [2]", "This project"],
              [["Task", "Placement prediction", "Admission prediction and university-program recommendation", "Placement prediction and company-role recommendation"],
               ["Data", "Synthetic, size not stated", "13,000 real GradCafe records, 2021-2025", "3,000 synthetic students; 30 invented companies"],
               ["Split", "80:20", "70/15/15 (9,100 / 1,950 / 1,950)", "70/15/15 (2,100 / 450 / 450)"],
               ["Models", "Logistic Regression, Random Forest, Gradient Boosting", "7 baselines; XGBoost + kNN / SVM hybrid", "6 baselines; calibrated XGBoost; kNN / SVM hybrids"],
               ["XGBoost accuracy", "not reported", "0.7241", f"{x['accuracy']:.4f}"],
               ["Hybrid accuracy", "no hybrid", "0.8723 (XGB + kNN)", f"{hk['accuracy']:.4f} with labels; {hl['accuracy']:.4f} label-free"],
               ["Brier score (Platt)", "not reported", "0.1864", f"{F.BRIER:.4f}"],
               ["Explainability", "Feature importance, skill-gap analysis", "SHAP", "SHAP ranking and rule-based tips"],
               ["Recommendation", "None", "University, program, hybrid; +65.1 % mean gain", "Company, role, hybrid; mean gain 43.7 points (60 students)"],
               ["Interface", "Streamlit; batch CSV, PDF, e-mail", "None", "Flask, FastAPI and React; recruiter shortlist; no CSV batch, PDF or e-mail"]],
              widths=[1.1, 1.7, 1.9, 1.9], align=["l", "l", "l", "l"], size=9),
          P("The IJETMS paper contains no accuracy, F1 or AUC value in its results section (it states only the 80:20 split and the three models), so there is nothing numeric to compare with. The accuracies of [2] come from "
            "noisy real data in which Logistic Regression reaches only 0.69; ours come from generated data in which it reaches 0.83. That is the main reason our baselines are higher, and it does not indicate a better method. "
            "What this project adds to [1] is a company-recommendation module and a dashboard; what it takes from [2] is the framework, with the label dependence of the residual rule made explicit.")]

    b += [H2("8.12 Sample inputs and outputs"),
          TAB("Sample requests and responses (real API output)", ["Request", "Output"],
              [["POST /api/predict: CGPA 8.4, aptitude 82, technical 84, communication 75, DSA 80, 3 projects, 1 internship, 2 certifications, 0 backlogs, CSE; Infosys, SDE", "probability 0.9032; PLACEMENT READY"],
               ["POST /api/predict: CGPA 6.2, aptitude 50, technical 45, no internship; Google", "probability 0.1212; NEEDS IMPROVEMENT; tips on CGPA below the 8.5 cutoff, aptitude, DSA and an internship"],
               ["POST /api/predict: CGPA 8.4, aptitude 84, technical 79, 1 internship, 3 projects; Microsoft, SDE (screenshot)", "probability 0.222; NEEDS IMPROVEMENT; technical 79 below cutoff 82"],
               ["POST /api/recommend: CGPA 7.2, aptitude 65, technical 65, target Google SDE, location Hyderabad", "base 0.1085; average gain 0.7833; 5 hybrid options; role-only list empty"],
               ["POST /api/recruiter/shortlist: CGPA >= 8.5, aptitude >= 70, CSE", "138 matches; the 50 with the highest CGPA returned"],
               ["POST /api/predict with CGPA 14", "HTTP 422 (validation error)"]],
              widths=[3.6, 3.0], align=["l", "l"], size=9.5)]

    b += [H2("8.13 Success and failure analysis"),
          H3("8.13.1 What works"),
          B("The prediction path is fast (median 56 ms over HTTP) and behaves in the expected direction: probability rises with CGPA and falls with backlogs and with a higher company tier.",
            "Probabilities are reasonably calibrated (mean 0.592 against 0.596 observed), so the percentages shown to a student are not misleading *for this data*.",
            "All 46 behaviour checks and the 15-check smoke test pass; invalid input is refused with clear status codes."),
          H3("8.13.2 What does not work, or is weaker than it looks"),
          B("**The headline hybrid gain is not deployable.** It needs the true label of the student whose probability is being estimated (Section 8.5).",
            "**The recommender steers weak profiles to the easiest companies.** The score is the probability, so Tier-3 companies win for any student below a Tier-1 cutoff; package and role fit are ignored. The screenshot shows five Tier-3 picks.",
            "**The role-only list can be empty** when the target company is outside the feasibility window; the user sees an empty tab with no explanation.",
            "**Unknown branches and roles are accepted**, and **recommendation takes seconds** because each candidate reloads four model files (Chapter 7).",
            "**Skill-gap tips are fixed rules** (below the CGPA, aptitude or technical cutoff; no internship). SHAP is computed for the whole test set, not for the student, so the tip is not an individual explanation of the probability.",
            "**A strong profile is still rated low at Tier 1.** CGPA 8.4 at Microsoft gives 22 %: the tier penalty is a property of the generator and cannot be checked against real hiring."),
          H3("8.13.3 Where the model is most and least certain"),
          P("Only 6.9 % of test students lie in the 0.4 to 0.6 band, and the model is right on about half of them (51.6 %). Errors outside the band (72 of the 87) are confident mistakes that no borderline rule can reach; "
            "they come from the noise (standard deviation 0.8) added to the generating score, which no model can predict.")]

    b += [H2("8.14 Limitations of the results"),
          B("The data are synthetic, so no accuracy figure is a claim about real campus placements.",
            "The labels follow a logistic rule, which favours Logistic Regression and the gap features.",
            "The test set has 450 students; one student is 0.22 percentage points, so most differences between models are not significant.",
            "The five-seed study re-splits the same 3,000 students; it measures sensitivity to the split, not to new data.",
            "The recommendation gains are model-estimated, never verified against outcomes, and the module's latency was measured over 60 students and 8 HTTP calls.",
            "The comparison with the base papers is qualitative because the datasets differ.")]

    rows = [[str(i), o, s, e] for i, (o, s, e) in enumerate(zip(OBJECTIVES, [
        "Partly met", "Partly met", "Met", "Met", "Met in part", "Met"], [
        "3,000 synthetic records and 30 companies were generated; no real placement records exist.",
        "Frequency encoding, standardisation and six engineered features are done; classes are 59.7 % / 40.3 % and no resampling was applied.",
        "Six baselines, calibrated XGBoost and two hybrids were trained and compared on one split and over five splits.",
        "A hybrid top-5 recommendation with company-only and role-only lists; gains are model-estimated only.",
        "Rule-based tips from the cutoffs and a global SHAP ranking; no per-student explanation.",
        "Officer dashboard and recruiter shortlist work; accuracy, precision, recall, F1, ROC-AUC and Brier are reported."]), 1)]
    b += [H2("8.15 Objectives versus outcomes"),
          TAB("Objectives of the batch against what was achieved", ["No.", "Objective", "Status", "Evidence"],
              [[r_[0], r_[1], r_[2], r_[3]] for r_ in rows],
              widths=[0.4, 2.5, 0.8, 2.9], align=["c", "l", "c", "l"], size=9.5),
          P("Not implemented although described in the batch documents: MySQL storage, logins for students, recruiters and officers, PDF and e-mail reports, batch prediction from a CSV file, matching against job-description "
            "requirement vectors, and any real placement data.")]
    return b
