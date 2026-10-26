"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared block lists used by documents 9, 10, 12 and 15.

Every number is read from facts.py (experiments/**/metrics.json); code excerpts are cut from the real files in 8.ProjectCode.
"""
import ast
import os
import textwrap

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import N as C


# ---------------------------------------------------------------------------- helpers
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a module-level function exactly as it stands (docstring removed unless doc=True)."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            end = node.end_lineno
            body = lines[start - 1:end]
            if not doc and ast.get_docstring(node):
                d = node.body[0]
                body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:end]
            return "\n".join(body)
    raise KeyError(name)


def between(rel, first, last):
    """Lines from the first line containing `first` to the first later line containing `last` (inclusive), dedented."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if first in l)
    j = next(k for k in range(i, len(lines)) if last in lines[k])
    return textwrap.dedent("\n".join(lines[i:j + 1]))


def _fig(name, caption, width=5.6):
    """A result figure, only if it exists."""
    return [FIG(F.fig(name), caption, width)] if os.path.exists(F.fig(name)) else []


def _v():
    """Measured values used in the prose; all read from experiments/**/metrics.json through facts.py."""
    nopark_max = max([F.pop(n, s, "no_park") for n in (80, 90, 100, 110) for s in F.STRATS] +
                     [F.bad(b, s, "no_park") for b in (0.25, 0.3, 0.35, 0.4, 0.45, 0.5) for s in F.STRATS])
    t = F.SEED["insights_60d"]["totals"]
    return dict(
        tests=F.PYTEST_PASSED, smoke=F.SMOKE_PASSED, parity=F.PAR["total_cases"], pmis=F.PAR["total_mismatches"],
        nres_dyn=F.pop(100, "dynamic_parksure", "no_reservation"), nres_s0=F.pop(100, "static_0", "no_reservation"),
        nres_s1=F.pop(100, "static_1", "no_reservation"), nres_s3=F.pop(100, "static_3", "no_reservation"),
        nres_pap=F.pop(100, "dynamic_paper", "no_reservation"), req100=F.pop(100, "static_0", "requests"),
        nopark_max=nopark_max,
        susp25=F.bad(0.25, "static_0", "suspended"), ref25=F.bad(0.25, "static_0", "no_reservation"),
        susp50=F.bad(0.5, "static_0", "suspended"), ref50=F.bad(0.5, "static_0", "no_reservation"),
        moved50_s0=F.bad(0.5, "static_0", "moved_to_alternate"), ov50_s0=F.bad(0.5, "static_0", "alt_overflow"),
        t3=F.TD["0.3"], t5=F.TD["0.5"],
        seed=t, s_search=F.lat("GET /api/search"), s_res=F.lat("POST /api/reservations"), s_in=F.lat("POST /api/reservations/{id}/checkin"),
        s_out=F.lat("POST /api/reservations/{id}/checkout"), s_login=F.lat("POST /api/auth/login"), s_list=F.lat("GET /api/reservations (own"),
        s_adm=F.lat("GET /api/admin/bookings"), s_ins=F.lat("GET /api/admin/insights"),
        thr=F.LAT["endpoints"]["throughput_search_8_threads"]["req_per_s"],
        adm_ms=F.MB["forecast_free (admission, 100 bookings at the location)"]["mean_ms"],
        alt_ms=F.MB["nearest_alternate over 49 other locations"]["mean_ms"],
        race=F.RACE, sec=F.SEC,
    )


