"""
Latency measurements for the verification pipeline (CPU only).

  A. cold start: time to load MediaPipe Face Mesh and InsightFace buffalo_l
  B. per-stage latency on real face images (decode, landmarks, liveness maths, embedding, face matching)
  C. end-to-end HTTP latency of the 6-step check-in through the FastAPI app (in-process TestClient,
     real models, throw-away SQLite database)
  D. duplicate-face scan time versus the number of faces already recorded in the session

Per-stage images: face crops of the group photo bundled with InsightFace. HTTP test: LFW photos chosen by
docs_personas.py (no camera is attached).

    venv\\Scripts\\python scripts\\eval_latency.py [--lfw DIR] [--n 40]    ->  docs/evaluation/latency.json
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_db = Path(tempfile.gettempdir()) / "am_latency.db"
if _db.exists():
    _db.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["AM_REQUIRE_ENROLLMENT"] = "true"

import config  # noqa: E402
from core import face_match, liveness  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=40)
ap.add_argument("--personas", required=True, help="personas.json from docs_personas.py (LFW photos for the HTTP test)")
ap.add_argument("--persona", default="Arnold_Schwarzenegger")
args = ap.parse_args()
OUT = ROOT / "docs" / "evaluation"
OUT.mkdir(parents=True, exist_ok=True)


def ms(fn, *a, **k):
    t = time.perf_counter()
    r = fn(*a, **k)
    return r, (time.perf_counter() - t) * 1000


def summ(xs):
    a = np.array(xs)
    return {"n": int(len(a)), "mean": float(a.mean()), "p50": float(np.percentile(a, 50)),
            "p95": float(np.percentile(a, 95)), "min": float(a.min()), "max": float(a.max())}


def jpg(img) -> bytes:
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def rotate(img, angle):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def sample_faces():
    from insightface.data import get_image
    img = get_image("t1")
    out = []
    for f in sorted(face_match.get_embedder().faces(img), key=lambda f: f.bbox[0]):
        x1, y1, x2, y2 = f.bbox.astype(int)
        m = int(0.6 * max(x2 - x1, y2 - y1))
        out.append(img[max(0, y1 - m): y2 + m, max(0, x1 - m): x2 + m].copy())
    return img, out


def main() -> None:
    res: dict = {"machine": {"cpu": "12th Gen Intel(R) Core(TM) i5-12500 (6 cores / 12 threads)", "ram_gb": 15.7,
                             "gpu_used": False, "os": platform.platform(), "python": platform.python_version()}}

    # ---- A. cold start --------------------------------------------------------- #
    _, t_mp = ms(liveness.get_detector)
    _, t_if = ms(face_match.get_embedder)
    res["A_cold_start_ms"] = {"mediapipe_face_mesh": t_mp, "insightface_buffalo_l": t_if}
    print("A", res["A_cold_start_ms"], flush=True)

    whole, crops = sample_faces()
    crops = [c for c in crops if liveness.analyze(c).ok][:4]
    sizes = [f"{c.shape[1]}x{c.shape[0]}" for c in crops]
    res["images"] = {"source": "InsightFace bundled sample photo (t1), face crops with 0.6 margin",
                     "crop_sizes_px": sizes, "full_photo_px": f"{whole.shape[1]}x{whole.shape[0]}"}

    # warm-up
    for c in crops:
        liveness.analyze(c)
        face_match.embed(c)

    # ---- B. per-stage ------------------------------------------------------------ #
    t = {k: [] for k in ("decode_1280px_jpeg", "mediapipe_landmarks", "verify_challenge_maths", "insightface_embed",
                         "verify_faces", "pipeline_ai_total_two_frames")}
    enc_full = jpg(whole)
    for i in range(args.n):
        c = crops[i % len(crops)]
        _, d = ms(liveness.decode_image, enc_full)
        t["decode_1280px_jpeg"].append(d)
        m, a = ms(liveness.analyze, c)
        t["mediapipe_landmarks"].append(a)
        _, v = ms(liveness.verify_challenge, "TILT_LEFT", m, m)
        t["verify_challenge_maths"].append(v)
        e, b = ms(face_match.embed, c)
        t["insightface_embed"].append(b)
        _, f = ms(face_match.verify_faces, e, e, [("X", e)] * 30, e)
        t["verify_faces"].append(f)
        t0 = time.perf_counter()
        n1, n2 = c, rotate(c, 20)
        liveness.verify_challenge("TILT_LEFT", liveness.analyze(n1), liveness.analyze(n2))
        face_match.embed(n1)
        face_match.embed(n2)
        t["pipeline_ai_total_two_frames"].append((time.perf_counter() - t0) * 1000)
    res["B_stage_ms"] = {k: summ(v) for k, v in t.items()}
    print("B", {k: round(v["p50"], 1) for k, v in res["B_stage_ms"].items()}, flush=True)

    # ---- D. duplicate scan scaling --------------------------------------------------- #
    rng = np.random.default_rng(1)
    e0 = face_match.embed(crops[0])
    scale = {}
    for n in (10, 50, 100, 500, 1000, 5000):
        recs = [(f"R{i}", (lambda v: v / np.linalg.norm(v))(rng.normal(size=512).astype(np.float32))) for i in range(n)]
        xs = []
        for _ in range(20):
            _, d = ms(face_match.verify_faces, e0, e0, recs, e0)
            xs.append(d)
        scale[str(n)] = summ(xs)
    res["D_duplicate_scan_ms"] = scale
    print("D", {k: round(v["p50"], 2) for k, v in scale.items()}, flush=True)

    # ---- C. end-to-end HTTP --------------------------------------------------------------- #
    from fastapi.testclient import TestClient
    from backend import api as api_module

    liveness.random_challenge = lambda rng=None: "TILT_LEFT"  # type: ignore[assignment]
    pj = {x["name"]: x for x in json.loads(Path(args.personas).read_text())}[args.persona]
    enroll_img, person = cv2.imread(pj["enroll"]), cv2.imread(pj["neutral"])
    CENTRE = (17.3850, 78.4867)
    INSIDE = (17.38505, 78.48675)
    chal_img = cv2.imread(pj["challenge"]["TILT_LEFT"])   # a real second photo of the same person

    class C:
        def __init__(self, tc, dev):
            self.tc, self.dev, self.tok = tc, dev, None

        def h(self):
            h = {"X-Device-Id": self.dev}
            if self.tok:
                h["Authorization"] = f"Bearer {self.tok}"
            return h

        def post(self, p, **k):
            t0 = time.perf_counter()
            r = self.tc.post(p, headers=self.h(), **k)
            return r, (time.perf_counter() - t0) * 1000

        def get(self, p, **k):
            t0 = time.perf_counter()
            r = self.tc.get(p, headers=self.h(), **k)
            return r, (time.perf_counter() - t0) * 1000

    e2e = {k: [] for k in ("login", "start_eligibility", "location", "liveness_two_photos", "face_match_and_record",
                           "checkin_total_after_login")}
    with TestClient(api_module.app) as tc:
        fac, stu = C(tc, "lat-fac"), C(tc, "lat-stu")
        fac.post("/api/auth/register", data={"role": "faculty", "full_name": "Lat Guide", "username": "g@lat", "password": "faculty123"})
        stu.post("/api/auth/register", data={"role": "student", "full_name": "Lat Student", "roll_number": "23K91A6706", "password": "student123"},
                 files={"face": ("f.jpg", jpg(enroll_img), "image/jpeg")})
        r, d = fac.post("/api/auth/login", json={"username": "g@lat", "password": "faculty123", "role": "faculty"})
        fac.tok = r.json()["token"]
        cfg = tc.get("/api/config").json()
        for i in range(args.n):
            r, d = stu.post("/api/auth/login", json={"username": "23K91A6706", "password": "student123", "role": "student"})
            stu.tok = r.json()["token"]
            e2e["login"].append(d)
            s = fac.post("/api/sessions", json={"course_code": f"L{i}", "course_name": "Latency", "section": "A",
                                                 "start_local": cfg["now_local"], "duration_min": 60, "latitude": CENTRE[0],
                                                 "longitude": CENTRE[1], "radius_m": 60, "allowed_rolls": "*"})[0].json()
            tok = s["token"]
            t_all = time.perf_counter()
            r, d = stu.post(f"/api/checkin/{tok}/start")
            e2e["start_eligibility"].append(d)
            assert r.json()["ok"], r.text
            r, d = stu.post(f"/api/checkin/{tok}/location", json={"lat": INSIDE[0], "lon": INSIDE[1], "accuracy": 10})
            e2e["location"].append(d)
            files = {"neutral": ("n.jpg", jpg(person), "image/jpeg"), "challenge": ("c.jpg", jpg(chal_img), "image/jpeg")}
            r, d = stu.post(f"/api/checkin/{tok}/liveness", files=files)
            e2e["liveness_two_photos"].append(d)
            assert r.json()["passed"], r.text
            r, d = stu.post(f"/api/checkin/{tok}/face")
            e2e["face_match_and_record"].append(d)
            assert r.json()["passed"], r.text
            e2e["checkin_total_after_login"].append((time.perf_counter() - t_all) * 1000)
            stu.post(f"/api/checkin/{tok}/reset")
    res["C_http_ms"] = {k: summ(v) for k, v in e2e.items()}
    res["C_note"] = (f"{args.n} complete check-ins, each in a new session, same enrolled student; challenge pinned to TILT_LEFT "
                     "and the two frames are real LFW photos of one person that satisfy it (no camera); in-process TestClient, so network latency is excluded.")
    print("C", {k: round(v["p50"], 1) for k, v in res["C_http_ms"].items()}, flush=True)

    (OUT / "latency.json").write_text(json.dumps(res, indent=1))
    try:
        _db.unlink()
    except OSError:
        pass
    print("wrote", OUT / "latency.json")


if __name__ == "__main__":
    main()
