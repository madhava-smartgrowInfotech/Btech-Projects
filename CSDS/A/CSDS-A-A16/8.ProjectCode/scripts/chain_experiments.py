"""Runs the whole measurement chain sequentially (detached). python scripts/chain_experiments.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = [sys.executable, "-u", str(ROOT / "scripts" / "run_experiments.py")]
JOBS = [
    ["ablate", "real_only", "1", "--save"],
    ["eval"],
    ["ablate", "synth", "1", "200"],
    ["ablate", "real_only", "2"],
    ["ablate", "synth", "2", "200"],
    ["ablate", "real_only", "3"],
    ["ablate", "synth", "3", "200"],
    ["ablate", "synth", "1", "50"],
    ["ablate", "synth", "1", "800"],
]
log = open(ROOT / "experiments" / "chain.log", "a", buffering=1)
for j in JOBS:
    log.write("=== " + " ".join(j) + "\n")
    r = subprocess.run(RUN + j, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
    log.write(f"exit {r.returncode}\n")
log.write("CHAIN DONE\n")
