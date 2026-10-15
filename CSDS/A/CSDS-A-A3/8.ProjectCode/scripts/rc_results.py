"""Chapter 8 sections (Results and Output Screens) and the screen catalogue shared with Appendix C."""
from __future__ import annotations

from doc_common import CHARTS, CV, DEMO, LAT, M, R, SHOTS, T, V2, X, RF, LR, p

# (file, caption, what it shows, width in inches, max height)
SCREENS = [
    ("01_landing.png", "Landing page", "The public front page: product name, the line \"Machine learning + crowdsourced threat intelligence\", a paste-a-link box, and a live badge showing the active model (XGBoost, F1 92.9 %, ROC-AUC 0.981) read from the API.", 4.9, 3.8),
    ("02_check_home.png", "Check URL: home", "The checking workspace after the demonstration run: single and batch tabs, example URLs to try, and below the form the counters (URLs checked, confirmed phishing URLs, community reports, F1 of the active model) and the recent checks table.", 4.9, 3.8),
    ("03_check_phishing.png", "Check URL: phishing verdict", "A phishing URL (http://secure-paypal-login.account-verify.tk/signin?user=a) is checked. The verdict is Phishing, decided by the ML model, with a 99.9 % probability gauge, the risk scale marked at 35 % and 60 %, and buttons to report the URL.", 4.9, 3.8),
    ("04_check_safe.png", "Check URL: safe verdict", "A reputable page (wikipedia.org/wiki/Phishing) is scored 0.1 % and shown as Looks safe, with no red flags.", 4.9, 3.8),
    ("05_check_community_override.png", "Check URL: community overrides the model", "A lookalike document-share URL that the model scores at 9.5 % (raw model score) is shown as Phishing at 97.0 %, decided by the community, after two reports. This is the zero-day behaviour of the system.", 4.9, 3.8),
    ("06_check_false_positive_corrected.png", "Check URL: false positive corrected", "docs.python.org was flagged by the model (raw score 60.1 %). After two safe reports the verdict is Looks safe, decided by the community, with the explanation \"Confirmed legitimate by community consensus\".", 4.9, 3.8),
    ("03b_check_phishing_full.png", "Check URL: full result page", "The complete result page for the phishing URL: red flags (three), the community-intelligence panel, and the table of the 47 extracted features grouped by lexical, structural and domain.", 3.4, 6.0),
    ("07_batch_results.png", "Batch check of ten URLs", "Ten pasted URLs are checked in one run (5 phishing, 5 safe). The table shows each verdict, probability and decided-by; the last row is decided by the community. A toast reports \"Checked 10 URLs - 5 flagged as phishing\".", 3.4, 6.0),
    ("08_report_form.png", "Report a URL", "The report form for http://sbi-netbanking-kyc-update.top/login.php: the three steps, the phishing or safe choice, reporter and note fields, the live community status (2 phishing, 0 safe, net +2, confirmed), the latest reports, and the consensus rules.", 4.9, 3.8),
    ("09_intel.png", "Threat intelligence board", "Counters (10 URLs tracked, 5 confirmed phishing, 2 confirmed safe, 3 pending; 7 awaiting training) and the table of entries with status, phishing and safe votes, source and age.", 4.9, 3.8),
    ("10_intel_detail.png", "Threat-intelligence entry", "The detail drawer of the document-share URL: status confirmed phishing, 2 phishing and 0 safe votes, source, first seen, not yet used in training, and the report history with reporter names and notes.", 4.9, 3.8),
    ("11_models.png", "Models: comparison (version 1)", "The shipped models: XGBoost selected (F1 92.88 %, ROC-AUC 0.981, false-positive rate 6.38 %), trained on 32,000 and tested on 8,000 URLs.", 4.9, 3.8),
    ("12_models_full.png", "Models: full page (version 1)", "Held-out metrics as bars and radar, the comparison table (XGBoost 92.93 %, Random Forest 92.49 %, Logistic Regression 82.81 % accuracy), the XGBoost confusion matrix (3,745 / 255 / 311 / 3,689) and its top-10 feature importances, and the retrain control.", 3.4, 6.0),
    ("13_activity.png", "Activity", "The check log: 56 checks, 36 flagged phishing, average probability 64.6 %, 10 decided by the community; a probability-per-check trend with the two thresholds dashed, and the verdict mix.", 4.9, 3.8),
    ("14_activity_full.png", "Activity: full page", "The same page scrolled to the searchable table of every check with verdict, probability, decided-by and time.", 3.4, 6.0),
    ("15_intel_sync_dialog.png", "Feed sync: dialog", "The dialog explains that URLs from OpenPhish and URLhaus are imported as trusted reports and confirmed as phishing at once.", 4.9, 3.8),
    ("16_intel_sync_result.png", "Feed sync: result", "The sync finished: openphish +300 URLs, urlhaus +500 URLs, 800 in total.", 4.9, 3.8),
    ("17_intel_after_sync.png", "Threat intelligence after sync", "The board now tracks 810 URLs, 805 of them confirmed phishing; the newest entries come from the feed.", 4.9, 3.8),
    ("18_retrain_confirm.png", "Retrain: confirmation", "Before retraining, the Models page asks for confirmation and states that the best model by F1 replaces the current one and checks keep working.", 4.9, 3.8),
    ("19_retrain_running.png", "Retrain: running", "While the retrain runs in the background the page shows a progress indicator and the topbar a Retraining badge.", 4.9, 3.8),
    ("20_models_after_retrain.png", "Models: after retraining (version 2)", "Version 2: trained on 33,953 rows including 807 community-confirmed URLs weighted x3, tested on 8,162; XGBoost F1 92.99 %. The topbar now reads XGBoost v2.", 4.9, 3.8),
    ("21_models_after_retrain_full.png", "Models: full page (version 2)", "Version 2 in full: XGBoost 92.91 % accuracy, confusion matrix 3,740 / 261 / 318 / 3,843, and 203.8 s training time recorded for that run.", 3.4, 6.0),
    ("22_intel_after_retrain.png", "Threat intelligence after retraining", "After the retrain, 0 entries are awaiting training: every confirmed URL has been consumed. The list shows real URLhaus entries.", 4.9, 3.8),
    ("23_check_dark.png", "Dark theme", "The same Check URL page in the dark theme.", 4.9, 3.8),
]
MAIN = ["01_landing.png", "03_check_phishing.png", "04_check_safe.png", "05_check_community_override.png", "06_check_false_positive_corrected.png",
        "07_batch_results.png", "08_report_form.png", "09_intel.png", "12_models_full.png", "20_models_after_retrain.png"]


