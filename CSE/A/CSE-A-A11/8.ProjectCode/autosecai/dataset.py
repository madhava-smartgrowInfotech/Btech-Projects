"""Synthetic labelled corpus of Python functions (vulnerable vs. safe) for the metric model.

The base paper trains on 21,759 C functions from 10 open-source projects (275 vulnerable).  Those
datasets are C/C++ and are not bundled, so this module *generates* a realistic imbalanced corpus
of Python functions instead: random filler logic of varying complexity + injected vulnerable
patterns (8 types, mirroring the paper's vulnerability-type grouping) + look-alike safe patterns
(hard negatives) + 1 % label noise.  Metrics are then computed from the real generated source with
`metrics.function_metrics`, exactly like they would be for a PR.

Use `build_dataset()` -> pandas.DataFrame with the 14 metric columns, `vulnerable`, `vuln_type`.
"""
from __future__ import annotations

import ast
import random
import textwrap

import pandas as pd

from .metrics import FEATURES, function_metrics, iter_functions

VULN_TYPES = ["sql_injection", "command_injection", "code_execution", "deserialization", "path_traversal",
              "xss", "hardcoded_secret", "weak_crypto"]

_NAMES = ["user", "item", "order", "value", "record", "payload", "data", "name", "count", "limit", "path", "text",
          "key", "row", "config", "query", "host", "token", "idx", "result"]


def _filler(rng: random.Random, params: list[str], indent="    ") -> list[str]:
    """Random benign logic; complexity is drawn from a heavy-tailed distribution."""
    lines = []
    n_blocks = rng.choice([0, 0, 1, 1, 2, 3, 4, 6])
    for _ in range(n_blocks):
        kind = rng.choice(["if", "loop", "nested", "try", "calc", "listcomp", "index"])
        p = rng.choice(params) if params else "x"
        v = rng.choice(_NAMES) + str(rng.randint(0, 9))
        if kind == "if":
            cond = f"{p} is not None" if rng.random() < .5 else f"len(str({p})) > {rng.randint(1, 9)}"
            if rng.random() < .3:
                cond += f" and {rng.choice(params or ['x'])} != {rng.randint(0, 5)}"
            lines += [f"if {cond}:", f"    {v} = str({p}).strip()", "else:", f"    {v} = ''"]
        elif kind == "loop":
            lines += [f"for i in range({rng.randint(2, 9)}):", f"    {v} = i * {rng.randint(1, 4)}"]
        elif kind == "nested":
            depth = rng.randint(2, 5)
            for d in range(depth):
                lines.append("    " * d + (f"if {p}:" if d % 2 == 0 else f"for j{d} in range(3):"))
            lines.append("    " * depth + f"{v} = {rng.randint(0, 99)}")
        elif kind == "try":
            lines += ["try:", f"    {v} = int({p})", "except ValueError:", f"    {v} = 0"]
        elif kind == "calc":
            lines += [f"{v} = ({p} or 0) + {rng.randint(1, 50)} * {rng.randint(1, 9)}"]
        elif kind == "listcomp":
            lines += [f"{v} = [c for c in str({p}) if c.isalnum()]"]
        elif kind == "index":
            lines += [f"{v} = str({p})[{rng.randint(0, 3)} + 1:]", f"w{rng.randint(0, 9)} = {v}[len({v}) - 1:]"]
    return [indent + l for l in lines]


def _vuln_snippet(kind: str, rng: random.Random, p: str, use_source: bool) -> list[str]:
    src = f"request.args.get('{p}')" if use_source else p
    v = f"u{rng.randint(0, 9)}"
    pre = [f"{v} = {src}"] if use_source else []
    if kind == "sql_injection":
        style = rng.choice(["f", "concat", "percent"])
        q = {"f": f"f\"SELECT * FROM t WHERE c = '{{{v}}}'\"",
             "concat": f"\"SELECT * FROM t WHERE c = '\" + {v} + \"'\"",
             "percent": f"\"SELECT * FROM t WHERE c = '%s'\" % {v}"}[style]
        return pre + [f"cur.execute({q})", "rows = cur.fetchall()"]
    if kind == "command_injection":
        return pre + rng.choice([[f"os.system(f\"ping -c 1 {{{v}}}\")"],
                                 [f"subprocess.run(\"ls \" + {v}, shell=True)"],
                                 [f"out = os.popen(f\"cat {{{v}}}\").read()"]])
    if kind == "code_execution":
        return pre + rng.choice([[f"result = eval({v})"], [f"exec({v})"], [f"result = eval(f\"{{{v}}} + 1\")"]])
    if kind == "deserialization":
        return pre + rng.choice([[f"obj = pickle.loads({v})"], [f"cfg = yaml.load({v})"], [f"obj = marshal.loads({v})"]])
    if kind == "path_traversal":
        return pre + rng.choice([[f"fh = open(os.path.join('/srv/files', {v}))", "body = fh.read()"],
                                 [f"return send_file({v})"], [f"os.remove('/tmp/' + {v})"]])
    if kind == "xss":
        return pre + [f"html = f\"<div class='msg'>{{{v}}}</div>\"", "return html"]
    if kind == "hardcoded_secret":
        return [f"password = '{rng.choice(['hunter2', 'Adm1n!23', 'letmein99'])}'", "conn = connect(user='admin', password=password)"]
    if kind == "weak_crypto":
        return pre + [f"token = hashlib.md5({(v if use_source else p)}.encode()).hexdigest()",
                      "session_key = random.randint(0, 999999)"]
    return []


