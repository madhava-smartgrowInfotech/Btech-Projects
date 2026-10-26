"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx."""

import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K
from .refs import REFS

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"

# the six objectives, verbatim from 6.OBJECTIVES&PROBLEM STATEMENT.docx
OBJECTIVES = [
    "Accept lab reports in PDF or scanned image form and extract text using high-speed OCR.",
    "Apply named entity recognition to identify test parameters, values, units and reference ranges.",
    "Compare each extracted value against its reference range and flag abnormal results.",
    "Generate plain-language explanations for abnormal findings, grounded in trusted medical sources.",
    "Track parameters across successive reports to display health trends over time.",
    "Present results through a dashboard and evaluate extraction accuracy against manually labelled reports.",
]


def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    # layout footer text carries the template's deck title
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "lab report analysis, OCR, named entity recognition, health insights, trend tracking"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def fill_title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def agenda(slide, items, colors):
    cols = 3
    w, h, gx, gy = 3.85, 1.45, 0.29, 0.3
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def finish(prs, S, notes, out_path):
    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.scrub_theme(out_path, "LabLens")
    return out_path


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}

    # ---- 1 title
    fill_title_slide(S[0], "A web platform that reads a lab report (PDF or scan), flags abnormal values, explains them in plain language and tracks them over time",
                     "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the project title. One sentence: a patient uploads a lab report and gets the values, which ones are abnormal, "
                "a plain-language explanation of each, and a history across reports.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey and evidence"), ("04", "Existing system and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review is about why the problem matters and what is missing in current work, not yet about results."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: from a confusing report to clear insight")
    wipe(s)
    W, H = 3.85, 4.75
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "Patients receive lab reports as PDFs or scans full of parameters and reference ranges they cannot interpret. Understanding them normally needs a follow-up consultation, which adds cost and delay.", K.ORANGE, "!"),
        ("Our idea", "Read the report with OCR, identify each test name, value, unit and reference range, flag Low, Normal or High, explain abnormal values in plain language, and keep every report so trends can be seen.", K.BLUE, "i"),
        ("The deliverable", "A web application: upload a report, see colour-coded results, explanations of abnormal findings, a dashboard, historical trend charts and a comparison between two reports.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=20)
    notes[3] = "Three sentences: the problem, the idea, the deliverable. The abstract's target is under 10 seconds per report."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, F.BASE_PAPER, size=14, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", "Retrieval-augmented generation on LLaMA-3 8B. Text chunks (1,024 characters, 100 overlap) are embedded into ChromaDB; the top 3 chunks plus the user's report values form the prompt. Sources are returned with the answer.", K.BLUE, "M"),
        ("Data and reported results", "Knowledge base of 20 medical books, 383 video transcripts and a 33-parameter range document. 20 responses were scored 1 to 100 by GPT-4 for correctness, clarity, helpfulness and completeness.", K.GREEN, "R"),
        ("What it does not cover", "Metabolic syndrome only. No extraction accuracy or processing time is reported. Trend tracking across reports is listed only as future scope.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.0, t, b_, col, gl, body_size=17)
    notes[4] = ("Read the citation. The paper answers questions about a blood test report for one condition using RAG. It stores reports and refers to them in later "
                "queries, but gives no measurement of reading values off the document. Our project generalises the scope.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Approach", "Data", "Result / note"],
            ["Karhade et al., 2025 [1] (base)", "RAG with LLaMA-3 8B on a curated knowledge base", "20 books, 383 transcripts, 33 parameters", "GPT-4 scores, 20 responses; metabolic syndrome only"],
            ["Ren et al., 2025 [2]", "Serialises photographed lab-report images into structured form", "Image-based laboratory reports", "Full text not reviewed in detail"],
            ["Xiang et al., 2026 [3]", "Action cards from multimodal check-up reports", "2,000 de-identified reports", "84 % of outputs judged fully reasonable by experts"],
            ["Bakhsheshi & Beigy, 2025 [4]", "General vision-language models read blood-report images", "100 report images, 3 models", "Answers compared with Sentence-BERT; small dataset"],
            ["Nguyen et al., 2025 [5]", "Three fine-tuned FLAN-T5-Large models for medical text", "Medical reports and conversations", "Web and mobile app; not reviewed in detail"],
            ["Du et al., 2020 [12]", "PP-OCR: ultra-lightweight OCR system", "General text images", "OCR stage named in the abstract"],
            ["Lafferty et al., 2001 [14]", "Conditional random fields for sequence labelling", "Sequence data", "Tagger named in the abstract"]]
    K.table(s, 0.6, 1.35, [2.65, 3.55, 2.8, 3.13], rows, font_size=13, row_h=0.66, header_size=13)
    notes[5] = ("Three groups: report understanding with language models [1][3][4][5], digitising report images [2], and the OCR and tagging building blocks named in the abstract [12][14]. "
                "Where a row says not reviewed in detail, only the title and abstract-level facts were checked.")

    # ---- 6 supporting evidence
    s = S[5]
    set_title(s, "Supporting evidence from the literature")
    wipe(s)
    K.text(s, 0.6, 1.3, 7.4, 0.4, "Base paper: stated averages vs averages recomputed from its Table 4 (20 responses, score 1-100)", size=13, color=K.TXT, bold=True)
    K.bar_chart(s, 0.6, 1.75, 7.4, 4.85, ["Correctness", "Clarity", "Helpfulness", "Completeness"],
                [("Stated in conclusion", [92.4, 89.7, 91.1, 88.9]), ("Recomputed from table", [94.0, 94.9, 90.1, 88.65])],
                colors=[K.BLUE, K.ORANGE], number_format="0.0", font_size=12, max_value=110)
    K.card(s, 8.3, 1.4, 4.43, 2.65, "Safety trade-off [3]", "Removing safety constraints raised problem recall from 0.527 to 0.825 but caused more diagnostic overstatement. Wording must stay educational.", K.GREEN, "!", body_size=14)
    K.card(s, 8.3, 4.2, 4.43, 2.45, "Image reports [4]", "Authors call results encouraging but warn they are limited by dataset size (100 images).", K.ORANGE, "i", body_size=14)
    notes[6] = ("The chart is computed from the paper's own Table 4: the conclusion quotes 92.4, 89.7, 91.1 and 88.9 but the table averages are 94.0, 94.9, 90.1 and 88.65. "
                "The safety numbers come from the abstract of Checkup2Action [3]; the dataset-size caution from the abstract of [4].")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.55, 12.13, 1.1, [("Lab issues PDF or scan", K.NAVY), ("Patient cannot interpret it", K.NAVY), ("Follow-up consultation", K.NAVY), ("Extra cost and delay", K.NAVY)], size=16, gap=0.5)
    K.card(s, 0.6, 3.1, 5.95, 3.55, "Digitisation tools", "OCR and report-digitising tools turn a document into structured data, but they stop there: the patient still does not learn what an abnormal value means, and no history is kept.", K.BLUE, "1", body_size=20)
    K.card(s, 6.78, 3.1, 5.95, 3.55, "Language-model assistants", "RAG and chat assistants can explain results in plain words, but the one in the base paper is built for a single condition and needs the user to type a query.", K.ORANGE, "2", body_size=20)
    notes[7] = "Today's typical path ends in a consultation. Existing tools solve either reading the report or explaining it, not both with history."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    items = [
        ("Written for clinicians", "Laboratory reports use terms and ranges that patients cannot interpret on their own.", K.ORANGE, "1"),
        ("Manual reading is slow", "Reading every parameter by hand is slow and error-prone for patients and for staff.", K.BLUE, "2"),
        ("No explanation", "Tools that digitise reports do not say what an abnormal value means.", K.GREEN, "3"),
        ("No history", "Without retained history a patient cannot see whether a parameter is improving or worsening.", K.PURPLE, "4"),
    ]
    for i, (t, b_, col, gl) in enumerate(items):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.5 + r * 2.7, 5.95, 2.5, t, b_, col, gl, body_size=21)
    notes[8] = "These four statements are the problem statement of the batch proposal. Each maps to one feature: extraction, flagging, explanations, trends."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    gaps = [("Scope", "The base paper applies RAG to blood reports for one condition; a general platform for arbitrary lab parameters is missing."),
            ("Extraction", "Reading values, units and ranges off the document is assumed, not measured, in the base paper."),
            ("Trends", "Comparing successive reports is future scope in the base paper; a patient cannot see change over time."),
            ("Evaluation", "Responses are scored by an LLM; extraction accuracy against labelled reports is not reported."),
            ("Safe wording", "Explanations must inform without diagnosing; unconstrained generation overstates [3].")]
    for i, (k, v) in enumerate(gaps):
        y = 1.45 + i * 1.08
        K.box(s, 0.6, y, 2.6, 0.9, fill=K.NAVY, line=None, radius=0.06)
        K.text(s, 0.6, y, 2.6, 0.9, k, size=16, color=K.WHITE, bold=True, align="c", anchor="m")
        K.text(s, 3.5, y, 9.2, 0.9, v, size=19, color=K.INK, anchor="m")
    notes[9] = ("The batch literature survey states the gap as: a general report-analysis platform covering arbitrary lab parameters with extraction, explanation and longitudinal "
                "trend tracking. The other four rows are backed by the base paper's own text.")

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 2.75, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.5, "Given a laboratory report as a **PDF or scanned image**, extract each test with its value, unit and reference range, **flag abnormal results**, explain them in **plain language without diagnosing**, and keep the history so that **trends over successive reports** can be seen, all through a web interface a patient can use.", size=22, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "A PDF, JPG, JPEG or PNG lab report, up to 15 MB"), ("Output", "Test table, Low / Normal / High flags, explanations of abnormal values"), ("Record", "Report library, dashboard, trend charts, report comparison")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.5, 3.85, 1.65)
        K.text(s, x + 0.25, 4.62, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.1, 3.4, 1.0, b_, size=16, color=K.TXT)
    notes[10] = "Read the statement slowly. Need: a platform that reads a lab report automatically, explains abnormal values in plain language, and tracks them over time."

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 5.3, [(f"{i}.  {o}", {"space_after": 9}) for i, o in enumerate(OBJECTIVES, 1)], size=24, color=K.INK)
    notes[11] = "The six objectives of the project proposal. Review 2 and the final review say plainly which were met."

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach (from the project abstract)")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Extract", "PP-OCR text extraction, designed for low-resolution and noisy scans of PDFs and images.", K.BLUE, "1"),
        ("Understand", "CRF-based named entity recognition: test name, result, unit, reference range and status flag.", K.GREEN, "2"),
        ("Explain", "Rule-based and LLM interpreter writes plain-language explanations, possible causes and simple advice.", K.ORANGE, "3"),
        ("Track", "Longitudinal trend engine shows parameter changes across successive checkups.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.45, t, b_, col, gl, body_size=17)
    K.box(s, 0.6, 5.15, 12.13, 1.5)
    K.circle(s, 0.85, 5.45, 0.7, K.NAVY, "S", 18)
    K.text(s, 1.8, 5.3, 10.7, 0.45, "Storage and interface", size=17, color=K.INK, bold=True)
    K.text(s, 1.8, 5.78, 10.7, 0.8, "Supabase (PostgreSQL with row-level security), React with Tailwind and Recharts, serverless Python functions; target below 10 seconds per report. Review 2 records what the implementation settled on.", size=14, color=K.TXT)
    notes[12] = "This is the plan in the abstract. Review 2 shows where the implementation differs: Tesseract and a regex parser with a TF-IDF name matcher instead of PP-OCR and a CRF, and SQLite and FastAPI instead of Supabase and cloud functions."

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 1.2, 1.3, 10.9, 5.3)
    K.text(s, 0.6, 6.6, 12.13, 0.3, "Upload, extraction, classification, explanation and storage behind a web interface (tiers as built; see Review 2 for the technology choices)", size=12, color=K.TXT, align="c", italic=True)
    notes[13] = "Follow the diagram: the user interface, the API, the processing pipeline, and the data store."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    outs = [("Structured extraction", "Test name, value, unit and reference range read from PDFs and scans.", K.BLUE, "1"),
            ("Clear flags", "Every result marked Low, Normal or High against its own range.", K.GREEN, "2"),
            ("Plain-language insight", "Explanations and general causes for abnormal values, without diagnosis.", K.ORANGE, "3"),
            ("Trend tracking", "A parameter followed across reports, and two reports compared side by side.", K.PURPLE, "4"),
            ("Measured accuracy", "Extraction accuracy reported on labelled reports, including where it fails.", K.BLUE, "5"),
            ("Fast and usable", "Report processed in seconds (abstract target: under 10) in a web dashboard.", K.GREEN, "6")]
    for i, (t, b_, col, gl) in enumerate(outs):
        r, c = divmod(i, 3)
        K.card(s, 0.6 + c * 4.14, 1.5 + r * 2.7, 3.85, 2.5, t, b_, col, gl, body_size=18)
    notes[14] = "These are expected outcomes, not results. The final review reports what was measured and what was not."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    idx = [0, 1, 2, 3, 4, 5, 11, 13]
    K.text(s, 0.6, 1.3, 12.13, 5.6, [(f"[{i + 1}] {REFS[i]}", {"space_after": 4}) for i in idx], size=14, color=K.INK)
    notes[15] = "Full references are in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = "Likely questions: why a general platform instead of one condition; how the explanations avoid diagnosing; what accuracy is expected."

    return finish(prs, S, notes, out_path)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
