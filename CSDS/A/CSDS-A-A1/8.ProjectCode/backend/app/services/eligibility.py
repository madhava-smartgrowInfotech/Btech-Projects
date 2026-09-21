"""Deterministic claim pre-checks from the Policy Card: waiting periods vs. policy age, co-payment,
deductible, sub-limits and an out-of-pocket estimate. These facts are computed, not generated, and are
also given to the model so its verdict stays consistent with them.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.services.text_match import normalise, token_overlap


def months_between(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(0, months)


def _months(item: dict | None) -> float | None:
    if not item or not item.get("found") or not isinstance(item.get("number"), (int, float)):
        return None
    unit = item.get("unit")
    if unit == "days":
        return float(item["number"]) / 30.0
    if unit in ("months", "none"):
        return float(item["number"])
    return None


def _src(item: dict | None) -> dict[str, Any]:
    item = item or {}
    return {"clause_ordinal": item.get("clause_ordinal"), "page": item.get("page")}


def treatment_matches(treatment: str, names: list[str]) -> str | None:
    t = normalise(treatment)
    for name in names:
        n = normalise(name)
        if not n:
            continue
        if n in t or t in n or token_overlap(t, n) >= 0.6:
            return name
    aliases = {"knee replacement": "joint replacement", "hip replacement": "joint replacement",
               "tkr": "joint replacement", "lens": "cataract", "piles": "haemorrhoids", "hernia repair": "hernia"}
    for alias, target in aliases.items():
        if alias in t:
            for name in names:
                if target in normalise(name):
                    return name
    return None


def pre_checks(card: dict[str, Any] | None, treatment: str, inputs: dict[str, Any],
               today: date | None = None) -> dict[str, Any]:
    """Return {"checks": [...], "estimate": {...} | None, "facts": [...plain strings for the prompt]}."""
    today = today or date.today()
    checks: list[dict[str, Any]] = []
    facts: list[str] = []
    if not card:
        return {"checks": [], "estimate": None, "facts": ["No Policy Card is available for this policy."]}

    wp = card.get("waiting_periods") or {}
    start = inputs.get("policy_start_date")
    policy_months = months_between(start, today) if isinstance(start, date) else None
    if policy_months is not None:
        facts.append(f"The policy has been in force for {policy_months} months (since {start.isoformat()}).")

    def waiting_check(key: str, label: str, applies: bool | None, detail_if_unknown: str) -> None:
        item = wp.get(key)
        need = _months(item)
        if need is None:
            return
        need_text = (item or {}).get("value") or f"{need:g} months"
        if applies is False:
            return
        if policy_months is None:
            status, detail = "unknown", f"{label}: {need_text}. {detail_if_unknown}"
        elif policy_months >= need:
            status, detail = "pass", f"{label} of {need_text} is complete ({policy_months} months of cover)."
        else:
            status = "fail" if applies else "warning"
            remaining = max(0, round(need - policy_months))
            detail = f"{label} is {need_text}; you have {policy_months} months of cover, {remaining} more to go."
        checks.append({"check": label, "status": status, "detail": detail, "source": "rule", **_src(item)})
        facts.append(f"{label}: {need_text} (status: {status}).")

    waiting_check("initial", "Initial waiting period", True,
                  "Add your policy start date to check it (accidents are usually exempt).")
    examples = card.get("specific_disease_examples") or []
    matched = treatment_matches(treatment, examples)
    if matched:
        facts.append(f"'{treatment}' matches '{matched}' in the specific-disease waiting-period list.")
    waiting_check("specific_diseases", "Specific disease/procedure waiting period",
                  True if matched else None,
                  "Add your policy start date to check whether it is complete.")
    ped = inputs.get("pre_existing")
    if ped in ("yes", "not_sure"):
        waiting_check("pre_existing", "Pre-existing disease waiting period", ped == "yes" or None,
                      "Add your policy start date to check it.")

    # Sub-limits that name this treatment.
    sub_hit = None
    for sub in card.get("sub_limits") or []:
        if sub.get("found") and treatment_matches(treatment, [sub.get("name") or ""]):
            sub_hit = sub
            checks.append({"check": f"Sub-limit: {sub.get('name')}", "status": "warning",
                           "detail": f"This treatment is capped at {sub.get('value')}.", "source": "rule", **_src(sub)})
            facts.append(f"Sub-limit for {sub.get('name')}: {sub.get('value')}.")
            break

    copay = card.get("co_payment") or {}
    copay_pct = copay.get("number") if copay.get("found") and copay.get("unit") == "percent" else None
    age = inputs.get("insured_age")
    for cond in card.get("co_payment_conditions") or []:
        name = (cond.get("name") or "").lower()
        if cond.get("found") and age and "age" in name and cond.get("unit") == "percent":
            digits = [int(d) for d in "".join(ch if ch.isdigit() else " " for ch in name).split()]
            if digits and age >= min(digits):
                copay_pct = max(copay_pct or 0, cond.get("number") or 0)
                checks.append({"check": "Age-based co-payment", "status": "warning",
                               "detail": f"{cond.get('value')} may apply at age {age}.", "source": "rule",
                               **_src(cond)})
    if copay_pct:
        facts.append(f"Co-payment: {copay_pct:g}% of the admissible amount.")
        if not any(c["check"] == "Age-based co-payment" for c in checks):
            checks.append({"check": "Co-payment", "status": "warning",
                           "detail": f"You pay {copay_pct:g}% of each admissible claim.", "source": "rule",
                           **_src(copay)})

    room_type = inputs.get("room_type")
    room = card.get("room_rent_limit") or {}
    if room.get("found") and room_type in ("single_private", "deluxe"):
        checks.append({"check": "Room category", "status": "warning",
                       "detail": f"Room rent rule: {room.get('value')}. A costlier room than allowed can reduce "
                                 "the whole claim proportionately.", "source": "rule", **_src(room)})

    estimate = None
    cost = inputs.get("estimated_cost")
    if isinstance(cost, (int, float)) and cost > 0:
        deductible = card.get("deductible") or {}
        ded = deductible.get("number") if deductible.get("found") and deductible.get("unit") == "INR" else 0
        payable = max(0.0, float(cost) - float(ded or 0))
        cap_note = None
        if sub_hit and sub_hit.get("unit") == "INR" and isinstance(sub_hit.get("number"), (int, float)):
            if payable > sub_hit["number"]:
                payable = float(sub_hit["number"])
                cap_note = f"capped by the sub-limit ({sub_hit.get('value')})"
        copay_amount = payable * (copay_pct or 0) / 100
        payable -= copay_amount
        estimate = {
            "estimated_cost": float(cost),
            "deductible": float(ded or 0),
            "co_payment_percent": float(copay_pct or 0),
            "co_payment_amount": round(copay_amount),
            "insurer_pays": round(payable),
            "you_pay": round(float(cost) - payable),
            "notes": [n for n in [cap_note, "Estimate before non-payable items (consumables, registration "
                                  "charges) and before any room-rent proportionate deduction."] if n],
        }
        facts.append(f"Estimated split for Rs. {cost:,.0f}: insurer about Rs. {estimate['insurer_pays']:,}, "
                     f"you about Rs. {estimate['you_pay']:,}.")
    return {"checks": checks, "estimate": estimate, "facts": facts, "matched_specific_disease": matched}
