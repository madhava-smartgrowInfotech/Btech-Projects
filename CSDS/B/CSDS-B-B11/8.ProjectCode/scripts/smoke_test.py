"""End-to-end smoke test against the running NutriSense API.

Usage:  venv\\Scripts\\python scripts\\smoke_test.py   (backend must be running on BACKEND_PORT, default 8211)

Walks the main flow: register -> profile -> targets -> 7-day plan -> swap -> recipe -> food search/log ->
photo log -> USDA log -> weights for a week -> automatic recalculation -> progress.
Gemini-dependent steps are reported as SKIP (not failure) when GEMINI_API_KEY is not configured.
"""
import os
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8211')}/api"
PHOTO = ROOT / "data" / "sample" / "photos" / "masala_dosa.jpg"

results = []


def check(name, ok, detail=""):
    results.append((name, "PASS" if ok else "FAIL", detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return ok


def skip(name, detail):
    results.append((name, "SKIP", detail))
    print(f"[SKIP] {name} {detail}")


def main():
    c = httpx.Client(base_url=BASE, timeout=120)
    h = c.get("/health").json()
    check("health", h["status"] == "ok" and h["foods"] > 500 and h["swap_model"], f"foods={h['foods']} gemini={h['gemini_configured']}")

    email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
    r = c.post("/auth/register", json={"name": "Smoke Test", "email": email, "password": "secret123"})
    check("register", r.status_code == 200, email)
    c.headers["Authorization"] = f"Bearer {r.json()['token']}"
    check("login", c.post("/auth/login", json={"email": email, "password": "secret123"}).status_code == 200)

    profile = dict(age=28, gender="female", height_cm=164, weight_kg=66, activity="moderate", diet_type="vegetarian",
                   cuisine="both", allergies=["peanut"], conditions=[], goal="lose")
    r = c.put("/profile", json=profile)
    t = r.json()["targets"]
    check("profile + targets", r.status_code == 200 and t["kcal"] == 1650,
          f"BMI={t['bmi']} BMR={t['bmr']} TDEE={t['tdee']} target={t['kcal']} P/C/F={t['protein_g']}/{t['carbs_g']}/{t['fat_g']} g")

    r = c.post("/plans", json={"seed": 7})
    plan = r.json()
    ok = r.status_code == 200 and len(plan.get("days", [])) == 7
    check("generate 7-day plan", ok, f"{plan.get('solve_seconds')} s, {plan.get('unique_dishes')} unique dishes")
    if not ok:
        print(plan)
        return finish()
    worst = max(abs(d["totals"]["kcal"] - t["kcal"]) / t["kcal"] for d in plan["days"])
    check("every day within 5% of target", worst <= 0.05, f"worst deviation {worst * 100:.1f}%")
    ids = [it["food_id"] for d in plan["days"] for items in d["meals"].values() for it in items]
    bad = [c.get(f"/foods/{i}").json() for i in set(ids)]
    bad = [f["name"] for f in bad if "peanut" in f["allergens"] or f["diet"] != "vegetarian"]
    check("no peanut or non-vegetarian dishes", not bad, ", ".join(bad))

    opts = c.get(f"/plans/{plan['id']}/swap-options", params={"day": 1, "meal": "lunch", "index": 0}).json()
    ok = len(opts["options"]) > 0
    check("swap options", ok, f"{opts['original']['name']} -> {[o['name'] for o in opts['options'][:3]]}")
    if ok:
        o = opts["options"][0]
        r = c.post(f"/plans/{plan['id']}/swap", json={"day": 1, "meal": "lunch", "index": 0, "food_id": o["food_id"], "grams": o["grams"]})
        check("apply swap", r.status_code == 200 and r.json()["days"][0]["meals"]["lunch"][0]["food_id"] == o["food_id"],
              f"new day total {r.json()['days'][0]['totals']['kcal']} kcal")

    item = plan["days"][1]["meals"]["dinner"][0]
    r = c.get(f"/recipes/{item['food_id']}", params={"grams": item["grams"]})
    if r.status_code == 503 and not h["gemini_configured"]:
        skip("recipe (Gemini)", "GEMINI_API_KEY not set")
    else:
        rec = r.json()
        check("recipe (Gemini)", r.status_code == 200 and len(rec.get("steps", [])) >= 2,
              f"{item['name']}: {len(rec.get('steps', []))} steps, {len(rec.get('ingredients', []))} ingredients, warnings={rec.get('warnings')}")

    res = c.get("/foods/search", params={"q": "dal"}).json()["results"]
    check("food search", len(res) > 0, f"'dal' -> {[x['name'] for x in res[:3]]}")
    r = c.post("/logs", json={"meal": "breakfast", "food_id": res[0]["food_id"], "grams": 150})
    check("log dish", r.status_code == 200, f"{r.json().get('name')} {r.json().get('kcal')} kcal")

    with open(PHOTO, "rb") as fh:
        r = c.post("/logs/photo", files={"file": ("masala_dosa.jpg", fh, "image/jpeg")})
    if r.status_code == 503 and not h["gemini_configured"]:
        skip("photo recognition (Gemini)", "GEMINI_API_KEY not set")
    else:
        items = r.json().get("items", [])
        ok = r.status_code == 200 and items and items[0]["matches"]
        check("photo recognition (Gemini)", bool(ok), f"detected {[i['detected'] for i in items]}")
        if ok:
            m = items[0]["matches"][0]
            r = c.post("/logs", json={"meal": "lunch", "food_id": m["food_id"], "grams": m["grams"], "source": "photo"})
            check("confirm photo log", r.status_code == 200 and r.json()["source"] == "photo", f"{m['name']} {m['grams']} g")

    r = c.get("/foods/usda", params={"q": "banana raw"})
    if r.status_code == 503:
        skip("USDA lookup", r.json().get("detail", ""))
    else:
        u = r.json()["results"]
        check("USDA lookup", r.status_code == 200 and len(u) > 0, f"{u[0]['name']} {u[0]['per_100g']['kcal']} kcal/100 g" if u else "")
        if u:
            r = c.post("/logs", json={"meal": "snack", "fdc_id": u[0]["fdc_id"], "grams": 120})
            check("log USDA ingredient", r.status_code == 200 and r.json()["source"] == "usda", f"{r.json().get('kcal')} kcal")

    day = c.get("/logs").json()
    check("intake totals", day["totals"]["kcal"] > 0, f"today {day['totals']['kcal']} / {day['targets']['kcal']} kcal")

    start = date.today() - timedelta(days=6)
    weights = [66.0, 65.9, 65.9, 65.8, 65.8, 65.7, 65.7]
    rc, fired_at = None, None
    for i, w in enumerate(weights):
        last = c.post("/weights", json={"date": (start + timedelta(days=i)).isoformat(), "weight_kg": w}).json()
        if last.get("recalculated") and rc is None:
            rc, fired_at = last["recalculated"], i + 1
    check("recalculation waits for a full week", fired_at == 7, f"fired after entry {fired_at}")
    check("weekly recalculation", rc is not None and rc["new_target_kcal"] != t["kcal"],
          f"trend {rc['observed_kg_week']} kg/wk -> target {rc['old_target_kcal']} -> {rc['new_target_kcal']} kcal" if rc else str(last))

    pr = c.get("/progress").json()
    check("progress", len(pr["weights"]) >= 7 and pr["intake"][-1]["kcal"] > 0 and len(pr["target_history"]) >= 2,
          f"adherence {pr['adherence']['score']} ({pr['adherence']['days_logged']} day logged), trend {pr['trend_kg_week']} kg/wk")

    r = c.put("/profile", json={**profile, "conditions": ["diabetes", "hypertension"]})
    t2 = r.json()["targets"]
    r = c.post("/plans", json={"seed": 3})
    p2 = r.json()
    if not check("plan with diabetes + hypertension", r.status_code == 200, str(p2.get("detail", ""))):
        return finish()
    ok = all(d["totals"]["sodium"] <= 1500 and d["totals"]["gl"] <= t2["gl_max"] for d in p2["days"])
    check("condition limits (diabetes + hypertension)", ok, f"max sodium {max(d['totals']['sodium'] for d in p2['days'])} mg, "
          f"max GL {max(d['totals']['gl'] for d in p2['days'])} / {t2['gl_max']}")
    return finish()


def finish():
    fails = [r for r in results if r[1] == "FAIL"]
    skips = [r for r in results if r[1] == "SKIP"]
    print(f"\n{len(results) - len(fails) - len(skips)} passed, {len(fails)} failed, {len(skips)} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
