"""Chapter 1 sections (introduction, scope, contributions, limitations) - shared by the chapter documents and the full report."""
from __future__ import annotations

from doc_common import (B1, B3, CMP, DEM, FM, M, P, REG, RF, ROL, SCAL, R_BASE, R_BREIMAN, R_MATH, R_OKELLY, R_CAMP, R_ZHANG, inr_m, pct)

TOTAL_ORDERS = int(DEM.orders.sum())
GREEDY_GAP = M["greedy"]["cost_vs_proposed_pct"]
KM_GAP = M["kmeans"]["cost_vs_proposed_pct"]
LG_GAP = M["largest"]["cost_vs_proposed_pct"]
FX_GAP = M["fixed_avg"]["cost_vs_proposed_pct"]
AD, ST = ROL["adaptive_avg"], ROL["static_avg"]


def sec_domain(d):
    d.h2("Domain and Background")
    d.paras(
        "Electronic commerce has changed what customers expect from a delivery network. Orders are placed at any hour, from any town, and are "
        "expected to arrive within a promised window. Behind that promise sits a physical network of warehouses, sorting centres and "
        "transport links. The nodes at which parcels are consolidated, sorted and re-dispatched are called *hubs*, and deciding where to "
        f"open them is the classical **Hub Location Problem** (HLP) of operations research [{R_OKELLY}], [{R_CAMP}].",
        "A hub-and-spoke design lets a carrier combine many small flows into fewer, larger shipments, which lowers the cost per parcel. The "
        "price is that every parcel travels to a hub before reaching its destination, so a badly placed hub adds distance, time and cost. "
        "Hub placement is therefore a trade-off between fixed cost (each hub must be built, staffed and run every month), transport cost "
        "(distance travelled by the parcels) and service quality (how long deliveries take and how many orders the hub can actually process).",
        "Two properties make the problem hard in practice. First, it is combinatorial: with 90 candidate sites there are billions of ways to "
        "choose six hubs, and every region must also be allocated to exactly one of them. Exact mixed-integer programming (MIP) solves small "
        "instances well but its running time grows quickly with the number of demand points. Second, the input is not fixed: e-commerce "
        "demand grows, peaks in festival months and shifts between regions, so a plan computed once on last year's average can be wrong by "
        "the time it is used.")
    d.h3("Predict, then optimise")
    d.p("The base paper [1] proposes to join two well-known tools: a machine-learning forecaster that predicts regional demand from "
        "historical orders, and a matheuristic, a heuristic search that calls exact mathematical-programming solvers on small sub-problems, "
        "that chooses the hubs for the forecast demand. The forecast replaces the fixed-demand assumption; the matheuristic replaces the "
        "slow exact solver. This project implements that predict-then-optimise loop end to end and measures it.")


def sec_motivation(d):
    d.h2("Motivation")
    d.paras(
        "Three observations motivated the work. First, the cost of a poor hub decision is paid every month, so even single-digit percentage "
        f"differences matter: on the October 2025 test the cheapest traditional heuristic costs {inr_m(M['kmeans']['total_cost'] - P['total_cost'])} "
        f"more per month than the proposed plan ({KM_GAP:.1f}% more) and the managerial 'largest markets' rule costs "
        f"{inr_m(M['largest']['total_cost'] - P['total_cost'])} more ({LG_GAP:.1f}% more), in the model's own units.",
        "Second, the demand a plan is built for is rarely the demand that arrives. In the October 2025 festival peak the network received "
        f"{CMP['realized_total_demand']:,} orders against a forecast of {CMP['forecast_total_demand']:,}; a plan that ignores forecasting "
        f"and uses the historical average serves only {pct(M['fixed_avg']['fulfilment_rate'])} of the realised orders in the same test.",
        "Third, the people who plan networks need to see the effect of their choices. A command-line research script is hard to hand to a "
        "logistics planner, so the project wraps the pipeline in a web application that shows forecasts, plans on a map, comparisons and "
        "the month-by-month behaviour of the network.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.p("Given a history of monthly orders for a set of demand regions, a set of candidate hub sites with fixed costs and capacities, and "
        "parameters for transport cost, delivery time and service level, choose which hubs to open and which hub serves each region so "
        "that total monthly cost is minimised, every region is served by exactly one hub, no hub exceeds its capacity, and the plan remains "
        "good as demand changes from month to month.")
    d.bullets([
        "Poor hub placement increases transportation cost and delays deliveries.",
        "Traditional hub location models assume fixed demand and ignore fluctuations.",
        "Exact optimisation is too slow for large, changing logistics networks.",
        "Forecasting and optimisation are usually done separately, which weakens hub decisions.",
    ])
    d.p("**Need.** A framework that feeds machine-learning demand forecasts directly into an efficient optimisation model, so hub choices "
        "adapt to changing demand, together with an honest measurement of what that adaptation buys.")


