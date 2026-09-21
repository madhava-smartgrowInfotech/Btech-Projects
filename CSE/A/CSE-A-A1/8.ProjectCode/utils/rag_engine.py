"""
Lightweight Retrieval-Augmented Generation engine.

Retrieval: TF-IDF + cosine similarity over document chunks (no external
model downloads needed, so the project runs fully offline).

Generation: if an ANTHROPIC_API_KEY is configured in the environment,
the retrieved chunks are sent as context to Claude for a natural-language
answer. Otherwise the engine falls back to an extractive method that
picks the most query-relevant sentences from the retrieved chunks, so
the app remains fully functional with zero API keys/costs.
"""
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RAGEngine:
    def __init__(self):
        self.vectorizer = None
        self.matrix = None
        self.chunks = []          # list of chunk text
        self.chunk_meta = []      # list of dicts: {doc_id, doc_name, chunk_index}

    def build_index(self, chunk_records):
        """
        chunk_records: list of dicts with keys 'text', 'doc_id', 'doc_name', 'chunk_index'
        """
        self.chunks = [c["text"] for c in chunk_records]
        self.chunk_meta = chunk_records
        if not self.chunks:
            self.vectorizer = None
            self.matrix = None
            return
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(self.chunks)

    def retrieve(self, query, top_k=4):
        if not self.chunks or self.vectorizer is None:
            return []
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.matrix).flatten()
        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if sims[idx] <= 0:
                continue
            meta = self.chunk_meta[idx]
            results.append({
                "text": self.chunks[idx],
                "score": float(sims[idx]),
                "doc_id": meta.get("doc_id"),
                "doc_name": meta.get("doc_name"),
                "chunk_index": meta.get("chunk_index"),
            })
        return results

    def _extractive_answer(self, query, retrieved):
        """Pick the sentences most relevant to the query from retrieved chunks."""
        if not retrieved:
            return "No relevant content was found in your uploaded documents for this question. Try uploading related notes first."

        sentences = []
        for r in retrieved:
            for s in re.split(r"(?<=[.!?])\s+", r["text"]):
                s = s.strip()
                if len(s) > 20:
                    sentences.append((s, r["doc_name"]))

        if not sentences:
            return retrieved[0]["text"][:500]

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            all_texts = [query] + [s for s, _ in sentences]
            mat = vectorizer.fit_transform(all_texts)
            sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
            ranked = sorted(zip(sentences, sims), key=lambda x: x[1], reverse=True)
            top_sents = [s for (s, _doc), score in ranked[:4] if score > 0]
        except ValueError:
            top_sents = [s for s, _ in sentences[:3]]

        if not top_sents:
            top_sents = [s for s, _ in sentences[:3]]

        answer = " ".join(top_sents)
        return answer

    def generate_answer(self, query, api_key=None, top_k=4):
        retrieved = self.retrieve(query, top_k=top_k)

        if api_key:
            try:
                answer = self._llm_answer(query, retrieved, api_key)
                return answer, retrieved
            except Exception:
                # Silently fall back to extractive mode if the API call fails
                pass

        return self._extractive_answer(query, retrieved), retrieved

    def _llm_answer(self, query, retrieved, api_key):
        import anthropic
        context = "\n\n".join(f"[Source: {r['doc_name']}]\n{r['text']}" for r in retrieved)
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": (
                    "You are a study assistant. Answer the student's question using ONLY "
                    "the context below. If the context is insufficient, say so.\n\n"
                    f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
                ),
            }],
        )
        parts = [block.text for block in message.content if getattr(block, "type", "") == "text"]
        return "\n".join(parts).strip() or "I could not generate an answer from the provided context."
