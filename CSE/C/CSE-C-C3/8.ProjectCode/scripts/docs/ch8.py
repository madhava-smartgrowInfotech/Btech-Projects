"""Chapter 8: Results and output screens. Every number is read from facts.py (experiments/**/metrics.json) or typed exactly as in docs/REPORT_FACTS.md."""
import json
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, P, PAIR, TAB
from .refs import N

SH = F.shot


def S(name, caption, base=5.6, max_h=3.7):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def G(name, caption, width=5.6):
    """Result figure from docs/figures; omitted if the file has not been produced."""
    path = F.fig(name)
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def _compact(blocks):
    """Report variant: drop the sub-headings and put the screenshots two per figure, each with its own caption."""
    out, pend = [], []
    for blk in blocks:
        if blk[0] == "h3":
            continue
        if blk[0] == "fig":
            pend.append((blk[1], blk[2]))
            if len(pend) == 2:
                out.append(PAIR(pend, 2.95))
                pend = []
        else:
            out.append(blk)
    if pend:
        out.append(FIG(pend[0][0], pend[0][1], 4.0))
    return out


def _pol_rows(group, getter, keys, label_fmt):
    rows = []
    for k in keys:
        for s in F.STRATS:
            g = getter(k, s)
            rows.append([label_fmt(k), F.STRAT_NAME[s], f"{g('requests'):.0f}", f"{g('no_reservation'):.1f}", f"{g('suspended'):.1f}", f"{g('no_park'):.2f}",
                         f"{g('moved_to_alternate'):.1f}", f"{g('alt_overflow'):.2f}", f"{g('success_rate') * 100:.1f}", f"{g('utilisation') * 100:.1f}"])
    return rows


HEAD = ["", "Policy", "Requests", "Refused: no space", "Refused: suspended", "No park", "Moved to alternate", "Alternate full", "Parked %", "Util. %"]


def _setup():
    return [H2("8.1 Experimental set-up"),
            P("ParkSure has no learned model and no external dataset, so the results of this chapter are of four kinds: what the application shows when it runs (Section 8.2), how its availability rules behave in a controlled simulation (Sections 8.3 to 8.5), "
              "what its Strategy Insights page computes on the seeded demo history (Section 8.6), and how fast it answers and where it fails (Chapter 7, summarised in Section 8.7). "
              f"All measurements were made on one machine, a 12th-generation Intel Core i5-12500 with 15.7 GB of memory and Windows 11, and every table and figure is drawn from the stored files `experiments/**/metrics.json`."),
            H3("8.1.1 The data"),
            P(f"The only data are the demo records that `app/seed.py` creates with a fixed random seed (42) on first start: {F.SEED['users']} users (one administrator and eight drivers, two of whom have overstay history), {F.SEED['locations']} locations "
              f"(20, 12, 15, 25 and 8 bays), and {F.SEED['reservations']} reservations spread over the previous 60 days, with eight Friday-evening peaks at Old Town Deck that oversubscribe it. "
              f"Of these, {F.SEED['status_counts']['completed']} are completed, {F.SEED['status_counts']['failed']} failed (the driver could not park) and {F.SEED['status_counts']['declined']} were declined. "
              "**These records are synthetic**: they show that the mechanisms work, not how real drivers behave. No real payment was taken."),
            H3("8.1.2 The simulation"),
            P(f"For the buffer experiments the team wrote a discrete-event simulator (`scripts/parking_sim.py`) that re-creates the scenario of the reservation paper {N('cabri')}: 8 areas of 10 bays (80 in all), 80 to 110 vehicles, each making 10 parks of 1 to 3 hours, a share of the vehicles overstaying by one hour, and two long stops outside the system. "
              f"The paper ran it in SUMO {N('sumo')}; ParkSure's simulator applies the product's own rules (admission, nearest-alternate move, Trust Score, suspension), which were compared with the real engine on {F.PAR['total_cases']:,} cases with {F.PAR['total_mismatches']} mismatches (Section 7.3). Each cell is the mean of {F.SEEDS} runs (the paper used 5)."),
            TAB("What the simulator assumes where the paper is silent (fixed before the runs).", ["Item", "Assumption"],
                [["Areas and requests", "8 areas x 10 bays about 1.3 km apart, uniform choice of area; first request in the first 2 hours, reservation 15 to 60 minutes before arrival, stay 1 to 3 hours, next request 15 to 60 minutes after leaving, two outside stops of 8 to 16 hours"],
                 ["Behaviour", "Good vehicles leave exactly at the end, bad vehicles one hour late; every driver checks in at the planned time"],
                 ["Policies", "Static buffer 0, 1 and 3; the rule as shipped (+1 on every on-time checkout, maximum 5, reset every 24 hours); the paper's rule (+1 on every late departure, same maximum and reset)"],
                 ["Trust Score", "On, as shipped; an ablation switches it off"]],
                widths=[1.4, 5.1], align=["l", "l"], size=9.5),
            P("Outcomes are counted per request. **Refused: no space** is a request rejected by the admission rule; **Refused: suspended** is a request rejected by the Trust Score lockout; **No park** is an admitted booking whose driver found the area full and no alternate with forecast space; "
              "**Moved to alternate** is a driver who found the area full and was served at the nearest alternate; **Alternate full** counts moves in which the alternate was physically full as well, which the shipped code does not re-check; "
              "**Parked %** is the share of all requests that ended with a parked car; **Util. %** is bay-hours used divided by bay-hours available over the run.")]


