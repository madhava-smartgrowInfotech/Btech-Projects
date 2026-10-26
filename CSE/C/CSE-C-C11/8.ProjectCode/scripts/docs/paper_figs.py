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


def _box(ax, x, y, w, h, text, fc="grey", ec=NAVY, fs=5.6, bold=False, lw=0.7, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=ec, lw=lw, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, style="-|>", lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 3.05, 100, 87)
    _box(ax, 1, 73, 98, 12, "Web console - React 18 + TypeScript + Vite (port 5411)\n13 pages: dashboard, transactions, analytics, budgets, goals,\ninvestments, assistant, reports, notifications, profile", "blue", fs=4.8, bold=True)
    _box(ax, 1, 54, 98, 14, "FastAPI service (port 8411) - 33 routes under /api, bearer-token guard\n(the original Streamlit pages call the same service functions)", "teal", fs=4.9, bold=True)
    _arrow(ax, 50, 73, 50, 68.6, style="<|-|>")
    _arrow(ax, 50, 54, 50, 49.6, style="<|-|>")
    _box(ax, 1, 31, 98, 18, "Service layer: transactions · budgets · goals · investments\nanalytics · assistant (rules + optional LLM) · reports · import", "orange", fs=4.9, bold=True)
    _box(ax, 1, 14, 31, 13, "ml/expense_classifier\nTF-IDF + logistic\nregression (51 seeds)", "green", fs=4.5)
    _box(ax, 34.5, 14, 31, 13, "ml/spending_prediction\nlinear trend over\nmonthly totals", "green", fs=4.5)
    _box(ax, 68, 14, 31, 13, "ml/financial_health\nsix weighted parts\nscore 0-100", "green", fs=4.5)
    for x in (16.5, 50, 83.5):
        _arrow(ax, x, 31, x, 27.6)
    _box(ax, 1, 1, 47, 9, "SQLAlchemy 2 + SQLite finjarvis.db\nusers · transactions · budgets · goals ·\ninvestments · notifications", "grey", fs=4.3)
    _box(ax, 52, 1, 47, 9, "auth: bcrypt hashes, HMAC-SHA256 tokens\nvalidators · PDF/Excel/CSV writers\nyfinance refresh (optional)", "grey", fs=4.3)
    _arrow(ax, 25, 14, 25, 10.6, style="<|-|>")
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 2.7, 100, 77)
    ax.set_ylim(9, 86)
    _box(ax, 1, 74, 30, 10, "Add transaction\nor import CSV/Excel\n(row checks, preview)", "blue", fs=4.6)
    _box(ax, 36, 74, 28, 10, "Category given?\nno: TF-IDF + LR\nlabel (never 'Other')", "orange", fs=4.6)
    _box(ax, 69, 74, 30, 10, "Save row for the user\nmanual label differs:\nretrain with correction", "teal", fs=4.6)
    _arrow(ax, 31.5, 79, 35.5, 79)
    _arrow(ax, 64.5, 79, 68.5, 79)
    _box(ax, 69, 54, 30, 12, "Budget check when the\ndashboard is read: used\n>= 75/90/100 % -> alert", "red", fs=4.6)
    _arrow(ax, 84, 74, 84, 66.6)
    _box(ax, 36, 54, 28, 12, "Monthly expense\ntotals per user\n(from stored rows)", "grey", fs=4.6)
    _arrow(ax, 68.5, 60, 64.5, 60)
    _box(ax, 1, 54, 30, 12, ">= 3 months?\nyes: polyfit degree 1\nnext month, max(0, .)", "orange", fs=4.6)
    _arrow(ax, 35.5, 60, 31.5, 60)
    _box(ax, 1, 33, 30, 12, "Forecast, trend label\n(slope > 1 up, < -1 down),\nbudget overrun risk", "green", fs=4.6)
    _arrow(ax, 16, 54, 16, 45.6)
    _box(ax, 36, 33, 28, 12, "Health score:\nsavings, expenses, budgets,\ncash cushion, assets, goals", "green", fs=4.5)
    _arrow(ax, 50, 54, 50, 45.6)
    _box(ax, 69, 33, 30, 12, "Assistant: route by\nintent, answer from SQL\nelse fixed help text", "blue", fs=4.6)
    _arrow(ax, 84, 54, 84, 45.6)
    _box(ax, 1, 12, 98, 15, "Dashboard, analytics, notifications and PDF / Excel / CSV\nreports show these results; every answer comes from the\nlogged-in user's own rows with a not-financial-advice notice", "grey", fs=4.8)
    for x in (16, 50, 84):
        _arrow(ax, x, 33, x, 27.6)
    return _save(fig, "paper_flow.png")


