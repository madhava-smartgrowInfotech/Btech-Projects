"""Run the pytest suite and record the outcome in experiments/tests/metrics.json (documentation run)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
t0 = time.perf_counter()
proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-v", "--tb=short", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True,
                      encoding="utf-8", errors="replace")
secs = round(time.perf_counter() - t0, 1)
out = proc.stdout
cases = []
for m in re.finditer(r"^(tests/\S+)::(\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)", out, re.M):
    cases.append({"file": m.group(1), "name": m.group(2), "result": m.group(3)})
summary = re.findall(r"=+ (.*?) in ([\d.]+)s", out)
res = {"experiment": "pytest", "python": sys.version.split()[0], "seconds": secs, "exit_code": proc.returncode,
       "summary_line": summary[-1][0] if summary else None, "cases": cases,
       "passed": sum(c["result"] == "PASSED" for c in cases), "failed": sum(c["result"] in ("FAILED", "ERROR") for c in cases),
       "by_file": {}}
for c in cases:
    d = res["by_file"].setdefault(c["file"], {"total": 0, "passed": 0})
    d["total"] += 1
    d["passed"] += c["result"] == "PASSED"
d = ROOT / "experiments" / "tests"
d.mkdir(parents=True, exist_ok=True)
(d / "metrics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
print(out[-3000:])
print("saved", d / "metrics.json")