def _screens():
    b = [H2("8.2 Output screens"),
         P("The screens below were captured from the running application at 1440 by 900 pixels on a freshly seeded database; none is a mock-up and every figure visible in a caption can be found in the picture. "
           "The remaining screens (landing page in both themes, login, the check-in and check-out confirmations, the second driver's bookings, the locations, bookings and users tables, the phone layout and the API documentation page) are in Appendix C.")]
    b += [H3("8.2.1 Searching and reserving"),
          S("06_find_parking.png", "Find parking for the default window (26 October, 3:00 to 5:00 PM): six locations with their bays, how many are held or reserved, the hourly price and the buffer (1 at five locations, 0 at the one-bay Kiosk Bay), and the bays that can still be reserved (Airport Express Park 24 free of 25, Central Station Garage 18 free of 20). Kiosk Bay is already Full for this window."),
          S("07_search_full_lot.png", "Search for a window that overlaps the booking of the one-bay Kiosk Bay: its card shows Full and a disabled No space for this window button, while the other five locations show free bays."),
          S("08_reserve_dialog.png", "Reserve dialog for Airport Express Park, 27 October 3:47 PM to 6:47 PM: 3 hours at $5.00 per hour with the driver's trust multiplier x0.95 gives an estimated fee of $14.25. The server computes the final fee with the same formula."),
          S("09_reservation_confirmed.png", "Reservation confirmed: booking #352 with a fee of $14.25 (x0.95 trust multiplier) and the amount due. Because no Stripe key is set, the demo checkout button is offered.")]
    b += [H3("8.2.2 Check-in, check-out and the Trust Score"),
          S("10_my_bookings.png", "My bookings for the demo driver: booking numbers, locations, windows, status badges, fees with the multiplier, and payment state. Reserved bookings offer Check in and Cancel; unpaid ones offer Confirm demo payment."),
          S("12_check_out_toast.png", "After the driver checked in and out of booking #348 through the buttons: the row is Completed, and the two confirmations read Checked in at Central Station Garage and Checked out on time."),
          S("13_trust_score.png", "Trust Score page: score 4 of 5, fee multiplier x0.95, on-time streak 1 (two more for the next point), no recent warnings, and the event history that begins with the on-time checkout just recorded above the seeded late checkouts.")]
    b += [H3("8.2.3 Arrival at a full location"),
          S("15_moved_to_alternate.png", "Second driver arriving at Kiosk Bay, whose single bay was occupied: booking #353 shows Unable to park with the reason, the replacement booking #354 at Central Station Garage is Parked and marked Alternate for #353, and the toast reads that the driver was moved 0.1 km away.")]
    b += [H3("8.2.4 Administrator screens"),
          S("17_admin_overview.png", f"Administrator overview of the fresh database after the capture session: 10 users, 6 locations, 354 reservations, paid revenue $1,604.00, 40 unable to park and 29 declined, with the Strategy Insights chart below."),
          S("19_admin_insights.png", "Strategy Insights over the last 60 days: the same stored booking history replayed under no buffer, a fixed buffer of 1, a fixed buffer of 3 and the dynamic policy, shown as unable-to-park and declined counts, with the per-location table below.")]
    return _compact(b) if F.REPORT else b


