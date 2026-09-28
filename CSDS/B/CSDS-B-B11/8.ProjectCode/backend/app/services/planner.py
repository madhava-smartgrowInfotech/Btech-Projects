"""7-day meal plan optimiser (mixed-integer linear programme solved with PuLP / CBC).

Each day is one MILP:
  * binary y[slot, dish] picks a dish for a meal slot; integer k[slot, dish] sets its portion in
    quarter servings (0.5 - 2.0 servings when picked)
  * meal structure: breakfast = 1 main (+ optional drink); lunch/dinner = staple + curry, or a one-dish
    meal (+ optional side); snack = 1 snack or drink
  * hard limits: calories within +-4 % of target, meal calorie shares, sodium cap, free-sugar cap,
    glycaemic-load cap (diabetes), fibre floor
  * objective: minimise relative deviation from protein / carb / fat targets + fibre shortfall, plus small
    penalties for fried or rich dishes, non-preferred cuisine and a seeded random term for variety
Allergens, diet type and condition exclusions are removed before optimisation (hard block) and
re-checked on the final plan. Variety: a dish appears at most twice a week (staples excepted) and not
on consecutive days.
"""
import random
import time
from datetime import date, timedelta

import pulp

from .foods import FoodDB, food_db, round_to

SLOTS = ["breakfast", "lunch", "snack", "dinner"]
SLOT_ROLES = {"breakfast": ["bf", "bev"], "lunch": ["staple", "curry", "onedish", "side"],
              "snack": ["snack", "bev"], "dinner": ["staple", "curry", "onedish", "side"]}
SLOT_SHARE = {"breakfast": (0.18, 0.32), "lunch": (0.28, 0.42), "snack": (0.05, 0.18), "dinner": (0.22, 0.38)}
POOL_SIZE = {"bf": 40, "bev": 20, "staple": 20, "curry": 45, "onedish": 30, "side": 35, "snack": 30}
MAX_WEEKLY_USES = 2
STAPLE_WEEKLY_USES = 4
KCAL_TOL = 0.04
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class PlanError(Exception):
    pass


def cuisine_weight(food_cuisine: str, pref: str) -> float:
    if food_cuisine == "indo_chinese":
        return 0.15
    if food_cuisine == "continental":
        return 0.3
    if pref in ("both", "any", "") or food_cuisine == pref:
        return 1.0
    return 0.35


def eligible_foods(db: FoodDB, prefs: dict):
    by_role = {r: [] for r in POOL_SIZE}
    for f in db.foods.values():
        if f["role"] in by_role and f["kcal"] > 0 and db.allowed(f, prefs):
            by_role[f["role"]].append(f)
    return by_role


def sample_pool(foods, n, rng, pref):
    """Weighted sampling without replacement (Efraimidis-Spirakis) favouring the preferred cuisine."""
    keyed = [(rng.random() ** (1.0 / cuisine_weight(f["cuisine"], pref)), f) for f in foods]
    keyed.sort(key=lambda x: -x[0])
    return [f for _, f in keyed[:n]]


