"""Charts for the documents, drawn from the measured JSON files (docs/figures/*.png, 150 dpi).

    set PYTHONHASHSEED=0 && python scripts/docs_build/make_figures.py
(PYTHONHASHSEED=0 is what run.bat uses; it fixes the heuristic's jitter for the confidence-vs-correctness chart.)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments" / "plantdoc"
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
M = json.loads((EXP / "metrics.json").read_text())
LAT = json.loads((EXP / "latency.json").read_text())
NAVY, GREEN, ORANGE, GREY, PURPLE, TEAL, RED, BLUE = "#1F3A5F", "#2F8F4E", "#D9772F", "#8A97A8", "#6B5BD2", "#14907F", "#B03A2E", "#2B6CB0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def short(n):
    return (n.replace("_leaf", "").replace("_Leaf", "").replace("Tomato_", "Tom. ").replace("Potato_", "Pot. ").replace("Corn_", "Corn ").replace("Apple_", "Apple ")
            .replace("Bell_pepper", "Pepper").replace("_", " ").replace("two spotted spider mites", "spider mites").replace("Squash Powdery mildew", "Squash mildew")
            .replace("Strawberry", "Strawb.").replace("Soyabean", "Soybean").strip() or n)


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def f01():
    h, c, mb, bl = M["heuristic"], M["cnn"], M["mobilenet"], M["baseline"]
    rows = [("Shipped heuristic\n(crop chosen)", h["test_crop_hint"]["accuracy"]["mean"], h["test_crop_hint"]["macro_f1"]["mean"], GREY),
            ("Shipped heuristic\n(crop 'general')", h["test_general"]["accuracy"]["mean"], h["test_general"]["macro_f1"]["mean"], GREY),
            ("Logistic regression\n(colour/texture)", bl["logistic_regression"]["accuracy"], bl["logistic_regression"]["macro_f1"], TEAL),
            ("Compact CNN of\ntrain.py (3 seeds)", c["accuracy"]["mean"], c["macro_f1"]["mean"], ORANGE),
            ("Random forest\n(colour/texture)", bl["random_forest"]["accuracy"], bl["random_forest"]["macro_f1"], TEAL),
            ("MobileNetV2\nhead only", mb["head_only_accuracy"]["mean"], mb["head_only_macro_f1"]["mean"], PURPLE),
            ("MobileNetV2\nfine-tuned", mb["accuracy"]["mean"], mb["macro_f1"]["mean"], PURPLE)]
    fig, ax = plt.subplots(figsize=(10.0, 4.2))
    x = np.arange(len(rows))
    ax.bar(x - 0.19, [r[1] * 100 for r in rows], 0.38, color=[r[3] for r in rows], label="Accuracy")
    ax.bar(x + 0.19, [r[2] * 100 for r in rows], 0.38, color=[r[3] for r in rows], alpha=0.55, label="Macro-F1 x 100")
    for i, r in enumerate(rows):
        ax.text(i - 0.19, r[1] * 100 + 0.8, f"{r[1] * 100:.1f}", ha="center", fontsize=7.5)
        ax.text(i + 0.19, r[2] * 100 + 0.8, f"{r[2] * 100:.1f}", ha="center", fontsize=7.5)
    ax.axhline(h["chance_general"] * 100, color=RED, ls="--", lw=1)
    ax.text(-0.45, h["chance_general"] * 100 - 2.2, "chance, 38 classes (2.6)", color=RED, fontsize=7.5, ha="left")
    ax.axhline(h["majority_class_test"] * 100, color=NAVY, ls=":", lw=1)
    ax.text(2.6, h["majority_class_test"] * 100 + 1.0, "majority class (5.1)", color=NAVY, fontsize=7.5, ha="left")
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in rows], fontsize=8)
    ax.set_ylabel("percent on the 236 PlantDoc test photos")
    ax.set_ylim(0, 62)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Test accuracy and macro-F1 of every engine measured", fontsize=10, color=NAVY)
    save(fig, "f01_model_comparison.png")


def f02():
    b = M["mobilenet"]["first_run"]
    names, cm = b["classes"], np.array(b["confusion"])
    keep = [i for i in range(len(names)) if cm[i].sum() > 0]
    cm = cm[np.ix_(keep, keep)]
    labels = [short(names[i]) for i in keep]
    norm = cm / cm.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(8.0, 7.2))
    im = ax.imshow(norm, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=6.5)
    ax.set_yticklabels(labels, fontsize=6.5)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j]:
                ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=6, color="white" if norm[i, j] > 0.55 else NAVY)
    ax.set_xlabel("predicted class")
    ax.set_ylabel("true class")
    ax.set_title("MobileNetV2 (fine-tuned, seed 42): confusion matrix on the 236 test photos", fontsize=9.5, color=NAVY)
    fig.colorbar(im, fraction=0.035, pad=0.02, label="share of the true class")
    save(fig, "f02_confusion_matrix_mobilenet.png")


def f03():
    mb = M["mobilenet"]["first_run"]["per_class"]
    cn = M["cnn"]["first_run"]["per_class"]
    names = [n for n in mb if mb[n]["support"] > 0]
    names.sort(key=lambda n: mb[n]["f1"])
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    y = np.arange(len(names))
    ax.barh(y + 0.2, [mb[n]["f1"] for n in names], 0.38, color=PURPLE, label="MobileNetV2 (seed 42)")
    ax.barh(y - 0.2, [cn[n]["f1"] for n in names], 0.38, color=ORANGE, label="Compact CNN of train.py (seed 42)")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{short(n)} (n={mb[n]['support']})" for n in names], fontsize=7)
    ax.set_xlabel("F1 score on the test photos")
    ax.set_xlim(0, 1.02)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Per-class F1 on the PlantDoc test split", fontsize=10, color=NAVY)
    save(fig, "f03_per_class_f1.png")


def f04():
    hst = M["cnn"]["first_run"]["history"]
    ep = np.arange(1, len(hst["loss"]) + 1)
    fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 3.3))
    a.plot(ep, np.array(hst["accuracy"]) * 100, color=ORANGE, label="training accuracy")
    a.plot(ep, np.array(hst["val_accuracy"]) * 100, color=BLUE, label="validation accuracy (10 % of train)")
    a.set_xlabel("epoch")
    a.set_ylabel("percent")
    a.legend(frameon=False, fontsize=7.5)
    a.set_title("Accuracy", fontsize=9, color=NAVY)
    b.plot(ep, hst["loss"], color=ORANGE, label="training loss")
    b.plot(ep, hst["val_loss"], color=BLUE, label="validation loss")
    b.set_xlabel("epoch")
    b.legend(frameon=False, fontsize=7.5)
    b.set_title("Loss", fontsize=9, color=NAVY)
    fig.suptitle("Compact CNN of train.py, seed 42: the network under-fits", fontsize=10, color=NAVY)
    fig.tight_layout()
    save(fig, "f04_cnn_training_curves.png")


def f05():
    h, c, mb, bl = M["heuristic"]["test_crop_hint"], M["cnn"], M["mobilenet"], M["baseline"]
    rows = [("Shipped heuristic", h["healthy_recall"]["mean"], h["diseased_recall"]["mean"]),
            ("Compact CNN", c["healthy_recall"]["mean"], c["diseased_recall"]["mean"]),
            ("Random forest", None, bl["random_forest"]["diseased_recall"]),
            ("MobileNetV2", mb["healthy_recall"]["mean"], mb["diseased_recall"]["mean"])]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = np.arange(len(rows))
    hv = [r[1] * 100 if r[1] is not None else 0 for r in rows]
    ax.bar(x - 0.19, hv, 0.38, color=GREEN, label="healthy leaves called healthy")
    ax.bar(x + 0.19, [r[2] * 100 for r in rows], 0.38, color=RED, label="diseased leaves called diseased")
    for i, r in enumerate(rows):
        if r[1] is not None:
            ax.text(i - 0.19, r[1] * 100 + 1, f"{r[1] * 100:.0f}", ha="center", fontsize=8)
        ax.text(i + 0.19, r[2] * 100 + 1, f"{r[2] * 100:.0f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in rows], fontsize=8)
    ax.set_ylim(0, 112)
    ax.set_ylabel("recall, percent")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=1)
    ax.set_title("Healthy-versus-diseased recall (random forest: healthy recall not stored)", fontsize=8.5, color=NAVY)
    save(fig, "f05_healthy_vs_diseased.png")


def f06():
    """Share of test photos that get no answer per crop, with the crop's number of candidate classes."""
    sys.path.insert(0, str(ROOT / "agrivision"))
    import inference
    crops = {"apple": 4, "blueberry": 1, "cherry": 2, "corn": 4, "grape": 4, "peach": 2, "pepper": 2, "potato": 3, "raspberry": 1, "soybean": 1, "squash": 1, "strawberry": 2, "tomato": 10}
    assert all(len(inference._candidates(k)) == v for k, v in crops.items()), "candidate counts changed"
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ks = sorted(crops, key=lambda k: crops[k])
    colors = [RED if crops[k] < 3 else GREEN for k in ks]
    ax.bar(range(len(ks)), [crops[k] for k in ks], color=colors)
    for i, k in enumerate(ks):
        ax.text(i, crops[k] + 0.2, str(crops[k]), ha="center", fontsize=8)
    ax.axhline(3, color=NAVY, ls="--", lw=1)
    ax.text(len(ks) - 0.5, 3.3, "needs at least 3", fontsize=7.5, color=NAVY, ha="right")
    ax.set_xticks(range(len(ks)))
    ax.set_xticklabels(ks, rotation=30, fontsize=8)
    ax.set_ylabel("candidate classes in the knowledge base")
    ax.set_title("Crops with fewer than 3 candidate classes make the heuristic fail (red)", fontsize=9.5, color=NAVY)
    save(fig, "f06_crop_candidates.png")


