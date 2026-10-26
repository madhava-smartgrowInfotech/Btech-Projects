"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so text stays legible)."""
import os
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, GREEN, RED, GREY = "#1B2A41", "#2F6DB5", "#1E9E8F", "#E08A1E", "#3C9D5D", "#C0392B", "#8A94A6"
PALE = {"blue": "#E4EEF9", "teal": "#DFF3EF", "orange": "#FCEBD3", "green": "#E3F3E8", "grey": "#EEF0F4", "red": "#F9E0DC"}


def _save(fig, name):
    os.makedirs(F.FIGS, exist_ok=True)
    p = os.path.join(F.FIGS, name)
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def _canvas(w, h, xmax, ymax):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, text, fc="grey", ec=NAVY, fs=5.6, bold=False, lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, style="-|>", lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 2.75, 100, 79)
    _box(ax, 1, 66, 98, 12, f"React + Vite console (port {F.WEB_PORT})\nKeys · Send · Receive · Analysis · Robustness · Log", "blue", fs=5.2, bold=True)
    _box(ax, 1, 46, 98, 15, f"FastAPI service (port {F.API_PORT}) - 24 endpoints\nJWT login (12 h) · bcrypt · ownership checks ·\n25 MB upload cap · no secrets in the log", "teal", fs=5.0, bold=True)
    _arrow(ax, 50, 66, 50, 61.6, style="<|-|>")
    names = [("crypto.py\nAES-256-GCM\nRSA-OAEP\nCVL1 bundle", "orange"), ("lsb.py\n1-bit LSB\ncapacity check\nextract", "green"),
             ("metrics.py\nplots.py\nPSNR, SSIM\nhistograms", "blue")]
    for i, (t, c) in enumerate(names):
        x = 1 + i * 33
        _box(ax, x, 17, 31, 23, t, c, fs=4.8)
        _arrow(ax, x + 15.5, 46, x + 15.5, 40.6)
    _box(ax, 1, 1, 48, 10.5, "SQLite: users · keypairs · oplog", "grey", fs=4.8)
    _box(ax, 51, 1, 48, 10.5, "Files: covers · payloads · PNG outputs", "grey", fs=4.8)
    _arrow(ax, 25, 17, 25, 12.1, style="-")
    _arrow(ax, 75, 17, 75, 12.1, style="-")
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 2.9, 100, 83)
    ax.text(50, 80, "SEND (sender)", ha="center", fontsize=5.6, fontweight="bold", color=NAVY)
    s = [("File +\nheader", "grey"), ("AES-256-\nGCM", "orange"), ("RSA-OAEP\nwrap key", "orange"),
         ("CVL1\nbundle", "teal"), ("Capacity\ncheck", "red"), ("LSB\nembed", "green"), ("Stego\nPNG", "blue")]
    xs = [1 + i * 14.1 for i in range(7)]
    for x, (t, c) in zip(xs, s):
        _box(ax, x, 58, 12.6, 17, t, c, fs=4.4)
    for i in range(6):
        _arrow(ax, xs[i] + 12.6, 66.5, xs[i + 1], 66.5, lw=0.6)
    ax.text(50, 50, "PNG file (lossless channel)", ha="center", fontsize=5.0, color=GREY, style="italic")
    _arrow(ax, xs[6] + 6, 58, xs[6] + 6, 53.5, color=GREY, ls="--")
    ax.text(50, 44, "RECEIVE (receiver)", ha="center", fontsize=5.6, fontweight="bold", color=NAVY)
    r = [("Read 32-bit\nlength + bits", "green"), ("Check magic,\nkey length", "grey"), ("RSA unwrap\n(private key)", "orange"),
         ("AES-GCM\ntag check", "red"), ("Compare\nSHA-256", "teal"), ("Restored\nfile", "blue")]
    xr = [1 + i * 16.5 for i in range(6)]
    for x, (t, c) in zip(xr, r):
        _box(ax, x, 22, 14.6, 17, t, c, fs=3.9)
    for i in range(5):
        _arrow(ax, xr[i] + 14.6, 30.5, xr[i + 1], 30.5, lw=0.6)
    _box(ax, 1, 3, 98, 12, "Any failed check stops the flow: no payload, bad key, modified bit or wrong size releases nothing", "red", fs=4.3)
    _arrow(ax, 50, 22, 50, 15.5, color=RED, ls="--", lw=0.6)
    return _save(fig, "paper_flow.png")


