"""DFD level 1 and level 2 for BotGraph (see make_diagrams.py)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def dfd1():
    fig, ax = canvas(10, 9.4, 100, 94)
    box(ax, 50, 90, 70, 6, "Analyst / moderator (browser)", WHITE, tc=INK, ec=BLUE, fs=8, bold=True)
    for x, y, t in [(20, 68, "1.0\nAuthenticate and\nauthorise (JWT)"), (44, 68, "6.0\nRecord moderator\ndecisions"), (76, 68, "5.0\nServe scores, accounts,\nclusters, metrics"),
                    (11, 30, "2.0\nBuild graph and\nfeatures"), (35, 30, "3.0\nTrain and evaluate\nmodels"), (60, 30, "4.0\nDetect botnet\nclusters"), (85, 30, "7.0\nRetrain on\ndecisions")]:
        ellipse(ax, x, y, 21 if x not in (11, 35, 60, 85) else 20, 12.5, t, PALE_BLUE, BLUE, fs=7.6)
    store(ax, 32, 50, 48, 5, "D1  SQLite: users, reviews, training_runs", fs=7.2)
    store(ax, 78, 50, 40, 5, "D4  models/ and experiments/ artefacts", fs=7.2)
    store(ax, 11, 8, 18, 5, "D2  data/raw", fs=7.4)
    store(ax, 55, 8, 56, 5, "D3  data/processed: graph.npz, accounts.csv", fs=7.4)
    # user -> processes
    arrow(ax, (20, 87), (20, 74.4), "credentials", lo=(7, 0), fs=6.8, color=NAVY)
    arrow(ax, (44, 87), (44, 74.4), "confirm / dismiss", lo=(9, 0), fs=6.8, color=NAVY)
    arrow(ax, (72, 87), (72, 74.4), "queries", lo=(5, 0), fs=6.8, color=NAVY)
    arrow(ax, (82, 74.4), (82, 87), "", color=TEAL)
    ax.text(83.5, 80, "scores,\nclusters", fontsize=6.8, color=INK)
    # D1 links
    arrow(ax, (20, 52.5), (20, 61.7), "users", lo=(4, 0), fs=6.8, color=TEAL)
    arrow(ax, (44, 61.7), (40, 52.5), "reviews", lo=(7, 0), fs=6.8, color=NAVY)
    arrow(ax, (55, 52.5), (68, 62), "decisions, runs", lo=(-5, 2.2), fs=6.4, color=TEAL)
    # D4 links
    arrow(ax, (80, 52.5), (80, 61.7), "", color=TEAL)
    arrow(ax, (63, 36.3), (65, 47.5), "clusters.json", lo=(-8, 0), fs=6.4, color=NAVY)
    arrow(ax, (44, 35.5), (62, 47.5), "weights, scores,\nmetrics", lo=(-8, 1.5), fs=6.4, color=NAVY)
    arrow(ax, (87, 36.3), (87, 47.5), "new artefacts", lo=(-7.5, 0), fs=6.4, color=NAVY)
    arrow(ax, (42, 47.5), (77, 36.5), "decisions as labels", lo=(-6, -2.5), fs=6.4, color=TEAL)
    # D2, D3 links
    arrow(ax, (11, 10.6), (11, 23.7), "public files", lo=(5.5, 0), fs=6.4, color=TEAL)
    arrow(ax, (15, 23.7), (30, 10.5), "graph", lo=(4, 1.5), fs=6.4, color=NAVY)
    arrow(ax, (35, 10.6), (35, 23.7), "", color=TEAL)
    arrow(ax, (60, 10.6), (60, 23.7), "", color=TEAL)
    arrow(ax, (78, 10.6), (85, 23.7), "reads", lo=(5, 0), fs=6.4, color=TEAL)
    ax.text(50, 1.5, "Processes 2.0 to 4.0 and 7.0 run in the ml package (7.0 reuses the 3.0 and 4.0 code in a background thread); 1.0, 5.0 and 6.0 run in the FastAPI routes.",
            ha="center", fontsize=6.9, color=GREY, style="italic")
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 7.6, 100, 76)
    ax.text(50, 73, "DFD level 2 - process 5.0 Serve scores, accounts and clusters (backend/app/routes + services/store.py)", ha="center", fontsize=8.6, color=NAVY, fontweight="bold")
    for x, y, t in [(16, 52, "5.1\nCheck token and\nrole (JWT)"), (50, 52, "5.2\nRank, filter, page\naccounts (score >=\nthreshold, status)"), (84, 52, "5.3\nJoin moderator\ndecisions to\neach account"),
                    (16, 25, "5.6\nCluster view:\nmembers, shared\nbehaviour, graph"), (50, 25, "5.5\nBuild neighbourhood:\ntop-scoring ties and\nlinks between them"), (84, 25, "5.4\nExplain account:\ngradient x input\nof the margin")]:
        ellipse(ax, x, y, 27, 15, t, PALE_BLUE, BLUE, fs=7.6)
    box(ax, 16, 68.5, 22, 5.5, "request + Bearer token", WHITE, tc=INK, ec=BLUE, fs=7.2, bold=True)
    store(ax, 50, 68.5, 26, 4.6, "D1  users, reviews", fs=7.2)
    store(ax, 84, 68.5, 26, 4.6, "D1  reviews (decisions_map)", fs=7.2)
    store(ax, 16, 6, 26, 4.6, "D4  clusters.json", fs=7.4)
    store(ax, 50, 6, 26, 4.6, "D3  ties (graph.npz)", fs=7.4)
    store(ax, 84, 6, 26, 4.6, "D4  sage.pt, scores.npz", fs=7.4)
    arrow(ax, (16, 65.7), (16, 59.7), "", color=NAVY)
    arrow(ax, (29.5, 52), (36.5, 52), "user", lo=(0, 2.0), fs=6.8, color=NAVY)
    arrow(ax, (50, 66.2), (50, 59.7), "", color=TEAL)
    arrow(ax, (63.5, 52), (70.5, 52), "page of\nscored accounts", lo=(0, 4.2), fs=6.4, color=NAVY)
    arrow(ax, (84, 66.2), (84, 59.7), "", color=TEAL)
    arrow(ax, (84, 44.5), (84, 32.7), "account id", lo=(-6.5, 0), fs=6.6, color=NAVY)
    arrow(ax, (70.5, 25), (63.5, 25), "top neighbours", lo=(0, 2.2), fs=6.4, color=NAVY)
    arrow(ax, (84, 8.3), (84, 17.5), "weights, scores", lo=(-9, 0), fs=6.4, color=TEAL)
    arrow(ax, (50, 8.3), (50, 17.5), "", color=TEAL)
    arrow(ax, (36.5, 25), (29.5, 25), "cluster id", lo=(0, 2.2), fs=6.6, color=NAVY)
    arrow(ax, (16, 8.3), (16, 17.5), "", color=TEAL)
    ax.text(50, 0.8, "Outputs to the browser: 5.2 page of accounts, 5.4 reasons, 5.5 neighbourhood graph, 5.6 cluster detail (all JSON, 200 or 404)", ha="center", fontsize=7.0, color=GREY, style="italic")
    save(fig, OUT / "05_dfd_level2.png")


def main():
    dfd1()
    dfd2()


if __name__ == "__main__":
    main()
