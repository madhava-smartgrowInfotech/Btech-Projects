"""Evaluation for the six product objectives -> experiments/eval/metrics.json

 O1 practice + automated evaluation : judge verdict accuracy on a labelled suite, question-bank coverage
 O2 contests + leaderboards         : rating engine recovers true skill in simulated contests (Spearman)
 O3 level / interview tracking      : level funnel of the sample cohort; NLP relevance separates on/off-topic answers
 O4 resume analysis                 : classifier metrics, ATS discrimination (true vs wrong target role), PDF parsing
 O5 recruiter shortlisting          : eligibility precision/recall of shortlists, score vs readiness correlation
 O6 readiness analytics             : readiness coverage and weak-topic detection on the cohort
Run from the project root:  python ml/eval.py   (seeds data/app.db on first run)
"""
import csv
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sklearn.metrics import roc_auc_score  # noqa: E402

from app import seed  # noqa: E402
from app.db import Drive, SessionLocal, jdump  # noqa: E402
from app.routes.interviews import text_metrics  # noqa: E402
from app.routes.recruiter import rank_candidates  # noqa: E402
from app.services import judge, problems, progress  # noqa: E402
from app.services import resume as resume_svc  # noqa: E402
from app.services.contests import rating_deltas  # noqa: E402

SEED = 11
OUT = ROOT / "experiments" / "eval"


def spearman(a, b):
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0] * len(x)
        for k, i in enumerate(order):
            r[i] = k
        return r
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    return 1 - 6 * sum((x - y) ** 2 for x, y in zip(ra, rb)) / (n * (n * n - 1))


# ------------------------------------------------------------------ O1
CPP_SUM = "#include <bits/stdc++.h>\nint main(){int n;std::cin>>n;long long s=0,x;while(n--){std::cin>>x;s+=x;}std::cout<<s<<\"\\n\";}\n"
JAVA_SUM = ("import java.io.*;import java.util.*;\npublic class Main{public static void main(String[] a)throws IOException{"
            "BufferedReader b=new BufferedReader(new InputStreamReader(System.in));int n=Integer.parseInt(b.readLine().trim());"
            "StringTokenizer t=new StringTokenizer(b.readLine());long s=0;for(int i=0;i<n;i++)s+=Long.parseLong(t.nextToken());System.out.println(s);}}\n")
QUADRATIC_PAIRS = ("import sys\nd=sys.stdin.read().split();n,k=int(d[0]),int(d[1]);a=list(map(int,d[2:2+n]));c=0\n"
                   "for i in range(n):\n    for j in range(i+1,n):\n        if a[i]+a[j]==k: c+=1\nprint(c)\n")


def eval_judge():
    cases = []
    for p in problems.all_problems():
        cases.append((p["slug"], "python", p["reference_python"], "Accepted"))
        cases.append((p["slug"], "python", "print(-12345)\n", "Wrong Answer"))
        cases.append((p["slug"], "python", "import sys\nsys.stdin.read()\nraise ValueError('boom')\n", "Runtime Error"))
    for slug in ("array-sum", "gcd-lcm", "prime-count", "lis-length"):
        cases.append((slug, "python", "while True:\n    pass\n", "Time Limit Exceeded"))
    cases.append(("two-sum-count", "python", QUADRATIC_PAIRS, "Time Limit Exceeded"))  # O(n^2) on the 2e5 hidden test
    tc = judge.toolchain()
    if tc["cpp"]:
        cases += [("array-sum", "cpp", CPP_SUM, "Accepted"), ("array-sum", "cpp", "int main( {", "Compile Error")]
    if tc["java"]:
        cases += [("array-sum", "java", JAVA_SUM, "Accepted"), ("array-sum", "java", "public class Main {", "Compile Error")]

    def run(c):
        slug, lang, code, want = c
        t = time.time()
        r = judge.judge(lang, code, problems.tests_for_submit(problems.get(slug)))
        return {"slug": slug, "lang": lang, "expected": want, "got": r["verdict"], "seconds": round(time.time() - t, 2)}

    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(run, cases))
    by = {}
    for r in res:
        b = by.setdefault(r["expected"], {"cases": 0, "correct": 0})
        b["cases"] += 1
        b["correct"] += r["got"] == r["expected"]
    bank = json.loads((ROOT / "data" / "question_bank.json").read_text(encoding="utf-8"))
    topics = {}
    for q in bank:
        topics.setdefault(q["kind"], set()).add(q["topic"])
    return {
        "judge_cases": len(res), "judge_verdict_accuracy": round(sum(r["got"] == r["expected"] for r in res) / len(res), 4),
        "judge_by_verdict": by, "judge_mismatches": [r for r in res if r["got"] != r["expected"]],
        "judge_mean_seconds_per_submission": round(sum(r["seconds"] for r in res) / len(res), 2),
        "languages_available": {k: bool(tc[k]) for k in ("python", "cpp", "java")},
        "problems": len(problems.all_problems()),
        "hidden_tests_total": sum(len(p["hidden"]) for p in problems.all_problems()),
        "question_bank": {"total": len(bank), "aptitude": sum(q["kind"] == "aptitude" for q in bank),
                          "technical": sum(q["kind"] == "technical" for q in bank),
                          "technical_topics": sorted(topics["technical"]), "aptitude_topics": len(topics["aptitude"])},
    }


