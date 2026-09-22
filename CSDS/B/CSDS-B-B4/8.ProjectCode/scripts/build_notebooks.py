"""Builds (and executes) the notebooks in notebooks/.

    01_data_exploration.ipynb         - what is in each dataset
    02_kaggle_behaviour_model.ipynb   - Kaggle-ready M1 training (runs on Kaggle or locally)
    03_risk_explainability.ipynb      - how M3 explains one risky payment with SHAP

Run: venv\\Scripts\\python scripts\\build_notebooks.py [--no-execute]
Needs: pip install nbformat nbclient ipykernel
"""
from __future__ import annotations

import argparse
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

SETUP = """import sys, json
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "backend")); sys.path.insert(0, str(ROOT / "ml"))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 30)
RAW = ROOT / "data" / "raw"
print("project root:", ROOT)"""

EXPLORE = [
    md("# UPI Guardian - data exploration\nA look at every dataset the models use. All datasets are committed under `data/raw/` (see `docs/04_DATASET.md`)."),
    code(SETUP),
    md("## 1. Digital Payment Fraud Detection Benchmark (M1)\n400,000 transactions over 2023 with a strict time split and drift after month 6."),
    code("""bench = pd.concat([pd.read_csv(RAW/"payment_fraud_benchmark"/f, parse_dates=["transaction_time"]) for f in ("transactions_train.csv","transactions_test.csv")])
print(bench.shape); bench.head(3)"""),
    code("""monthly = bench.groupby(bench.transaction_time.dt.month).is_fraud.mean()
ax = monthly.plot(kind="bar", color="#0d9488", figsize=(7,3), title="Fraud rate by month (drift after month 6)")
ax.set_xlabel("month"); ax.set_ylabel("fraud rate"); plt.tight_layout(); plt.show()"""),
    code("""corr = bench.drop(columns=["transaction_id","customer_id","merchant_id"]).select_dtypes("number").corr()["is_fraud"].drop("is_fraud").sort_values()
corr.plot(kind="barh", color="#f59e0b", figsize=(7,5), title="Correlation with is_fraud (post_auth_risk_score is leakage and is dropped)"); plt.tight_layout(); plt.show()"""),
    md("## 2. UPI Transactions 2024 (behaviour profiles)\nIts `fraud_flag` turns out not to be learnable, so it is used for amounts and time-of-day profiles."),
    code("""upi = pd.read_csv(RAW/"upi_transactions_2024"/"upi_transactions_2024.csv", parse_dates=["timestamp"])
print(upi.shape, "fraud_flag rate", round(upi.fraud_flag.mean(), 4))
fig, ax = plt.subplots(1, 2, figsize=(11,3))
upi.hour_of_day.value_counts().sort_index().plot(kind="bar", ax=ax[0], color="#0d9488", title="Payments by hour")
upi.groupby("merchant_category")["amount (INR)"].median().sort_values().plot(kind="barh", ax=ax[1], color="#f59e0b", title="Median amount by category (INR)")
plt.tight_layout(); plt.show()"""),
    code("""for c in ["transaction type", "merchant_category", "device_type"]:
    print(c, upi.groupby(c).fraud_flag.mean().round(4).to_dict())"""),
    md("## 3. SMS Spam Collection + Indian UPI-scam SMS set (M2)"),
    code("""uci = pd.read_csv(RAW/"sms_spam_collection"/"spam.csv", encoding="latin-1")[["v1","v2"]]
ind = pd.read_csv(RAW/"upi_scam_sms"/"upi_scam_sms.csv")
print("UCI:", uci.v1.value_counts().to_dict(), "| Indian set:", ind.label.value_counts().to_dict())
pd.crosstab(ind.category, ind.language)"""),
    code("""ind.groupby(["language","script"]).size().unstack(fill_value=0)"""),
    md("## 4. Scenario simulator sample (M3)\nA 5,000-row sample of the simulated UPI year (`data/sample/upi_scenarios_sample.csv`, scams over-sampled for readability)."),
    code("""sim = pd.read_csv(ROOT/"data"/"sample"/"upi_scenarios_sample.csv")
print(sim.shape); print(sim.scam_type.value_counts().to_dict())
sim.groupby("label")[["is_new_payee","payee_account_age_days","payee_reports","sms_scam_prob","is_night","amount_to_median"]].mean().round(3)"""),
]