def _population():
    n100 = lambda s, m: F.pop(100, s, m)  # noqa: E731
    return ([H2("8.3 Buffer policies against the number of vehicles"),
             P(f"The table and figure below vary the population from 80 vehicles, equal to the number of bays, to 110, with 25 % of the vehicles overstaying. "
               f"The clearest result is the price of the buffer. At 100 vehicles, which produce {n100('static_0', 'requests'):.0f} requests per run, a location with no buffer refuses {n100('static_0', 'no_reservation'):.0f} of them for lack of space, a buffer of 1 refuses {n100('static_1', 'no_reservation'):.0f}, "
               f"a buffer of 3 refuses {n100('static_3', 'no_reservation'):.0f}, the paper's dynamic rule {n100('dynamic_paper', 'no_reservation'):.0f}, and the dynamic rule as ParkSure ships it **{n100('dynamic_parksure', 'no_reservation'):.0f}**. "
               f"The shipped rule grows the buffer on every on-time checkout, and most checkouts are on time, so the buffer quickly reaches its maximum of 5 and half of each ten-bay area is held back; its share of requests that end with a parked car is {n100('dynamic_parksure', 'success_rate') * 100:.1f} %, "
               f"against {n100('static_0', 'success_rate') * 100:.1f} % with no buffer."),
             TAB("Outcomes per run, 25 % bad vehicles, mean of 30 runs (requests = vehicles x 10).", HEAD, _pol_rows(F.POP, lambda k, s: (lambda m: F.pop(k, s, m)), [80, 100, 110], lambda k: str(k)),
                 widths=[0.45, 1.1, 0.55, 0.6, 0.6, 0.5, 0.6, 0.5, 0.5, 0.5], align=["c", "l", "c", "c", "c", "c", "c", "c", "c", "c"], size=8),
             ] + G("f01_buffer_population.png", "Refused requests, arrivals with no bay and success rate against the number of vehicles for the five buffer policies (25 % bad vehicles, 30 runs per point).", 6.0) +
            [P(f"The benefit of a buffer is hard to see. 'No park' stays at or below {max(F.pop(n, s, 'no_park') for n in (80, 90, 100, 110) for s in F.STRATS):.1f} events per run in every policy and population, "
               f"because an arriving driver who finds the area full is moved to the nearest alternate: with no buffer and 110 vehicles {F.pop(110, 'static_0', 'moved_to_alternate'):.1f} drivers per run are moved, and in {F.pop(110, 'static_0', 'alt_overflow'):.1f} of those moves the alternate was itself full. "
               f"A buffer of 3 removes the moves almost completely ({F.pop(110, 'static_3', 'moved_to_alternate'):.2f} per run) at the cost of {F.pop(110, 'static_3', 'no_reservation'):.0f} refused requests, against {F.pop(110, 'static_0', 'no_reservation'):.0f} with none. "
               f"Utilisation falls as the buffer grows, from {F.pop(110, 'static_0', 'utilisation') * 100:.1f} % with no buffer to {F.pop(110, 'dynamic_parksure', 'utilisation') * 100:.1f} % with the shipped dynamic rule at 110 vehicles."),
             ])


def _badshare():
    sel = [0.25, 0.50]
    return ([H2("8.4 Buffer policies against the share of overstaying vehicles"),
             P(f"The table and figure below keep the population random between 80 and 110 and raise the share of vehicles that overstay from 25 % to 50 %. "
               f"For a location with no buffer the number of arrivals that find no bay rises with the share of bad vehicles: 'no park' plus 'alternate full' goes from {F.bad(0.25, 'static_0', 'no_park') + F.bad(0.25, 'static_0', 'alt_overflow'):.2f} to {F.bad(0.5, 'static_0', 'no_park') + F.bad(0.5, 'static_0', 'alt_overflow'):.2f} events per run. "
               f"A buffer holds it down: static 3 stays at {F.bad(0.5, 'static_3', 'no_park') + F.bad(0.5, 'static_3', 'alt_overflow'):.2f} at 50 %. The shipped dynamic rule ends at {F.bad(0.5, 'dynamic_parksure', 'no_park') + F.bad(0.5, 'dynamic_parksure', 'alt_overflow'):.2f} and the paper's rule at {F.bad(0.5, 'dynamic_paper', 'no_park') + F.bad(0.5, 'dynamic_paper', 'alt_overflow'):.2f}, "
               "so neither dynamic rule does better than a fixed buffer of 3 on this measure, and both refuse more requests than a buffer of 1."),
             TAB("Outcomes per run against the share of bad vehicles (population 80 to 110, mean of 30 runs).", HEAD,
                 _pol_rows(F.BAD, lambda k, s: (lambda m: F.bad(k, s, m)), sel, lambda k: f"{int(k * 100)} %"),
                 widths=[0.45, 1.1, 0.55, 0.6, 0.6, 0.5, 0.6, 0.5, 0.5, 0.5], align=["c", "l", "c", "c", "c", "c", "c", "c", "c", "c"], size=8),
             ] + G("f02_buffer_badshare.png", "Refused requests, arrivals with no bay and Trust Score lockouts against the share of overstaying vehicles (population 80 to 110, 30 runs per point).", 6.0) +
            [P(f"Panel (a) of the figure shows a pattern that the reservation paper also noticed in its own results {N('cabri')}: the number of refused reservations of the shipped dynamic rule falls as more vehicles misbehave, from {F.bad(0.25, 'dynamic_parksure', 'no_reservation'):.0f} to {F.bad(0.5, 'dynamic_parksure', 'no_reservation'):.0f}. "
               f"The paper put this down to fewer requests being generated when vehicles stay longer. In this simulator the number of requests is fixed, so the explanation is different and can be read from panel (c): suspended drivers stop requesting, and the number of requests refused by the Trust lockout rises from {F.bad(0.25, 'dynamic_parksure', 'suspended'):.0f} to {F.bad(0.5, 'dynamic_parksure', 'suspended'):.0f}. "
               "A fall in refusals therefore does not mean that the admission policy has improved."),
             ] + G("f03_arrival_outcomes.png", "What happens at the gate when half of the drivers overstay: no park, alternate physically full, and moved to the alternate, per run for each policy.", 5.0))


