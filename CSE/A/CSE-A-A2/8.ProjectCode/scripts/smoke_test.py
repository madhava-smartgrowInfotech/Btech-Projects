"""ResQAI smoke test: exercises the main flow through the same /api URLs the React app uses.

Usage:  python scripts/smoke_test.py [base_url]
The base URL defaults to the Vite dev server (http://localhost:5302), which proxies /api to the
Flask backend, so a pass proves the frontend wiring as well as the API. Pass http://localhost:8302 to
test the backend directly. Exit code 0 = all checks passed.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5302").rstrip("/")
failures = []


def call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, json.loads(r.read().decode())


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


def main():
    try:
        _, health = call("GET", "/api/health")
    except (urllib.error.URLError, OSError) as e:
        print(f"[FAIL] cannot reach {BASE}: {e}\nStart the app with run.bat first.")
        return 1
    check("health ok", health.get("status") == "ok", f"models_loaded={health.get('models_loaded')}")

    expected = {"normal": 0, "brake": 0, "minor": 1, "moderate": 2, "severe": 3}
    severe_result = None
    for scenario in expected:
        _, reading = call("GET", f"/api/simulate?scenario={scenario}")
        has_keys = all(k in reading for k in ("acc_magnitude", "gyro_magnitude", "speed_change", "jerk"))
        check(f"simulate {scenario} returns a reading", has_keys and reading.get("scenario") == scenario)
        _, res = call("POST", "/api/predict", reading)
        ok_shape = {"accident_detected", "severity_label", "confidence", "features_used", "model_source"} <= set(res)
        check(f"predict {scenario} has response shape", ok_shape, f"{res.get('severity_label')} @ {res.get('confidence')}")
        if scenario == "normal":
            check("normal driving is not an accident", res["accident_detected"] is False)
        if scenario == "severe":
            severe_result = res
            check("severe crash is detected", res["accident_detected"] is True and res["severity_label"] in ("Moderate", "Severe"))

    # Each simulated scenario must be rated as its own severity (the simulator mirrors the training data).
    labels = {"minor": "Minor", "moderate": "Moderate", "severe": "Severe"}
    for scenario, label in labels.items():
        hits = 0
        for _ in range(40):
            _, reading = call("GET", f"/api/simulate?scenario={scenario}")
            _, res = call("POST", "/api/predict", reading)
            hits += res["severity_label"] == label
        check(f"{scenario} scenario is rated {label} (>=90% of 40)", hits >= 36, f"{hits}/40")

    # Manual-override payload exactly as the Manual screen builds it.
    manual = {"acc_x": 0, "acc_y": 0, "acc_z": 9.81, "gyro_x": 0, "gyro_y": 0, "gyro_z": 0.1,
              "gyro_magnitude": 0.1, "speed_before": 40, "speed_change": 0, "jerk": 0, "acc_magnitude": 9.81}
    _, res = call("POST", "/api/predict", manual)
    check("manual calm reading predicts no accident", res["accident_detected"] is False)

    _, hosp = call("GET", "/api/hospitals?k=5")
    hs = hosp["hospitals"]
    check("hospitals returns 5 sorted by distance", len(hs) == 5 and hs == sorted(hs, key=lambda h: h["distance_km"]))

    sev = severe_result or {"severity_label": "Severe", "confidence": 0.95}
    _, em = call("POST", "/api/emergency", {"severity_label": sev["severity_label"], "confidence": sev["confidence"], "lat": 17.4, "lon": 78.45})
    check("emergency dispatches", em.get("status") == "dispatched" and em["alert_id"].startswith("RQ-"), em.get("alert_id", ""))
    check("emergency lists 3 nearest hospitals", len(em["nearest_hospitals"]) == 3)
    check("emergency message names the severity", sev["severity_label"] in em["message"])
    check("emergency numbers present", em["ambulance_number"] == "108" and em["national_emergency_number"] == "112")

    _, em2 = call("POST", "/api/emergency", {"severity_label": "Severe", "confidence": 0.9})
    check("emergency without GPS falls back to a server location", "lat" in em2["location"] and "lon" in em2["location"])

    if BASE.endswith(":5302"):
        with urllib.request.urlopen(BASE + "/", timeout=15) as r:
            check("frontend serves the app shell", r.status == 200 and b'id="root"' in r.read())

    print(f"\n{'ALL CHECKS PASSED' if not failures else str(len(failures)) + ' CHECK(S) FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
