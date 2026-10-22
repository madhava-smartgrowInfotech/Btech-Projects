"""Real measurements for the project documents. Writes docs/metrics/metrics.json (nothing is typed in by hand).

Run in the project venv:  .venv\\Scripts\\python.exe scripts\\measure_metrics.py

What it measures (all on the bundled 176-record synthetic knowledge base, CPU only):
  * retrieval ablation: BM25 only, dense only, hybrid, hybrid + cross-encoder (shipped), shipped without HyDE expansion,
    and the offline TF-IDF fallback, on five query sets (see below);
  * the shipped evaluation protocol (held-out record still in the index) against leave-one-record-out;
  * the displayed relevance score on in-knowledge-base versus out-of-knowledge-base queries;
  * the local generator (echo rate) and the evidence-based fallback;
  * the rule-based safety layer and the answer safety filter;
  * per-stage latency of the whole pipeline.
"""
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))

import numpy as np  # noqa: E402

from probe_data import FILTER_CASES, LAY, OUT_OF_KB, SAFETY_NEG, SAFETY_POS  # noqa: E402

OUT = BASE / "docs" / "metrics"
OUT.mkdir(parents=True, exist_ok=True)
K_CAND = 15
TOP_K = 5


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return [round((c - h) / d, 4), round((c + h) / d, 4)]


