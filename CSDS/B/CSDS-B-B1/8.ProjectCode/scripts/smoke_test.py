"""End-to-end smoke test against the RUNNING API (start the backend first).

    venv\\Scripts\\python scripts\\smoke_test.py [--base http://localhost:8201] [--skip-retrain]

Drives the real flow: citizen files a Hindi complaint with a photo + location -> AI suggestions with
LIME/SHAP explanations -> Gemini extraction -> officer accepts -> officer overrides a department on a
second complaint -> one-click retrain -> status updates -> Gemini draft reply sent to the citizen ->
analytics + admin SLA edit. Exits non-zero on the first failure.
"""
import argparse
import os
import struct
import sys
import time
import zlib

import httpx

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--base", default=f"http://localhost:{os.getenv('BACKEND_PORT', '8201')}")
ap.add_argument("--skip-retrain", action="store_true")
args = ap.parse_args()
api = httpx.Client(base_url=args.base, timeout=300)
passed = 0


def check(cond, msg):
    global passed
    if not cond:
        print(f"FAIL  {msg}")
        sys.exit(1)
    passed += 1
    print(f"ok    {msg}")


def call(method, url, token=None, expect=200, **kw):
    r = api.request(method, url, headers={"Authorization": f"Bearer {token}"} if token else {}, **kw)
    if r.status_code != expect:
        print(f"FAIL  {method} {url} -> {r.status_code} {r.text[:400]}")
        sys.exit(1)
    return r.json()


def login(email, pw):
    return call("POST", "/api/auth/login", json={"email": email, "password": pw})["token"]


