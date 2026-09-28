"""Evaluate NutriSense against its objectives. Writes experiments/eval/metrics.json.

1. Requirements   - BMR/target maths vs an independent Mifflin-St Jeor implementation; calorie floor never breached
2. Meal plans     - 30 seeded random profiles x 7 days: calorie/macro accuracy, fibre, variety, solve time
3. Safety         - allergen, diet-type, sodium-cap and glycaemic-load-cap violations on every generated day
4. Swaps          - calorie match after portioning, same-cluster rate, safety of every suggestion
5. Dish matching  - fuzzy matcher used after photo recognition, on perturbed dish names (typos, dropped words)
6. Adaptation     - simulated users whose true energy needs differ from the estimate: weekly recalculation vs none

Everything is seeded, so repeated runs give the same numbers.
"""
import json
import os
import random
import statistics as st
import sys
import time
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.foods import ALLERGENS, food_db  # noqa: E402
from app.services.planner import PlanError, generate_week, swap_options  # noqa: E402
from app.services.progress import recalculation  # noqa: E402
from app.services.targets import ACTIVITY_FACTORS, compute_targets  # noqa: E402

SEED = 2024
N_PROFILES = 30


def random_profile(rng):
    gender = rng.choice(["female", "male"])
    h = rng.uniform(150, 175) if gender == "female" else rng.uniform(160, 188)
    bmi = rng.uniform(19, 32)
    return {
        "age": rng.randint(20, 65), "gender": gender, "height_cm": round(h, 1), "weight_kg": round(bmi * (h / 100) ** 2, 1),
        "activity": rng.choice(list(ACTIVITY_FACTORS)), "goal": rng.choice(["lose", "maintain", "gain"]),
        "diet_type": rng.choice(["vegetarian", "vegetarian", "eggetarian", "non_vegetarian", "vegan"]),
        "cuisine": rng.choice(["north", "south", "both"]),
        "allergies": rng.sample(["peanut", "tree_nut", "dairy", "gluten", "soy", "sesame"], rng.choice([0, 1, 1, 2])),
        "conditions": rng.sample(["diabetes", "hypertension", "high_cholesterol"], rng.choice([0, 0, 1, 2])),
        "adaptive_adjust": 0,
    }


def eval_targets(rng):
    errs, floor_ok = [], 0
    n = 500
    for _ in range(n):
        p = random_profile(rng)
        t = compute_targets(p)
        s = 5 if p["gender"] == "male" else -161
        ref = 10 * p["weight_kg"] + 6.25 * p["height_cm"] - 5 * p["age"] + s
        errs.append(abs(t["bmr"] - ref))
        floor_ok += t["kcal"] >= t["calorie_floor"]
    demo = compute_targets(dict(age=28, gender="female", height_cm=164, weight_kg=66, activity="moderate", goal="lose", conditions=[]))
    return {"profiles": n, "bmr_max_abs_error_kcal": round(max(errs), 2), "calorie_floor_respected_pct": round(100 * floor_ok / n, 1),
            "demo_profile_target_kcal": demo["kcal"]}


def eval_plans(rng):
    db = food_db()
    days_total = within5 = fibre_ok = 0
    kcal_err, p_err, c_err, f_err = [], [], [], []
    allergen_v = diet_v = sodium_v = gl_v = 0
    diabetic_days = 0
    uniques, secs, failures, profiles_out = [], [], 0, []
    plans = []
    for i in range(N_PROFILES):
        p = random_profile(rng)
        t = compute_targets(p)
        t0 = time.time()
        try:
            week = generate_week(p, t, seed=SEED + i)
        except PlanError as e:
            failures += 1
            profiles_out.append({"profile": p, "error": str(e)})
            continue
        secs.append(time.time() - t0)
        uniques.append(week["unique_dishes"])
        plans.append((p, t, week))
        for d in week["days"]:
            tt = d["totals"]
            days_total += 1
            err = abs(tt["kcal"] - t["kcal"]) / t["kcal"]
            kcal_err.append(err)
            within5 += err <= 0.05
            p_err.append(abs(tt["protein"] - t["protein_g"]) / t["protein_g"])
            c_err.append(abs(tt["carbs"] - t["carbs_g"]) / t["carbs_g"])
            f_err.append(abs(tt["fat"] - t["fat_g"]) / t["fat_g"])
            fibre_ok += tt["fibre"] >= 0.9 * t["fibre_g"]
            sodium_v += tt["sodium"] > t["sodium_max_mg"]
            if t["gl_max"]:
                diabetic_days += 1
                gl_v += tt["gl"] > t["gl_max"]
            for items in d["meals"].values():
                for it in items:
                    f = db.get(it["food_id"])
                    allergen_v += bool(f["allergen_set"] & set(p["allergies"]))
                    diet_v += not db.allowed(f, {**p, "allergies": []})
    pct = lambda x: round(100 * x, 2)
    return plans, {
        "profiles": N_PROFILES, "plans_built": N_PROFILES - failures, "failures": failures, "days": days_total,
        "days_within_5pct_kcal_pct": pct(within5 / days_total),
        "mean_abs_kcal_error_pct": pct(st.mean(kcal_err)),
        "max_abs_kcal_error_pct": pct(max(kcal_err)),
        "mean_abs_protein_error_pct": pct(st.mean(p_err)),
        "mean_abs_carbs_error_pct": pct(st.mean(c_err)),
        "mean_abs_fat_error_pct": pct(st.mean(f_err)),
        "days_meeting_90pct_fibre_target_pct": pct(fibre_ok / days_total),
        "mean_unique_dishes_per_week": round(st.mean(uniques), 1),
        "mean_solve_seconds_per_week": round(st.mean(secs), 2),
        "safety": {"allergen_violations": allergen_v, "diet_or_condition_exclusion_violations": diet_v,
                   "sodium_cap_violations": sodium_v, "glycaemic_load_cap_violations": gl_v, "diabetic_days_checked": diabetic_days},
        "failed_profiles": profiles_out,
    }


