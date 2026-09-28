"""Local code judge: one subprocess per test inside a fresh temp folder, with a wall-clock time limit,
an output-size cap and a heap cap for Java. Verdicts: Accepted, Wrong Answer, Time Limit Exceeded,
Runtime Error, Compile Error."""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ..config import GXX_PATH, JAVA_PATH, JAVAC_PATH, JUDGE_MAX_OUTPUT, JUDGE_TIME_LIMIT

LANGS = {"python": "Python 3", "cpp": "C++17", "java": "Java 17"}
TIME_FACTOR = {"python": 1.5, "cpp": 1.0, "java": 1.5}
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

TEMPLATES = {
    "python": "import sys\n\ndef main():\n    data = sys.stdin.read().split()\n    # write your solution here\n\nmain()\n",
    "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    // write your solution here\n    return 0;\n}\n",
    "java": "import java.util.*;\nimport java.io.*;\n\npublic class Main {\n    public static void main(String[] args) throws IOException {\n        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        // write your solution here\n    }\n}\n",
}


def _find_gxx():
    if GXX_PATH:
        return GXX_PATH
    found = shutil.which("g++")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA", "")
    hits = glob.glob(os.path.join(local, "Microsoft", "WinGet", "Packages", "*WinLibs*", "mingw64", "bin", "g++.exe"))
    hits += glob.glob(r"C:\msys64\ucrt64\bin\g++.exe") + glob.glob(r"C:\msys64\mingw64\bin\g++.exe")
    return hits[0] if hits else None


def _find_java(name, override):
    if override:
        return override
    found = shutil.which(name)
    if found:
        return found
    home = os.environ.get("JAVA_HOME")
    if home and os.path.exists(os.path.join(home, "bin", name + ".exe")):
        return os.path.join(home, "bin", name + ".exe")
    return None


def toolchain():
    return {"python": sys.executable, "cpp": _find_gxx(), "java": _find_java("javac", JAVAC_PATH) and _find_java("java", JAVA_PATH),
            "javac": _find_java("javac", JAVAC_PATH)}


def available_languages():
    t = toolchain()
    return [{"id": k, "name": v, "available": bool(t[k]), "template": TEMPLATES[k]} for k, v in LANGS.items()]


def _env(extra_path=None):
    env = {k: v for k, v in os.environ.items() if k.upper() in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "JAVA_HOME")}
    if extra_path:
        env["PATH"] = extra_path + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def normalise(out):
    lines = [ln.rstrip() for ln in out.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def _compile(lang, code, work):
    tc = toolchain()
    if lang == "python":
        (work / "main.py").write_text(code, encoding="utf-8")
        return [tc["python"], "-I", "main.py"], None, None
    if lang == "cpp":
        if not tc["cpp"]:
            return None, "C++ compiler (g++) is not installed on this server", None
        (work / "main.cpp").write_text(code, encoding="utf-8")
        gxx = tc["cpp"]
        exe = "main.exe" if os.name == "nt" else "main"
        r = subprocess.run([gxx, "-O2", "-std=c++17", "-static", "-o", exe, "main.cpp"], cwd=work, capture_output=True,
                           timeout=60, creationflags=NO_WINDOW, env=_env(str(Path(gxx).parent)))
        if r.returncode != 0:
            return None, r.stderr.decode(errors="replace")[-3000:], None
        return [str(work / exe)], None, None
    if lang == "java":
        if not tc["java"]:
            return None, "Java (JDK 17) is not installed on this server", None
        (work / "Main.java").write_text(code, encoding="utf-8")
        r = subprocess.run([tc["javac"], "-encoding", "UTF-8", "Main.java"], cwd=work, capture_output=True, timeout=60,
                           creationflags=NO_WINDOW, env=_env())
        if r.returncode != 0:
            return None, r.stderr.decode(errors="replace")[-3000:], None
        java = _find_java("java", JAVA_PATH)
        return [java, "-Xmx256m", "-Xss64m", "-XX:+UseSerialGC", "-XX:TieredStopAtLevel=1", "-cp", ".", "Main"], None, None
    return None, f"Unsupported language: {lang}", None


def judge(lang, code, tests, stop_on_fail=True, show_io=False):
    """Run code against tests [{input, output}]. Returns a result dict."""
    if lang not in LANGS:
        return {"verdict": "Compile Error", "passed": 0, "total": len(tests), "time_ms": 0,
                "message": f"Unsupported language: {lang}", "tests": []}
    limit = JUDGE_TIME_LIMIT * TIME_FACTOR[lang]
    with tempfile.TemporaryDirectory(prefix="tt_judge_") as tmp:
        work = Path(tmp)
        try:
            cmd, err, _ = _compile(lang, code, work)
        except subprocess.TimeoutExpired:
            cmd, err = None, "Compilation took too long"
        if err:
            return {"verdict": "Compile Error", "passed": 0, "total": len(tests), "time_ms": 0, "message": err, "tests": []}
        results, verdict, passed, max_ms, message = [], "Accepted", 0, 0, ""
        for i, t in enumerate(tests, 1):
            start = time.perf_counter()
            status, out, err_text = "Accepted", "", ""
            try:
                r = subprocess.run(cmd, input=t["input"].encode(), capture_output=True, timeout=limit, cwd=work,
                                   creationflags=NO_WINDOW, env=_env())
                out = r.stdout.decode(errors="replace")
                err_text = r.stderr.decode(errors="replace")[-1500:]
                if r.returncode != 0:
                    status = "Runtime Error"
                elif len(r.stdout) > JUDGE_MAX_OUTPUT:
                    status, err_text = "Wrong Answer", "Output limit exceeded"
                elif normalise(out) != normalise(t["output"]):
                    status = "Wrong Answer"
            except subprocess.TimeoutExpired:
                status = "Time Limit Exceeded"
            ms = int((time.perf_counter() - start) * 1000)
            max_ms = max(max_ms, ms)
            row = {"test": i, "status": status, "time_ms": ms}
            if show_io:
                row.update(input=t["input"][:2000], expected=t["output"][:2000], output=out[:2000], stderr=err_text)
            results.append(row)
            if status == "Accepted":
                passed += 1
            else:
                if verdict == "Accepted":
                    verdict = status
                    message = f"Failed on test {i}" + (f": {err_text.strip().splitlines()[-1]}" if err_text.strip() else "")
                if stop_on_fail:
                    break
        return {"verdict": verdict, "passed": passed, "total": len(tests), "time_ms": max_ms, "message": message,
                "tests": results, "time_limit_ms": int(limit * 1000)}
