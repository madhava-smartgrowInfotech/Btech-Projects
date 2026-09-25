"""F2: clause classification - CUAD-style clause type via Gemini embeddings +
nearest-centroid search, with Gemini generateContent as a tie-breaker when the
top two candidates are close."""
import json
from pathlib import Path

import numpy as np

from ..config import DATA_DIR
from . import gemini_client
from .vectorstore import cosine_similarity_matrix

SAMPLE_PATH = Path(__file__).resolve().parents[3] / "data" / "sample" / "cuad_train_examples.json"
CENTROID_CACHE = DATA_DIR / "cuad_centroids.npz"

TIE_BREAK_MARGIN = 0.03  # if top1-top2 similarity gap is below this, ask Gemini to pick
UNKNOWN_LABEL = "Other / Unclassified"


def _load_categories_and_examples() -> tuple[list[str], dict[str, list[str]]]:
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    return payload["categories"], payload["examples"]


def build_or_load_centroids() -> tuple[list[str], np.ndarray]:
    """Returns (categories, centroid_matrix). Cached to disk after first build
    so we don't re-embed 500 examples on every backend restart."""
    categories, examples = _load_categories_and_examples()

    if CENTROID_CACHE.exists():
        cached = np.load(CENTROID_CACHE, allow_pickle=True)
        if list(cached["categories"]) == categories:
            return categories, cached["centroids"]

    vectors_by_cat = []
    for cat in categories:
        texts = examples[cat]
        embeddings = [gemini_client.embed_text(t, task_type="RETRIEVAL_DOCUMENT") for t in texts]
        centroid = np.mean(np.asarray(embeddings, dtype=np.float32), axis=0)
        vectors_by_cat.append(centroid)

    centroid_matrix = np.vstack(vectors_by_cat)
    np.savez(CENTROID_CACHE, categories=np.array(categories, dtype=object), centroids=centroid_matrix)
    return categories, centroid_matrix


_CENTROIDS_CACHE: tuple[list[str], np.ndarray] | None = None


def _get_centroids():
    global _CENTROIDS_CACHE
    if _CENTROIDS_CACHE is None:
        _CENTROIDS_CACHE = build_or_load_centroids()
    return _CENTROIDS_CACHE


def classify_clause(text: str, embedding: np.ndarray | None = None) -> dict:
    """Returns {clause_type, confidence, method, embedding (np.ndarray)}."""
    categories, centroids = _get_centroids()

    if embedding is None:
        embedding = np.asarray(
            gemini_client.embed_text(text, task_type="RETRIEVAL_QUERY"), dtype=np.float32
        )

    sims = cosine_similarity_matrix(embedding, centroids)
    order = np.argsort(-sims)
    top1_idx, top2_idx = int(order[0]), int(order[1])
    top1_sim, top2_sim = float(sims[top1_idx]), float(sims[top2_idx])

    method = "embedding"
    label = categories[top1_idx]
    confidence = top1_sim

    if top1_sim - top2_sim < TIE_BREAK_MARGIN and top1_sim < 0.60:
        top3_idx = [int(i) for i in order[:3]]
        candidates = [categories[i] for i in top3_idx]
        try:
            label, confidence = _tie_break(text, candidates, top1_sim)
            method = "gemini_tiebreak"
        except Exception:  # noqa: BLE001 - fall back to embedding result
            pass

    if confidence < 0.35:
        label = UNKNOWN_LABEL

    return {
        "clause_type": label,
        "confidence": round(float(confidence), 3),
        "method": method,
        "embedding": embedding,
    }


def _tie_break(text: str, candidates: list[str], fallback_sim: float) -> tuple[str, float]:
    prompt = f"""You are classifying a clause from a commercial contract into one of these
CUAD clause-type categories: {json.dumps(candidates)}.

Clause text:
\"\"\"{text[:1500]}\"\"\"

Reply with ONLY a JSON object: {{"category": "<one of the candidates exactly>", "confidence": <0-1 float>}}"""
    result = gemini_client.generate_json(prompt)
    category = result.get("category")
    if category not in candidates:
        return candidates[0], fallback_sim
    confidence = float(result.get("confidence", fallback_sim))
    return category, confidence
