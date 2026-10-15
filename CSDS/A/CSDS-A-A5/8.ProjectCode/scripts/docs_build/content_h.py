"""Front matter of the final report and the implementation-decisions table."""
from docbuild import *
from docbuild import _runs, _set_font
from common import *

ABSTRACT_TEXT = [
    "Input Tax Credit (ITC) fraud under the Goods and Services Tax, carried out through fake invoices, circular trading and shell companies, causes large revenue losses. Manual audits and fixed rules are slow and easy to evade, confirmed fraud labels are scarce, and existing systems rarely explain why a claim is flagged. The base paper by Datta, Thakkar and Dabhade (2026) describes these frauds and calls for analytics and network analysis, but proposes no model. This project builds one.",
    "TaxSentinel learns normal GST behaviour without labels using a Joint Embedding Predictive Architecture (JEPA): a 53,420-value model, trained in 11.7 s on a CPU, that predicts the embedding of a taxpayer-month from its history and from the month with one feature layer hidden. Its prediction error is combined, through a noisy-OR, with circular-trading and shared-identity cluster detection and with an eight-signal invoice anomaly score. Taxpayers and invoice chains are ranked, each flag carries a numbered evidence list, and Gemini writes a case note in which every claim cites that evidence; notes are checked automatically for invalid citations and ungrounded numbers. The system is a secured FastAPI and React application.",
    "On a seeded synthetic ecosystem of 600 taxpayers and 64,474 invoices with 79 injected fraud taxpayers, TaxSentinel reaches precision@79 of 0.949, F1 0.955 and ROC-AUC 0.997, against 0.620, 0.432 and 0.876 for a rule baseline, recovers all 5 injected rings and scores invoices with F1 0.924. Ablations show that the JEPA alone is the weakest layer (F1 0.327) and the layers are complementary. On five other generated ecosystems the F1 at the fixed threshold is lower and varies more, so the headline figures are a best case. Six evaluated case notes had no invalid citations. The data is synthetic, the language model is prompted and not fine-tuned, and the output is a risk indication for review, not a finding of fraud.",
]
KEYWORDS = "GST, input tax credit fraud, JEPA, self-supervised learning, circular trading, shell entities, network analysis, explainable AI, large language model, FastAPI."


def cover(doc):
    center(doc, PROJECT, 18, True, before=24, after=10, caps=True)
    center(doc, f"({PRODUCT})", 14, True, after=26)
    center(doc, "A project report submitted in partial fulfilment of the requirements for the award of the degree of", 12, after=10)
    center(doc, "BACHELOR OF TECHNOLOGY", 14, True, after=4)
    center(doc, "in", 12, after=4)
    center(doc, "COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)", 14, True, after=24)
    center(doc, "Submitted by", 12, True, after=6)
    student_table(doc, STUDENTS)
    center(doc, "Batch A5 (CSE-DS, Section A)", 12, before=10, after=18)
    center(doc, "Under the esteemed guidance of", 12, after=2)
    center(doc, GUIDE, 13, True, after=0)
    center(doc, GUIDE_DESIG, 12, after=18)
    center(doc, "[COLLEGE LOGO]", 11, italic=True, after=8)
    center(doc, "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)", 13, True, after=2)
    center(doc, COLLEGE, 13, True, after=2)
    center(doc, "[COLLEGE ADDRESS / AFFILIATING UNIVERSITY]", 11, after=2)
    center(doc, f"Academic year {YEAR[:4]}-{'20' + YEAR[5:]}", 12, after=0)


def certificate(doc):
    center(doc, "[COLLEGE LOGO]", 11, italic=True, after=4)
    center(doc, COLLEGE, 13, True, after=2)
    center(doc, "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)", 12, True, after=18)
    center(doc, "CERTIFICATE", 14, True, after=14)
    names = ", ".join(f"{n} ({r})" for n, r in STUDENTS)
    p = doc.add_paragraph()
    _runs(p, f"This is to certify that the project report entitled \"{PROJECT}\" is a bonafide record of the work carried out by {names}, in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering (Data Science), during the academic year {YEAR[:4]}-{'20' + YEAR[5:]}, under my supervision.")
    for _ in range(3):
        doc.add_paragraph()
    t = doc.add_table(rows=2, cols=3)
    cells = [[("Project Guide", True), ("Head of the Department", True), ("External Examiner", True)],
             [(f"{GUIDE}\n{GUIDE_DESIG}", False), ("[HOD NAME]\nDepartment of Computer Science and Engineering (Data Science)", False), ("[NAME AND SIGNATURE]", False)]]
    for i, row in enumerate(cells):
        for j, (txt, b) in enumerate(row):
            c = t.rows[i].cells[j]
            c.text = ""
            par = c.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.15
            _runs(par, txt, 12, bold_all=b)
    doc.add_paragraph()
    center(doc, "Principal: [PRINCIPAL NAME]", 12, after=0)


def declaration(doc):
    center(doc, "DECLARATION", 14, True, before=12, after=14)
    p = doc.add_paragraph()
    _runs(p, f"We hereby declare that the project report entitled \"{PROJECT}\", submitted to the {DEPT}, {COLLEGE}, in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering (Data Science), is a record of original work carried out by us under the guidance of {GUIDE}, {GUIDE_DESIG}. The results embodied in this report have not been submitted to any other university or institution for the award of any degree or diploma.")
    doc.add_paragraph()
    for n, r in STUDENTS:
        center(doc, f"{n}    {r}", 12, after=2)
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _runs(p, "Place: [PLACE]\nDate: [DATE]")


