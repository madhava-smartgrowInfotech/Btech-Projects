"""Dense clause index in ChromaDB (local, persistent under data/chroma/).

One collection per embedding provider; every vector carries its ``document_id`` so a
policy that several users upload is embedded only once.
"""

from __future__ import annotations

import threading
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger, log_event
from app.ml.embeddings import get_embedding_provider
from app.ml.retrieval.clause_cache import ClauseRecord, load_clauses

log = get_logger("chroma")
_lock = threading.Lock()
_client = None


def _get_client():  # noqa: ANN202
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                import chromadb
                from chromadb.config import Settings as ChromaSettings

                path = get_settings().chroma_dir
                path.mkdir(parents=True, exist_ok=True)
                _client = chromadb.PersistentClient(
                    path=str(path), settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False)
                )
    return _client


def collection_name(provider: str | None = None) -> str:
    return f"clauses_{get_embedding_provider(provider).name}"


def _collection(provider: str | None = None):  # noqa: ANN202
    client = _get_client()
    name = collection_name(provider)
    try:
        return client.get_or_create_collection(
            name=name, embedding_function=None, configuration={"hnsw": {"space": "cosine"}}
        )
    except TypeError:
        return client.get_or_create_collection(name=name, embedding_function=None, metadata={"hnsw:space": "cosine"})


def _vector_id(document_id: int, ordinal: int) -> str:
    return f"d{document_id}-c{ordinal}"


def index_document(document_id: int, provider: str | None = None) -> int:
    """(Re)build the dense vectors for one document. Returns the number of clauses indexed."""
    clauses = load_clauses(document_id)
    col = _collection(provider)
    col.delete(where={"document_id": document_id})
    if not clauses:
        return 0
    embedder = get_embedding_provider(provider)
    vectors = embedder.embed_documents([c.index_text for c in clauses])
    for start in range(0, len(clauses), 500):
        batch = clauses[start:start + 500]
        col.upsert(
            ids=[_vector_id(document_id, c.ordinal) for c in batch],
            embeddings=vectors[start:start + 500],
            metadatas=[{"document_id": document_id, "ordinal": c.ordinal, "page": c.page_start} for c in batch],
        )
    log_event(log, "document_indexed", document_id=document_id, clauses=len(clauses), provider=embedder.name)
    return len(clauses)


def count_for(document_id: int, provider: str | None = None) -> int:
    try:
        res = _collection(provider).get(where={"document_id": document_id}, include=[])
        return len(res.get("ids", []))
    except Exception:  # noqa: BLE001
        return 0


def delete_document(document_id: int) -> None:
    for provider in ("local", "gemini"):
        try:
            _collection(provider).delete(where={"document_id": document_id})
        except Exception:  # noqa: BLE001 - the gemini collection may not exist
            continue


def search(document_id: int, query: str, k: int = 30, provider: str | None = None) -> list[tuple[ClauseRecord, float]]:
    clauses = {c.ordinal: c for c in load_clauses(document_id)}
    if not clauses:
        return []
    vector = get_embedding_provider(provider).embed_query(query)
    res = _collection(provider).query(
        query_embeddings=[vector], n_results=min(k, len(clauses)), where={"document_id": document_id},
        include=["distances", "metadatas"],
    )
    out: list[tuple[ClauseRecord, float]] = []
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        clause = clauses.get(int(meta["ordinal"]))
        if clause is not None:
            out.append((clause, round(1.0 - float(dist), 4)))  # cosine similarity
    return out


def vector_store_status() -> dict[str, Any]:
    try:
        col = _collection()
        return {"status": "ok", "collection": col.name, "vectors": col.count()}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)[:200]}
