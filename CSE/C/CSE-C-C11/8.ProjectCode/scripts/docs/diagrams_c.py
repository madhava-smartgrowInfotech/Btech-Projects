"""Diagrams 10-12: core algorithm flowchart, expense-categoriser pipeline, financial-health score model (FINJARVIS)."""

from .dgm_common import W, poly, save, txt
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, WHITE,
                      arrow, box, canvas, circle, diamond, panel)

RED = "#C0392B"
PALE_RED = "#F9E0DC"


def _lane(ax, y, label):
    txt(ax, 1, y, label, 9, NAVY, ha="left", bold=True)


# ------------------------------------------------------------------------------------------------ 10 algorithm flowchart
def d_algo():
    h_in = 10.8
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    y1, y2, y3 = 87, 54, 25
    # ---- A: validate and categorise
    _lane(ax, y1 + 8.6, "A   Add a transaction: POST /api/transactions")
    box(ax, 9, y1, 14, 8, "Request\n(token, text,\namount, category)", fc=NAVY, fs=8)
    diamond(ax, 30, y1, 20, 12, "description\nnot blank and\namount > 0?", fs=8)
    box(ax, 53, y1, 20, 8.5, "predicted =\npredict_category\n(description)", fc=BLUE, fs=8)
    diamond(ax, 76, y1, 20, 12, "category blank\nor Auto-detect?", fs=8)
    box(ax, 93, y1, 11, 8.5, "category =\npredicted", fc=TEAL, fs=8)
    arrow(ax, (16.1, y1), (20.0, y1), color=GREY)
    arrow(ax, (40.0, y1), (43.0, y1), "yes", color=GREY, lo=(0, 1.8))
    arrow(ax, (63.0, y1), (66.0, y1), color=GREY)
    arrow(ax, (86.0, y1), (87.5, y1), "yes", color=GREY, lo=(0, 1.8))
    box(ax, 30, y1 - 13.0, 18, 6.4, "400: enter a description /\na valid amount", fc=PALE_RED, tc=INK, ec=RED, fs=8)
    arrow(ax, (30, y1 - 6.1), (30, y1 - 9.8), "no", color=RED, lo=(2.0, 0))
    # ---- B: correction and storing
    txt(ax, 12, y2 + 8.4, "B   Manual category, learning and storing", 9, NAVY, ha="left", bold=True)
    box(ax, 9, y2, 14, 8, "category =\nthe user's pick", fc=NAVY, fs=8)
    diamond(ax, 30, y2, 20, 12, "pick differs from\npredicted?", fs=8)
    box(ax, 53, y2, 24, 10.5, "learn_from_correction:\nretrain on seed list +\nuser history + this pick,\nrewrite the pickle (best effort)", fc=ORANGE, fs=7.8)
    box(ax, 77, y2, 20, 9, "add_transaction:\nINSERT row with\nuser_id, amount > 0", fc=BLUE, fs=8)
    box(ax, 94, y2, 11, 9, "201: id,\ncategory", fc=TEAL, fs=8)
    arrow(ax, (16.1, y2), (20.0, y2), color=GREY)
    arrow(ax, (40.0, y2), (40.9, y2), "yes", color=ORANGE, lo=(0, 2.0))
    arrow(ax, (65.1, y2), (66.9, y2), color=GREY)
    arrow(ax, (87.1, y2), (88.4, y2), color=GREY)
    poly(ax, [(30, y2 - 6.1), (30, y2 - 9.0), (77, y2 - 9.0), (77, y2 - 4.7)], color=GREY, lw=1.4)
    txt(ax, 36, y2 - 7.2, "no", 8.2, INK)
    poly(ax, [(93, y1 - 4.4), (93, y2 + 10.5), (77, y2 + 10.5), (77, y2 + 4.7)], color=TEAL, lw=1.4)
    poly(ax, [(76, y1 - 6.1), (76, y1 - 19.0), (9, y1 - 19.0), (9, y2 + 4.1)], color=GREY, lw=1.4)
    txt(ax, 85, y1 - 12.5, "no: the user\nchose a category", 8.2, INK)
    # ---- C: budget alerts
    _lane(ax, y3 + 12.4, "C   When the dashboard or the notification list is opened: check_and_raise_alerts")
    box(ax, 8, y3, 13, 9, "get_budget_status:\nspent / budget\nfor each budget\n(this month)", fc=NAVY, fs=7.8)
    xs = [27, 46, 65]
    labs = ["used >= 100 % ?", "used >= 90 % ?", "used >= 75 % ?"]
    for x, l in zip(xs, labs):
        diamond(ax, x, y3, 15, 10, l, fs=8)
    arrow(ax, (14.6, y3), (19.5, y3), color=GREY)
    arrow(ax, (34.5, y3), (38.5, y3), "no", color=GREY, lo=(0, 1.8))
    arrow(ax, (53.5, y3), (57.5, y3), "no", color=GREY, lo=(0, 1.8))
    box(ax, 83, y3, 14, 6.5, "no alert for\nthis budget", fc=LIGHT, tc=INK, ec=GREY, fs=8)
    arrow(ax, (72.5, y3), (76.0, y3), "no", color=GREY, lo=(0, 1.8))
    yb = y3 - 11.5
    msgs = ["danger: You have\nexceeded your\n<category> budget.", "warning: Your\n<category> budget\nis 90% used.", "warning: Your\n<category> budget\nis 75% used."]
    for x, m in zip(xs, msgs):
        box(ax, x, yb, 15.5, 8.4, m, fc=PALE_RED if "danger" in m else PALE_ORANGE, tc=INK, ec=RED if "danger" in m else ORANGE, fs=7.8)
        arrow(ax, (x, y3 - 5.1), (x, yb + 4.3), "yes", color=ORANGE, lo=(2.0, 0))
    box(ax, 91, yb, 16, 8.4, "insert Notification\nonly if no identical\nmessage exists", fc=TEAL, fs=7.8)
    ybus = yb - 6.0
    for x in xs:
        poly(ax, [(x, yb - 4.3), (x, ybus)], color=GREY, lw=1.3, head=False)
    poly(ax, [(xs[0], ybus), (91, ybus), (91, yb - 4.3)], color=GREY, lw=1.3)
    ax.set_ylim(0, H)
    save(fig, "10_flowchart_algorithm.png")


