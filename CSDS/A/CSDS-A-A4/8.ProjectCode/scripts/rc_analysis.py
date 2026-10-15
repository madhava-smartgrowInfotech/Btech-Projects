"""Chapters 3 and 4 sections: feasibility study, system requirements and analysis."""
from __future__ import annotations

from doc_common import HW, LATENCY, M, OPT_LAT, P, SCAL, inr_m


def sec_feasibility(d):
    d.h2("Technical Feasibility")
    d.paras(
        "The technology needed by the project is mature and free. Demand forecasting uses scikit-learn's RandomForestRegressor [13]; the "
        "optimisation models are written with PuLP [14] and solved by the CBC branch-and-cut solver [15] that PuLP bundles, so no commercial "
        "solver licence is needed; the API uses FastAPI and uvicorn, and the user interface uses React and Vite.",
        f"The feasibility of the computation was checked by measurement on a desktop machine ({HW}). Training the Random Forest on 2,430 rows "
        "takes under one second; a 90-region plan takes about 3 to 12 seconds end to end depending on the method and the parameters; the "
        "270-node scalability instance (73,170 binary variables) is solved by the matheuristic in about 31 seconds, while the exact MIP did not "
        "finish within 67 seconds. The measured results are in Chapter 8.")
    d.table([["Requirement", "Technology", "Evidence it works"],
             ["Demand forecasting", "scikit-learn 1.4.2 Random Forest", "MAPE 7.67% on 540 held-out region-months"],
             ["Mixed-integer optimisation", "PuLP 3.3.2 + CBC", "Exact plan for 90 regions in 8-15 s; optimal status reported"],
             ["Heuristic search", "Python + NumPy 1.26.4", "Matheuristic solves the same instance in 4.9 s (solver time)"],
             ["API", "FastAPI 0.110.0 + uvicorn 0.29.0", "18 smoke checks pass"],
             ["User interface", "React 18.3.1 + Vite 5.4.11", "7 routes captured with real data"]],
            "Technical feasibility: needs and evidence", widths=[0.26, 0.34, 0.4], font=9.5)

    d.h2("Economic Feasibility")
    d.paras(
        "Every software component is open source (scikit-learn, pandas and NumPy under BSD licences, PuLP and React under MIT, CBC under the "
        "Eclipse Public License), so the project has no licence cost. It runs on a standard desktop; no GPU, server or cloud service is needed. "
        "The development cost is the students' time.",
        "The economic case for the *method* is a modelled one. In the model's own units, the proposed plan for October 2025 costs "
        f"{inr_m(P['total_cost'])} per month; the greedy plan would cost {inr_m(M['greedy']['total_cost'])}, k-means {inr_m(M['kmeans']['total_cost'])}, "
        f"the largest-markets rule {inr_m(M['largest']['total_cost'])} and planning on the historical average {inr_m(M['fixed_avg']['total_cost'])}. "
        "The differences, INR 2.3 M to INR 10.0 M per month, are produced by cost parameters that are plausible but not taken from a real carrier, "
        "so they show the *direction and relative size* of the benefit and not a forecast of real savings.")

    d.h2("Operational Feasibility")
    d.bullets([
        "**Users.** A logistics planner uses a browser; the interface asks only for a month, the number of hubs and a few cost parameters, all with defaults.",
        "**Installation.** One command installs the Python packages (`pip install -r backend/requirements.txt`), one script (`run.bat`) starts both servers and opens the browser.",
        "**Data.** Replacing `data/regions.csv` and `data/demand_history.csv` with real files of the same schema is enough to run the pipeline on real data; preprocessing already removes duplicates and fills gaps.",
        "**Maintenance.** The code is split into six small modules (data, forecast, model, matheuristic, baselines, rolling) with a shared configuration file.",
        "**Limits.** There is no sign-in, so the application must run on a trusted machine; this is acceptable for a desktop planning tool but not for shared hosting.",
    ])

    d.h2("Schedule Feasibility")
    d.p("The project was carried out between September and October 2026. The dates below are the dates recorded in the repository history and "
        "on the artefacts, not a retrospective plan.")
    d.table([["Date (2026)", "Milestone", "Evidence"],
             ["21 Sep", "Project folder, base-paper record and the first code drop", "repository history"],
             ["22 Sep", "Synthetic dataset generated (90 regions x 36 months)", "data/*.csv file dates"],
             ["26 Sep", "Random Forest trained, forecast metrics saved", "models/forecast_metrics.json (trained_at)"],
             ["14 Oct", "Comparison, rolling and scalability results regenerated; React/FastAPI application completed", "results/*.json; frontend commit"],
             ["15 Oct", "Tests re-run, screenshots, diagrams, charts and the submission documents produced", "docs/, scripts/, this report"]],
            "Project milestones from the repository history", widths=[0.15, 0.55, 0.3], font=10)

    d.h2("Advantages and Constraints")
    d.table([["Advantages", "Constraints"],
             ["Free, open-source stack; no licence cost", "Synthetic data; no real-world calibration"],
             ["Runs offline on one desktop; plans in seconds", "No robustness analysis; plan trusts the forecast"],
             ["Same code from command line, API and browser", "Single user; no authentication or database"],
             ["Reproducible: fixed seed, saved models and results", "Matheuristic slightly worse than exact at 270 nodes (+3.67%)"],
             ["Exact MIP available as a baseline in the same tool", "Exact MIP needs minutes beyond about 180 nodes"]],
            "Advantages and constraints", widths=[0.5, 0.5], font=10)


