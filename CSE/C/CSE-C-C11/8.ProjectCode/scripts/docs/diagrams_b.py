"""Diagrams 06-09: UML class diagram, sequence diagram, use-case diagram, entity-relationship diagram (FINJARVIS)."""

from matplotlib.patches import Ellipse, Rectangle

from .dgm_common import W, actor, poly, save, txt, uml
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, WHITE,
                      arrow, box, canvas, panel)


# ------------------------------------------------------------------------------------------------ 06 UML
def d_uml():
    h_in = 11.0
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    T = H - 0.8
    kw = dict(fs=9.0, lh=2.15)
    bud = uml(ax, 1, T, 27, "Budget", ["id: int  PK", "user_id: int  FK", "category: str(80)", "budget_amount: float", "month: int  1-12", "year: int"], [], stereotype="entity", **kw)
    goal = uml(ax, 1, T - 25.5, 27, "FinancialGoal", ["id: int  PK", "user_id: int  FK", "goal_name: str(120)", "target_amount: float", "current_amount: float", "target_date: date", "status: active |", "   completed | abandoned"], [], stereotype="entity", **kw)
    user = uml(ax, 36.5, T, 27, "User", ["id: int  PK", "name: str(120)", "email: str  unique", "username: str  unique", "password_hash: str", "currency: str = INR", "monthly_income: float", "risk_profile: str", "savings_target: float", "created_at: datetime"], [], stereotype="entity", **kw)
    txn = uml(ax, 72, T, 27, "Transaction", ["id: int  PK", "user_id: int  FK", "date: date", "description: str(255)", "category: str(80)", "amount: float", "transaction_type:", "   income | expense", "payment_method: str", "notes: text"], [], stereotype="entity", hdr=TEAL, **kw)
    inv = uml(ax, 72, T - 36.5, 27, "Investment", ["id: int  PK", "user_id: int  FK", "asset_name: str(120)", "symbol: str(20)", "asset_type: str(30)", "quantity: float", "purchase_price: float", "current_price: float", "purchase_date: date"], [], stereotype="entity", **kw)
    note = uml(ax, 72, T - 68.0, 27, "Notification", ["id: int  PK", "user_id: int  FK", "message: str(255)", "notification_type: str", "created_at: datetime", "is_read: bool"], [], stereotype="entity", **kw)
    # function modules
    mk = dict(fs=8.8, lh=2.15)
    uml(ax, 36.5, T - 36.0, 27, "expense_classifier", [], ["predict_category(desc)", "learn_from_correction()", "train_and_save()"], stereotype="module ml/", hdr=ORANGE, **mk)
    uml(ax, 36.5, T - 54.0, 27, "spending_prediction", [], ["predict_next_month_expense()", "predict_category_spending()", "check_budget_overrun_risk()"], stereotype="module ml/", hdr=ORANGE, **mk)
    uml(ax, 36.5, T - 72.0, 27, "financial_health", [], ["calculate_financial_health()", "score_savings_rate()", "score_budget_adherence() ..."], stereotype="module ml/", hdr=ORANGE, **mk)
    uml(ax, 1, T - 57.0, 27, "budget_service", [], ["get_budget_status()", "check_and_raise_alerts()", "set_budget()"], stereotype="module services/", hdr=PURPLE, **mk)
    uml(ax, 1, T - 75.0, 27, "ai_service", [], ["answer_question()", "generate_insights()"], stereotype="module services/", hdr=PURPLE, **mk)
    # associations: User 1 - * children (solid)
    def rel(p, q, a, b, ax_=ax):
        arrow(ax_, p, q, color=NAVY, lw=1.4, style="-")
        txt(ax_, a[0], a[1], "1", 10, NAVY, bold=True)
        txt(ax_, b[0], b[1], "*", 10, NAVY, bold=True)
    y = T - 12.0
    rel((36.4, y), (28.1, y), (35.0, y + 2.0), (29.5, y + 2.0))
    txt(ax, 32.2, y - 2.0, "sets", 9, GREY)
    rel((63.6, y), (71.9, y), (65.0, y + 2.0), (70.5, y + 2.0))
    txt(ax, 67.8, y - 2.0, "records", 9, GREY)
    # User -> FinancialGoal (channel x = 32)
    poly(ax, [(36.5, T - 21), (32, T - 21), (32, T - 33), (28.1, T - 33)], color=NAVY, lw=1.4, head=False)
    txt(ax, 34.5, T - 19.0, "1", 10, NAVY, bold=True)
    txt(ax, 29.7, T - 31.2, "*", 10, NAVY, bold=True)
    txt(ax, 33.4, T - 26.5, "plans", 9, GREY, bg=True)
    # User -> Investment and Notification (channel x = 67.8)
    poly(ax, [(63.6, T - 21), (67.8, T - 21), (67.8, T - 43), (71.9, T - 43)], color=NAVY, lw=1.4, head=False)
    txt(ax, 65.8, T - 19.0, "1", 10, NAVY, bold=True)
    txt(ax, 70.3, T - 41.2, "*", 10, NAVY, bold=True)
    txt(ax, 66.4, T - 28.0, "holds", 9, GREY, bg=True)
    poly(ax, [(67.8, T - 43), (67.8, T - 73), (71.9, T - 73)], color=NAVY, lw=1.4, head=False)
    txt(ax, 70.3, T - 71.2, "*", 10, NAVY, bold=True)
    txt(ax, 66.4, T - 58.0, "is told", 9, GREY, bg=True)
    box(ax, 17, 5.0, 31, 6.4, "solid line: foreign key, 1 user - many rows\nmodule boxes: functions that take the user id;\nno class instances (see ml/ and services/)", fc=LIGHT, tc=INK, ec=GREY, fs=8, r=0.5)
    ax.set_ylim(0, H)
    save(fig, "06_uml_class.png")


