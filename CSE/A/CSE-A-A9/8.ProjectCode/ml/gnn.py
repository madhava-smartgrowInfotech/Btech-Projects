"""F3 - GCN, GAT and GraphSAGE written directly against sparse tensors (no torch-geometric)."""
from __future__ import annotations

import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import config as C

torch.set_num_threads(max(1, min(4, torch.get_num_threads())))


class Graph:
    """Everything the layers need, built once from an undirected edge list (i < j)."""

    def __init__(self, n: int, edge_index: np.ndarray):
        src = np.concatenate([edge_index[:, 0], edge_index[:, 1]])
        dst = np.concatenate([edge_index[:, 1], edge_index[:, 0]])
        self.n = n
        self.src = torch.as_tensor(src, dtype=torch.long)
        self.dst = torch.as_tensor(dst, dtype=torch.long)
        loops = torch.arange(n)
        self.src_sl = torch.cat([self.src, loops])
        self.dst_sl = torch.cat([self.dst, loops])
        deg = torch.bincount(self.dst_sl, minlength=n).float()
        w = (deg[self.src_sl] * deg[self.dst_sl]).rsqrt()
        self.a_hat = torch.sparse_coo_tensor(torch.stack([self.dst_sl, self.src_sl]), w, (n, n)).coalesce()
        deg0 = torch.bincount(self.dst, minlength=n).clamp(min=1).float()
        self.a_mean = torch.sparse_coo_tensor(torch.stack([self.dst, self.src]), 1.0 / deg0[self.dst], (n, n)).coalesce()


class GCNLayer(nn.Module):
    def __init__(self, i, o):
        super().__init__()
        self.lin = nn.Linear(i, o)

    def forward(self, x, g: Graph):
        return torch.sparse.mm(g.a_hat, self.lin(x))


class SAGELayer(nn.Module):
    def __init__(self, i, o):
        super().__init__()
        self.self_lin = nn.Linear(i, o)
        self.neigh_lin = nn.Linear(i, o, bias=False)

    def forward(self, x, g: Graph):
        return self.self_lin(x) + self.neigh_lin(torch.sparse.mm(g.a_mean, x))


class GATLayer(nn.Module):
    def __init__(self, i, o, heads=4, concat=True, dropout=0.2):
        super().__init__()
        self.h, self.o, self.concat, self.dropout = heads, o, concat, dropout
        self.lin = nn.Linear(i, heads * o, bias=False)
        self.a_src = nn.Parameter(torch.empty(1, heads, o))
        self.a_dst = nn.Parameter(torch.empty(1, heads, o))
        self.bias = nn.Parameter(torch.zeros(heads * o if concat else o))
        nn.init.xavier_uniform_(self.a_src)
        nn.init.xavier_uniform_(self.a_dst)

    def forward(self, x, g: Graph, return_attention=False):
        n = x.shape[0]
        h = self.lin(x).view(n, self.h, self.o)
        s = (h * self.a_src).sum(-1)
        d = (h * self.a_dst).sum(-1)
        e = F.leaky_relu(s[g.src_sl] + d[g.dst_sl], 0.2)                    # [E, heads]
        mx = torch.full((n, self.h), -1e30).scatter_reduce(0, g.dst_sl[:, None].expand_as(e), e, "amax", include_self=True)
        ex = torch.exp(e - mx[g.dst_sl])
        den = torch.zeros(n, self.h).index_add_(0, g.dst_sl, ex)
        alpha = ex / (den[g.dst_sl] + 1e-16)
        alpha = F.dropout(alpha, self.dropout, self.training)
        out = torch.zeros(n, self.h, self.o).index_add_(0, g.dst_sl, h[g.src_sl] * alpha[:, :, None])
        out = out.reshape(n, -1) if self.concat else out.mean(1)
        out = out + self.bias
        return (out, alpha) if return_attention else out


