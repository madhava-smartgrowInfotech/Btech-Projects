"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so text stays legible)."""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from . import facts as F

sys.path.insert(0, os.path.join(F.CODE, "scripts", "docs_build"))
from dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, WHITE, arrow, box,  # noqa: E402
                     canvas, panel, save)

RED = "#C0392B"


def _save(fig, name):
    p = os.path.join(F.FIGS, name)
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def arch():
    fig, ax = canvas(3.5, 2.9, 100, 82.9)
    panel(ax, 1, 66, 98, 16, "Web app (React 18 + Vite 5, port 5309)", PALE_BLUE, BLUE, fs=6)
    for x, t in [(18, "Overview\nGraph & features"), (40, "Accounts\nAccount detail"), (62, "Botnet clusters\nModerator queue"), (84, "Models & scale")]:
        box(ax, x, 70, 19.5, 8.5, t, BLUE, fs=5.2)
    panel(ax, 1, 43, 98, 21, "FastAPI service (127.0.0.1:8309), JWT roles", PALE_TEAL, TEAL, fs=6)
    box(ax, 17, 50, 30, 11, "/api/accounts\n/api/clusters\n/api/graph/summary", TEAL, fs=5.2)
    box(ax, 50, 50, 30, 11, "/api/queue/decisions\n/api/models/retrain\n(moderator only)", TEAL, fs=5.2)
    box(ax, 83, 50, 28, 11, "/api/auth/login\n/api/models\n/api/health", TEAL, fs=5.2)
    panel(ax, 1, 17, 98, 24, "Core (loaded once at start-up)", PALE_ORANGE, ORANGE, fs=6)
    box(ax, 25, 25, 46, 13, "ml/: graph builder (23 features),\nGCN / GAT / GraphSAGE in plain\nPyTorch, Louvain clustering", ORANGE, fs=5.2)
    box(ax, 75, 25, 46, 13, "services/store.py: scores, clusters,\nneighbour index, gradient x input\nreasons, retrain thread", ORANGE, fs=5.2)
    panel(ax, 1, 0.5, 98, 15, "Storage", LIGHT, "#B7C3D3", fs=6)
    for x, t in [(17, "SQLite: users,\nreviews, training_runs"), (50, "graph.npz, accounts.csv\nmodels/*.pt, clusters.json"), (83, "experiments/*.json\nmetrics, scalability")]:
        box(ax, x, 5.2, 29, 7.5, t, WHITE, tc=INK, ec=NAVY, fs=4.9)
    arrow(ax, (50, 66), (50, 64), "", color=NAVY, lw=1.0)
    arrow(ax, (50, 43), (50, 41), "", color=NAVY, lw=1.0)
    arrow(ax, (50, 17), (50, 15.5), "", color=NAVY, lw=1.0)
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = canvas(3.5, 2.75, 100, 78.6)
    xs = [10, 29.5, 49, 68.5, 88]
    ax.text(1, 75.5, "Training and scoring", fontsize=6.4, color=PURPLE, fontweight="bold")
    a = [("Facebook ties\n+ profile and\nposting rows", BLUE), ("Inject 8 botnets\n+ 150 lone\nspammers", BLUE), ("23 features,\nstratified\n60/20/20", BLUE), ("4 models x\n3 seeds,\nvalidation F1", PURPLE), ("Threshold\non validation,\nserve best", PURPLE)]
    for x, (t, c) in zip(xs, a):
        box(ax, x, 63, 17.5, 15, t, c, fs=4.9)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 9, 63), (q - 9, 63), "", color=NAVY, lw=1.0)
    ax.text(1, 49.5, "Clusters and moderator loop", fontsize=6.4, color=ORANGE, fontweight="bold")
    b = [("Candidates\np >= 0.30", PURPLE), ("kNN cosine\ngraph + real\nties", PURPLE), ("Louvain,\ndrop groups\n< 5", ORANGE), ("Moderator\nconfirms or\ndismisses", TEAL), ("Retrain on\ndecisions\n(test split\nuntouched)", TEAL)]
    for x, (t, c) in zip(xs, b):
        box(ax, x, 33, 17.5, 15, t, c, fs=4.9)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 9, 33), (q - 9, 33), "", color=NAVY, lw=1.0)
    arrow(ax, (88, 25), (88, 14), "", color=NAVY, lw=1.0)
    arrow(ax, (88, 14), (12, 14), "", color=GREY, lw=0.9, ls="--")
    ax.text(50, 10.5, "decisions become training labels for the next run; F1 before / after is logged", fontsize=4.8, ha="center", color=INK)
    return _save(fig, "paper_flow.png")


