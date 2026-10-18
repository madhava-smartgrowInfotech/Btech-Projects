"""Source-code metrics per function (Python AST adaptation of the base paper's 14 metrics).

Base paper: "Leveraging Key Source Code Metrics for Predicting Software Vulnerabilities With
Machine Learning" (IEEE Access 2026).  The paper derives 14 metrics from a Code Property Graph of
C/C++ functions.  Here the same *families* of metrics are computed from Python's AST/CFG so the
technique can run inside a Python-only pull-request pipeline.  The paper's most influential
metrics (M1 cyclomatic complexity, M5 caller-argument count, M6/M7 pointer-arithmetic ->
index-arithmetic, M9 nested control structures, M11 control dependency) keep their numbering.
"""
from __future__ import annotations

import ast
import re
from typing import Iterator

METRICS = [
    ("M1", "cyclomatic", "Cyclomatic complexity", "Independent paths (branches) through the function"),
    ("M2", "loc", "Lines of code", "Physical lines of the function body"),
    ("M3", "n_vars", "Local variables", "Distinct names assigned in the function"),
    ("M4", "n_calls", "Call sites", "Number of function/method calls (fan-out)"),
    ("M5", "n_params", "Parameters", "Variables in the function's argument list (caller-argument metric)"),
    ("M6", "idx_arith", "Index arithmetic", "Subscripts/slices computed with arithmetic (analogue of pointer arithmetic)"),
    ("M7", "idx_vars", "Vars in index arithmetic", "Distinct variables used inside arithmetic subscripts"),
    ("M8", "n_io", "I/O & query calls", "open/read/write/execute/send style calls"),
    ("M9", "max_nesting", "Nested control structures", "Deepest nesting of if/for/while/try/with"),
    ("M10", "n_loops", "Loops", "for/while/comprehension loops"),
    ("M11", "max_ctrl_dep", "Max control dependency", "Max number of guarding conditions on any statement"),
    ("M12", "n_danger", "Risky API calls", "eval/exec/os.system/subprocess/pickle/yaml.load, weak hash/PRNG ..."),
    ("M13", "n_strbuild_args", "String-built sinks", "Call arguments or returned markup built by f-string/%/format/+"),
    ("M14", "n_sources", "Untrusted/sensitive sources", "request.*, input(), sys.argv, secret-named literals ..."),
]
FEATURES = [m[1] for m in METRICS]
FEATURE_LABEL = {m[1]: f"{m[0]} {m[2]}" for m in METRICS}
FEATURE_ID = {m[1]: m[0] for m in METRICS}

DANGEROUS = {
    "eval", "exec", "compile", "os.system", "os.popen", "subprocess.call", "subprocess.run", "subprocess.Popen",
    "subprocess.check_output", "subprocess.check_call", "subprocess.getoutput", "pickle.load", "pickle.loads",
    "cPickle.loads", "marshal.loads", "yaml.load", "yaml.unsafe_load", "shelve.open", "dill.loads", "jsonpickle.decode",
    "__import__", "importlib.import_module", "render_template_string", "mark_safe", "Markup",
    "hashlib.md5", "hashlib.sha1", "random.random", "random.randint", "random.choice", "random.getrandbits",
    "random.randrange", "tempfile.mktemp", "os.chmod",
}
IO_LAST = {"open", "read", "write", "execute", "executemany", "executescript", "send", "sendall", "recv", "urlopen",
           "get", "post", "put", "delete", "connect", "send_file", "readlines", "writelines", "commit", "fetchall",
           "fetchone", "raw"}
SOURCE_PREFIX = ("request.", "self.request.", "flask.request.", "sys.argv", "os.environ", "os.getenv",
                 "st.text_input", "st.text_area")
SOURCE_CALLS = {"input", "raw_input"}
SECRET_NAME_RE = re.compile(r"(passw|secret|api_?key|token|private_key|credential)", re.I)