def sec_need(d):
    d.h2("Need for the System")
    d.bullets([
        "**Adaptation.** Plans must be re-computed as each new month of data arrives; doing this by hand is not realistic.",
        "**Speed.** A planner exploring 'what if we open one more hub?' needs an answer in seconds, not in the minutes an exact solver may need on a larger network.",
        "**Evidence.** The value of forecasting and of the matheuristic should be measured against the methods used today: exact MIP, greedy rules, clustering and managerial judgement.",
        "**Accessibility.** The same pipeline should be usable from a browser, with parameters, maps and tables, by someone who does not read Python.",
    ])


def sec_objectives(d):
    d.h2("Objectives")
    d.numbered([
        "Collect and preprocess historical e-commerce logistics data.",
        "Predict regional demand using a Random Forest model.",
        "Formulate hub location as an optimisation problem with cost, time and capacity constraints.",
        "Solve the problem efficiently with a matheuristic approach.",
        "Re-optimise hub configurations as demand changes.",
        "Compare performance with traditional hub location methods.",
    ])
    d.p("The status of each objective against the measured results is given in the Results chapter.")


def sec_scope(d):
    d.h2("Scope")
    d.h3("In scope")
    d.bullets([
        "A synthetic but realistic monthly demand history for 90 regions (30 Indian cities and 60 satellite districts) over 36 months, with growth, festival peaks, promotions and noise, and the preprocessing that a real file of the same schema would need.",
        "A Random Forest demand forecaster with lag, rolling, seasonal, promotion and region features, evaluated on a time-based hold-out of six months against two naive forecasters.",
        "A capacitated single-allocation hub location model with fixed hub cost, transport cost, a delivery-time penalty, hub capacity, a limit of p hubs and an optional hard service-level constraint.",
        "A matheuristic (greedy/k-medoids construction, MIP-priced local search, kernel search) and the exact MIP as the traditional reference.",
        "Four baseline methods: greedy heuristic, k-means clustering, a 'largest markets' rule and a planning-on-historical-average method with no forecast.",
        "A rolling-horizon simulation over six months and a scalability benchmark with 90, 180 and 270 demand points.",
        "A FastAPI service with 14 endpoints, a React web application with seven screens, and a command-line interface.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "Real company data. No real order history was available; all figures are produced on the synthetic data and must not be read as field measurements.",
        "Vehicle routing, multi-echelon networks, hub-to-hub flows and economies of scale between hubs (the model is single-allocation: each region is served by exactly one hub).",
        "Robust or stochastic optimisation and the 'network robustness' indicator reported by the base paper.",
        "Multiple capacity levels for a hub, capacity expansion over time and hub-disruption scenarios.",
        "Real-time data feeds, user accounts, authentication and multi-user deployment.",
        "Forecasting models other than the Random Forest (deep learning, gradient boosting) and hyper-parameter search.",
    ])


def sec_contrib(d):
    d.h2("Contributions")
    d.numbered([
        "**An end-to-end, reproducible implementation of predict-then-optimise** (data preparation, Random Forest forecast, capacitated hub MIP, matheuristic, KPI evaluation) in about 2,000 lines of Python, with a fixed random seed and saved models and results.",
        f"**A matheuristic with a screening bound.** Swap, drop and add moves are first screened with a cheap greedy cost bound and only the promising ones are priced by an exact assignment MIP; a kernel search then polishes the result. It matched the exact optimum on the 90- and 180-node instances (gap 0.00% and -0.05%) and ran in {SCAL[0]['matheuristic_seconds']:.1f} s and {SCAL[1]['matheuristic_seconds']:.1f} s against {SCAL[0]['exact_seconds']:.1f} s and {SCAL[1]['exact_seconds']:.1f} s for the exact MIP.",
        f"**A no-look-ahead evaluation protocol.** For a past month the forecaster sees only earlier data, plans are made on the forecast and scored on the demand that actually occurred, so capacity overload caused by forecast error is visible (3 of 6 hubs overloaded in the October 2025 peak). Six methods are compared on the same instance: relative to the proposed plan, the greedy plan costs {GREEDY_GAP:.1f}% more, k-means {KM_GAP:.1f}% more, the largest-markets rule {LG_GAP:.1f}% more and planning without a forecast {FX_GAP:.1f}% more.",
        f"**Rolling re-optimisation.** Re-forecasting and re-planning every month gave {pct(AD['fulfilment_rate'])} average simulated fulfilment against {pct(ST['fulfilment_rate'])} for a static plan, at {abs(AD['total_cost'] / ST['total_cost'] - 1) * 100:.1f}% lower average operating cost, with one hub change in six months.",
        "**A usable product.** A FastAPI layer (14 endpoints, background jobs) and a React application (landing page, dashboard, forecast, plan, compare, re-optimise, regions) that run the same code as the command line; 4 test functions and 18 API smoke checks pass.",
    ])


