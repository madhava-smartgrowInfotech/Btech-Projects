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
    fig, ax = canvas(3.5, 2.75, 100, 78.5)
    panel(ax, 1, 63, 98, 15, "Console (React + Vite, port 5305) / legacy dashboard", PALE_BLUE, BLUE, fs=6)
    for x, t in [(18, "Live scoring"), (40, "Secure transfer"), (62, "Alerts"), (84, "Performance")]:
        box(ax, x, 66, 19.5, 6.2, t, BLUE, fs=5.6)
    panel(ax, 1, 40, 98, 21, "FastAPI service (127.0.0.1:8305)", PALE_TEAL, TEAL, fs=6)
    box(ax, 17, 47, 30, 11, "/api/ids/score\n/api/ids/score-batch\n/api/alerts", TEAL, fs=5.4)
    box(ax, 50, 47, 30, 11, "/api/crypto/encrypt\n/api/crypto/decrypt\n/api/crypto/encrypt-file", TEAL, fs=5.4)
    box(ax, 83, 47, 28, 11, "/api/health\n/api/metrics\ninput limits, 400/503", TEAL, fs=5.4)
    panel(ax, 1, 15, 98, 23, "Core modules", PALE_ORANGE, ORANGE, fs=6)
    box(ax, 25, 23, 46, 12, "ThreatSense Engine\nMinMax + one-hot, XGBoost,\n1D CNN, logistic-regression stacking", ORANGE, fs=5.4)
    box(ax, 75, 23, 46, 12, "SecureChannel\nECDH P-256, HKDF-SHA256,\nAES-256-GCM, mock cloud keys", ORANGE, fs=5.4)
    panel(ax, 1, 0.5, 98, 13, "Files and memory (no database)", LIGHT, "#B7C3D3", fs=6)
    for x, t in [(17, "models/ *.joblib, .pt"), (50, "reports/metrics.json"), (83, "alerts (<=500), key cache")]:
        box(ax, x, 4.5, 29, 5.2, t, WHITE, tc=INK, ec=NAVY, fs=5.2)
    arrow(ax, (50, 63), (50, 61), "", color=NAVY, lw=1.0)
    arrow(ax, (50, 40), (50, 38), "", color=NAVY, lw=1.0)
    arrow(ax, (50, 15), (50, 13.5), "", color=NAVY, lw=1.0)
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = canvas(3.5, 2.5, 100, 71.4)
    ax.text(1, 68.5, "Lane A - SecureChannel", fontsize=6.4, color=TEAL, fontweight="bold")
    a = [("Payload\n<= 1 MB", BLUE), ("Ephemeral\nP-256 key", TEAL), ("ECDH +\nHKDF\n-> key K", TEAL), ("AES-GCM\nnonce 12 B\ntag 16 B", TEAL), ("Envelope\n+ 65 B key", NAVY)]
    xs = [10, 29.5, 49, 68.5, 88]
    for x, (t, c) in zip(xs, a):
        box(ax, x, 57, 17, 15, t, c, fs=5.2)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 8.6, 57), (q - 8.6, 57), "", color=NAVY, lw=1.0)
    box(ax, 88, 38, 17, 11, "Cloud:\nre-derive K,\ncheck tag", ORANGE, fs=5.2)
    arrow(ax, (88, 49.5), (88, 43.7), "", color=NAVY, lw=1.0)
    box(ax, 49, 38, 40, 11, "plaintext (verified)  or  HTTP 400", WHITE, tc=INK, ec=ORANGE, fs=5.4)
    arrow(ax, (79.4, 38), (69.2, 38), "", color=NAVY, lw=1.0)
    ax.text(1, 26.5, "Lane B - ThreatSense Engine", fontsize=6.4, color=PURPLE, fontweight="bold")
    b = [("Flow\nrecord\n(42 feat.)", BLUE), ("Scale +\none-hot", PURPLE), ("XGBoost\n+ 1D CNN", PURPLE), ("LR stack\np >= 0.5", PURPLE), ("Verdict,\nseverity,\nalert", ORANGE)]
    for x, (t, c) in zip(xs, b):
        box(ax, x, 12, 17, 15, t, c, fs=5.2)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 8.6, 12), (q - 8.6, 12), "", color=NAVY, lw=1.0)
    return _save(fig, "paper_flow.png")


