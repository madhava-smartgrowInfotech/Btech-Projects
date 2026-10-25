"""
Design diagrams for the report and the decks, drawn from what the code does (backend/main.py, db.py, utils/*).

    python scripts\\make_diagrams.py        # system Python with matplotlib; writes docs/diagrams/*.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagram_kit import *  # noqa: E402,F401,F403

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)


def out(name):
    return os.path.join(OUT, name)


# ---------------------------------------------------------------- 01 architecture
def d01():
    fig, ax = canvas(10, 7.0, ylim=(0, 70))
    title(ax, "System architecture", y=69)
    box(ax, 2, 44, 26, 22, "", theme="violet")
    label(ax, 15, 64, "Browser: React 19 app", fs=9, color=VIOLET, bold=True)
    for i, t in enumerate(["Landing, Login, Register", "Upload  |  Documents", "Ask  |  Quiz", "Roadmap  |  Dashboard"]):
        box(ax, 4, 58.2 - i * 3.8, 22, 3.2, t, theme="white", fs=7.6)
    box(ax, 40, 30, 34, 36, "", theme="cyan")
    label(ax, 57, 64, "FastAPI service (port 8301)", fs=9, color=CYAN, bold=True)
    box(ax, 42, 56.5, 30, 4.5, "CORS  +  signed session cookie\n(alip_session, 7 days)", theme="white", fs=7.8)
    box(ax, 42, 46, 30, 9, "14 JSON endpoints\n/api/auth  /api/documents  /api/ask\n/api/quiz  /api/roadmap  /api/dashboard", theme="white", fs=7.8)
    box(ax, 42, 32, 14, 12.5, "RAGEngine\nTF-IDF index\nper user\n(in memory)", theme="green", fs=7.8)
    box(ax, 58, 32, 14, 12.5, "Document analysis\nQuiz generator\nRoadmap rules", theme="green", fs=7.8)
    cylinder(ax, 82, 46, 15, 14, "SQLite\napp.db\n5 tables", theme="amber", fs=8.5)
    box(ax, 80, 30, 19, 11, "uploads/<user id>/\noriginal PDF, DOCX,\nTXT files", theme="amber", fs=7.8)
    box(ax, 80, 8, 18, 12, "Anthropic API\n(optional, only if\nANTHROPIC_API_KEY\nis set)", theme="grey", fs=7.8, ls="--")
    box(ax, 2, 8, 28, 14, "Original Flask interface\n(port 5000, Jinja templates)\nshares db.py and utils/", theme="grey", fs=8, ls="--")
    arrow(ax, (28, 55), (40, 55), theme="violet", lw=1.8)
    arrow(ax, (40, 50), (28, 50), theme="violet", lw=1.8)
    label(ax, 34, 47.5, "JSON over /api\n(Vite proxy\n5301 to 8301)", fs=7, va="top")
    arrow(ax, (74, 53), (82, 53), "SQL", theme="amber", fs=8)
    arrow(ax, (74, 36), (80, 36), "files", theme="amber", fs=8)
    arrow(ax, (49, 32), (49, 22), theme="grey")
    poly_arrow(ax, [(65, 32), (65, 14), (80, 14)], "HTTPS\nrequest", theme="grey", ls="--", fs=7.5, tidx=1, toff=(0, 4))
    poly_arrow(ax, [(16, 22), (16, 27), (42, 27), (42, 32)], theme="grey", ls="--")
    label(ax, 29, 25.5, "same modules", fs=7.5, color=MUTED)
    label(ax, 51, 20.5, "reads chunks of the\nuser's documents", fs=7.5, color=MUTED, va="top", ha="left")
    ax.text(50, 3.0, "Solid arrows: the React interface path. Dashed: optional or legacy paths.", ha="center", fontsize=8, color=MUTED)
    save(fig, out("01_system_architecture.png"))


# ---------------------------------------------------------------- 03 DFD0
def d03():
    fig, ax = canvas(9, 4.6, ylim=(0, 46))
    title(ax, "Data flow diagram, level 0 (context)", y=45)
    box(ax, 2, 17, 17, 12, "Student", theme="violet", fs=11, bold=True)
    circle_process(ax, 50, 23, 13.5, "Adaptive Learning\nIntelligence\nPlatform", theme="cyan", fs=9.5, num="0")
    box(ax, 78, 28, 19, 10, "LLM provider\n(Anthropic API,\noptional)", theme="grey", fs=8.2)
    arrow(ax, (19, 27), (36.8, 27), "registration, login,\nstudy files, questions,\nquiz answers", theme="violet", fs=7.8, toff=(0, 4.8))
    arrow(ax, (36.8, 19), (19, 19), "topics, cited answers,\nquizzes and scores,\nroadmap, dashboard", theme="cyan", fs=7.8, toff=(0, -5))
    arrow(ax, (63.2, 27.5), (78, 31), "question +\nretrieved context", theme="grey", fs=7.5, ls="--", toff=(0, 4.5))
    arrow(ax, (78, 34.5), (62.5, 30.5), theme="grey", ls="--", rad=-0.3)
    label(ax, 74, 22, "generated\nanswer", fs=7.5, color=MUTED)
    save(fig, out("03_dfd_level0.png"))


# ---------------------------------------------------------------- 04 DFD1
def d04():
    fig, ax = canvas(10, 8.4, xlim=(0, 104), ylim=(0, 84))
    title(ax, "Data flow diagram, level 1", y=83.5)
    box(ax, 1, 34, 13, 14, "Student", theme="violet", fs=11, bold=True)
    P = {"1.0": (36, 72, "Authenticate\nuser"), "2.0": (36, 57, "Analyse\ndocuments"), "3.0": (36, 42, "Answer\nquestions"),
         "4.0": (36, 27, "Generate and\ngrade quizzes"), "5.0": (36, 12, "Build roadmap\nand dashboard")}
    for n, (cx, cy, t) in P.items():
        circle_process(ax, cx, cy, 7.0, t, theme="cyan", fs=7.6, num=n)
    S = {"D1": (69, "D1  users"), "D2": (59, "D2  documents"), "D3": (49.5, "D3  chunks"), "D4": (39, "D4  queries"), "D5": (14, "D5  quiz_results")}
    for k, (y, t) in S.items():
        store(ax, 76, y, 22, 6.5, t, "amber")
    arrow(ax, (10, 48), (30.5, 68), "credentials", theme="violet", fs=7.5, tpos=0.42, toff=(-3, 2.5))
    arrow(ax, (12, 48), (30, 59.5), "PDF, DOCX, TXT", theme="violet", fs=7.5, tpos=0.42, toff=(-5, 2.5))
    arrow(ax, (14, 43), (29, 43), "question", theme="violet", fs=7.5, tpos=0.5, toff=(0, 1.8))
    arrow(ax, (29, 40.5), (14, 40.5), "cited answer", theme="cyan", fs=7.5, tpos=0.5, toff=(0, -1.9))
    arrow(ax, (12, 34), (30, 28.5), "quiz answers", theme="violet", fs=7.5, tpos=0.5, toff=(-1, -2.2))
    arrow(ax, (30, 25.5), (10, 34), "questions,\nscore", theme="cyan", fs=7.5, tpos=0.42, toff=(1.5, -4.2))
    arrow(ax, (30.5, 14), (6, 34), "roadmap,\ndashboard", theme="cyan", fs=7.5, tpos=0.30, toff=(-5, 0))
    arrow(ax, (43, 72.5), (76, 72.5), "user record", theme="amber", fs=7.5, toff=(0, 1.8))
    arrow(ax, (76, 71), (43, 71), theme="amber")
    arrow(ax, (43, 58.5), (76, 62.2), "document row + topics", theme="amber", fs=7.5, tpos=0.6, toff=(0, 2.4))
    arrow(ax, (43, 55.5), (76, 53.3), "chunks", theme="amber", fs=7.5, tpos=0.66, toff=(0, -1.9))
    arrow(ax, (76, 50.5), (43, 45.5), "chunks of the\nuser's documents", theme="amber", fs=7.5, tpos=0.6, toff=(0, -3.4))
    arrow(ax, (43, 40.5), (76, 42.2), "question, answer,\nsource files", theme="amber", fs=7.5, tpos=0.62, toff=(0, -3.5))
    arrow(ax, (43, 25.5), (76, 17.2), "result per topic\n(correct / wrong)", theme="amber", fs=7.5, tpos=0.62, toff=(0, 3.6))
    arrow(ax, (76, 15), (43, 11), "attempts per topic", theme="amber", fs=7.5, tpos=0.55, toff=(0, -2.3))
    poly_arrow(ax, [(98, 52.7), (100, 52.7), (100, 29), (43, 29)], "chunks of the chosen document", theme="amber", fs=7.5, tidx=2, toff=(-5, 1.8))
    poly_arrow(ax, [(98, 62.2), (102.2, 62.2), (102.2, 7.5), (43, 7.5)], "documents, queries (counts)", theme="amber", fs=7.5, tidx=2, toff=(-5, -1.8))
    poly_arrow(ax, [(98, 42.2), (102.2, 42.2)], theme="amber")
    label(ax, 50, 2.0, "The uploaded file itself is also written to uploads/<user id>/ by process 2.0.", fs=7.8, color=MUTED)
    save(fig, out("04_dfd_level1.png"))


# ---------------------------------------------------------------- 02 workflow
def d02():
    fig, ax = canvas(10, 6.4, ylim=(0, 64))
    title(ax, "High-level workflow", y=63)
    label(ax, 2, 58, "1  Ingest and analyse", fs=9, color=VIOLET, bold=True, ha="left")
    steps = ["Upload\nPDF / DOCX / TXT", "Extract text\n(pypdf, python-docx)", "Clean and chunk\n180 words, 30 overlap", "Detect subject / unit\nhints + TF-IDF topics", "Store document,\ntopics and chunks"]
    xs = [2, 21, 40, 59, 78]
    for i, (x, t) in enumerate(zip(xs, steps)):
        box(ax, x, 45, 18, 10, t, theme="violet", fs=8.2)
        if i:
            arrow(ax, (xs[i - 1] + 18, 50), (x, 50), theme="violet", lw=1.8)
    box(ax, 56, 31, 39, 8, "Rebuild the user's TF-IDF index\n(unigrams + bigrams, English stop words)", theme="cyan", fs=8.2)
    poly_arrow(ax, [(87, 45), (87, 39)], theme="cyan", lw=1.8)
    label(ax, 2, 33, "2  Ask your notes", fs=9, color=GREEN, bold=True, ha="left")
    box(ax, 2, 15, 14, 9, "Question", theme="green", fs=8.2)
    box(ax, 21, 15, 18, 9, "Retrieve top 4 chunks\n(cosine similarity)", theme="green", fs=8.2)
    box(ax, 44, 15, 22, 9, "Select key sentences\n(or ask Claude if a key is set)", theme="green", fs=8.2)
    box(ax, 71, 15, 24, 9, "Answer + cited\nsource passages", theme="green", fs=8.2)
    arrow(ax, (16, 19.5), (21, 19.5), theme="green", lw=1.8)
    arrow(ax, (39, 19.5), (44, 19.5), theme="green", lw=1.8)
    arrow(ax, (66, 19.5), (71, 19.5), theme="green", lw=1.8)
    poly_arrow(ax, [(56, 35), (30, 35), (30, 24)], theme="cyan", ls="--")
    label(ax, 43, 36.4, "index used for retrieval", fs=7.3, color=MUTED)
    label(ax, 2, 10.6, "3  Practise and adapt", fs=9, color=AMBER, bold=True, ha="left")
    box(ax, 2, 1, 21, 6.5, "Generate 5 fill-in-the-blank\nquestions from a document", theme="amber", fs=7.8)
    box(ax, 28, 1, 18, 6.5, "Submit answers,\nserver grades them", theme="amber", fs=7.8)
    box(ax, 51, 1, 22, 6.5, "Accuracy per topic:\nHigh <50, Medium <80, Low", theme="amber", fs=7.8)
    box(ax, 78, 1, 18, 6.5, "Roadmap and\ndashboard update", theme="amber", fs=7.8)
    for a, b in [(23, 28), (46, 51), (73, 78)]:
        arrow(ax, (a, 4.2), (b, 4.2), theme="amber", lw=1.8)
    save(fig, out("02_high_level_workflow.png"))


# ---------------------------------------------------------------- 05 / 06 DFD2
def flow_labels(ax, xs, y, names, fs=6.9):
    for (a, b), n in zip(zip(xs[:-1], xs[1:]), names):
        label(ax, (a + b) / 2, y, n, fs=fs, color=MUTED)


def d05():
    fig, ax = canvas(10, 5.6, xlim=(0, 104), ylim=(0, 56))
    title(ax, "Data flow diagram, level 2: process 2.0 Analyse documents", y=55.5)
    box(ax, 1, 33, 11, 10, "Student", theme="violet", fs=10, bold=True)
    items = [("2.1", "Validate\nfile"), ("2.2", "Save\nfile"), ("2.3", "Extract\ntext"), ("2.4", "Clean and\nchunk"), ("2.5", "Detect hints\nand topics"), ("2.6", "Persist and\nre-index")]
    xs = [26, 40, 54, 68, 82, 96]
    for x, (n, t) in zip(xs, items):
        circle_process(ax, x, 38, 6.2, t, theme="cyan", fs=7, num=n)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 6.2, 38), (b - 6.2, 38), theme="grey", lw=1.5)
    flow_labels(ax, xs, 46.4, ["valid file", "saved\nfile", "raw\ntext", "word\nchunks", "chunks +\ntopics"])
    arrow(ax, (12, 38), (19.8, 38), theme="violet")
    label(ax, 16, 41.2, "file,\nsubject", fs=7, color=INK)
    arrow(ax, (26, 44.2), (26, 51), theme="rose")
    label(ax, 36, 50, "error: type, size, empty", fs=7.2, color=ROSE)
    poly_arrow(ax, [(26, 51), (6, 51), (6, 43)], theme="rose")
    store(ax, 26, 12, 24, 6.5, "files: uploads/<user>/", "amber", fs=7.6)
    store(ax, 56, 12, 20, 6.5, "D2  documents", "amber", fs=7.8)
    store(ax, 80, 12, 20, 6.5, "D3  chunks", "amber", fs=7.8)
    arrow(ax, (40, 31.8), (38, 18.5), "original file", theme="amber", fs=7.2, tpos=0.5, toff=(-7, 0))
    arrow(ax, (92, 33.5), (66, 18.5), "document row, topics", theme="amber", fs=7.2, tpos=0.55, toff=(-1.5, 3.8))
    arrow(ax, (97, 31.8), (92, 18.5), "chunks", theme="amber", fs=7.2, tpos=0.5, toff=(5, 0))
    box(ax, 56, 1, 44, 6, "User's in-memory TF-IDF index rebuilt from all chunks", theme="green", fs=7.6)
    arrow(ax, (90, 12), (90, 7), theme="green", ls="--")
    save(fig, out("05_dfd_level2_documents.png"))


def d06():
    fig, ax = canvas(10, 6.4, xlim=(0, 104), ylim=(0, 64))
    title(ax, "Data flow diagram, level 2: process 3.0 Answer questions", y=63.5)
    box(ax, 1, 28, 11, 10, "Student", theme="violet", fs=10, bold=True)
    items = [("3.1", "Validate\nquestion"), ("3.2", "Get the\nuser's index"), ("3.3", "Score\nchunks"), ("3.4", "Select\ntop 4"), ("3.5", "Compose\nanswer"), ("3.6", "Log\nquery")]
    xs = [26, 40, 54, 68, 82, 96]
    for x, (n, t) in zip(xs, items):
        circle_process(ax, x, 33, 6.2, t, theme="cyan", fs=7, num=n)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 6.2, 33), (b - 6.2, 33), theme="grey", lw=1.5)
    flow_labels(ax, xs[:4], 41.2, ["question", "TF-IDF\nindex", "cosine\nscores"])
    label(ax, 75, 41.2, "top 4\nchunks", fs=6.9, color=MUTED)
    label(ax, 89, 29.4, "answer +\nsources", fs=6.9, color=MUTED, va="top")
    arrow(ax, (12, 33), (19.8, 33), theme="violet")
    label(ax, 16, 36.2, "question", fs=7, color=INK)
    arrow(ax, (26, 39.2), (26, 46), theme="rose")
    label(ax, 36, 46.5, "empty: error 400", fs=7.2, color=ROSE)
    poly_arrow(ax, [(26, 46), (6, 46), (6, 38)], theme="rose")
    poly_arrow(ax, [(82, 26.8), (82, 19), (6, 19), (6, 28)], theme="cyan")
    label(ax, 64, 20.8, "answer + source passages (file, passage number, match score)", fs=7.2, color=INK)
    store(ax, 28, 3, 28, 6.5, "D3 chunks + D2 documents", "amber", fs=7.6)
    arrow(ax, (40, 9.5), (40, 26.8), "user's chunks\n(only if no cached index)", theme="amber", fs=7.2, tpos=0.2, toff=(12, 0.5))
    store(ax, 76, 3, 24, 6.5, "D4  queries", "amber", fs=7.8)
    arrow(ax, (96, 26.8), (92, 9.5), theme="amber")
    label(ax, 86.5, 13.5, "question, answer,\nsource files", fs=7.2, color=INK)
    box(ax, 62, 52, 36, 9, "LLM provider (optional): used only when\nANTHROPIC_API_KEY is set; a failed call\nfalls back to the extractive answer", theme="grey", fs=7, ls="--")
    arrow(ax, (80, 52), (80, 39.4), theme="grey", ls="--")
    arrow(ax, (84, 39.4), (84, 52), theme="grey", ls="--")
    label(ax, 79, 46, "question +\ncontext", fs=6.8, color=MUTED, ha="right")
    label(ax, 85, 46, "text", fs=6.8, color=MUTED, ha="left")
    save(fig, out("06_dfd_level2_rag.png"))


# ---------------------------------------------------------------- 07 UML class diagram
def uml_class(ax, x, y, w, name, attrs, ops, theme="white", fs=6.9, stereotype=None, row=2.45):
    ec, fc = THEMES[theme]
    h_head = 5.0 if stereotype else 3.5
    h_attr = max(1, len(attrs)) * row + 1.0
    h_ops = max(1, len(ops)) * row + 1.0 if ops else 0
    H = h_head + h_attr + h_ops
    ax.add_patch(Rectangle((x, y - H), w, H, fc=WHITE, ec=ec, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x, y - h_head), w, h_head, fc=fc, ec=ec, lw=1.4, zorder=3))
    if stereotype:
        ax.text(x + w / 2, y - 1.2, stereotype, ha="center", va="center", fontsize=fs - 0.6, color=MUTED, zorder=4)
        ax.text(x + w / 2, y - 3.4, name, ha="center", va="center", fontsize=fs + 0.8, color=INK, fontweight="bold", zorder=4)
    else:
        ax.text(x + w / 2, y - h_head / 2, name, ha="center", va="center", fontsize=fs + 0.8, color=INK, fontweight="bold", zorder=4)
    if ops:
        ax.plot([x, x + w], [y - h_head - h_attr, y - h_head - h_attr], color=ec, lw=1.0, zorder=3)
    for i, a in enumerate(attrs):
        ax.text(x + 0.9, y - h_head - 0.5 - i * row, a, ha="left", va="top", fontsize=fs, color=INK, zorder=4, family="DejaVu Sans Mono")
    for i, o in enumerate(ops):
        ax.text(x + 0.9, y - h_head - h_attr - 0.5 - i * row, o, ha="left", va="top", fontsize=fs, color=INK, zorder=4, family="DejaVu Sans Mono")
    return (x, y - H, w, H)


def d07():
    fig, ax = canvas(11, 9.6, xlim=(0, 120), ylim=(0, 104))
    title(ax, "UML class diagram", y=103.5)
    top = 95
    uml_class(ax, 2, top, 44, "ApiService  (backend/main.py)", ["api: FastAPI", "_active_quizzes: dict[user_id, quiz]", "FRONTEND_PORT: str"],
              ["current_user(request)", "register(RegisterBody)", "login(LoginBody)", "upload_document(file, subject)", "delete_document(doc_id)", "ask(AskBody)",
               "quiz_generate(QuizGenerateBody)", "quiz_submit(QuizSubmitBody)", "roadmap()", "dashboard()"], theme="cyan", stereotype="<<FastAPI module>>")
    uml_class(ax, 52, top, 38, "RAGEngine  (utils/rag_engine.py)", ["vectorizer: TfidfVectorizer", "matrix: sparse matrix", "chunks: list[str]", "chunk_meta: list[dict]"],
              ["build_index(chunk_records)", "retrieve(query, top_k=4)", "_extractive_answer(query, retrieved)", "generate_answer(query, api_key, top_k)", "_llm_answer(query, retrieved, key)"], theme="green")
    uml_class(ax, 52, 62, 38, "TextExtraction  (utils/text_extraction.py)", ["SUBJECT_HINT_PATTERNS: list[str]"],
              ["extract_text(path)", "clean_text(text)", "chunk_text(text, 180, 30)", "detect_subject_hints(text)", "extract_topics(text, 12)", "allowed_file(name, exts)"], theme="green", stereotype="<<utility>>")
    uml_class(ax, 94, top, 24, "QuizGenerator", ["(module functions)"], ["generate_quiz(chunks,", "              n, subject)", "_candidate_terms(text)"], theme="green", stereotype="<<utility>>")
    uml_class(ax, 94, 70, 24, "Database  (db.py)", ["SCHEMA: str"], ["get_db()", "init_db()", "now()"], theme="amber", stereotype="<<utility>>")
    # dependency arrows
    arrow(ax, (46, 88), (52, 88), style="-|>", theme="grey", ls="--", lw=1.2)
    label(ax, 49, 89.6, "uses", fs=6.8, color=MUTED)
    arrow(ax, (46, 56), (52, 56), style="-|>", theme="grey", ls="--", lw=1.2)
    label(ax, 49, 57.6, "uses", fs=6.8, color=MUTED)
    poly_arrow(ax, [(24, 95), (24, 97.4), (106, 97.4), (106, 95)], theme="grey", ls="--", lw=1.2)
    label(ax, 66, 98.6, "uses", fs=6.8, color=MUTED)
    poly_arrow(ax, [(46, 66.2), (92, 66.2), (92, 66.2), (94, 66.2)], theme="grey", ls="--", lw=1.2)
    label(ax, 93, 67.6, "uses", fs=6.8, color=MUTED, ha="right")
    # entities
    ey = 28
    ents = [("User", 2, 21, ["id: int (PK)", "username: str (unique)", "password_hash: str", "interests: str", "created_at: str"]),
            ("Document", 26, 25, ["id: int (PK)", "user_id: int (FK)", "filename: str", "filepath: str", "subject: str", "topics: JSON text", "uploaded_at: str"]),
            ("Chunk", 54, 21, ["id: int (PK)", "document_id: int (FK)", "chunk_index: int", "text: str"]),
            ("Query", 78, 20, ["id: int (PK)", "user_id: int (FK)", "question: str", "answer: str", "sources: JSON text", "created_at: str"]),
            ("QuizResult", 101, 17, ["id: int (PK)", "user_id: int (FK)", "subject: str", "topic: str", "correct: 0 | 1", "created_at: str"])]
    for n, x, w, a in ents:
        uml_class(ax, x, ey, w, n, a, [], theme="amber", fs=6.5, row=2.35)
    A = THEMES["amber"][0]
    arrow(ax, (23, 18), (26, 18), style="-", theme="amber", lw=1.5)
    label(ax, 23.9, 19.4, "1", fs=7, color=INK)
    label(ax, 25.4, 19.4, "*", fs=8, color=INK)
    arrow(ax, (51, 18), (54, 18), style="-", theme="amber", lw=1.5)
    label(ax, 51.9, 19.4, "1", fs=7, color=INK)
    label(ax, 53.4, 19.4, "*", fs=8, color=INK)
    for x_to, ytop, w_, lab in [(88, 30.6, 0, "queries"), (109.5, 33.0, 0, "quiz_results")]:
        ax.plot([12, 12], [ey, ytop], color=A, lw=1.5, zorder=2)
        ax.plot([12, x_to], [ytop, ytop], color=A, lw=1.5, zorder=2)
        ax.plot([x_to, x_to], [ytop, ey], color=A, lw=1.5, zorder=2)
        label(ax, 13.6, ytop - 1.0, "1", fs=7, color=INK)
        label(ax, x_to - 1.6, ytop - 1.0, "*", fs=8, color=INK)
    label(ax, 64, 36.6, "RAGEngine.build_index() receives Chunk rows joined with Document names as dictionaries", fs=7, color=MUTED)
    ax.text(60, 2.0, "Solid lines: associations, one to many, ON DELETE CASCADE.   Dashed arrows: dependencies (the module calls the other).", ha="center", fontsize=7.4, color=MUTED)
    save(fig, out("07_uml_class_diagram.png"))


# ---------------------------------------------------------------- 08 / 09 sequence diagrams
def msg(ax, x1, x2, y, text, dashed=False, theme="violet", fs=7.4, above=True):
    arrow(ax, (x1, y), (x2, y), theme=theme, lw=1.3, ls="--" if dashed else "-")
    ax.text((x1 + x2) / 2, y + (1.3 if above else -1.3), text, ha="center", va="bottom" if above else "top", fontsize=fs, color=INK, zorder=6, linespacing=1.15)


def selfmsg(ax, x, y, text, theme="violet", fs=7.4, side=1):
    ec = THEMES[theme][0]
    ax.plot([x, x + 5 * side, x + 5 * side], [y, y, y - 2.6], color=ec, lw=1.3, zorder=4)
    arrow(ax, (x + 5 * side, y - 2.6), (x, y - 2.6), theme=theme, lw=1.3)
    ax.text(x + 6 * side, y - 1.3, text, ha="left" if side > 0 else "right", va="center", fontsize=fs, color=INK, zorder=6, linespacing=1.15)


def d08():
    fig, ax = canvas(10, 9.8, xlim=(0, 104), ylim=(0, 104))
    title(ax, "Sequence diagram: uploading a study document", y=103.5)
    X = {"s": 8, "ui": 24, "api": 44, "ut": 66, "db": 82, "rag": 96}
    names = {"s": ("Student", "violet"), "ui": ("React UI", "violet"), "api": ("FastAPI", "cyan"), "ut": ("text_extraction", "green"), "db": ("SQLite", "amber"), "rag": ("RAGEngine", "green")}
    for k, (t, th) in names.items():
        lifeline(ax, X[k], 93, 4, t, theme=th, w=14, fs=7.8)
    y = 86
    msg(ax, X["s"], X["ui"], y, "choose file + subject"); y -= 6
    msg(ax, X["ui"], X["api"], y, "POST /api/documents (multipart)"); y -= 5
    selfmsg(ax, X["api"], y, "session user, type and 16 MB check", theme="cyan"); y -= 7
    msg(ax, X["api"], X["ut"], y, "extract_text, clean_text", theme="cyan"); y -= 5.5
    msg(ax, X["ut"], X["api"], y, "plain text", dashed=True, theme="green"); y -= 6
    msg(ax, X["api"], X["ut"], y, "extract_topics, chunk_text(180, 30)", theme="cyan"); y -= 5.5
    msg(ax, X["ut"], X["api"], y, "topics (max 12), chunks", dashed=True, theme="green"); y -= 6
    msg(ax, X["api"], X["db"], y, "INSERT document, INSERT chunks", theme="cyan"); y -= 6
    msg(ax, X["api"], X["rag"], y, "get_engine_for_user(user_id)", theme="cyan"); y -= 5.5
    msg(ax, X["rag"], X["db"], y, "SELECT chunks JOIN documents", theme="green"); y -= 5.5
    selfmsg(ax, X["rag"], y, "TfidfVectorizer\n.fit_transform", theme="green", side=-1); y -= 8
    msg(ax, X["api"], X["ui"], y, "201 {document, topics_count, chunks_count}", dashed=True, theme="cyan", above=True); y -= 6
    msg(ax, X["ui"], X["s"], y, "toast + topic chips", dashed=True); y -= 4
    save(fig, out("08_sequence_upload.png"))


def d09():
    fig, ax = canvas(10, 9.8, xlim=(0, 104), ylim=(0, 104))
    title(ax, "Sequence diagram: asking a question", y=103.5)
    X = {"s": 8, "ui": 24, "api": 44, "rag": 64, "db": 80, "llm": 96}
    names = {"s": ("Student", "violet"), "ui": ("React UI", "violet"), "api": ("FastAPI", "cyan"), "rag": ("RAGEngine", "green"), "db": ("SQLite", "amber"), "llm": ("LLM (optional)", "grey")}
    for k, (t, th) in names.items():
        lifeline(ax, X[k], 93, 4, t, theme=th, w=14, fs=7.8)
    y = 86
    msg(ax, X["s"], X["ui"], y, "type question, Ctrl+Enter"); y -= 6
    msg(ax, X["ui"], X["api"], y, "POST /api/ask {question}"); y -= 5
    selfmsg(ax, X["api"], y, "current_user (cookie),\nreject empty", theme="cyan"); y -= 8
    msg(ax, X["api"], X["rag"], y, "cached engine or get_engine_for_user", theme="cyan"); y -= 5.5
    msg(ax, X["rag"], X["db"], y, "SELECT chunks (cache miss only)", dashed=True, theme="green"); y -= 6
    msg(ax, X["api"], X["rag"], y, "generate_answer(q, api_key, top_k=4)", theme="cyan"); y -= 5
    selfmsg(ax, X["rag"], y, "retrieve: vectorise query,\ncosine, top 4 (score > 0)", theme="green", side=-1); y -= 9
    # alt frame
    ax.add_patch(Rectangle((52, y - 15.5), 49, 17.5, fc="none", ec=GREY, lw=1.0, ls=(0, (3, 2)), zorder=2))
    ax.text(53, y + 1.0, "alt  API key configured", fontsize=7, color=MUTED, va="center", fontweight="bold")
    msg(ax, X["rag"], X["llm"], y - 3.2, "messages.create(context only)", theme="green");
    msg(ax, X["llm"], X["rag"], y - 8.0, "answer text", dashed=True, theme="grey")
    ax.plot([52, 101], [y - 9.6, y - 9.6], color=GREY, lw=0.8, ls=(0, (3, 2)))
    ax.text(53, y - 10.6, "else  extractive (also if the call fails)", fontsize=7, color=MUTED, va="center", fontweight="bold")
    selfmsg(ax, X["rag"], y - 11.2, "top sentences by TF-IDF", theme="green", side=-1)
    y -= 20
    msg(ax, X["rag"], X["api"], y, "answer, retrieved chunks", dashed=True, theme="green"); y -= 6
    msg(ax, X["api"], X["db"], y, "INSERT queries (question, answer, sources)", theme="cyan"); y -= 6
    msg(ax, X["api"], X["ui"], y, "{answer, sources[file, passage, score], llm_enabled}", dashed=True, theme="cyan"); y -= 6
    msg(ax, X["ui"], X["s"], y, "answer bubble, mode badge, sources", dashed=True)
    save(fig, out("09_sequence_ask.png"))


# ---------------------------------------------------------------- 10 use case diagram
def ucase(ax, cx, cy, w, h, text, theme="cyan", fs=7.8):
    ec, fc = THEMES[theme]
    ax.add_patch(Ellipse((cx, cy), w, h, fc=fc, ec=ec, lw=1.3, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, zorder=4, linespacing=1.1)


def d10():
    fig, ax = canvas(10, 8.6, xlim=(0, 120), ylim=(0, 100))
    title(ax, "Use case diagram", y=99.5)
    ax.add_patch(Rectangle((26, 3), 70, 92, fc="none", ec=GREY, lw=1.2, zorder=1))
    ax.text(61, 92.4, "Adaptive Learning Intelligence Platform", ha="center", fontsize=8.6, color=MUTED, fontweight="bold")
    actor(ax, 10, 44, "Student", theme="violet", s=1.4, fs=10)
    actor(ax, 110, 55, "LLM provider\n(optional)", theme="grey", s=1.4, fs=8.5)
    cases = ["Register an account", "Log in", "Log out", "Upload study material", "Browse documents\nand detected topics", "Delete a document", "Ask a question\nabout the notes",
             "Review recent questions", "Take a quiz on a document", "View the study roadmap", "View the dashboard"]
    ys = [84 - i * 7.3 for i in range(len(cases))]
    for t, y in zip(cases, ys):
        ucase(ax, 52, y, 36, 6.2, t, theme="cyan", fs=7.6)
        arrow(ax, (15, 50), (34.2, y), style="-", theme="violet", lw=0.9)
    ucase(ax, 86, ys[6] - 1, 24, 6.2, "Generate answer\nwith Claude", theme="grey", fs=7.4)
    arrow(ax, (74.2, ys[6] - 0.8), (70.2, ys[6] - 0.2), style="-|>", theme="grey", ls="--", lw=1.2)
    label(ax, 72.4, ys[6] + 3.4, "<<extend>>", fs=7, color=MUTED, ha="left")
    arrow(ax, (98, ys[6] - 1), (105, 56), style="-", theme="grey", lw=0.9)
    ucase(ax, 86, ys[8], 24, 6.2, "Grade answers\nand record topics", theme="cyan", fs=7.4)
    arrow(ax, (74, ys[8]), (70.2, ys[8]), style="-|>", theme="grey", ls="--", lw=1.2)
    label(ax, 72.4, ys[8] + 3.4, "<<include>>", fs=7, color=MUTED, ha="left")
    ax.text(61, 0.8, "Every use case except Register and Log in requires an authenticated session (HTTP 401 otherwise).", ha="center", fontsize=7.6, color=MUTED)
    save(fig, out("10_use_case_diagram.png"))


# ---------------------------------------------------------------- 11 ER diagram
def entity(ax, x, y, w, name, rows, theme="amber", fs=7.6, row=3.4):
    ec, fc = THEMES[theme]
    H = 4.6 + len(rows) * row + 1
    ax.add_patch(Rectangle((x, y - H), w, H, fc=WHITE, ec=ec, lw=1.5, zorder=2))
    ax.add_patch(Rectangle((x, y - 4.6), w, 4.6, fc=fc, ec=ec, lw=1.5, zorder=3))
    ax.text(x + w / 2, y - 2.3, name, ha="center", va="center", fontsize=fs + 1.2, fontweight="bold", color=INK, zorder=4)
    for i, (key, col, typ) in enumerate(rows):
        yy = y - 4.6 - 0.6 - i * row - row / 2
        ax.text(x + 1.2, yy, key, ha="left", va="center", fontsize=fs - 0.8, color=ec, fontweight="bold", zorder=4)
        ax.text(x + 6.2, yy, col, ha="left", va="center", fontsize=fs, color=INK, zorder=4)
        ax.text(x + w - 1.0, yy, typ, ha="right", va="center", fontsize=fs - 0.8, color=MUTED, zorder=4)
    return x, y - H, w, H


def d11():
    fig, ax = canvas(10, 8.0, xlim=(0, 120), ylim=(0, 96))
    title(ax, "Entity-relationship diagram (SQLite, instance/app.db)", y=95.5)
    users = entity(ax, 44, 86, 32, "users", [("PK", "id", "INTEGER"), ("", "username", "TEXT unique"), ("", "password_hash", "TEXT"), ("", "interests", "TEXT"), ("", "created_at", "TEXT")])
    docs = entity(ax, 86, 86, 32, "documents", [("PK", "id", "INTEGER"), ("FK", "user_id", "INTEGER"), ("", "filename", "TEXT"), ("", "filepath", "TEXT"), ("", "subject", "TEXT"), ("", "topics (JSON)", "TEXT"), ("", "uploaded_at", "TEXT")])
    chunks = entity(ax, 86, 46, 32, "chunks", [("PK", "id", "INTEGER"), ("FK", "document_id", "INTEGER"), ("", "chunk_index", "INTEGER"), ("", "text", "TEXT")])
    entity(ax, 2, 86, 32, "queries", [("PK", "id", "INTEGER"), ("FK", "user_id", "INTEGER"), ("", "question", "TEXT"), ("", "answer", "TEXT"), ("", "sources (JSON)", "TEXT"), ("", "created_at", "TEXT")])
    quiz = entity(ax, 44, 52, 32, "quiz_results", [("PK", "id", "INTEGER"), ("FK", "user_id", "INTEGER"), ("", "subject", "TEXT"), ("", "topic", "TEXT"), ("", "correct (0/1)", "INTEGER"), ("", "created_at", "TEXT")])
    arrow(ax, (34, 75), (44, 75), style="-", theme="amber", lw=1.6)
    label(ax, 42.4, 77.0, "1", fs=8, color=INK)
    label(ax, 35.6, 77.0, "N", fs=8, color=INK)
    label(ax, 39, 72.6, "asks", fs=7, color=MUTED)
    arrow(ax, (76, 75), (86, 75), style="-", theme="amber", lw=1.6)
    label(ax, 77.6, 77.0, "1", fs=8, color=INK)
    label(ax, 84.4, 77.0, "N", fs=8, color=INK)
    label(ax, 81, 72.6, "owns", fs=7, color=MUTED)
    ytop_c, ybot_d = 46, docs[1]
    arrow(ax, (102, ybot_d), (102, ytop_c), style="-", theme="amber", lw=1.6)
    label(ax, 104.2, ybot_d - 1.6, "1", fs=8, color=INK)
    label(ax, 104.2, ytop_c + 1.6, "N", fs=8, color=INK)
    label(ax, 108.5, (ybot_d + ytop_c) / 2, "split into", fs=7, color=MUTED, ha="left")
    arrow(ax, (60, users[1]), (60, 52), style="-", theme="amber", lw=1.6)
    label(ax, 62, users[1] - 1.6, "1", fs=8, color=INK)
    label(ax, 62, 53.6, "N", fs=8, color=INK)
    label(ax, 64, (users[1] + 52) / 2, "attempts", fs=7, color=MUTED, ha="left")
    ax.text(60, 20, "All foreign keys use ON DELETE CASCADE and PRAGMA foreign_keys = ON.\nquiz_results stores subject and topic as text (no foreign key to documents), so a roadmap survives deleting a document.\nqueries.sources and documents.topics hold JSON text. Uploaded files are kept on disk under uploads/<user id>/, not in the database.",
            ha="center", va="top", fontsize=7.6, color=MUTED, linespacing=1.5)
    save(fig, out("11_er_diagram.png"))


# ---------------------------------------------------------------- 12 / 13 flowcharts
def fc_arrow(ax, p, q, text=None, theme="grey", **kw):
    arrow(ax, p, q, text, theme=theme, lw=1.4, **kw)


def d12():
    fig, ax = canvas(10, 12.2, xlim=(0, 100), ylim=(0, 122))
    title(ax, "Flowchart of the core algorithm: answering a question", y=121.5)
    cx = 32
    terminator(ax, cx, 114, 26, 5, "Receive question", theme="green", fs=8.5)
    diamond(ax, cx, 103, 26, 9, "Question\nempty?", fs=7.8)
    fc_arrow(ax, (cx, 111.5), (cx, 107.5))
    box(ax, 62, 100.5, 28, 5, "Error 400:\n'Please type a question.'", theme="rose", fs=7.4)
    fc_arrow(ax, (cx + 13, 103), (62, 103), "yes")
    diamond(ax, cx, 90.5, 26, 9, "Index cached\nfor this user?", fs=7.6)
    fc_arrow(ax, (cx, 98.5), (cx, 95), "no")
    box(ax, 60, 87.5, 33, 6, "Read the user's chunks from SQLite,\nfit TF-IDF (1-2 grams, stop words)", theme="cyan", fs=7.2)
    fc_arrow(ax, (cx + 13, 90.5), (60, 90.5), "no")
    box(ax, cx - 17, 74, 34, 6.5, "Vectorise the question; cosine similarity\nwith every chunk", theme="cyan", fs=7.4)
    fc_arrow(ax, (cx, 86), (cx, 80.5), "yes")
    poly_arrow(ax, [(76.5, 87.5), (76.5, 77.2), (cx + 17, 77.2)], theme="cyan")
    box(ax, cx - 17, 63, 34, 6.5, "Sort by score, keep the top 4\nchunks with score above 0", theme="cyan", fs=7.4)
    fc_arrow(ax, (cx, 74), (cx, 69.5))
    diamond(ax, cx, 54, 26, 9, "Any chunk\nretrieved?", fs=7.6)
    fc_arrow(ax, (cx, 63), (cx, 58.5))
    box(ax, 62, 51.2, 31, 5.5, "'No relevant content was found in\nyour uploaded documents ...'", theme="rose", fs=7.2)
    fc_arrow(ax, (cx + 13, 54), (62, 54), "no")
    diamond(ax, cx, 41, 26, 9, "API key\nconfigured?", fs=7.6)
    fc_arrow(ax, (cx, 49.5), (cx, 45.5), "yes")
    box(ax, 60, 37.5, 34, 7, "Send question + chunks to Claude:\n'answer using ONLY the context'", theme="grey", fs=7.2)
    fc_arrow(ax, (cx + 13, 41), (60, 41), "yes")
    diamond(ax, 77, 28, 22, 8, "Call\nsucceeded?", fs=7.4)
    fc_arrow(ax, (77, 37.5), (77, 32))
    box(ax, cx - 17, 13, 34, 12, "Extractive answer: split chunks into sentences\n(over 20 characters), TF-IDF rank them against\nthe question, keep the top 4 with score above 0\n(first 3 sentences if none), join them", theme="cyan", fs=7.0)
    fc_arrow(ax, (cx, 36.5), (cx, 25), "no")
    poly_arrow(ax, [(66, 28), (55, 28), (55, 19), (cx + 17, 19)], "no", theme="grey", tidx=0)
    box(ax, 62, 14, 32, 5.5, "Answer text from Claude", theme="grey", fs=7.4)
    fc_arrow(ax, (77, 24), (77, 19.5), "yes")
    box(ax, cx - 17, 2, 34, 6, "Store question, answer, source file names\n(queries); return answer + sources", theme="amber", fs=7.4)
    fc_arrow(ax, (cx, 13), (cx, 8))
    poly_arrow(ax, [(62, 16.7), (52, 16.7), (52, 5), (cx + 17, 5)], theme="grey")
    save(fig, out("12_flowchart_rag.png"))


def d13():
    fig, ax = canvas(10, 8.6, xlim=(0, 118), ylim=(0, 92))
    title(ax, "Flowcharts: quiz generation and roadmap priority", y=91.5)
    ax.text(26, 87, "A. Generate a quiz from one document", ha="center", fontsize=8.8, color=VIOLET, fontweight="bold")
    ax.text(88, 87, "B. Build the roadmap", ha="center", fontsize=8.8, color=AMBER, fontweight="bold")
    cx = 26
    terminator(ax, cx, 82, 28, 4.6, "Chunks of the document", theme="green", fs=8)
    box(ax, cx - 18, 70, 36, 7, "Rank terms by TF-IDF (words of 4+ letters);\nkeep the top 40", theme="cyan", fs=7.3)
    fc_arrow(ax, (cx, 79.7), (cx, 77))
    diamond(ax, cx, 60, 28, 9, "At least 4\nterms?", fs=7.6)
    fc_arrow(ax, (cx, 70), (cx, 64.5))
    box(ax, 45, 57.5, 17, 5, "return [ ]\n(HTTP 422)", theme="rose", fs=7.2)
    fc_arrow(ax, (cx + 14, 60), (45, 60), "no")
    box(ax, cx - 18, 45, 36, 7, "Take sentences of 26 to 219 characters,\nshuffle them", theme="cyan", fs=7.3)
    fc_arrow(ax, (cx, 55.5), (cx, 52), "yes")
    diamond(ax, cx, 36, 30, 9.5, "Sentence has an\nunused term?\n(whole word)", fs=7.2)
    fc_arrow(ax, (cx, 45), (cx, 40.8))
    box(ax, cx - 18, 20.5, 36, 9.5, "Blank its first occurrence; options = the term +\n3 random other terms, shuffled;\nremember the answer index and topic", theme="cyan", fs=7.1)
    fc_arrow(ax, (cx, 31.2), (cx, 30), "yes")
    diamond(ax, cx, 11, 28, 8.5, "5 questions or\nno sentences left?", fs=6.9)
    fc_arrow(ax, (cx, 20.5), (cx, 15.3))
    poly_arrow(ax, [(cx - 15, 36), (4, 36), (4, 48.5), (cx - 18, 48.5)], "no: next sentence", theme="grey", tidx=0, toff=(2, 1.5), fs=6.8)
    poly_arrow(ax, [(cx + 14, 11), (47, 11), (47, 36), (cx + 15, 36)], "no", theme="grey", tidx=0, toff=(0, 1.5))
    terminator(ax, cx, 2.5, 24, 4, "Return questions", theme="green", fs=7.8)
    fc_arrow(ax, (cx, 6.7), (cx, 4.5), "yes")
    cx2 = 82
    terminator(ax, cx2, 82, 30, 4.6, "quiz_results of the user", theme="green", fs=8)
    box(ax, cx2 - 19, 70, 38, 7, "Group rows by topic: attempts = rows,\ncorrect = sum of the 0/1 flags", theme="cyan", fs=7.3)
    fc_arrow(ax, (cx2, 79.7), (cx2, 77))
    box(ax, cx2 - 19, 58, 38, 7, "accuracy = 100 x correct / attempts", theme="cyan", fs=7.6)
    fc_arrow(ax, (cx2, 70), (cx2, 65))
    diamond(ax, cx2, 45, 28, 9, "accuracy\nbelow 50?", fs=7.6)
    fc_arrow(ax, (cx2, 58), (cx2, 49.5))
    box(ax, 101, 41.5, 14, 7, "High", theme="rose", bold=True, color=ROSE, fs=8)
    fc_arrow(ax, (cx2 + 14, 45), (101, 45), "yes", tpos=0.5, toff=(0, 1.6), bg="none")
    diamond(ax, cx2, 29, 28, 9, "accuracy\nbelow 80?", fs=7.6)
    fc_arrow(ax, (cx2, 40.5), (cx2, 33.5), "no")
    box(ax, 101, 25.5, 14, 7, "Medium", theme="amber", bold=True, color=AMBER, fs=8)
    fc_arrow(ax, (cx2 + 14, 29), (101, 29), "yes", tpos=0.5, toff=(0, 1.6), bg="none")
    box(ax, cx2 - 11, 11, 22, 7, "Low", theme="green", bold=True, color=GREEN, fs=8)
    fc_arrow(ax, (cx2, 24.5), (cx2, 18), "no")
    box(ax, cx2 - 19, 1.5, 38, 6, "Sort by priority (High, Medium, Low),\nthen by accuracy ascending", theme="amber", fs=7.3)
    fc_arrow(ax, (cx2, 11), (cx2, 7.5))
    save(fig, out("13_flowchart_quiz_roadmap.png"))


if __name__ == "__main__":
    import sys as _sys
    only = set(_sys.argv[1:])
    for f in (d01, d02, d03, d04, d05, d06, d07, d08, d09, d10, d11, d12, d13):
        if not only or f.__name__ in only:
            f()
