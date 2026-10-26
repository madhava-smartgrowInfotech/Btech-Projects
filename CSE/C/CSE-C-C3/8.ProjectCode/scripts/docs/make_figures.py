"""Result charts for the documents, drawn from experiments/**/metrics.json into docs/figures/ (matplotlib, 150 dpi).

    python -m scripts.docs.make_figures
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#5B6B7F", "#C0392B"
COL = {"static_0": GREY, "static_1": BLUE, "static_3": NAVY, "dynamic_parksure": ORANGE, "dynamic_paper": TEAL}
MARK = {"static_0": "s", "static_1": "o", "static_3": "^", "dynamic_parksure": "D", "dynamic_paper": "v"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.titlesize": 10, "axes.titleweight": "bold"})


def out(name):
    os.makedirs(F.FIGS, exist_ok=True)
    return os.path.join(F.FIGS, name)


def save(fig, name):
    fig.savefig(out(name), dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def lines(ax, xs, getter, ylabel, title, xlabel):
    for s in F.STRATS:
        ax.plot(xs, [getter(x, s) for x in xs], marker=MARK[s], color=COL[s], label=F.STRAT_NAME[s], lw=1.8, ms=5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)


def f01():
    pops = [80, 90, 100, 110]
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    lines(ax[0], pops, lambda n, s: F.pop(n, s, "no_reservation"), "refused by admission (of N x 10 requests)", "(a) No reservation", "vehicles")
    lines(ax[1], pops, lambda n, s: F.pop(n, s, "no_park") + F.pop(n, s, "alt_overflow"), "arrivals with no bay (mean per run)", "(b) No park + alternate overflow", "vehicles")
    lines(ax[2], pops, lambda n, s: 100 * F.pop(n, s, "success_rate"), "requests ending in a parked car (%)", "(c) Success rate", "vehicles")
    ax[0].legend(fontsize=7.5, frameon=False)
    fig.suptitle("Buffer policies against population size (25 % bad vehicles, 30 runs per point)", fontsize=10.5, y=1.03)
    save(fig, "f01_buffer_population.png")


def f02():
    shares = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    xs = [int(s * 100) for s in shares]
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    lines(ax[0], shares, lambda b, s: F.bad(b, s, "no_reservation"), "refused by admission (mean per run)", "(a) No reservation", "share of bad vehicles")
    lines(ax[1], shares, lambda b, s: F.bad(b, s, "no_park") + F.bad(b, s, "alt_overflow"), "arrivals with no bay (mean per run)", "(b) No park + alternate overflow", "share of bad vehicles")
    lines(ax[2], shares, lambda b, s: F.bad(b, s, "suspended"), "refused by Trust lockout (mean)", "(c) Suspended", "share of bad vehicles")
    for a in ax:
        a.set_xticks(shares)
        a.set_xticklabels([f"{x}%" for x in xs])
    ax[0].legend(fontsize=7.5, frameon=False)
    fig.subplots_adjust(wspace=0.38)
    fig.suptitle("Buffer policies against the share of overstaying vehicles (population 80-110, 30 runs per point)", fontsize=10.5, y=1.03)
    save(fig, "f02_buffer_badshare.png")


def f03():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    w = 0.2
    x = np.arange(len(F.STRATS))
    keys = [("no_park", "No park (no alternate)", RED), ("alt_overflow", "Alternate physically full", ORANGE), ("moved_to_alternate", "Moved to alternate (served)", TEAL)]
    for i, (k, lab, c) in enumerate(keys):
        vals = [F.bad(0.5, s, k) for s in F.STRATS]
        ax.bar(x + (i - 1) * w * 1.35, vals, w * 1.25, label=lab, color=c)
        for xi, v in zip(x + (i - 1) * w * 1.35, vals):
            ax.text(xi, v + 0.15, f"{v:.1f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([F.STRAT_NAME[s].replace(" (", "\n(") for s in F.STRATS], fontsize=8)
    ax.set_ylabel("events per run (mean of 30)")
    ax.set_title("What happens at the gate when 50 % of drivers overstay")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f03_arrival_outcomes.png")


def f04():
    ps = list(F.TD.keys())
    xs = [float(p) for p in ps]
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].errorbar(xs, [F.TD[p]["mean_final_trust"] for p in ps], yerr=[F.TD[p]["std_final_trust"] for p in ps], marker="o", color=NAVY, capsize=3)
    ax[0].set_ylim(-0.2, 5.4)
    ax[0].set_xlabel("probability that a session ends late")
    ax[0].set_ylabel("trust score after 100 sessions (mean +/- sd)")
    ax[0].set_title("(a) Final Trust Score")
    ax[1].plot(xs, [100 * F.TD[p]["share_ever_suspended"] for p in ps], marker="s", color=ORANGE, label="drivers ever suspended (%)")
    ax2 = ax[1].twinx()
    ax2.plot(xs, [F.TD[p]["mean_fee_multiplier"] for p in ps], marker="D", color=TEAL, label="mean fee multiplier")
    ax2.set_ylabel("fee multiplier", color=TEAL)
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax[1].set_xlabel("probability that a session ends late")
    ax[1].set_ylabel("drivers ever suspended (%)", color=ORANGE)
    ax[1].set_title("(b) Suspension and fee multiplier")
    save(fig, "f04_trust_dynamics.png")


def f05():
    eps = {k: v for k, v in F.LAT["endpoints"].items() if not k.startswith("throughput")}
    names = list(eps)
    mean = [eps[k]["mean_ms"] for k in names]
    p95 = [eps[k]["p95_ms"] for k in names]
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    y = np.arange(len(names))
    ax.barh(y, mean, color=BLUE, label="mean")
    ax.scatter(p95, y, color=ORANGE, zorder=3, label="p95", s=22)
    for yi, m, q in zip(y, mean, p95):
        ax.text(max(m, q) + 6, yi, f"{m:.1f}", va="center", fontsize=7.5)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 360)
    ax.set_xlabel("milliseconds, 200 sequential requests per endpoint (bar = mean, dot = p95)")
    ax.set_title("ParkSure API response time on 127.0.0.1")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f05_api_latency.png")


def f06():
    t = F.SEED["insights_60d"]["totals"]
    keys = ["fixed_0", "fixed_1", "fixed_3", "dynamic"]
    lab = ["No buffer", "Fixed 1", "Fixed 3", "Dynamic (ParkSure)"]
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    x = np.arange(4)
    ax.bar(x - 0.18, [t[k]["unable_to_park"] for k in keys], 0.34, color=RED, label="Unable to park")
    ax.bar(x + 0.18, [t[k]["declined"] for k in keys], 0.34, color=ORANGE, label="Declined")
    for xi, k in zip(x, keys):
        ax.text(xi - 0.18, t[k]["unable_to_park"] + 0.8, str(t[k]["unable_to_park"]), ha="center", fontsize=8)
        ax.text(xi + 0.18, t[k]["declined"] + 0.8, str(t[k]["declined"]), ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(lab, fontsize=8.5)
    ax.set_ylabel("requests (60-day seeded history)")
    ax.set_title("Strategy Insights: same history replayed under four buffer policies")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f06_seeded_insights.png")


def f07():
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5), sharey=True)
    x = np.arange(len(F.STRATS))
    for a, share in zip(ax, (0.25, 0.5)):
        on = [F.abl(share, True, s, "success_rate") * 100 for s in F.STRATS]
        off = [F.abl(share, False, s, "success_rate") * 100 for s in F.STRATS]
        a.bar(x - 0.2, on, 0.38, color=NAVY, label="Trust Score on (as shipped)")
        a.bar(x + 0.2, off, 0.38, color=TEAL, label="Trust Score off")
        for xi, v in zip(x - 0.2, on):
            a.text(xi, v + 0.8, f"{v:.0f}", ha="center", fontsize=7.5)
        for xi, v in zip(x + 0.2, off):
            a.text(xi, v + 0.8, f"{v:.0f}", ha="center", fontsize=7.5)
        a.set_xticks(x)
        a.set_xticklabels([F.STRAT_NAME[s].replace(" (", "\n(") for s in F.STRATS], fontsize=7.5)
        a.set_title(f"{int(share * 100)} % bad vehicles")
        a.set_ylim(0, 108)
    ax[0].set_ylabel("requests ending in a parked car (%)")
    ax[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle("Effect of the Trust Score lockout on the success rate (population 80-110, 30 runs)", fontsize=10.5, y=1.02)
    save(fig, "f07_trust_ablation.png")


def f08():
    pops = [80, 90, 100, 110]
    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    lines(ax, pops, lambda n, s: 100 * F.pop(n, s, "utilisation"), "bay-hours used / bay-hours available (%)", "Bay utilisation by policy (25 % bad vehicles)", "vehicles")
    ax.legend(fontsize=7.5, frameon=False)
    save(fig, "f08_utilisation.png")


def f09():
    tr = [o["accepted"] for o in F.RACE["per_trial"]]
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ax.bar(range(1, len(tr) + 1), tr, color=[RED if t > 1 else TEAL for t in tr])
    ax.axhline(1, color=GREY, ls="--", lw=1)
    ax.set_xlabel("trial (20 simultaneous requests, 1 bookable bay)")
    ax.set_ylabel("reservations accepted")
    ax.set_yticks(range(0, max(tr) + 2))
    ax.set_title("Concurrency probe: accepted bookings per trial")
    save(fig, "f09_race_probe.png")


def main():
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09):
        fn()


if __name__ == "__main__":
    main()