def results():
    plt.rcParams.update({"font.size": 6.5})
    fig, axs = plt.subplots(1, 2, figsize=(3.55, 2.45), gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.5})
    ax = axs[0]
    keys = F.ORDER
    labs = ["MLP", "GCN", "GAT", "SAGE"]
    x = np.arange(4)
    for off, (k, c, n) in zip((-0.27, 0, 0.27), [("precision", BLUE, "P"), ("recall", ORANGE, "R"), ("f1", TEAL, "F1")]):
        v = [F.mean(m, k) for m in keys]
        e = [F.std(m, k) for m in keys]
        ax.bar(x + off, v, 0.26, yerr=e, color=c, capsize=1, error_kw={"lw": 0.5}, label=n)
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=5.6)
    ax.set_ylim(0.6, 1.0)
    ax.legend(frameon=False, fontsize=5, ncol=3, loc="upper left", columnspacing=0.6, handlelength=0.9)
    ax.set_title("(a) test split, 3 seeds", fontsize=6.2)
    ax = axs[1]
    ab = F.EXTRA["ablation"]
    rows = [("all 23", "all 23 features"), ("no temporal", "without temporal pattern"), ("profile only", "profile metadata only"), ("degree only", "degree only (structure, no attributes)")]
    y = np.arange(len(rows))[::-1]
    ax.barh(y + 0.19, [ab[r[1]]["baseline"]["f1_mean"] for r in rows], 0.36, color="#8795A8", label="MLP")
    ax.barh(y - 0.19, [ab[r[1]]["sage"]["f1_mean"] for r in rows], 0.36, color=TEAL, label="GraphSAGE")
    for yy, r in zip(y, rows):
        ax.text(ab[r[1]]["baseline"]["f1_mean"] + 0.015, yy + 0.19, f"{ab[r[1]]['baseline']['f1_mean']:.3f}", va="center", fontsize=4.8)
        ax.text(ab[r[1]]["sage"]["f1_mean"] + 0.015, yy - 0.19, f"{ab[r[1]]['sage']['f1_mean']:.3f}", va="center", fontsize=4.8)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=5.4)
    ax.set_xlim(0, 1.2)
    ax.set_xlabel("test F1", fontsize=5.8)
    ax.legend(frameon=False, fontsize=4.8, loc="upper center", bbox_to_anchor=(0.45, -0.19), ncol=2, handlelength=0.9)
    ax.set_title("(b) feature ablation", fontsize=6.2)
    for a in axs:
        a.tick_params(axis="both", labelsize=5.2, length=2)
        a.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.22, top=0.89)
    return _save(fig, "paper_results.png")


def screens():
    s = Image.open(F.shot("07b_account_reasons_and_neighbourhood.png")).convert("RGB")
    p1 = os.path.join(F.FIGS, "paper_screen_account.png")
    s.crop((292, 100, 842, 560)).save(p1)
    c = Image.open(F.shot("08_clusters.png")).convert("RGB")
    p2 = os.path.join(F.FIGS, "paper_screen_clusters.png")
    c.crop((315, 430, 935, 880)).save(p2)
    return p1, p2


def sweep():
    plt.rcParams.update({"font.size": 6.5})
    sw = F.EXTRA["threshold_sweep"]
    fig, axs = plt.subplots(1, 2, figsize=(3.55, 1.9), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, (k, ttl) in zip(axs, [("baseline", "(a) MLP baseline"), ("sage", "(b) GraphSAGE")]):
        t = [r["threshold"] for r in sw[k]]
        for key, c, n in [("precision", BLUE, "precision"), ("recall", ORANGE, "recall"), ("f1", TEAL, "F1")]:
            ax.plot(t, [r[key] for r in sw[k]], color=c, lw=1.1, label=n)
        ax.axvline(0.5, color=GREY, ls="--", lw=0.6)
        ax.set_xlabel("decision threshold", fontsize=5.8)
        ax.set_title(ttl, fontsize=6.2)
        ax.set_ylim(0.3, 1.02)
        ax.tick_params(axis="both", labelsize=5.2, length=2)
        ax.spines[["top", "right"]].set_visible(False)
    axs[0].legend(frameon=False, fontsize=5, loc="lower left", handlelength=1)
    fig.subplots_adjust(left=0.1, right=0.99, bottom=0.2, top=0.88)
    return _save(fig, "paper_sweep.png")


def make():
    a, b = screens()
    return {"arch": arch(), "flow": flow(), "results": results(), "sweep": sweep(), "account": a, "clusters": b}


if __name__ == "__main__":
    print(make())