def dotted(node) -> str:
    """Best-effort dotted name for Name/Attribute chains and calls on them."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return dotted(node.func)
    if isinstance(node, ast.Subscript):
        return dotted(node.value)
    return ""


def is_string_built(node) -> bool:
    """True for f-strings with values, 'a' + x, 'a %s' % x and 'a{}'.format(x)."""
    if isinstance(node, ast.JoinedStr):
        return any(isinstance(v, ast.FormattedValue) for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        sides = (node.left, node.right)
        has_str = any(_is_strish(s) for s in sides)
        has_dyn = any(not isinstance(s, ast.Constant) for s in sides)
        return has_str and has_dyn
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        return isinstance(node.func.value, (ast.Constant, ast.JoinedStr)) and bool(node.args or node.keywords)
    return False


def _is_strish(n) -> bool:
    return (isinstance(n, ast.Constant) and isinstance(n.value, str)) or isinstance(n, ast.JoinedStr) or (
        isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)) and (_is_strish(n.left) or _is_strish(n.right)))


def is_source_expr(node) -> bool:
    d = dotted(node)
    if not d:
        return False
    if isinstance(node, ast.Call) and d in SOURCE_CALLS:
        return True
    return any(d == p.rstrip(".") or d.startswith(p) for p in SOURCE_PREFIX)


def iter_functions(tree: ast.AST) -> Iterator[tuple[str, ast.AST]]:
    """Yield (qualified_name, node) for every function, plus '<module>' if it has script code."""
    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{prefix}{child.name}"
                yield q, child
                yield from walk(child, q + ".")
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, f"{prefix}{child.name}.")
            else:
                yield from walk(child, prefix)
    yield from walk(tree, "")


def _bool_ops(node) -> int:
    return sum(len(n.values) - 1 for n in ast.walk(node) if isinstance(n, ast.BoolOp))


def function_metrics(fn: ast.AST) -> dict:
    """Compute the 14 metrics for a FunctionDef (or Module for script-level code)."""
    is_fn = isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
    args = fn.args if is_fn else None
    params = []
    if args:
        params = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs if a.arg not in ("self", "cls")]
        if args.vararg:
            params.append(args.vararg.arg)
        if args.kwarg:
            params.append(args.kwarg.arg)

    body_nodes = list(ast.walk(fn))
    # do not descend into nested function bodies for per-function counts
    def own_nodes(root):
        stack = list(ast.iter_child_nodes(root))
        while stack:
            n = stack.pop()
            yield n
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            stack.extend(ast.iter_child_nodes(n))

    nodes = list(own_nodes(fn)) if is_fn else [n for n in body_nodes
                                              if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    cyclo = 1
    n_loops = n_calls = n_io = n_danger = n_str = idx_arith = 0
    idx_vars: set[str] = set()
    assigned: set[str] = set()
    src_pos: set[tuple[int, int]] = set()
    for n in nodes:
        if isinstance(n, (ast.If, ast.IfExp, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.Assert)):
            cyclo += 1
        if isinstance(n, (ast.For, ast.AsyncFor, ast.While)):
            n_loops += 1
        if isinstance(n, ast.comprehension):
            n_loops += 1
            cyclo += 1 + len(n.ifs)
        if isinstance(n, ast.BoolOp):
            cyclo += len(n.values) - 1
        if hasattr(ast, "match_case") and isinstance(n, ast.match_case):
            cyclo += 1
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            assigned.add(n.id)
        if isinstance(n, ast.Return) and n.value is not None and is_string_built(n.value):
            n_str += 1
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)                 and len(n.value.value) >= 4 and any(isinstance(t, ast.Name) and SECRET_NAME_RE.search(t.id) for t in n.targets):
            src_pos.add((n.lineno, n.col_offset))
        if isinstance(n, ast.Assign) and is_string_built(n.value) and any(
                isinstance(c, ast.Constant) and isinstance(c.value, str) and re.search(r"<\s*[a-zA-Z]", c.value)
                for c in ast.walk(n.value)):
            n_str += 1
        if isinstance(n, ast.Subscript):
            sl = n.slice
            if any(isinstance(x, ast.BinOp) for x in ast.walk(sl)):
                idx_arith += 1
                idx_vars.update(x.id for x in ast.walk(sl) if isinstance(x, ast.Name))
        if isinstance(n, ast.Call):
            n_calls += 1
            d = dotted(n.func)
            last = d.rsplit(".", 1)[-1]
            if d in DANGEROUS or last in ("eval", "exec", "system", "popen"):
                n_danger += 1
            if last in IO_LAST and ("." in d or d == "open"):
                n_io += 1
            if any(is_string_built(a) for a in n.args) or any(is_string_built(k.value) for k in n.keywords):
                n_str += 1
            if is_source_expr(n):
                src_pos.add((n.lineno, n.col_offset))
        elif isinstance(n, (ast.Attribute, ast.Subscript)) and isinstance(n.ctx, ast.Load) and is_source_expr(n):
            src_pos.add((n.lineno, n.col_offset))

    n_src = len(src_pos)
    # nesting depth and control dependency (recursive over statements)
    max_nest = 0
    max_dep = 0

    def visit(stmts, depth, dep):
        nonlocal max_nest, max_dep
        for s in stmts:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            max_dep = max(max_dep, dep)
            if isinstance(s, (ast.If, ast.While)):
                d = depth + 1
                max_nest = max(max_nest, d)
                nd = dep + 1 + _bool_ops(s.test)
                visit(s.body, d, nd)
                visit(s.orelse, d, dep + 1)
            elif isinstance(s, (ast.For, ast.AsyncFor)):
                d = depth + 1
                max_nest = max(max_nest, d)
                visit(s.body, d, dep + 1)
                visit(s.orelse, d, dep + 1)
            elif isinstance(s, (ast.With, ast.AsyncWith)):
                d = depth + 1
                max_nest = max(max_nest, d)
                visit(s.body, d, dep)
            elif isinstance(s, ast.Try):
                d = depth + 1
                max_nest = max(max_nest, d)
                visit(s.body, d, dep)
                for h in s.handlers:
                    visit(h.body, d, dep + 1)
                visit(s.orelse, d, dep)
                visit(s.finalbody, d, dep)
    visit(fn.body, 0, 0)

    loc = (getattr(fn, "end_lineno", 0) - getattr(fn, "lineno", 0) + 1) if is_fn else max(
        (getattr(n, "end_lineno", 0) or 0) for n in fn.body) if getattr(fn, "body", None) else 0
    return {
        "cyclomatic": cyclo, "loc": max(loc, 1), "n_vars": len(assigned | set(params)), "n_calls": n_calls,
        "n_params": len(params), "idx_arith": idx_arith, "idx_vars": len(idx_vars), "n_io": n_io,
        "max_nesting": max_nest, "n_loops": n_loops, "max_ctrl_dep": max_dep, "n_danger": n_danger,
        "n_strbuild_args": n_str, "n_sources": n_src,
    }


def metrics_for_source(source: str) -> list[dict]:
    """Metrics for every function in a source string (used by the Model Lab 'try it')."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out = []
    for name, fn in iter_functions(tree):
        m = function_metrics(fn)
        m.update(name=name, line=fn.lineno)
        out.append(m)
    return out
