"""Ranking and classification metrics (numpy only)."""
import numpy as np


def precision_at_k(y, score, k):
    order = np.argsort(-np.asarray(score), kind="stable")[:k]
    return float(np.asarray(y)[order].mean()) if k else 0.0


def recall_at_k(y, score, k):
    y = np.asarray(y)
    order = np.argsort(-np.asarray(score), kind="stable")[:k]
    return float(y[order].sum() / max(y.sum(), 1))


def prf(y, pred):
    y, pred = np.asarray(y).astype(bool), np.asarray(pred).astype(bool)
    tp = int((y & pred).sum())
    fp = int((~y & pred).sum())
    fn = int((y & ~pred).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return dict(precision=round(p, 4), recall=round(r, 4), f1=round(f, 4), tp=tp, fp=fp, fn=fn,
                flagged=int(pred.sum()))


def roc_auc(y, score):
    y, s = np.asarray(y).astype(bool), np.asarray(score, dtype=float)
    npos, nneg = int(y.sum()), int((~y).sum())
    if not npos or not nneg:
        return None
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    sorted_s = s[order]
    i = 0
    while i < len(s):  # average ranks for ties
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return round(float((ranks[y].sum() - npos * (npos + 1) / 2) / (npos * nneg)), 4)


def average_precision(y, score):
    y = np.asarray(y).astype(bool)
    order = np.argsort(-np.asarray(score, dtype=float), kind="stable")
    hits = y[order]
    if not hits.sum():
        return None
    prec = np.cumsum(hits) / (np.arange(len(hits)) + 1)
    return round(float(prec[hits].mean()), 4)


def ranking_report(y, score, ks):
    return dict(
        precision_at_k={str(k): round(precision_at_k(y, score, k), 4) for k in ks},
        recall_at_k={str(k): round(recall_at_k(y, score, k), 4) for k in ks},
        roc_auc=roc_auc(y, score), average_precision=average_precision(y, score))
