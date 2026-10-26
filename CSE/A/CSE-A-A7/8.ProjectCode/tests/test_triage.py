"""Unit tests for the fused record and the calibrated triage model."""
import pytest

from app.services import features, triage

VIT = dict(age=58, heart_rate=112, sbp=96, dbp=60, spo2=93, temp_c=36.9, resp_rate=22, arrival_mode="ambulance")
WELL = dict(age=30, heart_rate=76, sbp=120, dbp=78, spo2=99, temp_c=36.7, resp_rate=15, arrival_mode="walk-in")


def test_fused_record_has_36_inputs_in_model_order():
    row = features.fuse(VIT, {"chest_pain": 1})
    assert list(row) == features.FEATURES and len(row) == 36
    assert row["arrival_code"] == 2 and row["chest_pain"] == 1 and row["dyspnea"] == 0


def test_unknown_arrival_mode_defaults_to_walk_in():
    assert features.fuse({**VIT, "arrival_mode": "helicopter"}, {})["arrival_code"] == 0


@pytest.mark.parametrize("priority,level", [(1, "High"), (2, "High"), (3, "Moderate"), (4, "Low"), (5, "Low")])
def test_risk_level_mapping(priority, level):
    assert features.risk_level(priority) == level


def test_probabilities_sum_to_one_and_priority_is_argmax():
    r = triage.predict(VIT, {"chest_pain": 1, "st_elevation": 1, "lab_troponin_high": 1})
    p = r["probabilities"]
    assert abs(sum(p.values()) - 1) < 1e-3
    assert r["priority"] == int(max(p, key=p.get)) and r["confidence"] == max(p.values())


def test_sick_patient_is_more_urgent_than_well_patient():
    sick = triage.predict(VIT, {"chest_pain": 1, "st_elevation": 1, "lab_troponin_high": 1})
    well = triage.predict(WELL, {})
    assert sick["priority"] < well["priority"]
    assert well["risk_level"] == "Low"


def test_shap_sorted_by_absolute_impact_and_labelled():
    r = triage.predict(VIT, {"chest_pain": 1, "st_elevation": 1})
    impacts = [abs(s["impact"]) for s in r["shap"]]
    assert impacts == sorted(impacts, reverse=True) and r["shap"]
    assert all(s["direction"] in ("raises urgency", "lowers urgency") for s in r["shap"])
    assert all(s["feature"] in features.FEATURES for s in r["shap"])


def test_absent_flags_with_negligible_effect_are_hidden():
    r = triage.predict(WELL, {})
    assert all(not (s["feature"] in features.FLAGS and s["value"] == "absent" and abs(s["impact"]) < 0.15) for s in r["shap"])
