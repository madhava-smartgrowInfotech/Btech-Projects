"""Static analysis engine: AST + lightweight taint tracking (Python) and regex rules (JS/PHP/Java...).

Taint levels: 0 clean, 1 string-built from variables, 2 derived from a function parameter,
3 derived from a direct external source (request.*, input(), sys.argv ...).
"""
from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass, field

from .knowledge import rule as kb
from .metrics import (dotted, is_source_expr, is_string_built, iter_functions, function_metrics)

SECRET_NAME = re.compile(r"(passw(or)?d|passwd|pwd|secret|api[_-]?key|apikey|token|private[_-]?key|access[_-]?key|"
                         r"auth[_-]?key|client[_-]?secret|credential)", re.I)
SECRET_VALUE = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Stripe/OpenAI-style key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}|\bsk-[A-Za-z0-9]{32,}")),
]
PLACEHOLDER = re.compile(r"^(|x+|\*+|changeme|change_me|your[_-].*|<.*>|\$\{.*\}|%\(.*\)s|none|null|todo|example.*)$", re.I)
SANITIZERS = {"escape", "html.escape", "markupsafe.escape", "shlex.quote", "int", "float", "bool", "len", "secure_filename",
              "os.path.basename", "basename", "quote", "urllib.parse.quote", "bleach.clean", "sanitize", "uuid.UUID",
              "re.escape", "str.isdigit", "Path.name", "abs", "round"}
TOKEN_CONTEXT = re.compile(r"(token|secret|password|passwd|otp|session|nonce|salt|api_?key|reset|csrf|auth)", re.I)
SQL_SINKS = {"execute", "executemany", "executescript", "raw", "read_sql", "read_sql_query", "text", "mogrify"}
FILE_SINKS = {"open", "send_file", "os.remove", "os.unlink", "shutil.rmtree", "shutil.copy", "shutil.move", "os.rename",
              "os.makedirs", "os.listdir", "pathlib.Path", "Path", "codecs.open", "io.open", "os.rmdir"}
HTTP_SINKS = {"requests.get", "requests.post", "requests.put", "requests.delete", "requests.head", "requests.request",
              "requests.patch", "urllib.request.urlopen", "urlopen", "httpx.get", "httpx.post", "urllib3.request",
              "session.get", "session.post"}
SUBPROC = {"subprocess.call", "subprocess.run", "subprocess.Popen", "subprocess.check_output", "subprocess.check_call",
           "subprocess.getoutput", "subprocess.getstatusoutput", "commands.getoutput"}
DESER = {"pickle.load", "pickle.loads", "cPickle.load", "cPickle.loads", "marshal.load", "marshal.loads", "dill.load",
         "dill.loads", "shelve.open", "jsonpickle.decode", "pandas.read_pickle", "pd.read_pickle", "joblib.load"}
XML_SINKS = {"xml.etree.ElementTree.parse", "xml.etree.ElementTree.fromstring", "ET.parse", "ET.fromstring",
             "etree.parse", "etree.fromstring", "minidom.parse", "minidom.parseString", "xml.dom.minidom.parseString",
             "xml.dom.minidom.parse", "xml.sax.parseString", "xml.sax.parse"}
LOG_CALLS = {"print", "logger.info", "logger.debug", "logger.warning", "logger.error", "logging.info", "logging.debug",
             "logging.warning", "logging.error", "log.info", "log.debug", "app.logger.info", "app.logger.debug"}
WEAK_RANDOM = {"random.random", "random.randint", "random.choice", "random.randrange", "random.getrandbits",
               "random.choices", "random.sample"}


@dataclass
class Finding:
    rule_id: str
    file: str
    line: int
    end_line: int
    function: str = ""
    snippet: str = ""
    confidence: str = "medium"
    evidence: str = ""
    sink: str = ""
    severity: str = ""          # filled from KB unless overridden
    detector: str = "static"
    fix: dict | None = None     # {start:(line,col), end:(line,col), text, note}
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        meta = kb(self.rule_id)
        self.severity = self.severity or meta["severity"]

    @property
    def category(self):
        return kb(self.rule_id)["category"]

    @property
    def key(self):
        return f"{self.rule_id}:{self.file}:{self.line}"


