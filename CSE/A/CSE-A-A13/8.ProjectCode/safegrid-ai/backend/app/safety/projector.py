"""Projection = largest scaling lam in [0,1] of an action's physical effect that stays safe."""
from __future__ import annotations

import math
from typing import Callable


def bisect_max(is_safe: Callable[[float], bool], hi: float = 1.0, iters: int = 30) -> float:
    """Largest lam <= hi with is_safe(lam), assuming safety is monotone in lam. Returns 0.0 if none."""
    if is_safe(hi):
        return hi
    if not is_safe(0.0):
        return 0.0
    lo, up = 0.0, hi
    for _ in range(iters):
        mid = 0.5 * (lo + up)
        if is_safe(mid):
            lo = mid
        else:
            up = mid
    return lo


def floor_to(x: float, places: int = 6) -> float:
    f = 10 ** places
    return math.floor(x * f) / f
