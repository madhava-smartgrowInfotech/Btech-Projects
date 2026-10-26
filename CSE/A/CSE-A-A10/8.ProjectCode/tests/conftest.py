import sys
from pathlib import Path

try:  # Windows: torch must load before scikit-learn / OpenCV
    import torch  # noqa: F401
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
