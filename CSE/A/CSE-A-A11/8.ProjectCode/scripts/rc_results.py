"""Chapter 8 content: output screens, model and product results, comparison, samples, failures, limits, objectives.

Every number is taken from doc_common (autosecai/artifacts/report.json, docs/measured_facts.json,
docs/measured_api_latency.json) or from a run of the shipped code on 18 October 2026.
"""
from __future__ import annotations

from doc_common import (API, BEST, CHARTS, DEMO, EV, LAT, MODELS, REP, RET, SEEDS, SHOTS, SIZE, f3,
                        RULE_ENTRIES, RULES_SECURITY, SMOKE_CHECKS, TESTS_API, TESTS_ENGINE, UI_FLOWS)

S = SEEDS["summary"]


def ms(model: str, metric: str) -> str:
    v = S[f"{model}|{metric}"]
    return f"{v['mean']:.3f} +/- {v['sd']:.3f}"


# ------------------------------------------------------------------ the 26 real screenshots
MAIN_SCREENS = [
    ("04_overview.png", "Overview page",
     "The page after signing in as Demo Reviewer: the heading \"Autonomous pull-request security review\", cards for PR review, Codebase assistant and Model lab, and the strip \"How the agents work together\" with the seven numbered agents from Ingestion to Judge."),
    ("05_review_new_demo.png", "New review: Demo PR input",
     "The five input modes (Demo PR, Paste diff, Compare versions, GitHub PR link, Upload files / repo), the sample \"Vulnerable Flask API (diff)\" with a preview of the diff of `app/users.py`, the setting chips (ML risk agent on, min severity info, LLM explanations off) and the run button."),
    ("26_review_verdict.png", "Review result: verdict, gauge and key figures",
     "The red banner \"Merge blocked\" (\"risk score 99/100 ... 15 security finding(s) ... 1 critical, 10 high, 4 medium\"), the gauge at 99, and the tiles 15 security findings, 11 merge blockers, 2 quality issues and 7 (7) verified auto-fixes; tabs Findings 17, Function risk 7, Files 1."),
    ("07_review_findings.png", "Findings tab with the first finding opened",
     "\"Secret-like token committed\" (CRITICAL, CWE-798, `app/users.py:13`) expanded: chips (high confidence, OWASP A07:2021, AST/taint), the quoted line, What is wrong, Impact, How to fix and Safe pattern. On the right, the severity donut (17 findings) and the CWE bar chart; the filters include \"Only changed lines\"."),
    ("08_review_function_risk.png", "Function risk (ML) tab",
     "The seven changed functions ranked by risk (login, import_data, find_user, ping, hello 1.00; fetch 0.96; download 0.89) with predicted type and top drivers. \"Inspect a function\" shows login: radar chart, probability 100% and drivers M12 = 2, M14 = 2, M8 = 2 against safe values 0.0, 0.0, 0.3."),
    ("10_review_agent_trace.png", "Agent trace tab",
     "The audit trail of the seven agents: static analysis \"16 security and 2 quality findings\" (0.011 s); ML Risk \"7 changed function(s) scored; 7 predicted vulnerable\" (0.321 s); Reasoner \"12 corroborated by ML\"; Remediation \"7/7 verified by re-scan\" (0.059 s); Judge \"17 unique findings after de-duplication\"."),
    ("11_review_export.png", "Export tab",
     "The PR comment preview (\"Blocked - security issues must be fixed\", risk 99/100, Critical/High/Medium 1/10/4, a table of findings), the downloads PR comment (.md), SARIF 2.1, Full JSON and Findings CSV, and the card stating \"No whole-file fixes\" because the input was a diff."),
    ("12_codebase_ask.png", "Codebase assistant: question and cited answer",
     "After the toast \"Indexed 10 files, 24 code units\", the question \"Where is the authentication mechanism implemented?\" is answered with `app/auth.py` (`login`, line 25; `hash_password`, line 13) and `tests/test_auth.py` (line 4), followed by four evidence rows."),
    ("13_codebase_map.png", "Codebase assistant: repository map",
     "Tiles for Files 10, Lines 132, Functions 14, Classes 1 and Import links 8; the table of API routes (POST /auth/login at `app/auth.py:25`, GET /api/orders at `app/routes.py:11`, and more); and the start of the module dependency graph."),
    ("17_lab_models.png", "Model Lab: nine models",
     "The key figures (6,000 functions; 501 vulnerable; XGBoost F1 0.851, accuracy 0.977; type accuracy 0.65), the data note that the paper used C functions while this system uses a generated Python corpus, and grouped bars of accuracy, precision, recall and F1 for the nine models."),
    ("18_lab_roc_confusion.png", "Model Lab: ROC curves and confusion matrix",
     "ROC curves of the nine models with AUC in the legend (0.90 for Decision Tree to 0.96 for the Voting Ensemble) and the XGBoost confusion matrix: 1369 safe correctly passed, 6 false alarms, 28 vulnerable functions missed, 97 found."),
    ("21_lab_try_it.png", "Model Lab: Try it",
     "A pasted function, `get_user(name)`, that builds its query with an f-string, and the button \"Analyse function\"; the result lies below the visible area. The model gives probability 0.006 while the static rule SQLI fires at line 3 (see the sample outputs)."),
    ("22_history.png", "History",
     "Five saved reviews with verdict, risk, security findings and ID: two Block verdicts of 18 October 2026 (risk 81 and 99) and three of 29 September (99, 99, 43), with a delete button per row, a search box and the start of the chart \"Risk score over time\"."),
]