def png(w=48, h=32):
    """A small real PNG (road-grey gradient) so the photo upload path is exercised."""
    raw = b"".join(b"\x00" + bytes((80 + x + y) % 256 for x in range(w) for _ in range(3)) for y in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


# --- 0. backend up ---
for _ in range(90):
    try:
        health = api.get("/api/health").json()
        break
    except httpx.HTTPError:
        time.sleep(2)
else:
    check(False, f"backend reachable at {args.base}")
check(health["status"] == "ok", f"health ok, model v{health['model_version']}, gemini={health['gemini_configured']}")

citizen = login("citizen@civicpulse.local", "Citizen@123")
officer = login("officer@civicpulse.local", "Officer@123")
admin = login("admin@civicpulse.local", "Admin@123")
check(True, "demo logins (citizen, officer, admin)")
call("GET", "/api/officer/queue", citizen, expect=403)
check(True, "citizen is blocked from the officer queue")

# --- 1. citizen files a Hindi complaint with photo + location ---
hindi = ("कोरमंगला 5th ब्लॉक की मुख्य सड़क पर बहुत बड़ा गड्ढा है, पिछले दो हफ्ते से कोई मरम्मत नहीं हुई। "
         "कल रात एक बाइक सवार गिरकर घायल हो गया, स्कूल के बच्चों के लिए बहुत खतरनाक है। कृपया तुरंत ठीक करें।")
c1 = call("POST", "/api/complaints", citizen, data={"text": hindi, "lat": "12.9340", "lng": "77.6230"},
          files={"photo": ("pothole.png", png(), "image/png")})
check(c1["tracking_id"].startswith("CP-"), f"tracking ID issued: {c1['tracking_id']}")
check(c1["language"] == "Hindi" and c1["ward"] == "Koramangala", f"language {c1['language']}, ward {c1['ward']}")
check(api.get(c1["photo_url"]).status_code == 200, "photo stored and served")
t = call("GET", f"/api/complaints/track/{c1['tracking_id']}", citizen)
check(t["status"] == "Submitted" and t["timeline"], "citizen status page shows Submitted + timeline")

# --- 2. officer queue shows AI suggestions with explanations ---
q = call("GET", "/api/officer/queue", officer, params={"status": "Submitted"})
item = next((i for i in q["items"] if i["id"] == c1["id"]), None)
check(item is not None, "complaint appears in the officer triage queue")
ai = item["ai"]
print(f"      AI: {ai['category']} / {ai['department']} / {ai['priority']} / ~{ai['expected_days']} days, "
      f"words {item['top_words']}")
check(ai["department"] == "Roads" and ai["priority"] in ("High", "Critical"), "Roads + High/Critical priority predicted")
d = call("GET", f"/api/complaints/{c1['id']}", officer)
ex = d["ai"]["explanations"]
check(len(ex["category_words"]) >= 3, f"LIME words: {[w['word'] for w in ex['category_words'][:5]]}")
check(ex["priority_factors"]["factors"], f"SHAP priority factors: {[f['factor'] for f in ex['priority_factors']['factors'][:3]]}")
check(ex["time_factors"]["factors"], f"SHAP time factors, baseline {ex['time_factors']['baseline_days']} days")

# --- 3. Gemini structured extraction (runs in the background after intake) ---
for _ in range(40):
    d = call("GET", f"/api/complaints/{c1['id']}", officer)
    if d["extraction_status"] != "pending":
        break
    time.sleep(1.5)
if d["extraction_status"] != "done":
    print(f"      background extraction: {d['extraction_status']} - retrying on demand")
    for attempt in range(3):
        r = api.post(f"/api/complaints/{c1['id']}/extract", headers={"Authorization": f"Bearer {officer}"})
        if r.status_code == 200:
            d["extraction"] = r.json()["extraction"]
            break
        time.sleep(10)
    else:
        check(False, f"Gemini extraction ({r.text[:200]})")
check(d["extraction"].get("issue"), f"Gemini extraction: place={d['extraction'].get('place')!r}, "
                                    f"issue={d['extraction'].get('issue')!r}")

# --- 4. officer accepts all suggestions ---
d = call("POST", f"/api/complaints/{c1['id']}/decision", officer,
         json={"category": ai["category"], "department": ai["department"], "priority": ai["priority"]})
check(d["status"] == "Assigned" and all(f["action"] == "accept" for f in d["feedback"]), "officer accepted -> Assigned")

# --- 5. second complaint: officer overrides the department with a reason ---
c2 = call("POST", "/api/complaints", citizen, data={
    "text": "Street light pole near Indiranagar 100 feet road bus stop is leaning badly after the storm and the "
            "wires are hanging low. Please send the team, people walk under it every evening.",
    "lat": "12.9790", "lng": "77.6400"})
d2 = call("GET", f"/api/complaints/{c2['id']}", officer)
ai2 = d2["ai"]
new_dept = "Public Safety" if ai2["department"] != "Public Safety" else "Roads"
call("POST", f"/api/complaints/{c2['id']}/decision", officer, expect=400,
     json={"category": ai2["category"], "department": new_dept, "priority": ai2["priority"]})
check(True, "override without a reason is rejected")
d2 = call("POST", f"/api/complaints/{c2['id']}/decision", officer, json={
    "category": ai2["category"], "department": new_dept, "priority": ai2["priority"],
    "reasons": {"department": "Leaning pole over a footpath is an immediate public safety hazard"}})
check(any(f["action"] == "override" and f["field"] == "department" for f in d2["feedback"]),
      f"department override stored as a label ({ai2['department']} -> {new_dept})")

# --- 6. one-click retrain ---
if not args.skip_retrain:
    t0 = time.time()
    r = call("POST", "/api/model/retrain", officer)
    after = r["after"]
    check(after["feedback"]["labels_used"] >= 2 and after["version"] > r["before"]["version"],
          f"retrained v{r['before']['version']} -> v{after['version']} in {time.time() - t0:.0f}s, "
          f"dept acc {after['department']['test']['accuracy']}, agreement {after['feedback']['officer_agreement_after']}")
    m = call("GET", "/api/model/metrics", officer)
    check(m["runs"] and m["runs"][0]["version"] == after["version"], "new metrics listed in model history")

# --- 7. status updates + Gemini draft reply in the citizen's language ---
call("POST", f"/api/complaints/{c1['id']}/status", officer, json={"status": "In Progress"})
draft = None
for attempt in range(3):
    r = api.post(f"/api/complaints/{c1['id']}/draft-reply", json={"note": "Repair crew scheduled"},
                 headers={"Authorization": f"Bearer {officer}"})
    if r.status_code == 200:
        draft = r.json()["draft"]
        break
    time.sleep(10)
check(draft and any("ऀ" <= ch <= "ॿ" for ch in draft), f"Gemini drafted a Hindi reply: {draft[:80] if draft else r.text[:200]}...")
call("POST", f"/api/complaints/{c1['id']}/reply", officer, json={"message": draft})
call("POST", f"/api/complaints/{c1['id']}/status", officer, json={"status": "Resolved", "note": "Pothole filled"})
t = call("GET", f"/api/complaints/track/{c1['tracking_id']}", citizen)
check(t["status"] == "Resolved" and any(e["kind"] == "reply" for e in t["timeline"]),
      "citizen sees the reply and Resolved status")

# --- 8. analytics ---
s = call("GET", "/api/analytics/summary", officer)
check(s["total"] > 2 and s["sla_compliance"] is not None, f"summary: {s['total']} complaints, SLA compliance {s['sla_compliance']}")
h = call("GET", "/api/analytics/hotspots", officer, params={"days": 30})
check(any(w["ward"] == "Koramangala" for w in h["wards"]) and h["points"], f"hotspots: {len(h['wards'])} wards, "
                                                                           f"{len(h['recurring'])} recurring issues")
check(call("GET", "/api/analytics/sla", officer), "SLA table by department")
tr = call("GET", "/api/analytics/trends", officer)
check(tr["series"], f"category trends over {len(tr['weeks'])} weeks")

# --- 9. admin edits an SLA ---
depts = call("GET", "/api/meta")["departments"]
roads = next(x for x in depts if x["name"] == "Roads")
call("PUT", f"/api/departments/{roads['id']}", officer, expect=403, json={"sla_days": 5})
call("PUT", f"/api/departments/{roads['id']}", admin, json={"sla_days": roads["sla_days"] + 1})
call("PUT", f"/api/departments/{roads['id']}", admin, json={"sla_days": roads["sla_days"]})
check(True, "admin can edit SLAs, officers cannot")

print(f"\nALL {passed} CHECKS PASSED")
