"""Dense embeddings: local MiniLM (default, offline) or Gemini embeddings (EMBEDDING_PROVIDER=gemini)."""

from __future__ import annotations

from collections.abc import Sequence

from app.core.config import get_settings


class LocalEmbedder:
    name = "minilm"
    dimensions = 384

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        from app.ml.local_models import get_embedder

        vectors = get_embedder().encode(list(texts), batch_size=32, normalize_embeddings=True,
                                        show_progress_bar=False, convert_to_numpy=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class GeminiEmbedder:
    name = "gemini"
    dimensions = 768

    def _embed(self, texts: Sequence[str], task: str) -> list[list[float]]:
        from google.genai import types

        from app.services.gemini_client import get_client

        settings = get_settings()
        client = get_client()
        out: list[list[float]] = []
        for start in range(0, len(texts), 90):
            batch = list(texts[start:start + 90])
            resp = client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task, output_dimensionality=self.dimensions),
            )
            for emb in resp.embeddings:
                values = list(emb.values)
                norm = sum(v * v for v in values) ** 0.5 or 1.0
                out.append([v / norm for v in values])
        return out

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]


_embedders: dict[str, LocalEmbedder | GeminiEmbedder] = {}


def get_embedding_provider(name: str | None = None) -> LocalEmbedder | GeminiEmbedder:
    provider = (name or get_settings().embedding_provider or "local").lower()
    key = "gemini" if provider == "gemini" else "local"
    if key not in _embedders:
        _embedders[key] = GeminiEmbedder() if key == "gemini" else LocalEmbedder()
    return _embedders[key]