def _trust():
    td = F.TD
    rows = [[p, f"{r['mean_final_trust']:.2f}", f"{r['std_final_trust']:.2f}", f"{r['mean_fee_multiplier']:.2f}", f"{r['share_ever_suspended'] * 100:.0f} %", "none" if r["median_first_suspension_session"] is None else str(r["median_first_suspension_session"])]
            for p, r in td.items()]
    return ([H2("8.5 Effect of the Trust Score system"),
             P(f"The Trust Score has two effects in the simulation. It lowers the fee multiplier of punctual drivers and raises it for late ones, and it locks out drivers whose score falls below 1.5 after a recent warning. "
               f"The ablation below switches the lockout off: with the Trust Score switched off, the share of requests that end with a parked car at 50 % bad vehicles is {F.abl(0.5, False, 'static_0', 'success_rate') * 100:.1f} % for a static buffer of 0, against {F.abl(0.5, True, 'static_0', 'success_rate') * 100:.1f} % with it on, "
               f"and for the shipped dynamic rule {F.abl(0.5, False, 'dynamic_parksure', 'success_rate') * 100:.1f} % against {F.abl(0.5, True, 'dynamic_parksure', 'success_rate') * 100:.1f} %. "
               f"The lockout is the largest source of refused requests at 50 % bad vehicles: for a static buffer of 0 {F.bad(0.5, 'static_0', 'suspended'):.0f} of {F.bad(0.5, 'static_0', 'requests'):.0f} requests per run are refused because the driver is suspended. "
               "The cause is in the engine: once the score is below 1.5, every request while the last warning is less than 14 days old re-applies the 24-hour pause, so a suspended driver cannot book for at least 14 days, whereas the reservation paper bars one subsequent session."),
             ] + G("f07_trust_ablation.png", "Share of requests that end in a parked car with the Trust Score on (as shipped) and off, at 25 % and 50 % bad vehicles.", 5.8) +
            [P("The second table follows a single driver for 100 daily sessions, 200 simulated drivers per setting, when each session ends late with a fixed probability. A driver who is late one session in ten ends with a mean score of "
               f"{td['0.1']['mean_final_trust']:.2f} and is almost never suspended ({td['0.1']['share_ever_suspended'] * 100:.1f} %). At 30 % the mean score is {td['0.3']['mean_final_trust']:.2f}, the mean fee multiplier {td['0.3']['mean_fee_multiplier']:.2f}, and {td['0.3']['share_ever_suspended'] * 100:.0f} % of drivers are suspended at some point, the median at session {td['0.3']['median_first_suspension_session']}. "
               f"At 50 % the mean score is {td['0.5']['mean_final_trust']:.2f} and every driver is suspended, the median at session {td['0.5']['median_first_suspension_session']}. The score separates punctual from unpunctual drivers clearly; whether a 14-day lockout is the right penalty is a policy question that these data cannot answer."),
             TAB("Trust Score outcome after 100 daily sessions against the probability of a late checkout (200 drivers per setting).",
                 ["Late probability", "Mean final score", "Std", "Mean fee multiplier", "Ever suspended", "Median first suspension (session)"], rows,
                 widths=[1.0, 1.1, 0.7, 1.2, 1.1, 1.4], align=["c", "c", "c", "c", "c", "c"], size=9.5),
             ] + G("f04_trust_dynamics.png", "Final Trust Score, share of drivers ever suspended and mean fee multiplier against the probability of a late checkout.", 5.6))


