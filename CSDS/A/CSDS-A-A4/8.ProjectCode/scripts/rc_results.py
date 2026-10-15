"""Chapter 8 sections: results and output screens."""
from __future__ import annotations

import json

import pandas as pd

from doc_common import (B1, B3, CHARTS, CMP, DEM, FM, M, MAIN_SCREENS, METHOD_ROWS, P, RF, ROL, SCAL, SCREENS, SHOTS, inr_m, pct, ROOT)

SAMPLES = ROOT / "docs" / "samples"
AD, ST = ROL["adaptive_avg"], ROL["static_avg"]
W = None  # figure width helper set by callers


def _w(d, f=0.95):
    return d.text_width * f


def sec_forecast_results(d):
    d.h2("Demand Forecast Results")
    d.p("The Random Forest was fitted on 2,430 region-months (2023-04 to 2025-06) and evaluated on the 540 region-months of July to December 2025, which it never saw. "
        "Two naive forecasters are scored on the same rows: the last month's value and the three-month moving average.")
    rows = [["Forecaster", "MAE (orders)", "RMSE (orders)", "MAPE (%)", "R-squared"]]
    for name, m in (("Random Forest (proposed)", RF), ("Last month's value", B1), ("3-month moving average", B3)):
        rows.append([name, f"{m['mae']:,.1f}", f"{m['rmse']:,.1f}", f"{m['mape']:.2f}", f"{m['r2']:.4f}"])
    d.table(rows, "Forecast accuracy on the held-out months", widths=[0.34, 0.17, 0.17, 0.15, 0.17], font=10, align=["l", "r", "r", "r", "r"])
    d.figure(CHARTS / "forecast_comparison.png", "Held-out accuracy of the three forecasters", width=_w(d))
    d.p(f"The Random Forest roughly halves the error of both naive forecasters: MAE {RF['mae']:,.0f} against {B1['mae']:,.0f} and {B3['mae']:,.0f}, MAPE {RF['mape']:.2f}% against "
        f"{B1['mape']:.2f}% and {B3['mape']:.2f}%. These are results on a synthetic series whose generating process the model can learn; they should not be read as accuracy that would be achieved on "
        "real orders.")
    d.h3("What the model relies on")
    d.figure(CHARTS / "feature_importance.png", "Top 10 Random Forest feature importances", width=_w(d, 0.8))
    d.p("Three features carry almost all of the importance: the three-month rolling mean (0.379), the previous month's orders (0.242) and the region's population (0.155). The calendar "
        "features that encode the festival peak have very small importance (festival 0.0017, month 0.0011, promo 0.0019). This is consistent with the dataset: the level of a region "
        "is the main driver, and the trees appear to take most of the festival effect from recent lags rather than from the calendar.")
    d.h3("Error by region and by month")
    e = pd.DataFrame(FM["last_period_detail"])
    d.figure_pair([(CHARTS / "forecast_scatter.png", "Per-region forecast and actual orders, Dec 2025"), (CHARTS / "error_histogram.png", "Distribution of per-region error, Dec 2025")], width=3.0, max_h=3.2)
    worst = e.sort_values("error_pct", ascending=False).head(5)
    names = dict(zip(pd.read_csv(ROOT / "data" / "regions.csv").region_id, pd.read_csv(ROOT / "data" / "regions.csv").city))
    d.p(f"In December 2025 the median absolute error across the 90 regions is {e.error_pct.median():.1f}% and the mean {e.error_pct.mean():.1f}%; {int((e.error_pct > 20).sum())} regions exceed 20%. "
        "The worst are " + ", ".join(f"{names[r.region_id]} ({r.error_pct:.1f}%)" for r in worst.head(3).itertuples()) + ", all over-forecasts of large tier-1 cities.")
    d.table([["Month", "Forecast total", "Realised total", "Network error (%)"]] +
            [[t["period"], f"{t['forecast_total']:,}", f"{t['realized_total']:,}", f"{t['forecast_error_pct']:.2f}"] for t in ROL["timeline"]],
            "Network-level forecast error by test month", widths=[0.2, 0.28, 0.28, 0.24], font=10, align=["l", "r", "r", "r"])
    d.figure(CHARTS / "rolling_demand.png", "Network forecast against realised demand, July to December 2025", width=_w(d, 0.8))
    d.p("Network errors are small in ordinary months (1.5-6.0%) and large at the festival peak (13.1% in October, an under-forecast) and in December (10.2%, an over-forecast after the peak). "
        "The October 2025 volume (2.38 million orders) is higher than any month the model was trained on (the previous maximum was 1.96 million in October 2024); a forest "
        "cannot predict beyond the range of the targets it has seen, so this is a likely cause of the under-forecast, although the project did not test it further.")


