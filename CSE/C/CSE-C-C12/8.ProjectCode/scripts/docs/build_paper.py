"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for SymptoTrackAI from facts.py (docs/metrics/*.json), the diagrams and the screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper
from .refs import CITE

pct, f2, f3 = F.pct, F.f2, F.f3
S = F.RET


def R(*keys):
    """Citation placeholder resolved by Paper.expand in order of first appearance."""
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


def t1(cfg, s):
    return S[cfg][s]["top1"]


def make_figures():
    """Fig. 3 (results chart) and the two output-screen crops, written to docs/figures/paper_*.png."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 12})
    out = {}
    NAVY, BLUE, TEAL, ORANGE, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#C0392B"
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.8, 7.4), gridspec_kw={"hspace": 0.62})
    cfgs = [("bm25", "BM25"), ("dense", "dense"), ("hybrid", "hybrid"), ("hybrid_rerank", "hybrid +\nrerank\n(shipped)"), ("hybrid_rerank_nohyde", "shipped,\nno HyDE"), ("hybrid_tfidf", "offline\nTF-IDF")]
    x = np.arange(len(cfgs))
    w = 0.27
    for k, (s, lab, col) in enumerate([("S2_verbatim_leave_one_out_176", "verbatim (176)", BLUE), ("S3_two_symptoms_leave_one_out_176", "two symptoms (176)", ORANGE), ("S4_lay_language_60", "lay language (60)", TEAL)]):
        vals = [S[c][s]["top1"] for c, _ in cfgs]
        bars = a.bar(x + (k - 1) * w, vals, w, color=col, label=lab)
        for bb in bars:
            a.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 0.01, f"{bb.get_height():.2f}", ha="center", fontsize=8, rotation=90)
    a.set_xticks(x)
    a.set_xticklabels([n for _, n in cfgs], fontsize=10)
    a.set_ylim(0.5, 1.12)
    a.set_ylabel("top-1 condition accuracy")
    a.legend(frameon=False, fontsize=10, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    a.set_title("(a) Retrieval configurations on three query sets", fontsize=12, pad=18)
    a.spines[["top", "right"]].set_visible(False)
    rel = F.REL
    rng = np.random.default_rng(3)
    inv, outv = rel["raw_rerank_in_kb_values"], rel["raw_rerank_out_kb_values"]
    b.scatter(rng.uniform(-0.18, 0.18, len(inv)), inv, s=22, color=TEAL, label="60 in-knowledge-base queries")
    b.scatter(1 + rng.uniform(-0.18, 0.18, len(outv)), outv, s=22, color=ORANGE, label="15 out-of-knowledge-base queries")
    b.axhline(0, color="#888", lw=0.8)
    b.set_xticks([0, 1])
    b.set_xticklabels(["in-KB", "out-of-KB"])
    b.set_xlim(-0.5, 1.5)
    b.set_ylabel("raw cross-encoder score of the top record")
    b.set_title("(b) Raw score separates them; the screen shows 100% for both", fontsize=12)
    b.legend(frameon=False, fontsize=9, loc="upper right")
    b.spines[["top", "right"]].set_visible(False)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    out["results"] = p

    out["safety"] = _safety_fig()
    out["arch"] = _arch_fig()
    out["flow"] = _flow_fig()
    s08 = Image.open(F.shot("08_assistant_emergency.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_emergency.png")
    s08.crop((282, 288, 1062, 654)).save(p)
    out["emergency"] = p
    s09 = Image.open(F.shot("09_history.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_history.png")
    s09.crop((280, 352, 1410, 900)).save(p)
    out["history"] = p
    return out


def _box(ax, x, y, w, h, text, fc, tc="white", fs=6.4, bold=False):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=fc, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)


def _arr(ax, p1, p2):
    ax.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle="-|>", color="#1F3A5F", lw=1.0, shrinkA=0, shrinkB=0))


def _safety_fig():
    import matplotlib.pyplot as plt

    sa = F.SAF
    lit, par, hard = sa["by_group_pos"]["literal"], sa["by_group_pos"]["paraphrase"], sa["by_group_neg"]["hard"]
    labels = ["emergency,\nliteral", "emergency,\nparaphrased", "ordinary\n(false alarm)", "hard negative\n(false alarm)"]
    vals = [lit["detected"] / lit["n"], par["detected"] / par["n"], 0.0, len(hard["false_emergency"]) / hard["n"]]
    txt = [f"{lit['detected']}/{lit['n']}", f"{par['detected']}/{par['n']}", "0/20", f"{len(hard['false_emergency'])}/{hard['n']}"]
    cols = ["#14907F", "#14907F", "#D9772F", "#D9772F"]
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    bars = ax.bar(range(4), vals, color=cols, width=0.6)
    for b, t in zip(bars, txt):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.03, t, ha="center", fontsize=7)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=6)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("fraction flagged as emergency", fontsize=6.5)
    ax.tick_params(axis="y", labelsize=6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    p = os.path.join(F.FIGS, "paper_safety.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    return p


def _arch_fig():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(3.4, 3.25))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 96)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    _box(ax, 2, 80, 96, 14, "React + Vite interface (port 5412)\nLanding - Sign in - Assistant - History - About", "#2B6CB0", fs=6.6)
    _box(ax, 2, 58, 96, 16, "FastAPI service (port 8412)\nbcrypt + JWT cookie auth - POST /api/chat\nGET/DELETE /api/history - GET /api/about/metrics", "#14907F", fs=6.4)
    _box(ax, 2, 34, 96, 18, "RAG pipeline (Pipeline.answer)\nexpand - MiniLM + FAISS | BM25 - fuse 0.65/0.35\ncross-encoder rerank (top 5) - generator - safety", "#D9772F", fs=6.4)
    _box(ax, 2, 4, 30, 24, "SQLite\nusers\nconsultations", "#EEF2F7", tc="#14213D", fs=6.2)
    _box(ax, 35, 4, 30, 24, "Indexes\nFAISS flat\nBM25 (176 rec.)", "#EEF2F7", tc="#14213D", fs=6.2)
    _box(ax, 68, 4, 30, 24, "Local models\nMiniLM, MS MARCO\ncross-enc., Flan-T5", "#EEF2F7", tc="#14213D", fs=5.9)
    for y1, y2 in ((80, 74.5), (58, 52.5), (34, 28.5)):
        _arr(ax, (50, y1), (50, y2))
    p = os.path.join(F.FIGS, "paper_arch.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    return p


def _flow_fig():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(3.4, 4.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 132)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    _box(ax, 10, 120, 80, 10, "Symptom text (3-2000 characters)", "#2B6CB0", fs=6.6)
    _box(ax, 10, 104, 80, 11, "Normalise + pseudo-document template\n(rule-based expansion, no model)", "#2B6CB0", fs=6.4)
    _box(ax, 2, 83, 44, 15, "MiniLM embedding\nFAISS inner product\ntop 15", "#14907F", fs=6.4)
    _box(ax, 54, 83, 44, 15, "BM25 on tokens\ntop 15", "#14907F", fs=6.4)
    _box(ax, 10, 66, 80, 11, "Min-max fusion: 0.65 dense + 0.35 BM25", "#D9772F", fs=6.4)
    _box(ax, 10, 49, 80, 12, "Cross-encoder rerank of 15 candidates\ntop 5 = evidence cards", "#D9772F", fs=6.4)
    _box(ax, 10, 33, 80, 11, "Answer: Flan-T5, else evidence-based fallback", "#6B5BD2", fs=6.2)
    _box(ax, 10, 17, 80, 11, "Safety: 10 rules + caution + answer filter", "#C0392B", fs=6.4)
    _box(ax, 10, 1, 80, 11, "Store in SQLite and show to the user", "#1F3A5F", fs=6.4)
    _arr(ax, (50, 120), (50, 115.5))
    _arr(ax, (50, 104), (24, 98.5))
    _arr(ax, (50, 104), (76, 98.5))
    _arr(ax, (24, 83), (40, 77.5))
    _arr(ax, (76, 83), (60, 77.5))
    for y1, y2 in ((66, 61.5), (49, 44.5), (33, 28.5), (17, 12.5)):
        _arr(ax, (50, y1), (50, y2))
    p = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    return p


def build(path):
    figs = make_figures()
    env, k, g, sa, lat = F.ENV, F.KB, F.GEN, F.SAF, F.LAT
    ship = F.SHIP
    S4, S3, S2, S1 = "S4_lay_language_60", "S3_two_symptoms_leave_one_out_176", "S2_verbatim_leave_one_out_176", "S1_leave_one_out_30"
    rel = F.REL
    lit = sa["by_group_pos"]["literal"]
    par = sa["by_group_pos"]["paraphrase"]
    hard = sa["by_group_neg"]["hard"]
    flt = sa["filter"]
    st = lat["stages_ms"]

    P = Paper()
    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", "TKR College of Engineering & Technology", "[CITY], India", "[EMAIL]"])
    P.title_block("SymptoTrackAI: Hybrid RAG Based Symptom Tracking and Health Monitoring System", authors)
    P.begin_two_columns()

    P.abstract(
        "Patients often delay care because early symptoms look minor, and web self-diagnosis returns alarming and unreliable answers. "
        "This paper presents SymptoTrackAI, implemented as the CareLens AI web application, a local symptom-monitoring assistant that answers only from a retrieved medical knowledge base. "
        "A symptom description in everyday language is normalised, expanded with a rule-based hypothetical-document template, searched by a dense retriever (MiniLM with FAISS) and a lexical retriever (BM25), "
        "fused, reranked by a cross-encoder, turned into a grounded answer and screened by a rule-based safety layer; each consultation is stored privately per user. "
        f"On a synthetic knowledge base of {k['records']} records and {k['conditions']} conditions, the shipped configuration ranks the right condition first for {pct(t1('hybrid_rerank', S4))} of 60 lay-language probes, "
        f"{pct(t1('hybrid_rerank', S3))} of two-symptom queries and {pct(t1('hybrid_rerank', S2))} of leave-one-out verbatim queries, in under one second per request on a CPU. "
        f"Testing also exposed defects: the local generator echoes its prompt, the displayed relevance is always 100%, and the safety rules caught none of {par['n']} paraphrased emergencies. "
        "The knowledge base is synthetic and the probes are written by the authors, so the results show that the pipeline works, not that it is clinically accurate.",
        ["FAISS semantic search", "healthcare chatbot", "hybrid retrieval", "query expansion", "retrieval-augmented generation", "safety escalation", "symptom monitoring"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("People often delay consulting a clinician because early symptoms seem minor or access is inconvenient, and a general web search for them returns alarming and frequently wrong conclusions. "
           f"Language models can interpret symptoms written in ordinary language, but ungrounded models hallucinate {R('halluc')}, which is unacceptable when the answer may be acted on. "
           f"Retrieval-augmented generation (RAG) {R('rag')} restricts the answer to passages fetched from a curated knowledge base, and a benchmark of medical question answering examines how far retrieval helps language models and how much the choice of retriever and corpus matters {R('medrag')}.")
    P.para(f"Medical chatbots have been built with machine learning, natural-language understanding and BERT {R('divya', 'hsu', 'babu')} and, more recently, with retrieval over medical books {R('peri')}. "
           f"The base paper {R('base')} combines a transformer encoder, FAISS similarity search and RAG in a web application with registration, login and a stored consultation history. "
           "It reports no measurement: its results are qualitative observations and one worked example, and it describes neither a lexical retriever, a reranker nor any handling of emergencies. "
           "A user is therefore left with no evidence of how often the right condition is retrieved, how long an answer takes, or what happens when the question is outside the knowledge base.")
    P.para("SymptoTrackAI, implemented as the CareLens AI web application, takes the base paper's retrieve-then-answer design and adds what is needed to measure and use it. The contributions are: "
           "(1) a local pipeline with hybrid dense and lexical retrieval, cross-encoder reranking, grounded generation with an offline fallback, a rule-based safety layer and a private per-user consultation history; "
           "(2) a retrieval evaluation that separates the shipped upper-bound protocol from leave-one-out, two-symptom and lay-language tests and from an ablation of each stage; "
           "(3) measurements of the safety layer, the displayed relevance score and latency; and "
           "(4) a plain record of the defects this testing found. Section II reviews related work, Section III the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All measurements used one desktop PC: {env['cpu']}, {env['ram_gb']} GB of RAM and Windows 11. Models ran on the CPU.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}; FastAPI {env['fastapi']} with SQLite through SQLAlchemy {env['sqlalchemy']}; sentence-transformers {env['sentence_transformers']} with all-MiniLM-L6-v2 {R('minilm', 'sbert')} "
           f"and the MS MARCO MiniLM cross-encoder {R('monobert')}; FAISS {env['faiss']} {R('faiss')}; rank-bm25; PyTorch {env['torch']} and Transformers {env['transformers']} running Flan-T5-small {R('flan')}; "
           f"scikit-learn {env['scikit_learn']} {R('sklearn')}; bcrypt and PyJWT for accounts; and a React and Vite interface.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Madhury and Ramesh {R('base')} present a symptom-monitoring framework in which a transformer (named Sequence-NQ in the paper) embeds user queries and the records of a symptom-disease knowledge base into one space, "
           "FAISS retrieves the nearest records, and a RAG step writes a response. A secure web application provides registration, login, a chatbot and a log of past consultations, "
           "and the paper's figure shows an example in which constipation, stomach ache, high fever and swollen lymph nodes lead to a suggestion of typhoid. "
           "The knowledge base is described as de-duplicated and indexed but its size, source and licence are not given, and the results section contains no accuracy, latency or ablation figure. "
           "Its stated future work is a larger knowledge base, multilingual support, multimodal input and cloud deployment.")
    P.para(f"**Medical chatbots.** Divya et al. {R('divya')} built an early self-diagnosis chatbot, Hsu and Yu {R('hsu')} combined machine learning with language understanding, and Babu and Boddu {R('babu')} used BERT; "
           f"as summarised in {R('base')} these works report better interaction or understanding than rule-based chatbots, without figures that can be compared here. "
           f"Peri et al. {R('peri')} answer from medical books with a RAG model. Son et al. {R('emr')} fine-tune embedding models for a hospital chatbot over electronic-medical-record manuals and report retrieval accuracy of 97.6% (BGE-M3) and 89.7% (Multilingual-E5-Large) on 5,931 question-document pairs with query latency under 10 ms. "
           f"ClinicBot {R('clinicbot')} extracts diabetes guidelines into structured units, ranks evidence by clinical priority and shows verifiable citations in a system demonstration.")
    P.para(f"**Retrieval components.** Dense passage retrieval {R('dpr')} and sentence embeddings {R('sbert')} compare meaning by vector similarity, FAISS {R('faiss')} makes that search fast, and BM25 {R('bm25')} remains a strong lexical baseline. "
           f"Hypothetical-document embeddings {R('hyde')} ask a language model to write a pseudo-document and search with it; here a fixed template plays that role. Cross-encoder rerankers score the query and a candidate together {R('monobert')}, "
           f"and reciprocal rank fusion {R('rrf')} is a common alternative to score fusion.")
    P.table("Representative related work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
        [R("base"), "Transformer + FAISS + RAG chatbot, history log", "Symptom-disease KB, size not given", "Qualitative; one typhoid example", "No metrics, no safety, no lexical or rerank stage"],
        [R("peri"), "RAG over medical books", "Medical literature", "Improved factual consistency (as summarised in [1])", "No figures in the summary"],
        [R("emr"), "Fine-tuned embeddings + RAG", "5,931 question-document pairs, EMR manuals", "97.6% / 89.7% retrieval accuracy, < 10 ms", "Hospital administration, not symptoms"],
        [R("clinicbot"), "Guideline extraction, prioritised evidence, citations", "ADA Standards of Care 2025", "System demonstration", "One disease area; no accuracy table"],
        [R("medrag"), "Benchmark of RAG for medical QA", "Medical QA sets", "Studies retrieval, retriever and corpus choices", "Question answering, not symptoms"],
    ], widths=[0.3, 0.85, 0.75, 0.8, 0.7], size=7, align=["c", "l", "l", "l", "l"])
    P.para("**Gap.** The surveyed chatbots either report no measurement or work on another task, none evaluates hybrid retrieval for symptom queries, and none reports what happens to the shown confidence when the question is outside the knowledge base or whether an emergency is flagged. "
           "The longitudinal tracking promised by the base paper is a stored list of consultations. SymptoTrackAI targets the missing measurement and safety evidence at demonstration scale; "
           "it does not enlarge the knowledge base to clinical scale.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the tiers. A React single-page application calls a FastAPI service on the same machine. The service runs the retrieval pipeline, keeps two SQLite tables (users and consultations), "
           "authenticates with bcrypt-hashed passwords and a signed JWT in an httponly cookie, and exposes ten endpoints for health, registration, login, logout, session check, chat, history list, detail and delete, and the stored metrics. Nothing leaves the machine.")
    P.figure(figs["arch"], "SymptoTrackAI (CareLens AI) architecture: React interface, FastAPI service with the retrieval pipeline, SQLite storage and local model files.")
    P.para(f"**Knowledge base.** The base holds {k['records']} records for {k['conditions']} conditions (4 to 6 each), with {k['mean_symptoms_per_record']} symptoms per record on average from a vocabulary of {k['symptom_vocabulary']}. "
           f"Each record has symptoms, a description, guidance, a severity level and red-flag symptoms; all records of a condition share one description and guidance ({k['distinct_description_guidance_pairs']} distinct pairs). "
           "The records were generated by the project from a hand-written table (random symptom subsets, seed 42) because no public dataset was used; the base is labelled synthetic in the application and has not been reviewed clinically.")
    P.para("**Main flow.** Fig. 2 follows one request. The text (3 to 2,000 characters) is lowercased and split into fragments, and a template turns them into a pseudo-document, \"medical symptom presentation involving ...\", that is appended to the query. "
           "This is a rule, not a model. The combined text is embedded by all-MiniLM-L6-v2 (384 dimensions, normalised) and matched by inner product in a flat FAISS index, and scored by BM25 with the standard saturation and length terms")
    P.eq("BM25(q, d) = Σ_t IDF(t) f(t,d)(k1+1) / (f(t,d) + k1(1 - b + b|d|/avgdl)),")
    P.figure(figs["flow"], "Main flow of one chat request: expansion, dual retrieval, fusion, reranking, grounded answer, safety check and storage.")
    P.para("Each retriever returns 15 candidates. Their scores are min-max normalised over the union and fused,")
    P.eq("s_hyb(d) = 0.65 n_dense(d) + 0.35 n_bm25(d),")
    P.para(indent=0, text="and the 15 fused candidates are rescored by a cross-encoder trained on MS MARCO, which reads the query and the record text together. The five best become the evidence cards. "
           "The relevance shown to the user is the cross-encoder score min-max normalised over the 15 candidates, with bands at 0.66 and 0.33 labelled Strong, Moderate and Weak.")
    P.para(f"**Generation and safety.** The answer is produced by Flan-T5-small {R('flan')} from a prompt that contains the symptoms and the retrieved records; if the model cannot be loaded, a deterministic template that lists the matched conditions, their symptoms and guidance is used instead. "
           "A safety layer of ten regular-expression rules (chest pain, breathing difficulty, severe bleeding, loss of consciousness, stroke signs, anaphylaxis, self-harm, sudden neurological signs, seizures, severe abdominal pain) "
           "prepends an emergency notice, six keywords raise a caution banner, a disclaimer is always shown, and a filter replaces five medication phrases in the answer.")
    P.para("**Implementation.** Requests are validated by Pydantic schemas (e-mail format, password of 6 to 128 characters, query of 3 to 2,000 characters), and failures return a JSON detail with a meaningful status: 400 for a duplicate account, 401 for a missing or invalid session or a wrong password, "
           "404 for another user's consultation, 422 for a malformed body, 503 when the knowledge base is missing and a generic 500 for an unexpected error. Every consultation row stores the query, the answer, the top condition, the five evidence records as JSON, the relevance and the safety flag, "
           "and every history query filters on the signed-in user, so one user cannot read or delete another's records (covered by a test). The history list returns the latest 200 consultations and can be searched by symptom or condition. "
           "The models load lazily on the first chat request, which takes about a minute on the test machine.")
    P.para("**Reproducibility.** The knowledge base, indexes, probe sets and every number in Section IV are produced by scripts in the repository (data preparation with a fixed seed, an index builder, a measurement script and a screen-capture script), "
           "and the figures quoted here are read from the JSON files they write, so the text cannot drift from the measurements. The application starts with one batch file, uses ports 8412 and 5412, and creates a demo account on first start.")
    P.para(f"**Evaluation protocol.** Top-1, top-3 and mean reciprocal rank (MRR@5) of the true condition are computed for five query sets: the 30 held-out records of the shipped script with the record still indexed (the shipped protocol); the same 30 with the record removed (leave-one-out); "
           f"all {k['records']} records as verbatim queries, leave-one-out; {k['records']} queries of two random symptoms, leave-one-out; and 60 lay-language descriptions (two per condition) written by the authors. "
           f"Seven configurations are compared: BM25, dense, hybrid, hybrid with the cross-encoder (shipped), the shipped system without the expansion template, and the offline TF-IDF fallback with and without BM25. "
           f"Intervals are Wilson 95% intervals. Safety rules were tried on {sa['n_pos']} emergency and {sa['n_neg']} non-emergency sentences written by the authors, and latency was timed over 30 requests. "
           f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} pytest tests and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} end-to-end smoke checks pass.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** Everything ran on the machine of Section I-A with warm models. The knowledge base is synthetic, siblings of a held-out record stay in the index, and the lay-language probes were written by the authors, not by clinicians, "
           "so all accuracies are optimistic and say nothing about real patients. Table II gives the top-1 results.")
    cfgs = [("bm25", "BM25 only"), ("dense", "Dense only (MiniLM, FAISS)"), ("hybrid", "Hybrid fusion"), ("hybrid_rerank", "Hybrid + cross-encoder (shipped)"), ("hybrid_rerank_nohyde", "Shipped, no expansion template"),
            ("hybrid_tfidf", "Offline: TF-IDF + BM25")]
    rows = []
    for c, lab in cfgs:
        rows.append([lab, f2(t1(c, "S1_shipped_protocol_30")), f2(t1(c, S2)), f2(t1(c, S3)), f2(t1(c, S4))])
    P.table("Top-1 condition accuracy by configuration and query set", ["Configuration", "Shipped (30)", "Verbatim LOO (176)", "Two symptoms (176)", "Lay (60)"], rows,
            widths=[1.35, 0.5, 0.5, 0.5, 0.5], size=7, align=["l", "c", "c", "c", "c"])
    P.figure(figs["results"], "(a) Top-1 accuracy of each retrieval configuration on three query sets. (b) The raw cross-encoder score of the top record for in-knowledge-base and out-of-knowledge-base queries.")
    P.para(f"**Retrieval.** The shipped protocol scores 1.00 for every configuration that includes BM25, which is why the 100% on the application's About page is an upper bound for the wiring and not an accuracy. "
           f"Removing the held-out record gives {f2(t1('hybrid_rerank', S1))} on the same 30 queries and {f2(t1('hybrid_rerank', S2))} on all {k['records']} verbatim queries (Wilson 95% interval {F.ci('hybrid_rerank', S2)}). "
           f"With only two symptoms the shipped system falls to {f2(t1('hybrid_rerank', S3))} ({F.ci('hybrid_rerank', S3)}), because pairs such as headache with fatigue or fever with chills fit several conditions, and on lay language it reaches {f2(t1('hybrid_rerank', S4))} ({F.ci('hybrid_rerank', S4)}). "
           f"The cross-encoder helps on lay language (hybrid {f2(t1('hybrid', S4))} to {f2(t1('hybrid_rerank', S4))}) and on two-symptom queries ({f2(t1('hybrid', S3))} to {f2(t1('hybrid_rerank', S3))}). "
           f"BM25 alone is competitive ({f2(t1('bm25', S4))} on lay language, 1.00 on verbatim queries) because the knowledge base is small and its vocabulary is repeated; dense retrieval alone is weaker on verbatim queries ({f2(t1('dense', S2))}) and on two symptoms ({f2(t1('dense', S3))}).")
    s2m = S["hybrid_rerank"][S2]["misses"]
    s3m = S["hybrid_rerank"][S3]["misses"]
    P.para(f"**Where retrieval fails.** The {S['hybrid_rerank'][S2]['n_misses']} verbatim misses are almost all typhoid, the condition with the fewest records ({F.KB['records_per_condition']['Typhoid']}): once one record is removed its remaining symptom lists look like influenza, appendicitis or migraine. "
           f"The {S['hybrid_rerank'][S3]['n_misses']} two-symptom misses are overlaps between conditions that really share symptoms in the base: \"{s3m[1]['query'].replace('I have ', '')}\" went to {s3m[1]['predicted'].lower()} instead of {s3m[1]['truth'].lower()}, "
           f"\"{s3m[3]['query'].replace('I have ', '')}\" to {s3m[3]['predicted'].lower()} instead of {s3m[3]['truth'].lower()}, and \"{s3m[6]['query'].replace('I have ', '')}\" to {s3m[6]['predicted'].lower()} instead of {s3m[6]['truth'].lower()}. "
           "Because the interface shows five cards that are mostly the same condition, a user is not shown the second-best alternative in these cases.")
    pc = F.M["lay_per_condition_correct"]
    both = sum(1 for v in pc.values() if v[0] == v[1])
    P.para(f"**Per-condition view.** On the lay probes {both} of {len(pc)} conditions were retrieved correctly for both of their descriptions. The two exceptions each lost one probe (common cold and typhoid). "
           "Emergency conditions (heart attack, stroke, anaphylaxis, appendicitis) were all retrieved correctly, but that is a statement about retrieval; whether the user is told to seek urgent care depends on the separate safety rules, which behave differently (below).")
    P.para(f"**Expansion and offline mode.** The template expansion does not help: without it the shipped system scores {f2(t1('hybrid_rerank_nohyde', S4))} on lay language, {f2(t1('hybrid_rerank_nohyde', S2))} on verbatim and {f2(t1('hybrid_rerank_nohyde', S3))} on two-symptom queries, "
           "never lower than with it, although the lay-language difference is only two of 60 probes. The template adds the same generic words to every query. In offline mode (TF-IDF vectors with BM25, no reranker) accuracy on lay language drops to "
           f"{f2(t1('hybrid_tfidf', S4))} while verbatim queries stay at {f2(t1('hybrid_tfidf', S2))}, so the fallback keeps the application usable but is weaker on everyday wording. "
           f"The five evidence cards are a poor differential: a condition has several near-identical records, so the top five contain on average {S['hybrid_rerank'][S4]['mean_distinct_conditions_in_top5']} distinct conditions on the lay probes.")
    P.para(f"**Failure cases.** On the lay probes the shipped system missed {S['hybrid_rerank'][S4]['n_misses']}: a running nose with a slight cough was called allergic rhinitis instead of a common cold, and a slow-rising fever with weakness and abdominal pain was called appendicitis instead of typhoid. "
           "Both are plausible confusions between conditions that share symptoms in the knowledge base.")
    P.para(f"**Displayed relevance.** The relevance is normalised over the candidates, so the top record is always 100%: all 60 in-base probes and all {rel['out_kb_n']} out-of-base complaints (tooth ache, sprained ankle, lower back pain) were shown as a Strong match, "
           f"and the 15 out-of-base queries still returned a condition. The raw cross-encoder score does separate them (mean {rel['raw_rerank_in_kb']['mean']} against {rel['raw_rerank_out_kb']['mean']}; area under the ROC curve {rel['auroc_in_vs_out_by_raw_rerank_score']:.2f}, "
           "Fig. 3b), so the information needed for an honest confidence exists but is discarded by the display.")
    P.table("Safety layer, generation and latency", ["Measurement", "Result"], [
        ["Emergency sentences flagged, literal wording", f"{lit['detected']}/{lit['n']}"],
        ["Emergency sentences flagged, paraphrased wording", f"{par['detected']}/{par['n']}"],
        ["False emergencies on 20 ordinary / 10 hard negatives", f"0/20 / {len(hard['false_emergency'])}/10"],
        [f"Medication filter, {flt['n']} test sentences cleaned", f"{flt['removed']}/{flt['n']}"],
        ["Flan-T5 answers that echo the prompt", f"{g['echo_answers']}/{g['n']}"],
        ["Cross-encoder stage, mean (p95)", f"{st['rerank']['mean']:.0f} ms ({st['rerank']['p95']:.0f} ms)"],
        ["POST /api/chat, fallback answer, mean (p95)", f"{F.LAT_FB['chat_ms']['mean']:.0f} ms ({F.LAT_FB['chat_ms']['p95']:.0f} ms)"],
        ["POST /api/chat, Flan-T5 answer, mean (p95)", f"{F.LAT_T5['chat_ms']['mean']:.0f} ms ({F.LAT_T5['chat_ms']['p95']:.0f} ms)"],
    ], widths=[2.45, 0.95], size=7, align=["l", "c"])
    P.para(f"**Safety layer.** The rules flagged {lit['detected']} of {lit['n']} emergency sentences worded like the rules and none of {par['n']} paraphrases (\"pressure in my chest and my left arm hurts\", \"gasping for air\", \"I do not want to live anymore\"), "
           f"so overall recall is {pct(sa['emergency_recall'], 1)} (Wilson interval {pct(sa['recall_ci'][0], 0)}-{pct(sa['recall_ci'][1], 0)}). Negation and history trigger false alarms: {len(hard['false_emergency'])} of 10 hard negatives such as \"I do not have difficulty breathing\" or a stroke in the family were flagged as emergencies. "
           f"The medication filter replaces text case-sensitively, so \"Take ibuprofen\" and \"Dosage:\" pass through, and drugs outside its five phrases are not touched ({flt['removed']} of {flt['n']} test sentences cleaned).")
    P.figure(figs["safety"], "Safety layer on the author-written sentences: emergencies flagged and false alarms.", width=3.0)
    P.para(f"**Generation.** With the installed Transformers {g['transformers_version']} the task used by the generator no longer exists, the code falls back to plain text generation, and Flan-T5 returns its prompt unchanged: all {g['echo_answers']} of {g['n']} answers repeat the instructions and the retrieved records and are still labelled as locally generated (Fig. 5 shows the evidence-based fallback instead). "
           f"The fallback is deterministic and cannot name a condition that was not retrieved, so answers are grounded by construction but not synthesised, they do not cite sources per statement, and groundedness was not judged by humans or a model.")
    P.para(f"**Speed and tests.** On the CPU the cross-encoder dominates ({st['rerank']['mean']:.0f} ms for 15 pairs); embedding takes {st['embed']['median']:.0f} ms (median) and FAISS, BM25 and fusion together under {st['faiss']['mean'] + st['bm25']['mean'] + st['fuse']['mean'] + 1:.0f} ms. "
           f"A chat request takes {F.LAT_FB['chat_ms']['mean']:.0f} ms over HTTP with the fallback answer and {F.LAT_T5['chat_ms']['mean']:.0f} ms with Flan-T5; loading all models on first use takes about a minute. "
           f"The {F.PYTEST_TOTAL} pytest tests ({F.PYTEST_SECONDS:.0f} s) and {F.SMOKE_TOTAL} smoke checks pass; there is no load test, user study or clinical review.")
    P.table("Pipeline stage latency (30 requests, warm models)", ["Stage", "Mean (ms)", "Median (ms)", "p95 (ms)"],
            [[lab, f"{st[key]['mean']:.2f}", f"{st[key]['median']:.2f}", f"{st[key]['p95']:.2f}"] for key, lab in
             (("expand", "Query expansion (template)"), ("embed", "MiniLM embedding"), ("faiss", "FAISS search"), ("bm25", "BM25 search"), ("fuse", "Score fusion"),
              ("rerank", "Cross-encoder, 15 pairs"), ("safety", "Safety rules"))],
            widths=[1.6, 0.6, 0.6, 0.6], size=7, align=["l", "c", "c", "c"])
    P.figure(figs["emergency"], "Output screen: an emergency query (\"severe chest pain and difficulty breathing\") shows the emergency banner above the evidence-based answer.", width=3.3)
    P.figure(figs["history"], "Output screen: the private consultation history with search, top condition, safety flag (routine, caution, emergency) and relevance, which is 100% for every row.")
    P.para(f"**Comparison with the base paper.** The base paper {R('base')} reports no number, so there is nothing to compare quantitatively, and its knowledge base is of unstated size. Qualitatively, SymptoTrackAI adds BM25 retrieval, a cross-encoder, query expansion, an offline fallback, a safety layer and measurements, "
           "and it keeps the base paper's registration, login and history. Its knowledge base is synthetic and tiny, so the conditions, data and tasks differ and no claim of superiority is made. "
           "Symptom tracking over time is still only a searchable list of consultations; trends and progression are not computed.")

    P.para(f"**Threats to validity.** The knowledge base and the condition descriptions were written by the project, so there is no external ground truth; sibling records of a condition share their description and guidance, which makes condition retrieval easier than in a real corpus; "
           f"the 60 lay-language probes and the {sa['n_pos'] + sa['n_neg']} safety sentences were written by the same authors who built the rules, which favours the system; the intervals are wide for 60 probes ({F.ci('hybrid_rerank', S4)}); "
           "answers were not rated by clinicians or users; and all timings come from one CPU-only machine. The numbers are evidence that the pipeline works and that specific defects exist, not a benchmark of clinical quality.")
    P.table("Objectives against outcome", ["Objective", "Status"], [
        ["1. Curated knowledge base, indexed", "Done: synthetic, 176 records, FAISS + BM25"],
        ["2. Natural language and query expansion", "Done: template expansion, no measured gain"],
        ["3. Hybrid retrieval with reranking", "Done and measured (Table II)"],
        ["4. Grounded answers, source cited per statement", "Partly: evidence cards, no per-statement citation"],
        ["5. Track symptoms over time, show trends", "Not done beyond storage and search"],
        ["6. Evaluate relevance, groundedness, time", "Relevance and time measured; groundedness not judged"],
    ], widths=[1.6, 1.8], size=7, align=["l", "l"])

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"SymptoTrackAI, as the CareLens AI application, retrieves grounded information for symptoms in everyday language with hybrid retrieval and reranking, escalates some emergencies, and keeps a private history. "
           f"Against the six objectives, the knowledge base (synthetic), query expansion (a template), hybrid retrieval with reranking and the evaluation of relevance and response time are achieved; grounded answers are partly achieved (no per-statement citation, and the local generator echoes its prompt); "
           f"and tracking symptoms over time is not achieved beyond storage. The key finding is that the ranking works on this small base ({pct(t1('hybrid_rerank', S4), 0)} on lay language) but that a lexical baseline is nearly as good, the expansion template adds nothing, "
           f"and the safety and confidence displays are weaker than the retrieval: none of {par['n']} paraphrased emergencies was flagged and every answer is shown as a strong match. Other limits are the synthetic base, the authors' own probes and one CPU-only machine.")
    P.para("Future work: replace the base with a clinically reviewed source; restore the generator with a supported task and add per-statement citations; show the raw reranker score as the confidence and refuse out-of-base queries; "
           "add a trained emergency classifier with negation handling; and compute symptom trends and progression from the stored history.")

    P.references()
    P.save(path)
    return path, P.order


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    path, order = build(out)
    print(path, "refs:", len(order), order)
