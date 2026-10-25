"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx."""

import os
import re
import zipfile

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"

BANNED = ["social media", "fakeddit", "pheme", "snopes", "mcnn", "bank transaction", "hidden risk", "recommender system", "skincare",
          "dayananda", "sindhu", "[student name", "[roll no", "sign language", "signspeak", "churn", "fraud", "placement", "xgboost",
          "campus", "manipulat", "multimodal detection"]

# Batch objectives (6.OBJECTIVES&PROBLEM STATEMENT.docx), shortened only by trimming
OBJECTIVES = [
    "Build a document ingestion module that parses syllabi, lecture notes and question banks and extracts subjects, units and topics.",
    "Store the extracted content as vector embeddings so the material can be searched semantically rather than by keyword.",
    "Implement a RAG question-answering engine that answers strictly from the uploaded material and cites the source.",
    "Apply semantic context compression so retrieval stays accurate without exceeding the model context window.",
    "Generate personalised study roadmaps and revision schedules from topic coverage and performance.",
    "Present curriculum coverage, study velocity and engagement metrics on an interactive dashboard.",
]

PROBLEM_STATEMENT = ("Build a platform that ingests a student's own academic documents (syllabi, notes, question banks), organises them by subject, unit and topic, "
                     "answers questions strictly from those documents with the source passage cited, and adapts the study plan to measured topic mastery - "
                     "running on an ordinary laptop and reporting its accuracy honestly.")

_FALLBACK_REFS = [
    "D. Zhang, H. Yu, J. Huo and M. Su, \"SAC-RAG: Semantic Adaptive Context Compression for Retrieval-Augmented Generation,\" IEEE Access, vol. 14, pp. 117406-117418, 2026, doi: 10.1109/ACCESS.2026.3718025.",
    "Z. Li, V. Yazdanpanah, J. Wang, W. Gu, L. Shi, A. I. Cristea, S. Kiden and S. Stein, \"TutorLLM: Customizing learning recommendations with knowledge tracing and retrieval-augmented generation,\" arXiv:2502.15709, 2025.",
    "R. Vatankhah Barenji, N. Salimi and S. Khoshgoftar, \"An LLM-powered assessment retrieval-augmented generation (RAG) for higher education,\" arXiv:2601.06141, 2026.",
    "P. Lewis et al., \"Retrieval-augmented generation for knowledge-intensive NLP tasks,\" in Advances in Neural Information Processing Systems 33, 2020, pp. 9459-9474.",
    "V. Karpukhin et al., \"Dense passage retrieval for open-domain question answering,\" in Proc. EMNLP, 2020, pp. 6769-6781.",
    "S. Robertson and H. Zaragoza, \"The probabilistic relevance framework: BM25 and beyond,\" Found. Trends Inf. Retr., vol. 3, no. 4, pp. 333-389, 2009.",
    "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Inf. Process. Manage., vol. 24, no. 5, pp. 513-523, 1988.",
    "S. Deerwester et al., \"Indexing by latent semantic analysis,\" J. Amer. Soc. Inf. Sci., vol. 41, no. 6, pp. 391-407, 1990.",
]


def _refs():
    """Reference list of the project (refs.py, numbering fixed across the documents); local fallback while it is being rewritten."""
    try:
        from .refs import REFS
        if len(REFS) >= 18 and "SAC-RAG" in REFS[0] and "TutorLLM" in REFS[1]:
            return REFS
    except Exception:
        pass
    return _FALLBACK_REFS


def scan_deck(path):
    """Return banned strings found anywhere in the saved package (slides, notes, layouts, masters, theme, properties)."""
    hits = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith((".xml", ".rels")):
                t = re.sub(r"<[^>]+>", " ", z.read(n).decode("utf-8", "ignore")).lower()
                for b in BANNED:
                    if b in t:
                        hits.append((n, b))
    return hits