KAGGLE = [
    md("""# UPI Guardian - M1 behaviour model (Kaggle-ready)
Runs as-is on Kaggle (**Add data** -> *Digital Payment Fraud Detection Benchmark* by rohit8527kmr7518) or locally from this repository.
It reproduces `ml/train_behaviour.py`: strict time split, XGBoost with early stopping on PR-AUC, SHAP.
Download `behaviour_model.joblib` from the notebook output and place it in `models/` to use it in the app."""),
    code("""import os, math, json
from pathlib import Path
import numpy as np, pandas as pd, xgboost as xgb, joblib
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve
KAGGLE_DIR = Path("/kaggle/input/digital-payment-fraud-detection-benchmark")
LOCAL_DIR = (Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()) / "data/raw/payment_fraud_benchmark"
DATA = KAGGLE_DIR if KAGGLE_DIR.exists() else LOCAL_DIR
OUT = Path("/kaggle/working") if KAGGLE_DIR.exists() else Path.cwd()
print("reading from", DATA)"""),
    code("""FEATURES = ["log_amount","amount_deviation_from_user_mean","avg_monthly_spend","account_age_days","txn_count_1h","txn_count_24h",
            "failed_txn_count_24h","geo_distance_from_last_txn","merchant_risk_score","is_international","hour_sin","hour_cos",
            "device_mobile","device_desktop","device_tablet"]
def frame(df):
    h = df.transaction_time.dt.hour + df.transaction_time.dt.minute / 60
    return pd.DataFrame({
        "log_amount": np.log1p(df.transaction_amount.clip(lower=0)),
        "amount_deviation_from_user_mean": df.amount_deviation_from_user_mean,
        "avg_monthly_spend": df.avg_monthly_spend,
        "account_age_days": df.account_age_days.clip(30, 2000).astype(float),
        "txn_count_1h": df.txn_count_1h.astype(float), "txn_count_24h": df.txn_count_24h.astype(float),
        "failed_txn_count_24h": df.failed_txn_count_24h.astype(float),
        "geo_distance_from_last_txn": df.geo_distance_from_last_txn.astype(float),
        "merchant_risk_score": df.merchant_risk_score, "is_international": df.is_international.astype(float),
        "hour_sin": np.sin(2*np.pi*h/24), "hour_cos": np.cos(2*np.pi*h/24),
        "device_mobile": (df.device_type=="mobile").astype(float), "device_desktop": (df.device_type=="desktop").astype(float),
        "device_tablet": (df.device_type=="tablet").astype(float)})[FEATURES]
train = pd.read_csv(DATA/"transactions_train.csv", parse_dates=["transaction_time"]).sort_values("transaction_time")
test = pd.read_csv(DATA/"transactions_test.csv", parse_dates=["transaction_time"]).sort_values("transaction_time")
fit, val = train[train.transaction_time < "2023-09-01"], train[train.transaction_time >= "2023-09-01"]
rng = np.random.default_rng(42)
x_fit = frame(fit); x_fit.loc[rng.random(len(x_fit)) < 0.5, "geo_distance_from_last_txn"] = np.nan
print(len(fit), len(val), len(test))"""),
    code("""model = xgb.XGBClassifier(n_estimators=1500, learning_rate=0.03, max_depth=4, min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
                          reg_lambda=2.0, tree_method="hist", eval_metric="aucpr", early_stopping_rounds=100, random_state=42, n_jobs=-1)
model.fit(x_fit, fit.is_fraud, eval_set=[(frame(val), val.is_fraud)], verbose=False)
s = model.predict_proba(frame(test))[:, 1]
print("best iteration", model.best_iteration, "| test PR-AUC", round(average_precision_score(test.is_fraud, s), 4), "| ROC-AUC", round(roc_auc_score(test.is_fraud, s), 4))"""),
    code("""import shap
sample = frame(test).sample(2000, random_state=42)
sv = shap.TreeExplainer(model).shap_values(sample)
shap.summary_plot(sv, sample, show=True, max_display=12)"""),
    code("""joblib.dump({"version": "m1-xgb-kaggle", "model": model, "features": FEATURES}, OUT / "behaviour_model_kaggle.joblib", compress=3)
print("saved", OUT / "behaviour_model_kaggle.joblib")"""),
]

EXPLAIN = [
    md("# UPI Guardian - explaining one payment\nHow M3 (the score users see) decides, using SHAP on a high-risk payment from the simulator sample."),
    code(SETUP + """
import joblib, shap
bundle = joblib.load(ROOT/"models"/"risk_model.joblib")
from app.ml.features import RISK_FEATURES
from app.services.risk import score_from_probability
sim = pd.read_csv(ROOT/"data"/"sample"/"upi_scenarios_sample.csv")
X = sim[RISK_FEATURES]
sim["probability"] = bundle["model"].predict_proba(X)[:, 1]
sim["score"] = [score_from_probability(p, bundle["score_anchors"]) for p in sim.probability]
sim.groupby("label").score.describe().round(1)"""),
    code("""row = sim[(sim.label == 1) & (sim.scam_type == "impersonation")].sort_values("score").iloc[len(sim[(sim.label==1)&(sim.scam_type=="impersonation")])//2]
print("scam type:", row.scam_type, "| score:", row.score, "| amount:", row.amount)
explainer = shap.TreeExplainer(bundle["model"])
exp = explainer(X.loc[[row.name]])
shap.plots.waterfall(exp[0], max_display=10, show=True)"""),
    code("""from app.services.explain import build_reasons
contrib = dict(zip(RISK_FEATURES, exp.values[0]))
feats = {k: float(row[k]) for k in RISK_FEATURES}
risk, safe = build_reasons(feats, contrib, {"payee_name": "this receiver", "amount": float(row.amount), "local_time": "late night",
                                            "has_history": True, "report_count": int(row.payee_reports > 0), "m1_top": None})
for r in risk: print("RISK  ", r["text"]["en"], "|", r["text"]["hi"])
for r in safe: print("SAFE  ", r["text"]["en"])"""),
]


def build(execute: bool) -> None:
    NB.mkdir(exist_ok=True)
    for name, cells in [("01_data_exploration.ipynb", EXPLORE), ("02_kaggle_behaviour_model.ipynb", KAGGLE), ("03_risk_explainability.ipynb", EXPLAIN)]:
        nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
        path = NB / name
        if execute:
            from nbclient import NotebookClient

            NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(NB)}}).execute()
        nbf.write(nb, path)
        print("wrote", path.relative_to(ROOT), "(executed)" if execute else "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-execute", action="store_true")
    build(not ap.parse_args().no_execute)
