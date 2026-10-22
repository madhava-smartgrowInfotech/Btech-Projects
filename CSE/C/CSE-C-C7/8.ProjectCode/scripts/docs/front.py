"""Front matter of the full report: cover, certificate, declaration, acknowledgement, abstract, abbreviations."""

import os

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from . import facts as F
from .kit import add_runs

def _letterhead(d):
    """The report template has no banner image: its pages open with these two placeholder lines."""
    d.p("[COLLEGE LOGO]", align="center", size=12, space_after=2)
    d.p(F.COLLEGE, align="center", size=14, bold=True, space_after=10)


def cover(d):
    _letterhead(d)
    d.spacer(8)
    d.p(F.TITLE.upper(), align="center", size=22, bold=True, space_after=8)
    d.p(f"{F.PRODUCT}: a hybrid, explainable course recommendation system with learning-path guidance", align="center", size=13, italic=True, space_after=14)
    d.p("A project report submitted in partial fulfilment of the requirements for the award of the degree of", align="center", size=12, space_after=6)
    d.p("BACHELOR OF TECHNOLOGY", align="center", size=15, bold=True, space_after=2)
    d.p("in", align="center", size=12, space_after=2)
    d.p("COMPUTER SCIENCE AND ENGINEERING", align="center", size=15, bold=True, space_after=12)
    d.p("Submitted by", align="center", size=12, bold=True, space_after=4)
    rows = [[n, r] for n, r in F.STUDENTS]
    t = d.doc.add_table(rows=len(rows), cols=2)
    t.alignment = 1
    for i, (n, r) in enumerate(rows):
        for j, v in enumerate((n, r)):
            c = t.rows[i].cells[j]
            c.text = ""
            par = c.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.15
            par.paragraph_format.space_after = Pt(2)
            add_runs(par, v, 12, True)
            c.width = Inches(3.2 if j == 0 else 1.6)
    d.spacer(6)
    d.p(f"Batch {F.BATCH_NO} ({F.SECTION})", align="center", size=12, space_after=10)
    d.p("Under the esteemed guidance of", align="center", size=12, space_after=2)
    d.p(F.GUIDE, align="center", size=13, bold=True, space_after=0)
    d.p(F.GUIDE_DESIGNATION, align="center", size=12, space_after=12)
    d.p("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", align="center", size=13, bold=True, space_after=2)
    d.p(F.COLLEGE.upper(), align="center", size=12, bold=True, space_after=2)
    d.p(F.CITY, align="center", size=11, space_after=2)
    d.p(f"Academic year {F.YEAR}", align="center", size=12, space_after=0)


def certificate(d):
    d.h1("CERTIFICATE", page_break=False)
    _letterhead(d)
    d.p(f"This is to certify that the project report entitled **\"{F.TITLE}\"** is a bonafide record of the work carried out by "
        + ", ".join(f"**{n}** ({r})" for n, r in F.STUDENTS)
        + f", in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, "
          f"during the academic year {F.YEAR}, under my supervision.")
    d.spacer(30)
    t = d.doc.add_table(rows=3, cols=3)
    cells = [("Project Guide", F.GUIDE, F.GUIDE_DESIGNATION), ("Head of the Department", F.HOD, f"{F.DEPT}"), ("Principal", F.PRINCIPAL, F.COLLEGE)]
    for j, (a, b, c) in enumerate(cells):
        for i, v in enumerate((a, b, c)):
            cell = t.rows[i].cells[j]
            cell.text = ""
            par = cell.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.15
            add_runs(par, v, 11, i == 0)
    d.spacer(30)
    d.p("External Examiner: [NAME AND SIGNATURE]", align="left")
    d.p(f"Place: {F.CITY}", align="left", space_after=0)
    d.p("Date: [DATE]", align="left")


def declaration(d):
    d.h1("DECLARATION")
    d.p(f"We hereby declare that the project report entitled **\"{F.TITLE}\"**, submitted to the {F.DEPT}, {F.COLLEGE}, in partial fulfilment of the "
        f"requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, is a record of original work carried out by us under the "
        f"guidance of {F.GUIDE}, {F.GUIDE_DESIGNATION}. The results embodied in this report have not been submitted to any other university or institution for the award of any degree or diploma.")
    d.spacer(24)
    for n, r in F.STUDENTS:
        d.p(f"{n}   {r}", align="right", space_after=2)
    d.spacer(18)
    d.p(f"Place: {F.CITY}", align="left", space_after=0)
    d.p("Date: [DATE]", align="left")




def acknowledgement(d):
    d.h1("ACKNOWLEDGEMENT")
    d.p(f"We express our sincere gratitude to our project guide, {F.GUIDE}, {F.GUIDE_DESIGNATION}, for valuable guidance, encouragement and constructive suggestions "
        "throughout this project.")
    d.p(f"We thank {F.HOD}, Head of the {F.DEPT}, for providing the facilities and support needed to complete this work, and {F.PRINCIPAL}, Principal, {F.COLLEGE}, "
        "for the encouragement given to us.")
    d.p("We thank the project coordinators and all faculty and staff members of the department for their help, and our families and friends for their constant support.")
    d.p("We also acknowledge the authors of the base paper and of the companion papers whose ideas shaped this work, the creators of the Open University Learning Analytics Dataset, "
        "which the base paper uses, and the developers of the open-source software on which the project is built (Python, FastAPI, SQLAlchemy, scikit-learn, XGBoost, React and Vite).")
    d.spacer(14)
    for n, r in F.STUDENTS:
        d.p(n, align="right", space_after=2)