# ---------------------------------------------------------------- autofix helpers
def _flatten_concat(node):
    """Flatten f-string / '+' chain to parts: ('s', text) | ('e', expr_node)."""
    parts = []
    if isinstance(node, ast.JoinedStr):
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(("s", str(v.value)))
            elif isinstance(v, ast.FormattedValue):
                parts.append(("e", v.value))
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        parts = _flatten_concat(node.left) + _flatten_concat(node.right)
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        parts.append(("s", node.value))
    else:
        parts.append(("e", node))
    return parts


def sql_parametrize(call: ast.Call, ph="?"):
    if not call.args or call.keywords or len(call.args) != 1:
        return None
    parts = _flatten_concat(call.args[0])
    if not any(k == "e" for k, _ in parts):
        return None
    text, params = "", []
    for i, (k, v) in enumerate(parts):
        if k == "s":
            text += v
        else:
            # strip quote chars around placeholders: '{x}' -> ?
            if text.endswith(("'", '"')):
                text = text[:-1]
                if i + 1 < len(parts) and parts[i + 1][0] == "s" and parts[i + 1][1][:1] in ("'", '"'):
                    parts[i + 1] = ("s", parts[i + 1][1][1:])
            text += ph
            params.append(ast.unparse(v))
    recv = ast.unparse(call.func)
    tup = "(" + ", ".join(params) + ("," if len(params) == 1 else "") + ")"
    lit = repr(text) if any(c in text for c in ('"', "\n", "\\")) else '"' + text + '"'
    return f"{recv}({lit}, {tup})"


def shell_to_list(call: ast.Call):
    """os.system(f"ping -c 1 {host}") -> subprocess.run(["ping", "-c", "1", host], check=True)"""
    if not call.args:
        return None
    parts = _flatten_concat(call.args[0])
    tokens: list[list] = [[]]
    for k, v in parts:
        if k == "s":
            chunks = re.split(r"(\s+)", v)
            for c in chunks:
                if not c:
                    continue
                if c.isspace():
                    if tokens[-1]:
                        tokens.append([])
                else:
                    tokens[-1].append(("s", c))
        else:
            tokens[-1].append(("e", v))
    tokens = [t for t in tokens if t]
    if not tokens:
        return None
    if any(c in "|&;<>`$" for t in tokens for k, c in t if k == "s"):
        return None
    out = []
    for t in tokens:
        if len(t) == 1 and t[0][0] == "s":
            out.append(repr(t[0][1]))
        elif len(t) == 1:
            out.append(ast.unparse(t[0][1]))
        else:
            out.append("f\"" + "".join(c.replace('"', '\\"') if k == "s" else "{" + ast.unparse(c) + "}" for k, c in t) + "\"")
    return "subprocess.run([" + ", ".join(out) + "], check=True, timeout=10)"


