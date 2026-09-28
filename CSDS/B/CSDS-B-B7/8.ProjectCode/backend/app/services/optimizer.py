"""Allocation optimiser (OR-Tools mixed-integer programme, SCIP backend).

Given the peak forecast load per facility x ward over the planning horizon, three small integer
programmes run in sequence (each minimises shortfall first, then the cost of the actions):
  1. beds      - bed conversions between compatible wards inside a facility, then diversion of
                 new admissions to another facility;
  2. nurses    - float surplus nurses between wards per shift, then extra nurse shifts;
  3. equipment - transfers between facilities.
Any shortfall is far more expensive than the actions that remove it.
"""
import math
import time

from ortools.linear_solver import pywraplp

from ..config import CONVERTIBLE, EQUIPMENT, FACILITIES, ICU_CONVERSION_LIMIT, NURSE_RATIO, SHIFTS, WARDS

COST = {"bed_short": 1000, "nurse_short": 400, "equip_short": 300,
        "convert": 4, "divert": 150, "float": 3, "extra_shift": 12, "transfer": 5}


def shortfalls(demand, capacity, roster, inventory, rates):
    """Shortfall of a given allocation against a load (no actions)."""
    beds = sum(max(0, demand[f][w] - capacity[f][w]) for f in FACILITIES for w in WARDS)
    nurses = sum(max(0, math.ceil(demand[f][w] / NURSE_RATIO[w][s]) - roster[f][w][s])
                 for f in FACILITIES for w in WARDS for s in SHIFTS)
    equip = 0
    for f in FACILITIES:
        for e in EQUIPMENT:
            need = math.ceil(sum(demand[f][w] * rates[w][e] for w in WARDS) - 1e-9)
            equip += max(0, need - inventory[f][e])
    return {"bed_shortfall": beds, "nurse_shift_gap": nurses, "equipment_gap": equip}


def _solver(time_limit):
    m = pywraplp.Solver.CreateSolver("SCIP")
    m.SetTimeLimit(int(time_limit * 1000))
    return m


def _solve(m):
    status = m.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        raise RuntimeError("Optimiser found no feasible plan")
    return status == pywraplp.Solver.OPTIMAL


def _val(x):
    return int(round(x.solution_value()))


def plan_beds(demand, capacity, time_limit):
    """Stage 1: bed conversions inside a facility, then diversions between facilities."""
    m = _solver(time_limit)
    conv, div = {}, {}
    for f in FACILITIES:
        for a, b in CONVERTIBLE:
            ub = capacity[f][a]
            if b == "ICU":
                ub = min(ub, math.floor(capacity[f]["ICU"] * ICU_CONVERSION_LIMIT))
            conv[f, a, b] = m.IntVar(0, ub, f"conv_{f}_{a}_{b}")
        for a in WARDS:
            m.Add(sum(conv[f, x, y] for x, y in CONVERTIBLE if x == a) <= capacity[f][a])
        for g in FACILITIES:
            if g != f:
                for w in WARDS:
                    div[f, g, w] = m.IntVar(0, demand[f][w], f"div_{f}_{g}_{w}")
    unmet = []
    for f in FACILITIES:
        for w in WARDS:
            beds = (capacity[f][w] - sum(conv[f, w, b] for a, b in CONVERTIBLE if a == w)
                    + sum(conv[f, a, w] for a, b in CONVERTIBLE if b == w))
            out = sum(div[f, g, w] for g in FACILITIES if g != f)
            load = demand[f][w] - out + sum(div[g, f, w] for g in FACILITIES if g != f)
            m.Add(out <= demand[f][w])
            u = m.IntVar(0, 100000, f"unmet_{f}_{w}")
            m.Add(u >= load - beds)
            unmet.append(u)
    m.Minimize(COST["bed_short"] * sum(unmet) + COST["convert"] * sum(conv.values())
               + COST["divert"] * sum(div.values()))
    optimal = _solve(m)
    actions = [{"type": "bed_conversion", "facility": f, "from_ward": a, "to_ward": b, "quantity": _val(x)}
               for (f, a, b), x in conv.items() if _val(x)]
    actions += [{"type": "diversion", "facility": f, "to_facility": g, "ward": w, "quantity": _val(x)}
                for (f, g, w), x in div.items() if _val(x)]
    return actions, optimal


