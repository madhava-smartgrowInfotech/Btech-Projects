"""Build 13.Review_2_PPT.pptx from D:\\abstracts\\Templates\\Review_2_PPT.pptx (20 slides)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (fill, put_picture, replace_chart, replace_everywhere, set_notes, set_paras, set_table, shape, style_chart, table_size)  # noqa: E402
from doc_common import (BATCH, CHARTS, COLLEGE, CV, DEPT, DIAG, GUIDE, GUIDE_DESIG, LAT, LR, M, PRODUCT, R, RF, SHOTS, STUDENTS, T, TITLE, X, YEAR, p)  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_2_PPT.pptx"
OUT = BATCH / "13.Review_2_PPT.pptx"
KEYWORDS = "phishing detection, URL classification, crowdsourced threat intelligence"


def px(v):
    return Emu(int(v * 9525))


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    replace_everywhere(prs, {"The Hidden Risk of Social Media": PRODUCT})
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Review 2", TITLE, "Batch A3", KEYWORDS
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A3"

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    set_paras(shape(s, 3), TITLE, 26)
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  Batch A3 (CSE-DS, Section A)  \u00b7  {YEAR}"], 13)
    set_notes(s, "Review 2 covers the design, methodology and progress of PhishGuard.")

    # 2 contents
    s = S[1]
    for sid, t in [(21, "Model and training"), (27, "Data flow, modules, database"), (36, "Preliminary results and screens")]:
        set_paras(shape(s, sid), t)
    set_notes(s, "Twelve parts, from a recap of Review 1 through design and methodology to progress, results, testing and next steps.")

    # 3 recap
    s = S[2]
    fill(s, 8, "Blacklists miss zero-day phishing URLs, fixed rules are easy to evade, and models trained once go stale. Users cannot see why a link is flagged.", 16)
    fill(s, 13, "The base paper's three stages: URL features, ML classification, crowdsourced refinement, built as a Flask API with a React interface.", 16)
    for sid, t in zip((15, 18, 21, 24, 27), ["URL string", "47 offline features", "3 models, best F1 deployed", "Community verdict first", "Report, retrain, reload"]):
        fill(s, sid, t, 15)
    set_notes(s, "Recap of Review 1: the problem and the proposed system as a five-step pipeline.")

    # 4 architecture
    s = S[3]
    put_picture(s, DIAG / "01_system_architecture.png", (57, 124, 720, 518), remove_ids=(4,), name="System architecture diagram")
    fill(s, 5, ["Client: React 18 + Vite (port 5103), seven pages, recharts, three.js hero.",
                "API: Flask (port 8103); backend/server.py wraps the original app and adds five read-only endpoints and CORS.",
                "Detector: community verdict first, then the best model with reputation and vote adjustments.",
                "ThreatIntel: SQLite store of reports, consensus, optional OpenPhish and URLhaus sync.",
                "Retrain: base data plus confirmed URLs, hot reload of the best model."], 16, bullet=True)
    set_notes(s, "The browser talks only to the Vite server, which proxies /api to Flask. The detection modules are plain Python behind the API.")

    # 5 methodology
    s = S[4]
    for sid, t in zip((5, 8, 11, 14, 17, 20, 23), ["Load 40,000 URLs", "Clean + normalise", "Extract 47 features", "Split 80 / 20", "Train 3 models", "Evaluate + select", "Check, report, retrain"]):
        fill(s, sid, t, 14)
    set_paras(shape(s, 25), "Same data for all")
    fill(s, 26, "All three classifiers use the same features and the same stratified split, so the comparison is fair.", 15)
    set_paras(shape(s, 28), "Community first")
    fill(s, 29, "A confirmed community verdict, phishing or safe, overrides the model at check time.", 15)
    set_paras(shape(s, 31), "Closed loop")
    fill(s, 32, "Confirmed URLs are added to the training data (x3) and the retrained model is hot-reloaded.", 15)
    set_notes(s, "End-to-end workflow in seven steps. Features are computed offline from the URL string so training and checking use identical code.")

    # 6 dataset
    s = S[5]
    set_paras(shape(s, 2), "Dataset and input sources")
    ch = replace_chart(s, 4, ["Phishing", "Legitimate"], [("URLs", [20000, 20000])])
    style_chart(ch, "Training data: URLs per class", ["3F3FBF"], legend=False, label_pt=11, axis_title="URLs")
    rows = [["Source", "Size", "Use"],
            ["Sample of a public labelled URL set", "40,000 URLs (20,000 + 20,000)", "Train and test"],
            ["Split (stratified, seed 42)", "32,000 train / 8,000 test", "Evaluation"],
            ["URL length", "mean 51.5, median 40, max 1,383", "Feature design"],
            ["Community reports", "Created at run time (SQLite)", "Zero-day verdicts"],
            ["OpenPhish and URLhaus feeds", "up to 500 URLs each, optional", "Trusted reports"]]
    sz = table_size(rows, 530, 400, [0.4, 0.38, 0.22], 12, 9)
    set_table(shape(s, 7), rows, sz, widths=[0.4, 0.38, 0.22], header_size=sz)
    set_notes(s, "The 40,000 URLs are a balanced sample of a public dataset of about 420,000 URLs. Its licence was not verified. Only 266 URLs contain a scheme, so the extractor adds http:// first.")

    # 7 preprocessing
    s = S[6]
    set_paras(shape(s, 2), "Data preparation and features")
    set_paras(shape(s, 7), "Cleaning")
    fill(s, 8, "Rows without a URL or label are dropped, labels mapped to 0/1, whitespace trimmed, URLs shorter than 4 characters removed and duplicates dropped.", 16)
    set_paras(shape(s, 12), "Normalisation")
    fill(s, 13, "Add a scheme when missing, lower-case the host, strip www., keep port, path and query. Malformed ports or brackets never raise an error.", 16)
    set_paras(shape(s, 17), "47 features")
    fill(s, 18, "23 lexical (lengths, counts, entropy, suspicious words), 9 structural (IP host, port, subdomains, shorteners, extensions) and 15 domain features (domain entropy, TLD, brand, reputation). No DNS or page download.", 16)
    set_notes(s, "Preprocessing is cleaning plus feature extraction. Everything is computed from the URL string, so training and real-time checking use the same code.")

    # 8 model
    s = S[7]
    set_paras(shape(s, 2), "Models: three classifiers compared")
    put_picture(s, CHARTS / "feature_importance.png", (75, 124, 693, 518), remove_ids=(4,), name="XGBoost feature importance")
    rows = [["Model", "Setting"], ["Logistic Regression", "scaled, C 1.0, balanced"], ["Random Forest", "300 trees, balanced"], ["XGBoost", "400 trees, depth 8, lr 0.08"]]
    set_table(shape(s, 9), rows, 12, header_size=12)
    set_paras(shape(s, 6), "Top-10 features of the selected XGBoost model. Selection rule: highest F1, ROC-AUC breaks ties.", 11)
    set_notes(s, "The three models match the project objectives. The deployed model is the best by F1: XGBoost.")

    # 9 training configuration
    s = S[8]
    set_paras(shape(s, 2), "Training configuration")
    rows = [["Setting", "Value"], ["Training / test rows", "32,000 / 8,000"], ["Features", "47"], ["Split", "stratified, seed 42"],
            ["Training time", f"RF {RF['train_seconds']} s, XGB {X['train_seconds']} s, LR {LR['train_seconds']} s"],
            ["Selection", "best F1 (ROC-AUC tie-break)"], ["Cross-validation", "5-fold, all 40,000 URLs"],
            ["Retrain weight", "confirmed URLs x3"], ["Hardware", "Intel Core i5-12500, 12 threads, no GPU"]]
    set_table(shape(s, 10), rows, 13, header_size=13)
    put_picture(s, CHARTS / "learning_curve.png", (672, 232, 550, 330), remove_ids=(5,), name="Learning curve")
    set_paras(shape(s, 7), "Learning curve: F1 rises from 89.5 % (3,200 URLs) to 93.2 % (32,000)", 11)
    set_notes(s, "Training is fast: all three models take about 15 seconds. The learning curve suggests more data would still help.")

    # 10 decision logic
    s = S[9]
    put_picture(s, DIAG / "10_algorithm_flowchart.png", (57, 124, 420, 520), remove_ids=(4,), name="Decision flowchart")
    for bid in (7, 10, 13):
        shape(s, bid).height = px(80)
    set_paras(shape(s, 6), "Community first")
    fill(s, 7, "A confirmed entry for the URL or its host decides at once: phishing (probability at least 0.97) or safe (at most 0.03).", 16)
    set_paras(shape(s, 9), "Model second")
    fill(s, 10, "Otherwise p from the model; x0.4 for popular domains; +-0.15 per net pending vote.", 16)
    set_paras(shape(s, 12), "Thresholds")
    fill(s, 13, "p >= 0.60 phishing; p >= 0.35 suspicious; otherwise safe. Every check is logged with its reason.", 16)
    set_notes(s, "Decision logic: the community verdict wins, then the model with two small adjustments, then two thresholds.")

    # 11 data flow
    s = S[10]
    set_paras(shape(s, 2), "Data flow and modules")
    put_picture(s, DIAG / "04_dfd_level1.png", (57, 118, 560, 330), remove_ids=(4,), name="DFD level 1")
    put_picture(s, DIAG / "05_dfd_level2.png", (632, 118, 589, 330), name="DFD level 2")
    set_paras(shape(s, 5), "DFD level 1 (left) and level 2 expansion of the check path (right)", 11)
    shape(s, 5).left, shape(s, 5).top = px(57), px(452)
    rows = [["Module", "Responsibility"], ["features / data", "normalise URLs, 47 features, dataset load and split"],
            ["train / retrain", "fit three models, evaluate, save metrics.json; merge confirmed URLs and retrain"],
            ["detector / threat_intel", "decision order, hot reload; reports, votes, consensus, feed sync, check log"]]
    set_table(shape(s, 12), rows, 12, widths=[0.2, 0.8], header_size=12, row_h=34)
    shape(s, 12).top = px(485)
    set_notes(s, "Level 1 shows seven processes and five data stores; level 2 opens the check path.")

    # 12 database and UML
    s = S[11]
    set_paras(shape(s, 2), "Database design and UML")
    put_picture(s, DIAG / "06_er_diagram.png", (57, 118, 560, 340), remove_ids=(5,), name="ER diagram")
    put_picture(s, DIAG / "07_uml_class_diagram.png", (632, 118, 589, 340), name="UML class diagram")
    set_paras(shape(s, 6), "ER diagram: 3 SQLite tables and 3 file stores (left); UML class diagram (right)", 11)
    shape(s, 6).left, shape(s, 6).top, shape(s, 6).width = px(57), px(460), px(1164)
    rows = [["Table", "Key fields", "Relations"],
            ["reports", "url_norm, url, verdict, reporter, source, note, created_at", "N per intel row (same url_norm)"],
            ["intel", "url_norm (PK), phishing_votes, safe_votes, status, used_in_training", "1 per URL"],
            ["checks", "url, verdict, probability, decided_by, created_at", "append-only log"]]
    set_table(shape(s, 13), rows, 11, widths=[0.14, 0.56, 0.3], header_size=11, row_h=30, total_px=1164)
    t = shape(s, 13)
    t.left, t.top, t.width = px(57), px(492), px(1164)
    set_notes(s, "Three SQLite tables in threat_intel.db. reports and intel are linked logically by the normalised URL; there is no SQL foreign key.")

    # 13 technology
    s = S[12]
    cards = [(7, 8, "Language", "Python 3.11, JavaScript (JSX)"), (12, 13, "Machine learning", "scikit-learn 1.4, XGBoost 2.0, pandas, NumPy, joblib"),
             (17, 18, "Frontend", "React 18, Vite 5, recharts, three.js, framer-motion, gsap, lucide"), (22, 23, "Backend", "Flask 3.1 JSON API, CORS, SQLite (sqlite3)"),
             (27, 28, "Data", "40,000-URL CSV, OpenPhish and URLhaus feeds (optional)"), (32, 33, "Testing", f"3 + 20 + {T['total']} automated checks; Playwright captures")]
    for tid, bid, ttl, body in cards:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 15)
    set_notes(s, "Everything runs locally. The only external connections are the two optional feeds.")

    # 14 progress
    s = S[13]
    rows = [["Component", "Status"], ["Dataset, cleaning, 47-feature extractor", "Completed"], ["Three classifiers, comparison, metrics.json", "Completed"],
            ["Threat-intelligence store, consensus, feed sync", "Completed"], ["Decision pipeline with community override", "Completed"],
            ["Retraining loop with hot reload", "Completed"], ["Flask API, CLI and React interface (7 pages)", "Completed"],
            ["Automated tests (95 checks) and measurements", "Completed"], ["User acceptance, load tests, sign-in", "Not done"]]
    set_table(shape(s, 15), rows, 13, widths=[0.78, 0.22], header_size=13)
    for vid, lid, v, lab in [(6, 7, "3", "classifiers trained"), (9, 10, "16", "API and page routes"), (12, 13, "95/95", "automated checks passing")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, "Every planned feature is implemented. Open items are user-acceptance testing, load testing and authentication.")

    # 15 preliminary results
    s = S[14]
    set_paras(shape(s, 2), "Preliminary results: held-out test set (8,000 URLs)")
    cats = ["Accuracy", "Precision", "Recall", "F1"]
    ser = [("XGBoost", [round(X[k] * 100, 2) for k in ("accuracy", "precision", "recall", "f1")]),
           ("Random Forest", [round(RF[k] * 100, 2) for k in ("accuracy", "precision", "recall", "f1")]),
           ("Logistic Regression", [round(LR[k] * 100, 2) for k in ("accuracy", "precision", "recall", "f1")])]
    ch = replace_chart(s, 4, cats, ser, number_format="0.0")
    style_chart(ch, "Test metrics by model (%)", ["0F7A5A", "3F3FBF", "D99A1E"], number_format="0.0", legend=True, label_pt=8, axis_title="percent")
    ch.value_axis.minimum_scale = 60
    ch.value_axis.maximum_scale = 100
    for vid, lid, v, lab in [(6, 7, p(X["f1"], 1), "XGBoost F1 (RF 92.5 %, LR 81.8 %)"), (9, 10, f"{X['roc_auc']:.3f}", "XGBoost ROC-AUC (5-fold CV F1 92.6 %)"),
                             (12, 13, f"{LAT['api_check_ms_mean']:.1f} ms", "mean time of a check through the API")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, "Held-out test results re-checked from the saved models. Cross-validation F1 is 92.56 % for XGBoost.")

    # 16 output screens
    s = S[15]
    put_picture(s, SHOTS / "05_check_community_override.png", (91, 128, 507, 476), remove_ids=(4,), name="Community override screenshot")
    put_picture(s, SHOTS / "09_intel.png", (679, 128, 512, 476), remove_ids=(7,), name="Threat intelligence screenshot")
    set_paras(shape(s, 6), "Check URL: a lookalike page scored 9.5 % by the model becomes Phishing (97 %) after two reports", 11)
    set_paras(shape(s, 9), "Threat intelligence: 10 URLs, 5 confirmed phishing, 2 confirmed safe, 3 pending", 11)
    set_notes(s, "Real captures of the running application with usage loaded: 19 reports, a feed sync and a retrain.")

    # 17 testing
    s = S[16]
    set_paras(shape(s, 2), "Testing and observations")
    rows = [["Test group", "Checks", "Result"], ["Original unit and web tests", "3", "Passed"], ["End-to-end API smoke test", "20", "Passed"],
            ["Extended: unit + integration", "31", "Passed"], ["Extended: functional + validation", "31", "Passed"], ["Extended: security + performance", "10", "Passed"], ["Total", "95", "95 passed"]]
    set_table(shape(s, 18), rows, 13, widths=[0.6, 0.15, 0.25], header_size=13)
    fill(s, 5, ["95 automated checks pass; malformed ports, 5,000-character URLs and javascript: URLs return normal responses.",
                "SQL-injection text is stored as data; script tags are HTML-escaped on every page.",
                "A check takes 8.0 ms on average through the API (p95 9.7 ms).",
                "Retraining with 807 confirmed URLs produced model v2 end to end.",
                "Not done: user-acceptance, load and authentication tests."], 16, bullet=True)
    set_notes(s, "The extended suite is scripts/extra_tests.py: 72 checks in six categories.")

    # 18 challenges
    s = S[17]
    cards = [(7, 8, "Zero-day URLs", "A community verdict overrides the model at once, in both directions."),
             (12, 13, "False positives", "docs.python.org and amazon.in are flagged; two safe reports clear them."),
             (17, 18, "Clean-looking phishing", "311 of 4,000 phishing URLs look ordinary; URL features alone cannot catch them."),
             (22, 23, "Version drift", "The saved logistic-regression file cannot be loaded by the installed scikit-learn; it was refitted."),
             (27, 28, "Does retraining help?", "Random in-distribution URLs change F1 by under 0.1 point; value is the override."),
             (32, 33, "Noisy reports", "Two net votes can be gamed; no sign-in or review yet. Recorded as a limitation.")]
    for tid, bid, ttl, body in cards:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 15)
    set_notes(s, "Six challenges found during the work and how each was handled or recorded.")

    # 19 next steps
    s = S[18]
    for sid, t in zip((5, 8, 11, 14), ["Real-user feedback", "Fresher, larger data", "Final report", "Final presentation and demo"]):
        fill(s, sid, t, 16)
    fill(s, 15, ["Ask analysts and reporters to try the interface (not yet done).",
                 "Evaluate on a larger, more recent dataset and URLs collected after training.",
                 "Add sign-in, rate limiting and an administrator review step for reports.",
                 "Document every diagram, test and result in the report."], 18, bullet=True)
    set_notes(s, "What remains: user feedback, stronger data and trust controls, then the report and the final demo.")

    set_notes(S[19], "Thank you. Questions are welcome.")
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
