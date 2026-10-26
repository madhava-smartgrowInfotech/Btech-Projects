"""Testing experiments for the ForgetSafe docs run: load / concurrency, security probes, scripted synthetic-user acceptance.

    python scripts/run_testing_experiments.py load
    python scripts/run_testing_experiments.py security
    python scripts/run_testing_experiments.py acceptance      (needs Playwright + Chrome; starts the API on 8109 and Vite on 5109)
    python scripts/run_testing_experiments.py charts

Every number is measured against the real server (`python app.py --port N`) started from a throw-away working directory,
so the real `data/audit_log.jsonl` is never touched.  Inputs are synthetic.  Writes experiments/<name>/metrics.json.
"""

from __future__ import annotations

import http.client
import json
import os
import random
import socket
import statistics as st
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments"
CHARTS = ROOT / "docs" / "charts"
SCRATCH = Path(os.environ.get("FS_SCRATCH", tempfile.gettempdir()))
LOG = SCRATCH / "testing_server_logs"
LOG.mkdir(parents=True, exist_ok=True)

try:
    import psutil
except Exception:  # noqa: BLE001
    psutil = None


def save(name: str, payload: dict) -> None:
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "metrics.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"wrote experiments/{name}/metrics.json")


# ----------------------------------------------------------------------------------------------------- server management
class Server:
    def __init__(self, port: int, tag: str):
        self.port = port
        self.cwd = Path(tempfile.mkdtemp(prefix=f"fs_{tag}_", dir=SCRATCH))
        self.logf = open(LOG / f"{tag}_{port}.log", "w")
        self.proc = subprocess.Popen([sys.executable, str(ROOT / "app.py"), "--port", str(port)], cwd=self.cwd,
                                     stdout=self.logf, stderr=subprocess.STDOUT)
        for _ in range(100):
            try:
                if call(port, "GET", "/api/health")[0] == 200:
                    break
            except OSError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("server did not start")

    @property
    def ledger(self) -> Path:
        return self.cwd / "data" / "audit_log.jsonl"

    def rss_mb(self):
        if not psutil:
            return None
        return psutil.Process(self.proc.pid).memory_info().rss / 1e6

    def threads(self):
        if not psutil:
            return None
        return psutil.Process(self.proc.pid).num_threads()

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            self.proc.kill()
        self.logf.close()


