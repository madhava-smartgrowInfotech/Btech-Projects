"""StoryVox reproducible evaluation entrypoint.

Example:
    python scripts/evaluate.py --samples 5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db  # noqa: E402
from app.services.evaluation_service import run_evaluation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="StoryVox evaluation pipeline")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--language", default=None)
    parser.add_argument("--skip-tts", action="store_true")
    parser.add_argument("--skip-story", action="store_true")
    args = parser.parse_args()
    init_db()
    metrics = run_evaluation(samples=args.samples, language_code=args.language, skip_tts=args.skip_tts, skip_story=args.skip_story)
    avg = metrics.get("averages", {})
    print("StoryVox evaluation complete")
    print(f"  samples: {metrics.get('sample_count')}")
    print(f"  WER: {avg.get('wer')}  CER: {avg.get('cer')}")
    print(f"  similarity: {avg.get('prompt_story_similarity')}  ROUGE-L: {avg.get('rougeL_prompt_vs_story')}")
    print(f"  story latency: {avg.get('story_time_s')}s  TTS latency: {avg.get('tts_time_s')}s  RTF: {avg.get('rtf')}")
    print(json.dumps(avg, indent=2))


if __name__ == "__main__":
    main()
