"""Shared facts for the submission documents. Every number comes from docs/REPORT_FACTS.md / docs/evaluation/*.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
EVAL = ROOT / "docs" / "evaluation"
CHARTS = ROOT / "docs" / "charts"

PRODUCT = "Attendance Magic"
TITLE = "Attendance Magic: A Smart Geo-Fenced Attendance System with Live Challenge Verification"
SUBTITLE = "A Smart Geo-Fenced Attendance System with Live Challenge Verification"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A2 (CSE - Data Science, Section A)"
COLLEGE = "TKR College of Engineering and Technology"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "[GUIDE NAME]"
GUIDE_DESIG = "[DESIGNATION]"
STUDENTS = [("A.GREESHMA", "23K91A6706"), ("B.VINAY", "23K91A6740"), ("G.SRIRAM", "23K91A6757"), ("B.SAI KUMAR", "24K95A6704")]

BASE_PAPER = ('K. B. Dharmaraj, C. N. Dhanushree, H. V. Revanth, N. Shashank and P. M. Tejaswini, "Real-Time Student Face Recognition '
              'Attendance System Using AI," International Advanced Research Journal in Science, Engineering and Technology (IARJSET), '
              'vol. 12, no. 5, pp. 1067-1072, May 2025, doi: 10.17148/IARJSET.2025.125183.')

REFERENCES = [
    BASE_PAPER,
    '"A comprehensive review on face recognition, anti-spoofing liveness verification and automated dress code enforcement techniques for smart attendance framework," International Journal of Research Publication and Reviews, 2026.',
    'A. Shandilya and H. R. Shah, "Smart attendance framework using face recognition, anti-spoofing liveness verification and automated dress code enforcement," International Journal of Innovative Science and Research Technology (IJISRT), vol. 11, no. 6, Jun. 2026, doi: 10.38124/ijisrt/26jun403.',
    '"A classroom attendance system with anti-spoofing based on ResNet101 and ArcFace for face recognition," Journal of Intelligence and Knowledge Engineering, 2026.',
    'A. E. U. Salam et al., "Automatic attendance system using silent face anti-spoofing to detect spoof on face recognition," in Proc. 2025 Int. Conf. Smart Computing, IoT and Machine Learning (SIML), 2025, doi: 10.1109/SIML65326.2025.11081084.',
    'J. Deng, J. Guo, N. Xue and S. Zafeiriou, "ArcFace: Additive angular margin loss for deep face recognition," in Proc. IEEE/CVF Conf. Computer Vision and Pattern Recognition (CVPR), 2019, pp. 4690-4699.',
    'J. Guo, J. Deng, A. Lattas and S. Zafeiriou, "Sample and computation redistribution for efficient face detection," in Proc. Int. Conf. Learning Representations (ICLR), 2022.',
    'Y. Kartynnik, A. Ablavatski, I. Grishchenko and M. Grundmann, "Real-time facial surface geometry from monocular video on mobile GPUs," in Proc. CVPR Workshops, 2019, arXiv:1907.06724.',
    'G. B. Huang, M. Ramesh, T. Berg and E. Learned-Miller, "Labeled Faces in the Wild: A database for studying face recognition in unconstrained environments," Univ. Massachusetts Amherst, Tech. Rep. 07-49, Oct. 2007.',
    'T. Soukupova and J. Cech, "Real-time eye blink detection using facial landmarks," in Proc. 21st Computer Vision Winter Workshop, 2016.',
    'G. Pan, L. Sun, Z. Wu and S. Lao, "Eyeblink-based anti-spoofing in face recognition from a generic webcamera," in Proc. IEEE Int. Conf. Computer Vision (ICCV), 2007.',
    'Z. Yu, Y. Qin, X. Li, C. Zhao, Z. Lei and G. Zhao, "Deep learning for face anti-spoofing: A survey," IEEE Trans. Pattern Analysis and Machine Intelligence, vol. 45, no. 5, pp. 5609-5631, 2023.',
    'F. Schroff, D. Kalenichenko and J. Philbin, "FaceNet: A unified embedding for face recognition and clustering," in Proc. IEEE CVPR, 2015, pp. 815-823.',
    'R. W. Sinnott, "Virtues of the haversine," Sky and Telescope, vol. 68, no. 2, p. 159, 1984.',
    'T. Vincenty, "Direct and inverse solutions of geodesics on the ellipsoid with application of nested equations," Survey Review, vol. 23, no. 176, pp. 88-93, 1975.',
    'M. Jones, J. Bradley and N. Sakimura, "JSON Web Token (JWT)," RFC 7519, Internet Engineering Task Force, May 2015.',
    'K. Moriarty, B. Kaliski and A. Rusch, "PKCS #5: Password-based cryptography specification version 2.1," RFC 8018, Internet Engineering Task Force, Jan. 2017.',
    'S. Ramirez, "FastAPI documentation." [Online]. Available: https://fastapi.tiangolo.com',
    'M. Bayer, "SQLAlchemy," in The Architecture of Open Source Applications, vol. 2, A. Brown and G. Wilson, Eds., 2012.',
    'Meta Platforms, "React documentation." [Online]. Available: https://react.dev',
]


def _j(name):
    return json.loads((EVAL / name).read_text())


FV = _j("face_verification.json")
LV = _j("liveness.json")
GF = _j("geofence.json")
LT = _j("latency.json")
PB = _j("photo_bank_attack.json")
FF = _j("face_failures.json")
CHALLENGES = ["TURN_LEFT", "TURN_RIGHT", "LOOK_UP", "LOOK_DOWN", "TILT_LEFT", "TILT_RIGHT", "OPEN_MOUTH", "CLOSE_EYES"]
CH_LABEL = {"TURN_LEFT": "Turn left", "TURN_RIGHT": "Turn right", "LOOK_UP": "Look up", "LOOK_DOWN": "Look down", "TILT_LEFT": "Tilt left",
            "TILT_RIGHT": "Tilt right", "OPEN_MOUTH": "Open mouth", "CLOSE_EYES": "Close eyes"}
CH_THRESH = {"TURN_LEFT": "|dyaw| >= 0.12", "TURN_RIGHT": "|dyaw| >= 0.12", "LOOK_UP": "dpitch >= 0.08", "LOOK_DOWN": "dpitch >= 0.08",
             "TILT_LEFT": "droll >= 12 deg", "TILT_RIGHT": "droll >= 12 deg", "OPEN_MOUTH": "MAR >= 0.35", "CLOSE_EYES": "EAR <= 0.18"}


def pct(x, nd=1):
    return f"{100 * x:.{nd}f}%"
