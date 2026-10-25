"""
Measures the platform's own components on the six-subject notes corpus (scripts/fetch_corpus.py) with the
72 hand-written questions of scripts/eval_questions.py. Everything runs on the project's real code
(utils.text_extraction, utils.rag_engine, utils.quiz_generator); nothing here is a model of them.

    venv\\Scripts\\python.exe scripts\\run_experiments.py          # writes experiments/results.json

Optional: scripts/dense_baseline.py (separate venv with fastembed) writes experiments/dense_sims.npy; when that
file exists the dense and hybrid retrievers are evaluated too.
"""
import json
import math
import os
import random
import re
import sys
import time

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from eval_questions import CORPUS, QUESTIONS, norm  # noqa: E402
from utils.quiz_generator import generate_quiz  # noqa: E402
from utils.rag_engine import RAGEngine  # noqa: E402
from utils.text_extraction import chunk_text, clean_text, detect_subject_hints, extract_text, extract_topics  # noqa: E402

OUT = os.path.join(ROOT, "experiments", "results.json")
KS = list(range(1, 11))


def load_chunks(size=180, overlap=30):
    records, docs = [], []
    for name in sorted(os.listdir(CORPUS)):
        path = os.path.join(CORPUS, name)
        text = clean_text(extract_text(path))
        chunks = chunk_text(text, chunk_size=size, overlap=overlap)
        docs.append({"file": name, "subject": name[3:-4].replace("_", " "), "words": len(text.split()), "chunks": len(chunks)})
        for i, c in enumerate(chunks):
            records.append({"text": c, "doc_id": len(docs), "doc_name": name, "chunk_index": i})
    return records, docs


# ------------------------------------------------------------------ retrievers
class Shipped:
    """The platform's retriever, called exactly as the API calls it."""
    def __init__(self, records):
        self.engine = RAGEngine()
        self.engine.build_index(records)
        self.n = len(records)

    def rank(self, q):
        res = self.engine.retrieve(q, top_k=self.n)
        return [r["chunk_index"] for r in res], res


def sims_to_rank(sims):
    return list(np.argsort(-sims, kind="stable"))


class Matrix:
    """Generic scorer: returns the ranking of all chunks for a query."""
    def __init__(self, scorer):
        self.scorer = scorer


class BM25:
    def __init__(self, texts, k1=1.5, b=0.75):
        self.cv = CountVectorizer(stop_words="english")
        tf = self.cv.fit_transform(texts).tocsc().astype(np.float64)
        n = tf.shape[0]
        df = np.diff(tf.indptr)
        self.idf = np.log((n - df + 0.5) / (df + 0.5) + 1.0)
        self.tf = tf.tocsr()
        self.dl = np.asarray(tf.sum(axis=1)).ravel()
        self.avg = self.dl.mean()
        self.k1, self.b = k1, b

    def scores(self, q):
        qv = self.cv.transform([q])
        idx = qv.indices
        out = np.zeros(self.tf.shape[0])
        if len(idx) == 0:
            return out
        sub = self.tf[:, idx].toarray()
        denom = sub + self.k1 * (1 - self.b + self.b * self.dl[:, None] / self.avg)
        out = ((sub * (self.k1 + 1)) / denom * self.idf[idx]).sum(axis=1)
        return out


def minmax(x):
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


# ------------------------------------------------------------------ metrics
def evaluate(rankings, chunk_texts, qs, only=None):
    """rankings[i] = list of chunk positions (best first). Returns hit@k, MRR@10 over qs (optionally subset)."""
    ev = [norm(q[3]) for q in qs]
    ntext = [norm(t) for t in chunk_texts]
    hits_at = {k: 0 for k in KS}
    rr, n = 0.0, 0
    first_ranks = []
    for i, order in enumerate(rankings):
        if only is not None and i not in only:
            continue
        n += 1
        rank = None
        for r, pos in enumerate(order[:10], 1):
            if ev[i] in ntext[pos]:
                rank = r
                break
        first_ranks.append(rank)
        if rank:
            rr += 1 / rank
            for k in KS:
                if rank <= k:
                    hits_at[k] += 1
    return {"n": n, "hit": {k: round(hits_at[k] / n, 4) for k in KS}, "mrr10": round(rr / n, 4), "first_rank": first_ranks}