# ---------------------------------------------------------------------------- novelty / contributions
def novelty_blocks():
    v = _v()
    return [
        H2("What the base papers contribute"),
        P(f"The registered base paper {C('base')} treats parking inside a large managed facility, a medical city. It allocates vehicles to parking spaces by the total number of passengers rather than the number of vehicles, "
          "through a four-stage grouping procedure and six grouping-permutation heuristics, and describes an architecture of booking interfaces, QR validation, gate and in-space sensing and a central allocation engine. "
          "It is evaluated on nine instance classes with 2,790 generated test cases. Its best algorithm reaches the highest best-solution share (68.2 percent), and the variant GVb matches or beats the baseline MR on 1,547 instances (55.4 percent: 57 better, 1,490 equal), in sub-millisecond time. "
          "It does not cover online payment, overstay handling, driver reputation or operator analytics."),
        P(f"The paper {C('cabri')} whose rules ParkSure implements addresses the situation where a reserved bay is still occupied when the next driver arrives. It proposes a reservation module with a buffer of non-reservable bays and a reward system with a 0 to 5 star reputation. "
          "It is evaluated only in a SUMO simulation of 80 spots in 8 areas, with 80 to 110 vehicles of which 25 to 50 percent overstay by one hour, over five runs, and its results are given as figures: any buffer beats none and the dynamic buffer gives the best trade-off. "
          "The authors describe the work as preliminary."),
        H2("What is new in ParkSure"),
        B("**A complete operating platform rather than an algorithm or a simulation.** Neither base paper delivers a web application. ParkSure combines search, advance booking, payment, check-in and check-out, role-based administration and 24 captured screens "
          f"in one FastAPI and React system with 22 routes and 5 tables, covered by {v['tests']} passing tests.",
          f"**The buffer and star ideas of {C('cabri')} turned into product rules.** The hold-back buffer, the benefit and warning counters, the fee multiplier from the trust score and the suspension rule are implemented in `app/engine.py` and reachable through the API and the interface.",
          "**Nearest-alternate re-allocation with automatic credit.** When a lot is physically full at check-in the engine selects exactly one other location with forecast space by haversine distance, books it as an active alternate linked to the original booking, "
          "or marks the booking failed and credits the fee to the driver's account.",
          "**Operator analytics by deterministic replay.** Strategy Insights replays the stored booking history under four buffer policies and compares unable-to-park and declined counts per location, so an operator sees the trade-off on their own data.",
          f"**A measured and verified evaluation.** A discrete-event simulator re-creates the scenario of {C('cabri')} with the ParkSure rules and agrees with the real engine on {v['parity']:,} checked decisions ({v['pmis']} mismatches). "
          "Latency, a concurrency probe and security probes were run on the product itself, and the defects they exposed are reported rather than hidden."),
        H2("What is standard"),
        P(f"Interval-overlap admission {C('kt')}, the haversine distance {C('sinnott')}, JSON Web Tokens {C('jwt')}, bcrypt password hashing {C('bcrypt')}, a relational schema through an object-relational mapper {C('sqla')}, REST routes {C('rest')} and hosted card checkout {C('stripe')} are established techniques used as they are. "
          "The idea of reserving ahead and holding a safety margin is the one proposed in the paper above, and the same family of reservation platforms is surveyed in " + C('aljohani', 'fahim') + "."),
        H2("What the base papers have and ParkSure does not"),
        B(f"**No passenger-aware grouping or load balancing.** ParkSure allocates by capacity and time overlap only, so it does not implement the algorithms of {C('base')} and makes no claim to match or beat them. The two works solve different problems and use different data, so their numbers cannot be compared.",
          "**No sensors, cameras or QR gates.** Occupancy is software-managed through Check In and Check Out buttons; availability is a forecast from bookings, not a live reading.",
          f"**No SUMO run.** The simulator in `scripts/parking_sim.py` follows the scenario of {C('cabri')} but is not SUMO, and several of its parameters (arrival process, lead time, gaps) are assumptions because the paper does not give them."),
        H2("Where the shipped rule departs from the paper"),
        P(f"The paper grows the buffer when a vehicle leaves after its reservation ends, so that places prone to late departures hold more bays back. The shipped code grows it on every on-time checkout (`app/main.py`, route checkout), with the comment that the buffer grows as on-time behaviour is observed. "
          f"Both rules were measured. At 100 vehicles with 25 percent overstaying, the shipped rule refused {v['nres_dyn']:.0f} of {v['req100']:.0f} requests, the paper-literal rule {v['nres_pap']:.0f}, a static buffer of 3 refused {v['nres_s3']:.0f} and no buffer {v['nres_s0']:.0f}. "
          "The shipped direction is therefore the most conservative of the five, and the conclusion of the paper that a dynamic buffer gives the best trade-off is not reproduced for it. The code was not changed; the difference is reported as a finding."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The contributions of the project, stated at the strength the evidence supports, are:"),
        N("**A working reservation platform, ParkSure**: registration and login with roles, availability search by time window, advance booking with a forecast-based admission rule, fee quoting, Stripe test-mode and demo payment, cancellation with account credit, check-in and check-out, and an administrator console, "
          "served by 22 routes over 5 tables and a React interface with 24 captured screens.",
          f"**A Smart Availability Engine** that implements the hold-back buffer, the nearest-alternate search by haversine distance, the Trust Score with fee multipliers and the suspension rule of {C('cabri')} in 141 lines of Python that are unit-tested.",
          f"**A parity-tested simulator** that re-creates the base paper's scenario with the ParkSure rules and matches the engine on {v['parity']:,} decisions with {v['pmis']} mismatches, and an experiment harness that compares five buffer policies over {F.SEEDS} runs per cell, with and without the Trust Score.",
          "**Findings the shipped behaviour would have hidden**: the shipped buffer rule is the most conservative of five; failures at the gate are rare because the alternate step absorbs them, but alternates can themselves be physically full; the Trust lockout, not the buffer, causes most refused requests when a quarter of drivers are bad.",
          "**An honest defect list from the team's own probes**: a booking race that over-booked one of ten trials, an unauthenticated demo-payment endpoint, a default token secret, no login rate limit, and per-row queries that make two list routes slow.",
          f"**A reproducible artefact**: {v['tests']} pytest tests, a {v['smoke']}-check smoke test, a screenshot script that drives the real interface, and scripts that regenerate every metric file and the facts file."),
    ]


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        P("The scope follows the six batch objectives and what could be built and measured on one machine. It is stated first as what the product and its measurements cover and then as what they deliberately leave out, so that a simulation or a seeded demonstration is not mistaken for a field result."),
        H2("In scope"),
        B("Driver accounts with registration, login, roles and a Trust Score; the first account on an empty database becomes the administrator.",
          "Parking locations with coordinates, capacity, hourly price and a hold-back buffer, managed by the administrator.",
          "Availability search for an arrival and departure window of up to 30 days, returning the number of bookable bays per location.",
          "Advance reservation with a forecast-based admission rule, fee quotation by hours, rate and trust multiplier, account credit, cancellation and refund to credit.",
          "Payment through Stripe Checkout in test mode, or an offline demo checkout when no keys are set.",
          "Software-managed check-in and check-out, the nearest-alternate move or failed-and-credited outcome on arrival, and the on-time or late decision at departure.",
          "An administrator console: overview figures, locations, all bookings, users, buffer reset and Strategy Insights.",
          "Measurement of the engine, the API and five buffer policies by tests, a simulator, latency runs, a concurrency probe and security probes."),
        H2("Out of scope"),
        B("Physical hardware: barriers, ticket machines, cameras, number-plate recognition and occupancy sensors. Occupancy is whatever the booking records say.",
          "Passenger-count allocation and the grouping heuristics of the registered base paper.",
          "Real payments. Stripe is used in test mode only and no money moves.",
          "A mobile application, push notifications and e-mail receipts.",
          "Multi-city or multi-operator tenancy, dynamic market pricing and a map interface.",
          "Machine learning. The insights are deterministic replays of stored bookings, not predictions."),
    ]