EXTRA_SCREENS = [
    ("03_login.png", "Sign in", "The sign-in card with the \"Use the demo account\" shortcut, the Sign in / Create account switch, the e-mail and password fields and the Sign in button.", None),
    ("06_review_new_paste_diff.png", "New review: Paste diff", "The Paste diff tab: title field, the drop zone for a .diff or .patch file and the text area for a unified diff. The cyan ring is the keyboard focus.", None),
    ("09_review_files.png", "Files tab", "The changed file `app/users.py` (Python, +67 / -1, 17 findings) and the complexity table of its eight functions: cyclomatic complexity 1 each, nesting 1 only for download.", None),
    ("14_codebase_guide.png", "Codebase assistant: onboarding guide", "The generated guide for demo-shop (10 files, about 132 lines, 14 functions): where to start, the files for authentication, routes, UI, database and configuration, the endpoints and the most complex functions (login, cc=3).", None),
    ("15_lab_pipeline.png", "Model Lab: pipeline and data", "The seven pipeline steps and the chart \"Training set size\" (4500 original, 8232 after SmoteTomek; 16 Tomek links removed), under the tiles for 6,000 functions, 501 vulnerable (8.3 %), XGBoost F1 0.851 and accuracy 0.977.", None),
    ("16_lab_feature_selection.png", "Model Lab: feature selection", "The importance heat table for the seven selection methods and the chart \"Validation F1 vs. number of metrics kept\", rising from about 0.57 at k = 5 to 0.79 at k = 13 (best) and 0.77 at k = 14.", None),
    ("19_lab_types.png", "Model Lab: vulnerability types", "F1 per vulnerability type (overall accuracy 0.65) and the metrics that separate the types, led by M12 Risky API calls, M8 I/O & query calls and M13 String-built sinks.", None),
    ("20_lab_ablation.png", "Model Lab: ablation", "Recall / precision / F1 of three Random Forest configurations: all 14 metrics unbalanced 0.776 / 0.933 / 0.847; top-5 with SmoteTomek 0.648 / 0.643 / 0.645; top-13 with SmoteTomek 0.776 / 0.882 / 0.826.", None),
    ("23_settings.png", "Settings", "Switches for the ML risk agent and minimum severity, the optional API key (LLM explanations stay off until a key is added) and GitHub token, the theme (Light, Dark, System) and the account card; settings are saved in this browser only.", None),
    ("24_about.png", "About", "The abstract, the base paper reference and the table \"From paper to product\", which maps each contribution of the paper to where it lives in AutoSecAI and marks the two extensions (explanation with fixes, codebase intelligence).", None),
    ("25_review_light_mode.png", "Review result in light mode", "The verdict screen in the light theme: banner, gauge 99, tiles, tabs, filters, finding list and severity donut; the theme button shows the sun icon.", None),
    ("01_landing_light.png", "Landing page, light theme (full page)", "The public page: headline, a live example finding (SQL injection, CWE-89, \"Patch verified by re-scan\"), the block \"Straight from the trained model report\" (7 agents, 14 metrics, 9 models, 7 selectors, 98% accuracy, 85% F1, 65% type accuracy), the three entry points and the call to action.", 7.4),
    ("02_landing_dark.png", "Landing page, dark theme (full page)", "The same page in the dark theme, the default look of the Aurora Glass interface kit.", 7.4),
]

SCREENS = [(f, c, t) for f, c, t in MAIN_SCREENS] + [(f, c, t) for f, c, t, _ in EXTRA_SCREENS]


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("Every screen below is a real capture of AutoSecAI running with real data on 18 October 2026: the built-in vulnerable pull request was "
        "reviewed through the interface, the demo repository was indexed, and the Model Lab shows the trained report. The captures are 1440 by 900 "
        "pixels unless stated, were taken with a scripted browser (`scripts/capture_screens.py`) and were checked for console errors and failed requests; none "
        "was found. The numbers visible in the screens are the same numbers that appear in the tables of this chapter.")
    if all_screens:
        for f, cap, text in MAIN_SCREENS:
            d.figure(SHOTS / f, cap, width=5.3)
            d.p(text, size=10.5, line=1.3)
        d.h3("Additional screens")
        extra_block(d)
    else:  # the full report: two screens side by side, each pair followed by one short paragraph per screen
        for i in range(0, len(MAIN_SCREENS), 2):
            pair = MAIN_SCREENS[i:i + 2]
            d.figure_pair([(SHOTS / f, cap) for f, cap, _t in pair], width=3.15, max_h=2.1)
            for f, cap, text in pair:
                d.p(f"**{cap}.** {text}", size=10, line=1.2, space_after=2)


def extra_block(d):
    """Additional screens in side-by-side pairs, each pair followed by one line per screen."""
    small = [e for e in EXTRA_SCREENS if e[3] is None]
    tall = [e for e in EXTRA_SCREENS if e[3] is not None]
    for group, width, mh in ((small, 3.15, 2.2), (tall, 2.9, 6.6)):
        for i in range(0, len(group), 2):
            pair = group[i:i + 2]
            d.figure_pair([(SHOTS / f, cap) for f, cap, _t, _m in pair], width=width, max_h=mh)
            for f, cap, text, _m in pair:
                d.p(f"**{cap}.** {text}", size=10.5, line=1.25)


