from datetime import date

from app.ml.retrieval.fusion import reciprocal_rank_fusion
from app.ml.retrieval.text import expand_query, tokenize
from app.services.eligibility import copay_applies, months_between, pre_checks, treatment_matches
from app.services.risk_engine import build_risks
from app.services.text_match import contains_text


def test_rrf_prefers_items_ranked_well_by_both():
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a", "d"]])
    assert fused[0][0] in {"a", "b"}
    assert {item for item, _ in fused} == {"a", "b", "c", "d"}


def test_tokenize_and_expand():
    assert "hospitalization" in tokenize("Hospitalisation expenses")
    expanded = expand_query("after how long is knee replacement covered?")
    assert "waiting period" in expanded and "joint replacement" in expanded


def test_contains_text_tolerates_layout_noise():
    clause = "shall be excluded until the expiry of 24 months of con-\ntinuous coverage after the date"
    assert contains_text(clause, "excluded until the expiry of 24 months of continuous coverage")
    assert not contains_text(clause, "maternity benefit is payable after 9 months")


def _item(value, number=None, unit="none", ordinal=1):
    return {"value": value, "number": number, "unit": unit, "found": True, "clause_ordinal": ordinal, "page": 1,
            "quote": None, "verified": True}


CARD = {
    "co_payment": _item("20% of admissible claim", 20, "percent"),
    "co_payment_conditions": [],
    "deductible": {"value": "Not specified", "found": False},
    "room_rent_limit": _item("Up to Rs. 5,000 per day", 5000, "INR"),
    "waiting_periods": {
        "pre_existing": _item("36 months", 36, "months"),
        "specific_diseases": _item("24 months", 24, "months"),
        "initial": _item("30 days", 30, "days"),
        "maternity": {"value": "Not covered", "found": False},
    },
    "specific_disease_examples": ["Cataract", "Joint replacement"],
    "sub_limits": [dict(_item("Up to Rs. 40,000 per eye", 40000, "INR"), name="Cataract")],
    "claim_timelines": {"emergency_intimation": _item("24 hours", 24, "hours")},
}


def test_risk_rules_and_dedupe():
    ai = [{"title": "36-Month Pre-Existing Disease Waiting Period", "category": "waiting_period", "severity": "high",
           "explanation": "PED covered after 36 months.", "clause_ordinal": 1, "page": 1, "quote": None, "source": "ai"},
          {"title": "Consumables are not payable", "category": "other", "severity": "medium",
           "explanation": "Gloves and masks are excluded.", "clause_ordinal": 9, "page": 2, "quote": None,
           "source": "ai"}]
    risks = build_risks(CARD, ai, [])
    titles = [r["title"] for r in risks]
    assert any("20% co-payment" in t for t in titles)
    assert any("3 years" in t for t in titles)
    assert "36-Month Pre-Existing Disease Waiting Period" not in titles  # duplicate of the rule finding
    assert "Consumables are not payable" in titles
    assert risks[0]["severity"] == "high"


def test_eligibility_waiting_periods_and_estimate():
    assert months_between(date(2024, 1, 15), date(2026, 1, 14)) == 23
    assert treatment_matches("knee replacement surgery", ["Joint replacement"]) == "Joint replacement"
    early = pre_checks(CARD, "Knee replacement", {"policy_start_date": date(2025, 12, 1), "estimated_cost": 200000},
                       today=date(2026, 6, 1))
    statuses = {c["check"]: c["status"] for c in early["checks"]}
    assert statuses["Specific disease/procedure waiting period"] == "fail"
    assert early["estimate"]["co_payment_percent"] == 20
    assert early["estimate"]["insurer_pays"] == 160000
    later = pre_checks(CARD, "Cataract surgery", {"policy_start_date": date(2022, 1, 1), "estimated_cost": 80000},
                       today=date(2026, 6, 1))
    statuses = {c["check"]: c["status"] for c in later["checks"]}
    assert statuses["Specific disease/procedure waiting period"] == "pass"
    assert later["estimate"]["insurer_pays"] == 32000  # capped at 40,000 then 20% co-payment


def test_copay_conditions():
    network = "Non-network hospitals 20% on each and every claim"
    assert copay_applies(network, 45, "cashless")[0] is False  # cashless means a network hospital
    assert copay_applies(network, 45, "reimbursement")[0] is None
    assert copay_applies("Treatment in hospitals other than those listed in Annexure III: 20%", 45, "cashless")[0] is False
    assert copay_applies("Age 61 years and above 20% co-payment", 58)[0] is False
    assert copay_applies("Age 61 years and above 20% co-payment", 64)[0] is True
    assert copay_applies("Voluntary co-payment of 10% if opted", 40)[0] is None
    assert copay_applies("20% of every admissible claim", 30)[0] is True
