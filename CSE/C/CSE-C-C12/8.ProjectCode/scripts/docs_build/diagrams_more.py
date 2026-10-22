"""Second half of the SymptoTrackAI diagram set (DFD 1/2, UML class, sequence, use case, retrieval flowchart)."""

from __future__ import annotations

import math
from pathlib import Path

from dgm_lib import *  # noqa: F401,F403
from diagrams_dfd_uml import class_diagram, dfd1, dfd2  # noqa: F401

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def duo(ax, p1, p2, l1=None, l2=None, off=1.2, fs=7.0, lo1=None, lo2=None):
    """Two parallel arrows between p1 and p2 (p1->p2 labelled l1, p2->p1 labelled l2)."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * off, dx / n * off
    a1, b1 = (p1[0] + ox, p1[1] + oy), (p2[0] + ox, p2[1] + oy)
    a2, b2 = (p2[0] - ox, p2[1] - oy), (p1[0] - ox, p1[1] - oy)
    arrow(ax, a1, b1, l1, fs=fs, lo=lo1 if lo1 is not None else (ox * 4.5, oy * 4.5))
    arrow(ax, a2, b2, l2, fs=fs, color=BLUE, lo=lo2 if lo2 is not None else (-ox * 4.5, -oy * 4.5))


def sequence_diagram():
    fig, ax = canvas(10, 13.4, 100, 134)
    names = ["Browser\n(React)", "chat\nrouter", "auth\nrequire_user", "Pipeline", "Embedding\n+ FAISS\n+ BM25", "Reranker", "Generator", "safety", "SQLite"]
    xs = [5.5, 16.5, 27.5, 39, 50.5, 62.5, 74, 85, 95]
    top = 129
    for x, n in zip(xs, names):
        box(ax, x, top, 9.2, 7.6, n, NAVY, fs=6.4, bold=True)
        ax.plot([x, x], [top - 3.8, 1], color="#9AA7B8", lw=1.0, ls="--", zorder=1)
    y = [top - 10]

    def msg(i, j, text, ret=False, gap=4.7, left=None):
        arrow(ax, (xs[i], y[0]), (xs[j], y[0]), None, color=(GREY if ret else BLUE), ls="--" if ret else "-", lw=1.3)
        lo, hi = sorted((xs[i], xs[j]))
        ax.text(left if left is not None else (lo + hi) / 2, y[0] + 0.9, text, ha="left" if left is not None else "center", fontsize=6.7, va="bottom", color=INK,
                bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.9))
        y[0] -= gap

    def self_call(i, text, gap=5.6, side=None):
        yy = y[0]
        sgn = side if side else (-1 if xs[i] > 60 else 1)
        ax.plot([xs[i], xs[i] + sgn * 2.6, xs[i] + sgn * 2.6, xs[i]], [yy + 0.8, yy + 0.8, yy - 2.0, yy - 2.0], color=BLUE, lw=1.2, zorder=4)
        arrow(ax, (xs[i] + sgn * 2.6, yy - 2.0), (xs[i], yy - 2.0), None, color=BLUE, lw=1.2)
        ax.text(xs[i] + sgn * 3.6, yy - 0.6, text, fontsize=6.7, ha="left" if sgn > 0 else "right", va="center", color=INK, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.9))
        y[0] -= gap

    msg(0, 1, "1  POST /api/chat  {query}   (httponly cookie)", gap=5.0, left=7.0)
    msg(1, 2, "2  Depends(require_user)")
    msg(2, 8, "3  decode JWT; SELECT user", gap=4.7)
    msg(8, 2, "4  user row (else 401)", ret=True)
    msg(2, 1, "5  user", ret=True)
    self_call(1, "6  strip; 3-2000 characters (else 400/422)")
    msg(1, 3, "7  get_pipeline().answer(query)")
    self_call(3, "8  expand_query_hyde -> normalised + combined text")
    msg(3, 4, "9  encode(combined)")
    self_call(4, "10  FAISS top 15 and BM25 top 15", side=1)
    msg(4, 3, "11  semantic hits, lexical hits", ret=True)
    self_call(3, "12  fuse: 0.65 sem + 0.35 lex (min-max), keep 15")
    msg(3, 5, "13  rerank(combined, fused, top 5)")
    msg(5, 3, "14  top 5 + relevance (min-max)", ret=True)
    msg(3, 7, "15  check_safety(raw query)")
    msg(7, 3, "16  flag, message", ret=True)
    msg(3, 6, "17  generate(normalised, top 5)")
    msg(6, 3, "18  answer, generated_by", ret=True)
    msg(3, 7, "19  apply_safety_filter(answer)")
    msg(7, 3, "20  filtered answer", ret=True)
    self_call(3, "21  prepend emergency message; label Strong/Moderate/Weak")
    msg(3, 1, "22  result dict", ret=True)
    msg(1, 8, "23  INSERT consultations (evidence JSON, score, flag)")
    msg(8, 1, "24  id, created_at", ret=True)
    msg(1, 0, "25  JSON: answer, evidence, safety, consultation_id", ret=True, gap=5.0, left=7.0)
    save(fig, OUT / "07_sequence_chat.png")


def use_case():
    fig, ax = canvas(10, 8.2, 100, 82)
    ax.add_patch(Rectangle((27, 0.2), 50, 80.6, fc="#FAFBFD", ec=NAVY, lw=1.6, zorder=0))
    ax.text(52, 78.4, "SymptoTrackAI web application (CareLens AI)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    names = [("UC1  Open landing page", "v"), ("UC2  Register an account", "v"), ("UC3  Sign in (own or demo account)", "b"), ("UC4  Describe symptoms in\neveryday language", "u"),
             ("UC5  Read grounded answer and\nevidence cards", "u"), ("UC6  See emergency / caution banner", "u"), ("UC7  See recent consultations", "u"),
             ("UC8  Search consultation history", "u"), ("UC9  Open consultation detail", "u"), ("UC10  Delete a consultation", "u"), ("UC11  View About page and\nmeasured metrics", "u"),
             ("UC12  Sign out, switch theme", "u")]
    ys = [72, 66, 60, 53.5, 47, 41, 35.5, 30, 24.5, 19, 13, 6.5]
    for (t, _), y in zip(names, ys):
        ellipse(ax, 52, y, 42, 5.0, t, fs=7.0)

    def actor(x, y, name):
        ax.add_patch(Circle((x, y + 6.5), 1.6, fc="white", ec=NAVY, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 4.9, y + 1.0], color=NAVY, lw=1.6)
        ax.plot([x - 3, x + 3], [y + 3.8, y + 3.8], color=NAVY, lw=1.6)
        ax.plot([x, x - 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.plot([x, x + 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.text(x, y - 5.0, name, ha="center", fontsize=8.4, fontweight="bold", color=INK)

    actor(10, 62, "Visitor\n(not signed in)")
    actor(10, 24, "Registered user")
    ax.add_patch(Rectangle((84, 44), 14, 9, fc=WHITE, ec=NAVY, lw=1.4, zorder=2))
    ax.text(91, 48.5, "Local models\n(MiniLM, reranker,\nFlan-T5)\n<<system>>", ha="center", va="center", fontsize=6.6, fontweight="bold", zorder=3)
    for idx in (0, 1, 2):
        arrow(ax, (15, 66), (31, ys[idx]), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    for idx in range(3, 12):
        arrow(ax, (15, 29), (31, ys[idx]), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (84, 48.5), (73, 48.5), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (52, 50.3), (52, 49.5), None, color=GREY, lw=1.0, ls="--")
    ax.text(74, 51.2, "<<include>>", fontsize=6.6, color=GREY, style="italic")
    ax.text(52, 1.4, "UC4 to UC12 require UC3 (a valid session cookie); UC6 is part of UC5", ha="center", fontsize=6.8, color=GREY)
    save(fig, OUT / "08_use_case.png")


def flowchart():
    fig, ax = canvas(10, 12.0, 100, 120)
    cx, w, hh = 36, 62, 7.2
    ax.text(50, 117, "Core algorithm: hybrid retrieval with reranking (Pipeline.answer, steps 1-6)", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    box(ax, cx, 109, w, hh, "raw symptom query (3-2000 characters)", BLUE, fs=7.8)
    box(ax, cx, 98.5, w, 9, "normalize_query: lower-case, collapse spaces, '?!;' -> '.'\nsplit on , . 'and' 'with' (max 8 fragments) -> core text", BLUE, fs=7.2)
    box(ax, cx, 86.5, w, 9, "combined = normalised query + hypothetical template\n'Medical symptom presentation involving <core> ...' (no model)", BLUE, fs=7.2)
    arrow(ax, (cx, 105.4), (cx, 103.0), color=NAVY)
    arrow(ax, (cx, 94.0), (cx, 91.0), color=NAVY)
    box(ax, cx, 74.5, w, 7.2, "query vector = MiniLM-L6-v2(combined), 384-d, L2-normalised\n(TF-IDF vector if the model cannot be loaded)", TEAL, fs=7.0)
    arrow(ax, (cx, 82.0), (cx, 78.1), color=NAVY)
    box(ax, 16, 61.5, 27, 8.5, "FAISS IndexFlatIP\ntop 15 by inner product\n(cosine)", TEAL, fs=7.0)
    box(ax, 56, 61.5, 27, 8.5, "BM25Okapi on tokens of\ncombined text\ntop 15 by BM25 score", TEAL, fs=7.0)
    ax.plot([cx, cx], [70.9, 68.2], color=NAVY, lw=1.5)
    ax.plot([16, 56], [68.2, 68.2], color=NAVY, lw=1.5)
    arrow(ax, (16, 68.2), (16, 65.8), color=NAVY)
    arrow(ax, (56, 68.2), (56, 65.8), color=NAVY)
    ax.plot([16, 16], [57.2, 54.5], color=NAVY, lw=1.5)
    ax.plot([56, 56], [57.2, 54.5], color=NAVY, lw=1.5)
    ax.plot([16, 56], [54.5, 54.5], color=NAVY, lw=1.5)
    arrow(ax, (cx, 54.5), (cx, 52.0), color=NAVY)
    box(ax, cx, 46, w, 11, "fuse: union of hits; min-max normalise each score list (missing = 0);\nhybrid = 0.65 x semantic + 0.35 x lexical;\nsort, keep 15 candidates", ORANGE, fs=7.2)
    arrow(ax, (cx, 40.5), (cx, 38.0), color=NAVY)
    box(ax, cx, 33, w, 9.5, "cross-encoder ms-marco-MiniLM-L-6-v2 scores each (combined, retrieval_text) pair;\nsort by score (hybrid order if the model is unavailable)", ORANGE, fs=7.0)
    arrow(ax, (cx, 28.2), (cx, 25.6), color=NAVY)
    box(ax, cx, 20, w, 10.5, "relevance = (score - min) / (max - min) over the 15 candidates -> top record = 1.00\nlabel: >= 0.66 Strong, >= 0.33 Moderate, else Weak\nkeep top 5 -> evidence cards", PURPLE, fs=7.0)
    arrow(ax, (cx, 14.8), (cx, 12.2), color=NAVY)
    box(ax, cx, 8, w, 7.2, "top_condition = disease of record 1; pass the 5 records to generation and safety", NAVY, fs=7.2)
    ax.add_patch(Rectangle((1.5, 49), 3.4, 15.5, fc="none", ec="none"))
    ax.text(78, 61.5, "the two searches\nrun on the same\ncombined text", fontsize=6.8, color=GREY, ha="left", va="center")
    ax.text(70.5, 46, "weights: config\nCARELENS_HYBRID_SEM,\nCARELENS_HYBRID_LEX", fontsize=6.6, color=GREY, ha="left", va="center")
    ax.text(70.5, 33, "pairs scored in one\npredict() call", fontsize=6.6, color=GREY, ha="left", va="center")
    ax.text(70.5, 20, "the score shown to the\nuser is relative, not\na probability", fontsize=6.6, color=GREY, ha="left", va="center")
    save(fig, OUT / "10_flowchart_retrieval.png")


def all_more():
    dfd1()
    dfd2()
    class_diagram()
    sequence_diagram()
    use_case()
    flowchart()