# ------------------------------------------------------------------ model results
def sec_engine_results(d):
    m, rf = MODELS[BEST], MODELS["Random Forest"]
    imp = REP["importance"]
    taint_share = sum(v for k, v in imp.items() if k.split()[0] in ("M12", "M13", "M14"))
    kc = REP["k_scores"]
    d.h2("Model Performance")
    d.p(f"AutoSecAI contains one trained component, the metric model that scores each changed function; the static rules, the agents and the retrieval "
        f"are deterministic code. This section reports the evaluation of that model and of the rule engine. All figures were produced by the shipped "
        f"code (`autosecai/mlmodel.py`, `scripts/measure_facts.py`) on one machine (Intel Core i5-12500, 15.7 GB RAM, no GPU). The corpus is **generated**: "
        f"{REP['n_functions']:,} Python functions, of which {REP['n_vulnerable']} ({REP['class_ratio'] * 100:.2f}%) are vulnerable, split 75 / 25 into "
        f"{REP['train_size']:,} training and {REP['test_size']:,} test functions (125 vulnerable, 1,375 safe). After SMOTE and Tomek-link cleaning the training "
        f"set held {REP['balanced_train_size']:,} rows ({REP['tomek_removed']} Tomek removals); the test set was never balanced. The results therefore describe how well "
        f"the metric model separates the generated vulnerable patterns from the generated safe look-alikes, not how it would perform on real repositories.")
    d.table([["Measure", "Result"],
             [f"Best model by F1 ({BEST}): accuracy / precision / recall", f"**{f3(m['accuracy'])}** / **{f3(m['precision'])}** / **{f3(m['recall'])}**"],
             [f"{BEST}: F1 and area under the ROC curve", f"**{f3(m['f1'])}** and {f3(m['auc'])}"],
             ["Random Forest (the base paper's choice): F1 and AUC", f"{f3(rf['f1'])} and {f3(rf['auc'])}"],
             [f"Metrics kept after validation (best k of 5 to 14)", f"**{REP['best_k']}** of 14 (validation F1 {f3(kc[str(REP['best_k'])])})"],
             ["Vulnerability-type classifier, accuracy / macro F1", f"**{f3(REP['type_accuracy'])}** / {f3(REP['type_report']['macro avg']['f1-score'])} (126 test functions, 8 types)"],
             [f"{BEST} F1 over five independent corpora", f"mean **{ms(BEST, 'f1')}** (minimum {f3(S[BEST + '|f1']['min'])})"],
             ["Rule engine alone, precision / recall / F1", f"{f3(EV['rule_engine']['precision'])} / {f3(EV['rule_engine']['recall'])} / {f3(EV['rule_engine']['f1'])}"],
             ["Rule engine or ML model, F1", f"**{f3(EV['combined_or']['f1'])}** (recall {f3(EV['combined_or']['recall'])})"],
             ["Training time of the full nine-model pipeline", f"{REP['seconds']} s"]],
            "Headline model results (generated Python corpus, 1,500 held-out functions)", widths=[0.58, 0.42], font=10)
    d.h3("Nine classifiers")
    rows = [["Model", "Accuracy", "Precision", "Recall", "F1", "AUC"]] + [
        [n + (" (best F1)" if n == BEST else ""), f3(v["accuracy"]), f3(v["precision"]), f3(v["recall"]), f3(v["f1"]), f3(v["auc"])] for n, v in MODELS.items()]
    d.table(rows, "Nine classifiers on the held-out test set", widths=[0.28, 0.14, 0.14, 0.14, 0.15, 0.15], font=9.5, align=["l"] + ["c"] * 5)
    d.figure(CHARTS / "models_prf.png", "Precision, recall and F1 of the nine classifiers", width=4.6)
    lr, nb = MODELS["Logistic Regression"], MODELS["Naive Bayes"]
    d.p(f"{BEST} gave the best F1 ({f3(m['f1'])}) and the highest precision ({f3(m['precision'])}); it raised six false alarms on 1,375 safe functions. Logistic "
        f"Regression and Naive Bayes found the most vulnerable functions (recall {f3(lr['recall'])} each) but flagged 172 and 175 safe functions, "
        f"so their precision was only {f3(lr['precision'])} and {f3(nb['precision'])}. Random Forest, the winner of the base paper [1], reached F1 {f3(rf['f1'])} and the "
        f"highest AUC of the single models ({f3(rf['auc'])}); the soft-voting ensemble had the highest AUC overall ({f3(MODELS['Voting Ensemble']['auc'])}). The model that "
        f"AutoSecAI stores and uses inside the pull-request pipeline is {BEST}, chosen by F1 on the test set.")
    d.h3("Confusion matrices and ROC curves")
    cm = REP["confusion"]
    d.table([["Model", "True negative", "False positive", "False negative", "True positive"]] +
            [[n, f"{cm[n][0][0]:,}", str(cm[n][0][1]), str(cm[n][1][0]), str(cm[n][1][1])] for n in (BEST, "Random Forest", "Voting Ensemble", "Logistic Regression")],
            "Confusion matrices of four models (rows: truth, 1,375 safe and 125 vulnerable)", widths=[0.28, 0.18, 0.18, 0.18, 0.18], font=9.5, align=["l"] + ["c"] * 4)
    d.figure_pair([(CHARTS / "confusion.png", f"Confusion matrices of {BEST} and Random Forest"), (CHARTS / "roc.png", "ROC curves of the nine classifiers")], width=3.2, max_h=2.9)
    d.p(f"The two best models missed the same number of vulnerable functions (28 of 125) and differ in false alarms: {cm[BEST][0][1]} for {BEST} and "
        f"{cm['Random Forest'][0][1]} for Random Forest. The ROC curves of all nine models rise steeply and lie close together at the top left, which is why the "
        f"AUC values range only from {f3(MODELS['Decision Tree']['auc'])} to {f3(MODELS['Voting Ensemble']['auc'])}; the models differ more in where they place the decision "
        f"threshold than in how well they rank the functions.")
    d.h3("Which metrics drive the score")
    d.table([["Metric", "Random Forest importance"]] + [[k, f3(v)] for k, v in list(imp.items())[:6]],
            "The six most important of the 13 selected metrics", widths=[0.6, 0.4], font=10, align=["l", "c"])
    d.figure_pair([(CHARTS / "importance.png", "Random Forest importance of the 13 selected metrics"), (CHARTS / "k_sweep.png", "Validation F1 against the number of metrics kept")], width=3.2, max_h=2.6)
    d.p(f"The three metrics added by this project to the base paper's families, M12 (risky API calls), M13 (string-built sinks) and M14 (untrusted or sensitive "
        f"sources), carry {taint_share * 100:.1f}% of the total importance, and they were the top three of the seven-method consensus. The base paper "
        f"reports M5, M6, M1, M9 and M11 as the most important metrics for C code [1]; on Python injection patterns the order is different, "
        f"which is expected because the flaws differ (memory errors there, injection here). The feature-count sweep supports the same point: with only "
        f"five metrics (the paper's setting) the validation F1 was {f3(kc['5'])}, with thirteen it was {f3(kc['13'])}, and with all fourteen {f3(kc['14'])}.")
    d.h3("Ablation")
    ab = REP["ablation"]
    d.table([["Configuration (Random Forest)", "Precision", "Recall", "F1"]] + [[k, f3(v["precision"]), f3(v["recall"]), f3(v["f1"])] for k, v in ab.items()],
            "Ablation of balancing and feature count", widths=[0.58, 0.14, 0.14, 0.14], font=10, align=["l", "c", "c", "c"])
    d.figure(CHARTS / "ablation.png", "Ablation: precision, recall and F1 of three Random Forest configurations", width=3.7)
    d.p("The ablation shows two things and hides a third. Keeping only the paper's five metrics was clearly worse (F1 0.645) than keeping thirteen "
        "(0.826). Balancing with SMOTE-Tomek did not raise recall on this corpus (0.776 with and without it); it lowered precision from 0.933 to 0.882. "
        "The two comparisons are confounded, however: the unbalanced baseline uses all fourteen metrics and the balanced system uses thirteen, so the effect "
        "of balancing alone was not isolated, and no single-factor experiment was run. The honest reading is that the extra taint metrics matter and "
        "that balancing was not shown to help here.")
    d.h3("Vulnerability types")
    tr = REP["type_report"]
    d.table([["Type", "Precision", "Recall", "F1", "Test functions"]] + [[k.replace("_", " "), f3(v["precision"]), f3(v["recall"]), f3(v["f1-score"]), str(int(v["support"]))]
                                                                      for k, v in tr.items() if k not in ("macro avg", "weighted avg")],
            f"Vulnerability-type classifier (accuracy {f3(REP['type_accuracy'])})", widths=[0.34, 0.16, 0.16, 0.16, 0.18], font=9.5, align=["l"] + ["c"] * 4)
    d.figure(CHARTS / "type_f1.png", "F1 of the vulnerability-type classifier by type", width=3.7)
    d.p(f"SQL injection ({f3(tr['sql_injection']['f1-score'])}), XSS ({f3(tr['xss']['f1-score'])}), command injection ({f3(tr['command_injection']['f1-score'])}), hard-coded secrets "
        f"({f3(tr['hardcoded_secret']['f1-score'])}) and weak cryptography ({f3(tr['weak_crypto']['f1-score'])}) are separated well; deserialization ({f3(tr['deserialization']['f1-score'])}), "
        f"path traversal ({f3(tr['path_traversal']['f1-score'])}) and code execution ({f3(tr['code_execution']['f1-score'])}) are not, because their metric signatures (one risky "
        f"call fed by one source) overlap with the injection types. This is why the product reports the exact weakness from the static rules and uses "
        f"the model's type only as a hint.")
    d.h3("Stability over five corpora")
    d.table([["Corpus seed", "Vulnerable", "RF F1", "RF precision", "RF recall", "XGB F1", "XGB precision", "XGB recall"]] +
            [[str(r["seed"]), str(r["positives"]), f3(r["Random Forest"]["f1"]), f3(r["Random Forest"]["precision"]), f3(r["Random Forest"]["recall"]),
              f3(r["XGBoost"]["f1"]), f3(r["XGBoost"]["precision"]), f3(r["XGBoost"]["recall"])] for r in SEEDS["runs"]],
            "Models retrained on five independently generated corpora (k fixed at 13)", widths=[0.12, 0.12, 0.11, 0.13, 0.11, 0.11, 0.15, 0.15], font=9, align=["c"] * 8)
    d.figure(CHARTS / "seeds.png", "F1 of XGBoost and Random Forest on five generated corpora", width=3.5)
    d.p(f"The stored report is the first of the five runs (seed 7, reproduced exactly by the study). Across the five corpora XGBoost reached an F1 of {ms('XGBoost', 'f1')} "
        f"and Random Forest {ms('Random Forest', 'f1')}; the headline {f3(m['f1'])} is therefore the best of five, not the typical value, and XGBoost was ahead of Random Forest on every "
        f"corpus. The spread is small relative to the difference between configurations, so the ranking of the models is stable on this generator. The number of "
        f"metrics was not re-selected for each corpus.")
    d.h3("Rule engine and metric model compared")
    d.table([["Detector (1,500 held-out functions)", "Precision", "Recall", "F1", "TP", "FP", "FN"]] +
            [[n, f3(EV[k]["precision"]), f3(EV[k]["recall"]), f3(EV[k]["f1"]), str(EV[k]["tp"]), str(EV[k]["fp"]), str(EV[k]["fn"])]
             for n, k in (("AST/taint rule engine (security, medium or higher)", "rule_engine"), (f"Metric model ({BEST})", "ml_model"),
                          ("Either flags (OR)", "combined_or"), ("Both flag (AND)", "combined_and"))],
            "Rule engine and metric model on the same held-out functions", widths=[0.4, 0.12, 0.1, 0.1, 0.08, 0.08, 0.08], font=9.5, align=["l"] + ["c"] * 6)
    d.figure(CHARTS / "engine_vs_ml.png", "Precision, recall and F1 of the rule engine, the metric model and their combinations", width=4.0)
    d.p(f"On the same 1,500 functions the rule engine (about {EV['rule_engine_seconds_per_function_ms']} ms per function) reached a precision of {f3(EV['rule_engine']['precision'])} and "
        f"a recall of {f3(EV['rule_engine']['recall'])}; the metric model a precision of {f3(EV['ml_model']['precision'])} and a recall of {f3(EV['ml_model']['recall'])}. The two "
        f"detectors miss different functions: flagging a function when either of them does lifts recall to {f3(EV['combined_or']['recall'])} and F1 to **{f3(EV['combined_or']['f1'])}**, "
        f"while requiring both gives a precision of {f3(EV['combined_and']['precision'])} with a recall of {f3(EV['combined_and']['recall'])}. This is the quantitative argument for "
        f"corroboration: the Security Reasoner marks a finding \"corroborated by ML\" when the model also rates the function as vulnerable, and the Judge "
        f"treats such findings as stronger evidence. The caveat is large: the corpus generator and the rules were written by the same team around the same eight "
        f"patterns, so the rule-engine figures are optimistic for real code, and about 1% of the labels are deliberately wrong, so no detector can reach 1.0.")


