"""
Single source of truth for the documentation build.

Nothing here is typed in by hand except batch details (copied from the batch documents) and
facts read from the code. All performance numbers are read from experiments/*/metrics.json,
experiments/api_latency.json and experiments/test_run.json at build time.
"""

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A12
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

TITLE = "Pneumonia Detection Using Deep Learning"
BATCH_NO = "A12"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
CITY = "Hyderabad, Telangana"
YEAR = "2026-2027"
STUDENTS = [
    ("CHOUDAM AKSHITHA", "23K91A0556"),
    ("BOGGULA SATVIK KUMAR", "23K91A0541"),
    ("ARUTLA ABHI THEJ REDDY", "23K91A0515"),
    ("DUGGARAJU LIKHITHA", "23K91A0565"),
]
GUIDE = "V. MEENAKSHI"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("S. M. Mahin, T. Hasan, S. Karim, M. B. R. Nuha, E. H. Tusher, A. R. Hussain, J. Uddin and D. Ghose, "
              "\"From Pneumonia to Multi-Disease: Interpretable and Uncertainty-Aware Semi-Supervised Learning Strategies "
              "for Chest X-Ray Classification,\" IEEE Access, vol. 14, pp. 127532-127551, 2026, doi: 10.1109/ACCESS.2026.3722370.")

CLASSES = ["Normal", "Bacterial Pneumonia", "Viral Pneumonia"]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def exp(name):
    return _load(os.path.join(EXP, name, "metrics.json"))


E1 = exp("exp01_custom_cnn_clahe")          # baseline: project defaults (lr 1e-4, patience 6), stopped early
E2 = exp("exp02_custom_cnn_tuned")          # tuned recipe, official split: the deployed model
E3 = exp("exp03_custom_cnn_patient_split")  # tuned recipe, patient-level re-partition
E4 = exp("exp04_mobilenetv3small")          # MobileNetV3Small (base-paper backbone)
E5 = exp("exp05_custom_cnn_noclahe")        # tuned recipe without CLAHE (ablation)
API_LAT = _load(os.path.join(EXP, "api_latency.json"))
TESTS = _load(os.path.join(EXP, "test_run.json"))
MODEL_INFO = _load(os.path.join(EXP, "model_summary.json"))
DEPLOYED_NAME = (_load(os.path.join(EXP, "deployed.json")) or {}).get("experiment", "exp02_custom_cnn_tuned")
LEAK = _load(os.path.join(EXP, DEPLOYED_NAME, "patient_disjoint_subset.json"))
LEAK_BASE = _load(os.path.join(EXP, "exp01_custom_cnn_clahe", "patient_disjoint_subset.json"))
DEPLOYED = exp(DEPLOYED_NAME)


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def shot(name):
    return os.path.join(SHOTS, name)


def shot_view(name, max_h=1500):
    """Screenshot path for documents: very tall full-page captures are cropped to the first `max_h` pixels."""
    from PIL import Image

    p = os.path.join(SHOTS, name)
    with Image.open(p) as im:
        w, h = im.size
        if h <= max_h * 1.35:
            return p
        os.makedirs(os.path.join(FIGS, "_crops"), exist_ok=True)
        out = os.path.join(FIGS, "_crops", name)
        im.convert("RGB").crop((0, 0, w, max_h)).save(out)
        return out


def shot_w(path, base=5.6, max_h_in=6.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, max_h_in * w / h)


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)