def eval_swaps(plans, rng):
    db = food_db()
    kcal_diff, same, n_items, n_opts, unsafe = [], 0, 0, 0, 0
    for p, t, week in plans:
        for _ in range(4):
            d = rng.randrange(7)
            slot = rng.choice(["breakfast", "lunch", "snack", "dinner"])
            idx = rng.randrange(len(week["days"][d]["meals"][slot]))
            res = swap_options(week, d, slot, idx, p, t, limit=5)
            n_items += 1
            for o in res["options"]:
                n_opts += 1
                kcal_diff.append(abs(o["kcal_diff"]) / max(res["original"]["kcal"], 1))
                same += o["same_cluster"]
                unsafe += not db.allowed(db.get(o["food_id"]), p)
    return {"items_tested": n_items, "options_returned": n_opts, "mean_options_per_item": round(n_opts / n_items, 2),
            "mean_abs_kcal_difference_pct": round(100 * st.mean(kcal_diff), 2),
            "median_abs_kcal_difference_pct": round(100 * st.median(kcal_diff), 2),
            "same_cluster_pct": round(100 * same / n_opts, 1), "unsafe_suggestions": unsafe}


def perturb(name, rng):
    words = name.lower().split()
    kind = rng.choice(["typo", "drop", "swap_case", "typo"])
    if kind == "drop" and len(words) > 2:
        words.pop(rng.randrange(len(words)))
        return " ".join(words)
    if kind == "typo":
        w = list(" ".join(words))
        for _ in range(rng.choice([1, 2])):
            i = rng.randrange(len(w))
            op = rng.choice(["del", "sub", "dup"])
            if op == "del" and len(w) > 4:
                w.pop(i)
            elif op == "sub":
                w[i] = rng.choice("aeiourstn")
            else:
                w.insert(i, w[i])
        return "".join(w)
    return name.upper()


def eval_matching(rng):
    db = food_db()
    foods = [f for f in db.foods.values() if f["role"] != "other"]
    sample = rng.sample(foods, 300)
    top1 = top3 = 0
    for f in sample:
        q = perturb(f["name"], rng)
        res = db.search(q, limit=3)
        ids = [r["food_id"] for r in res]
        top1 += bool(ids) and ids[0] == f["food_id"]
        top3 += f["food_id"] in ids
    return {"queries": len(sample), "top1_accuracy_pct": round(100 * top1 / len(sample), 1),
            "top3_accuracy_pct": round(100 * top3 / len(sample), 1),
            "note": "Measures the dish-name matcher applied to Gemini's photo labels; Gemini's visual recognition itself needs an API key and labelled photos."}


def eval_adaptation(rng):
    errs_on, errs_off = [], []
    for i in range(40):
        seed = rng.randrange(10**9)
        for adaptive, bucket in ((True, errs_on), (False, errs_off)):
            r = random.Random(seed)
            p = random_profile(r)
            p["goal"] = "lose"
            true_factor = r.uniform(0.85, 1.15)
            w, adjust = p["weight_kg"], 0.0
            weekly, history = [], []
            base = date(2025, 1, 1)
            for wk in range(10):
                t = compute_targets({**p, "weight_kg": w, "adaptive_adjust": adjust})
                true_tdee = t["tdee"] * true_factor
                start_w = w
                pts = []
                for day in range(7):
                    w += (t["kcal"] - true_tdee) / 7700
                    pts.append((base + timedelta(days=wk * 7 + day), w + r.gauss(0, 0.2)))
                weekly.append(w - start_w)
                history.extend(pts)
                if adaptive:
                    rc = recalculation(history[-14:], "lose", adjust)  # same 14-day window as the app
                    if rc:
                        adjust = rc["adaptive_adjust"]
            bucket.append(st.mean(abs(x - (-0.5)) for x in weekly[-4:]))
    return {"simulated_users": 40, "weeks": 10, "true_needs_vs_estimate": "uniform 85-115%",
            "final_4wk_rate_error_kg_week_with_adaptation": round(st.mean(errs_on), 3),
            "final_4wk_rate_error_kg_week_without_adaptation": round(st.mean(errs_off), 3),
            "error_reduction_pct": round(100 * (1 - st.mean(errs_on) / st.mean(errs_off)), 1)}


def main():
    rng = random.Random(SEED)
    t0 = time.time()
    out = {"seed": SEED}
    out["requirements"] = eval_targets(rng)
    print("requirements", out["requirements"])
    plans, out["meal_plans"] = eval_plans(rng)
    print("meal_plans", {k: v for k, v in out["meal_plans"].items() if k != "failed_profiles"})
    out["swaps"] = eval_swaps(plans, rng)
    print("swaps", out["swaps"])
    out["dish_matching"] = eval_matching(rng)
    print("dish_matching", out["dish_matching"])
    out["adaptation"] = eval_adaptation(rng)
    print("adaptation", out["adaptation"])
    km = json.loads((ROOT / "experiments" / "metrics.json").read_text())
    out["swap_model"] = {k: km[k] for k in ("chosen_k", "silhouette", "davies_bouldin", "swap_check")}
    out["food_database"] = {"dishes": len(food_db().foods), "allergens_tracked": ALLERGENS}
    out["eval_seconds"] = round(time.time() - t0, 1)
    d = ROOT / "experiments" / "eval"
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(out, indent=2))
    print(f"saved experiments/eval/metrics.json in {out['eval_seconds']} s")


if __name__ == "__main__":
    main()
