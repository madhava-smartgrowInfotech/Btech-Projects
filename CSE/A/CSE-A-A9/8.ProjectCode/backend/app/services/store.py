"""In-memory view of the trained artifacts: graph, scores, clusters, metrics, explanations."""
from __future__ import annotations

import json
import sys
import threading
from functools import lru_cache

import numpy as np
import pandas as pd
import torch

from ..settings import ROOT

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml import config as C  # noqa: E402
from ml import data as D  # noqa: E402
from ml import gnn  # noqa: E402

DATASETS = [
    {"name": "Social circles: Facebook (SNAP)", "role": "Real social-graph topology", "licence": "Public research data",
     "used_for": "All real nodes and ties (ten ego networks, merged)", "real": True},
    {"name": "Instagram fake, spammer and genuine accounts", "role": "Labelled profile attributes", "licence": "CC BY 3.0",
     "used_for": "Profile metadata of every account (resampled, jittered)", "real": True},
    {"name": "Twitter Bot Detection Dataset", "role": "Posting behaviour rows", "licence": "CC0",
     "used_for": "Retweets, mentions, post length, hashtags, account age", "real": True},
    {"name": "Injected botnets (seeded script)", "role": "Ground truth for cluster detection", "licence": "Generated",
     "used_for": "8 coordinated bot clusters + 150 lone spammers, temporal and interaction features, handles", "real": False},
]


