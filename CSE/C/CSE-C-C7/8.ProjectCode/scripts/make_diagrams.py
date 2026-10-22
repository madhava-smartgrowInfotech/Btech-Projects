"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does:
  app/main.py, app/api_routes.py (FastAPI routes), app/recommender.py (hybrid ranker, success + uplift models),
  app/models.py (six tables), app/security.py (tokens), scripts/train_pipeline.py (offline training).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diagram_kit as K
from diagram_kit import (BLUE, GOLD, GREEN, INK, LINE, NAVY, ORANGE, PURPLE, SLATE, arrow, box, canvas, diamond, entity, process, save, store, uml_class)
from matplotlib.patches import Circle, Ellipse, Rectangle

PINK = "#C2456B"


# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11.5, 7.6, "System architecture of LearnPathIQ", ty=78)
    for x, w, label in ((1, 20, "Presentation tier"), (24, 25, "Application tier (FastAPI)"), (52, 24, "Recommendation tier"), (79, 20, "Data tier")):
        ax.add_patch(Rectangle((x, 6), w, 64, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 67.6, label, ha="center", fontsize=9.2, color=SLATE, fontweight="bold")
    box(ax, 2.5, 38, 17, 22, "React 19 SPA\nVite dev server\nport 5407\n\n12 pages: Landing,\nCatalog, Dashboard,\nRecommendations,\nLearning path, Insights,\nActivity, Profile,\nAnalytics", fc="#E8F0FC", ec=BLUE, fs=6.9)
    box(ax, 2.5, 12, 17, 14, "Original Jinja2 UI\nserver-rendered pages\nport 8407\n(/, /dashboard, /path ...)", fc="#FFF1EA", ec=ORANGE, fs=7.2)
    box(ax, 25.5, 55, 22, 10, "app/main.py\nFastAPI app, seed_courses(),\nstatic mount, Jinja pages", fc="#E6F6EF", ec=GREEN, fs=7.5)
    box(ax, 25.5, 32, 22, 17, "app/api_routes.py\n18 JSON routes under /api\nrequire_user() via cookie\nlpq_token / X-Token", fc="#E6F6EF", ec=GREEN, fs=7.8)
    box(ax, 25.5, 12, 22, 14, "security.py + schemas.py\npbkdf2_sha256, token_urlsafe,\nPydantic v2 validation", fc="#EFEBFC", ec=PURPLE, fs=7.6)
    box(ax, 53.5, 35, 21, 12, "rank_courses()\nhybrid score of 8 terms\nper course, top-N", fc="#E6F6EF", ec=GREEN, fs=7.8)
    box(ax, 53.5, 21, 21, 11.5, "content_scores() TF-IDF\nskill, topic, goal, rating\nbehavioral_boost()", fc=K.PAPER, ec=NAVY, fs=7.6)
    box(ax, 53.5, 8, 21, 11.5, "engagement_level()\npredict_success()\nuplift_scores() T-learner\nvia load_ml_bundle()", fc=K.PAPER, ec=NAVY, fs=7.4)
    box(ax, 80.5, 46, 17, 11, "SQLite learnpathiq.db\nSQLAlchemy 2 ORM\n6 tables", fc="#FFF8E5", ec=GOLD, fs=7.8)
    box(ax, 80.5, 59, 17, 8, "data/catalog/courses.json\n24 seeded courses", fc="#FFF8E5", ec=GOLD, fs=7.2)
    box(ax, 80.5, 29, 17, 11, "models/*.joblib\nartifacts/metrics\nartifacts/plots (3 PNG)", fc="#FFF8E5", ec=GOLD, fs=7.4)
    box(ax, 80.5, 8.5, 17, 11, "scripts/train_pipeline.py\n(offline, seed 42)", fc="#EFEBFC", ec=PURPLE, fs=7.2, ls="--")
    arrow(ax, (19.5, 48), (25.5, 42), "/api\n(proxy)", color=BLUE, off=(-2.2, 3.4), fs=7)
    arrow(ax, (19.5, 19), (25.5, 60), None, color=ORANGE)
    arrow(ax, (36.5, 55), (36.5, 49), None)
    arrow(ax, (36.5, 32), (36.5, 26), None)
    arrow(ax, (47.5, 41), (53.5, 41), "calls", off=(0, 1.8), fs=7.2)
    arrow(ax, (64, 35), (64, 32.5), None)
    arrow(ax, (64, 21), (64, 19.5), None)
    arrow(ax, (47.5, 50), (80.5, 52), "ORM rows", off=(0, 2.4), color=GREEN, fs=7.2)
    arrow(ax, (47.5, 62), (80.5, 63), "seed at start-up", off=(0, 2.2), fs=7.2, ls="--")
    arrow(ax, (74.5, 12), (80.5, 33), "load", off=(-1.6, -1.8), fs=7.2, ls="--")
    arrow(ax, (89, 19.5), (89, 29), "writes", off=(3.6, 0), fs=7.2, ls="--", color=PURPLE)
    ax.text(50, 2.2, "Dashed = offline or start-up only. The model bundle is loaded once and cached; recommendations are recomputed on every request.",
            ha="center", fontsize=7.6, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11.5, 4.9, "High-level workflow of one learner session", ty=52)
    steps = [
        ("1  Register / sign in", "pbkdf2 hash check\nHttpOnly cookie lpq_token", NAVY),
        ("2  Build profile", "education, skill level,\ninterests, goals, weekly hours", BLUE),
        ("3  Score catalog", "TF-IDF + skill + topic\n+ goal + rating terms", ORANGE),
        ("4  Predict + uplift", "success probability and\nbenefit of 5 actions", PURPLE),
        ("5  Rank + explain", "8-term hybrid score,\ntop-N with reasons", GREEN),
        ("6  Learn + log", "view, start, quiz, complete,\ndismiss ... to interactions", GOLD),
        ("7  Adapt", "behaviour boost and\nengagement change at once", NAVY),
        ("8  Review", "dashboard, learning path,\ninsights, model analytics", BLUE),
    ]
    w, gap = 21.4, 2.0
    for i, (t, s, c) in enumerate(steps):
        row_y = 28 if i < 4 else 6
        xx = 1.5 + (i % 4) * (w + gap)
        box(ax, xx, row_y, w, 15, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 10.4), w, 4.6, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 12.7, t, ha="center", va="center", color="white", fontsize=8.8, fontweight="bold")
        ax.text(xx + w / 2, row_y + 5.0, s, ha="center", va="center", color=INK, fontsize=7.8, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 6), (xx + w + gap, row_y + 6), None)
    ax.annotate("", xy=(1.5 + w / 2, 21.4), xytext=(1.5 + 3 * (w + gap) + w / 2, 28),
                arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=1.4, connectionstyle="angle,angleA=180,angleB=90,rad=0"))
    ax.text(50, 47, "Steps 6 and 7 form a loop: every logged event changes the next ranking, without retraining.", ha="center", fontsize=8.3, color=SLATE, style="italic")
    save(fig, "02_high_level_workflow.png")


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(11, 5.4, "Data flow diagram, level 0 (context)", ty=58)
    entity(ax, 3, 28, 17, 14, "Learner")
    process(ax, 50, 35, 15, "LearnPathIQ\nRecommendation\nSystem", "0", fs=9)
    store(ax, 76, 42, 22, 8, "SQLite: users, profiles,\ninteractions, logs", "D1")
    store(ax, 76, 26, 22, 8, "course catalog (24)", "D2")
    store(ax, 76, 8, 22, 8, "trained model bundle", "D3")
    arrow(ax, (20, 38.5), (35.3, 38.5), "credentials, profile,\ninteraction events", off=(0, 4.6), fs=7.8)
    arrow(ax, (35.3, 31), (20, 31), "ranked courses, learning path,\ninsights, model metrics", off=(0, -5.0), fs=7.8)
    arrow(ax, (63.5, 41), (76, 46), None)
    ax.text(70, 51.4, "accounts, events,\nrecommendation log", fontsize=7.4, ha="center", color=SLATE)
    arrow(ax, (76, 30), (64.6, 32.5), "courses", off=(0, 2.0), fs=7.8)
    arrow(ax, (76, 12), (58, 23), "weights", off=(2.4, -1), fs=7.8)
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11, 7.4, "Data flow diagram, level 1", ty=96)
    entity(ax, 1.5, 45, 12.5, 14, "Learner")
    process(ax, 29, 82, 8, "Authenticate", "1.0")
    process(ax, 29, 52, 7.6, "Manage\nprofile", "2.0")
    process(ax, 50, 52, 8.6, "Rank courses\n(hybrid)", "3.0", fs=7.4)
    process(ax, 71, 52, 7.6, "Record\ninteraction", "4.0")
    process(ax, 50, 17, 8.8, "Insights, path\nand model\nanalytics", "5.0", fs=7.1)
    store(ax, 52, 78, 30, 8, "users + auth_tokens", "D0")
    store(ax, 30, 30, 32, 8, "model bundle + catalog", "D3")
    store(ax, 83, 48, 16, 8, "profiles,\ninteractions", "D1")
    store(ax, 83, 66, 16, 8, "recommendation\nlogs", "D2")
    arrow(ax, (14, 58), (23.5, 76.5), "login", off=(-3.2, 0.5), fs=7.6)
    arrow(ax, (37, 82), (52, 82), "token, cookie", off=(0, 2.4), fs=7.6)
    arrow(ax, (14, 52), (21.4, 52), "profile", off=(0, 2.4), fs=7.6)
    arrow(ax, (36.6, 52), (41.4, 52), "state", off=(0, 3.0), fs=7.0)
    arrow(ax, (58.6, 52), (63.4, 52), "log", off=(0, 3.0), fs=7.0)
    arrow(ax, (78.6, 52), (83, 52), None)
    ax.text(80.8, 56.6, "event", fontsize=7.4, ha="center", color=SLATE)
    arrow(ax, (54, 60.2), (83, 70), "ranked list", lp=(70, 68.6), fs=7.4, rad=-0.15)
    arrow(ax, (44, 38), (47.4, 43.4), "weights", off=(-4.4, 0.4), fs=7.6)
    arrow(ax, (10, 45), (42.5, 20.5), "path / insights request", lp=(30, 40.5), fs=7.4, rad=0.22)
    arrow(ax, (41.4, 13.5), (12.5, 44.5), "path, insights, metrics", lp=(14, 22.5), fs=7.4, rad=0.22)
    arrow(ax, (58.6, 20), (84, 47.6), "events", lp=(74, 36.0), fs=7.4)
    ax.text(50, 3.0, "Every process except 1.0 requires a valid session token (HTTP 401 otherwise).", ha="center", fontsize=8.3, color=SLATE, style="italic")
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(11, 6.6, "Data flow diagram, level 2: process 3.0 expanded", ty=94)
    store(ax, 2, 62, 22, 8, "profile + interactions", "D1")
    labels = [("3.1", "Build learner\nstate"), ("3.2", "TF-IDF\ncontent sim"), ("3.3", "Skill, topic,\ngoal, rating"),
              ("3.4", "Behaviour\nboost"), ("3.5", "Success +\nuplift")]
    xs = [11, 28, 45, 62, 79]
    for (n, t), x in zip(labels, xs):
        process(ax, x, 84, 7.6, t, n, fs=7.0)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.6, 84), (b - 7.6, 84), None)
    arrow(ax, (11, 70), (11, 76.4), "rows", off=(3.2, 0), fs=7.6)
    process(ax, 57, 56, 8, "Weighted\nsum of 8\nterms", "3.6", fs=7.0)
    process(ax, 36, 56, 8, "Clip to\n[0,1], sort", "3.7", fs=7.2)
    process(ax, 36, 30, 8, "Explain\n(3 reasons)", "3.8", fs=7.4)
    process(ax, 57, 30, 8, "Attach best\naction", "3.9", fs=7.4)
    entity(ax, 70, 4, 28, 14, "Ranked list\nscore, parts, reasons,\nsuggested action")
    store(ax, 76, 62, 22, 8, "model bundle", "D3")
    arrow(ax, (86, 70), (81, 77), "weights", off=(5.4, 0.2), fs=7.4)
    arrow(ax, (73, 79), (61.6, 62.6), "8 terms", off=(5.2, 1.6), fs=7.4)
    arrow(ax, (49, 56), (44, 56), "score", off=(0, 2.4), fs=7.4)
    arrow(ax, (36, 48), (36, 38), "top-N", off=(4.4, 0), fs=7.4)
    arrow(ax, (44, 30), (49, 30), None)
    ax.text(46.5, 33, "reasons", fontsize=7.2, ha="center", color=SLATE)
    arrow(ax, (62, 23), (73, 14.5), "cards", off=(-2, -2.4), fs=7.4)
    ax.text(50, 0.4, "Terms and weights: 0.30 content, 0.15 skill, 0.15 topic, 0.12 success, 0.10 behaviour, 0.08 goal, 0.05 rating, 0.05 engagement.",
            ha="center", fontsize=7.6, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML class
def class_diagram():
    fig, ax = canvas(12.4, 8.8, "UML class diagram (ORM classes and the recommender module)", ty=96)
    uml_class(ax, 2, 92, 22, "User", ["+id : int", "+name : str", "+email : str", "+password_hash", "+created_at"], [], "table users", NAVY)
    uml_class(ax, 2, 70, 22, "AuthToken", ["+id : int", "+user_id : FK", "+token : str", "+created_at"], [], "table auth_tokens", PURPLE)
    uml_class(ax, 2, 46, 22, "RecommendationLog", ["+id : int", "+user_id : int", "+course_id : str", "+score : float", "+explanation : text", "+created_at"], [], "table", NAVY)
    uml_class(ax, 28, 92, 24, "Profile", ["+user_id : FK unique", "+education : str", "+skill_level : str", "+interests : text", "+preferred_topics", "+learning_style",
                                          "+goals : text", "+course_preferences", "+weekly_hours : float", "+age_band, gender"], [], "table profiles", BLUE)
    uml_class(ax, 28, 60, 24, "Interaction", ["+id : int", "+user_id : FK", "+course_id : str", "+event_type : str", "+value : float", "+created_at"], [], "table interactions", BLUE)
    uml_class(ax, 56, 92, 22, "Course", ["+id : str (PK)", "+title, category", "+topic, skill_level", "+description", "+duration_hours", "+prerequisites", "+tags, outcomes",
                                         "+resource_type", "+rating : float"], [], "table courses", GOLD)
    uml_class(ax, 56, 62, 43, "Recommender  (app/recommender.py)", ["WEIGHTS: 0.30 0.15 0.15 0.12 0.10 0.08 0.05 0.05"],
              ["+content_scores(profile, courses)", "+skill_compat(learner, course)", "+topic_interest_score(profile, course)",
               "+behavioral_boost(user_id, course_id, db)", "+engagement_level(db, user_id)", "+learner_state_vector(profile, eng)",
               "+predict_success(bundle, state)", "+uplift_scores(bundle, state)", "+rank_courses(profile, courses, db, uid, bundle, n)"],
              "module", GREEN)
    uml_class(ax, 82, 92, 17, "Security", [], ["+hash_password(pw)", "+verify_password(pw, h)", "+new_token()"], "module", PURPLE)
    uml_class(ax, 2, 26, 30, "ApiRouter  (app/api_routes.py)", [],
              ["+register / login / logout", "+get_profile / put_profile", "+list_courses / course_detail", "+recommendations / refresh_rec", "+record_interaction",
               "+activity / history / learning_path", "+insights / metrics / fairness", "+require_user(request, db)"], "module", GREEN)
    uml_class(ax, 38, 26, 28, "ModelBundle  (joblib)", ["scaler", "model (LR / RF / XGB winner)", "features (8)", "uplift (5 x 2 LR)", "opecfg"], ["+predict_proba(X)"], "artifact", SLATE)
    uml_class(ax, 71, 26, 28, "TrainPipeline  (offline)", [], ["+acquire_data()", "+split_learners()", "+train_eval()", "+fit_uplift()", "+offline_policy_eval()", "+fairness_audit()"],
              "scripts/train_pipeline.py", PURPLE)

    def link(p, q, label=None, ls="-", lp=None, head="-|>"):
        arrow(ax, p, q, label, color=SLATE, lw=1.1, ls=ls, fs=7.2, head=head, lp=lp)

    link((24, 88), (28, 88), None, head="-")
    ax.text(26, 89.8, "1:1", fontsize=7, ha="center", color=NAVY, fontweight="bold")
    link((13, 76.6), (13, 70), None, head="-")
    ax.text(15.6, 73.4, "1:n", fontsize=7, color=NAVY, fontweight="bold")
    ax.plot([24, 26, 26, 28], [79, 79, 54, 54], color=SLATE, lw=1.1)
    ax.text(27, 66, "1:n", fontsize=7, color=NAVY, fontweight="bold", rotation=90, va="center", ha="center")
    link((13, 26), (13, 28.5), None, ls="--")
    ax.text(15.6, 27.2, "writes log rows", fontsize=6.6, color=SLATE)
    link((67, 68), (67, 62), "scored by", ls="--", lp=(70, 65), head="-|>")
    link((56, 50), (52, 50), None, ls="--")
    ax.text(54, 51.6, "reads", fontsize=6.6, ha="center", color=SLATE)
    link((61, 34.7), (61, 26), "predict_proba", ls="--", lp=(68, 31), head="-|>")
    link((71, 21), (66, 21), "writes", ls="--", lp=(68.5, 22.8))
    link((32, 17), (38, 17), "loads", ls="--", lp=(35, 19))
    ax.text(2, 0.6, "Solid lines: foreign-key relations. Dashed: module calls and logical references. ApiRouter calls Recommender and Security (not drawn, to keep lines apart).",
            fontsize=7.2, color=SLATE, style="italic")
    save(fig, "06_uml_class_diagram.png")


# ---------------------------------------------------------------- 07 sequence
def sequence():
    fig, ax = canvas(11.5, 8.4, "Sequence diagram: requesting recommendations and logging feedback", ty=92)
    actors = [("Learner", 8), ("React SPA", 24), ("FastAPI\napi_routes", 41), ("Recommender", 58), ("Model bundle", 74), ("SQLite", 90)]
    top = 78
    for n, x in actors:
        box(ax, x - 7.5, top, 15, 7, n, fc=NAVY, ec=NAVY, tc="white", fs=8, bold=True)
        ax.plot([x, x], [top, 12], color=LINE, lw=1, ls=(0, (4, 3)))
    X = dict(actors)
    seq = [
        ("Learner", "React SPA", "open Recommendations", 74, False),
        ("React SPA", "FastAPI\napi_routes", "GET /api/recommendations?top_n=8 (cookie)", 70.5, False),
        ("FastAPI\napi_routes", "SQLite", "token -> user, profile, 24 courses", 66.8, False),
        ("SQLite", "FastAPI\napi_routes", "rows", 63.6, True),
        ("FastAPI\napi_routes", "Recommender", "rank_courses(profile, courses, db, uid, bundle)", 60.2, False),
        ("Recommender", "SQLite", "recent interactions (engagement, boost)", 56.8, False),
        ("Recommender", "Model bundle", "predict_proba(state), uplift per action", 53.4, False),
        ("Model bundle", "Recommender", "p_success, 5 benefits", 50.0, True),
        ("Recommender", "FastAPI\napi_routes", "ranked list + reasons + engagement", 46.6, True),
        ("FastAPI\napi_routes", "SQLite", "INSERT recommendation_logs (8 rows)", 43.2, False),
        ("FastAPI\napi_routes", "React SPA", "200 JSON", 39.8, True),
        ("React SPA", "Learner", "cards: match %, success, reason", 36.4, True),
        ("Learner", "React SPA", "press Start / Dismiss / Save", 32.8, False),
        ("React SPA", "FastAPI\napi_routes", "POST /api/interactions {course_id, event_type}", 29.4, False),
        ("FastAPI\napi_routes", "SQLite", "validate event_type, INSERT interactions", 26.0, False),
        ("React SPA", "FastAPI\napi_routes", "GET /api/recommendations  (re-rank with new boost)", 22.6, False),
        ("FastAPI\napi_routes", "React SPA", "200 JSON (new order)", 19.2, True),
    ]
    for a, b, label, y, ret in seq:
        xa, xb = X[a], X[b]
        arrow(ax, (xa, y), (xb, y), None, color=BLUE if not ret else GREEN, ls="--" if ret else "-", lw=1.4)
        ax.text((xa + xb) / 2, y + 1.3, label, fontsize=7.3, ha="center", color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
    ax.text(50, 9, "Alternative: a missing or expired token gives 401, an unknown event_type gives 400; nothing is written.",
            ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "07_sequence_diagram.png")


# ---------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(11, 7.8, "Use-case diagram", ty=80)
    ax.add_patch(Rectangle((24, 3), 52, 72, fc="#FBFCFE", ec="#D5DCE6", lw=1.4))
    ax.text(50, 72.4, "LearnPathIQ", ha="center", fontsize=10, fontweight="bold", color=NAVY)
    cases = [
        "Register / sign in", "Fill learner profile", "Browse and search catalog", "View ranked recommendations",
        "Read why a course\nwas recommended", "Log interactions\n(start, quiz, complete, dismiss)", "Follow staged learning path",
        "View insights and\nsuggested next action", "Review activity and history", "Inspect model analytics\nand fairness audit",
    ]
    ys = [66.5 - i * 6.5 for i in range(len(cases))]
    for t, y in zip(cases, ys):
        ax.add_patch(Ellipse((50, y), 40, 5.2, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(50, y, t, ha="center", va="center", fontsize=7.6, color=INK, linespacing=1.05)

    def actor(x, y, label, color):
        ax.add_patch(Circle((x, y + 8), 2.2, fc="white", ec=color, lw=1.8))
        ax.plot([x, x], [y + 5.8, y + 1.2], color=color, lw=1.8)
        ax.plot([x - 3, x + 3], [y + 4.2, y + 4.2], color=color, lw=1.8)
        ax.plot([x, x - 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.plot([x, x + 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.text(x, y - 5, label, ha="center", fontsize=8.6, fontweight="bold", color=INK, linespacing=1.15)

    actor(10, 36, "Learner", ORANGE)
    for y in ys:
        ax.plot([13, 30], [42, y], color=LINE, lw=0.9)
    actor(90, 40, "Developer /\nadministrator", PURPLE)
    box(ax, 79, 18, 19, 8, "Retrain models, refresh\nartifacts, run tests\n(scripts, outside the UI)", fc="#EFEBFC", ec=PURPLE, fs=7.0)
    ax.plot([90, 90], [31.5, 26], color=PURPLE, lw=1)
    ax.text(50, 0.2, "Registration, sign-in, the landing page, the catalog and model analytics are public; every other case needs a valid session.", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "08_use_case_diagram.png")


# ---------------------------------------------------------------- 09 ER
def er():
    fig, ax = canvas(11.5, 7.6, "Entity-relationship diagram of the SQLite database", ty=86)

    def table(x, y, w, name, cols, color):
        lh = 3.0
        h = 4.6 + lh * len(cols)
        ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.6))
        ax.add_patch(Rectangle((x, y - 4.6), w, 4.6, fc=color, ec=color))
        ax.text(x + w / 2, y - 2.3, name, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        for i, (n, t, tag) in enumerate(cols):
            yy = y - 4.6 - lh * (i + 0.5)
            ax.text(x + 1, yy, (tag + " ").ljust(3) + n, fontsize=7.2, va="center", family="monospace", color=INK, fontweight="bold" if tag == "PK" else "normal")
            ax.text(x + w - 1, yy, t, fontsize=6.6, va="center", ha="right", family="monospace", color=BLUE)

    table(36, 82, 28, "users", [("id", "INT", "PK"), ("name", "VARCHAR(120)", ""), ("email", "VARCHAR(255) UQ", ""), ("password_hash", "VARCHAR(255)", ""), ("created_at", "DATETIME", "")], NAVY)
    table(2, 82, 28, "profiles", [("id", "INT", "PK"), ("user_id", "INT UQ", "FK"), ("education", "VARCHAR(120)", ""), ("skill_level", "VARCHAR(60)", ""), ("interests", "TEXT", ""),
                                  ("preferred_topics", "TEXT", ""), ("learning_style", "VARCHAR(80)", ""), ("goals", "TEXT", ""), ("course_preferences", "TEXT", ""),
                                  ("weekly_hours", "FLOAT", ""), ("age_band", "VARCHAR(30)", ""), ("gender", "VARCHAR(30)", "")], BLUE)
    table(70, 82, 28, "auth_tokens", [("id", "INT", "PK"), ("user_id", "INT", "FK"), ("token", "VARCHAR(255) UQ", ""), ("created_at", "DATETIME", "")], PURPLE)
    table(36, 56, 28, "interactions", [("id", "INT", "PK"), ("user_id", "INT", "FK"), ("course_id", "VARCHAR(30)", ""), ("event_type", "VARCHAR(60)", ""), ("value", "FLOAT", ""), ("created_at", "DATETIME", "")], GREEN)
    table(70, 56, 28, "courses", [("id", "VARCHAR(30)", "PK"), ("title", "VARCHAR(255)", ""), ("category", "VARCHAR(120)", ""), ("topic", "VARCHAR(120)", ""), ("skill_level", "VARCHAR(60)", ""),
                                  ("description", "TEXT", ""), ("duration_hours", "FLOAT", ""), ("difficulty", "VARCHAR(40)", ""), ("prerequisites, outcomes", "TEXT", ""),
                                  ("tags", "TEXT", ""), ("resource_type", "VARCHAR(80)", ""), ("rating", "FLOAT", "")], GOLD)
    table(36, 30, 28, "recommendation_logs", [("id", "INT", "PK"), ("user_id", "INT", ""), ("course_id", "VARCHAR(30)", ""), ("score", "FLOAT", ""), ("explanation", "TEXT", ""), ("created_at", "DATETIME", "")], ORANGE)
    arrow(ax, (30, 76), (36, 76), None, head="-")
    ax.text(30.6, 77.6, "1", fontsize=8.5, color=NAVY, fontweight="bold")
    ax.text(34, 77.6, "1", fontsize=8.5, color=NAVY, fontweight="bold")
    arrow(ax, (64, 76), (70, 76), None, head="-")
    ax.text(64.6, 77.6, "1", fontsize=8.5, color=NAVY, fontweight="bold")
    ax.text(68.4, 77.6, "n", fontsize=8.5, color=NAVY, fontweight="bold")
    arrow(ax, (50, 62.4), (50, 56), None, head="-")
    ax.text(51.5, 59.2, "1 : n", fontsize=8, color=NAVY, fontweight="bold")
    arrow(ax, (64, 46), (70, 46), None, head="-", ls="--")
    ax.text(67, 47.8, "course_id", fontsize=6.6, color=SLATE, ha="center")
    arrow(ax, (50, 33.4), (50, 30), None, head="-", ls="--")
    ax.text(51.5, 31.7, "logical", fontsize=6.6, color=SLATE)
    ax.text(2, 0.3, "Solid links are declared foreign keys (SQLite does not enforce them unless a pragma is set, and the code does not set it). Dashed links are logical references stored as plain columns (interactions.course_id, recommendation_logs.user_id/course_id),\n"
                    "so no database constraint ties them to courses or users. profiles.user_id is unique, so users and profiles are 1 : 1.\n"
                    "Deleting a user cascades (ORM) to profile, interactions and tokens.",
            fontsize=7.0, color=SLATE, style="italic", linespacing=1.5, va="bottom")
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 flowchart
def flowchart():
    fig, ax = canvas(11.2, 9.8, "Flowchart of the core algorithm: rank_courses()", ty=104)
    cx = 33

    def term(y, t):
        box(ax, cx - 15, y - 2.2, 30, 4.4, t, fc=NAVY, ec=NAVY, tc="white", fs=8.2, bold=True, rounding=2.2)

    def step(y, t, c=BLUE, w=48):
        box(ax, cx - w / 2, y - 2.9, w, 5.8, t, fc="#F4F8FE", ec=c, fs=7.4)

    ys = [97, 89, 80.5, 71.5, 62.5, 53.5, 44.5, 35.5, 26.5, 17.5, 9]
    term(ys[0], "Start: GET /api/recommendations")
    step(ys[1], "token -> user; load profile, 24 courses,\nrecent interactions", NAVY)
    step(ys[2], "engagement = min(1, .25 + .04 recent + .03 quiz + .08 done)\nstate = 8 features (clicks, quizzes, hours, skill ...)", PURPLE)
    step(ys[3], "p_success = model.predict_proba(scaled state)\nuplift[a] = P(success | a=1) - P(success | a=0), 5 actions", GREEN)
    step(ys[4], "TF-IDF (profile text vs each course text) -> cosine similarity", BLUE)
    step(ys[5], "per course: skill, topic, goal, rating, behaviour boost\n(boost = sum of event weights, clipped to -0.3 .. 0.35)", BLUE)
    step(ys[6], "score = .30 sim + .15 skill + .15 topic + .12 p_success\n+ .10 (0.5 + boost) + .08 goal + .05 rating + .05 engagement", ORANGE)
    step(ys[7], "clip score to [0, 1]; add up to 3 reasons;\nattach best action = argmax uplift", GOLD)
    step(ys[8], "sort by score descending, keep top-N", NAVY, 34)
    step(ys[9], "INSERT one recommendation_logs row per card", NAVY, 40)
    term(ys[10], "Return JSON ranked list")
    for a, b in zip(ys[:-1], ys[1:]):
        ta = 2.2 if a == ys[0] else 2.9
        tb = 2.2 if b == ys[10] else 2.9
        arrow(ax, (cx, a - ta), (cx, b + tb), None, lw=1.3)
    box(ax, 62, 85, 22, 9, "401 if token is\nmissing or invalid\n(nothing computed)", fc="#FFF1EA", ec=ORANGE, fs=7.6)
    arrow(ax, (cx + 24, 89), (62, 89.5), "no", off=(0, 1.6), fs=7.6, color=ORANGE, lw=1.3)
    box(ax, 62, 55, 24, 15, "Cold start: with no interests\nor goals only education and\nskill words feed the content\nterm, so it is weak; the other\nterms still rank the catalog", fc="#EFEBFC", ec=PURPLE, fs=7.0, ls="--")
    arrow(ax, (cx + 24, 62.5), (62, 62.5), None, color=PURPLE, ls="--", lw=1.0)
    save(fig, "10_core_algorithm_flowchart.png")


def main():
    for fn in (architecture, workflow, dfd0, dfd1, dfd2, class_diagram, sequence, use_case, er, flowchart):
        fn()


if __name__ == "__main__":
    main()
