"""Text of the IEEE paper (19.IEEE_Paper.docx). Numbers are read from the saved results through doc_common."""
from __future__ import annotations

from doc_common import B1, B3, M, P, PAPER, RF, ROL, SCAL

TITLE = "HubOptima: Combining Random Forest Demand Forecasting with a Matheuristic for E-Commerce Hub Location"
ABSTRACT = (
    "Hub networks of e-commerce carriers are usually planned on a fixed demand with exact solvers or simple rules, although demand "
    "moves between regions and seasons and exact solvers slow down as networks grow. This paper implements and measures a predict-then-"
    "optimise framework. A Random Forest forecasts regional demand from order history; a capacitated hub-location model is built from "
    "the forecast and solved by a matheuristic that prices hub sets with exact assignment programs and polishes the result with a "
    "kernel search; plans are scored on the demand that actually occurred and are re-made every month. On a synthetic dataset of 90 "
    "regions and 36 months, the forecaster reaches a MAPE of 7.67% against 17.6-19.7% for naive forecasters. For the October 2025 "
    "festival peak, the plan matches the exact optimum, costs 3.6-16.1% less than a clustering heuristic, a greedy heuristic and a "
    "largest-markets rule, and re-planning every month raises simulated fulfilment from 83.7% to 98.3% against a static plan. The "
    "matheuristic is 3.67% above the exact incumbent at 270 nodes, the peak was under-forecast by 13.2%, and the data are synthetic."
)
KEYWORDS = ("demand forecasting, e-commerce logistics, hub location problem, matheuristic, mixed-integer programming, random forest, "
            "rolling-horizon re-optimisation")

G, K, L, X, F = M["greedy"], M["kmeans"], M["largest"], M["fixed_avg"], M["exact_mip"]
AD, ST = ROL["adaptive_avg"], ROL["static_avg"]


