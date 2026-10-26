"""Front matter of the full report: cover, certificate, declaration, acknowledgement, abstract, abbreviations."""

import os

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from . import facts as F
from .kit import add_runs

BANNER = os.path.join(F.DOCS, "figures", "college_banner.png")


def _banner():
    """The institution's letterhead image, taken from the final-review template (written once to docs/figures)."""
    if os.path.exists(BANNER):
        return BANNER
    try:
        from pptx import Presentation

        os.makedirs(os.path.dirname(BANNER), exist_ok=True)
        prs = Presentation(r"D:\abstracts\Templates\Final_PPT.pptx")
        for sh in prs.slides[0].shapes:
            if sh.shape_type == 13:
                with open(BANNER, "wb") as f:
                    f.write(sh.image.blob)
                return BANNER
    except Exception:
        pass
    return None


def _banner_par(d, width=5.9):
    b = _banner()
    if b:
        par = d.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.line_spacing = 1.0
        par.add_run().add_picture(b, width=Inches(width))


def cover(d):
    _banner_par(d)
    d.spacer(2)
    d.p(F.FULL_TITLE.upper(), align="center", size=17, bold=True, space_after=6)
    d.p(f"{F.PRODUCT}: {F.SUBTITLE}", align="center", size=12, italic=True, space_after=8)
    d.p("A project report submitted in partial fulfilment of the requirements for the award of the degree of", align="center", size=12, space_after=6)
    d.p("BACHELOR OF TECHNOLOGY", align="center", size=15, bold=True, space_after=2)
    d.p("in", align="center", size=12, space_after=2)
    d.p("COMPUTER SCIENCE AND ENGINEERING", align="center", size=15, bold=True, space_after=6)
    d.p("Submitted by", align="center", size=12, bold=True, space_after=4)
    rows = [[n.upper(), r] for n, r in F.STUDENTS]
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
    d.p(f"Batch {F.BATCH_NO} ({F.SECTION})", align="center", size=12, space_after=6)
    d.p("Under the esteemed guidance of", align="center", size=12, space_after=2)
    d.p(F.GUIDE.upper(), align="center", size=13, bold=True, space_after=0)
    d.p(F.GUIDE_DESIGNATION, align="center", size=12, space_after=8)
    d.p("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", align="center", size=13, bold=True, space_after=2)
    d.p(F.COLLEGE.upper(), align="center", size=12, bold=True, space_after=2)
    d.p(F.ADDRESS, align="center", size=11, space_after=2)
    d.p(f"Academic year {F.YEAR}", align="center", size=12, space_after=0)


def certificate(d):
    d.h1("CERTIFICATE", page_break=False)
    _banner_par(d, 5.2)
    d.p(f"This is to certify that the project report entitled **\"{F.FULL_TITLE}\"** is a bonafide record of the work carried out by "
        + ", ".join(f"**{n.upper()}** ({r})" for n, r in F.STUDENTS)
        + f", in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, "
          f"during the academic year {F.YEAR}, under my supervision.")
    d.spacer(30)
    t = d.doc.add_table(rows=3, cols=3)
    cells = [("Project Guide", F.GUIDE, F.GUIDE_DESIGNATION), ("Head of the Department", F.HOD, F.DEPT), ("Principal", F.PRINCIPAL, F.COLLEGE_SHORT)]
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
    d.p(f"Place: {F.PLACE}", align="left", space_after=0)
    d.p(f"Date: {F.DATE}", align="left")


def declaration(d):
    d.h1("DECLARATION")
    d.p(f"We hereby declare that the project report entitled **\"{F.FULL_TITLE}\"**, submitted to the {F.DEPT}, {F.COLLEGE_SHORT}, in partial fulfilment of the "
        f"requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, is a record of original work carried out by us under the "
        f"guidance of {F.GUIDE}, {F.GUIDE_DESIGNATION}. The results embodied in this report have not been submitted to any other university or institution for the award of any degree or diploma.")
    d.spacer(24)
    for n, r in F.STUDENTS:
        d.p(f"{n.upper()}   {r}", align="right", space_after=2)
    d.spacer(18)
    d.p(f"Place: {F.PLACE}", align="left", space_after=0)
    d.p(f"Date: {F.DATE}", align="left")


