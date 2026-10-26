"""The experiment simulator must make the same decisions as the real engine."""
from scripts import parity
from scripts.parking_sim import STRATEGIES, simulate


def test_admission_decisions_match_engine():
    r = parity.admission_parity(250)
    assert r["cases"] == 1250 and r["mismatches"] == 0


def test_trust_updates_match_engine():
    r = parity.trust_parity(80, 30)
    assert r["mismatches"] == 0


def test_suspension_matches_engine():
    r = parity.suspension_parity(150)
    assert r["mismatches"] == 0


def test_simulation_is_deterministic_per_seed():
    a = simulate(100, 0.25, "dynamic_parksure", 3)
    b = simulate(100, 0.25, "dynamic_parksure", 3)
    assert a == b


def test_every_request_has_exactly_one_outcome():
    for strat in STRATEGIES:
        m = simulate(90, 0.3, strat, 5)
        assert m["requests"] == m["no_reservation"] + m["suspended"] + m["no_park"] + m["parks_completed"]
