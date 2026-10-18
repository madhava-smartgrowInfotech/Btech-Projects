"""Build 7.Review_1_PPT.pptx from D:\\abstracts\\Templates\\Review_1_PPT.pptx (16 slides)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (fill, put_picture, replace_chart, replace_everywhere, set_notes, set_paras, set_table, shape, style_chart, table_size)  # noqa: E402
from doc_common import BASE_PAPER, BATCH, BATCH_NAME, COLLEGE, DEPT, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, STUDENTS, TITLE, YEAR  # noqa: E402
from pptx import Presentation  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_1_PPT.pptx"
OUT = BATCH / "7.Review_1_PPT.pptx"
KEYWORDS = "pull request review, vulnerability detection, source-code metrics, multi-agent, code quality"


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    replace_everywhere(prs, {"The Hidden Risk of Social Media": PRODUCT})
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Review 1", TITLE, "Batch A11", KEYWORDS
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A11"

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    fill(s, 3, TITLE.split(": ",1)[1], 26)
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  {BATCH_NAME}  \u00b7  {YEAR}"], 12)
    set_notes(s, "Review 1 covers problem identification and research for AutoSecAI, an autonomous pull-request reviewer for security, vulnerability detection and code quality.")

    # 2 contents
    set_notes(S[1], "Nine parts: the abstract, the base paper and related work, the existing approaches and their limits, the gap, the problem statement and objectives, the approach, expected outcomes and references.")

    # 3 abstract
    s = S[2]
    set_paras(shape(s, 2), "Abstract: a security reviewer for every pull request")
    fill(s, 8, "Modern teams merge many pull requests, and manual review for flaws such as SQL injection or XSS is slow and inconsistent. Static analysers add many low-value warnings, and newcomers struggle to find their way around a large codebase.", 17)
    fill(s, 13, "AutoSecAI extracts the changed files, runs AST static analysis, scores each changed function with the base paper's source-code metrics, and lets seven cooperating agents explain every finding, propose a verified fix and issue a verdict. A codebase assistant answers questions about the repository.", 17)
    fill(s, 18, "A web application: paste or upload a diff, or give a GitHub PR link; read the verdict, findings and patches; export Markdown, SARIF, JSON or CSV; ask the repository where authentication or routing lives.", 17)
    set_notes(s, "The abstract in one slide: the review problem, the multi-agent idea built on a metric-based risk model, and the deliverable.")

    # 4 base paper
    s = S[3]
    fill(s, 5, BASE_PAPER, 14)
    set_paras(shape(s, 7), "Method")
    fill(s, 8, "14 source-code metrics are computed per C/C++ function from a code property graph; seven feature-selection methods pick the five most useful; SmoteTomek balances the classes; Min-Max scaling; nine ML models, with Random Forest best; the same metrics also classify the vulnerability type.", 15)
    set_paras(shape(s, 10), "Data and reported results")
    fill(s, 11, "21,759 functions from 10 open-source projects, 275 vulnerable (1.26%). Random Forest: accuracy 0.96, precision 0.948, recall 0.974, F1 0.961. The most useful metrics: M5, M6, M1, M9 and M11.", 15)
    set_paras(shape(s, 13, ), "What we adopt and what we change")
    fill(s, 14, "We adopt the 14-metric idea, the selection, balancing and nine-model pipeline, and reproduce it for Python. We move the signal into the live pull-request workflow, add taint-aware static analysis, agentic explanations and verified patches. The paper's own future work: other languages than C and C++.", 15)
    set_notes(s, "The base paper predicts vulnerable functions offline from code metrics. AutoSecAI applies that signal inside the pull-request workflow and adds explanation and remediation around it.")

    # 5 literature survey
    s = S[4]
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Abbasi and Shameli-Sendi, 2026 (base) [1]", "14 code metrics, feature selection, SmoteTomek, 9 ML models", "21,759 C/C++ functions, 10 projects", "Random Forest F1 0.961, accuracy 0.96"],
            ["Zhang et al., 2026 [2]", "Sphinx: structured data generation, checklist benchmark, checklist-reward training for LLM PR review", "Pull-request review comments", "Up to 40% higher checklist coverage than baselines"],
            ["CNN-LSTM hybrid, 2025 [3]", "Deep hybrid vulnerability detection", "Not retrieved", "Not retrieved (listed in batch survey)"],
            ["Real-time AI code security auditing, 2025 [4]", "Automated detection and remediation", "Not retrieved", "Not retrieved (listed in batch survey)"],
            ["Multi-modal framework with meta-learning, 2025 [5]", "Code simplification and meta-learning", "Not retrieved", "Not retrieved (listed in batch survey)"],
            ["DcodeBERT, 2024 [6]", "Automatic vulnerability detection and repair", "Not retrieved", "Not retrieved (listed in batch survey)"]]
    sz = table_size(rows, 1164, 470, [0.27, 0.33, 0.18, 0.22], 16, 9)
    set_table(shape(s, 6), rows, sz, header_size=sz)
    set_notes(s, "[1] and [2] were read; [3] to [6] are listed in the batch literature survey but could not be retrieved, so no results are claimed for them.")

    # 6 supporting evidence
    s = S[5]
    set_paras(shape(s, 2), "Supporting evidence: metrics predict vulnerable code")
    ch = replace_chart(s, 4, ["Accuracy", "Precision", "Recall", "F1"], [("Random Forest [1]", [0.96, 0.948, 0.974, 0.961])], number_format="0.000")
    style_chart(ch, "Base paper [1]: Random Forest on 10 real C/C++ projects", ["6D5BD0"], number_format="0.000", legend=False, label_pt=12, axis_title="score")
    ch.value_axis.maximum_scale = 1.05
    set_paras(shape(s, 8), "Takeaway")
    fill(s, 9, "Fourteen interpretable metrics are enough to rank vulnerable functions well: the base paper reports F1 0.961 with Random Forest, and the metrics that matter most are about control flow, nesting and arguments [1].", 14)
    set_paras(shape(s, 13), "Caveat")
    fill(s, 14, "Published figures on C/C++ projects with a different class balance. They motivate our design; they are not our results, which are measured later on a generated Python corpus.", 14)
    set_notes(s, "These numbers are published by the base paper, not ours. AutoSecAI's own measurements come in Reviews 2 and 3.")

    # 7 existing system
    s = S[6]
    set_paras(shape(s, 2), "Existing system and current approaches")
    for sid, t in zip((5, 8, 11, 14, 17, 20), ["Developer opens a pull request", "Reviewer reads the diff", "Linter / static tool runs", "Reviewer comments", "Author fixes, re-review", "Merge"]):
        fill(s, sid, t, 14)
    set_paras(shape(s, 24), "Manual review")
    fill(s, 25, "Reviewers read diffs by hand. It is slow, depends on who reviews and on their security knowledge, and subtle injection or access-control flaws are routinely missed.", 17)
    set_paras(shape(s, 29), "Static analysers on their own")
    fill(s, 30, "Tools catch known patterns but report large volumes of low-value warnings without saying why a change is risky or how to fix it, and they do not see the wider codebase.", 17)
    set_notes(s, "How a pull request is reviewed today, as stated in the batch introduction.")

    # 8 limitations
    s = S[7]
    set_paras(shape(s, 2), "Limitations of existing methods")
    for tid, bid, ttl, body in [
            (7, 8, "Does not scale", "Manual review cannot keep pace with the number of pull requests a team merges."),
            (12, 13, "Uneven security depth", "Whether a flaw is found depends on whether the reviewer happens to have security expertise."),
            (17, 18, "Warning overload", "Static analysers flag many items that are not real problems, so developers stop reading them."),
            (22, 23, "No codebase context", "A small diff is judged without knowing how the rest of the repository works.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 18)
    set_notes(s, "Four limitations taken from the problem statement of the batch.")

    # 9 research gap
    s = S[8]
    gaps = [("Workflow", "Metric-based vulnerability prediction is studied offline [1]; it is not applied to each pull request as it arrives."),
            ("Explanation", "Scanners and models return a label or a warning, not why a change is risky, its impact or a fix."),
            ("Remediation", "Few tools offer a patch and check that the patch actually removes the finding."),
            ("Context", "Review comments rarely reflect the rest of the repository; newcomers cannot ask where a feature lives."),
            ("Evidence", "No repeatable measurement joins static rules, a metric model and agent output on the same code.")]
    for (lid, tid), (lab, txt) in zip([(5, 6), (8, 9), (11, 12), (14, 15), (17, 18)], gaps):
        set_paras(shape(s, lid), lab)
        fill(s, tid, txt, 18)
    set_notes(s, "The batch survey states the gap: the signal is predicted offline, and it must be applied inside the live pull-request workflow together with agentic review that explains each finding.")

    # 10 problem statement
    s = S[9]
    fill(s, 5, "Given a pull request (a diff, two file versions, a GitHub PR link or uploaded files), find security flaws and quality problems in the changed code, rank functions by vulnerability likelihood with source-code metrics, explain each finding with its impact, propose a fix that is verified by re-scanning, and give a merge verdict; and let developers ask natural-language questions about the repository, in an application whose behaviour is measured.", 22)
    set_paras(shape(s, 8), "Diff, PR link, files, questions")
    set_paras(shape(s, 11), "Verdict, findings, patches, answers")
    set_paras(shape(s, 14), "Risk score and exports (SARIF, MD)")
    set_notes(s, "Inputs are the change set and the user's questions; outputs are the verdict, explained findings, verified patches and cited answers.")

    # 11 objectives
    s = S[10]
    fill(s, 4, ["Extract changed files and diff context automatically when a pull request is opened.",
                "Compute source-code metrics for changed files and use them to rank vulnerability likelihood.",
                "Perform AST-based static analysis to detect injection, access-control and validation flaws.",
                "Deploy multiple agents covering security, code quality and maintainability concerns.",
                "Retrieve related code from the repository so review comments reflect the wider codebase.",
                "Post consolidated review comments and evaluate precision against manually reviewed pull requests."], 26, bullet=True)
    set_notes(s, "The six objectives from the batch document. The last one, precision against manually reviewed pull requests, needs a labelled set that does not exist yet and is reported later as a gap.")

    # 12 proposed approach
    s = S[11]
    for tid, bid, ttl, body in [
            (7, 8, "Ingest the change", "Diff, two versions, GitHub PR, files, zip or folder become changed files with line ranges."),
            (12, 13, "Static + ML risk", "AST and taint rules plus the 14-metric model score every changed function."),
            (17, 18, "Explain and fix", "CWE/OWASP-mapped explanation, impact, safe example, patch re-scanned to verify."),
            (22, 23, "Judge and report", "De-duplicate, risk score 0-100, verdict BLOCK / REQUEST_CHANGES / APPROVE.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_paras(shape(s, 27), "Web application and codebase assistant")
    fill(s, 28, "React + FastAPI: live agent progress, findings, charts, exports and history; a retrieval assistant that answers where authentication, routing or the UI is implemented.", 14)
    set_notes(s, "Seven software agents cooperate: ingestion, static analysis, ML risk, reasoner, remediation, quality and judge; an optional language-model layer can reword explanations.")

    # 13 architecture
    s = S[12]
    put_picture(s, DIAG / "01_system_architecture.png", (270, 124, 740, 475), remove_ids=(4,), name="System architecture diagram")
    set_paras(shape(s, 5), "Proposed architecture: React app, FastAPI backend, seven-agent engine, SQLite and model artefacts, optional GitHub and LLM calls")
    set_notes(s, "The browser talks to the React app, which proxies /api to FastAPI. The engine runs locally; GitHub and an optional language-model key are the only external calls.")

    # 14 expected outcomes
    s = S[13]
    for tid, bid, ttl, body in [
            (7, 8, "Risk ranking", "Each changed function gets a vulnerability probability and a likely type."),
            (12, 13, "Explained findings", "Every finding carries a CWE, impact, flow and remediation, not a bare warning."),
            (17, 18, "Verified patches", "Fixes are offered only when a re-scan shows the finding is gone."),
            (22, 23, "Codebase answers", "Natural-language questions return the files and functions that implement a feature."),
            (27, 28, "Usable application", "Sign-in, history, exports and a clear verdict for each pull request."),
            (32, 33, "Honest evaluation", "Model scores, rule-engine scores and speed measured; gaps reported plainly.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 17)
    set_notes(s, "Outcomes are stated as targets here and are measured in the next reviews.")

    # 15 references
    s = S[14]
    fill(s, 4, [f"[{i}] {r}" for i, r in enumerate(REFERENCES[:10], 1)], 15, min_pt=8.5, bullet=True, gap_pt=3)
    set_notes(s, "References [1] to [12]; the full list is in the report.")

    set_notes(S[15], "Thank you. Questions are welcome.")
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
