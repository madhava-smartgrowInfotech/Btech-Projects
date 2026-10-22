"""Smoke test for the API: starts its own server on a spare port with a COPY of the model
(so retraining never overwrites models/msvm_model.pkl), then exercises every endpoint.

    python scripts/smoke_test.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8496
URL = f"http://127.0.0.1:{PORT}"
failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  -> {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def call(method, path, body=None, form=None, files=None):
    headers, data = {}, None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif form is not None or files is not None:
        boundary = uuid.uuid4().hex
        parts = []
        for k, v in (form or {}).items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        for k, (fname, content) in (files or {}).items():
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{fname}"\r\n'
                          "Content-Type: text/csv\r\n\r\n").encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = urllib.request.Request(URL + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def main():
    work = tempfile.mkdtemp(prefix="fn_smoke_")
    model_copy = os.path.join(work, "msvm_model.pkl")
    shutil.copy(os.path.join(ROOT, "models", "msvm_model.pkl"), model_copy)
    env = dict(os.environ, FAKENEWS_MODEL=model_copy)
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(PORT)],
                              cwd=ROOT, env=env, stdout=open(os.path.join(work, "server.log"), "w"), stderr=subprocess.STDOUT)
    try:
        for _ in range(120):
            try:
                if call("GET", "/api/health")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            check("server starts", False, open(os.path.join(work, "server.log")).read()[-800:])
            return

        s, h = call("GET", "/api/health")
        check("health", s == 200 and h["model_loaded"])

        s, m = call("GET", "/api/model")
        check("model stats", s == 200 and m["labels"] == ["REAL", "PARTIALLY TRUE", "FAKE"]
              and "accuracy" in m["stats"] and "y_test" not in m["stats"], m)

        s, sm = call("GET", "/api/samples")
        check("samples cover all classes", s == 200 and {x["label"] for x in sm["samples"]} ==
              {"REAL", "PARTIALLY TRUE", "FAKE"})

        s, p = call("POST", "/api/predict", {"title": "", "text": "Official report confirmed by independent experts with verified data"})
        check("predict REAL", s == 200 and p["label"] == "REAL" and 0 < p["confidence"] <= 1
              and abs(sum(p["probabilities"].values()) - 1) < 1e-6, p)
        s, p = call("POST", "/api/predict", {"text": "SHOCKING secret miracle exposed hidden truth click now"})
        check("predict FAKE with cues", s == 200 and p["label"] == "FAKE" and "shocking" in p["cues"]["sensational"], p)
        s, p = call("POST", "/api/predict", {"text": "too short"})
        check("predict rejects < 5 words", s == 422 and "at least" in p["detail"], p)

        csv = b"id,text\n1,Official report confirmed by experts with verified data\n2,SHOCKING secret miracle exposed click now\n3,\n"
        s, pv = call("POST", "/api/batch/preview", files={"file": ("t.csv", csv)})
        check("batch preview", s == 200 and pv["guessed_column"] == "text" and pv["n_rows"] == 3, pv)
        s, br = call("POST", "/api/batch/run", form={"column": "text"}, files={"file": ("t.csv", csv)})
        check("batch run", s == 200 and br["n_rows"] == 3 and sum(br["distribution"].values()) == 3
              and br["rows"][0]["predicted"] == "REAL" and br["csv"].startswith("id,text,predicted,confidence"), br)
        s, e = call("POST", "/api/batch/run", form={"column": "nope"}, files={"file": ("t.csv", csv)})
        check("batch bad column -> 400", s == 400, e)
        s, e = call("POST", "/api/batch/preview", files={"file": ("t.txt", b"hello")})
        check("batch non-csv -> 400", s == 400, e)

        s, e = call("POST", "/api/retrain", form={"fireflies": "2", "generations": "12", "max_tfidf": "4000"})
        check("retrain validates ranges", s == 422, e)
        s, j = call("POST", "/api/retrain", form={"fireflies": "4", "generations": "3", "max_tfidf": "2000"})
        check("retrain accepted", s == 202 and "job_id" in j, j)
        if s == 202:
            s2, e = call("POST", "/api/retrain", form={"fireflies": "4", "generations": "3", "max_tfidf": "2000"})
            check("second retrain -> 409 while running", s2 == 409, e)
            for _ in range(180):
                s, st = call("GET", f"/api/retrain/{j['job_id']}")
                if st["status"] != "running":
                    break
                time.sleep(2)
            check("retrain finishes", st["status"] == "done" and st["result"]["accuracy"] > 0, st)
            s, p = call("POST", "/api/predict", {"text": "Official report confirmed by independent experts with verified data"})
            check("predict works on the retrained model", s == 200 and p["label"] == "REAL", p)
        s, e = call("GET", "/api/retrain/unknown")
        check("unknown job -> 404", s == 404)
    finally:
        server.terminate()
        shutil.rmtree(work, ignore_errors=True)
    print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
