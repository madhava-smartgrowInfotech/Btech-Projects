"""Machine-learning traffic prediction: forecast each approach's queue 30 s ahead."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from .sim import Sim

HORIZON = 30


def build_dataset(seeds=(1, 2, 3, 4, 5, 6), seconds=1800, demands=(0.7, 1.0, 1.3, 1.6)):
    X, y = [], []
    for k, s in enumerate(seeds):
        rows, cols = (2, 2) if k % 2 == 0 else (3, 3)
        sim = Sim(rows, cols, "adaptive", demands[k % len(demands)], seed=100 + s,
                  start_hour=[7.0, 8.0, 12.0, 17.0][k % 4], emergencies=False, violations=False)
        snaps = []
        for t in range(seconds):
            sim.step()
            if t >= 40 and t % 10 == 0:
                snaps.append((t, sim.feature_matrix()))
        for t, F in snaps:
            if t + HORIZON < seconds:
                X.append(F)
                y.append(sim.qhist[t + HORIZON].reshape(-1))
    return np.vstack(X), np.concatenate(y)


class QueuePredictor:
    """Gradient-boosted regressor with RandomForest and persistence baselines."""

    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=160, max_depth=4, learning_rate=0.08,
                                               subsample=0.9, random_state=0)
        self.metrics = {}
        self.test = None

    def fit(self, X=None, y=None):
        if X is None:
            X, y = build_dataset()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=1)
        self.model.fit(Xtr, ytr)
        rf = RandomForestRegressor(n_estimators=80, max_depth=10, random_state=0, n_jobs=-1).fit(Xtr, ytr)
        pred_gb, pred_rf, persist = self.model.predict(Xte), rf.predict(Xte), Xte[:, 0]
        self.metrics = {
            "Persistence baseline": (mean_absolute_error(yte, persist), r2_score(yte, persist)),
            "Random Forest": (mean_absolute_error(yte, pred_rf), r2_score(yte, pred_rf)),
            "Gradient Boosting (used)": (mean_absolute_error(yte, pred_gb), r2_score(yte, pred_gb)),
        }
        self.test = (yte, pred_gb)
        self.importance = dict(zip(Sim.FEATURES, self.model.feature_importances_))
        self.n_samples = len(y)
        return self

    def predict(self, X):
        return np.clip(self.model.predict(X), 0, 40)
