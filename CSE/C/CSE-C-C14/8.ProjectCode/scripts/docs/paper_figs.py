"""Compact figures for the IEEE paper (drawn at the final column width of 3.4 in so the type stays readable).

Written to docs/figures/paper_*.png. Numbers come from facts.py (experiments/cifake/metrics.json).
"""

import os

from PIL import Image

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, RED, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#C0392B", "#6B5BD2", "#5B6B7F"


def _mpl():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 7})
    return plt


def _box(ax, x, y, w, h, text, fc, tc="white", fs=6.2, lw=0.0, ec="none"):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=1.4", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, linespacing=1.15)


def _arrow(ax, x0, y0, x1, y1, color=NAVY):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=color, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=6))


def fig_architecture():
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 88)
    ax.axis("off")
    # tiers
    for y, h, fc, ec, label in [(72, 15, "#E3EEF9", BLUE, "React + Vite web app (port 5414)"), (49, 20, "#DDF2EE", TEAL, "Flask application (port 8414)"),
                                (17, 29, "#FCEADB", ORANGE, "PyTorch inference (CPU)"), (1, 13, "#EEF1F6", GREY, "Local files only")]:
        from matplotlib.patches import FancyBboxPatch

        ax.add_patch(FancyBboxPatch((1, y), 98, h, boxstyle="round,pad=0,rounding_size=2", fc=fc, ec=ec, lw=0.9))
        ax.text(3, y + h - 2.2, label, fontsize=6.4, fontweight="bold", color=NAVY, va="top")
    _box(ax, 4, 74, 28, 7, "Landing, Login,\nAnalyze, Insights", BLUE)
    _box(ax, 35, 74, 28, 7, "Bearer token,\n/api proxy", BLUE)
    _box(ax, 66, 74, 29, 7, "Verdict, votes,\nheat map tabs", BLUE)
    _box(ax, 4, 51, 28, 11, "Status\n/health /api/config\n/api/insights", TEAL)
    _box(ax, 35, 51, 28, 11, "Demo sign-in\n/api/auth/login\nsigned 12 h token", TEAL)
    _box(ax, 66, 51, 29, 11, "/api/analyze\n(10 MB, png jpg\nwebp, RGB check)", TEAL)
    for i, (t, x) in enumerate([("A1\nEffNet-B0\n224 px", 4), ("A2\nEffNet-B0\nhardened", 21), ("B\nResNet50\n320 px, flip", 38), ("C\nMobileNetV3\nfocal loss", 55)]):
        _box(ax, x, 29, 15.5, 11, t, ORANGE, fs=5.6)
    _box(ax, 74, 29, 21, 11, "Logit fusion\n+ two gates", NAVY, fs=5.8)
    _box(ax, 4, 19, 45, 7, "Grad-CAM on A1, B, C", PURPLE, fs=5.8)
    _box(ax, 52, 19, 43, 7, "JPEG / resize / blur re-test", PURPLE, fs=5.8)
    _box(ax, 4, 2, 28, 6, "models/*.pt (4)", "#DDF2EE", tc=NAVY, fs=5.8, lw=0.6, ec=TEAL)
    _box(ax, 35, 2, 28, 6, "model_metadata.json", "#DDF2EE", tc=NAVY, fs=5.8, lw=0.6, ec=TEAL)
    _box(ax, 66, 2, 29, 6, "metrics JSON, PNG", "#DDF2EE", tc=NAVY, fs=5.8, lw=0.6, ec=TEAL)
    _arrow(ax, 50, 72, 50, 69)
    _arrow(ax, 50, 49, 50, 46)
    _arrow(ax, 50, 17, 50, 14)
    p = os.path.join(F.FIGS, "paper_architecture.png")
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return p


def fig_flow():
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(3.4, 2.15))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 64)
    ax.axis("off")
    w, h = 28, 14
    xs = [2, 36, 70]
    rows = [46, 25, 4]
    items = [
        [("1 Upload\n(browser, token)", BLUE), ("2 Validate\ntype, size, RGB", TEAL), ("3 Resize and\nnormalise per route", TEAL)],
        [("4 Four routes\nlogit pairs\n(B: flip TTA)", ORANGE), ("5 Gate 1, weighted\nsum, Gate 2", NAVY), ("6 Softmax: verdict,\nconfidence, votes", NAVY)],
        [("7 Grad-CAM\nA1, B, C", PURPLE), ("8 Re-test: JPEG,\nresize, blur", PURPLE), ("9 JSON reply:\nverdict, maps,\nconsistency k/n", BLUE)],
    ]
    for r, y in enumerate(rows):
        for c, x in enumerate(xs):
            t, col = items[r][c]
            _box(ax, x, y, w, h, t, col, fs=5.8)
    for r, y in enumerate(rows):
        _arrow(ax, xs[0] + w, y + h / 2, xs[1], y + h / 2)
        _arrow(ax, xs[1] + w, y + h / 2, xs[2], y + h / 2)
    for r in (0, 1):
        yb = rows[r] - 3.5
        ax.plot([xs[2] + w / 2, xs[2] + w / 2], [rows[r], yb], color=NAVY, lw=0.8)
        ax.plot([xs[2] + w / 2, xs[0] + w / 2], [yb, yb], color=NAVY, lw=0.8)
        _arrow(ax, xs[0] + w / 2, yb, xs[0] + w / 2, rows[r + 1] + h)
    p = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return p


