"""Evaluation plots (matplotlib, PNG) using the same validated palette as the product's charts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

SERIES = ["#0d9488", "#eb6834", "#2a78d6", "#e87ba4"]
INK, MUTED, GRID = "#1f2933", "#5b6673", "#e4e7eb"
METHOD_LABELS = {"bm25": "BM25 (keyword)", "dense": "Dense (MiniLM)", "hybrid": "Hybrid (RRF)",
                 "hybrid_rerank": "Hybrid + re-rank"}
METHOD_COLORS = {"bm25": SERIES[1], "dense": SERIES[2], "hybrid": SERIES[3], "hybrid_rerank": SERIES[0]}


def _style(ax, title: str) -> None:  # noqa: ANN001
    ax.set_title(title, loc="left", fontsize=12, color=INK, fontweight="bold", pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, path: Path) -> None:  # noqa: ANN001
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor="white")
    plt.close(fig)


def retrieval_ablation(metrics: dict[str, Any], path: Path) -> None:
    keys = ["hit@1", "hit@3", "hit@5", "mrr@10"]
    methods = [m for m in METHOD_LABELS if m in metrics]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    width = 0.8 / max(1, len(methods))
    for i, m in enumerate(methods):
        values = [metrics[m].get(k, 0) * 100 for k in keys]
        xs = [j + (i - (len(methods) - 1) / 2) * width for j in range(len(keys))]
        bars = ax.bar(xs, values, width * 0.92, color=METHOD_COLORS[m], label=METHOD_LABELS[m], zorder=3)
        if m == "hybrid_rerank":
            for bar, v in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5, f"{v:.0f}", ha="center", fontsize=8, color=INK)
    ax.set_xticks(range(len(keys)), [k.upper().replace("@", " @") for k in keys])
    ax.set_ylim(0, 108)
    ax.set_ylabel("% of questions", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper left", bbox_to_anchor=(0, -0.12))
    _style(ax, "Retrieval: expected clause found (higher is better)")
    _save(fig, path)


def faithfulness_distribution(bins: list[dict], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.6))
    labels = [b["bin"] for b in bins]
    values = [b["count"] for b in bins]
    bars = ax.bar(labels, values, 0.55, color=SERIES[0], zorder=3)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.3, str(v), ha="center", fontsize=9, color=INK)
    ax.set_xlabel("Faithfulness score (0-100)", color=MUTED, fontsize=9)
    ax.set_ylabel("Answers", color=MUTED, fontsize=9)
    _style(ax, "Faithfulness of generated answers")
    _save(fig, path)


def latency_by_stage(stages: dict[str, dict], path: Path) -> None:
    names = list(stages)
    p50 = [stages[n].get("p50_ms", 0) / 1000 for n in names]
    p95 = [stages[n].get("p95_ms", 0) / 1000 for n in names]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ys = range(len(names))
    ax.barh([y + 0.2 for y in ys], p50, 0.38, color=SERIES[0], label="Median (p50)", zorder=3)
    ax.barh([y - 0.2 for y in ys], p95, 0.38, color=SERIES[1], label="p95", zorder=3)
    ax.set_yticks(list(ys), names)
    ax.set_xlabel("Seconds", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _style(ax, "Response time by stage")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    _save(fig, path)


def confusion_matrix(report: dict[str, Any], path: Path) -> None:
    labels = [l.replace("_", " ") for l in report["labels"]]
    matrix = report["confusion_matrix"]
    cmap = LinearSegmentedColormap.from_list("teal", ["#f0fdfa", "#0f766e"])
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    ax.imshow(matrix, cmap=cmap)
    peak = max(max(r) for r in matrix) or 1
    for i, row in enumerate(matrix):
        for j, v in enumerate(row):
            ax.text(j, i, str(v), ha="center", va="center", fontsize=11,
                    color="white" if v / peak > 0.55 else INK, fontweight="bold")
    ax.set_xticks(range(len(labels)), labels, rotation=20, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted", color=MUTED, fontsize=9)
    ax.set_ylabel("Expected", color=MUTED, fontsize=9)
    ax.set_title(f"Claim Copilot verdicts (accuracy {report['accuracy'] * 100:.0f}%)", loc="left", fontsize=12,
                 color=INK, fontweight="bold", pad=12)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    _save(fig, path)


def horizontal_scores(scores: dict[str, float], title: str, path: Path) -> None:
    items = sorted(scores.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7, max(2.6, 0.34 * len(items) + 1)))
    names = [k.replace("_", " ") for k, _ in items]
    values = [v * 100 for _, v in items]
    ax.barh(names, values, 0.6, color=SERIES[0], zorder=3)
    for y, v in enumerate(values):
        ax.text(v + 1, y, f"{v:.0f}%", va="center", fontsize=8, color=INK)
    ax.set_xlim(0, 110)
    _style(ax, title)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    _save(fig, path)


def make_all(metrics: dict[str, Any], plot_dir: Path) -> list[str]:
    plot_dir.mkdir(parents=True, exist_ok=True)
    made: list[str] = []
    if metrics.get("retrieval"):
        retrieval_ablation(metrics["retrieval"], plot_dir / "retrieval_ablation.png")
        made.append("retrieval_ablation.png")
    answers = metrics.get("answers") or {}
    if answers.get("faithfulness", {}).get("bins"):
        faithfulness_distribution(answers["faithfulness"]["bins"], plot_dir / "faithfulness_distribution.png")
        made.append("faithfulness_distribution.png")
    if answers.get("stage_latency_ms"):
        latency_by_stage(answers["stage_latency_ms"], plot_dir / "latency_by_stage.png")
        made.append("latency_by_stage.png")
    if answers.get("by_category"):
        horizontal_scores({k: v["accuracy"] for k, v in answers["by_category"].items()},
                          "Answer accuracy by question type", plot_dir / "answer_accuracy_by_category.png")
        made.append("answer_accuracy_by_category.png")
    claims = metrics.get("claims") or {}
    if claims.get("confusion_matrix"):
        confusion_matrix(claims, plot_dir / "claims_confusion_matrix.png")
        made.append("claims_confusion_matrix.png")
    extraction = metrics.get("extraction") or {}
    if extraction.get("by_field"):
        horizontal_scores(extraction["by_field"], "Policy Card extraction accuracy by field",
                          plot_dir / "extraction_accuracy_by_field.png")
        made.append("extraction_accuracy_by_field.png")
    return made
