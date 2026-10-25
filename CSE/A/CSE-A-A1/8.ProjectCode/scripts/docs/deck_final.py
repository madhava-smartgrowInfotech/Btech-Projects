"""16.Final_PPT.pptx: 28 slides. Built from D:\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited).

All numbers come from scripts/docs/facts.py (experiments/*.json). References use the fixed numbering [1]-[22] of the report.
"""

import os
import re
import zipfile
from collections import Counter

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520

# short IEEE entries for the references slide (numbering fixed for all documents)
REF_SHORT = {
    1: "D. Zhang, H. Yu, J. Huo and M. Su, \"SAC-RAG: Semantic adaptive context compression for retrieval-augmented generation,\" IEEE Access, vol. 14, pp. 117406-117418, 2026, doi: 10.1109/ACCESS.2026.3718025.",
    2: "Z. Li et al., \"TutorLLM: Customizing learning recommendations with knowledge tracing and retrieval-augmented generation,\" arXiv:2502.15709, 2025.",
    3: "R. Vatankhah Barenji, N. Salimi and S. Khoshgoftar, \"An LLM-powered assessment retrieval-augmented generation (RAG) for higher education,\" arXiv:2601.06141, 2026.",
    4: "P. Lewis et al., \"Retrieval-augmented generation for knowledge-intensive NLP tasks,\" in Proc. NeurIPS, vol. 33, 2020, pp. 9459-9474.",
    5: "V. Karpukhin et al., \"Dense passage retrieval for open-domain question answering,\" in Proc. EMNLP, 2020, pp. 6769-6781.",
    6: "S. Robertson and H. Zaragoza, \"The probabilistic relevance framework: BM25 and beyond,\" Found. Trends Inf. Retr., vol. 3, no. 4, pp. 333-389, 2009.",
    7: "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Inf. Process. Manage., vol. 24, no. 5, pp. 513-523, 1988.",
    8: "S. Deerwester et al., \"Indexing by latent semantic analysis,\" J. Amer. Soc. Inf. Sci., vol. 41, no. 6, pp. 391-407, 1990.",
    9: "S. Xiao et al., \"C-Pack: Packaged resources to advance general Chinese embedding,\" arXiv:2309.07597, 2023 (BGE models).",
    10: "H. Jiang et al., \"LLMLingua: Compressing prompts for accelerated inference of large language models,\" in Proc. EMNLP, 2023, pp. 13358-13376.",
    11: "S. Jeong et al., \"Adaptive-RAG: Learning to adapt retrieval-augmented large language models through question complexity,\" in Proc. NAACL, 2024, pp. 7036-7050.",
    12: "N. F. Liu et al., \"Lost in the middle: How language models use long contexts,\" Trans. Assoc. Comput. Linguistics, vol. 12, pp. 157-173, 2024.",
    13: "Z. Yang et al., \"HotpotQA: A dataset for diverse, explainable multi-hop question answering,\" in Proc. EMNLP, 2018, pp. 2369-2380.",
    14: "A. Asai et al., \"Self-RAG: Learning to retrieve, generate, and critique through self-reflection,\" arXiv:2310.11511, 2023.",
    15: "F. Xu, W. Shi and E. Choi, \"RECOMP: Improving retrieval-augmented LMs with compression and selective augmentation,\" arXiv:2310.04408, 2023.",
    16: "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.",
    17: "A. T. Corbett and J. R. Anderson, \"Knowledge tracing: Modeling the acquisition of procedural knowledge,\" User Model. User-Adapt. Interact., vol. 4, no. 4, pp. 253-278, 1994.",
    18: "Wikipedia contributors, English Wikipedia (articles pinned by revision id), text under CC BY-SA 4.0, 2026.",
}

OBJECTIVES = [
    "Build a document ingestion module that parses syllabi, lecture notes and question banks and extracts subjects, units and topics.",
    "Store the extracted content as vector embeddings so the material can be searched semantically rather than by keyword.",
    "Implement a RAG question-answering engine that answers strictly from the uploaded material and cites the source.",
    "Apply semantic context compression so retrieval stays accurate without exceeding the model context window.",
    "Generate personalised study roadmaps and revision schedules from topic coverage and performance.",
    "Present curriculum coverage, study velocity and engagement metrics on an interactive dashboard.",
]


def chrome(sh):
    return sh.top in (TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT)


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if sh.top == TOP_TITLE:
            K.replace_text(sh, text, size)
            return


def wipe(slide):
    K.clear(slide, chrome)


def fbox(slide, x, y, w, h, fill=K.FHEAD, line=None):
    return K.box(slide, x, y, w, h, fill=fill, line=line, radius=0.04)


def ftable(slide, x, y, widths, rows, size=13, row_h=0.45, align=None, first_bold=True):
    return K.table(slide, x, y, widths, rows, font_size=size, row_h=row_h, header_fill=K.FHEAD, header_color=K.FNAVY, zebra=K.FZEBRA,
                   body_color=K.DARK, first_bold=first_bold, font=FONT, align=align, border=K.RGBColor(0xBF, 0xBF, 0xBF))


