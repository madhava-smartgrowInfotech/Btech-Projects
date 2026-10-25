"""
End-to-end latency of the running JSON API (127.0.0.1, one user, the six-subject corpus uploaded one file at a time).
Start a scratch backend first:  venv\\Scripts\\python.exe scripts\\serve_scratch.py --data <dir> --port 8301

    venv\\Scripts\\python.exe scripts\\measure_api.py        # writes experiments/api_latency.json
"""
import http.cookiejar
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get("API_BASE", "http://127.0.0.1:8301")
CORPUS = os.path.join(ROOT, "experiments", "corpus")
N = 30

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def call(method, path, body=None, raw=None, headers=None):
    data, hdrs = raw, dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=hdrs)
    t0 = time.perf_counter()
    try:
        with opener.open(req) as resp:
            payload = json.loads(resp.read() or b"null")
            status = resp.status
    except urllib.error.HTTPError as e:
        payload, status = e.read().decode(errors="replace"), e.code
    return status, payload, (time.perf_counter() - t0) * 1000


def multipart(fields, filename, content):
    boundary = uuid.uuid4().hex
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()]
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{filename}"\r\n'
                 "Content-Type: application/octet-stream\r\n\r\n".encode() + content + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def stats(ms):
    ms = sorted(ms)
    return {"n": len(ms), "median_ms": round(statistics.median(ms), 1), "p95_ms": round(ms[max(0, int(0.95 * len(ms)) - 1)], 1),
            "min_ms": round(ms[0], 1), "max_ms": round(ms[-1], 1)}


def main():
    out = {"base": BASE, "runs_per_endpoint": N}
    name = "lat_" + uuid.uuid4().hex[:8]
    assert call("POST", "/api/auth/register", {"username": name, "password": "Lat#1234"})[0] == 201
    out["login"] = stats([call("POST", "/api/auth/login", {"username": name, "password": "Lat#1234"})[2] for _ in range(10)])
    out["health"] = stats([call("GET", "/api/health")[2] for _ in range(N)])

    # uploads, one subject file after another: every upload re-indexes ALL of the user's chunks
    uploads, doc_ids = [], []
    total_chunks = 0
    for fname in sorted(os.listdir(CORPUS)):
        with open(os.path.join(CORPUS, fname), "rb") as f:
            content = f.read()
        body, h = multipart({"subject": fname[3:-4].replace("_", " ")}, fname, content)
        status, payload, ms = call("POST", "/api/documents", raw=body, headers=h)
        assert status == 201, payload
        total_chunks += payload["chunks_count"]
        doc_ids.append(payload["document"]["id"])
        uploads.append({"file": fname, "kb": round(len(content) / 1024, 1), "chunks_added": payload["chunks_count"],
                        "chunks_total": total_chunks, "topics": payload["topics_count"], "ms": round(ms, 1)})
    out["uploads"] = uploads

    from_questions = ["What is the LIFO principle?", "What is a deadlock?", "Why does TCP use acknowledgments and retransmission?",
                      "How does write-ahead logging guarantee durability?", "What is overfitting?", "Why can a binary search tree become as slow as a linked list?"]
    ask = [call("POST", "/api/ask", {"question": from_questions[i % len(from_questions)]})[2] for i in range(N)]
    out["ask"] = stats(ask)
    out["documents_list"] = stats([call("GET", "/api/documents")[2] for _ in range(N)])
    out["dashboard"] = stats([call("GET", "/api/dashboard")[2] for _ in range(N)])
    out["history"] = stats([call("GET", "/api/ask/history")[2] for _ in range(N)])

    gen, sub = [], []
    for i in range(N):
        s, p, ms = call("POST", "/api/quiz/generate", {"doc_id": doc_ids[i % len(doc_ids)]})
        gen.append(ms)
        s, p, ms = call("POST", "/api/quiz/submit", {"answers": [0, 1, 2, 3, 0]})
        sub.append(ms)
    out["quiz_generate"], out["quiz_submit"] = stats(gen), stats(sub)
    out["roadmap"] = stats([call("GET", "/api/roadmap")[2] for _ in range(N)])

    # delete + re-upload of the first file (index rebuild after a delete)
    out["delete"] = round(call("DELETE", f"/api/documents/{doc_ids[0]}")[2], 1)
    out["total_chunks_indexed"] = total_chunks
    with open(os.path.join(ROOT, "experiments", "api_latency.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    sys.exit(main())
