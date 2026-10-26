"""Diagrams 01-05: architecture, high-level workflow, DFD levels 0, 1 and 2 (FINJARVIS)."""

from matplotlib.patches import FancyBboxPatch

from .dgm_common import W, poly, save, txt
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL,
                      arrow, box, canvas, circle, ellipse, panel, store)


# ------------------------------------------------------------------------------------------------ 01 architecture
def d_arch():
    h_in = 8.6
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    # presentation
    panel(ax, 1, 59, 98, 18, "Presentation tier (browser)")
    box(ax, 27, 67.4, 50, 8.6, "React 18 + TypeScript single-page app (frontend/src)\nVite, Tailwind v4, Recharts, TanStack Query, Axios\n13 pages: landing, login, sign-up, dashboard, transactions, analytics,\nbudgets, goals, investments, assistant, reports, notifications, profile", fc=NAVY, fs=8, bold=True)
    box(ax, 73, 67.4, 40, 8.6, "Original Streamlit app (app.py, ui/)\nsame services, same SQLite file;\nkept as the first front end", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8)
    box(ax, 27, 60.9, 50, 2.9, "Vite dev server :5411   ->   /api   ->   FastAPI :8411  (CORS: localhost:5411 only)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    # application
    panel(ax, 1, 20, 98, 36, "Application tier: FastAPI backend, port 8411 (backend/main.py, no business logic)")
    box(ax, 15, 46, 22, 11, "main.py\n33 routes under /api\nbearer token (HMAC-SHA256,\n7 days), pydantic checks", fc=NAVY, fs=8)
    box(ax, 39, 46, 20, 11, "auth/authentication.py\nutils/security.py (bcrypt)\nutils/validators.py", fc=BLUE, fs=8)
    box(ax, 70, 46, 38, 11, "services/  (every query scoped by user_id)\ntransaction, budget, goal, investment,\nanalytics, ai (assistant), report, data_import", fc=BLUE, fs=8)
    box(ax, 18, 30.5, 31, 12.5, "ml/expense_classifier.py\nTF-IDF (1-2 grams) + logistic regression\nseed list of 51 examples, keyword fallback,\nlearn_from_correction", fc=TEAL, fs=8, bold=True)
    box(ax, 52, 30.5, 31, 12.5, "ml/spending_prediction.py\nmonthly expense totals ->\nnumpy.polyfit(x, y, 1) -> next month\n(needs >= 3 months), category trends", fc=TEAL, fs=8, bold=True)
    box(ax, 84, 30.5, 25, 12.5, "ml/financial_health.py\nsix weighted components\n-> score 0-100,\nfive rating bands", fc=TEAL, fs=8, bold=True)
    box(ax, 14, 23.0, 24, 3.0, "backend/demo_seed.py: demo account", fc=LIGHT, tc=INK, ec=GREY, fs=8)
    box(ax, 59, 23.0, 54, 3.0, "services/report_service.py: PDF (ReportLab), Excel (OpenPyXL), CSV into reports/", fc=LIGHT, tc=INK, ec=GREY, fs=8)
    arrow(ax, (26.1, 46), (28.9, 46), color=GREY)
    arrow(ax, (60, 40.4), (52, 36.9), color=GREY, lw=1.3)
    arrow(ax, (76, 40.4), (84, 36.9), color=GREY, lw=1.3)
    arrow(ax, (63, 40.4), (24, 36.9), color=GREY, lw=1.3)
    arrow(ax, (12, 59.4), (12, 51.7), color=NAVY, lw=1.6)
    txt(ax, 19, 55.6, "HTTP / JSON", 8, NAVY, bg=True)
    # storage
    panel(ax, 1, 1.5, 98, 16, "Storage and external services")
    box(ax, 21, 8.2, 34, 6.8, "SQLAlchemy 2 ORM  (database/models.py)\nusers, transactions, budgets,\nfinancial_goals, investments, notifications", fc=BLUE, fs=8)
    box(ax, 51, 8.2, 20, 6.8, "finjarvis.db\n(SQLite file, or the\npath in FINJARVIS_DB)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    box(ax, 70.5, 8.2, 18, 6.8, "ml/expense_model.pkl\npickled pipeline, read and\nrewritten by the classifier", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    box(ax, 91.7, 8.2, 13, 6.8, "optional, off by\ndefault: yfinance\nprices, Anthropic\nLLM", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=7.8, ls="--")
    arrow(ax, (38.2, 8.2), (41.0, 8.2), color=GREY, lw=1.5)
    arrow(ax, (29, 24.2), (24, 11.8), color=GREY, lw=1.5)
    poly(ax, [(89.2, 46), (97.6, 46), (97.6, 11.8)], color=PURPLE, lw=1.3, ls="--")
    ax.set_ylim(0, H)
    save(fig, "01_system_architecture.png")


# ------------------------------------------------------------------------------------------------ 02 workflow
def d_flow():
    h_in = 6.2
    fig, ax = canvas(W, h_in, 100)
    top = ["1  Sign up / log in\nbcrypt hash, signed\ntoken (7 days)", "2  Add data\nform entry or CSV /\nExcel import with\npreview", "3  Categorise\nTF-IDF + logistic\nregression label,\nor the user's pick",
           "4  Store\ntransaction row\nscoped to user_id\n(SQLite)", "5  Analyse\nsummary metrics,\ncategory totals,\nmonthly trend", "6  Forecast\nlinear trend over\nmonthly totals\n(>= 3 months)"]
    bot = ["7  Budgets\nspend vs monthly\nbudget; alerts at\n75 / 90 / 100 %", "8  Health score\nsix weighted\ncomponents,\n0-100 and a band", "9  Goals and holdings\nprogress, required\nmonthly saving,\nportfolio value",
           "10  Assistant\nrule-routed answers\nfrom the user's own\ndata + disclaimer", "11  Dashboard\ncards and charts\nfor the current\nmonth", "12  Reports and\nnotifications\nPDF, Excel, CSV;\nunread alerts"]
    xs = [9.5 + i * 16.2 for i in range(6)]
    for i, s in enumerate(top):
        box(ax, xs[i], 43, 14.6, 13, s, fc=NAVY if i != 2 else TEAL, fs=8)
        if i:
            arrow(ax, (xs[i - 1] + 7.4, 43), (xs[i] - 7.4, 43), color=GREY)
    for i, s in enumerate(bot):
        x = xs[i]
        fc = TEAL if i in (0, 1) else BLUE
        box(ax, x, 18, 14.6, 13, s, fc=fc, fs=8)
        if i:
            arrow(ax, (xs[i - 1] + 7.4, 18), (x - 7.4, 18), color=GREY)
    poly(ax, [(xs[5], 36.4), (xs[5], 31.0), (xs[0], 31.0), (xs[0], 24.6)], color=GREY, lw=1.5)
    txt(ax, 50, 33.3, "everything below is computed from the stored transactions, budgets, goals and holdings", 8, GREY, bg=True, style="italic")
    txt(ax, 50, 54.8, "A manual category that differs from the model's label is a correction: the model is retrained on the seed list, the user's history and that correction", 8.2, ORANGE, style="italic")
    arrow(ax, (xs[2], 49.6), (xs[2], 53.0), color=ORANGE, ls="--", lw=1.2)
    box(ax, 27, 4.2, 40, 5.6, "Every request carries the signed token; the server reads\nthe user id from it and never from the request body", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8)
    box(ax, 73, 4.2, 40, 5.6, "Optional and off by default: live price refresh (yfinance)\nand free-form LLM answers (needs AI_API_KEY)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8)
    save(fig, "02_high_level_workflow.png")


# ------------------------------------------------------------------------------------------------ 03 DFD 0
def d_dfd0():
    h_in = 5.0
    fig, ax = canvas(W, h_in, 100)
    circle(ax, 50, 26, 12.5, "FINJARVIS\n0", fc=NAVY, fs=11)
    box(ax, 10, 26, 17, 16, "User", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=11, bold=True, r=0.6)
    box(ax, 88, 38.5, 20, 7, "Price source\n(yfinance, optional)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.8, r=0.6, ls="--")
    box(ax, 88, 12, 20, 7, "LLM provider\n(Anthropic, optional)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.8, r=0.6, ls="--")
    arrow(ax, (18.6, 31.5), (38.0, 29.6), "sign-up, login, transactions, CSV / Excel\nfile, budgets, goals, holdings, questions", lo=(0, 6.0), fs=8, color=NAVY)
    arrow(ax, (38.0, 22.5), (18.6, 20.5), "dashboard, categories, forecast, health score,\nbudget alerts, answers, reports", lo=(0, -6.0), fs=8, color=TEAL)
    arrow(ax, (80, 38.0), (60.5, 31.0), color=PURPLE, ls="--")
    arrow(ax, (59.5, 33.0), (78.0, 39.8), color=PURPLE, ls="--")
    txt(ax, 64, 41.0, "symbol", 8, INK)
    txt(ax, 75, 31.5, "latest price", 8, INK)
    arrow(ax, (59.5, 18.5), (78.0, 11.5), color=PURPLE, ls="--")
    arrow(ax, (78.0, 13.8), (60.5, 21.0), color=PURPLE, ls="--")
    txt(ax, 70, 8.3, "question + data context", 8, INK)
    txt(ax, 74, 20.6, "answer", 8, INK)
    save(fig, "03_dfd_level0.png")


# ------------------------------------------------------------------------------------------------ 04 DFD 1
def d_dfd1():
    h_in = 9.4
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    ys = {"1": 78, "2": 66, "3": 52, "4": 40, "5": 28, "6": 14}
    names = {"1": "1.0  Authenticate\nusers", "2": "2.0  Record and\ncategorise", "3": "3.0  Manage budgets,\ngoals, holdings", "4": "4.0  Analyse,\nforecast, score", "5": "5.0  Assistant\nand insights", "6": "6.0  Reports and\nnotifications"}
    for k, y in ys.items():
        hot = k in ("2", "4")
        ellipse(ax, 36, y, 21, 9.6, names[k], fc=PALE_TEAL if hot else PALE_BLUE, ec=TEAL if hot else BLUE, fs=8.4)
    ax.add_patch(FancyBboxPatch((1, 7), 13, 78, boxstyle="round,pad=0,rounding_size=0.6", fc=PALE_BLUE, ec=BLUE, lw=1.3, zorder=2))
    txt(ax, 7.5, 46, "User", 10.5, INK, bold=True)
    for k, lab in (("1", "credentials"), ("2", "transaction,\nfile"), ("3", "budget, goal,\nholding"), ("4", "page request"), ("5", "question"), ("6", "download,\nread alerts")):
        arrow(ax, (14.1, ys[k]), (25.4, ys[k]), color=NAVY, lw=1.2)
        txt(ax, 19.7, ys[k] + 3.4, lab, 8, NAVY)
    box(ax, 62, 37, 15, 6.0, "Price source\n(yfinance)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.4, r=0.6, ls="--")
    arrow(ax, (43.5, 48.5), (55.5, 39.2), color=PURPLE, lw=1.2, ls="--")
    arrow(ax, (55.5, 35.6), (44.4, 44.2), color=PURPLE, lw=1.2, ls="--")
    txt(ax, 53.0, 45.4, "symbol", 8, INK, bg=True)
    txt(ax, 49.0, 36.6, "price", 8, INK, bg=True)
    box(ax, 62, 27, 15, 6.0, "LLM provider\n(optional)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.4, r=0.6, ls="--")
    arrow(ax, (45.2, 27.0), (54.5, 27.0), color=PURPLE, lw=1.2, ls="--")
    txt(ax, 50, 29.2, "context", 8, INK, bg=True)
    arrow(ax, (54.5, 25.2), (45.2, 25.2), color=PURPLE, lw=1.2, ls="--")
    txt(ax, 50, 23.0, "answer", 8, INK, bg=True)
    sx, sw = 88, 22
    store(ax, sx, 80, sw, 5.0, "D1  users", fs=8.2)
    store(ax, sx, 70, sw, 5.0, "D2  transactions", fs=8.2)
    store(ax, sx, 62, sw, 5.0, "D7  expense_model.pkl", fs=8.2)
    store(ax, sx, 54, sw, 4.4, "D3  budgets", fs=8.2)
    store(ax, sx, 49, sw, 4.4, "D4  financial_goals", fs=8.2)
    store(ax, sx, 44, sw, 4.4, "D5  investments", fs=8.2)
    store(ax, sx, 14, sw, 5.0, "D6  notifications", fs=8.2)
    arrow(ax, (46.5, 78.5), (76.8, 80), "user row, token", lo=(0, 1.9), fs=8, color=GREY)
    arrow(ax, (46.5, 67.5), (76.8, 70), "transaction row", lo=(0, 1.9), fs=8, color=GREY)
    arrow(ax, (45.5, 63.0), (76.8, 62), "retrain on correction", lo=(0, -1.9), fs=8, color=ORANGE, lw=1.2, ls="--")
    arrow(ax, (46.5, 52.5), (76.8, 54), "budget row", lo=(0, 1.9), fs=8, color=GREY)
    arrow(ax, (45.8, 50.5), (76.8, 49), "goal row", lo=(8, -1.6), fs=8, color=GREY)
    arrow(ax, (44.6, 48.0), (76.8, 44), "holding row", lo=(8, -1.9), fs=8, color=GREY)
    arrow(ax, (46.5, 14), (76.8, 14), "alert rows (read: Notifications)", lo=(0, 1.9), fs=8, color=GREY)
    box(ax, 50, 91.3, 97, 6.4, "Not drawn as separate arrows: 2.0 predicts with D7 and reads D2 for the correction history; 4.0, 5.0 and 6.0 read D2 to D5 (4.0 on the dashboard and 6.0 on the notification list also write D6 through the budget-alert check);\n"
                                "every read and write is filtered by the user id taken from the token; 3.0 writes budgets (D3), goals (D4) and holdings (D5).",
        fc=LIGHT, tc=INK, ec=GREY, fs=8, r=0.5)
    ax.set_ylim(0, H)
    save(fig, "04_dfd_level1.png")


# ------------------------------------------------------------------------------------------------ 05 DFD 2 (process 4.0)
def d_dfd2():
    h_in = 9.0
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    P = dict(fc=PALE_BLUE, ec=BLUE, fs=8.2)
    yt, yb = 52, 20
    ax.add_patch(FancyBboxPatch((1, 12), 13, 52, boxstyle="round,pad=0,rounding_size=0.6", fc=PALE_BLUE, ec=BLUE, lw=1.3, zorder=2))
    txt(ax, 7.5, 38, "User", 10.5, INK, bold=True)
    ellipse(ax, 36, yt, 21, 11.5, "4.1  Load the user's\ntransactions\n(DataFrame)", **P)
    ellipse(ax, 62, yt, 21, 11.5, "4.2  Summary metrics\nand category totals", **P)
    ellipse(ax, 87, yt, 20, 11.5, "4.3  Monthly\nexpense totals", **P)
    ellipse(ax, 87, yb, 20, 11.5, "4.4  Fit linear trend\npolyfit(x, y, 1),\nclip at 0", fc=PALE_TEAL, ec=TEAL, fs=8.2)
    ellipse(ax, 62, yb, 21, 11.5, "4.5  Category trends\nand budget\noverrun check", **P)
    ellipse(ax, 36, yb, 21, 11.5, "4.6  Financial health\nscore (six weights)", fc=PALE_TEAL, ec=TEAL, fs=8.2)
    arrow(ax, (14.1, yt + 0.5), (25.5, yt + 0.5), "request:\ndashboard,\nanalytics", lo=(0, 4.4), fs=8, color=NAVY)
    arrow(ax, (46.5, yt), (51.5, yt), color=GREY)
    arrow(ax, (72.5, yt), (77.0, yt), color=GREY)
    arrow(ax, (89, yt - 5.8), (89, yb + 5.8), "monthly\nseries", lo=(5.5, 0), fs=8, color=GREY)
    arrow(ax, (77.0, yb), (72.5, yb), "slope,\nintercept", lo=(0, 3.4), fs=8, color=GREY)
    arrow(ax, (51.5, yb), (46.5, yb), color=GREY)
    # result bus to the user
    yb2 = 36
    poly(ax, [(55, yt - 4.4), (55, yb2), (14.1, yb2)], color=TEAL, lw=1.4)
    poly(ax, [(36, yb + 5.8), (36, yb2)], color=TEAL, lw=1.4, head=False)
    poly(ax, [(69, yb + 4.2), (69, yb2)], color=TEAL, lw=1.4, head=False)
    poly(ax, [(81, yb + 4.5), (81, yb2)], color=TEAL, lw=1.4, head=False)
    poly(ax, [(81, yb2), (55, yb2)], color=TEAL, lw=1.4, head=False)
    txt(ax, 24.5, yb2 - 4.4, "metrics, charts,\nnext-month forecast,\nrisk alerts, score", 8.2, TEAL, bold=True)
    # stores
    store(ax, 36, 75, 24, 5.6, "D2  transactions", fs=8.2)
    store(ax, 62, 4.4, 22, 5.6, "D3  budgets", fs=8.2)
    store(ax, 36, 4.4, 22, 5.6, "D4  goals,  D5  holdings", fs=8.0)
    arrow(ax, (36, 72.2), (36, yt + 5.8), "rows of this user", lo=(-9.5, 0), fs=8, color=GREY)
    arrow(ax, (62, 7.2), (62, yb - 5.8), "budget status", lo=(8.5, 0), fs=8, color=GREY)
    arrow(ax, (36, 7.2), (36, yb - 5.8), "goal progress,\nasset types", lo=(-9.5, 0), fs=8, color=GREY)
    arrow(ax, (57, 7.2), (41.5, 14.6), "", color=GREY)
    box(ax, 74, 72, 30, 6.0, "needs >= 3 distinct months, otherwise\n\"available: false\" with a message", fc="white", tc=INK, ec=ORANGE, fs=8, r=0.4, ls="--")
    arrow(ax, (86, yt + 5.8), (80, 68.9), "", color=ORANGE, ls="--", lw=1.1)
    ax.set_ylim(0, H)
    save(fig, "05_dfd_level2.png")


DRAWERS = {"arch": d_arch, "flow": d_flow, "dfd0": d_dfd0, "dfd1": d_dfd1, "dfd2": d_dfd2}
