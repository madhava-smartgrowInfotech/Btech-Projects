"""
Additive, read-only endpoints for the React frontend.
They only read what the existing code already holds (dataset, fitted pipeline, saved histories);
nothing here trains, mutates or changes an existing route.
"""
import json
import numpy as np
from flask import Blueprint, jsonify, send_from_directory

MODES = ["classical", "sa", "qa"]
HOUR_SECONDS = 3600
DAY_SECONDS = 86400
AMOUNT_BINS = [0, 50, 100, 250, 500, 1000, float("inf")]
AMOUNT_LABELS = ["< 50", "50-100", "100-250", "250-500", "500-1000", "1000+"]


def _group(df, col):
    out = []
    for key, g in df.groupby(col):
        total = int(len(g))
        fraud = int((g["Class"] == 1).sum())
        out.append({"name": str(key), "total": total, "fraud": fraud, "rate": fraud / total if total else 0.0})
    return sorted(out, key=lambda r: r["rate"], reverse=True)


def create_blueprint(store, ensure_data, ensure_pipeline, base_path, model_dir):
    bp = Blueprint("extra", __name__)

    @bp.route("/api/dataset_stats")
    def dataset_stats():
        df = ensure_data()
        legit = df[df["Class"] == 0]
        fraud = df[df["Class"] == 1]
        hours = ((df["Time"] % DAY_SECONDS) // HOUR_SECONDS).astype(int)
        by_hour = []
        for h in range(24):
            sel = df[hours == h]
            total = int(len(sel))
            f = int((sel["Class"] == 1).sum())
            by_hour.append({"hour": h, "total": total, "fraud": f, "rate": f / total if total else 0.0})
        buckets = []
        cats = np.digitize(df["Amount"].values, AMOUNT_BINS[1:-1])
        for i, label in enumerate(AMOUNT_LABELS):
            m = cats == i
            buckets.append({
                "name": label,
                "legit": int(((df["Class"].values == 0) & m).sum()),
                "fraud": int(((df["Class"].values == 1) & m).sum()),
            })

        def split(col, names):
            res = {}
            for val, name in names.items():
                g = df[df[col] == val]
                total = int(len(g))
                f = int((g["Class"] == 1).sum())
                res[name] = {"total": total, "fraud": f, "rate": f / total if total else 0.0}
            return res

        return jsonify({
            "rows": int(len(df)),
            "fraud": int(len(fraud)),
            "legit": int(len(legit)),
            "amount": {
                "legit_mean": float(legit["Amount"].mean()), "fraud_mean": float(fraud["Amount"].mean()),
                "legit_median": float(legit["Amount"].median()), "fraud_median": float(fraud["Amount"].median()),
                "max": float(df["Amount"].max()),
            },
            "by_merchant": _group(df, "Merchant_Category"),
            "by_channel": _group(df, "Transaction_Type"),
            "by_hour": by_hour,
            "amount_buckets": buckets,
            "card_present": split("Card_Present", {1: "present", 0: "not_present"}),
            "country_match": split("Country_Match", {1: "match", 0: "mismatch"}),
        })

    @bp.route("/api/model_history")
    def model_history():
        out = {}
        for mode in MODES:
            hist = store["histories"].get(mode)
            if not hist:
                p = model_dir / f"history_{mode}.json"
                if p.exists():
                    with open(p) as f:
                        hist = json.load(f)
                    store["histories"][mode] = hist
            if hist:
                out[mode] = hist
        return jsonify(out)

    @bp.route("/api/feature_importance")
    def feature_importance():
        res = ensure_pipeline()
        imp = res.get("feature_importance", {})
        ranked = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)
        selected = set(res.get("columns", []))
        return jsonify({
            "importance": [{"feature": k, "importance": float(v), "selected": k in selected} for k, v in ranked[:30]],
            "columns": list(res.get("columns", [])),
            "dropped_corr": list(res.get("dropped_corr", [])),
            "train_shape": [int(x) for x in res["X_train"].shape],
            "test_shape": [int(x) for x in res["X_test"].shape],
        })

    @bp.route("/api/sample_batch")
    def sample_batch():
        return send_from_directory(str(base_path / "data"), "sample_batch.csv", as_attachment=True)

    return bp
