"""Simulate leak / no-leak scenarios on the twin (seeded) -> data/sample/leak_scenarios.csv.

Each row is what the 16 pressure loggers and 5 zone inlet meters would report at the minimum-night-flow
window, as residuals against the twin's no-leak expectation, with demand uncertainty and sensor noise.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import twin  # noqa: E402

N_LEAK, N_NONE = 700, 700


def main():
    rng = np.random.default_rng(2024)
    pipes = twin.candidate_pipes()
    rows = []
    for i in range(N_LEAK + N_NONE):
        if i < N_LEAK:
            pipe, lps = str(rng.choice(pipes)), float(rng.uniform(2.0, 20.0))
        else:
            pipe, lps = None, 0.0
        r = twin.residuals(twin.observe(pipe, lps, rng))
        rows.append({**dict(zip(twin.FEATURES, np.round(r, 4))), "leak": int(pipe is not None),
                     "pipe": pipe or "", "zone": twin.pipe_zone()[pipe] if pipe else "", "leak_lps": round(lps, 2)})
        if (i + 1) % 200 == 0:
            print(f"{i + 1} scenarios")
    out = ROOT / "data" / "sample" / "leak_scenarios.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved {len(rows)} scenarios -> {out}")


if __name__ == "__main__":
    main()
