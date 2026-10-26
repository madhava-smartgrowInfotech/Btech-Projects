"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so text stays legible)."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
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
    fig, ax = _canvas(3.5, 2.9, 100, 83)
    _box(ax, 1, 70, 98, 12, "Operator console - React 19 + Vite (port 5310)\nLanding · Live control · Benchmark · Vision · Prediction · Violations · About", "blue", fs=5.2, bold=True)
    _box(ax, 1, 51, 98, 15, "FastAPI service (port 8310) - 20 endpoints\ntoken auth · live · benchmark · vision · prediction ·\nviolations routes · 12 MB upload guard", "teal", fs=5.2, bold=True)
    _arrow(ax, 50, 70, 50, 66.6, style="<|-|>")
    _box(ax, 1, 20, 31, 26, "Simulator\n(sim.py)\n2x2 / 3x3 junctions\n4 controllers on\nidentical demand\nviolation log", "orange", fs=5.0, bold=False)
    _box(ax, 34.5, 20, 31, 26, "Queue forecaster\n(predictor.py)\n11 features ->\nqueue in 30 s\nGradient Boosting\n+ RF, persistence", "green", fs=5.0)
    _box(ax, 68, 20, 31, 26, "Vision layer\n(vision.py)\nYOLOv8n vehicles\nHSV light-bar rule\nPCU density ->\ngreen time", "blue", fs=5.0)
    for x in (16.5, 50, 83.5):
        _arrow(ax, x, 52, x, 46.5)
    _arrow(ax, 34.5, 33, 32.5, 33, color=GREEN)
    _box(ax, 1, 2, 98, 12, "In-memory state: one shared live simulation · benchmark cache · last-run violations\nNo database - models are trained or downloaded at start (yolov8n.pt, ~6 s forecaster fit)", "grey", fs=5.0)
    _arrow(ax, 50, 20, 50, 14.5, style="-")
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 3.1, 100, 89)
    _box(ax, 2, 80, 54, 7, "Every simulated second (1 s tick)", "grey", fs=5.4, bold=True)
    steps = [("1  Poisson arrivals at entry roads\n   x demand x rush-hour profile; ambulance and violators", "orange"),
             ("2  Vehicles reach next junction after 12 s link", "orange"),
             ("3  Signal decision per junction (below)", "teal"),
             ("4  Discharge at 0.5 veh/s while green; spill-back at 30", "orange"),
             ("5  Record queues, phases, delays, violations", "orange")]
    y = 70
    for t, c in steps:
        _box(ax, 2, y, 54, 7.2, t, c, fs=4.7)
        y -= 10.2
    for i in range(4):
        _arrow(ax, 29, 70 - i * 10.2, 29, 70 - i * 10.2 - 2.8)
    _arrow(ax, 29, 80, 29, 77.6)
    # decision panel on the right
    ax.add_patch(FancyBboxPatch((60, 18), 39, 68, boxstyle="round,pad=0.25,rounding_size=1.2", fc="white", ec=TEAL, lw=0.9, ls="--"))
    ax.text(79.5, 82, "Advanced controller", ha="center", fontsize=5.2, fontweight="bold", color=NAVY)
    d = [("Ambulance queued or\ninbound within 15 s?", "red"), ("Yes: force its phase\ngreen (green wave)", "red"),
         ("Score both phases:\nPCU queue + 0.7 x forecast\n+ inbound + head wait / 12", "green"),
         ("x 0.3 if downstream\nqueue >= 26", "green"), ("Switch if current idle,\nother > 2x + 4,\nor green >= 60 s", "teal")]
    ys = [68, 57, 43, 32, 20]
    hs = [8, 8, 11, 8, 10]
    for (t, c), yy, hh in zip(d, ys, hs):
        _box(ax, 63, yy, 33, hh, t, c, fs=4.5)
    for i in range(4):
        _arrow(ax, 79.5, ys[i], 79.5, ys[i + 1] + hs[i + 1] + 0.4)
    _arrow(ax, 56, 50, 60, 50, color=TEAL)
    _box(ax, 2, 3, 96, 9, "Output per run: average delay, queue, throughput, ambulance delay, idle fuel, violations", "grey", fs=4.9)
    _arrow(ax, 29, 19.5, 29, 12.6)
    return _save(fig, "paper_flow.png")