# ------------------------------------------------------------------ product results
def sec_product_results(d):
    st = DEMO["stats"]
    sev = st["by_severity"]
    pa = LAT["per_agent_median_s"]
    d.h2("Product-Level Results")
    d.h3("The demonstration pull request")
    d.p(f"The built-in pull request adds 67 lines (one line removed) to `app/users.py` and deliberately contains many flaws. The review produced a risk score of "
        f"**{DEMO['score']} / 100** and the verdict **{DEMO['verdict']}**, with {DEMO['findings']} unique findings: {sev['critical']} critical, {sev['high']} high, "
        f"{sev['medium']} medium and {sev['info']} informational; {st['by_category']['security']} are security findings and {st['by_category']['quality']} are quality findings. "
        f"All {st['functions_scored']} changed functions were scored by the metric model and all {st['functions_flagged']} were flagged. Seven auto-patches were generated and "
        f"{st['autofix_verified']} of {st['autofix']} passed the re-scan, that is, the patched source no longer triggers the same rule. Eight security findings "
        f"received no patch (the two hard-coded secrets, the string-concatenated SQL query in `login`, the cross-site scripting return, the path traversal, the pickle load, "
        f"the predictable random token and the request to a user-supplied URL), because the rule engine has a fix template only for the cases it can rewrite safely.")
    d.figure(CHARTS / "demo_severity.png", "Findings of the demonstration pull request by severity", width=3.3)
    d.h3("Review time")
    d.table([["Agent", "Median time"]] + [[k, f"{v * 1000:.1f} ms"] for k, v in pa.items()] + [["**Whole review**", f"**{LAT['median_s'] * 1000:.0f} ms**"]],
            f"Median time per agent over {LAT['runs']} runs of the demonstration review (engine only)", widths=[0.6, 0.4], font=10, align=["l", "c"])
    d.figure(CHARTS / "latency_agents.png", "Median time per agent", width=3.7)
    d.p(f"A whole review took a median of {LAT['median_s'] * 1000:.0f} ms (mean {LAT['mean_s'] * 1000:.0f} ms, fastest {LAT['min_s'] * 1000:.0f} ms, 95th percentile "
        f"{LAT['p95_s'] * 1000:.0f} ms, slowest {LAT['max_s'] * 1000:.0f} ms). The ML Risk Agent accounts for about {100 * pa['ML Risk Agent'] / LAT['median_s']:.0f}% of the time, because "
        f"it computes fourteen metrics and runs the model for every changed function; the Remediation Agent, which re-scans every patched file, accounts for about "
        f"{100 * pa['Remediation Agent'] / LAT['median_s']:.0f}%, and the static analysis needs only {pa['Static Analysis Agent'] * 1000:.0f} ms. The measurements were made on an otherwise idle "
        f"machine; absolute values shift between runs, and no larger pull request was timed.")
    d.h3("HTTP interface")
    rows = [["Endpoint", "Runs", "Median", "95th percentile"]]
    for k, v in API.items():
        if "ms" in v:
            rows.append([k, str(v["n"]), f"{v['ms']} ms (single run)", "-"])
        elif "demo-diff" in k:
            rows.append([k, str(v["n"]), f"{v['median_ms']} ms", f"max {v['max_ms']} ms"])
        else:
            rows.append([k, str(v["n"]), f"{v['median_ms']} ms", f"{v['p95_ms']} ms"])
    d.table(rows, "Latency of the HTTP API on localhost (one client)", widths=[0.5, 0.1, 0.2, 0.2], font=9, align=["l", "c", "c", "c"])
    d.figure(CHARTS / "api_latency.png", "Median latency of the API endpoints (logarithmic axis)", width=4.0)
    d.p(f"Read-only endpoints answered in a few milliseconds. Login took about {API['POST /api/auth/login (bcrypt)']['median_ms']} ms because bcrypt is deliberately slow, and a demonstration "
        f"review submitted as a job and polled every 50 ms was complete after a median of {API['POST /api/reviews demo-diff -> done (polled 50 ms)']['median_ms']:.0f} ms. The web application polls every 350 ms,"
        f"so the user sees each agent's message as it appears. No concurrency or load test was run.")
    d.h3("Codebase assistant")
    d.p(f"The assistant was evaluated on the built-in demo shop ({RET['files']} files) with {RET['questions']} questions written by hand before the run, each with the file that "
        f"should come first. The expected file was ranked first for **{RET['top1']} of {RET['questions']}** questions and within the first three files for **{RET['top3']} of {RET['questions']}**. "
        f"Building the index took {RET['index_build_ms']} ms and answering a question a median of {RET['ask_median_ms']} ms in the engine. This is a small, hand-made check on one tiny repository, not a benchmark.")
    d.table([["Question", "Expected file", "Files returned (first three)", "Rank"]] +
            [[r["question"], r["expected"], ", ".join(r["got"]), str(r["rank"]) if r["rank"] else "not returned"] for r in RET["rows"]],
            "Retrieval check on the demo repository", widths=[0.36, 0.17, 0.35, 0.12], font=8.5, align=["l", "l", "l", "c"])
    d.h3("Automated checks")
    d.table([["Check", "Result"],
             ["Unit and API tests (`pytest tests`)", f"**{TESTS_ENGINE + TESTS_API} passed** ({TESTS_ENGINE} engine tests, {TESTS_API} API tests)"],
             ["API smoke test against the running server", f"**{SMOKE_CHECKS} of {SMOKE_CHECKS}** checks passed"],
             ["Browser flows (scripted, real browser)", f"**{UI_FLOWS} flows passed**, 0 console errors"],
             ["Production build of the web application (type check and bundle)", "Passes"],
             ["Screens captured for this report", f"{len(SCREENS)} screenshots, console clean, no HTTP error responses"],
             ["Horizontal overflow at 360 px and 768 px, light and dark", "None found on any screen"]],
            "Automated checks run on 18 October 2026", widths=[0.58, 0.42], font=10)


