"""Build the Word documents 9, 10, 11, 12, 14, 15 and the full report 17 at the batch root.

    python scripts/docs_build.py            (system Python: needs python-docx; run scripts/docs_finish.py afterwards)
    python scripts/docs_build.py 9 17       (only some)
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
from doc_common import BATCH, BATCH_NAME, CHARTS, COLLEGE, DEPT, GUIDE, GUIDE_DESIG, HOD, PRINCIPAL, PRODUCT, STUDENTS, TITLE, YEAR  # noqa: E402
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
    d.p(DEPT, align="center", bold=True, size=13, space_after=2, line=1.15)
    d.p(f"CSDS-A   |   {BATCH_NAME}", align="center", size=11, space_after=6, line=1.15)
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
    d.p("The base paper [1] (Almutairy et al., IEEE Access, 2026) is a Saudi-law system with two parts: a retrieval-augmented legal chatbot over an Arabic corpus and "
        "a contract-analysis module that checks Arabic contracts against a checklist of essential clauses with an LLM. ClauseGuard keeps the idea of a "
        "jurisdiction-aware, Gemini-based contract reader and changes the target (English-language Indian contracts), the analysis (clause-level rules and "
        "clause combinations, a complexity grade) and the way the system is evaluated. The table lists the differences; none of them is claimed as new to the "
        "field, and the two systems are not compared numerically because their tasks, data and metrics differ.")
    d.table([["Element", "Base paper [1]", "ClauseGuard (this project)"],
             ["Jurisdiction and language", "Saudi law, Arabic contracts and questions", "Indian contract law (Contract Act 1872 ss. 27, 73, 74; Arbitration and Conciliation Act 1996; Consumer Protection Act 2019; Copyright Act 1957), English contracts"],
             ["Retrieval and corpus", "Custom Arabic legal corpus, GATE-AraBERT embeddings, Chroma and a FAISS index of about 18,400 vectors, cross-encoder re-ranking", "No legal corpus: 500 CUAD clause spans give 20 category centroids; Gemini embeddings (3,072-d) compared by cosine similarity in NumPy"],
             ["Contract analysis", "Checklist of essential clauses plus LLM-assisted semantic check of each clause", "8 deterministic regex rules tied to Indian statutes, 3 clause-combination patterns, a complexity grade A-F; the LLM only writes the explanation and safer wording"],
             ["Output", "Chatbot answers and a clause-by-clause assessment of the draft", "Per-contract grade, flagged clauses with reason, quoted provision and safer wording, clause graph, plain summary and obligations"],
             ["Evaluation", "150 legal questions (accuracy 98.67 % for Gemini 1.5 Flash); contract analysis judged qualitatively on sample outputs for 50 contract drafts", "Classification (top-1 79.2 %, top-3 97.9 % on 240 CUAD spans) and predatory-clause rules scored separately; an independent probe set (precision 0.79, recall 0.46); a 510-contract run; 68 automated tests"],
             ["Delivery", "Platform with chatbot and analysis modules", "Web application with accounts, upload, report, clause pages and graph, evaluation screen"],
             ["Evidence of limits", "Failure cases noted: retrieval across chunk boundaries and clause misclassification", "Measured limits: paraphrases missed by the rules, PDF line breaks losing 2 of 8 rules, thresholds that never fire, forced labels, 113.6 s upload"]],
            "What differs from the base paper", widths=[0.17, 0.38, 0.45], font=9.5)


# ---------------------------------------------------------------- the six chapter documents
def doc9(d):
    d.paras("This document describes how ClauseGuard works from end to end, why its algorithms were chosen, what is different from the base paper, and the "
            "contributions of the project. All figures are measured values from the project's own artefacts (`docs/REPORT_FACTS.md`).")
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
    d.paras("This document states what ClauseGuard covers and what it deliberately does not, the assumptions behind the design, and the honest limitations "
            "of the system and of the evidence for it.")
    I.sec_scope(d)
    d.h2("System Boundary")
    d.p("The two diagrams below show the boundary of ClauseGuard: what flows across it (context diagram) and who may do what inside it (use-case diagram).")
    D.diagram(d, "dfd0")
    D.diagram(d, "usecase")
    I.sec_limits(d)
    A.sec_feasibility_summary(d)
    T.sec_test_limits(d)
    R.sec_results_limits(d)


def doc11(d):
    d.paras("This document collects every design diagram of ClauseGuard. Each diagram was drawn from the real code, database models and routes and is followed "
            "by a paragraph that explains it. The diagrams were generated by `scripts/make_diagrams.py` with matplotlib.")
    d.table([["No.", "Diagram", "Shows"],
             ["1", "System architecture", "Browser, FastAPI routers and services, SQLite, local files, Gemini API"],
             ["2", "High-level workflow", "Ten steps from upload to report"],
             ["3", "DFD level 0", "Context: ClauseGuard and its external entities"],
             ["4", "DFD level 1", "Seven processes and five data stores"],
             ["5", "DFD level 2", "Expansion of the clause-classification process"],
             ["6", "Use-case diagram", "Actors and their use cases"],
             ["7", "Sequence diagram", "Uploading a contract and reading the report"],
             ["8", "ER diagram", "Four database tables"],
             ["9", "UML class diagram", "Entities, rule model and services"],
             ["10", "Algorithm flowcharts", "process_upload() and classify_clause()"]],
            "Diagrams in this document", widths=[0.08, 0.28, 0.64], font=9.5)
    names = {"architecture": "System Architecture", "workflow": "High-Level Workflow", "dfd0": "Data-Flow Diagram: Level 0",
             "dfd1": "Data-Flow Diagram: Level 1", "dfd2": "Data-Flow Diagram: Level 2", "usecase": "Use-Case Diagram",
             "sequence": "Sequence Diagram", "er": "Entity-Relationship Diagram", "uml": "UML Class Diagram", "flowchart": "Flowcharts of the Core Algorithms"}
    for key in D.ORDER:
        d.h2(names[key])
        D.diagram(d, key)


def doc12(d):
    d.paras("This document describes the design of ClauseGuard and how it was implemented: the architecture, the modules, the database schema, the API, key code "
            "walkthroughs, and the reasoning behind the main implementation decisions.")
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
    d.paras("This document reports the real results of the project: the evaluation of clause classification and of the predatory-clause rules, the corpus-scale run, "
            "every output screen with a caption, the success and failure cases, and the objectives measured against the outcomes. The shipped 40-clause test set was "
            "written together with the rules, so an independent probe set is reported next to it.")
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
    d.paras("This document concludes the project: what was achieved, the key findings, the known limitations, concrete future work, and the numbered list of references.")
    E.sec_conclusion_summary(d)
    E.sec_conclusion_objectives(d)
    E.sec_conclusion_findings(d)
    d.figure(CHARTS / "03_rules_two_test_sets.png", "Predatory-clause rules scored on the shipped test set and on the independent probe set", width=4.4)
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
    ("AI", "Artificial Intelligence"), ("API", "Application Programming Interface"), ("CC BY", "Creative Commons Attribution"), ("CSS", "Cascading Style Sheets"),
    ("CUAD", "Contract Understanding Atticus Dataset"), ("DFD", "Data-Flow Diagram"), ("DOCX", "Office Open XML Word document"), ("ER", "Entity-Relationship"),
    ("FK", "Foreign Key"), ("FR", "Functional Requirement"), ("HTTP", "Hypertext Transfer Protocol"), ("JSON", "JavaScript Object Notation"),
    ("JWT", "JSON Web Token"), ("kNN", "k-Nearest Neighbours"), ("LLM", "Large Language Model"), ("ML", "Machine Learning"), ("NFR", "Non-Functional Requirement"),
    ("NLP", "Natural Language Processing"), ("ORM", "Object-Relational Mapping"), ("PDF", "Portable Document Format"), ("PK", "Primary Key"),
    ("RAG", "Retrieval-Augmented Generation"), ("REST", "Representational State Transfer"), ("SLM", "Small Language Model"), ("SQL", "Structured Query Language"),
    ("TF-IDF", "Term Frequency-Inverse Document Frequency"), ("UI", "User Interface"), ("UML", "Unified Modeling Language"), ("URL", "Uniform Resource Locator"),
]

ABSTRACT = [
    "Individuals, freelancers and small businesses sign contracts without legal help, and such contracts can hide unfair termination terms, penalties, unlimited "
    "liability or one-sided arbitration. Professional review is costly, commercial analysis tools target US and EU law, and most research systems judge clauses "
    "one at a time. The base paper by Almutairy et al. (IEEE Access, 2026) builds a retrieval-augmented, Gemini-based legal assistant and contract checker for "
    "Saudi Arabia; for Indian contracts no comparable open, measured system was found in the literature survey.",
    "This project builds ClauseGuard, a web application that reads an uploaded PDF or DOCX contract, splits it into clauses with page numbers, assigns each clause one "
    "of 20 CUAD categories by comparing a Gemini embedding with category centroids, flags eight predatory patterns with deterministic rules tied to Indian statutes, "
    "detects three risky clause combinations in a clause graph, and scores complexity from readability, legal jargon, cross-references and sentence length into a grade "
    "A to F. Gemini then writes a plain-language reason, the triggering provision and safer wording for each flag, and a summary of the contract. The backend is FastAPI "
    "with SQLite and JWT authentication; the front end is React. The abstract named the Claude API, pgvector and Neo4j; the build uses Gemini, SQLite with NumPy and an "
    "in-memory NetworkX graph, and does not retrieve from a legal corpus.",
    "Classification and predatory detection are scored separately. On 240 held-out CUAD spans the classifier reaches top-1 accuracy 0.792 and top-3 accuracy 0.979 "
    "(0.800 when no training span comes from the same contract). The 40-clause test set, written with the rules, gives precision 1.00 and recall 0.94; on an independent "
    "probe set of 40 clauses the same rules reach precision 0.79 and recall 0.46, because paraphrases without the keyword are missed. The non-API pipeline processes "
    "all 510 CUAD contracts at 56 ms each. Further findings: the tie-break and unclassified thresholds never fire, a PDF loses two of eight rules that the identical "
    "DOCX triggers, and an upload with eight flags takes 113.6 s. Sixty-eight automated tests pass and five documented limits are marked as expected failures. "
    "The report states these limits and lists the work needed to move from a validated prototype to use on real Indian contracts.",
]
KEYWORDS = "Keywords: contract analysis, predatory clauses, Indian contract law, CUAD, text embeddings, clause graph, readability."


def cover(d):
    d.p(TITLE.upper(), align="center", bold=True, size=17, space_after=2, line=1.2)
    d.p(f"({PRODUCT})", align="center", italic=True, size=14, space_after=24, line=1.2)
    d.p("A project report submitted in partial fulfilment of the requirements for the award of the degree of", align="center", size=12, space_after=10, line=1.3)
    d.p("BACHELOR OF TECHNOLOGY", align="center", bold=True, size=14, space_after=2, line=1.2)
    d.p("in", align="center", size=12, space_after=2, line=1.2)
    d.p("COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)", align="center", bold=True, size=13, space_after=18, line=1.2)
    d.p("Submitted by", align="center", size=12, space_after=6, line=1.2)
    d.simple_table([[n, r] for n, r in STUDENTS], widths=[0.5, 0.5], font=12, borders=False)
    d.p(BATCH_NAME, align="center", size=12, space_after=14, line=1.3)
    d.p("Under the esteemed guidance of", align="center", size=12, space_after=2, line=1.2)
    d.p(GUIDE, align="center", bold=True, size=12, space_after=0, line=1.2)
    d.p(GUIDE_DESIG, align="center", size=12, space_after=22, line=1.2)
    d.p("[COLLEGE LOGO]", align="center", size=11, space_after=10, line=1.2)
    d.p(DEPT.upper(), align="center", bold=True, size=12, space_after=2, line=1.2)
    d.p(COLLEGE, align="center", bold=True, size=12, space_after=2, line=1.2)
    d.p("[COLLEGE ADDRESS / AFFILIATING UNIVERSITY]", align="center", size=11, space_after=2, line=1.2)
    d.p(YEAR, align="center", size=12, space_after=0, line=1.2)


def front_matter(d):
    names_rolls = ", ".join(f"{n} ({r})" for n, r in STUDENTS)
    d.d.paragraphs[-1].paragraph_format.page_break_before = False
    d.p("[COLLEGE LOGO]", align="center", size=11, space_after=2, line=1.2)
    d.p(COLLEGE, align="center", bold=True, size=13, space_after=2, line=1.2)
    d.p(DEPT.upper(), align="center", bold=True, size=12, space_after=14, line=1.2)
    d.front_heading("Certificate", page_break=False)
    d.p(f"This is to certify that the project report entitled \"{TITLE} ({PRODUCT})\" is a bonafide record of the work carried out by "
        f"{names_rolls}, in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer "
        f"Science and Engineering (Data Science), during the academic year {YEAR}, under my supervision.")
    d.p(" ", space_after=30)
    d.simple_table([[f"Project Guide\n{GUIDE}\n{GUIDE_DESIG}", f"Head of the Department\n{HOD}\nDepartment of Computer Science and Engineering (Data Science)", "External Examiner\n[NAME AND SIGNATURE]"]],
                   widths=[0.3, 0.4, 0.3], font=11, borders=False)
    d.front_heading("Declaration")
    d.p(f"We hereby declare that the project report entitled \"{TITLE} ({PRODUCT})\", submitted to the {DEPT}, {COLLEGE}, in partial "
        f"fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering "
        f"(Data Science), is a record of original work carried out by us under the guidance of {GUIDE}, {GUIDE_DESIG}. The results "
        f"embodied in this report have not been submitted to any other university or institution for the award of any degree or diploma.")
    d.p(" ", space_after=24)
    d.simple_table([[n, r] for n, r in STUDENTS], widths=[0.5, 0.5], font=12, borders=False)
    d.p("Place: [PLACE]", align="left", space_after=0)
    d.p("Date: [DATE]", align="left")
    d.front_heading("Acknowledgement")
    d.paras(f"We express our sincere gratitude to our project guide, {GUIDE}, {GUIDE_DESIG}, for valuable guidance, encouragement and "
            "constructive suggestions throughout this project.",
            f"We thank {HOD}, Head of the Department of Computer Science and Engineering (Data Science), for providing the facilities and support "
            f"needed to complete this work, and {PRINCIPAL}, Principal, {COLLEGE}, for the encouragement given to us.",
            "We thank the project coordinators and all faculty and staff members of the department for their help, and our families and "
            "friends for their constant support.",
            "We also acknowledge the authors of the base paper, Fayha Almutairy, Shahad Almutairi, Milaf Abdullah and Sara Salman, the creators of the Contract "
            "Understanding Atticus Dataset (Hendrycks, Burns, Chen and Ball) and The Atticus Project that released it under a CC BY 4.0 licence, and the authors and "
            "maintainers of the open-source software on which ClauseGuard is built, in particular FastAPI, SQLAlchemy, PyMuPDF, python-docx, NumPy, NetworkX, "
            "scikit-learn, React and Vite.")
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
    d.report = True
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