def by_type(rankings, chunk_texts, qs):
    out = {}
    for t in ("fact", "definition", "reasoning"):
        idx = {i for i, q in enumerate(qs) if q[1] == t}
        e = evaluate(rankings, chunk_texts, qs, only=idx)
        out[t] = {"n": e["n"], "hit1": e["hit"][1], "hit3": e["hit"][3], "hit4": e["hit"][4], "mrr10": e["mrr10"]}
    return out


def pct(x, p):
    return float(np.percentile(x, p))


# ------------------------------------------------------------------ main experiments
def exp_retrieval(records, qs):
    texts = [r["text"] for r in records]
    res = {}
    shipped = Shipped(records)
    order_shipped = []
    for q in qs:
        res_list = shipped.engine.retrieve(q[2], top_k=len(records))
        # map back to positions by (doc_id, chunk_index)
        order_shipped.append([pos_of[(r["doc_id"], r["chunk_index"])] for r in res_list])
    # (positions with zero similarity are dropped by the engine, pad them at the end for completeness)
    results = {}

    def add(name, rankings):
        e = evaluate(rankings, texts, qs)
        results[name] = {"hit": e["hit"], "mrr10": e["mrr10"], "by_type": by_type(rankings, texts, qs), "first_rank": e["first_rank"]}

    add("tfidf_shipped (1-2gram)", order_shipped)

    tf1 = TfidfVectorizer(stop_words="english")
    m1 = tf1.fit_transform(texts)
    add("tfidf_unigram", [sims_to_rank(cosine_similarity(tf1.transform([q[2]]), m1).ravel()) for q in qs])

    bm = BM25(texts)
    add("bm25", [sims_to_rank(bm.scores(q[2])) for q in qs])

    lsa_tf = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    mm = lsa_tf.fit_transform(texts)
    svd = TruncatedSVD(n_components=200, random_state=0)
    Z = svd.fit_transform(mm)
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)

    def lsa_scores(q):
        qz = svd.transform(lsa_tf.transform([q]))
        qz = qz / (np.linalg.norm(qz) + 1e-9)
        return (Zn @ qz.T).ravel()

    add("tfidf_lsa200", [sims_to_rank(lsa_scores(q[2])) for q in qs])
    add("hybrid_bm25_lsa", [sims_to_rank(0.5 * minmax(bm.scores(q[2])) + 0.5 * minmax(lsa_scores(q[2]))) for q in qs])

    dense_path = os.path.join(ROOT, "experiments", "dense_sims.npy")
    if os.path.exists(dense_path):
        S = np.load(dense_path)  # (n_questions, n_chunks) cosine similarity, BGE-small
        if S.shape == (len(qs), len(records)):
            add("dense_bge_small", [sims_to_rank(S[i]) for i in range(len(qs))])
            add("hybrid_bm25_dense", [sims_to_rank(0.5 * minmax(bm.scores(q[2])) + 0.5 * minmax(S[i])) for i, q in enumerate(qs)])
    return results


def exp_chunk_sizes(qs):
    out = {}
    for size, ov in [(60, 15), (100, 20), (180, 30), (300, 50), (450, 75)]:
        recs, _ = load_chunks(size, ov)
        texts = [r["text"] for r in recs]
        eng = RAGEngine()
        eng.build_index(recs)
        pos = {(r["doc_id"], r["chunk_index"]): i for i, r in enumerate(recs)}
        rankings = [[pos[(h["doc_id"], h["chunk_index"])] for h in eng.retrieve(q[2], top_k=10)] for q in qs]
        e = evaluate(rankings, texts, qs)
        ntexts = [norm(t) for t in texts]
        intact = sum(1 for q in qs if any(norm(q[3]) in t for t in ntexts))
        words = [len(t.split()) for t in texts]
        out[f"{size}/{ov}"] = {"chunks": len(recs), "evidence_intact": intact, "hit1": e["hit"][1], "hit3": e["hit"][3],
                               "hit4": e["hit"][4], "hit10": e["hit"][10], "mrr10": e["mrr10"],
                               "mean_words": round(float(np.mean(words)), 1)}
    return out


