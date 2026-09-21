"""F7 - Risk highlights: deterministic rules over the Policy Card + AI-found gotchas, with severity."""

from __future__ import annotations

import re
from typing import Any

from app.ml.retrieval.clause_cache import ClauseRecord
from app.services.text_match import token_overlap

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_CONDITIONAL = re.compile(r"\b(age|aged|zone|if|when|entry|optional|voluntary|non-?network|opted|chosen|city)\b", re.I)
_DURATION = re.compile(r"(\d+)\s*-?\s*(month|year)s?", re.I)
_UNLIMITED = re.compile(r"\b(no (limit|capping|cap|sub-?limit|restriction)|any room|actuals?|up to sum insured|"
                        r"upto sum insured|single private (a/?c )?room|no room rent)\b", re.I)


def _src(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {"clause_ordinal": item.get("clause_ordinal"), "page": item.get("page"), "quote": item.get("quote")}


def _num(item: dict[str, Any] | None) -> float | None:
    if not item or not item.get("found"):
        return None
    n = item.get("number")
    return float(n) if isinstance(n, (int, float)) else None


def _months(item: dict[str, Any] | None) -> float | None:
    n = _num(item)
    if n is None:
        return None
    unit = (item or {}).get("unit")
    if unit == "days":
        return n / 30.0
    if unit in ("months", "none"):
        return n
    return None


def _risk(rule_id: str, title: str, category: str, severity: str, explanation: str, item: dict | None) -> dict:
    return {"rule_id": rule_id, "title": title, "category": category, "severity": severity,
            "explanation": explanation, "source": "rule", **_src(item)}


def _fmt_months(m: float) -> str:
    m = round(m)
    return f"{m // 12} years" if m % 12 == 0 and m >= 12 else f"{m} months"


def rule_risks(card: dict[str, Any], clauses: list[ClauseRecord]) -> list[dict]:
    risks: list[dict] = []

    # Co-payment: a general one, unless it is really one of the conditional co-payments.
    copay = card.get("co_payment")
    pct = _num(copay)
    conditional_pcts = {_num(c) for c in card.get("co_payment_conditions") or [] if c.get("found")}
    if pct and pct > 0 and pct not in conditional_pcts and (copay or {}).get("unit") in ("percent", "none"):
        severity = "high" if pct >= 20 else "medium" if pct >= 10 else "low"
        conditional = bool(_CONDITIONAL.search((copay or {}).get("value") or ""))
        title = f"{pct:g}% co-payment (conditions apply)" if conditional else f"{pct:g}% co-payment on every claim"
        risks.append(_risk("copay_general", title, "co_payment", severity,
                           f"You pay {pct:g}% of each admissible claim yourself"
                           + (f" when it applies ({copay.get('value')})" if conditional else "")
                           + f"; on a Rs. 2 lakh bill that is Rs. {2_00_000 * pct / 100:,.0f}.", copay))
    for cond in card.get("co_payment_conditions") or []:
        cp = _num(cond)
        if cond.get("found") and cp:
            severity = "high" if cp >= 20 else "medium"
            risks.append(_risk("copay_conditional", f"{cp:g}% co-payment: {cond.get('name') or 'conditional'}",
                               "co_payment", severity,
                               f"A {cp:g}% co-payment applies when this condition is met ({cond.get('value')}).",
                               cond))

    # Deductible.
    ded = card.get("deductible")
    amount = _num(ded)
    if amount and amount > 0 and (ded or {}).get("unit") == "INR":
        risks.append(_risk("deductible", f"Deductible of Rs. {amount:,.0f}", "deductible", "medium",
                           "Claims are paid only above this amount each year/claim, so smaller bills may be "
                           "fully out of pocket.", ded))

    # Room rent cap, especially with proportionate deduction.
    room = card.get("room_rent_limit")
    if room and room.get("found") and not _UNLIMITED.search(room.get("value") or ""):
        proportionate = next((c for c in clauses if re.search(r"proportion(ate)?\b", c.text, re.I)
                              and re.search(r"room", c.text, re.I)), None)
        if proportionate:
            item = {"clause_ordinal": proportionate.ordinal, "page": proportionate.page_start, "quote": None}
            risks.append(_risk("room_rent_proportionate", "Room-rent limit with proportionate deduction", "room_rent",
                               "high", f"Room rent is capped ({room.get('value')}). Choosing a costlier room can "
                               "reduce the payout for the whole bill (doctor fees, tests) in the same proportion.",
                               item))
        else:
            risks.append(_risk("room_rent_cap", "Room rent is capped", "room_rent", "medium",
                               f"Room rent is limited to {room.get('value')}; the excess is yours to pay.", room))

    # Waiting periods.
    wp = card.get("waiting_periods") or {}
    ped = _months(wp.get("pre_existing"))
    if ped:
        severity = "high" if ped >= 36 else "medium" if ped >= 24 else "low"
        risks.append(_risk("ped_waiting", f"Pre-existing diseases covered only after {_fmt_months(ped)}",
                           "waiting_period", severity,
                           "Any illness you had before buying the policy is not covered until this period of "
                           "continuous cover is complete.", wp.get("pre_existing")))
    spec = _months(wp.get("specific_diseases"))
    if spec:
        examples = ", ".join((card.get("specific_disease_examples") or [])[:4])
        severity = "high" if spec >= 36 else "medium" if spec >= 24 else "low"
        risks.append(_risk("specific_waiting", f"{_fmt_months(spec)} wait for listed diseases/procedures",
                           "waiting_period", severity,
                           "Treatments on the specific list" + (f" (e.g. {examples})" if examples else "")
                           + " are not covered in this period.", wp.get("specific_diseases")))
    mat = _months(wp.get("maternity"))
    if mat and mat >= 24:
        risks.append(_risk("maternity_waiting", f"Maternity covered only after {_fmt_months(mat)}", "waiting_period",
                           "medium", "Plan ahead: pregnancy-related claims are paid only after this waiting period.",
                           wp.get("maternity")))

    # Sub-limits.
    for sub in (card.get("sub_limits") or [])[:6]:
        if sub.get("found"):
            risks.append(_risk("sub_limit", f"Sub-limit: {sub.get('name') or 'capped expense'}", "sub_limit",
                               "medium", f"This expense is capped at {sub.get('value')} even if your sum insured "
                               "is higher.", sub))

    # Tight claim intimation.
    emergency = (card.get("claim_timelines") or {}).get("emergency_intimation")
    hours = _num(emergency)
    if hours and (emergency or {}).get("unit") == "hours" and hours <= 24:
        risks.append(_risk("intimation", f"Emergency admission must be reported within {hours:g} hours",
                           "claim_process", "medium", "Late intimation can delay or complicate the claim.",
                           emergency))
    return risks


def _durations(text: str) -> set[int]:
    """Durations mentioned in a text, in months ("3 years" and "36-month" both -> 36)."""
    return {int(n) * (12 if unit.lower() == "year" else 1) for n, unit in _DURATION.findall(text)}


def _percents(text: str) -> set[str]:
    return set(re.findall(r"(\d+(?:\.\d+)?)\s*%", text))


def _same_finding(rule: dict, ai: dict) -> bool:
    if rule["category"] != ai["category"]:
        return False
    if token_overlap(rule["title"], ai["title"]) >= 0.5:
        return True
    rule_text, ai_text = f"{rule['title']} {rule['explanation']}", f"{ai['title']} {ai['explanation']}"
    if _durations(rule["title"]) & _durations(ai_text) or _percents(rule["title"]) & _percents(ai_text):
        return True
    return bool(rule.get("clause_ordinal")) and rule.get("clause_ordinal") == ai.get("clause_ordinal") \
        and token_overlap(rule_text, ai_text) >= 0.3


def build_risks(card: dict[str, Any], ai_risks: list[dict], clauses: list[ClauseRecord]) -> list[dict]:
    risks = rule_risks(card, clauses)
    rules = list(risks)
    for ai in ai_risks:
        if not any(_same_finding(r, ai) for r in rules):
            risks.append(ai)
    risks.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 3), r["source"] != "rule"))
    return risks
