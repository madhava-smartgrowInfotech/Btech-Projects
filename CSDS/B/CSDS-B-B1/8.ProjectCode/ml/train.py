"""Train every CivicPulse model from data/raw and write experiments/metrics.json.

    venv\\Scripts\\python ml\\train.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.training import METRICS_PATH, train_full  # noqa: E402

if __name__ == "__main__":
    m = train_full()
    print(json.dumps({k: m[k] for k in ("version", "train_seconds")}, indent=2))
    for f in ("category", "department", "priority"):
        print(f"{f:10s} test acc {m[f]['test']['accuracy']:.3f}  macro-F1 {m[f]['test']['macro_f1']:.3f}  "
              f"by language {m[f]['by_language']}")
    r = m["resolution"]
    print(f"resolution MAE {r['mae_days']} days (baseline {r['baseline_category_median_mae_days']}), "
          f"SLA flag accuracy {r['sla_breach_flag_accuracy']}")
    print("metrics ->", METRICS_PATH)
