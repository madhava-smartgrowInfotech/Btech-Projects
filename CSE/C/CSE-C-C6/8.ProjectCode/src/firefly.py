"""Firefly Algorithm for joint feature-selection + MSVM hyperparameter tuning.

Each firefly encodes:
  - binary mask over PCA components (feature selection)
  - log10(C) in [-1, 3], log10(gamma) in [-4, 1]

Brightness (fitness) = stratified 3-fold CV macro-F1 - penalty * selection_ratio.
Class weighting (balanced) is baked into every evaluation to handle
imbalanced fake-news data.
"""
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold, cross_val_score


class FireflyOptimizer:
    def __init__(self, n_fireflies=12, n_generations=15, alpha=0.2, beta0=1.0,
                 gamma=1.0, penalty=0.02, cv=3, random_state=42):
        self.n_fireflies = n_fireflies
        self.n_generations = n_generations
        self.alpha = alpha
        self.beta0 = beta0
        self.gamma = gamma
        self.penalty = penalty
        self.cv = cv
        self.random_state = random_state
        self.history_ = []
        self.best_mask_ = None
        self.best_C_ = 1.0
        self.best_gamma_ = "scale"
        self.best_gamma_val_ = None
        self.best_score_ = -np.inf

    def _decode(self, vec, n_features):
        n = n_features
        mask_sig = 1.0 / (1.0 + np.exp(-vec[:n]))
        mask = mask_sig > 0.5
        if mask.sum() == 0:
            mask[np.argmax(mask_sig)] = True
        logC = float(np.clip(vec[n], -1, 3))
        logG = float(np.clip(vec[n + 1], -4, 1))
        return mask, 10 ** logC, 10 ** logG

    def _fitness(self, vec, X, y):
        n_features = X.shape[1]
        mask, C, g = self._decode(vec, n_features)
        if mask.sum() < 2:
            return 0.0
        clf = SVC(C=C, gamma=g, kernel="rbf", class_weight="balanced",
                  decision_function_shape="ovr")
        cv = StratifiedKFold(n_splits=self.cv, shuffle=True,
                             random_state=self.random_state)
        try:
            scores = cross_val_score(clf, X[:, mask], y, cv=cv,
                                     scoring="f1_macro", n_jobs=-1)
            f1 = float(np.mean(scores))
        except Exception:
            return 0.0
        return f1 - self.penalty * (mask.sum() / n_features)

    def optimize(self, X, y, verbose=False):
        rng = np.random.default_rng(self.random_state)
        n_features = X.shape[1]
        dim = n_features + 2
        # init population: sigmoid-friendly range + hyperparams
        pop = rng.uniform(-1, 1, size=(self.n_fireflies, dim))
        pop[:, n_features] = rng.uniform(-1, 2, size=self.n_fireflies)    # logC
        pop[:, n_features + 1] = rng.uniform(-3, 0, size=self.n_fireflies)  # logG
        brightness = np.array([self._fitness(v, X, y) for v in pop])

        best_idx = int(np.argmax(brightness))
        self.best_score_ = float(brightness[best_idx])
        best_vec = pop[best_idx].copy()

        for gen in range(self.n_generations):
            alpha_t = self.alpha * (0.97 ** gen)  # decay randomness
            for i in range(self.n_fireflies):
                for j in range(self.n_fireflies):
                    if brightness[j] > brightness[i]:
                        r2 = float(np.sum((pop[i] - pop[j]) ** 2))
                        beta = self.beta0 * np.exp(-self.gamma * r2 / dim)
                        step = alpha_t * (rng.random(dim) - 0.5) * 2.0
                        pop[i] = pop[i] + beta * (pop[j] - pop[i]) + step
                        # keep hyperparam dims in range
                        pop[i][n_features] = np.clip(pop[i][n_features], -1, 3)
                        pop[i][n_features + 1] = np.clip(pop[i][n_features + 1], -4, 1)
                        brightness[i] = self._fitness(pop[i], X, y)
            cur_best = int(np.argmax(brightness))
            if brightness[cur_best] > self.best_score_:
                self.best_score_ = float(brightness[cur_best])
                best_vec = pop[cur_best].copy()
            # elitist random walk of worst firefly
            worst = int(np.argmin(brightness))
            pop[worst] = best_vec + alpha_t * (rng.random(dim) - 0.5)
            brightness[worst] = self._fitness(pop[worst], X, y)
            self.history_.append(float(np.max(brightness)))
            if verbose:
                print(f"  [Firefly] gen {gen+1}/{self.n_generations} "
                      f"best={self.best_score_:.4f}")

        mask, C, g = self._decode(best_vec, n_features)
        self.best_mask_ = mask
        self.best_C_ = float(C)
        self.best_gamma_val_ = float(g)
        self.best_gamma_ = float(g)
        return self