def plan_nurses(load, roster, time_limit):
    """Stage 2: per facility and shift, float surplus nurses between wards, then add extra shifts."""
    actions, optimal = [], True
    for f in FACILITIES:
        for s in SHIFTS:
            m = _solver(time_limit)
            flt = {(a, b): m.IntVar(0, roster[f][a][s], f"flt_{a}_{b}")
                   for a in WARDS for b in WARDS if a != b and not (b == "ICU" and a != "ICU")}
            extra = {w: m.IntVar(0, 1000, f"extra_{w}") for w in WARDS}
            gaps = []
            for w in WARDS:
                out = sum(v for (a, b), v in flt.items() if a == w)
                m.Add(out <= roster[f][w][s])
                staff = roster[f][w][s] + extra[w] - out + sum(v for (a, b), v in flt.items() if b == w)
                gap = m.IntVar(0, 1000, f"gap_{w}")
                m.Add(gap >= math.ceil(load[f][w] / NURSE_RATIO[w][s]) - staff)
                gaps.append(gap)
            m.Minimize(COST["nurse_short"] * sum(gaps) + COST["float"] * sum(flt.values())
                       + COST["extra_shift"] * sum(extra.values()))
            optimal &= _solve(m)
            actions += [{"type": "nurse_float", "facility": f, "from_ward": a, "to_ward": b, "shift": s,
                         "quantity": _val(x)} for (a, b), x in flt.items() if _val(x)]
            actions += [{"type": "extra_shift", "facility": f, "ward": w, "shift": s, "quantity": _val(x)}
                        for w, x in extra.items() if _val(x)]
    return actions, optimal


def plan_equipment(load, inventory, rates, time_limit):
    """Stage 3: move equipment from facilities with spare units to those that are short."""
    actions, optimal = [], True
    for e in EQUIPMENT:
        m = _solver(time_limit)
        trf = {(f, g): m.IntVar(0, inventory[f][e], f"trf_{f}_{g}") for f in FACILITIES for g in FACILITIES if f != g}
        gaps = []
        for f in FACILITIES:
            need = math.ceil(sum(load[f][w] * rates[w][e] for w in WARDS) - 1e-9)
            out = sum(trf[f, g] for g in FACILITIES if g != f)
            m.Add(out <= inventory[f][e])
            gap = m.IntVar(0, 100000, f"gap_{f}")
            m.Add(gap >= need - (inventory[f][e] - out + sum(trf[g, f] for g in FACILITIES if g != f)))
            gaps.append(gap)
        m.Minimize(COST["equip_short"] * sum(gaps) + COST["transfer"] * sum(trf.values()))
        optimal &= _solve(m)
        actions += [{"type": "equipment_transfer", "facility": f, "to_facility": g, "item": e, "quantity": _val(x)}
                    for (f, g), x in trf.items() if _val(x)]
    return actions, optimal


def optimize(demand, capacity, roster, inventory, rates, time_limit=10.0):
    """demand[f][w] = integer patients to plan for. Returns the recommended actions."""
    t0 = time.time()
    bed_actions, ok1 = plan_beds(demand, capacity, time_limit)
    _, _, _, load = apply_actions(bed_actions, demand, capacity, roster, inventory)
    nurse_actions, ok2 = plan_nurses(load, roster, time_limit)
    equip_actions, ok3 = plan_equipment(load, inventory, rates, time_limit)
    actions = bed_actions + nurse_actions + equip_actions
    for i, a in enumerate(actions):
        a["id"] = i + 1
    return {"status": "OPTIMAL" if ok1 and ok2 and ok3 else "FEASIBLE", "actions": actions,
            "solve_seconds": round(time.time() - t0, 2)}


def apply_actions(actions, demand, capacity, roster, inventory):
    """Allocation (and load) after applying actions; used for evaluation and plan acceptance."""
    cap = {f: dict(capacity[f]) for f in FACILITIES}
    ros = {f: {w: dict(roster[f][w]) for w in WARDS} for f in FACILITIES}
    inv = {f: dict(inventory[f]) for f in FACILITIES}
    load = {f: dict(demand[f]) for f in FACILITIES} if demand else None
    for a in actions:
        q = int(a["quantity"])
        if q <= 0:
            continue
        t, f = a["type"], a["facility"]
        if t == "bed_conversion":
            cap[f][a["from_ward"]] -= q
            cap[f][a["to_ward"]] += q
        elif t == "diversion" and load is not None:
            q = min(q, load[f][a["ward"]])
            load[f][a["ward"]] -= q
            load[a["to_facility"]][a["ward"]] += q
        elif t == "nurse_float":
            ros[f][a["from_ward"]][a["shift"]] -= q
            ros[f][a["to_ward"]][a["shift"]] += q
        elif t == "extra_shift":
            ros[f][a["ward"]][a["shift"]] += q
        elif t == "equipment_transfer":
            inv[f][a["item"]] -= q
            inv[a["to_facility"]][a["item"]] += q
    return cap, ros, inv, load


