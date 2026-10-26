"""Chapter 7: System Testing for ParkSure. Numbers come from facts.py (experiments/**/metrics.json) and docs/REPORT_FACTS.md sections 5-8."""
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def _lat_rows():
    rows = []
    for k, v in F.LAT["endpoints"].items():
        if k.startswith("throughput"):
            continue
        rows.append([k, f"{v['mean_ms']:.1f}", f"{v['p50_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['p99_ms']:.1f}", f"{v['max_ms']:.1f}"])
    return rows


def _probe_rows():
    s = F.SEC
    yn = lambda b: "Yes" if b else "No"  # noqa: E731
    return [
        ["Unauthenticated `GET /api/payments/demo-confirm` on a pending booking",
         f"HTTP {s['unauthenticated_demo_confirm_marks_paid']['http_status']}; payment status changed from {s['unauthenticated_demo_confirm_marks_paid']['status_before']} to {s['unauthenticated_demo_confirm_marks_paid']['status_after']}",
         "Defect: the demo-checkout endpoint takes no token, so anyone who knows a booking number can mark it paid"],
        ["Token forged with the shipped default JWT secret, sent to `/api/admin/overview`",
         f"HTTP {s['forged_token_with_default_secret']['http_status']}; accepted: {yn(s['forged_token_with_default_secret']['accepted'])}",
         "Defect when the secret is not changed: the development secret in `config.py` is public; production must set `PARKSURE_JWT_SECRET`"],
        ["30 wrong passwords in a row, then the right one",
         f"All 401: {yn(s['login_has_no_lockout_or_rate_limit']['all_401'])}; correct login afterwards: HTTP {s['login_has_no_lockout_or_rate_limit']['correct_login_after']}",
         "Gap: no lockout and no rate limit on login (each attempt costs about 220 ms of bcrypt work, which slows guessing only slightly)"],
        ["SQL-injection style text in the login e-mail, the login password and the search time",
         f"HTTP {s['injection_inputs']['login_email_payload']}, {s['injection_inputs']['login_password_payload']} and {s['injection_inputs']['search_param_payload']}; server error: {yn(s['injection_inputs']['any_server_error'])}",
         "Passed: input is validated by pydantic and every query is built by the ORM with bound parameters"],
        ["Another driver cancels a booking that is not theirs",
         f"HTTP {s['cross_user_cancel_blocked']['http_status']}",
         "Passed: an unknown or foreign booking answers 404 and reveals nothing"],
        ["Booking window two days in the past",
         f"HTTP {s['past_window_accepted']['http_status']}; accepted: {yn(s['past_window_accepted']['accepted'])}",
         "Gap: only the 30-day length limit is checked, not that the start lies in the future"],
        ["Check-in 25 days before the booked window",
         f"HTTP {s['early_checkin_accepted']['http_status']}; accepted: {yn(s['early_checkin_accepted']['accepted'])}",
         "Gap: check-in is not tied to the booked window, so a bay can be occupied long before the booking starts"],
        ["Script tag as a user name",
         f"HTTP {s['markup_in_name']['http_status']}; stored verbatim: {yn(s['markup_in_name']['stored_verbatim'])}",
         "Acceptable for the React console, which escapes text when it renders; a different client would have to escape it itself"],
    ]


