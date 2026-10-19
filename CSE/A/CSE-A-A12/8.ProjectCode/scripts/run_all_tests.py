"""
Runs the whole verification set and records the counts the documents quote (experiments/test_run.json).

    python scripts/run_all_tests.py [--base http://localhost:8312] [--ui http://localhost:5312] [--skip-ui]

* pytest (no servers needed): per-file pass counts and total time
* smoke test (API server needed)
* UI verification (API + front end needed)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8312")
    ap.add_argument("--ui", default="http://localhost:5312")
    ap.add_argument("--skip-ui", action="store_true")
    ap.add_argument("--skip-servers", action="store_true", help="only run pytest")
    a = ap.parse_args()
    res = {"date": time.strftime("%Y-%m-%d %H:%M")}

    xml = os.path.join(ROOT, "experiments", "pytest_junit.xml")
    t0 = time.time()
    p = run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", "-W", "ignore"])
    secs = time.time() - t0
    root = ET.parse(xml).getroot()
    per = {}
    tot = fail = skip = 0
    for tc in root.iter("testcase"):
        f = tc.get("classname", "").replace(".", "/")
        f = "tests/" + f.split("/")[-1] + ".py"
        per[f] = per.get(f, 0) + 1
        tot += 1
        if tc.find("failure") is not None or tc.find("error") is not None:
            fail += 1
        if tc.find("skipped") is not None:
            skip += 1
    res["pytest"] = {"collected": tot, "passed": tot - fail - skip, "failed": fail, "skipped": skip, "seconds": round(secs, 1), "per_file": per, "exit_code": p.returncode}
    print("pytest:", res["pytest"])
    os.remove(xml)

    if not a.skip_servers:
        p = run([sys.executable, "scripts/smoke_test.py", "--base", a.base])
        passed = len(re.findall(r"^\[PASS\]", p.stdout, re.M))
        failed = len(re.findall(r"^\[FAIL\]", p.stdout, re.M))
        res["smoke"] = {"checks": passed + failed, "passed": passed, "failed": failed, "exit_code": p.returncode}
        print("smoke:", res["smoke"])
        if not a.skip_ui:
            t0 = time.time()
            p = run([sys.executable, "scripts/verify_ui.py", "--base", a.ui])
            ok = p.returncode == 0
            res["ui"] = {"configurations": 6, "passed": ok, "seconds": round(time.time() - t0), "exit_code": p.returncode,
                         "tail": p.stdout.strip().splitlines()[-3:]}
            print("ui:", res["ui"])
    json.dump(res, open(os.path.join(ROOT, "experiments", "test_run.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
