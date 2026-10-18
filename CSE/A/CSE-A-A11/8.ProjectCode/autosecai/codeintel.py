"""Codebase intelligence: index a repository and answer natural-language questions about it.

Retrieval = TF-IDF (lexical) + concept lexicon (auth / routing / ui / database / config / tests / security)
+ graph proximity (personalised PageRank over the import + call graph built from the AST).
"""
from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from . import llm
from .metrics import dotted, function_metrics

CONCEPTS = {
    "authentication": dict(
        label="Authentication & sessions",
        words="login logout signin signup register password passwd credential token jwt session oauth auth authenticate "
              "authorization permission role bcrypt pbkdf2 hash salt csrf cookie sso 2fa otp",
        ask="auth authentication login logout sign password credential token jwt session oauth permission role user access security who",
        path="auth login session user account permission"),
    "routing": dict(
        label="Routing & API endpoints",
        words="route router routes blueprint endpoint url urls urlpatterns path get post put delete patch api view controller handler",
        ask="route routes routing router endpoint endpoints url urls api controller handler request http rest view",
        path="route routes urls views api controller handler"),
    "ui": dict(
        label="UI / front-end",
        words="template html render component button form page layout css style jsx tsx react vue widget streamlit sidebar "
              "innerhtml document window element dom click",
        ask="ui frontend front-end page template html view component button form screen layout css style display render interface",
        path="templates static components pages views public assets ui app.js"),
    "database": dict(
        label="Database & models",
        words="sql sqlite query execute cursor connection database db model orm table select insert update delete commit "
              "migrate schema session",
        ask="database db sql query queries model models orm table schema storage store persistence data sqlite postgres mysql",
        path="db model models database schema migrations repository"),
    "config": dict(
        label="Configuration",
        words="config configuration settings environ env environment secret key debug constant option flag",
        ask="config configuration settings environment env option flag constant setup",
        path="config settings conf env constants"),
    "testing": dict(
        label="Tests",
        words="test tests pytest assert unittest mock fixture",
        ask="test tests testing pytest unittest coverage",
        path="test tests spec"),
    "security": dict(
        label="Security controls",
        words="escape sanitize validate validation encrypt decrypt hmac sign verify csrf xss injection secure safe allowlist "
              "whitelist permission",
        ask="security secure validation sanitize escape encrypt protect vulnerability xss injection",
        path="security validators sanitize"),
    "entry": dict(
        label="Entry points",
        words="main app run serve start launch init create_app __main__ bootstrap",
        ask="entry start main run launch begin bootstrap startup boot",
        path="main app run manage wsgi asgi index"),
}
CONCEPT_RX = {k: re.compile(r"\b(" + "|".join(v["words"].split()) + r")\b", re.I) for k, v in CONCEPTS.items()}
STOP = set("the a an of to in is are where how what which who does do find show me for and or on with from this that "
           "code file files function functions class used use handled handles handle implemented implementation located "
           "can i we you it its be by at as when why".split())
ROUTE_DEC = re.compile(r"(route|get|post|put|delete|patch|websocket|api_view|path)$")