def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "adaptive learning, retrieval-augmented generation, educational document analysis, learning analytics"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 28)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def build(out_path):
    REFS = _refs()
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}

    # ---- 1 title
    title_slide(S[0], "Document-grounded question answering, adaptive quizzes and a personal study roadmap",
                "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the title. One sentence: the platform reads the student's own syllabi and notes, answers questions only from them with the "
                "source shown, and turns quiz results into a priority-ranked study roadmap.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey"), ("04", "Existing system and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review is about why the problem matters and what is missing in current work; design and results come in the later reviews."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: from scattered study files to a personal tutor")
    wipe(s)
    W, H = 3.85, 4.9
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "Students keep syllabi, notes and question banks as scattered files across six to eight subjects. Portals store them without understanding them, and general chatbots answer from the internet, not from the prescribed syllabus.", K.ORANGE, "!"),
        ("Our idea", "Extract subjects, units and topics from uploaded documents, retrieve the passages that match a question, and answer only from them with the source cited (RAG). Turn quiz results into a priority-ranked roadmap.", K.BLUE, "i"),
        ("The deliverable", "A web application: upload, document repository with detected topics, cited question answering, auto-generated quizzes, a study roadmap and a dashboard, running offline on a laptop with an optional LLM.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=16)
    notes[3] = "Three points: the study-material problem, the grounded-answer idea taken from retrieval-augmented generation, and a complete application that runs offline."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper: SAC-RAG")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, REFS[0] + "  [1]", size=12, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("What it proposes [1]", "Semantic Adaptive Compress RAG: an LLM classifies a question as fact, definition or reasoning, a type-specific retrieval strategy fetches passages, and an LLM compression step keeps only evidence snippets before answering.", K.BLUE, "1"),
        ("What it reports [1]", "On HotpotQA, 2WikiMultiHopQA and MuSiQue (1,000 questions each): token use cut by 38-58% for a 1-2 point drop in exact match; adaptive retrieval lifts HotpotQA EM from 0.560 to 0.611.", K.GREEN, "2"),
        ("What we adopt", "Retrieve-then-answer from the student's own material, a compact context instead of whole chunks, and the question-type view. The paper targets open-domain multi-hop QA, not a student's curriculum or progress analytics.", K.ORANGE, "3"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.0, t, b_, col, gl, body_size=14)
    notes[4] = ("Base paper from the batch file: SAC-RAG, IEEE Access 2026. Figures are from its abstract and Section V. Its setting is general multi-hop question answering with an LLM; "
                "our setting is a student's own documents, so only the retrieve-and-compress idea carries over.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Approach", "Venue, year", "What is known"],
            ["SAC-RAG [1] (base)", "Question-type-adaptive retrieval + LLM context compression", "IEEE Access, 2026", "Tokens -38 to -58% for -1 to -2 points EM (multi-hop QA)"],
            ["TutorLLM [2]", "Knowledge tracing + RAG with an LLM for personalised recommendations", "arXiv / RecSys 2024 format, 2025", "+10% user satisfaction, +5% quiz score vs a general LLM"],
            ["LLM assessment RAG [3]", "Rubric-grounded RAG grading and feedback for essays", "arXiv, 2026", "701 essays; 94-99% agreement with human markers"],
            ["RAG for medical spaced repetition [19]", "RAG-generated medical content for spaced-repetition study", "CSEDU, 2025", "Title and venue only (full text not read)"],
            ["Vision-language RAG teaching platform [20]", "Automatic teaching platform on vision-language RAG", "IEEE ISEC, 2025", "Title and venue only (full text not read)"],
            ["API-driven RAG for financial education [21]", "RAG platform for financial education through an API", "ICETC, 2025", "Title and venue only (full text not read)"],
            ["Lean learning resources with RAG [22]", "Student-designed Lean resources using ChatGPT and RAG", "ZDM Math. Education, 2026", "Title and venue only (full text not read)"]]
    K.table(s, 0.6, 1.35, [3.0, 4.3, 2.0, 2.83], rows, font_size=12, row_h=0.66, header_size=13)
    notes[5] = ("The batch survey lists five papers; the base paper is first. TutorLLM and the assessment-RAG paper were read in full from the archived PDFs. "
                "For the four other batch items only title, year and venue are known, so no results are quoted.")

    # ---- 6 supporting evidence (chart)
    s = S[5]
    set_title(s, "Supporting evidence from the base paper")
    wipe(s)
    gf = K.bar_chart(s, 0.6, 1.4, 7.6, 5.3, ["Exact match\n(HotpotQA)", "Recall@10\n(HotpotQA)"],
                     [("Naive RAG", [0.560, 0.787]), ("Adaptive RAG", [0.611, 0.880])],
                     colors=[K.BLUE, K.ORANGE], number_format="0.000", font_size=13, max_value=1.1)
    K.card(s, 8.5, 1.45, 4.23, 2.6, "Retrieval matters [1]", "Choosing the retrieval strategy by question type raised EM from 0.560 to 0.611 and Recall@10 from 0.787 to 0.880 on HotpotQA.", K.GREEN, "↑", body_size=14)
    K.card(s, 8.5, 4.2, 4.23, 2.5, "Education evidence [2][3]", "TutorLLM: +10% satisfaction, +5% quiz score. Assessment RAG: 94-99% agreement with humans on 701 essays.", K.ORANGE, "i", body_size=14)
    notes[6] = ("Chart values are from the SAC-RAG paper's text (HotpotQA, 1,000 questions, gpt-5-mini). They are the paper's results, not ours; our own measurements "
                "come in later reviews on a different, smaller notes corpus.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.55, 12.13, 1.1, [("PDFs, notes, timetables on disk", K.NAVY), ("Portal stores the files", K.NAVY), ("Keyword search or a general chatbot", K.NAVY), ("Student studies without feedback", K.NAVY)], size=15, gap=0.5)
    K.card(s, 0.6, 3.1, 5.95, 3.55, "Learning portals", "Hold content and track completion but do not read what is inside the files: units, topics and learning objectives stay invisible, and recommendations are identical for every learner.", K.BLUE, "1", body_size=16)
    K.card(s, 6.78, 3.1, 5.95, 3.55, "General chatbots", "Explain concepts well but answer from public data, may hallucinate when not grounded in a trusted source, and know nothing about the student's syllabus or progress.", K.ORANGE, "2", body_size=16)
    notes[7] = "Today's path: files in folders, a portal that stores them, and a chatbot that does not know the syllabus."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    items = [
        ("Files are not understood", "Learning platforms store academic files but never extract the units, topics or learning objectives inside them.", K.ORANGE, "1"),
        ("One size for everyone", "Recommendations are identical for every learner and ignore prior performance and study behaviour.", K.BLUE, "2"),
        ("Answers off the syllabus", "General-purpose chatbots answer from public internet data rather than the student's prescribed syllabus.", K.GREEN, "3"),
        ("No single progress view", "Students cannot see what has been studied, what remains and how well each topic is understood.", K.PURPLE, "4"),
    ]
    for i, (t, b_, col, gl) in enumerate(items):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.5 + r * 2.7, 5.95, 2.5, t, b_, col, gl, body_size=17)
    notes[8] = "The four problem points come from the batch problem statement. Each maps to a module: document analysis, roadmap, cited question answering, dashboard."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    gaps = [("RAG for QA only", "Existing RAG work targets general question answering and context compression, not a student's own curriculum."),
            ("Ingestion missing", "None of the surveyed systems combines document ingestion with tutoring grounded in the student's syllabus."),
            ("Analytics missing", "Progress analytics (topic mastery, priorities) is not joined to retrieval-based tutoring."),
            ("Honest evaluation", "Educational RAG papers report satisfaction or agreement; retrieval hit rate, context size and abstention on a notes corpus are rarely measured."),
            ("Small-scale use", "Published systems assume LLM services or GPUs; a laptop-only, offline platform for one student is not covered.")]
    for i, (k, v) in enumerate(gaps):
        y = 1.45 + i * 1.08
        K.box(s, 0.6, y, 2.6, 0.9, fill=K.NAVY, line=None, radius=0.06)
        K.text(s, 0.6, y, 2.6, 0.9, k, size=16, color=K.WHITE, bold=True, align="c", anchor="m")
        K.text(s, 3.5, y, 9.2, 0.9, v, size=17, color=K.INK, anchor="m")
    notes[9] = ("The first two rows restate the gap in the batch survey. The last three are our reading of the surveyed papers; "
                "they are why the project measures its own retrieval quality instead of quoting results.")

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 2.75, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.5, PROBLEM_STATEMENT, size=19, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "Syllabi, lecture notes, timetables and question banks as PDF, DOCX or TXT; free-text questions; quiz answers"),
                                 ("Output", "Detected subjects and topics, answers with cited source passages, quizzes, a ranked roadmap, a dashboard"),
                                 ("Users", "Students (the platform keeps each student's documents and results separate)")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.5, 3.85, 2.0)
        K.text(s, x + 0.25, 4.62, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.05, 3.4, 1.1, b_, size=14, color=K.TXT)
    notes[10] = "Read the statement slowly: the input is the student's own files, the output is a cited answer plus an adaptive plan, and each student's data is private."

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 5.4, [(f"{i}.  {o}", {"space_after": 10}) for i, o in enumerate(OBJECTIVES, 1)], size=22, color=K.INK)
    notes[11] = "The six objectives from the proposal. Later reviews report which were met and which only partly (for example embeddings and compression)."

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Ingest", "Extract text from PDF, DOCX and TXT, clean it, cut it into 180-word chunks, detect subject and unit headings and TF-IDF keywords as topics.", K.BLUE, "1"),
        ("Retrieve", "Index each student's chunks (TF-IDF, cosine similarity) and fetch the top passages for a question; baselines BM25 and dense embeddings are compared.", K.GREEN, "2"),
        ("Answer", "Select the key sentences of the retrieved passages (offline) or send them to an optional LLM; always show the source file and passage.", K.ORANGE, "3"),
        ("Adapt", "Generate fill-in-the-blank quizzes from the notes, grade them, and rank topics High, Medium or Low by accuracy for the roadmap and dashboard.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.4, t, b_, col, gl, body_size=14)
    K.box(s, 0.6, 5.1, 12.13, 1.5)
    K.circle(s, 0.85, 5.4, 0.7, K.NAVY, "W", 18)
    K.text(s, 1.8, 5.3, 10.7, 0.5, "Application", size=17, color=K.INK, bold=True)
    K.text(s, 1.8, 5.8, 10.7, 0.75, "FastAPI service (14 endpoints) with a signed-cookie login and SQLite storage, a React interface (upload, documents, ask, quiz, roadmap, dashboard) and the original Flask pages.", size=15, color=K.TXT)
    notes[12] = "Four stages from files to an adaptive plan, and the application around them. The compression idea from [1] is approximated by extractive sentence selection."

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 2.0, 1.3, 9.3, 5.3)
    K.text(s, 0.6, 6.62, 12.13, 0.3, "The React interface calls the FastAPI service; retrieval, document analysis and quiz modules share one SQLite database and an uploads folder", size=12, color=K.TXT, align="c", italic=True)
    notes[13] = "Follow the diagram: the browser on the left, the API with the retrieval and quiz modules in the middle, storage on the right, and the optional LLM below."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    outs = [("Document repository", "Subjects, units and topics detected per upload; chunks stored per student.", K.BLUE, "1"),
            ("Cited answers", "Every answer lists the source file, passage number and match score.", K.GREEN, "2"),
            ("Context compression", "A short answer from a long retrieved context; we measure what it costs in recall.", K.ORANGE, "3"),
            ("Adaptive roadmap", "Topics ranked High, Medium or Low from quiz accuracy.", K.PURPLE, "4"),
            ("Honest evaluation", "Hit@k and MRR on 72 questions over a 672-chunk corpus, abstention, quiz quality, latency and an 84-test suite.", K.BLUE, "5"),
            ("Reproducibility", "Scripts rebuild the corpus, metrics, figures, screenshots and tests.", K.GREEN, "6")]
    for i, (t, b_, col, gl) in enumerate(outs):
        r, c = divmod(i, 3)
        K.card(s, 0.6 + c * 4.14, 1.5 + r * 2.7, 3.85, 2.5, t, b_, col, gl, body_size=15)
    notes[14] = ("Expected outcomes. The baseline already measured for the shipped retriever is Hit@4 0.792 on 672 chunks; "
                 "we report whatever the experiments show, including where objectives are only partly met.")

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    idx = [n for n in (1, 2, 3, 4, 5, 6, 7, 8) if n <= len(REFS)]
    half = (len(idx) + 1) // 2
    K.text(s, 0.6, 1.35, 5.95, 5.5, [(f"[{n}] {REFS[n - 1]}", {"space_after": 8}) for n in idx[:half]], size=14, color=K.INK)
    K.text(s, 6.78, 1.35, 5.95, 5.5, [(f"[{n}] {REFS[n - 1]}", {"space_after": 8}) for n in idx[half:]], size=14, color=K.INK)
    notes[15] = "Selected references; the complete numbered list, including the four batch-survey items, is in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = "Likely questions: why TF-IDF and not embeddings; what 'compression' means here; what happens without an LLM key; how the roadmap decides priority."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "Adaptive Learning")
    return out_path


if __name__ == "__main__":
    p = build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx"))
    print(p, scan_deck(p))
