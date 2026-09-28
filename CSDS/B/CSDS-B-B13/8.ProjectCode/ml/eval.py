"""Evaluation: scan every practice target, compare findings with each target's
known-vulnerability list, and write the objective metrics.

Run (with the target apps running): python ml/eval.py
Writes: experiments/eval/metrics.json
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.ai_tests import run_ai_tests  # noqa: E402
from app.services.scanner import scan_target  # noqa: E402
from app.services.spec_parser import parse_spec  # noqa: E402
from app.services.validation import validate  # noqa: E402

TARGETS = ["demopay", "vulnbank"]


async def eval_target(name: str) -> dict:
    spec_text = (ROOT / "targets" / f"{name}_openapi.json").read_text(encoding="utf-8")
    meta = json.loads((ROOT / "targets" / f"{name}_vulns.json").read_text(encoding="utf-8"))
    base_url, endpoints, _ = parse_spec(spec_text)
    base_url = meta.get("base_url") or base_url

    result = await scan_target(base_url, endpoints, meta.get("auth", {}))
    findings = [f for f in result["findings"] if f["severity"] != "info"]
    v = validate(meta.get("known_vulns", []), findings)

    ai_results, generator = await run_ai_tests(base_url, endpoints, meta.get("auth", {}))
    ai_vuln = sum(1 for t in ai_results if t["result"] == "vulnerable")

    return {
        "target": meta.get("target", name),
        "base_url": base_url,
        "endpoints": len(endpoints),
        "score": result["score"],
        "grade": result["grade"],
        "findings": len(findings),
        "detection_rate": v["detection_rate"],
        "detected": v["detected_count"],
        "known_total": v["total_known"],
        "missed": v["missed_count"],
        "missed_items": v["missed"],
        "false_positives": v["false_positive_count"],
        "ai_tests": len(ai_results),
        "ai_vulnerable": ai_vuln,
        "ai_generator": generator,
    }


async def main():
    per_target = []
    for name in TARGETS:
        try:
            per_target.append(await eval_target(name))
        except Exception as exc:  # noqa: BLE001
            per_target.append({"target": name, "error": str(exc)})

    ok = [t for t in per_target if "error" not in t]
    total_known = sum(t["known_total"] for t in ok)
    total_detected = sum(t["detected"] for t in ok)
    total_fp = sum(t["false_positives"] for t in ok)
    overall = round(100 * total_detected / total_known, 1) if total_known else 0.0

    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "targets_evaluated": len(ok),
        "overall_detection_rate": overall,
        "total_known_vulns": total_known,
        "total_detected": total_detected,
        "total_false_positives": total_fp,
        "per_target": per_target,
    }

    out_dir = ROOT / "experiments" / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    print(f"\nWrote {out_path.relative_to(ROOT)}")
    print(f"Overall detection rate: {overall}%  "
          f"({total_detected}/{total_known}), false positives: {total_fp}")


if __name__ == "__main__":
    asyncio.run(main())