def ftext(slide, x, y, w, h, paras, size=16, color=K.DARK, **kw):
    return K.text(slide, x, y, w, h, paras, size=size, color=color, font=FONT, **kw)


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=12, color=K.DARK, font=FONT)


def scan_deck(path):
    """Slide count and any banned template words left in the package (text, notes, XML)."""
    banned = ["Fakeddit", "PHEME", "Snopes", "MCNN", "bank transaction", "social media manipulation", "[STUDENT NAME", "[ROLL NO",
              "Fraud", "FraudShield", "Sindhuja", "Sarwosri"]
    prs = Presentation(path)
    hits = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith(".xml") or n.endswith(".rels"):
                txt = z.read(n).decode("utf-8", "ignore")
                for b in banned:
                    if b in txt:
                        hits.append((n, b))
    return len(prs.slides), hits


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE"
    cp.comments = ""
    cp.subject = F.PRODUCT
    cp.keywords = "adaptive learning, retrieval-augmented generation, learning analytics, TF-IDF"
    cp.last_modified_by = ""
    notes = {}
    RET, CMP, ABS, DA, QZ = F.RET, F.CMP, F.ABS, F.DOCAN, F.QUIZ
    sh_ = F.SHIPPED
    h = lambda name, k: F.hit(name, k)

    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    s = S[0]
    for sh in s.shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.TITLE, 24)
        elif sh.name == "Text 2":
            K.replace_text(sh, f"Final Review  ·  {F.PRODUCT}")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_.upper()}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and the project: a platform that analyses a student's own study documents, answers questions from them with sources, and adapts a study roadmap to quiz results."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Dataset & Parameters\nDecision Workflow, Interaction & Database\nImplementation Highlights\nResults, Question Types & Parameter Analysis\nPerformance & Testing\nComparison with the Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, measured results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [
        ("Students keep syllabi, notes and question banks in scattered files; portals store them but do not read them, and general chatbots answer from the internet, not from the student's own curriculum.", {"bullet": True, "space_after": 9}),
        ("The Adaptive Learning Intelligence Platform ingests PDF, DOCX and TXT material, detects subjects, units and topics, answers questions from the uploaded text with cited source passages (TF-IDF retrieval, extractive answer, optional Claude), generates fill-in-the-blank quizzes and ranks topics by quiz accuracy in a study roadmap.", {"bullet": True, "space_after": 9}),
        (f"Measured on a {F.CORPUS['chunks']}-chunk, six-subject notes corpus with {F.CORPUS['questions']} questions: the shipped retriever finds the evidence in the top 4 chunks for **{F.pct(h(sh_, 4), 1)}** of questions (Hit@4); BM25 + dense retrieval reaches {F.pct(h('hybrid_bm25_dense', 4), 1)}. Sentence selection removes {CMP['4']['token_reduction_pct']:.1f}% of the words but lowers answer-key recall from {CMP['4']['key_in_ctx']:.3f} to {CMP['4']['key_in_ans']:.3f}.", {"bullet": True, "space_after": 9}),
        (f"{F.TESTS['tests']} automated tests pass; an ask request takes {F.API['ask']['median_ms']:.0f} ms (median) on the local machine.", {"bullet": True, "space_after": 9}),
        ("Gaps stated plainly: no learned embeddings, no SAC-RAG question-type routing or LLM compression, no relevance threshold, Claude mode not measured.", {"bullet": True}),
    ], size=17)
    notes[3] = "Read the first two bullets, then the headline numbers with their protocol, then the honest gaps."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.75, REF_SHORT[1] + " [1]", size=12, color=K.FNAVY)
    rows = [["Aspect", "SAC-RAG [1] (base paper)", "This project"],
            ["Problem", "Standard RAG uses one retrieval strategy for all questions and feeds redundant chunks to the generator (high token cost) [1]", "Students cannot search or be tutored from their own notes; answers must come from the uploaded files"],
            ["Method", "LLM classifies the question (fact / definition / reasoning), type-specific retrieval (BM25 + dense + rerank, dense only, or sub-question decomposition), LLM context compression, generation", "TF-IDF retrieval over the user's chunks, top 4; extractive sentence selection; optional Claude generation; quiz and roadmap layers"],
            ["Evaluation", "HotpotQA, 2WikiMultiHopQA, MuSiQue, 1,000 questions each; EM, F1, Recall@10, tokens; gpt-5-mini", f"{F.CORPUS['questions']} questions over {F.CORPUS['chunks']} chunks; Hit@k, MRR, answer-key recall, words"],
            ["Headline result", "Tokens reduced 38-58% for a 1-2 point EM drop; HotpotQA Recall@10 0.787 to 0.880 with adaptive retrieval", f"Words reduced {CMP['4']['token_reduction_pct']:.1f}%; Hit@4 {h(sh_, 4):.3f} (shipped), {h('hybrid_bm25_dense', 4):.3f} (BM25 + dense)"],
            ["Adopted / not adopted", "Idea of retrieve, compress, then answer; question types used only to analyse results", "Question-type routing, LLM compression and reranking are not implemented"]]
    ftable(s, 0.55, 2.65, [1.7, 5.4, 5.1], rows, size=11.5, row_h=0.72)
    notes[4] = "The base paper is SAC-RAG. We adopt its pipeline idea (retrieve, compress, answer) and its question taxonomy for analysis; the adaptive routing and LLM compression are not implemented, which the report states."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Author / Year", "Methodology", "Data / Setting", "Key Results", "Limitations"],
            ["Zhang et al. 2026 [1]", "SAC-RAG: question-type-adaptive retrieval + LLM compression", "HotpotQA, 2Wiki, MuSiQue", "-38 to -58% tokens for 1-2 pt EM; question classifier 92.0% accurate", "Extra LLM calls: about 27.8 s vs 9.6 s per question"],
            ["Li et al. 2025 [2] TutorLLM", "Knowledge tracing (MLFBK) + RAG + scraper with an LLM for personalised recommendations", "Learner interaction data, user study", "+10% user satisfaction, +5% quiz scores vs general LLMs", "Needs interaction logs; not grounded on a student's own files"],
            ["Vatankhah Barenji et al. 2026 [3]", "Agentic assessment RAG over rubrics, exemplar essays and feedback", "701 student essays", "94-99% agreement with human evaluators", "Grading focus; originality and dialogue limits noted"],
            ["Jeong et al. 2024 [11] Adaptive-RAG", "Routes questions by complexity: no, single or multi-step retrieval", "Open-domain QA", "Better accuracy-cost balance (as cited in [1])", "No context compression [1]"],
            ["Jiang et al. 2023 [10] LLMLingua", "Small-model prompt compression of retrieved context", "Long-prompt benchmarks", "Fewer tokens at fixed task quality (as cited in [1])", "Fixed retrieval pipeline [1]"]]
    ftable(s, 0.55, 1.85, [2.1, 3.2, 2.0, 2.8, 2.1], rows, size=11, row_h=0.74)
    ftext(s, 0.55, 6.55, 12.2, 0.4, "Rows 4-5 are described as reported in [1]; their own result tables were not re-read. Lost in the middle [12] motivates compression. Four further batch-survey titles could not be verified and are listed as unverified in the report.", size=10.5, color=K.FNAVY, italic=True)
    notes[5] = "Representative work. Only facts read from the PDFs we hold are stated; entries 4 to 6 are described as the base paper cites them."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.8, [
        ("**Own curriculum:** RAG work targets general question answering and context compression; none of the surveyed systems combines document ingestion, syllabus-grounded tutoring and progress analytics for a student's own files [1]-[3].", {"bullet": True, "space_after": 12}),
        ("**Structure:** documents are stored but their subjects, units and topics are not extracted.", {"bullet": True, "space_after": 12}),
        ("**Adaptation:** recommendations ignore the individual learner's measured performance.", {"bullet": True, "space_after": 12}),
        ("**Grounding:** chatbots answer from public data and do not show which passage supports an answer.", {"bullet": True, "space_after": 12}),
        ("**Evidence:** educational RAG systems are rarely measured for retrieval accuracy, abstention and compression loss on notes; we measure them.", {"bullet": True}),
    ], size=19)
    notes[6] = "The batch gap is the first bullet. The last bullet is what this report adds: measurement."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.95, 12.2, 2.0)
    ftext(s, 0.85, 2.0, 11.6, 1.9, "Learning platforms store academic files but never extract the units, topics or objectives inside them; recommendations are identical for every learner; chatbots answer from public data rather than the prescribed syllabus; and students have no single view of what is studied, what remains and how well each topic is understood.", size=16, anchor="m")
    for i, (t, b_) in enumerate([("Input", "Syllabi, notes, question banks (PDF, DOCX, TXT), questions in plain language, quiz answers"), ("Output", "Detected topics, cited answers, quizzes, a priority-ranked roadmap and a dashboard"), ("Need", "A platform that ingests the student's own documents, answers strictly from them, and adapts the plan to measured topic mastery")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.3, 3.9, 2.1, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.4, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 4.9, 3.5, 1.4, b_, size=14)
    notes[7] = "The statement comes from the batch problem document; input, output and need summarise it."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=20)
    notes[8] = "The six objectives of the batch proposal. The conclusion states for each whether it was met; objectives 2 and 4 were only partly met."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 2.0, 12.2, 1.1, [("Upload PDF / DOCX / TXT", K.FNAVY), ("Chunks + topics", K.FBLUE), ("TF-IDF index per user", K.GREEN), ("Cited answer", K.ORANGE), ("Quiz, roadmap, dashboard", K.PURPLE)], size=14, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, [
        ("Text is extracted, cleaned and cut into 180-word chunks with 30 words of overlap; subject and unit headings and TF-IDF keywords become the topics (at most 12).", {"bullet": True, "space_after": 10}),
        ("A question is matched to the user's chunks by cosine similarity; the top 4 passages are shown as sources and the most relevant sentences form the answer. With an API key Claude can write the answer from the same context.", {"bullet": True, "space_after": 10}),
        ("Quizzes are fill-in-the-blank questions made from the document's key terms; each answer updates a per-topic accuracy that drives High / Medium / Low priorities.", {"bullet": True, "space_after": 10}),
        ("A FastAPI service (14 endpoints) and a React interface sit over the original Flask project code.", {"bullet": True}),
    ], size=17)
    notes[9] = "The proposed system in one row of boxes, then four properties that matter."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.85, 8.3, 5.0)
    ftext(s, 9.1, 2.0, 3.7, 4.7, [
        ("Browser: React 19 app (port 5301); original Flask pages (5000)", {"bullet": True, "space_after": 8}),
        ("Service: FastAPI (8301), 14 JSON endpoints, signed session cookie", {"bullet": True, "space_after": 8}),
        ("Core: text extraction, per-user TF-IDF engine, quiz generator, roadmap rules", {"bullet": True, "space_after": 8}),
        ("Storage: SQLite (5 tables) and the uploaded files", {"bullet": True}),
    ], size=15)
    notes[10] = "Interfaces on the left, one shared core in the middle, storage on the right; the Anthropic API is optional."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.picture(s, F.diag("02_high_level_workflow.png"), 0.55, 1.85, 7.7, 4.9)
    ftext(s, 8.5, 1.95, 4.3, 4.8, [
        ("One chunking and indexing path for every upload; the index of a user is rebuilt after each upload or delete.", {"bullet": True, "space_after": 9}),
        (f"Evaluation corpus: {len(F.CORPUS['documents'])} subject files built from 36 Wikipedia articles [18], {F.CORPUS['words']:,} words.", {"bullet": True, "space_after": 9}),
        (f"{F.CORPUS['questions']} hand-written questions (fact, definition, reasoning [1]); a hit means a retrieved chunk contains the gold evidence sentence.", {"bullet": True, "space_after": 9}),
        ("Reference retrievers: BM25 [6], LSA [8], dense BGE-small [9] and hybrids, measured on the same chunks.", {"bullet": True}),
    ], size=14)
    notes[11] = "The workflow, and the way it was measured. The reference retrievers exist only in the experiments; the product ships TF-IDF."

    # ---- 12 dataset, parameters
    s = S[11]
    set_title(s, "Dataset, Parameters & Model")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.1, f"{F.CORPUS['words']:,}", "words in 6 subject files", K.FBLUE, 26)
    ftile(s, 0.55, 3.15, 2.9, 1.1, f"{F.CORPUS['chunks']}", "chunks of about 180 words", K.GREEN, 26)
    ftile(s, 0.55, 4.4, 2.9, 1.1, f"{F.CORPUS['questions']} + {F.CORPUS['off_topic_questions']}", "in-scope + off-topic questions", K.ORANGE, 26)
    docs = F.CORPUS["documents"]
    K.bar_chart(s, 3.7, 1.85, 4.8, 3.3, [d["subject"].replace(" Systems", "").replace("Computer ", "") for d in docs], [("Chunks per subject", [d["chunks"] for d in docs])],
                colors=[K.FBLUE], number_format="0", font_size=10, max_value=140)
    rows = [["Component", "Setting"], ["Chunking", "180 words, overlap 30"], ["Retriever", "TF-IDF 1-2 grams, cosine"], ["Top k", "4 chunks (score > 0)"], ["Answer", "top 4 sentences"], ["Quiz", "5 cloze questions"], ["Roadmap", "<50 High, <80 Medium"]]
    ftable(s, 8.7, 1.9, [1.5, 2.6], rows, size=11, row_h=0.45)
    ftext(s, 0.55, 5.7, 12.2, 1.2, "There is no model training: the platform uses TF-IDF vectors fitted on each user's chunks [7], scikit-learn 1.5.1 [16]. Corpus: 36 English Wikipedia articles at pinned revisions (CC BY-SA 4.0) [18], 6 per subject; all 72 questions are test questions; every gold evidence sentence lies inside one chunk (72/72).", size=12, color=K.FNAVY)
    notes[12] = "Dataset and parameters in one view. The platform has no training set; the corpus exists to measure it."

    # ---- 13 decision workflow
    s = S[12]
    set_title(s, "Decision Workflow")
    wipe(s)
    K.picture(s, F.diag("12_flowchart_rag.png"), 0.55, 1.8, 5.0, 5.1)
    ftext(s, 5.9, 2.0, 6.9, 4.8, [
        ("Empty question: rejected (HTTP 400); otherwise the user's cached index is used, or built from SQLite.", {"bullet": True, "space_after": 11}),
        ("Retrieve: cosine similarity with every chunk; keep the top 4 with a score above 0.", {"bullet": True, "space_after": 11}),
        ("Answer: if an API key is set, Claude answers from the chunks only; any failure falls back to the extractive answer.", {"bullet": True, "space_after": 11}),
        ("Extractive answer: rank the sentences of the retrieved chunks against the question and join the top 4.", {"bullet": True, "space_after": 11}),
        ("No chunk with a positive score: 'No relevant content was found'. There is no relevance threshold above zero.", {"bullet": True}),
    ], size=16)
    notes[13] = "The core algorithm of utils/rag_engine.py. The missing threshold is analysed on slide 19."

    # ---- 14 user-system interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("09_sequence_ask.png"), 0.55, 1.8, 6.3, 5.1)
    K.picture(s, F.diag("10_use_case_diagram.png"), 7.1, 1.8, 5.7, 5.1)
    notes[14] = "Sequence of one Ask request, and the use cases of the single user role."

    # ---- 15 database
    s = S[14]
    set_title(s, "Database Design")
    wipe(s)
    K.picture(s, F.diag("11_er_diagram.png"), 0.55, 1.8, 7.0, 4.7)
    rows = [["Table", "Holds"], ["users", "name, password hash, interests"], ["documents", "file, subject, topics (JSON)"], ["chunks", "180-word passages"], ["queries", "question, answer, sources"], ["quiz_results", "subject, topic, correct 0/1"]]
    ftable(s, 7.8, 1.9, [1.7, 3.3], rows, size=12, row_h=0.5)
    ftext(s, 7.8, 5.1, 5.0, 1.6, "SQLite with foreign keys and ON DELETE CASCADE; uploaded originals stay on disk under uploads/<user id>/.", size=13, color=K.FNAVY, italic=True)
    notes[15] = "Five tables; users own documents, queries and quiz results; documents own chunks."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("14", "REST endpoints (+ /api/docs)", K.FBLUE), (str(F.TESTS["tests"]), "pytest tests, all pass", K.GREEN), ("10", "React pages (light and dark)", K.ORANGE), ("1,252", "lines of Python application code", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.3, 12.2, 3.5, [
        ("FastAPI layer reuses the original db.py and utils modules unchanged, so the Flask and React interfaces give the same answers; the per-user index is cached in memory.", {"bullet": True, "space_after": 9}),
        ("Passwords are hashed (scrypt/pbkdf2); session cookie is HttpOnly and SameSite=Lax; file names pass secure_filename; only PDF, DOCX and TXT up to 16 MB are accepted; CORS allows only the front-end origin.", {"bullet": True, "space_after": 9}),
        ("Quiz answers stay on the server until grading; every query is filtered by the logged-in user id, so users never see each other's documents.", {"bullet": True, "space_after": 9}),
        ("React app: TanStack Query, Recharts, 53 TypeScript files (4,867 lines); the production build and type check succeed.", {"bullet": True}),
    ], size=16)
    notes[16] = "Highlights: reuse of the original code, security measures that tests check, and the size of the code."

    # ---- 17 results: retrieval performance
    s = S[16]
    set_title(s, f"Results – Retrieval Quality ({F.CORPUS['chunks']} chunks, {F.CORPUS['questions']} questions)")
    wipe(s)
    names = ["tfidf_shipped (1-2gram)", "tfidf_unigram", "bm25", "tfidf_lsa200", "hybrid_bm25_lsa", "dense_bge_small", "hybrid_bm25_dense"]
    rows = [["Retriever", "Hit@1", "Hit@3", "Hit@4", "Hit@10", "MRR@10"]] + [F.ret_row(n) for n in names]
    ftable(s, 0.55, 1.85, [3.0, 0.95, 0.95, 0.95, 0.95, 1.05], rows, size=12.5, row_h=0.46, align=["l", "c", "c", "c", "c", "c"])
    ftext(s, 0.55, 5.7, 8.5, 1.2, f"Hit@k: a retrieved chunk among the top k contains the gold evidence sentence. 95% bootstrap interval of the shipped retriever: Hit@1 {F.RET_CI['hit1'][0]:.2f}-{F.RET_CI['hit1'][1]:.2f}, Hit@4 {F.RET_CI['hit4'][0]:.2f}-{F.RET_CI['hit4'][1]:.2f}. With 72 questions, gaps of a few points are within noise. Dense model: BGE-small, quantised ONNX [9], reference only.", size=11.5, color=K.FNAVY)
    K.card(s, 9.3, 1.85, 3.5, 3.9, "Reading", f"BM25 beats the shipped TF-IDF at Hit@1 ({h('bm25', 1):.3f} vs {h(sh_, 1):.3f}). BM25 + dense is best on every column (Hit@4 {h('hybrid_bm25_dense', 4):.3f}). The shipped retriever is lexical, so the 'semantic search' objective is not met by the product itself.", K.FBLUE, "i", body_size=13)
    notes[17] = "The headline retrieval table. Stress that the shipped retriever is TF-IDF, that BM25 and the hybrid are better, and that the interval is wide."

    # ---- 18 question types / first-rank breakdown (confusion-matrix equivalent)
    s = S[17]
    set_title(s, "Where the Evidence Is Found, by Question Type")
    wipe(s)
    rows = [["Retriever", "Rank 1", "Rank 2-4", "Rank 5-10", "Not in top 10"]]
    for n in ("tfidf_shipped (1-2gram)", "bm25", "hybrid_bm25_dense"):
        c = Counter("r1" if r == 1 else "r24" if r and r <= 4 else "r510" if r else "miss" for r in RET[n]["first_rank"])
        rows.append([F.RET_LABELS[n], str(c["r1"]), str(c["r24"]), str(c["r510"]), str(c["miss"])])
    ftable(s, 0.55, 1.85, [3.2, 1.6, 1.6, 1.6, 1.8], rows, size=12.5, row_h=0.42, align=["l", "c", "c", "c", "c"])
    ftext(s, 10.6, 1.85, 2.3, 1.7, "Rank of the first chunk that contains the evidence (counts of 72 questions).", size=11, color=K.FNAVY, italic=True)
    K.picture(s, F.fig("fig_by_type.png"), 0.55, 3.7, 7.4, 3.2)
    bt = RET[sh_]["by_type"]
    ftext(s, 8.2, 3.75, 4.6, 3.2, [
        (f"Shipped Hit@4: fact {bt['fact']['hit4']:.3f}, definition {bt['definition']['hit4']:.3f}, reasoning {bt['reasoning']['hit4']:.3f} (24 questions each).", {"bullet": True, "space_after": 7}),
        (f"Hit@1 is low for definitions ({bt['definition']['hit1']:.3f}): many chunks mention the term, the defining one is not first.", {"bullet": True, "space_after": 7}),
        (f"BM25 + dense lifts definition Hit@4 to {RET['hybrid_bm25_dense']['by_type']['definition']['hit4']:.3f}; BM25 gives fact Hit@4 {RET['bm25']['by_type']['fact']['hit4']:.3f}.", {"bullet": True, "space_after": 7}),
        ("Question types are the three of the base paper [1], assigned from the wording.", {"bullet": True}),
    ], size=12.5)
    notes[18] = "This is the equivalent of a confusion matrix for retrieval: where the first correct chunk lands. Five questions of 72 have no hit in the top 10 for the shipped retriever."

    # ---- 19 parameter analysis
    s = S[18]
    set_title(s, "Parameter Analysis: Refusal Threshold, Compression, Chunk Size")
    wipe(s)
    K.picture(s, F.fig("fig_abstention.png"), 0.55, 1.8, 6.1, 3.0)
    K.picture(s, F.fig("fig_compression.png"), 6.9, 1.8, 5.9, 3.0)
    sw = {round(x["tau"], 2): x for x in ABS["sweep"]}
    ftext(s, 0.55, 4.85, 6.1, 0.55, f"Shipped engine answered {ABS['off_topic_answered_by_shipped']} of {ABS['n_off_topic']} off-topic questions. A threshold of 0.15 on the top-1 score would answer {sw[0.15]['in_scope_answered'] * 100:.0f}% of in-scope and refuse {sw[0.15]['off_topic_refused'] * 100:.0f}% of off-topic questions (not implemented).", size=10.5, color=K.FNAVY)
    ftext(s, 6.9, 4.85, 5.9, 0.55, f"At k = 4: {CMP['4']['token_reduction_pct']:.1f}% fewer words, answer-key recall {CMP['4']['key_in_ctx']:.3f} in the chunks vs {CMP['4']['key_in_ans']:.3f} in the extractive answer.", size=10.5, color=K.FNAVY)
    cs = F.CHUNKS
    rows = [["Chunk size / overlap"] + list(cs), ["Chunks"] + [f"{v['chunks']:,}" for v in cs.values()], ["Hit@1"] + [f"{v['hit1']:.3f}" for v in cs.values()],
            ["Hit@4"] + [f"{v['hit4']:.3f}" for v in cs.values()], ["MRR@10"] + [f"{v['mrr10']:.3f}" for v in cs.values()]]
    ftable(s, 0.55, 5.45, [2.6] + [1.9] * 5, rows, size=10.5, row_h=0.27, align=["l"] + ["c"] * 5)
    notes[19] = "Three parameter sweeps. Larger chunks score higher because there are fewer of them and each carries more words, so compare with care; 180/30 is the shipped setting."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    A = F.API
    for i, (v, l, c) in enumerate([(f"{A['ask']['median_ms']:.0f} ms", f"POST /api/ask, median (p95 {A['ask']['p95_ms']:.0f})", K.FBLUE), (f"{A['quiz_generate']['median_ms']:.0f} ms", "quiz generate, median", K.GREEN),
                                   (f"{A['login']['median_ms']:.0f} ms", "login (password hashing), median", K.ORANGE), (f"{F.SCALE[0]['answer_ms_median']:.1f} ms", f"retrieve + answer, {F.SCALE[0]['chunks']} chunks, in process", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.15, v, l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["API and roadmap", "registration, login, uploads, delete, ask, quiz, roadmap thresholds, dashboard, isolation between users", f"{F.TEST_FILES['test_api.py']} / {F.TEST_FILES['test_api.py']}"],
            ["Text extraction", "TXT, DOCX, PDF, scans, corrupt files, chunking, hints, topics", f"{F.TEST_FILES['test_text_extraction.py']} / {F.TEST_FILES['test_text_extraction.py']}"],
            ["Security", "401s, hashing, injection strings, path traversal, cookie flags, CORS", f"{F.TEST_FILES['test_security.py']} / {F.TEST_FILES['test_security.py']}"],
            ["Engine and quiz", "retrieval, extractive answer, LLM fallback, quiz structure", f"{F.TEST_FILES['test_rag_engine.py'] + F.TEST_FILES['test_quiz_generator.py']} / {F.TEST_FILES['test_rag_engine.py'] + F.TEST_FILES['test_quiz_generator.py']}"],
            ["Smoke test", "running server, every endpoint the React app uses", f"{F.SMOKE_TOTAL} / {F.SMOKE_TOTAL}"]]
    ftable(s, 0.55, 3.3, [2.6, 7.2, 2.4], rows, size=12.5, row_h=0.48)
    ftext(s, 0.55, 6.3, 12.2, 0.65, f"Total {F.TESTS['tests']} tests, {F.TESTS['failures']} failures, {F.TESTS['seconds']:.0f} s. 127.0.0.1, one user, CPU only. quiz submit showed 1-2 s outliers on 1-2 of 30 calls (SQLite commit, cause not isolated). Not tested: Claude mode (no API key), concurrent users, OCR, real syllabi, a user study.", size=11.5, color=K.FNAVY, italic=True)
    notes[20] = "84 pytest tests plus the 24-check smoke test. Latencies are medians of 30 calls. The limits of the testing are stated on the slide."

    # ---- 21 comparison with the base paper
    s = S[20]
    set_title(s, "Comparison with the Base Paper (context only – data differ)")
    wipe(s)
    rows = [["Aspect", "SAC-RAG [1]", "This project"],
            ["Task and data", "Multi-hop QA: HotpotQA, 2Wiki, MuSiQue, 1,000 questions each", f"Notes QA: 36 Wikipedia articles, {F.CORPUS['chunks']} chunks, {F.CORPUS['questions']} questions"],
            ["Retrieval", "Type-adaptive: BM25 + dense (1,536-d) + BGE rerank; dense only; decomposition", f"TF-IDF cosine, no routing; BM25 + dense measured as reference (Hit@4 {h('hybrid_bm25_dense', 4):.3f})"],
            ["Compression", "LLM extracts evidence snippets", "Extractive sentence selection (top 4 sentences)"],
            ["Generator", "gpt-5-mini, temperature 0", "None by default; optional Claude (not measured)"],
            ["Compression result", "Tokens -38 to -58%, EM -1 to -2 points", f"Words -{CMP['4']['token_reduction_pct']:.1f}%, answer-key recall {CMP['4']['key_in_ctx']:.3f} to {CMP['4']['key_in_ans']:.3f}"],
            ["Retrieval result", "HotpotQA Recall@10 0.787 to 0.880 (adaptive)", f"Hit@10 {h(sh_, 10):.3f} (shipped), {h('hybrid_bm25_dense', 10):.3f} (BM25 + dense)"],
            ["Latency", "About 27.8 s vs 9.6 s per question (extra LLM calls)", f"{F.API['ask']['median_ms']:.0f} ms median per ask (no LLM calls)"]]
    ftable(s, 0.55, 1.85, [2.0, 5.0, 5.2], rows, size=12, row_h=0.56)
    ftext(s, 0.55, 6.45, 12.2, 0.5, "Different datasets, models and metrics: the numbers are not comparable. Only the pattern is: compression saves most words but loses evidence, and dense plus lexical retrieval beats lexical alone.", size=12, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that the datasets and conditions differ. No superiority is claimed."

    # ---- 22-24 output screens
    def shots(i, title, f1, f2, c1, c2, cap):
        s = S[i]
        set_title(s, title)
        wipe(s)
        K.picture(s, F.shot(f1), 0.55, 1.85, 6.0, 3.75, border=True)
        K.picture(s, F.shot(f2), 6.8, 1.85, 6.0, 3.75, border=True)
        ftext(s, 0.55, 5.7, 6.0, 1.25, c1, size=12, color=K.FNAVY)
        ftext(s, 6.8, 5.7, 6.0, 1.25, c2, size=12, color=K.FNAVY)
        return cap

    notes[22] = shots(21, "Output – Upload and Documents", "06_upload-done.png", "08_documents.png",
                      "Upload: 'sample_notes_data_structures.txt' processed, 12 topics detected (Subject and Unit headings first, then TF-IDF keywords), 4 chunks indexed.",
                      "Documents: five uploaded files with subject, detected topics (Unit titles such as 'Deadlock (computer science)'), chunk counts 101, 104, 112, 114 and 4, quiz and delete buttons.",
                      "Real screenshots of the running application with the demo corpus uploaded.")
    notes[23] = shots(22, "Output – Ask Your Notes and Quiz Result", "09_ask.png", "12_quiz-result.png",
                      "Ask: 'What is a deadlock?' is answered from 02_Operating_Systems.txt passage 8 (match 0.46) with the 'Offline mode: key sentences from your notes' badge; recent questions at right.",
                      "Quiz result: 80% (4 of 5) on the sample notes, with the correct term and topic for each question.",
                      "The answer is extractive, so it quotes sentences; the sources panel shows where each came from.")
    notes[24] = shots(23, "Output – Dashboard and Study Roadmap", "07_dashboard.png", "13_roadmap.png",
                      "Dashboard: 5 documents, 4 questions, 40 quiz questions; subject accuracy Data Structures 85%, Algorithms 80%, Operating Systems 60%, Database Systems 30%.",
                      "Roadmap: 30 topics ranked, High 9, Medium 2, Low 19. Topics are single TF-IDF keywords, some generic ('using', 'used', 'normal').",
                      "Quiz answers for these screens were scripted to simulate different mastery per subject; the application, documents and numbers are real.")

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [
        ("**Delivered:** a working platform: document ingestion with topic detection, cited question answering over the user's own files, quizzes, a priority roadmap and dashboard, a FastAPI service and a React interface, with 84 passing tests.", {"bullet": True, "space_after": 10}),
        (f"**Measured:** the shipped TF-IDF retriever finds the evidence in the top 4 chunks for {F.pct(h(sh_, 4), 1)} of questions; BM25 + dense reaches {F.pct(h('hybrid_bm25_dense', 4), 1)}. Extractive compression removes {CMP['4']['token_reduction_pct']:.1f}% of the words at the cost of answer-key recall ({CMP['4']['key_in_ctx']:.3f} to {CMP['4']['key_in_ans']:.3f}).", {"bullet": True, "space_after": 10}),
        ("**Objectives:** 3 met in extractive mode; 1, 4, 5 and 6 partly met; 2 (embeddings) not met by the shipped code.", {"bullet": True, "space_after": 10}),
        ("**Limits:** no relevance threshold (9 of 12 off-topic questions still answered), only 17 of 30 reviewed quiz questions acceptable, no question-type routing, Claude mode and real-student use not measured.", {"bullet": True}),
    ], size=21)
    notes[25] = "Be explicit about which objectives were met and which were not."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [
        ("Replace or combine the retriever with BM25 and a dense model [6], [9]; add a relevance threshold near 0.15 so off-topic questions are refused.", {"bullet": True, "space_after": 11}),
        ("Add SAC-RAG-style question-type routing and LLM context compression [1], and measure the Claude answer mode on the same questions.", {"bullet": True, "space_after": 11}),
        ("Recognise Roman-numeral and 'Module' headings, read DOCX tables, add OCR for scanned PDFs.", {"bullet": True, "space_after": 11}),
        ("Better quizzes: whole-sentence questions, no leaked answers, concept-level topics instead of single keywords.", {"bullet": True, "space_after": 11}),
        ("Knowledge tracing and spaced-repetition schedules [2], [17]; coverage and study-velocity metrics; unique file names per upload; multi-process deployment.", {"bullet": True}),
    ], size=21)
    notes[26] = "Concrete next steps, ordered by the gaps measured in this report."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    ids = list(range(1, 19))
    half = 9
    ftext(s, 0.55, 1.8, 6.1, 5.1, [(f"[{n}] {REF_SHORT[n]}", {"space_after": 3}) for n in ids[:half]], size=11)
    ftext(s, 6.8, 1.8, 6.0, 5.1, [(f"[{n}] {REF_SHORT[n]}", {"space_after": 3}) for n in ids[half:]], size=11)
    notes[27] = "Selected references; the complete numbered list, including the batch-survey titles, is in the report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "Adaptive")
    return out_path


if __name__ == "__main__":
    p = build(os.path.join(F.BATCH, "16.Final_PPT.pptx"))
    print(p, scan_deck(p))
