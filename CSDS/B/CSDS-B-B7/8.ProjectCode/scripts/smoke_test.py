"""End-to-end smoke test against the running API (default http://127.0.0.1:8207).

Flow: login (admin + doctor) -> dashboard -> sample patient -> predict with SHAP -> admit ->
occupancy / ICU / resource forecasts -> run optimiser -> accept a modified plan -> state updated -> metrics.
"""
import os
import sys

import requests

BASE = os.getenv("HOSPISENSE_API", f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8207')}")
ok = True


def check(name, cond, detail=""):
    global ok
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
    ok &= bool(cond)


def main():
    s = requests.Session()
    r = s.get(f"{BASE}/api/health", timeout=10)
    check("health", r.ok)

    r = s.post(f"{BASE}/api/auth/login", json={"email": "doctor@hospisense.app", "password": "wrong"})
    check("bad password rejected", r.status_code == 401)
    doc = s.post(f"{BASE}/api/auth/login", json={"email": "doctor@hospisense.app", "password": "Doctor@123"}).json()
    adm = s.post(f"{BASE}/api/auth/login", json={"email": "admin@hospisense.app", "password": "Admin@123"}).json()
    D = {"Authorization": f"Bearer {doc['token']}"}
    A = {"Authorization": f"Bearer {adm['token']}"}
    check("login doctor/admin", doc["user"]["role"] == "doctor" and adm["user"]["role"] == "admin")
    check("auth required", s.get(f"{BASE}/api/dashboard").status_code == 401)

    dash = s.get(f"{BASE}/api/dashboard", headers=D, timeout=60).json()
    k = dash["kpis"]
    check("dashboard KPIs", k["beds"] > 0 and 0 < k["occupancy"] < 2, f"occupancy={k['occupancy']:.1%} alerts={len(dash['alerts'])}")

    sample = s.get(f"{BASE}/api/admissions/sample", params={"profile": "long"}, headers=D).json()["sample"]
    pred = s.post(f"{BASE}/api/admissions/predict", json=sample, headers=D).json()
    check("LOS prediction with SHAP", pred["predicted_days"] >= 1 and len(pred["reasons"]) >= 3,
          f"{pred['predicted_days']} days, long={pred['long_stay']} ({pred['long_stay_probability']:.0%}), "
          f"top reason: {pred['reasons'][0]['label']} {pred['reasons'][0]['impact_days']:+}")
    bad = dict(sample, sodium=999)
    check("input validation", s.post(f"{BASE}/api/admissions/predict", json=bad, headers=D).status_code == 422)

    before = s.get(f"{BASE}/api/forecast/icu", headers=D).json()
    sample_icu = s.get(f"{BASE}/api/admissions/sample", params={"profile": "long", "ward": "ICU"}, headers=D).json()["sample"]
    a = s.post(f"{BASE}/api/admissions", json=sample_icu, headers=D).json()
    check("admit patient", a["id"] > 0 and a["ward"] == "ICU", f"{a['patient_ref']} -> Facility {a['facility']} ICU")
    lst = s.get(f"{BASE}/api/admissions", headers=D).json()
    check("admissions list", any(x["id"] == a["id"] for x in lst))

    icu = s.get(f"{BASE}/api/forecast/icu", headers=D).json()
    f_before = next(x for x in before["facilities"] if x["facility"] == a["facility"])
    f_after = next(x for x in icu["facilities"] if x["facility"] == a["facility"])
    check("admission feeds ICU forecast", f_after["current"] == f_before["current"] + 1,
          f"{f_before['current']} -> {f_after['current']}")
    check("ICU early warnings", isinstance(icu["alerts"], list), f"{len(icu['alerts'])} warnings; first: "
          f"{icu['alerts'][0]['message'] if icu['alerts'] else '-'}")

    occ = s.get(f"{BASE}/api/forecast", params={"facility": "A", "days": 14}, headers=D).json()
    w = occ["wards"][0]
    check("occupancy forecast 14 days", len(w["series"]) == 14 and w["series"][0]["lower"] <= w["series"][0]["mean"] <= w["series"][0]["upper"])
    res = s.get(f"{BASE}/api/forecast/resources", params={"facility": "B", "days": 7}, headers=D).json()
    check("staff & equipment demand", len(res["days"]) == 7 and len(res["days"][0]["equipment"]) == 4,
          f"day 1 nurse gap={res['days'][0]['nurse_gap']} equipment gap={res['days'][0]['equipment_gap']}")

    check("doctor cannot run optimiser", s.post(f"{BASE}/api/allocation/run", json={}, headers=D).status_code == 403)
    plan = s.post(f"{BASE}/api/allocation/run", json={"horizon_days": 7, "planning_level": "expected"}, headers=A, timeout=120).json()
    types = {x["type"] for x in plan["actions"]}
    check("optimiser plan", plan["status"] == "proposed" and len(plan["actions"]) > 0,
          f"{len(plan['actions'])} actions {sorted(types)}; before={plan['summary']['before']} after={plan['summary']['after']}")
    check("every action explained", all(x.get("reason") for x in plan["actions"]))

    first = plan["actions"][0]
    edits = [{"id": first["id"], "quantity": max(0, first["quantity"] - 1)}]
    cap0 = s.get(f"{BASE}/api/forecast", params={"facility": first["facility"]}, headers=D).json()
    acc = s.post(f"{BASE}/api/allocation/plans/{plan['id']}/accept", json={"actions": edits}, headers=A).json()
    check("accept modified plan", acc["status"] == "accepted" and acc["modified"] is True)
    check("plan cannot be accepted twice",
          s.post(f"{BASE}/api/allocation/plans/{plan['id']}/accept", json={}, headers=A).status_code == 409)
    if first["type"] == "bed_conversion" and edits[0]["quantity"] > 0:
        cap1 = s.get(f"{BASE}/api/forecast", params={"facility": first["facility"]}, headers=D).json()
        c0 = {x["ward"]: x["capacity"] for x in cap0["wards"]}
        c1 = {x["ward"]: x["capacity"] for x in cap1["wards"]}
        check("accepted plan updates capacity", c1[first["to_ward"]] == c0[first["to_ward"]] + edits[0]["quantity"],
              f"{first['to_ward']}: {c0[first['to_ward']]} -> {c1[first['to_ward']]}")

    m = s.get(f"{BASE}/api/metrics", headers=D).json()
    reg = m["training"]["length_of_stay"]["regression"]
    check("model metrics", reg["mae_days"] < reg["baseline_mean_mae_days"], f"MAE={reg['mae_days']:.2f} R2={reg['r2']:.3f}")
    print("\nSMOKE TEST", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
