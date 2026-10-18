"""Result figures for the SignSpeak documents, drawn from models/*, docs/metrics/metrics.json and real dataset photos.

Run with the project venv (TensorFlow 2.15; needs the trained model for the failure-case figure):
    .venv\\Scripts\\python scripts\\docs_build\\make_figures.py
Writes PNGs (150 dpi) to docs/figures/ and docs/metrics/failure_cases.json.
"""

from __future__ import annotations

import tensorflow as tf  # noqa: F401  (before scikit-learn on Windows)

import json
import random
import sys
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sign_language_app import config, dataset  # noqa: E402
from sign_language_app.preprocessing import normalize_for_model, reduce_noise, segment_hand, segment_threshold  # noqa: E402

OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
M = json.loads((ROOT / "docs" / "metrics" / "metrics.json").read_text(encoding="utf-8"))
HIST = json.loads(config.HISTORY_PATH.read_text(encoding="utf-8"))
CM = json.loads((config.MODELS_DIR / "confusion_matrix.json").read_text(encoding="utf-8"))
LABELS = CM["labels"]
ARCHIVE = ROOT / "archive" / "asl_alphabet_train" / "asl_alphabet_train"

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#5B6B7F"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.titleweight": "bold", "axes.titlesize": 11, "axes.labelsize": 10})


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def training_curves():
    ep = np.arange(1, len(HIST["accuracy"]) + 1)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].plot(ep, HIST["accuracy"], color=BLUE, lw=2, label="training")
    ax[0].plot(ep, HIST["val_accuracy"], color=ORANGE, lw=2, label="validation")
    ax[0].set(xlabel="epoch", ylabel="accuracy", title="Accuracy per epoch")
    ax[0].legend(frameon=False)
    ax[1].plot(ep, HIST["loss"], color=BLUE, lw=2, label="training")
    ax[1].plot(ep, HIST["val_loss"], color=ORANGE, lw=2, label="validation")
    ax[1].set(xlabel="epoch", ylabel="categorical cross-entropy", title="Loss per epoch")
    ax[1].legend(frameon=False)
    fig.tight_layout()
    save(fig, "f01_training_curves.png")


def per_class():
    f1 = M["test_split"]["per_class_f1"]
    un = M["unseen_archive"]["per_class_accuracy"]
    x = np.arange(len(LABELS))
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.bar(x - 0.2, [f1[l] for l in LABELS], 0.4, color=BLUE, label="F1, held-out test split (n = 1,088)")
    ax.bar(x + 0.2, [un[l] for l in LABELS], 0.4, color=TEAL, label="accuracy, other archive photos (n = 2,900)")
    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, rotation=60, fontsize=8)
    ax.set_ylim(0.4, 1.12)
    ax.set(ylabel="score", title="Per-class performance")
    ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=8)
    fig.tight_layout()
    save(fig, "f02_per_class.png")


def confusion():
    cm = np.array(CM["matrix"], dtype=float)
    norm = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(LABELS)))
    ax.set_yticks(range(len(LABELS)))
    ax.set_xticklabels(LABELS, rotation=90, fontsize=7)
    ax.set_yticklabels(LABELS, fontsize=7)
    ax.set(xlabel="predicted class", ylabel="true class", title="Confusion matrix, test split (row-normalised)")
    ax.grid(False)
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            if cm[i, j] > 0 and (i != j or norm[i, j] < 0.85):
                ax.text(j, i, int(cm[i, j]), ha="center", va="center", fontsize=5.2, color="white" if norm[i, j] > 0.55 else "#223")
    fig.colorbar(im, fraction=0.046, pad=0.02)
    fig.tight_layout()
    save(fig, "f03_confusion_matrix.png")
    pairs = []
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            if i != j and cm[i, j] > 0:
                pairs.append((int(cm[i, j]), LABELS[i], LABELS[j]))
    pairs.sort(reverse=True)
    top = pairs[:10]
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.barh([f"{a} -> {b}" for _, a, b in top][::-1], [n for n, _, _ in top][::-1], color=ORANGE)
    ax.set(xlabel="test images", title="Ten most frequent confusions (true -> predicted)")
    fig.tight_layout()
    save(fig, "f04_top_confusions.png")
    json.dump([{"count": n, "true": a, "predicted": b} for n, a, b in pairs[:15]], open(ROOT / "docs" / "metrics" / "top_confusions.json", "w"), indent=1)


