"""JSON-safe conversion for numpy / pandas values (NaN -> null)."""
import json
import math

import numpy as np
import pandas as pd
from fastapi.responses import JSONResponse


def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, pd.DataFrame):
        return jsonable(obj.to_dict(orient="records"))
    if isinstance(obj, (pd.Series, pd.Index, np.ndarray)):
        return jsonable(obj.tolist())
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        return None if math.isnan(f) or math.isinf(f) else f
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if obj is pd.NA or obj is pd.NaT:
        return None
    if obj is None or isinstance(obj, (str, int, bool)):
        return obj
    return str(obj)


class SafeJSON(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(jsonable(content), ensure_ascii=False, allow_nan=False).encode("utf-8")


def downsample(xs, ys, n: int = 120):
    """Keep at most n evenly spaced points of a curve (always including both ends)."""
    xs, ys = list(xs), list(ys)
    if len(xs) <= n:
        return xs, ys
    idx = np.unique(np.linspace(0, len(xs) - 1, n).round().astype(int))
    return [xs[i] for i in idx], [ys[i] for i in idx]