# ---------------------------------------------------------------- Python analyzer
class PyAnalyzer:
    def __init__(self, source: str, filename: str, line_offset: int = 0):
        self.src = source
        self.file = filename
        self.off = line_offset
        self.lines = source.splitlines()
        self.findings: list[Finding] = []
        self.tree: ast.AST | None = None
        self.func_metrics: list[dict] = []

    # -- helpers
    def _snip(self, node) -> str:
        ln = getattr(node, "lineno", 1)
        return self.lines[ln - 1].strip()[:200] if 0 < ln <= len(self.lines) else ""

    def _add(self, rule_id, node, func="", confidence="medium", evidence="", sink="", severity="", fix=None, end=None):
        ln = getattr(node, "lineno", 1)
        f = Finding(rule_id, self.file, ln + self.off, (end or getattr(node, "end_lineno", ln)) + self.off, func,
                    self._snip(node), confidence, evidence, sink, severity=severity, fix=fix)
        if not any(x.key == f.key for x in self.findings):
            self.findings.append(f)
        return f

    def _seg_fix(self, node, new_text, note):
        """Fix replacing the source segment of `node` (single/multi-line, char offsets)."""
        return {"start": (node.lineno, node.col_offset), "end": (node.end_lineno, node.end_col_offset),
                "text": new_text, "note": note}

    # -- taint
    def _level_of(self, node, env, params) -> int:
        if node is None:
            return 0
        if isinstance(node, ast.Constant):
            return 0
        if isinstance(node, ast.Name):
            return env.get(node.id, 2 if node.id in params else 0)
        if is_source_expr(node):
            return 3
        if isinstance(node, ast.Call):
            d = dotted(node.func)
            if d in SANITIZERS or d.rsplit(".", 1)[-1] in ("escape", "quote", "basename", "secure_filename"):
                return 0
            lv = max([self._level_of(a, env, params) for a in node.args] +
                     [self._level_of(k.value, env, params) for k in node.keywords] +
                     [self._level_of(node.func.value, env, params) if isinstance(node.func, ast.Attribute) else 0])
            return lv
        if isinstance(node, (ast.JoinedStr, ast.BinOp, ast.Attribute, ast.Subscript, ast.Tuple, ast.List, ast.IfExp,
                             ast.FormattedValue, ast.Dict, ast.Set, ast.Starred, ast.BoolOp, ast.UnaryOp)):
            lv = max((self._level_of(c, env, params) for c in ast.iter_child_nodes(node)
                      if not isinstance(c, (ast.operator, ast.Load, ast.Store, ast.cmpop, ast.boolop, ast.unaryop))),
                     default=0)
            if is_string_built(node):
                lv = max(lv, 1)
            return lv
        return 0

    def _build_env(self, fn, params):
        env: dict[str, int] = {}
        assigns = [n for n in ast.walk(fn) if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.For, ast.NamedExpr))]
        assigns.sort(key=lambda n: (n.lineno, n.col_offset))
        for _ in range(2):
            for n in assigns:
                if isinstance(n, ast.Assign):
                    lv = self._level_of(n.value, env, params)
                    for t in n.targets:
                        for name in [x for x in ast.walk(t) if isinstance(x, ast.Name)]:
                            env[name.id] = lv
                elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
                    lv = max(self._level_of(n.value, env, params), env.get(n.target.id, 0))
                    if is_string_built(n.value) or isinstance(n.op, ast.Add):
                        lv = max(lv, 1 if lv else 0)
                    env[n.target.id] = lv
                elif isinstance(n, ast.AnnAssign) and n.value is not None and isinstance(n.target, ast.Name):
                    env[n.target.id] = self._level_of(n.value, env, params)
                elif isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name):
                    env[n.target.id] = self._level_of(n.value, env, params)
                elif isinstance(n, ast.For):
                    lv = self._level_of(n.iter, env, params)
                    for name in [x for x in ast.walk(n.target) if isinstance(x, ast.Name)]:
                        env[name.id] = lv
        return env

    @staticmethod
    def _conf(level):
        return {3: "high", 2: "medium"}.get(level, "low")

    def _taint_only(self, node, env, params) -> int:
        """Taint from real sources/parameters only (ignores the 'string-built' bump)."""
        if node is None:
            return 0
        best = 0
        for n in ast.walk(node):
            if isinstance(n, ast.Name):
                best = max(best, env.get(n.id, 2 if n.id in params else 0) if env.get(n.id, 2 if n.id in params else 0) >= 2 else 0)
            if is_source_expr(n):
                best = 3
        return best

    def _tainted_desc(self, node, env, params) -> str:
        names = [n.id for n in ast.walk(node) if isinstance(n, ast.Name) and env.get(n.id, 2 if n.id in params else 0) >= 2]
        if names:
            return "value(s) " + ", ".join(sorted(set(names))[:3]) + (" from request/input" if any(
                env.get(n, 0) == 3 for n in names) else " from function parameters")
        if is_source_expr(node):
            return "direct external input " + ast.unparse(node)[:40]
        return "string-built from variables"

    # -- main scan
    def scan(self):
        try:
            self.tree = ast.parse(self.src)
        except SyntaxError:
            self.tree = self._robust_parse()
        if self.tree is None:
            return self
        self._module_level()
        scopes = list(iter_functions(self.tree))
        seen_calls: set[int] = set()
        for qual, fn in scopes:
            self._scan_scope(fn, qual, seen_calls)
        mod = self.tree
        self._scan_scope(mod, "<module>", seen_calls, module=True)
        self._quality(scopes)
        return self

    def _robust_parse(self):
        """Hunk snippets may start mid-block; try dedent and wrapping."""
        code = textwrap.dedent(self.src)
        for attempt in (code, "if True:\n" + textwrap.indent(code, "    "), "def _hunk_():\n" + textwrap.indent(code, "    ")):
            try:
                tree = ast.parse(attempt)
                if attempt is not code:
                    ast.increment_lineno(tree, -1)
                    self._wrapped = True
                return tree
            except SyntaxError:
                continue
        return None

    def _scan_scope(self, fn, qual, seen, module=False):
        is_fn = isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
        params = set()
        if is_fn:
            a = fn.args
            params = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs if x.arg not in ("self", "cls")}
            if a.vararg:
                params.add(a.vararg.arg)
            if a.kwarg:
                params.add(a.kwarg.arg)
        env = self._build_env(fn, params)
        for stmt_fn in ([fn] if is_fn or module else []):
            for node in self._own_walk(stmt_fn):
                if isinstance(node, ast.Call) and id(node) not in seen:
                    seen.add(id(node))
                    self._check_call(node, qual, env, params)
                elif isinstance(node, ast.Return) and node.value is not None:
                    self._check_return(node, qual, env, params)
        if is_fn:
            for dec in fn.decorator_list:
                if dotted(dec).endswith("csrf_exempt"):
                    self._add("CSRF_EXEMPT", dec, qual, "high")

    def _own_walk(self, root):
        stack = list(ast.iter_child_nodes(root))
        while stack:
            n = stack.pop()
            yield n
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            stack.extend(ast.iter_child_nodes(n))

    def _kw(self, call, name):
        for k in call.keywords:
            if k.arg == name:
                return k.value
        return None

    def _check_return(self, node, qual, env, params):
        v = node.value
        if is_string_built(v) or isinstance(v, ast.JoinedStr):
            consts = "".join(str(c.value) for c in ast.walk(v) if isinstance(c, ast.Constant) and isinstance(c.value, str))
            if re.search(r"<\s*[a-zA-Z/!]", consts):
                lv = self._level_of(v, env, params)
                if lv >= 2 and not self._escaped(v):
                    self._add("XSS", node, qual, self._conf(lv), self._tainted_desc(v, env, params), "return <html>")

    @staticmethod
    def _escaped(v):
        return any(isinstance(c, ast.Call) and dotted(c.func).rsplit(".", 1)[-1] in ("escape", "quote") for c in ast.walk(v))

    def _check_call(self, call, qual, env, params):
        d = dotted(call.func)
        last = d.rsplit(".", 1)[-1]
        arg0 = call.args[0] if call.args else None
        lv0 = self._level_of(arg0, env, params) if arg0 is not None else 0
        built0 = arg0 is not None and (is_string_built(arg0) or (isinstance(arg0, ast.Name) and env.get(arg0.id, 0) >= 1))
        anylv = max([self._level_of(a, env, params) for a in call.args] + [0])

        # --- SQL injection
        if last in SQL_SINKS and isinstance(call.func, ast.Attribute) or d in ("text",):
            if arg0 is not None and not isinstance(arg0, ast.Constant) and (built0 or lv0 >= 2):
                if is_string_built(arg0) or lv0 >= 1:
                    fix = None
                    new = sql_parametrize(call) if is_string_built(arg0) else None
                    if new:
                        fix = self._seg_fix(call, new, "Parameterised the query; placeholders use `?` (sqlite). "
                                                        "Use `%s` for psycopg2/MySQL drivers.")
                    self._add("SQLI", call, qual, self._conf(max(lv0, 1)), self._tainted_desc(arg0, env, params),
                              d, fix=fix)
                    return
        # --- commands
        tl0 = self._taint_only(arg0, env, params)
        if d in ("os.system", "os.popen") and arg0 is not None and not isinstance(arg0, ast.Constant) and tl0:
            new = shell_to_list(call) if is_string_built(arg0) else None
            fix = self._seg_fix(call, new, "Replaced shell string with an argument list (needs `import subprocess`).") if new else None
            self._add("CMDI", call, qual, self._conf(tl0), self._tainted_desc(arg0, env, params), d, fix=fix)
            return
        if d in SUBPROC:
            sh = self._kw(call, "shell")
            shell_true = isinstance(sh, ast.Constant) and sh.value is True
            if shell_true and arg0 is not None and not isinstance(arg0, ast.Constant) and tl0:
                new = shell_to_list(call) if is_string_built(arg0) else None
                fix = None
                if new:
                    fix = self._seg_fix(call, new, "Replaced shell string with an argument list and shell=False.")
                self._add("CMDI", call, qual, self._conf(tl0), self._tainted_desc(arg0, env, params), d, fix=fix)
                return
            if shell_true:
                self._add("CMD_SHELL", call, qual, "high", "shell=True", d)
                return
            if arg0 is not None and lv0 >= 2 and isinstance(arg0, (ast.Name, ast.JoinedStr)):
                self._add("CMDI", call, qual, "medium", self._tainted_desc(arg0, env, params), d)
                return
        # --- eval / exec
        if d in ("eval", "exec", "compile") and arg0 is not None and not isinstance(arg0, ast.Constant):
            fix = None
            if d == "eval":
                fix = self._seg_fix(call.func, "ast.literal_eval", "Use ast.literal_eval (needs `import ast`); "
                                                                  "restricts input to Python literals.")
            self._add("EVAL", call, qual, self._conf(max(lv0, 1)) if lv0 else "low",
                      self._tainted_desc(arg0, env, params) if lv0 else "non-constant expression", d, fix=fix)
            return
        # --- deserialization
        if d in DESER:
            self._add("DESER", call, qual, self._conf(lv0) if lv0 else "medium", self._tainted_desc(arg0, env, params) if lv0 else "untrusted bytes",
                      d)
            return
        if d in ("yaml.load", "yaml.unsafe_load", "yaml.full_load"):
            loader = self._kw(call, "Loader")
            if loader is None or "Safe" not in dotted(loader):
                fix = self._seg_fix(call.func, "yaml.safe_load", "Use yaml.safe_load.") if d == "yaml.load" and loader is None else None
                self._add("YAML_LOAD", call, qual, "high", d, d, fix=fix)
                return
        # --- path traversal
        if d in FILE_SINKS and arg0 is not None and lv0 >= 2:
            self._add("PATH", call, qual, self._conf(lv0), self._tainted_desc(arg0, env, params), d)
            return
        # --- XSS / SSTI
        if last == "render_template_string" and arg0 is not None and not isinstance(arg0, ast.Constant) and (lv0 or built0):
            self._add("SSTI", call, qual, self._conf(max(lv0, 1)), self._tainted_desc(arg0, env, params), d)
            return
        if last in ("Markup", "mark_safe") and arg0 is not None and lv0 >= 2:
            self._add("XSS", call, qual, self._conf(lv0), self._tainted_desc(arg0, env, params), d)
            return
        if last in ("HttpResponse", "make_response", "Response") and arg0 is not None and lv0 >= 2 and is_string_built(arg0) \
                and not self._escaped(arg0):
            self._add("XSS", call, qual, self._conf(lv0), self._tainted_desc(arg0, env, params), d)
            return
        # --- SSRF, TLS
        if d in HTTP_SINKS:
            v = self._kw(call, "verify")
            if isinstance(v, ast.Constant) and v.value is False:
                fix = self._seg_fix(v, "True", "Re-enable certificate verification.")
                self._add("TLS_VERIFY", call, qual, "high", "verify=False", d, fix=fix)
            if arg0 is not None and lv0 >= 2:
                self._add("SSRF", call, qual, self._conf(lv0), self._tainted_desc(arg0, env, params), d)
                return
            if isinstance(v, ast.Constant) and v.value is False:
                return
        if d in ("ssl._create_unverified_context",) or (last == "verify_mode" and False):
            self._add("TLS_INSECURE_CTX", call, qual, "high", d, d)
        # --- crypto
        if d in ("hashlib.md5", "hashlib.sha1") or (d == "hashlib.new" and arg0 is not None and isinstance(arg0, ast.Constant)
                                                    and str(arg0.value).lower() in ("md5", "sha1")):
            ctx = self._line_text(call)
            conf = "high" if TOKEN_CONTEXT.search(ctx) else "medium"
            fix = self._seg_fix(call.func, "hashlib.sha256", "Use SHA-256 (or bcrypt/argon2 for passwords).") \
                if d in ("hashlib.md5", "hashlib.sha1") else None
            self._add("WEAK_HASH", call, qual, conf, d, d, severity="high" if conf == "high" else "", fix=fix)
            return
        if d in WEAK_RANDOM:
            ctx = qual + " " + self._line_text(call)
            m = TOKEN_CONTEXT.search(ctx)
            if m:
                self._add("WEAK_RANDOM", call, qual, "medium", m.group(1), d)
                return
        # --- misc misconfig
        if d in ("app.run", "socketio.run") or last == "run":
            dbg = self._kw(call, "debug")
            if isinstance(dbg, ast.Constant) and dbg.value is True:
                self._add("DEBUG_ON", call, qual, "high", "debug=True", d, fix=self._seg_fix(dbg, "False", "Disable debug."))
                return
        if d == "tempfile.mktemp":
            self._add("INSECURE_TEMP", call, qual, "high", d, d)
        if d in ("os.chmod", "os.fchmod") and len(call.args) >= 2 and isinstance(call.args[1], ast.Constant) \
                and isinstance(call.args[1].value, int) and call.args[1].value & 0o002:
            self._add("PERMS", call, qual, "high", oct(call.args[1].value), d)
        if d in ("jwt.decode",):
            opt = self._kw(call, "options")
            v = self._kw(call, "verify")
            if (isinstance(v, ast.Constant) and v.value is False) or (opt is not None and "False" in ast.unparse(opt)):
                self._add("JWT_NOVERIFY", call, qual, "high", d, d)
        if d in XML_SINKS and "defused" not in d:
            self._add("XXE", call, qual, "medium" if lv0 >= 2 else "low", d, d)
        if last in ("redirect",) and arg0 is not None and lv0 >= 2 and not isinstance(arg0, ast.Constant) \
                and not re.search(r"url_for", ast.unparse(arg0)):
            self._add("OPEN_REDIRECT", call, qual, self._conf(lv0), self._tainted_desc(arg0, env, params), d)
        if d in LOG_CALLS:
            for a in call.args:
                for nm in ast.walk(a):
                    if isinstance(nm, ast.Name) and re.search(r"(passw|secret|token|api_?key|credential)", nm.id, re.I):
                        self._add("LOG_SECRET", call, qual, "medium", nm.id, d)
                        return
        # --- quality-ish call checks
        if d == "print":
            self._add("Q_PRINT", call, qual, "high")

    def _line_text(self, node):
        ln = node.lineno
        return " ".join(self.lines[max(0, ln - 2):ln + 1]) if self.lines else ""

    # -- module-level assignment checks (secrets, debug flags, star-import)
    def _module_level(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    name = t.id if isinstance(t, ast.Name) else t.attr if isinstance(t, ast.Attribute) else \
                        (t.slice.value if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) else "")
                    if not isinstance(name, str) or not name:
                        continue
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        sv = value.value
                        if SECRET_NAME.search(name) and len(sv) >= 4 and not PLACEHOLDER.match(sv) and " " not in sv[:2]:
                            if not re.search(r"(url|path|file|name|type|header|prefix|field|label|env|id_?$)", name, re.I) or "key" in name.lower():
                                self._add("HARDCODED_SECRET", node, "", "high", name)
                    if name.upper() == "DEBUG" and isinstance(value, ast.Constant) and value.value is True:
                        self._add("DEBUG_ON", node, "", "medium", f"{name}=True",
                                  fix=self._seg_fix(value, "False", "Disable debug."))
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str) and isinstance(v, ast.Constant) \
                            and isinstance(v.value, str) and SECRET_NAME.search(k.value) and len(v.value) >= 6 \
                            and not PLACEHOLDER.match(v.value):
                        self._add("HARDCODED_SECRET", k, "", "medium", f'["{k.value}"]')
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) >= 16:
                for label, rx in SECRET_VALUE:
                    if rx.search(node.value):
                        self._add("GENERIC_SECRET", node, "", "high", label)
                        break
            if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
                self._add("Q_STAR_IMPORT", node, "", "high", node.module or "")

    # -- quality
    def _quality(self, scopes):
        for qual, fn in scopes:
            m = function_metrics(fn)
            m.update(name=qual, line=fn.lineno + self.off, file=self.file)
            self.func_metrics.append(m)
            if m["cyclomatic"] > 10:
                self._add("Q_COMPLEXITY", fn, qual, "high", str(m["cyclomatic"]),
                          severity="high" if m["cyclomatic"] > 20 else "", end=fn.lineno)
            if m["max_nesting"] > 4:
                self._add("Q_NESTING", fn, qual, "high", str(m["max_nesting"]), end=fn.lineno)
            if m["loc"] > 60:
                self._add("Q_LONG_FUNC", fn, qual, "high", str(m["loc"]), end=fn.lineno)
            if m["n_params"] > 6:
                self._add("Q_MANY_PARAMS", fn, qual, "high", str(m["n_params"]), end=fn.lineno)
            if not ast.get_docstring(fn) and m["loc"] >= 8 and not qual.split(".")[-1].startswith("_"):
                self._add("Q_NO_DOCSTRING", fn, qual, "high", end=fn.lineno)
            for d in fn.args.defaults + [x for x in fn.args.kw_defaults if x is not None]:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)) or (isinstance(d, ast.Call) and dotted(d.func) in ("list", "dict", "set")):
                    self._add("Q_MUTABLE_DEFAULT", d, qual, "high", ast.unparse(d))
            for n in self._own_walk(fn):
                if isinstance(n, ast.ExceptHandler):
                    body_pass = all(isinstance(b, (ast.Pass, ast.Continue)) or (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))
                                    for b in n.body)
                    if n.type is None or body_pass:
                        self._add("Q_BARE_EXCEPT", n, qual, "high", "bare except" if n.type is None else "pass")
                if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in n.ops) and \
                        any(isinstance(c, ast.Constant) and c.value is None for c in n.comparators):
                    new = ast.unparse(n).replace("!= None", "is not None").replace("== None", "is None")
                    self._add("Q_NONE_CMP", n, qual, "high", fix=self._seg_fix(n, new, "Use identity comparison."))
        # unused imports
        imported = {}
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    imported[(a.asname or a.name).split(".")[0]] = n
            elif isinstance(n, ast.ImportFrom):
                for a in n.names:
                    if a.name != "*":
                        imported[a.asname or a.name] = n
        used = {n.id for n in ast.walk(self.tree) if isinstance(n, ast.Name)} | \
               {dotted(n).split(".")[0] for n in ast.walk(self.tree) if isinstance(n, ast.Attribute)}
        if not getattr(self, "_wrapped", False) and self.off == 0 and not self.file.endswith("__init__.py"):
            for name, node in imported.items():
                if name not in used and name not in self.src.replace("import " + name, ""):
                    self._add("Q_UNUSED_IMPORT", node, "", "high", name)
        for i, line in enumerate(self.lines, 1):
            m = re.search(r"#\s*(TODO|FIXME|XXX|HACK)\b", line)
            if m:
                f = Finding("Q_TODO", self.file, i + self.off, i + self.off, "", line.strip()[:200], "high", m.group(1))
                self.findings.append(f)


