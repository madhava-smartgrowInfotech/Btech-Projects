"""
Result figures for the documents (matplotlib only, 150 dpi) -> docs/figures/*.png

    python scripts/make_figures.py [--exp exp01_custom_cnn_clahe] [--data_root <chest_xray>]

Reads experiments/<exp>/metrics.json and test_predictions.csv written by scripts/train_experiment.py,
and (for the preprocessing and Grad-CAM panels) the images in dataset_sample/ and the test split.
"""

import argparse
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib

matplotlib.use("Agg")
import cv2
import matplotlib.pyplot as plt
import numpy as np

OUT = os.path.join(ROOT, "docs", "figures")
os.makedirs(OUT, exist_ok=True)
NAVY, BLUE, ORANGE, GREEN, PURPLE, GOLD, SLATE = "#1B2A41", "#2A78D6", "#EB6834", "#1BAF7A", "#6B52D6", "#E8A317", "#475569"
CLASS_COLORS = {"Normal": GREEN, "Bacterial Pneumonia": ORANGE, "Viral Pneumonia": GOLD}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p)


def load_metrics(exp):
    return json.load(open(os.path.join(ROOT, "experiments", exp, "metrics.json")))


def fig_preprocessing():
    from model.preprocess import apply_clahe

    samples = [("Normal", "normal_pa.jpg"), ("Pneumonia (lobar)", "lobar_pneumonia.jpg")]
    fig, axes = plt.subplots(2, 4, figsize=(10, 5.4))
    for r, (title, f) in enumerate(samples):
        g = cv2.imread(os.path.join(ROOT, "dataset_sample", f), cv2.IMREAD_GRAYSCALE)
        small = cv2.resize(g, (224, 224), interpolation=cv2.INTER_AREA)
        enh = apply_clahe(small)
        blur = cv2.GaussianBlur(enh, (3, 3), 0)
        for c, (img, cap) in enumerate([(g, f"original {g.shape[1]}x{g.shape[0]}"), (small, "resize 224 x 224"), (enh, "CLAHE (clip 2.5, 8x8)"), (blur, "Gaussian 3x3 = model input")]):
            ax = axes[r, c]
            ax.imshow(img, cmap="gray", vmin=0, vmax=255)
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            ax.set_title(cap if r == 0 else "", fontsize=9, color=SLATE)
        axes[r, 0].set_ylabel(title, fontsize=10, color=NAVY)
    fig.tight_layout()
    save(fig, "preprocessing_steps.png")


