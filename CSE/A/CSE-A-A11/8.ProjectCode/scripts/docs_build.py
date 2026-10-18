"""Build the Word documents 9, 10, 11, 12, 14, 15 and the full report 17 at the batch root.

    python scripts/docs_build.py            (system Python: needs python-docx; run scripts/docs_finish.py afterwards)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docx  # noqa: E402

import rc_analysis as A  # noqa: E402
import rc_design as D  # noqa: E402
import rc_end as E  # noqa: E402
import rc_intro as I  # noqa: E402
import rc_lit as L  # noqa: E402
import rc_method as M  # noqa: E402
import rc_results as R  # noqa: E402
import rc_test as T  # noqa: E402
from doc_common import (BATCH, BATCH_NAME, BEST, COLLEGE, DEPT, EV, GUIDE, GUIDE_DESIG, LAT, MODELS, PRODUCT, RET, SEEDS, STUDENTS, TITLE,  # noqa: E402
                        YEAR, f3)
from docxkit import Doc  # noqa: E402

NAMES = {
    9: "9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx",
    10: "10.SCOPE & LIMITATIONS.docx",
    11: "11. BLOCK DIAGRAMS ALL.docx",
    12: "12.DESIGN &IMPLEMENTATION.docx",
    14: "14.RESULTS.docx",
    15: "15.CONCLUSION&FUTURE SCOPE&REFERENCES.docx",
    17: "17.Final Document.docx",
}


def team_rows():
    return [["S.No.", "Student name", "Roll / hall ticket no."]] + [[str(i), n, r] for i, (n, r) in enumerate(STUDENTS, 1)]


def title_block(d, doc_title):
    d.p(COLLEGE, align="center", bold=True, size=12, space_after=2, line=1.15)
    d.p(DEPT, align="center", bold=True, size=13, space_after=2, line=1.15)
    d.p(f"CSE-A   |   {BATCH_NAME}", align="center", size=11, space_after=6, line=1.15)
    d.p(TITLE, align="center", bold=True, size=16, space_after=2, line=1.2)
    d.p(f"({PRODUCT})", align="center", italic=True, size=12, space_after=8, line=1.15)
    d.simple_table(team_rows(), widths=[0.12, 0.46, 0.42], font=10.5, bold_header=True)
    d.p(f"Under the guidance of: {GUIDE}, {GUIDE_DESIG}", align="center", size=11, space_after=6, line=1.3)
    p = d.p(doc_title, align="center", bold=True, size=15, space_after=10, line=1.2)
    p.paragraph_format.space_before = docx.shared.Pt(6)


def chapter_doc(number, doc_title, builder):
    d = Doc(f"{PRODUCT} - {doc_title.title()}", numbering="flat")
    d.header_footer()
    title_block(d, doc_title)
    builder(d)
    d.save(BATCH / NAMES[number])
    print("saved", NAMES[number])


def novelty(d):
    d.h2("Novelty Compared with the Base Paper")
    d.p("The base paper [1] predicts, offline, whether a C or C++ function is vulnerable from 14 source-code metrics, and classifies the type of "
        "vulnerability. AutoSecAI keeps that signal and moves it into the place where code is actually reviewed: the pull request. The table lists "
        "what differs; none of it is claimed as new to the field, and the system's accuracy figures are not comparable with the paper's because the "
        "language, the data and the class balance are different.")
    d.table([["Element", "Base paper [1]", "AutoSecAI (new here)"],
             ["Setting", "Offline classification of functions in 10 open-source C/C++ projects", "Inside a pull-request workflow: diff ingestion, per-function scoring of the changed code, verdict, report"],
             ["Language", "C / C++ (code property graph)", "Python AST for the metrics and the taint rules; regex rules for JavaScript, PHP and Java"],
             ["Metrics", "14 metrics M1-M14 from a code property graph", "Python analogues of the same families (M1-M11) plus three taint-oriented metrics M12-M14 (risky calls, string-built sinks, untrusted sources)"],
             ["Evidence beyond the score", "Feature importance only", "AST/taint rule engine with source-to-sink evidence; CWE and OWASP mapping; explanation, impact and remediation text"],
             ["Remediation", "Not addressed", "Auto-generated patches that are re-scanned and kept only if the finding disappears"],
             ["Decision", "Class label", "Risk score 0-100 and a merge verdict (APPROVE, REQUEST_CHANGES, BLOCK) from an explicit, documented rule"],
             ["Agents", "Single model pipeline", "Seven cooperating software agents with a visible trace; an optional LLM text layer, off by default"],
             ["Codebase context", "Not addressed", "Repository assistant: TF-IDF, concept scores and call-graph retrieval answer questions with evidence"],
             ["Interfaces", "Scripts", "FastAPI service with login, background jobs, exports (Markdown, SARIF, JSON, CSV) and a React web application"],
             ["Evidence", "Accuracy, precision, recall, F1 on real projects", f"Same metrics on a generated Python corpus, five-seed repeat, rule-engine-versus-model study, latency, retrieval test, 17 automated tests"]],
            "What is new compared with the base paper", widths=[0.2, 0.34, 0.46], font=9.5)


# ---------------------------------------------------------------- the six chapter documents
def doc9(d):
    d.paras("This document describes how AutoSecAI works from end to end, why its algorithms were chosen, what is new in it compared with the "
            "base paper, and the contributions of the project. All figures are measured values from the project's own artefacts "
            "(`docs/REPORT_FACTS.md`).")
    M.sec_method_overview(d)
    M.sec_dataset(d)
    M.sec_preprocessing(d)
    M.sec_algorithm_choice(d)
    M.sec_math(d)
    M.sec_model_training(d)
    L.sec_base_paper(d)
    novelty(d)
    I.sec_contrib(d)


def doc10(d):
    d.paras("This document states what AutoSecAI covers and what it deliberately does not, the assumptions behind the design, and the honest "
            "limitations of the system and of the evidence for it.")
    I.sec_scope(d)
    d.h2("System Boundary")
    d.p("The two diagrams below show the boundary of AutoSecAI: what flows across it (context diagram) and who may do what inside it (use-case diagram).")
    D.diagram(d, "dfd0")
    D.diagram(d, "usecase")
    I.sec_limits(d)
    A.sec_feasibility_summary(d)
    T.sec_test_limits(d)
    R.sec_results_limits(d)


def doc11(d):
    d.paras("This document collects every design diagram of AutoSecAI. Each diagram was drawn from the real code, the database tables and the routes "
            "and is followed by a paragraph that explains it. The diagrams were generated by `scripts/make_diagrams.py` with matplotlib.")
    d.table([["No.", "Diagram", "Shows"],
             ["1", "System architecture", "Layers: browser, React web app, FastAPI backend, engine modules, storage, optional external services"],
             ["2", "High-level workflow", "Ten steps from sign-in to the review, plus the codebase and Model Lab paths"],
             ["3", "DFD level 0", "Context: AutoSecAI and its external entities"],
             ["4", "DFD level 1", "Six processes and six data stores"],
             ["5", "DFD level 2", "Expansion of the seven-agent review process"],
             ["6", "Use-case diagram", "Actors and their use cases"],
             ["7", "Sequence diagram", "Starting a review, polling the job and reading the result"],
             ["8", "ER diagram", "Two SQLite databases and the JSON structure of a review"],
             ["9", "UML class diagram", "Domain types, engine classes and the backend job table"],
             ["10", "Algorithm flowchart", "Control flow of review_changes() down to the verdict"]],
            "Diagrams in this document", widths=[0.08, 0.28, 0.64], font=9.5)
    names = {"architecture": "System Architecture", "workflow": "High-Level Workflow", "dfd0": "Data-Flow Diagram: Level 0",
             "dfd1": "Data-Flow Diagram: Level 1", "dfd2": "Data-Flow Diagram: Level 2", "usecase": "Use-Case Diagram",
             "sequence": "Sequence Diagram", "er": "Entity-Relationship Diagram", "uml": "UML Class Diagram", "flowchart": "Flowchart of the Core Algorithm"}
    for key in D.ORDER:
        d.h2(names[key])
        D.diagram(d, key)


def doc12(d):
    d.paras("This document describes the design of AutoSecAI and how it was implemented: the architecture, the modules, the database schema, "
            "the API, key code walkthroughs, and the reasoning behind the main implementation decisions.")
    D.sec_arch(d)
    D.sec_modules(d)
    D.sec_database(d)
    M.sec_app_arch(d)
    M.sec_api(d)
    M.sec_walkthrough(d)
    E.sec_decisions(d)
    M.sec_security(d)
    D.sec_ui(d)
    M.sec_install(d)


def doc14(d):
    d.paras("This document reports the real results of the project: the evaluation of the vulnerability model and the rule engine, the performance "
            "of the review pipeline, every output screen with a caption, the success and failure cases, and the objectives measured against the outcomes. "
            "The model was trained on a generated corpus, so the figures describe how the pipeline behaves on that corpus, not on real-world pull requests.")
    R.sec_engine_results(d)
    R.sec_product_results(d)
    T.sec_functional(d)
    T.sec_performance(d)
    R.sec_screens(d, all_screens=True)
    R.sec_samples(d)
    R.sec_comparison(d)
    R.sec_success_failure(d)
    R.sec_results_limits(d)
    R.sec_objectives(d)


def doc15(d):
    d.paras("This document concludes the project: what was achieved, the key findings, the known limitations, concrete future work, and "
            "the numbered list of references.")
    E.sec_conclusion_summary(d)
    E.sec_conclusion_objectives(d)
    E.sec_conclusion_findings(d)
    E.sec_conclusion_applications(d)
    E.sec_conclusion_limits(d)
    d.h2("Future Scope")
    d.p("The items below follow from the limitations and from the gaps found in the literature survey.")
    E.sec_future_improvements(d)
    E.sec_future_features(d)
    E.sec_future_deploy(d)
    E.sec_future_research(d)
    d.h_plain("REFERENCES", level=1).paragraph_format.page_break_before = True
    E.sec_references(d, heading=False)


# ---------------------------------------------------------------- the full report
ABBREVIATIONS = [
    ("AI", "Artificial Intelligence"), ("API", "Application Programming Interface"), ("AST", "Abstract Syntax Tree"),
    ("AUC", "Area Under the ROC Curve"), ("CPU", "Central Processing Unit"), ("CSV", "Comma-Separated Values"),
    ("CWE", "Common Weakness Enumeration"), ("DFD", "Data-Flow Diagram"), ("ER", "Entity-Relationship"),
    ("FN / FP", "False Negative / False Positive"), ("FR", "Functional Requirement"), ("HTTP", "Hypertext Transfer Protocol"),
    ("JSON", "JavaScript Object Notation"), ("JWT", "JSON Web Token"), ("KNN", "k-Nearest Neighbours"), ("LLM", "Large Language Model"),
    ("ML", "Machine Learning"), ("NFR", "Non-Functional Requirement"), ("OWASP", "Open Worldwide Application Security Project"),
    ("PR", "Pull Request"), ("RF", "Random Forest"), ("REST", "Representational State Transfer"), ("ROC", "Receiver Operating Characteristic"),
    ("SARIF", "Static Analysis Results Interchange Format"), ("SMOTE", "Synthetic Minority Over-sampling Technique"),
    ("SQL", "Structured Query Language"), ("SVM", "Support Vector Machine"), ("TF-IDF", "Term Frequency - Inverse Document Frequency"),
    ("TP / TN", "True Positive / True Negative"), ("UI", "User Interface"), ("UML", "Unified Modeling Language"),
    ("XGBoost", "Extreme Gradient Boosting"), ("XSS", "Cross-Site Scripting"),
]

ABSTRACT = [
    "Modern software teams merge many pull requests every week, and each one can introduce a vulnerability such as SQL injection or cross-site "
    "scripting. Manual review is slow, its security coverage depends on who happens to review, static analysers return long lists of warnings that "
    "are mostly noise, and a reviewer judging a small change rarely has the context of a large codebase. The base paper by Abbasi and Shameli-Sendi "
    "(IEEE Access, 2026) shows that 14 source-code metrics can predict which C or C++ functions are vulnerable, but it works offline on whole "
    "projects and does not explain findings or propose fixes.",
    "This project builds AutoSecAI, an autonomous pull-request analyser. The changed files are extracted from a pasted diff, two file versions, a "
    "GitHub pull-request link or uploaded files. Seven cooperating agents then run: ingestion, an AST and taint static analysis, a machine-learning "
    "risk agent that scores each changed function with the metric model of the base paper (adapted to Python), a reasoner that explains each "
    "finding with its CWE and OWASP class, impact and source-to-sink flow, a remediation agent whose patches are re-scanned before they are "
    "offered, a quality reviewer and a judge that de-duplicates findings and issues a risk score and a merge verdict. A codebase assistant answers "
    "natural-language questions about a repository with evidence, and a Model Lab shows how the model was built. A FastAPI service with login "
    "and background jobs and a React web application deliver all of this; an optional large-language-model layer for the wording is off by default.",
    f"Because real labelled Python vulnerability data was not available, the model is trained on a generated corpus of 6,000 functions of which "
    f"501 are vulnerable. On 1,500 held-out functions the stored {BEST} model reaches F1 {f3(MODELS[BEST]['f1'])} (precision {f3(MODELS[BEST]['precision'])}, "
    f"recall {f3(MODELS[BEST]['recall'])}); over five independently generated corpora its mean F1 is {f3(SEEDS['summary']['XGBoost|f1']['mean'])}. The rule "
    f"engine and the model are complementary: flagging a function when either reports it gives F1 {f3(EV['combined_or']['f1'])}. The built-in demo "
    f"pull request is reviewed in a median of {LAT['median_s']:.2f} s and receives the verdict BLOCK with 15 security findings. The codebase assistant "
    f"ranks the expected file first for {RET['top1']} of {RET['questions']} test questions. Seventeen automated tests, a sixteen-step API smoke test and "
    "twenty-two browser flows pass. The corpus is synthetic, no labelled set of real pull requests was available so precision on real reviews is "
    "unknown, the optional language-model layer was not evaluated and no numeric comparison with the base paper is valid.",
]
KEYWORDS = ("Keywords: multi-agent review, pull request, automated vulnerability detection, code quality, AST static analysis, codebase "
            "intelligence, graph-based retrieval, software security.")


def cover(d):
    d.p(TITLE.upper(), align="center", bold=True, size=16, space_after=2, line=1.2)
    d.p(f"({PRODUCT})", align="center", italic=True, size=14, space_after=24, line=1.2)
    d.p("A project report submitted in partial fulfilment of the requirements for the award of the degree of", align="center", size=12, space_after=10, line=1.3)
    d.p("BACHELOR OF TECHNOLOGY", align="center", bold=True, size=14, space_after=2, line=1.2)
    d.p("in", align="center", size=12, space_after=2, line=1.2)
    d.p("COMPUTER SCIENCE AND ENGINEERING", align="center", bold=True, size=13, space_after=18, line=1.2)
    d.p("Submitted by", align="center", size=12, space_after=6, line=1.2)
    d.simple_table([[n, r] for n, r in STUDENTS], widths=[0.5, 0.5], font=12, borders=False)
    d.p(BATCH_NAME, align="center", size=12, space_after=14, line=1.3)
    d.p("Under the esteemed guidance of", align="center", size=12, space_after=2, line=1.2)
    d.p(GUIDE, align="center", bold=True, size=12, space_after=0, line=1.2)
    d.p(GUIDE_DESIG, align="center", size=12, space_after=22, line=1.2)
    d.p("[COLLEGE LOGO]", align="center", size=11, space_after=10, line=1.2)
    d.p(DEPT.upper(), align="center", bold=True, size=12, space_after=2, line=1.2)
    d.p(COLLEGE.upper(), align="center", bold=True, size=12, space_after=2, line=1.2)
    d.p("[COLLEGE ADDRESS / AFFILIATING UNIVERSITY]", align="center", size=11, space_after=2, line=1.2)
    d.p(YEAR, align="center", size=12, space_after=0, line=1.2)


def front_matter(d):
    names_rolls = ", ".join(f"{n} ({r})" for n, r in STUDENTS)
    d.d.paragraphs[-1].paragraph_format.page_break_before = False
    d.p("[COLLEGE LOGO]", align="center", size=11, space_after=2, line=1.2)
    d.p(COLLEGE.upper(), align="center", bold=True, size=13, space_after=2, line=1.2)
    d.p(DEPT.upper(), align="center", bold=True, size=12, space_after=14, line=1.2)
    d.front_heading("Certificate", page_break=False)
    d.p(f"This is to certify that the project report entitled \"{TITLE} ({PRODUCT})\" is a bonafide record of the work carried out by "
        f"{names_rolls}, in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer "
        f"Science and Engineering, during the academic year {YEAR}, under my supervision.")
    d.p(" ", space_after=30)
    d.simple_table([[f"Project Guide\n{GUIDE}\n{GUIDE_DESIG}", "Head of the Department\n[HOD NAME]\nDepartment of Computer Science and Engineering", "External Examiner\n[NAME AND SIGNATURE]"]],
                   widths=[0.3, 0.4, 0.3], font=11, borders=False)
    d.front_heading("Declaration")
    d.p(f"We hereby declare that the project report entitled \"{TITLE} ({PRODUCT})\", submitted to the {DEPT}, {COLLEGE}, in partial "
        f"fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, "
        f"is a record of original work carried out by us under the guidance of {GUIDE}, {GUIDE_DESIG}. The results "
        f"embodied in this report have not been submitted to any other university or institution for the award of any degree or diploma.")
    d.p(" ", space_after=24)
    d.simple_table([[n, r] for n, r in STUDENTS], widths=[0.5, 0.5], font=12, borders=False)
    d.p("Place: [PLACE]", align="left", space_after=0)
    d.p("Date: [DATE]", align="left")
    d.front_heading("Acknowledgement")
    d.paras(f"We express our sincere gratitude to our project guide, {GUIDE}, {GUIDE_DESIG}, for valuable guidance, encouragement and "
            "constructive suggestions throughout this project.",
            "We thank [HOD NAME], Head of the Department of Computer Science and Engineering, for providing the facilities and support "
            f"needed to complete this work, and [PRINCIPAL NAME], Principal, {COLLEGE}, for the encouragement given to us.",
            "We thank the project coordinators and all faculty and staff members of the department for their help, and our families and "
            "friends for their constant support.",
            "We also acknowledge the authors of the base paper, Behzad Khalaji Emamzadeh Abbasi and Alireza Shameli-Sendi, whose work on "
            "source-code metrics for vulnerability prediction is the starting point of this project, and the authors and maintainers of the "
            "open-source software on which AutoSecAI is built, in particular Python, FastAPI, scikit-learn, XGBoost, NetworkX, React, Vite and Tailwind CSS.")
    d.p(" ")
    for n, _ in STUDENTS:
        d.p(n, align="right", space_after=0, line=1.15)
    d.front_heading("Abstract")
    for t in ABSTRACT:
        d.p(t)
    d.p(KEYWORDS, italic=True)
    d.toc()
    d.lof()
    d.lot()
    d.front_heading("List of Abbreviations")
    d.simple_table([["Abbreviation", "Expansion"]] + [[a, b] for a, b in ABBREVIATIONS], widths=[0.22, 0.78], font=11, bold_header=True)


def full_report():
    d = Doc(f"{PRODUCT} - {TITLE}", numbering="chapter")
    d.report = True  # the full report leaves out figures and listings that repeat another chapter
    cover(d)
    d.new_section()
    d.number_format("lowerRoman", 1)
    d.header_footer()
    front_matter(d)
    d.new_section()
    d.number_format("decimal", 1)
    d.header_footer()

    d.h1("Introduction")
    for f in (I.sec_domain, I.sec_motivation, I.sec_problem, I.sec_need, I.sec_objectives, I.sec_scope, I.sec_contrib, I.sec_limits, I.sec_organisation):
        f(d)
    d.h1("Literature Survey")
    for f in (L.sec_lit_overview, L.sec_base_paper, L.sec_related, L.sec_lit_algorithms, L.sec_lit_strengths, L.sec_gap):
        f(d)
    d.h1("Feasibility Study")
    for f in (A.sec_feasibility_technical, A.sec_feasibility_economic, A.sec_feasibility_operational, A.sec_feasibility_schedule, A.sec_feasibility_summary):
        f(d)
    d.h1("System Requirements and Analysis")
    for f in (A.sec_existing, A.sec_proposed, A.sec_requirements_functional, A.sec_requirements_nonfunctional, A.sec_requirements_platform, A.sec_roles):
        f(d)
    d.h1("System Design")
    for f in (D.sec_arch, D.sec_workflow, D.sec_dfd, D.sec_uml, D.sec_database, D.sec_modules, D.sec_ui):
        f(d)
    d.h1("Methodology and Software Implementation")
    for f in (M.sec_method_overview, M.sec_dataset, M.sec_preprocessing, M.sec_algorithm_choice, M.sec_math, M.sec_model_training, M.sec_app_arch,
              M.sec_walkthrough, E.sec_decisions, M.sec_api, M.sec_security, M.sec_install):
        f(d)
    d.h1("System Testing")
    for f in (T.sec_test_strategy, T.sec_unit, T.sec_integration, T.sec_functional, T.sec_security_test, T.sec_validation, T.sec_performance, T.sec_uat, T.sec_test_limits):
        f(d)
    d.h1("Results and Output Screens")
    R.sec_screens(d)
    for f in (R.sec_engine_results, R.sec_product_results, R.sec_comparison, R.sec_samples, R.sec_success_failure, R.sec_results_limits, R.sec_objectives):
        f(d)
    d.h1("Conclusion")
    for f in (E.sec_conclusion_summary, E.sec_conclusion_objectives, E.sec_conclusion_findings, E.sec_conclusion_applications, E.sec_conclusion_limits):
        f(d)
    d.h1("Future Scope")
    for f in (E.sec_future_improvements, E.sec_future_features, E.sec_future_deploy, E.sec_future_research):
        f(d)
    d.h1("References", chapter=False)
    E.sec_references(d, heading=False)
    d.appendix_h1("A", "Important Code")
    E.appendix_a(d)
    d.appendix_h1("B", "Installation and User Guide")
    E.appendix_b(d)
    d.appendix_h1("C", "Additional Screens")
    E.appendix_c(d)
    d.save(BATCH / NAMES[17])
    print("saved", NAMES[17])


if __name__ == "__main__":
    which = sys.argv[1:] or ["9", "10", "11", "12", "14", "15", "17"]
    table = {"9": ("METHODOLOGY, NOVELTY AND KEY CONTRIBUTIONS", doc9), "10": ("SCOPE AND LIMITATIONS", doc10), "11": ("BLOCK DIAGRAMS", doc11),
             "12": ("DESIGN AND IMPLEMENTATION", doc12), "14": ("RESULTS", doc14), "15": ("CONCLUSION, FUTURE SCOPE AND REFERENCES", doc15)}
    for w in which:
        if w == "17":
            full_report()
        else:
            chapter_doc(int(w), *table[w][:1], table[w][1])