# ---------------------------------------------------------------- generic (regex) analyzer
GENERIC_RULES = [
    ("JS_INNERHTML", (".js", ".jsx", ".ts", ".tsx", ".html", ".vue"), re.compile(r"(\.innerHTML\s*[+]?=|document\.write(ln)?\s*\(|dangerouslySetInnerHTML|v-html)"), "medium"),
    ("JS_EVAL", (".js", ".jsx", ".ts", ".tsx"), re.compile(r"\b(eval\s*\(|new\s+Function\s*\(|setTimeout\s*\(\s*[\"'`])"), "medium"),
    ("JS_EXEC", (".js", ".ts"), re.compile(r"child_process[^\n]*\bexec(Sync)?\s*\(|\bexec(Sync)?\s*\([^)]*(\+|\$\{)"), "medium"),
    ("PHP_SQLI", (".php",), re.compile(r"(mysql_query|mysqli_query|->query)\s*\([^)]*\$_(GET|POST|REQUEST|COOKIE)|\"\s*(SELECT|INSERT|UPDATE|DELETE)[^\"]*\"\s*\.\s*\$_(GET|POST|REQUEST)", re.I), "high"),
    ("PHP_INCLUDE", (".php",), re.compile(r"\b(include|require)(_once)?\s*\(?[^;]*\$_(GET|POST|REQUEST)"), "high"),
    ("JAVA_SQLI", (".java", ".kt"), re.compile(r"(executeQuery|executeUpdate|createStatement\(\)\.execute)\s*\(\s*\"[^\"]*\"\s*\+", re.I), "high"),
    ("EVAL", (".php",), re.compile(r"\beval\s*\(\s*\$"), "high"),
    ("HARDCODED_SECRET", (".js", ".ts", ".php", ".java", ".go", ".rb", ".cs", ".env", ".yml", ".yaml", ".json", ".ini", ".cfg", ".properties", ".toml", ".sh"),
     re.compile(r"(?i)[\"']?(password|passwd|secret|api[_-]?key|token|client_secret|private_key)[\"']?\s*[:=]\s*[\"'][^\"'\s]{6,}[\"']"), "medium"),
]


