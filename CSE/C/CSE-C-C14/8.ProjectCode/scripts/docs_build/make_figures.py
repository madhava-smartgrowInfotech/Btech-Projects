"""Charts for the VeriVision AI documents, drawn from experiments/cifake/metrics.json and logits.npz -> docs/figures/ (PNG, 150 dpi).

    python scripts/docs_build/make_figures.py
Every value plotted is read from the measured results; nothing is typed in.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
EXP = ROOT / "experiments" / "cifake"

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#8795A8", "#C0392B"
BR = ["a1", "a2", "b", "c"]
NAME = {"a1": "A1\nEffNet-B0", "a2": "A2\nEffNet-B0", "b": "B\nResNet50", "c": "C\nMobileNetV3", "ens": "Ensemble"}
COL = {"a1": BLUE, "a2": TEAL, "b": ORANGE, "c": PURPLE, "ens": NAVY}
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "font.size": 9})

M = json.load(open(EXP / "metrics.json", encoding="utf-8"))
L = np.load(EXP / "logits.npz", allow_pickle=True)
clean = M["clean"]


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def softmax_fake(z):
    z = np.asarray(z, dtype=np.float64)
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return (e / e.sum(1, keepdims=True))[:, 1]


def fused_clean():
    from app import ensemble as ens
    lg = {b: L[f"clean__{b}"] for b in BR}
    n = len(lg["a1"])
    out = np.zeros((n, 2))
    for i in range(n):
        out[i] = ens.ensemble_predict({b: [float(lg[b][i][0]), float(lg[b][i][1])] for b in BR})["fused_logits"]
    return out


def bars_labels(ax, bars, fmt="{:.3f}", dy=0.004, fs=7):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy, fmt.format(b.get_height()), ha="center", va="bottom", fontsize=fs)


def f01_dataset():
    c = json.load(open(ROOT / "docs" / "metrics" / "data_counts.json"))
    fig, ax = plt.subplots(figsize=(6.2, 3.1))
    splits = ["train", "val", "test"]
    x = np.arange(3)
    r = [c[f"{s}_real"] for s in splits]
    f = [c[f"{s}_fake"] for s in splits]
    b1 = ax.bar(x - 0.18, r, 0.36, color=TEAL, label="REAL (CIFAR-10 photographs)")
    b2 = ax.bar(x + 0.18, f, 0.36, color=ORANGE, label="AI_GENERATED (Stable Diffusion 1.4)")
    bars_labels(ax, list(b1) + list(b2), "{:.0f}", 30)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s}\n({'official train split' if s != 'test' else 'official test split'})" for s in splits])
    ax.set_ylabel("images")
    ax.set_title("Class-balanced CIFAKE subset used for training and evaluation")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f01_dataset_split.png")


def f02_models():
    keys = BR + ["ens"]
    ms = [clean["branches"][b] if b != "ens" else clean["ensemble"] for b in keys]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    w = 0.26
    x = np.arange(len(keys))
    for i, (k, lab, col) in enumerate((("accuracy", "Accuracy", BLUE), ("f1", "F1", TEAL), ("roc_auc", "ROC-AUC", ORANGE))):
        bars = ax.bar(x + (i - 1) * w, [m[k] for m in ms], w, color=col, label=lab)
        bars_labels(ax, bars, "{:.3f}", 0.003, 6.5)
    ax.set_xticks(x)
    ax.set_xticklabels([NAME[k] for k in keys])
    lo = min(m["accuracy"] for m in ms)
    ax.set_ylim(max(0.5, lo - 0.08), 1.02)
    ax.set_ylabel("score")
    ax.set_title(f"Held-out test, n = {M['n_test']} (single run, seed 42)")
    ax.legend(frameon=False, ncol=3, fontsize=8, loc="upper left")
    save(fig, "f02_branch_metrics.png")


def f03_confusion():
    cm = np.array(clean["ensemble"]["confusion_matrix"])
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.1))
    for ax, mat, title, fmt in ((axs[0], cm, "Counts", "{:d}"), (axs[1], cm / cm.sum(1, keepdims=True), "Row-normalised", "{:.3f}")):
        ax.imshow(mat, cmap="Blues", vmin=0)
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(["REAL", "AI_GEN"]); ax.set_yticklabels(["REAL", "AI_GEN"])
        ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(title)
        for i in range(2):
            for j in range(2):
                v = mat[i, j]
                ax.text(j, i, fmt.format(int(v) if fmt == "{:d}" else v), ha="center", va="center", fontsize=12, color="white" if v > mat.max() / 2 else "black")
        for s in ax.spines.values():
            s.set_visible(True)
    fig.suptitle("Ensemble confusion matrix on the held-out test subset", fontsize=10)
    save(fig, "f03_confusion_matrix.png")


def f04_training():
    H = M["histories"]
    fig, axs = plt.subplots(1, 3, figsize=(9.0, 2.9))
    for b in BR:
        h = H.get(b)
        if not h:
            continue
        ep = np.arange(1, len(h["val_acc"]) + 1)
        axs[0].plot(ep, h["train_loss"], "-o", ms=3, color=COL[b], label=NAME[b].split("\n")[0])
        axs[1].plot(ep, h["val_loss"], "-o", ms=3, color=COL[b])
        axs[2].plot(ep, h["val_acc"], "-o", ms=3, color=COL[b])
    for ax, t in zip(axs, ("Training loss", "Validation loss", "Validation accuracy")):
        ax.set_title(t, fontsize=9); ax.set_xlabel("epoch"); ax.grid(alpha=0.25)
    axs[0].legend(frameon=False, fontsize=7.5)
    fig.suptitle("Training history of the four routes (A2 and C use their own loss and augmentation; C uses focal loss, so its loss scale differs)", fontsize=8.5)
    fig.tight_layout()
    save(fig, "f04_training_curves.png")


def f05_roc():
    from sklearn.metrics import roc_curve
    y = L["clean__labels"]
    fused = fused_clean()
    fig, ax = plt.subplots(figsize=(4.6, 3.9))
    for b in BR:
        fpr, tpr, _ = roc_curve(y, softmax_fake(L[f"clean__{b}"]))
        ax.plot(fpr, tpr, color=COL[b], lw=1.2, label=f"{NAME[b].split(chr(10))[0]} (AUC {clean['branches'][b]['roc_auc']:.3f})")
    fpr, tpr, _ = roc_curve(y, softmax_fake(fused))
    ax.plot(fpr, tpr, color=NAVY, lw=2.2, label=f"Ensemble (AUC {clean['ensemble']['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], "--", color=GREY, lw=0.8)
    ax.set_xlabel("false-positive rate"); ax.set_ylabel("true-positive rate"); ax.set_title("ROC curves, held-out test")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    save(fig, "f05_roc.png")


def f06_ablation():
    V = clean["ensemble_variants"]
    names = [("full", "Deployed\n(weights + 2 gates)"), ("no_gates", "No gates"), ("gate1_only", "Gate 1\nonly"), ("gate2_only", "Gate 2\nonly"),
             ("equal_weights", "Equal\nweights"), ("prob_avg", "Probability\naveraging"), ("majority", "Majority\nvote")]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    x = np.arange(len(names))
    b1 = ax.bar(x - 0.2, [V[k]["accuracy"] for k, _ in names], 0.4, color=BLUE, label="Accuracy")
    b2 = ax.bar(x + 0.2, [V[k]["f1"] for k, _ in names], 0.4, color=TEAL, label="F1")
    bars_labels(ax, list(b1) + list(b2), "{:.3f}", 0.002, 6.2)
    lo = min(min(V[k]["accuracy"], V[k]["f1"]) for k, _ in names)
    ax.set_ylim(lo - 0.02, min(1.0, max(V[k]["accuracy"] for k, _ in names) + 0.02))
    ax.set_xticks(x); ax.set_xticklabels([n for _, n in names], fontsize=7.5)
    ax.set_title("Fusion-rule ablation on the held-out test subset")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    save(fig, "f06_fusion_ablation.png")


def f07_threshold():
    S = M["threshold_sweep"]
    t = [s["threshold"] for s in S]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    for k, lab, col in (("precision", "Precision", BLUE), ("recall", "Recall", TEAL), ("f1", "F1", ORANGE), ("accuracy", "Accuracy", GREY)):
        ax.plot(t, [s[k] for s in S], "-o", ms=3.5, color=col, label=lab)
    ax.axvline(0.5, color=NAVY, ls=":", lw=1)
    ax.text(0.505, ax.get_ylim()[0] + 0.01, "deployed 0.5", fontsize=7.5, color=NAVY)
    ax.set_xlabel("decision threshold on the fused fake probability"); ax.set_ylabel("score")
    ax.set_title("Threshold analysis of the ensemble"); ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.25)
    save(fig, "f07_threshold_sweep.png")


def f08_robustness():
    conds = ["clean_subset", "jpeg", "resize", "blur", "noise"]
    lab = ["Clean\n(1000-image\nsubset)", "JPEG\nq = 60", "Down-up\nresize x2", "Gaussian\nblur 5x5", "Noise\nsigma 6"]
    keys = BR + ["ens"]
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    w = 0.16
    x = np.arange(len(conds))
    for i, k in enumerate(keys):
        vals = [(M["robustness"][c]["ensemble"] if k == "ens" else M["robustness"][c]["branches"][k])["accuracy"] for c in conds]
        ax.bar(x + (i - 2) * w, vals, w, color=COL[k], label=NAME[k].split("\n")[0])
    ax.axhline(0.5, color=GREY, ls="--", lw=0.8); ax.text(len(conds) - 0.55, 0.51, "chance", fontsize=7, color=GREY)
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=8)
    ax.set_ylim(0.4, 1.12); ax.set_ylabel("accuracy")
    ax.set_title("Robustness to degradations (accuracy, same 1000 images in every condition)")
    ax.legend(frameon=False, ncol=5, fontsize=7.5, loc="upper right")
    save(fig, "f08_robustness.png")


def f09_xdomain():
    X = M.get("xdomain")
    if not X:
        return
    keys = BR + ["ens"]
    ms = [X["branches"][b] if b != "ens" else X["ensemble"] for b in keys]
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.1))
    axs[0].bar(range(5), [m["accuracy"] for m in ms], color=[COL[k] for k in keys])
    axs[0].axhline(0.5, color=GREY, ls="--", lw=0.8)
    for i, m in enumerate(ms):
        axs[0].text(i, m["accuracy"] + 0.01, f"{m['accuracy']:.3f}", ha="center", fontsize=7.5)
    axs[0].set_xticks(range(5)); axs[0].set_xticklabels([NAME[k].split("\n")[0] for k in keys], fontsize=8)
    axs[0].set_ylim(0, 1.05); axs[0].set_title("Accuracy on the cross-domain probe")
    cm_f = [m["confusion_matrix"] for m in ms]
    rr = [c[0][0] / max(sum(c[0]), 1) for c in cm_f]
    fr = [c[1][1] / max(sum(c[1]), 1) for c in cm_f]
    axs[1].bar(np.arange(5) - 0.2, rr, 0.4, color=TEAL, label="real images kept REAL")
    axs[1].bar(np.arange(5) + 0.2, fr, 0.4, color=ORANGE, label="AI images found")
    axs[1].set_xticks(range(5)); axs[1].set_xticklabels([NAME[k].split("\n")[0] for k in keys], fontsize=8)
    axs[1].set_ylim(0, 1.05); axs[1].set_title("Per-class recall"); axs[1].legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.suptitle(f"Cross-domain probe: {X['n']} full-resolution photographs and AI images, models trained on CIFAKE only", fontsize=9)
    fig.tight_layout()
    save(fig, "f09_cross_domain.png")


def f10_calibration():
    y = L["clean__labels"]
    p = softmax_fake(fused_clean())
    conf = np.maximum(p, 1 - p)
    pred = (p >= 0.5).astype(int)
    acc = (pred == y).astype(float)
    edges = np.linspace(0.5, 1.0, 11)
    xs, ys, ns = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.sum() >= 5:
            xs.append(conf[m].mean()); ys.append(acc[m].mean()); ns.append(int(m.sum()))
    fig, ax = plt.subplots(figsize=(4.4, 3.8))
    ax.plot([0.5, 1], [0.5, 1], "--", color=GREY, lw=0.9, label="perfect calibration")
    ax.plot(xs, ys, "-o", color=NAVY, label=f"ensemble (ECE {M['ece_ensemble']:.3f})")
    for a, b, n in zip(xs, ys, ns):
        ax.text(a, b - 0.025, str(n), fontsize=6.5, ha="center", color=GREY)
    ax.set_xlabel("confidence (winning-class probability)"); ax.set_ylabel("accuracy in the bin"); ax.set_title("Reliability diagram (bin sizes shown)")
    ax.legend(frameon=False, fontsize=8, loc="upper left"); ax.set_ylim(0.4, 1.02)
    save(fig, "f10_calibration.png")


def f11_margin():
    y = L["clean__labels"]
    z = fused_clean()
    margin = z[:, 1] - z[:, 0]
    wrong = np.argmax(z, 1) != y
    fig, ax = plt.subplots(figsize=(5.6, 3.1))
    bins = np.linspace(margin.min(), margin.max(), 40)
    ax.hist(margin[~wrong], bins=bins, color=TEAL, alpha=0.8, label=f"correct ({int((~wrong).sum())})")
    ax.hist(margin[wrong], bins=bins, color=RED, alpha=0.85, label=f"wrong ({int(wrong.sum())})")
    ax.axvline(0, color=NAVY, lw=1, ls=":")
    ax.set_xlabel("fused logit margin (fake minus real)"); ax.set_ylabel("images"); ax.set_title("Where the ensemble errs: small margins")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f11_margin_hist.png")


def f12_failures():
    from PIL import Image
    err = M["error_analysis"]
    y = L["clean__labels"]
    z = fused_clean()
    p = softmax_fake(z)
    paths = err["test_paths"]
    fp = err["false_positive_indices"][:6]
    fn = err["false_negative_indices"][:6]
    rows = [("REAL images called AI_GENERATED (false positives)", fp), ("AI_GENERATED images called REAL (false negatives)", fn)]
    fig, axs = plt.subplots(2, 6, figsize=(8.4, 3.5))
    for r, (title, idx) in enumerate(rows):
        for c in range(6):
            ax = axs[r, c]
            ax.axis("off")
            if c < len(idx):
                i = idx[c]
                with Image.open(paths[i]) as im:
                    ax.imshow(im.convert("RGB").resize((96, 96), Image.NEAREST))
                ax.set_title(f"P(fake) {p[i]:.2f}", fontsize=7.5)
        axs[r, 0].text(-0.1, 1.28, title, transform=axs[r, 0].transAxes, fontsize=8.5, fontweight="bold", color=NAVY)
    fig.tight_layout()
    save(fig, "f12_failure_cases.png")


def f13_branch_agree():
    A = M["branch_vs_ensemble_agreement"]
    fig, ax = plt.subplots(figsize=(4.8, 2.9))
    vals = [A[b] for b in BR]
    bars = ax.bar(range(4), vals, color=[COL[b] for b in BR])
    bars_labels(ax, bars, "{:.3f}", 0.002, 8)
    ax.set_xticks(range(4)); ax.set_xticklabels([NAME[b] for b in BR], fontsize=7.5)
    ax.set_ylim(max(0.5, min(vals) - 0.05), 1.01); ax.set_ylabel("agreement with the final label")
    ax.set_title(f"Route agrees with ensemble (all four unanimous in {M['unanimous_rate']*100:.1f}%)", fontsize=8.5)
    save(fig, "f13_route_agreement.png")


if __name__ == "__main__":
    for fn in (f01_dataset, f02_models, f03_confusion, f04_training, f05_roc, f06_ablation, f07_threshold, f08_robustness, f09_xdomain,
               f10_calibration, f11_margin, f12_failures, f13_branch_agree):
        fn()
