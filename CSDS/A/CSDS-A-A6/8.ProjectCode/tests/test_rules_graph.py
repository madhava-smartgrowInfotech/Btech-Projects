"""Rule engine (F3) and clause-combination graph (F4)."""
import json
from pathlib import Path

import pytest

from app.services.graph import RISKY_COMBOS, detect_risky_combinations, graph_to_json
from app.services.rules import RULES, RULES_BY_ID, detect_flags

ROOT = Path(__file__).resolve().parents[1]


def ids(text):
    return {r.id for r in detect_flags(text)}


POSITIVE = {
    "restraint_of_trade": "The Consultant shall not, directly or indirectly, engage in any competing business for two years.",
    "penalty_clause": "The Consultant shall pay a penalty of Rs. 25,000 per day of delay.",
    "unilateral_termination": "The Company may terminate this Agreement at any time without cause or notice.",
    "unlimited_liability": "The Contractor shall be liable for any and all losses, damages and claims.",
    "one_sided_arbitration": "Disputes go to arbitration by a person solely appointed by the Company.",
    "auto_renewal": "This Agreement shall automatically renew for successive one-year terms.",
    "ip_overreach": "The Contractor irrevocably assigns all right, title and interest in all deliverables worldwide.",
    "no_refund": "All fees paid under this Agreement are non-refundable.",
}


def test_eight_rules_with_unique_ids_and_severities():
    assert len(RULES) == 8
    assert len({r.id for r in RULES}) == 8
    assert {r.severity for r in RULES} <= {"low", "medium", "high"}
    assert set(RULES_BY_ID) == set(POSITIVE)


@pytest.mark.parametrize("rule_id,text", POSITIVE.items())
def test_each_rule_fires_on_its_textbook_clause(rule_id, text):
    assert rule_id in ids(text)


@pytest.mark.parametrize("text", [
    "Either party may terminate this Agreement by giving thirty days' written notice.",
    "Payment shall be made within thirty days of receipt of a valid invoice.",
    "This Agreement is governed by the laws of India and the courts at Hyderabad have jurisdiction.",
    "The Licensor grants the Licensee a non-exclusive licence to use the Software in India.",
    "Each party shall maintain adequate insurance cover for the duration of this Agreement.",
])
def test_ordinary_clauses_raise_no_flag(text):
    assert ids(text) == set()


def test_matching_is_case_insensitive_and_returns_rule_objects():
    hits = detect_flags("ALL FEES ARE NON-REFUNDABLE.")
    assert [r.id for r in hits] == ["no_refund"]
    assert hits[0].legal_basis


def test_one_clause_can_trigger_several_rules():
    text = ("The Company may terminate this Agreement at any time without notice. All fees are non-refundable "
            "and the Consultant shall pay a penalty of Rs. 10,000.")
    assert {"unilateral_termination", "no_refund", "penalty_clause"} <= ids(text)


def test_shipped_test_set_scores_as_documented():
    items = json.loads((ROOT / "data/sample/predatory_test_set.json").read_text(encoding="utf-8"))
    tp = fp = fn = 0
    for it in items:
        pred, exp = ids(it["text"]), set(it["expected_rules"])
        tp += len(pred & exp)
        fp += len(pred - exp)
        fn += len(exp - pred)
    assert len(items) == 40
    assert fp == 0
    assert tp / (tp + fn) == pytest.approx(0.941, abs=0.001)


# Paraphrases that a human reader would call predatory but the keyword patterns do not match.
@pytest.mark.xfail(reason="regex rules need the keyword; paraphrases slip through (documented limitation)", strict=True)
@pytest.mark.parametrize("rule_id,text", [
    ("restraint_of_trade", "The Freelancer agrees not to accept any engagement from another software house in India for twenty-four months."),
    ("no_refund", "Fees once paid cannot be returned for any reason."),
    ("unlimited_liability", "The Consultant's liability under this Agreement shall be unlimited."),
])
def test_known_false_negatives(rule_id, text):
    assert rule_id in ids(text)


@pytest.mark.xfail(reason="'liquidated damages' is flagged even when the clause is a fair, capped pre-estimate", strict=True)
def test_known_false_positive_on_fair_liquidated_damages():
    assert ids("Liquidated damages of 0.5% per week of delay, capped at 5%, are a genuine pre-estimate of the loss.") == set()


def combo_input(*rule_sets):
    return [{"id": i + 1, "flags": list(s)} for i, s in enumerate(rule_sets)]


def test_three_combinations_are_defined():
    assert {c["id"] for c in RISKY_COMBOS} == {"termination_norefund_penalty", "restraint_unlimited_liability", "autorenew_unilateral_termination"}


def test_combination_found_across_different_clauses():
    hits = detect_risky_combinations(combo_input(["unilateral_termination"], [], ["no_refund"], ["penalty_clause"]))
    assert [h["combo_id"] for h in hits] == ["termination_norefund_penalty"]
    assert hits[0]["clause_ids"] == [1, 3, 4]


def test_partial_combination_is_not_reported():
    assert detect_risky_combinations(combo_input(["unilateral_termination"], ["no_refund"])) == []


def test_two_combinations_can_fire_together():
    hits = detect_risky_combinations(combo_input(["restraint_of_trade"], ["unlimited_liability", "auto_renewal"], ["unilateral_termination"]))
    assert {h["combo_id"] for h in hits} == {"restraint_unlimited_liability", "autorenew_unilateral_termination"}


def test_graph_json_has_a_node_per_clause_and_pairwise_edges():
    clauses = [{"id": i, "clause_type": "X", "flags": f, "text_preview": "t"} for i, f in
               [(1, ["unilateral_termination"]), (2, ["no_refund"]), (3, ["penalty_clause"]), (4, [])]]
    combos = detect_risky_combinations(clauses)
    g = graph_to_json(clauses, combos)
    assert len(g["nodes"]) == 4
    assert [n["risky"] for n in g["nodes"]] == [True, True, True, False]
    assert len(g["edges"]) == 3  # 3 clauses in the combination -> 3 pairs
    assert g["risky_combinations"] == combos
