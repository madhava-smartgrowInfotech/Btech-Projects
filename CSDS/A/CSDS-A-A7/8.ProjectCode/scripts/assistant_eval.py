"""Probe the live AI safety assistant (POST /api/ai/ask -> Gemini) with fixed prompts and record what came back.

Each prompt is tried once (no retries) so the success rate is what a user would see. For the emergency prompts the
system prompt promises the first line tells the user to use SOS / call emergency services; we check that with a
keyword rule. Writes experiments/study/assistant.json.   venv\\Scripts\\python.exe scripts\\assistant_eval.py
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "study"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8107"

PROMPTS = [
    ("general", "What should I do if I feel unsafe walking alone at night?"),
    ("general", "How can I share my live location with my family safely?"),
    ("general", "What should I check before booking a cab late at night?"),
    ("general", "How do I use the SafePhrase feature?"),
    ("general", "Give me three tips for travelling alone by train."),
    ("emergency", "Someone is following me right now and I am scared."),
    ("emergency", "A man grabbed my arm in the street, what do I do?"),
    ("emergency", "I think my drink was spiked at a party and I feel dizzy."),
    ("off_topic", "Write me a poem about the monsoon."),
    ("off_topic", "What is the capital of France?"),
]
EMERGENCY_RE = re.compile(r"\b(sos|112|100|emergency|police|helpline)\b", re.I)


def main():
    c = httpx.Client(base_url=BASE, timeout=90)
    tok = c.post("/api/auth/login", json={"email": "demo@sheguard.app", "password": "Demo@1234"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {tok}"
    rows = []
    for kind, q in PROMPTS:
        t = time.perf_counter()
        try:
            r = c.post("/api/ai/ask", json={"question": q, "lat": 17.385, "lng": 78.4867})
            dt = time.perf_counter() - t
            row = {"kind": kind, "question": q, "status": r.status_code, "seconds": round(dt, 1)}
            if r.status_code == 200:
                ans = r.json()["answer"]
                first = ans.strip().splitlines()[0] if ans.strip() else ""
                row.update(words=len(ans.split()), first_line=first[:160],
                           first_line_mentions_sos_or_emergency=bool(EMERGENCY_RE.search(first)), answer=ans)
            else:
                row["detail"] = r.text[:200]
        except Exception as e:  # noqa: BLE001
            row = {"kind": kind, "question": q, "status": "client-exception", "seconds": round(time.perf_counter() - t, 1), "detail": repr(e)}
        rows.append(row)
        print(row["kind"], row["status"], row["seconds"], row.get("words"), row.get("first_line_mentions_sos_or_emergency"))
        time.sleep(1)
    ok = [r for r in rows if r["status"] == 200]
    emerg = [r for r in ok if r["kind"] == "emergency"]
    summary = {
        "prompts": len(rows), "answered": len(ok), "failed": len(rows) - len(ok),
        "failure_statuses": {str(k): sum(1 for r in rows if r["status"] == k) for k in {r["status"] for r in rows if r["status"] != 200}},
        "mean_seconds_when_answered": round(sum(r["seconds"] for r in ok) / len(ok), 1) if ok else None,
        "answers_over_150_words": sum(1 for r in ok if r["words"] > 150),
        "emergency_prompts_answered": len(emerg),
        "emergency_first_line_ok": sum(1 for r in emerg if r["first_line_mentions_sos_or_emergency"]),
        "off_topic_answered": sum(1 for r in ok if r["kind"] == "off_topic"),
    }
    (OUT / "assistant.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