def fig_results():
    plt = _mpl()
    import numpy as np

    fig, (a, b) = plt.subplots(2, 1, figsize=(3.4, 3.1), gridspec_kw={"hspace": 0.62, "height_ratios": [1, 1.0]})
    names = ["A1", "A2", "B", "C", "Ens."]
    keys = ["a1", "a2", "b", "c", "ensemble"]
    acc = [F.BR[k]["accuracy"] if k != "ensemble" else F.ENS["accuracy"] for k in keys]
    auc = [F.BR[k]["roc_auc"] if k != "ensemble" else F.ENS["roc_auc"] for k in keys]
    lo = [F.CI[k][0] for k in keys]
    hi = [F.CI[k][1] for k in keys]
    x = np.arange(len(keys))
    err = [[a_ - l for a_, l in zip(acc, lo)], [h_ - a_ for a_, h_ in zip(acc, hi)]]
    cols = [BLUE, BLUE, BLUE, BLUE, NAVY]
    b1 = a.bar(x - 0.2, acc, 0.38, color=cols, yerr=err, error_kw=dict(lw=0.7, capsize=1.5), label="accuracy (95% CI)")
    b2 = a.bar(x + 0.2, auc, 0.38, color=ORANGE, label="ROC-AUC")
    for bb in list(b1) + list(b2):
        a.text(bb.get_x() + bb.get_width() / 2, 0.806, f"{bb.get_height():.4f}", ha="center", va="bottom", fontsize=5.2, rotation=90, color="white")
    a.set_ylim(0.8, 1.0)
    a.set_xticks(x)
    a.set_xticklabels(names)
    a.set_ylabel("score, n = 2000")
    a.legend(frameon=False, fontsize=6, loc="upper left", ncol=2, bbox_to_anchor=(0, 1.2))
    a.spines[["top", "right"]].set_visible(False)
    a.set_title("(a) Held-out test set", fontsize=7, pad=11)
    conds = [("clean_subset", "clean"), ("jpeg", "JPEG\nq60"), ("resize", "resize\n1/2"), ("blur", "blur\n5x5"), ("noise", "noise\nσ6")]
    xs = np.arange(len(conds))
    for k, lab, col, mk in [("a1", "A1", BLUE, "o"), ("b", "B", TEAL, "s"), ("ensemble", "Ensemble", NAVY, "D")]:
        vals = [(F.ROB[c]["ensemble"] if k == "ensemble" else F.ROB[c]["branches"][k])["accuracy"] for c, _ in conds]
        b.plot(xs, vals, marker=mk, ms=3, lw=1.0, color=col, label=lab)
    b.axhline(0.5, color=RED, ls=":", lw=0.9)
    b.text(4.3, 0.505, "chance", color=RED, fontsize=6, ha="right", va="bottom")
    b.set_xticks(xs)
    b.set_xticklabels([n for _, n in conds], fontsize=6.4)
    b.set_ylim(0.45, 1.08)
    b.set_ylabel("accuracy, n = 1000")
    b.legend(frameon=False, fontsize=6, loc="upper right", ncol=3)
    b.spines[["top", "right"]].set_visible(False)
    b.set_title("(b) Degraded inputs", fontsize=7, pad=3)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return p


def fig_threshold():
    plt = _mpl()

    fig, ax = plt.subplots(figsize=(3.4, 1.75))
    th = [s["threshold"] for s in F.SWEEP]
    ax.plot(th, [s["accuracy"] for s in F.SWEEP], marker="o", ms=2.5, lw=1.0, color=NAVY, label="accuracy")
    ax.plot(th, [s["fpr"] for s in F.SWEEP], marker="s", ms=2.5, lw=1.0, color=RED, label="false-positive rate")
    ax.plot(th, [s["fnr"] for s in F.SWEEP], marker="^", ms=2.5, lw=1.0, color=TEAL, label="false-negative rate")
    ax.axvline(0.5, color=GREY, ls=":", lw=0.8)
    ax.text(0.51, 0.72, "deployed threshold", fontsize=5.8, color=GREY, va="center")
    ax.set_xlabel("decision threshold on the fused AI-generated probability")
    ax.set_ylabel("rate")
    ax.set_ylim(0, 1.0)
    ax.legend(frameon=False, fontsize=6, loc="center right", bbox_to_anchor=(1.0, 0.45))
    ax.spines[["top", "right"]].set_visible(False)
    p = os.path.join(F.FIGS, "paper_threshold.png")
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return p


def crop_screens():
    """Fig. 4 = verdict card, Fig. 5 = Grad-CAM panel (both real captures, cropped to the product area)."""
    out = {}
    s = Image.open(F.shot("07_result_verdict.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_verdict.png")
    s.crop((290, 285, 1415, 700)).save(p)
    out["verdict"] = p
    s = Image.open(F.shot("08_result_votes_robustness.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_votes.png")
    s.crop((290, 80, 1415, 592)).save(p)
    out["votes"] = p
    s = Image.open(F.shot("09_result_gradcam.png")).convert("RGB")
    p = os.path.join(F.FIGS, "paper_screen_gradcam.png")
    s.crop((300, 80, 1405, 800)).save(p)
    out["gradcam"] = p
    return out


def make_all():
    out = {"arch": fig_architecture(), "flow": fig_flow(), "results": fig_results(), "threshold": fig_threshold()}
    out.update(crop_screens())
    return out


if __name__ == "__main__":
    print(make_all())
