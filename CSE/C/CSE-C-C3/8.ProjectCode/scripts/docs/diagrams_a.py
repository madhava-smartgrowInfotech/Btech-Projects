"""Diagrams 01-05: architecture, high-level workflow, DFD levels 0, 1 and 2."""

from matplotlib.patches import FancyBboxPatch

from .dgm_common import W, poly, save, txt
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL,
                      arrow, box, canvas, circle, ellipse, panel, store)


# ------------------------------------------------------------------------------------------------ 01 architecture
def d_arch():
    h_in = 7.3
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    panel(ax, 1, 52, 98, 14, "Presentation tier (browser)")
    box(ax, 21, 57.3, 36, 7.5, "React 19 + Vite console (frontend/src)\nlanding, login, find parking, my bookings,\ntrust score, 5 admin pages", fc=NAVY, fs=8.2, bold=True)
    box(ax, 59, 57.3, 28, 7.5, "Original pages (static/)\nserved by FastAPI at :8403", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8.2)
    box(ax, 86, 57.3, 20, 7.5, "Stripe Checkout\n(test mode, external)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.2, ls="--")
    box(ax, 21, 47.4, 36, 3.8, "Vite dev server :5403  proxies  /api  ->  127.0.0.1:8403", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    arrow(ax, (21, 53.5), (21, 49.4), color=NAVY)

    panel(ax, 1, 21, 98, 24, "Application tier: FastAPI backend, port 8403 (app/)")
    box(ax, 14, 35.0, 22, 11, "main.py\n22 routes under /api\nlifespan: create tables,\nseed, start scheduler", fc=NAVY, fs=8)
    box(ax, 38, 35.0, 22, 11, "auth.py\nJWT HS256 (12 h), bcrypt,\nroles driver / admin", fc=BLUE, fs=8)
    box(ax, 61, 35.0, 20, 11, "schemas.py\npydantic validation\n(422 on bad input)", fc=BLUE, fs=8)
    box(ax, 85, 35.0, 22, 11, "stripe_pay.py\nCheckout session or\noffline demo checkout", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8)
    box(ax, 26, 24.6, 46, 4.8, "engine.py  Smart Availability Engine: admission, hold-back buffer,\nhaversine nearest alternate, Trust Score, fee multiplier", fc=TEAL, fs=8, bold=True)
    box(ax, 85, 24.6, 22, 4.8, "APScheduler job\nbuffer reset, every 30 min", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    arrow(ax, (14, 29.4), (14, 27.1), color=NAVY, lw=1.4)
    arrow(ax, (73.9, 24.6), (49.1, 24.6), color=ORANGE, lw=1.4)
    arrow(ax, (10, 45.5), (10, 41.3), color=NAVY, lw=1.5)
    arrow(ax, (86, 53.3), (88, 40.7), color=PURPLE, lw=1.4, ls="--")
    txt(ax, 93.5, 46.6, "pay / webhook", 8, PURPLE, bg=True)

    panel(ax, 1, 1.5, 98, 17, "Storage")
    box(ax, 22, 8.2, 38, 7, "SQLAlchemy 2.0 ORM\napp/models.py, app/database.py", fc=BLUE, fs=8.2)
    box(ax, 62, 8.2, 36, 7, "parksure.db  (SQLite file)\nusers, parking_locations, reservations,\npayments, trust_events", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    box(ax, 90, 8.2, 16, 7, ".env\nports, Stripe\nkeys, secret", fc=LIGHT, tc=INK, ec=GREY, fs=8)
    arrow(ax, (41.2, 8.2), (43.8, 8.2), color=GREY, lw=1.5)
    arrow(ax, (26, 22.2), (26, 11.8), color=GREY, lw=1.5)
    ax.set_ylim(0, H)
    save(fig, "01_system_architecture.png")


# ------------------------------------------------------------------------------------------------ 02 workflow
def d_flow():
    h_in = 6.2
    fig, ax = canvas(W, h_in, 100)
    top = ["1  Search window\narrival and departure", "2  Availability\nbookable = capacity\n- buffer - overlapping", "3  Reserve request\nPOST /api/reservations",
           "4  Checks\nnot suspended, and\noverlapping + buffer\n< capacity", "5  Fee quote\nhours x rate x trust\nmultiplier, minus credit", "6  Payment\nStripe Checkout or\ndemo confirm"]
    bot = ["7  Arrive, check in\nPOST /checkin", "8  Lot full on arrival?\nno: park in the booked lot\nyes: nearest alternate,\nor failed and credited", "9  Parked", "10  Check out\nend + 10 min grace",
           "11  On time: buffer +1,\nbenefit; late: warning", "12  Trust Score changes\nnext fee multiplier"]
    xs = [9.5 + i * 16.2 for i in range(6)]
    for i, s in enumerate(top):
        box(ax, xs[i], 43, 14.6, 13, s, fc=NAVY, fs=8)
        if i:
            arrow(ax, (xs[i - 1] + 7.4, 43), (xs[i] - 7.4, 43), color=GREY)
    for i, s in enumerate(bot):
        x = xs[i]
        fc = TEAL if i in (1, 4) else BLUE
        box(ax, x, 18, 14.6, 13, s, fc=fc, fs=8)
        if i:
            arrow(ax, (xs[i - 1] + 7.4, 18), (x - 7.4, 18), color=GREY)
    poly(ax, [(xs[5], 36.4), (xs[5], 31.0), (xs[0], 31.0), (xs[0], 24.6)], color=GREY, lw=1.5)
    txt(ax, 50, 33.3, "the driver travels to the lot", 8, GREY, bg=True, style="italic")
    txt(ax, 50, 54.8, "Declined requests (suspended, or window full) are stored with a reason and answered with 403 or 409", 8.4, ORANGE, style="italic")
    arrow(ax, (xs[3], 49.6), (xs[3], 53.0), color=ORANGE, ls="--", lw=1.2)
    box(ax, 27, 4.2, 40, 5.6, "Every outcome is a stored status: reserved, active,\ncompleted, cancelled, failed or declined", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8)
    box(ax, 73, 4.2, 40, 5.6, "A completed trip updates the next request's price\nand the lot's buffer: the loop closes at step 12", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    save(fig, "02_high_level_workflow.png")


# ------------------------------------------------------------------------------------------------ 03 DFD 0
def d_dfd0():
    h_in = 4.7
    fig, ax = canvas(W, h_in, 100)
    circle(ax, 50, 24.5, 12, "ParkSure\n0", fc=NAVY, fs=11)
    box(ax, 10, 24.5, 17, 8, "Driver", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=11, bold=True, r=0.6)
    box(ax, 90, 33, 17, 8, "Administrator", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=10.5, bold=True, r=0.6)
    box(ax, 50, 3.6, 30, 5.5, "Payment provider\n(Stripe or demo checkout)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=9.5, r=0.6, ls="--")
    arrow(ax, (18.6, 29.5), (38.4, 28), "registration, login, search window,\nreservation, check-in, check-out", lo=(0, 5.5), fs=8, color=NAVY)
    arrow(ax, (38.4, 20.5), (18.6, 19.5), "availability, quote, booking status,\nTrust Score, messages", lo=(0, -5.5), fs=8, color=TEAL)
    arrow(ax, (81.4, 37), (61.5, 29.5), "location data,\nreset buffers", lo=(3, 4.5), fs=8, color=NAVY)
    arrow(ax, (61.5, 21.5), (81.4, 29), "overview, users, bookings,\nStrategy Insights", lo=(5, -3.5), fs=8, color=TEAL)
    arrow(ax, (47, 12.5), (47, 6.5), "amount, e-mail,\nreservation id", lo=(-10.5, 0), fs=8, color=PURPLE)
    arrow(ax, (53, 6.5), (53, 12.5), "payment confirmation", lo=(11.5, 0), fs=8, color=PURPLE)
    save(fig, "03_dfd_level0.png")


# ------------------------------------------------------------------------------------------------ 04 DFD 1
def d_dfd1():
    h_in = 9.0
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    ys = {"1": 66, "2": 54, "3": 42, "4": 30, "5": 18, "6": 6}
    names = {"1": "1.0  Authenticate\nusers", "2": "2.0  Search\navailability", "3": "3.0  Reserve\nand pay", "4": "4.0  Check in\n(arrival)", "5": "5.0  Check out\nand trust", "6": "6.0  Administer\nand analyse"}
    for k, y in ys.items():
        hot = k in ("4", "5")
        ellipse(ax, 38, y, 21, 9.6, names[k], fc=PALE_TEAL if hot else PALE_BLUE, ec=TEAL if hot else BLUE, fs=8.4)
    # external entities
    ax.add_patch(FancyBboxPatch((1, 13), 13, 59, boxstyle="round,pad=0,rounding_size=0.6", fc=PALE_BLUE, ec=BLUE, lw=1.3, zorder=2))
    txt(ax, 7.5, 42, "Driver", 10, INK, bold=True)
    box(ax, 7.5, 6, 13, 8, "Administrator", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, bold=True, r=0.6)
    for k, lab in (("1", "credentials"), ("2", "window"), ("3", "booking\nrequest"), ("4", "check-in"), ("5", "check-out")):
        arrow(ax, (14.1, ys[k]), (27.4, ys[k]), color=NAVY, lw=1.2)
        txt(ax, 20.7, ys[k] + 2.9, lab, 8, NAVY)
    arrow(ax, (14.1, 6), (27.4, 6), color=NAVY, lw=1.2)
    txt(ax, 20.7, 8.7, "commands", 8, NAVY)
    # payment provider (above the 3.0 -> D4 flow)
    box(ax, 62, 49.5, 15, 6.5, "Payment\nprovider", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.6, r=0.6, ls="--")
    arrow(ax, (45.6, 45.6), (54.4, 48.2), "amount", lo=(-1.5, 2.6), fs=8, color=PURPLE, lw=1.2)
    arrow(ax, (54.4, 46.8), (46.4, 43.6), "paid", lo=(5.8, -1.4), fs=8, color=PURPLE, lw=1.2)
    # data stores
    store(ax, 87, 66, 22, 6, "D1  users", fs=8.2)
    store(ax, 87, 56, 22, 6, "D2  parking_locations", fs=8.2)
    store(ax, 87, 42, 22, 6, "D4  payments", fs=8.2)
    store(ax, 87, 24, 22, 20, "D3\nreservations", fs=8.2)
    store(ax, 87, 6, 22, 6, "D5  trust_events", fs=8.2)
    arrow(ax, (48.6, 66), (75.8, 66), "user row, token", lo=(0, 1.9), fs=8, color=GREY)
    arrow(ax, (48.6, 56), (75.8, 56), "bays, price, buffer", lo=(0, 1.9), fs=8, color=GREY)
    arrow(ax, (48.6, 42), (75.8, 42), "payment row", lo=(0, -1.9), fs=8, color=GREY)
    arrow(ax, (47.8, 38.6), (75.8, 32), "reservation row", lo=(3, -3.4), fs=8, color=GREY)
    arrow(ax, (48.6, 30), (75.8, 27), "status active / failed", lo=(0, 1.9), fs=8, color=GREY)
    arrow(ax, (48.6, 18), (75.8, 21), "status completed", lo=(0, 1.9), fs=8, color=GREY)
    arrow(ax, (47.6, 14.8), (75.8, 7.4), "benefit / warning", lo=(0, -2.4), fs=8, color=GREY)
    arrow(ax, (48.6, 6), (75.8, 5.6), "reads and writes all stores", lo=(0, -1.9), fs=8, color=GREY)
    box(ax, 50, 78.0, 96, 5.4, "Reads and updates not drawn as separate arrows: 2.0 reads D3 (overlapping bookings); 4.0 reads D2 (alternate search); "
                                "5.0 updates D2 (buffer)\nand D1 (trust score, streak, warnings); the administrator process 6.0 reads and writes D1 to D5.",
        fc=LIGHT, tc=INK, ec=GREY, fs=8, r=0.5)
    ax.set_ylim(0, H)
    save(fig, "04_dfd_level1.png")


# ------------------------------------------------------------------------------------------------ 05 DFD 2
def d_dfd2():
    h_in = 8.0
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    P = dict(fc=PALE_BLUE, ec=BLUE, fs=8.2)
    yt, yb = 48, 20
    ax.add_patch(FancyBboxPatch((1, 15), 13, 44, boxstyle="round,pad=0,rounding_size=0.6", fc=PALE_BLUE, ec=BLUE, lw=1.3, zorder=2))
    txt(ax, 7.5, 40, "Driver", 10.5, INK, bold=True)
    box(ax, 8, 7, 14, 8, "Payment\nprovider", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=9, r=0.6, ls="--")
    ellipse(ax, 36, yt, 20, 11, "3.1  Check\nsuspension", **P)
    ellipse(ax, 62, yt, 20, 11, "3.2  Forecast\nadmission", **P)
    ellipse(ax, 87, yt, 18, 11, "3.3  Quote\nfee", **P)
    ellipse(ax, 87, yb, 18, 11, "3.4  Apply\naccount credit", **P)
    ellipse(ax, 62, yb, 20, 11, "3.5  Store reservation\nand payment", **P)
    ellipse(ax, 36, yb, 20, 11, "3.6  Create checkout\nand reply", fc=PALE_PURPLE, ec=PURPLE, fs=8.2)
    arrow(ax, (14.1, yt + 0.5), (25.8, yt + 0.5), "reservation\nrequest", lo=(0, 4), fs=8, color=NAVY)
    arrow(ax, (46.2, yt), (51.8, yt), color=GREY)
    arrow(ax, (72.2, yt), (77.8, yt), color=GREY)
    arrow(ax, (87, yt - 5.7), (87, yb + 5.7), color=GREY)
    arrow(ax, (77.8, yb), (72.2, yb), color=GREY)
    arrow(ax, (51.8, yb), (46.2, yb), color=GREY)
    arrow(ax, (25.8, yb + 0.5), (14.1, yb + 0.5), "quote, link,\nmessage", lo=(0, 4.0), fs=8, color=TEAL)
    arrow(ax, (27.6, yb - 4.4), (15.2, 10.4), "amount", lo=(3.6, 2.6), fs=8, color=PURPLE)
    arrow(ax, (15.2, 6.2), (31.0, yb - 5.2), "confirmation", lo=(1.0, -3.4), fs=8, color=PURPLE)
    # declined path
    poly(ax, [(62, yt - 5.7), (62, 36.5), (36, 36.5)], color=ORANGE, ls="--", lw=1.3, head=False)
    poly(ax, [(36, yt - 5.7), (36, 36.5), (14.1, 36.5)], color=ORANGE, ls="--", lw=1.3)
    txt(ax, 48, 33.6, "declined: stored with the reason, 403 / 409 returned to the driver", 8.4, ORANGE, style="italic")
    # stores
    store(ax, 36, 68, 22, 5.6, "D1  users", fs=8.2)
    store(ax, 62, 68, 22, 5.6, "D2  parking_locations", fs=8.2)
    store(ax, 36, 4.2, 22, 5.6, "D3  reservations", fs=8.2)
    store(ax, 62, 4.2, 22, 5.6, "D4  payments", fs=8.2)
    store(ax, 87, 4.2, 22, 5.6, "D1  users (credit)", fs=8.2)
    arrow(ax, (36, 65.2), (36, yt + 5.7), "role, trust,\ncooldown", lo=(-8.5, 0), fs=8, color=GREY)
    arrow(ax, (62, 65.2), (62, yt + 5.7), "capacity,\nbuffer, price", lo=(-8.5, 0), fs=8, color=GREY)
    arrow(ax, (87, yb - 5.7), (87, 7.1), "debit", lo=(5, 0), fs=8, color=GREY)
    arrow(ax, (62, yb - 5.7), (62, 7.1), "payment row", lo=(8.3, 0), fs=8, color=GREY)
    arrow(ax, (54, yb - 4.8), (40, 7.1), "reservation\nrow", lo=(0.5, 0.4), fs=8, color=GREY)
    box(ax, 49, 28.0, 36, 3.8, "3.2 also reads D3: overlapping reserved / active bookings", fc="white", tc=INK, ec=GREY, fs=8, r=0.4)
    ax.set_ylim(0, H)
    save(fig, "05_dfd_level2.png")


DRAWERS = {"arch": d_arch, "flow": d_flow, "dfd0": d_dfd0, "dfd1": d_dfd1, "dfd2": d_dfd2}