def _safe_snippet(rng: random.Random, p: str) -> list[str]:
    """Look-alike but safe operations (hard negatives)."""
    return rng.choice([
        [f"cur.execute('SELECT * FROM t WHERE c = ?', ({p},))", "rows = cur.fetchall()"],
        [f"subprocess.run(['ping', '-c', '1', str({p})], check=True)"],
        [f"value = ast.literal_eval(str({p}))"],
        [f"obj = json.loads({p})"],
        [f"cfg = yaml.safe_load({p})"],
        [f"name = os.path.basename(str({p}))", "fh = open(os.path.join('/srv/files', name))"],
        [f"return f\"<div>{{html.escape(str({p}))}}</div>\""],
        [f"digest = hashlib.sha256(str({p}).encode()).hexdigest()"],
        [f"token = secrets.token_hex(16)"],
        [f"password = os.environ.get('DB_PASSWORD')"],
        ["with open('/etc/app.conf') as fh:", "    body = fh.read()"],
        [f"logger.info('handled %s', {p})"],
        [],
    ])


def _make_function(rng: random.Random, vuln: str | None, hard_negative: bool) -> str:
    n_params = rng.choice([1, 1, 2, 2, 3, 4, 5, 6, 8])
    params = rng.sample(_NAMES, n_params)
    body = _filler(rng, params)
    use_source = rng.random() < 0.5
    if vuln:
        snip = _vuln_snippet(vuln, rng, params[0], use_source)
    elif hard_negative:
        snip = _safe_snippet(rng, params[0])
    else:
        snip = rng.choice([[], [], [f"total = sum(len(str({params[0]})) for _ in range(3))"],
                           [f"logger.debug('run %s', {params[0]})"], [f"res = {params[0]}"]])
    pos = rng.randint(0, len(body))
    # keep block structure intact: insert only at top-level boundaries
    while pos < len(body) and pos > 0 and body[pos].startswith("        "):
        pos += 1
    if pos < len(body) and body[pos].startswith(("    else", "    except")):
        pos = len(body)
    body = body[:pos] + ["    " + s for s in snip] + body[pos:]
    if not body:
        body = ["    pass"]
    if not any(l.strip().startswith("return") for l in body) and rng.random() < .6:
        body.append("    return None")
    return f"def fn_{rng.randint(0, 10**6)}({', '.join(params)}):\n" + "\n".join(body) + "\n"


def build_dataset(n: int = 6000, vuln_rate: float = 0.075, seed: int = 7, label_noise: float = 0.01) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        vuln = rng.choice(VULN_TYPES) if rng.random() < vuln_rate else None
        src = _make_function(rng, vuln, hard_negative=rng.random() < 0.55)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        fn = next(f for _, f in iter_functions(tree))
        m = function_metrics(fn)
        label = 1 if vuln else 0
        if rng.random() < label_noise:      # annotation noise, as in real vulnerability datasets
            label = 1 - label
        m.update(vulnerable=label, vuln_type=vuln if (vuln and label) else ("noise" if label else "none"), source=src)
        rows.append(m)
    df = pd.DataFrame(rows)
    # noisy positives with no real type get a random type so the type-classifier sees plausible labels
    noise = df["vuln_type"] == "noise"
    df.loc[noise, "vuln_type"] = [rng.choice(VULN_TYPES) for _ in range(int(noise.sum()))]
    return df[FEATURES + ["vulnerable", "vuln_type", "source"]]


if __name__ == "__main__":
    d = build_dataset()
    print(d.vulnerable.value_counts(), d.vuln_type.value_counts(), sep="\n")