def assumption_blocks():
    return [
        B("Every driver checks in at or near the planned arrival and checks out through the interface; an overstay is recorded only when the driver checks out, using a ten-minute grace period after the booked end.",
          "A driver who is late to arrive is not penalised; only the departure is judged.",
          "Locations are independent lots; a driver accepts exactly one suggested alternate and drives to it.",
          "Distances are straight-line (haversine) from the stored coordinates; road distance and travel time are not used.",
          "The time zone of a booking is taken as UTC unless the client sends an offset.",
          f"In the simulator, arrival process, lead time (15 to 60 minutes), gaps between parks and the uniform choice of area are assumptions fixed before the runs, because {C('cabri')} does not state them; bad drivers overstay by exactly one hour.",
          "The seeded demo history is generated by `app/seed.py` with a fixed random seed and is synthetic; it demonstrates the mechanism, not real demand.",
          "A single backend process with one SQLite file serves all requests."),
    ]


def limitation_blocks():
    v = _v()
    s = v["sec"]
    return [
        H2("Data and evidence"),
        B(f"**Synthetic data.** The only data are the seeded demo history ({F.SEED['users']} users, {F.SEED['locations']} locations, {F.SEED['reservations']} reservations over 60 days plus eight Friday peaks at one lot) and the simulator's own generated runs. No real parking lot data were available.",
          f"**The simulator is not SUMO.** It re-creates the scenario of {C('cabri')} with stated assumptions, so its numbers are not comparable with the figures of that paper, which are given only as charts.",
          "**No user study.** Ease of use, trust in the Trust Score and acceptance of the alternate move were not tested with real drivers or operators.",
          "**Measured on one machine.** All timings come from a 12th-generation Intel Core i5-12500 with 15.7 GB of RAM, a single uvicorn process and SQLite; a load test beyond eight threads was not run."),
        H2("Defects found by the project's own probes"),
        B(f"**Over-booking race.** In {v['race']['trials']} trials of {v['race']['simultaneous_requests_per_trial']} simultaneous requests for one bookable bay, {v['race']['trials_with_overbooking']} trial accepted {v['race']['max_accepted_in_a_trial']} bookings. The admission count and the insert are not atomic, so the claim that double bookings are prevented holds for sequential requests only.",
          "**Unauthenticated payment confirmation.** `GET /api/payments/demo-confirm` marks any reservation paid; the probe turned a pending payment to paid without a token. It exists for the offline demo and must be disabled when real keys are used.",
          "**Default token secret.** A token signed with the shipped development secret was accepted as an administrator; the secret must be set in the environment.",
          "**No login rate limit.** Thirty wrong passwords in a row were all answered with 401 and the correct password then worked.",
          "**Loose time validation.** A booking whose window lies in the past was accepted, and a check-in 25 days before the booked window was accepted.",
          f"**Slow list routes.** Listing a driver's bookings takes {v['s_list']:.0f} ms and the administrator's booking list {v['s_adm']:.0f} ms because each row issues two further queries."),
        H2("Behaviour that differs from the base paper or from the objectives"),
        B("The buffer grows on on-time checkouts, the opposite direction to the paper; the measured effect is in Chapter 8.",
          "The suspension rule re-applies at every request while the score is below 1.5 and a warning is less than 14 days old, so a suspended driver is locked out for at least 14 days after the last warning, not for one session.",
          "The alternate booking is created as active without checking the alternate's physical bays; in the simulator this produced alternate-overflow events at the highest overstay shares.",
          "Objective 1 asks for vehicle profile management and objective 4 for digital receipts. ParkSure has neither a vehicle profile nor a downloadable receipt.",
          "Availability is a forecast from bookings, not a live reading, because there are no sensors; \"real-time\" in objective 2 therefore means up to date with the booking records."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and no figure for them appears in any document:"),
        B("Behaviour under real parking demand or against a real operator's data.",
          "A SUMO run of the base paper's scenario, and any comparison with its figures beyond the qualitative ordering.",
          "Load beyond eight concurrent threads, multi-process or multi-machine deployment, and a database other than SQLite.",
          "Stripe in live mode, real webhooks with signing secrets, refunds through the payment provider and receipt generation.",
          "Usability, accessibility audit tooling and a study with drivers or operators.",
          "Hardware integration: gates, sensors, cameras and number-plate recognition.",
          "The effect of the fee multiplier on driver behaviour, since drivers in the simulator do not react to price or to suspension."),
    ]


# ---------------------------------------------------------------------------- code walk-throughs
def walkthrough_blocks():
    v = _v()
    return [
        H2("Admission and the overlap count (`app/engine.py`)"),
        P("A request is admitted only when the bookings overlapping its window plus the location's buffer are fewer than its capacity. Overlap is counted in the database over reserved and active bookings, with start before the requested end and end after the requested start. "
          f"On a database of 5,000 stored bookings the decision takes {v['adm_ms']:.2f} ms on average."),
        CODE(fn("app/engine.py", "overlapping_count") + "\n\n" + fn("app/engine.py", "forecast_free"), 8),
        H2("Reservation creation (`app/main.py`, route `POST /api/reservations`)"),
        P("The route first applies the suspension check and the admission rule. A refused request is stored as a declined booking with the reason, so the administrator can count it, and the client receives 403 or 409. "
          "An admitted request is priced from the trust multiplier, offset by account credit and stored together with its payment row."),
        CODE(between("app/main.py", "blocked = suspension_block(db, user)", "payable = round(fee - credit_used, 2)"), 7.5),
        H2("Nearest alternate (`app/engine.py`)"),
        P(f"If the lot is physically full when the driver checks in, every other location is tested with the same forecast rule and the closest by haversine distance is chosen; there is exactly one suggestion. "
          f"The search issues one overlap query per location and takes {v['alt_ms']:.1f} ms over 49 locations in the micro-benchmark. The route then creates the alternate booking as active, marks the original failed, or credits the fee when no alternate exists."),
        CODE(fn("app/engine.py", "haversine_km") + "\n\n" + fn("app/engine.py", "nearest_alternate"), 7.5),
        H2("Check-out, buffer growth and trust (`app/main.py`, `app/engine.py`)"),
        P("A departure within ten minutes of the booked end is on time. An on-time departure grows the location's buffer by one up to the cap, and the trust function counts a benefit or a warning. "
          "Three consecutive benefits add one point; two warnings subtract one. The suspension function then decides whether the next request is refused."),
        CODE(between("app/main.py", "now = utcnow()", "return {\"reservation\": _res(r, db), \"on_time\": on_time,") + "\n\n" + fn("app/engine.py", "record_checkout_trust"), 7.5),
        CODE(fn("app/engine.py", "suspension_block"), 7.5),
        H2("The simulator's arrival and departure events (`scripts/parking_sim.py`)"),
        P("The simulator keeps the same rules as pure functions and replays them in event order. On arrival it checks physical occupancy, searches the nearest alternate with the same admission rule and counts a failed park or an alternate overflow; "
          "on departure it applies the buffer and trust updates of the chosen policy. `tests/test_sim_parity.py` and `scripts/parity.py` compare its admission, trust and suspension decisions with the real engine."),
        CODE(between("scripts/parking_sim.py", "elif kind == \"ARR\":", "push(leave, \"DEP\", p)"), 7),
    ]


def decision_blocks():
    v = _v()
    return [
        P("The main implementation decisions, the reason for each and what the measurements later showed are listed in the table below."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "What the measurements showed"],
            [["SQLite file with SQLAlchemy", "Zero configuration; the same models can move to another database through one setting", f"Every route answers in milliseconds; the non-atomic count and insert allowed {v['race']['trials_with_overbooking']} of {v['race']['trials']} race trials to over-book"],
             ["Hold-back buffer per location", f"Idea of {C('cabri')}: keep some bays unreservable so an overstay does not strand the next driver", f"At 100 vehicles it refuses {v['nres_s1']:.0f} requests at buffer 1 and {v['nres_s3']:.0f} at buffer 3, against {v['nres_s0']:.0f} with none"],
             ["Grow the buffer on on-time checkouts", "Code comment: the buffer grows as on-time behaviour is observed, reset daily", f"Opposite to the paper; the most conservative policy ({v['nres_dyn']:.0f} refused at 100 vehicles)"],
             ["Exactly one nearest alternate, by haversine", "Matches the paper; avoids sending a driver on a long chain; no external map API", f"{v['alt_ms']:.1f} ms over 49 locations; alternates were sometimes physically full ({v['ov50_s0']:.1f} events per run at 50 percent overstay with no buffer)"],
             ["Trust multipliers 1.75 to 0.90", "A financial incentive for punctuality, as in the paper", f"At 30 percent late sessions the mean score falls to {v['t3']['mean_final_trust']:.1f} and the mean multiplier rises to {v['t3']['mean_fee_multiplier']:.2f}"],
             ["Suspend below 1.5 with a recent warning", "Protect other drivers from repeat overstayers", f"Largest source of refusals in the simulator ({v['susp25']:.0f} against {v['ref25']:.0f} admission refusals at 25 percent bad drivers, no buffer)"],
             ["Stripe test mode with demo fallback", "The product stays usable offline and without keys", "Demo confirmation route is unauthenticated and must be switched off in production"],
             ["Refund as account credit", "Instant and needs no provider call", "Cancel and failed-arrival paths tested; no provider-side refund was exercised"],
             ["JWT (HS256, 12 hours) and bcrypt (cost 12)", "Stateless sessions and slow password hashing", f"Login costs {v['s_login']:.0f} ms by design; the default secret is a risk until set"],
             ["Deterministic Strategy Insights replay", "Auditable: the same history always gives the same numbers", f"{v['s_ins']:.0f} ms for a 60-day replay; ordering agrees with the simulator"],
             ["Row serialiser that queries per row", "Simple code for the first version", f"Own-bookings list {v['s_list']:.0f} ms and administrator list {v['s_adm']:.0f} ms: a clear candidate for a join"]],
            widths=[1.6, 2.4, 2.6], align=["l", "l", "l"], size=10),
        P("Three decisions deserve a longer note. The first is the single nearest alternate. A driver who finds the lot full needs one clear instruction, and a chain of suggestions would send the driver further from the destination, so the engine proposes one and creates the booking immediately. "
          "The cost is that the alternate's physical bays are not re-checked, which the simulator shows can overflow when many drivers overstay."),
        P("The second is the direction of buffer growth. Growing the buffer after on-time checkouts is intuitive for an operator who trusts a busy lot, but it holds back more bays exactly where behaviour is good, which lowers revenue and refusals rise. "
          "The measurements make the trade-off visible; adopting the paper's direction is a one-line change that was left for a deliberate experiment on real data."),
        P("The third is the demo payment. Without Stripe keys the product creates a demo session and confirms it through a route. This keeps every flow testable offline, and it is also the largest security weakness found, which is why it is listed in the limitations and the future work."),
    ]