# ------------------------------------------------------------------ comparison
def sec_comparison(d):
    m = MODELS[BEST]
    rf = MODELS["Random Forest"]
    d.h2("Comparison with the Base Paper")
    d.p(f"The base paper [1] trains classifiers on 21,759 functions of ten open-source C and C++ projects, of which only 275 (1.26%) are vulnerable, and reports a Random "
        f"Forest with accuracy 0.96, precision 0.948, recall 0.974 and F1 0.961. AutoSecAI reproduces the pipeline on a **generated corpus of Python functions** "
        f"and obtains an F1 of {f3(m['f1'])} for {BEST} and {f3(rf['f1'])} for Random Forest. **The two sets of figures are not comparable.** The language, the origin and "
        f"the class balance of the data, the way the metrics are extracted and the labels (real CVE and NVD records against injected patterns with 1% noise) all "
        f"differ, and the generated corpus was designed together with the rules that are also evaluated here. No claim is made that AutoSecAI is more or less accurate than the paper; "
        f"the figure that is comparable is the structure of the evidence, which the table below sets side by side.")
    d.table([["Aspect", "Base paper [1]", "AutoSecAI"],
             ["Data", "21,759 C/C++ functions, 275 vulnerable, ten real projects", f"{REP['n_functions']:,} generated Python functions, {REP['n_vulnerable']} vulnerable ({REP['class_ratio'] * 100:.2f}%)"],
             ["Metric extraction", "Code property graph from a fuzzy parser; 14 metrics", "Python `ast` and control-flow analogues; 14 metrics, M1-M11 mirror the paper, M12-M14 added"],
             ["Feature selection", "Several methods, top five kept (M5, M6, M1, M9, M11)", f"Seven methods with vote and rank consensus; k validated, {REP['best_k']} kept; top five are {', '.join(x.split()[0] for x in REP['selected_labels'][:5])}"],
             ["Balancing", "SmoteTomek (balanced set of 21,474)", f"Own SMOTE and Tomek-link implementation ({REP['balanced_train_size']:,} rows)"],
             ["Best model", "Random Forest, F1 0.961", f"{BEST}, F1 {f3(m['f1'])} (Random Forest {f3(rf['f1'])}); five-corpus mean {ms(BEST, 'f1')}"],
             ["Use of the model", "Offline classification of functions", "Scores every changed function inside a pull request, corroborates static findings, ranks risk"],
             ["Beyond the model", "None", "Static rules with CWE and OWASP mapping, explanations, verified patches, SARIF export, codebase assistant"],
             ["Weakness types", "Eight types of C vulnerability", f"Eight Python-oriented types (accuracy {f3(REP['type_accuracy'])}); exact CWE from the {RULES_SECURITY} security rules"],
             ["Evidence of real-world accuracy", "Ten real projects", "None: no real or labelled pull requests were available"]],
            "AutoSecAI and the base paper", widths=[0.2, 0.38, 0.42], font=9)
    d.p("The Sphinx study of LLM-driven review [2] addresses the same activity from a different side: it generates review comments with a trained language "
        "model and evaluates them with a checklist-based benchmark. AutoSecAI trains no language model; its findings come from deterministic analysis and the "
        "optional language-model layer only rewrites the text. The two works measure different things (coverage of review points against detection of "
        "vulnerable functions), so only the approach can be compared: Sphinx is a learned reviewer evaluated on comment quality, AutoSecAI an analyser whose "
        "findings carry evidence, a patch and a re-scan. The lesson taken from [2] is the value of an explicit checklist of verification points, which the "
        "Agent trace and the PR comment mirror in a simple form.")


