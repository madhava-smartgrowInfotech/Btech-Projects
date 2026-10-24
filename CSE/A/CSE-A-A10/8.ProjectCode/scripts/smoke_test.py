"""End-to-end smoke test: drives the real FlowSense API (no mocks).

Usage:  python scripts/smoke_test.py [http://localhost:8310]
Starts nothing itself - run the backend first (run.bat, or `uvicorn backend.main:app --port 8310`).
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8310").rstrip("/")
TOKEN = None
FAILS = []


def call(method, path, body=None, raw=None, headers=None, auth=True):
    h = dict(headers or {})
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if auth and TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


def multipart(field, filename, content, ctype, fields=None):
    b = "----flowsense" + str(int(time.time()))
    out = io.BytesIO()
    for k, v in (fields or {}).items():
        out.write(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    out.write(f'--{b}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n'.encode())
    out.write(content)
    out.write(f"\r\n--{b}--\r\n".encode())
    return out.getvalue(), {"Content-Type": f"multipart/form-data; boundary={b}"}


def main():
    global TOKEN
    s, h = call("GET", "/api/health", auth=False)
    check("health", s == 200 and h.get("ok"))
    for _ in range(60):  # predictor trains in the background on first start
        s, h = call("GET", "/api/health", auth=False)
        if h.get("predictor_ready"):
            break
        time.sleep(1)
    check("predictor ready", h.get("predictor_ready"), str(h))

    s, _ = call("GET", "/api/live", auth=False)
    check("protected route rejects anonymous", s == 401)
    s, d = call("POST", "/api/auth/login", {"email": "nobody@x.io", "password": "bad"}, auth=False)
    check("bad login -> 401 with message", s == 401 and d["detail"]["message"])
    s, demo = call("GET", "/api/auth/demo", auth=False)
    s, d = call("POST", "/api/auth/login", demo, auth=False)
    check("demo login", s == 200 and d.get("token"))
    TOKEN = d["token"]
    s, d = call("GET", "/api/auth/me")
    check("auth/me", s == 200 and d["email"])

    s, d = call("GET", "/api/public/pulse", auth=False)
    check("landing pulse (public, real sim)", s == 200 and d["map"]["signals"] and "kpis" in d)
    s, d = call("GET", "/api/meta")
    check("meta lists 4 controllers", s == 200 and len(d["controllers"]) == 4)

    # ---- live control center
    s, d = call("POST", "/api/live/reset")
    check("live reset -> t=0", s == 200 and d["t"] == 0)
    s, d = call("PUT", "/api/live/config", {"grid": "2x2", "controller": "advanced", "demand": 1.4, "emergencies": True, "use_ml": True})
    check("live config", s == 200 and d["config"]["demand"] == 1.4 and d["config"]["controller"] == "advanced")
    for _ in range(5):
        s, d = call("POST", "/api/live/step", {"seconds": 2})
    check("live step x5 advances 10 s", s == 200 and d["t"] == 10)
    s, d = call("POST", "/api/live/step", {"seconds": 300})
    check("skip 5 min", d["t"] == 310 and d["kpis"]["throughput"] > 0, str(d["kpis"]))
    check("map has roads/signals/vehicles/labels", len(d["map"]["roads"]) == 4 and len(d["map"]["signals"]) == 16
          and d["map"]["vehicles"] and len(d["map"]["labels"]) == 4)
    check("junction table (4 rows) + queue series", len(d["junctions"]) == 4 and len(d["queue_series"]) > 100)
    s, d = call("POST", "/api/live/ambulance")
    check("send ambulance -> active + banner", s == 200 and d["kpis"]["emg_active"] >= 1 and d["banner"], str(d.get("banner")))
    s, d = call("PUT", "/api/live/config", {"controller": "fixed"})
    check("switch to fixed -> banner says ignored", d["banner"] and d["banner"]["kind"] == "ignored", str(d.get("banner")))
    s, d = call("PUT", "/api/live/config", {"demand": 9})
    check("demand out of range -> 422 with message", s == 422 and d["detail"]["message"])
    s, d = call("PUT", "/api/live/config", {"grid": "3x3", "controller": "advanced"})
    check("grid 3x3 restarts sim", s == 200 and d["t"] == 0 and len(d["junctions"]) == 9)
    s, d = call("PUT", "/api/live/config", {"grid": "2x2"})

    # ---- violations (after enough sim time)
    call("PUT", "/api/live/config", {"demand": 1.6, "controller": "fixed"})
    call("POST", "/api/live/step", {"seconds": 900})
    s, d = call("GET", "/api/violations")
    check("violations", s == 200 and "kpis" in d and (d["empty"] or d["log"]), str(d.get("kpis")))
    if not d["empty"]:
        check("violation log rows have plate+kind", d["log"][0]["plate"] and d["log"][0]["kind"])

    # ---- prediction
    s, d = call("GET", "/api/prediction")
    check("prediction metrics (GBM beats persistence)", s == 200 and d["kpis"]["vs_persistence"] > 0 and len(d["scatter"]) > 100, str(d.get("kpis")))
    s, d = call("GET", "/api/prediction/live")
    check("prediction live forecast", s == 200 and d["available"] and d["worst"], str(d)[:200])

    # ---- benchmark
    s, d = call("POST", "/api/benchmark", {"grid": "2x2", "seconds": 900, "demand": 1.2, "seeds": 2, "start_hour": 8, "use_ml": True})
    check("benchmark 4 controllers", s == 200 and len(d["controllers"]) == 4 and len(d["table"]) == 4)
    check("benchmark: advanced beats fixed on delay", d["kpis"]["d_fixed"] > 0, str(d["kpis"]))
    s, d = call("POST", "/api/benchmark", {"grid": "2x2", "seconds": 10, "demand": 1.2, "seeds": 2, "start_hour": 8, "use_ml": True})
    check("benchmark out of range -> 422", s == 422)
    s, d = call("GET", "/api/violations")
    check("violations page sees last benchmark", len(d["last_benchmark"]) == 4)
    s, d = call("POST", "/api/benchmark/sweep", {"grid": "2x2", "use_ml": True})
    check("demand sweep", s == 200 and len(d["series"]["fixed"]) == 5)

    # ---- vision
    s, d = call("GET", "/api/vision/synthetic?vehicles=9&ambulance=true&flash=A&seed=3")
    check("vision synthetic detects ambulance via light-bar", s == 200 and d["report"]["emergency"] and d["annotated"].startswith("data:image/jpeg"))
    s, d = call("GET", "/api/vision/synthetic?vehicles=9&ambulance=false&flash=B&seed=3")
    check("vision synthetic without ambulance -> no emergency", s == 200 and not d["report"]["emergency"])
    health_ok = call("GET", "/api/health", auth=False)[1]["yolo_available"]
    if health_ok:
        s, d = call("GET", "/api/vision/sample?conf=0.3")
        check("YOLOv8 sample photo", s == 200 and len(d["detections"]) > 0, str(d)[:200])
        import cv2
        import numpy as np
        ok, buf = cv2.imencode(".png", np.full((120, 160, 3), 90, np.uint8))
        body, hh = multipart("file", "blank.png", buf.tobytes(), "image/png", {"conf": "0.3"})
        s, d = call("POST", "/api/vision/analyze", raw=body, headers=hh)
        check("YOLOv8 upload (blank image -> 0 vehicles)", s == 200 and len(d["detections"]) == 0, str(d)[:200])
    else:
        print("SKIP  YOLOv8 checks (ultralytics not installed)")
    body, hh = multipart("file", "x.png", b"not an image", "image/png", {"conf": "0.3"})
    s, d = call("POST", "/api/vision/analyze", raw=body, headers=hh)
    check("bad upload -> 4xx with message", 400 <= s < 600 and d["detail"]["message"], str(d))

    print("\n%d failed" % len(FAILS) if FAILS else "\nALL CHECKS PASSED")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