def sec_novelty(d):
    d.h2("Novelty Against the Base Paper")
    d.p("The base paper [1] describes the framework and reports service-level results on a proprietary dataset. It does not publish code, "
        "the dataset or the parameters of its matheuristic. The table lists what this project adds or does differently. None of it is a "
        "claim of better performance than the base paper: the datasets are different and the paper's figures cannot be reproduced.")
    d.table([["Aspect", "Base paper [1]", "This project"],
             ["Data", "Real logistics data of a global transport company (two years, thousands of customer locations); not public", "Synthetic data, 90 regions x 36 months, generated by a seeded script and shipped with the code"],
             ["Forecast model", "Random Forest, with hyper-parameter tuning and cross-validation stated; the improvement over statistical methods is left as 'X %'", "Random Forest with fixed parameters, time-based hold-out, compared with two naive forecasters; all numbers reported"],
             ["Matheuristic", "MILP for an initial solution, then Variable Neighbourhood Search (VNS)", "Greedy/k-medoids construction, swap/drop/add local search priced by exact assignment MIPs after a greedy-bound screen, kernel search; no VNS"],
             ["Model", "Multiple capacity levels, unmet-demand penalty, scenario-based robust objective", "Single capacity level, soft or hard SLA, time penalty; no robust objective"],
             ["Evaluation", "Delivery-time compliance 92.3%, fulfilment 97.6%, robustness 0.87; networks of 50-500 nodes", "Cost, delivery time, simulated fulfilment and SLA reliability on realised demand; 90-270 nodes; no robustness measure"],
             ["Adaptation", "Re-optimisation described; temporal effects modelled by time-dependent constraints", "Rolling-horizon simulation over six months with a static plan as the control"],
             ["Delivery", "Paper only", "Open code, tests, 14-endpoint API and a web application"]],
            "Base paper and this project compared", widths=[0.16, 0.42, 0.42], font=9.5)


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.h3("Assumptions")
    d.bullets([
        "Demand in a region is the monthly number of orders; one order is one parcel of the same size.",
        "Road distance is 1.25 times the great-circle (haversine) distance; trucks average 45 km/h; a hub needs 6 hours of handling.",
        "Each region is served by exactly one hub (single allocation); every region can host a hub.",
        "A hub's capacity is 1.25 times the average planned demand per hub; fixed hub cost is INR 2.5 million per month scaled by city tier (1.35, 1.0, 0.75).",
        "Costs are model parameters (INR 0.04 per order-km, INR 1.5 per order-hour). They are plausible but not calibrated to any real carrier.",
    ])
    d.h3("Limitations")
    d.bullets([
        "**Synthetic data.** The demand process was generated by the project, so the Random Forest learns a process the authors wrote down. The forecast accuracy (MAPE 7.67%) is therefore not evidence of accuracy on real data.",
        "**Forecast error is not handled by the optimiser.** The plan trusts the forecast. In the October 2025 peak the forecast was 13.2% low and three of six hubs ran above capacity (fulfilment 92.3%).",
        "**Little gain from the matheuristic at 90 nodes.** The matheuristic and the exact MIP found the same plan and solved in comparable times; the speed advantage appears from 180 nodes, and at 270 nodes the matheuristic was 3.67% above the exact incumbent.",
        "**No robustness analysis.** The base paper's robustness indicator was not implemented or measured.",
        "**Single hold-out.** There is one six-month hold-out split; no cross-validation or hyper-parameter search was run.",
        "**No user study.** The web application was exercised by scripted walkthroughs only; no real planner has evaluated it.",
        "**Local deployment.** There is no database, authentication or multi-user support; results are files on disk that background jobs overwrite.",
    ])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Content"],
             ["1 Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations"],
             ["2 Literature Survey", "The base paper, related work by theme, datasets and algorithms, research gap"],
             ["3 Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4 System Requirements and Analysis", "Existing and proposed system, requirements, hardware and software"],
             ["5 System Design", "Architecture, workflow, data-flow diagrams, UML, data model, modules, user interface"],
             ["6 Methodology and Software Implementation", "Data, features, forecaster, optimisation model, matheuristic, application, API, security, installation"],
             ["7 System Testing", "Strategy, tests that were run, edge cases, performance and the limits of the testing"],
             ["8 Results and Output Screens", "Measured results, output screens, comparison with the base paper, objectives against outcomes"],
             ["9 Conclusion", "Summary, findings, applications, known limitations"],
             ["10 Future Scope", "Improvements, features, deployment and research directions"]],
            "Organisation of the report", widths=[0.33, 0.67], font=10)
