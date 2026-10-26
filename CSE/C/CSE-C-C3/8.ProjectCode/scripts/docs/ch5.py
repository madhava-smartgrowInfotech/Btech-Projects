"""Chapter 5: System Design for ParkSure.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
Line counts are measured from the code at build time; diagrams are drawn by make_diagrams.py.
"""

import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB
from .diagram_index import DIAGRAMS
from .refs import N as cite

_D = {k: (t, f, cap, txt) for k, t, f, cap, txt in DIAGRAMS}


def _lines(rel):
    path = os.path.join(F.CODE, rel)
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def _tree_lines(rel, exts):
    total = 0
    for root, dirs, files in os.walk(os.path.join(F.CODE, rel)):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", "__pycache__", "docs")]
        for f in files:
            if f.endswith(exts):
                with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                    total += sum(1 for _ in fh)
    return total


def _dg(key, width=5.4):
    """Diagram figure block, or nothing if the file has not been drawn yet."""
    t, f, cap, _ = _D[key]
    path = F.diag(f)
    return [FIG(path, cap, width)] if os.path.exists(path) else []


_DROP_P = ("Three decisions about this structure", "Four design rules", "Every design has costs", "Two further choices")
_DROP_TAB = ("Principal design decisions",)


def _trim(out):
    """Report variant: same 12 diagrams, no design screenshots (Chapter 8 shows the screens), 5.10 shortened to its table."""
    res = []
    for b in out:
        if b[0] == "p" and b[1].startswith(_DROP_P[:1]):
            continue
        if b[0] == "fig" and os.sep + "screenshots" + os.sep in b[1]:
            continue
        res.append(b)
    return res


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    shot = lambda n, cap, base=5.0, mh=3.6: [FIG(F.shot(n), cap, F.shot_w(F.shot(n), base, mh))] if os.path.exists(F.shot(n)) else []  # noqa: E731

    mods = [
        ("`app/main.py`", "app/main.py", "FastAPI application: 22 routes, lifespan (create tables, seed, scheduler), static serving"),
        ("`app/engine.py`", "app/engine.py", "Smart Availability Engine: overlap count, admission, haversine, nearest alternate, buffer reset, trust update, suspension, fee quote"),
        ("`app/models.py`", "app/models.py", "Five SQLAlchemy models: User, ParkingLocation, Reservation, Payment, TrustEvent"),
        ("`app/auth.py`", "app/auth.py", "bcrypt hashing, JWT creation and decoding, `current_user` and `admin_user` guards"),
        ("`app/schemas.py`", "app/schemas.py", "pydantic input models with length and range limits"),
        ("`app/stripe_pay.py`", "app/stripe_pay.py", "Stripe Checkout session in test mode, or the offline demo checkout"),
        ("`app/config.py`", "app/config.py", "Policy constants (buffer, trust, fee multipliers) and secrets read from the environment"),
        ("`app/database.py`", "app/database.py", "SQLite engine, session factory and the `get_db` dependency"),
        ("`app/seed.py`", "app/seed.py", "Seeded demo data: 5 locations, 1 admin, 8 drivers, 60 days of booking history"),
        ("`scripts/compute_buffer_strategy_metrics.py`", "scripts/compute_buffer_strategy_metrics.py", "Deterministic replay of stored bookings under four buffer policies (Strategy Insights)"),
        ("`scripts/parking_sim.py`, `scripts/parity.py`", "scripts/parking_sim.py", "Discrete-event simulator of the reservation rules and its parity check against the engine"),
        ("`scripts/run_experiments.py`, `scripts/measure_api.py`", "scripts/run_experiments.py", "Experiments, API latency, concurrency and security probes"),
        ("`scripts/smoke_test.py`", "scripts/smoke_test.py", f"{F.SMOKE_TOTAL}-check end-to-end test on a throw-away database"),
    ]
    mod_rows = [[n, str(_lines(rel)), d] for n, rel, d in mods]
    fe_lines, test_lines = _tree_lines("frontend/src", (".jsx", ".js", ".css")), _tree_lines("tests", (".py",))
    mod_rows.append(["`frontend/src/`", f"{fe_lines:,}", "React 19 console: 11 page components, UI kit, charts, three.js hero, API client, auth and theme providers"])
    mod_rows.append(["`tests/`", str(test_lines), f"{F.PYTEST_TOTAL} pytest tests ({F.PYTEST_ENGINE} engine, {F.PYTEST_API} API, {F.PYTEST_PARITY} simulator parity)"])

    routes = [
        ["POST", "/api/auth/register", "-", "Create a driver account (the first account on an empty database becomes admin); returns token and user", "400 duplicate email; 422 validation"],
        ["POST", "/api/auth/login", "-", "Check the bcrypt hash; returns token and user", "401 wrong email or password"],
        ["GET", "/api/auth/me", "user", "Profile with trust score, streak, warnings, credit, suspension time", "401"],
        ["GET", "/api/locations", "-", "All locations, ordered by name", "-"],
        ["POST", "/api/locations", "admin", "Create a location", "403; 422"],
        ["PUT", "/api/locations/{id}", "admin", "Update a location", "403; 404; 422"],
        ["DELETE", "/api/locations/{id}", "admin", "Delete a location and, by cascade, its reservations", "403; 404"],
        ["GET", "/api/search", "-", "Per location: overlapping bookings, bookable bays, available flag for a time window", "400 end before start or window over 30 days; 422"],
        ["POST", "/api/reservations", "user", "Suspension check, admission rule, fee quote, credit, payment record, checkout link", "403 suspended; 409 full; 404; 400; 422"],
        ["GET", "/api/reservations", "user", "The caller's reservations, newest window first", "401"],
        ["POST", "/api/reservations/{id}/cancel", "owner or admin", "Cancel a reserved booking; a paid fee returns as account credit", "404; 400 not cancellable"],
        ["POST", "/api/reservations/{id}/checkin", "owner or admin", "Activate; if the lot is physically full, move to the nearest alternate or fail and credit", "404; 400 not reserved"],
        ["POST", "/api/reservations/{id}/checkout", "owner or admin", "Complete; on time or late; buffer and trust update", "404; 400 not active"],
        ["GET", "/api/trust", "user", "Score, streak, warnings, next reward, fee multiplier and the last 20 trust events", "401"],
        ["GET", "/api/payments/demo-confirm", "-", "Offline demo checkout link: marks the payment paid", "404"],
        ["POST", "/api/payments/{id}/confirm", "owner or admin", "Confirm a payment from the console", "404; 403"],
        ["POST", "/api/stripe/webhook", "Stripe signature", "On checkout.session.completed mark the payment paid", "400 bad signature; inert without keys"],
        ["GET", "/api/admin/overview", "admin", "Counts of users, locations, reservations, paid revenue, unable-to-park, declined", "403"],
        ["GET", "/api/admin/users", "admin", "All users with trust and credit", "403"],
        ["GET", "/api/admin/bookings", "admin", "The 300 most recent reservations", "403"],
        ["POST", "/api/admin/reset-buffers", "admin", "Reset buffers by policy, or force a reset", "403"],
        ["GET", "/api/admin/insights", "admin", "Deterministic replay under four buffer policies for a window of days", "403"],
    ]

    out = [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how ParkSure is put together: the architecture and workflow, the data flow, the UML and database design, the core algorithm, the modules, the API and the user interface. "
          "The diagrams were drawn from the code in `app/` and `frontend/src/`; the complete set, each with a longer explanation, is also in the Block Diagrams document. "
          "ParkSure is a multi-user web platform with two roles, a driver and an administrator, and one persisted state, a single SQLite database. The sections below state the design as built, including the places where the build differs from what a production system would need."),

        H2("5.1 Design goals and architecture"),
        P("Five goals shaped the design. First, **the availability a driver sees must be the same number the booking rule enforces**: the search route and the admission rule use the same overlap count and the same buffer, so a bay shown as free can be booked and a bay shown as full cannot. "
          "Second, **an overstay must not silently strand the next driver**: the hold-back buffer, the arrival check and the nearest-alternate move exist for that purpose, following the dual mechanism of " + cite("cabri") + ". "
          "Third, **behaviour has a price**: the Trust Score changes the fee and, at the bottom of the scale, access. Fourth, **every outcome is recorded**: declined, failed and cancelled bookings stay in the database with a reason, so the administrator can replay them. "
          "Fifth, **zero-configuration deployment**: SQLite, a demo checkout and seeded data let the product run on a student's laptop with one launcher script."),
        *_dg("arch", 5.6),
        P(f"The React console on port {w} reaches the FastAPI application on 127.0.0.1:{a} through the Vite development proxy, so the browser sees one origin. "
          "The application exposes 22 routes in `app/main.py`. Each route is a thin function: it validates input with pydantic, resolves the caller with a bearer token, calls a function of the engine module or queries the SQLAlchemy session, and returns JSON. "
          "The rules themselves live in `app/engine.py` so that they can be tested without HTTP; the unit tests, the simulator and the Strategy Insights script all import them. "
          "The architectural style is a stateless REST interface " + cite("rest") + " over one relational store; the only state kept in the server process is the scheduler."),
        P("The deliberate gaps in this architecture are worth stating. There is one backend process and one SQLite file, so there is no horizontal scaling and writes are serialised by the database. "
          "The admission check and the insert are two separate steps without a lock, which is why the concurrency probe in Chapter 7 found one trial in ten in which two simultaneous requests both took the last bay. "
          "The buffer-reset job runs inside the web process, so a second process would run it twice. And entry and exit are software events (the Check in and Check out buttons); there are no barriers, sensors or cameras, so the physical occupancy the arrival check uses is the count of bookings the system itself has marked active."),

        H2("5.2 High-level workflow"),
        *_dg("flow", 5.6),
        P("The workflow has seven stages and every stage maps to a route or a page. **Search** (`GET /api/search`, Find parking) shows bookable bays per location for a window. **Reserve** (`POST /api/reservations`) applies the suspension check and the admission rule and stores either a reserved or a declined booking. "
          "**Pay** completes through Stripe Checkout in test mode or through the offline demo checkout. **Check in** (`POST /api/reservations/{id}/checkin`) activates the booking or triggers the alternate move. "
          "**Check out** judges the departure against the end time plus ten minutes of grace. **Trust and buffer update** happen in the same call. **Analytics** (Strategy Insights) replays the stored history for the administrator."),
        P("The booking has six states, shown below. Every transition is caused by one API call, and the four final states keep the row for reporting. Two details are easy to miss. A declined request is stored as a row of its own, with the reason in `decline_reason`, so refused demand is visible to the administrator; "
          "and an automatic move to an alternate does not edit the original booking into a new one: the original becomes failed, with the explanation, and a second booking is created as active with `parent_id` pointing back."),
        *_dg("state", 5.4),

        H2("5.3 Data flow diagrams"),
        H3("5.3.1 Level 0: context"),
        *_dg("dfd0", 4.8),
        P("At level 0 ParkSure is one process with three external entities. The **driver** supplies credentials, search windows and booking actions and receives availability, quotes, booking status, messages and the Trust Score. "
          "The **administrator** supplies location definitions and reset commands and receives overview figures, the user and booking lists and the Strategy Insights replay. "
          "The **payment provider** is Stripe in test mode, or the built-in demo checkout when no key is configured; it receives an amount and a reservation number and returns a confirmation."),
        H3("5.3.2 Level 1: six processes"),
        *_dg("dfd1", 5.4),
        P("Level 1 shows six processes and five data stores. **1.0 Authenticate** reads and writes the users store (D1). **2.0 Search availability** reads locations (D2) and reservations (D3). **3.0 Reserve and pay** writes reservations (D3) and payments (D4). "
          "**4.0 Check in** reads D2 and D3 and, in the full-lot case, writes a second reservation (D3). **5.0 Check out** writes the buffer size back to D2 and appends to the trust events (D5). **6.0 Administer and analyse** reads everything and writes only location changes and buffer resets."),
        H3("5.3.3 Level 2: reservation and payment"),
        *_dg("dfd2", 5.4),
        P("The reservation process is expanded because it holds the main business rules. Six sub-processes run in a fixed order, and the order matters: the suspension check comes before the admission rule so that a suspended driver never consumes an availability query; "
          "the fee is quoted only after admission; and the account credit is applied before the payment row is written, so a booking fully covered by credit is stored as paid and needs no checkout. "
          "Both refusals (403 and 409) store a declined booking before raising the error, which is what feeds the declined counter on the admin overview."),

        H2("5.4 UML design"),
        H3("5.4.1 Class diagram"),
        *_dg("uml", 5.6),
        P("The persistence layer is object-relational: five SQLAlchemy classes map to five tables " + cite("sqla") + ". Behaviour is kept out of the model classes and placed in `engine.py` as functions that take a session, which makes each rule a plain function that a test can call with an in-memory database. "
          "The only other classes are four pydantic input models (`RegisterIn`, `LoginIn`, `LocationIn`, `ReservationIn`), which carry the length and range limits of the API. "
          "The diagram draws the engine, the auth module and the scheduler job as class-like boxes so that the dependencies are visible."),
        H3("5.4.2 Sequence diagram"),
        *_dg("seq", 5.4),
        P("The sequence follows one booking from search to check-out. The reservation request passes four gates before any row is written: the token, the existence of the location, the suspension check and the admission rule. "
          "The payment is created in the same transaction as the reservation, and the checkout link is requested afterwards, so a failure of the payment provider leaves a booking with a pending payment row instead of a lost booking. "
          "At check-out the buffer is updated in the same request as the booking status, then the trust update commits its own events."),
        H3("5.4.3 Use-case diagram"),
        *_dg("usecase", 4.8),
        P("There are two human actors and one system actor. Reserving includes the availability check and the suspension check, and check-in is extended by the alternate move when the lot is full. "
          "The administrator account can also use the driver screens (the sidebar shows both groups), but only the admin routes are role-guarded."),

        H2("5.5 Database design"),
        *_dg("er", 5.4),
        P("The schema has five tables in one SQLite file, `parksure.db`; it is created by `Base.metadata.create_all` at start-up, and the file path can be changed with `PARKSURE_DB` to point SQLAlchemy at another database. "
          "A user has many reservations and many trust events; a location has many reservations; a reservation has at most one payment (a unique foreign key). Deleting a user or a location cascades, through the ORM, to the reservations and events that belong to it."),
        TAB("The five tables and their columns.",
            ["Table", "Columns", "Keys, indexes, defaults"],
            [["users", "id, name(120), email(200), password_hash(255), role(20), trust_score, benefit_streak, warning_count, account_credit, suspended_until, created_at",
              "PK id; unique index on email; role driver or admin; trust_score 3.0; streak, warnings and credit 0"],
             ["parking_locations", "id, name(160), address(255), latitude, longitude, capacity, buffer_size, price_per_hour, last_buffer_reset, created_at",
              "PK id; buffer_size 1; price 3.0; capacity limited to 1-5,000 by the schema"],
             ["reservations", "id, user_id, location_id, start_time, end_time, status(30), fee, fee_multiplier, checked_in_at, checked_out_at, decline_reason, parent_id, created_at",
              "PK id; FK user_id and location_id; indexes on user, location, start and end; status reserved; parent_id is a plain integer"],
             ["payments", "id, reservation_id, user_id, amount, currency, provider(20), stripe_session_id, stripe_payment_intent, status(30), created_at",
              "PK id; unique FK reservation_id; provider demo or stripe; status pending, paid, refunded or failed"],
             ["trust_events", "id, user_id, kind(20), detail(255), created_at",
              "PK id; FK user_id (indexed); kind benefit, warning, reward or penalty"]],
            widths=[1.2, 3.3, 1.9], align=["l", "l", "l"], size=9),
        P("Three design points deserve a note. The reservation window is stored as two timezone-aware timestamps and the overlap test is the half-open interval comparison `start < other_end AND end > other_start`, so a booking that ends at 14:00 does not conflict with one that starts at 14:00. "
          "The hold-back buffer is a column of the location, not a computed value, because it is state that grows and is reset by the scheduler. "
          "And the fee is stored on the reservation together with the multiplier that produced it, so a later change to the driver's score does not rewrite the price of an old booking."),

        H2("5.6 Core algorithm design"),
        *_dg("algo", 5.4),
        P("The engine makes three decisions at three moments. At **request time** it refuses a suspended driver and applies the admission rule: the number of reserved and active bookings that overlap the window plus the location's buffer must be smaller than its capacity. "
          "This is interval-overlap counting, the simplest form of the interval scheduling that " + cite("cabri") + " attributes to earlier reservation work " + cite("doulamis") + "; the buffer is what turns it into a rule that tolerates overstays. "
          "At **arrival time** it compares the number of bookings marked active at the location with its capacity; if the lot is full it scans every other location, keeps those whose own admission rule would accept the window, and books the one with the smallest great-circle distance " + cite("sinnott") + ". "
          "At **departure time** it compares the checkout instant with the end time plus ten minutes, grows the buffer on an on-time departure and updates the Trust Score."),
        *_dg("reward", 5.4),
        P("The Trust Score and the buffer are the two feedback loops. The score changes the fee multiplier from 1.75 at score 0 to 0.90 at score 5, so a driver who ends sessions late pays more and is eventually suspended; the buffer changes the number of bookable bays at the location. "
          "A consequence of the shipped design, measured in Chapter 8, is that the buffer rises when departures are on time, whereas the dynamic rule in " + cite("cabri") + " raises it when departures are late. The diagram shows the rule as implemented. "
          "The design keeps the alternate search simple on purpose, following the same paper: exactly one alternate is offered, because a second alternate would be too far from the driver's destination to be useful."),

        H2("5.7 Module design"),
        P("The code is split so that each file has one reason to change. Line counts below were measured from the repository when this report was built."),
        TAB("Modules, sizes and responsibilities.", ["Module", "Lines", "Responsibility"], mod_rows, widths=[2.2, 0.6, 3.6], align=["l", "r", "l"], size=9),
        P("Three decisions about this structure are worth recording. The rules sit in one module with no web imports, so the simulator in `scripts/parking_sim.py` can import the pure functions (haversine, fee multiplier) and a parity test can run the stateful ones against an in-memory database. "
          "The experiment scripts and the tests exercise the product's own functions and routes, not copies of them. "
          "And the console has its own small UI kit (buttons, cards, tables, badges, toasts, modals), so the pages contain layout and calls and no styling."),

        H2("5.8 API design"),
        P("All routes live under `/api`. Reads are GET and actions are POST; the three location-management routes use PUT and DELETE. Failures return the FastAPI `detail` string, which the console shows verbatim, so error messages are written for the driver, for example "
          "'Booking paused until ... after a recent late checkout.' or '... is fully reserved for the requested window'. The status codes follow one rule set: 401 means the token is missing or invalid, 403 means the role or the Trust Score does not allow the action, "
          "404 means the object does not exist or does not belong to the caller, 409 means the window is full, 400 means the request is well formed but not acceptable, and 422 means input validation failed."),
        TAB("The 22 routes of the ParkSure API.", ["Method", "Path", "Who", "Purpose", "Errors"], routes, widths=[0.55, 1.65, 0.7, 2.4, 1.1], align=["c", "l", "l", "l", "l"], size=8),
        P("`GET /api/search` and `GET /api/locations` need no login, so that the landing page can show live capacity. `GET /api/admin/insights` takes a window in days and is the only route that runs a simulation; "
          "it replays each location's stored bookings under no buffer, fixed buffers of one and three, and the dynamic rule, and returns the counts per location and in total."),

        H2("5.9 User interface design"),
        P("The console has eleven page components: a public landing page, a login page with sign-in and registration tabs, three driver pages (Find parking, My bookings, Trust score), five administrator pages (Overview, Locations, Strategy insights, All bookings, Users) and a not-found page. "
          "A role guard hides the administrator group from drivers, and a 401 from the API clears the session and returns to the login page. The visual language is a dark-first interface with a light theme, one accent colour, a three.js hero on the landing page and a static fallback image for users who prefer reduced motion."),
        TAB("Pages, routes and the endpoints they use.", ["Page", "Route", "Endpoints used"],
            [["Landing", "/", "GET /api/locations (live capacity and location names)"],
             ["Login and registration", "/login", "POST /api/auth/login, POST /api/auth/register"],
             ["Find parking", "/app/find", "GET /api/search, POST /api/reservations, GET /api/trust"],
             ["My bookings", "/app/bookings", "GET /api/reservations, POST /api/reservations/{id}/cancel, checkin, checkout, POST /api/payments/{id}/confirm"],
             ["Trust score", "/app/trust", "GET /api/trust"],
             ["Admin overview", "/app/admin", "GET /api/admin/overview, GET /api/admin/insights"],
             ["Admin locations", "/app/admin/locations", "GET, POST, PUT, DELETE /api/locations, POST /api/admin/reset-buffers"],
             ["Strategy insights", "/app/admin/insights", "GET /api/admin/insights"],
             ["All bookings", "/app/admin/bookings", "GET /api/admin/bookings"],
             ["Users", "/app/admin/users", "GET /api/admin/users"]],
            widths=[1.6, 1.6, 3.2], align=["l", "l", "l"], size=9.5),
        P("Four design rules were applied to every working page. Each page opens with its purpose in one sentence. Long actions show a busy state and finish with a toast, and the toast names the consequence (for example 'Moved to Central Station Garage'). "
          "Money and times are formatted the same way everywhere, and a booking's status is a coloured badge with the reason beneath it when it is declined or failed. "
          "Errors from the API appear in an inline panel with a retry button. Chapter 8 shows the working pages with real data; the screens below illustrate the design itself."),
        *shot("08_reserve_dialog.png", "Reserve dialog on the Find parking page: the estimate uses the same formula as the server (hours x rate x trust multiplier).", 5.0, 3.5),
        *shot("13_trust_score.png", "Trust score page: score, fee multiplier, benefit streak and the event timeline.", 5.0, 3.5),
        *shot("17_admin_overview.png", "Admin overview: totals read live from the reservation database.", 5.0, 3.5),

        H2("5.10 Design decisions and trade-offs"),
        P("Every design has costs. The table records the main decisions, what each bought and what it cost, so that the limitations in Chapter 9 can be traced back to a choice and not to an accident."),
        TAB("Principal design decisions.",
            ["Decision", "Reason", "Cost"],
            [["Keep the rules in `engine.py`, separate from the routes", "Each rule is testable with an in-memory database; the simulator and the replay reuse the same functions", "Two rules (buffer growth and the late test) are still written inside the check-out route"],
             ["SQLite with `create_all` and seeded data", "Zero configuration; a clean database is re-seeded on first start", "One writer at a time; no migrations; the admission check and the insert are not atomic"],
             ["Admit on forecast (overlapping bookings plus buffer), check physical space only on arrival", "Cheap, deterministic, explainable to the driver; no sensors needed", "The arrival check counts bookings marked active, not real cars; the alternate is booked without re-checking its own bays"],
             ["One nearest alternate by haversine distance", "Follows the base paper; no routing service or external API", "Straight-line distance, not driving distance; no choice for the driver"],
             ["Fee multiplier and suspension from the Trust Score", "Gives drivers a price signal for punctuality", "A suspended driver is locked out for at least 14 days after the last warning because the check repeats at each request"],
             ["Stripe test mode with an offline demo checkout", "Everything works without keys; the demo is labelled in the interface", "The demo confirmation route is not authenticated (Chapter 7 reports it)"],
             ["Deterministic Strategy Insights replay", "The same stored history always gives the same counts, so results can be checked", "It replays seeded history; its 45-minute overstay linger is a model, not a measurement"]],
            widths=[2.0, 2.4, 2.0], align=["l", "l", "l"], size=9),
        P("Two further choices concern what was left out. There is no vehicle profile (plate, model) and no downloadable receipt: the batch objectives mention both, and the delivered design stores only the payment record. "
          "There is also no live occupancy feed, so 'real-time availability' means the forecast of bookable bays for a chosen window, computed from stored bookings at the moment of the request. These are stated plainly as the gap between the objectives and the delivered design."),
    ]
    return _trim(out) if F.REPORT else out
