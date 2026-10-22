"""DFD level 1, DFD level 2 and the UML class diagram of SymptoTrackAI (drawn with dgm_lib)."""

from __future__ import annotations

from pathlib import Path

from dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def route(ax, pts, label=None, lpos=None, color=GREY, fs=7.0, ls="-", lw=1.5):
    """Poly-line with an arrow head on the last segment; optional label at lpos."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    if len(pts) > 2:
        ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, ls=ls, zorder=4, solid_capstyle="butt")
    arrow(ax, pts[-2], pts[-1], None, color=color, lw=lw, ls=ls)
    if label:
        ax.text(lpos[0], lpos[1], label, fontsize=fs, ha="center", va="center", color=INK, zorder=6, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def dfd1():
    fig, ax = canvas(10, 10, 100, 100)
    R = 7.4
    ax.text(50, 98.6, "Process 1.0 guards 2.0, 4.0 and 5.0 (require_user); model downloads are shown at level 0", ha="center", fontsize=7.2, color=GREY, style="italic")
    box(ax, 9, 52, 14, 9, "User", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    circle(ax, 40, 80, R, "2.0\nRetrieve\nevidence", BLUE, fs=7.6)
    circle(ax, 68, 80, R, "3.0\nGenerate and\nscreen answer", BLUE, fs=6.8)
    circle(ax, 40, 52, R, "5.0\nManage\nhistory", BLUE, fs=7.6)
    circle(ax, 68, 52, R, "4.0\nStore\nconsultation", BLUE, fs=7.2)
    circle(ax, 40, 23, R, "1.0\nAuthenticate\nuser", BLUE, fs=7.0)
    circle(ax, 74, 23, R, "6.0\nReport\nmetrics", BLUE, fs=7.6)
    circle(ax, 90, 66, 6.2, "7.0\nBuild KB\nand index", BLUE, fs=6.4)
    store(ax, 46, 66, 22, 5.0, "D2  knowledge base + indexes", fs=6.6)
    store(ax, 40, 8, 22, 5.2, "D1  users table", fs=7.4)
    store(ax, 54, 38, 24, 5.2, "D3  consultations table", fs=7.2)
    store(ax, 94, 23, 11, 8.5, "D4\nmetrics\n.json", fs=6.6)

    route(ax, [(14, 56.8), (33.5, 76.4)], "symptom text", (18.5, 71.5))
    route(ax, [(63, 85.3), (63, 91), (4, 91), (4, 56.8)], "answer, safety flag, evidence cards", (33, 91), color=BLUE)
    route(ax, [(47.4, 80), (60.6, 80)], "top-5 records", (54, 83.3))
    route(ax, [(42, 72.6), (42, 68.6)], None, None)
    route(ax, [(45, 68.6), (45, 72.6)], None, None, color=BLUE)
    ax.text(34, 70.6, "query,\nrecords", fontsize=6.6, ha="center", va="center")
    route(ax, [(68, 72.6), (68, 59.4)], "result", (71.5, 73.5))
    route(ax, [(16, 50), (32.6, 50)], "search, delete,\nhistory, detail", (24, 46.2))
    route(ax, [(32.6, 54.4), (16, 54.4)], None, None, color=BLUE)
    ax.text(24, 57.6, "history rows", fontsize=7.0, ha="center", color=BLUE)
    route(ax, [(64, 58.4), (60, 40.8)], None, None)
    ax.text(54.5, 48.0, "new row", fontsize=6.8, ha="center")
    route(ax, [(44.5, 45.6), (49, 40.8)], None, None)
    route(ax, [(50, 40.8), (46.6, 45.8)], None, None, color=BLUE)
    ax.text(40.5, 41.0, "rows,\ndeletes", fontsize=6.6, ha="center", va="center")
    route(ax, [(11, 47.5), (11, 23), (32.6, 23)], "credentials", (21, 25.2))
    route(ax, [(32.6, 19.6), (7.5, 19.6), (7.5, 47.5)], "session cookie", (20, 17.2), color=BLUE)
    route(ax, [(38, 15.6), (38, 10.8)], None, None)
    route(ax, [(42, 10.8), (42, 15.6)], None, None, color=BLUE)
    ax.text(45.5, 13.2, "user rows", fontsize=6.6, ha="left")
    route(ax, [(36, 30.4), (36, 44.6)], "user id of the valid session", (26.5, 36.5), ls="--")
    route(ax, [(14.5, 47.5), (14.5, 2.2), (69.5, 2.2), (69.5, 16.9)], "metrics request, metrics page", (40, 2.2))
    route(ax, [(81.4, 23), (88.4, 23)], "metrics", (85, 27.8))
    route(ax, [(83.8, 66), (57.2, 66)], "KB, FAISS, BM25 files", (78, 62.6))
    ax.text(90, 58, "offline scripts:\nprepare_data,\nbuild_index", fontsize=6.6, ha="center", va="top", color=GREY)
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 6.8, 100, 68)
    R = 6.3
    ax.text(50, 65, "Level 2 - expansion of processes 2.0 and 3.0 (Pipeline.answer)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    circle(ax, 11, 47, R, "2.1\nNormalise and\nexpand", BLUE, fs=6.6)
    circle(ax, 31, 47, R, "2.2\nEmbed\nquery", BLUE, fs=6.7)
    circle(ax, 51, 47, R, "2.3\nSemantic\nsearch", BLUE, fs=6.7)
    circle(ax, 89, 47, R, "2.5\nFuse\n(0.65 / 0.35)", BLUE, fs=6.5)
    circle(ax, 68, 28, R, "2.4\nLexical\nsearch", BLUE, fs=6.7)
    route(ax, [(11 + R, 47), (31 - R, 47)], "combined\ntext", (21, 52.5), fs=6.7)
    route(ax, [(31 + R, 47), (51 - R, 47)], "query\nvector", (41, 52.5), fs=6.7)
    route(ax, [(51 + R, 47), (89 - R, 47)], "15 semantic hits", (70, 50), fs=6.7)
    route(ax, [(11, 40.6), (11, 21), (68, 21), (68, 21.6)], "combined text (BM25 query)", (39, 21), fs=6.7)
    route(ax, [(68 + R - 0.8, 31.5), (89 - 4.5, 41.8)], "15 lexical hits", (84, 34.0), fs=6.7)
    store(ax, 27, 29, 26, 4.8, "D2  BM25 index", fs=7.0)
    route(ax, [(40.2, 28.5), (61.7, 28.5)], "tokens", (51, 31.2), fs=6.7)
    store(ax, 51, 62, 28, 4.6, "D2  FAISS index", fs=7.0)
    route(ax, [(51, 59.7), (51, 53.4)], "vectors", (55.5, 56.5), fs=6.7)
    circle(ax, 89, 12, R, "2.6\nCross-encoder\nrerank", BLUE, fs=6.2)
    route(ax, [(89, 40.6), (89, 18.4)], "15 fused\ncandidates", (94.5, 30), fs=6.7)
    circle(ax, 68, 8, R, "3.1\nGrounded\nanswer", BLUE, fs=6.7)
    route(ax, [(89 - R, 11), (68 + R, 9)], "top 5 records\n+ relevance", (78.5, 15.0), fs=6.7)
    circle(ax, 46, 8, R, "3.2\nSafety check\nand filter", BLUE, fs=6.3)
    route(ax, [(68 - R, 8), (46 + R, 8)], "answer", (57, 11.5), fs=6.7)
    box(ax, 17, 8, 22, 8, "to 4.0\nresult dict", NAVY, fs=7.6)
    route(ax, [(46 - R, 8), (28, 8)], "answer,\nflag, message", (37, 12.5), fs=6.7)
    ax.text(4, 59, "model cache: MiniLM (2.2),\ncross-encoder (2.6),\nFlan-T5-small or fallback (3.1)", fontsize=6.6, ha="left", va="center", color=GREY, style="italic")
    ax.text(4, 2.5, "raw query goes to 3.2 for the safety rules; 3.1 uses the normalised query", fontsize=6.6, ha="left", color=GREY, style="italic")
    save(fig, OUT / "05_dfd_level2.png")


def class_diagram():
    fig, ax = canvas(10, 12.0, 100, 120)
    W = 21.5
    cx = [2, 27, 52, 77]
    fs = 6.5

    def rel(p1, p2, label=None, ls="-", lo=(0, 1.2), style="-|>"):
        arrow(ax, p1, p2, label, color=NAVY, lw=1.2, style=style, ls=ls, fs=6.8, lo=lo)

    yA, yB, yC, yD = 112, 72, 44, 17
    a = uml_class(ax, cx[0], yA, W, "API routers", [], ["register(payload)", "login(payload)", "logout()", "me()", "require_user(request)", "chat(payload, user)", "list_history(search)", "get_one(cid)", "delete_one(cid)", "metrics()  /api/about"], hdr=TEAL, fs=fs, stereotype="routes/*.py")
    uml_class(ax, cx[1], yA, W, "User", ["id: int  <<PK>>", "email: str  <<unique>>", "password_hash: str", "created_at: datetime"], [], hdr=BLUE, fs=fs, stereotype="ORM users")
    uml_class(ax, cx[2], yA, W, "Consultation", ["id: int  <<PK>>", "user_id: int  <<FK>>", "symptom_query: text", "generated_response: text", "top_condition: str", "retrieved_evidence: text", "retrieval_score: float", "safety_flag: str", "created_at: datetime"], [], hdr=BLUE, fs=fs, stereotype="ORM consultations")
    uml_class(ax, cx[3], yA, W, "Pydantic schemas", ["RegisterRequest:", "  email, password", "LoginRequest:", "  email, password", "ChatRequest:", "  query (3-2000)", "ChatResponse,", "EvidenceItem"], [], hdr=GREY, fs=fs, stereotype="schemas.py")

    e = uml_class(ax, cx[0], yB, W, "Pipeline", ["embeddings, faiss, bm25", "reranker, generator", "ready: bool"], ["_ensure_index()", "rebuild()", "answer(raw_query, top_k)", "get_pipeline()  singleton"], hdr=ORANGE, fs=fs, stereotype="rag/pipeline.py")
    uml_class(ax, cx[1], yB, W, "EmbeddingBackend", ["model_name, mode, dim=384", "model: SentenceTransformer", "vectorizer: TF-IDF"], ["_load()", "fit_fallback(texts)", "encode(texts)"], hdr=ORANGE, fs=fs, stereotype="rag/embeddings.py")
    uml_class(ax, cx[2], yB, W, "FaissStore", ["index: IndexFlatIP", "records: list[dict]"], ["build(vectors, records)", "save()", "load()", "search(query_vec, k)"], hdr=ORANGE, fs=fs, stereotype="rag/faiss_store.py")
    uml_class(ax, cx[3], yB, W, "BM25Store", ["bm25: BM25Okapi", "corpus_tokens", "records"], ["build(records)", "save()", "load()", "search(query, k)"], hdr=ORANGE, fs=fs, stereotype="rag/bm25_store.py")

    uml_class(ax, cx[0], yC, W, "Reranker", ["model: CrossEncoder", "available: bool"], ["_load()", "rerank(query, cands, top_k)", "  relevance = min-max"], hdr=PURPLE, fs=fs, stereotype="rag/reranker.py")
    uml_class(ax, cx[1], yC, W, "Generator", ["pipe: text-generation", "available: bool"], ["_load()", "_prompt(query, evidence)", "fallback_answer(...)", "generate(query, evidence)"], hdr=PURPLE, fs=fs, stereotype="rag/generator.py")
    uml_class(ax, cx[2], yC, W, "Settings", ["EMBEDDING_MODEL", "RERANKER_MODEL", "GENERATOR_MODEL", "RETRIEVAL_TOP_K = 5", "CANDIDATE_K = 15", "HYBRID_SEMANTIC = 0.65", "HYBRID_LEXICAL = 0.35", "SECRET_KEY, TOKEN_MIN"], [], hdr=GREY, fs=fs, stereotype="config.py")
    uml_class(ax, cx[3], yC, W, "auth (module)", [], ["hash_password(pw)", "verify_password(pw, h)", "create_token(id, email)", "decode_token(token)"], hdr=GREY, fs=fs, stereotype="auth.py")

    uml_class(ax, cx[0], yD, W, "safety (module)", ["EMERGENCY_PATTERNS (10)"], ["check_safety(query)", "apply_safety_filter(answer)"], hdr=ORANGE, fs=fs, stereotype="rag/safety.py")
    uml_class(ax, cx[1], yD, W, "query_expansion", [], ["normalize_query(text)", "expand_query_hyde(raw)"], hdr=ORANGE, fs=fs, stereotype="rag/query_expansion.py")
    uml_class(ax, cx[2], yD, W, "hybrid_retriever", [], ["_minmax(values)", "fuse(sem, lex, w_sem,", "     w_lex, k)"], hdr=ORANGE, fs=fs, stereotype="rag/hybrid_retriever.py")

    # users 1 - * consultations
    ax.plot([cx[1] + W, cx[2]], [yA - 7, yA - 7], color=NAVY, lw=1.4)
    ax.text(cx[1] + W + 0.4, yA - 5.3, "1", fontsize=8, color=NAVY, fontweight="bold")
    ax.text(cx[2] - 1.6, yA - 5.3, "*", fontsize=9, color=NAVY, fontweight="bold")
    # routers -> user, consultation, schemas (bus above the row)
    top = yA + 4.0
    ax.plot([cx[0] + 12, cx[0] + 12], [yA, top], color=NAVY, lw=1.2)
    ax.plot([cx[0] + 12, cx[3] + 10], [top, top], color=NAVY, lw=1.2)
    for x, ls in ((cx[1] + 11, "-"), (cx[2] + 11, "-"), (cx[3] + 10, "--")):
        arrow(ax, (x, top), (x, yA), None, color=NAVY, lw=1.2, ls=ls)
    ax.text(cx[1] + 12, top + 1.0, "SQLAlchemy queries and request validation", fontsize=6.8, color=INK)
    # routers -> pipeline
    rel((cx[0] + 5, yA - a[3]), (cx[0] + 5, yB), "get_pipeline().answer()", lo=(10.5, 0))
    # pipeline -> embeddings, faiss, bm25 (bus above row B)
    topb = yB + 3.0
    ax.plot([cx[0] + 16, cx[0] + 16], [yB, topb], color=NAVY, lw=1.2)
    ax.plot([cx[0] + 16, cx[3] + 11], [topb, topb], color=NAVY, lw=1.2)
    for x in (cx[1] + 11, cx[2] + 11, cx[3] + 11):
        arrow(ax, (x, topb), (x, yB), None, color=NAVY, lw=1.2)
    ax.text(cx[1] + 3, topb + 1.0, "has (one instance each)", fontsize=6.8, color=INK)
    # pipeline -> reranker, generator (below)
    yb = yB - e[3]
    rel((cx[0] + 5, yb), (cx[0] + 5, yC), "has", lo=(2.2, 0))
    ax.plot([cx[0] + 16, cx[0] + 16, cx[1] + 11], [yb, yb - 3.2, yb - 3.2], color=NAVY, lw=1.2)
    arrow(ax, (cx[1] + 11, yb - 3.2), (cx[1] + 11, yC), None, color=NAVY, lw=1.2)
    # notes
    ax.text(cx[3] - 0.5, 14.5, "Pipeline.answer() calls the", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[3] - 0.5, 11.7, "three modules on the left and", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[3] - 0.5, 8.9, "reads Settings; the routers use", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[3] - 0.5, 6.1, "the auth module. Solid: owns", fontsize=6.8, color=GREY, ha="left")
    ax.text(cx[3] - 0.5, 3.3, "or calls; dashed: validates.", fontsize=6.8, color=GREY, ha="left")
    save(fig, OUT / "06_uml_class.png")