def threshold():
    rows = M["threshold_analysis"]
    t = [r["threshold"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(t, [r["coverage"] for r in rows], "-o", color=BLUE, lw=2, label="share of frames accepted")
    ax.plot(t, [r["accuracy_on_accepted"] for r in rows], "-s", color=TEAL, lw=2, label="accuracy on accepted frames")
    ax.axvline(0.75, color=ORANGE, ls="--", lw=1.5)
    ax.text(0.755, 0.34, "deployed\nthreshold 0.75", color=ORANGE, fontsize=8.5)
    ax.set(xlabel="confidence threshold", ylabel="fraction", ylim=(0.25, 1.03), title="Confidence threshold trade-off (test split)")
    ax.legend(frameon=False, loc="lower left", fontsize=8.5)
    fig.tight_layout()
    save(fig, "f05_threshold.png")


def robustness():
    r = M["robustness"]["accuracy"]
    names = list(r)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    cols = [GREY if n == "clean" else (ORANGE if r[n] < r["clean"] - 0.05 else BLUE) for n in names]
    ax.bar(range(len(names)), [r[n] for n in names], color=cols)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=28, ha="right", fontsize=8.5)
    for i, n in enumerate(names):
        ax.text(i, r[n] + 0.01, f"{r[n]*100:.1f}", ha="center", fontsize=8)
    ax.set(ylim=(0.4, 0.95), ylabel="accuracy", title=f"Robustness to input changes (n = {M['robustness']['n']} photos)")
    fig.tight_layout()
    save(fig, "f06_robustness.png")


def latency():
    L = M["latency"]
    stages = [("JPEG decode\n960x540", L["jpeg_decode_960x540"]["median_ms"], BLUE),
              ("ROI + segment\n+ normalise", L["roi_crop_and_segmentation_and_normalisation"]["median_ms"], TEAL),
              ("CNN forward\n(model.predict)", L["cnn_forward_batch1"]["median_ms"], PURPLE),
              ("Server total\nper frame", L["server_side_total_per_frame"]["median_ms"], NAVY),
              ("HTTP round trip\n(localhost)", L["http_recognize_frame_round_trip"]["median_ms"], ORANGE)]
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax.bar(range(len(stages)), [s[1] for s in stages], color=[s[2] for s in stages])
    for i, s in enumerate(stages):
        ax.text(i, s[1] + 1, f"{s[1]:.1f} ms", ha="center", fontsize=8.5)
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels([s[0] for s in stages], fontsize=8.5)
    ax.set(ylabel="median milliseconds", title="Per-frame latency (CPU only, 300 frames)", ylim=(0, 70))
    fig.tight_layout()
    save(fig, "f07_latency.png")


def split_and_counts():
    d = M["dataset"]
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.2), gridspec_kw={"width_ratios": [1, 2]})
    ax[0].bar(["train", "validation", "test"], [d["train"], d["validation"], d["test"]], color=[BLUE, TEAL, ORANGE])
    for i, v in enumerate([d["train"], d["validation"], d["test"]]):
        ax[0].text(i, v + 80, f"{v:,}", ha="center", fontsize=9)
    ax[0].set(ylabel="images", title="Stratified 70 / 15 / 15 split", ylim=(0, 6000))
    counts = d["per_class_in_data_folder"]
    ax[1].bar(range(len(counts)), list(counts.values()), color=BLUE)
    ax[1].set_xticks(range(len(counts)))
    ax[1].set_xticklabels(list(counts), rotation=60, fontsize=7.5)
    ax[1].set(ylabel="images", title="Images per class in data/ (250 each)", ylim=(0, 300))
    fig.tight_layout()
    save(fig, "f08_dataset_split.png")


def sample_grid():
    labels = [l for l in LABELS]
    cols = 8
    rows = int(np.ceil(len(labels) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(9, 1.2 * rows + 0.3))
    for ax in axes.ravel():
        ax.axis("off")
    for ax, l in zip(axes.ravel(), labels):
        p = sorted((ARCHIVE / l).glob("*.jpg"))[1200]
        ax.imshow(cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB))
        ax.set_title(l, fontsize=9, pad=2)
    fig.tight_layout(pad=0.4)
    save(fig, "f09_dataset_samples.png")