def sec_plan_results(d):
    d.h2("The Proposed Plan for October 2025")
    a = pd.DataFrame(P["assignment"])
    g = a.groupby("hub").agg(n=("region", "count"), demand=("demand", "sum"), maxh=("hours", "max"), avgkm=("distance_km", "mean"))
    rows = [["Hub", "Regions served", "Realised demand", "Utilisation", "Longest delivery (h)", "Mean distance (km)"]]
    for h, idx in zip(P["hub_cities"], P["hubs"]):
        r = g.loc[h]
        u = P["utilisation"][str(idx)]
        rows.append([h, str(int(r.n)), f"{int(r.demand):,}", f"{u * 100:.0f}%" + (" (over)" if u > 1 else ""), f"{r.maxh:.1f}", f"{r.avgkm:.0f}"])
    d.p("The matheuristic, planned on the forecast of 2,067,718 orders and scored on the 2,383,534 orders that occurred, opens six hubs: three tier-1 cities (Mumbai, Delhi, Kolkata) and "
        "three satellite districts (Hyderabad-W2, Bengaluru-SE, Ahmedabad-SE).")
    d.table(rows, "Hubs of the proposed plan, Oct 2025 (scored on realised demand)", widths=[0.2, 0.14, 0.18, 0.16, 0.16, 0.16], font=9.5, align=["l", "r", "r", "r", "r", "r"])
    d.table([["Measure", "Value"], ["Operating cost", f"INR {P['total_cost']:,.0f} per month (INR {P['cost_per_order']:.2f} per order)"],
             ["Fixed / transport / delivery-time penalty", f"INR {P['fixed_cost']:,.0f} / {P['transport_cost']:,.0f} / {P['time_cost']:,.0f}"],
             ["Average / maximum delivery time", f"{P['avg_delivery_hours']:.2f} h / {P['max_delivery_hours']:.2f} h"], ["Average distance", f"{P['avg_distance_km']:.1f} km"],
             ["Simulated fulfilment / SLA reliability (48 h)", f"{pct(P['fulfilment_rate'])} / {pct(P['reliability_sla'])}"], ["Overloaded hubs", f"{P['overloaded_hubs']} of 6"],
             ["Solver time (saved comparison)", f"{CMP['methods']['proposed']['seconds']} s (matheuristic), {CMP['methods']['exact_mip']['seconds']} s (exact MIP)"]],
            "KPIs of the proposed plan", widths=[0.4, 0.6], font=10)
    d.figure(CHARTS / "hub_utilisation.png", "Hub utilisation of the proposed plan on realised demand", width=_w(d, 0.7))
    d.p("Delhi (122%), Bengaluru-SE (111%) and Mumbai (110%) are above capacity. Capacity was sized from the forecast, which was 13.2% below the realised demand, so the "
        "three hubs that serve the biggest markets run over, and 7.7% of the realised orders are counted as unfulfilled. No hub is far under-used except Hyderabad-W2 (59%). "
        "The longest delivery (37.7 h to Dehradun-N through Ahmedabad-SE, 1,427 km) is within the 48 h SLA; with only six hubs, the north of the country is served from distant hubs.")