class Net(nn.Module):
    """Two message-passing layers (or two dense layers for the baseline) + a linear classifier head."""

    def __init__(self, arch: str, in_dim: int, hidden: int = C.HIDDEN, dropout: float = C.DROPOUT):
        super().__init__()
        self.arch, self.dropout = arch, dropout
        if arch == "gcn":
            self.l1, self.l2 = GCNLayer(in_dim, hidden), GCNLayer(hidden, hidden)
        elif arch == "sage":
            self.l1, self.l2 = SAGELayer(in_dim, hidden), SAGELayer(hidden, hidden)
        elif arch == "gat":
            self.l1 = GATLayer(in_dim, hidden // 4, heads=4, concat=True, dropout=0.2)
            self.l2 = GATLayer(hidden, hidden, heads=1, concat=False, dropout=0.2)
        elif arch == C.BASELINE:
            self.l1, self.l2 = nn.Linear(in_dim, hidden), nn.Linear(hidden, hidden)
        else:
            raise ValueError(arch)
        self.head = nn.Linear(hidden, 2)

    def _layer(self, layer, x, g):
        return layer(x) if self.arch == C.BASELINE else layer(x, g)

    def forward(self, x, g: Graph):
        h = F.dropout(x, self.dropout, self.training)
        h = F.elu(self._layer(self.l1, h, g))
        h = F.dropout(h, self.dropout, self.training)
        emb = F.elu(self._layer(self.l2, h, g))
        return self.head(F.dropout(emb, self.dropout, self.training)), emb


# --------------------------------------------------------------------------- training / metrics
def class_weights(y_train: np.ndarray) -> torch.Tensor:
    pos = max(1, int(y_train.sum()))
    neg = max(1, len(y_train) - pos)
    return torch.tensor([1.0, float(np.sqrt(neg / pos))], dtype=torch.float32)


def prob_fake(model: Net, x, g) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    with torch.no_grad():
        logits, emb = model(x, g)
    return torch.softmax(logits, 1)[:, 1].numpy(), emb.numpy()


def best_threshold(y: np.ndarray, p: np.ndarray) -> float:
    from sklearn.metrics import f1_score

    grid = np.linspace(0.1, 0.9, 33)
    scores = [f1_score(y, p >= t, zero_division=0) for t in grid]
    return float(grid[int(np.argmax(scores))])


def metrics(y: np.ndarray, p: np.ndarray, thr: float) -> dict:
    from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, f1_score,
                                 precision_score, recall_score, roc_auc_score)

    pred = p >= thr
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y, pred)), "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)), "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
        "threshold": float(thr), "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def train_model(arch: str, x: torch.Tensor, g: Graph, y: np.ndarray, train_idx: np.ndarray, val_idx: np.ndarray,
                seed: int = 0, epochs: int = C.EPOCHS, patience: int = C.PATIENCE, y_train: np.ndarray | None = None):
    """Train with a class-weighted loss, keep the epoch with the best validation F1.

    y_train lets the caller override the labels the loss sees on train_idx (moderator feedback).
    """
    from sklearn.metrics import f1_score

    torch.manual_seed(seed)
    np.random.seed(seed)
    model = Net(arch, x.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=C.LR, weight_decay=C.WEIGHT_DECAY)
    yt = torch.as_tensor(y if y_train is None else y_train, dtype=torch.long)
    tr = torch.as_tensor(train_idx)
    w = class_weights(yt[tr].numpy())
    best, best_state, bad = -1.0, None, 0
    t0 = time.perf_counter()
    for ep in range(epochs):
        model.train()
        opt.zero_grad()
        logits, _ = model(x, g)
        loss = F.cross_entropy(logits[tr], yt[tr], weight=w)
        loss.backward()
        opt.step()
        p, _ = prob_fake(model, x, g)
        f1 = f1_score(y[val_idx], p[val_idx] >= 0.5, zero_division=0)
        if f1 > best:
            best, bad = f1, 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    return model, {"train_seconds": time.perf_counter() - t0, "epochs_run": ep + 1, "best_val_f1_at_0.5": best}


def standardise(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mu, sd = X.mean(0), X.std(0)
    sd[sd < 1e-6] = 1.0
    return ((X - mu) / sd).astype(np.float32), mu.astype(np.float32), sd.astype(np.float32)
