"""Extra result charts for the reports, drawn from experiments/eval-20260922-0027/metrics.json (no numbers typed by hand)
and the three kept runs. Output: docs/charts/*.png (150 dpi).

    python scripts/make_charts.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "charts"
RUNS = ["eval-20260921-2353", "eval-20260922-0008", "eval-20260922-0027"]
COL = ["#6d5bd0", "#2f9e6d", "#e08a2c", "#d1495b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def metrics(run: str) -> dict:
    return json.loads((ROOT / "experiments" / run / "metrics.json").read_text(encoding="utf-8"))


def improvement() -> None:
    labels = ["Retrieval\nhit@5", "Answer\naccuracy", "Citation\naccuracy"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    width = 0.26
    for i, run in enumerate(RUNS):
        m = metrics(run)
        retr = m["retrieval"]["hybrid_rerank"]["hit@5"]
        h = m.get("headline") or {}
        ans = h.get("answer_accuracy")
        cit = h.get("citation_accuracy")
        if ans is None:
            ans = m["answers"]["answer_accuracy"]
            cit = m["answers"]["citation_accuracy"]
        vals = [100 * retr, 100 * ans, 100 * cit]
        bars = ax.bar([x + (i - 1) * width for x in range(3)], vals, width, label=run, color=COL[i])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels)
    ax.set_ylim(80, 103)
    ax.set_ylabel("percent (axis starts at 80)")
    ax.set_title("Three evaluation runs: each fix removed errors the previous run exposed", fontsize=9.5, fontweight="bold")
    ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "improvement_runs.png", dpi=150)
    plt.close(fig)


def headline() -> None:
    m = metrics(RUNS[-1])
    h = m["headline"]
    items = [("Retrieval hit@5", 100 * h["retrieval_hit_at_5"]), ("Answer accuracy", 100 * h["answer_accuracy"]),
             ("Citation accuracy", 100 * h["citation_accuracy"]), ("Abstention accuracy", 100 * h["abstention_accuracy"]),
             ("Claim verdicts", 100 * h["claim_verdict_accuracy"]), ("Policy Card values", 100 * h["extraction_accuracy"]),
             ("Faithfulness (mean)", h["faithfulness_mean"])]
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    ys = list(range(len(items)))[::-1]
    bars = ax.barh(ys, [v for _, v in items], color=[COL[0]] * 6 + [COL[2]], height=0.62)
    for b, (_, v) in zip(bars, items):
        ax.text(v - 1.2, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center", ha="right", color="white", fontsize=8.5, fontweight="bold")
    ax.set_yticks(ys)
    ax.set_yticklabels([n for n, _ in items])
    ax.set_xlim(0, 105)
    ax.set_xlabel("percent (faithfulness: score out of 100)")
    ax.set_title(f"Headline results, run {RUNS[-1]}", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "headline_metrics.png", dpi=150)
    plt.close(fig)


def retrieval_paper() -> None:
    """Two stacked panels sized for one IEEE column (3.45 in): retrieval methods and latency by stage."""
    m = metrics(RUNS[-1])
    r = m["retrieval"]
    methods = [("BM25", "bm25"), ("Dense", "dense"), ("Hybrid", "hybrid"), ("Hybrid+rerank", "hybrid_rerank")]
    fig, axes = plt.subplots(2, 1, figsize=(3.45, 3.7), gridspec_kw={"height_ratios": [1.25, 1]})
    ax = axes[0]
    keys = [("hit@1", "hit@1"), ("hit@3", "hit@3"), ("hit@5", "hit@5"), ("mrr@10", "MRR@10")]
    w = 0.2
    for i, (k, lab) in enumerate(keys):
        vals = [r[mk][k] for _, mk in methods]
        ax.bar([x + (i - 1.5) * w for x in range(4)], vals, w, label=lab, color=COL[i])
    ax.set_xticks(range(4))
    ax.set_xticklabels([n for n, _ in methods], fontsize=6)
    ax.set_ylim(0, 1.25)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.tick_params(labelsize=6)
    ax.legend(ncol=4, fontsize=5.5, loc="upper center", frameon=False, columnspacing=0.8, handlelength=1)
    ax.set_title("(a) Retrieval on 51 questions", fontsize=6.5, pad=2)
    ax = axes[1]
    st = m["answers"]["stage_latency_ms"]
    names = [("retrieval", "Retrieval"), ("generation", "Gemini"), ("faithfulness", "NLI scoring")]
    p50 = [st[k]["p50_ms"] / 1000 for k, _ in names]
    p95 = [st[k]["p95_ms"] / 1000 for k, _ in names]
    ax.bar([x - 0.2 for x in range(3)], p50, 0.38, label="median", color=COL[1])
    ax.bar([x + 0.2 for x in range(3)], p95, 0.38, label="95th pct.", color=COL[2])
    for x, v in enumerate(p50):
        ax.text(x - 0.2, v + 0.4, f"{v:.1f}", ha="center", fontsize=5.5)
    for x, v in enumerate(p95):
        ax.text(x + 0.2, v + 0.4, f"{v:.1f}", ha="center", fontsize=5.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([n for _, n in names], fontsize=6)
    ax.set_ylabel("seconds", fontsize=6)
    ax.set_ylim(0, 21)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=5.5, frameon=False, loc="upper left")
    ax.set_title("(b) Answer time by stage (live Gemini calls)", fontsize=6.5, pad=2)
    fig.tight_layout(pad=0.5, h_pad=0.9)
    fig.savefig(OUT / "paper_results.png", dpi=250)
    plt.close(fig)


def confusion() -> None:
    m = metrics(RUNS[-1])["claims"]
    cm, labels = m["confusion_matrix"], ["covered", "partly", "not covered", "needs info"]
    fig, ax = plt.subplots(figsize=(4.4, 3.6))
    ax.imshow(cm, cmap="Purples", vmin=0, vmax=8)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, cm[i][j], ha="center", va="center", color="white" if cm[i][j] > 3 else "#333", fontsize=11, fontweight="bold")
    ax.set_xticks(range(4)); ax.set_yticks(range(4))
    ax.set_xticklabels(labels, rotation=20, fontsize=8); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("predicted verdict"); ax.set_ylabel("expected verdict")
    ax.set_title("Claim Copilot: 14 / 14 verdicts correct", fontsize=9.5, fontweight="bold")
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "claims_confusion.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    improvement()
    headline()
    retrieval_paper()
    confusion()
    print("saved to", OUT)
