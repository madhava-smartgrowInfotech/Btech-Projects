"""Diagrams 06-09: UML class diagram, sequence diagram, use-case diagram, entity-relationship diagram."""

from matplotlib.patches import Ellipse, Rectangle

from .dgm_common import W, actor, poly, save, txt, uml
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, WHITE,
                      arrow, box, canvas, panel)


# ------------------------------------------------------------------------------------------------ 06 UML
def d_uml():
    h_in = 10.1
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    T = H - 0.8
    user = uml(ax, 1, T, 26, "User", ["id: int  PK", "name: str(120)", "email: str(200)  unique", "password_hash: str", "role: driver | admin", "trust_score: float = 3.0",
                                      "benefit_streak: int", "warning_count: int", "account_credit: float", "suspended_until: datetime?", "created_at: datetime"], [], stereotype="entity")
    res = uml(ax, 36, T, 28, "Reservation", ["id: int  PK", "user_id: int  FK", "location_id: int  FK", "start_time: datetime", "end_time: datetime", "status: str", "fee: float",
                                            "fee_multiplier: float", "checked_in_at: datetime?", "checked_out_at: datetime?", "decline_reason: text", "parent_id: int?", "created_at: datetime"], [],
              stereotype="entity", hdr=TEAL)
    loc = uml(ax, 73, T, 26, "ParkingLocation", ["id: int  PK", "name: str(160)", "address: str(255)", "latitude: float", "longitude: float", "capacity: int", "buffer_size: int = 1",
                                                "price_per_hour: float", "last_buffer_reset: datetime", "created_at: datetime"], [], stereotype="entity")
    trust = uml(ax, 1, T - 43.5, 26, "TrustEvent", ["id: int  PK", "user_id: int  FK", "kind: benefit | warning |", "      reward | penalty", "detail: str(255)", "created_at: datetime"], [], stereotype="entity")
    pay = uml(ax, 36, T - 44.2, 28, "Payment", ["id: int  PK", "reservation_id: int  FK unique", "user_id: int  FK", "amount: float", "currency: str", "provider: stripe | demo", "stripe_session_id: str?",
                                                "stripe_payment_intent: str?", "status: pending | paid |", "        refunded | failed", "created_at: datetime"], [], stereotype="entity")
    eng = uml(ax, 73, 55, 26, "engine", [], ["forecast_free()", "nearest_alternate()", "quote_fee()", "fee_multiplier()", "record_checkout_trust()", "suspension_block()", "reset_buffers_if_due()", "haversine_km()"],
              stereotype="module app/engine.py", hdr=ORANGE)
    auth = uml(ax, 73, 24, 26, "auth", [], ["hash_password()", "verify_password()", "create_token()", "current_user()", "admin_user()"], stereotype="module app/auth.py", hdr=PURPLE)
    sch = uml(ax, 1, 21, 26, "BackgroundScheduler", [], ["_job_reset_buffers()", "interval: 30 min"], stereotype="APScheduler", hdr=PURPLE)
    y_rel = T - 9
    # foreign-key relations (solid)
    arrow(ax, (27.1, y_rel), (35.9, y_rel), color=NAVY, lw=1.4, style="-")
    txt(ax, 28.5, y_rel + 2.0, "1", 10, NAVY, bold=True)
    txt(ax, 34.5, y_rel + 2.0, "*", 10, NAVY, bold=True)
    txt(ax, 31.5, y_rel - 2.0, "owns", 9, GREY)
    arrow(ax, (72.9, y_rel), (64.1, y_rel), color=NAVY, lw=1.4, style="-")
    txt(ax, 71.5, y_rel + 2.0, "1", 10, NAVY, bold=True)
    txt(ax, 65.5, y_rel + 2.0, "*", 10, NAVY, bold=True)
    txt(ax, 68.5, y_rel - 2.0, "holds", 9, GREY)
    arrow(ax, (14, T - 34.6), (14, T - 43.6), color=NAVY, lw=1.4, style="-")
    txt(ax, 11.4, T - 36.3, "1", 10, NAVY, bold=True)
    txt(ax, 11.4, T - 41.8, "*", 10, NAVY, bold=True)
    txt(ax, 18.5, T - 39.0, "earns", 9, GREY)
    arrow(ax, (50, T - 39.3), (50, T - 44.3), color=NAVY, lw=1.4, style="-")
    txt(ax, 47.6, T - 40.9, "1", 10, NAVY, bold=True)
    txt(ax, 54.0, T - 42.7, "0..1", 10, NAVY, bold=True)
    poly(ax, [(36, 31), (31.5, 31), (31.5, T - 22), (27.1, T - 22)], color=NAVY, lw=1.4, head=False)
    txt(ax, 33.6, 32.8, "*", 10, NAVY, bold=True)
    txt(ax, 29.3, T - 20.2, "1", 10, NAVY, bold=True)
    txt(ax, 31.5, T - 45, "pays", 9, GREY, bg=True)
    # uses / calls (dashed)
    arrow(ax, (72.9, 54), (64.3, 54), color=ORANGE, lw=1.3, ls="--")
    txt(ax, 68.6, 57.2, "reads,\nupdates", 9, ORANGE)
    arrow(ax, (86, 55.1), (86, 58.8), color=ORANGE, lw=1.3, ls="--")
    txt(ax, 93, 57, "buffer", 9, ORANGE)
    poly(ax, [(14, 7.7), (14, 2), (70.5, 2), (70.5, 38), (72.9, 38)], color=PURPLE, lw=1.3, ls="--")
    txt(ax, 33, 2, "calls reset_buffers_if_due()", 9, PURPLE, bg=True)
    box(ax, 53, 7.2, 24, 6.8, "solid line: foreign key\ndashed line: uses / calls\n1, *, 0..1: multiplicity", fc=LIGHT, tc=INK, ec=GREY, fs=9, r=0.5)
    ax.set_ylim(0, H)
    save(fig, "06_uml_class.png")


