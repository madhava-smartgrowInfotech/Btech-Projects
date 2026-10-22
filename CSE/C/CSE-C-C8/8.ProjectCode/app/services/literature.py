"""PeerScope literature grounding via the OpenAlex public API (timeouts + graceful failure)."""
from __future__ import annotations

import urllib.parse

import requests

from app.config import LITERATURE_COUNT, LITERATURE_TIMEOUT_S

OPENALEX = "https://api.openalex.org/works"


def retrieve_literature(title: str, keywords: list[str], topics: list[str]) -> dict:
    query = title or " ".join((keywords or [])[:6])
    query = query.strip()[:220] or "machine learning research"
    params = {
        "search": query,
        "per-page": max(3, min(int(LITERATURE_COUNT), 8)),
        "select": "id,title,publication_year,authorships,primary_location,doi",
    }
    url = OPENALEX + "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": "PeerScope/1.0 (mailto:peerscope-local@example.com)"}
    try:
        resp = requests.get(url, headers=headers, timeout=float(LITERATURE_TIMEOUT_S))
        resp.raise_for_status()
        data = resp.json()
        items = []
        for w in (data.get("results") or [])[: int(LITERATURE_COUNT)]:
            authors = []
            for a in (w.get("authorships") or [])[:4]:
                nm = (a.get("author") or {}).get("display_name")
                if nm:
                    authors.append(nm)
            loc = w.get("primary_location") or {}
            src = (loc.get("source") or {}).get("display_name", "")
            items.append({
                "title": w.get("title") or "Untitled",
                "year": w.get("publication_year"),
                "authors": authors,
                "source": src,
                "doi": w.get("doi", ""),
                "url": w.get("id", ""),
            })
        scored = score_literature(query, items)
        return {"literature_retrieval_status": "ok", "query": query, "works": scored, "source": "OpenAlex"}
    except Exception as exc:
        return {"literature_retrieval_status": "unavailable", "query": query,
                "works": [], "source": "OpenAlex",
                "error": f"OpenAlex retrieval failed ({type(exc).__name__}): {exc}"}


def score_literature(query: str, works: list[dict]) -> list[dict]:
    """Rank works by semantic similarity when embeddings exist, else keyword overlap."""
    try:
        from app.services.embeddings import embed_texts

        vecs = embed_texts([query] + [w.get("title", "") for w in works])
        import numpy as np

        q = vecs[0]
        scored = []
        for w, v in zip(works, vecs[1:]):
            denom = (float((q * q).sum()) ** 0.5) * (float((v * v).sum()) ** 0.5)
            sim = float((q * v).sum() / denom) if denom else 0.0
            scored.append({**w, "relevance": round(max(0.0, min(1.0, sim)), 4)})
        scored.sort(key=lambda d: d["relevance"], reverse=True)
        return scored
    except Exception:
        qtok = set(query.lower().split())
        out = []
        for w in works:
            ttok = set((w.get("title") or "").lower().split())
            inter = len(qtok & ttok)
            union = max(len(qtok | ttok), 1)
            out.append({**w, "relevance": round(inter / union, 4)})
        out.sort(key=lambda d: d["relevance"], reverse=True)
        return out
