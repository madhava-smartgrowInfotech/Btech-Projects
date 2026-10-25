"""
Dense-retrieval reference point for the experiments (not part of the product).

Embeds the evaluation chunks (experiments/chunks.json, written by run_experiments.py) and the 72 questions with
BAAI/bge-small-en-v1.5 through fastembed (ONNX, CPU) and stores the question x chunk cosine matrix in
experiments/dense_sims.npy. run_experiments.py then reports dense and BM25+dense hybrid retrieval next to the
platform's TF-IDF retriever. Needs a separate environment:  pip install fastembed==0.5.1 numpy

    <dense-venv>\\Scripts\\python.exe scripts\\dense_baseline.py
"""
import json
import os
import sys
import time

import numpy as np
from fastembed import TextEmbedding

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from eval_questions import QUESTIONS  # noqa: E402

with open(os.path.join(ROOT, "experiments", "chunks.json"), encoding="utf-8") as f:
    chunks = json.load(f)

model = TextEmbedding("BAAI/bge-small-en-v1.5")
t0 = time.perf_counter()
C = np.array(list(model.embed(chunks, batch_size=32)), dtype=np.float32)
t_chunks = time.perf_counter() - t0
t0 = time.perf_counter()
Q = np.array([next(iter(model.query_embed([q[2]]))) for q in QUESTIONS], dtype=np.float32)
t_q = time.perf_counter() - t0
C /= np.linalg.norm(C, axis=1, keepdims=True)
Q /= np.linalg.norm(Q, axis=1, keepdims=True)
np.save(os.path.join(ROOT, "experiments", "dense_sims.npy"), Q @ C.T)
with open(os.path.join(ROOT, "experiments", "dense_meta.json"), "w") as f:
    json.dump({"model": "BAAI/bge-small-en-v1.5", "dim": int(C.shape[1]), "chunks": len(chunks),
               "embed_chunks_s": round(t_chunks, 1), "embed_query_ms_each": round(1000 * t_q / len(QUESTIONS), 1)}, f)
print("saved", Q.shape, C.shape, round(t_chunks, 1), "s for chunks,", round(1000 * t_q / len(QUESTIONS), 1), "ms per query")
