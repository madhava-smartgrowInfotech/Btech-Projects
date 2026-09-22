"""A small PyTorch MLP with a scikit-learn style interface (fit / predict_proba), picklable with joblib."""
from __future__ import annotations

import copy
import io

import numpy as np


class TorchMLPClassifier:
    def __init__(self, hidden: tuple[int, ...] = (64, 32), dropout: float = 0.1, epochs: int = 25,
                 batch_size: int = 1024, lr: float = 2e-3, weight_decay: float = 1e-4,
                 class_weight: str | None = "balanced", patience: int = 4, seed: int = 42):
        self.hidden = hidden
        self.dropout = dropout
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.weight_decay = weight_decay
        self.class_weight = class_weight
        self.patience = patience
        self.seed = seed
        self.classes_ = None
        self.history_: list[dict] = []
        self._net = None
        self._mean = None
        self._std = None

    # -- preprocessing: standardise, then missing values become 0 (= the mean); has_* features carry missingness
    def _prep(self, X) -> np.ndarray:
        X = np.asarray(X, dtype=np.float32)
        Z = (X - self._mean) / self._std
        return np.nan_to_num(Z, nan=0.0).astype(np.float32)

    def _build(self, n_in: int, n_out: int):
        import torch.nn as nn

        layers, prev = [], n_in
        for h in self.hidden:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(self.dropout)]
            prev = h
        layers.append(nn.Linear(prev, n_out))
        return nn.Sequential(*layers)

    def fit(self, X, y, X_val=None, y_val=None, log=print):
        import torch
        import torch.nn as nn
        from sklearn.metrics import f1_score

        torch.manual_seed(self.seed)
        rng = np.random.default_rng(self.seed)
        X = np.asarray(X, dtype=np.float32)
        y = np.array(y, dtype=np.int64, copy=True)
        self.classes_ = np.unique(y)
        self._mean = np.nanmean(X, axis=0)
        self._std = np.nanstd(X, axis=0)
        self._mean = np.nan_to_num(self._mean, nan=0.0).astype(np.float32)
        self._std = np.where(np.nan_to_num(self._std, nan=0.0) < 1e-6, 1.0, self._std).astype(np.float32)
        Xt = torch.from_numpy(self._prep(X))
        yt = torch.from_numpy(y)

        weights = None
        if self.class_weight == "balanced":
            counts = np.bincount(y, minlength=len(self.classes_)).astype(np.float32)
            weights = torch.tensor(len(y) / (len(self.classes_) * np.maximum(counts, 1)), dtype=torch.float32)
        self._net = self._build(X.shape[1], len(self.classes_))
        opt = torch.optim.AdamW(self._net.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        loss_fn = nn.CrossEntropyLoss(weight=weights)

        best_f1, best_state, stale = -1.0, None, 0
        for epoch in range(1, self.epochs + 1):
            self._net.train()
            order = rng.permutation(len(Xt))
            total = 0.0
            for start in range(0, len(order), self.batch_size):
                batch = torch.from_numpy(order[start:start + self.batch_size])
                opt.zero_grad()
                loss = loss_fn(self._net(Xt[batch]), yt[batch])
                loss.backward()
                opt.step()
                total += loss.item() * len(batch)
            entry = {"epoch": epoch, "train_loss": total / len(Xt)}
            if X_val is not None:
                pred = self.predict(X_val)
                entry["val_macro_f1"] = float(f1_score(y_val, pred, average="macro"))
                if entry["val_macro_f1"] > best_f1 + 1e-4:
                    best_f1, best_state, stale = entry["val_macro_f1"], copy.deepcopy(self._net.state_dict()), 0
                else:
                    stale += 1
            self.history_.append(entry)
            log(f"  epoch {epoch:2d}  loss {entry['train_loss']:.4f}" + (f"  val macro-F1 {entry['val_macro_f1']:.4f}" if "val_macro_f1" in entry else ""))
            if X_val is not None and stale >= self.patience:
                log(f"  early stop (best val macro-F1 {best_f1:.4f})")
                break
        if best_state is not None:
            self._net.load_state_dict(best_state)
        return self

    def predict_proba(self, X) -> np.ndarray:
        import torch

        self._net.eval()
        with torch.no_grad():
            logits = self._net(torch.from_numpy(self._prep(X)))
            return torch.softmax(logits, dim=1).numpy()

    def predict(self, X) -> np.ndarray:
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]

    # -- pickling: store the weights as bytes so joblib files load without the training process
    def __getstate__(self):
        import torch

        state = self.__dict__.copy()
        if self._net is not None:
            buf = io.BytesIO()
            torch.save(self._net.state_dict(), buf)
            state["_net"] = buf.getvalue()
            state["_n_in"] = int(self._mean.shape[0])
        return state

    def __setstate__(self, state):
        import torch

        raw = state.get("_net")
        self.__dict__.update(state)
        if isinstance(raw, (bytes, bytearray)):
            self._net = self._build(state["_n_in"], len(self.classes_))
            self._net.load_state_dict(torch.load(io.BytesIO(raw), weights_only=True))
            self._net.eval()