# ------------------------------------------------------------------ samples
def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.p("The first sample is the built-in pull request. A part of its diff is shown below, followed by the findings that the review returned for it, "
        "in the order of severity (the line numbers refer to the new file).")
    d.code('''@app.route("/user")
def find_user():
    name = request.args.get("name")
    cur = get_db().cursor()
    cur.execute(f"SELECT id, email FROM users WHERE name = '{name}'")
    return jsonify(cur.fetchall())

@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    os.system(f"ping -c 1 {host}")
    return "done"

@app.route("/import", methods=["POST"])
def import_data():
    blob = request.data
    obj = pickle.loads(blob)
    cfg = yaml.load(request.form["config"])
    calc = eval(request.args.get("expr"))
    return jsonify(obj=str(obj), cfg=cfg, calc=calc)''', "Excerpt of the demonstration diff (added lines of app/users.py)")
    rows = [["Rule", "Line", "Severity", "CWE", "Finding", "Verified patch"]]
    data = [("GENERIC_SECRET", 13, "critical", "CWE-798", "Secret-like token committed", "no"), ("HARDCODED_SECRET", 12, "high", "CWE-798", "Hard-coded credential / secret", "no"),
            ("SQLI", 24, "high", "CWE-89", "SQL injection (`find_user`)", "yes"), ("WEAK_HASH", 32, "high", "CWE-327", "Weak hash algorithm (md5)", "yes"),
            ("SQLI", 34, "high", "CWE-89", "SQL injection by concatenation (`login`)", "no"), ("CMDI", 42, "high", "CWE-78", "OS command injection (`ping`)", "yes"),
            ("XSS", 49, "high", "CWE-79", "Cross-site scripting (`hello`)", "no"), ("PATH", 55, "high", "CWE-22", "Path traversal (`download`)", "no"),
            ("DESER", 62, "high", "CWE-502", "Unsafe deserialization (pickle)", "no"), ("YAML_LOAD", 63, "high", "CWE-502", "yaml.load without SafeLoader", "yes"),
            ("EVAL", 64, "high", "CWE-95", "Dynamic code evaluation (eval)", "yes"), ("WEAK_RANDOM", 35, "medium", "CWE-338", "Predictable random for a secret", "no"),
            ("TLS_VERIFY", 71, "medium", "CWE-295", "TLS certificate verification disabled", "yes"), ("SSRF", 71, "medium", "CWE-918", "Server-side request forgery", "no"),
            ("DEBUG_ON", 75, "medium", "CWE-489", "Debug mode enabled", "yes"), ("Q_UNUSED_IMPORT", 5, "info", "-", "Unused import", "-"),
            ("Q_NO_DOCSTRING", 29, "info", "-", "Missing docstring", "-")]
    rows += [list(map(str, r)) for r in data]
    d.table(rows, "Findings returned for the demonstration pull request (risk 99, BLOCK)", widths=[0.2, 0.07, 0.11, 0.12, 0.38, 0.12], font=9, align=["l", "c", "c", "c", "l", "c"])
    d.p("For the SQL injection in `find_user` the Remediation Agent produced the following patch, applied it to a copy of the file and re-ran the analyser; "
        "the rule no longer fired, so the patch was marked as verified. The Security Reasoner described the flow as attacker-controlled input entering the function, "
        "reaching `cur.execute` without sanitisation, and executing with attacker data, and it added that the independent metric model also rated `find_user` as "
        "vulnerable (probability 1.00, drivers M14 untrusted sources and M13 string-built sinks).")
    d.code('''--- a/app/users.py
+++ b/app/users.py
@@ -22,5 +22,5 @@
     name = request.args.get("name")
     cur = get_db().cursor()
-    cur.execute(f"SELECT id, email FROM users WHERE name = '{name}'")
+    cur.execute("SELECT id, email FROM users WHERE name = ?", (name,))
     return jsonify(cur.fetchall())''', "Verified patch for the SQL injection at line 24")
    d.table([["Input", "Output"],
             ["Model Lab, Try it: `get_user(name)` builds `q = f\"SELECT ... '{name}'\"` and calls `cur.execute(q)`",
              "Metric model: probability 0.006, no type (below the 0.5 threshold), driver M8 I/O & query calls. Static rules: SQLI, line 3, high. The two detectors disagree; the rule is right."],
             ["Codebase question: \"Where is the authentication mechanism implemented?\" (demo shop)",
              "Intent \"Authentication & sessions\"; `app/auth.py` (module overview, `login` line 25, `hash_password` line 13) and `tests/test_auth.py` (`test_hash_is_stable`, line 4). Correct file ranked first."],
             ["Compare versions: the before / after sample of one file",
              "Review \"Demo: refactor user service\": risk 81, verdict BLOCK, 4 security findings and 11 findings in total (visible in the history screen). Findings that were already in the old version are shown separately as pre-existing."],
             ["Paste a diff that is not a diff", "The API answers 422 with a readable message and no job is started."],
             ["GitHub PR link that does not exist", "The job ends with a readable error (tested); a real pull request was not fetched in this project."]],
            "Further sample inputs and outputs (run on 18 October 2026)", widths=[0.4, 0.6], font=9)