def acknowledgement(d):
    d.h1("ACKNOWLEDGEMENT")
    d.p(f"We express our sincere gratitude to our project guide, {F.GUIDE}, {F.GUIDE_DESIGNATION}, for valuable guidance, encouragement and constructive suggestions "
        "throughout this project.")
    d.p(f"We thank {F.HOD}, Head of the {F.DEPT}, for providing the facilities and support needed to complete this work, and {F.PRINCIPAL}, Principal, {F.COLLEGE_SHORT}, "
        "for the encouragement given to us.")
    d.p("We thank the project coordinators and all faculty and staff members of the department for their help, and our families and friends for their constant support.")
    d.p("We also acknowledge R. Kharat, S. Solapurkar, A. Tikkas, M. Uttarwar and A. Yadav, whose multi-model personal finance assistant is the registered base paper of this project, "
        "and the other authors whose work is listed in the references. "
        "We are grateful to the maintainers of the open-source software used here: FastAPI, SQLAlchemy, SQLite, scikit-learn, pandas, ReportLab, OpenPyXL, React, Vite, Recharts, pytest, matplotlib and Playwright.")
    d.spacer(14)
    for n, r in F.STUDENTS:
        d.p(n.upper(), align="right", space_after=2)


def abstract(d):
    c, fc = F.CLS, F.FC["demo_backtest"]
    d.p("Managing personal money is hard when income, recurring bills and investments are scattered across many digital transactions, and most tools only record what already happened. "
        f"This project builds {F.PRODUCT}, a web application in which a user signs up, records or imports transactions, and gets an automatic category for each one, a forecast of next month's spending, "
        "monthly budgets with alerts at 75, 90 and 100 per cent, savings goals, a manual investment portfolio, a 0-100 financial health score and an assistant that answers questions from the user's own data. "
        "The categoriser is a TF-IDF and logistic-regression model trained on a 51-description seed list, the forecast is a least-squares linear trend over monthly totals, and the health score is a weighted sum of six explainable components. "
        "The back end is FastAPI over SQLAlchemy and SQLite and the front end is React; the original Streamlit pages run on the same Python code. "
        "The registered base paper combines BERT, Q-learning, LSTM and Isolation Forest; this work implements the first two tasks in a much simpler form and does not implement anomaly detection or reinforcement learning.")
    d.p(f"We measured it with its own tools. All {F.PYTEST_PASSED} unit tests and {F.SMOKE_PASSED} end-to-end smoke checks pass. On a 198-description probe set the categoriser scores {c['tfidf_lr']['accuracy'] * 100:.1f} % "
        f"(macro-F1 {c['tfidf_lr']['macro_f1']:.3f}), but {c['tfidf_lr']['accuracy_by_tier']['A'] * 100:.0f} % on seed-like wording against {c['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % on merchants it has not seen, "
        f"where it falls back to the Transport class. On the demo account the linear trend has a one-step MAPE of {fc['mape_pct']['linear_trend (app)']:.1f} % over three test months, worse than a plain mean ({fc['mape_pct']['mean_of_all']:.1f} %), "
        "and a simulation shows it only beats the mean after about seven months of history. Typical API responses take 7 to 130 ms on a laptop-class CPU. "
        "All data are fictional or synthetic and no study with real users was done.")
    d.p("**Keywords:** personal finance automation, expense categorisation, expense forecasting, financial health score, budgeting assistance, smart alerts, data visualisation, FastAPI, linear regression, TF-IDF.")


ABBR = [
    ("API", "Application Programming Interface"), ("BERT", "Bidirectional Encoder Representations from Transformers"), ("CORS", "Cross-Origin Resource Sharing"),
    ("CRUD", "Create, Read, Update, Delete"), ("CSV", "Comma-Separated Values"), ("DFD", "Data Flow Diagram"), ("ER", "Entity-Relationship"),
    ("FR", "Functional Requirement"), ("HMAC", "Hash-based Message Authentication Code"), ("HTTP", "Hypertext Transfer Protocol"), ("INR", "Indian Rupee"),
    ("JSON", "JavaScript Object Notation"), ("LLM", "Large Language Model"), ("LOO", "Leave-One-Out"), ("LR", "Logistic Regression"), ("LSTM", "Long Short-Term Memory"),
    ("MAE", "Mean Absolute Error"), ("MAPE", "Mean Absolute Percentage Error"), ("ML", "Machine Learning"), ("NFR", "Non-Functional Requirement"),
    ("ORM", "Object-Relational Mapping"), ("REST", "Representational State Transfer"), ("RL", "Reinforcement Learning"), ("SMOTE", "Synthetic Minority Over-sampling Technique"),
    ("SPA", "Single-Page Application"), ("SQL", "Structured Query Language"), ("TF-IDF", "Term Frequency - Inverse Document Frequency"), ("UI", "User Interface"),
    ("UML", "Unified Modeling Language"), ("UPI", "Unified Payments Interface"),
]


def abbreviations(d):
    """Two abbreviation/expansion pairs per row so the list takes half the space."""
    half = (len(ABBR) + 1) // 2
    rows = [list(ABBR[i]) + (list(ABBR[i + half]) if i + half < len(ABBR) else ["", ""]) for i in range(half)]
    d.table("Abbreviations used in this report", ["Abbreviation", "Expansion", "Abbreviation", "Expansion"], rows, widths=[0.95, 2.25, 0.95, 2.25], size=10)