def f07():
    sys.path.insert(0, str(ROOT / "agrivision"))
    import inference
    from disease_db import CLASSES
    names = sorted(p.name for p in (ROOT / "datasets" / "plantdoc-images" / "train").iterdir() if p.is_dir())
    canon = [inference.PLANTDOC_MAP[n] for n in names]
    crop_hint = {"Apple": "apple", "Bell": "pepper", "Blueberry": "blueberry", "Cherry": "cherry", "Corn": "corn", "Peach": "peach", "Potato": "potato", "Raspberry": "raspberry",
                 "Soyabean": "soybean", "Squash": "squash", "Strawberry": "strawberry", "Tomato": "tomato", "grape": "grape"}
    conf, ok, sums = [], [], []
    for ci, n in enumerate(names):
        folder = ROOT / "datasets" / "plantdoc-images" / "test" / n
        if not folder.exists():
            continue
        hint = crop_hint[n.split("_")[0]]
        if len(inference._candidates(hint)) < 3:
            continue
        for f in sorted(folder.iterdir()):
            try:
                out = inference.predict(f.read_bytes(), hint)
            except Exception:
                continue
            conf.append(out["top3"][0][1])
            ok.append(out["predicted"] == canon[ci])
            sums.append(sum(p for _, p in out["top3"]))
    conf, ok, sums = np.array(conf), np.array(ok), np.array(sums)
    bins = [0.62, 0.8, 0.9, 0.95, 1.0]
    fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 3.3))
    acc, cnt = [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf >= lo) & (conf < hi + (1e-9 if hi == 1.0 else 0))
        cnt.append(int(m.sum()))
        acc.append(ok[m].mean() * 100 if m.any() else 0)
    labels = [f"{lo:.2f}-{hi:.2f}\n(n={c})" for (lo, hi), c in zip(zip(bins[:-1], bins[1:]), cnt)]
    a.bar(range(len(acc)), acc, color=ORANGE)
    for i, v in enumerate(acc):
        a.text(i, v + 0.5, f"{v:.0f}", ha="center", fontsize=8)
    a.set_xticks(range(len(acc)))
    a.set_xticklabels(labels, fontsize=7.5)
    a.set_ylabel("top-1 correct, percent")
    a.set_xlabel("confidence shown to the user")
    a.set_title("Confidence does not predict correctness", fontsize=9, color=NAVY)
    b.hist(sums * 100, bins=14, color=TEAL)
    b.axvline(100, color=RED, ls="--", lw=1)
    b.set_xlabel("sum of the three shown scores, percent")
    b.set_ylabel("photos")
    b.set_title("Top-3 scores add up to more than 100 %", fontsize=9, color=NAVY)
    fig.tight_layout()
    save(fig, "f07_heuristic_confidence.png")
    json.dump({"n": int(len(conf)), "acc_by_bin": acc, "count_by_bin": cnt, "share_sum_over_102": float((sums > 1.02).mean()), "max_sum": float(sums.max()),
               "mean_conf": float(conf.mean())}, open(EXP / "heuristic_confidence.json", "w"), indent=1)