def screens_by_files(files):
    byname = {s[0]: s for s in SCREENS}
    return [byname[f] for f in files]


def screens(d, files):
    for f, cap, desc, w, h in screens_by_files(files):
        d.figure(SHOTS / f, cap, width=w, max_h=h)
        d.p(desc)


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("All screens are real captures of the running application at 1440 x 900 pixels, taken by script after loading real usage into it: a scenario of 42 checks, "
        "19 community reports, a feed sync of 800 real URLs from OpenPhish and URLhaus, and a retrain from the interface. None is a mock-up.")
    if all_screens:
        screens(d, [s[0] for s in SCREENS])
    else:
        screens(d, MAIN)


def sec_model_results(d):
    d.h2("Model Performance")
    d.p("All figures in this section come from `models/metrics.json` (the shipped run), re-checked by `scripts/measure_results.py`, which re-scored the saved "
        "models on the same split and found exact agreement. The test set is 8,000 URLs (4,000 phishing, 4,000 legitimate) that no model saw in training.")
    rows = [["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "FPR", "Train (s)"]]
    for n, m in (("XGBoost (selected)", X), ("Random Forest", RF), ("Logistic Regression", LR)):
        rows.append([n, p(m["accuracy"]), p(m["precision"]), p(m["recall"]), p(m["f1"]), f"{m['roc_auc']:.4f}", p(m["false_positive_rate"]), str(m["train_seconds"])])
    d.table(rows, "Held-out test results of the three classifiers", widths=[0.2, 0.12, 0.12, 0.1, 0.1, 0.12, 0.1, 0.14], font=9)
    d.figure(CHARTS / "model_comparison.png", "Comparison of the three classifiers on five metrics", width=5.4)
    d.p("XGBoost is the best on every metric except recall, where Random Forest is higher by 0.02 points (92.25 % against 92.23 %). Logistic Regression misses about "
        "23 % of phishing URLs (recall 77.2 %), so a linear boundary is not adequate. The top two models differ by 0.4 points of accuracy.")
    d.h3("Confusion matrices")
    d.figure(CHARTS / "confusion_matrices.png", "Confusion matrices on the 8,000 test URLs", width=5.8)
    d.p("For XGBoost, 3,745 legitimate URLs were correctly passed and 255 wrongly flagged (a false-positive rate of 6.38 %); 3,689 phishing URLs "
        "were caught and 311 missed (a false-negative rate of 7.8 %). The error is balanced between the two kinds.")
    d.h3("ROC curves")
    d.figure(CHARTS / "roc_curves.png", "ROC curves of the three models", width=3.8)
    d.h3("Cross-validation")
    d.p("The same models were evaluated with 5-fold stratified cross-validation over all 40,000 URLs, the protocol used in the base paper [1].")
    rows = [["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]]
    for n, k in (("XGBoost", "xgboost"), ("Random Forest", "random_forest"), ("Logistic Regression", "logistic_regression")):
        c = CV[k]
        rows.append([n] + [f"{c[m]['mean'] * 100:.2f} +- {c[m]['std'] * 100:.2f}" for m in ("accuracy", "precision", "recall", "f1")] + [f"{c['roc_auc']['mean']:.4f} +- {c['roc_auc']['std']:.4f}"])
    d.table(rows, "5-fold cross-validation (mean +- standard deviation, %)", widths=[0.2, 0.17, 0.17, 0.17, 0.15, 0.14], font=9)
    d.figure(CHARTS / "cross_validation.png", "F1 of each fold and the mean, per model", width=4.4)
    d.p("The standard deviation of XGBoost's F1 across folds is 0.18 points, so the held-out result is not a lucky split; the cross-validated F1 "
        f"({p(CV['xgboost']['f1']['mean'])}) is slightly lower than the held-out F1 ({p(X['f1'])}).")


def sec_model_analysis(d):
    d.h2("Threshold, Feature and Data Analysis")
    d.h3("Choice of threshold")
    d.p("The detector uses 0.60 for phishing and 0.35 for suspicious. The sweep below shows the trade-off for XGBoost: a lower threshold finds more phishing "
        "at the cost of more false alarms.")
    rows = [["Threshold", "Precision", "Recall", "F1", "FPR", "False positives", "False negatives"]]
    for t in R["thresholds"]:
        rows.append([f"{t['threshold']:.2f}", p(t["precision"]), p(t["recall"]), p(t["f1"]), p(t["fpr"]), str(t["fp"]), str(t["fn"])])
    d.table(rows, "XGBoost on the 8,000 test URLs at different probability thresholds", widths=[0.12, 0.15, 0.15, 0.14, 0.12, 0.16, 0.16], font=9)
    d.figure(CHARTS / "threshold_sweep.png", "Precision, recall and F1 against the threshold", width=4.8)
    b = R["verdict_bands"]
    d.p(f"F1 is highest between 0.40 and 0.50 (92.9 %). The deployed three-band scheme with the reputation discount gives: of 4,000 phishing URLs, "
        f"{b['phishing_urls']['phishing']:,} are called phishing, {b['phishing_urls']['suspicious']} suspicious and {b['phishing_urls']['safe']} safe; of 4,000 legitimate URLs, "
        f"{b['legitimate_urls']['safe']:,} are safe, {b['legitimate_urls']['suspicious']} suspicious and {b['legitimate_urls']['phishing']} phishing. "
        f"Counting only \"phishing\" as a positive gives precision {p(b['phishing_only_as_positive']['precision'])} and recall {p(b['phishing_only_as_positive']['recall'])}; "
        f"counting suspicious as well gives precision {p(b['suspicious_as_positive']['precision'])} and recall {p(b['suspicious_as_positive']['recall'])}. "
        "The suspicious band therefore trades a few false alarms for 187 phishing URLs that would otherwise be reported safe.")
    d.figure(CHARTS / "verdict_bands.png", "Deployed verdicts on the test set", width=4.8)
    d.h3("Which features matter")
    d.figure(CHARTS / "feature_importance.png", "Top-10 feature importances of the XGBoost model", width=4.7)
    d.p("The most important features are is_common_tld (0.195), is_popular_domain (0.165) and suspicious_word_count (0.121), followed by "
        "brand_outside_domain, has_executable_extension and is_suspicious_tld. Two of the top three are domain-reputation signals, so an ablation was run.")
    rows = [["Features used", "Count", "Accuracy", "F1", "ROC-AUC"]]
    for k, v in R["ablation"].items():
        rows.append([k, str(v["n_features"]), p(v["accuracy"]), p(v["f1"]), f"{v['roc_auc']:.4f}"])
    d.table(rows, "Feature ablation (XGBoost refitted, threshold 0.5)", widths=[0.36, 0.1, 0.18, 0.18, 0.18], font=9)
    d.figure(CHARTS / "feature_ablation.png", "F1 of XGBoost with different feature subsets", width=4.9)
    d.p("Lexical features alone reach F1 89.2 %; structural features alone are weak (66.0 %); domain features alone reach 77.7 %. Adding domain to lexical "
        "features gives 92.4 %, close to the full 92.8 %. Removing both of the two dominant features costs only 0.2 points, so the model is not relying on "
        "them alone. The refitted \"all 47\" model differs from the saved one by 0.1 point of accuracy because of run-to-run variation in XGBoost.")
    d.h3("Learning curve")
    d.figure(CHARTS / "learning_curve.png", "XGBoost F1 and accuracy against the amount of training data", width=4.7)
    d.p("F1 rises from 89.5 % with 3,200 training URLs to 93.2 % with 32,000, and is still rising slowly at the end. More data would likely help; "
        "the 32,000-row point differs from the shipped model (92.88 %) by about 0.3 points because the rows were permuted for this experiment.")


def sec_product_results(d):
    d.h2("Crowdsourcing and Retraining Results")
    d.h3("Zero-day override and false-positive correction")
    rows = [["URL", "Before reports", "After reports"]]
    before = {x["url"]: x for x in DEMO["before"]}
    after = {x["url"]: x for x in DEMO["after"]}
    for u in ("https://docs-share.cloudhost-files.com/drive/view?id=44", "http://sbi-netbanking-kyc-update.top/login.php",
              "https://docs.python.org/3/library/urllib.html", "https://www.amazon.in/gp/cart/view.html"):
        b, a = before[u], after[u]
        rows.append([u, f"{b['verdict']} ({b['probability']:.3f}, {b['decided_by']})", f"{a['verdict']} ({a['probability']:.3f}, {a['decided_by']})"])
    d.table(rows, "Verdict before and after two community reports (demonstration run)", widths=[0.46, 0.27, 0.27], font=9)
    d.p("The lookalike document-share page is scored safe by the model (0.095) and becomes phishing at once after two reports; the two legitimate pages that "
        "the model flagged become safe after two safe reports each. In both directions the change takes effect on the next check, without retraining. "
        "The other four phishing lures in the run were already caught by the model, so the reports confirmed rather than changed them.")
    d.h3("Feed synchronisation and retraining (version 1 to 2)")
    d.p("Synchronising the two public feeds added 800 URLs (OpenPhish 300, URLhaus 500) as trusted reports, giving 810 tracked URLs of which 805 were confirmed "
        "phishing. A retrain from the Models page then used the base 40,000 rows plus 807 confirmed URLs, repeated three times in the training portion, "
        "producing model version 2.")
    rows = [["Model", "v1 F1 (8,000 test)", "v2 F1 (8,162 test)", "v1 accuracy", "v2 accuracy"]]
    for n, k in (("XGBoost", "xgboost"), ("Random Forest", "random_forest"), ("Logistic Regression", "logistic_regression")):
        rows.append([n, p(M["models"][k]["f1"]), p(V2["models"][k]["f1"]), p(M["models"][k]["accuracy"]), p(V2["models"][k]["accuracy"])])
    d.table(rows, "Model metrics before and after the retraining demonstration", widths=[0.24, 0.19, 0.19, 0.19, 0.19], font=9)
    d.figure(CHARTS / "retrain_versions.png", "F1 before and after retraining (note the different test sets)", width=4.6)
    d.p("The two versions were tested on different test sets (the split is recomputed on 40,807 rows, and the added URLs are mostly phishing), so the difference "
        "of about 0.1 points for XGBoost is not a measured improvement. What the run does show is that the loop works end to end: reports and feed URLs "
        "become training data, a new version is trained, the detector loads it, and the interface shows version 2 and zero entries awaiting training. "
        "XGBoost took 203.8 s in that run against 2.7 s in the original run; the run was concurrent with a browser polling the page and is not a clean timing.")
    d.h3("Does retraining improve the model? A controlled experiment")
    d.p("To measure the effect of crowd data on unseen URLs, 250 to 2,000 correctly labelled test URLs were added to the training data (repeated three times) and "
        "the model was scored on the remaining test URLs, averaged over three random draws.")
    rows = [["Confirmed URLs added", "Held-out URLs", "F1 before", "F1 after", "Missed before", "Missed after"]]
    for c in R["crowd"]:
        rows.append([f"{c['confirmed_urls']:,}", f"{c['heldout_urls']:,}", p(c["f1_before"]), p(c["f1_after"]), f"{c['missed_before']:.1f}", f"{c['missed_after']:.1f}"])
    d.table(rows, "Effect of adding confirmed URLs to training (mean of 3 draws)", widths=[0.2, 0.15, 0.15, 0.15, 0.17, 0.18], font=9)
    d.figure(CHARTS / "crowd_experiment.png", "F1 before and after adding confirmed URLs", width=4.6)
    d.p("The change is within +-0.1 point at every size (standard deviation of the paired difference 0.02 to 0.11 points). Adding random, correctly "
        "labelled URLs from the same distribution does not change the average score, which is what one would expect when the model has already seen 32,000 similar "
        "examples. The value of the loop here is the immediate override and the reversal of known mistakes. Whether retraining helps against a genuinely new "
        "campaign could not be tested with a static dataset, and is stated as an open question.")
    d.h3("Response time")
    d.p(f"A check through the API takes {LAT['api_check_ms_mean']:.1f} ms on average (p95 {LAT['api_check_ms_p95']:.1f} ms); extraction of the 47 features takes "
        f"{LAT['feature_extraction_ms_per_url']:.3f} ms per URL.")


def sec_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("The comparison below must be read with care: the base paper and this project differ in data, features and model, so the numbers are not a "
        "head-to-head benchmark.")
    d.table([["Item", "Base paper [1]", "PhishGuard"],
             ["Dataset", "PhiUSIIL, 235,804 URLs (classes balanced by undersampling)", "Sample of a public set, 40,000 URLs (balanced)"],
             ["Features", "34 URL and page-content features after selection", "47 offline URL features"],
             ["Model", "LSTM + attention + dense hybrid network", f"XGBoost (best of three); RF and LR compared"],
             ["Test accuracy", "99.80 %", p(X["accuracy"])],
             ["F1", "0.9988", f"{X['f1']:.4f}"],
             ["Cross-validation", "5-fold (mean reported)", f"5-fold: accuracy {p(CV['xgboost']['accuracy']['mean'])}, F1 {p(CV['xgboost']['f1']['mean'])}"],
             ["Time per URL", "about 0.20 ms (model inference)", f"{LAT['single_url_score_ms']:.2f} ms (extraction + model, single URL); {LAT['api_check_ms_mean']:.1f} ms through the API"],
             ["Crowd loop", "Designed; evaluated by a learning-curve simulation", "Built and run end to end on real feed data; effect on average accuracy not measurable"],
             ["Explainability", "Not provided", "Red flags and reason with each verdict"]],
            "PhishGuard against the base paper (different datasets and conditions)", widths=[0.2, 0.4, 0.4], font=9.5)
    d.p("The base paper's accuracy is 6.9 points higher than this project's. Three differences probably explain much of the gap, but none was isolated "
        "experimentally: the base paper's dataset is about six times larger, its features include page content that this project deliberately does not "
        "compute, and its model is a deep network. This project does not claim to match or surpass the base paper's accuracy.")


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    rows = [["URL", "Verdict", "Probability", "Correct?"]]
    truth = {"https://docs.python.org/3/library/urllib.html": "No (false positive)", "https://www.amazon.in/gp/cart/view.html": "No (false positive)"}
    for s in R["samples"]:
        verdict = s["verdict"]
        ok = truth.get(s["url"], "Yes")
        rows.append([s["url"], verdict, f"{s['probability']:.4f}", ok])
    d.table(rows, "Verdicts of the live detector on a hand-written set of 14 URLs (empty community store)", widths=[0.55, 0.13, 0.15, 0.17], font=8.5)
    d.p("The eight phishing-style URLs are all caught, and four of the six legitimate URLs are passed. The two errors are discussed in the next section. "
        "The phishing-style URLs were written for this report, imitating common lure patterns; they are not live sites.")


def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("Where the system succeeds")
    d.bullets(["URLs with an IP host, an '@' symbol, an abused TLD, brand names in sub-domains or several credential words are scored above 0.99.",
               "Well-known domains with common TLDs are scored near zero (wikipedia 0.001, stackoverflow 0.002, github 0.021).",
               "Known mistakes can be fixed in one step by two safe reports; new lures can be blocked by two phishing reports.",
               "The system degrades gracefully: malformed input never crashes it."])
    d.h3("Where it fails")
    e = R["errors"]
    d.p(f"On the 8,000 test URLs XGBoost makes {e['fp_total']} false positives and {e['fn_total']} false negatives. Looking at the most confident errors shows what the "
        "features cannot see.")
    rows = [["Kind", "URL (truncated)", "Model probability"]]
    for x in e["false_positives"][:5]:
        rows.append(["False positive", x["url"], f"{x['p']:.3f}"])
    for x in e["false_negatives"][:5]:
        rows.append(["False negative", x["url"], f"{x['p']:.3f}"])
    d.table(rows, "The most confident errors of the XGBoost model on the test set", widths=[0.17, 0.65, 0.18], font=8.5)
    d.bullets(["**False negatives look like ordinary pages**: a blog post on a blogging platform, a form-sharing page, a PDF on a research site. A phishing page hosted on a "
               "legitimate service has no suspicious URL features at all; only page content or reports can catch it.",
               "**False positives look like unusual pages on small sites**: personal profile pages, long identifiers and query strings, unfamiliar TLDs such as .info.",
               "**Reputation list gaps**: docs.python.org (0.601) and amazon.in (0.787) are flagged because the popular-domain list lacks python and applies no discount to the two-letter country TLD.",
               "**Host-wide override**: a confirmed phishing URL on a shared host marks every URL on that host as phishing, which would wrongly block a hosting service."])


def sec_results_limits(d):
    d.h2("Limitations of the Results")
    d.bullets(["The dataset is a 40,000-URL sample from one source; results may not transfer to live traffic or to other datasets.",
               "The test set is part of the same dataset as the training set; no time-based split was possible because the data has no dates.",
               "No hyper-parameter tuning was done, so the model comparison reflects default-like settings.",
               "The retraining effect on new campaigns, and the behaviour with many dishonest reporters, were not measured.",
               "Latency was measured in process, without network or browser overhead; load tests were not run.",
               "The v1 and v2 metrics come from different test sets and cannot be compared directly."])


def sec_objectives(d):
    d.h2("Objectives against Outcomes")
    d.table([["No.", "Objective", "Outcome", "Evidence", "Status"],
             ["1", "Collect and preprocess a URL dataset", "40,000 balanced URLs cleaned and split 80/20", "Chapter 6; data/urls_sample.csv", "Achieved (sample size modest)"],
             ["2", "Extract lexical, structural and domain features", "47 offline features in three groups with red flags", "Chapter 6; 18 unit checks", "Achieved"],
             ["3", "Train and compare RF, XGBoost and LR", f"XGBoost best: F1 {p(X['f1'])}, AUC {X['roc_auc']:.3f}; 5-fold CV F1 {p(CV['xgboost']['f1']['mean'])}", "Tables in this chapter", "Achieved"],
             ["4", "Integrate crowdsourced threat intelligence", "Vote consensus, trusted feeds, community-first decision; zero-day override shown", "Section on crowdsourcing", "Achieved (no administrator verification)"],
             ["5", "Refine the model continuously", "Retrain from the interface or after 25 confirmations; hot reload; v1 to v2 run", "Section on retraining", "Achieved as a mechanism; benefit on new campaigns not measured"],
             ["6", "Real-time classification through a web interface", f"React UI and Flask API; mean check {LAT['api_check_ms_mean']:.1f} ms", "Output screens", "Achieved (no sign-in)"]],
            "Objectives measured against outcomes", widths=[0.06, 0.22, 0.3, 0.2, 0.22], font=9)
