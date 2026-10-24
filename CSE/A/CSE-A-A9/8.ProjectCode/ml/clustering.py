"""F5 - botnet clusters: Louvain community detection over the learned embeddings.

Candidates are the accounts the model finds suspicious (probability >= CANDIDATE_PROB). They are linked by
  * embedding similarity - each candidate to its K most cosine-similar candidates, and
  * a real interaction edge - when two candidates are connected in the platform graph.
Louvain then groups the weighted candidate graph. Groups smaller than MIN_CLUSTER are dropped.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

from . import config as C


def detect(emb: np.ndarray, prob: np.ndarray, edge_index: np.ndarray, seed: int = 0) -> list[np.ndarray]:
    cand = np.where(prob >= C.CANDIDATE_PROB)[0]
    if len(cand) < C.MIN_CLUSTER:
        return []
    e = emb[cand]
    e = e / np.maximum(np.linalg.norm(e, axis=1, keepdims=True), 1e-9)
    sim = e @ e.T
    np.fill_diagonal(sim, -1)
    k = min(C.KNN, len(cand) - 1)
    nn_idx = np.argpartition(-sim, k - 1, axis=1)[:, :k]
    G = nx.Graph()
    G.add_nodes_from(cand.tolist())
    for a in range(len(cand)):
        for b in nn_idx[a]:
            w = max(float(sim[a, b]), 0.0)
            if w > 0:
                G.add_edge(int(cand[a]), int(cand[b]), weight=w)
    cand_set = set(cand.tolist())
    for u, v in edge_index:
        if int(u) in cand_set and int(v) in cand_set:
            G.add_edge(int(u), int(v), weight=G.get_edge_data(int(u), int(v), {"weight": 0.0})["weight"] + 1.0)
    comms = nx.community.louvain_communities(G, weight="weight", resolution=1.0, seed=seed)
    out = [np.array(sorted(c)) for c in comms if len(c) >= C.MIN_CLUSTER]
    out.sort(key=lambda c: -len(c))
    return out


def describe(members: np.ndarray, accounts: pd.DataFrame, prob: np.ndarray, edge_index: np.ndarray, threshold: float) -> dict:
    """Size, density and the behaviour the members share."""
    a = accounts.iloc[members]
    mset = set(members.tolist())
    internal = int(sum(1 for u, v in edge_index if int(u) in mset and int(v) in mset))
    n = len(members)
    density = internal / (n * (n - 1) / 2) if n > 1 else 0.0
    hours = a["peak_hour"].to_numpy()
    counts = np.bincount(hours, minlength=24)
    # the busiest 3-hour window (circular); its centre is reported as the shared peak hour
    window_counts = [counts[(h - 1) % 24] + counts[h] + counts[(h + 1) % 24] for h in range(24)]
    top_hour = int(np.argmax(window_counts))
    hour_share = float(window_counts[top_hour] / len(hours))
    age = a["account_age_days"].to_numpy()
    created_span = int(np.percentile(age, 90) - np.percentile(age, 10))
    ratio = a["followers"].to_numpy() / np.maximum(a["following"].to_numpy(), 1)
    return {
        "size": int(n),
        "mean_score": float(prob[members].mean()),
        "flagged_share": float((prob[members] >= threshold).mean()),
        "internal_edges": internal,
        "density": float(density),
        "peak_hour": top_hour,
        "peak_hour_share": hour_share,
        "created_span_days": created_span,
        "median_account_age_days": int(np.median(age)),
        "median_posts_per_day": float(a["posts_per_day"].median()),
        "median_interactions_per_week": float(a["interactions_per_week"].median()),
        "median_followers": int(a["followers"].median()),
        "median_follower_ratio": float(np.median(ratio)),
        "no_profile_pic_share": float(1 - a["has_profile_pic"].mean()),
    }


def recovery(clusters: list[np.ndarray], truth: np.ndarray, y: np.ndarray) -> dict:
    """Compare detected clusters with the injected botnets (ground truth known only for synthetic data)."""
    per = []
    n_truth = int(truth.max() + 1)
    for k in range(n_truth):
        gt = set(np.where(truth == k)[0].tolist())
        best, best_overlap = None, 0
        for ci, c in enumerate(clusters):
            ov = len(gt & set(c.tolist()))
            if ov > best_overlap:
                best, best_overlap = ci, ov
        recall = best_overlap / len(gt)
        precision = best_overlap / len(clusters[best]) if best is not None else 0.0
        per.append({"botnet": k, "size": len(gt), "matched_cluster": best, "recall": recall, "precision": precision,
                    "recovered": bool(recall >= 0.8 and precision >= 0.8)})
    in_clusters = np.concatenate(clusters) if clusters else np.array([], dtype=int)
    purity = float(np.mean(y[in_clusters])) if len(in_clusters) else 0.0
    return {
        "botnets": n_truth, "recovered": int(sum(p["recovered"] for p in per)),
        "mean_recall": float(np.mean([p["recall"] for p in per])),
        "mean_precision": float(np.mean([p["precision"] for p in per])),
        "clusters_found": len(clusters), "fake_purity": purity, "per_botnet": per,
    }
