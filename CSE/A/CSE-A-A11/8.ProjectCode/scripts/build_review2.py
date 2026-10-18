"""Build 13.Review_2_PPT.pptx from D:\\abstracts\\Templates\\Review_2_PPT.pptx (20 slides)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (fill, put_picture, replace_chart, replace_everywhere, set_notes, set_paras, set_table, shape, style_chart, table_size)  # noqa: E402
from doc_common import (API, BATCH, BATCH_NAME, BEST, CHARTS, COLLEGE, DEMO, DEPT, DIAG, EV, GUIDE, GUIDE_DESIG, LAT, MODELS, PRODUCT, REP, SEEDS, SHOTS,  # noqa: E402
                        STUDENTS, TITLE, YEAR, f3)
from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_2_PPT.pptx"
OUT = BATCH / "13.Review_2_PPT.pptx"
CACHE = Path(tempfile.gettempdir()) / "autosecai_deck"
CACHE.mkdir(exist_ok=True)
KEYWORDS = "pull request review, vulnerability detection, source-code metrics, multi-agent, code quality"


def px(v):
    return Emu(int(v * 9525))


def crop(name, top=0, bottom=0, left=0):
    """Crop the sticky top bar (or footer) off a screenshot; returns the cached file."""
    out = CACHE / f"{Path(name).stem}_{top}_{bottom}_{left}.png"
    with Image.open(SHOTS / name) as im:
        im.crop((left, top, im.width, im.height - bottom)).save(out)
    return out


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    replace_everywhere(prs, {"The Hidden Risk of Social Media": PRODUCT})
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Review 2", TITLE, "Batch A11", KEYWORDS
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A11"
    best = MODELS[BEST]
    rf = MODELS["Random Forest"]

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    fill(s, 3, TITLE.split(": ", 1)[1], 26)
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  {BATCH_NAME}  \u00b7  {YEAR}"], 12)
    set_notes(s, "Review 2 covers design, methodology and progress of AutoSecAI.")

    # 2 contents
    s = S[1]
    for sid, t in [(15, "Corpus and dataset"), (18, "Metrics and balancing"), (21, "Models and training"), (24, "Verdict logic"), (27, "Data flow, modules, database"), (36, "Preliminary results and screens")]:
        set_paras(shape(s, sid), t)
    set_notes(s, "Twelve parts, from a recap of Review 1 through the design and the pipeline to progress, results, testing and next steps.")

    # 3 recap
    s = S[2]
    fill(s, 8, "Pull requests arrive faster than they can be reviewed; manual review is uneven on security, static analysers drown reviewers in warnings, and a small diff is judged without the context of the codebase.", 16)
    fill(s, 13, "Seven cooperating agents: AST + taint static analysis, a metric-based ML risk score, explanation, verified patches, quality review and a judge; plus a retrieval assistant for the repository.", 16)
    for sid, t in zip((15, 18, 21, 24, 27), ["PR diff, files or GitHub link", "Static analysis + metric risk", "Explain + patch + verify", "Score + verdict", "Export, history, ask the repo"]):
        fill(s, sid, t, 15)
    set_notes(s, "Recap of Review 1: the problem and the proposed system as a five-step pipeline.")

    # 4 architecture
    s = S[3]
    put_picture(s, DIAG / "01_system_architecture.png", (50, 124, 730, 518), remove_ids=(4,), name="System architecture diagram")
    fill(s, 5, ["Client: React 19 + TypeScript + Vite (port 5311), TanStack Query, recharts, dark mode.",
                "API: FastAPI (port 8311): JWT sign-in, 25 route handlers, background jobs with live agent messages.",
                "Engine: autosecai package: diff parsing, AST/taint rules, 14-metric model, 7 agents, exports.",
                "Assistant: TF-IDF + concept scores + call graph retrieval over the repository.",
                "Data: SQLite (users, reviews as JSON), model artefacts; GitHub and an LLM key are optional."], 16, bullet=True)
    set_notes(s, "The browser talks only to the Vite server, which proxies /api to FastAPI. The engine runs locally; GitHub and an optional Anthropic key are the only external calls.")

    # 5 methodology
    s = S[4]
    for sid, t in zip((5, 8, 11, 14, 17, 20, 23), ["Sign in + choose input", "Ingest: diff, hunks, lines", "Static analysis: AST + taint", "ML risk: 14 metrics", "Reason + remediate", "Quality + judge: verdict", "Export + history"]):
        fill(s, sid, t, 14)
    set_paras(shape(s, 25), "Changed code first")
    fill(s, 26, "Findings are marked in or out of the diff, so the verdict is driven by what the pull request changes.", 15)
    set_paras(shape(s, 28), "Fixes are checked")
    fill(s, 29, "A patch is shown only if re-scanning the patched code no longer reports the finding.", 15)
    set_paras(shape(s, 31), "Evidence kept")
    fill(s, 32, "Every agent writes a trace entry; exports include Markdown, SARIF 2.1.0, JSON and CSV.", 15)
    set_notes(s, "End-to-end workflow in seven steps. The central idea: static rules and a metric model look at the same changed functions, and every agent leaves an audit trail.")

    # 6 dataset
    s = S[5]
    set_paras(shape(s, 2), "Dataset: a generated Python corpus")
    tc = REP["type_counts"]
    ch = replace_chart(s, 4, [k.replace("_", " ") for k in tc], [("Vulnerable functions", list(tc.values()))])
    style_chart(ch, f"Vulnerable functions per type ({REP['n_vulnerable']} of {REP['n_functions']:,})", ["3F3FBF"], legend=False, label_pt=11, axis_title="functions")
    rows = [["Data", "Size", "Use"],
            ["Generated Python corpus (seed 7)", f"{REP['n_functions']:,} functions, {REP['n_vulnerable']} vulnerable ({REP['class_ratio'] * 100:.2f}%)", "Train and test the metric model"],
            ["Split (stratified, seed 42)", f"{REP['train_size']:,} train / {REP['test_size']:,} test", "Held-out scores"],
            ["After SMOTE + Tomek (train only)", f"{REP['balanced_train_size']:,} rows", "Balanced training"],
            ["Built-in demo pull request", "1 file, +67 / -1 lines, 7 functions", "Demo and measurement"],
            ["Demo repository", "10 files, 24 code units", "Codebase assistant"],
            ["Base paper data (not used)", "21,759 C/C++ functions, 275 vulnerable", "Not distributable here"]]
    sz = table_size(rows, 530, 400, [0.38, 0.38, 0.24], 12, 9)
    set_table(shape(s, 7), rows, sz, widths=[0.38, 0.38, 0.24], header_size=sz)
    set_notes(s, "The corpus is generated, not collected: random benign logic plus injected vulnerable patterns of eight types, look-alike safe patterns and 1 percent label noise. It stands in for the base paper's C/C++ data, which is not available, so scores differ from the paper's.")

    # 7 preprocessing
    s = S[6]
    set_paras(shape(s, 2), "Data preparation: metrics, selection, balancing")
    set_paras(shape(s, 7), "Metric extraction")
    fill(s, 8, "Python's ast gives 14 metrics per function: M1 cyclomatic complexity ... M11 control dependency from the base paper, plus M12 risky API calls, M13 string-built sinks and M14 untrusted sources for taint-style flaws.", 16)
    set_paras(shape(s, 12), "Selection and scaling")
    fill(s, 13, f"Seven selectors (Pearson, SVM, Lasso, chi-squared, two RFE variants, variance) vote; k is swept from 5 to 14 and k = {REP['best_k']} is chosen (validation F1 {f3(REP['k_scores'][str(REP['best_k'])])}). Min-Max scaling.", 16)
    set_paras(shape(s, 17), "Class balancing")
    fill(s, 18, f"SMOTE (k = 5) then Tomek-link removal, implemented in-house: {REP['train_size']:,} training rows become {REP['balanced_train_size']:,} ({REP['tomek_removed']} Tomek removals). The test set is never touched.", 16)
    set_notes(s, "Preprocessing here means turning source code into metrics, choosing the useful ones and balancing the rare vulnerable class.")

    # 8 model
    s = S[7]
    set_paras(shape(s, 2), "Models and pipeline components")
    put_picture(s, CHARTS / "models_prf.png", (60, 150, 720, 400), remove_ids=(4,), name="Nine classifiers")
    rows = [["Component", "Detail"], ["Risk model", f"{BEST} (200 trees, depth 5)"], ["Compared", "8 other models, incl. Random Forest"], ["Type classifier", "Random Forest, 400 trees"],
            ["Rule engine", "30 security + 12 quality rules"], ["Explainer", "43-entry CWE / OWASP base"]]
    set_table(shape(s, 9), rows, 12, header_size=12)
    set_paras(shape(s, 6), "scikit-learn / XGBoost models trained here on the generated corpus; no deep network is used.", 11)
    shape(s, 6).left, shape(s, 6).top, shape(s, 6).width = px(60), px(560), px(720)
    set_notes(s, f"Nine classifiers were trained as in the base paper. {BEST} has the best F1 ({f3(best['f1'])}); Random Forest, the paper's winner, scores {f3(rf['f1'])} on this corpus.")

    # 9 configuration
    s = S[8]
    set_paras(shape(s, 2), "Training configuration")
    rows = [["Setting", "Value"], ["Corpus / split seeds", "7 / 42"], ["Split", "75 / 25 stratified"], ["Selected metrics", f"top {REP['best_k']} of 14"],
            ["Balancing", "SMOTE k = 5 + Tomek links"], ["Random Forest", "300 trees"], ["XGBoost", "200 trees, depth 5, rate 0.1"], ["Training time", f"{REP['seconds']} s, CPU only"]]
    set_table(shape(s, 10), rows, 13, header_size=13)
    put_picture(s, CHARTS / "k_sweep.png", (672, 232, 550, 330), remove_ids=(5,), name="k sweep chart")
    set_paras(shape(s, 7), "Feature-count sweep: validation F1 rises from 0.566 at k = 5 to 0.786 at k = 13")
    set_notes(s, "The base paper keeps the top five metrics. On this corpus validation F1 is 0.566 at k = 5 and 0.786 at k = 13 (test F1 0.645 against 0.826 for Random Forest), because the extra taint metrics matter.")

    # 10 decision logic
    s = S[9]
    put_picture(s, DIAG / "10_algorithm_flowchart.png", (30, 130, 610, 505), remove_ids=(4,), name="Decision flowchart")
    dx = 215
    for ids in ((5, 6, 7), (8, 9, 10), (11, 12, 13)):
        for sid in ids:
            sh = shape(s, sid)
            sh.left = Emu(sh.left + px(dx))
            sh.width = Emu(sh.width - px(dx))
    set_paras(shape(s, 6), "Verdict")
    fill(s, 7, "BLOCK if a high or critical security finding in the changed lines is likely real, or the risk score is 70 or more; REQUEST_CHANGES at a medium finding or 30 or more; otherwise APPROVE.", 15)
    set_paras(shape(s, 9), "Score")
    fill(s, 10, "Risk = 100 x (1 - exp(-W / 18)), W = sum of severity x confidence weights; findings outside the diff count 15%.", 15)
    set_paras(shape(s, 12), "Verified patches")
    fill(s, 13, "Each fix is applied to a copy and re-scanned; it is kept only when the same rule no longer fires near that line.", 15)
    set_notes(s, "Decision logic of the judge agent: how findings become a score and a verdict, and when a patch is trusted.")

    # 11 data flow
    s = S[10]
    set_paras(shape(s, 2), "Data flow and modules")
    put_picture(s, DIAG / "04_dfd_level1.png", (57, 112, 470, 350), remove_ids=(4,), name="DFD level 1")
    put_picture(s, DIAG / "05_dfd_level2.png", (545, 112, 676, 350), name="DFD level 2")
    set_paras(shape(s, 5), "DFD level 1 (left) and level 2 expansion of the 7-agent review (right)", 11)
    shape(s, 5).left, shape(s, 5).top = px(57), px(466)
    rows = [["Module", "Responsibility"], ["diffutil + rules", "parse diffs, zips, GitHub PRs; AST and taint rules; regex rules for JS, PHP, Java"],
            ["metrics + mlmodel + agents", "14 metrics, risk model, seven agents, scoring and verdict"],
            ["codeintel + report + store", "repository retrieval, exports, SQLite history"]]
    set_table(shape(s, 12), rows, 12, widths=[0.24, 0.76], header_size=12, row_h=34)
    shape(s, 12).top = px(500)
    set_notes(s, "Level 1 shows six processes and six data stores; level 2 opens the review process into the seven agents.")

    # 12 database and UML
    s = S[11]
    set_paras(shape(s, 2), "Database design and UML")
    put_picture(s, DIAG / "06_er_diagram.png", (57, 118, 560, 340), remove_ids=(5,), name="ER diagram")
    put_picture(s, DIAG / "07_uml_class_diagram.png", (632, 118, 589, 340), name="UML class diagram")
    set_paras(shape(s, 6), "ER diagram, 2 SQLite tables (left) and UML class diagram (right)", 11)
    shape(s, 6).left, shape(s, 6).top, shape(s, 6).width = px(57), px(460), px(1164)
    rows = [["Table", "Key fields", "Notes"],
            ["users (app.db)", "id, email UNIQUE, name, password_hash (bcrypt), created", "demo account seeded at start-up"],
            ["reviews (history.db)", "id, created, title, source, score, verdict, n_findings, n_security, payload", "payload holds findings, ML rows, trace, files as JSON"]]
    set_table(shape(s, 13), rows, 11, widths=[0.2, 0.46, 0.34], header_size=11, row_h=30, total_px=1164)
    t = shape(s, 13)
    t.left, t.top, t.width = px(57), px(492), px(1164)
    set_notes(s, "Two small SQLite databases. A review is stored as one JSON document, so there are no foreign keys; reviews are not linked to a user in this version.")

    # 13 technology
    s = S[12]
    cards = [(7, 8, "Language", "Python 3.11, TypeScript"), (12, 13, "Analysis and ML", "ast, scikit-learn, XGBoost, networkx, TF-IDF"),
             (17, 18, "Frontend", "React 19, Vite 8, Tailwind 4, TanStack Query, recharts, framer-motion"), (22, 23, "Backend", "FastAPI, Pydantic, PyJWT, bcrypt, uvicorn, SQLite"),
             (27, 28, "Exports", "Markdown, SARIF 2.1.0, JSON, CSV, patched files"), (32, 33, "Testing", "pytest (17 tests), API smoke test, Playwright UI flows, strict TypeScript build")]
    for tid, bid, ttl, body in cards:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 15)
    set_notes(s, "Everything runs on one laptop with no GPU; an Anthropic key is optional.")

    # 14 progress
    s = S[13]
    rows = [["Component", "Status"], ["Diff, zip, folder and GitHub PR ingestion", "Completed"], ["AST + taint rule engine, 43 rule entries", "Completed"],
            ["14-metric model, 9 classifiers, type classifier", "Completed"], ["Seven agents, verified patches, verdict", "Completed"],
            ["Exports: Markdown, SARIF, JSON, CSV", "Completed"], ["Codebase assistant and Model Lab", "Completed"],
            ["React web app with sign-in, history, dark mode", "Completed"], ["Precision on real reviewed pull requests", "Not done"]]
    set_table(shape(s, 15), rows, 13, widths=[0.78, 0.22], header_size=13)
    for vid, lid, v, lab in [(6, 7, "25", "API route handlers"), (9, 10, "43", "rule knowledge-base entries"), (12, 13, "17/17", "automated tests passing")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, "Every planned feature is implemented. The open item is measuring precision against manually reviewed real pull requests: no labelled set exists yet.")

    # 15 preliminary results
    s = S[14]
    set_paras(shape(s, 2), "Preliminary results: held-out 1,500 functions")
    names = list(MODELS)
    ch = replace_chart(s, 4, [n.replace(" (RBF)", "").replace("Logistic Regression", "Log. Reg.").replace("Gradient Boosting", "Grad. Boost").replace("Voting Ensemble", "Voting") for n in names],
                       [("F1", [round(MODELS[n]["f1"], 3) for n in names]), ("Recall", [round(MODELS[n]["recall"], 3) for n in names])], number_format="0.00")
    style_chart(ch, "F1 and recall of nine models on the generated corpus", ["3F3FBF", "2F9E6D"], number_format="0.00", legend=True, label_pt=8, axis_title="score")
    ch.value_axis.maximum_scale = 1.05
    for vid, lid, v, lab in [(6, 7, f3(best["f1"]), f"{BEST} F1 (Random Forest {f3(rf['f1'])})"), (9, 10, f3(EV["combined_or"]["f1"]), f"F1 when rules or ML flag (rules {f3(EV['rule_engine']['f1'])}, ML {f3(EV['ml_model']['f1'])})"),
                             (12, 13, f"{LAT['median_s']} s", "median full review of the demo PR")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, "Scores are on a generated Python corpus, so they are not comparable with the base paper's. The rule engine and ML model were scored on the same 1,500 held-out functions; the rule engine and the corpus generator were written by the same team, so the rule scores are optimistic.")

    # 16 output screens
    s = S[15]
    put_picture(s, crop("26_review_verdict.png", 0, 0, 270), (57, 128, 576, 410), remove_ids=(4, 5), name="Review verdict screenshot")
    put_picture(s, crop("12_codebase_ask.png", 110, 0, 270), (647, 128, 576, 410), remove_ids=(7, 8), name="Codebase assistant screenshot")
    for cid in (6, 9):
        shape(s, cid).top = px(556)
    set_paras(shape(s, 6), "Review result: BLOCK, risk 99, 15 security findings, 7 verified fixes", 11)
    set_paras(shape(s, 9), "Codebase assistant: where is authentication implemented?", 11)
    set_notes(s, "Real captures of the running application with the built-in demo pull request and demo repository.")

    # 17 testing
    s = S[16]
    set_paras(shape(s, 2), "Testing and observations")
    rows = [["Test group", "Tests", "Result"], ["Engine: rules, taint, autofix, metrics, diff, ML, SMOTE-Tomek, codebase", "10", "Passed"], ["API: auth, validation, review job, SARIF, codebase, lab", "7", "Passed"],
            ["Live API smoke test", "16", "Passed"], ["Browser UI flows (Playwright)", "22", "Passed"], ["Production build (tsc + vite)", "-", "Passed"]]
    set_table(shape(s, 18), rows, 13, widths=[0.6, 0.15, 0.25], header_size=13)
    fill(s, 5, ["17 pytest tests pass in about 10 s; 16 of 16 API checks and 22 of 22 browser flows pass with zero console errors.",
                f"The demo pull request gets risk {DEMO['score']} and BLOCK with {DEMO['findings']} findings; 7 of 7 patches verified by re-scan.",
                f"Rule engine F1 {f3(EV['rule_engine']['f1'])}, ML model {f3(EV['ml_model']['f1'])}, either {f3(EV['combined_or']['f1'])} on 1,500 held-out functions.",
                "Across five corpus seeds XGBoost F1 averages 0.842 (sd 0.006): the headline 0.851 is the best seed.",
                "Not done: real-PR precision, comparison with other scanners, load and user testing."], 16, bullet=True)
    set_notes(s, "All counts come from runs made on 18 October 2026. The LLM text mode and a real GitHub PR fetch were not exercised.")

    # 18 challenges
    s = S[17]
    cards = [(7, 8, "No labelled real data", "The base paper's C/C++ data is not available; a generated Python corpus with hard negatives and label noise is used and stated plainly."),
             (12, 13, "Rare vulnerable class", "Only 8.4% of functions are vulnerable; SMOTE-Tomek and a feature sweep were applied, and the ablation shows what each step buys."),
             (17, 18, "Partial code in a diff", "Hunks are padded to their line offsets; whole-file fixes exist only when the full file is given."),
             (22, 23, "Fixes that do not fix", "Each patch is applied to a copy and re-scanned before it is shown."),
             (27, 28, "Warning overload", "Findings carry confidence, severity and an in-diff flag so changed lines drive the verdict."),
             (32, 33, "Long reviews in a web page", "Reviews run as background jobs; the UI polls and shows each agent's message as it finishes.")]
    for tid, bid, ttl, body in cards:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 14)
    set_notes(s, "Six challenges and how each was handled.")

    # 19 next steps
    s = S[18]
    for sid, t in zip((5, 8, 11, 14), ["Real-PR evaluation", "User acceptance testing", "Final report", "Final presentation and demo"]):
        fill(s, sid, t, 16)
    fill(s, 15, ["Collect manually reviewed pull requests and measure the precision of each agent against them (objective 6, not yet measured).",
                 "Try the optional LLM explanation mode with a key and compare it with the offline text.",
                 "Compare the findings with another open-source scanner on the same code.",
                 "Document every diagram, test and result in the report."], 18, bullet=True)
    set_notes(s, "What remains: a labelled real-pull-request evaluation and user feedback, then the report and the final demo.")

    set_notes(S[19], "Thank you. Questions are welcome.")
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