def sec_existing(d):
    d.h2("Existing System and its Limitations")
    d.paras(
        "In practice, hub networks are planned in one of four ways. Managers choose hubs by judgement, usually at the largest markets; analysts "
        "solve an exact model such as a mixed-integer program once for a fixed demand; teams run greedy or clustering heuristics that are fast but "
        "give no quality guarantee; and the demand forecast, if one exists, is produced by a different team and is not connected to the location model.")
    d.bullets([
        "Exact models become computationally expensive for large logistics networks (the 270-node instance of this project was not solved by CBC within 67 s).",
        "Fixed-demand assumptions do not reflect fluctuating e-commerce orders (a plan on the historical average served 66.0% of October 2025 orders).",
        "Hub configurations are not updated when demand or operating conditions change (a static plan averaged 83.7% against 98.3% for re-planning).",
        "Separating forecasting from optimisation leads to sub-optimal hub decisions.",
        "Pure heuristics do not guarantee solution quality (the greedy plan cost 11.5% more than the proposed plan on the same instance).",
    ])


def sec_proposed(d):
    d.h2("Proposed System and its Advantages")
    d.p("HubOptima connects the four steps into one pipeline: it cleans and loads the order history, trains a Random Forest, forecasts next "
        "month's demand per region, builds a capacitated hub-location model from the forecast, solves it with a matheuristic (or the exact "
        "MIP on request), scores the plan on realised demand and repeats the cycle each month. A web application exposes every step.")
    d.bullets([
        "Forecast and optimisation are one pipeline, so the plan always uses the latest forecast.",
        "The matheuristic reaches the exact optimum on the 90- and 180-node instances and keeps solving where the exact MIP stalls.",
        "Re-optimisation each month follows demand: one hub was moved in the six simulated months (Kolkata-W to Kolkata for the October peak).",
        "Plans are evaluated on the demand that actually occurred, which exposes overloaded hubs instead of hiding them.",
        "Baselines are built in, so any plan can be compared with the methods used today.",
    ])


