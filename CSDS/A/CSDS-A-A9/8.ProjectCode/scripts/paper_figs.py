"""Column-width figures for the IEEE paper (drawn at 3.45 in so the text reads at print size) into docs/paper_figs/."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO_L, ROSE_L, Canvas  # noqa: E402
from doc_common import ROOT, SHOTS, metrics  # noqa: E402

OUT = ROOT / "docs" / "paper_figs"
OUT.mkdir(parents=True, exist_ok=True)
INDIGO, MINT, ROSE, AMBER, INK, GREY = "#5b5bd6", "#2f9e77", "#d6455d", "#e0a030", "#1b2238", "#9aa5ba"


def fig1():
    """Architecture, 3.45 x 3.0 in (units of 0.1 in)."""
    c = Canvas(3.45, 3.0)
    c.zone(1, 22.5, 33, 7, "Browser (React 19 + Vite, port 5109)", fc=GREY_L, fs=5.5)
    c.box(2, 23.2, 7.2, 3.6, "Landing", fc="white", fs=5.6, r=1)
    c.box(10, 23.2, 7.2, 3.6, "Training", fc="white", fs=5.6, r=1)
    c.box(18, 23.2, 7.2, 3.6, "Unlearning\n+ certificate", fc="white", fs=5.2, r=1)
    c.box(26, 23.2, 7.2, 3.6, "Explorer\n+ Audit", fc="white", fs=5.2, r=1)
    c.arrow((17.5, 22.5), (17.5, 19.8), "/api (JSON, Vite proxy)", fs=5.6, loff=(9, 0))
    c.zone(1, 2, 33, 17.5, "Python standard-library server (http.server, port 8109)", fc=BLUE_L, fs=5.5)
    c.box(2.5, 12.6, 9.5, 4.2, "web.py\nroutes + lock", fc="white", fs=5.6, r=1)
    c.box(13.5, 12.6, 9.5, 4.2, "engine.py\ntrain / unlearn /\ncertify", fc=INDIGO_L, fs=5.2, r=1)
    c.box(24.5, 12.6, 8.5, 4.2, "audit.py\nSHA-256 chain", fc=GREEN_L, fs=5.2, r=1)
    c.box(2.5, 4.0, 9.5, 5.6, "dataset.py\n5 clients x 5\nsentences", fc="white", fs=5.2, r=1)
    c.box(13.5, 4.0, 9.5, 5.6, "model.py\nbigram LM,\n1,089 params,\nclip, MIA AUC", fc="white", fs=5, r=1)
    c.box(24.5, 4.0, 8.5, 5.6, "data/\naudit_log\n.jsonl", fc=AMBER_L, fs=5.2, r=1)
    c.arrow((12, 14.7), (13.5, 14.7), head=True)
    c.arrow((23, 14.7), (24.5, 14.7), head=True)
    c.arrow((18.2, 12.6), (18.2, 9.6), head=True)
    c.arrow((28.7, 12.6), (28.7, 9.6), head=True)
    c.arrow((12, 6.8), (13.5, 6.8), head=True)
    c.text(17.5, 0.9, "In-memory state: clipped updates, noise vector, model parameters", fs=5.2, italic=True)
    c.save(OUT / "fig1_architecture.png")


def fig2():
    """Main flow, 3.45 x 3.1 in."""
    c = Canvas(3.45, 3.1)
    cx = 17
    c.terminal(cx, 29.2, 13, 2.4, "POST /api/train", fs=6)
    c.box(cx - 15, 23.2, 30, 3.6, "Clip each client update to C = 25;\nsum + N(0, (sigma C)^2); divide by n", fc=INDIGO_L, fs=5.6, r=1)
    c.arrow((cx, 28), (cx, 26.8))
    c.terminal(cx, 20.5, 15, 2.4, "POST /api/unlearn {client}", fs=6)
    c.arrow((cx, 23.2), (cx, 21.7))
    c.box(cx - 15, 14.4, 30, 3.6, "Subtract stored clipped update;\ndivide by (n - 1); keep the same noise", fc=INDIGO_L, fs=5.6, r=1)
    c.arrow((cx, 19.3), (cx, 18))
    c.box(cx - 15, 8.6, 14.2, 3.9, "L2 distance to retained-\nonly aggregate <= 1e-10", fc=AMBER_L, fs=5, r=1)
    c.box(cx + 0.8, 8.6, 14.2, 3.9, "Attack AUC, perplexity,\naccuracy, retention >= 70 %", fc=AMBER_L, fs=5, r=1)
    c.arrow((cx, 14.4), (cx - 7.9, 12.5))
    c.arrow((cx, 14.4), (cx + 7.9, 12.5))
    c.diamond(cx, 5.0, 13, 4.2, "both pass?", fs=5.5)
    c.arrow((cx - 7.9, 8.6), (cx - 3.5, 6.6))
    c.arrow((cx + 7.9, 8.6), (cx + 3.5, 6.6))
    c.box(1, 0.4, 13, 2.8, "CERTIFIED", fc=GREEN_L, fs=5.6, r=1, bold=True)
    c.box(20, 0.4, 14, 2.8, "REVIEW_REQUIRED", fc=ROSE_L, fs=5.2, r=1, bold=True)
    c.arrow((cx - 3.5, 3.9), (8, 3.2), "yes", fs=5.2, loff=(-1.5, 0.6))
    c.arrow((cx + 3.5, 3.9), (27, 3.2), "no", fs=5.2, loff=(1.5, 0.6))
    c.text(cx + 1, 0.1, "", fs=4)
    c.save(OUT / "fig2_flow.png")


def fig3():
    rows = metrics("noise_sweep")["rows"]
    sig = np.array([r["noise_multiplier"] for r in rows])
    ppl = np.array([r["perplexity"]["mean"] for r in rows])
    aucb = np.array([r["membership_auc_before"]["mean"] for r in rows])
    auca = np.array([r["membership_auc_after"]["mean"] for r in rows])
    gold = metrics("gold_retrain")["results"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e3e7ef", "grid.linewidth": 0.5})
    fig, ax = plt.subplots(1, 2, figsize=(3.45, 2.15), gridspec_kw={"width_ratios": [1.45, 1]})
    a = ax[0]
    a.plot(sig, ppl, color=INDIGO, marker="o", ms=2.5, lw=1.1, label="perplexity")
    a.axhline(32, color=ROSE, ls="--", lw=0.8)
    a.text(0.0011, 36, "uniform = 32", color=ROSE, fontsize=5.5)
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xlabel("noise multiplier $\\sigma$"); a.set_ylabel("perplexity", color=INDIGO)
    a.axvline(4.85, color=MINT, ls=":", lw=0.9); a.text(4.5, 14, "$\\epsilon<1$", color=MINT, fontsize=6, ha="right")
    b = a.twinx()
    b.plot(sig, aucb, color=AMBER, marker="s", ms=2.2, lw=1.1)
    b.plot(sig, auca, color=MINT, marker="^", ms=2.2, lw=1.1)
    b.set_ylim(0.4, 1.05); b.set_ylabel("attack AUC", color=AMBER); b.grid(False); b.spines["right"].set_visible(True)
    b.text(0.0011, 0.86, "AUC before", color=AMBER, fontsize=5.5)
    b.text(0.0011, 0.45, "AUC after", color=MINT, fontsize=5.5)
    a.set_title("(a) noise sweep", fontsize=6.5, fontweight="bold")
    g = ax[1]
    w = 0.34
    for i, r in enumerate(gold):
        x1, x2 = r["l2_unlearned_vs_fresh_retrain"], r["l2_fresh_retrain_vs_fresh_retrain"]
        g.bar(i - w / 2, x1["mean"], w, yerr=x1["sd"], color=INDIGO, capsize=1.5, error_kw={"lw": 0.6})
        g.bar(i + w / 2, x2["mean"], w, yerr=x2["sd"], color=AMBER, capsize=1.5, error_kw={"lw": 0.6})
    g.set_yscale("log"); g.set_xticks([0, 1]); g.set_xticklabels(["$\\sigma$=3", "$\\sigma$=0.5"])
    g.set_ylabel("L2 between models")
    g.bar(0, 0, color=INDIGO, label="unlearned vs retrain"); g.bar(0, 0, color=AMBER, label="retrain vs retrain")
    g.legend(fontsize=5, frameon=False, loc="upper right", bbox_to_anchor=(1.02, 1.02))
    g.set_ylim(60, 2500)
    g.set_title("(b) retrain check", fontsize=6.5, fontweight="bold")
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig3_results.png", dpi=300, facecolor="white")
    plt.close(fig)



def fig6():
    """(a) synthetic corpus: clients needed for a useful release at epsilon < 1; (b) neural adapters: attack AUC and cost."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e3e7ef", "grid.linewidth": 0.5})
    sc = metrics("synthetic_corpus")["n_sweep"]["rows"]
    nn = metrics("neural_adapter")["summary"]["by_sigma"]
    fig, ax = plt.subplots(1, 2, figsize=(3.45, 2.0), gridspec_kw={"width_ratios": [1, 1.1]})
    a = ax[0]
    for sg, col, lab in ((1.0, AMBER, "$\\sigma$=1"), (4.85, INDIGO, "$\\sigma$=4.85 ($\\epsilon<1$)")):
        rr = [r for r in sc if r["sigma"] == sg]
        a.plot([r["n_clients"] for r in rr], [r["ratio_to_noise_free"] for r in rr], color=col, marker="o", ms=2.3, lw=1.1, label=lab)
    a.axhline(1.2, color=ROSE, ls="--", lw=0.8); a.text(5.5, 1.35, "1.2x", color=ROSE, fontsize=5.8)
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xlabel("federated clients n"); a.set_ylabel("perplexity / noise-free")
    a.legend(fontsize=5, frameon=False, loc="upper right")
    a.set_title("(a) synthetic corpus", fontsize=6.5, fontweight="bold")
    b = ax[1]
    keep = [r for r in nn if r["sigma"] in (0.0, 0.01, 0.03, 0.05, 0.1, 0.3, 1.0)]
    x = np.arange(len(keep))
    get = lambda r, k: r[k]["mean"] if isinstance(r[k], dict) else r[k]
    b.plot(x, [get(r, "client_auc_before") for r in keep], color=AMBER, marker="s", ms=2.3, lw=1.1, label="before")
    b.plot(x, [get(r, "client_auc_after") for r in keep], color=MINT, marker="^", ms=2.3, lw=1.1, label="after removal")
    b.plot(x, [get(r, "client_auc_retrain") for r in keep], color=INDIGO, marker="o", ms=2.0, lw=0.8, ls=":", label="fresh retrain")
    b.axhline(0.5, color=ROSE, ls="--", lw=0.7)
    b.axvspan(4.5, 6.4, color="#f3d6da", alpha=0.6, lw=0); b.text(5.45, 0.93, "model\ndestroyed", ha="center", fontsize=5.2, color=ROSE)
    b.set_xticks(x); b.set_xticklabels(["0" if r["sigma"] == 0 else f"{r['sigma']:g}" for r in keep], fontsize=5.6)
    b.set_xlabel("noise multiplier $\\sigma$"); b.set_ylabel("client-level attack AUC"); b.set_ylim(0.38, 1.0)
    b.legend(fontsize=5, frameon=False, loc="upper right", bbox_to_anchor=(0.74, 1.0))
    b.set_title("(b) neural adapters", fontsize=6.5, fontweight="bold")
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig6_scale.png", dpi=300, facecolor="white")
    plt.close(fig)


def crop(src, box, dst, width=1100):
    im = Image.open(SHOTS / src).convert("RGB").crop(box)
    h = int(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(OUT / dst)


def screens():
    crop("09_unlearning_certificate.png", (290, 515, 1420, 900), "fig4_certificate.png")
    crop("13_audit_ledger.png", (290, 280, 1420, 780), "fig5_audit.png")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig6(); screens()
    print("paper figures written to", OUT)
