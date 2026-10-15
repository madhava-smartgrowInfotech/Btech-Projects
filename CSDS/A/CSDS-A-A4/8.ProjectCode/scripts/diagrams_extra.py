"""Two extra diagrams drawn for the slide decks (larger type than the report versions)."""
from __future__ import annotations

from diagram_kit import AMBER_L, GREEN_L, INDIGO_L, Canvas


def flowchart_wide(out):
    c = Canvas(10.4, 6.6)
    bw, bh = 17.5, 9.5
    xs = [10.5, 31.5, 52.5, 73.5, 94.5]
    y1, y2, y3 = 52, 30, 9

    def box(cx, cy, t, fc=INDIGO_L, w=bw, h=bh):
        return c.box(cx - w / 2, cy - h / 2, w, h, t, fc=fc, fs=7.4, r=1.2)
    box(xs[0], y1, "Build instance:\ndistances, time, cost,\ncapacity")
    box(xs[1], y1, "Construct start set:\ngreedy k-medoids")
    box(xs[2], y1, "Price start set:\nexact assignment MIP")
    c.diamond(xs[3], y1, 18.5, 12, "feasible?\n(else add hubs)", fs=7.2)
    box(xs[4], y1, "Rank candidates;\nbuild swap / drop /\nadd moves")
    box(xs[4], y2, "Screen moves by\ngreedy estimate\n(within 6%)")
    box(xs[3], y2, "Price next move:\nexact assignment\nMIP (cached)")
    c.diamond(xs[2], y2, 18.5, 12, "cheaper than\ncurrent plan?", fs=7.2)
    box(xs[1], y2, "Accept move\n(first improvement)", fc=GREEN_L)
    c.diamond(xs[2], y3, 21, 12, "more promising moves\nand time < 70%?", fs=6.8)
    box(xs[1], y3, "Kernel search:\nMIP over <= 24 hubs", fc=INDIGO_L)
    box(xs[0], y3, "Return hubs,\nallocation, log", fc=GREEN_L)
    for a, b in ((0, 1), (1, 2)):
        c.arrow((xs[a] + bw / 2, y1), (xs[b] - bw / 2, y1))
    c.arrow((xs[2] + bw / 2, y1), (xs[3] - 9.25, y1))
    c.arrow((xs[3] + 9.25, y1), (xs[4] - bw / 2, y1), label="yes", loff=(0, 1.8), fs=6.5)
    c.arrow((xs[4], y1 - bh / 2), (xs[4], y2 + bh / 2))
    c.arrow((xs[4] - bw / 2, y2), (xs[3] + bw / 2, y2))
    c.arrow((xs[3] - bw / 2, y2), (xs[2] + 9.25, y2))
    c.arrow((xs[2] - 9.25, y2), (xs[1] + bw / 2, y2), label="yes", loff=(0, 1.8), fs=6.5)
    c.path([(xs[1], y2 + bh / 2), (xs[1], 40.5), (xs[4] - 6, 40.5), (xs[4] - 6, y1 - bh / 2)], label="restart from the new hub set", seg=1, loff=(-8, 1.6), fs=6.5)
    c.arrow((xs[2], y2 - 6), (xs[2], y3 + 6), label="no", loff=(2.4, 0), fs=6.5)
    c.path([(xs[2] + 10.5, y3), (xs[3], y3), (xs[3], y2 - bh / 2 - 0.4)], label="yes: next move", seg=0, loff=(0, 1.8), fs=6.5)
    c.arrow((xs[2] - 10.5, y3), (xs[1] + bw / 2, y3), label="no", loff=(0, 1.8), fs=6.5)
    c.arrow((xs[1] - bw / 2, y3), (xs[0] + bw / 2, y3))
    c.save(out)


def decision_logic(out):
    c = Canvas(4.4, 5.4)
    cx = 22

    def box(y, t, fc=INDIGO_L, w=34, h=7.5):
        return c.box(cx - w / 2, y - h / 2, w, h, t, fc=fc, fs=7.6, r=1.2)
    box(49.5, "Candidate move:\nswap, drop or add a hub")
    c.diamond(cx, 38.5, 30, 10, "greedy estimate\n<= 1.06 x current\ncost?", fs=6.8)
    box(27, "Price exactly:\nassignment MIP (CBC)")
    c.diamond(cx, 16.5, 30, 10, "cheaper than the\ncurrent plan?", fs=7.2)
    c.box(cx - 17.5, 1.2, 15.5, 6, "accept,\nre-rank", fc=GREEN_L, fs=7.4, r=1)
    c.box(cx + 2, 1.2, 15.5, 6, "try next\nmove", fc=AMBER_L, fs=7.4, r=1)
    c.arrow((cx, 45.7), (cx, 43.6))
    c.arrow((cx, 33.5), (cx, 30.8), label="yes", loff=(2.4, 0), fs=6.6)
    c.arrow((cx, 23.2), (cx, 21.6))
    c.arrow((cx - 6, 12.2), (cx - 9.75, 7.2), label="yes", loff=(-3.0, 0.4), fs=6.6)
    c.arrow((cx + 6, 12.2), (cx + 9.75, 7.2), label="no", loff=(3.0, 0.4), fs=6.6)
    c.text(cx + 19.6, 38.5, "no:\nskip", fs=6.4, italic=True)
    c.arrow((cx + 15, 38.5), (cx + 17.6, 38.5), head=False)
    c.save(out)
