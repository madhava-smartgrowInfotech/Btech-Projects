"""Chapters 6 (decisions), 9, 10, the reference list and the appendices."""
from __future__ import annotations

from doc_common import CHARTS, CV, DEMO, LAT, M, R, REF_NOTE, REFERENCES, ROOT, SHOTS, T, V2, X, RF, LR, p
from rc_method import PG, src
from rc_results import MAIN, SCREENS, screens, screens_by_files


def sec_decisions(d):
    d.h2("Implementation Decisions and Reasoning")
    d.table([["Decision", "Reasoning", "Consequence"],
             ["Offline URL-only features", "Training and run time must use identical code; fetching pages is slow and risky", "Fast and safe; cannot see page content"],
             ["Three classical models, not a deep network", "Objective 3 names them; they train in seconds and give importances", "Lower accuracy than the base paper's network"],
             ["Same split and features for every model", "A fair comparison needs identical data", "Differences reflect the algorithm only"],
             ["Select by F1, break ties by ROC-AUC", "Classes are balanced; F1 balances missed phishing and false alarms", "XGBoost selected"],
             ["Community verdict before the model", "A confirmed human verdict is stronger evidence than a score; it gives zero-day coverage at once", "Wrong consensus overrides a right model"],
             ["Net votes of 2 for confirmation", "Simple, explainable, quick; one report is not enough", "Two cooperating reporters can confirm anything"],
             ["Confirmed-safe status", "The community must be able to undo false positives (problem statement point 4)", "Not in the base paper"],
             ["Host-level lookup", "A confirmed phishing host usually serves many pages", "Over-blocks shared hosts"],
             ["Reputation discount x0.4 for popular domains", "Cuts false alarms on well-known sites cheaply", "Hand-written list; misses amazon.in and docs.python.org"],
             ["Retrain weight 3 by row repetition", "Works with every model without special sample-weight support", "Memory grows with weight"],
             ["Hot reload under a lock", "Avoid restarts and torn reads of the model", "In-flight requests use old or new model, never a mix"],
             ["Keep the original Flask app and add an API layer", "Preserves the tested pages and CLI; the new UI needs only a thin, additive layer", "Two interfaces to maintain"],
             ["SQLite", "Single file, no server, enough for a local deployment", "Not for heavy concurrent writes"]],
            "Main implementation decisions", widths=[0.28, 0.4, 0.32], font=9)