def call(port, method, path, body=None, headers=None, timeout=30, raw_body=None):
    """One HTTP request on a fresh connection (the server speaks HTTP/1.0). Returns (status, parsed-or-text, ms)."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Content-Type": "application/json"} if data is not None else {}
    h.update(headers or {})
    t0 = time.perf_counter()
    try:
        conn.request(method, path, body=data, headers=h)
        r = conn.getresponse()
        payload = r.read()
        ms = (time.perf_counter() - t0) * 1000
        try:
            parsed = json.loads(payload)
        except Exception:  # noqa: BLE001
            parsed = payload[:200].decode("utf-8", "replace")
        return r.status, parsed, ms
    finally:
        conn.close()


def safe_call(port, method, path, body=None, **kw):
    try:
        return call(port, method, path, body, **kw)
    except Exception as exc:  # noqa: BLE001
        return -1, f"{type(exc).__name__}: {exc}", 0.0


def pct(vals, p):
    vals = sorted(vals)
    if not vals:
        return None
    k = min(len(vals) - 1, max(0, int(round(p / 100 * len(vals) + 0.5)) - 1))
    return vals[k]


def lat_summary(ms):
    return {"p50_ms": pct(ms, 50), "p95_ms": pct(ms, 95), "p99_ms": pct(ms, 99), "max_ms": max(ms) if ms else None,
            "mean_ms": st.fmean(ms) if ms else None}


# ----------------------------------------------------------------------------------------------------- load / concurrency
CLIENTS = ["client_finance", "client_health", "client_education", "client_retail", "client_travel"]


def run_level(port, level, make_op, cap=500, seconds=20):
    lock = threading.Lock()
    state = {"n": 0}
    rows = []
    t_start = time.perf_counter()
    deadline = t_start + seconds

    def worker(seed):
        rng = random.Random(seed)
        while True:
            with lock:
                if state["n"] >= cap or time.perf_counter() > deadline:
                    return
                state["n"] += 1
            method, path, body = make_op(rng)
            status, _, ms = safe_call(port, method, path, body)
            with lock:
                rows.append((status, ms))

    threads = [threading.Thread(target=worker, args=(1000 * level + i,)) for i in range(level)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t_start
    statuses = {}
    for s, _ in rows:
        statuses[s] = statuses.get(s, 0) + 1
    ok_ms = [ms for s, ms in rows if s == 200]
    return {"concurrency": level, "requests": len(rows), "elapsed_s": elapsed, "requests_per_s": len(rows) / elapsed,
            "status_counts": {str(k): v for k, v in sorted(statuses.items())},
            "errors_5xx_or_connection": sum(v for k, v in statuses.items() if k < 0 or k >= 500),
            "rejections_4xx": sum(v for k, v in statuses.items() if 400 <= k < 500), **lat_summary([ms for _, ms in rows]),
            "ok_p50_ms": pct(ok_ms, 50)}


OPS = {
    "GET /api/health": lambda rng: ("GET", "/api/health", None),
    "GET /api/state": lambda rng: ("GET", "/api/state", None),
    "POST /api/generate": lambda rng: ("POST", "/api/generate", {"seed": "privacy"}),
}


def mixed_op(rng):
    r = rng.random()
    if r < 0.40:
        return "GET", "/api/state", None
    if r < 0.60:
        return "POST", "/api/generate", {"seed": rng.choice(["privacy", "data", "client", "model"])}
    if r < 0.75:
        return "POST", "/api/train", None
    if r < 0.90:
        return "POST", "/api/unlearn", {"client_id": rng.choice(CLIENTS)}
    return "POST", "/api/session", None


def exp_load():
    port = 8196
    levels = [1, 2, 4, 8, 16, 32, 64]
    result = {"host": f"127.0.0.1:{port}", "per_level_cap_requests": 500, "per_level_cap_seconds": 20, "scenarios": {}}
    rss = {}
    for name, op in list(OPS.items()) + [("mixed read/write", mixed_op)]:
        srv = Server(port, "load")
        try:
            call(port, "POST", "/api/train")
            rss_before = srv.rss_mb()
            rows = []
            for lv in levels:
                r = run_level(port, lv, op)
                print(name, lv, f"{r['requests_per_s']:.0f} rps p95 {r['p95_ms']:.1f} ms 5xx/conn {r['errors_5xx_or_connection']}")
                rows.append(r)
            ok, det, _ = call(port, "POST", "/api/audit/verify")
            result["scenarios"][name] = {"levels": rows, "ledger_valid_after": det.get("valid"), "ledger_detail": det.get("detail"),
                                         "rss_mb_before": rss_before, "rss_mb_after": srv.rss_mb(), "server_threads_after": srv.threads()}
        finally:
            srv.stop()

    # ---- race tests (fresh server each)
    races = {}
    srv = Server(port, "race_unlearn")
    try:
        call(port, "POST", "/api/train")
        barrier = threading.Barrier(32)
        out = []

        def go():
            barrier.wait()
            out.append(safe_call(port, "POST", "/api/unlearn", {"client_id": "client_finance"})[0])

        ts = [threading.Thread(target=go) for _ in range(32)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        state = call(port, "GET", "/api/state")[1]
        races["32 simultaneous unlearn requests for the same client"] = {
            "status_counts": {str(k): out.count(k) for k in sorted(set(out))}, "expected": "exactly one 200, 31 x 400",
            "ledger_records": len(state["audit"]["records"]), "unlearning_events": sum(r["event_type"] == "CLIENT_UNLEARNING" for r in state["audit"]["records"]),
            "ledger_valid": state["audit"]["valid"], "active_clients": len(state["active_clients"]), "certificates_in_state": state["latest_certificate"] is not None}
    finally:
        srv.stop()
    srv = Server(port, "race_train")
    try:
        barrier = threading.Barrier(16)
        out = []

        def go2():
            barrier.wait()
            out.append(safe_call(port, "POST", "/api/train")[0])

        ts = [threading.Thread(target=go2) for _ in range(16)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        state = call(port, "GET", "/api/state")[1]
        races["16 simultaneous train requests"] = {
            "status_counts": {str(k): out.count(k) for k in sorted(set(out))}, "ok_responses": out.count(200),
            "ledger_records": len(state["audit"]["records"]), "ledger_valid": state["audit"]["valid"],
            "records_equal_ok_responses": len(state["audit"]["records"]) == out.count(200),
            "sequence_numbers_contiguous": [r["sequence"] for r in state["audit"]["records"]] == list(range(1, len(state["audit"]["records"]) + 1))}
    finally:
        srv.stop()
    srv = Server(port, "race_verify")
    try:
        stop = threading.Event()
        verify_results = []
        write_status = []

        def writer():
            for _ in range(15):
                write_status.append(safe_call(port, "POST", "/api/train")[0])

        def verifier():
            while not stop.is_set():
                s, d, _ = safe_call(port, "POST", "/api/audit/verify")
                verify_results.append((s, d.get("valid") if isinstance(d, dict) else None))

        ws = [threading.Thread(target=writer) for _ in range(8)]
        v = threading.Thread(target=verifier)
        v.start()
        [t.start() for t in ws]
        [t.join() for t in ws]
        stop.set()
        v.join()
        state = call(port, "GET", "/api/state")[1]
        races["8 writers (120 train requests) while one thread verifies the chain"] = {
            "writes_ok": write_status.count(200), "write_errors": len(write_status) - write_status.count(200),
            "verify_calls": len(verify_results), "verify_invalid": sum(1 for s, ok in verify_results if ok is not True),
            "final_ledger_records": len(state["audit"]["records"]), "final_ledger_valid": state["audit"]["valid"]}
    finally:
        srv.stop()
    result["races"] = races

    # ---- soak: 2,000 sequential mixed requests on one server
    srv = Server(port, "soak")
    try:
        pattern = [("POST", "/api/session", None), ("POST", "/api/train", None), ("GET", "/api/state", None), ("POST", "/api/generate", {"seed": "privacy"}),
                   ("POST", "/api/unlearn", {"client_id": "client_finance"}), ("GET", "/api/state", None), ("POST", "/api/generate", {"seed": "data"}),
                   ("POST", "/api/audit/verify", None), ("GET", "/api/state", None), ("GET", "/api/health", None)]
        rss0, thr0 = srv.rss_mb(), srv.threads()
        rows = []
        for i in range(2000):
            m, p, b = pattern[i % len(pattern)]
            s, _, ms = safe_call(port, m, p, b)
            rows.append((s, ms, p))
        ms_all = [r[1] for r in rows]
        state = call(port, "GET", "/api/state")[1]
        result["soak"] = {"requests": 2000, "errors_5xx_or_connection": sum(1 for r in rows if r[0] < 0 or r[0] >= 500),
                          "non_200": sum(1 for r in rows if r[0] != 200), "first200": lat_summary(ms_all[:200]), "last200": lat_summary(ms_all[-200:]),
                          "ledger_records_end": len(state["audit"]["records"]), "ledger_valid_end": state["audit"]["valid"],
                          "rss_mb_before": rss0, "rss_mb_after": srv.rss_mb(), "threads_before": thr0, "threads_after": srv.threads(),
                          "state_ms_first50": lat_summary([r[1] for r in rows if r[2] == "/api/state"][:50]),
                          "state_ms_last50": lat_summary([r[1] for r in rows if r[2] == "/api/state"][-50:])}
    finally:
        srv.stop()
    save("load_test", result)


# ----------------------------------------------------------------------------------------------------- security probes
def req_bytes(method, path, body=b"", headers=None, cl="auto", version="HTTP/1.0"):
    h = {"Host": "127.0.0.1"}
    h.update(headers or {})
    lines = [f"{method} {path} {version}"] + [f"{k}: {v}" for k, v in h.items()]
    if cl == "auto" and (body or method == "POST"):
        lines.append(f"Content-Length: {len(body)}")
    elif cl not in ("auto", None):
        lines.append(f"Content-Length: {cl}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1", "replace") + body


def raw(port, data, timeout=5, half_close=False, hold_after_send=0.0, max_bytes=3_000_000):
    """Send raw bytes; return dict with status, headers, body size, whether the server closed the connection, timing."""
    t0 = time.perf_counter()
    out = {"status": None, "server_closed": None, "send_error": None, "body_bytes": 0, "headers": {}, "elapsed_ms": None, "body_head": ""}
    s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    try:
        try:
            s.sendall(data)
        except OSError as exc:
            out["send_error"] = f"{type(exc).__name__}: {exc}"
        if half_close:
            try:
                s.shutdown(socket.SHUT_WR)
            except OSError:
                pass
        if hold_after_send:
            time.sleep(hold_after_send)
        chunks, total = [], 0
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    out["server_closed"] = True
                    break
                chunks.append(c)
                total += len(c)
                if total > max_bytes:
                    break
        except socket.timeout:
            out["server_closed"] = False
        except OSError as exc:
            out["server_closed"] = True
            out["recv_error"] = f"{type(exc).__name__}: {exc}"
        resp = b"".join(chunks)
        out["elapsed_ms"] = (time.perf_counter() - t0) * 1000
        if resp:
            head, _, body = resp.partition(b"\r\n\r\n")
            lines = head.decode("latin-1", "replace").split("\r\n")
            parts = lines[0].split(" ", 2)
            if lines[0].startswith("HTTP/"):
                out["status"] = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                out["headers"] = {l.split(":", 1)[0].strip().lower(): l.split(":", 1)[1].strip() for l in lines[1:] if ":" in l}
            else:
                body = resp  # HTTP/0.9 style: no status line
            out["body_bytes"] = len(body)
            out["body_head"] = body[:160].decode("utf-8", "replace")
            out["raw_responses_seen"] = resp.count(b"HTTP/1.0 ") + resp.count(b"HTTP/1.1 ")
        return out
    finally:
        s.close()


def exp_security():
    port = 8196
    srv = Server(port, "security")
    probes = []

    def alive():
        s, _, ms = safe_call(port, "GET", "/api/health", timeout=5)
        return s == 200

    def reset():
        call(port, "POST", "/api/session")
        call(port, "POST", "/api/train")

    def record(group, case, obs, cls, note):
        probes.append({"group": group, "case": case, "classification": cls, "evidence": note, "observed": obs, "server_alive_after": alive()})
        print(f"[{cls:9}] {group}: {case}  ->  {note}")

    JSON_UNLEARN = b'{"client_id":"client_finance"}'
    try:
        reset()
        # ---------------- Content-Length handling
        g = "Content-Length"
        o = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, cl="abc"))
        record(g, "non-numeric value 'abc'", o, "handled" if o["status"] == 400 else "defect", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, cl=""))
        record(g, "empty value", o, "handled" if o["status"] == 400 else "defect", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, cl="99999999999"))
        record(g, "huge value 99999999999", o, "handled" if o["status"] == 400 else "defect", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, cl="-1"), timeout=4)
        hang = o["status"] is None and o["server_closed"] is False
        record(g, "negative value -1 (client keeps the socket open)", o, "defect" if hang else ("handled" if o["status"] == 400 else "noteworthy"),
               "server thread blocks in rfile.read(-1) until the client closes: no response within 4 s" if hang else f"HTTP {o['status']}: {o['body_head'][:70]}")
        o2 = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, cl="-1"), timeout=4, half_close=True)
        record(g, "negative value -1 followed by half-close", o2, "noteworthy", f"once the client closes its side the abandoned request IS executed: the first probe's unlearn ran after the client had gone (this request then got HTTP {o2['status']}: already unlearned)")
        reset()
        o = raw(port, req_bytes("POST", "/api/unlearn", b'{"client_id":"client_finance"}', cl="500"), timeout=4)
        hang = o["status"] is None and o["server_closed"] is False
        record(g, "declared 500 bytes, 30 sent, socket kept open", o, "defect" if hang else "handled",
               "server waits for the missing bytes indefinitely (no read timeout)" if hang else f"HTTP {o['status']}")
        o = raw(port, req_bytes("POST", "/api/unlearn", b'{"client_id":"client_finance"}', cl="5"))
        record(g, "declared 5 bytes, 30 sent", o, "handled" if o["status"] == 400 else "noteworthy", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, cl=None))
        record(g, "body sent without Content-Length", o, "handled" if o["status"] == 400 else "noteworthy", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, headers={"Content-Length": "5"}, cl=len(JSON_UNLEARN)))
        record(g, "two Content-Length headers (5 and 30)", o, "noteworthy", f"HTTP {o['status']}: {o['body_head'][:70]} (first header wins, as http.client semantics)")
        # ---------------- body encodings
        g = "Body content"
        reset()
        o = raw(port, req_bytes("POST", "/api/unlearn", b'\xff\xfe{"client_id":"client_finance"}'))
        record(g, "invalid UTF-8 body", o, "handled" if o["status"] == 400 else "defect", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/generate", b"[" * 10000 + b"]" * 10000))
        record(g, "JSON nested 10,000 deep", o, "handled" if o["status"] in (400, 413) else "defect", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/generate", b'{"seed":"a","seed":"privacy"}'))
        record(g, "duplicate JSON keys", o, "noteworthy", f"HTTP {o['status']}: last key wins, text starts {json.loads(o['body_head'])['text'][:12]!r}" if o["status"] == 200 else f"HTTP {o['status']}")
        o = raw(port, req_bytes("POST", "/api/generate", b'{"seed": 12345}'))
        record(g, "seed given as a number", o, "handled" if o["status"] in (200, 400) else "defect", f"HTTP {o['status']} (converted with str())")
        o = raw(port, req_bytes("POST", "/api/generate", b'{"seed": null}'))
        record(g, "seed null", o, "handled" if o["status"] in (200, 400) else "defect", f"HTTP {o['status']}: {o['body_head'][:60]}")
        o = raw(port, req_bytes("POST", "/api/unlearn", b"", cl="0"))
        record(g, "empty body on /api/unlearn", o, "handled" if o["status"] == 400 else "defect", f"HTTP {o['status']}: {o['body_head'][:60]}")
        # ---------------- client_id variants
        g = "client_id values"
        variants = {"number 5": 5, "list ['client_finance']": ["client_finance"], "null": None, "object": {"a": 1}, "true": True,
                    "path traversal ../../etc/passwd": "../../etc/passwd", "NUL byte appended": "client_finance\u0000", "CRLF appended": "client_finance\r\nX: y",
                    "trailing space": "client_finance ", "upper case": "CLIENT_FINANCE", "SQL-like": "x'; DROP TABLE users;--"}
        for name, val in variants.items():
            o = raw(port, req_bytes("POST", "/api/unlearn", json.dumps({"client_id": val}).encode()))
            record(g, name, o, "handled" if o["status"] == 400 else "defect", f"HTTP {o['status']}: {o['body_head'][:70]}")
        o = raw(port, req_bytes("POST", "/api/unlearn", json.dumps({"client_id": "A" * 100_000}).encode()))
        reflect = o["body_bytes"] > 90_000
        record(g, "100 kB string", o, "noteworthy" if reflect else "handled",
               f"HTTP {o['status']}; the {o['body_bytes']:,}-byte response echoes the id back (reflection / amplification)" if reflect else f"HTTP {o['status']}")
        # ---------------- size cap
        g = "Body size cap"
        pre, post = b'{"seed":"', b'"}'
        for delta, label in ((0, "exactly 1,000,000 bytes"), (-1, "999,999 bytes"), (1, "1,000,001 bytes")):
            n = 1_000_000 + delta - len(pre) - len(post)
            body = pre + b"a" * n + post
            o = raw(port, req_bytes("POST", "/api/generate", body), timeout=20)
            ok_cap = (o["status"] == 200) if delta <= 0 else (o["status"] == 400 or o["send_error"] is not None or o["server_closed"])
            note = f"HTTP {o['status']}, response {o['body_bytes']:,} bytes in {o['elapsed_ms']:.0f} ms" + (f", send error {o['send_error'][:50]}" if o["send_error"] else "")
            record(g, label, o, "handled" if ok_cap else "noteworthy", note)
        o = raw(port, req_bytes("POST", "/api/generate", b'{"seed":"' + b"x" * 1_500_000 + b'"}'), timeout=20)
        record(g, "1.5 MB body", o, "handled" if (o["status"] == 400 or o["send_error"] or o["server_closed"]) else "defect",
               f"HTTP {o['status']}, send_error={bool(o['send_error'])}: server answers before reading the body, so the client may see a reset instead of the 400")
        # ---------------- header handling
        g = "Headers and request line"
        o = raw(port, b"GET /api/health%0d%0aInjected:%20yes HTTP/1.0\r\nHost: x\r\n\r\n")
        record(g, "encoded CRLF in the path", o, "handled" if o["status"] == 404 and "injected" not in o["headers"] else "defect", f"HTTP {o['status']}; no header injected into the response")
        o = raw(port, req_bytes("GET", "/api/health", headers={"X-Big": "a" * 100_000}))
        record(g, "100 kB header line", o, "handled" if o["status"] in (400, 431) else "defect", f"HTTP {o['status']}")
        many = {f"X-H{i}": "v" for i in range(10_000)}
        o = raw(port, req_bytes("GET", "/api/health", headers=many))
        record(g, "10,000 headers", o, "handled" if o["status"] in (400, 431) else "defect", f"HTTP {o['status']}")
        o = raw(port, b"GET /api/health\r\n\r\n")
        record(g, "HTTP/0.9 style request line", o, "noteworthy", f"served: status line {'absent' if o['status'] is None else o['status']}, {o['body_bytes']} body bytes (stdlib legacy behaviour)")
        o = raw(port, req_bytes("GET", "/api/health") + req_bytes("GET", "/api/health"))
        record(g, "two pipelined requests in one packet", o, "handled", f"{o.get('raw_responses_seen')} response(s) returned; the server answers once and closes (HTTP/1.0, no keep-alive)")
        o = raw(port, b"GARBAGE\r\n\r\n")
        record(g, "garbage request line", o, "handled" if o["status"] in (400, 501, None) else "noteworthy", "stdlib answers with an HTML 400 error page and, lacking a protocol version, no status line (HTTP/0.9 fallback)" if o["status"] is None else f"HTTP {o['status']}")
        o = raw(port, req_bytes("GET", "//api//health"))
        record(g, "double slashes in the path", o, "handled" if o["status"] in (404, 200) else "noteworthy", f"HTTP {o['status']}")
        o = raw(port, req_bytes("GET", "/api/health?x=" + "a" * 70_000))
        record(g, "70 kB query string", o, "handled" if o["status"] in (414, 400) else "noteworthy", f"HTTP {o['status']}")
        # ---------------- methods
        g = "HTTP methods"
        for m in ("OPTIONS", "HEAD", "TRACE", "PUT", "DELETE", "PATCH"):
            o = raw(port, req_bytes(m, "/api/state"))
            record(g, m, o, "noteworthy" if o["status"] == 501 else "defect" if o["status"] == 200 and m == "TRACE" else "handled",
                   f"HTTP {o['status']}, Content-Type {o['headers'].get('content-type', '-')}: stdlib 501 page, not JSON" if o["status"] == 501 else f"HTTP {o['status']}")
        # ---------------- headers of responses / CORS / CSRF / host validation
        g = "Browser-facing hardening"
        s, _, _ = call(port, "GET", "/api/state", headers={"Origin": "http://evil.example"})
        o = raw(port, req_bytes("GET", "/api/state", headers={"Origin": "http://evil.example"}))
        record(g, "CORS: Origin header from another site on GET /api/state", o,
               "handled" if "access-control-allow-origin" not in o["headers"] else "defect",
               "no Access-Control-Allow-Origin header, so a browser blocks cross-site JavaScript from reading the response" if "access-control-allow-origin" not in o["headers"] else "wildcard CORS")
        reset()
        o = raw(port, req_bytes("POST", "/api/unlearn", JSON_UNLEARN, headers={"Origin": "http://evil.example", "Content-Type": "text/plain"}))
        record(g, "cross-site 'simple' POST (Content-Type text/plain, Origin evil.example) to /api/unlearn", o,
               "defect" if o["status"] == 200 else "handled",
               f"HTTP {o['status']}: the server ignores Content-Type and Origin and executes the removal; a web page the operator visits can issue this request (CSRF) because there is no token, no authentication and no preflight is required for text/plain")
        reset()
        o = raw(port, req_bytes("GET", "/api/state", headers={"Host": "evil.example"}))
        record(g, "Host header evil.example (DNS-rebinding precondition)", o, "defect" if o["status"] == 200 else "handled",
               f"HTTP {o['status']}: Host is not validated")
        o = raw(port, req_bytes("GET", "/api/state"))
        hdrs = o["headers"]
        missing = [h for h in ("x-content-type-options", "content-security-policy", "x-frame-options", "strict-transport-security", "referrer-policy") if h not in hdrs]
        record(g, "security response headers on /api/state", {"headers": hdrs}, "noteworthy",
               f"Cache-Control: {hdrs.get('cache-control')}; Server: {hdrs.get('server')}; missing: {', '.join(missing)}")
        o = raw(port, req_bytes("GET", "/"))
        missing = [h for h in ("x-content-type-options", "content-security-policy", "x-frame-options") if h not in o["headers"]]
        record(g, "security response headers on the legacy page /", {"headers": o["headers"]}, "noteworthy", f"HTTP {o['status']}; missing: {', '.join(missing)}")
        o = raw(port, req_bytes("POST", "/api/generate", b'{"seed":"privacy"}', headers={"Content-Type": ""}))
        record(g, "POST without a Content-Type", o, "noteworthy", f"HTTP {o['status']}: Content-Type is ignored")
        # ---------------- resource exhaustion
        g = "Connections"
        sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        sock.sendall(b"POST /api/unlearn HTTP/1.0\r\nHost: x\r\nContent-Length: 50\r\n\r\n{")
        lat, st_ = [], []
        t_end = time.perf_counter() + 5
        while time.perf_counter() < t_end:
            s, _, ms = safe_call(port, "GET", "/api/health", timeout=5)
            st_.append(s); lat.append(ms)
            time.sleep(0.05)
        sock.close()
        record(g, "slowloris: one connection holds a half-sent body for 5 s while 100 other requests are made",
               {"requests": len(lat), "status_counts": {str(k): st_.count(k) for k in set(st_)}, **lat_summary(lat)},
               "handled" if all(s == 200 for s in st_) else "defect",
               f"{len(lat)} concurrent health requests, all {'200' if all(s == 200 for s in st_) else 'not all 200'}, p95 {pct(lat, 95):.1f} ms (thread per connection); but no read timeout exists, so the stalled thread lives until the client disconnects")
        thr0 = srv.threads()
        socks = []
        for _ in range(200):
            try:
                socks.append(socket.create_connection(("127.0.0.1", port), timeout=5))
            except OSError:
                break
        time.sleep(0.5)
        thr1 = srv.threads()
        lat = [safe_call(port, "GET", "/api/health", timeout=5)[2] for _ in range(30)]
        for s_ in socks:
            s_.close()
        time.sleep(1.0)
        record(g, "200 idle connections held open", {"opened": len(socks), "server_threads_before": thr0, "server_threads_during": thr1, "server_threads_after": srv.threads(), **lat_summary(lat)},
               "noteworthy", f"{len(socks)} sockets opened; server threads {thr0} -> {thr1} while idle -> {srv.threads()} after close; health p95 {pct(lat, 95):.1f} ms. Idle connections each pin a thread, there is no connection limit or idle timeout")
        import socketserver
        def burst(n):
            barrier = threading.Barrier(n)
            res = []
            def one():
                barrier.wait()
                t0 = time.perf_counter()
                try:
                    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                    c.request("GET", "/api/health")
                    r = c.getresponse(); r.read(); c.close()
                    res.append(("ok", (time.perf_counter() - t0) * 1000))
                except Exception as exc:  # noqa: BLE001
                    res.append((type(exc).__name__ + ": " + str(exc)[:60], (time.perf_counter() - t0) * 1000))
            ts = [threading.Thread(target=one) for _ in range(n)]
            [t.start() for t in ts]
            [t.join() for t in ts]
            kinds = {}
            for k, _ in res:
                kinds[k] = kinds.get(k, 0) + 1
            ok_ms = [ms for k, ms in res if k == "ok"]
            return {"simultaneous_connections": n, "outcomes": kinds, **lat_summary(ok_ms)}
        bursts = [burst(n) for n in (16, 64, 128)]
        failed = sum(v for b in bursts for k, v in b["outcomes"].items() if k != "ok")
        record(g, "burst of 16 / 64 / 128 simultaneous new connections", {"bursts": bursts, "listen_backlog_request_queue_size": socketserver.TCPServer.request_queue_size},
               "defect" if failed else "handled",
               "; ".join(f"{b['simultaneous_connections']}: {b['outcomes']} (p95 of the successful ones {b['p95_ms'] or 0:.0f} ms, max {b['max_ms'] or 0:.0f} ms)" for b in bursts)
               + f"; the stdlib listen backlog is {socketserver.TCPServer.request_queue_size}, so bursts of new connections are delayed by SYN retransmission (0.5-2 s) or refused")
        # ---------------- corrupted ledger
        g = "Data integrity"
        reset()
        call(port, "POST", "/api/unlearn", {"client_id": "client_finance"})
        led = srv.ledger
        good = led.read_text(encoding="utf-8")
        led.write_text(good + "THIS IS NOT JSON\n", encoding="utf-8")
        a = safe_call(port, "GET", "/api/state")
        b = safe_call(port, "POST", "/api/train")
        c = safe_call(port, "POST", "/api/audit/verify")
        d_ = safe_call(port, "GET", "/api/health")
        record(g, "garbage line appended to the ledger file while the server runs",
               {"GET /api/state": a[0], "POST /api/train": b[0], "POST /api/audit/verify": c[0], "verify_body": c[1], "state_body": a[1], "health": d_[0]},
               "defect" if a[0] >= 500 else "noteworthy",
               f"GET /api/state -> {a[0]}, POST /api/train -> {b[0]}, POST /api/audit/verify -> {c[0]} {c[1]}: the whole UI stops loading until the file is repaired by hand (fail closed, but no recovery path)")
        led.write_text(good, encoding="utf-8")
        record(g, "ledger restored", {"GET /api/state": safe_call(port, "GET", "/api/state")[0]}, "handled", "service recovers as soon as the file is valid again")
        led.write_text("", encoding="utf-8")
        s_, d_, _ = safe_call(port, "POST", "/api/audit/verify")
        record(g, "ledger file truncated to zero bytes (attacker with file access)", {"verify": d_}, "defect" if isinstance(d_, dict) and d_.get("valid") else "handled",
               f"verify -> {d_}: an empty ledger verifies as valid, so deleting the whole history is not detected")
        # ---------------- what an unauthenticated caller can do
        reset()
        facts = {}
        s, d, _ = call(port, "GET", "/api/state")
        facts["read_full_audit_log_with_hashes_and_client_ids"] = {"status": s, "records_returned": len(d["audit"]["records"])}
        s, d, _ = call(port, "POST", "/api/unlearn", {"client_id": "client_travel"})
        facts["erase_a_client_from_the_model"] = {"status": s, "certificate_status": d.get("status") if isinstance(d, dict) else None}
        s, d, _ = call(port, "GET", "/api/certificate/latest")
        facts["download_certificate"] = {"status": s}
        s, d, _ = call(port, "POST", "/api/train")
        facts["retrain_and_discard_certificates"] = {"status": s}
        s, d, _ = call(port, "POST", "/api/generate", {"seed": "privacy"})
        facts["sample_the_model"] = {"status": s}
        s, d, _ = call(port, "POST", "/api/session")
        facts["reset_the_session_and_discard_all_state"] = {"status": s}
        record("Authentication", "unauthenticated caller capabilities", facts, "defect",
               "every route works with no credentials: " + ", ".join(f"{k.replace('_', ' ')} (HTTP {v['status']})" for k, v in facts.items()))
    finally:
        srv.stop()
    cls_counts = {}
    for p in probes:
        cls_counts[p["classification"]] = cls_counts.get(p["classification"], 0) + 1
    save("security_probe", {"probes": probes, "classification_counts": cls_counts, "n_probes": len(probes),
                            "server_alive_after_all": all(p["server_alive_after"] for p in probes),
                            "defects": [{"case": f"{p['group']}: {p['case']}", "evidence": p["evidence"]} for p in probes if p["classification"] == "defect"]})


# ----------------------------------------------------------------------------------------------------- scripted acceptance
def exp_acceptance():
    from playwright.sync_api import sync_playwright

    api_port, ui_port = 8109, 5109
    srv = Server(api_port, "accept")
    vite = subprocess.Popen(["cmd.exe", "/c", "npm run dev"], cwd=ROOT / "frontend", stdout=open(LOG / "vite.log", "w"), stderr=subprocess.STDOUT)
    for _ in range(100):
        try:
            if call(ui_port, "GET", "/api/health")[0] == 200:
                break
        except OSError:
            pass
        time.sleep(0.3)
    UI, API = f"http://127.0.0.1:{ui_port}", f"http://127.0.0.1:{api_port}"
    journeys = []
    step_names = ["load training page", "train", "generate sample", "unlearn (certificate)", "audit verify", "theme toggle", "no console errors"]
    seeds = ["privacy", "data science", "federated", "client records", "the model", "forget me", "secure", "audit trail"]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True, args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
            for j in range(int(os.environ.get("FS_JOURNEYS", "20"))):
                rng = random.Random(7000 + j)
                mobile = rng.random() < 0.4
                dark = rng.random() < 0.5
                cancel_first = rng.random() < 0.25
                k = rng.randint(1, 3)
                seed_text = rng.choice(seeds)
                vp = {"width": 390, "height": 844} if mobile else {"width": 1440, "height": 900}
                ctx = browser.new_context(viewport=vp)
                page = ctx.new_page()
                errors = []
                page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: errors.append(str(e)))
                steps, causes = {}, {}
                t_j = time.perf_counter()
                load_ms = None

                def step(name, fn):
                    try:
                        fn()
                        steps[name] = True
                    except Exception as exc:  # noqa: BLE001
                        steps[name] = False
                        causes[name] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"

                ctx.request.post(f"{API}/api/session")
                n0 = len(call(api_port, "GET", "/api/state")[1]["audit"]["records"])

                def s_load():
                    nonlocal load_ms
                    t0 = time.perf_counter()
                    page.goto(UI + "/app/training", wait_until="networkidle")
                    page.get_by_role("heading", name="Federated training").first.wait_for(timeout=10000)
                    load_ms = (time.perf_counter() - t0) * 1000
                step("load training page", s_load)

                def s_train():
                    page.get_by_role("button", name="Train federated model").first.click()
                    page.get_by_text("Federated training complete").first.wait_for(timeout=10000)
                    state = call(api_port, "GET", "/api/state")[1]
                    assert state["trained"] and state["metrics"]["active_clients"] == 5, "state not trained"
                    eps = f"{state['metrics']['epsilon']:.4f}"
                    assert eps in page.inner_text("body"), f"epsilon {eps} not on page"
                    assert len(state["audit"]["records"]) == n0 + 1, "ledger did not grow by one"
                step("train", s_train)

                def s_gen():
                    page.goto(UI + "/app/explorer", wait_until="networkidle")
                    page.get_by_label("Seed text").fill(seed_text)
                    page.get_by_role("button", name="Generate sample").click()
                    page.wait_for_timeout(1500)
                    norm = seed_text.lower()
                    assert norm in page.inner_text("body").lower(), "generated sample does not start with the seed"
                step("generate sample", s_gen)

                removed = []

                def s_unlearn():
                    for i in range(k):
                        page.goto(UI + "/app/unlearning", wait_until="networkidle")
                        sel = page.locator("select").first
                        opts = sel.locator("option").count()
                        sel.select_option(index=rng.randrange(opts))
                        chosen = sel.input_value()
                        if cancel_first and i == 0:
                            page.get_by_role("button", name="Execute & certify").first.click()
                            page.get_by_role("dialog").get_by_role("button", name="Cancel").click()
                            page.wait_for_timeout(400)
                            st0 = call(api_port, "GET", "/api/state")[1]
                            assert len(st0["active_clients"]) == 5 - len(removed), "cancel changed the model"
                        page.get_by_role("button", name="Execute & certify").first.click()
                        page.get_by_role("dialog").get_by_role("button", name="Remove & certify").click()
                        page.get_by_text("Client removed and certified").first.wait_for(timeout=10000)
                        removed.append(chosen)
                        state = call(api_port, "GET", "/api/state")[1]
                        cert = state["latest_certificate"]
                        assert cert and cert["status"] == "CERTIFIED", f"certificate status {cert and cert['status']}"
                        assert cert["certificate_id"] in page.inner_text("body"), "certificate id not shown"
                        assert len(state["active_clients"]) == 5 - len(removed), "active client count wrong"
                        assert len(state["audit"]["records"]) == n0 + 1 + len(removed), "ledger count wrong"
                step("unlearn (certificate)", s_unlearn)

                def s_audit():
                    page.goto(UI + "/app/audit", wait_until="networkidle")
                    page.get_by_role("button", name="Verify hash chain").click()
                    page.get_by_text("Hash chain verified").first.wait_for(timeout=10000)
                    v = call(api_port, "POST", "/api/audit/verify")[1]
                    assert v["valid"] is True, "API says chain invalid"
                    assert str(n0 + 1 + len(removed)) in v["detail"], f"detail {v['detail']}"
                step("audit verify", s_audit)

                def s_theme():
                    page.goto(UI + "/app", wait_until="networkidle")
                    if dark:
                        page.get_by_role("button", name="Switch to dark mode").first.click()
                        page.wait_for_timeout(300)
                        assert page.evaluate("document.documentElement.dataset.theme") == "dark", "theme did not switch"
                    else:
                        assert page.evaluate("document.documentElement.dataset.theme") in ("light", None, ""), "unexpected initial theme"
                    page.wait_for_timeout(1500)
                step("theme toggle", s_theme)

                steps["no console errors"] = len(errors) == 0
                if errors:
                    causes["no console errors"] = errors[0][:160]
                journeys.append({"journey": j + 1, "viewport": "390x844" if mobile else "1440x900", "dark_mode": dark, "cancelled_first_dialog": cancel_first,
                                 "clients_removed": k, "seed_text": seed_text, "training_page_load_ms": load_ms, "duration_s": time.perf_counter() - t_j,
                                 "steps": steps, "failure_causes": causes, "console_errors": errors[:3], "passed_all": all(steps.values())})
                print(f"journey {j + 1}: {'PASS' if all(steps.values()) else 'FAIL'} {causes}")
                ctx.close()
            browser.close()
    finally:
        # stop Vite (npm runs it through cmd): kill the tree
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(vite.pid)], capture_output=True)
        if psutil:
            for c in psutil.net_connections(kind="tcp"):
                if c.laddr and c.laddr.port == ui_port and c.status == "LISTEN" and c.pid:
                    try:
                        psutil.Process(c.pid).kill()
                    except Exception:  # noqa: BLE001
                        pass
        srv.stop()
    per_step = {n: sum(1 for jr in journeys if jr["steps"].get(n)) for n in step_names}
    save("acceptance", {"kind": "scripted synthetic-user acceptance (Playwright + Chrome); not a study with human users",
                        "journeys": len(journeys), "journeys_passed_all_steps": sum(jr["passed_all"] for jr in journeys),
                        "pass_count_per_step": per_step, "mean_duration_s": st.fmean(jr["duration_s"] for jr in journeys),
                        "training_page_load_ms": lat_summary([jr["training_page_load_ms"] for jr in journeys if jr["training_page_load_ms"]]),
                        "desktop_journeys": sum(1 for jr in journeys if jr["viewport"] == "1440x900"), "mobile_journeys": sum(1 for jr in journeys if jr["viewport"] != "1440x900"),
                        "dark_mode_journeys": sum(jr["dark_mode"] for jr in journeys), "cancelled_dialog_journeys": sum(jr["cancelled_first_dialog"] for jr in journeys),
                        "total_certificates_checked": sum(jr["clients_removed"] for jr in journeys if jr["steps"].get("unlearn (certificate)")),
                        "console_error_journeys": sum(1 for jr in journeys if jr["console_errors"]), "details": journeys})


# ----------------------------------------------------------------------------------------------------- charts
def charts():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e7ef"})
    cols = {"GET /api/health": "#5b5bd6", "GET /api/state": "#2f9e77", "POST /api/generate": "#e0a030", "mixed read/write": "#d6455d"}
    load = json.loads((OUT / "load_test" / "metrics.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(1, 2, figsize=(8.8, 3.3))
    for name, sc in load["scenarios"].items():
        lv = [r["concurrency"] for r in sc["levels"]]
        ax[0].plot(lv, [r["requests_per_s"] for r in sc["levels"]], marker="o", ms=4, lw=1.4, color=cols[name], label=name)
        ax[1].plot(lv, [r["p95_ms"] for r in sc["levels"]], marker="o", ms=4, lw=1.4, color=cols[name], label=name)
    ax[0].set_xscale("log", base=2); ax[1].set_xscale("log", base=2); ax[1].set_yscale("log")
    ax[0].set_xlabel("concurrent clients"); ax[0].set_ylabel("requests per second"); ax[0].set_title("Throughput", fontsize=9.5, fontweight="bold")
    ax[1].set_xlabel("concurrent clients"); ax[1].set_ylabel("95th-percentile latency (ms)"); ax[1].set_title("Latency", fontsize=9.5, fontweight="bold")
    ax[0].legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(CHARTS / "t01_load.png", dpi=150, facecolor="white", bbox_inches="tight")
    print("saved t01_load.png")
    acc_path = OUT / "acceptance" / "metrics.json"
    if acc_path.exists():
        acc = json.loads(acc_path.read_text(encoding="utf-8"))
        fig, ax = plt.subplots(1, 2, figsize=(8.8, 3.1))
        names = list(acc["pass_count_per_step"])
        ax[0].barh(range(len(names)), [acc["pass_count_per_step"][n] for n in names], color="#2f9e77")
        ax[0].set_yticks(range(len(names))); ax[0].set_yticklabels(names, fontsize=8); ax[0].invert_yaxis(); ax[0].set_xlim(0, acc["journeys"])
        ax[0].set_xlabel(f"journeys passing the step (of {acc['journeys']})"); ax[0].set_title("Scripted synthetic-user acceptance", fontsize=9.5, fontweight="bold")
        ax[1].bar(range(len(acc["details"])), [d["duration_s"] for d in acc["details"]], color=["#5b5bd6" if d["viewport"] == "1440x900" else "#e0a030" for d in acc["details"]])
        ax[1].set_xlabel("journey"); ax[1].set_ylabel("duration (s)"); ax[1].set_title("Journey duration (blue desktop, amber phone)", fontsize=9.5, fontweight="bold")
        fig.tight_layout()
        fig.savefig(CHARTS / "t02_acceptance.png", dpi=150, facecolor="white", bbox_inches="tight")
        print("saved t02_acceptance.png")


if __name__ == "__main__":
    wanted = sys.argv[1:] or ["load", "security", "acceptance", "charts"]
    table = {"load": exp_load, "security": exp_security, "acceptance": exp_acceptance, "charts": charts}
    for w in wanted:
        t0 = time.perf_counter()
        print(f"== {w}")
        table[w]()
        print(f"   {time.perf_counter() - t0:.1f}s")