def analyze_generic(source: str, filename: str, line_offset: int = 0) -> list[Finding]:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    out = []
    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(("//", "#", "*", "/*")) and "password" not in stripped.lower():
            continue
        for rid, exts, rx, conf in GENERIC_RULES:
            if ext in exts and rx.search(line):
                if rid == "HARDCODED_SECRET" and PLACEHOLDER.match(re.split(r"[:=]\s*", stripped, 1)[-1].strip("\"',; ")):
                    continue
                m = re.search(r"(?i)(password|passwd|secret|api[_-]?key|token|client_secret|private_key)", line)
                out.append(Finding(rid, filename, i + line_offset, i + line_offset, "", stripped[:200], conf,
                                   m.group(1) if (rid == "HARDCODED_SECRET" and m) else stripped[:40],
                                   detector="regex"))
        for label, rx in SECRET_VALUE:
            if rx.search(line):
                out.append(Finding("GENERIC_SECRET", filename, i + line_offset, i + line_offset, "", stripped[:200],
                                   "high", label, detector="regex"))
    return out


def analyze_source(source: str, filename: str, line_offset: int = 0) -> tuple[list[Finding], list[dict]]:
    """Analyze one file (or hunk). Returns (findings, per-function metrics)."""
    if filename.endswith((".py", ".pyw")):
        a = PyAnalyzer(source, filename, line_offset).scan()
        extra = []
        if a.tree is None:  # unparsable -> at least secrets/regex
            extra = analyze_generic(source, filename, line_offset)
        return a.findings + extra, a.func_metrics
    return analyze_generic(source, filename, line_offset), []
