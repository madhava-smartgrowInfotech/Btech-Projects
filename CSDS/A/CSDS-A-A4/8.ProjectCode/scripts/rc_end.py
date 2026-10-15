"""Chapters 9 and 10 sections, references and appendices."""
from __future__ import annotations

from doc_common import CMP, EXTRA_REFS, FM, M, P, REFERENCES, RF, ROL, SCAL, SHOTS, SCREENS, inr_m, pct
from rc_method import excerpt

AD, ST = ROL["adaptive_avg"], ROL["static_avg"]


def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "This project implemented the predict-then-optimise framework of the base paper end to end. A Random Forest forecasts regional demand from lag, rolling, calendar and region "
        "features; the forecast feeds a capacitated single-allocation hub-location model; a matheuristic that combines greedy construction, a screened and MIP-priced local search and "
        "a kernel search solves it; the plan is scored on the demand that actually occurred; and the cycle is repeated month by month. A FastAPI service and a React application make "
        "the pipeline usable from a browser, and a command line and 22 captured screens document it.",
        "The work was carried out on a synthetic dataset of 90 regions and 36 months, because no real order history was available. Every number reported is read from the project's "
        "own saved models and results, and the report states where the evidence is weaker than the base paper's.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.table([["Objective", "Outcome"],
             ["1 Data collection and preprocessing", "Synthetic dataset with cleaning, de-duplication and gap filling (real data not available)"],
             ["2 Random Forest demand prediction", f"MAPE {RF['mape']:.2f}%, R-squared {RF['r2']:.4f}; naive forecasters 17.6-19.7% MAPE"],
             ["3 Optimisation model", "Capacitated MIP with cost, delivery-time and capacity constraints and an optional hard SLA"],
             ["4 Matheuristic", "Same plan as the exact MIP at 90 nodes; 4-5 times faster at 90-180 nodes; 3.67% above the exact incumbent at 270 nodes"],
             ["5 Re-optimisation", f"{pct(AD['fulfilment_rate'])} against {pct(ST['fulfilment_rate'])} simulated fulfilment for a static plan"],
             ["6 Comparison", "Proposed plan cheapest of six methods on October 2025; others cost 3.6% to 16.1% more"]],
            "Objectives achieved", widths=[0.34, 0.66], font=10)


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    d.numbered([
        f"**Forecasting before optimising pays.** Planning on the historical average instead of a forecast cost {M['fixed_avg']['cost_vs_proposed_pct']:.1f}% more and served 66.0% of the October 2025 orders, against {pct(P['fulfilment_rate'])}.",
        "**The matheuristic is exact where exactness can be checked.** It found the optimum at 90 and 180 nodes. Its advantage is speed at 180 nodes and above; at 90 nodes there was no practical gain.",
        f"**Re-planning protects service in the peak.** In October the adaptive plan kept {pct(ROL['timeline'][3]['adaptive']['fulfilment_rate'])} fulfilment against {pct(ROL['timeline'][3]['static']['fulfilment_rate'])} for the static plan.",
        "**Forecast error shows up as overload.** A 13.2% under-forecast of the peak left three of six hubs above capacity; the optimiser has no safety margin, which is the main weakness found.",
        "**Simple rules are costly.** The largest-markets rule costs 16.1% more than the optimised plan and breaches the 48 h service level for some regions.",
    ])
    from doc_common import CHARTS
    d.figure(CHARTS / "cost_by_method.png", "Operating cost by method (October 2025)", width=d.text_width * 0.9)


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.bullets([
        "Monthly review of a regional e-commerce hub network: forecast, plan and see which hubs would be overloaded.",
        "What-if analysis: change the number of hubs, capacity or service level and see the effect in seconds.",
        "Teaching: a compact, readable implementation of forecasting plus mixed-integer optimisation plus heuristic search.",
        "A benchmark harness for comparing a new hub-location heuristic with an exact solver and simple rules.",
    ])


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets([
        "Synthetic data; no calibration to a real carrier; fulfilment and reliability are simulated.",
        "No robustness analysis; the plan is not hedged against forecast error.",
        "Single capacity level, single allocation, no routing or hub-to-hub economies of scale.",
        "One hold-out split, no cross-validation or tuning; the model is not retrained monthly in the simulation.",
        "At 270 nodes the matheuristic is 3.67% above the exact incumbent; networks beyond 270 nodes were not tested.",
        "No authentication, database or multi-user support; no user acceptance study; no frontend unit tests.",
    ])