def blocks():
    th = F.LAT["endpoints"]["throughput_search_8_threads"]
    mb = F.MB
    fa = mb["forecast_free (admission, 100 bookings at the location)"]
    na = mb["nearest_alternate over 49 other locations"]
    hv = mb["haversine_km (one pair)"]
    race = F.RACE
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("ParkSure was handed over as a working web application with one smoke script and a screenshot script, and no automated test suite. "
            "The documentation run added a pytest suite and the measurement scripts used in Chapter 8. The testing follows the structure of the code. "
            "The Smart Availability Engine in `app/engine.py` is a set of small functions with exact, checkable rules (the admission inequality, the haversine distance, the fee multiplier, the Trust Score counters, the suspension rule, the buffer reset), "
            "so it is tested at unit level with assertions whose right answer is known in advance. The 22 API routes are tested through FastAPI's test client against a throw-away SQLite database that the application seeds on start. "
            "A smoke script walks the complete driver and admin flow, and a separate set of probes measures latency, concurrency and a few security questions against a running server."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest, tests/test_engine.py: haversine, fee multiplier and quote, admission rule, nearest alternate, Trust Score, suspension, buffer reset, policy constants", f"{F.PYTEST_ENGINE} tests", "All passed"],
               ["API / integration", "pytest with the FastAPI test client, tests/test_api.py: authentication, role guards, locations, search, reservations, check-in and check-out, payments, admin", f"{F.PYTEST_API} tests", "All passed"],
               ["Simulator parity", "pytest, tests/test_sim_parity.py: the experiment simulator against the real engine (admission, trust, suspension), determinism, one outcome per request", f"{F.PYTEST_PARITY} tests", f"All passed; {F.PAR['total_cases']:,} decisions compared, {F.PAR['total_mismatches']} mismatches"],
               ["Functional / smoke", "scripts/smoke_test.py: register, search, reserve, pay, check in, check out, trust, cancel and the admin screens on a throw-away database", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Screens", "Playwright walk of the React console on a fresh seeded database (scripts/capture_docs_screens.py)", "24 screenshots", "Rendered with real application data (Section 7.8)"],
               ["Performance, concurrency, security", "scripts/measure_api.py against a live server on 127.0.0.1", "12 endpoints x 200 calls; 10 race trials; 8 probes", "Sections 7.5 and 7.7"]],
              widths=[1.2, 3.2, 1.1, 1.3], align=["l", "l", "l", "l"], size=9.5),
          P(f"The complete suite of {F.PYTEST_TOTAL} tests passed ({F.PYTEST_PASSED} passed, none failed). Everything was run on one machine: a 12th-generation Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, Windows 11 and Python 3.14.7, with FastAPI 0.141.1 and SQLAlchemy 2.0.52. "
            "Timings were taken while other programs were running on the same machine and are indicative.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The file `tests/test_engine.py` holds **{F.PYTEST_ENGINE} tests, and all of them passed**. They run against an in-memory SQLite database that is separate from the one used by the API tests, "
            "and each test builds only the locations, users and bookings it needs, so one rule is checked at a time. Windows are placed days in the future so that no test depends on the clock."),
          TAB("Unit tests of the engine, grouped by rule (tests/test_engine.py).",
              ["Rule (tests)", "What is asserted"],
              [["Haversine distance (3)", "The distance from a point to itself is zero; London to Paris comes out at about 343.5 km (within 1.5 km); the distance is the same in both directions"],
               ["Fee multiplier (6 + 1 + 2 tests)", "Scores 0 to 5 map to 1.75, 1.50, 1.25, 1.00, 0.95 and 0.90; scores outside the range are clamped; a two-hour booking at $4.00 per hour costs $8.00 at score 3 and $7.20 at score 5; a one-minute booking is billed as 0.25 hour ($1.00)"],
               ["Admission rule (3)", "With capacity 3 and buffer 1 the third booking in the same window is refused (2 + 1 is not below 3); bookings in other windows and cancelled bookings are not counted; with buffer 0 a location can be filled completely"],
               ["Nearest alternate (3)", "A location that can never be admitted (capacity 1, buffer 1) is skipped; the closer of two eligible locations is chosen and its distance equals the haversine value; with every other location excluded the answer is none and the distance is 0"],
               ["Trust Score (5)", "Three on-time checkouts raise the score from 3 to 4 and write three benefit events and one reward event; the score never exceeds 5 or falls below 0; two late checkouts lower it by one; a late checkout resets the benefit streak"],
               ["Suspension (3)", "A driver in good standing is not blocked; a low score without a recent warning is not blocked; a score of 1 with a recent warning is blocked, a cooldown time is stored, and the cooldown keeps blocking"],
               ["Buffer reset (2)", "A buffer of 4 whose last reset is 25 hours old returns to 1; one reset 3 hours ago is left at 4"],
               ["Policy constants (1)", "Initial buffer 1, maximum 5, reset every 24 hours, 3 benefits and 2 warnings, start score 3.0 and suspension threshold 1.5 are the documented values"]],
              widths=[1.9, 4.6], align=["l", "l"], size=9.5),
          P("The admission test fails if the inequality in `forecast_free` is changed from strict to non-strict, which would silently let the buffer be booked, and the trust tests fail if a late checkout does not reset the benefit streak.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration and API testing"),
          P(f"The file `tests/test_api.py` holds **{F.PYTEST_API} tests, and all of them passed**. A session-scoped test client starts the real application, which creates the tables and seeds the demo data, "
            "so the tests exercise the same start-up path as a user. They cover the routes in the order a driver meets them."),
          TAB("API and integration tests by area (tests/test_api.py).",
              ["Area (tests)", "What is asserted"],
              [["Authentication (10)", "The seeded admin and driver can log in; a wrong password and an unknown user answer 401; a duplicate e-mail (compared without regard to case) answers 400; a short name, an invalid e-mail and a short password answer 422; `/api/auth/me` needs a valid token; a new driver starts at trust 3.0; passwords are stored as bcrypt hashes"],
               ["Role guards (2)", "A driver receives 403 on every admin route and on admin writes; an anonymous reservation request receives 401"],
               ["Locations (1)", "Create, update, validation (latitude 95 is refused), 404 on an unknown location, delete and a second delete"],
               ["Search (2)", "A location with capacity 5 and buffer 1 shows 4 bookable bays, and 3 after one booking; end before start and a window over 31 days answer 400 and a missing parameter 422"],
               ["Reservations (8)", "The fee uses the trust multiplier (2 h at $5.00 is $10.00 at multiplier 1.0); a full window returns 409 and stores a declined booking; end before start gives 422; an unknown location 404; a window over 30 days 400; cancelling a paid booking refunds the fee to account credit and a second cancel answers 400; credit offsets the next fee; another user's booking cannot be cancelled or checked in (404)"],
               ["Check-in and check-out (5)", "An on-time round trip completes the booking, grows the location's buffer from 1 to 2 and writes a benefit event; checkout without check-in and a second check-in answer 400; a late checkout records one warning; with a one-bay location occupied the second driver is moved to the nearest alternate, 0.5 to 2 km away, with `parent_id` set; with no alternate the booking is marked failed and the fee is credited"],
               ["Suspension (1)", "A driver with score 1.0 and a recent warning receives 403 with the pause message"],
               ["Payments (2)", "Demo confirmation sets the payment to paid; the Stripe webhook is inert (`received: false`) when no key is configured"],
               ["Admin (5)", "Overview fields and user count; four strategies in Strategy Insights with the policy init 1, max 5, reset 24; two calls with the same input give identical totals; reset sets every buffer to 1; a new registration on a seeded database is a driver, not an admin"]],
              widths=[1.7, 4.8], align=["l", "l"], size=9.5),
          P(f"A further {F.PYTEST_PARITY} tests (tests/test_sim_parity.py) check the simulator used for the experiments of Chapter 8 against the real engine. "
            f"`scripts/parity.py` replays {F.PAR['admission']['cases']:,} admission decisions on five capacity and buffer settings, {F.PAR['trust']['cases']:,} trust updates for 200 simulated drivers, and {F.PAR['suspension']['cases']} suspension decisions in the engine and in the simulator, "
            f"and compares them one by one: **{F.PAR['total_mismatches']} mismatches in {F.PAR['total_cases']:,} decisions**. This shows that the rules the simulator applies are the product's rules, not that it is a good model of drivers.")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing with the smoke script"),
          P(f"`scripts/smoke_test.py` starts the application on a throw-away database, so the real `parksure.db` is untouched, and runs **{F.SMOKE_TOTAL} checks, {F.SMOKE_PASSED} of which passed**. "
            "It is written from the driver's point of view: reject a bad password, register, reject a duplicate e-mail, read the profile, list the seeded locations, search, reject an end time before the start, reserve, receive a checkout, confirm the demo payment, check in, check out on time, read the trust events, "
            "reserve a second booking and cancel it with a refund, refuse a second cancel, list the bookings, refuse a window over 30 days, and confirm that a driver cannot reach the admin routes. "
            "It then signs in as the administrator and checks the overview, the user list, the booking list, the four strategies of Strategy Insights, adding, editing and deleting a location, and resetting the buffers. "
            "A twenty-eighth, optional check confirms that the Vite development server proxies `/api` to the backend; it is skipped when the dev server is not running, as it was in this run."),
          ]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("Authentication uses bcrypt password hashes (cost 12) and signed JWT tokens that expire after 12 hours; roles are enforced by a dependency on every admin route. "
            "`scripts/measure_api.py` sends eight probes to a running server on a throw-away database. They were written by the project team to test its own system; they are not a penetration test and they were chosen from what the code suggested might be weak."),
          TAB("Security probes and what they showed.", ["Probe", "Observed", "Reading"], _probe_rows(), widths=[2.2, 2.0, 2.3], align=["l", "l", "l"], size=9.2),
          P("Four of the eight probes are findings against the product, not passes: the unauthenticated demo-confirm route, the default signing secret, the missing login throttle and the unchecked booking and check-in times. "
            "They are reported here and again in Chapters 8 and 9 because they limit what can honestly be claimed about the objective of secure online payment. "
            "None was corrected in the code during the documentation run. The demo route exists so that the product is usable without Stripe keys, and in a deployment with Stripe configured it should be removed or restricted to authenticated owners.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          TAB("Edge cases and how the product behaves.", ["Case", "Behaviour", "Result"],
              [["End time not after start time", "422 from the schema (and 400 from the search route)", "Passed"],
               ["Booking longer than 30 days", "400, reservations are limited to 30 days", "Passed"],
               ["Unknown or foreign booking", "404", "Passed"],
               ["Cancel or check in a booking in the wrong state", "400 with the current state in the message", "Passed"],
               ["Window that is full (overlapping bookings + buffer at capacity)", "409, a declined booking with the reason is stored", "Passed"],
               ["Cancelled booking in the same window", "Not counted by the admission rule", "Passed"],
               ["Booking shorter than 15 minutes", "Billed as 0.25 hour", "Passed"],
               ["Site physically full at check-in, an alternate exists", "Moved to the nearest alternate, new booking linked by `parent_id`", "Passed"],
               ["Site full and no alternate", "Booking marked failed, fee credited to the account", "Passed"],
               ["Driver at trust 1.0 with a recent warning", "403, booking paused for 24 hours", "Passed"],
               ["Trust score at 5 or 0", "Not raised above 5, not lowered below 0", "Passed"],
               ["Booking start in the past", "Accepted", "Gap (Section 7.5)"],
               ["Check-in long before the window", "Accepted", "Gap (Section 7.5)"],
               ["Many simultaneous requests for the last bay", "Occasionally more than one accepted", "Defect (Section 7.7)"]],
              widths=[2.7, 2.6, 1.2], align=["l", "l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P(f"`scripts/measure_api.py` calls the live API on 127.0.0.1 and sends 200 sequential requests to each endpoint with a persistent connection. The server was one uvicorn process on a SQLite file, on the machine described in Section 7.1. "
            "Calls went to 127.0.0.1 because on this machine the name `localhost` adds about two seconds per request through an IPv6 fallback, which would make every latency far too high."),
          TAB("Response time of the API (milliseconds, 200 sequential requests per endpoint).", ["Endpoint", "Mean", "p50", "p95", "p99", "Max"], _lat_rows(),
              widths=[2.9, 0.7, 0.7, 0.7, 0.7, 0.8], align=["l", "c", "c", "c", "c", "c"], size=9.5)]
    b.append(FIG(F.fig("f05_api_latency.png"), "Mean and 95th-percentile response time of each endpoint of the live API.", 5.6))
    b += [P(f"Everything a driver does in one click answers within about {F.lat('POST /api/reservations/{id}/checkin', 'p95_ms'):.0f} to {F.lat('POST /api/reservations', 'p95_ms'):.0f} ms at the 95th percentile "
            f"(search {F.lat('GET /api/search'):.1f} ms mean, reservation {F.lat('POST /api/reservations'):.1f} ms, check-in {F.lat('POST /api/reservations/{id}/checkin'):.1f} ms, check-out {F.lat('POST /api/reservations/{id}/checkout'):.1f} ms). "
            f"Login is slower, {F.lat('POST /api/auth/login'):.0f} ms, by design: the bcrypt work factor is the cost of protecting passwords. "
            f"Two endpoints are slow for a reason in the code: `GET /api/reservations` ({F.lat('GET /api/reservations'):.0f} ms mean) and `GET /api/admin/bookings` ({F.lat('GET /api/admin/bookings'):.0f} ms mean) build each row with two extra queries (the location name and the payment), "
            "so the cost grows with the number of rows, about 400 stored bookings in this run (an N+1 query pattern). Strategy Insights replays the stored history in "
            f"{F.lat('GET /api/admin/insights'):.0f} ms."),
          P(f"With 8 client threads sending {th['requests']} search requests the server handled {th['req_per_s']:.0f} requests per second, with a mean of {th['mean_ms']:.0f} ms, a 95th percentile of {th['p95_ms']:.0f} ms and a maximum of {th['max_ms']:.0f} ms. "
            f"Measured in-process on an in-memory database holding {mb['database'].split('=')[-1].strip()}, the admission decision `forecast_free` takes {fa['mean_ms']:.2f} ms on average (95th percentile {fa['p95_ms']:.2f} ms), "
            f"the nearest-alternate search over 49 other locations {na['mean_ms']:.1f} ms (95th percentile {na['p95_ms']:.1f} ms, about 0.4 ms per location because it runs one overlap query per location), and one haversine distance {hv['mean_ms'] * 1000:.1f} microseconds."),
          H3("7.7.1 Concurrency probe"),
          P(f"Admission counts the overlapping bookings and then inserts the new one, in two separate steps without a lock. To see whether that matters, the probe created a location with capacity 2 and buffer 1, so exactly one bay could be booked, "
            f"and sent {race['simultaneous_requests_per_trial']} reservation requests for it at the same instant from {race['simultaneous_requests_per_trial']} different drivers, ten times. "
            f"In {race['trials'] - race['trials_with_overbooking']} trials exactly one request was accepted and the rest received 409. In **{race['trials_with_overbooking']} of {race['trials']} trials two requests were accepted** (the most seen was {race['max_accepted_in_a_trial']}), "
            "so the last bay was sold twice. The objective of preventing double bookings is therefore met for requests that arrive one after another, and not under simultaneous requests. "
            "The window is small, since the check and the insert are a few milliseconds apart, but it is real. A database-level fix (a transaction that locks the location row, or a unique allocation record per bay) was not implemented."),
          FIG(F.fig("f09_race_probe.png"), "Number of reservations accepted in each of the ten trials; one bookable bay, twenty simultaneous requests.", 4.6)]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance and the browser walk-through"),
          P("**No user study was run.** Nobody other than the project team used the application under observation, so there are no task times, error counts or satisfaction scores, and no claim about usability is made from them. "
            "What was done instead is a scripted walk of the console that a real user would follow."),
          P("`scripts/capture_docs_screens.py` starts from a freshly seeded database and drives the React console at 1440 by 900 pixels in Chrome. As a driver it searches a window in which a one-bay location is full, searches a later window, opens the reservation dialog, "
            "reserves, opens My bookings, checks in and checks out through the buttons, and opens the Trust Score page. A second driver books the one-bay location for a later window while it is occupied, signs in, checks in, and is moved to the nearest alternate. "
            "As the administrator the script opens the overview, locations, Strategy Insights, all bookings and users pages. It also opens the search page at 390 pixels wide and the API documentation page. "
            "It saves 24 screenshots that are used in Chapter 8 and Appendix C. Every action in the walk succeeded on the first run of the final script; the earlier run showed that the first Check in button on the page belonged to a booking two days ahead rather than the one meant, "
            "so the script was changed to select the button by booking number and the database was reset before the final capture.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing done"),
          B("**The data are synthetic.** Every test and the Strategy Insights screens use the demo history generated by `app/seed.py`. No real parking lot, driver or payment contributed to any result.",
            "**The experiments are simulations.** The buffer comparison of Chapter 8 ran in a purpose-built simulator. It uses the engine's rules, verified decision for decision, but its driver behaviour (arrival times, gaps, a fixed one-hour overstay) is assumed.",
            "**Concurrency was probed only on admission.** Other races, such as two check-ins at the same moment, were not tested.",
            "**Load was small.** The heaviest test used 8 client threads on the same machine as the server; no test used many users, a network between client and server, or a database other than SQLite.",
            "**Stripe was tested only through its demo fallback.** No Stripe key was configured, so Checkout sessions, the webhook signature check and real refunds were not exercised.",
            "**One browser, one display.** The walk used Chrome at two viewport widths; other browsers, assistive technology and an accessibility audit tool were not used.",
            "**No hardware.** Barriers, sensors and cameras do not exist in the product, so the physical entry and exit are represented by the Check in and Check out buttons.",
            "**Timings come from a shared machine** and should be read as orders of magnitude."),
          P(f"In short: the engine rules and the API contract are well covered ({F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} smoke checks, all passing), the screens render real application data, and the probes found a small number of genuine weaknesses, "
            "which are listed rather than hidden. What the testing cannot say is how ParkSure behaves with real drivers, real money or real concurrency at scale.")]
    return b