def body(Pp):
    # ---------------------------------------------------------------- I
    Pp.h1("I. Introduction")
    Pp.para("Electronic commerce depends on a physical network of hubs where parcels are consolidated, sorted and dispatched. Where the hubs "
            "are opened decides the fixed cost of the network, the distance parcels travel and how long deliveries take, which makes the hub "
            "location problem (HLP) a central problem of logistics planning [1], [6], [7]. The problem is combinatorial: even with 90 candidate "
            "sites, choosing six hubs and allocating every region to one of them has billions of solutions, and exact mixed-integer programming "
            "(MIP) is practical only for moderate networks [8], [9].")
    Pp.para("In practice, plans are made on a fixed demand, often an average of past months, by solving an exact model once, by applying a "
            "greedy or clustering heuristic, or by placing hubs at the largest markets. This costs money twice. The demand is wrong when the "
            f"plan is used: in our October 2025 test a plan built on the historical average served only {X['fulfilment_rate'] * 100:.1f}% of the "
            f"orders that arrived. And the rules are not optimal: the largest-markets plan cost {L['cost_vs_proposed_pct']:.1f}% more than the optimised one. "
            "The base paper [1] proposes to forecast demand with a Random Forest and to feed the forecast to a matheuristic, but it reports results "
            "on proprietary data, does not release code, and states the gain of the forecaster only as “X %”.")
    Pp.para("This paper presents HubOptima, an open implementation of that predict-then-optimise framework with a measured evaluation. The contributions are:", after=2)
    Pp.numbered([
        "an end-to-end pipeline (cleaning, 19 features, Random Forest, capacitated hub MIP, matheuristic, evaluation) in about 2,000 lines of Python;",
        "a matheuristic that screens swap, drop and add moves with a cheap estimate, prices the promising ones with exact assignment MIPs and finishes with a kernel search;",
        "an evaluation protocol that plans on the forecast and scores on realised demand, so that forecast error appears as overloaded hubs, with five baselines and a rolling-horizon control;",
        "a FastAPI and React application with 14 endpoints that exposes forecasting, planning, comparison and re-optimisation.",
    ])
    Pp.para("Section II reviews the literature, Section III the method, Section IV the results and Section V concludes.", before=2)
    Pp.h2("A. System Hardware")
    Pp.para("All timings were measured on one desktop with an Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of memory and Windows 11 Pro. "
            "No GPU was used and no other machine was tested.")
    Pp.h2("B. Software Requirements")
    Pp.para("Python 3.11.9 with pandas 2.2.1, NumPy 1.26.4 and scikit-learn 1.4.2 [13] (Random Forest [11], k-means [18]); PuLP 3.3.2 [14] with the "
            "bundled CBC solver [15]; FastAPI 0.110 with uvicorn; React 18.3 and Vite 5.4 for the interface; and Node.js 24. All components are "
            "open source and the system runs offline.")

    # ---------------------------------------------------------------- II
    Pp.h1("II. Literature Survey")
    Pp.h2("A. Base Paper")
    Pp.para("Danach et al. [1] study the HLP for e-commerce with centralised hubs, dynamic demand, capacity limits and service levels. Their "
            "model minimises fixed hub cost, variable transport cost and a penalty on unmet demand, with continuous flows, binary hubs and "
            "capacity levels. The solution approach is a matheuristic: a relaxed MILP gives an initial solution, Variable Neighbourhood Search "
            "(VNS) [16] improves it, a Random Forest trained on historical demand forecasts the demand at each location, and the forecasts "
            "re-optimise the hubs and are validated on peak, spike and disruption scenarios. On the proprietary data of a global transport company "
            "(two years of demand, thousands of locations) the paper reports delivery-time compliance of 92.3%, fulfilment of 97.6%, robustness "
            "of 0.87, improvements of 7.8%, 9.4% and 16% over traditional methods, cost reductions of 15-20% and networks of 50 to 500 nodes. "
            "The authors list sector-specific data, limited scalability testing, offline evaluation and unexplored learners as limitations. "
            "HubOptima differs in that it releases code and data, measures the forecaster against naive benchmarks, evaluates plans on realised "
            "demand, and replaces VNS by a screened local search with kernel search [17].")
    Pp.h2("B. Related Work")
    Pp.para("*Foundations.* O'Kelly introduced interacting hub facilities [6]; Campbell et al. surveyed the problem family [7]; Ernst and "
            "Krishnamoorthy gave efficient algorithms for the uncapacitated single-allocation p-hub median [8]; Danach et al. combined Lagrangian "
            "relaxation with a hyper-heuristic for a capacitated single-allocation location-routing problem [9].")
    Pp.para("*Metaheuristics.* Zheng et al. locate drone logistics hubs with a diversity-based hybrid particle swarm optimiser, reporting a "
            "42.58% efficiency gain over other algorithms in the abstract [2]. Dehghan Chenary et al. combine Pareto-based clustering with a "
            "metaheuristic for a bi-objective mobile hub problem with congestion and compare it with MOPSO and NSGA-II on Australian Post data [4].")
    Pp.para("*Exact methods and uncertainty.* Yang et al. model a maximal-detour liner-shipping p-hub centre with three MILPs and an improved "
            "Benders decomposition [3]. Zhang et al. formulate a two-stage adaptive robust hub location problem under budgeted demand uncertainty and "
            "solve it by column-and-constraint generation, reporting better out-of-sample performance than a stochastic model [5]. "
            "Kahalimoghadam et al. address the number and location of micro-consolidation centres under growing e-commerce demand [10].")
    Pp.para("*Methods.* Maniezzo et al. define matheuristics [12]; kernel search [17] and VNS [16] are the building blocks the base paper and "
            "this work draw on; Hyndman and Athanasopoulos give the evaluation conventions for forecasts [19]. Table I summarises the works; "
            "[2]-[5] are summarised from their abstracts only.")
    Pp.table([
        ["Work", "Approach", "Data", "Reported result", "Limitation"],
        ["[1]", "RF forecast + matheuristic", "Proprietary", "92.3% / 97.6% / 0.87", "Data not public"],
        ["[2]", "Hybrid PSO", "Village drones", "+42.58% (abstract)", "No forecast"],
        ["[3]", "MILP + Benders", "Liner shipping", "Faster exact solve", "Fixed demand"],
        ["[4]", "Pareto clustering", "Australian Post", "Beats MOPSO, NSGA-II", "Demand given"],
        ["[5]", "Adaptive robust", "Not stated", "Better out-of-sample", "Assumed set"],
        ["[9]", "Lagrangian + hyper-heur.", "Not reviewed", "As cited in [1]", "No forecast"],
    ], "Related work", [0.09, 0.27, 0.19, 0.25, 0.20], size=6.6)
    Pp.para("*Research gap.* Most studies take demand as given or assume an uncertainty set; the base paper's data, code and matheuristic parameters "
            "are unavailable; the effect of forecast error on the plan is not shown; and the value of monthly re-planning and the exact-versus-"
            "matheuristic trade-off as networks grow are not measured. HubOptima addresses these four points.")

    # ---------------------------------------------------------------- III
    Pp.h1("III. Methodology")
    Pp.h2("A. Data")
    Pp.para("No public region-level order data was available, so the data are synthetic (seed 42): 90 regions (30 Indian cities and 60 satellite "
            "districts) and 36 months, 2023-01 to 2025-12, giving 3,240 region-months and 48.3 million orders. Monthly orders follow population x "
            "tier-specific penetration, a 1.0-2.2% monthly growth, festival factors (October 1.35, November 1.25), a promotion lift of 14% and 6% "
            "noise; the network peaks at 2.38 million orders in October 2025. Loading removes duplicates, interpolates gaps and sorts; the "
            "generated data has no gaps, so these guards serve real files. The Random Forest learns a process that the authors wrote down, so "
            "its accuracy is not evidence of accuracy on real orders.")
    Pp.h2("B. Demand Forecasting")
    Pp.para("For every region and month, 19 features are built: lags 1, 2, 3, 6 and 12, rolling means over 3 and 6 months and a rolling "
            "standard deviation (all shifted one month so that a month never sees itself), a trend, month, quarter, a festival flag, the promotion "
            "flags, population, tier, penetration, order value and return rate. A Random Forest regressor [11] with 400 trees, minimum leaf "
            "size 2 and 60% of features per split is trained on 2023-04 to 2025-06 (2,430 rows) and tested on the six months 2025-07 to 2025-12 "
            "(540 rows); there is no tuning and no cross-validation. A past month is forecast using only earlier data, and the next month is forecast from the lags of the latest month; the forest is a single global model for all regions, so small regions borrow strength from large ones. Training takes 0.8 s. Fig. 1 shows the pipeline and Fig. 2 the software.")
    Pp.figure(PAPER / "fig2_flow.png", "Predict-then-optimise flow of HubOptima.", width=2.7)
    Pp.h2("C. Hub-Location Model")
    Pp.para("Every region i is a demand point with planned demand D_i (the forecast) and a candidate hub site j. Distance is 1.25 times the "
            "haversine distance [20], delivery time is t_ij = d_ij / 45 km/h + 6 h (3 h for local delivery), the unit cost is c_ij = 0.04 d_ij + 1.5 t_ij "
            "(INR per order), the fixed cost is INR 2.5 million per month scaled by tier (1.35, 1.0, 0.75) and the capacity of a hub is "
            "C = 1.25 SUM_i D_i / p with p = 6. With binary y_j (hub open) and x_ij (region i served by j):")
    Pp.eq("min  Σ_{j} f_{j} y_{j} + Σ_{i} Σ_{j} c_{ij} D_{i} x_{ij}", 1)
    Pp.eq("s.t.  Σ_{j} x_{ij} = 1  ∀i;   x_{ij} ≤ y_{j};   Σ_{j} y_{j} ≤ p", 2)
    Pp.eq("Σ_{i} D_{i} x_{ij} ≤ C y_{j}  ∀j", 3)
    Pp.para("An optional hard constraint x_ij = 0 whenever t_ij exceeds the 48 h SLA is available; by default the SLA is soft, so late deliveries are "
            "penalised through the time term and reported by a reliability indicator instead of being forbidden. A hard SLA can make the problem "
            "infeasible, and the API then returns an explanation instead of a plan. Compared with [1] the "
            "model is single-allocation with one capacity level, no unmet-demand variable and no robust objective: the role of the unmet-demand penalty "
            "is played by the evaluation step below, in which orders above a hub's capacity count as unfulfilled.")
    Pp.h2("D. Matheuristic")
    Pp.para("Fixing the hub set leaves an assignment MIP of n x p variables (540 for six hubs), which CBC solves exactly, whereas the full model has "
            "n + n^2 binaries (8,190 for 90 regions). The matheuristic therefore searches over hub sets [12]. (1) A greedy weighted k-medoids "
            "start set is built and priced. (2) Swap, drop and add moves are generated for the closed candidates ranked by nearby demand; every move "
            "is estimated by a capacity-aware greedy allocation, moves more than 6% above the current cost are skipped, and the rest are priced "
            "by the exact assignment MIP with a cache; the first strictly better plan is accepted and the search restarts, until no move helps or "
            "70% of the time limit is used. (3) A kernel search [17] solves the full MIP restricted to about 24 promising hubs: the open hubs, their nearest "
            "neighbours, the best-priced hub sets seen and the most attractive unexamined sites. For n = 90 and p = 6 a pass generates up to 138 moves "
            "(132 swaps, 6 drops); in the reported runs 14 to 18 assignment MIPs were solved per search, so most moves are rejected by the estimate. "
            "If the start set is infeasible, hubs are added by demand until it is feasible.")
    Pp.h2("E. Evaluation Protocol and Implementation")
    Pp.para("Plans are made on the forecast and scored on the realised demand R_i. With L_j the realised load of hub j and a(i) the hub of region i, "
            "the share a hub serves is s_j = min(1, C / L_j), and")
    Pp.eq("fulfilment = Σ_{i} s_{a(i)} R_{i} / Σ_{i} R_{i}", 4)
    Pp.eq("reliability = Σ_{i} 1[t_{i,a(i)} ≤ 48 h] s_{a(i)} R_{i} / Σ_{i} R_{i}", 5)
    Pp.para("Together with total cost, average delivery time and utilisation L_j / C these form the KPIs. They are simulated capacity "
            "measures, not observed deliveries. Baselines on the same forecast are a greedy heuristic, demand-weighted k-means [18], the "
            "largest-markets rule and the exact MIP (30 s limit); a fifth plan uses the historical average instead of the forecast. A rolling horizon "
            "re-forecasts and re-plans for each month from July to December 2025 and is compared with a static plan fixed on the earlier average; "
            "the forest is not retrained during the simulation. A scalability benchmark splits every region into 1, 2 or 3 nearby demand points to give 90, 180 and 270 nodes, with an exact-MIP time limit. The core "
            "package (about 1,000 lines) is called by a FastAPI layer with 14 endpoints, pydantic validation (for example p between 1 and 20, time limit 2 to 300 s) and background jobs, and by a React application with seven pages "
            "(Fig. 2). Data, model and results are plain CSV, joblib and JSON files, there is no database, and the random seed is fixed, so a run can be repeated. "
            "The command line, the original Flask interface and the API call the same functions, which keeps their numbers identical. The code was "
            "checked by four test functions (data, forecast contract, optimisation constraints including the 2% agreement of matheuristic and exact MIP, and the web "
            "pages) and an 18-check API smoke test, all of which pass.")
    Pp.figure(PAPER / "fig1_architecture.png", "Architecture: interface, API layer, core package, solvers and files.", width=3.0)

    # ---------------------------------------------------------------- IV
    Pp.h1("IV. Results")
    Pp.h2("A. Forecast Accuracy")
    Pp.para(f"On the 540 held-out region-months the Random Forest reaches MAE {RF['mae']:,.0f}, RMSE {RF['rmse']:,.0f}, MAPE {RF['mape']:.2f}% and "
            f"R^2 {RF['r2']:.4f}, against MAE {B1['mae']:,.0f} and MAPE {B1['mape']:.2f}% for last month's value and MAE {B3['mae']:,.0f} and MAPE "
            f"{B3['mape']:.2f}% for the 3-month moving average. The most important features are the 3-month mean (0.379), last month (0.242) "
            "and population (0.155). Network-level errors are 1.5-6.0% in ordinary months but 13.1% in October 2025 (an under-forecast) and 10.2% "
            "in December; the October volume of 2.38 million exceeds every earlier month (previous maximum 1.96 million), which a forest cannot "
            "extrapolate, a likely but untested cause. In December the median regional error is 7.0%, the mean 8.9% and 8 of 90 regions exceed 20%; the three worst, Pune (39.9%), Ahmedabad (39.3%) and "
            "Chennai (39.0%), are all over-forecasts, and their cause was not investigated.")
    Pp.h2("B. Comparison with Traditional Methods")
    Pp.para("Table II gives the October 2025 plans for p = 6 scored on the 2,383,534 realised orders (forecast 2,067,718).")
    rows = [["Method", "Cost (INR M)", "vs prop.", "Avg h", "Fulf. %", "Solve s"]]
    for k, lab in [("proposed", "RF + matheuristic"), ("exact_mip", "RF + exact MIP"), ("greedy", "RF + greedy"), ("kmeans", "RF + k-means"), ("largest", "Largest markets"), ("fixed_avg", "Hist. avg, no RF")]:
        m = M[k]
        rows.append([lab, f"{m['total_cost'] / 1e6:.1f}", "-" if k == "proposed" else f"{m['cost_vs_proposed_pct']:+.1f}%", f"{m['avg_delivery_hours']:.2f}",
                     f"{m['fulfilment_rate'] * 100:.1f}", f"{m['seconds']:.2f}"])
    Pp.table(rows, "October 2025 plans (p = 6, scored on realised demand)", [0.30, 0.16, 0.13, 0.11, 0.14, 0.16], size=6.8)
    Pp.para(f"The matheuristic and the exact MIP open the same six hubs (Mumbai, Delhi, Kolkata, Hyderabad-W2, Bengaluru-SE, Ahmedabad-SE) at INR "
            f"{P['total_cost'] / 1e6:.1f} M per month; CBC proved optimality in {F['seconds']} s against {P['seconds']} s. Greedy, k-means and the largest-"
            f"markets rule cost {G['cost_vs_proposed_pct']:.1f}%, {K['cost_vs_proposed_pct']:.1f}% and {L['cost_vs_proposed_pct']:.1f}% more, and planning without a forecast "
            f"costs {X['cost_vs_proposed_pct']:.1f}% more and serves only {X['fulfilment_rate'] * 100:.1f}% of orders. Because the peak was under-forecast, every "
            "forecast-based plan has three overloaded hubs and 89-92% fulfilment (Fig. 3, Fig. 4): Delhi runs at 122%, Bengaluru-SE at 111% and Mumbai "
            "at 110%. The plan costs INR 15.8 M in fixed hub cost, 15.8 M in transport and 30.6 M in delivery-time penalty, with an average delivery time of "
            f"{P['avg_delivery_hours']:.2f} h, a maximum of {P['max_delivery_hours']:.1f} h and an average distance of {P['avg_distance_km']:.0f} km; Hyderabad-W2 (59%), Ahmedabad-SE (71%) and Kolkata (80%) "
            "stay below capacity. Greedy swaps Ahmedabad-SE for Nagpur-N, k-means opens Warangal, and the largest-markets rule has a longest delivery of 50.0 h, beyond "
            "the 48 h SLA. These are single-instance results without repeated runs.")
    Pp.figure(PAPER / "fig3_results.png", "Cost and simulated fulfilment by method, October 2025.", width=3.3)
    Pp.figure(PAPER / "fig4_plan.png", "Output screen: the October 2025 plan (6 hubs, INR 62.2 M, 92.3%).", width=3.3)
    Pp.h2("C. Rolling Re-Optimisation and Scalability")
    Pp.para(f"Re-planning every month from July to December 2025 gives {AD['fulfilment_rate'] * 100:.1f}% average fulfilment against {ST['fulfilment_rate'] * 100:.1f}% for a "
            f"static plan (+{(AD['fulfilment_rate'] - ST['fulfilment_rate']) * 100:.1f} points), an average delivery time of {AD['avg_delivery_hours']:.2f} h against {ST['avg_delivery_hours']:.2f} h, "
            f"and {abs(AD['total_cost'] / ST['total_cost'] - 1) * 100:.1f}% lower average cost, with one hub change (Kolkata-W replaced by Kolkata in October). "
            "In the October peak the gap is widest, 92.4% against 64.9% (Table III, Fig. 6). The static plan is a simple control, and a generously sized static plan "
            f"or monthly retraining was not tested. At {SCAL[0]['nodes']} and {SCAL[1]['nodes']} nodes the matheuristic equals the exact MIP (gap 0.00% and -0.05%) and is "
            f"{SCAL[0]['exact_seconds'] / SCAL[0]['matheuristic_seconds']:.1f} and {SCAL[1]['exact_seconds'] / SCAL[1]['matheuristic_seconds']:.1f} times faster ({SCAL[0]['matheuristic_seconds']:.1f} s against "
            f"{SCAL[0]['exact_seconds']:.1f} s; {SCAL[1]['matheuristic_seconds']:.1f} s against {SCAL[1]['exact_seconds']:.1f} s). At {SCAL[2]['nodes']} nodes "
            f"({SCAL[2]['binary_vars']:,} binary variables) CBC stopped without proof and the matheuristic ({SCAL[2]['matheuristic_seconds']:.1f} s) is "
            f"{SCAL[2]['matheuristic_gap_pct']:.2f}% above its incumbent.")
    rrows = [["Month", "Forecast error", "Adaptive fulf. %", "Static fulf. %", "Hub change"]]
    for t in ROL["timeline"]:
        rrows.append([t["period"], f"{t['forecast_error_pct']:.1f}%", f"{t['adaptive']['fulfilment_rate'] * 100:.1f}", f"{t['static']['fulfilment_rate'] * 100:.1f}",
                      "-" if not t["opened"] else "+" + t["opened"][0] + " / -" + t["closed"][0]])
    rrows.append(["Average", "-", f"{AD['fulfilment_rate'] * 100:.1f}", f"{ST['fulfilment_rate'] * 100:.1f}", "1 opening"])
    Pp.table(rrows, "Rolling re-optimisation, July to December 2025", [0.17, 0.19, 0.2, 0.18, 0.26], size=6.6)
    Pp.figure(PAPER / "fig6_rolling.png", "Fulfilment of the adaptive and the static plan by month.", width=3.2)
    Pp.h2("D. Comparison with the Base Paper")
    Pp.para("The datasets and metric definitions differ, so there is no head-to-head comparison. The base paper [1] reports compliance of 92.3% and "
            "fulfilment of 97.6% on proprietary data and robustness of 0.87; this work reports simulated fulfilment of 92.3% in the peak and "
            "98.3% with monthly re-planning on synthetic data, and does not implement robustness. The base paper reports cost reductions of 15-20%; the "
            "reductions here, 3.6-16.1% against heuristics and rules and 0% against the exact MIP, point the same way against different baselines. It "
            "tests 50-500 nodes; this work tests 90-270.")
    Pp.h2("E. Failure Cases and Observed Limits")
    Pp.para("The weakest result is the October peak, where a 13.2% under-forecast leaves 7.7% of orders unserved because capacity is sized from "
            "the forecast and the optimiser has no margin. At 90 nodes the matheuristic gives no practical gain over CBC: end-to-end planning took 12.2 s "
            "against 15.3 s for the exact MIP, and the UI showed 9.23 s against 9.29 s. At 270 nodes it is 3.67% worse than the incumbent. With six hubs, "
            "Dehradun-N is served 1,427 km away (37.7 h). The input API rejects n = 0 hubs (HTTP 422) and unknown months (HTTP 400), and the 4 tests "
            "and 18 API checks pass; no user study, load test or authentication test was done, and Fig. 5 shows the comparison screen.")
    Pp.figure(PAPER / "fig5_compare.png", "Output screen: six methods scored on realised demand.", width=3.3)
    Pp.h2("F. Discussion")
    Pp.para("Three results are robust to the choice of dataset because they follow from the structure of the problem: a plan built on a forecast "
            "beats one built on an average when demand moves; an optimised hub set beats rules that ignore the cost structure; and capacity sized from "
            "a forecast is only as good as the forecast. Three others depend on the synthetic data and should be re-measured on real orders: the "
            "absolute forecast error, the absolute cost differences, which come from assumed cost parameters, and the size of the re-planning gain, which "
            "depends on how strongly the generated demand moves. The matheuristic's value is in scale, not at 90 nodes, and the 3.67% gap shows the price of the "
            "kernel restriction when CBC cannot finish. Planning for six hubs in about ten seconds on a desktop suggests the tool is usable interactively; "
            "whether planners find it so was not tested.")

    Pp.h2("G. Threats to Validity")
    Pp.para("Internal: the hyper-parameters were fixed once and not tuned, and the solver times vary by several seconds between runs because of CBC and "
            "processor load. The forest was trained on data up to June 2025, so forecasts for earlier months are partly in-sample and are not used in any "
            "reported result. External: the demand process, the cost parameters and the SLA are assumptions; fulfilment and reliability are simulated; "
            "the comparison covers one month, the rolling horizon six months and the benchmark three network sizes. Construct: the base paper's "
            "compliance, fulfilment and robustness are defined on its own data and are not the quantities measured here.")

    # ---------------------------------------------------------------- V
    Pp.h1("V. Conclusion and Future Scope")
    Pp.para(f"HubOptima implements and measures the predict-then-optimise framework of [1]. Against the objectives, the data are cleaned and "
            f"featurised, the Random Forest cuts the MAPE from 17.6-19.7% to {RF['mape']:.2f}%, the capacitated model includes cost, time and capacity, the matheuristic "
            "reaches the exact optimum at 90 and 180 nodes, monthly re-planning raises simulated fulfilment by 14.6 points, and five baselines are "
            "beaten on cost. The key finding is that forecast error becomes capacity overload, so the plan needs a margin. The limits are synthetic data, one "
            "split, no robustness analysis, a 3.67% gap at 270 nodes and no user study.")
    Pp.para("Future work: pilot on real orders; a safety margin or scenario objective; monthly retraining and other learners; VNS and multiple "
            "capacity levels; and a database with authentication for shared use.")