# ------------------------------------------------------------------------------------------------ 07 sequence
def d_seq():
    h_in = 9.3
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    X = {"D": 8.5, "C": 25, "A": 42, "E": 59, "B": 76, "S": 92}
    heads = {"D": ("Driver", PALE_BLUE, BLUE, INK), "C": ("React console", NAVY, NAVY, "white"), "A": ("FastAPI (main.py)", NAVY, NAVY, "white"),
             "E": ("engine.py", TEAL, TEAL, "white"), "B": ("SQLite (parksure.db)", PALE_TEAL, TEAL, INK), "S": ("Stripe / demo", PALE_PURPLE, PURPLE, INK)}
    top = H - 3.2
    for k, (lab, fc, ec, tc) in heads.items():
        box(ax, X[k], top, 14.5 if k != "B" else 16.5, 4.6, lab, fc=fc, tc=tc, ec=ec, fs=8.2, r=0.6, bold=True)
        ax.plot([X[k], X[k]], [top - 2.3, 0.8], color=GREY, lw=1.0, ls=(0, (4, 3)), zorder=1)
    msgs = [
        ("D", "C", "enter window, Search", 0), ("C", "A", "GET /api/search", 0), ("A", "B", "overlapping count per location", 0), ("A", "C", "bookable bays per location", 1),
        ("D", "C", "Reserve", 0), ("C", "A", "POST /api/reservations + JWT", 0), ("A", "E", "suspension_block, forecast_free", 0), ("E", "B", "overlap count, trust events", 0),
        ("E", "A", "admit or decline", 1), ("A", "E", "quote_fee (hours x rate x mult.)", 0), ("A", "B", "insert reservation + payment", 0), ("A", "S", "create checkout (or demo link)", 0),
        ("A", "C", "booking, amount due, link", 1), ("D", "S", "pay", 0), ("S", "A", "webhook / confirm: paid", 0),
        ("D", "C", "Check in", 0), ("C", "A", "POST /reservations/{id}/checkin", 0), ("A", "E", "parked >= capacity?  nearest_alternate", 0), ("A", "B", "status active (or alternate / failed)", 0),
        ("D", "C", "Check out", 0), ("C", "A", "POST /reservations/{id}/checkout", 0), ("A", "B", "status completed, checked_out_at", 0), ("A", "E", "record_checkout_trust(on_time)", 0),
        ("E", "B", "trust_events, score, buffer +1", 0), ("A", "C", "message, on_time", 1),
    ]
    y0, step = top - 6.0, (top - 6.0 - 2.5) / (len(msgs) - 1)
    ys = []
    for i, (a, b, lab, ret) in enumerate(msgs):
        y = y0 - i * step
        ys.append(y)
        xa, xb = X[a], X[b]
        d = 0.9 if xb > xa else -0.9
        arrow(ax, (xa + (0.4 if xb > xa else -0.4), y), (xb - d * 0.35, y), color=TEAL if ret else NAVY, ls="--" if ret else "-", lw=1.3)
        txt(ax, (xa + xb) / 2, y + 1.15, lab, 8, INK, bg=True)
        ax.add_patch(Rectangle((xa - 0.35, y - 0.0), 0.0, 0.0))
    for (i0, i1, name) in ((0, 3, "Search"), (4, 14, "Reserve and pay"), (15, 18, "Check in"), (19, 24, "Check out")):
        ya, yb = ys[i0] + step * 0.55, ys[i1] - step * 0.55
        ax.add_patch(Rectangle((1.2, yb), 97.6, ya - yb, fc="#F3F6FA" if i0 in (0, 15) else "#FFFFFF", ec="#C9D3DF", lw=0.9, zorder=0))
        ax.text(98.4, (ya + yb) / 2, name, rotation=90, ha="center", va="center", fontsize=8, color=GREY, style="italic", fontweight="bold")
    ax.set_ylim(0, H)
    save(fig, "07_sequence_diagram.png")


