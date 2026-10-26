"""Diagrams 10-12: core algorithm flowchart, reservation state diagram, Trust Score and buffer policy."""

from matplotlib.patches import Circle, FancyBboxPatch

from .dgm_common import W, poly, save, txt
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, WHITE,
                      arrow, box, canvas, circle, diamond, panel)

RED = "#C0392B"
PALE_RED = "#F9E0DC"


def _lane(ax, y, label):
    txt(ax, 1, y, label, 9, NAVY, ha="left", bold=True)


# ------------------------------------------------------------------------------------------------ 10 algorithm flowchart
def d_algo():
    h_in = 9.4
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    y1, y2, y3 = 76, 47, 13
    # ---- A: request time
    _lane(ax, y1 + 8.6, "A   At request time: POST /api/reservations")
    box(ax, 9, y1, 14, 8, "Request\n(token, location,\nstart, end)", fc=NAVY, fs=8)
    diamond(ax, 29, y1, 17, 11, "Suspended?", fs=8.4)
    diamond(ax, 49, y1, 20, 12, "overlapping\n+ buffer\n< capacity?", fs=8)
    box(ax, 69, y1, 15, 9, "Quote fee:\nhours x rate\nx multiplier,\nminus credit", fc=BLUE, fs=8)
    box(ax, 88, y1, 15, 9, "Reserved;\npayment paid\nor pending", fc=TEAL, fs=8)
    arrow(ax, (16.1, y1), (20.4, y1), color=GREY)
    arrow(ax, (37.6, y1), (39, y1), "no", color=GREY, lo=(0, 1.8))
    arrow(ax, (59, y1), (61.4, y1), "yes", color=GREY, lo=(0.2, 1.8))
    arrow(ax, (76.6, y1), (80.4, y1), color=GREY)
    box(ax, 29, y1 - 13.5, 16, 8, "Declined, 403\nstored with the\nsuspension reason", fc=PALE_RED, tc=INK, ec=RED, fs=8)
    box(ax, 49, y1 - 13.5, 16, 8, "Declined, 409\nstored: window\nfully reserved", fc=PALE_RED, tc=INK, ec=RED, fs=8)
    arrow(ax, (29, y1 - 5.6), (29, y1 - 9.6), "yes", color=RED, lo=(2.2, 0))
    arrow(ax, (49, y1 - 6.1), (49, y1 - 9.6), "no", color=RED, lo=(2.0, 0))
    # ---- B: arrival
    _lane(ax, y2 + 8.6, "B   On arrival: POST /api/reservations/{id}/checkin")
    box(ax, 9, y2, 14, 8, "Check in\n(booking\nreserved)", fc=NAVY, fs=8)
    diamond(ax, 29, y2, 19, 12, "Lot full?\nactive parked\n>= capacity", fs=8)
    box(ax, 50, y2, 18, 10, "nearest_alternate:\nminimum haversine\ndistance with\nforecast space", fc=BLUE, fs=8)
    diamond(ax, 70, y2, 16, 11, "Alternate\nfound?", fs=8.2)
    box(ax, 89, y2, 17, 11, "Original booking\nfailed; new active\nbooking at the\nalternate (parent_id)", fc=TEAL, fs=7.8)
    arrow(ax, (16.1, y2), (19.4, y2), color=GREY)
    arrow(ax, (38.6, y2), (40.9, y2), "yes", color=GREY, lo=(0, 1.8))
    arrow(ax, (59.1, y2), (62, y2), color=GREY)
    arrow(ax, (78.1, y2), (80.4, y2), "yes", color=GREY, lo=(0, 1.8))
    box(ax, 29, y2 - 14, 16, 8, "Booking active:\nthe driver parks\nin the booked lot", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    arrow(ax, (29, y2 - 6.1), (29, y2 - 10.0), "no", color=TEAL, lo=(2.0, 0))
    box(ax, 70, y2 - 14, 17, 8, "Failed; the fee is\ncredited to the\naccount", fc=PALE_RED, tc=INK, ec=RED, fs=8)
    arrow(ax, (70, y2 - 5.6), (70, y2 - 10.0), "no", color=RED, lo=(2.0, 0))
    # ---- C: departure
    _lane(ax, y3 + 12.2, "C   On departure: POST /api/reservations/{id}/checkout")
    box(ax, 9, y3, 14, 8, "Check out\n(booking\nactive)", fc=NAVY, fs=8)
    diamond(ax, 31, y3, 20, 12, "now <= end\n+ 10 min?", fs=8.2)
    box(ax, 66, y3 + 5.6, 32, 8.6, "On time: buffer +1 (max 5);  benefit +1;\n3 consecutive benefits: trust +1 (cap 5)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    box(ax, 66, y3 - 5.8, 32, 8.6, "Late: warning +1, benefit streak reset to 0;\n2 warnings: trust -1 (floor 0)", fc=PALE_RED, tc=INK, ec=RED, fs=8)
    arrow(ax, (16.1, y3), (21, y3), color=GREY)
    poly(ax, [(36, y3 + 4.0), (40, y3 + 5.6), (47.9, y3 + 5.6)], color=TEAL, lw=1.3)
    txt(ax, 41.2, y3 + 8.3, "yes", 8.2, INK)
    poly(ax, [(36, y3 - 4.0), (40, y3 - 5.8), (47.9, y3 - 5.8)], color=RED, lw=1.3)
    txt(ax, 41.2, y3 - 8.6, "no", 8.2, INK)
    box(ax, 92, y3, 13, 14, "Trust score\nselects the\nnext fee\nmultiplier", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    arrow(ax, (82.1, y3 + 5.6), (85.4, y3 + 3.6), color=ORANGE, lw=1.3)
    arrow(ax, (82.1, y3 - 5.8), (85.4, y3 - 3.6), color=ORANGE, lw=1.3)
    ax.set_ylim(0, H)
    save(fig, "10_flowchart_algorithm.png")


# ------------------------------------------------------------------------------------------------ 11 state diagram
def d_state():
    h_in = 6.4
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    circle(ax, 4, 30, 1.8, "", fc=NAVY)
    S = dict(tc=INK, fs=9.2, bold=True, r=1.8)
    box(ax, 28, 30, 15, 8, "reserved", fc=PALE_BLUE, ec=BLUE, **S)
    box(ax, 62, 30, 15, 8, "active", fc=PALE_TEAL, ec=TEAL, **S)
    box(ax, 91, 30, 15, 8, "completed", fc=PALE_TEAL, ec=TEAL, **S)
    box(ax, 28, 6.5, 15, 8, "cancelled", fc=LIGHT, ec=GREY, **S)
    box(ax, 62, 6.5, 15, 8, "failed", fc=PALE_RED, ec=RED, **S)
    box(ax, 28, H - 6.5, 15, 8, "declined", fc=PALE_RED, ec=RED, **S)
    arrow(ax, (5.9, 30), (20.4, 30), "request admitted", color=NAVY, lo=(-0.5, 2.2), fs=8)
    poly(ax, [(4, 31.9), (4, H - 6.5), (20.4, H - 6.5)], color=RED, lw=1.5)
    txt(ax, 12, H - 11.5, "suspended, or\nwindow full", 8.2, RED)
    arrow(ax, (28, 25.9), (28, 10.7), "cancel\n(paid fee -> credit)", color=GREY, lo=(-10.5, 0), fs=8)
    arrow(ax, (35.6, 30), (54.4, 30), "check in, lot has a free bay", color=TEAL, lo=(0, 2.2), fs=8)
    arrow(ax, (69.6, 30), (83.4, 30), "check out", color=TEAL, lo=(0, 2.2), fs=8)
    arrow(ax, (33, 25.9), (56, 9.5), "check in, lot full:\nthis booking fails", color=RED, lo=(10.5, 4.2), fs=8)
    poly(ax, [(62, 10.6), (62, 25.9)], color=PURPLE, lw=1.4, ls="--")
    txt(ax, 80, 17, "an alternate with forecast space gets a\nnew booking that starts as active\n(parent_id = the failed booking);\nwith no alternate the fee is credited", 8.2, PURPLE, bg=True)
    txt(ax, 70, H - 6.5, "Final states: completed, cancelled, failed, declined", 8.6, GREY, style="italic")
    save(fig, "11_reservation_state.png")


# ------------------------------------------------------------------------------------------------ 12 trust score and buffer policy
def d_reward():
    h_in = 6.8
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    panel(ax, 0.8, 1.5, 59, H - 3, "Trust Score (per driver, users table)", fc="#F7F9FC")
    panel(ax, 62, 1.5, 37.2, H - 3, "Hold-back buffer (per location)", fc="#F7F9FC")
    mult = ["1.75", "1.50", "1.25", "1.00", "0.95", "0.90"]
    xs = [8 + 9.8 * i for i in range(6)]
    cy = 30
    for i, x in enumerate(xs):
        low = i < 2
        circle(ax, x, cy, 3.6, str(i), fc=ORANGE if low else (NAVY if i != 3 else TEAL), fs=11)
        txt(ax, x, cy - 6.4, f"fee x{mult[i]}", 8.4, INK)
    txt(ax, xs[3], cy + 6.4, "start", 8, TEAL, bold=True)
    for i in range(5):
        arrow(ax, (xs[i] + 1.8, cy + 3.4), (xs[i + 1] - 1.8, cy + 3.4), color=TEAL, lw=1.4, rad=-0.55)
        arrow(ax, (xs[i + 1] - 1.8, cy - 3.4), (xs[i] + 1.8, cy - 3.4), color=RED, lw=1.4, rad=-0.55)
    txt(ax, 30, 47.6, "up: 3 consecutive on-time checkouts (benefits) add 1, cap 5", 8.4, TEAL, bold=True)
    txt(ax, 30, 12.8, "down: 2 late checkouts (warnings) subtract 1, floor 0", 8.4, RED, bold=True)
    box(ax, 30, H - 9.2, 54, 5.6, "Check-out is on time if now <= end + 10 min.  On time: benefit +1.\nLate: warning +1 and the benefit streak resets to 0.", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, r=0.6)
    box(ax, 30, 6.0, 54, 5.0, "Suspension: score < 1.5 and a warning in the last 14 days refuses the booking\n(24 h cooldown, applied again at every refused request).", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.6)
    # buffer
    bx = [67.5 + 6.9 * i for i in range(5)]
    for i, x in enumerate(bx):
        box(ax, x, 33, 5.2, 6, str(i + 1), fc=NAVY if i else TEAL, fs=11, bold=True, r=0.8)
        if i:
            arrow(ax, (bx[i - 1] + 2.7, 33), (x - 2.7, 33), color=GREY, lw=1.4)
    txt(ax, 81, 39.6, "+1 on every on-time checkout", 8.4, INK, bold=True)
    txt(ax, bx[0], 27.6, "init", 8, TEAL, bold=True)
    txt(ax, bx[4], 27.6, "max", 8, NAVY, bold=True)
    poly(ax, [(bx[4], 29.8), (bx[4], 23), (bx[0], 23), (bx[0], 29.8)], color=ORANGE, lw=1.6)
    txt(ax, 81, 20.6, "reset to 1 when 24 h have passed\nsince the last reset", 8.2, ORANGE, bg=True, bold=True)
    box(ax, 80.6, 47.5, 33, 5.6, "Admission rule:\noverlapping bookings + buffer < capacity", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, r=0.6)
    box(ax, 80.6, 10.2, 33, 8.5, "APScheduler runs reset_buffers_if_due()\nevery 30 minutes; the admin button\n\"Reset buffers\" forces the reset now.\nA late checkout leaves the buffer as is.", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.6)
    ax.set_ylim(0, H)
    save(fig, "12_trust_buffer_policy.png")


DRAWERS = {"algo": d_algo, "state": d_state, "reward": d_reward}
