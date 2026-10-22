"""Draw the SymptoTrackAI (CareLens AI) design diagrams, first half, into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: app/main.py and app/routes/* (API), app/models.py (tables), app/rag/* (pipeline),
app/rag/safety.py (rules) and frontend/src (React pages).
    .venv\\Scripts\\python scripts\\docs_build\\make_diagrams.py     (also draws the second half)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------------------------------
def system_architecture():
    fig, ax = canvas(10, 9.0, 100, 90)
    panel(ax, 2, 71, 96, 18, "Presentation tier - React 19 + Vite 8 single-page app (port 5412)", PALE_BLUE, BLUE)
    box(ax, 16, 77, 25, 10.5, "Pages\nLanding - Login - Register\nAssistant - History\nConsultation detail - About", BLUE, fs=7.4)
    box(ax, 41.5, 77, 22, 10.5, "lib/api.js, lib/auth.jsx\nfetch wrapper over /api\n(Vite proxies /api to 8412)", BLUE, fs=7.4)
    box(ax, 65.5, 77, 23, 10.5, "UI kit V2 'Neo Brutal Grid'\nRecharts - Framer Motion\nGSAP - theme toggle", BLUE, fs=7.4)
    box(ax, 87.5, 77, 20, 10.5, "Legacy Jinja pages\napp/templates + static\nserved by the API at /", GREY, fs=7.4)

    panel(ax, 2, 51, 96, 18, "Application tier - FastAPI + Uvicorn (port 8412, app/main.py)", PALE_TEAL, TEAL)
    box(ax, 14, 57, 22, 10.5, "auth router\nPOST register, login,\nlogout - GET me\nbcrypt + JWT cookie", TEAL, fs=7.2)
    box(ax, 38, 57, 22, 10.5, "chat router\nPOST /api/chat\nrequire_user, 3-2000\ncharacters, save result", TEAL, fs=7.2)
    box(ax, 62, 57, 22, 10.5, "history router\nGET list + ?search=\nGET / DELETE {id}\nowner-only (404 else)", TEAL, fs=7.2)
    box(ax, 85, 57, 22, 10.5, "about + health + pages\nGET /api/about/metrics\nGET /api/health\nGET /, /login ...", TEAL, fs=7.2)

    panel(ax, 2, 24, 96, 25, "RAG tier - app/rag (Pipeline singleton, built lazily on the first chat request)", PALE_ORANGE, ORANGE)
    r1 = [("query_expansion", "normalise +\nHyDE-style template"), ("embeddings", "MiniLM-L6-v2,\nTF-IDF fallback"), ("faiss_store", "IndexFlatIP\n384-d, top 15"),
          ("bm25_store", "BM25Okapi\ntop 15")]
    r2 = [("hybrid_retriever", "min-max fusion\n0.65 / 0.35"), ("reranker", "cross-encoder\nms-marco MiniLM"), ("generator", "Flan-T5-small or\nevidence fallback"),
          ("safety", "10 emergency rules,\nanswer filter")]
    for i, (n, d) in enumerate(r1):
        box(ax, 14 + i * 24, 40.5, 21, 8.8, f"{n}\n{d}", ORANGE, fs=6.9)
    for i, (n, d) in enumerate(r2):
        box(ax, 14 + i * 24, 29.2, 21, 8.8, f"{n}\n{d}", ORANGE, fs=6.9)

    panel(ax, 2, 1.5, 96, 20, "Data tier - everything stays on the machine (models are downloaded once from the Hugging Face Hub)", LIGHT, "#B7C3D3")
    store(ax, 15, 9, 24, 9.5, "SQLite data/carelens.db\nusers - consultations", fs=7.0)
    store(ax, 41, 9, 24, 9.5, "data/processed/\nknowledge_base.json + csv\n176 records, 30 conditions", fs=6.8)
    store(ax, 67, 9, 24, 9.5, "data/index/\nfaiss.index, bm25.json,\nrecords.json", fs=6.9)
    store(ax, 90, 9, 15, 9.5, "results/\nmetrics.json\nHF model cache", fs=6.6)

    arrow(ax, (50, 71), (50, 69), "HTTP + JSON, httponly cookie", lo=(22, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 51), (50, 49), "Python calls", lo=(9, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 24), (50, 21.5), "read / write", lo=(7, 0), fs=7.2, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 6.4, 100, 64)
    ax.text(50, 61.2, "One consultation, end to end (POST /api/chat)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    top = [("Sign in", "demo or own\naccount (cookie)", BLUE), ("Describe\nsymptoms", "free text,\n3-2000 chars", BLUE), ("Normalise and\nexpand", "lower-case, split,\nHyDE-style template", TEAL),
           ("Dual retrieval", "FAISS semantic +\nBM25 lexical, 15 each", TEAL), ("Fuse and\nrerank", "0.65 / 0.35, then\ncross-encoder, top 5", TEAL)]
    xs = [10 + i * 20 for i in range(5)]
    for x, (t, d, c) in zip(xs, top):
        box(ax, x, 46, 17, 13.5, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.7, 46), (b - 8.7, 46), color=NAVY)
    bot = [("Safety check", "10 emergency rules,\n6 caution keywords", ORANGE), ("Grounded\nanswer", "Flan-T5-small, else\nevidence-based text", ORANGE),
           ("Answer filter", "banned medication\nphrases replaced", ORANGE), ("Save", "consultation row\nin SQLite", PURPLE), ("Show", "answer, banner,\nevidence cards", PURPLE)]
    for x, (t, d, c) in zip(xs, bot):
        box(ax, x, 18, 17, 13.5, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.7, 18), (b - 8.7, 18), color=NAVY)
    ax.plot([xs[-1], xs[-1]], [39, 34], color=NAVY, lw=1.5)
    ax.plot([xs[-1], xs[0]], [34, 34], color=NAVY, lw=1.5)
    arrow(ax, (xs[0], 34), (xs[0], 24.8), color=NAVY)
    ax.text(50, 36.2, "top 5 records (condition, symptoms, guidance, severity, red flags) + relevance", ha="center", fontsize=7.4, color=INK)
    ax.text(50, 4.5, "Degradation paths: no embedding model -> TF-IDF vectors;  no reranker -> hybrid order;  no generator -> deterministic evidence-based answer.\n"
                     "History page: search, open, delete (owner only).", ha="center", fontsize=7.6, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(9, 5.6, 100, 62)
    circle(ax, 50, 31, 13, "0\nSymptoTrackAI\n(CareLens AI)", BLUE, fs=9.5)
    box(ax, 11, 31, 18, 9, "User\n(patient / visitor)", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    box(ax, 90, 31, 18, 10, "Hugging Face Hub\n(first run only)", WHITE, tc=INK, ec=NAVY, fs=9, bold=True)
    arrow(ax, (20, 36), (38.5, 35), "registration, credentials,\nsymptom text, search,\ndelete request", lo=(-1, 7.5), fs=7.8)
    arrow(ax, (38.5, 27), (20, 26), "answer, evidence cards,\nsafety banner, history,\nmetrics page", lo=(-1, -7.5), fs=7.8)
    arrow(ax, (63, 34), (81, 34), "model download\nrequest", lo=(0, 4.2), fs=7.8)
    arrow(ax, (81, 28), (63, 28), "embedding, reranker and\ngenerator weights", lo=(0, -4.4), fs=7.6)
    ax.text(50, 8.0, "knowledge base, indexes and evaluation metrics are read from local files; accounts and consultations are kept in local SQLite",
            ha="center", fontsize=7.6, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


# --------------------------------------------------------------------------------------------------
def er_diagram():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.text(50, 71.5, "Two SQLite tables (one-to-many) and the file-based knowledge base", ha="center", fontsize=10, color=NAVY, fontweight="bold")

    def entity(x, ytop, w, title, rows, fc=NAVY, fs=6.6, lh=2.75):
        h = 4.4 + lh * len(rows) + 1.0
        ax.add_patch(Rectangle((x, ytop - h), w, h, fc=WHITE, ec=NAVY, lw=1.4, zorder=2))
        ax.add_patch(Rectangle((x, ytop - 4.4), w, 4.4, fc=fc, ec=NAVY, lw=1.4, zorder=3))
        ax.text(x + w / 2, ytop - 2.2, title, ha="center", va="center", color=WHITE, fontsize=9.2, fontweight="bold", zorder=4)
        for i, r in enumerate(rows):
            ax.text(x + 1.0, ytop - 4.4 - 1.9 - lh * i, r, ha="left", va="center", fontsize=fs, zorder=4, family="DejaVu Sans Mono")
        return h

    def fmt(pairs, w=24):
        return [(n).ljust(w) + t for n, t in pairs]

    entity(3, 66, 36, "users", fmt([("PK id", "Integer (index)"), ("email", "String(255) UNIQUE"), ("password_hash", "String(255) bcrypt"), ("created_at", "DateTime (UTC now)")]), BLUE)
    entity(53, 66, 44, "consultations", fmt([("PK id", "Integer (index)"), ("FK user_id", "-> users.id, NOT NULL"), ("symptom_query", "Text NOT NULL"), ("generated_response", "Text NOT NULL"),
                                              ("top_condition", "String(255)"), ("retrieved_evidence", "Text (JSON list of 5)"), ("retrieval_score", "Float"),
                                              ("safety_flag", "String(50) routine|caution|emergency"), ("created_at", "DateTime (UTC now)")], 20), TEAL, fs=6.2)
    arrow(ax, (39, 55), (53, 55), None, style="-", color=ORANGE, lw=1.8)
    ax.text(46, 58.2, "1", ha="center", fontsize=10, color=ORANGE, fontweight="bold")
    ax.text(50.5, 56.8, "*", ha="center", fontsize=12, color=ORANGE, fontweight="bold")
    ax.text(46, 51.4, "has many\n(cascade\ndelete-orphan)", ha="center", va="top", fontsize=6.8, color=INK)

    store(ax, 18, 11.5, 31, 12.5, "data/processed/knowledge_base.json\nrecord_id, disease, symptoms,\ndescription, guidance, severity,\nred_flags, source, source_type,\nretrieval_text   (176 records)", fs=6.5)
    store(ax, 51.5, 11.5, 29, 12.5, "data/index/\nfaiss.index (IndexFlatIP, 384-d)\nrecords.json (record metadata)\nbm25.json (tokenised corpus)", fs=6.8)
    store(ax, 85, 11.5, 24, 12.5, "results/metrics.json\n(scripts/evaluate.py,\nserved by\nGET /api/about/metrics)", fs=6.8)
    arrow(ax, (33.5, 11.5), (37, 11.5), None, color=GREY, lw=1.2)
    ax.text(50, 22, "File artefacts written by scripts/prepare_data.py, build_index.py and evaluate.py; read by app/rag/pipeline.py and app/routes/about.py", ha="center", fontsize=7.2, color=NAVY)
    ax.text(50, 3.0, "No foreign key links consultations to the knowledge base: retrieved_evidence stores a JSON copy of the five matched records.", ha="center", fontsize=7.2, color=GREY, style="italic")
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------------------------------------------
def safety_flow():
    fig, ax = canvas(10, 10.6, 100, 106)
    ax.text(50, 103, "Safety decision flow (app/rag/safety.py + Pipeline.answer)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    cx = 36
    box(ax, cx, 95, 44, 6, "raw user query (lower-cased)", BLUE, fs=8)
    diamond(ax, cx, 82, 46, 13, "any of the 10 emergency\nregex rules matches?", fs=7.8)
    arrow(ax, (cx, 92), (cx, 88.5), color=NAVY)
    box(ax, 80, 82, 28, 11, "flag = emergency\nmessage = rule advice\n+ 'seek urgent care'\n+ disclaimer", ORANGE, fs=7.2)
    arrow(ax, (cx + 23, 82), (66, 82), "yes", lo=(0, 1.8), fs=8, color=NAVY)
    diamond(ax, cx, 64, 46, 13, "contains a caution keyword?\n(chest pain, breathing, bleeding,\npregnant, infant, newborn)", fs=7.0)
    arrow(ax, (cx, 75.5), (cx, 70.5), "no", lo=(2.5, 0), fs=8, color=NAVY)
    box(ax, 80, 64, 28, 9, "flag = caution\nmessage = 'consider\ncontacting a professional'", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.2)
    arrow(ax, (cx + 23, 64), (66, 64), "yes", lo=(0, 1.8), fs=8, color=NAVY)
    box(ax, cx, 48, 36, 7, "flag = routine, message = disclaimer", PALE_TEAL, tc=INK, ec=TEAL, fs=7.6)
    arrow(ax, (cx, 57.5), (cx, 51.5), "no", lo=(2.5, 0), fs=8, color=NAVY)
    box(ax, cx, 34, 44, 7.5, "generator answer (Flan-T5 or evidence fallback)\nbuilt independently from the retrieved records", BLUE, fs=7.2)
    arrow(ax, (cx, 44.5), (cx, 37.8), color=NAVY)
    box(ax, cx, 20.5, 44, 8.5, "apply_safety_filter: replace 5 banned phrases\n('take ibuprofen', 'take antibiotics', 'dosage',\n'prescribe', 'mg twice daily') with a removal note", ORANGE, fs=7.0)
    arrow(ax, (cx, 30.2), (cx, 24.8), color=NAVY)
    diamond(ax, cx, 7.5, 36, 10, "flag = emergency?", fs=7.8)
    arrow(ax, (cx, 16.2), (cx, 12.5), color=NAVY)
    box(ax, 80, 7.5, 28, 9, "prepend the emergency\nmessage to the answer\n(UI also shows a banner)", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.0)
    arrow(ax, (cx + 18, 7.5), (66, 7.5), "yes", lo=(0, 1.8), fs=8, color=NAVY)
    ax.text(66, 41, "the resulting flag (emergency, caution\nor routine) and its message are carried\nforward, returned with the answer and\nstored in consultations.safety_flag", fontsize=6.8, color=GREY, style="italic", ha="left", va="center")
    ax.text(cx, -0.5, "no: the answer is returned unchanged with the disclaimer", ha="center", fontsize=6.8, color=GREY)
    save(fig, OUT / "11_safety_decision_flow.png")


if __name__ == "__main__":
    system_architecture()
    high_level_workflow()
    dfd0()
    er_diagram()
    safety_flow()
    from diagrams_more import all_more

    all_more()
