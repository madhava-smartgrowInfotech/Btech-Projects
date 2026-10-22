"""End-to-end pipeline: TF-IDF + stylometric -> scaling -> PCA -> Firefly -> MSVM."""
import time
import numpy as np
import joblib
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.metrics import (accuracy_score, f1_score, classification_report,
                             confusion_matrix)
from sklearn.model_selection import train_test_split

from .preprocessing import clean_text, stylometric_features, LABELS
from .firefly import FireflyOptimizer


class FakeNewsMSVMPipeline:
    def __init__(self, max_tfidf=5000, pca_variance=0.95, pca_max=300,
                 n_fireflies=12, n_generations=15, test_size=0.2,
                 random_state=42):
        self.max_tfidf = max_tfidf
        self.pca_variance = pca_variance
        self.pca_max = pca_max
        self.n_fireflies = n_fireflies
        self.n_generations = n_generations
        self.test_size = test_size
        self.random_state = random_state
        # fitted objects
        self.vectorizer = None
        self.scaler = None
        self.pca = None
        self.optimizer = None
        self.clf = None
        self.stats_ = {}

    def fit(self, raw_texts, y, verbose=True):
        t0 = time.time()
        y = np.asarray(y)
        cleaned = [clean_text(t) for t in raw_texts]
        if verbose:
            print(f"[1/5] Cleaned {len(cleaned)} docs")

        self.vectorizer = TfidfVectorizer(max_features=self.max_tfidf,
                                          ngram_range=(1, 2),
                                          sublinear_tf=True,
                                          min_df=2, max_df=0.9)
        X_tfidf = self.vectorizer.fit_transform(cleaned)
        X_style = stylometric_features(raw_texts)
        X_full = hstack([X_tfidf, csr_matrix(X_style)]).toarray()
        n_tfidf = X_tfidf.shape[1]
        if verbose:
            print(f"[2/5] Features: TF-IDF={n_tfidf} + stylometric=25 "
                  f"-> total {X_full.shape[1]}")

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_full)

        # PCA — cap components for speed, keep target variance
        pca_full = PCA(random_state=self.random_state)
        pca_full.fit(X_scaled)
        cumvar = np.cumsum(pca_full.explained_variance_ratio_)
        n_keep = int(np.searchsorted(cumvar, self.pca_variance) + 1)
        n_keep = max(10, min(n_keep, self.pca_max, X_scaled.shape[0] - 1,
                             X_scaled.shape[1]))
        self.pca = PCA(n_components=n_keep, random_state=self.random_state)
        X_pca = self.pca.fit_transform(X_scaled)
        if verbose:
            print(f"[3/5] PCA: {X_scaled.shape[1]} -> {n_keep} "
                  f"(var={self.pca.explained_variance_ratio_.sum():.3f})")

        Xtr, Xte, ytr, yte = train_test_split(
            X_pca, y, test_size=self.test_size, stratify=y,
            random_state=self.random_state)

        # Firefly feature selection + hyperparameter tuning on train split
        if verbose:
            print(f"[4/5] Firefly optimising "
                  f"({self.n_fireflies} fireflies x {self.n_generations} gens)...")
        self.optimizer = FireflyOptimizer(
            n_fireflies=self.n_fireflies, n_generations=self.n_generations,
            random_state=self.random_state)
        self.optimizer.optimize(Xtr, ytr, verbose=verbose)
        mask = self.optimizer.best_mask_
        if verbose:
            print(f"      selected {mask.sum()}/{len(mask)} PCA comps | "
                  f"C={self.optimizer.best_C_:.3f} "
                  f"gamma={self.optimizer.best_gamma_val_:.5f} "
                  f"cv-fit={self.optimizer.best_score_:.4f}")

        # Final MSVM (multi-class SVC, OvR, balanced weights)
        self.clf = SVC(C=self.optimizer.best_C_,
                       gamma=self.optimizer.best_gamma_val_,
                       kernel="rbf", class_weight="balanced",
                       decision_function_shape="ovr", probability=True,
                       random_state=self.random_state)
        self.clf.fit(Xtr[:, mask], ytr)

        # Evaluate + baselines
        t_train = time.time() - t0
        pred = self.clf.predict(Xte[:, mask])
        acc = accuracy_score(yte, pred)
        f1m = f1_score(yte, pred, average="macro")
        # baseline: plain SVM on PCA (no firefly) for the report table
        base = SVC(class_weight="balanced", decision_function_shape="ovr",
                   random_state=self.random_state)
        t_b = time.time()
        base.fit(Xtr, ytr)
        t_b = time.time() - t_b
        bpred = base.predict(Xte)
        self.stats_ = {
            "n_docs": len(y),
            "n_tfidf": n_tfidf,
            "n_total_features": int(X_full.shape[1]),
            "n_pca": int(n_keep),
            "pca_variance": float(self.pca.explained_variance_ratio_.sum()),
            "n_selected": int(mask.sum()),
            "best_C": float(self.optimizer.best_C_),
            "best_gamma": float(self.optimizer.best_gamma_val_),
            "firefly_history": list(self.optimizer.history_),
            "accuracy": float(acc),
            "f1_macro": float(f1m),
            "report": classification_report(yte, pred, target_names=LABELS,
                                            output_dict=True, zero_division=0),
            "report_str": classification_report(yte, pred, target_names=LABELS,
                                                zero_division=0),
            "confusion_matrix": confusion_matrix(yte, pred).tolist(),
            "baseline_accuracy": float(accuracy_score(yte, bpred)),
            "baseline_f1": float(f1_score(yte, bpred, average="macro")),
            "train_time_s": float(t_train),
            "baseline_time_s": float(t_b),
            "y_test": yte.tolist(),
            "y_pred": pred.tolist(),
        }
        if verbose:
            print(f"[5/5] MSVM test acc={acc:.4f} f1-macro={f1m:.4f} "
                  f"(baseline acc={self.stats_['baseline_accuracy']:.4f}) "
                  f"in {t_train:.1f}s")
        return self

    def transform(self, raw_texts):
        cleaned = [clean_text(t) for t in raw_texts]
        X_tfidf = self.vectorizer.transform(cleaned)
        X_style = stylometric_features(raw_texts)
        from scipy.sparse import hstack as _hs, csr_matrix as _csr
        X_full = _hs([X_tfidf, _csr(X_style)]).toarray()
        X_scaled = self.scaler.transform(X_full)
        return self.pca.transform(X_scaled)

    def predict(self, raw_texts):
        X_pca = self.transform(raw_texts)
        mask = self.optimizer.best_mask_
        ids = self.clf.predict(X_pca[:, mask])
        proba = self.clf.predict_proba(X_pca[:, mask]) if hasattr(
            self.clf, "predict_proba") else None
        return ids, proba

    def save(self, path):
        joblib.dump({"vectorizer": self.vectorizer, "scaler": self.scaler,
                     "pca": self.pca, "optimizer_mask": self.optimizer.best_mask_,
                     "best_C": self.optimizer.best_C_,
                     "best_gamma": self.optimizer.best_gamma_val_,
                     "clf": self.clf, "stats": self.stats_,
                     "params": {"max_tfidf": self.max_tfidf}},
                    path)

    @staticmethod
    def load(path):
        d = joblib.load(path)
        pipe = FakeNewsMSVMPipeline(max_tfidf=d["params"]["max_tfidf"])
        pipe.vectorizer = d["vectorizer"]
        pipe.scaler = d["scaler"]
        pipe.pca = d["pca"]
        pipe.clf = d["clf"]
        pipe.stats_ = d["stats"]
        opt = FireflyOptimizer()
        opt.best_mask_ = d["optimizer_mask"]
        opt.best_C_ = d["best_C"]
        opt.best_gamma_val_ = d["best_gamma"]
        pipe.optimizer = opt
        return pipe
