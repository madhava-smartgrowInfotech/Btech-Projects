"""Content agent.

TF-IDF over the merchandising text of every product (name, descriptions, tags,
category, subcategory, attributes) with cosine similarity between items. A
shopper is represented as the interaction-weighted centroid of the products
they have engaged with; a product page is represented by its own row.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize


def product_document(product: dict) -> str:
    attrs = " ".join(str(v) for v in product["attributes"].values())
    return " ".join(
        [
            product["name"],
            product["name"],  # repeated so the line/model name carries weight
            product["category"],
            product["subcategory"],
            " ".join(product["tags"]),
            " ".join(product["tags"]),
            product["short_description"],
            product["description"],
            attrs,
            product["colorway"],
        ]
    )


class ContentAgent:
    def __init__(self, products: list[dict]):
        self.products = products
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=9000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        docs = [product_document(p) for p in products]
        self.tfidf = self.vectorizer.fit_transform(docs)
        self.tfidf_norm = normalize(self.tfidf)
        self.item_sim = cosine_similarity(self.tfidf_norm).astype(np.float32)
        np.fill_diagonal(self.item_sim, 0.0)
        self.vocabulary = self.vectorizer.get_feature_names_out()

    def score_from_vector(self, interaction_vector: np.ndarray) -> np.ndarray:
        """Cosine similarity of every product against the shopper's taste centroid."""
        if not np.any(interaction_vector):
            return np.zeros(len(self.products), dtype=np.float32)
        weights = np.asarray(interaction_vector, dtype=np.float64)
        # Interaction-weighted centroid in TF-IDF space.
        profile = self.tfidf_norm.T.dot(weights)
        norm = np.linalg.norm(profile)
        if norm == 0:
            return np.zeros(len(self.products), dtype=np.float32)
        profile = profile / norm
        scores = self.tfidf_norm.dot(profile)
        scores = np.where(interaction_vector > 4.5, scores * 0.3, scores)
        return scores.astype(np.float32)

    def score_for_product(self, product_idx: int) -> np.ndarray:
        return self.item_sim[product_idx].copy()

    def score_for_query(self, query: str) -> np.ndarray:
        """Relevance of every product to a free-text search."""
        if not query.strip():
            return np.zeros(len(self.products), dtype=np.float32)
        q = normalize(self.vectorizer.transform([query]))
        return (self.tfidf_norm @ q.T).toarray().ravel().astype(np.float32)

    def shared_terms(self, a_idx: int, b_idx: int, k: int = 3) -> list[str]:
        """Highest-weight TF-IDF terms two products have in common."""
        row_a = self.tfidf_norm[a_idx].toarray().ravel()
        row_b = self.tfidf_norm[b_idx].toarray().ravel()
        overlap = row_a * row_b
        order = np.argsort(-overlap)[:k]
        return [str(self.vocabulary[i]) for i in order if overlap[i] > 1e-6]

    def top_drivers(self, interaction_vector: np.ndarray, product_idx: int, k: int = 3):
        contributions = interaction_vector * self.item_sim[:, product_idx]
        order = np.argsort(-contributions)[:k]
        return [(int(i), float(self.item_sim[i, product_idx])) for i in order if contributions[i] > 1e-6]