def split_ident(s: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    return re.sub(r"[_\W]+", " ", s).lower()


class RepoIndex:
    def __init__(self, files: dict[str, str], name: str = "repository"):
        self.name = name
        self.files = {p: t for p, t in files.items() if t is not None}
        self.chunks: list[dict] = []
        self.graph = nx.DiGraph()
        self.routes: list[dict] = []
        self.entry_points: list[str] = []
        self.hotspots: list[dict] = []
        self.imports: dict[str, set] = defaultdict(set)
        self._build()

    # ------------------------------------------------------------- build
    def _module_map(self):
        m = {}
        for p in self.files:
            if p.endswith(".py"):
                mod = p[:-3].replace("/", ".")
                m[mod] = p
                if mod.endswith(".__init__"):
                    m[mod[: -len(".__init__")]] = p
        return m

    def _add_chunk(self, **kw):
        kw["id"] = len(self.chunks)
        self.chunks.append(kw)
        self.graph.add_node(f"c{kw['id']}", kind="chunk")
        self.graph.add_edge(kw["file"], f"c{kw['id']}", kind="defines")
        return kw["id"]

    def _build(self):
        modmap = self._module_map()
        func_by_name: dict[str, list[int]] = defaultdict(list)
        calls_of: dict[int, set] = {}
        for path, text in sorted(self.files.items()):
            self.graph.add_node(path, kind="file")
            ext = Path(path).suffix.lower()
            if ext == ".py":
                self._index_python(path, text, modmap, func_by_name, calls_of)
            elif ext in (".js", ".jsx", ".ts", ".tsx", ".vue"):
                self._index_js(path, text)
            else:
                self._index_window(path, text)
            if re.search(r"__name__\s*==\s*['\"]__main__['\"]|\.run\(|app\.listen\(", text):
                self.entry_points.append(path)
        # resolve blueprint / router prefixes: app.register_blueprint(api_bp, url_prefix="/api")
        prefixes = {}
        for text in self.files.values():
            for m in re.finditer(r"register_blueprint\(\s*(\w+)[^)]*url_prefix\s*=\s*['\"]([^'\"]*)['\"]", text):
                prefixes[m.group(1)] = m.group(2)
            for m in re.finditer(r"include_router\(\s*(\w+)[^)]*prefix\s*=\s*['\"]([^'\"]*)['\"]", text):
                prefixes[m.group(1)] = m.group(2)
        for r in self.routes:
            pre = prefixes.get(r.get("obj", ""), "")
            if pre and not r["path"].startswith(pre):
                r["path"] = pre.rstrip("/") + "/" + r["path"].lstrip("/") if r["path"] != "/" else pre
        # call edges
        for cid, names in calls_of.items():
            src = self.chunks[cid]
            for n in names:
                targets = func_by_name.get(n, [])
                same = [t for t in targets if self.chunks[t]["file"] == src["file"]]
                for t in (same or targets)[:3]:
                    if t != cid:
                        self.graph.add_edge(f"c{cid}", f"c{t}", kind="calls")
        # vectorise
        docs = [c["doc_text"] for c in self.chunks] or ["empty"]
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1, stop_words="english")
        try:
            self.matrix = self.vec.fit_transform(docs)
        except ValueError:
            self.vec = TfidfVectorizer()
            self.matrix = self.vec.fit_transform(["empty"])
        self.concept_scores = np.array([[self._affinity(c, k) for k in CONCEPTS] for c in self.chunks]) \
            if self.chunks else np.zeros((0, len(CONCEPTS)))
        self.hotspots = sorted([c for c in self.chunks if c["kind"] == "function"],
                               key=lambda c: -c["metrics"]["cyclomatic"])[:8]

    def _index_python(self, path, text, modmap, func_by_name, calls_of):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return self._index_window(path, text)
        lines = text.splitlines()
        pathtok = split_ident(path)
        # imports -> file edges
        for n in ast.walk(tree):
            mods = []
            if isinstance(n, ast.Import):
                mods = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module:
                mods = [n.module] + [f"{n.module}.{a.name}" for a in n.names]
            for m in mods:
                tgt = modmap.get(m)
                if tgt and tgt != path:
                    self.graph.add_edge(path, tgt, kind="imports")
                    self.imports[path].add(tgt)
        mod_doc = ast.get_docstring(tree) or ""
        self._add_chunk(kind="file", file=path, name=path, line=1, end=len(lines), doc=mod_doc, code=text[:1500],
                        decorators=[], metrics=None,
                        doc_text=f"{pathtok} {pathtok} {mod_doc} " + " ".join(split_ident(n.id) for n in ast.walk(tree)
                                                                                 if isinstance(n, ast.Name))[:1500])
        for qual, fn in _iter_defs(tree):
            is_fn = isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
            doc = ast.get_docstring(fn) or ""
            decs = [ast.unparse(d) for d in fn.decorator_list]
            seg = "\n".join(lines[fn.lineno - 1: min(fn.end_lineno, fn.lineno + 40)])
            idents = " ".join(split_ident(n.id) for n in ast.walk(fn) if isinstance(n, ast.Name))
            attrs = " ".join(split_ident(n.attr) for n in ast.walk(fn) if isinstance(n, ast.Attribute))
            strs = " ".join(str(n.value)[:60] for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str))
            name_tok = split_ident(qual)
            doc_text = f"{name_tok} {name_tok} {name_tok} {doc} {doc} {' '.join(split_ident(d) for d in decs)} " \
                       f"{pathtok} {idents} {attrs} {strs}"[:3500]
            met = function_metrics(fn) if is_fn else None
            cid = self._add_chunk(kind="function" if is_fn else "class", file=path, name=qual, line=fn.lineno,
                                  end=fn.end_lineno, doc=doc, code=seg, decorators=decs, metrics=met, doc_text=doc_text)
            self.graph.add_edge(path, f"c{cid}", kind="defines")
            if is_fn:
                func_by_name[qual.split(".")[-1]].append(cid)
                calls = {dotted(n.func).split(".")[-1] for n in ast.walk(fn) if isinstance(n, ast.Call)}
                calls_of[cid] = {c for c in calls if c}
                for d in fn.decorator_list:
                    dn = dotted(d)
                    if ROUTE_DEC.search(dn.split(".")[-1]) and isinstance(d, ast.Call):
                        pth = ast.unparse(d.args[0]).strip("'\"") if d.args else ""
                        methods = next((ast.unparse(k.value) for k in d.keywords if k.arg == "methods"), "")
                        verb = dn.split(".")[-1].upper() if dn.split(".")[-1] in ("get", "post", "put", "delete", "patch") else \
                            (methods.strip("[]'\" ").replace("'", "") or "GET")
                        self.routes.append(dict(method=verb, path=pth, handler=qual, file=path, line=fn.lineno,
                                                obj=dn.rsplit(".", 1)[0] if "." in dn else ""))

    def _index_js(self, path, text):
        lines = text.splitlines()
        pat = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)|^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>|^\s*class\s+(\w+)")
        starts = [(i, next(g for g in m.groups() if g)) for i, l in enumerate(lines) if (m := pat.match(l))]
        pathtok = split_ident(path)
        if not starts:
            return self._index_window(path, text)
        for k, (i, name) in enumerate(starts):
            j = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
            seg = "\n".join(lines[i:j][:50])
            cid = self._add_chunk(kind="function", file=path, name=name, line=i + 1, end=j, doc="", code=seg,
                                  decorators=[], metrics=dict(cyclomatic=1 + len(re.findall(r"\b(if|for|while|case|&&|\|\|)\b", seg))),
                                  doc_text=f"{split_ident(name)} {split_ident(name)} {pathtok} {split_ident(seg)}"[:3000])
            self.graph.add_edge(path, f"c{cid}", kind="defines")
        for i, l in enumerate(lines):
            m = re.search(r"(?:app|router|server)\.(get|post|put|delete|patch)\(\s*['\"`]([^'\"`]+)", l)
            if m:
                self.routes.append(dict(method=m.group(1).upper(), path=m.group(2), handler="(inline)", file=path, line=i + 1))

    def _index_window(self, path, text, size=60):
        lines = text.splitlines()
        pathtok = split_ident(path)
        for i in range(0, max(len(lines), 1), size):
            seg = "\n".join(lines[i:i + size])
            cid = self._add_chunk(kind="file", file=path, name=path if i == 0 else f"{path}#L{i + 1}", line=i + 1,
                                  end=min(i + size, len(lines)), doc="", code=seg[:1500], decorators=[], metrics=None,
                                  doc_text=f"{pathtok} {pathtok} {split_ident(seg)}"[:3000])
            self.graph.add_edge(path, f"c{cid}", kind="defines")

    # ------------------------------------------------------------- retrieval
    def _affinity(self, chunk, concept) -> float:
        txt = chunk["doc_text"] + " " + chunk["file"]
        hits = len(CONCEPT_RX[concept].findall(txt))
        path_hit = any(w in chunk["file"].lower() for w in CONCEPTS[concept]["path"].split())
        aff = min(hits / 6.0, 1.0) + (0.6 if path_hit else 0)
        if concept == "routing" and any(ROUTE_DEC.search(d.split("(")[0].split(".")[-1]) for d in chunk["decorators"]):
            aff += 1.0
        if concept == "ui" and Path(chunk["file"]).suffix in (".html", ".jsx", ".tsx", ".vue", ".css", ".js"):
            aff += 0.8
        if concept == "testing" and ("test" in chunk["file"].lower()):
            aff += 1.0
        if concept == "entry" and chunk["kind"] == "file" and chunk["file"] in getattr(self, "entry_points", []):
            aff += 0.8
        return min(aff, 2.0)

    def detect_intent(self, question: str) -> list[str]:
        q = question.lower()
        toks = set(re.findall(r"[a-z0-9\-]+", q))
        scored = []
        for k, v in CONCEPTS.items():
            s = len(toks & set(v["ask"].split()))
            if s:
                scored.append((s, k))
        scored.sort(reverse=True)
        return [k for _, k in scored[:2]]

    def ask(self, question: str, k: int = 6, use_llm=False, api_key=None) -> dict:
        if not self.chunks:
            return dict(answer="The repository index is empty.", hits=[], intents=[])
        intents = self.detect_intent(question)
        toks = [t for t in re.findall(r"[A-Za-z0-9_]+", question) if t.lower() not in STOP]
        expanded = " ".join(split_ident(t) for t in toks)
        qv = self.vec.transform([expanded or question])
        sim = (self.matrix @ qv.T).toarray().ravel()
        score = sim.copy()
        if intents:
            cols = [list(CONCEPTS).index(i) for i in intents]
            score += 0.30 * self.concept_scores[:, cols].max(axis=1) / 2.0
        # exact identifier / path mentions
        for t in toks:
            tl = t.lower()
            for i, c in enumerate(self.chunks):
                if tl == c["name"].split(".")[-1].lower():
                    score[i] += 0.5
                elif len(tl) > 3 and tl in c["file"].lower():
                    score[i] += 0.1
        # prefer function chunks over whole-file chunks when both present
        for i, c in enumerate(self.chunks):
            if c["kind"] == "function":
                score[i] *= 1.15
            elif c["kind"] == "class":
                score[i] *= 1.05
        top = list(np.argsort(-score)[: max(k * 2, 8)])
        # graph expansion: personalised PageRank from the strongest seeds
        seeds = {f"c{i}": float(score[i]) for i in top[:5] if score[i] > 0}
        graph_boost = {}
        if seeds and self.graph.number_of_nodes() > 1:
            try:
                pr = nx.pagerank(self.graph.to_undirected(as_view=True), personalization=seeds, alpha=0.6, max_iter=60)
                mx = max(pr.values()) or 1
                for n, v in pr.items():
                    if n.startswith("c"):
                        graph_boost[int(n[1:])] = v / mx
            except Exception:
                pass
        for i, b in graph_boost.items():
            score[i] += 0.08 * b
        order = [int(i) for i in np.argsort(-score) if score[i] > 0.02][: k]
        hits = []
        for i in order:
            c = self.chunks[i]
            why = []
            if sim[i] > 0.05:
                why.append(f"text match {sim[i]:.2f}")
            for cn in intents:
                a = self.concept_scores[i, list(CONCEPTS).index(cn)]
                if a >= 0.6:
                    why.append(f"{CONCEPTS[cn]['label'].lower()} signal")
            if any(ROUTE_DEC.search(d.split("(")[0].split(".")[-1]) for d in c["decorators"]):
                why.append("route decorator " + c["decorators"][0])
            callers = [self.chunks[int(p[1:])]["name"] for p in self.graph.predecessors(f"c{i}")
                       if p.startswith("c") and self.graph.edges[p, f"c{i}"].get("kind") == "calls"][:3]
            callees = [self.chunks[int(s[1:])]["name"] for s in self.graph.successors(f"c{i}")
                       if s.startswith("c") and self.graph.edges[f"c{i}", s].get("kind") == "calls"][:3]
            if callers:
                why.append("called by " + ", ".join(callers))
            if callees:
                why.append("calls " + ", ".join(callees))
            hits.append(dict(file=c["file"], name=c["name"], kind=c["kind"], line=c["line"], end=c["end"],
                             score=round(float(score[i]), 3), doc=c["doc"].split("\n")[0][:160], why=why,
                             code=c["code"][:900], decorators=c["decorators"], callers=callers, callees=callees))
        answer = self._compose(question, intents, hits)
        if use_llm and llm.available(api_key) and hits:
            ctx = "\n\n".join(f"### {h['file']}:{h['line']} {h['name']}\n{h['code'][:700]}" for h in hits[:5])
            txt = llm.ask(f"Repository question: {question}\n\nRetrieved code:\n{ctx}\n\nAnswer concisely for a new team member, "
                          f"citing file paths and function names from the retrieved code only.",
                          system="You are a codebase onboarding assistant.", key=api_key, max_tokens=600)
            if txt:
                answer = txt
        return dict(answer=answer, hits=hits, intents=intents)

    def _compose(self, question, intents, hits) -> str:
        if not hits:
            return "I could not find anything relevant. Try naming a feature, file or function (e.g. *login*, *orders API*)."
        lead = ""
        if intents:
            lead = f"This looks like a question about **{' / '.join(CONCEPTS[i]['label'] for i in intents)}**. "
        by_file = defaultdict(list)
        for h in hits:
            by_file[h["file"]].append(h)
        parts = [lead + f"The most relevant location{'s are' if len(by_file) > 1 else ' is'}:"]
        for f, hs in list(by_file.items())[:4]:
            items = "; ".join((("module overview" if h["kind"] == "file" else f"`{h['name']}` (line {h['line']})")
                               + (f" - {h['doc']}" if h["doc"] else "")) for h in hs[:3])
            parts.append(f"- **`{f}`** -> {items}")
        top = hits[0]
        if top["callees"] or top["callers"]:
            flow = []
            if top["callers"]:
                flow.append("called by " + ", ".join(f"`{c}`" for c in top["callers"]))
            if top["callees"]:
                flow.append("and calls " + ", ".join(f"`{c}`" for c in top["callees"]))
            parts.append(f"\n`{top['name']}` is {' '.join(flow)}.")
        return "\n".join(parts)

    # ------------------------------------------------------------- overview
    def overview(self) -> dict:
        lang = Counter()
        loc = 0
        for p, t in self.files.items():
            lang[Path(p).suffix.lower() or "other"] += 1
            loc += len(t.splitlines())
        fn = [c for c in self.chunks if c["kind"] == "function"]
        cls = [c for c in self.chunks if c["kind"] == "class"]
        by_concept = {}
        for k in ("authentication", "routing", "ui", "database", "config", "testing"):
            ci = list(CONCEPTS).index(k)
            agg = defaultdict(float)
            for i, c in enumerate(self.chunks):
                agg[c["file"]] += self.concept_scores[i, ci]
            by_concept[k] = [f for f, v in sorted(agg.items(), key=lambda x: -x[1]) if v >= 0.9][:5]
        return dict(files=len(self.files), loc=loc, functions=len(fn), classes=len(cls), languages=dict(lang),
                    entry_points=self.entry_points[:6], routes=self.routes, hotspots=[
                        dict(name=c["name"], file=c["file"], line=c["line"], cyclomatic=c["metrics"]["cyclomatic"]) for c in self.hotspots],
                    by_concept=by_concept, import_edges=sum(1 for _, _, d in self.graph.edges(data=True) if d.get("kind") == "imports"))

    def onboarding_guide(self) -> str:
        o = self.overview()
        L = [f"### Onboarding guide for `{self.name}`",
             f"{o['files']} files, ~{o['loc']:,} lines, {o['functions']} functions, {o['classes']} classes."]
        if o["entry_points"]:
            L.append("**Start here:** " + ", ".join(f"`{e}`" for e in o["entry_points"]))
        for k, label in (("authentication", "Authentication"), ("routing", "Routes / API"), ("ui", "UI"),
                         ("database", "Database"), ("config", "Configuration")):
            if o["by_concept"].get(k):
                L.append(f"**{label}:** " + ", ".join(f"`{f}`" for f in o["by_concept"][k][:4]))
        if o["routes"]:
            L.append("**Endpoints:** " + ", ".join(f"`{r['method']} {r['path']}`" for r in o["routes"][:8]))
        if o["hotspots"]:
            L.append("**Most complex functions (read carefully):** " + ", ".join(
                f"`{h['name']}` (cc={h['cyclomatic']})" for h in o["hotspots"][:3]))
        return "\n\n".join(L)

    def file_graph(self):
        """Nodes/edges for visualisation: files + import edges."""
        nodes = [n for n, d in self.graph.nodes(data=True) if d.get("kind") == "file"]
        edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d.get("kind") == "imports"]
        return nodes, edges


def _iter_defs(tree):
    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield f"{prefix}{ch.name}", ch
                yield from walk(ch, f"{prefix}{ch.name}.")
            elif isinstance(ch, ast.ClassDef):
                yield f"{prefix}{ch.name}", ch
                yield from walk(ch, f"{prefix}{ch.name}.")
    yield from walk(tree, "")