def sec_comparison_results(d):
    d.h2("Comparison with Traditional Methods")
    d.p("All methods plan the same month (October 2025) from the same forecast with p = 6 hubs and are scored on the realised demand. The exact MIP had a 30 s time limit.")
    rows = [["Method", "Cost (INR M)", "vs proposed", "Avg delivery (h)", "Fulfilment", "Overloaded", "Solve (s)"]]
    for k, lab in METHOD_ROWS:
        m = M[k]
        rows.append([lab, f"{m['total_cost'] / 1e6:.2f}", "reference" if k == "proposed" else f"{m['cost_vs_proposed_pct']:+.2f}%", f"{m['avg_delivery_hours']:.2f}",
                     pct(m["fulfilment_rate"]), str(m["overloaded_hubs"]), f"{m['seconds']:.2f}"])
    d.table(rows, "Methods compared on October 2025 (p = 6)", widths=[0.34, 0.11, 0.12, 0.12, 0.11, 0.1, 0.1], font=9, align=["l", "r", "r", "r", "r", "r", "r"])
    d.figure(CHARTS / "cost_by_method.png", "Operating cost by method", width=_w(d))
    d.figure(CHARTS / "fulfilment_by_method.png", "Simulated fulfilment by method", width=_w(d))
    d.figure(CHARTS / "cost_breakdown.png", "Cost components by method", width=_w(d))
    d.h3("Reading the comparison")
    d.bullets([
        f"**The matheuristic equals the exact MIP.** Both open the same six hubs and cost INR {P['total_cost'] / 1e6:.2f} M; CBC proved the exact plan optimal in {M['exact_mip']['seconds']} s against {P['seconds']} s. On a 90-region network the matheuristic confirms the optimum but does not yet save much time (Section 'Scalability').",
        f"**Heuristics cost more.** Greedy is {M['greedy']['cost_vs_proposed_pct']:.1f}% more expensive (it opens Nagpur-N instead of Ahmedabad-SE and has the lowest fulfilment of the forecast-based methods, 89.3%); k-means is {M['kmeans']['cost_vs_proposed_pct']:.1f}% more expensive; the largest-markets rule is {M['largest']['cost_vs_proposed_pct']:.1f}% more expensive and has the longest delivery of any plan (50.0 h maximum, beyond the 48 h SLA).",
        f"**Forecasting matters.** Planning on the historical average costs {M['fixed_avg']['cost_vs_proposed_pct']:.1f}% more in the model and serves only {pct(M['fixed_avg']['fulfilment_rate'])} of realised orders, with five of six hubs overloaded, because its capacities are sized for much lower demand.",
        "**Fulfilment is similar for the forecast-based methods** (89-92%): all of them inherit the 13.2% under-forecast, so every method has overloaded hubs (3 each). The proposed plan has the highest fulfilment and the lowest cost of the six, but its fulfilment advantage over k-means is 0.5 points only.",
        "These are single-instance results; no repeated runs, confidence intervals or other months were evaluated in this comparison.",
    ])


def sec_rolling_results(d):
    d.h2("Rolling Re-Optimisation")
    d.p("For each month from July to December 2025 the forecaster is applied using only earlier data, the matheuristic re-plans, and the plan is scored on the realised demand. A *static* plan, "
        "computed once from the average demand before July, is scored on the same months. The forecaster is not retrained during the simulation; its lag features are updated each month.")
    rows = [["Month", "Adaptive fulfilment", "Static fulfilment", "Adaptive cost (INR M)", "Static cost (INR M)", "Hub change"]]
    for t in ROL["timeline"]:
        ch = "none" if not t["opened"] else "open " + ", ".join(t["opened"]) + "; close " + ", ".join(t["closed"])
        rows.append([t["period"], pct(t["adaptive"]["fulfilment_rate"]), pct(t["static"]["fulfilment_rate"]), f"{t['adaptive']['total_cost'] / 1e6:.2f}", f"{t['static']['total_cost'] / 1e6:.2f}", ch])
    rows.append(["Average", pct(AD["fulfilment_rate"]), pct(ST["fulfilment_rate"]), f"{AD['total_cost'] / 1e6:.2f}", f"{ST['total_cost'] / 1e6:.2f}", "1 opening"])
    d.table(rows, "Adaptive and static plans, July to December 2025", widths=[0.12, 0.15, 0.14, 0.17, 0.15, 0.27], font=9, align=["l", "r", "r", "r", "r", "l"])
    d.figure(CHARTS / "rolling_fulfilment.png", "Fulfilment of the adaptive and the static plan by month", width=_w(d, 0.85))
    d.p(f"Adaptive re-planning achieves {pct(AD['fulfilment_rate'])} average fulfilment against {pct(ST['fulfilment_rate'])} for the static plan (+{(AD['fulfilment_rate'] - ST['fulfilment_rate']) * 100:.1f} points), "
        f"an average delivery time of {AD['avg_delivery_hours']:.2f} h against {ST['avg_delivery_hours']:.2f} h, and an average cost of INR {AD['total_cost'] / 1e6:.1f} M against INR {ST['total_cost'] / 1e6:.1f} M "
        f"({(AD['total_cost'] / ST['total_cost'] - 1) * 100:.1f}%). The gap is widest in the October peak (92.4% against 64.9%), where the static plan is sized for ordinary demand. The only hub change "
        "is Kolkata-W being replaced by Kolkata in October. The static plan was fitted on the earlier average, so it is a deliberately simple control; a static plan with generous capacity or "
        "a plan re-trained monthly was not tested.")