def ngram_coverage(answer, context_norm, n=1):
    """Share of the answer's words that occur in the retrieved context (1.0 = nothing was added by the answerer)."""
    ctx = set(context_norm.split())
    w = norm(answer).split()
    return sum(x in ctx for x in w) / len(w) if w else 1.0


def exp_compression(records, qs):
    """Shipped TF-IDF retrieval + shipped extractive answer step, versus passing the retrieved chunks whole."""
    eng = RAGEngine()
    eng.build_index(records)
    out = {}
    per_q = []
    for k in (1, 2, 4, 6, 8):
        rows = []
        for q in qs:
            ans, retrieved = eng.generate_answer(q[2], api_key=None, top_k=k)
            ctx = " ".join(r["text"] for r in retrieved)
            nctx, nans = norm(ctx), norm(ans)
            keys = [a.lower() for a in q[4]]
            rows.append({
                "ctx_words": len(ctx.split()), "ans_words": len(ans.split()),
                "ev_in_ctx": norm(q[3]) in nctx, "ev_in_ans": norm(q[3]) in nans,
                "key_in_ctx": any(a in nctx for a in keys), "key_in_ans": any(a in nans for a in keys),
                "grounded": ngram_coverage(ans, nctx),
                "type": q[1],
            })
        n = len(rows)
        cw, aw = np.mean([r["ctx_words"] for r in rows]), np.mean([r["ans_words"] for r in rows])
        out[str(k)] = {
            "mean_ctx_words": round(float(cw), 1), "mean_ans_words": round(float(aw), 1),
            "token_reduction_pct": round(100 * (1 - aw / cw), 1),
            "evidence_in_ctx": round(sum(r["ev_in_ctx"] for r in rows) / n, 4),
            "evidence_in_ans": round(sum(r["ev_in_ans"] for r in rows) / n, 4),
            "key_in_ctx": round(sum(r["key_in_ctx"] for r in rows) / n, 4),
            "key_in_ans": round(sum(r["key_in_ans"] for r in rows) / n, 4),
            "answer_words_in_context": round(float(np.mean([r["grounded"] for r in rows])), 4),
            "answers_fully_grounded": round(sum(r["grounded"] >= 0.999 for r in rows) / n, 4),
        }
        if k == 4:
            per_q = rows
            for t in ("fact", "definition", "reasoning"):
                sub = [r for r in rows if r["type"] == t]
                out["by_type_k4"] = out.get("by_type_k4", {})
                out["by_type_k4"][t] = {
                    "key_in_ctx": round(sum(r["key_in_ctx"] for r in sub) / len(sub), 4),
                    "key_in_ans": round(sum(r["key_in_ans"] for r in sub) / len(sub), 4),
                    "evidence_in_ans": round(sum(r["ev_in_ans"] for r in sub) / len(sub), 4),
                    "ans_words": round(float(np.mean([r["ans_words"] for r in sub])), 1),
                }
            hit = [r for r in rows if r["ev_in_ctx"]]
            out["k4_given_retrieval_hit"] = {
                "n": len(hit),
                "key_in_ans": round(sum(r["key_in_ans"] for r in hit) / len(hit), 4),
                "evidence_in_ans": round(sum(r["ev_in_ans"] for r in hit) / len(hit), 4),
            }
    return out


