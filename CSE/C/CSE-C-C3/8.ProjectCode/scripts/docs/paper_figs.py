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
COL = {"static_0": GREY, "static_1": BLUE, "static_3": NAVY, "dynamic_parksure": ORANGE, "dynamic_paper": TEAL}


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


def _box(ax, x, y, w, h, text, fc="grey", ec=NAVY, fs=5.6, bold=False, lw=0.7, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=ec, lw=lw, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, style="-|>", lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 2.95, 100, 84)
    _box(ax, 1, 70, 98, 12, "Driver and admin console - React 19 + Vite (port 5403)\nFind · My bookings · Trust score · Admin: overview, locations,\ninsights, bookings, users", "blue", fs=4.9, bold=True)
    _box(ax, 1, 46, 98, 19, "FastAPI service (port 8403) - 22 routes under /api\nauth.py: JWT HS256 + bcrypt + role guards   schemas.py: validation\n"
         "engine.py: admission · buffer · alternate · trust · fee", "teal", fs=5.0, bold=True)
    _arrow(ax, 50, 70, 50, 65.6, style="<|-|>")
    _box(ax, 1, 20, 31, 20, "Reservations\nsearch · reserve\ncancel · check in\ncheck out", "orange", fs=4.9)
    _box(ax, 34.5, 20, 31, 20, "Trust and fees\nbenefit / warning\nscore 0-5 · multiplier\nsuspension", "green", fs=4.9)
    _box(ax, 68, 20, 31, 20, "Admin\nlocations CRUD\noverview · users\nStrategy Insights", "blue", fs=4.9)
    for x in (16.5, 50, 83.5):
        _arrow(ax, x, 46.5, x, 40.6)
    _box(ax, 1, 2, 31, 13, "Stripe Checkout\n(test) or demo\ncheckout", "orange", fs=4.6)
    _box(ax, 34.5, 2, 31, 13, "SQLite parksure.db\n5 tables: users, locations,\nreservations, payments,\ntrust_events", "grey", fs=4.4)
    _box(ax, 68, 2, 31, 13, "APScheduler\nbuffer reset job\nevery 30 min", "grey", fs=4.6)
    _arrow(ax, 16.5, 20, 16.5, 15.6, style="<|-|>", color=ORANGE, ls="--")
    _arrow(ax, 50, 20, 50, 15.6, style="<|-|>")
    _arrow(ax, 83.5, 20, 83.5, 15.6, style="<|-", color=GREY, ls="--")
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 3.0, 100, 86)
    _box(ax, 1, 76, 30, 8, "Search window\nbookable = C - b - overlap", "blue", fs=4.7)
    _box(ax, 36, 76, 28, 8, "Suspended?\n(trust < 1.5 + warning)", "red", fs=4.7)
    _box(ax, 69, 76, 30, 8, "overlap + b < C ?\nelse declined (409)", "orange", fs=4.7)
    _arrow(ax, 31.5, 80, 35.5, 80)
    _arrow(ax, 64.5, 80, 68.5, 80)
    _box(ax, 1, 60, 30, 9, "Quote fee\nhours x rate x m(trust)\nless account credit", "teal", fs=4.7)
    _box(ax, 36, 60, 28, 9, "Reserve + payment\nStripe or demo", "teal", fs=4.7)
    _box(ax, 69, 60, 30, 9, "Arrival: check in\nparked >= C ?", "orange", fs=4.7)
    _arrow(ax, 84, 76, 84, 69.6)
    _arrow(ax, 31.5, 64.5, 35.5, 64.5)
    _arrow(ax, 64.5, 64.5, 68.5, 64.5, style="<|-")
    _box(ax, 1, 40, 30, 11, "No: status active\nbay used", "green", fs=4.7)
    _box(ax, 36, 40, 31, 11, "Yes: nearest other lot\nwith forecast space\n(haversine) -> active\nalternate booking", "blue", fs=4.7)
    _box(ax, 72, 40, 27, 11, "None: status failed\nfee credited to\naccount", "red", fs=4.7)
    _arrow(ax, 76, 60, 16, 51.6)
    _arrow(ax, 80, 60, 51, 51.6)
    _arrow(ax, 90, 60, 90, 51.6)
    _box(ax, 1, 20, 47, 12, "Check out: on time if t <= end + 10 min\non time: benefit +1, buffer +1 (max 5)\nlate: warning +1, streak reset", "orange", fs=4.6)
    _box(ax, 53, 20, 46, 12, "3 benefits: trust +1 (cap 5)\n2 warnings: trust -1 (floor 0)\ntrust sets the next fee multiplier", "green", fs=4.6)
    _arrow(ax, 16, 40, 24, 32.6)
    _arrow(ax, 50, 40, 36, 32.6)
    _arrow(ax, 48.5, 26, 52.5, 26)
    _box(ax, 1, 3, 98, 10, "Every 30 min: buffer reset to 1 at locations whose last reset is older than 24 h", "grey", fs=4.7)
    return _save(fig, "paper_flow.png")


