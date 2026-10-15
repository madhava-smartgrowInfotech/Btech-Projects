"""Record real API request/response samples (in-process FastAPI TestClient) into docs/samples/ for the documents."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

OUT = ROOT / "docs" / "samples"
OUT.mkdir(parents=True, exist_ok=True)
c = TestClient(app)
(OUT / "health.json").write_text(json.dumps(c.get("/api/health").json(), indent=2))
req = {"period": "2025-12", "n_hubs": 4, "method": "matheuristic"}
(OUT / "optimize_request.json").write_text(json.dumps(req, indent=2))
r = c.post("/api/optimize", json=req).json()
kpi = r["kpi"]
trim = {"period": r["period"], "realized": r["realized"],
        "sol": {k: r["sol"][k] for k in ("status", "hubs", "objective", "seconds", "iterations", "subproblems_solved", "kernel_status")},
        "kpi": {k: kpi[k] for k in ("n_hubs", "hub_cities", "total_cost", "fixed_cost", "transport_cost", "time_cost", "cost_per_order", "avg_delivery_hours",
                                    "max_delivery_hours", "avg_distance_km", "fulfilment_rate", "reliability_sla", "overloaded_hubs", "utilisation")},
        "kpi.assignment[0]": kpi["assignment"][0], "demand_used": f"[{len(r['demand_used'])} values]"}
(OUT / "optimize_response_trimmed.json").write_text(json.dumps(trim, indent=2))
bad = c.post("/api/optimize", json={"n_hubs": 0})
(OUT / "optimize_422.json").write_text(json.dumps({"status": bad.status_code, "body": bad.json()}, indent=2))
bad2 = c.post("/api/optimize", json={"period": "1999-01"})
(OUT / "optimize_400.json").write_text(json.dumps({"status": bad2.status_code, "body": bad2.json()}, indent=2))
f = c.get("/api/forecast").json()
(OUT / "forecast_head.json").write_text(json.dumps({"period": f["period"], "total": f["total"], "regions[0:2]": f["regions"][:2], "metrics": f["metrics"]}, indent=2))
print("samples written")
