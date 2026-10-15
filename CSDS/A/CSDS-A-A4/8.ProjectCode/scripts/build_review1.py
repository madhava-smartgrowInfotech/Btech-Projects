"""Build 7.Review_1_PPT.pptx from D:\\abstracts\\Templates\\Review_1_PPT.pptx (16 slides)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (fill, put_picture, replace_chart, replace_everywhere, set_notes, set_paras, set_table, shape, style_chart, table_size)  # noqa: E402
from doc_common import (BATCH, COLLEGE, DEPT, DIAG, GUIDE, GUIDE_DESIG, M, P, PRODUCT, REFERENCES, ROL, STUDENTS, TITLE, YEAR)  # noqa: E402
from pptx import Presentation  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_1_PPT.pptx"
OUT = BATCH / "7.Review_1_PPT.pptx"
BASE = REFERENCES[0]


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    replace_everywhere(prs, {"The Hidden Risk of Social Media": PRODUCT})
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Review 1", TITLE, "Batch A4", "hub location, matheuristic, random forest, e-commerce logistics"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A4"

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    set_paras(shape(s, 3), TITLE, 22)
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  Batch A4 (CSE-DS, Section A)  \u00b7  {YEAR}"], 13)
    set_notes(s, "Review 1 covers problem identification and research for HubOptima: forecast-driven hub location for e-commerce logistics.")

    set_notes(S[1], "Nine parts: the abstract, the base paper, the literature survey, existing approaches, the gap, the problem and objectives, the approach, expected outcomes and references.")

    # 3 abstract
    s = S[2]
    set_paras(shape(s, 2), "Abstract: put hubs where tomorrow's orders will be")
    fill(s, 8, "E-commerce networks route parcels through hubs, so hub placement drives cost and delivery time. Classical hub location models assume a fixed demand, but real demand moves between regions and seasons, and exact solvers slow down on large networks.", 16)
    fill(s, 13, "Predict, then optimise: a Random Forest forecasts regional demand from order history, and a matheuristic (exact MIP sub-problems inside a heuristic search) chooses the hubs for the forecast, then re-plans each month.", 16)
    fill(s, 18, "A FastAPI + React application: forecast, plan hubs on a map, compare with traditional methods, benchmark scalability and re-optimise as demand changes.", 16)
    set_notes(s, "The abstract in one slide: fixed-demand models and slow exact solvers are the problem; forecasting plus a matheuristic is the idea; a web application is the deliverable.")

    # 4 base paper
    s = S[3]
    fill(s, 5, BASE, 13)
    set_paras(shape(s, 7), "Method")
    fill(s, 8, "A Random Forest forecasts demand from historical data; a matheuristic (a relaxed MILP for a starting solution, then Variable Neighbourhood Search) selects hubs; forecasts are fed back to re-optimise; the result is validated on peak, spike and disruption scenarios.", 15)
    set_paras(shape(s, 10), "Data and reported results")
    fill(s, 11, "Proprietary data of a global transport company (two years). Reported: delivery-time compliance 92.3%, fulfilment 97.6%, robustness 0.87; +7.8% / +9.4% / +16% over traditional methods; networks of 50-500 nodes.", 15)
    set_paras(shape(s, 13), "Limitations stated by the authors")
    fill(s, 14, "Sector-specific data, scalability not extensively tested, a snapshot of conditions, other ML models not explored, offline evaluation only. The paper gives the Random Forest gain only as 'X %'.", 15)
    set_notes(s, "The base paper is a framework paper with results on private data. Its numbers cannot be reproduced here, so we compare directions, not values.")

    # 5 literature survey
    s = S[4]
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Danach et al., 2025 [1] (base)", "Random Forest forecast + matheuristic (MILP + VNS)", "Proprietary logistics data", "Compliance 92.3%, fulfilment 97.6%, robustness 0.87"],
            ["Zheng et al., 2024 [2]", "Diversity-based hybrid PSO for drone hub location", "Village delivery scenario", "42.58% efficiency gain (abstract)"],
            ["Yang et al., 2023 [3]", "Maximal-detour liner hub location; MILP + Benders decomposition", "Liner shipping networks", "Detour limits modelled; faster exact solve"],
            ["Dehghan Chenary et al., 2024 [4]", "Bi-objective mobile hubs with congestion; Pareto clustering metaheuristic", "Australian Post dataset", "Better Pareto sets than MOPSO, NSGA-II"],
            ["Zhang et al., 2025 [5]", "Two-stage adaptive robust hub location (C&CG + Benders)", "Not stated in abstract", "Better out-of-sample than stochastic model"],
            ["Danach et al., 2019 [9]", "Capacitated p-hub location-routing: Lagrangian + hyper-heuristic", "Not reviewed", "Described in [1]"],
            ["O'Kelly 1986; Campbell et al. 2002; Ernst and Krishnamoorthy 1996 [6]-[8]", "Foundations: single-allocation p-hub models and exact algorithms", "Classical benchmarks", "Foundations of the model"]]
    sz = table_size(rows, 1164, 460, [0.26, 0.34, 0.18, 0.22], 13, 9)
    set_table(shape(s, 6), rows, sz, header_size=sz)
    set_notes(s, "Five works come from the batch survey; the foundations are the classical references the base paper cites. We summarise only what the abstracts state.")

    # 6 supporting evidence
    s = S[5]
    set_paras(shape(s, 2), "Evidence: a fixed plan fails when demand moves")
    cats = [t["period"][2:] for t in ROL["timeline"]]
    ch = replace_chart(s, 4, cats, [("Static plan (fixed on historical average)", [round(t["static"]["fulfilment_rate"] * 100, 1) for t in ROL["timeline"]]),
                                    ("Plan re-made each month from a forecast", [round(t["adaptive"]["fulfilment_rate"] * 100, 1) for t in ROL["timeline"]])], number_format="0.0")
    style_chart(ch, "Simulated fulfilment (%) by month, Jul-Dec 2025", ["D9534F", "4B46C8"], number_format="0.0", axis_title="fulfilment (%)", label_pt=8)
    set_paras(shape(s, 8), "Takeaway")
    fill(s, 9, "In the October 2025 festival peak a plan fixed on the historical average served only 64.9% of orders; re-planning from a forecast served 92.4%. Averaged over six months: 83.7% against 98.3%.", 15)
    set_paras(shape(s, 13), "Caveat")
    fill(s, 14, "Our own measurement on synthetic data (a simulation of fulfilment, not observed deliveries). The base paper reports no comparable figure.", 15)
    set_notes(s, "This slide is our own evidence for the problem: the static plan is a deliberately simple control, and the numbers come from the rolling-horizon experiment of this project.")

    # 7 existing system
    s = S[6]
    set_paras(shape(s, 2), "Existing system and current approaches")
    steps = ["Order history", "Demand forecast (separate)", "Fix demand to an average", "Solve hub model once", "Open hubs", "Revisit rarely"]
    for sid, t in zip((5, 8, 11, 14, 17, 20), steps):
        fill(s, sid, t, 13)
    set_paras(shape(s, 24), "Exact and rule-based planning")
    fill(s, 25, "Analysts solve a mixed-integer hub model once for a fixed demand, or managers put hubs at the largest markets. Exact models slow down as the network grows; rules give no quality guarantee.", 15)
    set_paras(shape(s, 29), "Heuristics")
    fill(s, 30, "Greedy and clustering heuristics are fast but give no guarantee, and the forecasting team and the network-design team usually work separately.", 15)
    set_notes(s, "How hub networks are planned today: fixed demand, exact models or rules, and forecasting disconnected from location decisions.")

    # 8 limitations
    s = S[7]
    set_paras(shape(s, 2), "Limitations of existing methods")
    for tid, bid, ttl, body in [
        (7, 8, "Fixed demand", "A plan on the historical average served 66.0% of October 2025 orders in our test."),
        (12, 13, "Slow exact solving", "The exact MIP did not finish a 270-node network within 67 s in our benchmark."),
        (17, 18, "No quality guarantee", "A greedy plan cost 11.5% more than the optimised plan on the same instance."),
        (22, 23, "Disconnected steps", "Forecasting and hub choice are separate, so plans are not updated when demand moves.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Four limitations, each illustrated with a measurement from this project.")

    # 9 research gap
    s = S[8]
    gaps = [("Fixed demand", "Most hub location studies assume known or assumed demand [2]-[5], [8], [9]."),
            ("Reproducibility", "The base paper's data, code and matheuristic parameters are not available [1]."),
            ("Forecast error", "The effect of forecast error on the hub plan is not shown."),
            ("Value of re-planning", "No evidence of what monthly re-optimisation is worth against a static plan."),
            ("Scale", "Exact versus matheuristic behaviour is described but not measured as networks grow.")]
    for (lid, tid), (lab, txt) in zip([(5, 6), (8, 9), (11, 12), (14, 15), (17, 18)], gaps):
        set_paras(shape(s, lid), lab)
        fill(s, tid, txt, 17)
    set_notes(s, "The gap: fixed-demand models, no open reproducible implementation, no measure of forecast-error effects, and little evidence on re-planning and scale.")

    # 10 problem statement
    s = S[9]
    fill(s, 5, "Given a history of monthly orders for demand regions, candidate hub sites with fixed costs and capacities, and cost and service parameters, choose which hubs to open and which hub serves each region so that total cost is minimised, every region has one hub, no hub exceeds its capacity, and the plan stays good as demand changes month to month.", 21)
    set_paras(shape(s, 8), "Order history, regions, costs, SLA")
    set_paras(shape(s, 11), "Hubs, allocation, KPIs, comparison")
    set_paras(shape(s, 14), "Re-plan each month as demand moves")
    set_notes(s, "The problem statement: inputs are the order history and the cost parameters; outputs are hubs and allocations with KPIs; the extra requirement is adaptation.")

    # 11 objectives
    s = S[10]
    fill(s, 4, ["Collect and preprocess historical e-commerce logistics data.",
                "Predict regional demand using a Random Forest model.",
                "Formulate hub location as an optimisation problem with cost, time and capacity constraints.",
                "Solve the problem efficiently with a matheuristic approach.",
                "Re-optimise hub configurations as demand changes.",
                "Compare performance with traditional hub location methods."], 20, bullet=True)
    set_notes(s, "The six objectives of the project.")

    # 12 proposed approach
    s = S[11]
    for tid, bid, ttl, body in [
        (7, 8, "Data and forecast", "Clean 36 months of orders for 90 regions; Random Forest with 19 lag, rolling, calendar and region features."),
        (12, 13, "Hub model", "Capacitated single-allocation MIP: fixed hub cost, transport cost, delivery-time penalty, capacity, p hubs."),
        (17, 18, "Matheuristic", "Greedy construction, swap/drop/add local search priced by exact assignment MIPs, kernel search."),
        (22, 23, "Evaluate and adapt", "Score plans on realised demand; compare five baselines; re-plan monthly.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 14)
    set_paras(shape(s, 27), "Web application")
    fill(s, 28, "FastAPI (14 endpoints) + React: forecast, plan with a network map, compare methods, scalability benchmark and rolling re-optimisation.", 16)
    set_notes(s, "The approach: forecast, model, matheuristic, evaluation, and a web application around them.")

    # 13 architecture
    s = S[12]
    put_picture(s, DIAG / "01_system_architecture.png", (215, 118, 790, 482), remove_ids=(4,), name="System architecture diagram")
    set_paras(shape(s, 5), "Proposed architecture: React frontend, FastAPI layer, hublocator core (forecast, MIP, matheuristic), files")
    set_notes(s, "Browser to React to FastAPI to the core package; storage is plain CSV, joblib and JSON files.")

    # 14 expected outcomes
    s = S[13]
    for tid, bid, ttl, body in [
        (7, 8, "Accurate forecast", "A Random Forest clearly better than naive forecasters on held-out months."),
        (12, 13, "Good plans fast", "Plans within seconds that match or approach the exact optimum."),
        (17, 18, "Lower cost", "Cost below greedy, clustering and managerial rules on the same instance."),
        (22, 23, "Adaptive network", "Higher fulfilment than a static plan as demand changes."),
        (27, 28, "Usable tool", "Maps, tables and comparisons a planner can read without code."),
        (32, 33, "Honest evaluation", "Synthetic-data limits and the base-paper gaps stated plainly.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Expected outcomes are targets at this stage and are measured in the later reviews.")

    # 15 references
    s = S[14]
    fill(s, 4, [f"[{i}] {r}" for i, r in enumerate(REFERENCES[:10], 1)], 13, min_pt=8.5, bullet=True, gap_pt=3)
    set_notes(s, "References [1] to [10]; the full list is in the report.")

    set_notes(S[15], "Thank you. Questions are welcome.")
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
