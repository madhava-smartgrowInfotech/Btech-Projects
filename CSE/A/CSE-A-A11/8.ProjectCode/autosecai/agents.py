"""Multi-agent pull-request review pipeline.

Agents (each appends a trace entry, so the UI can show what every agent did):
  1. Ingestion Agent        - parses the PR, identifies changed files/lines and languages
  2. Static Analysis Agent  - AST + taint rules (security) and quality checks on changed code
  3. ML Risk Agent          - base-paper metric model scores each changed function (+ vulnerability type)
  4. Security Reasoner      - correlates evidence, explains the flaw in context (source -> sink), impact, CWE/OWASP
  5. Remediation Agent      - proposes safe fixes, generates patches and *verifies* them by re-scanning
  6. Quality Reviewer       - summarises maintainability findings
  7. Judge Agent            - de-duplicates, scores risk, issues a verdict and the PR comment
"""
from __future__ import annotations

import ast
import math
import re
import time
import uuid
from collections import Counter
from datetime import datetime

from . import llm
from .diffutil import ChangedFile, apply_fixes, make_patch
from .knowledge import CONF_WEIGHT, SEVERITY_ORDER, SEVERITY_WEIGHT, rule as kb
from .metrics import FEATURE_LABEL
from .rules import Finding, analyze_source

_FILL = re.compile(r"\{(func|sink|evidence|line)\}")


def _fill(text: str, f: Finding) -> str:
    vals = {"func": f.function or "this module", "sink": f.sink or "the call", "evidence": f.evidence or "the value",
            "line": str(f.line)}
    return _FILL.sub(lambda m: vals[m.group(1)], text)


class Trace:
    def __init__(self):
        self.items = []

    def run(self, agent: str, role: str, fn):
        t0 = time.time()
        summary, details = fn()
        self.items.append(dict(agent=agent, role=role, seconds=round(time.time() - t0, 3), summary=summary,
                               details=details))


def _padded(snippet_lines: list[str], offset: int) -> str:
    return "\n" * offset + "\n".join(snippet_lines)


