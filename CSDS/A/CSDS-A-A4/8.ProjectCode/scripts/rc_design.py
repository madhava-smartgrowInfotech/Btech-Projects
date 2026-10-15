"""Chapter 5 sections: system design (architecture, workflow, DFDs, UML, data model, modules, user interface)."""
from __future__ import annotations

from doc_common import DIAG, SHOTS

ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "uml", "usecase", "sequence", "er", "flowchart"]

DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of HubOptima",
                     ["The architecture has five layers. The *user* works in a browser, or a developer uses the command line. The *frontend* is a React application "
                      "served by Vite on port 5104; it holds the seven pages, the SVG network map, the charts, the theme and the small data layer (`api.js`, `useApi`, `usePoll`) "
                      "that polls background jobs.",
                      "The *API layer* is a FastAPI service on port 8104 with 14 endpoints. It validates request bodies with pydantic, runs long jobs in a thread guarded by a lock, "
                      "and converts numpy values to JSON (NaN and infinity become null). The *core package* `hublocator` contains all of the science: data preparation, the Random Forest, "
                      "the hub model and exact solver, the matheuristic, the baselines and the rolling-horizon simulation. No forecasting or optimisation logic lives in the API layer.",
                      "The bottom layer holds the libraries (scikit-learn, PuLP with CBC) and the files that act as storage: two CSV files in `data/`, the trained model and metrics in "
                      "`models/` and the result files in `results/`. The command line calls the core package directly, which is why the dotted line bypasses the web tiers."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow",
                 ["The ten steps are the predict-then-optimise loop. Steps 1 to 5 prepare the data and produce a demand forecast; steps 6 and 7 turn the forecast into a hub-location "
                  "model and solve it; step 8 scores the plan on the demand that actually occurred; step 9 compares methods and re-plans month by month; step 10 presents the "
                  "outcome. The dashed arrow shows the cycle: when a new month of data arrives the forecast is recomputed, the model is rebuilt and the network is re-optimised."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context)",
             ["The context diagram shows HubOptima as one process with three external entities. The *logistics planner* supplies the planning month, the number of hubs, cost and "
              "service parameters and the method, and receives forecasts, hub plans, KPIs, comparisons and rolling results. The *data files* supply the region master and the order "
              "history. The *CBC solver* receives mixed-integer sub-problems and returns optimal or feasible assignments."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1",
             ["Level 1 splits the system into nine processes and four data stores. Process 1 reads `regions.csv` and `demand_history.csv` (D1, D2), cleans them and passes features to "
              "process 2, which trains the Random Forest and writes the model and its metrics (D3). Process 3 forecasts next month's demand from the model and the history. "
              "Process 4 builds the hub-location instance from the forecast and the planner's parameters; process 5 solves it; process 6 evaluates the KPIs on realised demand. "
              "Processes 7 (comparison and scalability) and 8 (rolling horizon) re-run processes 3 to 6 for each method or month and store their results in D4. Process 9 presents "
              "everything to the planner."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: solving the hub-location problem",
             ["Level 2 opens process 5. The start set is constructed greedily (5.1), moves are generated (5.2) and screened with a cheap greedy cost bound (5.3), the promising ones are "
              "priced by an exact assignment MIP solved by CBC (5.4), and the first improving move is accepted (5.5) and triggers a restart. When no move helps, or 70% of the time "
              "limit is used, a kernel search solves the full MIP restricted to about 24 promising hubs (5.6) and the best plan is returned (5.7). A cache of priced hub sets avoids solving "
              "the same sub-problem twice."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram",
            ["The core is the `Instance` dataclass, which holds the regions, the demand vector, the distance matrix and the parameters and derives the delivery time, the unit cost, the "
             "fixed cost per hub and the capacity. The functional modules `model.py`, `matheuristic.py`, `baselines.py` and `rolling.py` all take an `Instance`. `forecast.py` owns the "
             "RandomForestRegressor and `data.py` supplies the data. `config.py` holds the defaults. The FastAPI application only calls these modules; it defines the three request "
             "bodies and the job table."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram",
                ["The logistics planner browses the dashboard and regions, views and retrains the forecast, plans hubs, compares methods, runs the scalability benchmark, re-optimises over time "
                 "and switches the theme. The developer or analyst uses the command line for the same functions and for regenerating the data, and may call the JSON API directly. The CBC "
                 "solver is a system actor used by planning, comparison and re-optimisation."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram of the main flow: planning hubs",
                 ["The planner chooses a month, the number of hubs and a method and clicks Optimise. The React page posts the body to `/api/optimize`. FastAPI validates it, obtains the "
                  "forecast for that month using only earlier data, builds the `Instance`, and runs the matheuristic, which calls CBC for the assignment sub-problems. The result is "
                  "scored on the realised demand by `evaluate_solution` and returned as JSON, which the page turns into KPI tiles, the network map, hub utilisation, the search log and the "
                  "allocation table."]),
    "er": ("06_er_diagram.png", "Entity-relationship diagram of the file-based data model",
           ["HubOptima does not use a database. Its data are two CSV files, a joblib model with a JSON metrics file, and JSON result files. The diagram shows them as entities "
            "so that the relationships are explicit. A *region* has many monthly *demand-history* rows (primary key region and period). The forecast model is trained from the demand "
            "history and predicts a *forecast* per region, which is derived and not stored. The result files (method results with their region-to-hub assignments, rolling-horizon months "
            "and scalability runs) are produced by the optimiser from forecasts and hold region names rather than foreign keys."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowchart of the core algorithm: the matheuristic",
                  ["The instance is built and a start set is constructed by a greedy weighted k-medoids rule followed by medoid refinement. It is priced by an exact assignment MIP; if it is "
                   "infeasible, more hubs are opened by demand until it is feasible. The local search then ranks closed candidates, builds swap, drop and add moves, screens them with a "
                   "greedy bound, and prices the best-screened move; a cheaper plan is accepted (first improvement) and the search restarts. When no promising move remains or 70% of the "
                   "time is spent, the kernel search polishes the result and the best plan is returned."]),
}


def diagram(d, key, width=None):
    f, cap, paras = DIAGRAMS[key]
    d.figure(DIAG / f, cap, width=width or d.text_width * 0.98, max_h=7.2)
    d.paras(*paras)


def sec_arch(d):
    d.h2("System Architecture")
    diagram(d, "architecture")
    d.p("**Design principles.** (1) One implementation of the science: the command line, the classic Flask interface and the FastAPI service import the same package. "
        "(2) Files as storage: the artefacts a planner would want to inspect or replace (the CSV inputs, the model, the JSON results) stay readable files. "
        "(3) Thin API: it validates, runs jobs and serialises; it never decides anything about hubs. (4) Honest evaluation: the evaluation function takes the realised demand "
        "separately from the planning demand, so capacity overload is visible.")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfds(d):
    d.h2("Data-Flow Diagrams")
    diagram(d, "dfd0")
    diagram(d, "dfd1")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    diagram(d, "uml")
    diagram(d, "usecase")
    diagram(d, "sequence")


def sec_database(d):
    d.h2("Data Model and Storage Design")
    d.p("The system keeps its data in files. This was a deliberate choice: the order history of a regional network (3,240 rows here) is small, "
        "the artefacts are easier to inspect and replace as files, and no server process or credentials are needed. The consequence is that "
        "there are no transactions and no multi-user access; background jobs overwrite result files.")
    diagram(d, "er")
    d.table([["File", "Fields", "Rows / size", "Written by"],
             ["data/regions.csv", "region_id, city, state, lat, lon, population (millions), tier (1-3), parent, penetration", "90 rows", "python run.py data"],
             ["data/demand_history.csv", "region_id, period (YYYY-MM), year, month, orders, promo, avg_order_value, avg_parcel_weight_kg, return_rate", "3,240 rows (90 x 36)", "python run.py data"],
             ["models/rf_demand.joblib", "the fitted RandomForestRegressor and its 19 feature names", "38.5 MB", "train_forecaster"],
             ["models/forecast_metrics.json", "trained_at, train/test rows and periods, metrics of three forecasters, feature importance, December 2025 per-region detail", "about 12 KB", "train_forecaster"],
             ["results/comparison.json", "parameters, forecast and realised totals, and for each of six methods the hubs, costs, KPIs, utilisation and the 90-row allocation", "about 118 KB", "run_comparison"],
             ["results/rolling.json", "per month: forecast and realised totals, hubs, opened and closed hubs, adaptive and static KPIs; averages", "about 6 KB", "rolling_reoptimisation"],
             ["results/scalability.json", "per instance size: binary variables, matheuristic and exact time and objective, gap, exact status", "about 1 KB", "scalability_benchmark"]],
            "Files that form the data model", widths=[0.2, 0.46, 0.17, 0.17], font=9)
    d.p("**Integrity rules in code.** `load_dataset` drops duplicate (region, period) rows, coerces `orders` to numbers, sorts by region and period, "
        "interpolates gaps inside each region and drops rows that remain empty. `tier` and `penetration` receive defaults if absent, and `year` and `month` "
        "are derived from `period` if missing. These guards are not exercised by the generated data, which has no gaps, but they make a real file usable.")


def sec_modules(d):
    d.h2("Module Breakdown")
    d.table([["Module", "Lines", "Responsibility", "Main functions"],
             ["config.py", "31", "Paths, random state, default model parameters", "DEFAULTS, RANDOM_STATE"],
             ["data.py", "177", "Dataset generation, loading, preprocessing, distances, summary", "generate_dataset, load_dataset, distance_matrix, dataset_summary, haversine_km"],
             ["forecast.py", "145", "Features, Random Forest training and evaluation, forecasting", "build_features, train_forecaster, forecast_next_period, forecast_for_period"],
             ["model.py", "203", "Instance, exact MIP, assignment sub-MIP, greedy assignment, KPI evaluation", "Instance, solve_exact, assign_exact, assign_greedy, evaluate_solution"],
             ["matheuristic.py", "167", "Construction, MIP-priced local search, kernel search", "construct, solve_matheuristic, _bound, _price"],
             ["baselines.py", "121", "Traditional methods and the comparison runner", "solve_greedy, solve_kmeans, solve_largest_markets, run_comparison"],
             ["rolling.py", "140", "Rolling-horizon simulation and the scalability benchmark", "rolling_reoptimisation, inflate_network, scalability_benchmark"],
             ["webapp.py", "349", "Original Flask interface and JSON API (port 5000)", "create_app and five routes"],
             ["backend/main.py", "272", "FastAPI layer for the React application (port 8104)", "14 endpoints, start_job, clean"],
             ["run.py / tests.py", "135 / 72", "Command-line entry point and smoke tests", "cmd_data ... cmd_serve; test_data ... test_webapp"],
             ["frontend/src", "4,235", "React application: 7 pages, UI kit, charts, SVG map, theme", "pages/*.jsx, components/ui, lib/api.js, useApi.js"]],
            "Modules, sizes and responsibilities", widths=[0.17, 0.08, 0.4, 0.35], font=9)


def sec_ui(d):
    d.h2("User Interface Design")
    d.p("The web application is a single-page React application with a persistent sidebar (Dashboard, Forecast, Plan hubs, Compare methods, Re-optimise, Regions), "
        "a top bar showing the API and solver status, and a light and a dark theme. The theme follows the operating-system setting until the user chooses and is then "
        "remembered in the browser. The visual style, called 'Soft Pastel Calm' in the project documents, uses soft colours, rounded cards and short animations; animations "
        "respect the reduced-motion setting of the operating system (the SVG map uses `useReducedMotion`).")
    d.table([["Route", "Page", "What the user can do"],
             ["/", "Landing", "Read the pipeline in five steps and the headline results; open the app"],
             ["/app", "Dashboard", "See the dataset size, forecaster accuracy and the monthly volume chart"],
             ["/app/forecast", "Forecast", "Compare the Random Forest with the naive forecasters, see feature importance, search the next-month forecast per region, view the December back-test, retrain"],
             ["/app/plan", "Plan hubs", "Set the month and parameters, choose matheuristic or exact, run, and read KPIs, the network map, utilisation, cost split, search log and allocation table"],
             ["/app/compare", "Compare methods", "Run the six-method comparison for a month or the scalability benchmark in the background; see tables and charts"],
             ["/app/rolling", "Re-optimise", "Run the rolling horizon for 2-12 months; see fulfilment and cost by month and the hub changes"],
             ["/app/regions", "Regions", "Search and filter the 90 regions; see where demand sits on a map"]],
            "Pages of the web application", widths=[0.16, 0.16, 0.68], font=9.5)
    d.h3("Interaction details")
    d.bullets([
        "**Validation before sending.** The planning form checks every numeric field against the same ranges as the API (for example p between 1 and 20) and shows the message under the field.",
        "**Progress and errors.** While a plan is computed the page shows the four pipeline steps (forecast demand, build the model, solve, score) and the elapsed time; an infeasible plan produces an explanation rather than an empty page; a network error says that the API on port 8104 could not be reached.",
        "**Background jobs.** Comparison, scalability and rolling runs return immediately and the page polls `/api/jobs` every two seconds until the job finishes.",
        "**Shared state.** The Plan page keeps the last plan and form while the user visits other pages.",
        "**Internet.** The only external request is the Google Fonts stylesheet declared in `index.html`; without a connection the browser falls back to system fonts and the application works unchanged.",
    ])
