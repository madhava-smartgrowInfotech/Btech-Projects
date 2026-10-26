"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, EQ, H1, H2, N, P, TAB
from .refs import N as C


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming helper (shared by the other chapter modules). drop: block-text prefixes to remove; drop_sections: heading
    prefixes whose whole section is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        v = b[1]
        k = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    nr = lambda s: F.pop(100, s, "no_reservation")           # noqa: E731
    ins = F.SEED["insights_60d"]["totals"]
    td3, td5 = F.TD["0.3"], F.TD["0.5"]
    out = [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Introduction to the Project Domain"),
        P("Parking is the last step of almost every car journey in a city, and it is the step with the least information. A driver who reaches a destination does not know which lot has a free bay, "
          "and a lot operator does not know how many cars are on their way. The batch introduction records the resulting observations: drivers in dense urban areas spend a significant share of a trip searching for parking, "
          "the search adds congestion, wasted fuel and avoidable emissions, and operators who keep occupancy in manual registers have no view of demand and cannot plan capacity. "
          f"Surveys of smart parking treat this as a core problem of intelligent transportation systems {C('aljohani', 'xiao')}."),
        P("Advance reservation is the obvious remedy. If the driver books a bay for a time window before leaving home, the uncertain search becomes a guaranteed place. "
          f"Reservation-based parking has been built in many forms: as interval scheduling in which the scheduler accepts or rejects each request {C('doulamis')}, as web, SMS and smartphone services {C('safitri', 'somani')}, "
          f"as optimisation of walking distance and congestion {C('mejri')}, and with flexible times and dynamic pricing {C('kotb')}. "
          f"All of them share one weakness that the technical base paper of this project puts at the centre: a reservation is a promise about the future, and the promise is broken when the previous occupant does not leave on time. "
          f"Cabri et al. call the resulting event \"No Park\": a driver arrives with a valid reservation and finds the bay occupied {C('cabri')}."),
        P("Terms used throughout this report. A **location** is one parking facility with a capacity of bays. A **reservation** is a booking of one bay at one location for a time window. "
          "**Admission** is the decision to accept or decline a reservation request. The **hold-back buffer** is a number of bays at a location that new reservations may not use, kept free so that an arriving driver can still be placed if an earlier occupant overstays. "
          "An **overstay** is a checkout later than the end of the reserved window plus ten minutes of grace. The **Trust Score** is a driver's rating from 0 to 5 that changes the fee and can suspend booking. "
          "An **alternate** is the one nearest other location, by great-circle (haversine) distance, to which a driver is moved when the booked location is physically full on arrival."),
        H2("1.2 Background and Motivation"),
        P(f"The batch registers a 2026 IEEE Open Journal of the Computer Society paper as the base paper: \"Smart parking for medical cities via passenger-aware allocation and fast grouping-permutation heuristics\" {C('base')}. "
          "Its authors observe that traditional parking systems allocate space by vehicle count and propose to allocate it by the total number of passengers, so that the number of people per parking space is balanced across the zones of a large medical campus. "
          "The framework combines booking interfaces, IoT sensing and a central allocation engine, and six grouping-permutation algorithms are evaluated on nine instance classes and 2,790 generated test cases. "
          "The best algorithm reaches the highest best-solution share among the six (68.2 %), and the variant called GVb matches or beats the baseline MR on 1,547 of the 2,790 instances (55.4 %) in sub-millisecond time."),
        P(f"That paper solves allocation inside one managed facility. The batch's own gap statement says what it leaves open: a general reservation platform that covers search, booking, payment and operator analytics for ordinary urban parking. "
          f"The mechanisms that make such a platform reliable are described by a second paper, which is in the project folder as the base paper of the code and is treated here as the technical base paper: Cabri et al. {C('cabri')}. "
          "It adds a buffer of non-reservable bays to the reservation module, with a dynamic size that adapts to observed overstays, and a reputation system in which a 0 to 5 star rating changes the fee and can suspend a driver. "
          "It is evaluated in the SUMO traffic simulator with 80 spots in 8 areas, and its conclusion, shown in figures rather than a table, is that any buffer beats none and that the dynamic buffer gives the best trade-off between failed parks and rejected reservations."),
        P(f"{F.PRODUCT} is the product built on these ideas. It is a working web application, not a simulation: drivers register, search a time window, reserve, pay through Stripe Checkout in test mode or an offline demo checkout, check in and check out; "
          "administrators manage locations, users and bookings and read a Strategy Insights page that replays stored booking history under different buffer policies. "
          "The motivation is therefore twofold. For drivers and operators it is a concrete platform that covers the whole booking life cycle. For the project it is a chance to test, on running code, whether the published ideas behave as claimed, and to measure the platform's own response time and defects."),
        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four difficulties. Drivers circle repeatedly because there is no way to know which slots are free. Parking operators manage occupancy through manual registers with no live view. "
          "Without reservation, arriving at a facility gives no guarantee of a space. Cash-based collection is slow at entry and leaves no usable records. The stated need is a reservation platform that shows live availability, "
          "guarantees a slot in advance and handles payment digitally."),
        P("We restate the problem as one that can be tested. **Build a reservation platform in which a request is admitted only if a bay will be free for the requested window, "
          "a driver who finds the booked lot full on arrival is placed elsewhere or refunded, drivers who overstay pay more and can lose access, and the operator can see how different buffer policies would have performed on the recorded bookings; "
          "then measure how the platform behaves, including where it fails.** "
          "Let a location have capacity c and buffer b, and let a request for the window (s, e) overlap k admitted bookings (reserved or active). The admission rule implemented in the engine is:"),
        EQ("admit(request) = true   if and only if   k + b < c,      where k = |{ booking : start < e  and  end > s }|"),
        P("A buffer of 0 admits up to c bookings at the same moment, and every unit of buffer removes one bookable bay from every window. "
          "The practical problem is that a larger buffer protects arriving drivers but refuses more requests, while a smaller one does the opposite. How large the buffer should be, and whether it should change with observed behaviour, is the central design question."),
        H2("1.4 Need for the Proposed System"),
        B("**A guarantee that holds in practice.** A booking that is honoured only when the previous driver leaves on time is not a guarantee. The platform needs a buffer, an alternate and a refund rule for the case in which it fails.",
          "**Incentives for punctuality.** Overstays are the cause of failed arrivals. A fee multiplier and a suspension rule driven by the driver's own record give drivers a reason to book realistic windows.",
          "**Digital payment and records.** Cash at the gate is slow and leaves no data. Online payment creates a record for every booking, which is also what the operator analytics are computed from.",
          "**Operator visibility.** An operator who can see bookings, revenue, refused requests and failed arrivals, and can replay history under other policies, can tune capacity and buffers instead of guessing.",
          "**Evidence, not assertion.** Published buffer results come from a simulator and a preliminary study. A platform that carries its own tests, a parity-checked simulator and measured response times lets a reader check what actually works."),
        H2("1.5 Project Objectives"),
        P("The six objectives set for the batch, and the outcome of each, are listed below. The outcome column is the short version; Chapter 8 gives the measurements and Chapter 9 the verdict."),
        TAB("Objectives of the project and their outcome", ["No.", "Objective", "Outcome (summary)"],
            [["1", "Build user registration, authentication and vehicle profile management", "Partly achieved: registration, login, JWT sessions and driver and admin roles work and are tested; there is no vehicle profile (plate, model) in the data model or the screens."],
             ["2", "Maintain real-time parking slot availability across registered parking facilities", "Achieved as forecast availability: search returns the bookable bays per location for any window from stored bookings and the buffer; there is no sensor or gate feed, so physical occupancy is known only from check-ins."],
             ["3", "Implement slot search, advance reservation and booking cancellation", "Achieved and tested; cancelling a paid booking returns the fee as account credit."],
             ["4", "Integrate secure online payment and generate digital receipts", "Partly achieved: Stripe Checkout in test mode and an offline demo checkout store a payment record for every booking; there is no downloadable receipt, and the demo confirmation route is not authenticated (Chapter 7)."],
             ["5", "Provide an administrator dashboard for slots, bookings, occupancy and revenue", "Achieved: overview, locations, users, bookings and Strategy Insights screens; occupancy is shown as reserved and held bays, not live."],
             ["6", "Evaluate booking success rate, allocation efficiency and system response time", f"Achieved with the project's own tools: {F.PYTEST_PASSED} passing tests, a parity-checked simulator for success rate and utilisation, and measured response times (for example search {F.lat('GET /api/search'):.1f} ms mean)."]],
            widths=[0.45, 2.6, 3.35], align=["c", "l", "l"], size=10),
        H2("1.6 Scope of the Project"),
        P("**In scope.** Registration and login with hashed passwords and signed tokens; driver and administrator roles; parking locations with capacity, price and coordinates; availability search for a time window; "
          "reservation with admission control, fee quote and account credit; cancellation with refund to credit; payment through Stripe Checkout in test mode or an offline demo checkout; check-in, check-out and the on-time rule with ten minutes of grace; "
          "the per-location hold-back buffer with its daily reset; the haversine nearest-alternate move and the failed-and-credited outcome; the Trust Score with fee multipliers and suspension; "
          "the administrator screens and the Strategy Insights replay; a React console of eleven page components, 22 REST routes and five database tables; and the tests, simulator and measurement scripts that produce every number in this report."),
        P("**Out of scope.** Gate hardware, barriers, cameras and occupancy sensors; number-plate recognition; live traffic data; dynamic pricing by demand; multi-bay or multi-vehicle bookings; downloadable receipts and invoices; "
          "email or SMS notifications; vehicle profiles; native mobile apps (the console is responsive but is a web application); production hosting, backups and live-mode payments; and any study with real drivers."),
        H2("1.7 Project Contributions"),
        N("**A complete reservation platform.** One code base covers search, booking, payment, check-in and check-out, trust and operator analytics through 22 REST routes, five tables and an eleven-page React console, with 24 captured output screens.",
          "**The base papers' buffer and reputation ideas in running code,** together with a haversine nearest-alternate re-allocation that creates a replacement booking, automatic fee credit when no alternate exists, and a fee multiplier that follows the Trust Score.",
          "**Strategy Insights.** A deterministic replay of stored booking history under four buffer policies that gives an operator the counts of unable-to-park and declined requests without running a live experiment.",
          f"**A parity-tested simulator.** A discrete-event simulator that re-creates the base paper's 80-bay, 8-area scenario with ParkSure's rules and agrees with the real engine on {F.PAR['total_cases']:,} decisions with {F.PAR['total_mismatches']} mismatches, used to compare five buffer policies over 30 runs per setting.",
          f"**An honest evaluation.** {F.PYTEST_PASSED} passing tests, measured response times, a concurrency probe and security probes. The evaluation reports what did not work: the shipped dynamic buffer refuses the most reservations, an over-booking race exists, and an unauthenticated route can mark a booking paid."),
        P(f"In one paragraph, what the measurements show. In the simulator at 100 vehicles and 25 % overstaying drivers, a request is refused by admission {nr('static_0'):.0f} times per 1,000 with no buffer, {nr('static_3'):.0f} with a static buffer of 3, "
          f"{nr('dynamic_paper'):.0f} with the base paper's rule (grow the buffer when a vehicle leaves late) and {nr('dynamic_parksure'):.0f} with the rule ParkSure ships (grow it on every on-time checkout). "
          "\"No Park\" stays rare under every policy because the nearest-alternate step absorbs the overflow, and the Trust Score lockout, not the buffer, is the largest source of refused requests once a quarter of the drivers overstay. "
          "The base paper's conclusion that the dynamic buffer is the best trade-off is therefore not reproduced for the shipped rule. The seeded-history replay in the product gives the same ordering. These results come from a simulator with assumed arrival parameters and from synthetic demo data, and they are reported with that limit."),
        H2("1.8 Limitations and Assumptions"),
        B("**Synthetic data.** The only booking history is the product's own seed (9 users, 5 locations, 347 bookings over 60 days). It exercises the mechanisms but says nothing about real parking demand.",
          "**Simulator, not SUMO.** The scenario of the technical base paper is re-created in a purpose-built simulator. Arrival process, lead time, gaps between parks and the choice of area are assumptions the paper does not give; they are listed in the report and were fixed before the runs.",
          "**Forecast availability.** Availability is computed from bookings and the buffer. There are no sensors, so a vehicle that parks without checking in is invisible, and every simulated driver is assumed to check in at the planned arrival time.",
          "**Payments in test mode.** Stripe runs in test mode or the demo checkout runs offline; no live payment, webhook with real keys or refund flow was exercised.",
          "**Known defects.** The probes found an over-booking race under simultaneous requests, an unauthenticated demo confirmation route, a default token secret, no login rate limit, acceptance of past booking windows and very early check-ins, and slow list routes caused by repeated queries. They are reported in Chapters 7 and 8 and listed as future work in Chapter 10.",
          "**Single machine.** All measurements were made on one desktop with one server process and a SQLite file; nothing is claimed about larger deployments.",
          "**No user study.** Usability is described from the screens and from the responsive layout, not from tests with drivers."),
        H2("1.9 Organization of the Report"),
        P("Chapter 2 surveys the literature and analyses the two base papers. Chapter 3 studies feasibility, and Chapter 4 sets out the existing and proposed systems and the requirements. "
          "Chapter 5 gives the design: architecture, workflow, data flow and UML diagrams, the database and the user interface. Chapter 6 describes the methodology and implementation: "
          "the data, the admission and re-allocation algorithms with their mathematics, the Trust Score, the simulator, the API, security and error handling, and how to install and run the system. "
          "Chapter 7 reports testing. Chapter 8 presents every output screen, the measured results, the comparison with the base papers and the objectives against outcomes. "
          "Chapter 9 concludes and Chapter 10 sets out the future scope. The references and three appendices (important code, installation and user guide, additional screens) follow."),
    ]
    return out