def sec_scalability_results(d):
    d.h2("Scalability")
    d.p("The scalability benchmark splits every region into 1, 2 or 3 nearby demand points to build networks of 90, 180 and 270 nodes and times the exact MIP (with a time limit) against the matheuristic.")
    rows = [["Nodes", "Binary variables", "Matheuristic (s)", "Exact MIP (s)", "Exact status", "Matheuristic gap"]]
    for r in SCAL:
        rows.append([str(r["nodes"]), f"{r['binary_vars']:,}", f"{r['matheuristic_seconds']:.2f}", f"{r['exact_seconds']:.2f}", r["exact_status"], f"{r['matheuristic_gap_pct']:+.2f}%"])
    d.table(rows, "Exact MIP against matheuristic by network size", widths=[0.1, 0.17, 0.18, 0.16, 0.17, 0.22], font=10, align=["r", "r", "r", "r", "l", "r"])
    d.figure(CHARTS / "scalability_time.png", "Solve time of the exact MIP and the matheuristic", width=_w(d, 0.75))
    d.bullets([
        "At 90 and 180 nodes both methods find the same plan (gap 0.00% and -0.05%, i.e. the matheuristic was marginally better at 180 nodes because CBC stops within its default tolerance); the matheuristic is 4.1 and 5.2 times faster.",
        "At 270 nodes (73,170 binary variables) CBC did not finish within its limit (status 'Not Solved') and reported an incumbent of INR 53.43 M; the matheuristic returned INR 55.39 M in 30.5 s, **3.67% above** the incumbent.",
        "The base paper reports networks of 50 to 500 nodes; this project measured three sizes up to 270 and makes no claim beyond them.",
    ])


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("Every screen below is a capture of the running application (1440 x 900, Chrome) with the real data of this project; the planning screens were produced by operating the form. "
        "The comparison, scalability and rolling screens display the saved results in `results/`.")
    wanted = [s for s in SCREENS if all_screens or s[0] in MAIN_SCREENS]
    for f, cap, desc in wanted:
        d.figure(SHOTS / f, cap, width=_w(d, 0.98), max_h=3.9)
        d.p(desc, size=11)


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.p("**Planning request and result.** Four hubs for December 2025 (the month is in the test range, so it is scored on realised demand):")
    d.code((SAMPLES / "optimize_request.json").read_text(), "sample input")
    d.code((SAMPLES / "optimize_response_trimmed.json").read_text(), "sample output (trimmed)")
    f = json.loads((SAMPLES / "forecast_head.json").read_text())
    d.p(f"**Forecast.** The next-month forecast (period {f['period']}) totals {f['total']:,} orders. The first two regions:")
    d.code(json.dumps(f["regions[0:2]"], indent=2), "GET /api/forecast: first two regions")
    d.p("**Rejected input.** `POST /api/optimize {\"n_hubs\": 0}` returns HTTP 422 and `{\"period\": \"1999-01\"}` returns HTTP 400 with 'Unknown planning month 1999-01.'.")


def sec_base_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("**The datasets and metric definitions differ, so the numbers below are not a head-to-head.** The base paper [1] uses a proprietary dataset from a global transport company with "
        "thousands of customer locations; this project uses a synthetic dataset of 90 regions. The base paper's 'delivery-time compliance', 'fulfilment' and 'robustness' are defined "
        "on its own data; the 'fulfilment' and 'SLA reliability' of this project are simulated capacity-based measures. The table puts the two side by side and states what is and "
        "is not comparable.")
    d.table([["Indicator", "Base paper [1]", "This project", "Comparable?"],
             ["Delivery-time compliance", "92.3% average", f"SLA reliability (48 h) {pct(P['reliability_sla'])} in the Oct 2025 peak; {pct(AD['reliability_sla'])} average with re-planning", "No: different data and definition"],
             ["Fulfilment rate", "97.6% average", f"{pct(P['fulfilment_rate'])} (Oct 2025 peak); {pct(AD['fulfilment_rate'])} average over Jul-Dec 2025 with re-planning", "No: simulated vs observed"],
             ["Network robustness", "0.87", "Not implemented, not measured", "-"],
             ["Cost improvement", "15-20% against benchmarks", f"{M['kmeans']['cost_vs_proposed_pct']:.1f}-{M['largest']['cost_vs_proposed_pct']:.1f}% lower than the heuristics and the managerial rule (greedy {M['greedy']['cost_vs_proposed_pct']:.1f}%, k-means {M['kmeans']['cost_vs_proposed_pct']:.1f}%, largest {M['largest']['cost_vs_proposed_pct']:.1f}%); 0% against the exact MIP", "Qualitatively similar direction; different baselines"],
             ["Improvement from adapting to demand", "+7.8% delivery compliance, +9.4% fulfilment (abstract)", f"+{(AD['fulfilment_rate'] - ST['fulfilment_rate']) * 100:.1f} points fulfilment against a static plan", "Different comparison"],
             ["Scalability", "50-500 nodes; near-optimal to 500", "90-270 nodes; exact failed at 270; matheuristic +3.67% there", "Smaller range tested"],
             ["Forecast accuracy", "'X %' improvement (not stated)", f"MAPE {RF['mape']:.2f}%, R-squared {RF['r2']:.4f} vs naive 17.6-19.7% MAPE", "Not reported by [1]"]],
            "Base paper and this project, side by side", widths=[0.19, 0.22, 0.4, 0.19], font=9)
    d.p("The qualitative agreement is that (i) forecasting demand before optimising helps, (ii) heuristic or managerial hub rules cost more than an optimised plan and (iii) adapting the "
        "network to changing demand improves service. This project does not reproduce the base paper's numbers and does not claim to.")


