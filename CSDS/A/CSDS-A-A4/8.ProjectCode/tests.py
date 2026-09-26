"""End-to-end smoke tests.  Run:  python tests.py   (after `python run.py forecast`)"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hublocator.data import distance_matrix, load_dataset  # noqa: E402
from hublocator.forecast import forecast_for_period, forecast_next_period, load_forecaster, train_forecaster  # noqa: E402
from hublocator.matheuristic import solve_matheuristic  # noqa: E402
from hublocator.model import HAS_PULP, Instance, evaluate_solution, solve_exact  # noqa: E402

regions, demand = load_dataset()


def test_data():
    assert len(regions) >= 30 and demand.period.nunique() >= 24
    assert set(["region_id", "period", "orders"]).issubset(demand.columns)
    d = distance_matrix(regions)
    assert d.shape == (len(regions), len(regions)) and d[0, 0] == 0 and d[0, 1] > 100
    print("data ................ ok")


def test_forecast():
    if load_forecaster() is None:
        train_forecaster(regions, demand, verbose=False)
    f = forecast_next_period(regions, demand)
    assert len(f) == len(regions) and (f.forecast > 0).all()
    b = forecast_for_period(regions, demand, "2025-10")
    real = demand[demand.period == "2025-10"].orders.sum()
    assert abs(b.forecast.sum() - real) / real < 0.3           # within 30 % on the peak month
    print("forecast ............ ok")


def test_optimisation():
    fc = forecast_next_period(regions, demand).set_index("region_id").loc[regions.region_id, "forecast"].to_numpy(float)
    inst = Instance.from_forecast(regions, fc, n_hubs=5, time_limit=15)
    mh = solve_matheuristic(inst)
    assert len(mh["hubs"]) <= 5 and mh["assign"] is not None
    assert all(mh["assign"][i] in mh["hubs"] for i in range(inst.n))
    kpi = evaluate_solution(inst, mh["hubs"], mh["assign"])
    assert 0.99 <= kpi["fulfilment_rate"] <= 1.0 and kpi["overloaded_hubs"] == 0     # capacity respected on the plan
    if HAS_PULP:
        ex = solve_exact(inst, time_limit=30)
        assert mh["objective"] <= ex["objective"] * 1.02          # matheuristic within 2 % of exact
    # hard SLA: no assignment beyond the SLA
    inst2 = Instance.from_forecast(regions, fc, n_hubs=8, sla_hours=30, sla_hard=True, time_limit=15)
    s2 = solve_matheuristic(inst2)
    assert np.all(inst2.time[np.arange(inst2.n), s2["assign"]] <= 30 + 1e-9)
    print("optimisation ........ ok")


def test_webapp():
    from hublocator.webapp import create_app
    c = create_app().test_client()
    for p in ("/", "/forecast", "/optimize", "/compare", "/rolling"):
        assert c.get(p).status_code == 200
    j = c.post("/api/optimize", json={"n_hubs": 4, "period": "2025-12"}).get_json()
    assert j["kpi"]["n_hubs"] <= 4 and j["realized"] is True
    assert c.get("/api/forecast").get_json()["total"] > 0
    print("web app + api ....... ok")


if __name__ == "__main__":
    test_data()
    test_forecast()
    test_optimisation()
    test_webapp()
    print("all tests passed")
