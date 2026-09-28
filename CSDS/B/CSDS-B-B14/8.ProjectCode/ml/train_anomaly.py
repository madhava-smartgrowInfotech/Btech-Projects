"""Fit the IsolationForest for abnormal meter consumption and score it against the injected anomalies."""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import anomaly  # noqa: E402

TYPE_MAP = {"night_flow": "night_flow", "burst": "burst", "theft": "suspected_theft"}


def main():
    day = anomaly.daily_features(anomaly.load_hourly())
    model = IsolationForest(n_estimators=300, contamination=0.025, random_state=42)
    model.fit(day[anomaly.FEATURES])
    joblib.dump(model, anomaly.MODEL_PATH)
    anomaly._cache.pop("scored", None)
    s = anomaly.scored()
    truth = pd.read_csv(ROOT / "data" / "sample" / "meter_anomaly_truth.csv", parse_dates=["date"])
    s = s.merge(truth.rename(columns={"type": "true_type"}), on=["meter_id", "date"], how="left")
    y = s.true_type.notna()
    typed = s[y & s.anomaly]
    metrics = {
        "meter_days": len(s), "true_anomalous_days": int(y.sum()),
        "day_level": {"precision": round(precision_score(y, s.anomaly), 4), "recall": round(recall_score(y, s.anomaly), 4)},
        "type_accuracy": round(float((typed.true_type.map(TYPE_MAP) == typed.type).mean()), 4),
        "recall_by_type": {t: round(float(g.anomaly.mean()), 4) for t, g in s[y].groupby("true_type")},
    }
    flagged = {m["meter_id"] for m in anomaly.flagged_meters()}
    last = s.date.max()
    true_recent = set(truth[truth.date > last - pd.Timedelta(days=anomaly.RECENT_DAYS)].meter_id)
    tp = len(flagged & true_recent)
    metrics["meter_level_last_7_days"] = {"flagged": len(flagged), "truly_anomalous": len(true_recent),
                                          "precision": round(tp / len(flagged), 4) if flagged else 0.0,
                                          "recall": round(tp / len(true_recent), 4) if true_recent else 0.0}
    print(json.dumps(metrics, indent=1))
    (ROOT / "experiments" / "anomaly_metrics.json").write_text(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()
