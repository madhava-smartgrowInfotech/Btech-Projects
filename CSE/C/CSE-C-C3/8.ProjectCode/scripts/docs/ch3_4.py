"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for ParkSure."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import N as C


def blocks():
    return chapter3() + chapter4()


def lat(prefix, key="mean_ms"):
    return F.lat(prefix, key)


# =====================================================================================================================
def chapter3():
    s_search, s_res, s_in, s_out = lat("GET /api/search"), lat("POST /api/reservations"), lat("POST /api/reservations/{id}/checkin"), lat("POST /api/reservations/{id}/checkout")
    s_login, s_list, s_adm = lat("POST /api/auth/login"), lat("GET /api/reservations"), lat("GET /api/admin/bookings")
    thr = F.LAT["endpoints"]["throughput_search_8_threads"]
    mb = F.MB
    adm_ms = mb["forecast_free (admission, 100 bookings at the location)"]["mean_ms"]
    alt_ms = mb["nearest_alternate over 49 other locations"]["mean_ms"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical Feasibility"),
        P("The question is whether the reservation rules, the payment flow, the web console and the analytics can be built with tools that the team and an ordinary desktop can support, and whether the result is fast and correct enough to use. "
          "Each part of the design was built and measured; the table lists what was used and the evidence that it works."),
        TAB("Technical feasibility: components and the evidence for each", ["Component", "Technology", "Evidence that it is feasible"],
            [["Web API", f"FastAPI {C('fastapi')}, pydantic validation", f"22 routes built; {F.PYTEST_API} API tests pass; search answers in {s_search:.1f} ms on average"],
             ["Database", f"SQLite through SQLAlchemy {C('sqla')}", "Five tables created from the models; the overlap query is indexed on user, location, start and end"],
             ["Availability engine", "Plain Python in app/engine.py", f"{F.PYTEST_ENGINE} unit tests; admission decision {adm_ms:.2f} ms; nearest alternate over 49 locations {alt_ms:.1f} ms"],
             ["Authentication", f"bcrypt {C('bcrypt')}, JSON Web Tokens {C('jwt')}", f"Login takes {s_login:.0f} ms because of the bcrypt cost factor 12; role guards tested for driver and admin"],
             ["Scheduler", "APScheduler inside the backend process", "Buffer-reset job every 30 minutes; reset rule covered by two unit tests"],
             ["Payments", f"Stripe Checkout in test mode {C('stripe')}, offline demo checkout", "Reserve returns a checkout link; demo confirmation and refund to credit tested; webhook inert without keys"],
             ["Front end", f"React 19 and Vite {C('react')}, three.js hero, Recharts", "Eleven page components, 24 screens captured from the running application, phone-width layout captured at 390 px"],
             ["Operator analytics", "Deterministic replay in scripts/compute_buffer_strategy_metrics.py", f"Four policies replayed over 60 days in {lat('GET /api/admin/insights'):.0f} ms; identical output on repeated calls (tested)"]],
            widths=[1.2, 2.0, 3.2], align=["l", "l", "l"], size=9.5),
        P(f"The measured response times show that the core booking path is cheap: reserving takes {s_res:.1f} ms on average, check-in {s_in:.1f} ms and check-out {s_out:.1f} ms, and eight client threads together obtain {thr['req_per_s']:.0f} search responses per second from one server process. "
          f"Two routes are slow for a stated reason: listing a driver's bookings takes {s_list:.0f} ms and the administrator's booking list {s_adm:.0f} ms, because every row issues two further queries. This is a defect of the implementation, not a limit of the technology, and it is listed as future work."),
        P("Two technical risks were identified and tested rather than assumed away. The first is concurrency: SQLite and the check-then-insert admission rule are not atomic, and a probe with 20 simultaneous requests for one bookable bay accepted two bookings in 1 of 10 trials. "
          "The second is the dependence on the clock: the buffer reset, the on-time rule and the suspension window all read the current time, which is why the simulator was parity-tested against the engine rather than patched into it. "
          "The first risk shows that the technology is feasible for a single-site pilot but needs a locking or transactional fix before it is relied on under load."),
        H2("3.2 Economic Feasibility"),
        P("The build needs no purchased software. Every library in the stack is available under a permissive open-source licence, the database is a single file, and the development machine is an ordinary desktop. "
          "Stripe is used in test mode, which needs no payment to run; in live mode Stripe charges transaction fees, which were not looked up for this report, and no revenue model is evaluated here."),
        TAB("Cost items", ["Item", "Cost for this project", "Note"],
            [["Software licences", "None", "FastAPI, SQLAlchemy, React, Vite, uvicorn, APScheduler and SQLite are open source"],
             ["Development hardware", "Existing desktop", "12th-generation Intel Core i5-12500, 15.7 GB RAM, Windows 11 Pro"],
             ["Database server", "None", "SQLite file; replaceable by another SQLAlchemy database through one setting (PARKSURE_DB)"],
             ["Payment gateway", "None in test mode", "Live-mode fees not evaluated"],
             ["Hosting", "Not evaluated", "One process serves the measured load; no hosting plan or price was studied"],
             ["Gate hardware and sensors", "Out of scope", "Entry and exit are software actions (check-in and check-out buttons)"]],
            widths=[1.8, 1.7, 2.9], align=["l", "l", "l"], size=10),
        P(f"For an operator, the economic argument is the one the system measures about itself: a platform that refuses a reservation in advance instead of failing a driver at the gate, records every payment, and lets the operator replay booking history to choose a buffer. "
          f"On the seeded history the replay shows the trade-off in numbers: {F.SEED['insights_60d']['totals']['fixed_0']['declined']} declined and {F.SEED['insights_60d']['totals']['fixed_0']['unable_to_park']} unable-to-park requests with no buffer, against "
          f"{F.SEED['insights_60d']['totals']['fixed_3']['declined']} and {F.SEED['insights_60d']['totals']['fixed_3']['unable_to_park']} with a fixed buffer of 3. These figures come from synthetic demo data and show the mechanism, not a saving."),
        H2("3.3 Operational Feasibility"),
        P("Drivers need only a browser: they register, search a window, reserve, pay, and press Check in and Check out. The console shows the reason whenever a request is declined or a driver is moved, and the Trust Score page explains the fee multiplier, so no training is needed to understand the rules. "
          "Administrators work in five screens, and their routine tasks are adding or editing a location, resetting buffers, reading bookings and users, and recomputing Strategy Insights."),
        P("Running the system takes little effort. run.bat creates the virtual environment, installs the Python and Node dependencies and starts the backend on port 8403 and the front end on port 5403; a first start creates the database and seeds demo data. "
          "Before any real use an operator must set a private token secret (PARKSURE_JWT_SECRET), Stripe keys, and a backup routine for parksure.db, because the shipped defaults are for demonstration. "
          "The scheduler runs inside the backend process, so no separate job service is needed, and the cost is that the buffer reset stops when the backend stops."),
        H2("3.4 Schedule Feasibility"),
        P("The work followed the dependencies of the design. Calendar dates are left as the placeholder [DATES] because the batch file does not give them."),
        TAB("Project phases", ["Phase", "Work", "Output"],
            [["1", "Problem study, reading of the two base papers, requirements", "Abstract, introduction, survey, objectives (documents 2 to 6)"],
             ["2", "Data model and availability engine", "models.py, engine.py, config.py, seed.py"],
             ["3", "API, authentication, payments and scheduler", "22 routes, JWT roles, Stripe and demo checkout"],
             ["4", "React console", "Eleven page components in the V3 design kit"],
             ["5", "Testing, simulator and measurements", f"{F.PYTEST_PASSED} tests, parity check, experiments, latency and probes"],
             ["6", "Screenshots and documentation", "24 screens, 12 diagrams, nine result charts, eleven documents"]],
            widths=[0.7, 3.2, 2.5], align=["c", "l", "l"], size=10),
        P("The schedule was feasible because each phase depends only on the one before it and no step is computationally heavy. The slowest operations in the project are the 200-request latency runs and the 30-run simulator sweeps, which take seconds to minutes on the development desktop. "
          "The real schedule risk was in the details that tests exposed late, such as the buffer direction that differs from the base paper, which was found while writing the simulator."),
        H2("3.5 Advantages and Constraints"),
        TAB("Advantages and constraints of the project", ["Advantages", "Constraints"],
            [["Complete booking life cycle in one application", "Single process and SQLite: no horizontal scaling and no atomic admission under simultaneous requests"],
             ["Every decision is a short, readable rule with a stored reason", "No sensors or gate feed: physical occupancy is known only from check-ins"],
             ["Parity-tested simulator reproduces the engine's decisions exactly", "The simulator is not SUMO and its arrival parameters are assumptions"],
             [f"{F.PYTEST_PASSED} automated tests plus a 27-check smoke test", "Demo data are synthetic; Stripe runs in test mode only"],
             ["Operator can replay history under other buffer policies", "No vehicle profile and no downloadable receipt"],
             ["Runs on one ordinary desktop with one command", "Default token secret and an unauthenticated demo-confirm route must be fixed before real use"]],
            widths=[3.2, 3.2], align=["l", "l"], size=10),
    ]