# ------------------------------------------------------------------------------------------------ 08 use case
def _uc(ax, x, y, text, w=21, h=5.4, fc=PALE_BLUE, ec=BLUE):
    ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec=ec, lw=1.3, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=8, color=INK, zorder=3, linespacing=1.1)


def d_usecase():
    h_in = 7.4
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    ax.add_patch(Rectangle((17, 1.5), 68, H - 3.2, fc="#FAFBFD", ec=GREY, lw=1.3, ls="--", zorder=0))
    ax.text(51, H - 3.3, "ParkSure", ha="center", va="center", fontsize=10, fontweight="bold", color=NAVY)
    left = [("Register", 58), ("Log in", 51.8), ("Search availability", 45.6), ("Reserve parking", 39.4), ("Pay for booking", 33.2), ("Cancel booking", 27), ("Check in", 20.8), ("Check out", 14.6), ("View bookings\nand Trust Score", 8.2)]
    for t, y in left:
        _uc(ax, 31, y, t, w=19, h=5.0)
    mids = [("Check availability\n(forecast_free)", 45.6), ("Check suspension", 39.4), ("Move to nearest\nalternate", 14.6 + 0)]
    _uc(ax, 57.5, 45.6, mids[0][0], w=17, h=5.4, fc=PALE_ORANGE, ec=ORANGE)
    _uc(ax, 57.5, 39.4, mids[1][0], w=17, h=5.0, fc=PALE_ORANGE, ec=ORANGE)
    _uc(ax, 57.5, 20.8, mids[2][0], w=17, h=5.4, fc=PALE_ORANGE, ec=ORANGE)
    admin = [("Manage locations", 58), ("Reset buffers", 51.8), ("View overview", 45.6), ("View all bookings", 39.4), ("View users", 33.2), ("View Strategy\nInsights", 27)]
    for t, y in admin:
        _uc(ax, 76, y, t, w=16, h=5.0, fc=PALE_TEAL, ec=TEAL)
    actor(ax, 7, 36, "Driver")
    actor(ax, 93, 40, "Administrator")
    box(ax, 93, 8, 12, 6.5, "Payment\nprovider", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.2, r=0.5, ls="--")
    for t, y in left:
        ax.plot([8.8, 21.6], [30, y], color=GREY, lw=0.9, zorder=1)
    for t, y in admin:
        ax.plot([91, 84.0], [34, y], color=GREY, lw=0.9, zorder=1)
    ax.plot([88, 40.8], [9.5, 33.2], color=PURPLE, lw=1.1, ls="--", zorder=1)
    # include / extend
    arrow(ax, (40.5, 45.6), (49.0, 45.6), "<<include>>", color=ORANGE, ls="--", lw=1.2, lo=(0, 2.0), fs=8)
    arrow(ax, (38, 41.2), (49.3, 44.1), "", color=ORANGE, ls="--", lw=1.2)
    txt(ax, 44.2, 40.6, "<<include>>", 8, ORANGE, bg=True)
    arrow(ax, (38, 38.4), (49.0, 39.2), "", color=ORANGE, ls="--", lw=1.2)
    arrow(ax, (49.0, 19.5), (39.8, 20.4), "<<extend>>", color=ORANGE, ls="--", lw=1.2, lo=(0, 2.2), fs=8)
    save(fig, "08_use_case.png")


# ------------------------------------------------------------------------------------------------ 09 ER
def _table(ax, x, y, w, name, cols, hdr=NAVY):
    lh = 2.5
    h = 4.4 + lh * len(cols) + 0.8
    ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((x, y - 4.4), w, 4.4, fc=hdr, ec=NAVY, lw=1.3, zorder=3))
    ax.text(x + w / 2, y - 2.2, name, ha="center", va="center", color=WHITE, fontsize=11, fontweight="bold", zorder=4)
    for i, (key, col, typ) in enumerate(cols):
        yy = y - 4.4 - 0.4 - lh * (i + 0.5)
        if key:
            ax.add_patch(Rectangle((x + 0.5, yy - 1.0), 3.6, 2.0, fc="#FBE9DA" if key == "PK" else "#E3EEFB", ec="none", zorder=3))
        ax.text(x + 2.3, yy, key, ha="center", va="center", fontsize=9, color=INK, fontweight="bold", zorder=4)
        ax.text(x + 5.0, yy, col, ha="left", va="center", fontsize=10, color=INK, zorder=4, family="DejaVu Sans Mono")
        ax.text(x + w - 0.8, yy, typ, ha="right", va="center", fontsize=9, color=GREY, zorder=4)
    return (x, y - h, w, h)


