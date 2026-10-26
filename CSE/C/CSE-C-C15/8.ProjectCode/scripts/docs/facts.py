"""
Single source of truth for the documentation build of SentinelFlow (CSE-C-C15).

Batch details come from 1.C15_BATCH_DETAILS.docx / Students.txt.  Every performance number is read at build time from
results/metrics.json (what the shipped app displays) and results/experiments/*.json (written by scripts/run_experiments.py and
scripts/measure_api.py).  docs/REPORT_FACTS.md is the human-readable copy (scripts/docs/make_report_facts.py).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C15
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "results", "experiments")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "SentinelFlow"
TITLE = "DDoS Attack Detection and Mitigation"
FULL_TITLE = "DDoS Attack Detection and Mitigation (Real-Time DDoS Detection and Adaptive Mitigation Framework Using Machine Learning)"
SUBTITLE = "Real-time DDoS detection with a Random Forest and adaptive, self-recovering mitigation"
TAGLINE = ("SentinelFlow: Scapy or simulated traffic windows, ten flow features, a 200-tree Random Forest, an explainable distributed-risk and severity layer, "
           "temporary quarantine with automatic recovery, SQLite history and a React console")
BATCH_NO = "C15"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "[COLLEGE NAME]"
COLLEGE_SHORT = "[COLLEGE NAME]"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Mallela Pallavi", "23K91A05E3"),
    ("Kattoju Durgabhavani", "24K95A0514"),
    ("Nimmala Rakshitha", "23K91A05H3"),
    ("Prodhatoor Shashi Preetham", "23K91A05K0"),
]
STUDENTS_UPPER = [(n.upper(), r) for n, r in STUDENTS]
GUIDE = "V Meenakshi"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("M. M. Trigui, M. S. Islam, M. D. Gambo, M. S. Alam and T. Helmy, \"Resource-aware ensemble framework for DDoS detection in SDN via novel "
              "game-theoretic feature selection,\" IEEE Access, vol. 14, pp. 1666-1676, 2026, doi: 10.1109/ACCESS.2025.3618519.")
BASE_SHORT = "Trigui et al. (IEEE Access, 2026)"
API_PORT, WEB_PORT = 8415, 5415
DEMO_EMAIL, DEMO_PASSWORD = "demo@sentinelflow.com", "Demo@1234"
FEATURES = ["received_packets", "received_bytes", "received_packets_per_second", "received_bytes_per_second", "average_received_packet_size",
            "sent_packets", "sent_bytes", "sent_packets_per_second", "sent_bytes_per_second", "average_sent_packet_size"]

# facts of the base paper as printed in it (IEEE Access, vol. 14, 2026)
BP = {
    "datasets": "SDN flow dataset (104,345 records, 23 features) and CIC-DDoS2023 subset (1,754,109 rows, 47 features)",
    "method": "RF + Banzhaf Power Index feature selection; XGBoost, RF, Gradient Boosting, SVM, kNN, AdaBoost, Naive Bayes; four hard-voting ensembles (clf1-clf4)",
    "result": "all four ensembles reach 100 % accuracy, precision, recall and F1 on both datasets",
    "resource": "clf3 and clf4 (SVM) need over 4,000 s to train on the SDN data; clf2 (kNN) needs over 150 s to classify the SDN test set; clf1 is the lightest",
    "future": "multi-class detection, online learning, federated SDN, sidecar next to the controller, live testbeds and production traces",
}


def _load(*p):
    path = os.path.join(*p)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


SHIP = _load(CODE, "results", "metrics.json")                 # shipped model: synthetic fallback + window rows
CMX = _load(CODE, "results", "confusion_matrix.json")["matrix"]
IMP = _load(CODE, "results", "feature_importance.json")
REAL = _load(EXP, "real_cicids2017.json")                      # real CICIDS2017 Friday-DDoS flows
HYB = _load(EXP, "hybrid_recipe.json")                         # product training recipe on real flows + window rows
WIN = _load(EXP, "window_pipeline.json")                       # shipped model through the window pipeline at 2/5/10 s
LAT = _load(EXP, "latency.json")
API = _load(EXP, "api_measurements.json")

# measured by the test runs (docs/metrics/*.txt) - updated after the final run
PYTEST_TOTAL, PYTEST_PASSED = 95, 95
SMOKE_TOTAL, SMOKE_PASSED = 25, 25   # backend checks of scripts/smoke_test.py (3 frontend-proxy checks need the Vite server)


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def mstd(m, s, d=2):
    return f"{m * 100:.{d}f} ± {s * 100:.{d}f}"


def shot(name):
    return os.path.join(SHOTS, name)


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)


def shot_w(path, base=5.6, max_h_in=6.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, max_h_in * w / h)


def K():
    """Derived headline numbers used by several documents (so every document quotes the same value)."""
    s, r = SHIP, REAL
    fpr_ship = CMX[0][1] / (CMX[0][0] + CMX[0][1])
    w2, w5, w10 = WIN["window_2s"], WIN["window_5s"], WIN["window_10s"]
    return {
        "ship_acc": s["accuracy"], "ship_prec": s["precision"], "ship_rec": s["recall"], "ship_f1": s["f1"], "ship_auc": s["roc_auc"], "ship_fpr": fpr_ship,
        "ship_n_test": s["test_samples"], "ship_n_train": s["train_samples"], "ship_fp": CMX[0][1], "ship_fn": CMX[1][0],
        "real_rows": r["rows"], "real_benign": r["benign"], "real_attack": r["attack"],
        "shipreal_acc": r["shipped_on_real_all"]["accuracy"], "shipreal_rec": r["shipped_on_real_all"]["recall"], "shipreal_prec": r["shipped_on_real_all"]["precision"],
        "shipreal_f1": r["shipped_on_real_all"]["f1"], "shipreal_fpr": r["shipped_on_real_all"]["fpr"], "shipreal_auc": r["shipped_on_real_all"]["roc_auc"],
        "rr_acc": (r["real_rf_accuracy_mean"], r["real_rf_accuracy_std"]), "rr_f1": (r["real_rf_f1_mean"], r["real_rf_f1_std"]),
        "rr_rec": (r["real_rf_recall_mean"], r["real_rf_recall_std"]), "rr_prec": (r["real_rf_precision_mean"], r["real_rf_precision_std"]),
        "rr_fpr": (r["real_rf_fpr_mean"], r["real_rf_fpr_std"]),
        "blk_acc": r["real_rf_block_split"]["accuracy"], "blk_fpr": r["real_rf_block_split"]["fpr"], "blk_rec": r["real_rf_block_split"]["recall"],
        "w2_fpr_ml": w2["ml_only"]["fpr"], "w5_fpr_ml": w5["ml_only"]["fpr"], "w10_fpr_ml": w10["ml_only"]["fpr"],
        "w2_fpr_act": w2["actionable_high_or_critical"]["fpr"], "w5_fpr_act": w5["actionable_high_or_critical"]["fpr"], "w10_fpr_act": w10["actionable_high_or_critical"]["fpr"],
        "w2_rec_act": w2["actionable_high_or_critical"]["recall"], "w5_rec_act": w5["actionable_high_or_critical"]["recall"], "w10_rec_act": w10["actionable_high_or_critical"]["recall"],
        "hyb_mixed_acc": HYB["mixed_test"]["accuracy"], "hyb_real_acc": HYB["hybrid_on_real_all_flows"]["accuracy"],
    }
