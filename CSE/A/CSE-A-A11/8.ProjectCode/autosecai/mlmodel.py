"""Reproduction of the base-paper pipeline (IEEE Access 2026, Abbasi & Shameli-Sendi).

Pipeline (paper Fig. 1):  metrics -> 7 feature-selection methods -> top-5 consensus features ->
SmoteTomek balancing -> Min-Max normalisation -> 9 ML models (Random Forest wins) ->
vulnerability-type classification.

Everything is implemented with scikit-learn/numpy only (SMOTE-Tomek is implemented here, no imblearn).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.feature_selection import RFE, VarianceThreshold, chi2
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier

from .dataset import build_dataset
from .metrics import FEATURES, FEATURE_LABEL

ART = Path(__file__).parent / "artifacts"
ART.mkdir(exist_ok=True)
BUNDLE = ART / "bundle.joblib"
REPORT = ART / "report.json"
SEED = 42


# ---------------------------------------------------------------- SMOTE + Tomek links
def smote(X, y, k=5, seed=SEED):
    """Balance the minority class by interpolating between a sample and its k nearest neighbours."""
    rng = np.random.default_rng(seed)
    classes, counts = np.unique(y, return_counts=True)
    minority, majority = classes[counts.argmin()], classes[counts.argmax()]
    Xm = X[y == minority]
    need = counts.max() - counts.min()
    if need <= 0 or len(Xm) < 2:
        return X, y
    kk = min(k, len(Xm) - 1)
    nn = NearestNeighbors(n_neighbors=kk + 1).fit(Xm)
    idx = nn.kneighbors(Xm, return_distance=False)[:, 1:]
    base = rng.integers(0, len(Xm), need)
    neigh = idx[base, rng.integers(0, kk, need)]
    gap = rng.random((need, 1))
    synth = Xm[base] + gap * (Xm[neigh] - Xm[base])
    return np.vstack([X, synth]), np.concatenate([y, np.full(need, minority)])


def tomek_clean(X, y):
    """Remove Tomek links: mutual nearest neighbours that belong to different classes (drop the majority one)."""
    nn = NearestNeighbors(n_neighbors=2).fit(X)
    nbr = nn.kneighbors(X, return_distance=False)[:, 1]
    majority = np.bincount(y).argmax()
    drop = set()
    for i, j in enumerate(nbr):
        if nbr[j] == i and y[i] != y[j] and i < j:
            drop.add(i if y[i] == majority else j)
    keep = np.array([i for i in range(len(y)) if i not in drop])
    return X[keep], y[keep], len(drop)


def smote_tomek(X, y):
    Xs, ys = smote(X, y)
    Xc, yc, removed = tomek_clean(Xs, ys)
    return Xc, yc, removed


# ---------------------------------------------------------------- feature selection (7 methods)
def feature_selection(X: pd.DataFrame, y, top=5):
    Xs = pd.DataFrame(MinMaxScaler().fit_transform(X), columns=X.columns)
    scores: dict[str, pd.Series] = {}
    scores["Pearson"] = Xs.apply(lambda c: abs(np.corrcoef(c, y)[0, 1]) if c.std() > 0 else 0)
    svm = LinearSVC(C=0.5, max_iter=5000, dual=False, class_weight="balanced").fit(Xs, y)
    scores["SVM"] = pd.Series(np.abs(svm.coef_[0]), index=X.columns)
    scores["Lasso"] = pd.Series(np.abs(Lasso(alpha=0.005, max_iter=5000).fit(Xs, y).coef_), index=X.columns)
    scores["Chi-Squared"] = pd.Series(np.nan_to_num(chi2(Xs, y)[0]), index=X.columns)
    for name, est in (("RFE-LogReg", LogisticRegression(max_iter=2000, class_weight="balanced")),
                      ("RFE-RandomForest", RandomForestClassifier(80, random_state=SEED, class_weight="balanced"))):
        rfe = RFE(est, n_features_to_select=top).fit(Xs, y)
        scores[name] = pd.Series(1.0 / rfe.ranking_, index=X.columns)
    scores["VarianceThreshold"] = pd.Series(VarianceThreshold().fit(Xs).variances_, index=X.columns)
    table = pd.DataFrame(scores)
    votes = pd.Series(0, index=X.columns)
    ranks = pd.DataFrame(index=X.columns)
    for c in table:
        r = table[c].rank(ascending=False, method="first")
        ranks[c] = r
        votes[r <= top] += 1
    order = pd.DataFrame({"votes": votes, "mean_rank": ranks.mean(axis=1)}).sort_values(
        ["votes", "mean_rank"], ascending=[False, True])
    selected = list(order.index[:top])
    return selected, table, order


# ---------------------------------------------------------------- models
def model_zoo():
    rf = RandomForestClassifier(300, random_state=SEED, n_jobs=-1)
    models = {
        "Random Forest": rf,
        "Decision Tree": DecisionTreeClassifier(random_state=SEED, max_depth=12),
        "Logistic Regression": LogisticRegression(max_iter=2000),
        "SVM (RBF)": SVC(probability=True, random_state=SEED),
        "KNN": KNeighborsClassifier(7),
        "Naive Bayes": GaussianNB(),
        "Gradient Boosting": GradientBoostingClassifier(random_state=SEED),
    }
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=.1, eval_metric="logloss",
                                          random_state=SEED, verbosity=0)
    except Exception:  # xgboost optional
        pass
    models["Voting Ensemble"] = VotingClassifier(
        [("rf", RandomForestClassifier(200, random_state=SEED)), ("gb", GradientBoostingClassifier(random_state=SEED)),
         ("lr", LogisticRegression(max_iter=2000))], voting="soft")
    return models


def train_all(n=6000, progress=None) -> dict:
    t0 = time.time()
    df = build_dataset(n=n)
    X, y = df[FEATURES], df["vulnerable"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)

    _, fs_table, fs_order = feature_selection(Xtr, ytr, top=5)
    # paper uses the top-5 consensus features; we also validate k (5..14) on a held-out slice of the
    # training data and keep the best k, reporting the k=5 configuration in the ablation table.
    Xa, Xv_, ya, yv_ = train_test_split(Xtr, ytr, test_size=0.25, stratify=ytr, random_state=SEED)
    k_scores = {}
    for k in range(5, len(FEATURES) + 1):
        cols = list(fs_order.index[:k])
        sc = MinMaxScaler().fit(Xa[cols])
        Xb, yb, _ = smote_tomek(sc.transform(Xa[cols]), ya)
        m_ = RandomForestClassifier(150, random_state=SEED, n_jobs=-1).fit(Xb, yb)
        k_scores[k] = float(f1_score(yv_, m_.predict(sc.transform(Xv_[cols]))))
    best_k = max(k_scores, key=lambda k: (k_scores[k], -k))
    selected = list(fs_order.index[:best_k])
    paper_sel = list(fs_order.index[:5])
    scaler = MinMaxScaler().fit(Xtr[selected])
    Xtr_s, Xte_s = scaler.transform(Xtr[selected]), scaler.transform(Xte[selected])
    Xbal, ybal, removed = smote_tomek(Xtr_s, ytr)

    results, roc, cms, fitted = {}, {}, {}, {}
    for name, model in model_zoo().items():
        if progress:
            progress(f"Training {name}")
        model.fit(Xbal, ybal)
        pred = model.predict(Xte_s)
        proba = model.predict_proba(Xte_s)[:, 1]
        results[name] = dict(accuracy=accuracy_score(yte, pred), precision=precision_score(yte, pred, zero_division=0),
                             recall=recall_score(yte, pred), f1=f1_score(yte, pred), auc=roc_auc_score(yte, proba))
        fpr, tpr, _ = roc_curve(yte, proba)
        roc[name] = dict(fpr=fpr[::max(1, len(fpr) // 60)].tolist(), tpr=tpr[::max(1, len(tpr) // 60)].tolist())
        cms[name] = confusion_matrix(yte, pred).tolist()
        fitted[name] = model
    best = max(results, key=lambda k: results[k]["f1"])

    # baseline without balancing/feature selection: shows what SmoteTomek + selection buys
    base = RandomForestClassifier(300, random_state=SEED, n_jobs=-1).fit(Xtr, ytr)
    bp = base.predict(Xte)
    sc5 = MinMaxScaler().fit(Xtr[paper_sel])
    X5, y5, _ = smote_tomek(sc5.transform(Xtr[paper_sel]), ytr)
    rf5 = RandomForestClassifier(300, random_state=SEED, n_jobs=-1).fit(X5, y5)
    p5 = rf5.predict(sc5.transform(Xte[paper_sel]))

    def _abl(pred):
        return dict(recall=recall_score(yte, pred), precision=precision_score(yte, pred, zero_division=0),
                    f1=f1_score(yte, pred))
    ablation = {
        "RF - all 14 metrics, no balancing": _abl(bp),
        "RF - top-5 metrics + SmoteTomek (paper setting)": _abl(p5),
        f"RF - top-{best_k} metrics + SmoteTomek (this system)": {k: results["Random Forest"][k] for k in ("recall", "precision", "f1")},
    }

    # ----- vulnerability-type classifier (paper: type detection) on the 14 metrics
    vd = df[df["vulnerable"] == 1]
    Xv, yv = vd[FEATURES], vd["vuln_type"]
    Xv_tr, Xv_te, yv_tr, yv_te = train_test_split(Xv, yv, test_size=0.25, stratify=yv, random_state=SEED)
    type_clf = RandomForestClassifier(400, random_state=SEED, class_weight="balanced", n_jobs=-1).fit(Xv_tr, yv_tr)
    tp = type_clf.predict(Xv_te)
    type_report = classification_report(yv_te, tp, output_dict=True, zero_division=0)
    type_acc = accuracy_score(yv_te, tp)
    type_imp = pd.Series(type_clf.feature_importances_, index=FEATURES).sort_values(ascending=False)

    rf = fitted["Random Forest"]
    imp = pd.Series(rf.feature_importances_, index=selected)
    safe_stats = Xtr[ytr == 0].agg(["mean", "std"]).T
    bundle = dict(features=selected, scaler=scaler, model=fitted[best], best_name=best, rf=rf, type_clf=type_clf,
                  importance=imp.to_dict(), safe_stats=safe_stats.to_dict(), all_features=FEATURES)
    joblib.dump(bundle, BUNDLE)

    report = dict(
        n_functions=int(len(df)), n_vulnerable=int(y.sum()), class_ratio=float(y.mean()),
        train_size=int(len(ytr)), test_size=int(len(yte)), balanced_train_size=int(len(ybal)),
        tomek_removed=int(removed), selected=selected, best_k=int(best_k), k_scores=k_scores,
        selected_labels=[FEATURE_LABEL[s] for s in selected],
        fs_scores=fs_table.round(4).to_dict(), fs_order=fs_order.round(3).to_dict(),
        results=results, best=best, roc=roc, confusion=cms, ablation=ablation,
        importance={FEATURE_LABEL[k]: float(v) for k, v in imp.sort_values(ascending=False).items()},
        type_accuracy=float(type_acc), type_report={k: v for k, v in type_report.items() if k not in ("accuracy",)},
        type_importance={FEATURE_LABEL[k]: float(v) for k, v in type_imp.head(8).items()},
        type_counts=vd["vuln_type"].value_counts().to_dict(),
        seconds=round(time.time() - t0, 1),
        corr=df[FEATURES].corr().round(3).to_dict(),
    )
    REPORT.write_text(json.dumps(report, default=float))
    df.drop(columns=["source"]).to_csv(ART / "dataset_metrics.csv", index=False)
    df.sample(min(40, len(df)), random_state=1)[["source", "vulnerable", "vuln_type"]].to_csv(ART / "dataset_samples.csv", index=False)
    return report


_cache: dict = {}


def load_bundle():
    if "b" not in _cache:
        if not BUNDLE.exists():
            train_all()
        _cache["b"] = joblib.load(BUNDLE)
    return _cache["b"]


def load_report() -> dict:
    if not REPORT.exists():
        train_all()
    return json.loads(REPORT.read_text())


def predict_metrics(m: dict) -> dict:
    """Score one function's metric dict -> probability, predicted type, and the metrics driving the score."""
    b = load_bundle()
    feats = b["features"]
    x = np.array([[m[f] for f in feats]], dtype=float)
    p = float(b["model"].predict_proba(b["scaler"].transform(pd.DataFrame(x, columns=feats)))[0, 1])
    stats = b["safe_stats"]
    contrib = []
    for f in feats:
        sd = stats["std"][f] or 1.0
        z = (m[f] - stats["mean"][f]) / sd
        contrib.append((f, float(b["importance"][f] * max(z, 0)), float(m[f]), float(stats["mean"][f])))
    contrib.sort(key=lambda t: -t[1])
    vtype = None
    if p >= 0.5:
        row = pd.DataFrame([[m[f] for f in b["all_features"]]], columns=b["all_features"])
        proba = b["type_clf"].predict_proba(row)[0]
        vtype = str(b["type_clf"].classes_[int(proba.argmax())])
    return dict(probability=p, vuln_type=vtype,
                drivers=[dict(feature=FEATURE_LABEL[f], contribution=c, value=v, safe_mean=mu)
                         for f, c, v, mu in contrib[:3] if c > 0])


if __name__ == "__main__":
    r = train_all(progress=print)
    for k, v in r["results"].items():
        print(f"{k:22s} " + "  ".join(f"{a}={b:.3f}" for a, b in v.items()))
    print("selected:", r["selected_labels"])
    print("type acc:", r["type_accuracy"], "seconds", r["seconds"])
    print(r["ablation"])
