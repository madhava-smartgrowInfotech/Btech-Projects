"""Appendices A (important code), B (installation and user guide) and C (additional screens) for ParkSure.

Code excerpts are cut from the real files in 8.ProjectCode at build time, so they can never drift from the code.
"""
import ast
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


# ------------------------------------------------------------------------------ source helpers
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a module-level function exactly as it stands (docstring removed unless doc=True)."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            end = node.end_lineno
            body = lines[start - 1:end]
            if not doc and ast.get_docstring(node):
                d = node.body[0]
                body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:end]
            return "\n".join(body)
    raise KeyError(name)


def between(rel, first, last):
    """Lines from the first line containing `first` to the first later line containing `last` (inclusive)."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if first in l)
    j = next(k for k in range(i, len(lines)) if last in lines[k])
    return "\n".join(lines[i:j + 1])


def _wrap(text, width=104):
    """Wrap over-long code lines at a space, indenting the continuation, so a listing never runs off the page."""
    out = []
    for line in text.split("\n"):
        while len(line) > width:
            cut = line.rfind(" ", 0, width)
            if cut < 20:
                cut = width
            out.append(line[:cut])
            line = " " * (len(line) - len(line.lstrip()) + 8) + line[cut:].lstrip()
        out.append(line)
    return "\n".join(out)


def _C(text, size):
    return CODE(_wrap(text), size)


# ------------------------------------------------------------------------------ Appendix A
def _intro():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` as they stood when the results were measured; docstrings are removed to save space (the full files are in the repository). "
          "The rules in Sections A.1 to A.3 are explained with formulas in Chapter 6, and the routes in A.4 to A.6 show how the rules are applied to a request."),
    ]


def _common():
    return _intro() + [
        H2("A.1 Overlap count, admission and fee (app/engine.py)"),
        P("A bay is free at arrival if the reserved and active bookings that overlap the window, plus the hold-back buffer, stay below the capacity. The fee is the billed hours (at least a quarter of an hour) times the hourly rate times the multiplier of the driver's rounded Trust Score."),
        _C(fn("app/engine.py", "overlapping_count") + "\n\n" + fn("app/engine.py", "forecast_free") + "\n\n" + fn("app/engine.py", "fee_multiplier") + "\n\n" + fn("app/engine.py", "quote_fee"), 7.6),
        H2("A.2 Haversine distance and the nearest alternate (app/engine.py)"),
        _C(fn("app/engine.py", "haversine_km") + "\n\n" + fn("app/engine.py", "nearest_alternate"), 7.6),
        H2("A.3 Trust Score, suspension and the buffer reset job (app/engine.py)"),
        _C(fn("app/engine.py", "record_checkout_trust") + "\n\n" + fn("app/engine.py", "suspension_block") + "\n\n" + fn("app/engine.py", "reset_buffers_if_due"), 7.4),
        H2("A.4 The reservation route (app/main.py)"),
        P("The route runs the gates in a fixed order: location, window length, suspension, admission, fee, credit, payment. Both refusals store a declined booking before the error is raised."),
        _C(fn("app/main.py", "create_reservation"), 7.2),
        H2("A.5 The check-in route (app/main.py)"),
        _C(fn("app/main.py", "checkin"), 7.2),
        H2("A.6 The check-out route (app/main.py)"),
        _C(fn("app/main.py", "checkout"), 7.4),
        H2("A.7 Password hashing, tokens and role guards (app/auth.py)"),
        _C(fn("app/auth.py", "hash_password") + "\n\n" + fn("app/auth.py", "verify_password") + "\n\n" + fn("app/auth.py", "create_token") + "\n\n"
             + fn("app/auth.py", "current_user") + "\n\n" + fn("app/auth.py", "admin_user"), 7.4),
        H2("A.8 Rules of the simulator and the parity check (scripts/parking_sim.py, scripts/parity.py)"),
        P("The simulator re-states the admission, trust and suspension rules on plain numbers; the parity function runs the same random requests through the real engine and counts disagreements."),
        _C(fn("scripts/parking_sim.py", "admit") + "\n\n" + fn("scripts/parking_sim.py", "trust_update") + "\n\n" + fn("scripts/parking_sim.py", "suspended") + "\n\n"
             + fn("scripts/parity.py", "admission_parity"), 7.4),
    ]


def _report():
    return _intro() + [
        H2("A.1 Admission and fee (app/engine.py)"),
        _C(fn("app/engine.py", "overlapping_count") + "\n\n" + fn("app/engine.py", "forecast_free") + "\n\n" + fn("app/engine.py", "quote_fee"), 7.2),
        H2("A.2 Nearest alternate (app/engine.py)"),
        _C(fn("app/engine.py", "haversine_km") + "\n\n" + fn("app/engine.py", "nearest_alternate"), 7.2),
        H2("A.3 Trust Score and suspension (app/engine.py)"),
        _C(fn("app/engine.py", "record_checkout_trust") + "\n\n" + fn("app/engine.py", "suspension_block"), 7.0),
        H2("A.4 The check-in route (app/main.py)"),
        _C(fn("app/main.py", "checkin"), 6.8),
        H2("A.5 The check-out route (app/main.py)"),
        _C(fn("app/main.py", "checkout"), 7.0),
    ]


def code_blocks():
    return _report() if F.REPORT else _common()


# ------------------------------------------------------------------------------ Appendix B
def guide_blocks():
    out = [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB("Requirements", ["Item", "Needed"],
            [["Operating system", "Windows 10 or 11 for `run.bat` (measured on Windows 11 Pro); the Python and Node commands also work on other systems"],
             ["Python", "3.11 or newer on PATH (the virtual environment used for the measurements runs 3.14.7)"],
             ["Node.js and npm", "Node 20 or newer (measured with 24.19.0); the console uses Vite and React 19"],
             ["Python packages", "fastapi, uvicorn, sqlalchemy, pydantic with e-mail validation, pydantic-settings, python-jose, passlib with bcrypt, bcrypt, apscheduler, stripe, python-multipart, reportlab, playwright, httpx2 (`requirements.txt`)"],
             ["Extra for tests and experiments", "`pip install pytest requests` (and matplotlib for the document figures); Chrome or `playwright install chromium` for screenshots"],
             ["Hardware", "Any recent laptop; the measurements used a 12th-generation Intel Core i5-12500 with 15.7 GB of memory"],
             ["Accounts and keys", "None required. Stripe test keys are optional; without them the demo checkout is used"]],
            widths=[1.7, 4.7], align=["l", "l"], size=10),
        H2("B.2 Installation and start with run.bat"),
        N("Copy or clone the project so that `8.ProjectCode` is on a local disk.",
          "Open the folder and double-click `run.bat` (or run it from a command prompt). It checks Python and Node, creates `.venv` if absent, installs `requirements.txt` (several minutes on the first run) and runs `npm install` in `frontend`.",
          "It starts the FastAPI backend on port 8403 and the Vite frontend on port 5403 in two console windows, waits up to 60 seconds for both to answer, and opens `http://127.0.0.1:5403`. Keep both windows open.",
          "Sign in with a demo account (B.4) or register. To stop, close the two windows.",
          "For the documentation run the servers were started with the commands in B.3 and the browser was driven by Playwright; a fresh-machine installation through `run.bat` was not repeated."),
        H2("B.3 Manual start"),
        _C("# backend (from 8.ProjectCode)\n"
             "python -m venv .venv\n"
             ".venv\\Scripts\\python.exe -m pip install -r requirements.txt\n"
             ".venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8403\n\n"
             "# frontend (from 8.ProjectCode\\frontend)\n"
             "npm install\n"
             "npm run dev\n\n"
             "# backend only, with the original static pages, in Docker\n"
             "docker compose build && docker compose up        # http://localhost:8000", 8.0),
        H2("B.4 Demo accounts and settings"),
        TAB("Seeded accounts", ["Account", "Role", "Initial Trust Score"],
            [["admin@parksure.app / admin123", "Administrator", "5"],
             ["driver1@parksure.app / driver123, driver2@parksure.app", "Driver", "4"],
             ["driver3@parksure.app, driver6@parksure.app", "Driver (overstay history)", "2"],
             ["driver4, driver5, driver7, driver8 @parksure.app", "Driver", "3"]],
            widths=[3.2, 1.8, 1.4], align=["l", "l", "c"], size=10),
        P("All driver accounts use the password `driver123`. A newly registered account starts at Trust Score 3; the first account registered on an empty database becomes the administrator. "
          "The settings below are read from environment variables (the backend does not read `.env`); each has a default."),
        TAB("Environment variables", ["Variable", "Default", "Meaning"],
            [["PARKSURE_DB", "sqlite:///./parksure.db", "Database URL; a throw-away file is used by the tests and measurement scripts"],
             ["PARKSURE_JWT_SECRET", "development secret", "Signing key of the tokens; must be changed for any real deployment"],
             ["PARKSURE_BUFFER_INIT / _MAX / _RESET_HOURS", "1 / 5 / 24", "Hold-back buffer policy"],
             ["PARKSURE_B / PARKSURE_W", "3 / 2", "Benefits for +1 trust and warnings for -1"],
             ["PARKSURE_TRUST_THRESHOLD, _VIOLATION_DAYS, _COOLDOWN_HOURS", "1.5 / 14 / 24", "Suspension rule"],
             ["STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET", "empty", "Stripe test mode; empty means the offline demo checkout"],
             ["PARKSURE_PORT, PARKSURE_BASE_URL", "8000 / http://localhost:PORT", "Set by `run.bat` to 8403 and the frontend address"]],
            widths=[2.6, 1.4, 2.4], align=["l", "l", "l"], size=9.5),
        H2("B.5 Using the console"),
        TAB("Driver steps", ["Page", "What to do", "What you see"],
            [["Landing /", "Read the pitch, pick a window, press Search, or press Log in", "Live location and bay counts"],
             ["Login /login", "Press a demo chip, or type e-mail and password, or open Create account", "Welcome toast and the Find parking page"],
             ["Find parking", "Choose arrival and departure, press Search availability, press Reserve on a card, read the estimate, confirm", "Cards with free bays, buffer and price; a confirmation with the fee, multiplier and payment status"],
             ["My bookings", "Press Confirm demo payment (or pay through Stripe), Check in on arrival, Check out before the end plus ten minutes, or Cancel", "Status badges and toasts; a moved booking shows 'Alternate for #...'"],
             ["Trust score", "Read the score, fee multiplier, streak and event timeline", "Stars, progress to the next reward, any suspension notice"]],
            widths=[1.3, 3.0, 2.1], align=["l", "l", "l"], size=9.5),
        TAB("Administrator steps", ["Page", "What to do", "What you see"],
            [["Overview", "Read the live totals", "Users, locations, reservations, paid revenue, unable to park, declined, and the policy chart"],
             ["Locations", "Add, edit or delete a location; Reset all buffers", "Table with bays, buffer, price and coordinates"],
             ["Strategy insights", "Choose the window and press Recompute", "Four buffer policies on the stored history, per-location table, policy and totals"],
             ["All bookings", "Search by number or location; filter by status", "The 300 latest reservations"],
             ["Users", "Search by name or e-mail", "Trust, streak, warnings, credit and whether booking is allowed"]],
            widths=[1.3, 2.7, 2.4], align=["l", "l", "l"], size=9.5),
        P("A booking can be checked in at any time while it is reserved, and the console does not restrict check-in to the booked window; check out before the end time plus ten minutes to earn a benefit. "
          "A payment shown as pending can be confirmed from My bookings when the demo checkout is in use."),
        H2("B.6 API quick reference"),
        P("The commands below use `curl` with Git Bash quoting; replace TOKEN with the token returned by the login call. Use 127.0.0.1, not localhost, to avoid the IPv6 delay seen on Windows."),
        _C("curl http://127.0.0.1:8403/api/locations\n"
             "curl -X POST -H \"Content-Type: application/json\" -d '{\"email\":\"driver1@parksure.app\",\"password\":\"driver123\"}' http://127.0.0.1:8403/api/auth/login\n"
             "curl \"http://127.0.0.1:8403/api/search?start_time=2026-11-02T09:00:00Z&end_time=2026-11-02T11:00:00Z\"\n"
             "curl -X POST -H \"Authorization: Bearer TOKEN\" -H \"Content-Type: application/json\" \\\n"
             "     -d '{\"location_id\":2,\"start_time\":\"2026-11-02T09:00:00Z\",\"end_time\":\"2026-11-02T11:00:00Z\"}' http://127.0.0.1:8403/api/reservations\n"
             "curl -X POST -H \"Authorization: Bearer TOKEN\" http://127.0.0.1:8403/api/reservations/355/checkin\n"
             "curl -X POST -H \"Authorization: Bearer TOKEN\" http://127.0.0.1:8403/api/reservations/355/checkout\n"
             "# interactive documentation: http://127.0.0.1:8403/docs", 7.6),
        H2("B.7 Tests, experiments and screenshots"),
        _C("python -m pytest tests -q                       # 70 tests\n"
             "python scripts/smoke_test.py                     # 27 checks on a throw-away database\n"
             "python scripts/run_experiments.py                # simulator, parity, trust dynamics, seeded replay -> experiments/**/metrics.json\n"
             "python scripts/measure_api.py --base http://127.0.0.1:8503   # latency, race and probes (start a throw-away backend first)\n"
             "python scripts/capture_docs_screens.py           # 24 screenshots -> docs/screenshots (app on 8403 and 5403, fresh database)\n"
             "python scripts/make_report_facts.py              # docs/REPORT_FACTS.md\n"
             "python scripts/compute_buffer_strategy_metrics.py --window-days 60", 8.0),
        H2("B.8 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and fix"],
            [["Python or Node was not found", "Install it and tick Add to PATH for Python, then reopen the terminal and run `run.bat` again"],
             ["Windows SmartScreen blocks run.bat", "More info, then Run anyway; the file is a plain-text launcher that can be inspected"],
             ["Port 8403 or 5403 already in use", "Another copy is running; close it. The frontend refuses another port on purpose because the backend address is fixed"],
             ["The page says 'Cannot reach the ParkSure server'", "The backend window is closed or crashed; read its error and start it again"],
             ["Dependency installation fails", "Check the internet connection, delete `.venv` or `frontend\\node_modules` and run `run.bat` again"],
             ["The demo data look wrong or crowded", "Stop the backend, delete `parksure.db`, start again: the tables are re-created and re-seeded"],
             ["A booking is refused with 'fully reserved'", "Overlapping bookings plus the buffer reach the capacity for that window; choose another time or location"],
             ["A driver is refused with 'Booking paused'", "The Trust Score is below 1.5 with a recent late checkout; the lockout lasts until the last warning is 14 days old, or the account can be re-seeded"],
             ["API calls from Python take about 2 seconds", "Use `127.0.0.1` instead of `localhost`"]],
            widths=[2.4, 4.0], align=["l", "l"], size=9.5),
    ]
    return _guide_trim(out) if F.REPORT else out


def _guide_trim(out):
    """Compact variant for the full report: requirements as one sentence, driver steps only, short troubleshooting."""
    res, skip = [], False
    for b in out:
        if b[0] == "h2":
            skip = b[1].startswith(("B.1", "B.6", "B.7"))
            if b[1].startswith("B.1"):
                res.append(("h2", "B.1 Requirements"))
                res.append(("p", "Python 3.11 or newer, Node.js 20 or newer and the packages in `requirements.txt`; for tests `pip install pytest requests`. No account or key is required: Stripe test keys are optional and the demo checkout is used without them."))
            if b[1].startswith("B.7"):
                res.append(("h2", "B.7 Tests and experiments"))
                res.append(("code", "python -m pytest tests -q\npython scripts/smoke_test.py\npython scripts/run_experiments.py\npython scripts/capture_docs_screens.py", 8.0))
        if skip:
            continue
        if b[0] == "tab" and b[1].startswith("Environment variables"):
            b = ("tab", b[1], b[2], b[3][:2]) + tuple(b[4:])
        if b[0] == "tab" and b[1].startswith("Common problems"):
            keep = ("Port 8403", "The page says", "The demo data", "A booking is refused", "A driver is refused")
            b = ("tab", b[1], b[2], [r for r in b[3] if r[0].startswith(keep)]) + tuple(b[4:])
        res.append(b)
    return res


# ------------------------------------------------------------------------------ Appendix C
def screens_blocks():
    SH = F.shot

    def pair(a, ca, b, cb):
        return PAIR([(SH(a), ca), (SH(b), cb)], 2.95)

    out = [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The screens below are captures that are not shown in Chapter 8: the public pages, the login page, the check-in result, the two-driver arrival scenario, the administrator's lists and the phone and API-documentation views. "
          "All were taken from the running application at 1440 x 900 pixels (the phone view at 390 x 844) on a freshly seeded database on 2026-10-26."),
        pair("01_landing_dark.png", "Additional screen: landing page, dark theme, with the live count of locations and bays and the search form.",
             "04_landing_light.png", "Additional screen: landing page, light theme."),
        P("The landing page is public. Its badge reads '6 locations, 81 bays, live' (the five seeded locations plus the one-bay Kiosk Bay added for the arrival scenario) and its search form leads to the Find parking page after login. "
          "Both themes use the same colour tokens, and the toggle is in the top bar."),
        pair("02_landing_how_it_works.png", "Additional screen: landing page 'how it works' section with live capacity bars per location.",
             "03_landing_features.png", "Additional screen: landing page feature cards (buffer, Trust-based pricing, nearest alternate, check-in and out, Stripe or demo checkout, Strategy insights)."),
        P("The first capture shows step one of four, the search for a time window, next to real locations from the database. The second lists the six features that correspond to the engine's mechanisms; each card restates a rule in one sentence, for example that exactly one nearest location is booked when a site is full and that the fee is credited back when none has space."),
        FIG(SH("05_login.png"), "Additional screen: login page with the Log in and Create account tabs and the two demo-account chips.", F.shot_w(SH("05_login.png"), 4.6, 3.2)),
        P("The login page validates the e-mail format and the password before calling the API; the chips fill in the seeded driver or administrator account. The same page registers a new account."),
        pair("11_check_in_toast.png", "Additional screen: My bookings after a check-in; booking #348 is Parked and shows the Check out action, with the 'Checked in' toast.",
             "14_bookings_before_arrival.png", "Additional screen: a second driver's bookings before arrival: one reserved booking at the one-bay Kiosk Bay."),
        P("In the first capture the table lists the driver's 45 bookings with a Parked tab count of one; the checked-in booking has no payment yet, which the interface shows as 'Payment due' next to a Confirm demo payment action, because check-in does not wait for payment. "
          "The second capture is the starting point of the full-lot scenario: the Kiosk Bay's only bay is already occupied by the first driver."),
        FIG(SH("16_bookings_after_move.png"), "Additional screen: after the arrival at the full lot: booking #353 is marked Unable to park and booking #354 at Central Station Garage is Parked as 'Alternate for #353'.", F.shot_w(SH("16_bookings_after_move.png"), 5.2, 3.6)),
        P("The original booking carries the reason 'No free slot at Kiosk Bay on arrival; moved to Central Station Garage (0.1 km away)', and the replacement booking has the alternate location's own rate (4.00 dollars for the hour) and no payment row of its own, shown as a dash. "
          "This is the behaviour of the code: the original payment stays with the failed booking."),
        pair("18_admin_locations.png", "Additional screen: administrator's Locations page with bays, buffer, price, coordinates and the Edit, Delete and Reset all buffers actions.",
             "20_admin_bookings.png", "Additional screen: administrator's All bookings page with search and status filter."),
        P("On the locations page the buffer column shows the policy at work: Central Station Garage has a buffer of 2 because one on-time check-out raised it from 1, while the Kiosk Bay, created with buffer 0, still shows 0. "
          "The bookings page lists the latest reservations of every driver, including the alternate booking marked 'Alternate for #353' and the failed booking it replaced."),
        pair("21_admin_users.png", "Additional screen: administrator's Users page with trust, on-time streak, warnings, credit and booking permission.",
             "22_admin_insights_table.png", "Additional screen: Strategy insights, per-location actual outcomes against the replayed dynamic policy, and the policy and totals panel."),
        P("The users table shows the seeded Trust Scores (4, 4, 2, 3, 3, 2, 3, 3 for the eight demo drivers) and that every account is currently allowed to book. "
          "The insights panel lists the buffer policy (start 1, maximum 5, reset every 24 hours) and the replay totals for the 60-day window; Old Town Deck, the over-subscribed lot, accounts for most of the refusals under the dynamic policy."),
        pair("23_mobile_find_parking.png", "Additional screen: Find parking at phone width (390 px): the sidebar becomes a menu and the form and cards stack.",
             "24_api_docs.png", "Additional screen: the FastAPI OpenAPI page at /docs on the backend port, listing the 22 routes with the Authorize button for the bearer token."),
        P("The phone capture shows the responsive layout; the API page is generated by FastAPI from the route definitions and can be used to try any route with a token."),
    ]
    return _screens_trim(out) if F.REPORT else out


def _screens_trim(out):
    """Compact variant for the full report: shorter explanations, the second and third pairs of public screens dropped."""
    res, drop = [], 0
    for b in out:
        if b[0] == "pair" and "02_landing_how_it_works" in b[1][0][0]:
            drop = 2           # this pair and its paragraph
        if drop:
            drop -= 1
            continue
        if b[0] == "p" and b[1].startswith("The screens below are captures"):
            b = ("p", "The screens below were not shown in Chapter 8; all were captured at 1440 x 900 pixels (the phone view at 390 x 844) on a freshly seeded database on 2026-10-26.")
        if b[0] == "p" and b[1].startswith("The landing page is public"):
            b = ("p", "The landing page is public; its badge reads '6 locations, 81 bays, live' (the five seeded locations plus the one-bay Kiosk Bay added for the arrival scenario). Both themes use the same colour tokens.")
        if b[0] == "p" and b[1].startswith("The login page validates"):
            b = ("p", "The login page validates the e-mail format and the password before calling the API; the chips fill in a seeded account.")
        if b[0] == "p" and b[1].startswith("On the locations page"):
            b = ("p", "On the locations page Central Station Garage has a buffer of 2 because one on-time check-out raised it from 1, while the Kiosk Bay, created with buffer 0, still shows 0.")
        if b[0] == "p" and b[1].startswith("The users table shows"):
            b = ("p", "The users table shows the seeded Trust Scores and that every account is allowed to book; the insights panel lists the buffer policy and the replay totals, with Old Town Deck accounting for most dynamic-policy refusals.")
        res.append(b)
    return res