def results():
    fig = plt.figure(figsize=(3.5, 3.75))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.95])
    ax = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])]
    tiers = ["A", "B", "C"]
    x = np.arange(3)
    for i, (nm, d, c) in enumerate((("TF-IDF + LR", F.CLS["tfidf_lr"], NAVY), ("keyword table", F.CLS["keyword_table"], ORANGE), ("majority", F.CLS["majority_class"], GREY))):
        ax[0].bar(x + (i - 1) * 0.27, [d["accuracy_by_tier"][t] * 100 for t in tiers], 0.26, color=c, label=nm)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels([chr(10).join(t) for t in (("A seed-", "like"), ("B state-", "ment"), ("C unseen", "merchant"))])
    ax[0].set_ylabel("accuracy (%)", fontsize=5.8)
    ax[0].set_title("(a) Categoriser, 66 per tier", fontsize=6.3)
    ax[0].legend(fontsize=4.6, frameon=False, loc="upper right")
    rows = F.FC["sim_mape_by_history_pct_noise_0.10"]
    hs = [r["history_months"] for r in rows]
    for key, c, mk, nm in (("linear_trend (app)", ORANGE, "D", "linear trend (app)"), ("mean_of_all", BLUE, "s", "mean of all"), ("mean_of_last_3", TEAL, "^", "mean of last 3")):
        ax[1].plot(hs, [r[key] for r in rows], marker=mk, ms=2.2, lw=1.0, color=c, label=nm)
    ax[1].set_xlabel("months of history (simulated)", fontsize=5.4)
    ax[1].set_ylabel("one-step MAPE (%)", fontsize=5.8)
    ax[1].set_title("(b) Forecast, simulation", fontsize=6.3)
    ax[1].legend(fontsize=4.6, frameon=False, loc="upper right")
    bt = F.FC["demo_backtest"]
    months, actual, steps = bt["months"], bt["actual"], bt["steps"]
    ax[2].plot([m[2:] for m in months], actual, "-o", color="black", lw=1.4, ms=3, label="actual")
    xs = [s_["predict_month"][2:] for s_ in steps]
    for key, c, mk, nm in (("linear_trend (app)", ORANGE, "D", "trend (app)"), ("mean_of_all", BLUE, "s", "mean of all"), ("mean_of_last_3", TEAL, "^", "mean of last 3"), ("last_value", GREY, "v", "last value")):
        ax[2].plot(xs, [s_[key] for s_ in steps], marker=mk, ms=2.6, lw=0.9, ls="--", color=c, label=f"{nm} (MAPE {bt['mape_pct'][key]:.1f} %)")
    ax[2].set_ylabel("INR per month", fontsize=5.8)
    ax[2].set_title("(c) Demo account: forecasts of months 4-6 (3 test points)", fontsize=6.3)
    ax[2].legend(fontsize=4.6, frameon=False, loc="upper left")
    for a in ax:
        a.tick_params(labelsize=5.2)
        a.grid(alpha=0.25)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    fig.tight_layout(pad=0.4, w_pad=0.8, h_pad=0.8)
    return _save(fig, "paper_results.png")


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
    return {"arch": arch(), "flow": flow(), "results": results(),
            "dash": crop("05_dashboard.png", (280, 190, 1420, 810), "paper_screen_dashboard.png"),
            "assist": crop("15_assistant.png", (280, 270, 1420, 830), "paper_screen_assistant.png")}
