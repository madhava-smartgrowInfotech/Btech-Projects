import time

import pytest

from monitoring.simulator import TrafficSimulator
from monitoring.traffic_aggregator import aggregate_packets
from security import distributed_analysis, severity
from security.mitigation import MitigationManager
from tests.conftest import attack_context, attack_features, benign_features

LOCAL = {"192.168.1.20"}


def pk(src, dst, proto="TCP", length=100):
    return {"src": src, "dst": dst, "proto": proto, "length": length}


# ---- aggregator -------------------------------------------------------------------------------------------------
def test_aggregator_orientation_and_rates():
    packets = [pk("192.168.1.20", "8.8.8.8", length=100)] * 4 + [pk("8.8.8.8", "192.168.1.20", length=300)] * 6
    feats, ctx = aggregate_packets(packets, 2.0, LOCAL)
    assert feats["sent_packets"] == 4 and feats["received_packets"] == 6
    assert feats["sent_bytes"] == 400 and feats["received_bytes"] == 1800
    assert feats["received_packets_per_second"] == pytest.approx(3.0)
    assert feats["average_received_packet_size"] == pytest.approx(300.0)
    assert ctx["unique_sources"] == 2 and ctx["unique_destinations"] == 2


def test_aggregator_external_transit_counts_as_received():
    feats, _ = aggregate_packets([pk("1.1.1.1", "2.2.2.2")], 1.0, LOCAL)
    assert feats["received_packets"] == 1 and feats["sent_packets"] == 0


def test_aggregator_empty_window_is_all_zero():
    feats, ctx = aggregate_packets([], 10.0, LOCAL)
    assert all(v == 0.0 for v in feats.values()) and ctx["packet_count"] == 0 and ctx["top_sources"] == []


def test_aggregator_skips_malformed_packet_and_ranks_top_sources():
    packets = [pk("9.9.9.9", "192.168.1.20")] * 3 + [pk("8.8.8.8", "192.168.1.20")] + [{"src": "x", "length": "bad"}]
    _, ctx = aggregate_packets(packets, 1.0, LOCAL)
    assert ctx["top_sources"][0] == {"ip": "9.9.9.9", "packets": 3}
    assert ctx["packet_count"] == 5


def test_aggregator_protocol_shares():
    packets = [pk("a", "b", "TCP")] * 3 + [pk("a", "b", "UDP")]
    _, ctx = aggregate_packets(packets, 1.0, LOCAL)
    assert ctx["tcp_share"] == pytest.approx(0.75) and ctx["udp_share"] == pytest.approx(0.25)


# ---- distributed risk ---------------------------------------------------------------------------------------------
def test_distributed_risk_low_for_concentrated_benign():
    r = distributed_analysis.compute_distributed_risk(benign_features(), {"unique_sources": 2, "unique_destinations": 2})
    assert r["distributed_risk_level"] == "Low" and 0 <= r["distributed_risk_score"] < 0.4


def test_distributed_risk_high_for_wide_spread_high_rate():
    r = distributed_analysis.compute_distributed_risk(attack_features(), attack_context())
    assert r["distributed_risk_level"] == "High" and r["distributed_risk_score"] <= 1.0
    assert "carpet" in r["explanation"] or "distributed" in r["explanation"]


def test_distributed_risk_components_sum_to_score():
    r = distributed_analysis.compute_distributed_risk(attack_features(), attack_context(12, 4), {"packet_rate": 100.0})
    c = r["components"]
    expected = (0.30 * c["source_diversity"] + 0.30 * c["destination_diversity"]
                + 0.25 * c["packet_rate_pressure"] + 0.15 * c["baseline_deviation"])
    assert r["distributed_risk_score"] == pytest.approx(expected, abs=0.01)


def test_carpet_bombing_label_for_many_destinations():
    r = distributed_analysis.compute_distributed_risk(benign_features(), {"unique_sources": 3, "unique_destinations": 10})
    assert "carpet" in r["explanation"]


# ---- severity -----------------------------------------------------------------------------------------------------
def _dist(rate=100.0, risk=0.1, src=2, dst=2):
    return {"packet_rate": rate, "distributed_risk_score": risk, "unique_sources": src,
            "unique_destinations": dst, "explanation": "x"}


def test_benign_window_never_exceeds_medium():
    s = severity.assess_severity("Benign", 0.99, benign_features(), _dist(5000, 0.95, 50, 20), 5)
    assert s["severity"] in ("Low", "Medium") and s["severity_score"] <= 45


