"""Text of 19.IEEE_Paper.docx (ParkSure). Every number is read from facts.py (experiments/**/metrics.json) or typed from docs/REPORT_FACTS.md.

Citations are written {r:key,key} (keys of refs.py); Paper.expand numbers them in order of first appearance, the base paper being [1].
"""
from . import facts as F
from . import paper_figs
from .paper import Paper


def build(path):
    figs = paper_figs.make()
    P = Paper()
    S = F.STRAT_NAME
    L = F.LAT["endpoints"]
    mb = F.MB
    adm = mb["forecast_free (admission, 100 bookings at the location)"]
    alt = mb["nearest_alternate over 49 other locations"]
    sd = F.SEED["insights_60d"]["totals"]
    t3, t5 = F.TD["0.3"], F.TD["0.5"]

    authors = [[n.upper(), f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY]", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY]", "[EMAIL]"])
    P.title_block("ParkSure: An Online Vehicle Parking Reservation System with a Hold-Back Buffer and Trust Score", authors)
    P.begin_two_columns()

    P.abstract(
        "Drivers in dense cities lose time looking for a free bay, and a reservation only helps if the reserved bay is really free on arrival. "
        "This paper presents ParkSure, a web platform in which drivers search availability for a time window, reserve a bay in advance, pay online and check in and out, while operators manage locations and see analytics. "
        "Its availability engine admits a request only if overlapping bookings plus a hold-back buffer stay below capacity, moves a driver to the nearest alternate location by haversine distance when a lot is full on arrival, "
        "and adjusts fees and access through a 0-5 Trust Score. The system has 22 API routes and five tables and is checked by "
        f"{F.PYTEST_PASSED} automated tests. A discrete-event simulator, verified decision by decision against the real engine, compares five buffer policies. "
        "In it the shipped dynamic buffer refuses the most requests, arrivals with no bay stay rare under every policy, and the Trust lockout is the largest source of refusals. "
        "Our own probes also found an over-booking race and an unauthenticated payment-confirmation route.",
        ["buffer policy", "haversine distance", "parking reservation", "reputation system", "smart parking", "web application"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Searching for a free space adds to urban congestion and emissions, and efficient parking management is a recurring theme of smart-city research {r:base,cabri}. "
           "In many car parks today the operator keeps manual registers or a cash counter, has no live view of occupancy and no record of demand, and the driver learns whether a space exists only on arrival. "
           "Advance reservation turns that search into a guaranteed bay, but it creates a failure of its own: a reserved bay may still be held by a previous driver who overstays, the \"No Park\" situation described by Cabri et al. {r:cabri}. "
           "The base paper of this project optimises how vehicles are assigned to spaces inside one large managed facility {r:base}; the work that proposes a reservation buffer {r:cabri} is evaluated only in simulation. "
           "What is missing is an operating reservation platform for ordinary urban parking that joins search, booking, payment and operator analytics with an overstay-aware availability rule, and that reports how it actually behaves.")
    P.para("This paper makes four contributions. (1) ParkSure, a tested full-stack platform (FastAPI, React, SQLite; 22 routes, five tables) for search, reservation, payment, check-in, check-out and administration. "
           "(2) A Smart Availability Engine that implements the reservation buffer and star-reputation ideas of Cabri et al. {r:cabri} in a product, and adds a haversine nearest-alternate move with automatic credit and a trust-based fee multiplier. "
           f"(3) Verification: {F.PYTEST_PASSED} pytest tests, a simulator that agrees with the engine on {F.PAR['total_cases']:,} decisions, and measured response times. "
           "(4) A comparison of five buffer policies and a plain list of the defects that our own probes found. Section II reviews related work, Section III the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All measurements were taken on one machine: 12th-generation Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, no GPU, other programs running.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.14.7, FastAPI 0.141.1 {r:fastapi}, SQLAlchemy 2.0.52, SQLite, APScheduler 3.11.3, python-jose 3.5.0 for JSON Web Tokens {r:jwt}, bcrypt 5.0.0 {r:bcrypt}, the Stripe SDK 15.6.1 {r:stripe} in test mode, "
           "React 19 with Vite 8 and Node 24.19.0 for the console, pytest and Playwright with Chrome for tests and screenshots.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Jemmali et al. {r:base} address parking in medical cities, where each vehicle carries a different number of people. They assign vehicles to parking spaces so that the total number of people per space, "
           "not the number of vehicles, is balanced, and minimise the total excess of the loads over the smallest load. Visitors register a request by web or mobile application with their passenger count, receive a QR code, "
           "and at the gate sensors compare the declared count with the occupancy seen by cameras before a scheduler allocates a space. A four-stage grouping procedure and six grouping-permutation heuristics are evaluated on nine instance classes and 2,790 test cases: "
           "the best algorithm has the highest best-solution share (68.2 %), the variant GVb matches or beats the baseline MR on 1,547 instances (55.4 %), and execution times are below a millisecond. "
           "In our reading the paper solves allocation inside one facility and does not treat payment, overstays or operator analytics.")
    P.para("**Technical basis.** Cabri et al. {r:cabri} study reservation-based parking in which only vehicles with a reservation may enter. A Reservation Module keeps a buffer of non-reservable bays per area; when a driver finds the area full, "
           "the system suggests exactly one nearby area and books it automatically, and if that fails the driver cannot park (\"No Park\"). The dynamic rule raises the buffer by one whenever a vehicle leaves after its reservation ended, up to a maximum, with a periodic reset. "
           "A Reward System keeps a 0-5 star rating: B benefits (on-time departures) add a star, W warnings (overstays) remove one, the rating changes the fee, and a low rating with a recent violation suspends booking. "
           "In a SUMO simulation {r:sumo} of 80 spots in 8 areas, with 80 to 110 vehicles, 25 to 50 % of them overstaying by one hour, and five runs, any buffer beats none and the dynamic buffer gives the best trade-off between failed parks and rejected reservations; the results are given as figures, not tables.")
    P.para("**Related work.** Reservation has been approached as scheduling, optimisation, pricing, auction and service design. Doulamis et al. {r:doulamis} model requests as time intervals that a scheduler accepts or rejects, "
           "a view that matches the classical interval-scheduling problem {r:kt}; Mejri et al. {r:mejri} formulate slot assignment as a multi-objective integer programme over walking distance, vehicle proximity and congestion; "
           "iParker {r:kotb} adds flexible reservation times with dynamic pricing; Somani et al. {r:somani} ask for part of the fee up front to prevent false bookings; and Safitri et al. {r:safitri} build a mobile reservation system with a heuristic and the haversine formula. "
           "Auction-based systems let agents or drivers bid for spaces {r:asap,mapark,kokolaki}; SmartParking {r:yan} offers on-the-fly reservation with real-time availability; Chen et al. {r:chen} analyse the efficiency and equity of reservation; "
           "and surveys organise the field {r:aljohani}. Table I summarises what each work reports, using only what the two papers above state about them.")
    P.table("Related work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["Jemmali et al. {r:base}", "Passenger-count zone balancing, 6 heuristics", "9 classes, 2,790 test cases", "Best 68.2 %; GVb ties or beats MR on 55.4 %", "One facility; no payment, overstay"],
             ["Cabri et al. {r:cabri}", "Buffer of non-reservable bays + star reward", "SUMO, 80 spots, 8 areas, 5 runs", "Any buffer beats none; dynamic best (figures)", "Simulation only; preliminary"],
             ["Doulamis et al. {r:doulamis}", "Interval scheduling of requests", "Not stated in {r:cabri}", "Not stated in {r:cabri}", "Overstays not described"],
             ["Mejri et al. {r:mejri}", "Multi-objective integer programme", "Not stated in {r:cabri}", "Not stated in {r:cabri}", "No operating platform described"],
             ["Kotb et al. {r:kotb}", "Flexible times, dynamic pricing", "Not stated in {r:cabri}", "Not stated in {r:cabri}", "Punctuality-based fees not described"],
             ["Somani et al. {r:somani}", "Part-payment to confirm a booking", "Not stated in {r:cabri}", "Not stated in {r:cabri}", "Overstays not addressed"],
             ["Safitri et al. {r:safitri}", "Mobile app, heuristic, haversine", "Not stated in {r:cabri}", "Not stated in {r:cabri}", "No buffer or reputation"],
             ["Rizvi, Kokolaki {r:asap,mapark,kokolaki}", "Auction-based allocation", "Not stated in {r:cabri}", "ASAP: better utilisation (per {r:cabri})", "Not a fixed-price service"]],
            [0.62, 0.74, 0.62, 0.78, 0.64], size=5.8, align=["l", "l", "l", "l", "l"])
    P.para("**Positioning.** Three observations follow from Table I. First, the two papers that matter most for ParkSure answer different questions: the registered base paper {r:base} decides where each vehicle goes inside a facility, "
           "while Cabri et al. {r:cabri} decide how many bays a booking system should hold back. ParkSure takes the booking-system side, so its rules come from {r:cabri} and its architecture from the web-booking interface that {r:base} also assumes. "
           "Second, none of the other works in the table is described, in the two papers that cite them, as handling the overstay that makes a reserved bay unavailable; the deposit of Somani et al. {r:somani} deters false bookings but not late departures. "
           "Third, the cited results are mostly not stated, so the comparison in Section IV is made against the two base papers only and does not pretend to rank ParkSure among the others.")
    P.para("**Gap.** The surveyed work either optimises allocation inside one managed facility, proposes a buffer and reputation mechanism that is evaluated only in simulation, or describes reservation components one at a time. "
           "A general platform that combines search, booking, payment, an overstay-aware availability rule and operator analytics, and that measures its own behaviour, is not reported. ParkSure implements that platform and tests it.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Architecture and Implementation")
    P.figure(figs["arch"], "ParkSure architecture: React console, FastAPI service with 22 routes and the availability engine, SQLite with five tables, a scheduler job and Stripe or the demo checkout.", 3.3)
    P.para("The console (Vite proxy from port 5403 to the API on 8403) has landing, login, find parking, my bookings and trust-score pages for drivers and five admin pages. The API follows the usual REST style: "
           "JSON bodies validated by pydantic (422 on bad input), bearer tokens with role guards (401, 403), 409 when a window is full. Passwords are hashed with bcrypt at cost 12. "
           "SQLAlchemy maps users, parking_locations, reservations, payments and trust_events to one SQLite file. When no Stripe key is configured an offline demo checkout keeps every flow usable, and the interface says so. "
           "A payment record is created with every reservation (paid at once when account credit covers the fee, pending otherwise) and moves to refunded when a paid booking is cancelled, the fee then returning as account credit. "
           "For operators, the Strategy Insights route replays the stored booking requests of each location in time order under four buffer settings (none, 1, 3 and the dynamic rule) and counts requests declined by admission and requests admitted but unable to park, "
           "so the same input always gives the same output.")
    P.para("Four implementation decisions are worth stating with their reasons. SQLite keeps installation to one file and is enough for a single-process demonstration, but it limits concurrent writers; "
           "the admission rule is a plain count over an indexed interval query because it is easy to audit and costs 0.33 ms for 100 stored bookings (Section IV); "
           "the nearest-alternate search issues one availability query per other location, which is simple and correct but grows linearly with the number of locations; "
           "and the engine is kept in one module with no web imports so that the simulator and the tests can call the same functions.")
    P.sub("B", "Admission, Buffer and Alternate")
    P.para("A reservation is an interval [s, e) at a location l with capacity C_l and buffer b_l. With n_ov(s, e) the number of reserved or active bookings that overlap the interval, the request is admitted only if")
    P.eq("n_ov(s, e) + b_l < C_l,")
    P.para("otherwise it is stored as declined with the reason. The buffer starts at 1; every on-time check-out (at most ten minutes after e) raises it by one up to 5, and a scheduler job running every 30 minutes resets it to 1 once 24 hours have passed. "
           "Note that this grows the buffer on punctual departures, whereas the paper {r:cabri} grows it on late ones; we keep the shipped rule and evaluate both. "
           "At check-in, if the number of parked vehicles already equals C_l, the engine searches the other locations that pass the admission test for the same window and picks the nearest by the haversine distance {r:sinnott}")
    P.eq("a = 2R asin( sqrt( sin²(Δφ/2) + cos φ_1 cos φ_2 sin²(Δλ/2) ) ),   R = 6371 km.")
    P.para("The driver is booked there as an active alternate; if no location qualifies, the booking is marked failed and the fee is credited to the account.")
    P.sub("C", "Trust Score and Fee")
    P.para("Each driver starts with a score T = 3 on a 0-5 scale. An on-time check-out records a benefit and three consecutive benefits add one point; a late check-out resets the streak and records a warning, and two warnings remove one point. "
           "The fee is")
    P.eq("fee = max(0.25, (e - s) / 1 h) × price_l × m(round T),   m = {1.75, 1.5, 1.25, 1.0, 0.95, 0.9} for T = 0...5.")
    P.para("A driver with T < 1.5 and a warning in the last 14 days is refused and paused for 24 hours at each attempt. Account credit offsets the fee before payment.")
    P.figure(figs["flow"], "Main flow of ParkSure: availability search, suspension and admission checks, fee quote and payment, arrival (direct, alternate or failed), check-out and the trust and buffer updates.", 3.3)
    P.sub("D", "Data and Evaluation Protocol")
    P.para("ParkSure uses no external dataset. Its demo database, produced by the product's own seed script, holds 5 locations, 9 users and 347 reservations over 60 days, and is therefore synthetic. We evaluate in four ways. "
           f"(i) {F.PYTEST_PASSED} pytest tests ({F.PYTEST_ENGINE} engine, {F.PYTEST_API} API, {F.PYTEST_PARITY} simulator) and 27 smoke checks. "
           f"(ii) A discrete-event simulator re-creates the setting of {{r:cabri}}: 8 areas of 10 bays, 80 to 110 vehicles making 10 parks of 1 to 3 hours, bad vehicles leaving one hour late, two long stops outside the system, and runs the ParkSure rules including the Trust Score. "
           f"It is not SUMO, and what the paper does not give (arrival process, lead time 15 to 60 minutes, gaps, uniform area choice) is our assumption, fixed before the runs. Each cell is the mean of {F.SEEDS} runs. "
           f"Its admission, trust and suspension functions agree with the real engine on {F.PAR['total_cases']:,} decisions with {F.PAR['total_mismatches']} mismatches. "
           "The simulator processes three event types in time order: a request (suspension check, then admission), an arrival (direct parking, alternate move or failure) and a departure (buffer and trust update, then the vehicle's next request). "
           "Every request ends in exactly one outcome, refused by admission, refused by the lockout, parked directly, parked at an alternate, or no park, and a test checks that the five counts sum to the number of requests. "
           "Utilisation is occupied bay-hours divided by the 80 bays times the length of the run. "
           "(iii) Response times on 127.0.0.1 with 200 sequential requests per endpoint. (iv) Probes for concurrency and security on a throw-away database.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Buffer Policies in the Simulator")
    P.para("Five policies are compared: static buffers of 0, 1 and 3 bays, the shipped dynamic rule (buffer grows on on-time departures) and the paper's rule (grows on late departures). "
           "\"Refused\" counts requests rejected by admission, \"no bay\" counts arrivals that found no bay (no alternate, or an alternate that was itself full), and \"success\" is the share of all requests that ended with a parked car. "
           "Table II gives two operating points.")
    rows = []
    for s in F.STRATS:
        rows.append([S[s], f"{F.pop(100, s, 'no_reservation'):.0f}", f"{F.pop(100, s, 'success_rate') * 100:.1f}",
                     f"{F.bad(0.5, s, 'no_reservation'):.0f}", f"{F.bad(0.5, s, 'no_park') + F.bad(0.5, s, 'alt_overflow'):.2f}", f"{F.bad(0.5, s, 'success_rate') * 100:.1f}"])
    P.table("Simulator results (mean of 30 runs per cell)", ["Policy", "Refused, 100 veh., 25 % bad", "Success %", "Refused, 50 % bad", "No bay, 50 % bad", "Success %"], rows,
            [0.92, 0.6, 0.45, 0.5, 0.45, 0.48], size=6.2, align=["l", "c", "c", "c", "c", "c"])
    P.para(f"At 100 vehicles and 25 % overstaying drivers the shipped dynamic rule refuses {F.pop(100, 'dynamic_parksure', 'no_reservation'):.0f} of 1,000 requests, the paper's rule {F.pop(100, 'dynamic_paper', 'no_reservation'):.0f}, "
           f"static 3 {F.pop(100, 'static_3', 'no_reservation'):.0f} and no buffer {F.pop(100, 'static_0', 'no_reservation'):.0f}; it raises the buffer after every punctual departure, up to the cap of five. "
           f"Arrivals with no bay are rare for every policy (at most {max(F.bad(0.5, s, 'no_park') + F.bad(0.5, s, 'alt_overflow') for s in F.STRATS):.1f} per run of about 936 requests at 50 % overstay): the alternate move absorbs the overflow. "
           f"The cost shows as the alternate itself being full: static 0 produces {F.bad(0.5, 'static_0', 'alt_overflow'):.1f} such events per run against {F.bad(0.5, 'static_3', 'alt_overflow'):.1f} for static 3, because the shipped code books the alternate without re-checking its bays. "
           f"Utilisation falls from {F.pop(100, 'static_0', 'utilisation') * 100:.1f} % (static 0) to {F.pop(100, 'dynamic_parksure', 'utilisation') * 100:.1f} % (shipped dynamic) at 100 vehicles. "
           f"The Trust lockout matters more than the buffer: at 50 % overstay it refuses {F.bad(0.5, 'dynamic_parksure', 'suspended'):.0f} to {F.bad(0.5, 'static_0', 'suspended'):.0f} requests per run, and switching it off lifts the success rate of static 0 from "
           f"{F.abl(0.5, True, 'static_0', 'success_rate') * 100:.0f} % to {F.abl(0.5, False, 'static_0', 'success_rate') * 100:.0f} %.")
    P.para(f"Demand pressure acts as expected. From 80 to 110 vehicles the refusals of static 0 rise from {F.pop(80, 'static_0', 'no_reservation'):.0f} to {F.pop(110, 'static_0', 'no_reservation'):.0f} per run and those of the shipped dynamic rule from "
           f"{F.pop(80, 'dynamic_parksure', 'no_reservation'):.0f} to {F.pop(110, 'dynamic_parksure', 'no_reservation'):.0f}, while the success rate of static 0 falls from {F.pop(80, 'static_0', 'success_rate') * 100:.0f} % to {F.pop(110, 'static_0', 'success_rate') * 100:.0f} % and that of the shipped rule from "
           f"{F.pop(80, 'dynamic_parksure', 'success_rate') * 100:.0f} % to {F.pop(110, 'dynamic_parksure', 'success_rate') * 100:.0f} %. "
           f"With more overstaying drivers the refusals by admission of the shipped rule fall from {F.bad(0.25, 'dynamic_parksure', 'no_reservation'):.0f} to {F.bad(0.5, 'dynamic_parksure', 'no_reservation'):.0f}, "
           f"but only because the refusals by the lockout rise from {F.bad(0.25, 'dynamic_parksure', 'suspended'):.0f} to {F.bad(0.5, 'dynamic_parksure', 'suspended'):.0f}: the requests are refused earlier, not served. "
           "Cabri et al. also see fewer rejected reservations as the share of bad vehicles grows and attribute it to lower turnover {r:cabri}; in our runs the cause is the lockout, and we make no claim about theirs.")
    P.figure(figs["results"], "Buffer policies in the simulator: (a) requests refused by admission against the number of vehicles (25 % overstaying); (b) arrivals with no bay against the share of overstaying drivers. Legend as in Table II.", 3.3)
    P.para(f"Replaying the 60-day seeded history under four buffers gives, as unable-to-park / declined, {sd['fixed_0']['unable_to_park']}/{sd['fixed_0']['declined']} (no buffer), {sd['fixed_1']['unable_to_park']}/{sd['fixed_1']['declined']} (fixed 1), "
           f"{sd['fixed_3']['unable_to_park']}/{sd['fixed_3']['declined']} (fixed 3) and {sd['dynamic']['unable_to_park']}/{sd['dynamic']['declined']} (dynamic), the same ordering on synthetic data. "
           f"For the Trust Score, a driver who ends 30 % of sessions late reaches a mean score of {t3['mean_final_trust']:.1f} after 100 daily sessions, a mean fee multiplier of {t3['mean_fee_multiplier']:.2f}, and {t3['share_ever_suspended'] * 100:.0f} % are suspended at some point; at 50 % the mean score is {t5['mean_final_trust']:.1f} and all are suspended.")
    P.figure(figs["trust"], "Trust Score dynamics of one driver over 100 daily sessions (200 simulated drivers per point): mean final score and share of drivers ever suspended against the probability of a late session.", 3.3)
    P.para(f"The curve shows how sharp the rule is: at a late-session probability of 0.1 the mean score stays at {F.TD['0.1']['mean_final_trust']:.1f} and {F.TD['0.1']['share_ever_suspended'] * 100:.1f} % of drivers are ever suspended, "
           f"at 0.2 the mean is {F.TD['0.2']['mean_final_trust']:.1f} and {F.TD['0.2']['share_ever_suspended'] * 100:.0f} % are suspended, and from 0.3 upwards most drivers are locked out within about {t3['median_first_suspension_session']} sessions. "
           "Because the lockout repeats at every attempt while the score is below 1.5 and the last warning is under 14 days old, a driver who is suspended cannot earn the benefits that would restore the score before the 14 days pass.")
    P.sub("B", "Response Time and Tests")
    lat = lambda k: F.lat(k)
    rows3 = [["Automated tests", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} pass; 27 of 27 smoke checks"],
             ["Simulator against engine", f"{F.PAR['total_cases']:,} decisions, {F.PAR['total_mismatches']} mismatches"],
             ["Search availability", f"{lat('GET /api/search'):.1f} ms mean, {F.lat('GET /api/search', 'p95_ms'):.1f} ms p95"],
             ["Reserve", f"{lat('POST /api/reservations'):.1f} ms mean, {F.lat('POST /api/reservations', 'p95_ms'):.1f} ms p95"],
             ["Check in / check out", f"{lat('POST /api/reservations/{id}/checkin'):.1f} / {lat('POST /api/reservations/{id}/checkout'):.1f} ms mean"],
             ["Login (bcrypt, cost 12)", f"{lat('POST /api/auth/login'):.0f} ms mean"],
             ["Own bookings list (about 400 rows)", f"{lat('GET /api/reservations'):.0f} ms mean"],
             ["Admin all bookings (300 rows)", f"{lat('GET /api/admin/bookings'):.0f} ms mean"],
             ["Admin Strategy Insights", f"{lat('GET /api/admin/insights'):.0f} ms mean"],
             ["Admission decision, in process", f"{adm['mean_ms']:.2f} ms mean"],
             ["Nearest alternate, 49 locations", f"{alt['mean_ms']:.1f} ms mean"],
             ["Search throughput, 8 threads", f"{F.LAT['endpoints']['throughput_search_8_threads']['req_per_s']:.0f} requests/s"]]
    P.table("Tests and measured response time", ["Measure", "Result"], rows3, [1.65, 1.7], size=6.4, align=["l", "l"])
    P.para(f"The {F.PYTEST_ENGINE} engine tests cover the haversine distance, every fee multiplier, the admission rule with and without buffers, the nearest-alternate choice, the trust updates and caps, suspension and the buffer reset; "
           f"the {F.PYTEST_API} API tests cover registration, login, role guards, location management, search, reservation, cancellation with credit, check-in with the alternate and the failed outcome, check-out, suspension, payment, administration and validation errors. "
           "The tests assert the intended behaviour of the code as shipped; they do not cover concurrency, which is why the race below was found only by a separate probe.")
    P.para("Ordinary calls take under 20 ms. The two slow list endpoints are slow because every row issues two extra database queries, a defect rather than a necessity. "
           "The admission decision itself is sub-millisecond, which echoes the sub-millisecond execution that the base paper reports for its heuristics {r:base}, but the two solve different problems and the numbers are not comparable.")
    P.sub("C", "Output Screens")
    P.para("The screens were captured from the running application on a fresh database with real data produced by the flows themselves. "
           "In Fig. 5 a second driver holds a booking at Kiosk Bay, a one-bay lot already occupied by an earlier driver, so on check-in the engine books Central Station Garage, 0.1 km away, "
           "marks the first booking unable to park and links the new booking to it. Fig. 6 is the operator view of the stored-history replay quoted above.")
    P.figure(figs["moved"], "Real screen: a driver arrives at the occupied one-bay Kiosk Bay, is moved to Central Station Garage 0.1 km away, and the original booking is marked unable to park.", 3.3)
    P.figure(figs["insights"], "Real screen: Strategy Insights, the stored booking history replayed under four buffer policies (unable to park and declined).", 3.3)
    P.sub("D", "Comparison with the Base Papers")
    P.para("The registered base paper {r:base} optimises zone load balance on 2,790 test instances; ParkSure does not implement its grouping algorithms, so no score is comparable and we do not claim to match or beat it. "
           "Both are web-booking systems with a central allocation step and fast decisions. Against Cabri et al. {r:cabri}, whose results are figures, the direction \"any buffer helps\" is partly visible here (no bay events at 50 % overstay: "
           f"{F.bad(0.5, 'static_0', 'no_park') + F.bad(0.5, 'static_0', 'alt_overflow'):.1f} for no buffer against {F.bad(0.5, 'static_3', 'no_park') + F.bad(0.5, 'static_3', 'alt_overflow'):.1f} for static 3), but \"dynamic is best\" is not reproduced for the shipped rule, which refuses the most. "
           "The settings differ in every respect: our simulator is not SUMO, the arrival process is assumed, the Trust Score is included, the alternate move is part of the system, and we use 30 runs where the paper uses five.")
    P.sub("E", "Failure Cases and Observed Limits")
    sec = F.SEC
    P.table("Defects found by the team's own probes", ["Probe", "Observed"],
            [["20 simultaneous requests, 1 bookable bay", f"{F.RACE['trials_with_overbooking']} of {F.RACE['trials']} trials accepted 2 bookings"],
             ["Payment confirm route without login", "Booking marked paid: " + ("yes" if sec["unauthenticated_demo_confirm_marks_paid"]["vulnerable"] else "no")],
             ["Token forged with the default JWT secret", "Admin route accepted: " + ("yes" if sec["forged_token_with_default_secret"]["accepted"] else "no")],
             ["30 wrong passwords in a row", "All refused, no lockout or rate limit"],
             ["Booking window in the past", "Accepted: " + ("yes" if sec["past_window_accepted"]["accepted"] else "no")],
             ["Check-in 25 days before the window", "Accepted: " + ("yes" if sec["early_checkin_accepted"]["accepted"] else "no")],
             ["Injection-style inputs, other user's booking", "Rejected (422), blocked (404)"]],
            [1.75, 1.6], size=6.3, align=["l", "l"])
    P.para(f"Our probes found real defects. In {F.RACE['trials_with_overbooking']} of {F.RACE['trials']} trials of 20 simultaneous requests for one bookable bay, two bookings were accepted, because the admission count and the insert are not atomic. "
           "The demo payment route can be called without a login and marks any booking paid; a token forged with the default secret is accepted; failed logins are not rate limited; bookings that start in the past and check-in 25 days early are accepted. "
           "The suspension lasts at least 14 days after the last warning, not one session. There is no vehicle profile and no downloadable receipt, so two of the six project objectives are only partly met. "
           "The data are synthetic, availability is a forecast without sensors, and there was no user study, no hardware gate and no SUMO run.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"ParkSure delivers a working path from availability search to reservation, payment, check-in, alternate re-allocation, check-out and operator analytics, verified by {F.PYTEST_PASSED} tests and by a simulator that agrees with the engine. "
           "Against the objectives, registration, search, booking, cancellation, payment in test mode, the admin dashboard and the evaluation are achieved; vehicle profiles and receipts are not. "
           "The main finding is that the shipped dynamic buffer, which grows on punctual departures, refuses the most requests and gives no clear gain over static buffers, and that the Trust lockout dominates refusals once a quarter of drivers overstay. "
           "Limits are the synthetic data, the simulator in place of SUMO and the defects listed above.")
    P.para("For an operator the practical reading is cautious. The product is usable for a demonstration and for studying reservation policy, but before any real deployment the payment route must be closed, admission made atomic, "
           "and the buffer rule chosen deliberately: a static buffer of one or three bays refused far fewer requests than the shipped dynamic rule in our simulator, at the price of more alternate moves.")
    P.para("Future work: make admission atomic and close the payment route; add vehicle profiles and PDF receipts; test the paper's rule in the product and re-check the alternate's bays; shorten the lockout to one session; "
           "predict overstays from history; and measure against real parking data and a SUMO scenario.")

    P.references()
    P.save(path)
    return path