def pipeline_montage():
    picks = [("A", 800), ("L", 1500), ("W", 2100), ("Y", 400)]
    heads = ["1  ROI (raw)", "2  Grayscale", "3  Gaussian blur 7x7", "4  Otsu mask + morphology", "5  Model input 64x64"]
    fig, axes = plt.subplots(len(picks), 5, figsize=(9, 7.2))
    for r, (l, idx) in enumerate(picks):
        raw = cv2.imread(str(sorted((ARCHIVE / l).glob("*.jpg"))[idx]))
        roi = cv2.resize(raw, (300, 300))
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = reduce_noise(gray)
        mask = segment_hand(roi)
        small = normalize_for_model(mask)[..., 0]
        imgs = [cv2.cvtColor(roi, cv2.COLOR_BGR2RGB), gray, blur, mask, small]
        for c, im in enumerate(imgs):
            ax = axes[r, c]
            ax.imshow(im, cmap=None if c == 0 else "gray", vmin=0, vmax=255 if c in (1, 2, 3) else None if c == 0 else 1)
            ax.axis("off")
            if r == 0:
                ax.set_title(heads[c], fontsize=8.8)
        axes[r, 0].text(-0.08, 0.5, f"'{l}'", transform=axes[r, 0].transAxes, rotation=90, va="center", ha="right", fontsize=11, fontweight="bold")
    fig.tight_layout(pad=0.6)
    save(fig, "f10_preprocessing_stages.png")


def failure_cases():
    from tensorflow.keras.models import load_model
    model = load_model(config.MODEL_PATH)
    rng = random.Random(11)
    used = {(c, p.name) for c in LABELS for p in (config.DATA_DIR / c).glob("*.*")}
    pool = []
    for l in LABELS:
        files = [p for p in sorted((ARCHIVE / l).glob("*.jpg")) if (l, p.name) not in used]
        pool += [(l, p) for p in rng.sample(files, 40)]
    raws = [cv2.imread(str(p)) for _, p in pool]
    x = np.stack([normalize_for_model(segment_hand(r)) for r in raws])
    probs = model.predict(x, verbose=0, batch_size=128)
    pred = probs.argmax(1)
    wrong = [(i, LABELS[pred[i]], float(probs[i].max())) for i in range(len(pool)) if LABELS[pred[i]] != pool[i][0]]
    wrong.sort(key=lambda t: -t[2])
    pick = wrong[:6]
    right = [(i, LABELS[pred[i]], float(probs[i].max())) for i in range(len(pool)) if LABELS[pred[i]] == pool[i][0]]
    right.sort(key=lambda t: -t[2])
    pick_ok = right[:2]
    fig, axes = plt.subplots(2, 8, figsize=(10, 3.2))
    items = [("ok", t) for t in pick_ok] + [("bad", t) for t in pick]
    for k, (kind, (i, p, c)) in enumerate(items):
        for r, im in enumerate([cv2.cvtColor(raws[i], cv2.COLOR_BGR2RGB), segment_hand(raws[i])]):
            ax = axes[r, k]
            ax.imshow(im, cmap=None if r == 0 else "gray")
            ax.axis("off")
        axes[0, k].set_title(f"true {pool[i][0]}\npred {p}  {c*100:.0f}%", fontsize=8, color=TEAL if kind == "ok" else ORANGE)
    fig.tight_layout(pad=0.4)
    save(fig, "f11_failure_cases.png")
    json.dump({"sampled": len(pool), "wrong": len(wrong), "examples": [{"true": pool[i][0], "predicted": p, "confidence": round(c, 3), "file": pool[i][1].name} for i, p, c in pick]},
              open(ROOT / "docs" / "metrics" / "failure_cases.json", "w"), indent=1)


if __name__ == "__main__":
    training_curves()
    per_class()
    confusion()
    threshold()
    robustness()
    latency()
    split_and_counts()
    sample_grid()
    pipeline_montage()
    failure_cases()
