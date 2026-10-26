"""
smoke_test.py
--------------
End-to-end check of the TrendCast API against a running backend (default http://localhost:8317).

    python scripts/smoke_test.py [--base http://localhost:8317] [--data data/sample_hm]

Walks the whole pipeline: upload -> explore -> features -> train -> domain adaptation -> evaluation -> forecast -> AI.
Needs H&M-shaped CSVs; `python scripts/make_sample_data.py` creates synthetic ones.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8317")
    ap.add_argument("--data", default=str(ROOT / "data" / "sample_hm"))
    args = ap.parse_args()
    api = args.base.rstrip("/") + "/api"
    data = Path(args.data)

    r = requests.get(f"{api}/health", timeout=10)
    check("health", r.ok and r.json()["status"] == "ok")

    # --- gating: nothing downstream works before upload ------------------
    requests.post(f"{api}/data/upload", timeout=10)  # no files -> 422, state untouched
    r = requests.get(f"{api}/state", timeout=10).json()
    if not r["data_loaded"]:
        check("explore is gated before upload", requests.get(f"{api}/explore", timeout=10).status_code == 409)

    # --- upload validation: wrong file gives a friendly 400 ---------------
    r = requests.post(
        f"{api}/data/upload",
        files={"transactions": ("t.csv", b"a,b\n1,2\n"), "articles": ("a.csv", (data / "articles.csv").read_bytes())},
        data={"sample_rows": 0},
        timeout=60,
    )
    check("bad transactions file -> 400 with column message", r.status_code == 400 and "missing required column" in r.json()["detail"], r.text[:90])

    # --- upload -----------------------------------------------------------
    with open(data / "transactions_train.csv", "rb") as t, open(data / "articles.csv", "rb") as a, open(data / "customers.csv", "rb") as c:
        r = requests.post(
            f"{api}/data/upload",
            files={"transactions": t, "articles": a, "customers": c},
            data={"sample_rows": 200000},
            timeout=300,
        )
    check("upload", r.ok, r.text[:120])
    rep = r.json()
    check("quality report has counts", rep["num_transactions"] > 0 and rep["num_products"] > 0, f"{rep['num_transactions']} txns, {rep['num_products']} products")
    check("report endpoint", requests.get(f"{api}/data/report", timeout=10).json()["num_transactions"] == rep["num_transactions"])

    # --- explore + demand table ------------------------------------------
    r = requests.get(f"{api}/explore", timeout=120)
    ex = r.json()
    check("explore series", r.ok and len(ex["daily"]) > 30 and len(ex["top_products"]) == 10 and len(ex["price_hist"]) == 50)
    r = requests.get(f"{api}/demand/table", params={"limit": 200}, timeout=30)
    check("demand table", r.ok and len(r.json()["rows"]) == 200 and r.json()["total"] >= 200)

    # --- gating on training before features -------------------------------
    check("training is gated before features", requests.post(f"{api}/training/baseline", json={"train_fraction": 0.8}, timeout=10).status_code == 409)

    # --- features ---------------------------------------------------------
    r = requests.post(f"{api}/features/build", timeout=600)
    ft = r.json()
    check("build features", r.ok and ft["rows"] > 1000 and "lag_7" in ft["feature_columns"], f"{ft.get('rows')} rows x {ft.get('columns')} cols")
    check("head has 50 rows", len(ft["head"]) == 50)

    # --- training ---------------------------------------------------------
    r = requests.get(f"{api}/training/split", params={"train_fraction": 0.8}, timeout=30)
    check("split summary", r.ok and r.json()["train_rows"] > r.json()["test_rows"] > 0)
    r = requests.post(f"{api}/training/baseline", json={"train_fraction": 0.8}, timeout=120)
    check("moving-average baseline", r.ok and r.json()["metrics"]["RMSE"] > 0, f"RMSE {r.json()['metrics']['RMSE']:.3f}")
    r = requests.post(f"{api}/training/xgboost", json={"train_fraction": 0.8, "tune": False}, timeout=600)
    xg = r.json()
    check("xgboost train", r.ok and xg["metrics"]["RMSE"] > 0 and len(xg["comparison"]) == 2, f"RMSE {xg['metrics']['RMSE']:.3f}")
    check("model persisted", requests.get(f"{api}/state", timeout=10).json()["saved_model_exists"])
    check("load saved model", requests.post(f"{api}/training/load", timeout=30).ok)

    # --- domain adaptation ------------------------------------------------
    opts = requests.get(f"{api}/domain/options", timeout=30).json()["options"]
    chan = next(o for o in opts if o["column"] == "sales_channel_id")
    check("domain options", len(chan["values"]) >= 2, ", ".join(v["label"] for v in chan["values"]))
    src, tgt = chan["values"][0]["value"], chan["values"][1]["value"]
    check("same source/target rejected", requests.post(f"{api}/domain/run", json={"domain_col": "sales_channel_id", "source": src, "target": src}, timeout=30).status_code == 400)
    r = requests.post(f"{api}/domain/run", json={"domain_col": "sales_channel_id", "source": src, "target": tgt}, timeout=600)
    dm = r.json()
    check("domain run", r.ok and 0 <= dm["classifier_accuracy"] <= 1 and len(dm["shift"]) > 0 and len(dm["report"]) == 4, f"clf acc {dm.get('classifier_accuracy', 0):.2%}")
    check("histogram + box data", len(dm["histogram"]) > 5 and dm["box"]["source"]["n"] > 0)

    # --- evaluation -------------------------------------------------------
    ev = requests.get(f"{api}/evaluation", timeout=30).json()
    check("evaluation", len(ev["comparison"]) == 2 and ev["domain"] is not None and len(ev["importance"]) > 0)

    # --- forecast ---------------------------------------------------------
    arts = requests.get(f"{api}/forecast/articles", timeout=30).json()["articles"]
    check("forecast articles", len(arts) > 10)
    for horizon in (7, 14, 30):
        r = requests.post(f"{api}/forecast", json={"article_id": arts[0]["id"], "horizon": horizon}, timeout=120)
        check(f"forecast {horizon}d", r.ok and len(r.json()["forecast"]) == horizon and len(r.json()["history"]) > 0)
    check("bad horizon rejected", requests.post(f"{api}/forecast", json={"article_id": arts[0]["id"], "horizon": 5}, timeout=10).status_code == 400)

    # --- AI (optional) ----------------------------------------------------
    st = requests.get(f"{api}/ai/status", timeout=10).json()
    if st["configured"]:
        r = requests.post(f"{api}/ai/explain", json={"question": "Which feature matters most?"}, timeout=90)
        check("ai explain (live Gemini or clear error)", r.ok or r.status_code in (502, 503), f"{r.status_code} {r.text[:100]}")
    else:
        check("ai not configured -> 503 with notice", requests.post(f"{api}/ai/explain", json={"question": ""}, timeout=10).status_code == 503)

    print(f"\n{len(failures)} failure(s)" if failures else "\nAll checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
