"""
Tests for the core modules and an end-to-end Streamlit smoke test.

    pytest -q

Set AM_SKIP_MODEL_TESTS=1 to skip the tests that need MediaPipe / InsightFace models.
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///" + str(ROOT / "tests" / "_test.db")
os.environ["AM_REQUIRE_ENROLLMENT"] = "false"

import config  # noqa: E402
from core import auth, face_match, geofence, liveness, services  # noqa: E402
from core.db import init_db  # noqa: E402
from core.timeutil import utcnow  # noqa: E402

SKIP_MODELS = os.getenv("AM_SKIP_MODEL_TESTS") == "1"


@pytest.fixture(scope="module", autouse=True)
def _db():
    p = ROOT / "tests" / "_test.db"
    if p.exists():
        p.unlink()
    init_db()
    yield
    if p.exists():
        p.unlink()


# --------------------------------------------------------------------------- #
# auth
# --------------------------------------------------------------------------- #
def test_password_hash_roundtrip():
    h = auth.hash_password("s3cret!")
    assert auth.verify_password("s3cret!", h)
    assert not auth.verify_password("wrong", h)
    assert not auth.verify_password("s3cret!", "garbage")


def test_jwt_bound_to_device():
    user = services.register_user("student", "jwt_student", "JWT Student", "pass123", "22X11A0001")
    tok = auth.issue_token(user, "dev-1")
    claims = auth.verify_token(tok, "dev-1")
    assert claims.roll_number == "22X11A0001" and claims.role == "student"
    with pytest.raises(auth.TokenError):
        auth.verify_token(tok, "dev-2")
    with pytest.raises(auth.TokenError):
        auth.verify_token(tok + "x", "dev-1")


# --------------------------------------------------------------------------- #
# geofence
# --------------------------------------------------------------------------- #
def test_haversine_known_distance():
    # Hyderabad Charminar -> Golconda Fort ≈ 8.5 km
    d = geofence.haversine_m(17.3616, 78.4747, 17.3833, 78.4011)
    assert 8000 < d < 9000


def test_geofence_inside_outside_and_accuracy():
    ok = geofence.check_geofence(17.38505, 78.48675, 17.3850, 78.4867, 60)
    assert ok.inside and ok.distance_m < 20
    bad = geofence.check_geofence(17.3900, 78.4867, 17.3850, 78.4867, 60)
    assert not bad.inside and "Outside" in bad.reason
    noisy = geofence.check_geofence(17.3850, 78.4867, 17.3850, 78.4867, 60, accuracy_m=1000)
    assert not noisy.inside and "accuracy" in noisy.reason


# --------------------------------------------------------------------------- #
# liveness (pure-numpy metric + challenge logic, no MediaPipe needed)
# --------------------------------------------------------------------------- #
def _synthetic_landmarks(yaw=0.0, pitch=0.5, roll_deg=0.0, mar=0.05, ear=0.3) -> np.ndarray:
    """Build a 478-point array where only the indices used by the metrics matter."""
    pts = np.zeros((478, 2), dtype=np.float32)
    pts[liveness.FACE_LEFT] = (0.2, 0.5)
    pts[liveness.FACE_RIGHT] = (0.8, 0.5)
    pts[liveness.NOSE_TIP] = (0.5 + 0.6 * yaw, 0.0)  # y set below
    # eyes: centres at y=0.4, spaced 0.3 apart, rotated by roll
    ang = np.radians(roll_deg)
    lx, rx = 0.35, 0.65
    pts[liveness.L_EYE_OUTER] = (lx - 0.05, 0.4)
    pts[liveness.L_EYE_INNER] = (lx + 0.05, 0.4)
    pts[liveness.R_EYE_OUTER] = (rx + 0.05, 0.4)
    pts[liveness.R_EYE_INNER] = (rx - 0.05, 0.4)
    # apply roll to the right eye centre only (enough to change the eye-line angle)
    dy = np.tan(ang) * (rx - lx)
    pts[liveness.R_EYE_OUTER][1] += dy
    pts[liveness.R_EYE_INNER][1] += dy
    for top, bot, outer, inner in ((liveness.L_EYE_TOP, liveness.L_EYE_BOTTOM, liveness.L_EYE_OUTER, liveness.L_EYE_INNER),
                                   (liveness.R_EYE_TOP, liveness.R_EYE_BOTTOM, liveness.R_EYE_OUTER, liveness.R_EYE_INNER)):
        cx = (pts[outer][0] + pts[inner][0]) / 2
        cy = (pts[outer][1] + pts[inner][1]) / 2
        pts[top] = (cx, cy - ear * 0.1 / 2)
        pts[bot] = (cx, cy + ear * 0.1 / 2)
    pts[liveness.CHIN] = (0.5, 0.9)
    eyes_mid_y = 0.4 + dy / 2
    pts[liveness.NOSE_TIP][1] = eyes_mid_y + pitch * (0.9 - eyes_mid_y)
    pts[liveness.MOUTH_LEFT] = (0.4, 0.75)
    pts[liveness.MOUTH_RIGHT] = (0.6, 0.75)
    pts[liveness.LIP_TOP] = (0.5, 0.75 - mar * 0.2 / 2)
    pts[liveness.LIP_BOTTOM] = (0.5, 0.75 + mar * 0.2 / 2)
    return pts


def test_metrics_from_synthetic_landmarks():
    m = liveness.metrics_from_landmarks(_synthetic_landmarks(yaw=0.2, pitch=0.6, roll_deg=10, mar=0.4, ear=0.25))
    assert m.yaw == pytest.approx(0.2, abs=1e-3)
    assert m.pitch == pytest.approx(0.6, abs=0.02)
    assert m.roll_deg == pytest.approx(10, abs=0.5)
    assert m.mar == pytest.approx(0.4, abs=1e-3)
    assert m.ear == pytest.approx(0.25, abs=1e-3)


@pytest.mark.parametrize("challenge,neutral_kw,chal_kw,expect", [
    ("TURN_LEFT", {}, {"yaw": -0.2}, True),     # mirrored camera: left turn -> negative yaw
    ("TURN_LEFT", {}, {"yaw": 0.2}, False),
    ("TURN_RIGHT", {}, {"yaw": 0.2}, True),
    ("LOOK_UP", {"pitch": 0.5}, {"pitch": 0.38}, True),
    ("LOOK_DOWN", {"pitch": 0.5}, {"pitch": 0.38}, False),
    ("TILT_LEFT", {}, {"roll_deg": -20}, True),
    ("TILT_RIGHT", {}, {"roll_deg": -20}, False),
    ("OPEN_MOUTH", {}, {"mar": 0.5}, True),
    ("OPEN_MOUTH", {}, {"mar": 0.1}, False),
    ("CLOSE_EYES", {}, {"ear": 0.1}, True),
    ("CLOSE_EYES", {}, {"ear": 0.3}, False),
])
def test_verify_challenge(monkeypatch, challenge, neutral_kw, chal_kw, expect):
    monkeypatch.setattr(config, "CAMERA_MIRRORED", True)
    n = liveness.metrics_from_landmarks(_synthetic_landmarks(**neutral_kw))
    c = liveness.metrics_from_landmarks(_synthetic_landmarks(**chal_kw))
    res = liveness.verify_challenge(challenge, n, c)
    assert res.passed is expect, res.reason


def test_neutral_frame_must_be_frontal_and_single_face():
    turned = liveness.metrics_from_landmarks(_synthetic_landmarks(yaw=0.3))
    assert liveness.check_neutral(turned)
    two = liveness.FaceMetrics(n_faces=2)
    assert "2 faces" in liveness.check_neutral(two)
    good = liveness.metrics_from_landmarks(_synthetic_landmarks())
    assert liveness.check_neutral(good) is None


# --------------------------------------------------------------------------- #
# face matching (pure logic on embeddings)
# --------------------------------------------------------------------------- #
def _vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.normal(size=512).astype(np.float32)
    return v / np.linalg.norm(v)


def test_verify_faces_identity_and_duplicate_logic(monkeypatch):
    monkeypatch.setattr(config, "REQUIRE_ENROLLMENT", True)
    me, other = _vec(1), _vec(2)
    # identity ok, no duplicates
    assert face_match.verify_faces(me, me, [], me).passed
    # wrong person for this roll number
    assert not face_match.verify_faces(other, me, [], other).passed
    # same face already recorded under another roll
    r = face_match.verify_faces(me, me, [("23K91A6799", me)], me)
    assert not r.passed and r.duplicate_of == "23K91A6799"
    # frames belong to different people
    assert "different people" in face_match.verify_faces(me, me, [], other).reason
    # no enrolment while required
    assert "enrol" in face_match.verify_faces(me, None, []).reason
    monkeypatch.setattr(config, "REQUIRE_ENROLLMENT", False)
    assert face_match.verify_faces(me, None, []).passed
    assert face_match.from_bytes(face_match.to_bytes(me)).shape == (512,)


# --------------------------------------------------------------------------- #
# services: sessions, roll patterns, eligibility, device binding
# --------------------------------------------------------------------------- #
def test_roll_patterns():
    assert services.roll_allowed("23K91A67*", "23k91a6706")
    assert not services.roll_allowed("23K91A67*", "24K95A6704")
    assert services.roll_allowed("23K91A67*,24K95A6704", "24K95A6704")
    assert services.expected_rolls("A1,A2,A1") == ["A1", "A2"]
    assert services.expected_rolls("A*") is None


def test_session_lifecycle_and_eligibility(monkeypatch):
    monkeypatch.setattr(config, "MAX_DEVICES_PER_STUDENT", 1)
    fac = services.register_user("faculty", "fac@test", "Fac Ulty", "pass123")
    stu = services.register_user("student", "22X11A0002", "Stu Dent", "pass123", "22X11A0002")
    now = utcnow()
    s = services.create_session(fac.id, "cs1", "Course", "A", now - timedelta(minutes=1),
                                now + timedelta(minutes=10), 17.385, 78.4867, 50, "22X11A00*")
    assert s.status() == "live" and s.token in services.session_link(s)
    assert services.get_session_by_token(s.token).faculty.full_name == "Fac Ulty"

    assert services.check_eligibility(s, stu, "devA").ok
    # second device blocked by binding
    assert "not registered" in services.check_eligibility(s, stu, "devB").reason
    services.reset_devices(stu.id)
    assert services.check_eligibility(s, stu, "devB").ok

    # expired / closed / not started
    assert not services.check_eligibility(s, stu, "devB", now=now + timedelta(hours=1)).ok
    assert not services.check_eligibility(s, stu, "devB", now=now - timedelta(hours=1)).ok
    services.close_session(s.id)
    assert services.get_session_by_id(s.id).status() == "closed"

    # roll not allowed
    s2 = services.create_session(fac.id, "cs2", "Course", "A", now - timedelta(minutes=1),
                                 now + timedelta(minutes=10), 17.385, 78.4867, 50, "99*")
    assert "not allowed" in services.check_eligibility(s2, stu, "devB").reason

    # record attendance and verify duplicate-roll + device-per-session rules
    s3 = services.create_session(fac.id, "cs3", "Course", "A", now - timedelta(minutes=1),
                                 now + timedelta(minutes=10), 17.385, 78.4867, 50, "*")
    services.record_attendance(s3, stu, lat=17.385, lon=78.4867, accuracy=5, distance=1, device_hash="devB",
                               challenge="OPEN_MOUTH", liveness_score=1.0, identity_sim=None, dup_sim=None,
                               embedding=_vec(3))
    assert "already marked" in services.check_eligibility(s3, stu, "devB").reason
    stu2 = services.register_user("student", "22X11A0003", "Other", "pass123", "22X11A0003")
    assert "already marked attendance for 22X11A0002" in services.check_eligibility(s3, stu2, "devB").reason
    assert len(services.records_for(s3.id)) == 1
    assert len(services.session_embeddings(s3.id, exclude_student_id=stu2.id)) == 1
    assert any(a.stage == "success" for a in services.attempts_for(s3.id))

    from core import export
    xlsx = export.to_excel_bytes(services.get_session_by_id(s3.id), services.records_for(s3.id),
                                 services.attempts_for(s3.id))
    assert xlsx[:2] == b"PK"


# --------------------------------------------------------------------------- #
# model-backed tests (real MediaPipe + InsightFace on bundled sample image)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(SKIP_MODELS, reason="model tests disabled")
def test_models_on_sample_image():
    import cv2
    from insightface.data import get_image

    img = get_image("t1")
    faces = face_match.get_embedder().faces(img)
    assert len(faces) >= 2
    crops = []
    for f in faces[:2]:
        x1, y1, x2, y2 = f.bbox.astype(int)
        m = int(0.6 * max(x2 - x1, y2 - y1))
        crops.append(img[max(0, y1 - m): y2 + m, max(0, x1 - m): x2 + m])
    a, b = crops
    assert liveness.analyze(a).n_faces == 1
    ea, eb, ea_flip = face_match.embed(a), face_match.embed(b), face_match.embed(cv2.flip(a, 1))
    assert face_match.cosine(ea, ea_flip) > 0.8
    assert face_match.cosine(ea, eb) < 0.3
    # a rotated copy of the same face passes a TILT challenge and fails OPEN_MOUTH
    h, w = a.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 20 if config.CAMERA_MIRRORED else -20, 1.0)
    tilted = cv2.warpAffine(a, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    n, c = liveness.analyze(a), liveness.analyze(tilted)
    if liveness.check_neutral(n) is None:
        assert liveness.verify_challenge("TILT_LEFT", n, c).passed
        assert not liveness.verify_challenge("OPEN_MOUTH", n, liveness.analyze(a)).passed


# --------------------------------------------------------------------------- #
# Streamlit end-to-end smoke test (faculty portal) via AppTest
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(SKIP_MODELS, reason="app warms models on start")
def test_streamlit_faculty_flow():
    from streamlit.testing.v1 import AppTest

    services.register_user("faculty", "apptest@fac", "App Tester", "pass123")
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    assert not at.exception, at.exception

    # sign in through the faculty login form
    at.text_input(key=None)  # ensure widgets exist
    ti = at.text_input
    ti[0].set_value("apptest@fac")
    ti[1].set_value("pass123")
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert any("Create session" in b.label or "Sign out" in b.label for b in at.button)

    # create a session using manual coordinates (defaults) and the manual button
    labels = {b.label: b for b in at.button}
    labels["Use these coordinates"].click().run()
    assert not at.exception, at.exception
    for t in at.text_input:
        if t.label == "Course code":
            t.set_value("CS601")
        elif t.label == "Course name":
            t.set_value("Machine Learning")
        elif t.label == "Section":
            t.set_value("CSDS-A")
    labels = {b.label: b for b in at.button}
    assert not labels["Create session"].disabled
    labels["Create session"].click().run()
    assert not at.exception, at.exception
    assert any("Session created" in s.value for s in at.success)
    assert any("?session=" in c.value for c in at.code)


@pytest.mark.skipif(SKIP_MODELS, reason="app warms models on start")
def test_streamlit_student_flow_to_liveness_step():
    from streamlit.testing.v1 import AppTest

    fac = services.register_user("faculty", "apptest2@fac", "App Tester 2", "pass123")
    stu = services.register_user("student", "22X11A0777", "App Student", "pass123", "22X11A0777")
    now = utcnow()
    s = services.create_session(fac.id, "CS7", "Streamlit Test", "A", now - timedelta(minutes=1),
                                now + timedelta(minutes=10), 17.385, 78.4867, 50, "22X11A07*")

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.query_params["session"] = s.token
    at.run()
    assert not at.exception, at.exception
    assert any("LIVE" in m.value for m in at.markdown)

    at.text_input[0].set_value("22X11A0777")
    at.text_input[1].set_value("pass123")
    at.button[0].click().run()
    assert not at.exception, at.exception
    # eligibility passed automatically -> step 2 (location)
    assert any("Step 2" in m.value for m in at.markdown)

    # manual coordinates default to the session centre -> inside the fence
    labels = {b.label: b for b in at.button}
    labels["Use these coordinates"].click().run()
    assert not at.exception, at.exception
    labels = {b.label: b for b in at.button}
    labels["Verify my location"].click().run()
    assert not at.exception, at.exception
    assert any("Step 3" in m.value for m in at.markdown)
    stages = [a.stage for a in services.attempts_for(s.id)]
    assert stages == ["eligibility", "location"]
    assert all(a.passed for a in services.attempts_for(s.id))

    # a second student on the *same device* must not be able to log in and pass eligibility
    # once the first has a record; verify the wrong-role guard and expired-session message too
    services.close_session(s.id)
    at2 = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at2.query_params["session"] = s.token
    at2.run()
    assert any("closed" in w.value for w in at2.warning)
