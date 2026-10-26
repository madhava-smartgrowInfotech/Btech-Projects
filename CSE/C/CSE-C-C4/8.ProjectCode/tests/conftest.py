import os
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tensorflow  # noqa: E402,F401  (imported first: sklearn/scipy before TensorFlow breaks its DLLs on this machine)