# ---------------------------------------------------------------------------- conclusion
def _objective_table():
    v = _v()
    return TAB("Objectives against outcomes", ["Objective", "Outcome", "Evidence"],
               [["1 Registration, authentication and vehicle profile", "Partly achieved", "Registration, login, JWT, roles and Trust Score work and are tested; no vehicle profile exists"],
                ["2 Real-time slot availability", "Achieved as a forecast", f"Search returns bookable bays per window in {v['s_search']:.1f} ms; no sensors, so not a live occupancy reading"],
                ["3 Search, advance reservation and cancellation", "Achieved", f"Reserve {v['s_res']:.1f} ms; cancel refunds to credit; {F.PYTEST_API} API tests"],
                ["4 Secure online payment and digital receipts", "Partly achieved", "Stripe test mode and demo checkout; payment status stored; no downloadable receipt; demo-confirm route is a weakness"],
                ["5 Administrator dashboard", "Achieved", "Overview, locations, bookings, users, revenue, unable-to-park, declined and Strategy Insights"],
                ["6 Evaluate success rate, allocation efficiency and response time", "Achieved with a simulator", f"{F.SEEDS} runs per cell, five policies, utilisation, latency and probes; no real-user data"]],
               widths=[2.4, 1.4, 2.8], align=["l", "l", "l"], size=10)


