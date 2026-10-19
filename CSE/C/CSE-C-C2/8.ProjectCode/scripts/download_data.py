"""StoryVox evaluation dataset downloader with local caching.

Prefers small public Hugging Face subsets (FLEURS / Common Voice style data).
Falls back to a clearly labeled synthetic evaluation set when the network or
dataset access is unavailable, so the build never stops on download errors.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("storyvox.data")

SYNTHETIC_SAMPLES = [
    {"text": "The young inventor opened the hidden library and the books began to glow.", "language_code": "en"},
    {"text": "A kind robot carried lanterns through the storm to guide the village home.", "language_code": "en"},
    {"text": "Le jardin secret cachait une porte vers les etoiles.", "language_code": "fr"},
    {"text": "Der mutige Baecker teilte warmes Brot mit dem ganzen Dorf.", "language_code": "de"},
    {"text": "Una nina siguio a una luciernaga hasta el bosque magico.", "language_code": "es"},
    {"text": "Ek chhota ladka sitaron se baat karta tha.", "language_code": "hi"},
]


def write_synthetic(target: Path, reason: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"provenance": "synthetic", "note": f"Synthetic evaluation data ({reason}). Functional testing only.", "samples": SYNTHETIC_SAMPLES}
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote synthetic evaluation set: %s", target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="StoryVox dataset downloader")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--dataset", default="google/fleurs")
    parser.add_argument("--out", default="data/datasets/eval_set.json")
    args = parser.parse_args()

    from app.config import BASE_DIR

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = BASE_DIR / out_path
    if out_path.exists():
        logger.info("Dataset cache hit: %s (skipping download)", out_path)
        return
    try:
        from datasets import load_dataset

        ds = load_dataset(args.dataset, "en_us", split=f"test[:{args.limit}]", trust_remote_code=True)
        samples = [{"text": str(r.get("transcription") or r.get("text") or ""), "language_code": "en"} for r in ds]
        samples = [s for s in samples if s["text"].strip()][: args.limit]
        if not samples:
            raise RuntimeError("Dataset returned no usable rows.")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({"provenance": "huggingface", "dataset": args.dataset, "samples": samples}, indent=2), encoding="utf-8")
        logger.info("Downloaded %d samples to %s", len(samples), out_path)
    except Exception as exc:
        logger.warning("Dataset download failed (%s). Creating synthetic set instead.", exc)
        write_synthetic(out_path, reason=str(exc)[:160])


if __name__ == "__main__":
    main()