# ---------------------------------------------------------------- Chapter 9
def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.p("This project built PhishGuard, an adaptive phishing URL detection system that follows the three-stage design of the base paper: extract features from a "
        "URL, classify it with machine learning, and refine the system with crowdsourced threat intelligence. A balanced sample of 40,000 labelled URLs was cleaned "
        f"and turned into 47 offline features; Random Forest, XGBoost and Logistic Regression were compared on the same split; and XGBoost was selected with accuracy "
        f"{p(X['accuracy'])}, F1 {p(X['f1'])} and ROC-AUC {X['roc_auc']:.3f} on 8,000 held-out URLs, and F1 {p(CV['xgboost']['f1']['mean'])} in 5-fold cross-validation.")
    d.p("Around the classifier, the project built a community store in which two net votes, or one trusted feed report, confirm a URL; a confirmed verdict, phishing or "
        "safe, overrides the model at once; and confirmed URLs are folded into the training data by a retraining loop that reloads the new model without a restart. "
        "A Flask API, a command-line interface and a seven-page React interface make the whole pipeline usable.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.table([["Objective", "Achieved?", "Note"],
             ["1. Collect and preprocess a dataset", "Yes", "40,000 URLs from a public set; one source"],
             ["2. Extract lexical, structural and domain features", "Yes", "47 features, 3 groups, red flags"],
             ["3. Train and compare RF, XGBoost, LR", "Yes", f"XGBoost F1 {p(X['f1'])}; LR is clearly weaker"],
             ["4. Integrate crowdsourced threat intelligence", "Yes", "Consensus, trusted feeds, community-first decisions; no administrator review"],
             ["5. Refine the model continuously", "Mechanism: yes; effect: not measurable here", "Retrain and hot reload run end to end; no gain on in-distribution data"],
             ["6. Real-time classification with a web interface", "Yes", f"Mean API check {LAT['api_check_ms_mean']:.1f} ms; no sign-in"]],
            "Objectives and their status", widths=[0.4, 0.22, 0.38], font=10)


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    d.numbered([f"Tree ensembles on 47 engineered URL features reach {p(X['accuracy'], 1)} accuracy; logistic regression reaches only {p(LR['accuracy'], 1)}, so the problem is not linearly separable in these features.",
                f"Lexical features carry most of the signal (F1 {p(R['ablation']['lexical only']['f1'], 1)} alone); structural features alone are weak; adding domain features gives the final 3 to 4 points.",
                "The model does not depend on its two strongest features: removing both costs only 0.2 points of F1.",
                "A well-chosen threshold matters: F1 is flat between 0.40 and 0.60, but the 0.35 suspicious band recovers 187 phishing URLs that would otherwise read as safe.",
                "The community override works in both directions and takes effect immediately: a lookalike page scored 9.5 % became phishing at 97 % after two reports, and two flagged legitimate pages were cleared.",
                "Retraining on random correctly labelled URLs from the same distribution does not change the average F1 (within 0.1 point); the loop's value is the override, not the average.",
                "URL-only features cannot catch phishing pages on clean-looking domains, and a hand-written reputation list causes false positives on legitimate sites such as docs.python.org."])
    d.figure(CHARTS / "model_comparison.png", "Summary: the three classifiers on the held-out test set", width=4.8)


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.bullets(["A first-line link checker for a team or a small organisation, with a shared community list of confirmed phishing and safe URLs.",
               "A teaching tool for URL-based phishing detection: its features, red flags, thresholds and retraining are visible in the interface.",
               "A back end for a browser extension, a mail-gateway plug-in or a chat bot through the JSON API.",
               "A test bed for studying crowd-fed learning, since the consensus rule, the weight and the thresholds are single constants in config.py."])


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets(["Small, single-source dataset; the 92.9 % accuracy is not comparable with the base paper's 99.8 %.",
               "URL-only features; clean-looking hosts and ordinary-looking pages are missed (311 false negatives of 4,000 phishing URLs).",
               "Hand-written reputation list (145 domains).",
               "Anonymous vote-based confirmation without sign-in, moderation, rate limiting or reporter reputation; host-wide override.",
               "Benefit of retraining on new campaigns not measured; v1 and v2 metrics not comparable.",
               "No load, concurrency or user-acceptance testing."])


# ---------------------------------------------------------------- Chapter 10
def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets(["Evaluate on a larger and more recent dataset such as PhiUSIIL [17], and on URLs collected after the training date, to measure generalisation honestly.",
               "Tune the hyper-parameters and add calibration, so that the probability is a true probability and the thresholds have a principled basis.",
               "Replace the hand-written popular-domain list with a ranked list such as a top-sites list, and handle country-code domains.",
               "Make host-level override smarter: apply it to a host only after several distinct URLs are confirmed, and never to shared-hosting providers.",
               "Add an administrator verification queue before reports reach the training set, as the base paper does [1]."])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets(["Sign-in, roles, reporter reputation and rate limiting, so that votes can be weighted and abuse limited.",
               "Optional page-level features (title, form fields, redirects) fetched in a sandbox for URLs the model is unsure about.",
               "A browser extension and an e-mail plug-in using the existing API.",
               "Export of confirmed URLs as a feed, and import of further public feeds.",
               "A drift monitor that tracks the score distribution and recent false-positive reports."])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.bullets(["Move the community store from SQLite to a server database when many reporters write at once.",
               "Run the API behind a production WSGI server, with the model loaded once per worker and a shared reload signal.",
               "Cache verdicts for popular URLs and batch scoring, since the model scores 8,000 rows in about 11 ms.",
               "Containerise the API and the frontend for a repeatable deployment; add authentication and TLS in front."])


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets(["Reproduce the base paper's LSTM-attention model on the same data and compare it with the tree ensembles under identical conditions.",
               "Study the crowd loop under realistic noise: simulate dishonest and careless reporters and measure how many votes the consensus needs.",
               "Evaluate adaptation to new campaigns with a time-split dataset or a live feed, which this static sample could not do.",
               "Add explanation methods such as SHAP values to the red flags, and study their effect on user trust.",
               "Investigate adversarial URLs crafted to defeat the features, and countermeasures [1]."])


