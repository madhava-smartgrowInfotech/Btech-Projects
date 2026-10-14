"""
End-to-end smoke test of the HTTP API the React frontend uses (no camera, no browser needed).

    venv\\Scripts\\python scripts\\smoke_test.py

Runs in-process against a throw-away SQLite database and the real MediaPipe + InsightFace models,
using the sample photo bundled with InsightFace (same approach as scripts/demo_pipeline.py):
faculty + students register, a session is created, a student completes the full 6-step check-in,
and the proxy checks (outside fence, failed challenge, duplicate face, closed session) are exercised,
followed by every faculty screen's endpoint (records, log, export, dashboard, students).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_db = Path(tempfile.gettempdir()) / "am_smoke_test.db"
if _db.exists():
    _db.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ.setdefault("AM_REQUIRE_ENROLLMENT", "true")
os.environ["AM_ALLOW_MANUAL_LOCATION"] = "true"

import cv2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import config  # noqa: E402
from core import face_match, liveness  # noqa: E402
from backend import api as api_module  # noqa: E402

CENTRE = (17.3850, 78.4867)
INSIDE = (17.38505, 78.48675)   # ~7 m from centre
OUTSIDE = (17.3900, 78.4867)    # ~550 m away
FAILS = 0


def check(name: str, cond: bool, detail: object = "") -> None:
    global FAILS
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  ->  {detail}" if detail != "" and not cond else ""))
    if not cond:
        FAILS += 1


def jpg(img) -> bytes:
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def face_crops() -> list:
    from insightface.data import get_image

    img = get_image("t1")
    crops = []
    for f in sorted(face_match.get_embedder().faces(img), key=lambda f: f.bbox[0]):
        x1, y1, x2, y2 = f.bbox.astype(int)
        m = int(0.6 * max(x2 - x1, y2 - y1))
        crops.append(img[max(0, y1 - m): y2 + m, max(0, x1 - m): x2 + m].copy())
    usable = [c for c in crops if liveness.check_neutral(liveness.analyze(c)) is None]
    if len(usable) < 2:  # relax for the sample photo, as demo_pipeline.py does
        config.NEUTRAL_MAX_YAW = 0.2
        usable = [c for c in crops if liveness.check_neutral(liveness.analyze(c)) is None]
    return usable


def tilted(img, challenge: str):
    """Synthetic TILT frame (as in demo_pipeline.make_challenge_frame)."""
    h, w = img.shape[:2]
    angle = {"TILT_LEFT": -20, "TILT_RIGHT": 20}.get(challenge, 0)
    if config.CAMERA_MIRRORED:
        angle = -angle
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


class Client:
    """One browser: fixed device id, optional bearer token."""

    def __init__(self, tc: TestClient, device: str):
        self.tc, self.device, self.token = tc, device, None

    def _h(self) -> dict:
        h = {"X-Device-Id": self.device}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get(self, path, **kw):
        return self.tc.get(path, headers=self._h(), **kw)

    def post(self, path, **kw):
        return self.tc.post(path, headers=self._h(), **kw)

    def login(self, username, password, role=None):
        r = self.post("/api/auth/login", json={"username": username, "password": password, "role": role})
        if r.status_code == 200:
            self.token = r.json()["token"]
        return r


def checkin(c: Client, token: str, face_img, lat_lon=INSIDE) -> dict:
    """Run the student wizard exactly as the React screen does. Returns the final response."""
    st = c.get(f"/api/checkin/{token}/state").json()
    if st["step"] == 1:
        r = c.post(f"/api/checkin/{token}/start").json()
        if not r["ok"]:
            return {"stage": "eligibility", **r}
        st = r["state"]
    if st["step"] == 2:
        r = c.post(f"/api/checkin/{token}/location", json={"lat": lat_lon[0], "lon": lat_lon[1], "accuracy": 12}).json()
        if not r["inside"]:
            return {"stage": "location", **r}
        st = r["state"]
    ch = st["challenge"]
    files = {"neutral": ("n.jpg", jpg(face_img), "image/jpeg"), "challenge": ("c.jpg", jpg(tilted(face_img, ch)), "image/jpeg")}
    r = c.post(f"/api/checkin/{token}/liveness", files=files).json()
    if not r["passed"]:
        return {"stage": "liveness", **r}
    r = c.post(f"/api/checkin/{token}/face").json()
    return {"stage": "face" if not r["passed"] else "success", **r}


def main() -> int:
    print("Loading models and sample faces…")
    # The challenge is random on the server; pin it to a tilt so a still photo can be rotated to pass.
    liveness.random_challenge = lambda rng=None: "TILT_LEFT"  # type: ignore[assignment]
    person_a, person_b = face_crops()[:2]

    with TestClient(api_module.app) as tc:
        anon = Client(tc, "smoke-anon")
        fac = Client(tc, "smoke-faculty")
        stu_a, stu_b, stu_c = Client(tc, "smoke-a"), Client(tc, "smoke-b"), Client(tc, "smoke-c")

        print("\nMeta")
        check("GET /api/health", anon.get("/api/health").json()["status"] == "ok")
        cfg = anon.get("/api/config").json()
        check("GET /api/config lists 8 challenges", len(cfg["challenges"]) == 8)
        check("GET /api/models", "landmarks" in anon.get("/api/models").json())
        check("GET /api/qr returns PNG", anon.get("/api/qr", params={"text": "x"}).content[:4] == b"\x89PNG")

        print("\nRegistration & sign-in")
        r = anon.post("/api/auth/register", data={"role": "faculty", "full_name": "Smoke Guide", "username": "guide@smoke", "password": "faculty123"})
        check("register faculty", r.status_code == 200, r.text)
        r = anon.post("/api/auth/register", data={"role": "student", "full_name": "No Face", "roll_number": "23K91A6799", "password": "student123"})
        check("student without face is rejected", r.status_code == 400 and "reference face" in r.json()["detail"], r.text)
        for roll, name, img in [("23K91A6706", "A. Greeshma", person_a), ("23K91A6740", "B. Vinay", person_b), ("23K91A6757", "G. Sriram", person_a)]:
            r = anon.post("/api/auth/register", data={"role": "student", "full_name": name, "roll_number": roll, "password": "student123"},
                          files={"face": ("f.jpg", jpg(img), "image/jpeg")})
            check(f"register student {roll} with face", r.status_code == 200 and r.json()["user"]["enrolled"], r.text)
        check("wrong-portal login blocked", fac.login("guide@smoke", "faculty123", "student").status_code == 403)
        check("bad password rejected", fac.login("guide@smoke", "nope", "faculty").status_code == 401)
        check("faculty login", fac.login("guide@smoke", "faculty123", "faculty").status_code == 200)
        check("/me with device-bound JWT", fac.get("/api/auth/me").status_code == 200)
        stolen = Client(tc, "other-device")
        stolen.token = fac.token
        check("JWT rejected from another device", stolen.get("/api/auth/me").status_code == 401)

        print("\nSession")
        r = fac.post("/api/sessions", json={"course_code": "cs601", "course_name": "Machine Learning", "section": "CSDS-A",
                                            "start_local": cfg["now_local"], "duration_min": 60, "latitude": CENTRE[0],
                                            "longitude": CENTRE[1], "radius_m": 60, "allowed_rolls": "23K91A67*"})
        check("create session", r.status_code == 200 and r.json()["status"] == "live", r.text)
        s = r.json()
        token, sid = s["token"], s["id"]
        check("public session by token", anon.get(f"/api/public/sessions/{token}").json()["course_code"] == "CS601")
        check("invalid token is 404", anon.get("/api/public/sessions/nope").status_code == 404)
        check("faculty cannot check in", fac.post(f"/api/checkin/{token}/start").status_code == 403)

        print("\nStudent A — full check-in")
        stu_a.login("23K91A6706", "student123", "student")
        r = stu_a.post(f"/api/checkin/{token}/start").json()
        check("eligibility passes", r["ok"], r)
        r = stu_a.post(f"/api/checkin/{token}/location", json={"lat": OUTSIDE[0], "lon": OUTSIDE[1], "accuracy": 10}).json()
        check("outside geo-fence is blocked", not r["inside"] and "Outside geo-fence" in r["reason"], r)
        r = stu_a.post(f"/api/checkin/{token}/location", json={"lat": INSIDE[0], "lon": INSIDE[1], "accuracy": 10}).json()
        check("inside geo-fence passes", r["inside"] and r["state"]["step"] == 3, r)
        r = stu_a.post(f"/api/checkin/{token}/neutral", files={"image": ("n.jpg", jpg(person_a), "image/jpeg")}).json()
        check("neutral frame accepted", r["ok"], r)
        r = stu_a.post(f"/api/checkin/{token}/liveness", files={"neutral": ("n.jpg", jpg(person_a), "image/jpeg"),
                                                                 "challenge": ("c.jpg", jpg(person_a), "image/jpeg")}).json()
        check("static photo fails the challenge", not r["passed"] and r["state"]["tries_left"] == 2, r)
        res = checkin(stu_a, token, person_a)
        check("tilted frame passes liveness and face match", res["stage"] == "success", res)
        result = res.get("state", {}).get("result", {})
        check("result has identity similarity", (result.get("identity_similarity") or 0) >= config.IDENTITY_THRESHOLD, result)
        stu_a.post(f"/api/checkin/{token}/reset")
        r = stu_a.post(f"/api/checkin/{token}/start").json()
        check("second attempt: already marked", not r["ok"] and "already marked" in r["reason"], r)

        print("\nProxy attempts")
        stu_c.login("23K91A6757", "student123", "student")
        res = checkin(stu_c, token, person_a)
        check("same face under another roll is blocked (duplicate)", res["stage"] == "face" and "already" in res["reason"].lower(), res)
        stu_b.login("23K91A6740", "student123", "student")
        res = checkin(stu_b, token, person_a)
        check("someone else's face for B is blocked (identity)", res["stage"] == "face" and "does not match" in res["reason"], res)

        print("\nFaculty screens")
        lst = fac.get("/api/sessions").json()
        check("sessions list", len(lst) == 1 and lst[0]["present"] == 1, lst)
        d = fac.get(f"/api/sessions/{sid}").json()
        check("session detail: 1 present, blocked logged", d["metrics"]["present"] == 1 and d["metrics"]["blocked"] >= 3, d["metrics"])
        check("records rows", d["rows"][0]["Roll Number"] == "23K91A6706", d["rows"])
        check("verification log", len(d["attempts"]) >= 8)
        x = fac.get(f"/api/sessions/{sid}/export")
        check("Excel export", x.status_code == 200 and x.content[:2] == b"PK" and "attachment" in x.headers["content-disposition"])
        dash = fac.get("/api/dashboard").json()
        check("dashboard totals", dash["totals"]["present"] == 1 and dash["stages"], dash["totals"])
        studs = fac.get("/api/students").json()
        check("students list", len(studs) == 3 and all(u["enrolled"] for u in studs))
        b = next(u for u in studs if u["roll_number"] == "23K91A6740")
        check("reset devices", fac.post(f"/api/students/{b['id']}/reset-devices").json()["removed"] == 1)
        r = fac.post(f"/api/students/{b['id']}/enroll", files={"face": ("f.jpg", jpg(person_b), "image/jpeg")})
        check("re-enrol face", r.status_code == 200, r.text)
        check("student cannot use faculty API", stu_b.get("/api/students").status_code == 403)
        check("close session", fac.post(f"/api/sessions/{sid}/close").json()["status"] == "closed")
        stu_b.post(f"/api/checkin/{token}/reset")
        r = stu_b.post(f"/api/checkin/{token}/start").json()
        check("closed session refuses check-in", not r["ok"] and "closed" in r["reason"], r)
        st = anon.get("/api/stats").json()
        check("stats", st["records"] == 1 and st["blocked"] >= 4, st)

    print(f"\n{'ALL CHECKS PASSED' if not FAILS else f'{FAILS} CHECK(S) FAILED'}")
    try:
        _db.unlink()
    except OSError:
        pass
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