def solve_day(pools, targets, rng, pref, tol=KCAL_TOL, use_shares=True):
    T = targets["kcal"]
    prob = pulp.LpProblem("day", pulp.LpMinimize)
    y, k, meta = {}, {}, {}
    for slot in SLOTS:
        for role in SLOT_ROLES[slot]:
            for f in pools.get(role, []):
                key = (slot, role, int(f["food_id"]))
                y[key] = pulp.LpVariable(f"y_{slot}_{role}_{f['food_id']}", cat="Binary")
                k[key] = pulp.LpVariable(f"k_{slot}_{role}_{f['food_id']}", lowBound=0, upBound=8, cat="Integer")
                prob += k[key] >= 2 * y[key]
                prob += k[key] <= 8 * y[key]
                meta[key] = f
    if not y:
        raise PlanError("No dishes match your diet and allergy settings.")

    def amount(key, nutrient):
        f = meta[key]
        quarter_g = f["serving_g"] / 4.0
        if nutrient == "gl":
            per_g = f["gi"] / 100.0 * f["carbs"] / 100.0
        else:
            per_g = f[nutrient] / 100.0
        return per_g * quarter_g * k[key]

    def total(nutrient, keys=None):
        return pulp.lpSum(amount(key, nutrient) for key in (keys if keys is not None else y))

    def keys_for(slot=None, roles=None):
        return [key for key in y if (slot is None or key[0] == slot) and (roles is None or key[1] in roles)]

    # meal structure
    prob += pulp.lpSum(y[q] for q in keys_for("breakfast", ["bf"])) == 1
    prob += pulp.lpSum(y[q] for q in keys_for("breakfast", ["bev"])) <= 1
    for slot in ("lunch", "dinner"):
        staple = pulp.lpSum(y[q] for q in keys_for(slot, ["staple"]))
        one = pulp.lpSum(y[q] for q in keys_for(slot, ["onedish"]))
        curry = pulp.lpSum(y[q] for q in keys_for(slot, ["curry"]))
        prob += staple + one == 1
        prob += curry == staple
        prob += pulp.lpSum(y[q] for q in keys_for(slot, ["side"])) <= 1
    prob += pulp.lpSum(y[q] for q in keys_for("snack")) == 1
    # a dish at most once per day
    by_food = {}
    for key in y:
        by_food.setdefault(key[2], []).append(y[key])
    for vars_ in by_food.values():
        if len(vars_) > 1:
            prob += pulp.lpSum(vars_) <= 1

    # energy
    E = total("kcal")
    prob += E >= (1 - tol) * T
    prob += E <= (1 + tol) * T
    if use_shares:
        for slot, (lo, hi) in SLOT_SHARE.items():
            e_slot = total("kcal", keys_for(slot))
            prob += e_slot >= lo * T
            prob += e_slot <= hi * T

    # condition limits (hard)
    # 1 % margin so rounding portions to whole grams can never push a day over a cap
    prob += total("sodium") <= 0.99 * targets["sodium_max_mg"]
    prob += total("sugar") <= 0.99 * targets["sugar_max_g"]
    if targets.get("gl_max"):
        prob += total("gl") <= 0.99 * targets["gl_max"]
    prob += total("fibre") >= 0.6 * targets["fibre_g"]

    # objective: macro deviations
    obj = []
    for nutrient, tgt_key, weight in (("protein", "protein_g", 3.0), ("carbs", "carbs_g", 2.0), ("fat", "fat_g", 2.0)):
        tgt = max(targets[tgt_key], 1)
        over = pulp.LpVariable(f"over_{nutrient}", lowBound=0)
        under = pulp.LpVariable(f"under_{nutrient}", lowBound=0)
        prob += total(nutrient) - tgt == over - under
        obj.append(weight * (over + under) / tgt)
    e_over = pulp.LpVariable("over_kcal", lowBound=0)
    e_under = pulp.LpVariable("under_kcal", lowBound=0)
    prob += E - T == e_over - e_under
    obj.append(4.0 * (e_over + e_under) / T)
    fib_short = pulp.LpVariable("fibre_short", lowBound=0)
    prob += fib_short >= targets["fibre_g"] - total("fibre")
    obj.append(2.0 * fib_short / targets["fibre_g"])
    for key, var in y.items():
        f = meta[key]
        pen = 0.12 * rng.random()
        pen += 0.25 if f["fried"] else 0
        pen += 0.08 if f["rich"] else 0
        pen += 0.1 * (1 - cuisine_weight(f["cuisine"], pref))
        obj.append(pen * var)
    prob += pulp.lpSum(obj)

    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=20))
    # accept a proven optimum or the best integer-feasible solution found within the time limit
    if prob.sol_status not in (pulp.LpSolutionOptimal, pulp.LpSolutionIntegerFeasible):
        return None
    picks = []
    for key, var in y.items():
        if var.value() and var.value() > 0.5:
            picks.append((key[0], key[1], meta[key], int(round(k[key].value()))))
    return picks


def build_day(db: FoodDB, picks, day_index, start):
    meals = {s: [] for s in SLOTS}
    for slot, role, f, quarters in picks:
        grams = round_to(f["serving_g"] * quarters / 4.0, 1)
        meals[slot].append({
            "food_id": int(f["food_id"]), "name": f["name"], "role": role, "cuisine": f["cuisine"],
            "servings": quarters / 4.0, "grams": grams, **db.nutrients(f, grams),
        })
    order = {"bf": 0, "staple": 1, "onedish": 1, "curry": 2, "side": 3, "snack": 4, "bev": 5}
    for s in SLOTS:
        meals[s].sort(key=lambda it: order.get(it["role"], 9))
    d = start + timedelta(days=day_index)
    return {"day": day_index + 1, "date": d.isoformat(), "weekday": DAY_NAMES[d.weekday()], "meals": meals,
            "totals": day_totals(meals)}


def day_totals(meals):
    keys = ["kcal", "protein", "carbs", "fat", "fibre", "sugar", "sodium", "gl"]
    out = {k: 0.0 for k in keys}
    for items in meals.values():
        for it in items:
            for k in keys:
                out[k] += it.get(k, 0.0)
    return {k: round(v, 1) for k, v in out.items()}


def check_day(db: FoodDB, day, prefs, targets):
    """Post-optimisation guardrail check. Returns a list of problems (empty = safe)."""
    problems = []
    for slot, items in day["meals"].items():
        for it in items:
            f = db.get(it["food_id"])
            if f is None or not db.allowed(f, prefs):
                problems.append(f"{it['name']} is not allowed for this profile")
    t = day["totals"]
    if t["kcal"] < targets["calorie_floor"]:
        problems.append("below the safe calorie floor")
    if t["sodium"] > targets["sodium_max_mg"] + 1:
        problems.append("sodium above cap")
    if targets.get("gl_max") and t["gl"] > targets["gl_max"] + 1:
        problems.append("glycaemic load above cap")
    return problems