def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "**Robust plans.** Add a safety margin or a scenario-based objective so that a forecast error of 10-15% does not overload the biggest hubs (the base paper's robust direction and [5]).",
        "**Real data.** Replace the synthetic files with a real order history (same schema) and re-run the pipeline; calibrate cost parameters with a carrier.",
        "**Forecast quality.** Cross-validated tuning, gradient boosting or LSTM benchmarks, prediction intervals, and a fix for the inability of forests to extrapolate beyond past peaks (for example by forecasting growth ratios).",
        "**Solver.** Add Variable Neighbourhood Search as in the base paper, tune the kernel size and time rules, and test on 500 nodes.",
        "**Retraining.** Retrain the forecaster every month inside the rolling horizon and compare with the fixed model.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "Multiple capacity levels per hub and capacity expansion over time.",
        "Split allocation (a region served by two hubs) and hub-to-hub transport with economies of scale.",
        "Explainability: a per-region forecast explanation and a map of why a hub was chosen (as proposed in the base paper's future work).",
        "Scenario manager: save, name and compare several plans side by side; export plans to Excel or PDF.",
        "Sustainability objectives such as emissions per parcel.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.bullets([
        "Move results from files to a database with versioning so several users can plan at once.",
        "Add sign-in, roles and rate limiting; put the API behind a reverse proxy; containerise the stack.",
        "Run long jobs in a worker queue instead of threads so that jobs survive a restart and can run in parallel.",
        "Use a faster commercial or open-source solver for networks above a few hundred nodes, and parallelise the sub-problem pricing.",
        "Stream new orders from the warehouse system so that the forecast is refreshed without manual file replacement.",
    ])


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "Compare the matheuristic with VNS-based and learning-based solvers on public hub-location benchmarks.",
        "Learn the matheuristic's parameters (screening tolerance, kernel size) from the instance, as the base paper suggests for the Random Forest.",
        "Study how forecast accuracy translates into plan quality: a sensitivity analysis of cost and overload against forecast error.",
        "Integrate demand uncertainty learned from data into a two-stage robust model.",
        "Evaluate with a logistics partner on real parcel data, including delivery-time compliance measured in the field.",
    ])


def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, r in enumerate(REFERENCES + EXTRA_REFS, 1):
        p = d.p(f"[{i}]\t{r}", align="left", line=1.15, space_after=4)
        p.paragraph_format.left_indent = __import__("docx").shared.Inches(0.45)
        p.paragraph_format.first_line_indent = -__import__("docx").shared.Inches(0.45)
        p.paragraph_format.tab_stops.add_tab_stop(__import__("docx").shared.Inches(0.45))


# ---------------------------------------------------------------- appendices
def appendix_code(d):
    d.p("The listings are extracted verbatim from the source files by the document builder, so they match the delivered code.")
    d.h2("Hub-location model: instance and exact MIP")
    d.code(excerpt("hublocator/model.py", "@dataclass", "def assign_greedy"), "hublocator/model.py - Instance and objective")
    d.h2("Matheuristic")
    d.code(excerpt("hublocator/matheuristic.py", "def _bound", "def solve_matheuristic"), "hublocator/matheuristic.py - bound, price, construct")
    d.code(excerpt("hublocator/matheuristic.py", "def solve_matheuristic", "# ---- phase 3"), "hublocator/matheuristic.py - construction and local search")
    d.code(excerpt("hublocator/matheuristic.py", "# ---- phase 3"), "hublocator/matheuristic.py - kernel search and result")
    d.h2("Forecasting")
    d.code(excerpt("hublocator/forecast.py", "def train_forecaster", "def load_forecaster"), "hublocator/forecast.py - train_forecaster")
    d.h2("Evaluation")
    d.code(excerpt("hublocator/model.py", "def evaluate_solution"), "hublocator/model.py - evaluate_solution")
    d.h2("API endpoint for planning")
    d.code(excerpt("backend/main.py", "class OptimizeBody", "class CompareBody"), "backend/main.py - /api/optimize")