def review_changes(changed: list[ChangedFile], title: str = "Pull request", source_label: str = "",
                   use_llm: bool = False, api_key: str | None = None, ml: bool = True,
                   min_severity: str = "info", progress=None) -> dict:
    trace = Trace()
    findings: list[Finding] = []
    func_rows: list[dict] = []
    patch_src: dict[str, str] = {}          # path -> text (padded for hunks) that findings' fixes refer to
    full_mode: dict[str, bool] = {}
    analysed: dict[str, list[tuple[str, int]]] = {}

    def tick(msg):
        if progress:
            progress(msg)

    # ---- 1. ingestion
    def ingest():
        langs = Counter(cf.language for cf in changed)
        add = sum(cf.n_added for cf in changed)
        rem = sum(cf.n_removed for cf in changed)
        return (f"{len(changed)} file(s), +{add}/-{rem} lines, languages: {', '.join(f'{k} ({v})' for k, v in langs.items()) or 'none'}",
                [f"{cf.path} [{cf.status}] +{cf.n_added}/-{cf.n_removed}" for cf in changed])
    tick("Ingestion Agent: parsing pull request")
    trace.run("Ingestion Agent", "Extracts changed files, hunks and line ranges", ingest)

    # ---- 2. static analysis
    def static():
        det = []
        for cf in changed:
            if cf.new_source is not None:
                fs, fm = analyze_source(cf.new_source, cf.path)
                analysed[cf.path] = [(cf.new_source, 0)]
                patch_src[cf.path] = cf.new_source
                full_mode[cf.path] = True
                for f in fs:
                    f.extra["in_diff"] = f.line in cf.added or any(l in cf.added for l in range(f.line, f.end_line + 1))
                    findings.append(f)
                for m in fm:
                    m["file"] = cf.path
                    m["in_diff"] = any(l in cf.added for l in range(m["line"], m["line"] + m["loc"]))
                    func_rows.append(m)
            else:
                full_mode[cf.path] = False
                padded_all = []
                for start, lines in cf.hunks:
                    off = start - 1
                    snippet = "\n".join(lines)
                    fs, fm = analyze_source(snippet, cf.path, off)
                    analysed.setdefault(cf.path, []).append((snippet, off))
                    padded_all.append((off, lines))
                    for f in fs:
                        f.extra["in_diff"] = any(l in cf.added for l in range(f.line, f.end_line + 1))
                        f.extra["hunk_off"] = off
                        findings.append(f)
                    for m in fm:
                        m["file"] = cf.path
                        m["in_diff"] = any(l in cf.added for l in range(m["line"], m["line"] + m["loc"]))
                        func_rows.append(m)
            det.append(f"{cf.path}: scanned ({'full file' if cf.new_source is not None else f'{len(cf.hunks)} hunk(s)'})")
        sec = sum(1 for f in findings if f.category == "security")
        return f"{sec} security and {len(findings) - sec} quality findings from AST/taint rules", det
    tick("Static Analysis Agent: AST + taint rules")
    trace.run("Static Analysis Agent", "AST parsing, taint tracking, regex rules for other languages", static)

    # function-level quality findings belong to the PR if any line of that function changed
    func_level = {"Q_COMPLEXITY", "Q_NESTING", "Q_LONG_FUNC", "Q_MANY_PARAMS", "Q_NO_DOCSTRING", "Q_MUTABLE_DEFAULT"}
    fn_in_diff = {(m["file"], m["name"]): m.get("in_diff", True) for m in func_rows}
    for f in findings:
        f.extra.setdefault("in_diff", True)
        if f.rule_id in func_level and (f.file, f.function) in fn_in_diff:
            f.extra["in_diff"] = fn_in_diff[(f.file, f.function)]

    # ---- 3. ML risk
    ml_rows = []

    def ml_agent():
        if not ml:
            return "Skipped (disabled)", []
        from .mlmodel import predict_metrics
        det = []
        for m in func_rows:
            if m["name"] == "<module>" or not m.get("in_diff", True):
                continue
            pr = predict_metrics(m)
            row = dict(file=m["file"], function=m["name"], line=m["line"], probability=pr["probability"],
                       vuln_type=pr["vuln_type"], drivers=pr["drivers"], metrics={k: m[k] for k in FEATURE_LABEL})
            ml_rows.append(row)
            if pr["probability"] >= 0.5:
                det.append(f"{m['file']}::{m['name']} p={pr['probability']:.2f} type={pr['vuln_type']}")
        # correlate with static findings and raise an ML-only finding for uncovered high-risk functions
        for row in ml_rows:
            near = [f for f in findings if f.file == row["file"] and f.category == "security"
                    and f.function == row["function"] and not f.rule_id.startswith("Q_")]
            for f in near:
                f.extra["ml"] = row["probability"]
                f.extra["ml_drivers"] = row["drivers"]
            if row["probability"] >= 0.75 and not near:
                fn_rows = [m for m in func_rows if m["file"] == row["file"] and m["name"] == row["function"]]
                line = row["line"]
                f = Finding("Q_ML_RISK", row["file"], line, line, row["function"], "", "medium",
                            f"{row['probability']:.0%}", detector="ml")
                f.extra.update(in_diff=True, ml=row["probability"], ml_drivers=row["drivers"])
                findings.append(f)
        flagged = sum(1 for r in ml_rows if r["probability"] >= 0.5)
        return f"{len(ml_rows)} changed function(s) scored; {flagged} predicted vulnerable", det
    tick("ML Risk Agent: source-code metric model")
    trace.run("ML Risk Agent", "Base-paper technique: 14 source-code metrics -> trained classifier risk score", ml_agent)

    # ---- 4. reasoning
    def reason():
        n = 0
        for f in findings:
            meta = kb(f.rule_id)
            f.extra["title"] = meta["title"]
            f.extra["explanation"] = _fill(meta["explanation"], f)
            f.extra["impact"] = meta["impact"]
            f.extra["exploit"] = meta["exploit"]
            f.extra["remediation"] = meta["fix"]
            f.extra["safe_example"] = meta["safe"]
            f.extra["cwe"] = meta["cwe"]
            f.extra["owasp"] = meta["owasp"]
            flow = []
            if f.category == "security" and f.detector == "static" and f.extra.get("in_diff"):
                if "request/input" in f.evidence:
                    flow = ["Attacker-controlled HTTP/CLI input enters the function",
                            f"Data flows into {f.sink or 'a sensitive operation'} without sanitisation",
                            "Sensitive operation executes with attacker data -> " + meta["title"]]
                elif "function parameters" in f.evidence:
                    flow = ["Value arrives as a function parameter (callers may pass untrusted data)",
                            f"Reaches {f.sink or 'sensitive operation'} unsanitised"]
            f.extra["flow"] = flow
            if f.extra.get("ml") is not None and f.extra["ml"] >= 0.5:
                d = ", ".join(x["feature"] for x in f.extra.get("ml_drivers", [])[:2])
                f.extra["corroboration"] = (f"Independent metric model also rates `{f.function}` as vulnerable "
                                            f"(p={f.extra['ml']:.2f}; drivers: {d or 'n/a'}).")
                if f.confidence == "low":
                    f.confidence = "medium"
                elif f.confidence == "medium" and f.extra["ml"] >= 0.8:
                    f.confidence = "high"
                n += 1
        llm_used = 0
        if use_llm and llm.available(api_key):
            top = sorted([f for f in findings if f.category == "security"],
                         key=lambda f: -SEVERITY_ORDER[f.severity])[:6]
            for f in top:
                txt = llm.ask(
                    f"Code line ({f.file}:{f.line}): `{f.snippet}`\nFinding: {f.extra['title']} ({f.extra['cwe']}).\n"
                    f"In 3 sentences, explain to a junior developer why this is dangerous here and what to change. No preamble.",
                    system="You are a senior application-security engineer reviewing a pull request.", key=api_key)
                if txt:
                    f.extra["llm_explanation"] = txt
                    llm_used += 1
        return (f"Enriched {len(findings)} findings; {n} corroborated by ML"
                + (f"; {llm_used} LLM explanations" if use_llm else ""), [])
    tick("Security Reasoner: contextual explanations")
    trace.run("Security Reasoner", "Explains each flaw in context: flow, impact, CWE/OWASP, ML corroboration", reason)

    # ---- 5. remediation
    patched: dict[str, str] = {}
    verified = {"ok": 0, "total": 0}

    def remediate():
        det = []
        by_file: dict[str, list[Finding]] = {}
        for f in findings:
            if f.fix:
                by_file.setdefault(f.file, []).append(f)
        for path, fl in by_file.items():
            if full_mode.get(path):
                base = patch_src[path]
                for f in fl:
                    fx = f.fix
                    new, ok = apply_fixes(base, [fx])
                    f.extra["patch"] = make_patch(path, base, new, 2) if ok else ""
                    f.extra["fix_note"] = fx.get("note", "")
                    verified["total"] += 1
                    if ok:
                        fs2, _ = analyze_source(new, path)
                        still = any(x.rule_id == f.rule_id and abs(x.line - f.line) <= 1 for x in fs2)
                        try:
                            ast.parse(new) if path.endswith(".py") else None
                            parses = True
                        except SyntaxError:
                            parses = False
                        f.extra["fix_verified"] = (not still) and parses
                        verified["ok"] += int(f.extra["fix_verified"])
                allfix, applied = apply_fixes(base, [f.fix for f in fl if f.extra.get("fix_verified", True)])
                if applied and allfix != base:
                    patched[path] = allfix
                det.append(f"{path}: {len(fl)} auto-fix(es)")
            else:
                # hunk mode: patch each snippet on padded text so line numbers stay true
                for f in fl:
                    off = f.extra.get("hunk_off", 0)
                    snippet = next((s for s, o in analysed.get(path, []) if o == off), None)
                    if snippet is None:
                        continue
                    base = "\n" * off + snippet
                    fx = f.fix
                    new, ok = apply_fixes(base, [fx])
                    f.extra["patch"] = make_patch(path, base, new, 2) if ok else ""
                    f.extra["fix_note"] = fx.get("note", "")
                    verified["total"] += 1
                    if ok:
                        fs2, _ = analyze_source(new[off:] if off and new.startswith("\n" * off) else new, path, off)
                        still = any(x.rule_id == f.rule_id and abs(x.line - f.line) <= 1 for x in fs2)
                        f.extra["fix_verified"] = not still
                        verified["ok"] += int(not still)
        for f in findings:
            if f.category == "security" and not f.extra.get("patch"):
                f.extra["patch"] = ""
        return (f"{sum(1 for f in findings if f.extra.get('patch'))} auto-patch(es) generated; "
                f"{verified['ok']}/{verified['total']} verified by re-scan", [])
    tick("Remediation Agent: generating and verifying patches")
    trace.run("Remediation Agent", "Generates safe patches and verifies them by re-running the analyzers", remediate)

    # ---- 6. quality
    def quality():
        q = [f for f in findings if f.category == "quality" and f.extra.get("in_diff")]
        c = Counter(f.rule_id for f in q)
        return f"{len(q)} maintainability issue(s) in changed code", [f"{kb(k)['title']}: {v}" for k, v in c.most_common(6)]
    trace.run("Quality Reviewer", "Complexity, nesting, size, error handling, dead imports", quality)

    # ---- 7. judge
    def judge():
        # de-duplicate: same file/line/CWE from different detectors
        seen, out = set(), []
        for f in sorted(findings, key=lambda f: (-SEVERITY_ORDER[f.severity], f.file, f.line)):
            k = (f.file, f.line, kb(f.rule_id)["cwe"] or f.rule_id)
            if k in seen:
                continue
            seen.add(k)
            out.append(f)
        findings[:] = out
        return f"{len(findings)} unique findings after de-duplication", []
    tick("Judge Agent: scoring and verdict")
    trace.run("Judge Agent", "De-duplicates, scores risk, issues merge verdict", judge)

    floor = SEVERITY_ORDER[min_severity]
    visible = [f for f in findings if SEVERITY_ORDER[f.severity] >= floor]
    weight = 0.0
    for f in visible:
        if f.category != "security" and f.severity in ("info",):
            continue
        w = SEVERITY_WEIGHT[f.severity] * CONF_WEIGHT[f.confidence]
        weight += w if f.extra.get("in_diff") else w * 0.15
    score = round(100 * (1 - math.exp(-weight / 18)))
    blockers = [f for f in visible if f.extra.get("in_diff") and f.category == "security"
                and SEVERITY_ORDER[f.severity] >= 3 and f.confidence in ("high", "medium")]
    mediums = [f for f in visible if f.extra.get("in_diff") and SEVERITY_ORDER[f.severity] >= 2]
    if blockers or score >= 70:
        verdict = "BLOCK"
    elif mediums or score >= 30:
        verdict = "REQUEST_CHANGES"
    else:
        verdict = "APPROVE"

    fdicts = [finding_to_dict(f) for f in visible]
    stats = dict(
        by_severity={s: sum(1 for f in fdicts if f["severity"] == s and f["in_diff"]) for s in SEVERITY_ORDER},
        by_category=dict(Counter(f["category"] for f in fdicts if f["in_diff"])),
        by_cwe=dict(Counter(f["cwe"] for f in fdicts if f["cwe"] and f["in_diff"])),
        by_file=dict(Counter(f["file"] for f in fdicts if f["in_diff"])),
        preexisting=sum(1 for f in fdicts if not f["in_diff"]),
        files=len(changed), lines_added=sum(cf.n_added for cf in changed), lines_removed=sum(cf.n_removed for cf in changed),
        functions_scored=len(ml_rows), functions_flagged=sum(1 for r in ml_rows if r["probability"] >= 0.5),
        autofix=sum(1 for f in fdicts if f["patch"]), autofix_verified=sum(1 for f in fdicts if f["fix_verified"]),
    )
    review = dict(id=uuid.uuid4().hex[:8], created=datetime.now().isoformat(timespec="seconds"), title=title,
                  source=source_label, score=score, verdict=verdict, findings=fdicts, ml=ml_rows,
                  functions=func_rows, trace=trace.items, stats=stats,
                  files=[dict(path=cf.path, status=cf.status, added=cf.n_added, removed=cf.n_removed, language=cf.language)
                         for cf in changed],
                  patched=patched)
    review["summary"] = summarize(review)
    return review


