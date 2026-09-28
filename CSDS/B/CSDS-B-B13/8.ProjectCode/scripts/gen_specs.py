"""Generate and commit each practice target's OpenAPI spec so it can be imported
without the target having to be running. Run: python scripts/gen_specs.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from targets import demopay, vulnbank  # noqa: E402

OUT = ROOT / "targets"


def dump(app, name: str):
    spec = app.openapi()
    path = OUT / f"{name}_openapi.json"
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(spec.get('paths', {}))} paths)")


if __name__ == "__main__":
    dump(demopay.app, "demopay")
    dump(vulnbank.app, "vulnbank")