def test_confident_wide_attack_is_critical_and_lists_factors():
    s = severity.assess_severity("Attack", 0.99, attack_features(), _dist(6000, 0.9, 40, 14), 3)
    assert s["severity"] == "Critical" and len(s["factors"]) >= 5 and "Quarantine" in s["recommendation"]


def test_weak_attack_is_medium_or_low():
    s = severity.assess_severity("Attack", 0.55, benign_features(), _dist(150, 0.1), 0)
    assert s["severity"] in ("Low", "Medium")


def test_persistence_raises_score():
    a = severity.assess_severity("Attack", 0.8, attack_features(), _dist(500, 0.3), 0)["severity_score"]
    b = severity.assess_severity("Attack", 0.8, attack_features(), _dist(500, 0.3), 3)["severity_score"]
    assert b == pytest.approx(a + 10)


# ---- mitigation ---------------------------------------------------------------------------------------------------
def test_high_severity_quarantines_top_three_sources(db):
    m = MitigationManager(db, quarantine_seconds=40)
    acts = m.decide("High", attack_context(), "test")
    assert [a["action"] for a in acts] == ["quarantine"] * 3 and all(a["duration"] == 40 for a in acts)
    assert len(m.get_active()) == 3 and len(db.get_mitigations()) == 3


def test_critical_doubles_duration(db):
    acts = MitigationManager(db, 40).decide("Critical", attack_context(), "test")
    assert all(a["duration"] == 80 for a in acts)


def test_medium_recommends_rate_limit_and_low_monitors(db):
    m = MitigationManager(db, 40)
    assert m.decide("Medium", attack_context(), "t")[0]["action"] == "rate_limit_recommended"
    assert m.decide("Low", attack_context(), "t")[0]["action"] == "monitor"
    assert m.get_active() == []


def test_protected_addresses_are_never_quarantined(db):
    ctx = {"top_sources": [{"ip": "127.0.0.1", "packets": 9}, {"ip": "192.168.1.20", "packets": 8},
                           {"ip": "unknown", "packets": 7}]}
    acts = MitigationManager(db, 40).decide("Critical", ctx, "t")
    assert acts[0]["action"] == "rate_limit_recommended"


def test_duplicate_quarantine_is_ignored_while_active(db):
    m = MitigationManager(db, 40)
    assert m.quarantine("10.0.0.9", "r") is True
    assert m.quarantine("10.0.0.9", "r") is False
    assert len(db.get_mitigations()) == 1


def test_quarantine_expires_and_history_marked_recovered(db, monkeypatch):
    m = MitigationManager(db, 40)
    m.quarantine("10.0.0.9", "r", 40)
    real = time.time()
    monkeypatch.setattr("security.mitigation.time.time", lambda: real + 41)
    assert m.get_active() == []
    assert db.get_mitigations()[0]["status"] == "recovered"


def test_remaining_seconds_counts_down(db):
    m = MitigationManager(db, 40)
    m.quarantine("10.0.0.9", "r", 40)
    assert 36 <= m.get_active()[0]["remaining_seconds"] <= 40


def test_set_duration_has_floor_of_five_seconds(db):
    m = MitigationManager(db, 40)
    m.set_duration(1)
    assert m.quarantine_seconds == 5


def test_os_firewall_integration_is_disabled(db):
    r = MitigationManager(db, 40).apply_os_firewall_block("1.2.3.4")
    assert r["applied"] is False


# ---- simulator ----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("is_attack", [False, True])
def test_simulator_packet_lengths_within_ethernet_bounds(is_attack):
    sim = TrafficSimulator(seed=3)
    for _ in range(20):
        packets = sim._make_window(is_attack)
        assert packets and all(40 <= p["length"] <= 1500 for p in packets)


def test_simulator_attack_windows_are_larger_than_benign_on_average():
    sim = TrafficSimulator(seed=5)
    benign = sum(len(sim._make_window(False)) for _ in range(30)) / 30
    attack = sum(len(sim._make_window(True)) for _ in range(30)) / 30
    assert attack > 2 * benign


def test_simulator_runs_calls_back_and_stops():
    got = []
    sim = TrafficSimulator(on_window=lambda f, c, s, i: got.append((s, i)))
    sim.start(window_seconds=2)
    deadline = time.time() + 5
    while not got and time.time() < deadline:
        time.sleep(0.1)
    with pytest.raises(RuntimeError):
        sim.start()
    sim.stop()
    assert got and got[0] == ("simulation", "simulation") and sim.running is False