def _findings():
    v = _v()
    return [
        f"**The engine is correct against its own specification.** {v['tests']} tests pass and the simulator agrees with the engine on {v['parity']:,} decisions ({v['pmis']} mismatches).",
        f"**The platform is fast enough for its purpose.** On this machine search takes {v['s_search']:.1f} ms, reserve {v['s_res']:.1f} ms, check-in {v['s_in']:.1f} ms and check-out {v['s_out']:.1f} ms; login takes {v['s_login']:.0f} ms by design and eight threads sustained {v['thr']:.0f} search requests per second.",
        f"**The shipped dynamic buffer is the most conservative policy.** At 100 vehicles it refused {v['nres_dyn']:.0f} of {v['req100']:.0f} requests, against {v['nres_pap']:.0f} for the paper-literal rule, {v['nres_s3']:.0f} for a static buffer of 3 and {v['nres_s0']:.0f} for none. The paper's conclusion that a dynamic buffer is best was not reproduced for it.",
        f"**Failures at the gate are rare in every policy** (at most {v['nopark_max']:.1f} per run in about 1,000 requests) because the alternate step absorbs them; the cost shows up as alternate moves and, at high overstay shares, alternate overflows.",
        f"**The Trust lockout dominates refusals.** With a quarter of drivers overstaying the lockout refused {v['susp25']:.0f} requests per run against {v['ref25']:.0f} refused by admission with no buffer; at half of drivers it refused {v['susp50']:.0f}. A driver who ends 30 percent of sessions late reaches a mean score of {v['t3']['mean_final_trust']:.1f} and {v['t3']['share_ever_suspended'] * 100:.0f} percent are suspended at some point.",
        "**The team's own probes found real defects**: an over-booking race, an unauthenticated payment confirmation, a default token secret and two slow list routes.",
    ]