# ------------------------------------------------------------------------------------------------ 07 sequence
def d_seq():
    h_in = 9.6
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    X = {"U": 7.5, "C": 23, "A": 40, "S": 58, "M": 75, "B": 91.5}
    heads = {"U": ("User", PALE_BLUE, BLUE, INK), "C": ("React SPA", NAVY, NAVY, "white"), "A": ("FastAPI\n(main.py)", NAVY, NAVY, "white"),
             "S": ("services/", BLUE, BLUE, "white"), "M": ("ml/ modules", TEAL, TEAL, "white"), "B": ("SQLite\n(finjarvis.db)", PALE_TEAL, TEAL, INK)}
    top = H - 3.4
    for k, (lab, fc, ec, tc) in heads.items():
        box(ax, X[k], top, 13.5, 5.2, lab, fc=fc, tc=tc, ec=ec, fs=8.2, r=0.6, bold=True)
        ax.plot([X[k], X[k]], [top - 2.6, 0.8], color=GREY, lw=1.0, ls=(0, (4, 3)), zorder=1)
    msgs = [
        ("U", "C", "fill form, category = Auto-detect", 0), ("C", "A", "POST /api/transactions + Bearer token", 0), ("A", "B", "read_token, load user row", 0),
        ("A", "M", "predict_category(description)", 0), ("M", "A", "label (TF-IDF + LR; keyword / Other fallback)", 1),
        ("A", "M", "learn_from_correction()  only if a manual pick differs", 0), ("A", "S", "add_transaction(user_id, ...)", 0), ("S", "B", "INSERT transactions row", 0),
        ("A", "C", "201: id, category, auto_categorised", 1), ("U", "C", "open Dashboard", 0), ("C", "A", "GET /api/dashboard", 0),
        ("A", "S", "summary_metrics, get_budget_status", 0), ("S", "B", "SELECT transactions, budgets", 0), ("A", "S", "check_and_raise_alerts()", 0),
        ("S", "B", "INSERT notification (>= 75 %, new message)", 0), ("A", "M", "calculate_financial_health(...)", 0), ("M", "A", "score, rating, components", 1),
        ("A", "C", "metrics, health, alerts, charts (JSON)", 1), ("C", "U", "cards, health ring, budget alerts", 1),
    ]
    y0, step = top - 7.0, (top - 7.0 - 2.5) / (len(msgs) - 1)
    ys = []
    for i, (a, b, lab, ret) in enumerate(msgs):
        y = y0 - i * step
        ys.append(y)
        xa, xb = X[a], X[b]
        d = 1 if xb > xa else -1
        arrow(ax, (xa + 0.4 * d, y), (xb - 0.5 * d, y), color=TEAL if ret else NAVY, ls="--" if ret else "-", lw=1.3)
        txt(ax, (xa + xb) / 2, y + 1.15, lab, 8, INK, bg=True)
    for (i0, i1, name) in ((0, 8, "Add a transaction"), (9, 18, "Open the dashboard")):
        ya, yb = ys[i0] + step * 0.55, ys[i1] - step * 0.55
        ax.add_patch(Rectangle((1.2, yb), 97.6, ya - yb, fc="#F3F6FA" if i0 == 0 else "#FFFFFF", ec="#C9D3DF", lw=0.9, zorder=0))
        ax.text(98.4, (ya + yb) / 2, name, rotation=90, ha="center", va="center", fontsize=8.4, color=GREY, style="italic", fontweight="bold")
    ax.set_ylim(0, H)
    save(fig, "07_sequence_diagram.png")