def _seeded():
    t = F.SEED["insights_60d"]["totals"]
    old = [p for p in F.SEED["insights_60d"]["per_location"] if p["location"] == "Old Town Deck"][0]
    return ([H2("8.6 Strategy Insights on the seeded history"),
             P(f"The administrator's Strategy Insights page replays the stored booking history deterministically under four buffer settings and counts the requests that would have been unable to park or declined. On the seeded 60-day history ({F.SEED['reservations']} reservations) the totals are: "
               f"no buffer {t['fixed_0']['unable_to_park']} unable to park and {t['fixed_0']['declined']} declined; a fixed buffer of 1, {t['fixed_1']['unable_to_park']} and {t['fixed_1']['declined']}; a fixed buffer of 3, {t['fixed_3']['unable_to_park']} and {t['fixed_3']['declined']}; and the dynamic policy, {t['dynamic']['unable_to_park']} and {t['dynamic']['declined']}. "
               f"The same ordering as in Sections 8.3 and 8.4 appears: each step towards a larger buffer removes the failures at arrival and adds refusals at booking, and the dynamic policy, which grows its buffer fastest, refuses the most. "
               f"Almost all of the difference comes from one location, Old Town Deck (8 bays, {old['requests']} requests in the window), where the seeded Friday peaks oversubscribe the bays; the actual history shows {old['actual']['unable_to_park']} unable to park and {old['actual']['declined']} declined there, against {old['simulated']['dynamic']['unable_to_park']} and {old['simulated']['dynamic']['declined']} under the dynamic policy. "
               "Because the history is generated, these counts illustrate the mechanism and say nothing about real demand. They are also not a validation of the simulator: both use the same buffer rule."),
             ] + G("f06_seeded_insights.png", "Strategy Insights totals on the seeded 60-day history under four buffer policies (synthetic data).", 4.8))


def _response():
    return [H2("8.7 Response time and allocation efficiency"),
            P(f"Chapter 7 gives the full measurements. The figures that matter for the sixth objective are these. A driver's actions answer quickly on a single uvicorn process with a SQLite file: search {F.lat('GET /api/search'):.1f} ms, reservation {F.lat('POST /api/reservations'):.1f} ms, check-in {F.lat('POST /api/reservations/{id}/checkin'):.1f} ms and check-out {F.lat('POST /api/reservations/{id}/checkout'):.1f} ms on average. "
              f"Login takes {F.lat('POST /api/auth/login'):.0f} ms because of bcrypt. The admission decision takes {F.MB['forecast_free (admission, 100 bookings at the location)']['mean_ms']:.2f} ms in process, and the nearest-alternate search over 49 locations {F.MB['nearest_alternate over 49 other locations']['mean_ms']:.1f} ms. "
              f"Allocation efficiency, measured as bay utilisation in the simulation, is {F.pop(100, 'static_0', 'utilisation') * 100:.1f} % with no buffer and {F.pop(100, 'dynamic_parksure', 'utilisation') * 100:.1f} % with the shipped dynamic rule at 100 vehicles; "
              f"the booking success rate, the share of requests that end in a parked car, is {F.pop(100, 'static_0', 'success_rate') * 100:.1f} % and {F.pop(100, 'dynamic_parksure', 'success_rate') * 100:.1f} % for the same two policies. "
              f"Two defects belong with these results: one of ten concurrency trials sold the last bay twice, and the two list endpoints slow down as the number of stored rows grows.")]