# ------------------------------------------------------------------ O2
def eval_ratings(players=30, contests=15, noise=250):
    rng = random.Random(SEED)
    skill = [rng.gauss(1500, 300) for _ in range(players)]
    rating = [1200] * players
    history = []
    for _ in range(contests):
        perf = [s + rng.gauss(0, noise) for s in skill]
        order = sorted(range(players), key=lambda i: -perf[i])
        ranks = [0] * players
        for r, i in enumerate(order, 1):
            ranks[i] = r
        d = rating_deltas(rating, ranks)
        rating = [r + x for r, x in zip(rating, d)]
        history.append(round(spearman(skill, rating), 4))
    return {"simulated_players": players, "simulated_contests": contests, "performance_noise_sd": noise,
            "spearman_skill_vs_rating_after_1": history[0], "spearman_skill_vs_rating_final": history[-1],
            "spearman_by_contest": history, "rating_sum_drift": sum(rating) - 1200 * players}


# ------------------------------------------------------------------ O3
def eval_levels_and_nlp(db):
    cands = [u for u in progress.candidates(db) if u.is_sample]
    stats = [progress.stats(db, u) for u in cands]
    funnel = {f"L{L['level']} {L['name']}": sum(s["level"] >= L["level"] for s in stats) for L in progress.LEVELS}
    # NLP relevance: each MCQ question vs its own explanation (on-topic) and vs a random other explanation (off-topic)
    bank = [q for q in json.loads((ROOT / "data" / "question_bank.json").read_text(encoding="utf-8"))
            if q["source"] == "original"]
    rng = random.Random(SEED)
    y, s = [], []
    for q in bank:
        other = rng.choice([x for x in bank if x["topic"] != q["topic"]])
        y += [1, 0]
        s += [text_metrics(q["text"], [], q["explanation"])["relevance"],
              text_metrics(q["text"], [], other["explanation"])["relevance"]]
    return {"sample_cohort": len(cands), "level_funnel_reached": funnel,
            "nlp_relevance_auc_on_vs_off_topic": round(roc_auc_score(y, s), 4), "nlp_pairs": len(y)}


