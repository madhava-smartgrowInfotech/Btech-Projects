"""Result charts for the CipherGuard Shield documents, drawn from experiments/**/metrics.json into docs/figures/ (PNG, 150 dpi).

    python scripts/docs_build/make_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments"
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, BLUE, TEAL, ORANGE, RED, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#C0392B", "#6B5BD2", "#8795A8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def J(*p):
    return json.loads((EXP.joinpath(*p)).read_text(encoding="utf-8"))


off, pap, sh, cry, pipe = J("unsw_nb15", "official", "metrics.json"), J("unsw_nb15", "paper_protocol", "metrics.json"), J("unsw_nb15", "shift", "metrics.json"), J("crypto", "metrics.json"), J("pipeline", "metrics.json")
shipped = json.loads((ROOT / "reports" / "metrics.json").read_text())
NAMES = {"stack": "Stacked\n(shipped design)", "xgb": "XGBoost", "cnn": "1D CNN", "mean": "Mean\nXGB+CNN", "rf": "Random\nforest", "dt": "Decision\ntree", "lr": "Logistic\nregression"}
ORDER = ["stack", "xgb", "cnn", "mean", "rf", "dt", "lr"]


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def cm_panel(ax, cm, title):
    cm = np.array(cm)
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]:,}\n{cm[i, j] / cm[i].sum() * 100:.1f}% of row", ha="center", va="center", fontsize=9.5, color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["pred normal", "pred attack"]); ax.set_yticks([0, 1]); ax.set_yticklabels(["actual\nnormal", "actual\nattack"], fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.spines[:].set_visible(False)


def f01():
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 3.8), gridspec_kw={"wspace": 0.35})
    cm_panel(axs[0], off["seed42"]["stack"]["confusion_matrix"], "Stacked ensemble, official test set\n(82,332 flows, seed 42)")
    cm_panel(axs[1], off["seed42"]["xgb"]["confusion_matrix"], "XGBoost alone, same test set")
    cm_panel(axs[2], shipped["confusion_matrix"], "Shipped model on its own\nsynthetic test split (1,800 rows)")
    save(fig, "f01_confusion_matrices.png")


def f02():
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.9))
    for ax, (k, t) in zip(axs, [("accuracy", "Accuracy"), ("f1", "F1 score"), ("fpr", "False-positive rate (lower is better)")]):
        m = [off["summary"][n][k]["mean"] for n in ORDER]
        sd = [off["summary"][n][k]["std"] for n in ORDER]
        cols = [ORANGE if n == "stack" else BLUE for n in ORDER]
        b = ax.bar(range(len(ORDER)), m, yerr=sd, color=cols, capsize=3)
        for r, v in zip(b, m):
            ax.text(r.get_x() + r.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=8)
        ax.set_xticks(range(len(ORDER))); ax.set_xticklabels([NAMES[n] for n in ORDER], fontsize=7.4)
        ax.set_title(t, fontsize=10); ax.set_ylim(0, 1.05)
    fig.suptitle("Official UNSW-NB15 partition, 5 seeds (mean, error bar = std)", fontsize=10.5, y=1.02)
    save(fig, "f02_model_comparison_official.png")


def f03():
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    for k, c, n in [("xgb", BLUE, "XGBoost (AUC 0.985)"), ("cnn", PURPLE, "1D CNN (AUC 0.976)"), ("stack", ORANGE, "Stacked (AUC 0.984)")]:
        ax.plot(off["roc"][k]["fpr"], off["roc"][k]["tpr"], color=c, lw=2, label=n)
    ax.plot([0, 1], [0, 1], color=GREY, ls=":")
    ax.set_xlabel("False-positive rate"); ax.set_ylabel("True-positive rate"); ax.legend(frameon=False, loc="lower right")
    ax.set_title("ROC curves on the official test set (seed 42)", fontsize=10)
    save(fig, "f03_roc_curves.png")


def f04():
    t = off["thresholds"]
    x = [r["threshold"] for r in t]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for k, c, n in [("precision", BLUE, "precision"), ("recall", TEAL, "recall"), ("f1", ORANGE, "F1"), ("fpr", RED, "false-positive rate")]:
        ax.plot(x, [r[k] for r in t], marker="o", ms=3, color=c, label=n, lw=1.8)
    ax.axvline(0.5, color=GREY, ls="--", lw=1); ax.text(0.505, 0.05, "shipped\nthreshold 0.5", fontsize=8, color=GREY)
    ax.set_xlabel("decision threshold on the stacked probability"); ax.set_ylabel("score"); ax.legend(frameon=False, ncol=2, loc="lower left")
    ax.set_title("Threshold analysis, official test set (seed 42)", fontsize=10); ax.set_ylim(0, 1.03)
    save(fig, "f04_threshold_sweep.png")


def f05():
    pc = off["per_category"]
    names = sorted(pc, key=lambda k: pc[k]["rate"])
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    vals = [pc[n]["rate"] for n in names]
    b = ax.barh(range(len(names)), vals, color=[RED if n == "Normal" else (ORANGE if pc[n]["rate"] < 0.95 else TEAL) for n in names])
    for i, (n, v) in enumerate(zip(names, vals)):
        ax.text(v + 0.005, i, f"{v * 100:.1f}%  (n={pc[n]['n']:,})", va="center", fontsize=8.5)
    ax.set_yticks(range(len(names))); ax.set_yticklabels([("Normal (passed)" if n == "Normal" else n) for n in names]); ax.set_xlim(0, 1.25)
    ax.set_xlabel("share detected (attack classes) or correctly passed (Normal)")
    ax.set_title("Stacked model by traffic category, official test set (seed 42)", fontsize=10)
    save(fig, "f05_per_category.png")


def f06():
    top = off["feature_importance_gain"][:12][::-1]
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    ax.barh(range(len(top)), [g for _, g in top], color=BLUE)
    ax.set_yticks(range(len(top))); ax.set_yticklabels([n.split("__")[1] for n, _ in top]); ax.set_xlabel("XGBoost gain")
    ax.set_title("Top features by gain (official data, seed 42)", fontsize=10)
    save(fig, "f06_feature_importance.png")


def f07():
    a = sh["shipped_on_fresh_synthetic_seed7"]["stack"]["accuracy"]
    rows = [("Shipped,\nits own\nsynthetic test", shipped["accuracy"], TEAL), ("Shipped,\nfresh synthetic\n(seed 7)", a, TEAL),
            ("Shipped,\nREAL official\ntest", sh["shipped_on_real_official_test"]["stack"]["accuracy"], RED),
            ("Real-trained,\nREAL official\ntest", off["summary"]["stack"]["accuracy"]["mean"], BLUE),
            ("Real-trained,\nsynthetic\ndemo CSV", sh["real_trained_on_synthetic_demo_csv"]["stack"]["accuracy"], RED)]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    b = ax.bar(range(len(rows)), [r[1] for r in rows], color=[r[2] for r in rows])
    for r, (n, v, c) in zip(b, rows):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=9)
    ax.axhline(0.5, color=GREY, ls=":"); ax.text(4.45, 0.51, "chance", fontsize=8, color=GREY, ha="right")
    ax.set_xticks(range(len(rows))); ax.set_xticklabels([r[0] for r in rows], fontsize=8); ax.set_ylim(0, 1.1); ax.set_ylabel("accuracy (stacked ensemble)")
    ax.set_title("Where the training data comes from decides everything", fontsize=10)
    save(fig, "f07_synthetic_vs_real.png")


def f08():
    base = [("QNN+ECC", 0.90492), ("QAE", 0.904385), ("PolyNet", 0.905035), ("LinkNet", 0.912707), ("Bi-LSTM", 0.899314), ("SqueezeNet", 0.935426), ("LeNet", 0.906939), ("Proposed\n(paper)", 0.948696)]
    ours = [("Logistic\nregression", pap["summary"]["lr"]["accuracy"]["mean"]), ("1D CNN", pap["summary"]["cnn"]["accuracy"]["mean"]), ("Stacked\n(ours)", pap["summary"]["stack"]["accuracy"]["mean"]),
            ("XGBoost", pap["summary"]["xgb"]["accuracy"]["mean"])]
    fig, ax = plt.subplots(figsize=(10.5, 4.3))
    labels = [n for n, _ in base] + [n for n, _ in ours]
    vals = [v for _, v in base] + [v for _, v in ours]
    cols = [GREY] * 7 + [NAVY] + [ORANGE if "ours" in n else BLUE for n, _ in ours]
    b = ax.bar(range(len(vals)), vals, color=cols)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.002, f"{v:.3f}", ha="center", fontsize=8)
    ax.axvline(7.5, color="black", lw=0.8, ls="--")
    ax.set_ylim(0.85, 0.97); ax.set_xticks(range(len(vals))); ax.set_xticklabels(labels, fontsize=7.4)
    ax.set_ylabel("mean accuracy")
    ax.text(3.5, 0.962, "reported in the base paper (Table 2)", ha="center", fontsize=9, color=GREY)
    ax.text(10.0, 0.962, "measured here, same style of protocol\n(9,000 balanced flows, 10 runs)", ha="center", fontsize=9, color=BLUE)
    ax.set_title("Comparison with the base paper (different subsets of UNSW-NB15: indicative only)", fontsize=10)
    save(fig, "f08_base_paper_comparison.png")


def f09():
    sizes = ["1 KB", "10 KB", "100 KB", "1 MB", "5 MB"]
    kb = [1, 10, 100, 1024, 5120]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, op, t in zip(axs, ["encrypt", "decrypt"], ["Encrypt (sender side)", "Decrypt (cloud side)"]):
        ax.plot(kb, [cry["secure_channel_ecdh_aesgcm"][s][op]["median_ms"] for s in sizes], "o-", color=ORANGE, lw=2, label="SecureChannel: ECDH + HKDF + AES-GCM (incl. base64)")
        ax.plot(kb, [cry["aes256gcm_only"][s][op]["median_ms"] for s in sizes], "s--", color=TEAL, lw=1.6, label="AES-256-GCM only")
        ax.plot(kb, [cry["rsa2048_oaep_aesgcm"]["sizes"][s][op]["median_ms"] for s in sizes], "^-", color=BLUE, lw=1.6, label="RSA-2048-OAEP + AES-GCM")
        ax.plot(kb, [cry["rsa3072_oaep_aesgcm"]["sizes"][s][op]["median_ms"] for s in sizes], "v-", color=PURPLE, lw=1.6, label="RSA-3072-OAEP + AES-GCM")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("payload size (KB)"); ax.set_title(t, fontsize=10)
        ax.set_xticks(kb); ax.set_xticklabels(sizes)
    axs[0].set_ylabel("median time (ms, log scale)"); axs[0].legend(frameon=False, fontsize=7.6, loc="upper left")
    save(fig, "f09_crypto_latency.png")


def f10():
    ip, ap = pipe["in_process"], pipe["api_127_0_0_1"]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.9), gridspec_kw={"width_ratios": [1, 1.3], "wspace": 0.75})
    parts = [("IDS scoring (1 flow)", ip["ids_score_single"]["median_ms"], PURPLE), ("Encrypt 100 KB", ip["encrypt_100kb"]["median_ms"], ORANGE), ("Decrypt 100 KB", ip["decrypt_100kb"]["median_ms"], TEAL)]
    left = 0
    for n, v, c in parts:
        axs[0].barh(0, v, left=left, color=c, label=f"{n}: {v:.2f} ms")
        left += v
    axs[0].set_yticks([]); axs[0].set_xlabel("median milliseconds (in process)"); axs[0].legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.25))
    axs[0].set_title(f"One protected 100 KB transfer: {ip['protected_transfer_100kb']['median_ms']:.2f} ms measured end to end\n(bar = its three parts, medians measured separately)", fontsize=9.5)
    keys = [("health", "GET /health"), ("score_single", "POST /ids/score"), ("encrypt_1kb_text", "POST /crypto/encrypt (1 KB)"), ("decrypt_1kb_text", "POST /crypto/decrypt (1 KB)"),
            ("score_batch_120_rows", "POST /ids/score-batch (120 rows)"), ("encrypt_file_1mb", "POST /crypto/encrypt-file (1 MB)"), ("protected_transfer_via_api_1kb", "score + encrypt + decrypt\n(3 calls, 1 KB)")]
    v = [ap[k]["median_ms"] for k, _ in keys]
    b = axs[1].barh(range(len(keys)), v, color=BLUE)
    for r, x in zip(b, v):
        axs[1].text(x + 0.3, r.get_y() + r.get_height() / 2, f"{x:.1f} ms", va="center", fontsize=8)
    axs[1].set_yticks(range(len(keys))); axs[1].set_yticklabels([n for _, n in keys], fontsize=8); axs[1].invert_yaxis()
    axs[1].set_xlabel("median milliseconds, HTTP on 127.0.0.1"); axs[1].set_title("API latency", fontsize=10); axs[1].set_xlim(0, max(v) * 1.2)
    save(fig, "f10_pipeline_latency.png")


def f11():
    runs = pap["per_seed"]
    data = [[r[n]["accuracy"] for r in runs] for n in ORDER]
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    bp = ax.boxplot(data, patch_artist=True, widths=0.55, medianprops=dict(color="black"))
    for patch, n in zip(bp["boxes"], ORDER):
        patch.set_facecolor(ORANGE if n == "stack" else "#9DB8D6")
    ax.set_xticklabels([NAMES[n] for n in ORDER], fontsize=7.8); ax.set_ylabel("test accuracy (1,350 flows)")
    ax.set_title("Base-paper-style protocol: 10 repetitions of the 9,000-flow experiment", fontsize=10)
    save(fig, "f11_paper_protocol_boxplot.png")


def f12():
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    seeds = off["seeds"]
    for n, c in [("xgb", BLUE), ("stack", ORANGE), ("mean", TEAL), ("cnn", PURPLE)]:
        ax.plot(seeds, [r[n]["accuracy"] for r in off["per_seed"]], "o-", color=c, label=n if n != "stack" else "stacked", lw=1.8)
    ax.set_xticks(seeds); ax.set_xlabel("seed (controls the fit/validation split and model initialisation)"); ax.set_ylabel("accuracy on the 82,332-flow test set")
    ax.legend(frameon=False, ncol=4, loc="center right"); ax.set_ylim(0.8, 0.95)
    ax.set_title("Seed-to-seed stability on the official partition", fontsize=10)
    save(fig, "f12_seed_stability.png")


if __name__ == "__main__":
    for f in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12):
        f()