# ------------------------------------------------------------------------------------------------ 11 categoriser pipeline
def d_pipe():
    h_in = 6.8
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    panel(ax, 0.8, 36, 98.4, H - 37.5, "Training path (ml/expense_classifier.py: train_and_save)", fc="#F7F9FC")
    panel(ax, 0.8, 1.2, 98.4, 33, "Prediction path (predict_category)", fc="#F7F9FC")
    yt = 50
    box(ax, 11, yt, 18, 10.5, "Seed list\nSEED_TRAINING_DATA\n51 pairs, 11 categories\n(3-6 per category)", fc=NAVY, fs=8)
    box(ax, 11, 41.2, 18, 3.8, "extra: history + correction", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.5)
    box(ax, 36, yt, 19, 10.5, "TfidfVectorizer\nlowercase, word\n1-2-grams, min_df = 1", fc=BLUE, fs=8)
    box(ax, 60, yt, 19, 10.5, "LogisticRegression\nmax_iter = 1000\n(C = 1, lbfgs)", fc=BLUE, fs=8)
    box(ax, 84, yt, 20, 10.5, "Pipeline fitted,\npickled to\nml/expense_model.pkl", fc=TEAL, fs=8)
    arrow(ax, (20.1, yt), (26.4, yt), color=GREY)
    arrow(ax, (45.6, yt), (50.4, yt), color=GREY)
    arrow(ax, (69.6, yt), (74.0, yt), color=GREY)
    poly(ax, [(11, 43.1), (11, 44.8)], color=ORANGE, lw=1.3, ls="--")
    txt(ax, 49, 61.2, "learn_from_correction(description, correct_category, user_history) -> train_and_save(extra_examples)  -> same pipeline, retrained and re-saved", 8.2, ORANGE, bold=True)
    # prediction
    yp = 19
    box(ax, 9, yp, 14, 9, "description\n(blank -> Other)", fc=NAVY, fs=8)
    box(ax, 28, yp, 17, 9, "_load_pipeline()\nreads the pickle,\ntrains if missing", fc=BLUE, fs=8)
    diamond(ax, 50, yp, 17, 11, "pipeline loads\nand predicts?", fs=8)
    box(ax, 73, yp, 18, 9, "label =\npipeline.predict\n(never \"Other\")", fc=TEAL, fs=8)
    box(ax, 92, yp, 11, 9, "category", fc=NAVY, fs=8.5, bold=True)
    arrow(ax, (16.1, yp), (19.4, yp), color=GREY)
    arrow(ax, (36.6, yp), (41.4, yp), color=GREY)
    arrow(ax, (58.6, yp), (63.9, yp), "yes", color=GREY, lo=(0, 1.8))
    arrow(ax, (82.1, yp), (86.4, yp), color=GREY)
    box(ax, 50, 6.8, 24, 6.4, "KEYWORD_FALLBACK table:\nfirst keyword found in the lower-cased\ntext; else \"Other\"", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    arrow(ax, (50, yp - 5.6), (50, 10.1), "no (exception)", color=ORANGE, lo=(7.5, 0))
    poly(ax, [(62, 6.8), (92, 6.8), (92, yp - 4.6)], color=ORANGE, lw=1.4)
    poly(ax, [(84, 44.7), (84, 31.0), (28, 31.0), (28, yp + 4.6)], color=TEAL, lw=1.3, ls="--")
    txt(ax, 56, 32.6, "model file read at prediction time", 8.2, TEAL, bg=True)
    save(fig, "11_categoriser_pipeline.png")


# ------------------------------------------------------------------------------------------------ 12 health score model
def d_health():
    h_in = 7.2
    fig, ax = canvas(W, h_in, 100)
    H = 100 * h_in / W
    comps = [("savings_rate", "0.30", "clip(rate / 20 x 100)", NAVY),
             ("expense_ratio", "0.20", "clip((1 - expenses / income) / 0.5 x 100); 0 if no income", NAVY),
             ("budget_adherence", "0.15", "share of budgets with used <= 100 %; 50 if no budgets", BLUE),
             ("emergency_fund", "0.15", "clip(balance / monthly expenses / 6 x 100); 50 if no expenses", BLUE),
             ("investment_diversification", "0.10", "clip(distinct asset types / 5 x 100); 0 if none", TEAL),
             ("goal_progress", "0.10", "mean percent complete of goals; 50 if no goals", TEAL)]
    ytop = H - 6.5
    step = 10.2
    for i, (name, w, f, c) in enumerate(comps):
        y = ytop - i * step
        box(ax, 12.5, y, 22, 7.6, f"{name}\nweight {w}", fc=c, fs=8.2, bold=True)
        box(ax, 43.5, y, 36, 7.6, f"s = {f}", fc=LIGHT, tc=INK, ec=GREY, fs=8.2, r=0.6)
        arrow(ax, (23.6, y), (25.4, y), color=GREY)
        ax.plot([61.6, 64.0], [y, y], color=GREY, lw=1.3, zorder=3)
    ax.plot([64.0, 64.0], [ytop, ytop - 5 * step], color=GREY, lw=1.3, zorder=3)
    arrow(ax, (64.0, H / 2), (66.4, H / 2), color=GREY, lw=1.5)
    circle(ax, 71, H / 2, 4.6, "SUM", fc=ORANGE, fs=10)
    txt(ax, 71, H / 2 - 9.0, "score = round(\nsum of w x s, 1)\nclipped to 0-100", 8.2, INK, bold=True)
    bands = [("Excellent", ">= 90", PALE_TEAL, TEAL), ("Good", ">= 75", PALE_BLUE, BLUE), ("Fair", ">= 60", "#FFF4D6", "#C9A227"), ("Needs Improvement", ">= 40", PALE_ORANGE, ORANGE), ("Critical", "< 40", PALE_RED, RED)]
    for i, (n, r, fc, ec) in enumerate(bands):
        y = H - 12 - i * 7.6
        box(ax, 91, y, 14.5, 6.0, f"{n}\n{r}", fc=fc, tc=INK, ec=ec, fs=8, r=0.6)
    arrow(ax, (75.7, H / 2), (83.6, H / 2), color=GREY, lw=1.5)
    box(ax, 84, 6.2, 30, 7.4, "weakest area = component with the lowest s;\nits fixed reason text is shown beside the score", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.6)
    ax.set_ylim(0, H)
    save(fig, "12_health_score_model.png")


DRAWERS = {"algo": d_algo, "pipe": d_pipe, "health": d_health}