# ------------------------------------------------------------------ success and failure
def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("Where it works")
    d.bullets([
        f"All {DEMO['stats']['functions_flagged']} vulnerable functions of the demonstration pull request were flagged, and every security finding has a CWE, an explanation, the quoted line and a remediation text.",
        f"{DEMO['stats']['autofix_verified']} of {DEMO['stats']['autofix']} generated patches passed the re-scan (parameterised queries, argument lists instead of shell strings, `safe_load` and similar rewrites).",
        f"The rule engine raised only {EV['rule_engine']['fp']} false alarms and the model {EV['ml_model']['fp']} on 1,375 safe look-alikes, and together they found {EV['combined_or']['tp']} of the 125 vulnerable functions.",
        "Input errors, expired tokens and failed jobs produce readable messages instead of stack traces, and every screen ran in the scripted browser flows without console errors.",
    ])
    d.h3("Where it fails or is weak")
    d.table([["Observation", "Cause", "Effect and handling"],
             [f"The rule engine missed {EV['rule_engine']['fn']} of 125 vulnerable test functions and the metric model {EV['ml_model']['fn']}", "Rules cover patterns they know; the model sees only counts of metrics; about 1% of the generated labels are wrong on purpose", "Both are reported; the combination misses 15. Real recall on real code is unknown"],
             ["`get_user` (query built in a variable, then executed) gets probability 0.006 from the model", "The f-string is assigned to `q` first, so the call argument is a plain name and the string-built-sink metric stays 0", "The rule SQLI still fires at line 3; this is why the product never relies on the model alone"],
             ["The predicted type of three of the seven demo functions disagrees with the rules (`hello` XSS shown as path traversal; `import_data` shown as weak crypto; `fetch` SSRF shown as path traversal). Deserialization, path traversal and code execution have type F1 of only 0.21, 0.33 and 0.38", f"Accuracy of the type classifier is {f3(REP['type_accuracy'])}; metric signatures overlap; SSRF is not one of its eight types", "Finding cards use the exact rule and CWE; the model's type is only a hint and decides no verdict"],
             ["Eight of the 15 security findings of the demonstration have no patch", "The engine rewrites only cases whose safe form it can derive; secrets, XSS and path traversal need design decisions", "The finding still carries a remediation text and a safe example"],
             ["Retrieval put the expected file second or lower for four of twelve questions (\"How is the user looked up by name?\" does not return `app/db.py`)", "Scoring by text similarity, concept words and graph links is ambiguous when a question shares few words with the code", "Evidence rows list several files with reasons; the check is small"],
             ["The review history of all accounts is one list", "The `reviews` table has no user column", "Documented as a limitation; the interface does not separate users' reviews"]],
            "Failure and weakness analysis", widths=[0.34, 0.33, 0.33], font=8.5)