def _base():
    c100 = lambda s, m: F.pop(100, s, m)  # noqa: E731
    return [H2("8.8 Comparison with the base papers"),
            P(f"Two papers are used as the base of this project, and neither can be compared with ParkSure on equal terms. The registered base paper {N('base')} (Jemmali et al.) solves a different problem: it balances the number of people across the parking spaces of a medical city using passenger counts, "
              "with six grouping-permutation heuristics evaluated on nine instance classes and 2,790 generated test cases. ParkSure implements none of those heuristics and makes no claim to match them. "
              f"The second paper {N('cabri')} (Cabri et al.) is the source of ParkSure's buffer and star-reputation ideas. It evaluates them only in a SUMO simulation with 80 spots in 8 areas, 80 to 110 vehicles, 25 to 50 % overstaying vehicles and 5 runs per setting, and presents its results as charts without a table of numbers. "
              "ParkSure's simulator re-creates that scenario but is not SUMO, uses assumed arrival times and runs the product's own rules, so a qualitative comparison is all that is meaningful."),
            TAB("Comparison of the setting and the findings.", ["Aspect", "Jemmali et al. [1]", "Cabri et al. [2]", "ParkSure (this work)"],
                [["Problem", "Allocate vehicles to parking spaces so that the number of people per space is balanced", "Keep a reserved bay available when earlier drivers overstay", "Reserve, pay and manage bays; keep bays available despite overstays"],
                 ["Method", "Four-stage grouping and six grouping-permutation heuristics", "Buffer of non-reservable slots (dynamic: grows on late departure) and 0-5 star reward system", "Same ideas implemented in a web product; buffer grows on on-time checkout; nearest-alternate move; fee multiplier; Strategy Insights"],
                 ["Evaluation setting", "2,790 generated instances in nine classes", "SUMO, 80 spots, 8 areas, 5 runs per setting", f"Own simulator, same sizes, {F.SEEDS} runs per setting; 70 tests; latency probes; seeded demo history"],
                 ["Reported result", "Best algorithm has the highest best-solution share (68.2 %); GVb matches or beats baseline MR on 55.4 % of instances; sub-millisecond", "Any buffer beats none; the dynamic buffer gives the best trade-off between failed parks and refused reservations (charts only)", "See the next two rows"],
                 ["Does a buffer reduce arrival failures?", "Not studied", "Yes: any buffer beats none", f"Yes, in the same direction: at 50 % bad vehicles 'no park' plus 'alternate full' is {F.bad(0.5, 'static_0', 'no_park') + F.bad(0.5, 'static_0', 'alt_overflow'):.2f} per run with no buffer and {F.bad(0.5, 'static_3', 'no_park') + F.bad(0.5, 'static_3', 'alt_overflow'):.2f} with a buffer of 3"],
                 ["Is the dynamic buffer the best trade-off?", "Not studied", "Yes", f"Not reproduced: at 100 vehicles the shipped rule refuses {c100('dynamic_parksure', 'no_reservation'):.0f} requests and the paper's rule {c100('dynamic_paper', 'no_reservation'):.0f}, against {c100('static_3', 'no_reservation'):.0f} for a fixed buffer of 3 that gives equal or fewer arrival failures"],
                 ["Execution time", "Sub-millisecond allocation", "Not reported", f"Admission decision {F.MB['forecast_free (admission, 100 bookings at the location)']['mean_ms']:.2f} ms; whole reservation call {F.lat('POST /api/reservations'):.1f} ms (different task)"]],
                widths=[1.2, 1.7, 1.7, 1.9], align=["l", "l", "l", "l"], size=8.5),
            P("The differences in setting limit the comparison. The reservation paper's vehicles are all equipped and enter through barriers, and its reward system bars a driver for one subsequent session; ParkSure has no barriers and its lockout lasts at least 14 days. "
              "The paper raises the buffer when a vehicle leaves late, ParkSure's code when it leaves on time, and the simulation shows that this choice is the main reason the shipped rule refuses so many requests. "
              "The paper's rule, run in the same simulator, refuses far fewer, but still does not beat a fixed buffer of 3 on the measures used here. Because the simulator is not SUMO and its arrival process is assumed, this is not a refutation of the paper: "
              "its claim that the dynamic buffer is the best trade-off could not be reproduced for either dynamic rule, and the shipped rule is the more conservative of the two.")]


