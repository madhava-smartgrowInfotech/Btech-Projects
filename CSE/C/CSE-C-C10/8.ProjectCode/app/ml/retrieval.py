"""Fused representation + cosine retrieval with class balancing."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from app.config import ALPHA
from app.ml.embeddings import l2norm


def fuse(structured: np.ndarray, text_emb: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    s = np.asarray(structured, dtype=np.float64)
    t = np.asarray(text_emb, dtype=np.float64)
    s = l2norm(s.astype(np.float32)).astype(np.float64)
    t = l2norm(t.astype(np.float32)).astype(np.float64)
    fused = np.hstack([alpha * s, (1.0 - alpha) * t])
    # final L2 normalize so cosine similarity is well-behaved
    n = np.linalg.norm(fused, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (fused / n).astype(np.float32)


def retrieve_similar(target_fused: np.ndarray, train_fused: np.ndarray,
                     train_df: pd.DataFrame, k: int = 50) -> pd.DataFrame:
    sims = cosine_similarity(target_fused.reshape(1, -1), train_fused)[0]
    order = np.argsort(-sims)
    # balanced selection: quotas half/half where possible
    k = int(max(1, min(k, len(order))))
    quota_s = k // 2
    quota_f = k - quota_s
    labels = train_df["label"].to_numpy()
    picked: list[int] = []
    c_s = c_f = 0
    for idx in order:
        lab = int(labels[idx])
        if lab == 1 and c_s < quota_s:
            picked.append(int(idx)); c_s += 1
        elif lab == 0 and c_f < quota_f:
            picked.append(int(idx)); c_f += 1
        if len(picked) >= k:
            break
    # fill remainder if a class ran short
    if len(picked) < k:
        chosen = set(picked)
        for idx in order:
            if int(idx) not in chosen:
                picked.append(int(idx))
                if len(picked) >= k:
                    break
    # sort picked by similarity desc for display
    picked = sorted(picked, key=lambda i: -sims[i])
    out = train_df.iloc[picked].copy()
    out["similarity"] = [float(sims[i]) for i in picked]
    return out