def sec_results_limits(d):
    d.h2("Limits of the Results")
    d.bullets([
        f"**Generated data.** The model was trained and tested on {REP['n_functions']:,} generated Python functions; its F1 of {f3(MODELS[BEST]['f1'])} does not show how it performs on real repositories, and the rule evaluation is optimistic because the rules and the generator were written by the same team.",
        f"**Best of five.** The headline XGBoost F1 is the best of five corpora (mean {ms(BEST, 'f1')}); the number of metrics was not re-selected for each corpus and the ablation is confounded.",
        "**No real labelled pull requests.** Precision and recall of the whole system on real pull requests were not measured, and no comparison with Bandit, Semgrep or CodeQL was run.",
        "**Untested paths.** The optional language-model mode (no API key) and the fetch of a real GitHub pull request (only the error path) were not tested; the retrieval check covers one small repository.",
        "**One machine, no user study.** All timings come from one desktop computer; no load test was run and no developer rated the findings or the answers.",
    ])


def sec_objectives(d):
    d.h2("Objectives Against Outcomes")
    d.p("The six objectives are those stated in the objectives document of the batch. The outcome column says plainly whether each was achieved, achieved in part or not measured.")
    d.table([["Objective", "Outcome", "Evidence"],
             ["1. Extract changed files and diff context automatically when a pull request is opened", "Achieved on demand; not on opening",
              "Diffs, two file versions, GitHub links, files, zip files and folders are parsed into changed files, hunks and line ranges (Ingestion Agent). There is no webhook: the user starts the review. Real GitHub fetching was not tested beyond the error path."],
             ["2. Compute source-code metrics for changed files and use them to rank vulnerability likelihood", "Achieved",
              f"14 metrics per function; nine models; {BEST} F1 {f3(MODELS[BEST]['f1'])} (best of five corpora) on generated data; all 7 functions of the demonstration ranked 0.89 to 1.00."],
             ["3. Perform AST-based static analysis to detect injection, access-control and validation flaws", "Achieved for injection and validation; access control only partly",
              f"{RULES_SECURITY} security rules with taint tracking in Python (SQL, command, code, path, template, XSS, SSRF, deserialization, secrets, TLS, JWT, CSRF) and regex rules for three more languages; rule engine precision {f3(EV['rule_engine']['precision'])} on the generated corpus. Missing object-level authorisation (IDOR) is not detected."],
             ["4. Deploy multiple LLM agents covering security, code quality and maintainability", "Achieved in part",
              "Seven cooperating agents (ingestion, static analysis, ML risk, security reasoner, remediation, quality reviewer, judge) run and are traced. They are deterministic programs; a language model only rewrites explanations when a key is supplied, and that mode was not measured."],
             ["5. Retrieve related code from the repository so that review comments reflect the wider codebase", "Achieved in part",
              f"The codebase assistant retrieves related code (expected file first for {RET['top1']} of {RET['questions']} questions). It is a separate feature: the review comments of a pull request do not yet pull in related repository code."],
             ["6. Post consolidated review comments and evaluate precision against manually reviewed pull requests", "Comment achieved; evaluation not achieved",
              f"A consolidated comment is generated and can be copied or exported (Markdown, SARIF, JSON, CSV); it is not posted to GitHub automatically. No manually reviewed pull requests were available, so precision on them was **not measured**; precision was measured only on the generated corpus (rules {f3(EV['rule_engine']['precision'])}, model {f3(EV['ml_model']['precision'])})."]],
            "Objectives against outcomes", widths=[0.3, 0.16, 0.54], font=9)
