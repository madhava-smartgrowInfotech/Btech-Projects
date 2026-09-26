"""Central configuration for HubLocator."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"
RESULTS_DIR = ROOT_DIR / "results"

REGIONS_CSV = DATA_DIR / "regions.csv"          # region_id, city, state, lat, lon, population, tier
DEMAND_CSV = DATA_DIR / "demand_history.csv"    # region_id, period (YYYY-MM), orders, promo, ...
FORECAST_MODEL = MODEL_DIR / "rf_demand.joblib"
FORECAST_METRICS = MODEL_DIR / "forecast_metrics.json"
COMPARISON_JSON = RESULTS_DIR / "comparison.json"
ROLLING_JSON = RESULTS_DIR / "rolling.json"

RANDOM_STATE = 42
N_HISTORY_MONTHS = 36

# ---- hub location model defaults --------------------------------------------
DEFAULTS = dict(
    n_hubs=6,                 # maximum number of hubs to open (p)
    capacity_factor=1.25,     # hub capacity = factor * (total demand / n_hubs)
    transport_rate=0.04,     # INR per order per km
    fixed_cost_per_hub=2_500_000.0,  # INR per month, scaled by city tier
    time_penalty=1.5,         # INR per order per hour of delivery time
    truck_speed_kmph=45.0,    # average line-haul speed
    hub_handling_hours=6.0,   # sorting/processing time at hub
    sla_hours=48.0,           # target delivery time for "reliable" delivery
    sla_hard=False,           # if True, assignments beyond SLA are forbidden
    time_limit=20,            # seconds for each MIP call
)
