"""Generate the committed SAMPLE call recordings from data/sample/scripts/calls.json (seeded, offline voices).

Each script becomes data/sample/calls/<id>.flac (agent = left channel, customer = right channel) plus
<id>.json with the exact line timings, which the evaluation uses as ground truth.
Usage: python scripts/generate_sample_calls.py [script_id ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import SAMPLE_CALLS_DIR  # noqa: E402
from app.services.studio import load_scripts, synthesize  # noqa: E402


def main(only):
    SAMPLE_CALLS_DIR.mkdir(parents=True, exist_ok=True)
    for i, script in enumerate(load_scripts()):
        if only and script["id"] not in only:
            continue
        out = SAMPLE_CALLS_DIR / f"{script['id']}.flac"
        ref = synthesize(script["lines"], out, seed=100 + i)
        meta = {k: script[k] for k in ("id", "title", "intent", "agent", "day_offset")}
        meta.update(ref, sample=True)
        (SAMPLE_CALLS_DIR / f"{script['id']}.json").write_text(json.dumps(meta, indent=1))
        print(f"{out.name}: {ref['duration']}s, {len(ref['lines'])} lines")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