def appendix_install(d):
    d.h2("Prerequisites")
    d.bullets(["Windows 10 or 11 (other systems work with the manual commands).", "Python 3.10 or later and Node.js 18 or later on the PATH.", "About 1 GB of free disk space and a modern browser."])
    d.h2("One-click start (Windows)")
    d.numbered(["Open the folder `8.ProjectCode`.", "Double-click `run.bat`. It installs any missing Python and npm packages, starts the API window (port 8104), waits for `/api/health`, starts the web window (port 5104) and opens http://localhost:5104.",
                "To stop, close the two windows. If a port is already in use the script says so and exits.", "Interactive API documentation is at http://localhost:8104/docs."])
    d.h2("Using the application")
    d.table([["To do this", "Go to", "Then"],
             ["See what the data and the model look like", "Dashboard, Forecast, Regions", "Read the tiles and charts; search the regions"],
             ["Plan hubs", "Plan hubs", "Pick a month (the first entry is the next month), adjust parameters if wished, choose Matheuristic or Exact MIP, click Optimise network; read the KPIs, map, utilisation, search log and allocation table"],
             ["Compare methods", "Compare methods", "Pick a month and click Run comparison; wait for the job to finish (the page polls); switch to the Scalability tab for the benchmark"],
             ["See the effect of re-planning", "Re-optimise", "Choose the number of months and click Run rolling horizon"],
             ["Retrain the forecaster", "Forecast", "Click Retrain and confirm; a new model and metrics replace the saved ones"],
             ["Use the dark theme", "Top bar", "Click the moon icon; the choice is remembered"]],
            "User guide", widths=[0.28, 0.24, 0.48], font=9.5)
    d.h2("Command line")
    d.code("python run.py data --seed 7                          # regenerate the synthetic history\n"
           "python run.py forecast                               # train the Random Forest\n"
           "python run.py optimize --period 2025-10 --hubs 6     # plan hubs (add --exact for the exact MIP)\n"
           "python run.py compare --period 2025-10               # proposed vs traditional methods\n"
           "python run.py rolling --months 6                     # month-by-month re-optimisation\n"
           "python run.py benchmark --factors 1 2 3              # scalability benchmark\n"
           "python run.py all                                    # data -> forecast -> compare -> rolling\n"
           "python run.py serve                                  # classic Flask interface on port 5000", "commands")
    d.h2("Tests")
    d.code("python tests.py                                       # 4 tests\n"
           "python scripts/smoke_test.py                          # 18 API checks, in-process\n"
           "python scripts/smoke_test.py --url http://127.0.0.1:8104 --frontend http://localhost:5104", "test commands")
    d.h2("Troubleshooting")
    d.table([["Symptom", "Cause and remedy"],
             ["'Could not reach the HubOptima API' in the browser", "The API window is closed or on another port; start `run.bat` again or check `.env`"],
             ["Port already in use", "HubOptima may already be running; close the old windows or change the port in `.env`"],
             ["Comparison or rolling page empty", "No saved result; click the Run button on that page"],
             ["'No feasible solution'", "Use more hubs, a larger capacity factor or a soft SLA"],
             ["Plans take longer than expected", "Lower the MIP time limit or choose the matheuristic; CBC time varies with the processor load"]],
            "Troubleshooting", widths=[0.38, 0.62], font=10)


def appendix_screens(d):
    d.p("These are the screens that are not part of the main results chapter. All were captured from the running application with the project's data.")
    shown = {"03_dashboard.png", "05_forecast.png", "07_regions.png", "08_plan_parameters.png", "09_plan_kpis.png", "11_plan_map.png", "12_plan_searchlog.png",
             "13_plan_next_month.png", "14_plan_exact.png", "16_compare_full.png", "17_compare_scalability.png", "19_rolling.png", "20_rolling_full.png"}
    for f, cap, desc in SCREENS:
        if f in shown:
            continue
        d.figure(SHOTS / f, cap, width=d.text_width * 0.98, max_h=3.9)
        d.p(desc, size=11)