# ------------------------------------------------------------------ O4
def eval_resume():
    clf = json.loads((ROOT / "experiments" / "resume_classifier" / "metrics.json").read_text())
    csv.field_size_limit(10**8)
    rows = []
    with open(ROOT / "data" / "resume" / "Resume.csv", encoding="utf-8", newline="") as f:
        rows = [(r["Resume_str"], r["Category"]) for r in csv.DictReader(f)]
    rng = random.Random(SEED)
    sample = rng.sample(rows, 150)
    cats = sorted({c for _, c in rows})
    true_ats, wrong_ats, skill_cov = [], [], []
    for text, cat in sample:
        a = resume_svc.analyze(text, cat)
        true_ats.append(a["ats_score"])
        skill_cov.append(len(a["matched_skills"]) / max(1, len(a["required_skills"])))
        wrong_ats.append(resume_svc.analyze(text, rng.choice([c for c in cats if c != cat]))["ats_score"])
    pdfs = sorted((ROOT / "data" / "sample" / "resumes").glob("*.pdf"))
    parsed, correct_top3 = 0, 0
    for p in pdfs:
        text = resume_svc.extract_text(p.read_bytes())
        if len(text) > 100:
            parsed += 1
            cat = p.name.rsplit("_", 1)[0]
            correct_top3 += cat in [r["role"] for r in resume_svc.classify(text)[:3]]
    ats_auc = roc_auc_score([1] * len(true_ats) + [0] * len(wrong_ats), true_ats + wrong_ats)
    return {"classifier_accuracy": clf["accuracy"], "classifier_macro_f1": clf["macro_f1"],
            "classifier_top3_accuracy": clf["top3_accuracy"], "classes": clf["n_classes"],
            "ats_mean_true_role": round(sum(true_ats) / len(true_ats), 1),
            "ats_mean_wrong_role": round(sum(wrong_ats) / len(wrong_ats), 1),
            "ats_auc_true_vs_wrong_role": round(ats_auc, 4), "ats_resumes_evaluated": len(sample),
            "mean_role_skill_coverage": round(sum(skill_cov) / len(skill_cov), 3),
            "sample_pdfs": len(pdfs), "pdf_parse_rate": round(parsed / len(pdfs), 3),
            "sample_pdf_top3_role_hit_rate": round(correct_top3 / max(1, parsed), 3)}


# ------------------------------------------------------------------ O5 / O6
def eval_shortlist_and_analytics(db):
    stats = {u.id: progress.stats(db, u) for u in progress.candidates(db)}
    out = {}
    for name, lvl, skills in (("level3_python", 3, ["python"]), ("level2_sql", 2, ["sql"]), ("level1_excel", 1, ["excel"])):
        d = Drive(recruiter_id=0, title=name, company="eval", role="eval", min_level=lvl, required_skills=jdump(skills),
                  min_readiness=0, min_aptitude=0)
        ranked, _ = rank_candidates(db, d)
        got = {r["candidate_id"] for r in ranked}
        truth = {uid for uid, s in stats.items() if s["level"] >= lvl and all(k in s["skills"] for k in skills)}
        tp = len(got & truth)
        out[name] = {"shortlisted": len(got), "eligible": len(truth),
                     "precision": round(tp / len(got), 3) if got else 1.0, "recall": round(tp / len(truth), 3) if truth else 1.0,
                     "spearman_score_vs_readiness": round(spearman([r["score"] for r in ranked],
                                                                   [r["evidence"]["readiness"] for r in ranked]), 3) if len(ranked) > 2 else None}
    ready = [s["readiness"] for s in stats.values()]
    from app.routes.analytics import readiness
    a = readiness(include_sample=True, user=None, db=db)
    return out, {"cohort": len(ready), "candidates_with_readiness": sum(r > 0 for r in ready),
                 "avg_readiness": a["avg_readiness"], "weak_topics_top3": [(t["topic"], t["accuracy"]) for t in a["weak_topics"][:3]],
                 "topics_tracked": len(a["topics"])}


def main():
    seed.run()
    db = SessionLocal()
    t0 = time.time()
    try:
        m = {"O1_practice_and_judge": eval_judge(), "O2_contest_ratings": eval_ratings(),
             "O3_levels_and_interview_nlp": eval_levels_and_nlp(db), "O4_resume_analysis": eval_resume()}
        m["O5_recruiter_shortlisting"], m["O6_readiness_analytics"] = eval_shortlist_and_analytics(db)
    finally:
        db.close()
    m["eval_seconds"] = round(time.time() - t0, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(json.dumps(m, indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("judge_mismatches", "spearman_by_contest")}
                      if isinstance(v, dict) else v for k, v in m.items()}, indent=1))


if __name__ == "__main__":
    main()
