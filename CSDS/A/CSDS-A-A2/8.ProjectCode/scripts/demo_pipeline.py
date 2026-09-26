"""
Headless end-to-end demonstration of the verification pipeline (no camera needed).

    python scripts/demo_pipeline.py [--db sqlite:///demo.db]

It uses the sample group photo bundled with InsightFace, crops single faces,
and runs the exact same service-layer pipeline the web app uses, showing every
proxy-prevention check in action:

  1. genuine student               -> PASS
  2. same student again             -> blocked (already marked)
  3. outside the geo-fence          -> blocked (location)
  4. wrong liveness action          -> blocked (liveness)
  5. different person, same roll    -> blocked (identity mismatch)
  6. same person, another roll no.  -> blocked (duplicate face in session)
  7. roll number not allowed        -> blocked (eligibility)
  8. second device for a student     -> blocked (device binding)
  9. genuine student B               -> PASS
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

parser = argparse.ArgumentParser()
parser.add_argument("--db", default=f"sqlite:///{ROOT / 'demo_pipeline.db'}")
args = parser.parse_args()
os.environ["DATABASE_URL"] = args.db
os.environ.setdefault("AM_REQUIRE_ENROLLMENT", "true")

import config  # noqa: E402
from core import face_match, liveness, services  # noqa: E402
from core.db import init_db  # noqa: E402
from core.timeutil import utcnow  # noqa: E402


def banner(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def face_crops() -> list[np.ndarray]:
    from insightface.data import get_image

    img = get_image("t1")
    faces = face_match.get_embedder().faces(img)
    crops = []
    for f in sorted(faces, key=lambda f: f.bbox[0]):
        x1, y1, x2, y2 = f.bbox.astype(int)
        m = int(0.6 * max(x2 - x1, y2 - y1))
        crops.append(img[max(0, y1 - m): y2 + m, max(0, x1 - m): x2 + m].copy())
    return crops


def make_challenge_frame(neutral: np.ndarray, challenge: str) -> np.ndarray:
    """
    Synthesise a 'challenge' frame from a neutral one so the demo can run without a
    person: a small rotation simulates a head tilt. Only TILT challenges are simulated;
    other challenges are demonstrated as failures (photo cannot respond).
    """
    h, w = neutral.shape[:2]
    angle = {"TILT_LEFT": -20, "TILT_RIGHT": 20}.get(challenge, 0)
    if config.CAMERA_MIRRORED:
        angle = -angle
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(neutral, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def show(res: services.PipelineResult) -> None:
    print(f"  -> {'PASS ✅' if res.success else 'BLOCKED 🚫'} at stage '{res.stage}': {res.reason}")


def main() -> None:
    if args.db.startswith("sqlite:///"):
        p = Path(args.db.replace("sqlite:///", ""))
        if p.exists():
            p.unlink()
    init_db()

    banner("Loading models and sample faces")
    crops = face_crops()
    # pick frontal-ish faces for the demo (neutral checks require |yaw| small)
    usable = []
    for c in crops:
        m = liveness.analyze(c)
        if m.ok and liveness.check_neutral(m) is None:
            usable.append(c)
    if len(usable) < 2:
        # relax neutral yaw for the demo images
        config.NEUTRAL_MAX_YAW = 0.2
        usable = [c for c in crops if liveness.analyze(c).ok and liveness.check_neutral(liveness.analyze(c)) is None]
    person_a, person_b = usable[0], usable[1]
    print(f"{len(crops)} faces found, using 2 frontal faces as 'Student A' and 'Student B'")

    banner("Registering faculty + students (Student A enrols Person A's face)")
    faculty = services.register_user("faculty", "guide@demo", "Demo Guide", "faculty123")
    stu_a = services.register_user("student", "23K91A6706", "A. Greeshma", "student123", "23K91A6706", person_a)
    stu_b = services.register_user("student", "23K91A6740", "B. Vinay", "student123", "23K91A6740", person_b)
    stu_c = services.register_user("student", "23K91A6757", "G. Sriram", "student123", "23K91A6757", person_a)  # enrolled with A's face (proxy setup)
    stu_x = services.register_user("student", "99X99X9999", "Outsider", "student123", "99X99X9999", person_b)

    now = utcnow()
    session = services.create_session(
        faculty.id, "CS601", "Machine Learning", "CSDS-A", now - timedelta(minutes=1), now + timedelta(minutes=30),
        latitude=17.3850, longitude=78.4867, radius_m=60, allowed_rolls="23K91A67*,24K95A6704",
    )
    print("Session link:", services.session_link(session))
    inside = (17.38505, 78.48675)     # ~7 m from centre
    outside = (17.3900, 78.4867)      # ~550 m away
    dev_a, dev_b = "device-A" * 8, "device-B" * 8

    banner("1) Genuine student A, inside fence, correct TILT_LEFT challenge")
    ch = "TILT_LEFT"
    show(services.run_pipeline(session, stu_a, dev_a, *inside, 12.0, ch, person_a, make_challenge_frame(person_a, ch)))

    banner("2) Student A tries again (already marked)")
    show(services.run_pipeline(session, stu_a, dev_a, *inside, 12.0, ch, person_a, make_challenge_frame(person_a, ch)))

    banner("3) Student B outside the geo-fence")
    show(services.run_pipeline(session, stu_b, dev_b, *outside, 12.0, ch, person_b, make_challenge_frame(person_b, ch)))

    banner("4) Student B inside, but challenge was OPEN_MOUTH and a static photo was submitted")
    show(services.run_pipeline(session, stu_b, dev_b, *inside, 12.0, "OPEN_MOUTH", person_b, person_b))

    banner("5) Someone submits Person A's face for Student B's roll number (identity mismatch)")
    show(services.run_pipeline(session, stu_b, dev_b, *inside, 12.0, ch, person_a, make_challenge_frame(person_a, ch)))

    banner("6) Person A (already marked as A) tries to mark Student C too (duplicate face)")
    show(services.run_pipeline(session, stu_c, dev_b, *inside, 12.0, ch, person_a, make_challenge_frame(person_a, ch)))

    banner("7) Roll number not in the allowed list")
    show(services.run_pipeline(session, stu_x, dev_b, *inside, 12.0, ch, person_b, make_challenge_frame(person_b, ch)))

    banner("8) Student D binds device D1 (attempt from outside), then tries from a second device D2")
    stu_d = services.register_user("student", "24K95A6704", "B. Sai Kumar", "student123", "24K95A6704", person_b)
    show(services.run_pipeline(session, stu_d, "device-D1" * 7, *outside, 12.0, ch, person_b, make_challenge_frame(person_b, ch)))
    show(services.run_pipeline(session, stu_d, "device-D2" * 7, *inside, 12.0, ch, person_b, make_challenge_frame(person_b, ch)))

    banner("9) Student B correctly from the device it registered with")
    show(services.run_pipeline(session, stu_b, dev_b, *inside, 12.0, ch, person_b, make_challenge_frame(person_b, ch)))

    banner("Final attendance for the session")
    for r in services.records_for(session.id):
        print(f"  {r.roll_number:<12} {r.student_name:<14} dist={r.distance_m:5.1f} m  challenge={r.challenge:<10} "
              f"liveness={r.liveness_score:.2f}  identity={r.identity_similarity:.2f}  "
              f"maxdup={(r.max_duplicate_similarity if r.max_duplicate_similarity is not None else 0):.2f}")
    attempts = services.attempts_for(session.id)
    print(f"\n{sum(1 for a in attempts if not a.passed)} blocked attempts logged, "
          f"{len(services.records_for(session.id))} students present.")

    from core import export

    out = ROOT / "demo_attendance.xlsx"
    out.write_bytes(export.to_excel_bytes(session, services.records_for(session.id), attempts,
                                          services.expected_rolls(session.allowed_rolls)))
    print("Excel export written to", out)


if __name__ == "__main__":
    main()