class Store:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.reload()

    # ------------------------------------------------------------------ loading
    def reload(self) -> None:
        with self.lock:
            g = D.load()
            sc = np.load(C.MODELS / "scores.npz")
            meta = json.loads((C.MODELS / "meta.json").read_text())
            self.g = g
            self.n = len(g["y"])
            self.meta = meta
            self.best = meta["best"]
            self.thr = float(meta["threshold"])
            self.mu, self.sd = sc["mu"], sc["sd"]
            self.probs = {m: sc[f"p_{m}"] for m in C.ALL_MODELS}
            self.score = self.probs[self.best]
            self.emb = sc["emb"]
            self.clusters = json.loads((C.MODELS / "clusters.json").read_text())
            self.cluster_by_id = {c["id"]: c for c in self.clusters}
            self.member_cluster: dict[int, str] = {}
            for c in self.clusters:
                for m in c["members"]:
                    self.member_cluster[m] = c["id"]
            full = C.EXPERIMENTS / "metrics.json"
            self.metrics = json.loads(full.read_text()) if full.exists() else None
            rt = C.EXPERIMENTS / "metrics_retrain.json"
            self.metrics_retrain = json.loads(rt.read_text()) if rt.exists() else None
            sca = C.EXPERIMENTS / "scalability.json"
            self.scalability = json.loads(sca.read_text()) if sca.exists() else None
            ei = g["edge_index"]
            both = np.concatenate([np.stack([ei[:, 0], ei[:, 1], g["edge_kind"]], 1), np.stack([ei[:, 1], ei[:, 0], g["edge_kind"]], 1)])
            order = np.argsort(both[:, 0], kind="stable")
            self._nbr = both[order, 1]
            self._nbr_kind = both[order, 2]
            self._ptr = np.concatenate([[0], np.cumsum(np.bincount(both[:, 0], minlength=self.n))])
            self.deg = np.diff(self._ptr)
            flagged = self.score >= self.thr
            src = np.concatenate([ei[:, 0], ei[:, 1]])
            dst = np.concatenate([ei[:, 1], ei[:, 0]])
            self.nb_flagged = np.bincount(src, weights=flagged[dst].astype(float), minlength=self.n).astype(int)
            self.nb_mean = np.bincount(src, weights=self.score[dst], minlength=self.n) / np.maximum(self.deg, 1)
            acc = g["accounts"].copy()
            acc["score"] = self.score
            acc["flagged"] = self.score >= self.thr
            acc["cluster_id"] = [self.member_cluster.get(i) for i in range(self.n)]
            self.accounts = acc
            self._model = None
            Store.explain.cache_clear()
            self.graph_summary = D.summary(g)
            self.graph_summary["degree_histogram"] = self._degree_hist()
            self.graph_summary["datasets"] = DATASETS

    def _degree_hist(self) -> list[dict]:
        edges = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 100000]
        out = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (self.deg >= lo) & (self.deg < hi)
            lab = f"{lo}" if hi == lo + 1 else (f"{lo}+" if hi == 100000 else f"{lo}-{hi - 1}")
            out.append({"bin": lab, "genuine": int((m & (self.g['y'] == 0)).sum()), "fake": int((m & (self.g['y'] == 1)).sum())})
        return out

    # ------------------------------------------------------------------ graph helpers
    def neighbours(self, i: int) -> tuple[np.ndarray, np.ndarray]:
        a, b = self._ptr[i], self._ptr[i + 1]
        return self._nbr[a:b], self._nbr_kind[a:b]

    def edge_set(self, nodes: set[int]) -> list[tuple[int, int, int]]:
        out = []
        for u in nodes:
            nb, kd = self.neighbours(u)
            for v, k in zip(nb, kd):
                if int(v) in nodes and u < int(v):
                    out.append((u, int(v), int(k)))
        return out

    def node_brief(self, i: int) -> dict:
        r = self.accounts.iloc[i]
        return {
            "id": int(i), "handle": r["handle"], "score": float(r["score"]), "flagged": bool(r["flagged"]),
            "cluster_id": r["cluster_id"] if isinstance(r["cluster_id"], str) else None,
            "followers": int(r["followers"]), "degree": int(self.deg[i]),
        }

    # ------------------------------------------------------------------ explanation
    def _load_model(self):
        if self._model is None:
            m = gnn.Net(self.best, self.g["X"].shape[1])
            m.load_state_dict(torch.load(C.MODELS / f"{self.best}.pt", map_location="cpu"))
            m.eval()
            self._model = m
            self._graph = gnn.Graph(self.n, self.g["edge_index"])
            self._x = torch.as_tensor(((self.g["X"] - self.mu) / self.sd).astype(np.float32))
        return self._model

    @lru_cache(maxsize=512)
    def explain(self, i: int) -> dict:
        """Gradient x input attribution of the account's fake-vs-genuine logit.

        own     - contribution of the account's own feature values
        network - signed contribution of every other account's features that flow in through message passing
        """
        with self.lock:
            model = self._load_model()
            x = self._x.clone().requires_grad_(True)
            logits, _ = model(x, self._graph)
            margin = logits[i, 1] - logits[i, 0]
            margin.backward()
            contrib = (x.grad * x).detach().numpy()
        own = contrib[i]
        network = float(contrib.sum() - own.sum())
        order = np.argsort(-np.abs(own))[:7]
        top = [{
            "feature": D.FEATURES[j], "label": D.FEATURE_LABELS[D.FEATURES[j]], "group": D.FEATURE_GROUPS[D.FEATURES[j]],
            "value": float(self.g["X"][i, j]), "z": float(self._x[i, j]), "contribution": float(own[j]),
        } for j in order]
        return {"margin": float(margin.item()), "own_total": float(own.sum()), "network": network, "top": top}

    # ------------------------------------------------------------------ lists
    def decisions_map(self, reviews: list) -> dict[int, dict]:
        """Latest decision per account (account decisions and cluster decisions fan out to members)."""
        out: dict[int, dict] = {}
        for r in sorted(reviews, key=lambda r: r.created_at):
            for m in (r.members or []):
                out[int(m)] = {"decision": r.decision, "by": r.target_type, "at": r.created_at.isoformat(), "review_id": r.id}
        return out


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def reload_store() -> Store:
    s = get_store()
    s.reload()
    return s


def accounts_df(s: Store) -> pd.DataFrame:
    return s.accounts