def results():
    ev, ex = F.EV, F.EX
    fs = ex["fill_study"]["rows"]
    fills = sorted({r["fill"] for r in fs})
    meas = [statistics.mean(r["psnr_mean"] for r in fs if r["fill"] == f) for f in fills]
    theo = [statistics.mean(r["psnr_theory"] for r in fs if r["fill"] == f) for f in fills]
    lo = [min(r["psnr_mean"] for r in fs if r["fill"] == f) for f in fills]
    sa = ex["steganalysis"]["rows"]
    sf = sorted({r["fill"] for r in sa})
    fig, axs = plt.subplots(1, 2, figsize=(3.5, 1.95))
    ax = axs[0]
    x = [100 * f for f in fills]
    ax.plot(x, theo, "-", color=GREY, lw=1.0, label="closed form")
    ax.plot(x, meas, "o", color=BLUE, ms=2.6, label="measured mean")
    ax.plot(x, lo, "v", color=ORANGE, ms=2.2, label="worst cover")
    ax.axhline(50, color=RED, lw=0.6, ls="--")
    ax.text(40, 50.4, "50 dB", fontsize=4.8, color=RED)
    ax.set_xscale("log")
    ax.set_xticks([1, 10, 100])
    ax.set_xticklabels(["1", "10", "100"])
    ax.set_xlabel("capacity used (%)", fontsize=5.5, labelpad=1)
    ax.set_ylabel("PSNR (dB)", fontsize=5.5, labelpad=1)
    ax.set_title("(a) Imperceptibility", fontsize=6, pad=2)
    ax.legend(fontsize=4.6, frameon=False, loc="upper right", handlelength=1.2, borderpad=0.1, labelspacing=0.2)
    ax = axs[1]
    true = [statistics.mean(r["true_fraction_of_samples"] for r in sa if r["fill"] == f) for f in sf]
    ws = [statistics.mean(r["ws_estimate_stego"] for r in sa if r["fill"] == f) for f in sf]
    wlo = [min(r["ws_estimate_stego"] for r in sa if r["fill"] == f) for f in sf]
    whi = [max(r["ws_estimate_stego"] for r in sa if r["fill"] == f) for f in sf]
    ax.fill_between(true, wlo, whi, color=TEAL, alpha=0.25, lw=0)
    ax.plot(true, ws, "o-", color=TEAL, ms=2.4, lw=0.9, label="estimate (mean, range)")
    ax.plot([0, 1], [0, 1], "--", color=GREY, lw=0.7, label="true fraction")
    base = [r["ws_estimate_cover"] for r in sa if r["fill"] == sf[0]]
    ax.axhspan(min(base), max(base), color=ORANGE, alpha=0.18, lw=0)
    ax.text(0.45, max(base) + 0.01, "clean covers", fontsize=4.6, color=ORANGE)
    ax.set_xlabel("true embedded fraction", fontsize=5.5, labelpad=1)
    ax.set_ylabel("weighted-stego estimate", fontsize=5.5, labelpad=1)
    ax.set_title("(b) Detectability", fontsize=6, pad=2)
    ax.legend(fontsize=4.6, frameon=False, loc="upper left", handlelength=1.2, borderpad=0.1, labelspacing=0.2)
    for a in axs:
        a.tick_params(labelsize=5, length=2, pad=1)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
        a.grid(lw=0.3, alpha=0.5)
    fig.tight_layout(pad=0.4, w_pad=0.8)
    return _save(fig, "paper_results.png")


def screens():
    """Fig. 4 send result (stego image, quality tiles, hash); Fig. 5 receive result and the wrong-key failure."""
    s6 = Image.open(F.shot("06_send_result.png")).convert("RGB")
    a = s6.crop((745, 175, 1410, 725))
    p1 = os.path.join(F.FIGS, "paper_screen_send.png")
    a.save(p1)
    s11 = Image.open(F.shot("11_receive_result.png")).convert("RGB")
    s12 = Image.open(F.shot("12_receive_wrong_key.png")).convert("RGB")
    b = s11.crop((745, 190, 1410, 700))
    c = s12.crop((288, 500, 728, 625)).resize((665, int(125 * 665 / 440)))
    im = Image.new("RGB", (665, b.height + 6 + c.height), (11, 13, 16))
    im.paste(b, (0, 0))
    im.paste(c, (0, b.height + 6))
    p2 = os.path.join(F.FIGS, "paper_screen_receive.png")
    im.save(p2)
    return p1, p2


def make():
    p1, p2 = screens()
    return {"arch": arch(), "flow": flow(), "results": results(), "send": p1, "receive": p2}


if __name__ == "__main__":
    print(make())