def results():
    o, p = F.OFFS, F.PAPS
    plt.rcParams.update({"font.size": 6.5})
    fig, axs = plt.subplots(2, 2, figsize=(3.55, 3.7), gridspec_kw={"wspace": 0.5, "hspace": 0.62})
    ax = axs[0][0]
    labs = ["Stacked", "XGBoost", "CNN"]
    keys = ["stack", "xgb", "cnn"]
    x = np.arange(3)
    v1 = [o[k]["accuracy"]["mean"] for k in keys]
    e1 = [o[k]["accuracy"]["std"] for k in keys]
    v2 = [p[k]["accuracy"]["mean"] for k in keys]
    e2 = [p[k]["accuracy"]["std"] for k in keys]
    b1 = ax.bar(x - 0.2, v1, 0.38, yerr=e1, color=ORANGE, capsize=1.5, error_kw={"lw": 0.6}, label="official")
    b2 = ax.bar(x + 0.2, v2, 0.38, yerr=e2, color=BLUE, capsize=1.5, error_kw={"lw": 0.6}, label="paper prot.")
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.012, f"{r.get_height():.2f}", ha="center", fontsize=5.2, rotation=90, va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=5.8)
    ax.set_ylim(0.6, 1.12)
    ax.set_ylabel("accuracy", fontsize=6.2)
    ax.legend(frameon=False, fontsize=5, loc="upper right", ncol=2, columnspacing=0.6, handlelength=1)
    ax.set_title("(a) real UNSW-NB15", fontsize=6.3)
    ax = axs[0][1]
    sh = F.SHIFT
    rows = [("shipped\nsynth.", F.SHIPPED["accuracy"], TEAL), ("shipped\nreal", sh["shipped_on_real_official_test"]["stack"]["accuracy"], RED),
            ("real-tr.\nreal", o["stack"]["accuracy"]["mean"], BLUE), ("real-tr.\nsynth.", sh["real_trained_on_synthetic_demo_csv"]["stack"]["accuracy"], RED)]
    bars = ax.bar(range(4), [r[1] for r in rows], color=[r[2] for r in rows], width=0.7)
    for r in bars:
        ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.015, f"{r.get_height():.2f}", ha="center", fontsize=5.4)
    ax.axhline(0.5, color=GREY, ls=":", lw=0.7)
    ax.set_xticks(range(4))
    ax.set_xticklabels([r[0] for r in rows], fontsize=4.9)
    ax.set_ylim(0, 1.14)
    ax.set_title("(b) model / test data", fontsize=6.3)
    ax = axs[1][0]
    t = F.OFF["thresholds"]
    xs = [r["threshold"] for r in t]
    for k, c, n in [("precision", BLUE, "precision"), ("recall", TEAL, "recall"), ("f1", ORANGE, "F1"), ("fpr", RED, "FPR")]:
        ax.plot(xs, [r[k] for r in t], color=c, lw=1.1, label=n)
    ax.axvline(0.5, color=GREY, ls="--", lw=0.6)
    ax.set_xlabel("decision threshold", fontsize=6)
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=4.9, loc="lower left", ncol=2, columnspacing=0.6, handlelength=1.1)
    ax.set_title("(c) threshold sweep, stacked", fontsize=6.3)
    ax = axs[1][1]
    pc = F.OFF["per_category"]
    names = sorted(pc, key=lambda k: pc[k]["rate"])
    ax.barh(range(len(names)), [pc[n]["rate"] for n in names], color=[RED if n == "Normal" else (ORANGE if pc[n]["rate"] < 0.95 else TEAL) for n in names], height=0.7)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([("Normal" if n == "Normal" else n[:6] + ("." if len(n) > 6 else "")) for n in names], fontsize=4.8)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("share handled correctly", fontsize=6)
    ax.set_title("(d) by traffic category", fontsize=6.3)
    for a in axs.ravel():
        a.tick_params(axis="y", labelsize=5.2, length=2)
        a.tick_params(axis="x", labelsize=5.2, length=2)
        a.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.94)
    return _save(fig, "paper_results.png")


def screens():
    s7 = Image.open(F.shot("07_secure-transfer-tampered.png")).convert("RGB")
    a = s7.crop((270, 240, 1415, 700))
    p1 = os.path.join(F.FIGS, "paper_screen_secure.png")
    a.save(p1)
    s11 = Image.open(F.shot("11_real-model-performance.png")).convert("RGB")
    s12 = Image.open(F.shot("12_real-flows-real-model.png")).convert("RGB")
    s10 = Image.open(F.shot("10_real-flows-shipped-model.png")).convert("RGB")
    top = s11.crop((270, 190, 1415, 650))
    c12 = s12.crop((290, 215, 1030, 400))
    c10 = s10.crop((290, 215, 1030, 400))
    w = top.width
    bw = w // 2 - 5
    c10 = c10.resize((bw, int(c10.height * bw / c10.width)))
    c12 = c12.resize((bw, int(c12.height * bw / c12.width)))
    im = Image.new("RGB", (w, top.height + 10 + c10.height), (11, 13, 16))
    im.paste(top, (0, 0))
    im.paste(c10, (0, top.height + 10))
    im.paste(c12, (w - bw, top.height + 10))
    p2 = os.path.join(F.FIGS, "paper_screen_real.png")
    im.save(p2)
    return p1, p2


def make():
    return {"arch": arch(), "flow": flow(), "results": results(), "secure": screens()[0], "real": screens()[1]}


if __name__ == "__main__":
    print(make())