def fig_dataset(exp):
    m = load_metrics(exp)["dataset"]
    names = ["Normal", "Bacterial", "Viral"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    x = np.arange(3)
    w = 0.26
    for i, (key, label, col) in enumerate((("train_by_class", f"train ({m['train']})", BLUE), ("validation_by_class", f"validation ({m['validation']})", GOLD), ("test_by_class", f"test ({m['test']})", GREEN))):
        vals = m[key]
        b = ax.bar(x + (i - 1) * w, vals, w, label=label, color=col)
        for rect, v in zip(b, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, v + 20, str(v), ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("images"); ax.set_title("Images per class and split (Kermany chest X-ray data)", fontsize=10, color=NAVY)
    ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, "dataset_distribution.png")


def fig_class_metrics(exp):
    t = load_metrics(exp)["test"]["per_class"]
    names = list(t)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    x = np.arange(len(names)); w = 0.26
    for i, (k, col) in enumerate((("precision", BLUE), ("recall", GREEN), ("f1", ORANGE))):
        vals = [t[n][k] for n in names]
        b = ax.bar(x + (i - 1) * w, vals, w, label=k, color=col)
        for rect, v in zip(b, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([n.replace(" Pneumonia", "\nPneumonia") for n in names])
    ax.set_ylim(0, 1.1); ax.set_title("Per-class precision, recall and F1 on the test split", fontsize=10, color=NAVY)
    ax.legend(frameon=False, ncol=3, loc="upper center")
    fig.tight_layout()
    save(fig, "per_class_metrics.png")


def fig_threshold(exp):
    t = load_metrics(exp)["test"]["confidence_threshold_analysis"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    th = [r["threshold"] for r in t if r["accuracy_on_kept"] is not None]
    acc = [r["accuracy_on_kept"] for r in t if r["accuracy_on_kept"] is not None]
    cov = [r["coverage"] for r in t if r["accuracy_on_kept"] is not None]
    ax.plot(th, acc, "-o", color=BLUE, label="accuracy on kept scans")
    ax.plot(th, cov, "-s", color=ORANGE, label="coverage (share of scans kept)")
    for a, b, c in zip(th, acc, cov):
        ax.text(a, b + 0.02, f"{b:.2f}", ha="center", fontsize=8, color=BLUE)
        ax.text(a, c - 0.07, f"{c:.2f}", ha="center", fontsize=8, color=ORANGE)
    ax.set_xlabel("minimum confidence required to auto-report"); ax.set_ylim(0, 1.1)
    ax.set_title("Confidence threshold: accuracy against coverage", fontsize=10, color=NAVY)
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    save(fig, "confidence_threshold.png")


def fig_decision_sweep(exp):
    s = load_metrics(exp)["test"]["pneumonia_decision_threshold_sweep"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    th = [r["threshold"] for r in s]
    ax.plot(th, [r["sensitivity"] for r in s], "-o", color=GREEN, label="sensitivity")
    ax.plot(th, [r["specificity"] for r in s], "-s", color=PURPLE, label="specificity")
    ax.plot(th, [r["accuracy"] for r in s], "-^", color=BLUE, label="accuracy")
    ax.axvline(0.5, color="grey", ls=":", lw=1)
    ax.set_xlabel("pneumonia score threshold on 1 - P(Normal)"); ax.set_ylim(0, 1.05)
    ax.set_title("Normal vs pneumonia: decision-threshold sweep", fontsize=10, color=NAVY)
    ax.legend(frameon=False, loc="lower center", ncol=3)
    fig.tight_layout()
    save(fig, "decision_threshold_sweep.png")


def fig_ablation(exps):
    rows = []
    for e, label in exps:
        p = os.path.join(ROOT, "experiments", e, "metrics.json")
        if os.path.exists(p):
            m = json.load(open(p))
            b = m["test"]["binary_normal_vs_pneumonia"]
            rows.append((label, m["test"]["accuracy"], m["test"]["macro_f1"], b["sensitivity"], b["specificity"]))
    if len(rows) < 2:
        return
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    x = np.arange(len(rows)); w = 0.2
    for i, (name, col) in enumerate((("3-class accuracy", BLUE), ("macro F1", ORANGE), ("sensitivity", GREEN), ("specificity", PURPLE))):
        vals = [r[i + 1] for r in rows]
        b = ax.bar(x + (i - 1.5) * w, vals, w, label=name, color=col)
        for rect, v in zip(b, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=7.5)
    ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows]); ax.set_ylim(0, 1.12)
    ax.set_title("Experiment comparison on the same 624 test images", fontsize=10, color=NAVY)
    ax.legend(frameon=False, ncol=4, loc="upper center", fontsize=8)
    fig.tight_layout()
    save(fig, "experiment_comparison.png")


def fig_gradcam(exp, data_root):
    """Grad-CAM panel from the deployed model on correctly and wrongly classified test images."""
    from app import get_model
    import app as flask_app
    from model.gradcam import make_gradcam_heatmap, overlay_heatmap
    from model.preprocess import load_and_preprocess_image, preprocess_for_display

    rows = list(csv.DictReader(open(os.path.join(ROOT, "experiments", exp, "test_predictions.csv"))))
    model = get_model()
    names = ["Normal", "Bacterial Pneumonia", "Viral Pneumonia"]
    picks = []
    for cls in names:  # highest-confidence correct example
        ok = [r for r in rows if r["true"] == cls and r["pred"] == cls]
        ok.sort(key=lambda r: -float(r["confidence"]))
        if ok:
            picks.append(("correct", ok[0]))
    wrong = [r for r in rows if r["true"] != r["pred"]]
    wrong.sort(key=lambda r: -float(r["confidence"]))
    if wrong:
        picks.append(("wrong", wrong[0]))
    fig, axes = plt.subplots(2, len(picks), figsize=(3.0 * len(picks), 6.3))
    for c, (kind, r) in enumerate(picks):
        path = os.path.join(data_root, "test", r["file"].split("\\")[-2] if "\\" in r["file"] else r["file"].split("/")[-2], os.path.basename(r["file"]))
        batch = np.expand_dims(load_and_preprocess_image(path), 0)
        disp = preprocess_for_display(path)
        probs = model.predict(batch, verbose=0)[0]
        heat, _ = make_gradcam_heatmap(batch, model, flask_app._last_conv_layer, pred_index=int(np.argmax(probs)))
        axes[0, c].imshow(disp)
        axes[1, c].imshow(overlay_heatmap(disp, heat))
        for ax in axes[:, c]:
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
        axes[0, c].set_title(f"true: {r['true'].replace(' Pneumonia', '')}\n({'correct' if kind == 'correct' else 'misclassified'})", fontsize=9, color=NAVY if kind == "correct" else ORANGE)
        axes[1, c].set_title(f"pred: {r['pred'].replace(' Pneumonia', '')}  {float(r['confidence']):.2f}", fontsize=9, color=SLATE)
    axes[0, 0].set_ylabel("preprocessed input", fontsize=9)
    axes[1, 0].set_ylabel("Grad-CAM overlay", fontsize=9)
    fig.tight_layout()
    save(fig, "gradcam_examples.png")


def copy_exp_figures():
    """Training curves and confusion matrices written by train_experiment.py, copied next to the other figures."""
    import shutil

    for e in sorted(os.listdir(os.path.join(ROOT, "experiments"))):
        d = os.path.join(ROOT, "experiments", e)
        if not os.path.isdir(d):
            continue
        for src, dst in (("training_curves.png", f"training_curves_{e[:5]}.png"), ("confusion_matrix.png", f"confusion_matrix_{e[:5]}.png")):
            if os.path.exists(os.path.join(d, src)):
                shutil.copyfile(os.path.join(d, src), os.path.join(OUT, dst))
                print("copied", dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="exp02_custom_cnn_tuned")
    ap.add_argument("--data_root", default=None)
    ap.add_argument("--compare", nargs="*", default=["exp01_custom_cnn_clahe:Baseline defaults", "exp02_custom_cnn_tuned:Tuned (deployed)", "exp05_custom_cnn_noclahe:Tuned, no CLAHE", "exp04_mobilenetv3small:MobileNetV3Small"])
    a = ap.parse_args()
    fig_preprocessing()
    copy_exp_figures()
    p = os.path.join(ROOT, "experiments", a.exp, "metrics.json")
    if os.path.exists(p):
        fig_dataset(a.exp); fig_class_metrics(a.exp); fig_threshold(a.exp); fig_decision_sweep(a.exp)
        fig_ablation([tuple(c.split(":", 1)) for c in a.compare])
        if a.data_root:
            fig_gradcam(a.exp, a.data_root)


if __name__ == "__main__":
    main()
