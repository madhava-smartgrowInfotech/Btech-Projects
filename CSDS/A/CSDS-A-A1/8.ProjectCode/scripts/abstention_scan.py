"""Measure the two scores behind the abstention rule for every evaluation question, through the running API.

For each of the 57 English questions in data/eval/qa.jsonl the script calls POST /policies/{id}/search (hybrid + re-rank, k = 7,
exactly what the answerer retrieves) and records the best final score and the best BM25 score of the returned clauses. Writes
docs/charts/abstention_scan.json and docs/charts/abstention_scatter.png.

    python scripts/abstention_scan.py          (PolicyLens API must be running on port 8101)
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8101/api"
OUT = ROOT / "docs" / "charts"
RERANK_FLOOR, BM25_FLOOR = 0.004, 9.0


def call(path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=headers, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def main():
    token = call("/auth/login", body={"email": "demo@policylens.app", "password": "Demo@12345"})["access_token"]
    slugs = {p["document"]["file_name"].replace(".pdf", ""): p["id"] for p in call("/policies", token)}
    rows = []
    for line in (ROOT / "data" / "eval" / "qa.jsonl").read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        pid = slugs.get(item["policy"])
        if pid is None:  # out-of-scope questions name a policy too; fall back to the first sample
            pid = next(iter(slugs.values()))
        res = call(f"/policies/{pid}/search", token, {"query": item["question"], "mode": "hybrid_rerank", "k": 7})
        items = res["items"]
        best = max((i["score"] for i in items), default=0.0)
        bm = max((i.get("bm25") or 0.0 for i in items), default=0.0)
        rows.append({"id": item["id"], "answerable": bool(item.get("answerable")), "best_score": best, "best_bm25": bm,
                     "abstains": best < RERANK_FLOOR and bm < BM25_FLOOR})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "abstention_scan.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    ans = [r for r in rows if r["answerable"]]
    out = [r for r in rows if not r["answerable"]]
    print("answerable", len(ans), "wrongly abstained:", sum(r["abstains"] for r in ans))
    print("out-of-scope", len(out), "abstained:", sum(r["abstains"] for r in out))
    print("answerable min score %.4f min bm25 %.1f | out-of-scope max score %.4f max bm25 %.1f" % (
        min(r["best_score"] for r in ans), min(r["best_bm25"] for r in ans), max(r["best_score"] for r in out), max(r["best_bm25"] for r in out)))

    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    ax.scatter([r["best_score"] for r in ans], [r["best_bm25"] for r in ans], s=26, c="#6d5bd0", label=f"answerable ({len(ans)})", alpha=0.85)
    ax.scatter([r["best_score"] for r in out], [r["best_bm25"] for r in out], s=46, c="#d1495b", marker="X", label=f"out-of-scope ({len(out)})")
    ax.axvline(RERANK_FLOOR, color="#555", ls="--", lw=1)
    ax.axhline(BM25_FLOOR, color="#555", ls="--", lw=1)
    ax.fill_betweenx([0, BM25_FLOOR], 0, RERANK_FLOOR, color="#e08a2c", alpha=0.18)
    ax.text(RERANK_FLOOR * 1.05, BM25_FLOOR * 0.45, "abstain\n(both low)", fontsize=8, color="#8a5a1a")
    ax.set_xscale("symlog", linthresh=0.001)
    ax.set_xlabel("best re-rank score of the retrieved clauses (symlog axis)")
    ax.set_ylabel("best BM25 score")
    ax.set_title("Abstention rule: re-rank < 0.004 and BM25 < 9.0", fontsize=9.5, fontweight="bold")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "abstention_scatter.png", dpi=150)
    print("saved", OUT / "abstention_scatter.png")


if __name__ == "__main__":
    main()