def _samples():
    search = {"id": 5, "name": "Old Town Deck", "address": "3 Heritage Lane", "latitude": 12.96, "longitude": 77.585, "capacity": 8, "buffer_size": 1,
              "price_per_hour": 2.0, "overlapping": 0, "bookable": 7, "available": True}
    reserve = {"id": 348, "location_id": 5, "location_name": "Old Town Deck", "start_time": "2026-10-28T08:28:42+00:00", "end_time": "2026-10-28T10:28:42+00:00",
               "status": "reserved", "fee": 3.8, "fee_multiplier": 0.95, "payment_status": "pending", "payment_provider": "demo", "credit_applied": 0.0, "amount_due": 3.8,
               "checkout": {"url": "/api/payments/demo-confirm?session_id=demo_41cedf3d3d25&reservation_id=348", "session_id": "demo_41cedf3d3d25", "provider": "demo"}}
    dump = lambda o: json.dumps(o, indent=2)  # noqa: E731
    return [H2("8.9 Sample inputs and outputs"),
            P("The following requests and responses were captured from the running application on a seeded database (long fields shortened, and the `checked_in_at`, `checked_out_at`, `decline_reason` and `parent_id` fields of a new booking, which are empty, omitted). "
              "The driver is the demo driver with trust score 4, so the fee carries the multiplier 0.95: two hours at $2.00 per hour is $4.00, and $4.00 x 0.95 = $3.80."),
            H3("8.9.1 Availability search"),
            CODE("GET /api/search?start_time=2026-10-28T08:28:42+00:00&end_time=2026-10-28T10:28:42+00:00\n\n# one element of the answer\n" + dump(search), 8),
            P("Old Town Deck has 8 bays and a buffer of 1, and no booking overlaps the window, so 8 - 1 - 0 = 7 bays can be reserved."),
            H3("8.9.2 Successful reservation"),
            CODE("POST /api/reservations\n{\"location_id\": 5, \"start_time\": \"2026-10-28T08:28:42+00:00\", \"end_time\": \"2026-10-28T10:28:42+00:00\"}\n\n# 200 OK\n" + dump(reserve), 8),
            H3("8.9.3 Refused reservation"),
            CODE("POST /api/reservations   (the same window, after seven bookings)\n\n# 409 Conflict\n{\"detail\": \"Old Town Deck is fully reserved for the requested window (capacity 8, hold-back buffer 1). Please try another time or location.\"}", 8),
            P("The refused request is stored as a declined booking with this reason, so the administrator's overview counts it. A reversed time window answers 422 and a wrong password 401 with the detail *Incorrect email or password*."),
            H3("8.9.4 Check-out, check-in and Strategy Insights"),
            P("Check-out answers with `on_time` true and the message *Checked out on time. Thank you!* within 10 minutes after the booked end, and otherwise with `on_time` false and a message that the checkout was recorded as an overstay. "
              "A check-in at a full location answers with `moved` true, the distance and the alternate, for example *Kiosk Bay was full on arrival. We moved you to Central Station Garage, 0.1 km away.* (Section 8.2.3), or with `failed` true and the fee credited when no alternate exists. "
              "`GET /api/admin/insights` answers with the four strategies and the policy `{init: 1, max: 5, reset_hours: 24}`; its totals on the seeded history are in Section 8.6.")]


def _analysis():
    return [H2("8.10 Success and failure analysis"),
            H3("8.10.1 Where the product succeeds"),
            B("Every flow a driver needs works end to end: search, reserve, pay in demo mode, check in, check out, cancel with an automatic credit, and the Trust Score page (Section 8.2).",
              f"The rules are exact and tested: {F.PYTEST_TOTAL} tests and {F.SMOKE_TOTAL} smoke checks pass, and the simulator agrees with the engine on {F.PAR['total_cases']:,} decisions.",
              "A driver who finds a location full is moved to the nearest alternate or has the fee credited automatically (Section 8.2.3), and the administrator's replay of the stored history is deterministic."),
            H3("8.10.2 Where it falls short"),
            B(f"**The shipped dynamic buffer is the most conservative policy tested.** At 100 vehicles it refuses {F.pop(100, 'dynamic_parksure', 'no_reservation'):.0f} of {F.pop(100, 'dynamic_parksure', 'requests'):.0f} requests and leaves {F.pop(100, 'dynamic_parksure', 'utilisation') * 100:.1f} % utilisation, with little extra protection against arrival failures compared with a fixed buffer of 3.",
              "**The Trust lockout is harsh.** Because the pause is re-applied at every refused request, a driver below 1.5 with a warning in the last 14 days cannot book for at least 14 days; in the simulation it refuses more requests than the admission rule does for every fixed-buffer policy at 25 % bad vehicles and for every policy at 50 %.",
              f"**A bay can be sold twice under simultaneous requests**: {F.RACE['trials_with_overbooking']} of {F.RACE['trials']} trials of the concurrency probe accepted two bookings for one bookable bay.",
              "**The alternate move does not check the alternate's physical bays**, so a driver can be sent to a location that is also full; the simulation counts these moves as 'alternate full', up to 2.9 per run at 50 % bad vehicles with no buffer.",
              "**Payment is only as secure as its demo path.** An unauthenticated route marks any booking paid, and the default signing secret accepts a forged administrator token. Both are documented in Chapter 7.",
              f"**Two list endpoints are slow**: the user's bookings ({F.lat('GET /api/reservations'):.0f} ms) and the administrator's bookings ({F.lat('GET /api/admin/bookings'):.0f} ms) issue extra queries for every row.",
              "**Past start times and early check-ins are accepted** (Chapter 7).")]