def d_er():
    h_in = 8.7
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    top = H - 1.0
    _table(ax, 1, top, 30, "users", [("PK", "id", "int"), ("", "name", "str"), ("", "email", "str  unique"), ("", "password_hash", "str"), ("", "role", "str"), ("", "trust_score", "float"),
                                     ("", "benefit_streak", "int"), ("", "warning_count", "int"), ("", "account_credit", "float"), ("", "suspended_until", "datetime"), ("", "created_at", "datetime")])
    _table(ax, 36, top, 30, "reservations", [("PK", "id", "int"), ("FK", "user_id", "int"), ("FK", "location_id", "int"), ("", "start_time", "datetime"), ("", "end_time", "datetime"), ("", "status", "str"),
                                             ("", "fee", "float"), ("", "fee_multiplier", "float"), ("", "checked_in_at", "datetime"), ("", "checked_out_at", "datetime"), ("", "decline_reason", "text"),
                                             ("", "parent_id", "int"), ("", "created_at", "datetime")], hdr=TEAL)
    _table(ax, 71, top, 28, "parking_locations", [("PK", "id", "int"), ("", "name", "str"), ("", "address", "str"), ("", "latitude", "float"), ("", "longitude", "float"), ("", "capacity", "int"),
                                                  ("", "buffer_size", "int"), ("", "price_per_hour", "float"), ("", "last_buffer_reset", "datetime"), ("", "created_at", "datetime")])
    _table(ax, 1, top - 38.5, 30, "trust_events", [("PK", "id", "int"), ("FK", "user_id", "int"), ("", "kind", "str"), ("", "detail", "str"), ("", "created_at", "datetime")])
    _table(ax, 36, top - 43.5, 30, "payments", [("PK", "id", "int"), ("FK", "reservation_id", "int  unique"), ("FK", "user_id", "int"), ("", "amount", "float"), ("", "currency", "str"), ("", "provider", "str"),
                                                ("", "stripe_session_id", "str"), ("", "stripe_payment_intent", "str"), ("", "status", "str"), ("", "created_at", "datetime")])
    y1 = top - 10
    arrow(ax, (31.1, y1), (35.9, y1), color=NAVY, lw=1.4, style="-")
    txt(ax, 32.0, y1 + 2.0, "1", 10, NAVY, bold=True)
    txt(ax, 35.0, y1 + 2.0, "N", 10, NAVY, bold=True)
    arrow(ax, (70.9, y1), (66.1, y1), color=NAVY, lw=1.4, style="-")
    txt(ax, 69.9, y1 + 2.0, "1", 10, NAVY, bold=True)
    txt(ax, 67.0, y1 + 2.0, "N", 10, NAVY, bold=True)
    arrow(ax, (16, top - 32.6), (16, top - 38.4), color=NAVY, lw=1.4, style="-")
    txt(ax, 13.6, top - 34.0, "1", 10, NAVY, bold=True)
    txt(ax, 13.6, top - 37.2, "N", 10, NAVY, bold=True)
    arrow(ax, (51, top - 37.7), (51, top - 43.4), color=NAVY, lw=1.4, style="-")
    txt(ax, 48.6, top - 39.2, "1", 10, NAVY, bold=True)
    txt(ax, 55.4, top - 42.0, "0..1", 10, NAVY, bold=True)
    poly(ax, [(36, top - 52), (33.5, top - 52), (33.5, top - 22), (31.1, top - 22)], color=NAVY, lw=1.4, head=False)
    txt(ax, 34.8, top - 49.8, "N", 10, NAVY, bold=True)
    txt(ax, 32.3, top - 20.0, "1", 10, NAVY, bold=True)
    box(ax, 85, 23, 28, 26, "Notes\nreservations.status: reserved,\nactive, completed, cancelled,\nfailed, declined.\nparent_id holds the id of the\nbooking an alternate replaced\n(plain integer, no foreign key).\nIndexed: users.email,\nreservation user, location,\nstart and end times.", fc=LIGHT, tc=INK, ec=GREY, fs=9, r=0.5)
    ax.set_ylim(0, H)
    save(fig, "09_er_diagram.png")


DRAWERS = {"uml": d_uml, "seq": d_seq, "usecase": d_usecase, "er": d_er}
