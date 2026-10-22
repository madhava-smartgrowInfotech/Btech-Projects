"""Weighted hybrid fusion of semantic + lexical scores (min-max normalized)."""

def _minmax(vals: list[float]) -> list[float]:
    if not vals:
        return []
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return [1.0 for _ in vals]
    return [(v - lo) / (hi - lo) for v in vals]

def fuse(sem_hits, lex_hits, w_sem: float = 0.65, w_lex: float = 0.35, k: int = 15):
    """sem_hits / lex_hits: list of (score, record, idx). Returns ranked list of dicts."""
    sem_scores = {idx: s for s, _, idx in sem_hits}
    lex_scores = {idx: s for s, _, idx in lex_hits}
    rec_by_idx = {}
    for _, r, idx in list(sem_hits) + list(lex_hits):
        rec_by_idx[idx] = r
    all_idx = list(rec_by_idx.keys())
    sv = _minmax([sem_scores.get(i, 0.0) for i in all_idx])
    lv = _minmax([lex_scores.get(i, 0.0) for i in all_idx])
    fused = []
    for i, a, b in zip(all_idx, sv, lv):
        fused.append({"idx": i, "record": rec_by_idx[i],
                      "sem": sem_scores.get(i, 0.0), "lex": lex_scores.get(i, 0.0),
                      "hybrid": w_sem * a + w_lex * b})
    fused.sort(key=lambda d: d["hybrid"], reverse=True)
    return fused[:k]
