"""
Writes the facts the documents quote about the machine, the software and the test runs:
experiments/environment.json and experiments/test_run.json.

    python scripts/collect_env.py            # project .venv; backend 8407 + frontend 5407 must be running for the smoke/UI checks
"""
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from importlib.metadata import version

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments")
os.makedirs(EXP, exist_ok=True)


def cmd(args, **kw):
    try:
        return subprocess.run(args, capture_output=True, text=True, shell=True, timeout=600, cwd=ROOT, **kw)
    except Exception:
        return None


def ps(expr):
    r = cmd(f'powershell -NoProfile -Command "{expr}"')
    return r.stdout.strip() if r else None


def main():
    env = {
        "os": platform.platform(), "cpu": ps("(Get-CimInstance Win32_Processor).Name"), "cores": ps("(Get-CimInstance Win32_Processor).NumberOfCores"),
        "logical_processors": ps("(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors"),
        "ram_gb": ps("[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"), "gpu": "none used (CPU only)",
        "python": platform.python_version(),
        "packages": {p: version(p) for p in ("fastapi", "uvicorn", "sqlalchemy", "pydantic", "pandas", "numpy", "scikit-learn", "xgboost", "joblib", "matplotlib", "passlib", "pytest")},
        "node": (cmd("node --version").stdout or "").strip(), "npm": (cmd("npm --version").stdout or "").strip(),
        "pinned_requirements": open(os.path.join(ROOT, "requirements.txt")).read().split(),
    }
    fp = json.load(open(os.path.join(ROOT, "frontend", "package.json")))
    env["frontend_dependencies"] = {**fp["dependencies"], **fp["devDependencies"]}
    json.dump(env, open(os.path.join(EXP, "environment.json"), "w", encoding="utf-8"), indent=2)

    res = {"date": time.strftime("%Y-%m-%d %H:%M")}
    xml = os.path.join(EXP, "pytest_junit.xml")
    t0 = time.time()
    p = cmd(f'"{sys.executable}" -m pytest tests -q -p no:cacheprovider --junitxml="{xml}" -W ignore')
    secs = time.time() - t0
    root = ET.parse(xml).getroot()
    names, fail = [], 0
    for tc in root.iter("testcase"):
        names.append(tc.get("name"))
        if tc.find("failure") is not None or tc.find("error") is not None:
            fail += 1
    os.remove(xml)
    res["pytest"] = {"collected": len(names), "passed": len(names) - fail, "failed": fail, "seconds": round(secs, 1), "tests": names, "exit_code": p.returncode}
    p = cmd(f'"{sys.executable}" scripts/smoke_test.py')
    passed = len(re.findall(r"^PASS ", p.stdout, re.M))
    failed = len(re.findall(r"^FAIL ", p.stdout, re.M))
    res["smoke"] = {"checks": passed + failed, "passed": passed, "failed": failed, "exit_code": p.returncode}
    t0 = time.time()
    p = cmd(f'"{sys.executable}" scripts/check_responsive.py')
    res["responsive"] = {"screens_private": 6, "screens_public": 5, "widths_px": [360, 768, 1440], "themes": ["light", "dark"], "passed": p.returncode == 0,
                         "seconds": round(time.time() - t0), "tail": p.stdout.strip().splitlines()[-1:]}
    json.dump(res, open(os.path.join(EXP, "test_run.json"), "w", encoding="utf-8"), indent=2)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
