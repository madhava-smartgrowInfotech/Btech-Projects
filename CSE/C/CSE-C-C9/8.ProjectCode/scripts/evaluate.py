"""Evaluate persisted FinSight AI artifacts (prints a readable report)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


def main():
    for f in ["training_summary.json", "model_comparison.json", "metrics.json",
              "validation_report.json", "stats_report.json", "forecast.json"]:
        p = ART / f
        print(f"\n===== {f} =====")
        if p.exists():
            print(p.read_text()[:3000])
        else:
            print("MISSING")


if __name__ == "__main__":
    main()
