"""Shared facts for the submission documents. Every figure here is read from the project's own artefacts
(models/forecast_metrics.json, results/*.json, data/*.csv) or comes from docs/REPORT_FACTS.md."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
CHARTS = ROOT / "docs" / "charts"
PAPER = ROOT / "docs" / "paper"

PRODUCT = "HubOptima"
TITLE = "Advanced Optimization in E-Commerce Logistics: Combining Matheuristics With Random Forests for Hub Location Efficiency"
SHORT_TITLE = "Matheuristics and Random Forests for Hub Location"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A4 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "[GUIDE NAME]"
GUIDE_DESIG = "[DESIGNATION]"

STUDENTS = [
    ("CH.ARCHANA", "23K91A6745"),
    ("A.MEENAKSHI", "23K91A6705"),
    ("B.ARUN", "23K91A6734"),
    ("A.SAMPATH", "23K91A6712"),
]

# ---------------------------------------------------------------- measured artefacts
FM = json.loads((ROOT / "models" / "forecast_metrics.json").read_text())
CMP = json.loads((ROOT / "results" / "comparison.json").read_text())
ROL = json.loads((ROOT / "results" / "rolling.json").read_text())
SCAL = json.loads((ROOT / "results" / "scalability.json").read_text())
DEM = pd.read_csv(ROOT / "data" / "demand_history.csv")
REG = pd.read_csv(ROOT / "data" / "regions.csv")
M = CMP["methods"]
RF, B1, B3 = FM["random_forest"], FM["baseline_last_value"], FM["baseline_moving_avg_3"]
P = M["proposed"]


def inr_m(v, nd=1):
    return f"INR {v / 1e6:.{nd}f} M"


def pct(v, nd=1):
    return f"{v * 100:.{nd}f}%"


METHOD_ROWS = [("proposed", "RF forecast + matheuristic (proposed)"), ("exact_mip", "RF forecast + exact MIP (CBC)"), ("greedy", "RF forecast + greedy heuristic"),
               ("kmeans", "RF forecast + k-means clustering"), ("largest", "Largest-markets rule (no optimisation)"),
               ("fixed_avg", "Historical-average demand + matheuristic (no forecast)")]

HW = "Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, Python 3.11.9, Node.js v24.19.0"

LATENCY = [("GET /api/health", 10, "2-27", 20), ("GET /api/summary", 30, "4-37", 20), ("GET /api/regions", 16, "2-32", 20),
           ("GET /api/forecast (next month, 90 regions)", 264, "200-343", 10), ("GET /api/forecast/metrics", 4, "2-24", 10),
           ("GET /api/compare", 11, "8-35", 10), ("GET /api/rolling", 3, "2-14", 10), ("GET /api/scalability", 2, "1-30", 10)]
OPT_LAT = [("POST /api/optimize, matheuristic, Oct 2025, p = 6", "12.2 s", "9.2-13.4 s", 5), ("POST /api/optimize, exact MIP, Oct 2025, p = 6", "15.3 s", "13.4-15.7 s", 3),
           ("POST /api/optimize, matheuristic, next month, p = 6", "10.7 s", "9.6-13.2 s", 5), ("POST /api/optimize, matheuristic, Dec 2025, p = 4", "3.4 s", "3.2-4.1 s", 5)]

SMOKE_CHECKS = [("health", "status ok, solver reported (CBC via PuLP)"), ("summary: dataset", "90 regions x 36 months"), ("summary: forecaster trained", "model file present"),
                ("regions with coordinates", "90 rows with latitude and longitude"), ("options", "next month first in the list, defaults present"),
                ("forecast (original contract)", "2026-01: 1,788,825 orders, 90 regions"), ("forecast metrics", "MAPE present, city names attached"),
                ("compare (original contract)", "proposed method present"), ("scalability", "list returned"), ("rolling (original contract)", "timeline present"),
                ("optimize: matheuristic on a past month", "4 hubs for Dec 2025, scored on realised demand"), ("optimize: allocation covers every region", "90 assignments"),
                ("optimize: next month on forecast", "scored on the forecast, not realised demand"), ("optimize: exact MIP", "status Optimal"),
                ("optimize: hard-SLA edge case", "1 hub, 5 h hard SLA: answered cleanly (plan, reliability 0.1957)"),
                ("optimize: validation rejects n_hubs = 0", "HTTP 422"), ("optimize: unknown month rejected", "HTTP 400"), ("jobs status", "compare and rolling jobs listed")]

# ---------------------------------------------------------------- references (IEEE style; verified entries only)
BASE_PAPER = ('K. Danach, A. Rammal, I. Moukadem, H. Harb, and A. Nasser, "Advanced optimization in e-commerce logistics: Combining matheuristics '
              'with random forests for hub location efficiency," IEEE Access, vol. 13, pp. 55915-55926, 2025, doi: 10.1109/ACCESS.2025.3550560.')
REFERENCES = [
    BASE_PAPER,
    'L. Zheng, G. Xu, and W. Chen, "Using improved particle swarm optimization algorithm for location problem of drone logistics hub," Computers, Materials & Continua, vol. 78, no. 1, pp. 935-957, 2024, doi: 10.32604/cmc.2023.046006.',
    'L. Yang, J. Zheng, J. Wang, and X. Hu, "The maximal detour liner shipping hub location problem: Improving the applicability of the p-hub center problem," Transportation Research Part E: Logistics and Transportation Review, vol. 179, Art. no. 103330, Nov. 2023, doi: 10.1016/j.tre.2023.103330.',
    'M. Dehghan Chenary, A. Ferdowsi, and R. F. Hartl, "A Pareto-based clustering approach for solving a bi-objective mobile hub location problem with congestion," Logistics, vol. 8, no. 4, Art. no. 130, Dec. 2024, doi: 10.3390/logistics8040130.',
    'H. Zhang, J.-C. Wang, and Y. Gao, "Two-stage adaptive robust hub location problem under demand uncertainty," Naval Research Logistics, Dec. 2025, doi: 10.1002/nav.70043.',
    "M. E. O'Kelly, \"The location of interacting hub facilities,\" Transportation Science, vol. 20, no. 2, pp. 92-106, 1986.",
    'J. F. Campbell, A. T. Ernst, and M. Krishnamoorthy, "Hub location problems," in Facility Location: Applications and Theory. Berlin, Germany: Springer, 2002, pp. 373-407.',
    'A. T. Ernst and M. Krishnamoorthy, "Efficient algorithms for the uncapacitated single allocation p-hub median problem," Location Science, vol. 4, no. 3, pp. 139-154, Oct. 1996.',
    'K. Danach, S. Gelareh, and R. Neamatian Monemi, "The capacitated single-allocation p-hub location routing problem: A Lagrangian relaxation and a hyper-heuristic approach," EURO Journal on Transportation and Logistics, vol. 8, no. 5, pp. 597-631, Dec. 2019.',
    'M. Kahalimoghadam, R. G. Thompson, and A. Rajabifard, "Determining the number and location of micro-consolidation centres as a solution to growing e-commerce demand," Journal of Transport Geography, vol. 117, Art. no. 103875, May 2024.',
    'L. Breiman, "Random forests," Machine Learning, vol. 45, no. 1, pp. 5-32, Oct. 2001.',
    'V. Maniezzo, M. A. Boschetti, and T. Stuetzle, Matheuristics: Algorithms and Implementations. Cham, Switzerland: Springer, 2021.',
    'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.',
    'S. Mitchell, M. O\'Sullivan, and I. Dunning, "PuLP: A linear programming toolkit for Python," Dept. of Engineering Science, University of Auckland, 2011.',
    'J. Forrest and R. Lougee-Heimer, "CBC user guide," in Emerging Theory, Methods, and Applications, INFORMS TutORials in Operations Research, 2005, pp. 257-277.',
    'P. Hansen and N. Mladenovic, "Variable neighborhood search: Principles and applications," European Journal of Operational Research, vol. 130, no. 3, pp. 449-467, May 2001.',
    'E. Angelelli, R. Mansini, and M. G. Speranza, "Kernel search: A general heuristic for the multi-dimensional knapsack problem," Computers & Operations Research, vol. 37, no. 11, pp. 2017-2026, Nov. 2010.',
    'S. P. Lloyd, "Least squares quantization in PCM," IEEE Transactions on Information Theory, vol. 28, no. 2, pp. 129-137, Mar. 1982.',
    'R. J. Hyndman and G. Athanasopoulos, Forecasting: Principles and Practice, 3rd ed. Melbourne, Australia: OTexts, 2021.',
    'R. W. Sinnott, "Virtues of the haversine," Sky and Telescope, vol. 68, no. 2, p. 159, 1984.',
]
EXTRA_REFS = [
    'S. Ramirez, "FastAPI documentation." [Online]. Available: https://fastapi.tiangolo.com',
    'Meta Platforms, "React documentation." [Online]. Available: https://react.dev',
]
# reference numbers used in the text
R_BASE, R_ZHENG, R_YANG, R_CHEN, R_ZHANG, R_OKELLY, R_CAMP, R_ERNST, R_DANACH19, R_KAHAL = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
R_BREIMAN, R_MATH, R_SKL, R_PULP, R_CBC, R_VNS, R_KERNEL, R_LLOYD, R_HYND, R_HAV = 11, 12, 13, 14, 15, 16, 17, 18, 19, 20

# ---------------------------------------------------------------- screenshots: file, caption, what it shows
SCREENS = [
    ("01_landing.png", "Landing page", "The product landing page: the headline, a preview of the planned network (INR 62.2 M per month) and the key claims (90 regions, Random Forest MAPE 7.67%, +14.6 points of fulfilment against a static plan)."),
    ("02_landing_pipeline.png", "Landing page: the pipeline", "The landing section that explains the pipeline in five steps: historical orders, Random Forest forecast, hub-location model, matheuristic solve and monthly re-optimisation."),
    ("03_dashboard.png", "Dashboard", "Network overview: 90 regions, 36 months, 48.3 M orders in the dataset, Random Forest MAPE 7.67% (R-squared 0.9766) and the monthly order volume with the October-November festival peaks."),
    ("05_forecast.png", "Forecast page", "Random Forest against the two naive forecasters on the 540 held-out region-months, with the training-run details."),
    ("06_forecast_full.png", "Forecast page (full)", "The whole forecast page: accuracy tiles, forecaster comparison, feature importance, the January 2026 forecast per region (1,788,825 orders in total) and the December 2025 back-test (mean error 8.9% across 90 regions)."),
    ("07_regions.png", "Regions page", "The 90 demand regions (30 cities and 60 satellite districts, 20 states) with search and filters, population, average monthly orders and a map of where demand sits."),
    ("08_plan_parameters.png", "Plan hubs: parameters", "The planning form: month, maximum hubs p = 6, capacity factor 1.25, transport rate, fixed hub cost, time penalty, SLA, time limit, method and hard/soft SLA."),
    ("09_plan_kpis.png", "Plan hubs: result KPIs", "Oct 2025 plan from the matheuristic: 6 hubs, INR 62.2 M per month, 8.6 h average delivery, 92.3% fulfilment and 92.3% within the 48 h SLA on realised demand, solved in 9.23 s."),
    ("10_plan_full.png", "Plan hubs: complete result", "The full result page: KPI tiles, network map, hub utilisation, cost split, search log and the region allocation table."),
    ("11_plan_map.png", "Plan hubs: network map and cost split", "Squares are hubs, circles are regions sized by demand and coloured by their hub; the cost split is INR 15.75 M fixed, 15.82 M transport and 30.59 M time penalty."),
    ("12_plan_searchlog.png", "Plan hubs: search log and allocation", "How the matheuristic improved the objective: construction INR 61.5 M, then two local-search swaps to INR 57.7 M planned cost; below it the allocation of each region to its hub."),
    ("13_plan_next_month.png", "Plan hubs: next month on the forecast", "The January 2026 plan, scored on the forecast because that month has not happened yet."),
    ("14_plan_exact.png", "Plan hubs: exact MIP", "The same October 2025 plan solved by the traditional exact MIP: identical hubs and cost, status Optimal."),
    ("15_compare.png", "Compare methods", "Proposed method against the traditional methods: the proposed hubs and the headline comparison."),
    ("16_compare_full.png", "Compare methods (full)", "All six methods scored on the realised October 2025 demand, with operating-cost and fulfilment charts."),
    ("17_compare_scalability.png", "Scalability benchmark", "Exact MIP against the matheuristic at 90, 180 and 270 demand points."),
    ("18_compare_scalability_full.png", "Scalability benchmark (full)", "The scalability charts and the table of benchmark runs."),
    ("19_rolling.png", "Re-optimise page", "Rolling-horizon summary: adaptive re-planning gives 98.3% fulfilment against 83.7% for a static plan."),
    ("20_rolling_full.png", "Re-optimise page (full)", "Month-by-month fulfilment, forecast against realised demand, hub changes and the monthly table."),
    ("21_dashboard_dark.png", "Dashboard in dark mode", "The same dashboard in the dark theme, which follows the operating-system setting until the user chooses."),
    ("22_not_found.png", "Not-found page", "A friendly page for routes that do not exist."),
]
MAIN_SCREENS = ["03_dashboard.png", "05_forecast.png", "07_regions.png", "08_plan_parameters.png", "09_plan_kpis.png", "11_plan_map.png", "12_plan_searchlog.png",
                "13_plan_next_month.png", "14_plan_exact.png", "16_compare_full.png", "17_compare_scalability.png", "19_rolling.png", "20_rolling_full.png"]
