"""PeerScope dataset preparation: try public PeerRead-style source, else realistic synthetic fallback."""
from __future__ import annotations

import csv
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "data" / "processed_dataset.csv"

RANDOM_SEED = 42

TOPICS = [
    ("vision", ["image", "detection", "segmentation", "convolutional", "benchmark", "pixels", "backbone"]),
    ("language", ["transformer", "tokens", "pretraining", "summarization", "retrieval", "benchmark", "corpus"]),
    ("learning", ["gradient", "regularization", "generalization", "optimization", "ablation", "baseline", "tuning"]),
    ("systems", ["throughput", "latency", "distributed", "scheduling", "measurement", "cluster", "overhead"]),
    ("security", ["anomaly", "threat", "detection", "audit", "robustness", "adversarial", "protocol"]),
    ("data", ["dataset", "annotation", "sampling", "bias", "curation", "statistics", "splits"]),
]

STRONG = ["thorough evaluation", "clear methodology", "strong baselines", "reproducible setup",
          "comprehensive ablations", "well-calibrated results", "careful error analysis"]
WEAK = ["missing baselines", "unclear methodology", "limited evaluation", "small dataset",
        "no ablations", "unsupported claims", "incomplete analysis"]


def try_public_download() -> list[dict] | None:
    """Attempt to fetch a small public PeerRead mirror; return None when unavailable."""
    import requests

    # AllenAI PeerRead repository hosts parsed reviews; raw parquet mirrors move often,
    # so we attempt a lightweight probe with a strict timeout and fall back on any failure.
    urls = [
        "https://raw.githubusercontent.com/allenai/PeerRead/main/data/iclr_2017/train/reviews.tsv",
    ]
    try:
        r = requests.get(urls[0], timeout=6)
        if r.status_code != 200 or not r.text.strip():
            return None
        rows: list[dict] = []
        lines = r.text.splitlines()
        for ln in lines[1:400]:
            parts = ln.split("\t")
            if len(parts) < 2:
                continue
            rows.append({"title": parts[0][:200], "text": ln[:2000], "label": "borderline"})
        return rows or None
    except Exception:
        return None


def synthetic_dataset(n: int = 1400, seed: int = RANDOM_SEED) -> tuple[list[dict], bool]:
    rng = random.Random(seed)
    rows: list[dict] = []
    for i in range(n):
        topic, vocab = rng.choice(TOPICS)
        quality = rng.random()
        if quality > 0.52:
            label = "accept" if quality > 0.72 else "borderline"
            desc = ", ".join(rng.sample(STRONG, 3))
        else:
            label = "reject" if quality < 0.30 else "borderline"
            desc = ", ".join(rng.sample(WEAK, 3))
        words = rng.sample(vocab, 4) + desc.split()
        title = f"{topic.title()} study {i}: {' '.join(rng.sample(vocab, 2))} with evaluation"
        text = (f"This paper studies {topic} using {' '.join(rng.sample(vocab, 3))}. "
                f"The contribution involves {desc}. Experiments compare baselines on a {topic} benchmark "
                f"with ablations, error analysis, and reproducibility notes. {' '.join(words[:12])}.")
        rows.append({"title": title, "text": text, "label": label})
    return rows, True


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = try_public_download()
    synthetic = False
    source = "public-mirror"
    if not rows or len(rows) < 200:
        rows, synthetic = synthetic_dataset()
        source = "synthetic-fallback"
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "text", "label", "source"])
        w.writeheader()
        for r in rows:
            w.writerow({"title": r["title"], "text": r["text"], "label": r["label"], "source": source})
    from collections import Counter

    print(f"Wrote {len(rows)} rows -> {OUT} (source={source}, synthetic={synthetic})")
    print("Class distribution:", dict(Counter(r['label'] for r in rows)))


if __name__ == "__main__":
    main()