OFF_TOPIC = [
    "Who won the football World Cup in 2018?", "What is the capital city of Australia?",
    "How do I bake a chocolate cake?", "Who painted the Mona Lisa?",
    "What is the boiling point of water at sea level?", "When did the French Revolution begin?",
    "Who wrote the play Hamlet?", "How many players are in a cricket team?",
    "What is the tallest mountain in the world?", "Which planet is closest to the Sun?",
    "What are the symptoms of influenza?", "How does photosynthesis work in plants?",
]


def exp_abstention(records, qs):
    eng = RAGEngine()
    eng.build_index(records)

    def top(q):
        r = eng.retrieve(q, top_k=4)
        return r[0]["score"] if r else 0.0

    ins = [top(q[2]) for q in qs]
    off = [top(q) for q in OFF_TOPIC]
    answered_off = sum(1 for s in off if s > 0)
    sweep = []
    for tau in (0.0, 0.02, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30):
        sweep.append({"tau": tau,
                      "in_scope_answered": round(sum(s > tau for s in ins) / len(ins), 4),
                      "off_topic_refused": round(sum(s <= tau for s in off) / len(off), 4)})
    # best accuracy threshold (balanced)
    return {
        "n_off_topic": len(OFF_TOPIC), "off_topic_answered_by_shipped": answered_off,
        "off_topic_refused_by_shipped": len(OFF_TOPIC) - answered_off,
        "top1_score_in_scope": {"mean": round(float(np.mean(ins)), 4), "min": round(min(ins), 4), "p10": round(pct(ins, 10), 4), "median": round(pct(ins, 50), 4)},
        "top1_score_off_topic": {"mean": round(float(np.mean(off)), 4), "max": round(max(off), 4), "median": round(pct(off, 50), 4)},
        "sweep": sweep, "in_scope_scores": [round(s, 4) for s in ins], "off_topic_scores": [round(s, 4) for s in off],
    }


def exp_document_analysis(docs):
    out = {"per_file": []}
    for name in sorted(os.listdir(CORPUS)):
        text = clean_text(extract_text(os.path.join(CORPUS, name)))
        hints = detect_subject_hints(text)
        topics = extract_topics(text)
        units = re.findall(r"(?im)^\s*unit\s*\d+\s*[:\-]\s*(.+)$", text)
        found = sum(1 for u in units if u.strip() in hints)
        out["per_file"].append({"file": name, "units_in_file": len(units), "units_detected": found,
                                "hints": hints, "topics": topics})
    total = sum(f["units_in_file"] for f in out["per_file"])
    det = sum(f["units_detected"] for f in out["per_file"])
    out["unit_recall"] = round(det / total, 4)
    out["subject_line_detected"] = sum(1 for f in out["per_file"] if any(h.endswith(f["file"][3:-4].replace("_", " ")) for h in f["hints"]))
    # heading-format robustness on a small synthetic syllabus (5 units each)
    titles = ["Introduction to Arrays", "Stacks and Queues", "Linked Lists", "Trees and Traversals", "Graph Algorithms"]
    formats = {
        "Unit 1: Title": lambda i, t: f"Unit {i}: {t}",
        "Unit 1 - Title": lambda i, t: f"Unit {i} - {t}",
        "UNIT-I Title": lambda i, t: f"UNIT-{['I','II','III','IV','V'][i-1]} {t}",
        "Unit I: Title": lambda i, t: f"Unit {['I','II','III','IV','V'][i-1]}: {t}",
        "Module 1: Title": lambda i, t: f"Module {i}: {t}",
        "Chapter 1: Title": lambda i, t: f"Chapter {i}: {t}",
        "1. Title": lambda i, t: f"{i}. {t}",
    }
    filler = "This unit explains the idea, the operations on it, typical applications and the time complexity of each operation in detail. "
    fmt = {}
    for label, f in formats.items():
        body = "Subject: Data Structures\n\n" + "\n\n".join(f(i, t) + "\n" + filler * 3 for i, t in enumerate(titles, 1))
        hints = detect_subject_hints(body)
        got = sum(1 for t in titles if t in hints)
        fmt[label] = {"units_found": got, "of": len(titles)}
    out["heading_formats"] = fmt
    return out