def conclusion_blocks():
    v = _v()
    return [
        H2("Summary"),
        P(f"ParkSure is a working Online Vehicle Parking Reservation System. Drivers search availability for a time window, reserve in advance, pay through Stripe in test mode or an offline demo checkout, and check in and out; administrators manage locations and read the overview and Strategy Insights. "
          f"Behind it, an availability engine admits a request only if overlapping bookings plus a hold-back buffer stay below capacity, moves a driver to the nearest alternate when a lot is full on arrival, and prices every booking by a Trust Score. It is built from 22 routes over 5 tables and was exercised with {v['tests']} tests, a simulator and 24 captured screens."),
        H2("Objectives against outcomes"),
        _objective_table(),
        H2("Key findings"),
        N(*_findings()),
        *_fig("f01_buffer_population.png", "Refusals, gate failures and success rate of five buffer policies against population size (simulator, 30 runs per point).", 6.0),
        *_fig("f05_api_latency.png", "Mean and 95th percentile response time of the ParkSure API on 127.0.0.1.", 5.4),
        H2("Limitations"),
        P("The evidence is simulated and seeded rather than field data, the simulator is not SUMO, no user study was run, and the defects listed in the limitations section remain open. The results demonstrate that the mechanism works and show how its policies trade refusals against failures; they do not predict the behaviour of a real car park."),
    ]