def results():
    fig, axs = plt.subplots(1, 2, figsize=(3.5, 2.05))
    labels = ["Fixed", "Adapt.", "Emerg.", "FlowSense"]
    keys = F.CTRL_KEYS
    cols = [GREY, BLUE, ORANGE, GREEN]
    for ax, key, title in ((axs[0], "Avg delay / vehicle (s)", "Average delay (s)"), (axs[1], "Emergency delay (s)", "Ambulance delay (s)")):
        w = 0.19
        for gi, grid in enumerate(("2x2", "3x3")):
            for ki, k in enumerate(keys):
                m, s = F.gm(grid, k, key)
                ax.bar(gi + (ki - 1.5) * w, m, w * 0.92, yerr=s, color=cols[ki], error_kw=dict(lw=0.5, capsize=1), label=labels[ki] if gi == 0 else None)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["2x2", "3x3"], fontsize=6)
        ax.set_title(title, fontsize=6.5, pad=2)
        ax.tick_params(labelsize=5.5, length=2)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.grid(axis="y", lw=0.3, alpha=0.5)
    axs[0].legend(fontsize=4.8, frameon=False, loc="upper left", handlelength=1, borderpad=0.1, labelspacing=0.2)
    fig.tight_layout(pad=0.4, w_pad=0.8)
    return _save(fig, "paper_results.png")


def screens():
    os.makedirs(F.FIGS, exist_ok=True)
    """Fig. 4 live control centre (map + junction status); Fig. 5 benchmark bars (delay and ambulance delay)."""
    s6 = Image.open(F.shot("06_live_map_and_status.png")).convert("RGB")
    amap = s6.crop((300, 135, 950, 780))
    tab = s6.crop((975, 80, 1410, 650))
    h = 500
    amap = amap.resize((int(amap.width * h / amap.height), h))
    tab = tab.resize((int(tab.width * h / tab.height), h))
    im = Image.new("RGB", (amap.width + 8 + tab.width, h), (11, 13, 16))
    im.paste(amap, (0, 0))
    im.paste(tab, (amap.width + 8, 0))
    p1 = os.path.join(F.FIGS, "paper_screen_live.png")
    im.save(p1)
    s8 = Image.open(F.shot("08_benchmark_charts.png")).convert("RGB")
    a = s8.crop((290, 60, 840, 400))
    b = s8.crop((857, 60, 1410, 400))
    s11 = Image.open(F.shot("11_vision_density.png")).convert("RGB")
    v = s11.crop((870, 57, 1395, 290))
    k = s11.crop((290, 325, 1405, 442))
    top_w = a.width + 8 + b.width
    kk = k.resize((top_w, int(k.height * top_w / k.width)))
    vv = v.resize((int(v.width * 1.5), int(v.height * 1.5)))
    W = max(top_w, vv.width)
    im2 = Image.new("RGB", (W, a.height + 8 + kk.height + 8 + vv.height), (11, 13, 16))
    im2.paste(a, (0, 0))
    im2.paste(b, (a.width + 8, 0))
    im2.paste(kk, (0, a.height + 8))
    im2.paste(vv, ((W - vv.width) // 2, a.height + 8 + kk.height + 8))
    p2 = os.path.join(F.FIGS, "paper_screen_bench_vision.png")
    im2.save(p2)
    return p1, p2


def make():
    p1, p2 = screens()
    return {"arch": arch(), "flow": flow(), "results": results(), "live": p1, "benchvis": p2}


if __name__ == "__main__":
    print(make())