def explain(actions, demand, capacity, roster, inventory, rates, peak_day_label):
    """Attach a plain-language reason to each action and summarise the trade-off."""
    cap, ros, inv, load = apply_actions(actions, demand, capacity, roster, inventory)
    for a in actions:
        f, q = a["facility"], a["quantity"]
        if a["type"] == "bed_conversion":
            s, t = a["from_ward"], a["to_ward"]
            a["reason"] = (f"{t} at Facility {f}: peak load {demand[f][t]} vs {capacity[f][t]} beds "
                           f"({peak_day_label[f][t]}). {s} keeps {cap[f][s]} beds for a load of {load[f][s]}.")
        elif a["type"] == "diversion":
            g, w = a["to_facility"], a["ward"]
            conv_note = f" after conversions ({capacity[f][w]} before)" if cap[f][w] != capacity[f][w] else ""
            a["reason"] = (f"Facility {f} {w}: peak {demand[f][w]} patients vs {cap[f][w]} beds{conv_note}, and no "
                           f"compatible beds are left to convert there. Facility {g} {w} can take them "
                           f"(load {load[g][w]} of {cap[g][w]} beds after the plan).")
        elif a["type"] == "nurse_float":
            s, t, sh = a["from_ward"], a["to_ward"], a["shift"]
            a["reason"] = (f"{sh} shift: {s} is over-rostered for its forecast load, {t} is short. "
                           f"Floating is cheaper than an extra shift.")
        elif a["type"] == "extra_shift":
            w, sh = a["ward"], a["shift"]
            need = math.ceil(load[f][w] / NURSE_RATIO[w][sh])
            a["reason"] = (f"{sh} shift needs {need} nurses for a peak of {load[f][w]} patients "
                           f"(1:{NURSE_RATIO[w][sh]}); {roster[f][w][sh]} rostered and no surplus nurse to float.")
        elif a["type"] == "equipment_transfer":
            g, e = a["to_facility"], a["item"]
            need_g = math.ceil(sum(load[g][w] * rates[w][e] for w in WARDS) - 1e-9)
            need_f = math.ceil(sum(load[f][w] * rates[w][e] for w in WARDS) - 1e-9)
            a["reason"] = (f"Facility {g} needs {need_g} {e.lower()}s and holds {inventory[g][e]}; "
                           f"Facility {f} needs {need_f} and holds {inventory[f][e]}.")
    before = shortfalls(demand, capacity, roster, inventory, rates)
    after = shortfalls(load, cap, ros, inv, rates)
    counts = {}
    for a in actions:
        counts[a["type"]] = counts.get(a["type"], 0) + a["quantity"]
    parts = []
    if counts.get("bed_conversion"):
        parts.append(f"{counts['bed_conversion']} beds are converted between wards (cheapest fix, keeps patients local)")
    if counts.get("diversion"):
        parts.append(f"{counts['diversion']} admissions are diverted to another facility where no bed can be converted")
    if counts.get("nurse_float"):
        parts.append(f"{counts['nurse_float']} nurse shifts float from over-rostered wards before paying for extras")
    if counts.get("extra_shift"):
        parts.append(f"{counts['extra_shift']} extra nurse shifts cover the remaining gap")
    if counts.get("equipment_transfer"):
        parts.append(f"{counts['equipment_transfer']} equipment units move from facilities with spare stock")
    text = "; ".join(parts) + "." if parts else "The current allocation already covers the forecast peak."
    if any(after.values()):
        text += (f" Remaining shortfall after the plan: {after['bed_shortfall']} beds, {after['nurse_shift_gap']} nurse "
                 f"shifts, {after['equipment_gap']} equipment units - no spare capacity is left to cover it.")
    return {"before": before, "after": after, "action_totals": counts, "text": text}