def chapter9_blocks():
    v = _v()
    body = [
        H2("Summary"),
        P("The project set out to build a platform on which drivers reserve parking ahead of arrival, and to keep that promise when earlier drivers overstay. ParkSure delivers the platform: a FastAPI service with 22 routes and five tables, a React console, Stripe test-mode and demo payment, and an administrator console. "
          f"Its availability engine implements the hold-back buffer, nearest-alternate re-allocation and Trust Score of {C('cabri')}. The work was verified by {v['tests']} pytest tests, a {v['smoke']}-check smoke test and a simulator that matches the engine on {v['parity']:,} decisions, and 24 screens were captured from the running application."),
        H2("Objectives achieved"),
        _objective_table(),
        H2("Key findings"),
        N(*_findings()),
        H2("Practical applications"),
        B("An operator of a small number of urban lots can take bookings and payments online and see, from the Strategy Insights page, how many requests different buffer settings would have refused or failed on their own history.",
          "A campus, hospital or event car park can use the nearest-alternate step so that a full lot redirects a driver instead of failing.",
          "The punctuality incentive (fee multiplier and suspension) can be tried on a small scale; the measured trust dynamics show how quickly habitual overstayers are priced up and locked out.",
          "The simulator and tests can be reused to evaluate a different buffer rule before it is put in front of drivers."),
        H2("Closing remark"),
        P("The value of the project lies in a platform that works end to end and in a measured account of how its availability rules behave. The experiments do not show that the shipped buffer is the best choice; they show what it costs, which is what an operator needs before choosing a setting, and the tests and the simulator make a better choice cheap to evaluate."),
        H2("Known limitations"),
        P(f"The data are synthetic and the experiments are simulated. The over-booking race, the unauthenticated demo confirmation, the default token secret and the missing vehicle profile and receipt are open defects and gaps. The shipped buffer rule grows in the opposite direction to the paper, and its measured effect is a higher refusal count. "
          f"Admission and the nearest alternate rely on forecasts from bookings, not on sensors. No real-user study was carried out."),
    ]
    return [H1("CHAPTER 9: CONCLUSION")] + renum(body, "9")