def main():
    t_start = time.time()
    from app.config import settings
    from app.rag.embeddings import EmbeddingBackend
    from app.rag.hybrid_retriever import fuse
    from app.rag.pipeline import get_pipeline
    from app.rag.query_expansion import expand_query_hyde
    from app.rag import safety as S
    import faiss

    pipe = get_pipeline()
    records = pipe.faiss.records
    n_rec = len(records)
    texts = [r["retrieval_text"] for r in records]
    vecs = pipe.faiss.index.reconstruct_n(0, n_rec)
    assert pipe.embeddings.mode == "sentence-transformer" and pipe.reranker.available

    # offline fallback: TF-IDF dense vectors in an in-memory flat index
    tf = EmbeddingBackend.__new__(EmbeddingBackend)
    tf.model_name, tf.mode, tf.model, tf.vectorizer, tf.dim = "tfidf", "tfidf", None, None, 384
    tf_vecs = tf.fit_fallback(texts)
    tf_index = faiss.IndexFlatIP(tf_vecs.shape[1])
    tf_index.add(tf_vecs.astype(np.float32))

    _enc_cache = {}

    def enc(text):
        if text not in _enc_cache:
            _enc_cache[text] = pipe.embeddings.encode([text])[0]
        return _enc_cache[text]

    def dense_hits(text, excl, mode="st"):
        if mode == "st":
            q = enc(text).astype(np.float32).reshape(1, -1)
            sc, ix = pipe.faiss.index.search(q, min(K_CAND + len(excl), n_rec))
        else:
            q = tf.encode([text]).astype(np.float32).reshape(1, -1)
            sc, ix = tf_index.search(q, min(K_CAND + len(excl), n_rec))
        out = [(float(s), records[int(i)], int(i)) for s, i in zip(sc[0], ix[0]) if int(i) >= 0 and int(i) not in excl]
        return out[:K_CAND]

    def lex_hits(text, excl):
        hits = pipe.bm25.search(text, k=K_CAND + len(excl))
        return [h for h in hits if h[2] not in excl][:K_CAND]

    def rank(query, cfg, excl=frozenset()):
        """Return ordered list of (record, display_score_or_None) for a configuration."""
        exp = expand_query_hyde(query)
        text = exp["normalized"] if cfg.endswith("_nohyde") else exp["combined"]
        if cfg == "bm25":
            return [(r, s) for s, r, _ in lex_hits(text, excl)][:TOP_K], {}
        if cfg == "dense":
            return [(r, s) for s, r, _ in dense_hits(text, excl)][:TOP_K], {}
        if cfg == "dense_tfidf":
            return [(r, s) for s, r, _ in dense_hits(text, excl, "tf")][:TOP_K], {}
        if cfg == "hybrid_tfidf":
            f = fuse(dense_hits(text, excl, "tf"), lex_hits(text, excl), settings.HYBRID_SEMANTIC_WEIGHT, settings.HYBRID_LEXICAL_WEIGHT, k=K_CAND)
            return [(c["record"], c["hybrid"]) for c in f][:TOP_K], {}
        f = fuse(dense_hits(text, excl), lex_hits(text, excl), settings.HYBRID_SEMANTIC_WEIGHT, settings.HYBRID_LEXICAL_WEIGHT, k=K_CAND)
        if cfg == "hybrid":
            return [(c["record"], c["hybrid"]) for c in f][:TOP_K], {"top_hybrid": f[0]["hybrid"] if f else 0.0}
        ranked = pipe.reranker.rerank(text, f, top_k=TOP_K)
        extra = {"top_rerank": ranked[0]["rerank"] if ranked else 0.0, "top_relevance": ranked[0]["relevance"] if ranked else 0.0}
        return [(c["record"], c["relevance"]) for c in ranked], extra

    CONFIGS = [
        ("bm25", "BM25 only (lexical)"),
        ("dense", "Dense only (MiniLM + FAISS)"),
        ("hybrid", "Hybrid fusion (0.65/0.35)"),
        ("hybrid_rerank", "Hybrid + cross-encoder (shipped)"),
        ("hybrid_rerank_nohyde", "Shipped, without HyDE expansion"),
        ("dense_tfidf", "Dense TF-IDF fallback"),
        ("hybrid_tfidf", "Hybrid with TF-IDF fallback (offline mode)"),
    ]

    def score_set(items, cfg, loo):
        """items: list of (true_disease, query, excluded_idx_set). Returns metric dict."""
        top1 = top3 = top5 = 0
        rr = []
        distinct = []
        misses = []
        y_true, y_pred = [], []
        t0 = time.perf_counter()
        for truth, q, ex in items:
            res, _ = rank(q, cfg, ex if loo else frozenset())
            names = [r["disease"] for r, _ in res]
            top1 += bool(names and names[0] == truth)
            top3 += truth in names[:3]
            top5 += truth in names
            rk = next((i + 1 for i, nme in enumerate(names) if nme == truth), None)
            rr.append(1.0 / rk if rk else 0.0)
            distinct.append(len(set(names)))
            y_true.append(truth)
            y_pred.append(names[0] if names else "")
            if not names or names[0] != truth:
                misses.append({"query": q, "truth": truth, "predicted": names[0] if names else "", "top5": names})
        n = len(items)
        return {
            "n": n, "top1": round(top1 / n, 4), "top1_ci": wilson(top1, n), "top3": round(top3 / n, 4), "top5": round(top5 / n, 4),
            "mrr5": round(sum(rr) / n, 4), "mean_distinct_conditions_in_top5": round(sum(distinct) / n, 3),
            "ms_per_query": round((time.perf_counter() - t0) * 1000 / n, 1), "misses": misses[:12], "n_misses": len(misses),
            "_y_true": y_true, "_y_pred": y_pred,
        }

    idx_by_id = {r["record_id"]: i for i, r in enumerate(records)}
    # ---- query sets
    random.seed(7)  # the seed used by scripts/evaluate.py
    by_dis = defaultdict(list)
    for r in records:
        by_dis[r["disease"]].append(r)
    shipped_test = []
    for d, rs in by_dis.items():
        if len(rs) >= 2:
            shipped_test.append(random.choice(rs))
    S1 = [(r["disease"], "I have " + r["symptoms"], frozenset([idx_by_id[r["record_id"]]])) for r in shipped_test]
    S2 = [(r["disease"], "I have " + r["symptoms"], frozenset([i])) for i, r in enumerate(records)]
    rng = random.Random(11)
    S3 = []
    for i, r in enumerate(records):
        syms = r["symptoms"].split(", ")
        pick = rng.sample(syms, 2)
        S3.append((r["disease"], f"I have {pick[0]} and {pick[1]}", frozenset([i])))
    S4 = [(d, q, frozenset()) for d, q in LAY]
    SETS = {
        "S1_shipped_protocol_30": (S1, False),
        "S1_leave_one_out_30": (S1, True),
        "S2_verbatim_leave_one_out_176": (S2, True),
        "S3_two_symptoms_leave_one_out_176": (S3, True),
        "S4_lay_language_60": (S4, False),
    }

    print("retrieval ablation ...", flush=True)
    retrieval = {}
    for cfg, label in CONFIGS:
        retrieval[cfg] = {"label": label}
        for sname, (items, loo) in SETS.items():
            if cfg.endswith("tfidf") and sname.startswith("S1_shipped"):
                pass
            retrieval[cfg][sname] = score_set(items, cfg, loo)
        print("  done", cfg, "S4 top1", retrieval[cfg]["S4_lay_language_60"]["top1"], flush=True)

    # per-condition result of the shipped configuration on lay probes (kept for the figures)
    cm_labels = sorted({d for d, _, _ in S4})
    s4_ship = retrieval["hybrid_rerank"]["S4_lay_language_60"]
    cm = [[0] * len(cm_labels) for _ in cm_labels]
    for t, p in zip(s4_ship["_y_true"], s4_ship["_y_pred"]):
        if p in cm_labels:
            cm[cm_labels.index(t)][cm_labels.index(p)] += 1
    per_cond = {}
    for t, p in zip(s4_ship["_y_true"], s4_ship["_y_pred"]):
        per_cond.setdefault(t, []).append(p == t)
    for cfg in retrieval:
        for sname in SETS:
            retrieval[cfg][sname].pop("_y_true"), retrieval[cfg][sname].pop("_y_pred")

    # ---- relevance display: in-KB (lay) vs out-of-KB
    print("relevance display ...", flush=True)
    rel = {"in_kb": [], "out_kb": []}
    for _, q in LAY:
        res, ex = rank(q, "hybrid_rerank")
        rel["in_kb"].append({"q": q, **{k: float(v) for k, v in ex.items()}, "top": res[0][0]["disease"]})
    for q in OUT_OF_KB:
        res, ex = rank(q, "hybrid_rerank")
        rel["out_kb"].append({"q": q, **{k: float(v) for k, v in ex.items()}, "top": res[0][0]["disease"]})
    label = lambda s: "Strong match" if s >= 0.66 else ("Moderate match" if s >= 0.33 else "Weak match")  # same bands as app/rag/pipeline.py
    from sklearn.metrics import roc_auc_score

    ytrue = [1] * len(rel["in_kb"]) + [0] * len(rel["out_kb"])
    auc = {}
    for key in ("top_rerank", "top_hybrid"):
        if key == "top_hybrid":
            vals = []
            for grp in ("in_kb", "out_kb"):
                for it in rel[grp]:
                    res, ex = rank(it["q"], "hybrid")
                    vals.append(ex["top_hybrid"])
            auc[key] = round(float(roc_auc_score(ytrue, vals)), 4)
        else:
            vals = [it["top_rerank"] for it in rel["in_kb"]] + [it["top_rerank"] for it in rel["out_kb"]]
            auc[key] = round(float(roc_auc_score(ytrue, vals)), 4)
    relevance = {
        "in_kb_n": len(rel["in_kb"]), "out_kb_n": len(rel["out_kb"]),
        "in_kb_top_relevance_all_1": all(abs(x["top_relevance"] - 1.0) < 1e-9 for x in rel["in_kb"]),
        "out_kb_top_relevance_all_1": all(abs(x["top_relevance"] - 1.0) < 1e-9 for x in rel["out_kb"]),
        "in_kb_labels": dict(Counter(label(x["top_relevance"]) for x in rel["in_kb"])),
        "out_kb_labels": dict(Counter(label(x["top_relevance"]) for x in rel["out_kb"])),
        "raw_rerank_in_kb": {"mean": round(float(np.mean([x["top_rerank"] for x in rel["in_kb"]])), 3), "min": round(float(np.min([x["top_rerank"] for x in rel["in_kb"]])), 3), "max": round(float(np.max([x["top_rerank"] for x in rel["in_kb"]])), 3)},
        "raw_rerank_out_kb": {"mean": round(float(np.mean([x["top_rerank"] for x in rel["out_kb"]])), 3), "min": round(float(np.min([x["top_rerank"] for x in rel["out_kb"]])), 3), "max": round(float(np.max([x["top_rerank"] for x in rel["out_kb"]])), 3)},
        "auroc_in_vs_out_by_raw_rerank_score": auc["top_rerank"],
        "auroc_in_vs_out_by_raw_hybrid_score": auc["top_hybrid"],
        "out_kb_examples": [{"query": x["q"], "top_condition": x["top"], "raw_rerank": round(x["top_rerank"], 3)} for x in rel["out_kb"]],
        "raw_rerank_in_kb_values": [round(x["top_rerank"], 3) for x in rel["in_kb"]],
        "raw_rerank_out_kb_values": [round(x["top_rerank"], 3) for x in rel["out_kb"]],
    }
    # the same in-KB/out-of-KB split through the real pipeline.answer() to confirm what the user sees
    seen = Counter()
    for q in OUT_OF_KB:
        seen[pipe.answer(q)["relevance_label"]] += 1
    relevance["out_kb_labels_via_pipeline_answer"] = dict(seen)

    # ---- generation
    print("generation ...", flush=True)
    gen_q = [q for _, q, _ in S1][:30]
    echo = 0
    gen_ms, fb_ms = [], []
    names_ok = 0
    sample_echo = None
    all_names = sorted({r["disease"] for r in records})
    for q in gen_q:
        exp = expand_query_hyde(q)
        res, _ = rank(q, "hybrid_rerank")
        ev = [{"record": r} for r, _ in res]
        t0 = time.perf_counter()
        ans, by = pipe.generator.generate(exp["normalized"], ev)
        gen_ms.append((time.perf_counter() - t0) * 1000)
        is_echo = ans.strip().startswith("Answer only from the retrieved context") or "Retrieved medical information:" in ans
        echo += is_echo
        if is_echo and sample_echo is None:
            sample_echo = ans[:400]
        t0 = time.perf_counter()
        fb = pipe.generator.fallback_answer(exp["normalized"], ev)
        fb_ms.append((time.perf_counter() - t0) * 1000)
        in_ev = {r["disease"] for r, _ in res}
        names_ok += all(n in in_ev for n in all_names if n in fb)
    generation = {
        "n": len(gen_q), "generator_label": f"local-generator:{settings.GENERATOR_MODEL}",
        "echo_answers": echo, "echo_rate": round(echo / len(gen_q), 3),
        "mean_generate_ms": round(float(np.mean(gen_ms)), 1), "mean_fallback_ms": round(float(np.mean(fb_ms)), 3),
        "fallback_names_only_retrieved_conditions": names_ok, "sample_echo_start": sample_echo,
        "text2text_task_in_installed_transformers": None,
    }
    import transformers
    generation["transformers_version"] = transformers.__version__
    try:
        from transformers import pipeline as _pl
        _pl("text2text-generation", model=settings.GENERATOR_MODEL, device=-1)
        generation["text2text_task_in_installed_transformers"] = "available"
    except Exception as e:
        generation["text2text_task_in_installed_transformers"] = f"unavailable: {type(e).__name__}"

    # ---- safety rule layer
    print("safety ...", flush=True)
    def flag(q):
        return S.check_safety(q)["flag"]

    pos = [(q, g, flag(q)) for q, g in SAFETY_POS]
    neg = [(q, g, flag(q)) for q, g in SAFETY_NEG]
    grp = {}
    for g in ("literal", "paraphrase"):
        sub = [x for x in pos if x[1] == g]
        grp[g] = {"n": len(sub), "detected": sum(x[2] == "emergency" for x in sub), "missed": [x[0] for x in sub if x[2] != "emergency"],
                  "flagged_caution_instead": sum(x[2] == "caution" for x in sub)}
    ngrp = {}
    for g in ("ordinary", "hard"):
        sub = [x for x in neg if x[1] == g]
        ngrp[g] = {"n": len(sub), "false_emergency": [x[0] for x in sub if x[2] == "emergency"], "caution": [x[0] for x in sub if x[2] == "caution"],
                   "routine": sum(x[2] == "routine" for x in sub)}
    tp = sum(x[2] == "emergency" for x in pos)
    fp = sum(x[2] == "emergency" for x in neg)
    safety = {
        "n_pos": len(pos), "n_neg": len(neg), "emergency_recall": round(tp / len(pos), 4), "recall_ci": wilson(tp, len(pos)),
        "emergency_precision": round(tp / max(tp + fp, 1), 4), "false_emergency": fp, "true_emergency": tp,
        "by_group_pos": grp, "by_group_neg": ngrp,
        "n_rules": len(S.EMERGENCY_PATTERNS), "n_caution_keywords": 6,
    }
    flt = []
    for text, phrase in FILTER_CASES:
        out = S.apply_safety_filter(text)
        flt.append({"input": text, "output": out, "phrase": phrase, "removed": phrase.lower() not in out.lower()})
    in_list = [x for x in flt if x["phrase"] in ("take ibuprofen", "take antibiotics", "dosage", "prescribe", "mg twice daily")]
    safety["filter"] = {"n": len(flt), "removed": sum(x["removed"] for x in flt), "n_listed_phrases": len(in_list), "listed_removed": sum(x["removed"] for x in in_list),
                        "cases": flt}

    # ---- latency (pipeline stages, warm)
    print("latency ...", flush=True)
    stages = defaultdict(list)
    for q in gen_q:
        t0 = time.perf_counter(); exp = expand_query_hyde(q); stages["expand"].append((time.perf_counter() - t0) * 1000)
        c = exp["combined"]
        t0 = time.perf_counter(); qv = pipe.embeddings.encode([c])[0]; stages["embed"].append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter(); sh = pipe.faiss.search(qv, k=K_CAND); stages["faiss"].append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter(); lh = pipe.bm25.search(c, k=K_CAND); stages["bm25"].append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter(); fz = fuse(sh, lh, 0.65, 0.35, k=K_CAND); stages["fuse"].append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter(); rk = pipe.reranker.rerank(c, fz, top_k=TOP_K); stages["rerank"].append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter(); S.check_safety(q); stages["safety"].append((time.perf_counter() - t0) * 1000)
    total_full, total_nogen = [], []
    for q in gen_q:
        t0 = time.perf_counter(); pipe.answer(q); total_full.append((time.perf_counter() - t0) * 1000)
    saved = (pipe.generator.available, pipe.generator.pipe)
    pipe.generator.available, pipe.generator.pipe = False, None
    for q in gen_q:
        t0 = time.perf_counter(); pipe.answer(q); total_nogen.append((time.perf_counter() - t0) * 1000)
    pipe.generator.available, pipe.generator.pipe = saved

    def sm(a):
        a = np.array(a)
        return {"mean": round(float(a.mean()), 2), "median": round(float(np.median(a)), 2), "p95": round(float(np.percentile(a, 95)), 2), "max": round(float(a.max()), 2)}

    latency = {"n": len(gen_q), "stages_ms": {k: sm(v) for k, v in stages.items()},
               "pipeline_answer_with_local_generator_ms": sm(total_full), "pipeline_answer_fallback_only_ms": sm(total_nogen)}

    # ---- knowledge base facts
    sev = Counter(r["severity"] for r in records)
    sym_counts = [len(r["symptoms"].split(", ")) for r in records]
    vocab = {s for r in records for s in r["symptoms"].split(", ")}
    per_cond_n = Counter(r["disease"] for r in records)
    desc_unique = len({(r["disease"], r["description"], r["guidance"]) for r in records})
    kb = {"records": n_rec, "conditions": len(per_cond_n), "records_per_condition": dict(sorted(per_cond_n.items())), "severity": dict(sev),
          "mean_symptoms_per_record": round(sum(sym_counts) / n_rec, 2), "min_symptoms": min(sym_counts), "max_symptoms": max(sym_counts),
          "symptom_vocabulary": len(vocab), "distinct_description_guidance_pairs": desc_unique,
          "source_type": sorted({r["source_type"] for r in records}), "embedding_dim": int(vecs.shape[1])}

    import platform
    import faiss as _f
    import sentence_transformers, sklearn, torch, fastapi, sqlalchemy, rank_bm25  # noqa: E401
    env = {
        "python": platform.python_version(), "os": platform.platform(), "torch": torch.__version__, "transformers": transformers.__version__,
        "sentence_transformers": sentence_transformers.__version__, "faiss": _f.__version__ if hasattr(_f, "__version__") else "faiss-cpu",
        "scikit_learn": sklearn.__version__, "fastapi": fastapi.__version__, "sqlalchemy": sqlalchemy.__version__,
        "embedding_model": settings.EMBEDDING_MODEL, "reranker_model": settings.RERANKER_MODEL, "generator_model": settings.GENERATOR_MODEL,
        "weights": [settings.HYBRID_SEMANTIC_WEIGHT, settings.HYBRID_LEXICAL_WEIGHT], "candidate_k": settings.CANDIDATE_K, "top_k": settings.RETRIEVAL_TOP_K,
        "cpu": "12th Gen Intel Core i5-12500 (6 cores / 12 threads), no GPU", "ram_gb": 15.7,
    }
    out = {"environment": env, "kb": kb, "retrieval": retrieval, "lay_confusion": {"labels": cm_labels, "matrix": cm},
           "lay_per_condition_correct": {k: [sum(v), len(v)] for k, v in per_cond.items()},
           "relevance": relevance, "generation": generation, "safety": safety, "latency": latency,
           "probe_sizes": {"lay": len(LAY), "out_of_kb": len(OUT_OF_KB), "safety_pos": len(SAFETY_POS), "safety_neg": len(SAFETY_NEG)},
           "elapsed_s": round(time.time() - t_start, 1)}
    (OUT / "metrics.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote", OUT / "metrics.json", "in", out["elapsed_s"], "s")


if __name__ == "__main__":
    main()
