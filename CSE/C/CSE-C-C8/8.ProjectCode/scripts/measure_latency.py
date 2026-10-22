"""Time the PeerScope pipeline stage by stage and over HTTP.

    python scripts/measure_latency.py stages    # in-process: every stage of one analysis, incl. local-LLM load and 3-step review
    python scripts/measure_latency.py api       # against a running API on 127.0.0.1:8408 (start it with the LLM disabled, see below)

For the HTTP part start the API with the local model switched off so the numbers are the deterministic path:
    set PEERSCOPE_LLM_MODEL=disabled & set PEERSCOPE_LLM_FALLBACK=disabled & python -m uvicorn app.main:app --port 8408
Results are merged into docs/metrics/latency.json. Use 127.0.0.1, not localhost (IPv6 fallback adds ~2 s per call on this machine).
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH = ROOT.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "metrics" / "latency.json"
R = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
DEMO = ROOT / "data" / "demo" / "demo_paper.pdf"
SURVEY = next((BATCH / "archived_base_papers").glob("BASEPAPER_Can_AI*.pdf"))


def save():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(R, indent=2), encoding="utf-8")


def stages():
    from types import SimpleNamespace

    from app.services import features as feat_svc
    from app.services import literature as lit_svc
    from app.services import llm_service
    from app.services import matching as match_svc
    from app.services import ml_predict as ml_svc
    from app.services import pdf_extract as pdf_svc
    from app.services import review_synthesis as rev_svc
    from app.services.embeddings import _get_model
    from app.services.seed import DEMO_REVIEWERS

    revs = [SimpleNamespace(id=i + 1, **d) for i, d in enumerate(DEMO_REVIEWERS)]
    t0 = time.perf_counter(); _get_model(); R["embedding_model_load_s"] = round(time.perf_counter() - t0, 1); save()
    ml_svc.predict_decision("warm", "up")
    t0 = time.perf_counter(); llm = llm_service.ensure_llm(); R["llm_load_s"] = round(time.perf_counter() - t0, 1)
    R["llm_status"] = llm_service.llm_status(); save()
    print("llm status", R["llm_status"], flush=True)
    runs = {}
    for label, pdf in (("demo", DEMO), ("survey_30_pages", SURVEY)):
        s = {}
        t = time.perf_counter(); doc = pdf_svc.extract_pdf(pdf); s["PDF extraction"] = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); feats = feat_svc.extract_features(doc); s["Feature extraction"] = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); ml_svc.predict_decision(doc["title"], doc["paper_summary"], doc["full_text"]); s["Decision signal"] = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); review = rev_svc.llm_review(doc, feats); s["Local AI review (3 steps)"] = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); lit = lit_svc.retrieve_literature(doc["title"], feats["keywords"], feats["research_topics"]); s["Literature (OpenAlex)"] = (time.perf_counter() - t) * 1000
        prof = match_svc.paper_profile(doc["title"], doc["paper_summary"], feats["keywords"], feats["methodology_terms"], feats["research_topics"])
        t = time.perf_counter(); match_svc.match_reviewers(prof, revs, doc["full_text"][:4000]); s["Reviewer matching"] = (time.perf_counter() - t) * 1000
        s = {k: round(v, 1) for k, v in s.items()}
        s["_total_ms"] = round(sum(s.values()), 1)
        s["_llm_status"] = review.get("llm_status")
        s["_ai_chars"] = len(review.get("ai_synthesis", "") or "")
        s["_literature_status"] = lit.get("literature_retrieval_status")
        if review.get("llm_status") == "ok":
            tok = llm.tokenizer
            s["_ai_tokens_synthesis"] = len(tok(review["ai_synthesis"])["input_ids"])
            s["_ai_tokens_all_steps"] = sum(len(tok(review.get(k, ""))["input_ids"]) for k in ("ai_analysis_step", "ai_critique_step", "ai_synthesis"))
            s["_llm_model"] = review.get("llm_model")
        else:
            s["_llm_note"] = review.get("llm_note")
        runs[label] = s
        print(label, s, flush=True)
        R["pipeline_stages"] = runs
        R["pipeline_stage_ms_demo"] = {k: v for k, v in runs["demo"].items() if not k.startswith("_")}
        save()


def api():
    import requests

    base = "http://127.0.0.1:8408"
    s = requests.Session()
    out = {}
    for name, path in (("health", "/api/health"), ("reviewers_list", "/api/reviewers"), ("model_metrics", "/api/model/metrics"), ("analyses_list", "/api/analyses")):
        ts = []
        for _ in range(40):
            t = time.perf_counter(); r = s.get(base + path, timeout=30); ts.append((time.perf_counter() - t) * 1000)
            assert r.status_code == 200, (path, r.status_code)
        ts.sort()
        out[name] = {"n": 40, "median_ms": round(st.median(ts), 1), "p95_ms": round(ts[int(0.95 * len(ts)) - 1], 1), "max_ms": round(ts[-1], 1)}
    for label, pdf, n in (("analyze_demo_3_pages", DEMO, 8), ("analyze_survey_30_pages", SURVEY, 4)):
        ts = []
        for _ in range(n):
            with open(pdf, "rb") as fh:
                t = time.perf_counter(); r = s.post(base + "/api/analyze", files={"file": (pdf.name, fh, "application/pdf")}, data={"active_only": "true"}, timeout=900)
                ts.append((time.perf_counter() - t) * 1000)
            assert r.status_code == 200, r.text[:200]
        out[label] = {"n": n, "median_ms": round(st.median(ts), 1), "min_ms": round(min(ts), 1), "max_ms": round(max(ts), 1),
                      "llm_status": r.json()["review"].get("llm_status"), "literature_status": r.json()["literature"]["literature_retrieval_status"]}
        aid = r.json()["analysis_id"]
    t = time.perf_counter(); r = s.get(f"{base}/api/analyses/{aid}/export?format=pdf", timeout=60); out["export_pdf"] = {"median_ms": round((time.perf_counter() - t) * 1000, 1), "bytes": len(r.content)}
    t = time.perf_counter(); r = s.get(f"{base}/api/analyses/{aid}/export?format=json", timeout=60); out["export_json"] = {"median_ms": round((time.perf_counter() - t) * 1000, 1), "bytes": len(r.content)}
    R["http_api"] = out
    save()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    {"stages": stages, "api": api}[sys.argv[1]]()
