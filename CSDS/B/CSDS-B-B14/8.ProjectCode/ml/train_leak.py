"""Train the leak detector and build localisation signatures from the simulated scenarios."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import leaks, twin  # noqa: E402


def localisation(test, sigs, center):
    top1 = top3 = zone = 0
    leak_rows = test[test.leak == 1]
    for r in leak_rows.itertuples():
        res = np.array([getattr(r, f) for f in twin.FEATURES])
        ranked = leaks.rank(res, sigs=sigs, center=center, top=3)
        top1 += ranked[0]["pipe"] == r.pipe
        top3 += r.pipe in [x["pipe"] for x in ranked]
        zone += ranked[0]["zone"] == r.zone
    n = len(leak_rows)
    return {"top1_accuracy": round(top1 / n, 4), "top3_accuracy": round(top3 / n, 4),
            "zone_accuracy": round(zone / n, 4), "leak_scenarios": n}


def main():
    df = pd.read_csv(ROOT / "data" / "sample" / "leak_scenarios.csv", keep_default_na=False)
    tr, te = train_test_split(df, test_size=0.25, stratify=df["leak"], random_state=42)
    clf = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1)
    clf.fit(tr[twin.FEATURES], tr["leak"])
    p = clf.predict_proba(te[twin.FEATURES])[:, 1]
    det = {"precision": round(precision_score(te.leak, p >= 0.5), 4), "recall": round(recall_score(te.leak, p >= 0.5), 4),
           "f1": round(f1_score(te.leak, p >= 0.5), 4), "roc_auc": round(roc_auc_score(te.leak, p), 4)}
    # recall by leak size
    lk = te[te.leak == 1].assign(pred=p[te.leak.values == 1] >= 0.5)
    bins = pd.cut(lk.leak_lps, [0, 4, 8, 14, 21])
    det["recall_by_size_lps"] = {str(k): round(float(v), 4) for k, v in lk.groupby(bins, observed=True)["pred"].mean().items()}
    sigs = leaks.compute_signatures()
    loc_raw = localisation(te, sigs, center=False)
    loc_ctr = localisation(te, sigs, center=True)
    center = loc_ctr["top3_accuracy"] >= loc_raw["top3_accuracy"]
    metrics = {"scenarios": len(df), "test_scenarios": len(te), "candidate_pipes": len(sigs),
               "sensors": {"pressure_loggers": len(twin.SENSORS), "zone_inlet_meters": len(twin.ZONES)},
               "detection": det, "localisation": loc_ctr if center else loc_raw,
               "localisation_variants": {"raw": loc_raw, "pressure_centered": loc_ctr}}
    print(json.dumps(metrics, indent=1))
    joblib.dump(clf, leaks.DETECTOR_PATH, compress=3)
    leaks.SIGNATURES_PATH.write_text(json.dumps({"ref_lps": leaks.SIG_LPS, "center_pressure": center, "pipes": sigs}))
    (ROOT / "experiments" / "leak_metrics.json").write_text(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()
