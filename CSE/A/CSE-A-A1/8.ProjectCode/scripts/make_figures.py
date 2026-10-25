"""
Result charts (150 dpi PNG) from experiments/results.json, experiments/api_latency.json and the quiz audit.

    python scripts\\make_figures.py      # system Python with matplotlib; writes docs/figures/*.png
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments")
OUT = os.path.join(ROOT, "docs", "figures")
os.makedirs(OUT, exist_ok=True)

R = json.load(open(os.path.join(EXP, "results.json"), encoding="utf-8"))
API = json.load(open(os.path.join(EXP, "api_latency.json"), encoding="utf-8"))
AUD = json.load(open(os.path.join(EXP, "quiz_audit.json"), encoding="utf-8"))["summary"]

INK, GRID = "#1f2937", "#d9dde5"
C = {"violet": "#6d5ae6", "cyan": "#12b5cb", "green": "#2fb67c", "amber": "#f0a62b", "rose": "#e0526d", "slate": "#8b95a7"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight"})

NAMES = {"tfidf_shipped (1-2gram)": "TF-IDF (shipped)", "tfidf_unigram": "TF-IDF unigram", "bm25": "BM25",
         "tfidf_lsa200": "TF-IDF + LSA", "hybrid_bm25_lsa": "BM25 + LSA", "dense_bge_small": "Dense (BGE-small)",
         "hybrid_bm25_dense": "BM25 + dense"}


def save(fig, name):
    fig.savefig(os.path.join(OUT, name))
    plt.close(fig)
    print("wrote", name)


# 1. retrieval methods ------------------------------------------------------
ret = R["retrieval"]
keys = list(NAMES)
fig, ax = plt.subplots(figsize=(7.2, 3.3))
x = np.arange(len(keys))
w = 0.26
for i, (lab, getter, col) in enumerate([("Hit@1", lambda v: v["hit"]["1"], C["violet"]), ("Hit@4", lambda v: v["hit"]["4"], C["cyan"]),
                                       ("MRR@10", lambda v: v["mrr10"], C["amber"])]):
    vals = [getter(ret[k]) for k in keys]
    b = ax.bar(x + (i - 1) * w, vals, w, label=lab, color=col)
    for rect, v in zip(b, vals):
        ax.text(rect.get_x() + rect.get_width() / 2, v + 0.012, f"{v:.2f}", ha="center", fontsize=6.5, color=INK)
ax.set_xticks(x)
ax.set_xticklabels([NAMES[k] for k in keys], rotation=18, ha="right")
ax.set_ylim(0, 1.05)
ax.set_ylabel("score (72 questions)")
ax.legend(ncol=3, frameon=False, loc="upper left")
ax.set_title("Retrieval quality of seven retrievers on the same 672 chunks", fontsize=9.5, color=INK)
save(fig, "fig_retrieval_methods.png")

# 2. hit@k curves -----------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.6, 3.3))
ks = list(range(1, 11))
for k, col, ls in [("tfidf_shipped (1-2gram)", C["violet"], "-"), ("bm25", C["green"], "-"), ("dense_bge_small", C["rose"], "--"),
                   ("hybrid_bm25_dense", C["cyan"], "-")]:
    ax.plot(ks, [ret[k]["hit"][str(i)] for i in ks], ls, color=col, marker="o", ms=3.5, lw=1.8, label=NAMES[k])
ax.axvline(4, color=C["slate"], lw=0.9, ls=":")
ax.text(4.1, 0.37, "top_k = 4 (default)", fontsize=7.5, color=C["slate"])
ax.set_xlabel("k (chunks returned)")
ax.set_ylabel("Hit@k")
ax.set_ylim(0.3, 1.02)
ax.set_xticks(ks)
ax.legend(frameon=False, loc="lower right", fontsize=8)
save(fig, "fig_hit_at_k.png")

# 3. by question type -------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
types = ["fact", "definition", "reasoning"]
for ax, metric, title in zip(axes, ["hit1", "hit4"], ["Hit@1", "Hit@4"]):
    for i, (k, col) in enumerate([("tfidf_shipped (1-2gram)", C["violet"]), ("bm25", C["green"]), ("hybrid_bm25_dense", C["cyan"])]):
        vals = [ret[k]["by_type"][t][metric] for t in types]
        b = ax.bar(np.arange(3) + (i - 1) * 0.26, vals, 0.26, color=col, label=NAMES[k])
        for rect, v in zip(b, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, v + 0.012, f"{v:.2f}", ha="center", fontsize=6.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([t.capitalize() + chr(10) + "(24 questions)" for t in types])
    ax.set_title(title, fontsize=9.5)
    ax.set_ylim(0, 1.08)
axes[0].set_ylabel("score")
axes[0].legend(frameon=False, fontsize=7.5, loc="upper left")
save(fig, "fig_by_type.png")

# 4. chunk size -------------------------------------------------------------
cs = R["chunk_sizes"]
labels = list(cs)
fig, ax = plt.subplots(figsize=(5.8, 3.2))
ax.plot(labels, [cs[k]["hit4"] for k in labels], marker="o", color=C["cyan"], lw=1.9, label="Hit@4")
ax.plot(labels, [cs[k]["hit1"] for k in labels], marker="o", color=C["violet"], lw=1.9, label="Hit@1")
ax.plot(labels, [cs[k]["mrr10"] for k in labels], marker="o", color=C["amber"], lw=1.9, label="MRR@10")
ax.set_xlabel("chunk size / overlap (words)")
ax.set_ylabel("score")
ax.set_ylim(0.2, 1.02)
ax2 = ax.twinx()
ax2.bar(labels, [cs[k]["chunks"] for k in labels], 0.45, color=C["slate"], alpha=0.22)
ax2.set_ylabel("chunks in index", color=C["slate"])
ax2.grid(False)
ax2.spines["right"].set_visible(True)
ax.legend(frameon=False, loc="lower right", fontsize=8)
save(fig, "fig_chunk_size.png")

# 5. compression trade-off --------------------------------------------------
cp = R["compression"]
kk = ["1", "2", "4", "6", "8"]
fig, ax = plt.subplots(figsize=(6.0, 3.3))
ax.plot(kk, [cp[k]["key_in_ctx"] for k in kk], marker="o", color=C["cyan"], lw=2, label="answer key in full retrieved chunks")
ax.plot(kk, [cp[k]["key_in_ans"] for k in kk], marker="o", color=C["violet"], lw=2, label="answer key in extractive answer")
ax.set_xlabel("chunks retrieved (top_k)")
ax.set_ylabel("answer-key recall")
ax.set_ylim(0.3, 1.02)
ax2 = ax.twinx()
ax2.plot(kk, [cp[k]["token_reduction_pct"] for k in kk], marker="s", ls="--", color=C["amber"], lw=1.6, label="words removed (%)")
ax2.set_ylabel("words removed (%)", color=C["amber"])
ax2.set_ylim(0, 100)
ax2.grid(False)
ax2.spines["right"].set_visible(True)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7.5, loc="lower right")
save(fig, "fig_compression.png")

# 6. abstention -------------------------------------------------------------
ab = R["abstention"]
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.1))
bins = np.linspace(0, 0.8, 17)
axes[0].hist(ab["in_scope_scores"], bins=bins, color=C["violet"], alpha=0.8, label=f"in-scope (n={len(ab['in_scope_scores'])})")
axes[0].hist(ab["off_topic_scores"], bins=bins, color=C["rose"], alpha=0.8, label=f"off-topic (n={len(ab['off_topic_scores'])})")
axes[0].set_xlabel("top-1 cosine score")
axes[0].set_ylabel("questions")
axes[0].legend(frameon=False, fontsize=8)
sw = ab["sweep"]
axes[1].plot([s["tau"] for s in sw], [s["in_scope_answered"] for s in sw], marker="o", color=C["violet"], lw=1.9, label="in-scope answered")
axes[1].plot([s["tau"] for s in sw], [s["off_topic_refused"] for s in sw], marker="o", color=C["rose"], lw=1.9, label="off-topic refused")
axes[1].set_xlabel("refusal threshold on the top-1 score")
axes[1].set_ylim(0, 1.05)
axes[1].legend(frameon=False, fontsize=8, loc="center left")
save(fig, "fig_abstention.png")

# 7. scaling ----------------------------------------------------------------
sc = R["scaling"]
fig, ax = plt.subplots(figsize=(5.8, 3.2))
xs = [s["chunks"] for s in sc]
ax.plot(xs, [s["retrieve_ms_median"] for s in sc], marker="o", color=C["violet"], lw=1.9, label="retrieve, median")
ax.plot(xs, [s["answer_ms_median"] for s in sc], marker="o", color=C["cyan"], lw=1.9, label="retrieve + extractive answer, median")
ax.plot(xs, [s["index_build_ms"] for s in sc], marker="s", color=C["amber"], lw=1.9, label="index rebuild (once per upload/delete)")
ax.set_xscale("log", base=2)
ax.set_xticks(xs)
ax.set_xticklabels([f"{x:,}" for x in xs])
ax.set_xlabel("chunks in the user's index (about 180 words each)")
ax.set_ylabel("milliseconds")
ax.legend(frameon=False, fontsize=7.8, loc="upper left")
save(fig, "fig_scaling.png")

# 8. API latency ------------------------------------------------------------
rows = [("health", API["health"]), ("login (hashing)", API["login"]), ("dashboard", API["dashboard"]), ("documents list", API["documents_list"]),
        ("roadmap", API["roadmap"]), ("ask", API["ask"]), ("quiz generate", API["quiz_generate"]), ("quiz submit", API["quiz_submit"])]
fig, ax = plt.subplots(figsize=(6.2, 3.3))
y = np.arange(len(rows))
ax.barh(y, [r[1]["median_ms"] for r in rows], color=C["violet"], label="median")
ax.scatter([r[1]["p95_ms"] for r in rows], y, color=C["rose"], zorder=3, s=22, label="95th percentile")
ax.set_yticks(y)
ax.set_yticklabels([r[0] for r in rows])
ax.invert_yaxis()
ax.set_xscale("log")
ax.set_xlabel("milliseconds (log scale), 127.0.0.1, 672 chunks indexed")
for yy, r in zip(y, rows):
    ax.text(r[1]["median_ms"] * 1.08, yy, f"{r[1]['median_ms']:.0f}", va="center", fontsize=7.5)
ax.legend(frameon=False, fontsize=8, loc="lower right")
save(fig, "fig_api_latency.png")

# 9. heading formats --------------------------------------------------------
hf = R["document_analysis"]["heading_formats"]
fig, ax = plt.subplots(figsize=(5.8, 3.0))
labs = list(hf)
vals = [hf[k]["units_found"] for k in labs]
ax.bar(range(len(labs)), vals, color=[C["green"] if v == 5 else C["rose"] for v in vals])
ax.set_xticks(range(len(labs)))
ax.set_xticklabels(labs, rotation=20, ha="right")
ax.set_ylabel("units found (of 5)")
ax.set_ylim(0, 5.6)
for i, v in enumerate(vals):
    ax.text(i, v + 0.1, str(v), ha="center", fontsize=8)
save(fig, "fig_heading_formats.png")

# 10. quiz quality ----------------------------------------------------------
qz = R["quiz"]
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
parts = [AUD["acceptable"], AUD["ambiguous"], AUD["poor"]]
axes[0].bar(["acceptable", "ambiguous", "poor"], parts, color=[C["green"], C["amber"], C["rose"]])
for i, v in enumerate(parts):
    axes[0].text(i, v + 0.3, f"{v}", ha="center", fontsize=8.5)
axes[0].set_title("Manual review, 30 questions", fontsize=9)
axes[0].set_ylabel("questions")
auto = [("structurally valid", qz["structurally_valid"]), ("another option in stem", qz["ambiguous_rate"]),
        ("answer repeated in stem", qz["answer_repeated_in_stem_rate"])]
axes[1].barh([a[0] for a in auto], [a[1] for a in auto], color=[C["green"], C["amber"], C["rose"]])
for i, a in enumerate(auto):
    axes[1].text(a[1] + 0.012, i, f"{100 * a[1]:.1f}%", va="center", fontsize=8)
axes[1].set_xlim(0, 1.15)
axes[1].invert_yaxis()
axes[1].set_title("Automatic checks, 900 questions", fontsize=9)
save(fig, "fig_quiz_quality.png")