def finding_to_dict(f: Finding) -> dict:
    meta = kb(f.rule_id)
    e = f.extra
    return dict(
        id=f"{f.rule_id}-{f.file}-{f.line}", rule_id=f.rule_id, title=meta["title"], category=f.category,
        severity=f.severity, confidence=f.confidence, cwe=meta["cwe"], owasp=meta["owasp"], file=f.file,
        line=f.line, end_line=f.end_line, function=f.function, snippet=f.snippet, detector=f.detector,
        in_diff=bool(e.get("in_diff", True)), explanation=e.get("llm_explanation") or e.get("explanation", ""),
        static_explanation=e.get("explanation", ""), llm=bool(e.get("llm_explanation")),
        impact=e.get("impact", ""), exploit=e.get("exploit", ""), remediation=e.get("remediation", ""),
        safe_example=e.get("safe_example", ""), flow=e.get("flow", []), corroboration=e.get("corroboration", ""),
        ml=e.get("ml"), patch=e.get("patch", ""), fix_note=e.get("fix_note", ""), fix_verified=bool(e.get("fix_verified")),
        evidence=f.evidence,
    )


def summarize(r: dict) -> str:
    s = r["stats"]["by_severity"]
    sec = r["stats"]["by_category"].get("security", 0)
    top = [f for f in r["findings"] if f["in_diff"] and f["category"] == "security"][:3]
    lead = {"BLOCK": "Do not merge:", "REQUEST_CHANGES": "Changes requested:", "APPROVE": "Looks good:"}[r["verdict"]]
    parts = [f"{lead} risk score {r['score']}/100 across {r['stats']['files']} file(s)."]
    if sec:
        parts.append(f"{sec} security finding(s) in the changed code "
                     f"({s['critical']} critical, {s['high']} high, {s['medium']} medium).")
        parts.append("Most serious: " + "; ".join(f"{f['title']} at {f['file']}:{f['line']}" for f in top) + ".")
    else:
        parts.append("No security findings in the changed code.")
    if r["stats"]["autofix"]:
        parts.append(f"{r['stats']['autofix']} finding(s) have auto-generated patches "
                     f"({r['stats']['autofix_verified']} verified by re-scan).")
    return " ".join(parts)