# =====================================================================================================================
def chapter4():
    s_search, s_res, s_in = lat("GET /api/search"), lat("POST /api/reservations"), lat("POST /api/reservations/{id}/checkin")
    s_login, s_list, s_adm = lat("POST /api/auth/login"), lat("GET /api/reservations"), lat("GET /api/admin/bookings")
    thr = F.LAT["endpoints"]["throughput_search_8_threads"]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System"),
        P("In the situation the batch describes, a driver reaches a facility with no knowledge of its occupancy and no guarantee of a bay. Entry is first come, first served, payment is collected in cash at the gate, "
          "and the operator keeps occupancy in a manual register. Nothing connects the driver's intention to park with the operator's capacity until the car is at the barrier."),
        P(f"Digital reservation systems exist, as Chapter 2 shows: interval-scheduled bookings {C('doulamis')}, mobile and cross-platform services {C('safitri', 'somani')}, flexible times with dynamic prices {C('kotb')}. "
          f"The technical base paper identifies what most of them leave open: a booking does not protect the driver when the previous occupant overstays {C('cabri')}. "
          "In practice the existing system therefore means manual registers and cash at the gate for many operators, and reservations that can fail silently for the digital ones."),
        H2("4.2 Limitations of the Existing System"),
        B("**No live view.** Drivers cannot see which bays are free, and operators cannot see demand ahead of time.",
          "**No guarantee on arrival.** A reservation, where one exists, is honoured only if the earlier driver leaves on time. Without a buffer or an alternate, the driver finds the bay occupied.",
          "**No incentive for punctuality.** The cost of an overstay falls on the next driver, not on the one who overstayed.",
          "**Cash and manual records.** Collection at entry is slow, leaves no usable records and gives the operator nothing to analyse.",
          "**No way to tune capacity.** Without recorded bookings and refusals, an operator cannot test how many bays to hold back.",
          "**Search adds traffic.** The batch introduction records that circling for a space adds congestion, wasted fuel and avoidable emissions."),
        H2("4.3 Proposed System"),
        P("ParkSure replaces the register and the gate with a web platform. A driver searches a time window, sees how many bays can still be reserved at every location, and reserves one. "
          "The engine admits the request only if overlapping bookings plus the location's buffer are below capacity, quotes the fee from the hours, the hourly rate and the driver's trust multiplier, applies account credit, and creates a payment. "
          "On arrival the driver checks in. If the lot is physically full, the engine moves the driver to the one nearest other location that has forecast space, or marks the booking failed and credits the fee. "
          "At check-out an on-time departure grows the location's buffer and advances the driver's benefit streak; a late departure records a warning. Administrators manage locations and read bookings, users, revenue and the Strategy Insights replay."),
        TAB("Modules of the proposed system", ["Module", "File", "Responsibility"],
            [["Routes and scheduler", "app/main.py", "22 REST routes, buffer-reset job, static pages"],
             ["Availability engine", "app/engine.py", "Admission, buffer reset, haversine alternate, trust updates, suspension, fee quote"],
             ["Models and database", "app/models.py, app/database.py", "Five tables, SQLite session"],
             ["Authentication", "app/auth.py", "bcrypt hashing, token creation and decoding, driver and admin guards"],
             ["Payments", "app/stripe_pay.py", "Stripe Checkout session or demo link"],
             ["Seed data and insights", "app/seed.py, scripts/compute_buffer_strategy_metrics.py", "Demo history; deterministic replay of four buffer policies"],
             ["React console", "frontend/src/pages", "Landing, login, find parking, my bookings, trust score, five admin pages"]],
            widths=[1.5, 2.2, 2.7], align=["l", "l", "l"], size=9.5),
        P("The data the system keeps follow directly from these steps. A user row holds the role, the Trust Score, the benefit streak, the warning count, the account credit and any suspension time. A location row holds its coordinates, capacity, hourly price and current buffer. "
          "A reservation row holds the window, the status, the fee and the multiplier that was applied, the check-in and check-out times, the reason for a decline or failure, and a link to the booking it replaced when the driver was moved. "
          "A payment row holds the amount, the provider and the status, and a trust-event row records every benefit, warning, reward and penalty. Because the reason and the multiplier are stored with each booking, a later reader can see why a request was declined and how its fee was computed."),
        H2("4.4 Advantages of the Proposed System"),
        TAB("Advantages and the evidence for each", ["Advantage", "Evidence"],
            [["Live availability for any window", f"Search returns bookable bays per location in {s_search:.1f} ms on average"],
             ["Reservations are admitted only when a bay will be free", f"Admission rule k + b < c tested; simulator parity {F.PAR['total_cases']:,} decisions, {F.PAR['total_mismatches']} mismatches"],
             ["Arriving driver is not left stranded", "Alternate move and failed-and-credited paths tested (screen 15 shows the move)"],
             ["Punctuality is rewarded", "Fee multiplier 0.90 to 1.75 from the Trust Score; three on-time checkouts raise the score, two late ones lower it (unit tests)"],
             ["Digital payment record for every booking", "Payment row per reservation; refund to account credit on cancellation (tested)"],
             ["Operator can compare buffer policies on recorded history", f"Strategy Insights replay computed in {lat('GET /api/admin/insights'):.0f} ms; identical on repeated calls"],
             ["Reproducible evaluation", f"{F.PYTEST_PASSED} tests, scripts/run_experiments.py, scripts/measure_api.py, experiments/*/metrics.json"]],
            widths=[2.7, 3.7], align=["l", "l"], size=10),
        P("The advantages are claimed only where the project holds a measurement or a test for them. Where a benefit is a design intention without a measurement, such as less time spent searching for a bay, it is not listed, because the project did not measure journeys or search time."),
        H2("4.5 Functional Requirements"),
        TAB("Functional requirements and how each is met", ["ID", "Requirement", "Implemented by", "Verified by"],
            [["FR1", "A visitor can register with name, email and password", "POST /api/auth/register", "test_api: duplicate email, validation"],
             ["FR2", "A user can log in and obtain a session token", "POST /api/auth/login, GET /api/auth/me", "test_api: login, bad password, token required"],
             ["FR3", "Admin routes are refused to drivers", "admin_user guard in auth.py", "test_api: role guards"],
             ["FR4", "An admin can add, edit and delete locations", "POST, PUT, DELETE /api/locations", "test_api: location CRUD and validation"],
             ["FR5", "Anyone can search availability for a window of at most 30 days", "GET /api/search", "test_api: bookable count, validation"],
             ["FR6", "A driver can reserve; the request is declined when k + b >= c", "POST /api/reservations, engine.forecast_free", "test_engine: admission; test_api: 409"],
             ["FR7", "The fee is hours x rate x trust multiplier, minimum 0.25 h, offset by account credit", "engine.quote_fee", "test_engine: fee; test_api: credit"],
             ["FR8", "A booking has a payment, confirmed through Stripe or the demo checkout", "stripe_pay.py, payment routes", "test_api: demo payment, webhook inert"],
             ["FR9", "A driver can cancel a reserved booking and a paid fee returns as credit", "POST /api/reservations/{id}/cancel", "test_api: cancel and refund"],
             ["FR10", "A driver can check in; a full lot moves the driver to the nearest alternate or fails the booking and credits the fee", "checkin route, engine.nearest_alternate", "test_api: alternate and failed paths"],
             ["FR11", "A driver can check out; on time means by end + 10 minutes", "checkout route", "test_api: on-time and late"],
             ["FR12", "The buffer grows by one per on-time checkout (cap 5) and is reset daily", "checkout route, reset_buffers_if_due", "test_api, test_engine: reset"],
             ["FR13", "The Trust Score rises after 3 benefits, falls after 2 warnings, within 0 to 5", "engine.record_checkout_trust", "test_engine: trust"],
             ["FR14", "A driver with trust below 1.5 and a recent warning is refused and cooled down for 24 h", "engine.suspension_block", "test_engine, test_api: suspension"],
             ["FR15", "A driver can view the score, streak, multiplier and event history", "GET /api/trust", "Screen 13"],
             ["FR16", "An admin can view totals, all bookings and all users", "GET /api/admin/overview, bookings, users", "test_api: admin listings"],
             ["FR17", "An admin can recompute Strategy Insights over a chosen window", "GET /api/admin/insights", "test_api: four strategies, deterministic"],
             ["FR18", "An admin can reset every buffer to its initial value", "POST /api/admin/reset-buffers", "test_api: reset"]],
            widths=[0.5, 2.7, 1.8, 1.4], align=["c", "l", "l", "l"], size=8.5),
        P("Each requirement below is traced to the route, module or test that meets it. The tests named are in tests/test_engine.py and tests/test_api.py. Requirements FR1 to FR18 were all exercised by at least one automated test or, for the trust page, by a captured screen."),
        H2("4.6 Non-Functional Requirements"),
        TAB("Non-functional requirements, measured values and status", ["ID", "Category", "Requirement", "Measured or observed", "Status"],
            [["NFR1", "Performance", "Core booking calls answer well within a second", f"Search {s_search:.1f} ms, reserve {s_res:.1f} ms, check-in {s_in:.1f} ms (means of 200 calls); 8 threads: {thr['req_per_s']:.0f} searches per second", "Met"],
             ["NFR2", "Performance", "List routes remain usable as bookings accumulate", f"Own bookings {s_list:.0f} ms, admin bookings {s_adm:.0f} ms with about 400 rows (two extra queries per row)", "Partly met"],
             ["NFR3", "Security", "Passwords hashed, routes guarded by role, input validated", f"bcrypt cost 12 ({s_login:.0f} ms login); role guards tested; injection payloads answered 422", "Met"],
             ["NFR4", "Security", "No unauthenticated state change, no default secrets", "Demo-confirm route marks a booking paid without login; forged token with the default secret accepted; no login rate limit", "Not met"],
             ["NFR5", "Correctness", "Never admit more than the bookable bays", "Sequentially correct (tests); 1 of 10 concurrent trials accepted 2 bookings for 1 bay", "Partly met"],
             ["NFR6", "Reliability", "Decisions reproducible and explainable", "Every declined or failed booking stores its reason; Strategy Insights identical on repeated calls", "Met"],
             ["NFR7", "Usability", "Clear states, light and dark theme, small screens", "24 screens; toasts state the reason for a decline or move; phone-width layout captured at 390 px (screen 23)", "Met, no user study"],
             ["NFR8", "Portability", "Start with one command on a clean machine", "run.bat installs and starts both servers; Docker image runs the backend only", "Met"],
             ["NFR9", "Maintainability", "Small, tested code base", f"Backend 977 lines in 10 files; {F.PYTEST_PASSED} tests", "Met"],
             ["NFR10", "Scalability", "Grow beyond one site", "Single process and SQLite; not measured beyond 8 client threads", "Not evaluated"]],
            widths=[0.55, 0.85, 1.5, 2.6, 0.9], align=["c", "l", "l", "l", "l"], size=8.5),
        P("The status column is deliberately blunt. One requirement is not met, one was not evaluated and two are met only in part; the first and the partly met ones correspond to defects found by the project's own probes and listed in Chapter 7. "
          "A requirement is marked Met only when a measurement or a test supports it, and no requirement is marked Met on the strength of the design alone."),
        H2("4.7 Hardware Requirements"),
        P("The system was developed and measured on one desktop. The minimum configuration was not tested on smaller machines, so the table gives the measured configuration and does not claim a lower bound."),
        TAB("Hardware used for development and measurement", ["Item", "Configuration"],
            [["Processor", "12th Gen Intel Core i5-12500, 6 cores, 12 threads"],
             ["Memory", "15.7 GB"],
             ["Storage", "Local disk; the database is a single file, parksure.db"],
             ["Display for screenshots", "1440 x 900 viewport; 390 x 844 for the phone-width screen"],
             ["Operating system", "Windows 11 Pro (build 10.0.26300)"]],
            widths=[1.8, 4.6], align=["l", "l"], size=10),
        H2("4.8 Software Requirements"),
        TAB("Software used", ["Layer", "Software and version"],
            [["Language and runtime", "Python 3.14.7 in the project virtual environment (the code targets Python 3.11 or newer); Node.js 24.19.0 for the front end"],
             ["Back end", "FastAPI 0.141.1, uvicorn 0.52.4, SQLAlchemy 2.0.52, pydantic 2.13.5, APScheduler 3.11.3"],
             ["Security and payments", "bcrypt 5.0.0, python-jose 3.5.0, Stripe SDK 15.6.1 (test mode)"],
             ["Front end", "React 19, Vite 8, react-router 7, three.js, framer-motion, GSAP, Recharts, lucide-react"],
             ["Database", "SQLite file parksure.db (replaceable through PARKSURE_DB)"],
             ["Testing and measurement", "pytest, requests, matplotlib, NumPy; Playwright with Google Chrome for the screenshots"],
             ["Browser", "Any current browser; Chrome was used for the captures"]],
            widths=[1.8, 4.6], align=["l", "l"], size=10),
        H2("4.9 User Roles and System Constraints"),
        TAB("User roles", ["Role", "Can do", "Cannot do"],
            [["Visitor (not logged in)", "See the landing page, the list of locations and search availability; register or log in", "Reserve, pay, check in or out, see any booking"],
             ["Driver", "Everything a visitor can; reserve, pay, cancel, check in and out, see own bookings and Trust Score", "Open admin screens or other users' bookings (answered 404)"],
             ["Administrator", "Everything a driver can; add, edit and delete locations, reset buffers, see overview, all bookings, all users and Strategy Insights", "Nothing is withheld; the first account created on an empty database becomes administrator"]],
            widths=[1.4, 3.1, 1.9], align=["l", "l", "l"], size=9.5),
        P("The constraints below are enforced by the schemas and the routes. Most of them are limits of this implementation, not requirements of parking."),
        B("A reservation window is at most 30 days long and must end after it starts; windows in the past are not rejected.",
          "A name has 2 to 120 characters, a password 6 to 128; a location has capacity 1 to 5,000, an hourly price from 0.50 to 100 and a buffer from 0 to 20.",
          "The billed time is at least 0.25 hours; fees are in US dollars; times are stored in UTC.",
          "Only a reserved booking can be cancelled, only a reserved booking can be checked in, and only an active booking can be checked out.",
          "A check-out is on time up to ten minutes after the end of the window.",
          "A driver is moved to at most one alternate location, and the alternate booking is created active without a second physical check.",
          "A session token lasts 12 hours and is signed with a secret that must be changed from the default before real use.",
          "One backend process serves all requests; the scheduler runs inside it."),
    ]