def abstract(d):
    d.h1("ABSTRACT")
    m = F.METRICS
    lr = m["models"]["logistic_regression"]
    sd = F.SEEDS["summary"]["logistic_regression"]["test_auc"]
    ope = m["policy_evaluation"]
    rec = F.REC["summary"]
    lat = F.API_LAT["endpoints"]["GET /api/recommendations?top_n=8"]
    d.p("Learners face far more online courses than they can compare, platform lists tend to reward engagement rather than learning, and a new learner has no history from which to recommend. "
        f"This project builds {F.PRODUCT}, a personalised course recommendation system. A learner registers, fills in a profile "
        f"and receives a ranking of a {len(F.CATALOG)}-course catalogue. The ranking is a hybrid score of eight interpretable terms: TF-IDF content similarity, skill fit, topic interest, goal fit, rating, "
        "a behavioural term built from the learner's own events, a predicted success probability and an engagement score. Every card shows its match percentage and up to three reasons, "
        "and each logged event (start, quiz, complete, dismiss) changes the next ranking at once. Up to six courses are arranged into a staged learning path.")
    d.p(f"A learner-success model (logistic regression, selected by validation AUC over random forest and XGBoost) reaches a test AUC of {lr['roc_auc']:.4f} (six-seed mean {sd['mean']:.3f}). "
        "A one-versus-rest T-learner estimates the benefit of five learning actions, and an offline policy evaluation is reported with its effective sample size "
        f"({ope['effective_sample_size']} of {ope['test_samples']:,} rows), so it is read as weak evidence and not as proof of gain. All of these models are trained on a reproducible synthetic data set that imitates the "
        "Open University Learning Analytics Dataset; the real data were not used. On ten hand-written learner personas the hybrid reaches a precision at 3 of "
        f"{rec['hybrid (shipped)']['p@3']:.3f} against {rec['popularity (rating only)']['p@3']:.2f} for popularity, but it does not beat plain content matching ({rec['content-only (TF-IDF)']['p@3']:.3f}).")
    d.p(f"The system is a FastAPI, SQLAlchemy and SQLite service with a React interface. {F.TESTS['pytest']['passed']} automated tests, a {F.TESTS['smoke']['checks']}-check smoke test and a responsive check pass, and a ranking takes "
        f"{lat['mean_ms']:.1f} ms on average on the test machine. Collaborative filtering across learners, the base paper's reinforcement-learning agent, a prerequisite graph and a study with real learners were not done "
        "and are listed as limitations and future work.")
    d.p("**Keywords:** personalised learning, course recommendation, hybrid recommendation, content-based filtering, learning path, uplift modelling, off-policy evaluation, explainable recommendation, FastAPI, React.", align="left")


ABBR = [
    ("AI", "Artificial Intelligence"), ("API", "Application Programming Interface"), ("AUC", "Area Under the ROC Curve"), ("CB", "Content-Based (filtering)"),
    ("CF", "Collaborative Filtering"), ("CSV", "Comma-Separated Values"), ("DB", "Database"), ("DFD", "Data Flow Diagram"), ("DR", "Doubly Robust (estimator)"),
    ("ER", "Entity-Relationship"), ("ESS", "Effective Sample Size"), ("F1", "Harmonic mean of precision and recall"), ("HTTP", "Hypertext Transfer Protocol"),
    ("IPS", "Inverse Propensity Scoring"), ("JSON", "JavaScript Object Notation"), ("LR", "Logistic Regression"), ("ML", "Machine Learning"), ("MOOC", "Massive Open Online Course"),
    ("MRR", "Mean Reciprocal Rank"), ("OPE", "Off-Policy Evaluation"), ("ORM", "Object-Relational Mapping"), ("OULAD", "Open University Learning Analytics Dataset"),
    ("P@k", "Precision at k"), ("REST", "Representational State Transfer"), ("RF", "Random Forest"), ("RL", "Reinforcement Learning"), ("ROC", "Receiver Operating Characteristic"),
    ("SNIPS", "Self-Normalised Inverse Propensity Scoring"), ("SPA", "Single-Page Application"), ("SQL", "Structured Query Language"), ("TF-IDF", "Term Frequency - Inverse Document Frequency"),
    ("UI", "User Interface"), ("UML", "Unified Modeling Language"), ("VLE", "Virtual Learning Environment"), ("XGB", "XGBoost (extreme gradient boosting)"),
]


def abbreviations(d):
    d.table("Abbreviations used in this report", ["Abbreviation", "Expansion"], [list(x) for x in ABBR], widths=[1.4, 4.9], size=11)
