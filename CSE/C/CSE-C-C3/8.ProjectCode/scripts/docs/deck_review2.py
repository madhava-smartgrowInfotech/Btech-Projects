"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers are defined here. All numbers come from facts.py (experiments/**/metrics.json).
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"
OUT = os.path.join(F.BATCH, "13.Review_2_PPT.pptx")


# ------------------------------------------------------------------ helpers
def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "parking reservation, hold-back buffer, trust score, FastAPI, React"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=4):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 30)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag):
    """Copy of a diagram with its white margins removed (written to the temp folder, source untouched)."""
    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"c3_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    K.picture(slide, F.shot(name), x, y, w, h - 0.5, border=True)
    K.text(slide, x, y + h - 0.45, w, 0.45, caption, size=11, color=K.TXT, align="c", italic=True)


def line_counts():
    out = {}
    for rel in ("app/main.py", "app/engine.py", "app/models.py", "app/auth.py", "app/schemas.py", "app/stripe_pay.py", "app/config.py",
                "app/database.py", "app/seed.py", "scripts/compute_buffer_strategy_metrics.py", "scripts/parking_sim.py"):
        with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
            out[rel] = sum(1 for _ in f)
    return out


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    lc = line_counts()
    seed = F.SEED
    sc = seed["status_counts"]
    n100 = 100

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: advance parking reservation with a hold-back buffer, nearest-alternate re-allocation and a driver Trust Score",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how ParkSure is designed and built, what is implemented, the first measured results from our own tests and simulator, and the open items. "
                "Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and data"), ("03", "Input handling and engine rules"), ("04", "Configuration and decision logic"),
               ("05", "Data flow, modules, UML"), ("06", "Technology stack"), ("07", "Implementation progress"), ("08", "Preliminary results"),
               ("09", "Output screens"), ("10", "Testing"), ("11", "Challenges"), ("12", "Next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Drivers circle for parking, operators keep manual registers with no live view, an arrival gives no guarantee of a bay, and cash collection leaves no usable record. Reservation systems add a new failure: the booked bay is still occupied by a vehicle that overstayed.", K.ORANGE, "!"),
        ("Proposed system", "ParkSure lets drivers search live availability, reserve in advance, pay online and check in and out. An availability engine keeps a hold-back buffer, moves a driver to the nearest alternate when the lot is full on arrival, and prices by a driver Trust Score.", K.BLUE, "i"),
        ("Base papers", "[1] Jemmali et al. (IEEE OJCS 2026) balance load across zones by passenger count. [2] Cabri et al. (arXiv 2026) propose a buffer of non-reservable bays and a star reputation, tested in simulation. ParkSure implements the ideas of [2] as a working web platform; the settings differ, so only relative findings are comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.2, t, b_, col, gl, body_size=15.5)
    notes[3] = ("Recap of Review 1. The batch's registered base paper is the OJCS paper; the reservation buffer and star rules that ParkSure implements come from the arXiv paper. "
                "Our gap is a complete operating reservation platform that is measured honestly.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.3, 5.7)
    K.text(s, 8.15, 1.45, 4.6, 5.4, [
        ("**Layered, one database file**", {"space_after": 8}),
        (f"Console: React 19 + Vite on port {F.WEB_PORT}: landing, login, three driver screens and five admin screens; /api is proxied to the backend.", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}, 22 routes in app/main.py with JWT roles driver and admin.", {"bullet": True}),
        ("Engine: app/engine.py owns admission, buffer, haversine alternate, Trust Score and fees.", {"bullet": True}),
        ("Storage: SQLAlchemy over SQLite (parksure.db, 5 tables); APScheduler resets buffers every 30 minutes; Stripe Checkout in test mode with a demo fallback.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[4] = f"app/main.py is {lc['app/main.py']} lines and app/engine.py {lc['app/engine.py']}; the routes call the engine functions and keep no rules of their own."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: search, reserve, pay, arrive, depart")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.5, 5.0)
    for i, (t, b_) in enumerate([("Admit", "A request is accepted only if overlapping bookings plus the buffer stay below capacity; otherwise it is declined with a reason."),
                                 ("Arrive", "At check-in a full lot moves the driver to exactly one nearest alternate by haversine distance, or the booking fails and the fee is credited."),
                                 ("Learn", "An on-time check-out grows the buffer and builds a benefit streak; a late one adds a warning. The score sets the next fee.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.35, y, 4.38, 1.65)
        K.text(s, 8.5, y + 0.07, 4.1, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.5, y + 0.42, 4.1, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.5, 0.45, "High-level workflow as implemented in the API.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "Every rule shown here is in app/engine.py and is exercised by the tests; the workflow diagram mirrors the routes."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Data: no ML dataset; a seeded demo history and a simulator")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{seed['locations']}", "locations in the seeded demo (8 to 25 bays each)", K.ORANGE),
                                   (f"{seed['users']}", "users: 1 admin and 8 drivers (2 with overstay history)", K.BLUE),
                                   (f"{seed['reservations']}", f"reservations over 60 days: {sc['completed']} done, {sc['failed']} failed, {sc['declined']} declined", K.GREEN),
                                   (f"{seed['payments']}", "payment records (demo provider)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=11.5)
    rows = [["", "Seeded demo history (app/seed.py)", "Simulator scenario (scripts/parking_sim.py)"],
            ["Origin", "generated by the product itself with random seed 42: SYNTHETIC, not real parking data", "re-creates the setting of base paper [2]: 8 areas x 10 bays, 80 to 110 vehicles"],
            ["Content", "60 days of bookings plus 8 Friday-evening over-subscription peaks at Old Town Deck", "each vehicle makes 10 parks of 1 to 3 h; 25 to 50 % overstay by 1 h"],
            ["Use", "gives Strategy Insights real contention to replay on a fresh install", "30 runs per cell (the paper used 5); 5 buffer policies; Trust Score on or off"],
            ["Not available", "no real parking-lot data, no licence issue, no split (there is no model to train)", "not SUMO; arrival process and gaps are our assumptions, fixed before the runs"]]
    K.table(s, 0.6, 2.95, [1.4, 5.3, 5.43], rows, font_size=12, row_h=0.76, first_bold=True)
    notes[6] = ("ParkSure has no machine-learning model, so there is no training dataset. All reported results come from our own tests, a simulator that reproduces the base paper's scenario, "
                "and the synthetic seed that ships with the product.")

    # ---- 7 input handling
    s = S[6]
    set_title(s, "Input handling and data preparation")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("pydantic validation", K.NAVY), ("Times to UTC", K.PURPLE), ("30-day window limit", K.PURPLE),
                                       ("Overlap count", K.GREEN), ("Fee quote", K.GREEN), ("Reservation + payment", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([("22", "routes; request bodies and query parameters are typed with pydantic, and bad input returns 422 (our injection-style probes: 422, never 500)", K.ORANGE),
                                   ("0.25 h", "minimum billed time; fee = hours x hourly rate x trust multiplier, rounded to cents", K.BLUE)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=11.5)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        ("Registration: name 2 to 120 characters, valid email, password 6 to 128; passwords are stored as bcrypt hashes (cost 12), tokens are HS256 JWTs valid for 12 hours.", {"bullet": True}),
        ("Locations: latitude -90 to 90, longitude -180 to 180, capacity 1 to 5,000, price 0.5 to 100, buffer 0 to 20.", {"bullet": True}),
        ("Reservations: end must be after start, window at most 30 days, naive times are treated as UTC; account credit offsets the fee automatically.", {"bullet": True}),
        ("Seeding: on an empty database the product creates 5 locations, 9 users and 60 days of bookings so the admin screens show data.", {"bullet": True}),
        ("Known gap: a booking window in the past is accepted (found by our probe).", {"bullet": True}),
    ], size=15, color=K.INK, space_after=8)
    notes[7] = "There is no data cleaning because there is no uploaded dataset; the equivalent step is strict validation at the API boundary (app/schemas.py)."

    # ---- 8 model (engine rules)
    s = S[7]
    set_title(s, "Engine rules: buffer and Trust Score")
    wipe(s)
    K.picture(s, trim(F.diag("12_trust_buffer_policy.png"), "12"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**Admission**: accept if overlapping bookings + buffer < capacity.", {"bullet": True, "space_after": 8}),
        ("**Buffer**: starts at 1, +1 on every on-time check-out up to 5, reset to 1 every 24 h.", {"bullet": True, "space_after": 8}),
        ("**Trust Score** 0 to 5, start 3: 3 on-time check-outs give +1, 2 late ones give -1; fee multiplier 1.75 down to 0.90.", {"bullet": True, "space_after": 8}),
        ("Base paper [2] grows its buffer on late departures; the shipped code grows it on on-time ones. We measure both.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=13.5, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "Trust Score and buffer policy, as coded in app/engine.py and app/config.py.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "The 'model' of this product is rule based, which makes every decision auditable. The direction of the buffer growth differs from the paper and is reported openly."

    # ---- 9 configuration
    s = S[8]
    set_title(s, "Policy constants and experiment configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Buffer policy", "initial 1, maximum 5, reset every 24 h by a job that runs every 30 minutes; +1 on an on-time check-out (end + 10 minutes of grace)"],
            ["Trust Score", "start 3, range 0 to 5; B = 3 benefits for +1, W = 2 warnings for -1; suspended below 1.5 with a warning in the last 14 days, 24 h cooldown"],
            ["Fees", "multiplier by rounded score: 1.75, 1.50, 1.25, 1.00, 0.95, 0.90; payments via Stripe test mode or the offline demo checkout"],
            ["Simulator", "8 areas x 10 bays; 80 to 110 vehicles; 10 parks each of 1 to 3 h; overstay 1 h; 30 seeds per cell; static 0, 1, 3, dynamic (ParkSure), dynamic (paper rule)"],
            ["Parity check", f"simulator against the real engine: {F.PAR['total_cases']:,} decisions, {F.PAR['total_mismatches']} mismatches"],
            ["Latency runs", "200 sequential requests per endpoint on 127.0.0.1, one uvicorn process, SQLite file"],
            ["Machine", "Intel Core i5-12500 (6 cores), 15.7 GB RAM, Windows 11, Python 3.14.7, no GPU"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=13, row_h=0.66, first_bold=True)
    notes[9] = "These are the constants in app/config.py and scripts/parking_sim.py. The simulator's unspecified parameters are listed in SIM_ASSUMPTIONS."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: admission, arrival and departure")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_algorithm.png"), "10"), 0.6, 1.3, 6.6, 5.7)
    K.text(s, 7.5, 1.45, 5.25, 5.5, [
        ("**At request**: suspended drivers are refused; otherwise overlapping + buffer < capacity decides, and a refusal is stored as a declined booking with its reason.", {"bullet": True, "space_after": 9}),
        ("**At arrival**: if parked bays have reached capacity, the nearest other location with forecast space (haversine, R = 6,371 km) receives an active alternate booking; with none, the booking fails and the fee is credited.", {"bullet": True, "space_after": 9}),
        ("**At departure**: more than 10 minutes late is a warning; on time grows the buffer and adds a benefit.", {"bullet": True, "space_after": 9}),
        ("**Limit**: the alternate is booked without re-checking its physical bays.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[10] = "Alternate search costs about 0.4 ms per other location (18.6 ms over 49 locations); the admission check itself takes 0.33 ms."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 6.4, 5.2)
    K.text(s, 0.6, 6.55, 6.4, 0.4, "DFD level 1: six processes and the data stores.", size=12, color=K.TXT, align="c", italic=True)
    mods = [["Module", "Lines", "Role"],
            ["app/main.py", lc["app/main.py"], "22 routes, scheduler"],
            ["app/engine.py", lc["app/engine.py"], "admission, buffer, trust, haversine"],
            ["app/models.py", lc["app/models.py"], "5 SQLAlchemy tables"],
            ["app/auth.py", lc["app/auth.py"], "bcrypt, JWT, role guards"],
            ["app/schemas.py", lc["app/schemas.py"], "pydantic validation"],
            ["app/stripe_pay.py", lc["app/stripe_pay.py"], "Checkout / demo fallback"],
            ["app/seed.py", lc["app/seed.py"], "synthetic demo history"],
            ["scripts/parking_sim.py", lc["scripts/parking_sim.py"], "discrete-event simulator"],
            ["scripts/compute_buffer_strategy_metrics.py", lc["scripts/compute_buffer_strategy_metrics.py"], "Strategy Insights replay"]]
    mods[-1][0] = "scripts/compute_buffer_\nstrategy_metrics.py"
    K.table(s, 7.2, 1.45, [2.75, 0.6, 2.18], mods, font_size=10.5, row_h=0.5, first_bold=True, align=["l", "r", "l"])
    notes[11] = "Line counts are taken from the files. The API layer is thin: it validates, calls the engine and shapes the JSON."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 0.6, 1.3, 6.4, 4.9)
    K.text(s, 0.6, 6.25, 6.4, 0.4, "UML class diagram: five entities, engine, auth and scheduler.", size=12, color=K.TXT, align="c", italic=True)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 7.2, 1.3, 5.55, 4.9)
    K.text(s, 7.2, 6.25, 5.55, 0.4, "ER diagram of the SQLite database (parksure.db).", size=12, color=K.TXT, align="c", italic=True)
    K.text(s, 0.6, 6.65, 12.13, 0.4, "users 1-N reservations and trust_events; parking_locations 1-N reservations; reservations 1-1 payments; alternate bookings link to the replaced one by parent_id.", size=11.5, color=K.TXT, align="c")
    notes[12] = "parent_id is a plain integer, not a foreign key. Indexes exist on user, location, start and end columns used by the overlap query."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    stack = [("Python 3.14.7", "venv interpreter; the code needs 3.11 or newer", K.BLUE), ("FastAPI 0.141.1", "22 routes; uvicorn 0.52.4; pydantic 2.13.5", K.ORANGE),
             ("SQLAlchemy 2.0.52", "5 tables on SQLite; APScheduler 3.11.3 for the buffer job", K.GREEN), ("JWT + bcrypt", "python-jose 3.5.0 (HS256), bcrypt 5.0.0, cost 12", K.PURPLE),
             ("Stripe SDK 15.6.1", "Checkout in test mode; offline demo fallback", K.BLUE), ("React 19 + Vite 8", "react-router 7, Recharts, three.js hero", K.ORANGE),
             ("pytest, Playwright", f"{F.PYTEST_TOTAL} tests; screenshots from the real UI", K.GREEN), ("Own simulator", "pure Python discrete-event model, parity-tested against the engine", K.PURPLE)]
    for i, (t, b_, col) in enumerate(stack):
        r, c = divmod(i, 4)
        x, y = 0.6 + c * 3.09, 1.5 + r * 2.5
        K.box(s, x, y, 2.85, 2.25)
        K.circle(s, x + 0.22, y + 0.22, 0.5, col, str(i + 1), 16)
        K.text(s, x + 0.22, y + 0.9, 2.45, 0.45, t, size=16, color=K.INK, bold=True)
        K.text(s, x + 0.22, y + 1.35, 2.45, 0.85, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Everything runs on one machine on CPU; the only external service is Stripe, and it is optional.", size=13, color=K.TXT, italic=True)
    notes[13] = "Versions are those installed in the project's virtual environment on the measuring machine."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Registration, login, roles", "Done", "JWT roles; bcrypt; cross-user access blocked (404)"],
            ["Search, reserve, cancel", "Done", f"search {F.lat('GET /api/search'):.1f} ms, reserve {F.lat('POST /api/reservations'):.1f} ms mean"],
            ["Check-in, alternate move, check-out", "Done", "alternate by haversine; failed bookings credited; buffer and trust updated"],
            ["Payments", "Partly", "Stripe test mode + demo; no receipt document; unauthenticated demo-confirm found"],
            ["Admin console and Strategy Insights", "Done", "overview, locations, bookings, users, deterministic replay"],
            ["Simulator and experiments", "Done", f"5 policies x 4 populations x 6 bad shares, {F.SEEDS} runs per cell"],
            ["Vehicle profile", "Not built", "objective 1 asks for it; no table or screen exists"],
            ["Concurrency safety", "Open", f"{F.RACE['trials_with_overbooking']} of {F.RACE['trials']} race trials accepted two bookings for one bay"]]
    K.table(s, 0.6, 1.45, [3.9, 1.7, 6.53], rows, font_size=13, row_h=0.6, first_bold=True)
    notes[14] = "Honest status: the core flow and the admin side are complete; two objectives are only partly met (vehicle profile, digital receipt) and the admission check is not safe under simultaneous requests."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: simulator and response time")
    wipe(s)
    order = [("Static 0", "static_0"), ("Static 1", "static_1"), ("Static 3", "static_3"), ("Dynamic (paper rule)", "dynamic_paper"), ("Dynamic (ParkSure)", "dynamic_parksure")]
    vals = [round(F.pop(n100, k, "no_reservation"), 1) for _, k in order]
    K.bar_chart(s, 0.6, 1.35, 6.3, 3.5, [o[0] for o in order], [("Reservations refused by admission", vals)], colors=[K.BLUE], number_format="0", font_size=10, max_value=330)
    K.text(s, 0.6, 4.85, 6.3, 0.5, f"Refused by admission out of 1,000 requests, {n100} vehicles, 25 % overstaying, mean of {F.SEEDS} runs.", size=11, color=K.TXT, align="c", italic=True)
    lrows = [["Endpoint", "mean ms", "p95 ms"]]
    for lab, pre in [("Search availability", "GET /api/search"), ("Reserve", "POST /api/reservations"), ("Check in", "POST /api/reservations/{id}/checkin"),
                     ("Check out", "POST /api/reservations/{id}/checkout"), ("Login (bcrypt)", "POST /api/auth/login"), ("My bookings (N+1)", "GET /api/reservations (own")]:
        lrows.append([lab, f"{F.lat(pre):.1f}", f"{F.lat(pre, 'p95_ms'):.1f}"])
    K.table(s, 7.2, 1.4, [2.9, 1.2, 1.43], lrows, font_size=11.5, row_h=0.42, first_bold=True, align=["l", "r", "r"])
    K.text(s, 0.6, 5.4, 12.13, 1.7, [
        (f"The shipped dynamic buffer refuses the most requests ({vals[4]:.0f} against {vals[0]:.0f} with no buffer); the paper's late-departure rule refuses {vals[3]:.0f}. The paper's 'dynamic is best' is not reproduced for the shipped rule.", {"bullet": True}),
        (f"'No park' stays rare under every policy (at most {max(F.pop(110, k, 'no_park') for _, k in order):.1f} per run) because the alternate step absorbs overflow; the Trust lockout causes more refusals than the buffer once 25 % of drivers overstay.", {"bullet": True}),
        ("Simulator, not SUMO, and synthetic seed: relative findings only.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=12.5, color=K.INK, space_after=4)
    notes[15] = "Numbers are from experiments/buffer_population and api_latency. Population 100 is the middle case; the same ordering holds at 80, 90 and 110."

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shot_box(s, "06_find_parking.png", 0.6, 1.3, 3.95, 2.9, "Find parking: forecast bookable bays per location")
    shot_box(s, "15_moved_to_alternate.png", 4.69, 1.3, 3.95, 2.9, "Arrival at a full lot: moved to the nearest alternate (0.1 km)")
    shot_box(s, "10_my_bookings.png", 8.78, 1.3, 3.95, 2.9, "My bookings with check-in, cancel and payment actions")
    shot_box(s, "13_trust_score.png", 0.6, 4.25, 3.95, 2.9, "Trust Score and event history")
    shot_box(s, "19_admin_insights.png", 4.69, 4.25, 3.95, 2.9, "Admin Strategy Insights")
    shot_box(s, "17_admin_overview.png", 8.78, 4.25, 3.95, 2.9, "Admin overview")
    notes[16] = "All screens are captures of the running application on a fresh seeded database; the alternate-move screen was produced by the real check-in flow."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests pass ({F.PYTEST_ENGINE} engine, {F.PYTEST_API} API, {F.PYTEST_PARITY} parity)", K.GREEN),
                                   (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "end-to-end smoke checks on a throw-away database", K.BLUE),
                                   (f"{F.PAR['total_mismatches']} / {F.PAR['total_cases']:,}", "simulator decisions that differ from the real engine", K.PURPLE),
                                   (f"{F.RACE['trials_with_overbooking']} / {F.RACE['trials']}", "concurrency trials that over-booked one bay", K.ORANGE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Probe on our own system", "Result"],
            ["Payment confirm without login", "marks a booking paid"],
            ["Token forged with default secret", "accepted"],
            ["30 wrong passwords in a row", "no lockout"],
            ["Past booking window", "accepted"],
            ["Check-in 25 days early", "accepted"],
            ["SQL-injection style inputs", "422, no server error"],
            ["Cross-user cancel", "blocked (404)"]]
    K.table(s, 0.6, 2.95, [3.6, 2.3], rows, font_size=12, row_h=0.46, first_bold=True)
    K.text(s, 6.9, 2.95, 5.83, 4.0, [
        ("**What the tests cover**: haversine, fees, admission, alternates, trust and suspension, buffer reset, every route group, role guards and the simulator's parity with the engine.", {"bullet": True, "space_after": 8}),
        ("**Found by the probes**: five weaknesses that are documented as limitations, not fixed in this phase.", {"bullet": True, "space_after": 8}),
        ("**Not done**: user study, load test beyond 8 threads, security audit, Stripe live mode.", {"bullet": True, "space_after": 8}),
        (f"Admission takes {F.MB['forecast_free (admission, 100 bookings at the location)']['mean_ms']:.2f} ms in process.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=13.5, color=K.INK)
    notes[17] = "The probes were run against a throw-away database of our own system; none is a defect of the tests."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "What we found", "Action"],
            ["No real parking data", "Only synthetic seed data exists", "Labelled it synthetic; added a simulator of the base paper's scenario"],
            ["Buffer direction differs", "Code grows the buffer on on-time check-outs, paper on late ones", "Measured both; reported, product code unchanged"],
            ["Refusals from lockout", f"Trust lockout refuses {F.bad(0.5, 'static_0', 'suspended'):.0f} requests per run at 50 % bad drivers (static 0)", "Added a Trust-off ablation; lockout length is future work"],
            ["Slow listings", f"My bookings {F.lat('GET /api/reservations (own'):.0f} ms, admin bookings {F.lat('GET /api/admin/bookings'):.0f} ms (2 queries per row)", "Documented; batch the queries"],
            ["Over-booking race", f"{F.RACE['trials_with_overbooking']} of {F.RACE['trials']} trials accepted two bookings for one bay", "Documented; needs an atomic check"],
            ["Payment confirm open", "Demo-confirm route needs no login", "Documented; disable outside demo mode"],
            ["Objectives only partly met", "No vehicle profile and no downloadable receipt exist", "Reported as gaps; planned for the next phase"]]
    K.table(s, 0.6, 1.4, [2.6, 5.0, 4.53], rows, font_size=12.5, row_h=0.68, first_bold=True)
    notes[18] = "Each challenge is a measured finding; the evidence is in docs/REPORT_FACTS.md."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Harden", "Make the admission check atomic, close the unauthenticated payment route, require a real JWT secret, rate-limit login, reject past windows, and batch the listing queries.", K.ORANGE, "1"),
        ("Complete", "Add the vehicle profile and a downloadable receipt (objectives 1 and 4), and decide the buffer direction and lockout length with the guide.", K.BLUE, "2"),
        ("Deliver", "Finish the final report and IEEE paper from the measured results, rehearse the final demo, and keep every number tied to the metrics files.", K.GREEN, "3"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 3.2, t, b_, col, gl, body_size=16)
    notes[19] = "The open items are the ones identified by our own measurements and probes, in priority order."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Close the review and invite questions."

    for i, t in notes.items():
        K.set_notes(S[i - 1], t)
    prs.save(out_path)
    K.rename_theme(out_path, "ParkSure")
    return out_path


def main():
    build(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
