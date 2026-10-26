"""Result charts for the BotGraph documents, drawn from experiments/**/metrics.json into docs/figures/ (PNG, 150 dpi).

    python scripts/docs_build/make_figures.py

f07, f08 and f12 need experiments/extra/metrics.json (scripts/run_extra_experiments.py); they are skipped while it is missing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
EXP = ROOT / "experiments"
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, TEAL, ORANGE, RED, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#C0392B", "#6B5BD2", "#8795A8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 10.5, "axes.titleweight": "bold"})

M = json.loads((EXP / "metrics.json").read_text(encoding="utf-8"))
SC = json.loads((EXP / "scalability.json").read_text(encoding="utf-8"))
EXTRA_P = EXP / "extra" / "metrics.json"
EXTRA = json.loads(EXTRA_P.read_text(encoding="utf-8")) if EXTRA_P.exists() else None
G = np.load(ROOT / "data" / "processed" / "graph.npz", allow_pickle=False)
S = np.load(ROOT / "models" / "scores.npz")
THR = json.loads((ROOT / "models" / "meta.json").read_text())["threshold"]

ORDER = ["baseline", "gcn", "gat", "sage"]
SHORT = {"baseline": "MLP baseline\n(no graph)", "gcn": "GCN", "gat": "GAT", "sage": "GraphSAGE"}
LEG = {"baseline": "MLP baseline", "gcn": "GCN", "gat": "GAT", "sage": "GraphSAGE"}
COL = {"baseline": GREY, "gcn": BLUE, "gat": PURPLE, "sage": TEAL}
MODELS = M["models"]


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def mean(m, k):
    return MODELS[m][k]["mean"]


def f01():
    fig, ax = plt.subplots(figsize=(8, 4.2))
    keys = [("precision", "Precision", BLUE), ("recall", "Recall", ORANGE), ("f1", "F1", TEAL)]
    w = 0.26
    x = np.arange(len(ORDER))
    for i, (k, lab, c) in enumerate(keys):
        v = [mean(m, k) for m in ORDER]
        e = [MODELS[m][k]["std"] for m in ORDER]
        b = ax.bar(x + (i - 1) * w, v, w, yerr=e, capsize=3, color=c, label=lab, error_kw={"lw": 1, "ecolor": "#333"})
        for xi, vi in zip(x + (i - 1) * w, v):
            ax.text(xi, vi + 0.03, f"{vi:.3f}", ha="center", fontsize=7.5, rotation=90)
    ax.set_xticks(x); ax.set_xticklabels([SHORT[m] for m in ORDER])
    ax.set_ylim(0.55, 1.12); ax.set_ylabel("Score on test split (908 accounts)")
    ax.set_title("Precision, recall and F1 (mean of 3 seeds, bars = std)")
    ax.legend(ncol=3, loc="upper left", frameon=False)
    ax.grid(axis="y", alpha=0.25)
    save(fig, "f01_model_comparison.png")


def f02():
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    for m in ORDER:
        r = MODELS[m]["roc"]
        ax.plot(r["fpr"], r["tpr"], color=COL[m], lw=2, label=f"{LEG[m]} (AUC {mean(m, 'roc_auc'):.3f})")
    ax.plot([0, 1], [0, 1], color="#bbb", ls="--", lw=1)
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.set_title("ROC curves on the test split (seed 0 curve,\nAUC = mean of 3 seeds)")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.grid(alpha=0.25)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    # zoomed inset on the useful corner
    ins = ax.inset_axes([0.36, 0.40, 0.36, 0.28])
    for m in ORDER:
        r = MODELS[m]["roc"]
        ins.plot(r["fpr"], r["tpr"], color=COL[m], lw=1.5)
    ins.set_xlim(0, 0.2); ins.set_ylim(0.6, 1.0); ins.tick_params(labelsize=7); ins.set_title("zoom: FPR 0-0.2", fontsize=7)
    ins.grid(alpha=0.25)
    save(fig, "f02_roc_curves.png")


def f03():
    fig, axs = plt.subplots(1, 4, figsize=(13.5, 3.6), gridspec_kw={"wspace": 0.35})
    for ax, m in zip(axs, ORDER):
        c = MODELS[m]["confusion"]
        cm = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
        ax.imshow(cm, cmap="Blues", vmax=cm.max() * 1.15)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]}\n{cm[i, j] / cm[i].sum() * 100:.1f}% of row", ha="center", va="center", fontsize=9,
                        color="white" if cm[i, j] > cm.max() / 2 else "black")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["pred\ngenuine", "pred\nfake"], fontsize=8.5)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["actual\ngenuine", "actual\nfake"], fontsize=8.5)
        ax.set_title(f"{LEG[m]}\n(threshold {MODELS[m]['threshold']:.3g})", fontsize=10)
        ax.spines[:].set_visible(False)
    fig.suptitle("Confusion matrices on the test split, seed 0 (908 accounts, 114 fake)", y=1.04, fontsize=11, fontweight="bold")
    save(fig, "f03_confusion_matrices.png")


def f04():
    fig, ax = plt.subplots(figsize=(7, 3.9))
    rng = np.random.default_rng(1)
    for i, m in enumerate(ORDER):
        v = [r["f1"] for r in MODELS[m]["per_seed"]]
        ax.scatter(np.full(len(v), i) + rng.uniform(-0.04, 0.04, len(v)), v, s=60, color=COL[m], zorder=3, edgecolor="white")
        ax.hlines(np.mean(v), i - 0.25, i + 0.25, color=COL[m], lw=2)
        ax.text(i + 0.28, np.mean(v), f"mean {np.mean(v):.3f}\nrange {min(v):.3f}-{max(v):.3f}", va="center", fontsize=8)
    ax.set_xticks(range(4)); ax.set_xticklabels([SHORT[m] for m in ORDER])
    ax.set_xlim(-0.5, 3.95); ax.set_ylabel("Test F1"); ax.set_ylim(0.78, 0.98)
    ax.set_title("F1 of each seed (0, 1, 2) on the same split")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "f04_seed_variance.png")


def f05():
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"wspace": 0.27})
    edges = [r["edges"] / 1000 for r in SC["rows"]]
    nodes = [r["nodes"] for r in SC["rows"]]
    for ax, key, ttl, yl in ((axs[0], "train_seconds_per_epoch", "Training time per epoch", "seconds per epoch"),
                              (axs[1], "inference_seconds", "Inference time (one forward pass)", "seconds")):
        for m in ORDER:
            v = [r["models"][m][key] for r in SC["rows"]]
            ax.plot(edges, v, "o-", color=COL[m], lw=2, label=LEG[m])
            ax.text(edges[-1] + 12, v[-1], f"{v[-1]:.2f}", fontsize=8, va="center", color=COL[m])
        ax.set_xlabel("Ties in the graph (thousands)"); ax.set_ylabel(yl); ax.set_title(ttl)
        ax.set_xlim(0, edges[-1] * 1.12); ax.grid(alpha=0.25)
        sec = ax.secondary_xaxis("top", functions=(lambda e: e * 1000 / 94456 * 4533 / 1000, lambda n: n * 94456 / 4533))
        sec.set_xlabel("Accounts (thousands)", fontsize=8.5)
    axs[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Scalability on CPU: disjoint copies of the graph, 4.5 k to 36 k accounts", y=1.14, fontsize=11, fontweight="bold")
    save(fig, "f05_scalability.png")


def f06():
    pb = M["cluster_recovery"]["per_botnet"]
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(pb))
    ax.bar(x, [b["size"] for b in pb], color="#CBD6E4", label="Injected botnet size (accounts)")
    for xi, b in zip(x, pb):
        ax.text(xi, b["size"] + 1, str(b["size"]), ha="center", fontsize=8.5)
    ax.set_ylabel("Accounts in the botnet"); ax.set_ylim(0, 85)
    ax.set_xticks(x); ax.set_xticklabels([f"botnet {b['botnet']}" for b in pb], fontsize=8.5)
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.plot(x, [b["recall"] for b in pb], "o", color=TEAL, ms=9, label="Recall of matched cluster")
    ax2.plot(x, [b["precision"] for b in pb], "D", color=ORANGE, ms=7, label="Precision of matched cluster")
    ax2.set_ylim(0.85, 1.03); ax2.set_ylabel("Recall / precision")
    for xi, b in zip(x, pb):
        if b["precision"] < 0.999:
            ax2.text(xi + 0.12, b["precision"] - 0.012, f"{b['precision']:.3f}", fontsize=8, color=ORANGE)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.1))
    ax.set_title(f"Recovery of the 8 injected botnets ({M['cluster_recovery']['recovered']}/8 found, mean precision {M['cluster_recovery']['mean_precision']:.3f})", pad=14)
    save(fig, "f06_cluster_recovery.png")


def f07():
    ts = EXTRA["threshold_sweep"]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, m, ttl in ((axs[0], "sage", "GraphSAGE (served)"), (axs[1], "baseline", "MLP baseline (no graph)")):
        rows = ts[m]
        t = [r["threshold"] for r in rows]
        ax.plot(t, [r["precision"] for r in rows], "-o", ms=3.5, color=BLUE, label="Precision")
        ax.plot(t, [r["recall"] for r in rows], "-o", ms=3.5, color=ORANGE, label="Recall")
        ax.plot(t, [r["f1"] for r in rows], "-o", ms=4, color=TEAL, lw=2.4, label="F1")
        ax.axvline(THR, color=GREY, ls="--", lw=1)
        ax.text(THR + 0.01, 0.06, f"served\nthreshold {THR:g}", fontsize=8, color=GREY)
        bi = int(np.argmax([r["f1"] for r in rows]))
        ax.annotate(f"best F1 {rows[bi]['f1']:.3f}\nat {t[bi]:.2f}", (t[bi], rows[bi]["f1"]), (t[bi] - 0.05, 0.55), fontsize=8,
                    arrowprops={"arrowstyle": "->", "color": "#555"})
        ax.set_xlabel("Decision threshold on fake probability"); ax.set_title(ttl)
        ax.set_ylim(0, 1.03); ax.grid(alpha=0.25)
    axs[0].set_ylabel("Score on test split"); axs[0].legend(frameon=False, loc="lower left", fontsize=9)
    fig.suptitle("Threshold sweep on the test split (shipped seed-0 scores)", y=1.02, fontsize=11, fontweight="bold")
    save(fig, "f07_threshold_sweep.png")


def f08():
    ab = EXTRA["ablation"]
    names = list(ab.keys())
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    y = np.arange(len(names))[::-1]
    h = 0.36
    for off, m, c, lab in ((-h / 2, "baseline", GREY, "MLP baseline"), (h / 2, "sage", TEAL, "GraphSAGE")):
        v = [ab[n][m]["f1_mean"] for n in names]
        e = [ab[n][m]["f1_std"] for n in names]
        ax.barh(y + off, v, h, xerr=e, color=c, label=lab, capsize=2.5, error_kw={"lw": 0.9})
        for yi, vi in zip(y + off, v):
            ax.text(vi + 0.012, yi, f"{vi:.3f}", va="center", fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels([f"{n} ({ab[n]['n_features']})" for n in names], fontsize=8.5)
    for yi, n in zip(y, names):
        if n.startswith("degree only"):
            ax.axhspan(yi - 0.5, yi + 0.5, color="#FFF3CD", zorder=0)
            ax.text(1.12, yi, "DEGREE ONLY: a single number\nper account (its tie count)\nreaches F1 %.3f, above all 23\nfeatures (%.3f); the MLP gets %.3f" % (
                ab[n]["sage"]["f1_mean"], ab["all 23 features"]["sage"]["f1_mean"], ab[n]["baseline"]["f1_mean"]),
                    fontsize=8, color="#7A5B00", va="center", fontweight="bold")
            ax.get_yticklabels()[list(y).index(yi)].set_fontweight("bold")
        if n.startswith("without temporal"):
            ax.text(1.12, yi, "largest drop when a group is\nremoved: MLP %.3f -> %.3f,\nGraphSAGE %.3f -> %.3f" % (
                ab["all 23 features"]["baseline"]["f1_mean"], ab[n]["baseline"]["f1_mean"],
                ab["all 23 features"]["sage"]["f1_mean"], ab[n]["sage"]["f1_mean"]),
                    fontsize=8, color=RED, va="center")
    ax.set_xlim(0, 1.6); ax.set_xticks(np.arange(0, 1.01, 0.2)); ax.set_xlabel("Test F1 (mean of 3 seeds, bars = std)")
    ax.set_title("Feature-group ablation: what each group contributes")
    ax.legend(frameon=False, loc="upper right"); ax.grid(axis="x", alpha=0.25)
    save(fig, "f08_ablation.png")


def f09():
    te = G["split"] == 2
    y, p = G["y"][te], S["p_sage"][te]
    bins = np.linspace(0, 1, 26)
    fig, ax = plt.subplots(figsize=(7.2, 4))
    ax.hist(p[y == 0], bins=bins, color=BLUE, alpha=0.8, label=f"Genuine ({(y == 0).sum()})")
    ax.hist(p[y == 1], bins=bins, color=RED, alpha=0.75, label=f"Fake ({(y == 1).sum()})")
    ax.set_yscale("log"); ax.axvline(THR, color="#333", ls="--", lw=1.2)
    ax.text(THR + 0.01, 250, f"threshold {THR:g}", fontsize=8.5)
    ax.set_xlabel("GraphSAGE fake probability"); ax.set_ylabel("Accounts (log scale)")
    ax.set_title("Score distribution on the test split: two well-separated groups")
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(0.9, 0.98)); ax.grid(axis="y", alpha=0.25)
    save(fig, "f09_score_distribution.png")


LAT = [("GET /api/health", 11.1, 20.1), ("GET /api/overview", 12.6, 26.9), ("GET /api/graph/summary", 8.3, 22.8),
       ("GET /api/accounts (25 rows)", 8.9, 23.1), ("GET /api/accounts/{id}", 10.6, 27.5),
       ("GET /api/accounts/{id}/neighbourhood", 13.8, 28.4), ("GET /api/clusters", 15.0, 23.2),
       ("GET /api/queue", 6.7, 22.4), ("GET /api/models", 16.0, 24.3), ("GET /api/models/scalability", 3.0, 27.7)]


def f10():
    fig, ax = plt.subplots(figsize=(8, 4.4))
    y = np.arange(len(LAT))[::-1]
    h = 0.38
    ax.barh(y + h / 2, [l[1] for l in LAT], h, color=TEAL, label="median")
    ax.barh(y - h / 2, [l[2] for l in LAT], h, color=ORANGE, label="95th percentile")
    for yi, l in zip(y, LAT):
        ax.text(l[1] + 0.4, yi + h / 2, f"{l[1]:.1f}", va="center", fontsize=8)
        ax.text(l[2] + 0.4, yi - h / 2, f"{l[2]:.1f}", va="center", fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels([l[0] for l in LAT], fontsize=8.5)
    ax.set_xlim(0, 40); ax.set_xlabel("Response time (ms), 20 requests per endpoint, 127.0.0.1")
    ax.set_title("API latency (login with bcrypt: 233 ms, not shown)")
    ax.legend(frameon=False, loc="upper right"); ax.grid(axis="x", alpha=0.25)
    save(fig, "f10_api_latency.png")


def f11():
    base = mean("baseline", "f1")
    gains = {m: (mean(m, "f1") - base) * 100 for m in ("gcn", "gat", "sage")}
    fig, ax = plt.subplots(figsize=(6, 3.8))
    ms = list(gains)
    b = ax.bar([LEG[m] for m in ms], [gains[m] for m in ms], color=[COL[m] for m in ms], width=0.55)
    for bi, m in zip(b, ms):
        ax.text(bi.get_x() + bi.get_width() / 2, gains[m] + 0.3, f"+{gains[m]:.1f} pt\n(F1 {mean(m, 'f1'):.3f})", ha="center", fontsize=9)
    ax.set_ylim(0, 14); ax.set_ylabel("F1 gain over MLP baseline (points)")
    ax.set_title(f"What the graph adds (baseline F1 {base:.3f})")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "f11_graph_lift.png")


def f12():
    ea = EXTRA["error_analysis"]
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.9), gridspec_kw={"wspace": 0.38})
    ax = axs[0]
    kinds = ["botnet member", "lone spammer"]
    x = np.arange(2)
    n = [ea["by_kind"][k]["n"] for k in kinds]
    ax.bar(x - 0.2, [ea["by_kind"][k]["baseline_caught"] for k in kinds], 0.38, color=GREY, label="caught by MLP baseline")
    ax.bar(x + 0.2, [ea["by_kind"][k]["sage_caught"] for k in kinds], 0.38, color=TEAL, label="caught by GraphSAGE")
    for xi, k, nn in zip(x, kinds, n):
        ax.text(xi - 0.2, ea["by_kind"][k]["baseline_caught"] + 1, str(ea["by_kind"][k]["baseline_caught"]), ha="center", fontsize=8.5)
        ax.text(xi + 0.2, ea["by_kind"][k]["sage_caught"] + 1, str(ea["by_kind"][k]["sage_caught"]), ha="center", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels([f"{k}\n(n={nn} in test)" for k, nn in zip(kinds, n)], fontsize=8.5)
    ax.set_ylim(0, max(n) * 1.3); ax.set_ylabel("Fake test accounts caught"); ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title("Fake accounts caught, by kind")
    ax = axs[1]
    vals = [ea["rescued_by_graph"], ea["lost_by_graph"], ea["missed_by_both"]]
    labs = ["rescued by\ngraph", "lost by\ngraph", "missed\nby both"]
    bars = ax.bar(range(3), vals, color=[TEAL, ORANGE, RED], width=0.55)
    for bi, v in zip(bars, vals):
        ax.text(bi.get_x() + bi.get_width() / 2, v + 0.4, str(v), ha="center", fontsize=9.5)
    ax.set_xticks(range(3)); ax.set_xticklabels(labs, fontsize=8); ax.set_ylim(0, max(vals) * 1.25 + 1)
    ax.set_ylabel("Fake test accounts"); ax.set_title(f"Graph vs no graph ({ea['test_fake']} fake in test)")
    ax.text(0.5, -0.3, "rescued = baseline missed, GraphSAGE caught\nlost = baseline caught, GraphSAGE missed", transform=ax.transAxes, ha="center", va="top", fontsize=7.5, color="#444")
    ax = axs[2]
    deg = ea["false_positive_degree"]
    missed = [m["degree"] for m in ea["missed"]]
    ax.scatter(range(len(deg)), deg, s=70, color=BLUE, label=f"false positives ({ea['false_positives']}), genuine accounts", zorder=3)
    ax.scatter(range(len(missed)), missed, s=70, marker="s", color=RED, label=f"missed fake accounts ({len(missed)})", zorder=3)
    ax.set_ylim(0, 54); ax.set_xlabel("Account (index within group)"); ax.set_ylabel("Ties (degree)")
    ax.set_title("Degree of the accounts GraphSAGE gets wrong")
    ax.legend(frameon=False, fontsize=8, loc="upper right"); ax.grid(alpha=0.25)
    ax.set_xticks(range(max(len(deg), len(missed))))
    fig.suptitle(f"Error analysis of the served GraphSAGE model at threshold {ea['threshold']:g}", y=1.04, fontsize=11, fontweight="bold")
    save(fig, "f12_error_analysis.png")


def f13():
    from ml import data as D

    X, y = G["X"], G["y"]
    sd = X.std(0)
    sd[sd < 1e-9] = 1
    d = (X[y == 1].mean(0) - X[y == 0].mean(0)) / sd
    names = list(D.FEATURES)
    groups = ["Profile metadata", "Posting behaviour", "Temporal pattern", "Interaction frequency"]
    gc = {"Profile metadata": BLUE, "Posting behaviour": PURPLE, "Temporal pattern": ORANGE, "Interaction frequency": TEAL}
    order = []
    for g in groups:
        idx = [i for i, n in enumerate(names) if D.FEATURE_GROUPS[n] == g]
        order += sorted(idx, key=lambda i: -abs(d[i]))
    fig, ax = plt.subplots(figsize=(8, 7))
    yy = np.arange(len(order))[::-1]
    ax.barh(yy, [d[i] for i in order], color=[gc[D.FEATURE_GROUPS[names[i]]] for i in order])
    for yi, i in zip(yy, order):
        ax.text(d[i] + (0.03 if d[i] >= 0 else -0.03), yi, f"{d[i]:+.2f}", va="center", ha="left" if d[i] >= 0 else "right", fontsize=7.5)
    ax.set_yticks(yy); ax.set_yticklabels([D.FEATURE_LABELS[names[i]] for i in order], fontsize=8.5)
    ax.axvline(0, color="#333", lw=0.8)
    ax.set_xlabel("(mean of fake - mean of genuine) / std, all 4,533 accounts")
    ax.set_title("How far each feature separates fake from genuine accounts")
    lim = np.abs(d).max() * 1.2
    ax.set_xlim(-lim, lim)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=gc[g], label=g) for g in groups], frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, fontsize=8.5)
    ax.grid(axis="x", alpha=0.25)
    save(fig, "f13_feature_means.png")


def f14():
    ei, real = G["edge_index"], G["is_real"]
    deg = np.bincount(ei.ravel(), minlength=len(real))
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"wspace": 0.25})
    bins = np.unique(np.logspace(0, np.log10(deg.max() + 1), 30).astype(int))
    for ax, log in ((axs[0], False), (axs[1], True)):
        ax.hist(deg[real], bins=bins, color=BLUE, alpha=0.8, label=f"real-topology accounts ({real.sum():,})")
        ax.hist(deg[~real], bins=bins, color=RED, alpha=0.75, label=f"injected accounts ({(~real).sum()})")
        ax.set_xscale("log"); ax.set_xlabel("Ties per account (log scale)")
        if log:
            ax.set_yscale("log"); ax.set_title("Same, log counts")
        else:
            ax.set_ylabel("Accounts"); ax.set_title("Degree distribution")
        ax.grid(alpha=0.25)
    axs[0].legend(frameon=False, fontsize=8.5, loc="upper left")
    axs[0].text(0.98, 0.55, f"median degree\nreal {np.median(deg[real]):.0f}\ninjected {np.median(deg[~real]):.0f}", transform=axs[0].transAxes,
                ha="right", fontsize=8.5)
    save(fig, "f14_degree_distribution.png")


if __name__ == "__main__":
    for fn in (f01, f02, f03, f04, f05, f06, f09, f10, f11, f13, f14):
        fn()
    if EXTRA:
        for fn in (f07, f08, f12):
            fn()
    else:
        print("experiments/extra/metrics.json missing - f07, f08, f12 skipped")
