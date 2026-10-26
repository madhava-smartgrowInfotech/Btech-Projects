"""Result charts and sample grids -> docs/figures/ (matplotlib, 150 dpi), drawn from experiments/**/metrics.json.

    python -m scripts.docs.make_figures        (from 8.ProjectCode)
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from . import facts as F

OUT = F.FIGS
os.makedirs(OUT, exist_ok=True)
NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#5B6B7F"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
LAB = [k.capitalize() for k in F.BASIC]


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", p)


def class_distribution():
    d = F.DATA["class_counts"]
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    x = np.arange(7)
    ax.bar(x - 0.2, [d["train"][k] for k in F.BASIC], 0.4, color=BLUE, label="train (28,709)")
    ax.bar(x + 0.2, [d["test"][k] for k in F.BASIC], 0.4, color=ORANGE, label="test (7,178)")
    for i, k in enumerate(F.BASIC):
        ax.text(i - 0.2, d["train"][k] + 80, f"{d['train'][k]:,}", ha="center", fontsize=7)
        ax.text(i + 0.2, d["test"][k] + 80, f"{d['test'][k]:,}", ha="center", fontsize=7)
    ax.set_xticks(x, LAB)
    ax.set_ylabel("images")
    ax.set_title("FER2013 class distribution (disgust is 1.5 % of the training set)", fontsize=9)
    ax.legend(frameon=False)
    save(fig, "fig_class_distribution.png")


def confusion(res, name, title):
    cm = np.array(res["confusion_matrix"], float)
    nm = cm / cm.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    im = ax.imshow(nm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(7), LAB, rotation=40, ha="right")
    ax.set_yticks(range(7), LAB)
    for i in range(7):
        for j in range(7):
            ax.text(j, i, f"{int(cm[i, j])}\n{nm[i, j] * 100:.0f}%", ha="center", va="center", fontsize=6.4, color="white" if nm[i, j] > 0.5 else "black")
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title, fontsize=9)
    fig.colorbar(im, fraction=0.046, pad=0.03)
    save(fig, name)


def per_class_f1():
    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    x = np.arange(7)
    b = [F.BASE["per_class"][k]["f1"] for k in F.BASIC]
    n = [F.FIN["per_class"][k]["f1"] for k in F.BASIC]
    ax.bar(x - 0.2, b, 0.4, color=GREY, label=f"single-label baseline (acc {F.BASE['accuracy'] * 100:.1f} %)")
    ax.bar(x + 0.2, n, 0.4, color=TEAL, label=f"final multi-label model (acc {F.FIN['accuracy'] * 100:.1f} %)")
    for i in range(7):
        ax.text(i - 0.2, b[i] + 0.01, f"{b[i]:.2f}", ha="center", fontsize=7)
        ax.text(i + 0.2, n[i] + 0.01, f"{n[i]:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x, LAB)
    ax.set_ylim(0, 1)
    ax.set_ylabel("F1 on the FER2013 test set")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    save(fig, "fig_per_class_f1.png")


def ablation():
    if not F.ABL:
        return
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1))
    rows = [("real data only", "real_only", GREY), ("real + 200 synthetic\nper compound class", "synth", TEAL)]
    for ax, key, title in ((axs[0], "accuracy", "Test accuracy (7 basic emotions)"), (axs[1], "macro_f1", "Test macro-F1")):
        for i, (lab, pre, col) in enumerate(rows):
            v = F.abl_vals(pre, key)
            ax.bar(i, np.mean(v), 0.55, color=col, yerr=(np.std(v, ddof=1) if len(v) > 1 else 0), capsize=4)
            ax.scatter([i] * len(v), v, color="black", s=10, zorder=3)
            ax.text(i + 0.32, np.mean(v) + 0.004, f"{np.mean(v) * 100:.1f} %", ha="left", fontsize=8)
        ax.axhline(F.BASE[key], color=ORANGE, ls="--", lw=1)
        ax.text(1.45, F.BASE[key] + 0.006, "stage-1 baseline", color=ORANGE, fontsize=7, ha="right")
        ax.set_xticks([0, 1], [r[0] for r in rows], fontsize=8)
        ax.set_ylim(0.4, 0.66)
        ax.set_title(title + f"  (n = {len(F.abl_vals('real_only', key))} seeds)", fontsize=8.5)
    save(fig, "fig_ablation.png")


def synth_sweep():
    keys = [("real_only_s1", 0), ("synth50_s1", 50), ("synth_s1", 200), ("synth800_s1", 800)]
    pts = [(n, F.ABL[k]["accuracy"], F.ABL[k]["macro_f1"]) for k, n in keys if k in F.ABL]
    if len(pts) < 3:
        return
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.plot([p[0] for p in pts], [p[1] * 100 for p in pts], "o-", color=BLUE, label="accuracy")
    ax.plot([p[0] for p in pts], [p[2] * 100 for p in pts], "s-", color=PURPLE, label="macro-F1")
    for p in pts:
        ax.text(p[0], p[1] * 100 + 0.35, f"{p[1] * 100:.1f}", ha="center", fontsize=7)
        ax.text(p[0], p[2] * 100 - 0.9, f"{p[2] * 100:.1f}", ha="center", fontsize=7)
    ax.set_xlabel("synthetic images per compound class (seed 1)")
    ax.set_ylabel("FER2013 test score (%)")
    ax.set_ylim(48, 62)
    ax.legend(frameon=False)
    save(fig, "fig_synth_sweep.png")


def compound_threshold():
    fm = F.SYN["final_model"]
    th = list(fm.keys())
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
    ax = axs[0]
    ax.plot(th, [fm[t]["micro_f1"] for t in th], "o-", color=BLUE, label="micro-F1 (18 labels)")
    ax.plot(th, [fm[t]["compound_recall"] for t in th], "s-", color=ORANGE, label="compound recall")
    ax.set_xlabel("decision threshold")
    ax.set_ylim(0, 1.02)
    ax.set_title("Synthetic hold-out (1,100 faces, seed 12345)", fontsize=8.5)
    ax.legend(frameon=False, fontsize=7.5)
    ax = axs[1]
    names = ["final model\n(hold-out)", "real-only\ncontrol", "chance"]
    vals = [fm["0.5"]["compound_roc_auc_macro"], S_CTRL(), 0.5]
    ax.bar(range(3), vals, color=[TEAL, GREY, "#BBBBBB"])
    for i, v in enumerate(vals):
        ax.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=8)
    ax.set_xticks(range(3), names, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title("Compound ROC-AUC (macro, 11 classes)", fontsize=8.5)
    save(fig, "fig_compound_threshold.png")


def S_CTRL():
    return F.SYN.get("real_only_control", {}).get("compound_roc_auc_macro", 0.5)


def gan_fidelity():
    g = F.GAN
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.1))
    ax = axs[0]
    v = [g["basic"][k]["stage1_accuracy_on_generated"] * 100 for k in F.BASIC]
    ax.bar(range(7), v, color=TEAL)
    ax.axhline(100 / 7, color=ORANGE, ls="--", lw=1)
    ax.text(6.4, 100 / 7 + 2, "chance 14.3 %", color=ORANGE, fontsize=7, ha="right")
    for i, x in enumerate(v):
        ax.text(i, x + 1.5, f"{x:.0f}", ha="center", fontsize=7)
    ax.set_xticks(range(7), LAB, rotation=40, ha="right")
    ax.set_ylabel("% of 500 generated faces read as the\ncondition by the stage-1 classifier")
    ax.set_title("Does the generator obey a one-hot condition?", fontsize=8.5)
    ax = axs[1]
    cs = F.COMPOUND
    v2 = [g["compound"][k]["stage1_top1_in_pair"] * 100 for k in cs]
    ax.barh(range(11), v2, color=PURPLE)
    ax.axvline(g["chance_top1_in_pair"] * 100, color=ORANGE, ls="--", lw=1)
    ax.set_yticks(range(11), [c.replace("_", " ") for c in cs], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("% top-1 inside the pair")
    ax.set_title("Compound conditions (chance 28.6 %)", fontsize=8.5)
    save(fig, "fig_gan_fidelity.png")


def sample_grids():
    base = os.path.join(F.EXP, "gan_fidelity")
    items = [("grid_real_basic.png", "Real FER2013 training faces (rows: angry, disgust, fear, happy, sad, surprise, neutral)"),
             ("grid_generated_basic.png", "cEmoGAN output for the same seven one-hot conditions"),
             ("grid_generated_compound.png", "cEmoGAN output for the 11 compound conditions (rows in taxonomy order)")]
    for fn, cap in items:
        im = Image.open(os.path.join(base, fn))
        w, h = im.size
        fig, ax = plt.subplots(figsize=(6.0, 6.0 * h / w + 0.35))
        ax.imshow(im, cmap="gray", interpolation="nearest")
        ax.axis("off")
        ax.set_title(cap, fontsize=7.5)
        save(fig, fn.replace("grid_", "fig_grid_"))


def detection():
    d = F.DET
    sc = [1, 2, 3, 4, 6]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9))
    ax = axs[0]
    v = [d[f"haar_detection_rate_scale_{s}x"] * 100 for s in sc]
    ax.plot([s * 48 for s in sc], v, "o-", color=BLUE)
    for s, x in zip(sc, v):
        ax.text(s * 48, x + 3, f"{x:.0f} %", ha="center", fontsize=7.5)
    ax.set_xlabel("face image size fed to the Haar detector (px)")
    ax.set_ylabel("faces detected (%)")
    ax.set_ylim(0, 80)
    ax.set_title("Haar detection of FER2013 faces", fontsize=8.5)
    ax = axs[1]
    vals = [d["accuracy_direct_64px_on_same_images"] * 100, d["accuracy_via_haar_crop_on_detected"] * 100]
    ax.bar([0, 1], vals, color=[TEAL, ORANGE], width=0.5)
    for i, x in enumerate(vals):
        ax.text(i, x + 1, f"{x:.1f} %", ha="center", fontsize=8)
    ax.set_xticks([0, 1], ["direct 64x64\nresize", "product path\n(Haar crop)"], fontsize=8)
    ax.set_ylim(0, 80)
    ax.set_title(f"Accuracy on the same {d['detected_at_3x']} detected faces", fontsize=8.5)
    save(fig, "fig_detection.png")


def latency():
    if not F.APIM:
        return
    L = [l for l in F.APIM["latency"]]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    names = [l["label"].replace("POST ", "").replace("GET ", "").replace(" (", "\n(") for l in L]
    ax.barh(range(len(L)), [l["p50_ms"] for l in L], color=BLUE, label="p50")
    ax.barh(range(len(L)), [l["p95_ms"] - l["p50_ms"] for l in L], left=[l["p50_ms"] for l in L], color="#9DBCE3", label="to p95")
    ax.set_yticks(range(len(L)), names, fontsize=6.8)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlabel("milliseconds (log scale), 127.0.0.1")
    for i, l in enumerate(L):
        ax.text(l["p95_ms"] * 1.08, i, f"{l['p50_ms']:.1f} / {l['p95_ms']:.1f}", va="center", fontsize=6.8)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    save(fig, "fig_latency.png")


def loss_curves():
    fig, ax = plt.subplots(figsize=(5.2, 2.9))
    for k, col, lab in (("real_only_s1", GREY, "real only"), ("synth_s1", TEAL, "real + synthetic")):
        if k in F.ABL:
            h = F.ABL[k]["config"]["loss_history"]
            ax.plot(range(1, len(h) + 1), h, "o-", color=col, label=lab)
    ax.set_xlabel("epoch")
    ax.set_ylabel("mean BCE loss (18 outputs)")
    ax.legend(frameon=False)
    ax.set_title("Final-classifier training loss (seed 1)", fontsize=8.5)
    save(fig, "fig_loss_curves.png")


def main():
    class_distribution()
    confusion(F.FIN, "fig_confusion_final.png", "Final model - FER2013 test (7,178 images)")
    confusion(F.BASE, "fig_confusion_baseline.png", "Stage-1 baseline - FER2013 test")
    per_class_f1()
    ablation()
    synth_sweep()
    compound_threshold()
    gan_fidelity()
    sample_grids()
    detection()
    latency()
    loss_curves()


if __name__ == "__main__":
    main()