def validate_question(q):
    opts = q["options"]
    ok_struct = len(opts) == 4 and len(set(opts)) == 4 and 0 <= q["answer_index"] < 4 and opts[q["answer_index"]] == q["topic"]
    sentence = q["question"].replace("Fill in the blank: ", "")
    ambiguous = any(re.search(r"\b" + re.escape(o) + r"\b", sentence, re.I) for i, o in enumerate(opts) if i != q["answer_index"])
    leak = re.search(r"\b" + re.escape(q["topic"]) + r"\b", sentence.replace("_____", " "), re.I) is not None
    return ok_struct, ambiguous, leak


def exp_quiz(records):
    by_doc = {}
    for r in records:
        by_doc.setdefault(r["doc_name"], []).append(r["text"])
    out = {"per_doc": {}}
    tot_q = tot_struct = tot_amb = tot_requested = tot_leak = 0
    times = []
    for name, chunks in by_doc.items():
        got = struct = amb = leak = 0
        for seed in range(30):
            random.seed(seed)
            t0 = time.perf_counter()
            qs = generate_quiz(chunks, num_questions=5, subject=name)
            times.append((time.perf_counter() - t0) * 1000)
            tot_requested += 5
            for q in qs:
                s, a, lk = validate_question(q)
                got += 1
                struct += s
                amb += a
                leak += lk
        out["per_doc"][name] = {"requested": 150, "generated": got, "structurally_valid": struct, "ambiguous_option_in_stem": amb, "answer_repeated_in_stem": leak}
        tot_q += got
        tot_struct += struct
        tot_amb += amb
        tot_leak += leak
    out.update({"requested": tot_requested, "generated": tot_q, "yield": round(tot_q / tot_requested, 4),
                "structurally_valid": round(tot_struct / tot_q, 4), "ambiguous_rate": round(tot_amb / tot_q, 4),
                "answer_repeated_in_stem_rate": round(tot_leak / tot_q, 4),
                "gen_ms_median": round(pct(times, 50), 2), "gen_ms_p95": round(pct(times, 95), 2)})
    # sample sets for the manual audit (seed 0, first 5 questions of every document)
    audit = []
    for name, chunks in by_doc.items():
        random.seed(0)
        for q in generate_quiz(chunks, num_questions=5, subject=name):
            audit.append({"file": name, "question": q["question"], "options": q["options"], "answer": q["options"][q["answer_index"]]})
    out["audit_sample"] = audit
    # tiny document (the bundled sample notes)
    sample = os.path.join(ROOT, "sample_data", "sample_notes_data_structures.txt")
    ch = chunk_text(clean_text(extract_text(sample)))
    yields = []
    for seed in range(30):
        random.seed(seed)
        yields.append(len(generate_quiz(ch, num_questions=5, subject="Data Structures")))
    out["sample_notes_yield"] = {"chunks": len(ch), "mean_questions": round(float(np.mean(yields)), 2), "min": min(yields)}
    return out


def exp_scaling(records, qs):
    out = []
    base = [r for r in records]
    for mult in (1, 2, 4, 8):
        recs = []
        for m in range(mult):
            for r in base:
                recs.append({**r, "doc_id": r["doc_id"] + 10 * m})
        eng = RAGEngine()
        t0 = time.perf_counter()
        eng.build_index(recs)
        build = (time.perf_counter() - t0) * 1000
        lat, alat = [], []
        for q in qs:
            t0 = time.perf_counter()
            eng.retrieve(q[2], top_k=4)
            lat.append((time.perf_counter() - t0) * 1000)
            t0 = time.perf_counter()
            eng.generate_answer(q[2], api_key=None, top_k=4)
            alat.append((time.perf_counter() - t0) * 1000)
        out.append({"chunks": len(recs), "words": sum(len(r["text"].split()) for r in recs),
                    "index_build_ms": round(build, 1), "retrieve_ms_median": round(pct(lat, 50), 2),
                    "retrieve_ms_p95": round(pct(lat, 95), 2), "answer_ms_median": round(pct(alat, 50), 2),
                    "answer_ms_p95": round(pct(alat, 95), 2)})
    return out


