"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for the Adaptive Learning Intelligence Platform from facts.py
(experiments/*.json), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from . import refs as REFMOD
from .paper import Paper

pct, f2, f3 = F.pct, F.f2, F.f3


def c(*nums):
    """Citation marker resolved by Paper.expand (global reference numbers in refs.py)."""
    return "{r:%s}" % ",".join(str(n) for n in nums)


# --------------------------------------------------------------------------- figures
def _box(ax, x, y, w, h, text, fc="#F2F5FA", ec="#1F4E79", fs=10, bold=False):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=1.5))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, p, q, color="#475569", ls="-", lw=1.5):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0))


def make_figures():
    """Compact figures for the paper, written to docs/figures/paper_*.png (large type so they read at column width)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 11})
    out = {}
    BLUE, GREEN, ORANGE, PURPLE, GOLD, GREY = "#2B6CB0", "#14907F", "#D9772F", "#6B52D6", "#C98A0B", "#64748B"

    # ---- Fig. 1 architecture
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")
    _box(ax, 1, 40, 26, 17, "Browser\nReact 19 SPA\nport 5301", "#E8F0FC", BLUE, 10.5, True)
    _box(ax, 37, 40, 28, 17, "FastAPI service\n14 JSON routes\nsession cookie, port 8301", "#E6F6EF", GREEN, 10, True)
    _box(ax, 75, 40, 24, 17, "Anthropic API\n(optional, key\nneeded)", "#F1F5F9", GREY, 10)
    _box(ax, 1, 14, 26, 17, "text_extraction\nPDF / DOCX / TXT\nchunks 180/30\ntopics", "#EFE9FB", PURPLE, 9.5)
    _box(ax, 37, 14, 28, 17, "RAGEngine\nTF-IDF 1-2 grams\ncosine, top 4\nextractive answer", "#EFE9FB", PURPLE, 9.5)
    _box(ax, 75, 14, 24, 17, "quiz_generator\n5 cloze items\nroadmap rules", "#EFE9FB", PURPLE, 9.5)
    _box(ax, 1, 0.5, 40, 9, "SQLite: 5 tables", "#FFF8E5", GOLD, 9)
    _box(ax, 50, 0.5, 49, 9, "uploaded files; per-user index in memory", "#FFF8E5", GOLD, 9)
    _arrow(ax, (27, 51), (37, 51), BLUE); _arrow(ax, (37, 46), (27, 46), BLUE)
    ax.text(32, 54.5, "JSON", ha="center", fontsize=9, color=BLUE)
    _arrow(ax, (65, 49), (75, 49), GREY, "--"); ax.text(70, 52.5, "if key", ha="center", fontsize=9, color=GREY)
    for x in (14, 51, 87):
        _arrow(ax, (x if x != 51 else 51, 40), (x if x != 51 else 51, 31), GREEN)
    _arrow(ax, (14, 14), (14, 9.5), GOLD); _arrow(ax, (51, 14), (51, 9.5), GOLD); _arrow(ax, (87, 14), (87, 9.5), GOLD, "--")
    out["arch"] = os.path.join(F.FIGS, "paper_architecture.png")
    fig.savefig(out["arch"], dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---- Fig. 2 main flow
    fig, ax = plt.subplots(figsize=(6.8, 4.1))
    ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")
    ax.text(1, 59.5, "Ingest (once per file)", fontsize=10, color=PURPLE, fontweight="bold")
    steps = ["Upload\nfile", "Extract\ntext", "Clean, chunk\n180 / 30 words", "Hints +\ntopics (12)", "Store rows,\nre-index"]
    xs = [1, 21, 41, 61, 81]
    for i, (x, t) in enumerate(zip(xs, steps)):
        _box(ax, x, 44, 18, 12, t, "#EFE9FB", PURPLE, 9.5)
        if i:
            _arrow(ax, (xs[i - 1] + 18, 50), (x, 50), PURPLE)
    ax.text(1, 38, "Answer (every question)", fontsize=10, color=GREEN, fontweight="bold")
    _box(ax, 1, 21, 15, 12, "Question", "#E6F6EF", GREEN, 9.5)
    _box(ax, 21, 21, 20, 12, "TF-IDF cosine\nvs all chunks", "#E6F6EF", GREEN, 9.5)
    _box(ax, 46, 21, 17, 12, "Top 4 with\nscore > 0", "#E6F6EF", GREEN, 9.5)
    ax.add_patch(Polygon([(75, 33), (83, 27), (75, 21), (67, 27)], fc="#FFF8E5", ec=GOLD, lw=1.5))
    ax.text(75, 27, "key?", ha="center", va="center", fontsize=9.5)
    _box(ax, 87, 28, 12, 7, "LLM", "#F1F5F9", GREY, 9.5)
    _box(ax, 64, 4, 36, 11, "Extractive: top 4 sentences\nAnswer + cited passages", "#E6F6EF", GREEN, 9.5, True)
    _arrow(ax, (16, 27), (21, 27), GREEN); _arrow(ax, (41, 27), (46, 27), GREEN); _arrow(ax, (63, 27), (67, 27), GREEN)
    _arrow(ax, (83, 29.5), (87, 31.5), GREY, "--"); ax.text(85, 24.8, "yes", fontsize=8.5, color=GREY)
    _arrow(ax, (75, 21), (75, 15), GREEN); ax.text(77, 17.5, "no / error", fontsize=8.5, color=GREEN)
    _arrow(ax, (93, 28), (93, 15), GREY, "--")
    ax.annotate("", xy=(30, 33.6), xytext=(90, 44), arrowprops=dict(arrowstyle="-|>", color=PURPLE, lw=1.3, ls="--", connectionstyle="arc3,rad=-0.15"))
    ax.text(58, 40, "index used for retrieval", fontsize=8.5, color=PURPLE, ha="center")
    out["flow"] = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(out["flow"], dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---- Fig. 3 results chart
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.8, 5.4), gridspec_kw={"hspace": 0.75})
    keys = list(F.RET_LABELS)
    short = {"tfidf_shipped (1-2gram)": "TF-IDF\n(shipped)", "tfidf_unigram": "TF-IDF\nunigram", "bm25": "BM25", "tfidf_lsa200": "TF-IDF\n+LSA",
             "hybrid_bm25_lsa": "BM25\n+LSA", "dense_bge_small": "Dense\nBGE", "hybrid_bm25_dense": "BM25\n+dense"}
    x = range(len(keys))
    for off, lab, col, g in ((-0.27, "Hit@1", BLUE, lambda k: F.hit(k, 1)), (0, "Hit@4", GREEN, lambda k: F.hit(k, 4)), (0.27, "MRR@10", ORANGE, lambda k: F.RET[k]["mrr10"])):
        a.bar([i + off for i in x], [g(k) for k in keys], 0.26, color=col, label=lab)
    a.set_xticks(list(x)); a.set_xticklabels([short[k] for k in keys], fontsize=9.5)
    a.set_ylim(0, 1.05); a.set_ylabel("score (72 questions)")
    a.legend(ncol=3, frameon=False, loc="upper left", fontsize=9.5)
    a.set_title("(a) Retrieval quality of seven retrievers", fontsize=11.5)
    a.spines[["top", "right"]].set_visible(False)
    ks = ["1", "2", "4", "6", "8"]
    b.plot(ks, [F.CMP[k]["key_in_ctx"] for k in ks], "o-", color=GREEN, lw=2, label="answer key in retrieved chunks")
    b.plot(ks, [F.CMP[k]["key_in_ans"] for k in ks], "s-", color=PURPLE, lw=2, label="answer key in extractive answer")
    b.set_xlabel("chunks retrieved (top_k)"); b.set_ylabel("answer-key recall"); b.set_ylim(0.4, 1.02)
    b2 = b.twinx()
    b2.plot(ks, [F.CMP[k]["token_reduction_pct"] for k in ks], "^--", color=ORANGE, lw=1.6, label="words removed (%)")
    b2.set_ylim(0, 100); b2.set_ylabel("words removed (%)", color=ORANGE)
    h1, l1 = b.get_legend_handles_labels(); h2, l2 = b2.get_legend_handles_labels()
    b.legend(h1 + h2, l1 + l2, frameon=False, fontsize=9, loc="lower right")
    b.set_title("(b) Extractive compression versus context size", fontsize=11.5)
    b.spines[["top"]].set_visible(False)
    out["results"] = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(out["results"], dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---- Fig. 4 / 5: real screenshots cropped to the application area
    for name, src, box in (("ask", "09_ask.png", (256, 80, 1440, 900)), ("roadmap", "13_roadmap.png", (256, 80, 1440, 900))):
        p = os.path.join(F.FIGS, f"paper_{name}.png")
        Image.open(F.shot(src)).convert("RGB").crop(box).save(p)
        out[name] = p
    return out


# --------------------------------------------------------------------------- text
def build(path):
    figs = make_figures()
    env = F.ENV
    R, CM = F.RET, F.CMP
    sh = R[F.SHIPPED]
    bm, hd = R["bm25"], R["hybrid_bm25_dense"]
    k4 = CM["4"]
    P = Paper()
    authors = [[n, "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY]", "Roll No. " + r, "[email address]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION}, Project Guide", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY]", "[email address]"])
    P.title_block("Adaptive Learning Intelligence Platform: Retrieval-Augmented Study Assistant over a Student's Own Documents", authors)
    P.begin_two_columns()

    P.abstract(
        "Students keep syllabi, lecture notes and question banks as scattered files that learning portals store but do not read, while general chatbots answer from public "
        "text instead of the prescribed syllabus. This paper presents the Adaptive Learning Intelligence Platform, a web application that extracts subjects and topics "
        "from uploaded PDF, DOCX and TXT files, answers questions from the student's own material with the source passage shown, generates fill-in-the-blank quizzes and ranks "
        "topics by quiz accuracy in a study roadmap. Retrieval is TF-IDF with cosine similarity and answers are extractive sentences; optional LLM generation exists but was not measured. "
        f"On a six-subject notes corpus of {F.CORPUS['words']:,} words with {F.CORPUS['questions']} hand-written questions, the shipped retriever places the evidence in its top four chunks "
        f"for {pct(F.hit(F.SHIPPED, 4))} of questions, while BM25 combined with dense embeddings reaches {pct(F.hit('hybrid_bm25_dense', 4))}. Extractive selection removes "
        f"{k4['token_reduction_pct']:.1f} % of the retrieved words but lowers answer-key recall from {k4['key_in_ctx']:.3f} to {k4['key_in_ans']:.3f}. "
        "Question-type routing and learned compression from the base paper are not implemented.",
        ["context compression", "learning analytics", "personalised roadmap", "question answering", "retrieval-augmented generation", "TF-IDF", "educational documents"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("A student handles scattered PDFs, syllabi, lecture notes and question banks across six to eight subjects every semester. Conventional e-learning portals store these "
           f"files but do not understand what is inside them, and large language models explain concepts well but may answer from memory rather than from the prescribed "
           f"source. Retrieval-augmented generation (RAG) retrieves the relevant passage first and answers from it {c(4)}, which suits a student who needs an answer that can be "
           f"traced back to their own notes.")
    P.para("Today a student searches several files by hand, or pastes text into a chatbot with no guarantee that the reply comes from the syllabus. Recommendations "
           "are identical for every learner, ignore earlier performance, and nothing shows which topics have been studied or how well they are understood. The cost is "
           "time lost searching, answers that cannot be checked, and revision that is not aimed at the weak topics.")
    P.para(f"The base paper, SAC-RAG {c(1)}, improves RAG in two ways: it routes each question to a retrieval strategy by type, and it compresses the retrieved context with an LLM, "
           "cutting token use by 38-58 % for a 1-2 point drop in exact match on multi-hop question-answering benchmarks. It does not address a student's own documents, "
           f"study planning or progress analytics, and other educational RAG systems {c(2, 3)} target personalised tutoring or essay assessment rather than document-grounded "
           "study over a personal curriculum. This work builds that missing combination and measures it honestly, including where it falls short of the base paper.")
    P.para("The contributions are: (1) a document-analysis module that stores uploaded study files as chunks with detected subjects, units and topics; (2) a question-answering "
           "engine that answers from the student's own chunks with source file, passage and match score, and abstains when nothing overlaps; (3) cloze quizzes whose per-topic "
           "results drive a priority-ranked study roadmap and dashboard behind a FastAPI service and a React interface; and (4) a measurement on a six-subject corpus of "
           f"retrieval, extractive compression, abstention, quiz quality, latency and {F.TESTS['tests']} automated tests, with what was not measured stated. "
           "Section II reviews related work, Section III gives the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All measurements ran on one desktop: {env['cpu']}, {env['ram']} RAM, {env['gpu']}, {env['os']}. Indexing {F.CORPUS['chunks']} chunks takes about "
           f"{F.SCALE[0]['index_build_ms'] / 1000:.2f} s and a query about {F.SCALE[0]['retrieve_ms_median']:.1f} ms on this machine.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}, scikit-learn {env['sklearn']} {c(16)}, NumPy {env['numpy']}, pypdf {env['pypdf']} and python-docx {env['python-docx']} for parsing, "
           f"FastAPI {env['fastapi']} with uvicorn {env['uvicorn']}, Flask {env['flask']} for the original interface, SQLite for storage, and React {env['react']} with Vite {env['vite']} "
           f"and Tailwind CSS {env['tailwind']} on Node {env['node']} for the browser interface. A dense BGE-small model {c(9)} was run only as a measurement reference.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** SAC-RAG {c(1)} observes that standard RAG applies one retrieval strategy to every question and passes redundant chunks to the generator. An LLM classifier "
           "labels each question Fact, Definition or Reasoning (92.0 % agreement with manual labels on 300 questions). Fact questions use hybrid BM25 plus dense retrieval with a cross-encoder reranker, "
           "Definition questions use dense retrieval only, and Reasoning questions are decomposed into sub-questions retrieved in parallel; a unified LLM module then extracts evidence "
           "snippets before generation. On HotpotQA, 2WikiMultiHopQA and MuSiQue, with 1,000 questions each and gpt-5-mini, adaptive retrieval raises HotpotQA exact match from 0.560 "
           "to 0.611 and Recall@10 from 0.787 to 0.880, and compression cuts token use by 38-58 % at a cost of 1-2 points of exact match. The price is latency: about 27.8 s "
           "per query against 9.6 s for naive RAG, because of the extra LLM calls.")
    P.para(f"**Foundations.** RAG was introduced by Lewis et al. {c(4)}; dense passage retrieval {c(5)} maps questions and passages into a shared vector space, while lexical scoring remains "
           f"competitive: TF-IDF weighting {c(7)} and the BM25 probabilistic framework {c(6)} reward terms that are frequent in a passage and rare in the collection. Latent semantic analysis {c(8)} "
           f"gives a low-dimensional lexical-semantic compromise, and general-purpose embedding models such as BGE {c(9)} are the usual dense choice. HotpotQA {c(13)} is the benchmark family used by {c(1)}.")
    P.para(f"**Adaptive retrieval and compression.** Adaptive-RAG {c(11)} routes questions among no retrieval, single-step and multi-step retrieval by complexity, and Self-RAG {c(14)} lets the model "
           f"decide when to retrieve; both are described in {c(1)} as lacking a compression stage. Long contexts are used less well by LLMs, which motivates compression {c(12)}: LLMLingua {c(10)} "
           f"prunes prompts with a small language model and RECOMP {c(15)} casts compression as summarisation, but both sit on top of a fixed retrieval strategy {c(1)}.")
    P.para(f"**Educational RAG.** TutorLLM {c(2)} combines knowledge tracing {c(17)} with RAG so that answers follow the learner's estimated state, and reports about 10 % higher user satisfaction "
           f"and 5 % higher quiz scores than a general LLM. An LLM assessment RAG {c(3)} retrieves rubrics and exemplar essays to grade and comment on essays, with 94-99 % agreement with human evaluators on "
           "701 essays. Neither answers questions from a student's own uploaded notes or ranks the student's topics by measured weakness.")
    P.table("Selected related work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        [f"SAC-RAG {c(1)}", "LLM question typing, type-specific retrieval, LLM compression", "HotpotQA, 2Wiki, MuSiQue; 1,000 questions each", "EM 0.560 to 0.611; tokens -38 to -58 %", "Extra LLM calls (27.8 s vs 9.6 s)"],
        [f"TutorLLM {c(2)}", "Knowledge tracing plus RAG with a web scraper", "Learner study with questionnaires", "+10 % satisfaction, +5 % quiz score", "Needs learner interaction history"],
        [f"Assessment RAG {c(3)}", "LLM agent retrieving rubrics and exemplar essays", "701 student essays", "94-99 % agreement with humans", "Grades essays; no study-note QA"],
        [f"Adaptive-RAG {c(11)}", "Routes by question complexity", "(see " + c(1) + ")", "Not read in full", "No compression stage " + c(1)],
        [f"LLMLingua {c(10)}", "Prompt compression by a small LM", "(see " + c(1) + ")", "Not read in full", "Fixed retrieval strategy " + c(1)],
        [f"RECOMP {c(15)}", "Compression as summarisation", "(see " + c(1) + ")", "Not read in full", "Fixed retrieval strategy " + c(1)],
    ], widths=[0.58, 0.84, 0.62, 0.7, 0.66], size=6.5, align=["l", "l", "l", "l", "l"])
    P.para(f"**Research gap.** The surveyed work optimises retrieval or compression for general questions {c(1)}, personalises tutoring {c(2)} or grades essays {c(3)}. None combines ingestion of a student's own "
           "syllabus and notes, answers that cite the source passage, and progress analytics that rank topics by measured weakness. We build that combination and, since it is a small system "
           "without an LLM in the measured path, we report how far its retrieval and compression fall short of the base paper's.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para(f"**Pipeline.** Fig. 1 shows the layers and Fig. 2 the main flow. On upload the text is extracted with pypdf or python-docx, whitespace is normalised and the text is cut into "
           "overlapping windows of 180 words with a 30-word overlap. Lines such as \"Subject:\", \"Course:\", \"Unit 3:\" and \"Chapter 2:\" are detected with regular expressions, and TF-IDF "
           "keywords over sentences fill the remaining places of a list of at most 12 topics. Document, topics and chunks are stored in SQLite and the user's index is rebuilt.")
    P.figure(figs["arch"], "System architecture: React front end, FastAPI service, shared Python modules, SQLite storage and an optional LLM.")
    P.para(f"**Data.** The product has no training set, so a six-subject notes corpus was built for measurement: 36 English Wikipedia articles {c(18)} pinned to revision identifiers, grouped as "
           f"Data Structures, Operating Systems, Database Systems, Computer Networks, Machine Learning and Algorithms, each file laid out with \"Subject:\" and \"Unit n:\" headings. "
           f"It holds {F.CORPUS['words']:,} words in {F.CORPUS['chunks']} chunks. We wrote {F.CORPUS['questions']} questions, 12 per subject and 24 each of fact, definition and reasoning type (the "
           f"base paper's taxonomy), with a gold evidence sentence copied from the text, plus {F.CORPUS['off_topic_questions']} off-topic questions. A retrieved chunk is a hit when it contains the evidence.")
    P.para(f"**Evaluation protocol.** Every evidence string was checked to occur exactly once in the corpus and wholly inside at least one chunk ({F.CORPUS['evidence_intact_in_a_chunk']} of {F.CORPUS['questions']}), so a miss is a "
           "retrieval miss and not a cut made by the chunker at the shipped size. The answer key is a short string with one to three accepted alternatives, searched in the retrieved text and in the generated answer; "
           "it is deliberately lenient, so it measures whether the needed fact survives and not whether the answer reads well. Confidence intervals come from 2,000 bootstrap resamples of the questions. "
           f"The off-topic set (football, cooking, geography and similar) tests abstention. Quiz quality is checked automatically on {F.QUIZ['generated']} questions (30 seeds, six files, five questions) and by one reviewer's labels on 30; "
           "latency is measured in process and over HTTP on 127.0.0.1 with 30 calls per endpoint.")
    P.para(f"**Retrieval.** Each chunk and the query are mapped to TF-IDF vectors over unigrams and bigrams with English stop words {c(7, 16)}, and chunks are ranked by cosine similarity,")
    P.eq("s(q, c) = (q · c) / (|q| |c|),")
    P.para(indent=0, text="keeping the top k = 4 chunks with s > 0. TF-IDF was chosen because it needs no model download, runs on any laptop and gives a score that can be shown to the student. "
           f"For comparison we also evaluate BM25 {c(6)} with k1 = 1.5 and b = 0.75,")
    P.eq("BM25(q,d) = Σ IDF(w) f(w,d)(k1+1) / (f(w,d) + k1(1 - b + b|d|/avgdl)),")
    P.para(indent=0, text=f"latent semantic analysis with 200 dimensions {c(8)}, dense BGE-small embeddings {c(9)}, and min-max-normalised 50/50 hybrids; only the TF-IDF retriever is part of the product. "
           "Quality is measured by the hit rate and the mean reciprocal rank over a question set Q,")
    P.eq("Hit@k = (1/|Q|) Σ 1[evidence in top-k],")
    P.eq("MRR = (1/|Q|) Σ 1/rank.")
    P.para("**Answering.** The default answer is extractive: the retrieved chunks are split into sentences longer than 20 characters, ranked by TF-IDF cosine against the question, and the top four with a positive score "
           "are joined. If an API key is configured the chunks and question go to an LLM instructed to answer only from the context, and any failure falls back to the extractive answer. "
           "The words removed are measured by")
    P.eq("compression = 1 - |answer| / |retrieved context|.")
    P.para("**Knowledge repository.** Each upload creates one document row (file name, subject, topic list) and one row per chunk, linked by foreign keys that cascade on deletion, so removing a document removes its chunks "
           "and its file. The topic list puts the detected headings first, for example the subject line and the unit titles, and fills the rest with the highest-weighted unigrams and bigrams of the document's "
           "sentences. The retrieval index is held in memory per user and rebuilt after every upload or deletion; rebuilding is linear in the number of chunks, which is acceptable for a personal collection "
           "but would need incremental updates for a shared one.")
    P.para("**Quiz and roadmap.** A quiz blanks the first occurrence of a high-weight TF-IDF term in a sentence and offers three other terms as distractors. A topic's accuracy is "
           "100 x correct / attempts over its quiz rows and its priority is High below 50, Medium below 80 and Low otherwise. **Implementation.** The service exposes 14 endpoints with a signed "
           f"session cookie and Pydantic bodies; the React pages are code-split. The suite has {F.TESTS['tests']} pytest tests and a {F.SMOKE_TOTAL}-check smoke test.")
    P.para(f"**Security and error handling.** Passwords are stored as salted hashes and the session cookie is signed, HttpOnly and SameSite=Lax; every SQL statement is parameterised; file names pass through a sanitiser and only PDF, "
           "DOCX and TXT files up to 16 MB are accepted; every document query filters on the user's identifier, so one user cannot list, delete, quiz on or search another's files. The tests assert these behaviours: unauthenticated "
           "calls to nine protected routes return 401, SQL-injection strings are stored as literal text, and a file named \"../../evil.txt\" is saved as \"evil.txt\" inside the user's folder. They also assert two known weaknesses: "
           "two uploads with the same name share one path on disk, and the cookie is not marked Secure in the local deployment.")
    P.figure(figs["flow"], "Main flow: ingestion of a document and answering of a question.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** All {F.CORPUS['questions']} questions are test questions; nothing is trained. The index holds {F.CORPUS['chunks']} chunks of the six files in one user account, as in the "
           f"application. The bootstrap 95 % interval of the shipped retriever's Hit@4 is {F.RET_CI['hit4'][0]:.3f}-{F.RET_CI['hit4'][1]:.3f}, so differences of a few points between retrievers are within noise. "
           "Table II gives the retrieval results.")
    rows = [F.ret_row(k, (1, 4, 10)) for k in F.RET_LABELS]
    P.table("Retrieval on 672 chunks, 72 questions", ["Retriever", "Hit@1", "Hit@4", "Hit@10", "MRR@10"],
            [[r[0], r[1], r[2], r[3], r[4]] for r in rows], widths=[1.35, 0.5, 0.5, 0.5, 0.55], size=7, align=["l", "c", "c", "c", "c"])
    fa, de, rs = sh["by_type"]["fact"], sh["by_type"]["definition"], sh["by_type"]["reasoning"]
    P.para(f"**Retrieval (Fig. 3a).** The shipped retriever reaches Hit@1 {F.hit(F.SHIPPED, 1):.3f}, Hit@4 {F.hit(F.SHIPPED, 4):.3f} and MRR {sh['mrr10']:.3f}. BM25 is better at the first position "
           f"({bm['hit']['1']:.3f}) and the BM25-plus-dense hybrid is best on every column (Hit@4 {hd['hit']['4']:.3f}), so the \"semantic\" retrieval named in the objectives is not delivered by TF-IDF. "
           f"By type, Hit@4 is {fa['hit4']:.3f} for fact, {de['hit4']:.3f} for definition and {rs['hit4']:.3f} for reasoning questions; at rank one, definition questions are weakest ({de['hit1']:.3f}). "
           f"Larger chunks help the measure: Hit@4 rises from {F.CHUNKS['100/20']['hit4']:.3f} at 100 words to {F.CHUNKS['300/50']['hit4']:.3f} at 300, but they hand more text to the reader, so 180 was kept.")
    P.para(f"**By question type.** The base paper routes fact, definition and reasoning questions differently, so we split the results the same way. TF-IDF scores Hit@4 {fa['hit4']:.3f}, {de['hit4']:.3f} and {rs['hit4']:.3f}; "
           f"BM25 scores {bm['by_type']['fact']['hit4']:.3f}, {bm['by_type']['definition']['hit4']:.3f} and {bm['by_type']['reasoning']['hit4']:.3f}; the BM25-plus-dense hybrid {hd['by_type']['fact']['hit4']:.3f}, "
           f"{hd['by_type']['definition']['hit4']:.3f} and {hd['by_type']['reasoning']['hit4']:.3f}. No single retriever wins every type, which is consistent with the base paper's argument for type-specific strategies, "
           "but with 24 questions per type these gaps are suggestive, not conclusive, and we did not implement a router to test it.")
    P.para(f"**Compression (Fig. 3b).** With four chunks retrieved, the extractive step turns {k4['mean_ctx_words']:.0f} words into {k4['mean_ans_words']:.0f} ({k4['token_reduction_pct']:.1f} % removed), "
           f"and every answer word comes from the retrieved chunks. The answer keeps the key for {pct(k4['key_in_ans'])} of questions where the full chunks held it for {pct(k4['key_in_ctx'])}, "
           f"a loss of {100 * (k4['key_in_ctx'] - k4['key_in_ans']):.1f} points; for definition questions the key is in the chunks for {pct(CM['by_type_k4']['definition']['key_in_ctx'])} "
           f"but in the answer for only {pct(CM['by_type_k4']['definition']['key_in_ans'])}, because the sentences chosen overlap the question's words rather than state the definition.")
    P.figure(figs["results"], "(a) Retrieval results; (b) answer-key recall and words removed by the extractive answer step.")
    P.table("Extractive answer step by chunks retrieved", ["k", "Words in", "Words out", "Removed", "Key in chunks", "Key in answer"],
            [[k, f"{CM[k]['mean_ctx_words']:.0f}", f"{CM[k]['mean_ans_words']:.0f}", f"{CM[k]['token_reduction_pct']:.1f} %", f"{CM[k]['key_in_ctx']:.3f}", f"{CM[k]['key_in_ans']:.3f}"] for k in ("1", "2", "4", "6", "8")],
            widths=[0.3, 0.55, 0.55, 0.6, 0.7, 0.7], size=7, align=["c", "c", "c", "c", "c", "c"])
    P.para(f"Even with eight chunks the answer step keeps the key in only {pct(CM['8']['key_in_ans'], 0)} of answers where the chunks held it in {pct(CM['8']['key_in_ctx'], 0)}: the loss comes from sentence "
           f"selection, not from retrieval. Given that retrieval succeeded, the answer holds the key for {pct(CM['k4_given_retrieval_hit']['key_in_ans'])} of the {CM['k4_given_retrieval_hit']['n']} questions.")
    P.para(f"**Chunk size and cost.** Hit@4 is {F.CHUNKS['60/15']['hit4']:.3f} at 60 words, {F.CHUNKS['100/20']['hit4']:.3f} at 100, {F.CHUNKS['180/30']['hit4']:.3f} at 180 (shipped), {F.CHUNKS['300/50']['hit4']:.3f} at 300 and "
           f"{F.CHUNKS['450/75']['hit4']:.3f} at 450; the shortest windows also cut {F.CORPUS['questions'] - F.CHUNKS['60/15']['evidence_intact']} of the 72 evidence sentences in two. The curve rewards larger chunks because fewer, longer candidates are easier to hit, "
           f"so the choice trades recall against the amount of text handed to the reader. Dense retrieval needed {F.DENSE['embed_chunks_s']:.0f} s to embed the {F.DENSE['chunks']} chunks on the CPU and {F.DENSE['embed_query_ms_each']:.1f} ms per query, "
           f"against {F.SCALE[0]['index_build_ms']:.0f} ms to build the TF-IDF index, which is why it was kept out of the product.")
    P.para(f"**Abstention.** The engine refuses only when no query term occurs in any chunk, so {F.ABS['off_topic_answered_by_shipped']} of {F.ABS['n_off_topic']} off-topic questions still received an "
           f"answer. In-scope top-1 scores have a median of {F.ABS['top1_score_in_scope']['median']:.2f}, off-topic ones {F.ABS['top1_score_off_topic']['median']:.2f}; a threshold of 0.15 would refuse "
           f"{pct(F.ABS['sweep'][6]['off_topic_refused'], 0)} of off-topic questions and answer {pct(F.ABS['sweep'][6]['in_scope_answered'], 0)} of in-scope ones (suggested, not implemented).")
    P.para("**Roadmap and dashboard.** For the screens we uploaded five documents, asked four questions and took eight quizzes with a scripted learner who knew a chosen number of answers per quiz, giving subject accuracies of "
           "85 % (Data Structures), 80 % (Algorithms), 60 % (Operating Systems) and 30 % (Database Systems). The dashboard shows these as bars coloured by band, and the roadmap lists 30 topics: 9 High, 2 Medium and 19 Low "
           "(Fig. 5). The scripted answers show that the bands follow the accuracy thresholds, not that the roadmap improves learning: no user study was run, and the topic names are keywords, so a student would see "
           "generic entries such as \"using\" next to meaningful ones.")
    P.para(f"**Analysis, quiz and speed (Fig. 7).** All {F.DOCAN['per_file'][0]['units_in_file'] * 6} \"Unit n:\" headings were found, but \"UNIT-I\", \"Module 1\" and \"1.\" styles were found in 0 of 5 units, and text "
           f"in DOCX tables is not read. Of {F.QUIZ['generated']} generated quiz questions all are well formed, yet the answer term remains visible in the stem for {pct(F.QUIZ['answer_repeated_in_stem_rate'])}, "
           f"and a manual review rated {F.AUDIT['summary']['acceptable']} of {F.AUDIT['summary']['n']} acceptable. Retrieval time grows about linearly from {F.SCALE[0]['retrieve_ms_median']:.1f} ms at "
           f"{F.SCALE[0]['chunks']} chunks to {F.SCALE[3]['retrieve_ms_median']:.1f} ms at {F.SCALE[3]['chunks']:,}; over HTTP an ask call has a median of {F.API['ask']['median_ms']:.0f} ms and login {F.API['login']['median_ms']:.0f} ms "
           f"(password hashing). {F.TESTS['tests']} pytest tests and {F.SMOKE_TOTAL} smoke checks pass; the LLM answer mode, concurrent users and real student files were not measured.")
    P.para(f"**Tests and builds.** The {F.TESTS['tests']} pytest tests (API {F.TEST_FILES['test_api.py']}, text extraction {F.TEST_FILES['test_text_extraction.py']}, security {F.TEST_FILES['test_security.py']}, retrieval engine "
           f"{F.TEST_FILES['test_rag_engine.py']}, quiz generator {F.TEST_FILES['test_quiz_generator.py']}) run in {F.TESTS['seconds']:.0f} s against a temporary database and pin the roadmap thresholds: 0, 33 and 49 % give High, 50, 78 and 79 % "
           "give Medium, 80 and 100 % give Low. The type-checked production build of the React interface succeeds, and a scripted browser walk through every screen at 1440, 768 and 360 pixels in light and dark themes "
           "found no console errors, page errors, failed requests or sideways scrolling.")
    P.para(f"**Response times (Fig. 6).** Over HTTP on one machine the medians are {F.API['dashboard']['median_ms']:.0f} ms for the dashboard, {F.API['documents_list']['median_ms']:.0f} ms for the document list, "
           f"{F.API['roadmap']['median_ms']:.0f} ms for the roadmap, {F.API['quiz_generate']['median_ms']:.0f} ms to generate and {F.API['quiz_submit']['median_ms']:.0f} ms to submit a quiz. Uploading a 90-110 kB file re-indexes every chunk of the user "
           "and took between 0.12 and 2.5 s over two runs, the spread coming from other jobs on the machine; one or two of 30 quiz submissions took one to two seconds, probably a slow database commit, which we did not isolate.")
    P.para("**Threats to validity.** The questions were written by the team who knew the corpus, which may favour lexical overlap; Wikipedia prose is more regular than student notes, which are often terse or scanned; "
           "the evidence test is strict and can under-count chunks that state the fact in other words, while the answer-key test is lenient and can over-count; 72 questions give wide intervals; all numbers come from one machine; "
           "and the learner behind the roadmap screens was scripted. The LLM mode, which the base paper's pipeline relies on, was not measured.")
    P.figure(figs["ask"], "Output screen: a question answered from the uploaded notes, with the source passage and match score.")
    P.para("**Comparison with the base paper.** The base paper evaluates multi-hop benchmarks with an LLM and reports exact match, F1, Recall@10 and tokens; we evaluate a 72-question notes corpus without "
           f"an LLM and report hit rates and answer-key containment, so the numbers are not comparable. The pattern is: the base paper trades 1-2 points of exact match for 38-58 % fewer tokens, "
           f"whereas our extractive step trades {100 * (k4['key_in_ctx'] - k4['key_in_ans']):.1f} points of key recall for {k4['token_reduction_pct']:.1f} % fewer words. Its use of a "
           f"BM25-plus-dense hybrid for fact questions is consistent with our data (hybrid retrieval was best, and BM25 beat TF-IDF on fact questions, Hit@4 {bm['by_type']['fact']['hit4']:.3f} against {fa['hit4']:.3f}); "
           "we did not test question-type routing or LLM compression.")
    P.figure(figs["roadmap"], "Output screen: the study roadmap ranks topics by quiz accuracy; topics are single keywords, some generic.")
    P.figure(F.fig("fig_api_latency.png"), "Median (bar) and 95th-percentile (dot) latency of the API over HTTP on 127.0.0.1 with 672 chunks indexed.")
    P.figure(F.fig("fig_quiz_quality.png"), "Quiz quality: manual review of 30 questions (left) and automatic checks on 900 questions (right).")
    P.para(f"**Limits and failure cases.** Retrieval misses {pct(1 - F.hit(F.SHIPPED, 4), 0)} of questions at four chunks; the extractive answer can place the right sentence outside its four; roadmap topics are keywords such as \"using\" "
           "or \"normal\"; and the roadmap uses only quiz accuracy, with no revision schedule, coverage or velocity measure. In Fig. 4 the question \"What is a deadlock?\" is answered from a passage "
           "with match score 0.46, but the sentences returned discuss deadlock avoidance and recovery rather than the definition, the failure the by-type results predict. Quiz sentences also "
           "sometimes begin in the middle of a heading (for example a blank before \"2: Stacks and Queues\"), and the same keyword can appear under two subjects in the roadmap.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"The platform delivers document ingestion, source-cited answers, quizzes, a priority roadmap and a dashboard behind a tested API. Against the objectives, ingestion and cited answering are met, "
           f"while embeddings, learned context compression and adaptive routing from the base paper are not implemented, and the roadmap covers quiz accuracy only. The central finding is that "
           f"plain TF-IDF finds the evidence in the top four chunks for {pct(F.hit(F.SHIPPED, 4))} of questions, BM25 plus dense embeddings for {pct(hd['hit']['4'])}, and that extractive compression removes "
           f"{k4['token_reduction_pct']:.1f} % of the words at a clear cost in answer-key recall.")
    P.para(f"Three observations follow. First, the lexical retriever is adequate for fact and definition lookups when the question reuses the notes' wording but weak at rank one, so showing four sources with match scores is part of the design. "
           f"Second, compression by sentence selection, not retrieval, limits answer quality: the evidence was in the chunks for {pct(k4['key_in_ctx'], 0)} of questions but in the answer for {pct(k4['key_in_ans'], 0)}. "
           "Third, with no relevance threshold the system can answer an off-topic question from unrelated notes, which weakens the promise of answering strictly from the student's material.")
    P.para("Against the six objectives: ingestion that extracts subjects, units and topics is partly met (it needs headings in the supported forms); semantic embeddings are not met by the shipped retriever; answering from the "
           "uploaded material with its source is met in extractive mode; context compression is partly met by sentence selection; the roadmap is partly met as an accuracy ranking without a revision schedule; and the dashboard is partly "
           "met, showing counts and subject accuracy but no coverage or study velocity.")
    P.para("Limitations: one corpus of encyclopaedia text rather than student files, 72 questions, an unmeasured LLM mode, no relevance threshold, and process-local quiz state and index cache. "
           "Future work: adopt BM25 and a dense hybrid, add a relevance threshold and a question-type router, compress with an LLM and measure it, recognise Roman-numeral and module headings, "
           "read DOCX tables and scanned PDFs, replace keyword topics with unit-level topics, add revision scheduling, and run a user study on real syllabi.")

    P.references()
    P.save(path)
    return P


def main():
    path = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    P = build(path)
    print("wrote", path)
    print("references cited:", len(P.order), "global numbers:", P.order)
    nv = getattr(REFMOD, "N_VERIFIED", None)
    if nv:
        print("unverified cited:", [g for g in P.order if g > nv])


if __name__ == "__main__":
    main()