def _limits():
    return [H2("8.11 Limitations of the evaluation"),
            B("All application data are synthetic, generated by the product's own seed; no real parking lot, driver or payment is involved.",
              "The buffer comparison is a simulation with assumed arrival, lead-time and gap distributions, a fixed one-hour overstay and perfect check-in on time; it is not SUMO and not the paper's exact scenario.",
              f"Each cell is the mean of {F.SEEDS} runs of one scenario family; the spread between runs is stored in the metrics files but a significance test was not carried out.",
              "The simulator mirrors the product's rules but not its timing details: the buffer reset in the product runs on a 30-minute schedule, in the simulator at the next event.",
              "Latency was measured on one machine with the client and server together, over the loopback address, with at most 8 client threads and a SQLite file.",
              "No user study was run, so no claim is made about ease of use or driver acceptance of the Trust Score pricing.",
              "Stripe was not configured; real Checkout, webhooks and refunds were not exercised.")]


def _objectives():
    rows = [["1. User registration, authentication and vehicle profile management", "Partly achieved", "Registration, login, JWT roles and account credit work and are tested; **there is no vehicle profile** (no plate or vehicle details are stored)"],
            ["2. Real-time slot availability across registered facilities", "Achieved as forecast", f"Search returns bookable bays per location and window (capacity - buffer - overlapping bookings), {F.lat('GET /api/search'):.1f} ms; no sensor feed, so occupancy is booked, not measured"],
            ["3. Slot search, advance reservation and cancellation", "Achieved", "Tested by API tests and the smoke script; cancellation refunds a paid fee to account credit; one concurrency race was found"],
            ["4. Secure online payment and digital receipts", "Partly achieved", "Stripe Checkout in test mode with a demo fallback; payment state is stored; **no downloadable receipt**; unauthenticated demo-confirm route and default JWT secret weaken the security claim"],
            ["5. Administrator dashboard for slots, bookings, occupancy and revenue", "Achieved", "Overview, locations, bookings, users and Strategy Insights pages (Section 8.2.4); occupancy shown is forecast, not live"],
            ["6. Evaluate booking success rate, allocation efficiency and system response time", "Achieved on simulated and synthetic data", f"Success rate and utilisation from {F.SEEDS}-run simulations (Sections 8.3 to 8.5); response times from 200-call probes (Chapter 7); no real-user data"]]
    return [H2("8.12 Objectives versus outcomes"),
            TAB("The six project objectives against what was measured.", ["Objective", "Status", "Evidence"], rows, widths=[2.2, 1.1, 3.2], align=["l", "l", "l"], size=9.5)]


def _summary():
    return [H2("8.13 Summary of findings"),
            B(f"ParkSure runs as a complete reservation platform: 22 routes, 5 tables, 24 captured screens, {F.PYTEST_TOTAL} passing tests and {F.SMOKE_TOTAL} passing smoke checks; the driver's one-click actions answer in {F.lat('GET /api/search'):.0f} to {F.lat('POST /api/reservations'):.0f} ms on average.",
              f"A hold-back buffer reduces arrival failures and alternate moves but costs refused reservations and utilisation; at 100 vehicles refusals rise from {F.pop(100, 'static_0', 'no_reservation'):.0f} (no buffer) to {F.pop(100, 'static_3', 'no_reservation'):.0f} (buffer 3).",
              f"The dynamic buffer as shipped (+1 on every on-time checkout) is the most conservative policy ({F.pop(100, 'dynamic_parksure', 'no_reservation'):.0f} refusals at 100 vehicles); the paper's rule (+1 on late departure) refuses {F.pop(100, 'dynamic_paper', 'no_reservation'):.0f}. Neither beats a fixed buffer of 3 on arrival failures, so the claim that the dynamic buffer is the best trade-off was not reproduced.",
              "'No park' events are rare in every policy because the nearest-alternate move absorbs overflow; the hidden cost is moves to alternates that are themselves full.",
              "The Trust Score separates punctual from late drivers, but its lockout of at least 14 days is the largest source of refused requests when half of the drivers overstay.",
              "The team's own probes found a concurrency race, an unauthenticated payment confirmation, a default signing secret and two slow list endpoints; none was fixed during the documentation run.",
              "Objectives 1 and 4 are only partly met (no vehicle profile, no receipt); the others are met on synthetic data and simulation. No real drivers, real money or SUMO runs were involved.")]


def blocks():
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    b += _setup() + _screens() + _population() + _badshare() + _trust() + _seeded() + _response() + _base() + _samples() + _analysis() + _limits() + _objectives() + _summary()
    return b