def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.table([["Success cases", "Evidence"],
             ["Forecast beats naive benchmarks by a wide margin", "MAPE 7.67% vs 19.71% and 17.56%"],
             ["Matheuristic reaches the optimum on 90 and 180 nodes", "Gap 0.00% and -0.05%; same hubs as CBC at 90 nodes"],
             ["Optimised plan is cheapest of six methods", "Others cost 3.6% to 16.1% more"],
             ["Re-planning protects service in the peak", "92.4% vs 64.9% fulfilment in October; 98.3% vs 83.7% average"],
             ["Everything runs from one interface", "4 tests and 18 API checks pass; 22 screens captured"]],
            "Success cases", widths=[0.5, 0.5], font=10)
    d.table([["Failure or weak case", "What happened", "Cause (as far as known)"],
             ["Peak under-forecast", "Oct 2025 forecast 13.2% low; 3 of 6 hubs above capacity; fulfilment 92.3%", "Volume above the training range; the optimiser trusts the forecast and has no safety margin"],
             ["December over-forecast", "10.2% high", "Probably the lag features still contain the October-November peak"],
             ["Large errors for some regions", "Pune, Ahmedabad and Chennai over-forecast by 39-40% in Dec 2025", "Not investigated; the post-peak drop is probably larger than the lags imply"],
             ["No gain at 90 nodes", "Same plan and similar time as the exact MIP", "The instance is small enough for CBC"],
             ["270 nodes", "Matheuristic 3.67% above the exact incumbent", "Probably the kernel of 24 candidates and the 70% time rule limit the search (not isolated by an experiment)"],
             ["Distant service", "Dehradun-N served 1,427 km away (37.7 h)", "Only six hubs; cost model favours consolidation"],
             ["Static control is simple", "A stronger static plan was not tried", "Comparison may overstate the benefit of re-planning"]],
            "Failure and weak cases", widths=[0.24, 0.4, 0.36], font=9.5)


def sec_results_limits(d):
    d.h2("Limitations of the Results")
    d.bullets([
        "All results come from one synthetic dataset and one random seed; absolute rupee values, delivery hours and fulfilment are model outputs.",
        "Fulfilment and SLA reliability are simulated capacity measures, not observed deliveries.",
        "The comparison covers a single month (October 2025); the rolling horizon covers six months; the benchmark three sizes.",
        "The base paper's real-data results are not reproduced and its robustness measure is not implemented.",
        "No confidence intervals, repeated runs or statistical tests; solve times vary by several seconds from run to run.",
    ])


def sec_objectives(d):
    d.h2("Objectives Against Outcomes")
    d.table([["Objective", "Outcome", "Status"],
             ["1 Collect and preprocess historical e-commerce logistics data", "Synthetic 90-region, 36-month dataset generated and cleaned (duplicates, gaps); real data is not available", "Met with synthetic data"],
             ["2 Predict regional demand with a Random Forest", "MAPE 7.67%, R-squared 0.9766 on held-out months; naive MAPE 17.6-19.7%", "Met"],
             ["3 Formulate hub location with cost, time and capacity constraints", "Capacitated single-allocation MIP with fixed, transport and time cost, capacity, p, optional hard SLA", "Met (single capacity level, no robustness)"],
             ["4 Solve efficiently with a matheuristic", "Optimal at 90 and 180 nodes, 4-5 times faster; 3.67% above the incumbent at 270 nodes", "Met, with a stated gap at the largest size"],
             ["5 Re-optimise as demand changes", "Rolling horizon: 98.3% vs 83.7% fulfilment, one hub change", "Met (model not retrained monthly)"],
             ["6 Compare with traditional methods", "Five baselines on the same instance; proposed is cheapest", "Met on one month; base-paper numbers not reproduced"]],
            "Objectives and outcomes", widths=[0.3, 0.5, 0.2], font=9.5)