def acknowledgement(doc):
    center(doc, "ACKNOWLEDGEMENT", 14, True, before=12, after=14)
    for t in [
        f"We express our sincere gratitude to our project guide, {GUIDE}, {GUIDE_DESIG}, for valuable guidance, encouragement and constructive suggestions throughout this project.",
        "We thank [HOD NAME], Head of the Department of Computer Science and Engineering (Data Science), for providing the facilities and support needed to complete this work, and [PRINCIPAL NAME], Principal, for the encouragement given to us.",
        "We thank the project coordinators and all faculty and staff members of the department for their help, and our families and friends for their constant support.",
        "We also acknowledge the authors of the base paper and of the related work cited in this report, the creators of the PaySim dataset and of the open-source software that the project is built on (PyTorch, NetworkX, FastAPI, SQLAlchemy, React and Vite), and the Gemini API used for the written explanations.",
    ]:
        p = doc.add_paragraph()
        _runs(p, t)
    doc.add_paragraph()
    for n, _ in STUDENTS:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(0)
        _runs(p, n)


def abstract(doc):
    center(doc, "ABSTRACT", 14, True, before=12, after=12)
    for t in ABSTRACT_TEXT:
        p = doc.add_paragraph()
        _runs(p, t)
    p = doc.add_paragraph()
    _runs(p, "**Keywords:** " + KEYWORDS)


def abbreviations(doc):
    center(doc, "LIST OF ABBREVIATIONS", 14, True, before=12, after=12)
    t = doc.add_table(rows=1, cols=2)
    t.style = "Table Grid"
    for i, h in enumerate(("Abbreviation", "Meaning")):
        c = t.rows[0].cells[i]
        c.text = ""
        _runs(c.paragraphs[0], h, 11, bold_all=True)
        shade(c, GREEN)
    for a, m in ABBREV:
        cells = t.add_row().cells
        for i, v in enumerate((a, m)):
            cells[i].text = ""
            cells[i].paragraphs[0].paragraph_format.line_spacing = 1.0
            cells[i].paragraphs[0].paragraph_format.space_after = Pt(1)
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            _runs(cells[i].paragraphs[0], v, 11)
    for row in t.rows:
        row.cells[0].width = Inches(1.3)
        row.cells[1].width = Inches(5.2)


DECISIONS = [
    ("tbl", "dec", "Implementation decisions and their reasons", ["Decision", "Alternatives considered", "Reason"], [
        ["Synthetic seeded generator with hard negatives", "Public tax datasets; scraping; hand-made sample", "No real GST data is public; a seeded generator is reproducible, labelled and can include legitimate irregularity, so detection is not trivial"],
        ["Small MLP JEPA (53,420 values), window of 3 months", "Transformer encoder; larger window; autoencoder", "About 7.0k taxpayer-months do not justify a large model; training takes 11.7 s on a CPU; the window covers a quarter. Alternatives were not trained, so this is a design choice, not a measured one"],
        ["Four mask variants", "Single whole-month masking", "Hiding each feature layer lets a deviation be attributed to a layer, and the behaviour-block variant catches one-month ITC spikes"],
        ["EMA target encoder and variance hinge", "Stop-gradient only; contrastive negatives", "Standard JEPA/BYOL/VICReg practice to prevent collapse without negatives"],
        ["Median-normalised errors, geometric mean, top-2 months", "Mean of raw errors", "Different months and variants have different error scales; the top-2 rule responds to sustained or repeated deviation without being dominated by one noisy month"],
        ["Explicit cycle search (length <= 5) on recurring, above-median edges", "Graph neural network; node2vec", "Exact, fast on this data and yields a loop that can be drawn and cited; no labels needed"],
        ["Noisy-OR with four hand-set weights", "Learned classifier; averaging", "One strong layer should suffice; parameters are readable; no labels needed. Weakness: weights tuned on seed 42 (Chapter 8)"],
        ["Pipeline state held in memory and pickled", "Compute per request; SQL tables for results", "Read endpoints become lookups (1.7 to 12 ms median); state is rebuilt on a regenerate"],
        ["Generation on a background thread with a polled status", "Celery/queue; synchronous request", "No extra infrastructure for a single-user prototype; keeps requests short; powers the stage stepper. A queue is future work"],
        ["SQLite via SQLAlchemy for users, runs and notes", "PostgreSQL; files", "Zero set-up for a Windows demo; ORM keeps a later move to a server database easy"],
        ["JWT bearer tokens (HS256, 12 h) and bcrypt", "Server-side sessions; Argon2", "Stateless API for the SPA; bcrypt is a well-established password scheme"],
        ["Notes generated on demand, stored with their evidence and quality checks", "Pre-generate for all flagged taxpayers", "Saves free-tier quota; a stored note can always be audited against the evidence it was written from"],
        ["Gemini with fallback models and one retry", "Single model; local model", "Free tier rate-limits and overloads (observed: 429, 503, 504); fallbacks improved completion but did not remove failures"],
        ["React with route-level code splitting, react-force-graph for the network", "Server-rendered pages; Cytoscape", "Each screen loads only its code; the force graph handles hundreds of nodes smoothly"],
    ], [2.0, 1.9, 3.1]),
]
