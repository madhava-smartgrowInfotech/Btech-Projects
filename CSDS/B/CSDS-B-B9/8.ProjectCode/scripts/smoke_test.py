"""End-to-end smoke test against the running API (default http://127.0.0.1:8209).

Flow: health -> candidate signs up -> aptitude + technical tests -> judge verdicts (AC/WA/TLE/RE/CE)
-> contest submission and live leaderboard -> resume upload -> AI mock interview (skipped with a
warning when GEMINI_API_KEY is not set) -> recruiter drive + shortlist + invites -> expert interview
-> career-services analytics.
Run:  python scripts/smoke_test.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = os.getenv("API_URL", f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8209')}")
PASSWORD = "Demo@123"
results = []


def call(method, path, body=None, token=None, raw=None, ctype="application/json", ok=(200,)):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", ctype)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            status, text = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode()
    payload = json.loads(text) if text else None
    if status not in ok:
        raise AssertionError(f"{method} {path} -> {status}: {text[:300]}")
    return status, payload


def step(name, fn):
    t = time.time()
    try:
        note = fn()
        results.append(("PASS" if note != "SKIP" else "SKIP", name, round(time.time() - t, 1)))
        print(f"[{'PASS' if note != 'SKIP' else 'SKIP'}] {name} ({time.time() - t:.1f}s)")
    except Exception as e:
        results.append(("FAIL", name, str(e)))
        print(f"[FAIL] {name}: {e}")


def multipart(fields, file_field, filename, content):
    b = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
                 f'Content-Type: application/pdf\r\n\r\n'.encode() + content + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={b}"


S = {}


def health():
    _, h = call("GET", "/api/health")
    S["ai"] = h["ai_configured"]
    S["langs"] = h["languages"]
    print("   languages:", h["languages"], "| AI configured:", h["ai_configured"])


def signup():
    email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
    _, r = call("POST", "/api/auth/register", {"name": "Smoke Test Candidate", "email": email, "password": PASSWORD})
    S["cand"] = r["token"]
    _, r = call("POST", "/api/auth/login", {"email": email, "password": PASSWORD})
    assert r["user"]["level"] == 1
    for who in ("recruiter", "career", "expert"):
        _, r = call("POST", "/api/auth/login", {"email": f"{who}@talenttrack.dev", "password": PASSWORD})
        S[who] = r["token"]


def take_test(kind, topic):
    _, topics = call("GET", f"/api/practice/topics?kind={kind}")
    assert topics, "no topics"
    _, t = call("POST", "/api/practice/start", {"kind": kind, "topic": topic, "difficulty": "Any", "count": 10}, S["cand"])
    assert len(t["questions"]) == 10 and "answer" not in t["questions"][0]
    # answer everything with option 0, then check the server-side score against the review
    _, r = call("POST", f"/api/practice/{t['attempt_id']}/submit", {"answers": {str(q["id"]): 0 for q in t["questions"]}}, S["cand"])
    assert r["correct"] == sum(1 for q in r["review"] if q["answer"] == 0)
    assert all(q["explanation"] for q in r["review"])
    S[f"{kind}_review"] = r["review"]
    return r


def aptitude():
    take_test("aptitude", "All")
    # learn answers of a whole topic, then score 100% on it
    _, topics = call("GET", "/api/practice/topics?kind=aptitude")
    small = [t for t in topics if 10 <= t["total"] <= 20][0]["topic"]
    known = {}
    for _ in range(12):
        _, t = call("POST", "/api/practice/start", {"kind": "aptitude", "topic": small, "count": 10}, S["cand"])
        if all(q["id"] in known for q in t["questions"]):
            _, r = call("POST", f"/api/practice/{t['attempt_id']}/submit",
                        {"answers": {str(q["id"]): known[q["id"]] for q in t["questions"]}}, S["cand"])
            assert r["score_pct"] == 100, r["score_pct"]
            assert r["level"] >= 2, "should reach level 2"
            return
        _, r = call("POST", f"/api/practice/{t['attempt_id']}/submit", {"answers": {}}, S["cand"])
        known.update({q["id"]: q["answer"] for q in r["review"]})
    raise AssertionError("could not learn the topic in 12 tries")


def technical():
    _, topics = call("GET", "/api/practice/topics?kind=technical")
    names = {t["topic"] for t in topics}
    assert {"DBMS", "Operating Systems", "Computer Networks", "Programming"} <= names, names
    known = {}
    for _ in range(15):
        _, t = call("POST", "/api/practice/start", {"kind": "technical", "topic": "Programming", "count": 10}, S["cand"])
        if all(q["id"] in known for q in t["questions"]):
            _, r = call("POST", f"/api/practice/{t['attempt_id']}/submit",
                        {"answers": {str(q["id"]): known[q["id"]] for q in t["questions"]}}, S["cand"])
            assert r["score_pct"] == 100
            return
        _, r = call("POST", f"/api/practice/{t['attempt_id']}/submit", {"answers": {}}, S["cand"])
        known.update({q["id"]: q["answer"] for q in r["review"]})
    raise AssertionError("could not learn the technical topic")


SOLUTIONS = {
    "array-sum": {"python": "import sys\nd=sys.stdin.read().split()\nprint(sum(map(int,d[1:1+int(d[0])])))\n",
                  "cpp": "#include <bits/stdc++.h>\nint main(){int n;std::cin>>n;long long s=0,x;while(n--){std::cin>>x;s+=x;}std::cout<<s<<\"\\n\";}\n",
                  "java": "import java.io.*;import java.util.*;\npublic class Main{public static void main(String[] a)throws IOException{BufferedReader b=new BufferedReader(new InputStreamReader(System.in));int n=Integer.parseInt(b.readLine().trim());StringTokenizer t=new StringTokenizer(b.readLine());long s=0;for(int i=0;i<n;i++)s+=Long.parseLong(t.nextToken());System.out.println(s);}}\n"},
}


def judge_verdicts():
    _, probs = call("GET", "/api/problems", token=S["cand"])
    assert len(probs) >= 30, len(probs)
    _, p = call("GET", "/api/problems/array-sum", token=S["cand"])
    assert p["samples"] and "hidden" not in p
    _, r = call("POST", "/api/problems/array-sum/run", {"language": "python", "code": SOLUTIONS["array-sum"]["python"]}, S["cand"])
    assert r["verdict"] == "Accepted" and r["tests"][0]["output"].strip() == "15"
    cases = [("print(42)", "Wrong Answer"), ("while True: pass", "Time Limit Exceeded"),
             ("raise SystemExit(3)", "Runtime Error"), ("def f(:\n", "Runtime Error")]
    for code, want in cases:
        _, r = call("POST", "/api/problems/array-sum/submit", {"language": "python", "code": code}, S["cand"])
        assert r["verdict"] == want, (code, r["verdict"])
    if S["langs"].get("cpp"):
        _, r = call("POST", "/api/problems/array-sum/submit", {"language": "cpp", "code": "int main( { }"}, S["cand"])
        assert r["verdict"] == "Compile Error", r["verdict"]
    for lang in ("python", "cpp", "java"):
        if not S["langs"].get(lang):
            print(f"   {lang} toolchain missing - skipped")
            continue
        _, r = call("POST", "/api/problems/array-sum/submit", {"language": lang, "code": SOLUTIONS["array-sum"][lang]}, S["cand"])
        assert r["verdict"] == "Accepted" and r["passed"] == r["total"] > len(p["samples"]), (lang, r)
        print(f"   {lang}: Accepted on {r['total']} tests ({r['time_ms']} ms max)")


def solve_three():
    """Solve two more problems with the reference solutions shipped in problems.json (read from disk)."""
    bank = {p["slug"]: p for p in json.loads((ROOT / "data" / "problems.json").read_text(encoding="utf-8"))}
    for slug in ("reverse-words", "two-sum-count"):
        _, r = call("POST", f"/api/problems/{slug}/submit", {"language": "python", "code": bank[slug]["reference_python"]}, S["cand"])
        assert r["verdict"] == "Accepted", (slug, r["verdict"], r["message"])
    _, d = call("GET", "/api/me/dashboard", token=S["cand"])
    assert d["stats"]["solved_count"] >= 3
    assert d["user"]["level"] >= 3, d["user"]["level"]
    S["bank"] = bank


def contest():
    _, cs = call("GET", "/api/contests", token=S["cand"])
    live = [c for c in cs if c["status"] == "running"][0]
    ended = [c for c in cs if c["status"] == "ended"][0]
    assert ended["rated"], "finished contest should be rated"
    _, board = call("GET", f"/api/contests/{ended['id']}/leaderboard", token=S["cand"])
    assert board["rows"] and board["rows"][0]["rating_change"] is not None
    _, c = call("GET", f"/api/contests/{live['id']}", token=S["cand"])
    slug = c["problems"][0]["slug"]
    _, before = call("GET", f"/api/contests/{live['id']}/leaderboard", token=S["cand"])
    _, r = call("POST", f"/api/problems/{slug}/submit", {"language": "python", "code": S["bank"][slug]["reference_python"],
                                                         "contest_id": live["id"]}, S["cand"])
    assert r["verdict"] == "Accepted"
    _, after = call("GET", f"/api/contests/{live['id']}/leaderboard", token=S["cand"])
    me = [x for x in after["rows"] if x["name"] == "Smoke Test Candidate"]
    assert me and me[0]["solved"] == 1 and len(after["rows"]) == len(before["rows"]) + 1, "live standings did not update"
    _, lb = call("GET", "/api/leaderboard", token=S["cand"])
    assert any(x["me"] and x["solved"] >= 3 for x in lb), "global leaderboard missing my solves"


def resume():
    pdf = sorted((ROOT / "data" / "sample" / "resumes").glob("INFORMATION-TECHNOLOGY_*.pdf"))[0]
    raw, ctype = multipart({"target_role": "INFORMATION-TECHNOLOGY", "ai_tips": "false"}, "file", pdf.name, pdf.read_bytes())
    _, r = call("POST", "/api/resume/analyze", raw=raw, ctype=ctype, token=S["cand"])
    assert 0 < r["ats_score"] <= 100 and r["required_skills"] and r["top_roles"]
    print(f"   ATS {r['ats_score']} | predicted {r['predicted_label']} | missing {r['missing_skills'][:4]}")
    raw, ctype = multipart({}, "file", "x.pdf", b"not a pdf")
    call("POST", "/api/resume/analyze", raw=raw, ctype=ctype, token=S["cand"], ok=(400,))


def interview():
    if not S["ai"]:
        call("POST", "/api/interviews/start", {"role": "Python Developer"}, S["cand"], ok=(503,))
        print("   GEMINI_API_KEY not set - AI interview returns 503 as designed; add the key to run this step")
        return "SKIP"
    _, iv = call("POST", "/api/interviews/start", {"role": "Python Backend Developer", "level": "Entry", "count": 3}, S["cand"])
    assert len(iv["questions"]) >= 3
    answers = ["A Python list is mutable and ordered; a tuple is immutable, hashable when its items are, and slightly "
               "faster. I use tuples for fixed records such as coordinates and lists when the data changes."] * len(iv["questions"])
    _, r = call("POST", f"/api/interviews/{iv['id']}/submit", {"answers": answers}, S["cand"])
    assert r["status"] == "completed" and r["report"]["answers"][0]["scores"] and r["score"] is not None
    print(f"   AI interview score {r['score']}/10")


def recruiter():
    _, d = call("POST", "/api/drives", {"title": "Backend Engineers 2026", "company": "Acme Cloud", "role": "Python Developer",
                                        "min_level": 3, "required_skills": ["Python"]}, S["recruiter"])
    _, s = call("POST", f"/api/drives/{d['id']}/shortlist", token=S["recruiter"])
    rows = s["shortlist"]
    assert rows, "shortlist should not be empty"
    assert all(r["evidence"]["level"] >= 3 and "python" in r["evidence"]["skills"] for r in rows)
    assert [r["score"] for r in rows] == sorted((r["score"] for r in rows), reverse=True)
    ids = [r["candidate_id"] for r in rows[:3]]
    _, u = call("POST", f"/api/drives/{d['id']}/status", {"candidate_ids": ids, "status": "invited"}, S["recruiter"])
    assert u["updated"] == len(ids)
    _, g = call("GET", f"/api/drives/{d['id']}", token=S["recruiter"])
    assert g["drive"]["pipeline"]["invited"] == len(ids)
    print(f"   shortlist {len(rows)} candidates, invited {len(ids)}")


def expert():
    _, q = call("GET", "/api/interviews/expert/queue", token=S["expert"])
    assert isinstance(q, list)
    call("POST", "/api/interviews/expert/request", {"role": "Python Developer"}, S["cand"], ok=(200, 400))


def analytics():
    _, a = call("GET", "/api/analytics/readiness", token=S["career"])
    assert a["cohort_size"] >= 25 and a["weak_topics"] and a["levels"]
    print(f"   cohort {a['cohort_size']}, avg readiness {a['avg_readiness']}, weakest topic {a['weak_topics'][0]['topic']}")
    call("GET", "/api/analytics/readiness", token=S["cand"], ok=(403,))


if __name__ == "__main__":
    print(f"TalentTrack smoke test -> {BASE}")
    for name, fn in [("health", health), ("sign-up and logins", signup), ("aptitude test + level 2", aptitude),
                     ("technical MCQs (4 areas)", technical), ("judge verdicts (Python/C++/Java)", judge_verdicts),
                     ("solve 3 problems + level 3", solve_three), ("contest + live leaderboard + ratings", contest),
                     ("resume analysis", resume), ("AI mock interview", interview),
                     ("recruiter drive + shortlist + invites", recruiter), ("expert interview queue", expert),
                     ("readiness analytics", analytics)]:
        step(name, fn)
    fails = [r for r in results if r[0] == "FAIL"]
    print(f"\n{len(results) - len(fails)}/{len(results)} steps passed ({sum(r[0] == 'SKIP' for r in results)} skipped)")
    sys.exit(1 if fails else 0)