def generate_week(prefs: dict, targets: dict, seed: int | None = None, start: date | None = None) -> dict:
    db = food_db()
    start = start or date.today()
    seed = seed if seed is not None else random.randrange(1_000_000)
    rng = random.Random(seed)
    by_role = eligible_foods(db, prefs)
    missing = [r for r in ("bf", "curry", "snack") if not by_role[r]]
    if missing or not (by_role["staple"] or by_role["onedish"]):
        raise PlanError("Too few dishes match your diet and allergy settings to build a plan.")
    pref = prefs.get("cuisine", "both")
    uses, yesterday = {}, set()
    days, t0 = [], time.time()
    for i in range(7):
        picks = None
        relax = None
        for attempt, (tol, shares) in enumerate([(KCAL_TOL, True), (KCAL_TOL, True), (0.05, False), (0.08, False)]):
            pools = {}
            for role, foods in by_role.items():
                cap = STAPLE_WEEKLY_USES if role == "staple" else MAX_WEEKLY_USES
                avail = [f for f in foods if uses.get(f["food_id"], 0) < cap
                         and (role == "staple" or f["food_id"] not in yesterday)]
                if len(avail) < 3:  # tiny pools (strict allergy combos): allow repeats rather than fail
                    avail = foods
                pools[role] = sample_pool(avail, POOL_SIZE[role] * (1 + attempt), rng, pref)
            picks = solve_day(pools, targets, rng, pref, tol=tol, use_shares=shares)
            if picks:
                if attempt >= 2:
                    relax = f"calorie band widened to +-{int(tol * 100)}% to respect your limits"
                break
        if not picks:
            raise PlanError("Could not build a day that satisfies all of your limits. Try a broader cuisine or fewer restrictions.")
        day = build_day(db, picks, i, start)
        if relax:
            day["note"] = relax
        problems = check_day(db, day, prefs, targets)
        if problems:
            raise PlanError("Safety check failed: " + "; ".join(problems))
        days.append(day)
        yesterday = set()
        for _, role, f, _ in picks:
            uses[f["food_id"]] = uses.get(f["food_id"], 0) + 1
            yesterday.add(f["food_id"])
    return {
        "seed": seed,
        "start_date": start.isoformat(),
        "targets": {k: targets[k] for k in ("kcal", "protein_g", "carbs_g", "fat_g", "fibre_g", "sodium_max_mg", "sugar_max_g", "gl_max", "calorie_floor")},
        "days": days,
        "solve_seconds": round(time.time() - t0, 2),
        "unique_dishes": len(uses),
    }


# ---------------------------------------------------------------------------- swaps
def swap_options(plan: dict, day_i: int, slot: str, idx: int, prefs: dict, targets: dict, limit: int = 6):
    db = food_db()
    day = plan["days"][day_i]
    item = day["meals"][slot][idx]
    food = db.get(item["food_id"])
    used_today = {it["food_id"] for items in day["meals"].values() for it in items}
    cands = [f for f in db.foods.values()
             if f["role"] == item["role"] and f["food_id"] not in used_today and f["kcal"] > 0 and db.allowed(f, prefs)]
    out = []
    for f, dist, same_cluster in db.similar(food, cands):
        grams = item["kcal"] / f["kcal"] * 100
        grams = min(max(grams, 0.5 * f["serving_g"]), 2.0 * f["serving_g"])
        grams = round_to(grams, 5)
        n = db.nutrients(f, grams)
        new_tot = {k: day["totals"][k] - item.get(k, 0) + n[k] for k in n}
        if new_tot["sodium"] > targets["sodium_max_mg"] or (targets.get("gl_max") and new_tot["gl"] > targets["gl_max"]):
            continue
        out.append({"food_id": int(f["food_id"]), "name": f["name"], "role": item["role"], "cuisine": f["cuisine"],
                    "grams": grams, "servings": round(grams / f["serving_g"], 2), **n,
                    "same_cluster": same_cluster, "similarity": round(1 / (1 + dist), 3),
                    "kcal_diff": round(n["kcal"] - item["kcal"], 1)})
        if len(out) >= limit:
            break
    return {"original": item, "options": out}


def apply_swap(plan: dict, day_i: int, slot: str, idx: int, food_id: int, grams: float, prefs: dict, targets: dict):
    db = food_db()
    f = db.get(food_id)
    if f is None:
        raise PlanError("Unknown dish.")
    if not db.allowed(f, prefs):
        raise PlanError("That dish is not allowed for your diet, allergies or conditions.")
    day = plan["days"][day_i]
    old = day["meals"][slot][idx]
    grams = round_to(min(max(grams, 0.25 * f["serving_g"]), 2.0 * f["serving_g"]), 1)
    day["meals"][slot][idx] = {"food_id": int(f["food_id"]), "name": f["name"], "role": old["role"],
                               "cuisine": f["cuisine"], "servings": round(grams / f["serving_g"], 2),
                               "grams": grams, **db.nutrients(f, grams), "swapped_from": old["name"]}
    day["totals"] = day_totals(day["meals"])
    problems = check_day(db, day, prefs, targets)
    if problems:
        day["meals"][slot][idx] = old
        day["totals"] = day_totals(day["meals"])
        raise PlanError("Swap rejected by safety check: " + "; ".join(problems))
    return plan
