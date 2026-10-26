"""Unit tests for the simulator, controllers, predictor and vision rules (no mocks)."""
import time

import numpy as np
import pytest

from smart_traffic import vision as V
from smart_traffic.predictor import QueuePredictor
from smart_traffic.sim import APPROACHES, CAP, CONTROLLERS, FIXED_GREEN, PCU, Sim, demand_profile


@pytest.fixture(scope="module")
def predictor():
    return QueuePredictor().fit()


def delay(ctrl, seed=40, secs=900, **kw):
    return Sim(2, 2, ctrl, 1.2, seed=seed, **kw).run(secs).summary()


# ------------------------------------------------------------------ simulator
def test_four_controllers_registered():
    assert set(CONTROLLERS) == {"fixed", "adaptive", "emergency", "advanced"}


def test_same_seed_is_deterministic():
    assert delay("adaptive") == delay("adaptive")


def test_different_seed_changes_traffic():
    assert delay("adaptive", seed=1)["Throughput (veh)"] != delay("adaptive", seed=2)["Throughput (veh)"] or \
        delay("adaptive", seed=1)["Avg queue (veh)"] != delay("adaptive", seed=2)["Avg queue (veh)"]


def test_demand_is_controller_independent():
    """Controllers must face identical emergencies, otherwise the benchmark is not like-for-like."""
    spawned = {c: Sim(2, 2, c, 1.2, seed=41).run(1200).spawned for c in CONTROLLERS}
    assert len(set(spawned.values())) == 1 and spawned["fixed"] > 0


def test_demand_profile_peaks_in_rush_hour():
    assert demand_profile(8.5) > demand_profile(13) < demand_profile(17.5)
    assert demand_profile(3) < 0.8


def test_phase_is_always_one_of_two_and_fixed_cycle_respected():
    s = Sim(2, 2, "fixed", 1.0, seed=3, emergencies=False)
    s.run(400)
    log = np.array(s.phases_log)[:, 0]
    assert set(log) <= {0, 1}
    changes = np.flatnonzero(np.diff(log)) + 1
    assert len(changes) >= 6
    gaps = np.diff(changes)
    assert gaps.min() >= FIXED_GREEN  # a green is never shorter than the fixed split


def test_spillback_limit_on_internal_links():
    s = Sim(3, 3, "fixed", 1.8, seed=5, emergencies=False).run(1500)
    internal = [(j, a) for j in range(s.n) for a in range(4) if (j, a) not in set(s.entries)]
    peak = max(s.qhist[t][j, a] for t in range(len(s.qhist)) for j, a in internal)
    assert peak <= CAP + 8  # in-flight vehicles may land after the check, so a small margin


def test_vehicle_weights():
    assert PCU["bus"] == 3.0 and PCU["bike"] == 0.5 and PCU["car"] == 1.0


def test_violations_off_means_none():
    s = Sim(2, 2, "fixed", 1.6, seed=7, violations=False).run(900)
    assert s.viol_log == []


def test_violation_log_fields():
    s = Sim(2, 2, "fixed", 1.6, seed=7).run(1800)
    assert s.viol_log, "red-light runners are 5 % of cars: some must be logged"
    v = s.viol_log[0]
    assert {"t", "junction", "approach", "kind", "plate", "vehicle", "confidence"} <= set(v)
    assert v["kind"] in ("Red-light jumping", "Wrong-way driving") and 0.86 <= v["confidence"] <= 0.99


def test_emergency_vehicles_served_faster_than_fixed():
    f = [delay("fixed", seed=s, secs=1800)["Emergency delay (s)"] for s in (40, 41, 42)]
    e = [delay("emergency", seed=s, secs=1800)["Emergency delay (s)"] for s in (40, 41, 42)]
    assert np.mean(e) < 0.5 * np.mean(f)


def test_emergency_vehicle_not_ignored_by_emergency_controller():
    s = Sim(2, 2, "emergency", 1.0, seed=9, emergencies=False)
    s.run(30)
    j, a = s.entries[0]
    v = s._new_vehicle(emg=True)
    s.q[j][a].append(v)
    s.active_emg[v.id] = v
    s.spawned += 1
    s.run(120)
    assert s.emg_log and s.preemptions >= 1


