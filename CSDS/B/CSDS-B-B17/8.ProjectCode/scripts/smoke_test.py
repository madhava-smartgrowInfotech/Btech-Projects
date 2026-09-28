"""End-to-end smoke test against the running API (start the backend first, e.g. with run.bat).

Flow: login -> generate a sample 'refund request' call in the studio -> wait for the pipeline -> check transcript
speakers, intent, emotion timeline, summary and scorecard -> upload a real single-channel recording -> search ->
analytics -> metrics -> access control.
Usage: python scripts/smoke_test.py
"""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8217')}/api"
PW = os.getenv("DEMO_PASSWORD", "CallSense@123")
results = []


def check(name, cond, detail=""):
    results.append(bool(cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    return cond


def login(email):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": PW}, timeout=30)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}, r.json()["user"]


def wait_done(h, call_id, timeout=900):
    t0, last = time.time(), ""
    while time.time() - t0 < timeout:
        c = requests.get(f"{BASE}/calls/{call_id}", headers=h, timeout=30).json()
        if c["status"] in ("done", "failed"):
            return c
        if c["stage"] != last:
            last = c["stage"]
            print(f"       ... {c['status']}: {last}")
        time.sleep(3)
    return c


def main():
    try:
        health = requests.get(f"{BASE}/health", timeout=10).json()
    except requests.ConnectionError:
        sys.exit(f"Backend is not running on {BASE} - start it with run.bat first")
    check("health", health.get("ok") and health.get("models_ready"), str(health))

    bad = requests.post(f"{BASE}/auth/login", json={"email": "supervisor@callsense.local", "password": "wrong"}, timeout=30)
    check("wrong password rejected", bad.status_code == 401)
    sup, _ = login("supervisor@callsense.local")
    alex, alex_user = login("agent@callsense.local")
    sam, _ = login("sam@callsense.local")
    check("demo logins", True)

    scripts = requests.get(f"{BASE}/studio/scripts", headers=alex, timeout=30).json()
    check("studio scripts", any(s["id"] == "refund_request" for s in scripts), f"{len(scripts)} scripts")

    t0 = time.time()
    r = requests.post(f"{BASE}/studio/generate", headers=alex, json={"script_id": "refund_request"}, timeout=300)
    check("generate sample refund call", r.status_code == 200, r.text[:200])
    call = r.json()
    check("sample is labelled", call["is_sample"] and call["title"].startswith("[Sample]"))
    c = wait_done(alex, call["id"])
    check("pipeline finished", c["status"] == "done", c.get("error") or f"{time.time() - t0:.0f}s")
    if c["status"] == "done":
        speakers = {s["speaker"] for s in c["segments"]}
        check("transcript split by speaker", speakers == {"agent", "customer"}, f"{len(c['segments'])} turns")
        check("intent is get_refund", c["intent"] == "get_refund", f"{c['intent']} ({c['intent_confidence']})")
        emo = [s["emotion"] for s in c["segments"] if s["speaker"] == "customer"]
        neg = [i for i, e in enumerate(emo) if e in ("frustrated", "angry", "concerned")]
        rel = [i for i, e in enumerate(emo) if e == "relieved"]
        check("emotion: frustration then relief", neg and rel and min(neg) < max(rel), " -> ".join(emo))
        check("keywords extracted", len(c["keywords"]) >= 3, ", ".join(c["keywords"]))
        card = c["scorecard"]
        check("scorecard with evidence", card and len(card["items"]) == 7 and all(i["evidence"] for i in card["items"]),
              f"{card['total']}/100" if card else "")
        if c["summary"]:
            check("summary (Gemini)", c["summary"]["reason"] and c["summary"]["resolution"],
                  f"{c['summary']['status']}; {len(c['summary']['action_items'])} action item(s)")
        else:
            check("summary (Gemini)", False, c["summary_error"])
        a = requests.get(f"{BASE}/calls/{call['id']}/audio", params={"token": alex["Authorization"][7:]}, timeout=30)
        check("audio playback endpoint", a.status_code == 200 and len(a.content) > 10000)

    wav = ROOT / "data" / "call_center" / "call_recording_02.wav"
    with open(wav, "rb") as f:
        r = requests.post(f"{BASE}/calls", headers=sup, files=[("files", (wav.name, f, "audio/wav"))],
                          data={"agent_id": str(alex_user["id"])}, timeout=120)
    check("upload a real recording", r.status_code == 200, r.text[:200])
    if r.status_code == 200:
        up = wait_done(sup, r.json()["calls"][0]["id"])
        check("mono recording analysed", up["status"] == "done" and up["segments"],
              up.get("error") or f"intent {up['intent']}, score {up['score']}")

    found = requests.get(f"{BASE}/calls", headers=sup, params={"q": "headphones"}, timeout=30).json()["calls"]
    check("transcript search", any(x["id"] == call["id"] for x in found) and found[0].get("snippet"))

    hidden = requests.get(f"{BASE}/calls/{call['id']}", headers=sam, timeout=30)
    check("agents only see their own calls", hidden.status_code == 404)

    an = requests.get(f"{BASE}/analytics", headers=sup, timeout=30).json()
    check("analytics", an["totals"]["analysed"] >= 1 and an["intents"] and an["leaderboard"],
          f"{an['totals']['calls']} calls, top intent {an['intents'][0]['intent'] if an['intents'] else '-'}")
    m = requests.get(f"{BASE}/metrics", headers=sup, timeout=30).json()
    check("model metrics", m["training"] and m["training"]["intent"]["accuracy"] > 0.9)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} checks passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
