import ast
from autosecai.agents import review_changes
from autosecai.codeintel import RepoIndex
from autosecai.diffutil import apply_fixes, diff_from_versions, parse_unified_diff
from autosecai.metrics import metrics_for_source
from autosecai.mlmodel import predict_metrics, smote_tomek
from autosecai.rules import analyze_source
from autosecai.samples import DEMO_DIFF, DEMO_REPO
import numpy as np

VULN = 'def f(n):\n    cur.execute(f"SELECT * FROM t WHERE a = \'{n}\'")\n'
SAFE = 'def f(n):\n    cur.execute("SELECT * FROM t WHERE a = ?", (n,))\n'


def rules(src):
    return {f.rule_id for f in analyze_source(src, "x.py")[0]}


def test_sqli_detected_and_safe_not():
    assert "SQLI" in rules(VULN)
    assert "SQLI" not in rules(SAFE)


def test_taint_from_request():
    src = "def f():\n    h = request.args.get('h')\n    os.system('ping ' + h)\n"
    assert "CMDI" in rules(src)


def test_sanitizer_stops_taint():
    src = "def f():\n    h = int(request.args.get('h'))\n    os.system(f'sleep {h}')\n"
    assert "CMDI" not in rules(src)


def test_autofix_parametrises_and_reparses():
    f = next(x for x in analyze_source(VULN, "x.py")[0] if x.rule_id == "SQLI")
    new, applied = apply_fixes(VULN, [f.fix])
    ast.parse(new)
    assert applied and "?" in new and "SQLI" not in rules(new)


def test_metrics_cyclomatic():
    m = metrics_for_source("def f(a):\n    if a:\n        for i in a:\n            pass\n")[0]
    assert m["cyclomatic"] == 3 and m["max_nesting"] == 2


def test_diff_parsing_and_review():
    ch = parse_unified_diff(DEMO_DIFF)
    assert ch and ch[0].added
    r = review_changes(ch)
    assert r["verdict"] == "BLOCK" and r["stats"]["autofix_verified"] > 0


def test_before_after_marks_preexisting():
    cf = diff_from_versions("import os\nx = 1\n", "import os\nx = 1\ny = eval(input())\n", "a.py")
    r = review_changes([cf])
    assert any(f["rule_id"] == "EVAL" and f["in_diff"] for f in r["findings"])


def test_ml_scores_vulnerable_higher():
    hi = predict_metrics(metrics_for_source(VULN.replace("f(n)", "f(n, q=request.args.get('x'))"))[0])["probability"]
    lo = predict_metrics(metrics_for_source("def g(a):\n    return a + 1\n")[0])["probability"]
    assert hi > lo


def test_smote_tomek_balances():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(0, 1, (200, 3)), rng.normal(3, 1, (20, 3))])
    y = np.array([0] * 200 + [1] * 20)
    Xb, yb, _ = smote_tomek(X, y)
    assert abs((yb == 1).sum() - (yb == 0).sum()) < 30


def test_codebase_finds_auth():
    ix = RepoIndex(DEMO_REPO, "demo")
    assert ix.ask("where is authentication implemented?")["hits"][0]["file"] == "app/auth.py"
    assert any(r["path"] == "/auth/login" for r in ix.routes)