def sec_requirements(d):
    d.h2("Functional Requirements")
    d.table([["ID", "Requirement", "Where it is met"],
             ["FR1", "Load and preprocess regions and order history; show a dataset summary", "data.py: load_dataset, dataset_summary; GET /api/summary, /api/regions; Dashboard and Regions pages"],
             ["FR2", "Train and evaluate a Random Forest against naive forecasters; allow retraining", "forecast.py; POST /api/train; Forecast page"],
             ["FR3", "Forecast the next month and back-test a past month using only earlier data", "forecast_next_period, forecast_for_period; GET /api/forecast"],
             ["FR4", "Plan hubs for a chosen month with p, capacity, costs, SLA (soft or hard), method and time limit", "POST /api/optimize; Plan hubs page"],
             ["FR5", "Solve with the matheuristic or the exact MIP", "matheuristic.py, model.py: solve_exact"],
             ["FR6", "Report cost, delivery time, fulfilment, SLA reliability, utilisation and the allocation per region", "model.py: evaluate_solution; Plan hubs page"],
             ["FR7", "Compare the proposed method with the traditional methods on the same month", "baselines.py: run_comparison; POST /api/compare/run; Compare page"],
             ["FR8", "Benchmark scalability of exact MIP against the matheuristic", "rolling.py: scalability_benchmark; Compare page, Scalability tab"],
             ["FR9", "Simulate month-by-month re-optimisation against a static plan", "rolling.py: rolling_reoptimisation; POST /api/rolling/run; Re-optimise page"],
             ["FR10", "Run long jobs in the background and report their status", "backend/main.py: start_job, GET /api/jobs; usePoll in the frontend"],
             ["FR11", "Provide the same functions from a command line", "run.py: data, forecast, optimize, compare, rolling, benchmark, serve, all"]],
            "Functional requirements", widths=[0.08, 0.52, 0.4], font=9.5)
    d.h2("Non-Functional Requirements")
    d.table([["ID", "Requirement", "How it is addressed"],
             ["NFR1 Performance", "Plan for 90 regions in seconds; forecast in under a second", f"Median {OPT_LAT[0][1]} (matheuristic) and {OPT_LAT[1][1]} (exact) end to end; forecast {LATENCY[3][1]} ms"],
             ["NFR2 Reproducibility", "Same data and seed give the same results", "random_state 42; saved model and result files; seeded dataset"],
             ["NFR3 Usability", "Defaults for every parameter; validation messages; light and dark themes", "Plan form validated in the browser and by the API; theme remembered per browser"],
             ["NFR4 Reliability", "Reject bad input; explain infeasible plans", "pydantic limits (p 1-20, SLA > 0, time limit 2-300 s); 'No feasible solution' message"],
             ["NFR5 Portability", "Run on a Windows desktop without admin tools", "Python 3.10+ and Node 18+; run.bat; CBC bundled with PuLP"],
             ["NFR6 Maintainability", "Small modules and shared configuration", "Six core modules of 120-205 lines; config.py"],
             ["NFR7 Security", "Limit exposure of the API", "CORS limited to the web port; no secrets stored; no sign-in (stated limitation)"]],
            "Non-functional requirements", widths=[0.2, 0.36, 0.44], font=9.5)
    d.h2("Hardware Requirements")
    d.table([["Item", "Minimum", "Used for the measurements"],
             ["Processor", "Any 64-bit dual-core CPU", "Intel Core i5-12500, 6 cores / 12 threads"],
             ["Memory", "4 GB", "15.7 GB"],
             ["Disk", "1 GB free (38.5 MB model file plus the npm packages)", "SSD"],
             ["GPU", "Not needed", "Not used"],
             ["Display", "1280 x 720", "1440 x 900 for screenshots"]],
            "Hardware requirements", widths=[0.2, 0.42, 0.38], font=10)
    d.h2("Software Requirements")
    d.table([["Software", "Version used", "Purpose"],
             ["Python", "3.11.9 (3.10 or later)", "Core package, API, scripts"],
             ["pandas / NumPy", "2.2.1 / 1.26.4", "Data handling"],
             ["scikit-learn / joblib", "1.4.2 / 1.3.2", "Random Forest, k-means, model persistence"],
             ["PuLP + CBC", "3.3.2", "Mixed-integer optimisation"],
             ["Flask", "3.1.0", "Original classic web interface (port 5000)"],
             ["FastAPI / uvicorn", "0.110.0 / 0.29.0", "JSON API (port 8104)"],
             ["Node.js / npm", "v24.19.0 (18 or later)", "Frontend tooling"],
             ["React / Vite / recharts", "18.3.1 / 5.4.11 / 2.13.3", "Web application (port 5104)"],
             ["Browser", "Chrome (any current browser)", "Using and capturing the application"]],
            "Software requirements", widths=[0.28, 0.32, 0.4], font=10)
    d.h2("User Roles and Constraints")
    d.p("HubOptima has a single user role, the *logistics planner*, who may view every page and run every action; a second kind of user, the "
        "*developer or analyst*, uses the command line. There is no sign-in and no administrator role, because the application is intended to run "
        "on the planner's own machine.")
    d.bullets([
        "Only one background job per kind (comparison/scalability, rolling horizon, training) runs at a time; a second request returns HTTP 409.",
        "Comparison, rolling and training runs overwrite the saved files in `models/` and `results/`.",
        "A planning month must be the next month or one of the history months after the first three (the forecaster needs lags).",
        "The exact MIP time limit is capped at 300 s; a plan with a hard SLA may be infeasible and is then reported as such.",
    ])