def exp_seeds_ci(rankings_first, n=72):
    """Bootstrap 95 % CI of Hit@4 and MRR for the shipped retriever."""
    rng = np.random.default_rng(0)
    fr = np.array([x if x else 0 for x in rankings_first])
    out = {}
    for name, f in {"hit1": lambda a: (a == 1).mean(), "hit4": lambda a: ((a > 0) & (a <= 4)).mean(),
                    "mrr10": lambda a: np.where(a > 0, 1 / np.maximum(a, 1), 0).mean()}.items():
        boots = [f(rng.choice(fr, size=len(fr), replace=True)) for _ in range(2000)]
        out[name] = [round(float(np.percentile(boots, 2.5)), 4), round(float(np.percentile(boots, 97.5)), 4)]
    return out


if __name__ == "__main__":
    t_start = time.time()
    records, docs = load_chunks()
    pos_of = {(r["doc_id"], r["chunk_index"]): i for i, r in enumerate(records)}
    with open(os.path.join(ROOT, "experiments", "chunks.json"), "w", encoding="utf-8") as f:
        json.dump([r["text"] for r in records], f)          # read by scripts/dense_baseline.py (git-ignored)
    qs = QUESTIONS
    texts = [r["text"] for r in records]
    ntexts = [norm(t) for t in texts]
    results = {
        "corpus": {"documents": docs, "chunks": len(records), "words": sum(d["words"] for d in docs),
                   "questions": len(qs), "off_topic_questions": len(OFF_TOPIC),
                   "evidence_intact_in_a_chunk": sum(1 for q in qs if any(norm(q[3]) in t for t in ntexts)),
                   "mean_chunk_words": round(float(np.mean([len(t.split()) for t in texts])), 1)},
    }
    print("corpus", results["corpus"])
    results["retrieval"] = exp_retrieval(records, qs)
    for k, v in results["retrieval"].items():
        print(f"{k:28s} hit1={v['hit'][1]:.3f} hit3={v['hit'][3]:.3f} hit4={v['hit'][4]:.3f} hit10={v['hit'][10]:.3f} mrr={v['mrr10']:.3f}")
    results["retrieval_ci_shipped"] = exp_seeds_ci(results["retrieval"]["tfidf_shipped (1-2gram)"]["first_rank"])
    results["chunk_sizes"] = exp_chunk_sizes(qs)
    for k, v in results["chunk_sizes"].items():
        print("chunk", k, v)
    results["compression"] = exp_compression(records, qs)
    print(json.dumps(results["compression"], indent=1)[:1800])
    results["abstention"] = exp_abstention(records, qs)
    print({k: v for k, v in results["abstention"].items() if k not in ("in_scope_scores", "off_topic_scores", "sweep")})
    results["document_analysis"] = exp_document_analysis(docs)
    print("unit recall", results["document_analysis"]["unit_recall"], results["document_analysis"]["heading_formats"])
    results["quiz"] = exp_quiz(records)
    print({k: v for k, v in results["quiz"].items() if k not in ("audit_sample", "per_doc")})
    results["scaling"] = exp_scaling(records, qs)
    for r in results["scaling"]:
        print(r)
    dm = os.path.join(ROOT, "experiments", "dense_meta.json")
    if os.path.exists(dm):
        with open(dm) as f:
            results["dense_meta"] = json.load(f)
    results["meta"] = {"python": sys.version.split()[0], "numpy": np.__version__,
                       "runtime_s": round(time.time() - t_start, 1)}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print("wrote", OUT)
