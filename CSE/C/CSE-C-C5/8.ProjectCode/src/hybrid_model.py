"""Hybrid XGBoost + kNN residual refinement (base paper Sec 3.5-3.6).
Baselines + calibration (Platt/sigmoid) + evaluation + SHAP + PCA plots.
"""
import os, json, pickle, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (accuracy_score, roc_auc_score, f1_score,
                             precision_score, recall_score, brier_score_loss)
from sklearn.decomposition import PCA
from xgboost import XGBClassifier

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except Exception:
    HAS_LGBM = False

from preprocess import load_raw, build_features, save_artifacts

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE, "models")
STATIC_DIR = os.path.join(BASE, "static")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
SEED = 42


def metrics(y, p, prob):
    return {
        "accuracy": round(float(accuracy_score(y, p)), 4),
        "roc_auc": round(float(roc_auc_score(y, prob)), 4),
        "f1": round(float(f1_score(y, p)), 4),
        "precision": round(float(precision_score(y, p)), 4),
        "recall": round(float(recall_score(y, p)), 4),
    }


def main():
    df, comp = load_raw()
    # stratified 70/15/15 like paper
    train_df, temp = train_test_split(df, test_size=0.30, stratify=df["Placed"], random_state=SEED)
    val_df, test_df = train_test_split(temp, test_size=0.50, stratify=temp["Placed"], random_state=SEED)
    print(f"train {len(train_df)} val {len(val_df)} test {len(test_df)}")

    Xtr, feats, fm, sc = build_features(train_df, comp, fit=True)
    save_artifacts(fm, sc, feats)
    Xval, _, _, _ = build_features(val_df, comp, freq_maps=fm, scaler_stats=sc)
    Xte, _, _, _ = build_features(test_df, comp, freq_maps=fm, scaler_stats=sc)
    ytr, yval, yte = train_df["Placed"].values, val_df["Placed"].values, test_df["Placed"].values

    # --- baselines (Table 4 equivalent) ---
    models = {
        "logreg": LogisticRegression(max_iter=1000, random_state=SEED),
        "tree": DecisionTreeClassifier(random_state=SEED),
        "rf": RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1),
        "svm": SVC(kernel="rbf", probability=True, random_state=SEED),
        "knn": KNeighborsClassifier(n_neighbors=9, weights="uniform"),
        "xgb": XGBClassifier(n_estimators=100, max_depth=8, learning_rate=0.1,
                             subsample=0.8, colsample_bytree=0.8,
                             reg_alpha=0.1, reg_lambda=1.0,
                             eval_metric="logloss", random_state=SEED, n_jobs=-1),
    }
    if HAS_LGBM:
        models["lgbm"] = LGBMClassifier(n_estimators=200, random_state=SEED, verbose=-1)

    results = {}
    fitted = {}
    for name, m in models.items():
        m.fit(Xtr, ytr)
        prob = m.predict_proba(Xte)[:, 1]
        pred = (prob >= 0.5).astype(int)
        results[name] = metrics(yte, pred, prob)
        fitted[name] = m
        print(name, results[name])

    # 9-fold CV for XGBoost (paper protocol)
    cv = StratifiedKFold(n_splits=9, shuffle=True, random_state=SEED)
    cv_acc = cross_val_score(fitted["xgb"], Xtr, ytr, cv=cv, scoring="accuracy").mean()
    print(f"xgb 9-fold CV accuracy: {cv_acc:.4f}")

    # --- calibration: Platt (sigmoid) like paper Table 6 ---
    base_xgb = models["xgb"]
    calib = CalibratedClassifierCV(base_xgb, method="sigmoid", cv=3)
    calib.fit(Xtr, ytr)
    pxgb = calib.predict_proba(Xte)[:, 1]
    pred_xgb = (pxgb >= 0.5).astype(int)
    brier = float(brier_score_loss(yte, pxgb))
    print(f"calibrated XGB brier={brier:.4f}")
    results["xgb_calibrated"] = metrics(yte, pred_xgb, pxgb)

    # --- hybrid residual refinement ---
    # R = misclassified OR prob in [0.4, 0.6]  (Eq.1 paper)
    residual_mask = (pred_xgb != yte) | ((pxgb >= 0.4) & (pxgb <= 0.6))
    print(f"residual rate on test: {residual_mask.mean():.3f}")

    knn_res = KNeighborsClassifier(n_neighbors=9, weights="uniform")
    knn_res.fit(Xtr, ytr)  # local model trained globally, applied locally (paper Fig.8)
    svm_res = SVC(kernel="rbf", probability=True, random_state=SEED)
    svm_res.fit(Xtr, ytr)

    def hybrid(pred_base, prob_base, local_pred):
        out = pred_base.copy()
        out[residual_mask] = local_pred[residual_mask]
        # for AUC use blended prob: keep base prob except residuals use local prob
        return out

    pknn = knn_res.predict(Xte)
    psvm = svm_res.predict(Xte)
    prob_knn = knn_res.predict_proba(Xte)[:, 1]
    prob_svm = svm_res.predict_proba(Xte)[:, 1]
    hybrid_knn = hybrid(pred_xgb, pxgb, pknn)
    hybrid_svm = hybrid(pred_xgb, pxgb, psvm)
    hprob_knn = pxgb.copy(); hprob_knn[residual_mask] = prob_knn[residual_mask]
    hprob_svm = pxgb.copy(); hprob_svm[residual_mask] = prob_svm[residual_mask]
    results["hybrid_xgb_knn"] = metrics(yte, hybrid_knn, hprob_knn)
    results["hybrid_xgb_svm"] = metrics(yte, hybrid_svm, hprob_svm)
    print("hybrid knn:", results["hybrid_xgb_knn"])
    print("hybrid svm:", results["hybrid_xgb_svm"])

    # save models
    with open(os.path.join(MODEL_DIR, "xgb_calibrated.pkl"), "wb") as f:
        pickle.dump(calib, f)
    with open(os.path.join(MODEL_DIR, "knn_residual.pkl"), "wb") as f:
        pickle.dump(knn_res, f)
    with open(os.path.join(MODEL_DIR, "svm_residual.pkl"), "wb") as f:
        pickle.dump(svm_res, f)
    with open(os.path.join(MODEL_DIR, "companies.pkl"), "wb") as f:
        pickle.dump(comp, f)
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump({"results": results, "cv_xgb_9fold": round(float(cv_acc), 4),
                   "brier_platt": round(brier, 4), "residual_rate": round(float(residual_mask.mean()), 4),
                   "test_size": len(yte)}, f, indent=2)

    # --- plots: probability histogram (Fig.6) + PCA (Fig.7) ---
    plt.figure(figsize=(7, 4))
    plt.hist(pxgb, bins=25, color="#2563eb", alpha=0.8)
    plt.xlabel("Predicted placement probability"); plt.ylabel("Count")
    plt.title("Predicted placement probabilities (test set)")
    plt.tight_layout(); plt.savefig(os.path.join(STATIC_DIR, "prob_hist.png")); plt.close()

    pca = PCA(n_components=2, random_state=SEED)
    Z = pca.fit_transform(Xte)
    correct_acc = (hybrid_knn == 1) & (yte == 1)
    correct_rej = (hybrid_knn == 0) & (yte == 0)
    wrong = hybrid_knn != yte
    plt.figure(figsize=(7, 5))
    plt.scatter(Z[correct_rej, 0], Z[correct_rej, 1], s=12, label="Correct Rejected", alpha=0.7)
    plt.scatter(Z[correct_acc, 0], Z[correct_acc, 1], s=12, label="Correct Placed", alpha=0.7)
    plt.scatter(Z[wrong, 0], Z[wrong, 1], s=18, label="Misclassified", alpha=0.9)
    plt.xlabel("PC1"); plt.ylabel("PC2"); plt.title("PCA of test set (hybrid predictions)")
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, "pca.png")); plt.close()

    # --- SHAP (Fig.9/10 equivalent, lightweight: TreeExplainer sample) ---
    try:
        import shap
        bg = Xtr[np.random.default_rng(SEED).choice(len(Xtr), min(200, len(Xtr)), replace=False)]
        ex = shap.TreeExplainer(fitted["xgb"])
        sv = ex.shap_values(Xte[:200])
        mean_abs = np.abs(sv).mean(0)
        order = np.argsort(mean_abs)
        plt.figure(figsize=(7, 5))
        plt.barh([feats[i] for i in order], mean_abs[order], color="#059669")
        plt.title("Mean |SHAP| feature importance"); plt.tight_layout()
        plt.savefig(os.path.join(STATIC_DIR, "shap.png")); plt.close()
        print("SHAP saved")
    except Exception as e:
        print("SHAP skipped:", e)

    print("DONE. See models/metrics.json")


if __name__ == "__main__":
    main()