def results():
    pops = [80, 90, 100, 110]
    fig, ax = plt.subplots(1, 2, figsize=(3.5, 1.95))
    for s in F.STRATS:
        ax[0].plot(pops, [F.pop(n, s, "no_reservation") for n in pops], marker="o", ms=2.2, lw=1.0, color=COL[s], label=F.STRAT_NAME[s])
    ax[0].set_xlabel("vehicles (25 % overstay)", fontsize=5.8)
    ax[0].set_ylabel("requests refused by admission", fontsize=5.8)
    ax[0].set_title("(a) No reservation", fontsize=6.3)
    shares = [0.25, 0.35, 0.45, 0.50]
    x = np.arange(len(shares))
    for i, s in enumerate(F.STRATS):
        ax[1].bar(x + (i - 2) * 0.16, [F.bad(b, s, "no_park") + F.bad(b, s, "alt_overflow") for b in shares], 0.15, color=COL[s])
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([f"{int(b * 100)}%" for b in shares])
    ax[1].set_xlabel("share of overstaying drivers", fontsize=5.8)
    ax[1].set_ylabel("arrivals with no bay", fontsize=5.8)
    ax[1].set_title("(b) No park + alternate full", fontsize=6.3)
    for a in ax:
        a.tick_params(labelsize=5.4)
        a.grid(alpha=0.25)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    ax[0].legend(fontsize=4.6, frameon=False, loc="upper left")
    fig.tight_layout(pad=0.4, w_pad=0.8)
    return _save(fig, "paper_results.png")


def trust():
    ps = list(F.TD.keys())
    xs = [float(p) for p in ps]
    fig, ax = plt.subplots(figsize=(3.5, 1.8))
    ax.errorbar(xs, [F.TD[p]["mean_final_trust"] for p in ps], yerr=[F.TD[p]["std_final_trust"] for p in ps], marker="o", ms=2.5, lw=1.0, capsize=1.5, color=NAVY, label="mean final Trust Score (+/- sd)")
    ax.set_xlabel("probability that a session ends late", fontsize=5.8)
    ax.set_ylabel("score after 100 sessions", fontsize=5.8, color=NAVY)
    ax2 = ax.twinx()
    ax2.plot(xs, [100 * F.TD[p]["share_ever_suspended"] for p in ps], marker="s", ms=2.5, lw=1.0, color=ORANGE, label="drivers ever suspended (%)")
    ax2.set_ylabel("drivers ever suspended (%)", fontsize=5.8, color=ORANGE)
    for a in (ax, ax2):
        a.tick_params(labelsize=5.4)
    ax.grid(alpha=0.25)
    for sp in ("top",):
        ax.spines[sp].set_visible(False)
        ax2.spines[sp].set_visible(False)
    fig.tight_layout(pad=0.4)
    return _save(fig, "paper_trust.png")


def crop(src, box, name, max_w=1100):
    """Crop a real screenshot (left, top, right, bottom in pixels) to docs/figures/paper_<name>.png."""
    os.makedirs(F.FIGS, exist_ok=True)
    im = Image.open(F.shot(src)).convert("RGB").crop(box)
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    p = os.path.join(F.FIGS, name)
    im.save(p)
    return p


def make():
    return {"arch": arch(), "flow": flow(), "results": results(), "trust": trust(),
            "moved": crop("15_moved_to_alternate.png", (256, 200, 1440, 890), "paper_screen_moved.png"),
            "insights": crop("19_admin_insights.png", (276, 225, 1412, 655), "paper_screen_insights.png")}