def test_summary_keys_and_fuel_relation():
    m = delay("fixed")
    assert m["CO2 (kg)"] == pytest.approx(m["Fuel wasted idling (L)"] * 2.31)
    assert m["Throughput (veh)"] > 0


def test_feature_matrix_shape():
    s = Sim(2, 2, "adaptive", 1.0, seed=1).run(60)
    assert s.feature_matrix().shape == (s.n * 4, len(Sim.FEATURES)) == (16, 11)


def test_advanced_cuts_delay_vs_fixed_on_three_seeds(predictor):
    f = [Sim(2, 2, "fixed", 1.2, seed=s).run(1200).summary()["Avg delay / vehicle (s)"] for s in (40, 41, 42)]
    a = [Sim(2, 2, "advanced", 1.2, seed=s, predictor=predictor).run(1200).summary()["Avg delay / vehicle (s)"] for s in (40, 41, 42)]
    assert np.mean(a) < np.mean(f)


# ------------------------------------------------------------------ predictor
def test_predictor_beats_persistence(predictor):
    assert predictor.metrics["Gradient Boosting (used)"][0] < predictor.metrics["Persistence baseline"][0]
    assert predictor.n_samples > 20000
    assert set(predictor.importance) == set(Sim.FEATURES)


def test_predictor_output_clipped(predictor):
    X = np.full((4, len(Sim.FEATURES)), 1e4)
    out = predictor.predict(X)
    assert out.min() >= 0 and out.max() <= 40


# --------------------------------------------------------------------- vision
def test_synthetic_scene_ambulance_flagged_by_lightbar():
    img, truth = V.render_scene(9, True, 0, 3)
    dets, bars = V.detect_classical(img)
    assert bars and any(d["cls"] == "ambulance" for d in dets)
    assert V.density_report(dets)["emergency"] and V.density_report(dets)["green"] == 12


def test_synthetic_scene_without_ambulance_is_not_flagged():
    img, _ = V.render_scene(9, False, 1, 3)
    dets, _ = V.detect_classical(img)
    assert not any(d["cls"] == "ambulance" for d in dets)


def test_blank_frame_has_no_detections():
    dets, bars = V.detect_classical(np.full((420, 640, 3), 70, np.uint8))
    assert dets == [] and bars == []


def test_density_levels_and_green_time():
    def rep(n_cars):
        return V.density_report([dict(cls="car", conf=.9, box=(0, 0, 1, 1), lightbar=0)] * n_cars)
    assert rep(2)["level"] == "LOW" and rep(7)["level"] == "MEDIUM" and rep(11)["level"] == "HIGH" and rep(20)["level"] == "JAMMED"
    assert 15 <= rep(2)["green"] <= 60 and rep(40)["green"] == 60  # clamped to the 60 s ceiling


def test_lightbar_needs_red_and_blue_touching():
    img = np.full((200, 300, 3), 40, np.uint8)
    img[50:60, 100:120] = (0, 0, 255)           # red patch only
    assert V.detect_lightbars(img) == []
    img[50:60, 120:140] = (255, 60, 0)          # blue patch next to it
    assert len(V.detect_lightbars(img)) == 1


def test_annotate_does_not_modify_input():
    img, _ = V.render_scene(6, True, 0, 1)
    before = img.copy()
    dets, bars = V.detect_classical(img)
    V.annotate(img, dets, bars)
    assert np.array_equal(img, before)


def test_yolo_sample_photo_finds_the_bus():
    if not V.yolo_available() or V.sample_image_path() is None:
        pytest.skip("ultralytics or the sample photo is not available")
    import cv2
    t = time.time()
    dets, _ = V.detect_yolo(cv2.imread(V.sample_image_path()), 0.3)
    assert any(d["cls"] == "bus" for d in dets)
    assert time.time() - t < 60