def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    d.p(REF_NOTE, italic=True)
    for i, r in enumerate(REFERENCES, 1):
        para = d.p(f"[{i}]\t{r}", align="left", size=11, space_after=3, line=1.15)
        para.paragraph_format.left_indent = __import__("docx").shared.Inches(0.45)
        para.paragraph_format.first_line_indent = __import__("docx").shared.Inches(-0.45)


# ---------------------------------------------------------------- appendices
def appendix_a(d):
    d.p("The listings below are the real source code, extracted by script from the files named in each caption.")
    d.h2("Feature extraction (phishguard/features.py)")
    d.code(src(PG / "features.py", "extract_features"), "extract_features")
    d.h2("Training and evaluation (phishguard/train.py)")
    d.code(src(PG / "train.py", "build_models"), "build_models")
    d.h2("Threat intelligence (phishguard/threat_intel.py)")
    d.code(src(PG / "threat_intel.py", "report"), "ThreatIntel.report")
    d.code(src(PG / "threat_intel.py", "_consensus").replace("    @staticmethod\n", ""), "ThreatIntel._consensus")
    d.h2("Real-time decision (phishguard/detector.py)")
    d.code(src(PG / "detector.py", "check"), "Detector.check")
    d.h2("Retraining (phishguard/retrain.py)")
    d.code(src(PG / "retrain.py", "retrain"), "retrain")
    d.h2("API layer (backend/server.py)")
    d.code(src(ROOT / "backend" / "server.py", "build_app"), "build_app")


def appendix_b(d):
    d.h2("Installation")
    d.numbered(["Install Python 3.10 or later and Node.js 18 or later.",
                "Open a terminal in the `8.ProjectCode` folder and run `pip install -r requirements.txt`.",
                "Run `run.bat`. It trains the models if they are missing (under a minute), installs the frontend packages on first use, starts the API on port 8103 "
                "and the interface on port 5103, and opens http://127.0.0.1:5103.",
                "To run the checks, use `python tests.py`, `python scripts/smoke_test.py` and `python scripts/extra_tests.py`."])
    d.h2("User guide")
    d.table([["To do this", "Open", "Steps"],
             ["Check one URL", "Check URL", "Paste or type the URL (the scheme is optional), press Check. Read the verdict, the probability gauge, the red flags and the reason."],
             ["Check many URLs", "Check URL, Batch tab", "Drop a .txt or .csv file or paste one URL per line (up to 100), press Check."],
             ["Report a URL", "Report", "Enter the URL, choose phishing or safe, optionally add your name and a note, press Submit. Two net votes confirm it."],
             ["See what the community reported", "Threat intelligence", "Search or filter the table; click a row for the report history."],
             ["Import public feeds", "Threat intelligence", "Press Sync feeds, then Start sync (internet needed)."],
             ["Compare models and retrain", "Models", "Read the table, the confusion matrix and the importances; press Retrain now and confirm."],
             ["Review activity", "Activity", "See every check, the probability trend and the verdict mix."]],
            "How to use the main screens", widths=[0.22, 0.2, 0.58], font=9.5)
    d.h2("Troubleshooting")
    d.bullets(["**\"Cannot reach the PhishGuard backend\"** - start the API (`python backend/server.py`) and check port 8103.",
               "**No verdicts, \"unknown\"** - no model found; run `python run.py train`.",
               "**Feed sync fails** - the feeds need an internet connection; the application keeps working offline.",
               "**A warning about XGBoost model versions** - the saved model was written by a different XGBoost version; it still loads and works, and retraining rewrites it."])


def appendix_c(d):
    d.p("These are the remaining output screens that are not shown in Chapter 8, two to a row. Each caption is followed by a short description.")
    rest = screens_by_files([s[0] for s in SCREENS if s[0] not in MAIN])
    for k in range(0, len(rest), 2):
        pair = rest[k:k + 2]
        d.figure_pair([(SHOTS / f, cap) for f, cap, _, _, _ in pair], width=3.0, max_h=3.4)
        for f, cap, desc, _, _ in pair:
            d.p(f"**{cap}.** {desc}", size=11)