def f08():
    keys = [("detect (upload + diagnose)", LAT["detect_client_ms"]), ("dashboard", LAT["get_dashboard_ms"]), ("history (20 rows)", LAT["get_history_ms"]),
            ("analytics", LAT["get_analytics_ms"]), ("disease guide (38 cards)", LAT["get_diseases_ms"]), ("health", LAT["get_health_ms"])]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    y = np.arange(len(keys))
    ax.barh(y + 0.19, [k[1]["median"] for k in keys], 0.38, color=GREEN, label="median")
    ax.barh(y - 0.19, [k[1]["p95"] for k in keys], 0.38, color=ORANGE, label="95th percentile")
    for i, k in enumerate(keys):
        ax.text(k[1]["median"] + 1, i + 0.19, f"{k[1]['median']:.0f}", va="center", fontsize=7.5)
        ax.text(k[1]["p95"] + 1, i - 0.19, f"{k[1]['p95']:.0f}", va="center", fontsize=7.5)
    ax.set_yticks(y)
    ax.set_yticklabels([k[0] for k in keys], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("milliseconds (client round trip on 127.0.0.1)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("API response time (detect: 100 real photos; others: 40 calls)", fontsize=9.5, color=NAVY)
    save(fig, "f08_api_latency.png")


def f09():
    d = M["dataset"]
    names = d["classes"]
    tr = [d["counts"]["train"][n] for n in names]
    te = [d["counts"]["test"][n] for n in names]
    order = np.argsort(tr)
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    y = np.arange(len(names))
    ax.barh(y + 0.2, [tr[i] for i in order], 0.38, color=GREEN, label="train")
    ax.barh(y - 0.2, [te[i] for i in order], 0.38, color=ORANGE, label="test")
    ax.set_yticks(y)
    ax.set_yticklabels([short(names[i]) for i in order], fontsize=7)
    ax.set_xlabel("images")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("PlantDoc class sizes (28 train folders, 27 test folders)", fontsize=10, color=NAVY)
    save(fig, "f09_class_distribution.png")


def f10():
    c, mb = M["cnn"], M["mobilenet"]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for k, (name, blk, col) in enumerate([("Compact CNN", c, ORANGE), ("MobileNetV2", mb, PURPLE)]):
        v = np.array(blk["accuracy"]["values"]) * 100
        ax.scatter([k] * len(v), v, color=col, s=40, zorder=3)
        ax.hlines(v.mean(), k - 0.25, k + 0.25, color=col, lw=2)
        ax.text(k + 0.3, v.mean(), f"mean {v.mean():.1f} ± {v.std():.1f}", va="center", fontsize=8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Compact CNN (seeds 42, 43, 44)", "MobileNetV2 (seeds 42, 43, 44)"], fontsize=8)
    ax.set_ylabel("test accuracy, percent")
    ax.set_xlim(-0.5, 1.9)
    ax.set_title("Seed-to-seed variation of test accuracy", fontsize=9.5, color=NAVY)
    save(fig, "f10_seed_variation.png")


if __name__ == "__main__":
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10):
        fn()