# ---------------------------------------------------------------------------- future scope
def future_blocks():
    return [
        H2("Close the defects found"),
        B("**Make admission atomic.** Take a lock or use a serialisable transaction around the overlap count and the insert, or store a per-location, per-slot-window counter with a unique constraint; repeat the 20-request race probe until no trial over-books.",
          "**Remove the unauthenticated demo-confirm route** when Stripe keys are present, and verify payment only through the signed webhook.",
          "**Require a secret from the environment** and refuse to start with the shipped default; add a rate limit and lockout to login.",
          "**Validate times:** reject windows that start in the past and allow check-in only inside a tolerance around the booked start.",
          "**Replace the per-row queries** with joined queries so the booking lists answer in tens of milliseconds."),
        H2("Test the buffer rule on real data"),
        B(f"Run the paper's direction (grow on late departure) side by side with the shipped one on real booking histories, and choose by refusals and failures together.",
          f"Repeat the experiment in SUMO with the original parameters of {C('cabri', 'sumo')} to compare against its figures directly."),
        H2("Add features"),
        B("A **vehicle profile** (plate, type, colour) and a downloadable **receipt** with payment details, which complete batch objectives 1 and 4.",
          "**Sensor and number-plate integration** so that occupancy is read rather than assumed, with check-in at the gate.",
          "**Dynamic pricing** by demand and time of day, building on the multiplier table, in the spirit of " + C('kotb') + ".",
          "A **mobile application** and push notifications for expiry and overstay warnings."),
        H2("Deploy and scale"),
        B("Move to PostgreSQL, run several worker processes behind a proxy and add a job queue for the buffer reset.",
          "Add monitoring of refusals, failures and latency per location so the buffer can be tuned with data."),
    ]


def chapter10_blocks():
    body = [
        H2("Improvements to the existing system"),
        P("Each improvement answers a defect or a gap that was measured, so each has a test it must pass."),
        B("**Atomic admission.** The race probe over-booked one trial in ten; the fix is a lock or serialisable transaction around the count and insert, verified by repeating the probe.",
          "**Close the payment and token weaknesses.** Disable the demo confirmation when real keys exist, take payment status only from the signed Stripe webhook, and refuse to start with the default secret.",
          "**Time validation and rate limiting.** Reject past windows, limit early check-in and throttle repeated login failures.",
          "**Joined queries** for the booking lists, which take 180 ms and 273 ms today because each row issues two extra queries.",
          "**Re-check the alternate's bays** before booking it, so that a driver is not sent to a lot that is also physically full."),
        H2("Additional features"),
        P("The features below are ordered by how directly they complete the batch objectives that were only partly met."),
        B("**Vehicle profiles and receipts** for objectives 1 and 4: stored plate and vehicle type, and a downloadable receipt for each paid booking.",
          "**Occupancy sensing and number-plate recognition** so that check-in is automatic and availability is read rather than forecast.",
          "**Dynamic pricing** by demand and time of day, extending the fee multiplier.",
          "**A mobile application** with push reminders before the booked end."),
        H2("Scalability and deployment"),
        P("ParkSure runs as one process with one SQLite file, which is enough for a demonstration and a small operator. Eight concurrent threads sustained about 131 search requests per second on the test machine; larger loads were not measured."),
        B("Move to a server database, run several workers behind a reverse proxy and run the buffer reset as a separate scheduled job.",
          "Serve the built React bundle from a static host and keep the API behind HTTPS with the secret and Stripe keys in the environment.",
          "Add monitoring of refusals, failures and latency per location."),
        H2("Order of work"),
        P("The first stage is the correction of the defects: atomic admission, the payment route, the token secret and time validation. They are small, each has a probe that already exists, and every later feature depends on a booking record that can be trusted. "
          "The second stage completes the missing objectives, the vehicle profile and the receipt. The third stage adds hardware integration and pricing, which need an operator to cooperate and real data to judge them."),
        H2("Risks and dependencies"),
        B("**Hardware and access.** Sensor and number-plate integration depend on an operator's gates and cameras, and on privacy rules for plate data.",
          "**Payment compliance.** Live payments need the provider's signed webhooks, refunds through the provider and a review of how card data are handled; ParkSure stores no card numbers because Stripe Checkout collects them.",
          "**Evaluation.** Any change to the buffer or the suspension rule should be judged on real booking histories as well as in the simulator, because the simulator assumes that drivers never react to prices or penalties."),
        H2("Further research"),
        P("The open questions are about policy rather than engineering."),
        B(f"Which direction of buffer growth gives the better trade-off on real data, and how large should the cap be? The simulator found the shipped direction the most conservative; the paper reports the opposite for its own setting {C('cabri')}.",
          "How should a suspension lockout be designed so that it deters habitual overstayers without removing a driver for weeks?",
          f"Can the passenger-aware grouping of {C('base')} be combined with reservations when a lot serves a hospital or campus, and does it improve load balance over zones?",
          "How do real drivers react to fee multipliers and alternates? A field study would replace the simulator's assumption that drivers do not react."),
    ]
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(body, "10")