# ------------------------------------------------------------------------------------------------ 08 use case
def _uc(ax, x, y, text, w=21, h=5.4, fc=PALE_BLUE, ec=BLUE):
    ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec=ec, lw=1.3, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=8, color=INK, zorder=3, linespacing=1.1)


def d_usecase():
    h_in = 8.4
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    ax.add_patch(Rectangle((15, 1.5), 70, H - 3.2, fc="#FAFBFD", ec=GREY, lw=1.3, ls="--", zorder=0))
    ax.text(50, H - 3.3, "FINJARVIS", ha="center", va="center", fontsize=10, fontweight="bold", color=NAVY)
    left = [("Sign up", 69), ("Log in", 63.2), ("Add transaction", 57.4), ("Import CSV / Excel", 51.6), ("Edit or delete\ntransaction", 45.8), ("Set budgets", 40), ("Track goals", 34.2),
            ("Track investments", 28.4), ("View dashboard and\nhealth score", 22.6), ("View analytics\nand forecast", 16.8), ("Ask the assistant", 11.0), ("Download report;\nread notifications", 5.2)]
    for t, y in left:
        _uc(ax, 30, y, t, w=20, h=5.0)
    inc = [("Categorise expense\n(TF-IDF + LR)", 54.5), ("Raise budget alerts\n(75 / 90 / 100 %)", 22.6), ("Fit linear trend\n(>= 3 months)", 16.8)]
    for t, y in inc:
        _uc(ax, 62, y, t, w=19, h=5.4, fc=PALE_ORANGE, ec=ORANGE)
    _uc(ax, 62, 28.4, "Refresh live price", w=17, h=5.0, fc=PALE_PURPLE, ec=PURPLE)
    _uc(ax, 62, 11.0, "Free-form LLM answer", w=17, h=5.0, fc=PALE_PURPLE, ec=PURPLE)
    actor(ax, 6, 40, "User")
    box(ax, 93, 28.4, 12, 6.5, "Price source\n(yfinance)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.2, r=0.5, ls="--")
    box(ax, 93, 11.0, 12, 6.5, "LLM provider\n(optional)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.2, r=0.5, ls="--")
    for t, y in left:
        ax.plot([8.6, 20.0], [32, y], color=GREY, lw=0.9, zorder=1)
    # include / extend
    arrow(ax, (40.0, 57.4), (52.6, 54.8), "", color=ORANGE, ls="--", lw=1.2)
    arrow(ax, (39.5, 51.6), (53.0, 53.8), "", color=ORANGE, ls="--", lw=1.2)
    txt(ax, 46.0, 57.8, "<<include>>", 8, ORANGE, bg=True)
    arrow(ax, (40.0, 22.6), (52.6, 22.6), "<<include>>", color=ORANGE, ls="--", lw=1.2, lo=(0, 2.0), fs=8)
    arrow(ax, (40.0, 16.8), (52.6, 16.8), "<<include>>", color=ORANGE, ls="--", lw=1.2, lo=(0, 2.0), fs=8)
    arrow(ax, (53.4, 28.4), (40.0, 28.4), "<<extend>>", color=PURPLE, ls="--", lw=1.2, lo=(0, 2.0), fs=8)
    arrow(ax, (53.4, 11.0), (40.0, 11.0), "<<extend>>", color=PURPLE, ls="--", lw=1.2, lo=(0, 2.0), fs=8)
    ax.plot([87, 70.5], [28.4, 28.4], color=PURPLE, lw=1.1, ls="--", zorder=1)
    ax.plot([87, 70.5], [11.0, 11.0], color=PURPLE, lw=1.1, ls="--", zorder=1)
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
    h_in = 8.4
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    top = H - 1.0
    _table(ax, 1, top, 30, "budgets", [("PK", "id", "int"), ("FK", "user_id", "int"), ("", "category", "str(80)"), ("", "budget_amount", "float"), ("", "month", "int 1-12"), ("", "year", "int")])
    _table(ax, 36, top, 30, "users", [("PK", "id", "int"), ("", "name", "str(120)"), ("", "email", "str  unique"), ("", "username", "str  unique"), ("", "password_hash", "str"), ("", "currency", "str"),
                                     ("", "monthly_income", "float"), ("", "risk_profile", "str(20)"), ("", "savings_target", "float"), ("", "created_at", "datetime")], hdr=TEAL)
    _table(ax, 71, top, 28, "transactions", [("PK", "id", "int"), ("FK", "user_id", "int"), ("", "date", "date"), ("", "description", "str(255)"), ("", "category", "str(80)"), ("", "amount", "float"),
                                             ("", "transaction_type", "str(10)"), ("", "payment_method", "str(50)"), ("", "notes", "text")])
    r2 = top - 36
    _table(ax, 1, r2, 30, "financial_goals", [("PK", "id", "int"), ("FK", "user_id", "int"), ("", "goal_name", "str(120)"), ("", "target_amount", "float"), ("", "current_amount", "float"), ("", "target_date", "date"), ("", "status", "str(20)")])
    _table(ax, 36, r2, 30, "investments", [("PK", "id", "int"), ("FK", "user_id", "int"), ("", "asset_name", "str(120)"), ("", "symbol", "str(20)"), ("", "asset_type", "str(30)"), ("", "quantity", "float"),
                                            ("", "purchase_price", "float"), ("", "current_price", "float"), ("", "purchase_date", "date")])
    _table(ax, 71, r2, 28, "notifications", [("PK", "id", "int"), ("FK", "user_id", "int"), ("", "message", "str(255)"), ("", "notification_type", "str(30)"), ("", "created_at", "datetime"), ("", "is_read", "bool")])
    y1 = top - 14
    arrow(ax, (35.9, y1), (31.1, y1), color=NAVY, lw=1.4, style="-")
    txt(ax, 35.0, y1 + 2.0, "1", 10, NAVY, bold=True)
    txt(ax, 32.0, y1 + 2.0, "N", 10, NAVY, bold=True)
    arrow(ax, (66.1, y1), (70.9, y1), color=NAVY, lw=1.4, style="-")
    txt(ax, 67.0, y1 + 2.0, "1", 10, NAVY, bold=True)
    txt(ax, 70.0, y1 + 2.0, "N", 10, NAVY, bold=True)
    # users -> investments (vertical)
    users_bottom = top - (4.4 + 2.5 * 10 + 0.8)
    arrow(ax, (51, users_bottom), (51, r2 + 0.1), color=NAVY, lw=1.4, style="-")
    txt(ax, 48.6, users_bottom - 1.8, "1", 10, NAVY, bold=True)
    txt(ax, 48.6, r2 + 2.0, "N", 10, NAVY, bold=True)
    # users -> financial_goals via channel x = 33.5
    poly(ax, [(36, top - 24), (33.5, top - 24), (33.5, r2 - 9), (31.1, r2 - 9)], color=NAVY, lw=1.4, head=False)
    txt(ax, 35.0, top - 22.0, "1", 10, NAVY, bold=True)
    txt(ax, 32.3, r2 - 7.0, "N", 10, NAVY, bold=True)
    # users -> notifications via channel x = 68.5
    poly(ax, [(66, top - 24), (68.5, top - 24), (68.5, r2 - 9), (70.9, r2 - 9)], color=NAVY, lw=1.4, head=False)
    txt(ax, 67.0, top - 22.0, "1", 10, NAVY, bold=True)
    txt(ax, 69.7, r2 - 7.0, "N", 10, NAVY, bold=True)
    box(ax, 16, top - 28.0, 28.6, 8.5, "Every child table has user_id; the ORM relation\nuses cascade=\"all, delete-orphan\", so deleting a\nuser removes all of that user's rows.", fc=LIGHT, tc=INK, ec=GREY, fs=8.2, r=0.5)
    box(ax, 50, 5.2, 96, 5.6, "Indexed: users.email, users.username and every user_id column.  Enumerated text values: transaction_type income | expense; goal status active | completed | abandoned;\n"
                                "notification_type info | warning | danger | success; risk_profile Conservative | Moderate | Aggressive.  No loan or account table exists.", fc=LIGHT, tc=INK, ec=GREY, fs=8, r=0.5)
    ax.set_ylim(0, H)
    save(fig, "09_er_diagram.png")


DRAWERS = {"uml": d_uml, "seq": d_seq, "usecase": d_usecase, "er": d_er}
