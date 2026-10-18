"""AutoSecAI - Autonomous pull-request analysis for security, vulnerability detection and code quality.

Run:  streamlit run app.py
"""
from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from autosecai import __version__, llm, report, store, ui
from autosecai.agents import review_changes
from autosecai.codeintel import CONCEPTS, RepoIndex
from autosecai.diffutil import (diff_from_versions, fetch_github_pr_diff, fetch_github_repo_zip, files_from_dir,
                                files_from_zip, full_files_to_changed, parse_unified_diff)
from autosecai.knowledge import SEVERITY_ORDER
from autosecai.metrics import FEATURE_LABEL, METRICS, metrics_for_source
from autosecai.rules import analyze_source
from autosecai.samples import AFTER, BEFORE, DEMO_DIFF, DEMO_REPO

ROOT = Path(__file__).parent

st.set_page_config(page_title="AutoSecAI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

PAGES = ["🏠 Overview", "🔍 PR Review", "💬 Codebase Assistant", "🧪 Model Lab", "🕘 History", "ℹ️ About"]
st.session_state.setdefault("nav", PAGES[0])
st.session_state.setdefault("review", None)
st.session_state.setdefault("index", None)
st.session_state.setdefault("chat", [])


def goto(page):
    st.session_state.nav = page


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown('<div class="brand"><div class="logo">🛡️</div><div><b>AutoSecAI</b>'
                f'<span>PR security &amp; code intelligence · v{__version__}</span></div></div>', unsafe_allow_html=True)
    st.radio("Navigate", PAGES, key="nav", label_visibility="collapsed")
    st.divider()
    with st.expander("⚙️ Settings", expanded=False):
        use_ml = st.toggle("ML risk agent (base paper)", value=True, help="Scores each changed function with the metric-based Random Forest.")
        min_sev = st.selectbox("Minimum severity shown", list(SEVERITY_ORDER)[::-1], index=0,
                               format_func=str.title, help="Hide findings below this level.")
        api_key = st.text_input("Anthropic API key (optional)", type="password",
                                help="Enables LLM-written explanations. Everything else works offline.")
        use_llm = st.toggle("LLM explanations", value=False, disabled=not (api_key or llm.available()))
        gh_token = st.text_input("GitHub token (optional)", type="password", help="For private repos / higher rate limits.")
    st.caption("Runs 100 % locally in Python. No code leaves your machine unless you enable the LLM option.")


# ------------------------------------------------------------------ helpers
@st.cache_data(show_spinner=False)
def _report():
    from autosecai.mlmodel import load_report
    return load_report()


def run_review(changed, title, source):
    with st.status("Agents are reviewing the pull request…", expanded=True) as status:
        t0 = time.time()
        r = review_changes(changed, title=title, source_label=source, use_llm=use_llm, api_key=api_key or None, ml=use_ml,
                           min_severity=min_sev, progress=lambda m: status.write("• " + m))
        status.update(label=f"Review complete in {time.time() - t0:.1f}s - verdict: {r['verdict'].replace('_', ' ')}",
                      state="complete", expanded=False)
    store.save(r)
    st.session_state.review = r
    return r


def render_review(r: dict, key: str = "rv"):
    ui.verdict_banner(r)
    st.write("")
    s = r["stats"]
    c = st.columns([1.15, 1, 1, 1, 1])
    c[0].plotly_chart(ui.gauge(r["score"]), width="stretch", key=f"{key}-gauge")
    ui.kpi(c[1], "Security findings", s["by_category"].get("security", 0), "#dc2626" if s["by_category"].get("security") else "#059669")
    ui.kpi(c[2], "Critical + High", s["by_severity"]["critical"] + s["by_severity"]["high"],
           "#dc2626" if s["by_severity"]["critical"] + s["by_severity"]["high"] else "#059669")
    ui.kpi(c[3], "Quality issues", s["by_category"].get("quality", 0), "#d97706")
    ui.kpi(c[4], "Auto-fixes (verified)", f"{s['autofix']} ({s['autofix_verified']})", "#4f46e5",
           "Patches generated, and how many were confirmed by re-scanning the patched code")
    st.write("")
    tabs = st.tabs(["🔎 Findings", "🤖 Function risk (ML)", "📁 Files", "🧠 Agent trace", "📤 Export"])

    # ---- findings
    with tabs[0]:
        fl_all = r["findings"]
        left, right = st.columns([2.2, 1])
        with right:
            if any(s["by_severity"].values()):
                st.plotly_chart(ui.donut(s["by_severity"]), width="stretch", key=f"{key}-donut")
            if s["by_cwe"]:
                st.plotly_chart(ui.hbar(s["by_cwe"], "Weakness types (CWE)", "#4f46e5", 6), width="stretch", key=f"{key}-cwe")
            if len(s["by_file"]) > 1:
                st.plotly_chart(ui.hbar(s["by_file"], "Findings per file", "#0ea5e9", 6), width="stretch", key=f"{key}-files")
        with left:
            f1, f2, f3 = st.columns([2, 1.3, 1.4])
            sev_sel = f1.multiselect("Severity", list(SEVERITY_ORDER)[::-1], default=["critical", "high", "medium", "low"],
                                     format_func=str.title, key=f"{key}-sev")
            cat = f2.radio("Category", ["All", "Security", "Quality"], horizontal=True, key=f"{key}-cat")
            only_diff = f3.toggle("Only changed lines", value=True, key=f"{key}-diff",
                                  help="Hide issues that already existed before this PR.")
            q = st.text_input("Search findings", placeholder="e.g. sql, CWE-78, users.py", key=f"{key}-q",
                              label_visibility="collapsed")
            fl = [f for f in fl_all if f["severity"] in sev_sel and (cat == "All" or f["category"] == cat.lower())
                  and (f["in_diff"] or not only_diff)
                  and (not q or q.lower() in (f["title"] + f["file"] + f["cwe"] + f["rule_id"] + f["function"]).lower())]
            fl = ui.sort_findings(fl)
            st.caption(f"Showing {len(fl)} of {len(fl_all)} findings · {s['preexisting']} pre-existing outside the diff")
            if not fl:
                st.success("Nothing to show with the current filters.", icon="🎉")
            for i, f in enumerate(fl[:50]):
                ui.finding_card(f, f"{key}-{i}")
            if len(fl) > 50:
                st.info(f"{len(fl) - 50} more findings hidden - narrow the filters or download the full report.")

    # ---- ML
    with tabs[1]:
        ml = r["ml"]
        if not ml:
            st.info("No functions were scored (ML agent disabled or no parsable Python functions in the changed code).")
        else:
            st.markdown("**Base-paper technique:** each changed function's source-code metrics (complexity, nesting, argument count, "
                        "risky calls, input sources …) are scored by a Random Forest trained to separate vulnerable from safe functions.")
            df = pd.DataFrame([dict(function=m["function"], file=m["file"], line=m["line"], risk=m["probability"],
                                    predicted_type=(m["vuln_type"] or "-").replace("_", " "),
                                    top_drivers=", ".join(d["feature"] for d in m["drivers"])) for m in ml]).sort_values("risk", ascending=False)
            st.dataframe(df, hide_index=True, width="stretch", column_config={
                "risk": st.column_config.ProgressColumn("Vulnerability risk", min_value=0, max_value=1, format="%.2f")})
            names = [f"{m['function']}  ({m['file']}:{m['line']})" for m in sorted(ml, key=lambda m: -m["probability"])]
            pick = st.selectbox("Inspect function", names, key=f"{key}-fn")
            m = sorted(ml, key=lambda m: -m["probability"])[names.index(pick)]
            from autosecai.mlmodel import load_bundle
            safe = load_bundle()["safe_stats"]["mean"]
            a, b = st.columns([1.1, 1])
            a.plotly_chart(ui.radar(m["metrics"], safe), width="stretch", key=f"{key}-radar")
            with b:
                st.metric("Vulnerability probability", f"{m['probability']:.0%}")
                if m["vuln_type"]:
                    st.metric("Most likely type", m["vuln_type"].replace("_", " ").title())
                if m["drivers"]:
                    st.markdown("**Why the model is worried**")
                    for d in m["drivers"]:
                        st.markdown(f"- **{d['feature']}** = {d['value']:g} (typical safe function: {d['safe_mean']:.1f})")
                st.dataframe(pd.DataFrame({"Metric": [FEATURE_LABEL[k] for k in m["metrics"]],
                                           "Value": list(m["metrics"].values())}), hide_index=True, height=250, width="stretch")

    # ---- files
    with tabs[2]:
        by_file = s["by_file"]
        df = pd.DataFrame([dict(file=f["path"], language=f["language"], status=f["status"], added=f["added"], removed=f["removed"],
                                findings=by_file.get(f["path"], 0)) for f in r["files"]]).sort_values("findings", ascending=False)
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            "findings": st.column_config.ProgressColumn("Findings in change", min_value=0, max_value=max(int(df["findings"].max()), 1),
                                                        format="%d")})
        fm = [m for m in r["functions"] if m["name"] != "<module>"]
        if fm:
            st.markdown("**Function complexity in changed files**")
            cdf = pd.DataFrame([dict(function=m["name"], file=m["file"], cyclomatic=m["cyclomatic"], nesting=m["max_nesting"],
                                     params=m["n_params"], loc=m["loc"], changed=m.get("in_diff", True)) for m in fm]) \
                .sort_values("cyclomatic", ascending=False).head(15)
            st.dataframe(cdf, hide_index=True, width="stretch")

    # ---- trace
    with tabs[3]:
        st.caption("What each agent did, in order. This is the audit trail behind the verdict.")
        for t in r["trace"]:
            det = "".join(f"<div class='small'>• {ui.esc(d)}</div>" for d in t["details"][:6])
            st.markdown(f'<div class="trace"><b>{ui.esc(t["agent"])}</b> <span class="r">· {ui.esc(t["role"])} · {t["seconds"]}s</span>'
                        f'<div class="d">{ui.esc(t["summary"])}</div>{det}</div>', unsafe_allow_html=True)

    # ---- export
    with tabs[4]:
        md = report.to_markdown(r)
        c1, c2 = st.columns([1.3, 1])
        with c1:
            st.markdown("**PR comment preview** (paste into GitHub)")
            with st.container(border=True, height=420):
                st.markdown(md, unsafe_allow_html=True)
        with c2:
            st.markdown("**Download**")
            st.download_button("⬇️ PR comment (.md)", md, f"autosecai-{r['id']}.md", width="stretch", key=f"{key}-dl-md")
            st.download_button("⬇️ SARIF 2.1 (GitHub code scanning)", report.to_sarif(r), f"autosecai-{r['id']}.sarif",
                               width="stretch", key=f"{key}-dl-sarif")
            st.download_button("⬇️ Full JSON", report.to_json(r), f"autosecai-{r['id']}.json", width="stretch", key=f"{key}-dl-json")
            st.download_button("⬇️ Findings CSV", report.to_csv(r), f"autosecai-{r['id']}.csv", width="stretch", key=f"{key}-dl-csv")
            if r.get("patched"):
                st.markdown("**Auto-fixed files**")
                for i, (p, txt) in enumerate(list(r["patched"].items())[:8]):
                    st.download_button(f"⬇️ {p}", txt, Path(p).name, width="stretch", key=f"{key}-dl-p{i}")


# ------------------------------------------------------------------ pages
def page_overview():
    st.markdown('<div class="hero"><h1>Autonomous pull-request security review</h1>'
                '<p>AutoSecAI reads every pull request like a security engineer: it finds vulnerabilities with static analysis, '
                'predicts risky functions with the metric model from the base paper, explains each flaw in plain language, '
                'proposes verified patches - and helps new developers find their way around the codebase.</p></div>', unsafe_allow_html=True)
    c = st.columns(3)
    cards = [("🔍 PR Review", "Paste a diff, compare two versions, drop a GitHub PR link or upload a repo. Get a verdict, risk score, "
                              "explanations and patches in seconds.", "🔍 PR Review", "Review a pull request"),
             ("💬 Codebase Assistant", "Ask “where is authentication handled?” or “which files define the routes?”. "
                                       "Graph-based retrieval answers with files, functions and call flow.", "💬 Codebase Assistant", "Ask your codebase"),
             ("🧪 Model Lab", "Reproduces the base paper: 14 metrics, 7 feature-selection methods, SmoteTomek, 9 models, "
                              "Random Forest and vulnerability-type classification.", "🧪 Model Lab", "Explore the model")]
    for col, (t, d, page, btn) in zip(c, cards):
        with col:
            st.markdown(f'<div class="card"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)
            st.button(btn, key=f"go-{page}", on_click=goto, args=(page,), width="stretch")
    st.write("")
    st.subheader("How the agents work together")
    st.markdown(ui.pipeline_html(), unsafe_allow_html=True)
    st.write("")
    hist = store.list_reviews(50)
    a, b = st.columns([1.2, 1])
    with a:
        st.subheader("Try it in one click")
        st.markdown("Load a deliberately vulnerable Flask pull request and watch the agents work.")
        if st.button("▶ Run demo pull request review", type="primary", key="demo-go"):
            r = run_review(parse_unified_diff(DEMO_DIFF), "Demo: add user API", "built-in demo diff")
            goto("🔍 PR Review")
            st.rerun()
    with b:
        st.subheader("Your activity")
        if hist:
            k = st.columns(3)
            ui.kpi(k[0], "Reviews", len(hist))
            ui.kpi(k[1], "Avg risk", round(sum(h["score"] for h in hist) / len(hist)))
            ui.kpi(k[2], "Blocked", sum(h["verdict"] == "BLOCK" for h in hist), "#dc2626")
        else:
            st.caption("No reviews yet - run the demo to get started.")


def page_review():
    st.title("🔍 Pull request review")
    st.caption("Choose how to provide the change. Only lines added or modified by the PR block the merge; older issues are shown separately.")
    mode = st.radio("Input", ["Demo PR", "Paste diff", "Compare two versions", "GitHub PR link", "Upload files / repo"],
                    horizontal=True, label_visibility="collapsed")
    changed, title, source, ready = [], "Pull request", mode, False
    if mode == "Demo PR":
        which = st.radio("Sample", ["Vulnerable Flask API (diff)", "Before / after of one file"], horizontal=True)
        if which.startswith("Vulnerable"):
            with st.expander("Preview diff"):
                st.code(DEMO_DIFF, language="diff")
            changed, title, ready = parse_unified_diff(DEMO_DIFF), "Demo: add user API", True
        else:
            with st.expander("Preview versions"):
                a, b = st.columns(2)
                a.code(BEFORE, language="python")
                b.code(AFTER, language="python")
            changed, title, ready = [diff_from_versions(BEFORE, AFTER, "services/users.py")], "Demo: refactor user service", True
    elif mode == "Paste diff":
        title = st.text_input("Title", "Pasted pull request")
        up = st.file_uploader("…or upload a .diff / .patch file", type=["diff", "patch", "txt"])
        txt = up.read().decode("utf-8", errors="replace") if up else st.text_area(
            "Unified diff (git diff / PR .diff)", height=260, placeholder="diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1,3 +1,5 @@ ...")
        if txt.strip():
            changed = parse_unified_diff(txt)
            ready = bool(changed)
            if not changed:
                st.warning("No files were found in that diff. Make sure it is a unified diff (starts with `diff --git` or `---/+++`).")
    elif mode == "Compare two versions":
        title = st.text_input("Title", "Local change")
        fname = st.text_input("File name", "app.py")
        c1, c2 = st.columns(2)
        old = c1.text_area("Before (optional - leave empty for a new file)", height=280, key="old_src")
        new = c2.text_area("After", height=280, key="new_src")
        if new.strip():
            changed, ready = [diff_from_versions(old or None, new, fname)], True
    elif mode == "GitHub PR link":
        url = st.text_input("Pull request URL", placeholder="https://github.com/owner/repo/pull/123")
        st.caption("Public PRs work without a token (60 requests/hour). Add a token in Settings for private repositories.")
        if url.strip():
            ready = True
            title, source = url.strip(), url.strip()
    else:
        up = st.file_uploader("Upload source files or a .zip of a repository", accept_multiple_files=True)
        path = st.text_input("…or a local folder path", placeholder=r"C:\projects\my-app")
        title = st.text_input("Title", "Repository scan")
        files = {}
        for f in up or []:
            data = f.read()
            if f.name.lower().endswith(".zip"):
                try:
                    files.update(files_from_zip(data))
                except zipfile.BadZipFile:
                    st.error(f"{f.name} is not a valid zip file.")
            else:
                files[f.name] = data.decode("utf-8", errors="replace")
        if path.strip():
            if Path(path.strip()).is_dir():
                files.update(files_from_dir(path.strip()))
            else:
                st.error("That folder does not exist.")
        if files:
            changed, ready = full_files_to_changed(files), True
            st.success(f"{len(files)} file(s) ready. All lines are treated as changed (full scan).")

    if st.button("🚀 Run multi-agent review", type="primary", disabled=not ready):
        try:
            if mode == "GitHub PR link":
                with st.spinner("Fetching pull request from GitHub…"):
                    diff, meta = fetch_github_pr_diff(url.strip(), gh_token or None)
                changed = parse_unified_diff(diff)
                title = f"{meta['repo']}#{meta['number']}: {meta['title']}"
                st.caption(f"By **{meta['author']}** · {meta['changed_files']} files · +{meta['additions']}/-{meta['deletions']}")
            if not changed:
                st.error("The change contains no files to analyse.")
            elif len(changed) > 300:
                st.error("Too many files (limit 300). Narrow the change.")
            else:
                run_review(changed, title, source)
        except Exception as e:  # network / parsing errors surface as friendly messages
            st.error(f"Could not complete the review: {e}")
    if st.session_state.review:
        st.divider()
        st.subheader(st.session_state.review["title"])
        render_review(st.session_state.review, "cur")
    else:
        st.info("Run a review to see the verdict, findings, patches and agent trace here.", icon="👆")


SUGGESTED = ["Where is the authentication mechanism implemented?", "Which files define the routes / API endpoints?",
             "Where is the login form in the UI?", "How does the app talk to the database?",
             "Where is configuration and secret handling?", "What are the entry points of this application?"]


def _build_index(src, files_up, folder, url):
    if src == "Demo shop app":
        return RepoIndex(DEMO_REPO, "demo-shop")
    if src == "AutoSecAI (this project)":
        return RepoIndex(files_from_dir(str(ROOT)), "AutoSecAI")
    if src == "Upload .zip":
        files = {}
        for f in files_up or []:
            files.update(files_from_zip(f.read()))
        return RepoIndex(files, files_up[0].name.rsplit(".", 1)[0]) if files else None
    if src == "Local folder":
        return RepoIndex(files_from_dir(folder), Path(folder).name) if folder and Path(folder).is_dir() else None
    return RepoIndex(fetch_github_repo_zip(url, gh_token or None), url.rstrip("/").split("/")[-1])


def page_codebase():
    st.title("💬 Codebase intelligence assistant")
    st.caption("Index a repository, then ask natural-language questions. Retrieval combines text similarity, concept detection "
               "(auth, routing, UI, database …) and the import/call graph.")
    with st.container(border=True):
        c1, c2 = st.columns([1.3, 1.7])
        src = c1.selectbox("Repository", ["Demo shop app", "AutoSecAI (this project)", "Upload .zip", "Local folder", "GitHub repo URL"])
        files_up = folder = url = None
        with c2:
            if src == "Upload .zip":
                files_up = st.file_uploader("Zip of the repository", type=["zip"], accept_multiple_files=True, label_visibility="collapsed")
            elif src == "Local folder":
                folder = st.text_input("Folder path", placeholder=r"C:\projects\my-app", label_visibility="collapsed")
            elif src == "GitHub repo URL":
                url = st.text_input("Repo URL", placeholder="https://github.com/owner/repo", label_visibility="collapsed")
            else:
                st.write("")
                st.caption("Ready to index.")
        if st.button("📚 Index repository", type="primary"):
            try:
                with st.spinner("Parsing files, building call graph and search index…"):
                    ix = _build_index(src, files_up, folder, url)
                if ix is None or not ix.chunks:
                    st.error("Nothing to index - check the source.")
                else:
                    st.session_state.index, st.session_state.chat = ix, []
                    st.success(f"Indexed {len(ix.files)} files, {len(ix.chunks)} code units.")
            except Exception as e:
                st.error(f"Indexing failed: {e}")
    ix: RepoIndex | None = st.session_state.index
    if ix is None:
        st.info("Index a repository to start asking questions.", icon="👆")
        return
    tabs = st.tabs(["💬 Ask", "🗺️ Repository map", "🧭 Onboarding guide"])
    with tabs[0]:
        st.markdown("**Try asking**")
        cols = st.columns(3)
        for i, q in enumerate(SUGGESTED):
            if cols[i % 3].button(q, key=f"sq{i}", width="stretch"):
                st.session_state.pending_q = q
        for m in st.session_state.chat:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
                for j, h in enumerate(m.get("hits", [])[:5]):
                    with st.expander(f"`{h['file']}` · {h['name'] if h['kind'] != 'file' else 'module overview'} · line {h['line']}"):
                        if h["why"]:
                            st.markdown(" ".join(ui.chip(w, "gray") for w in h["why"]), unsafe_allow_html=True)
                        st.code(h["code"], language="python" if h["file"].endswith(".py") else None)
        q = st.chat_input("Ask about the codebase…") or st.session_state.pop("pending_q", None)
        if q:
            st.session_state.chat.append({"role": "user", "content": q})
            res = ix.ask(q, k=6, use_llm=use_llm, api_key=api_key or None)
            st.session_state.chat.append({"role": "assistant", "content": res["answer"], "hits": res["hits"]})
            st.rerun()
    with tabs[1]:
        o = ix.overview()
        k = st.columns(5)
        for col, (l, v) in zip(k, [("Files", o["files"]), ("Lines", f"{o['loc']:,}"), ("Functions", o["functions"]),
                                   ("Classes", o["classes"]), ("Import links", o["import_edges"])]):
            ui.kpi(col, l, v)
        st.write("")
        a, b = st.columns([1, 1])
        with a:
            if o["routes"]:
                st.markdown("**API routes**")
                st.dataframe(pd.DataFrame(o["routes"])[["method", "path", "handler", "file", "line"]], hide_index=True, width="stretch")
            st.markdown("**Where things live**")
            for kx, files in o["by_concept"].items():
                if files:
                    st.markdown(f"- **{CONCEPTS[kx]['label']}:** " + ", ".join(f"`{f}`" for f in files[:4]))
            if o["hotspots"]:
                st.markdown("**Complexity hotspots**")
                st.dataframe(pd.DataFrame(o["hotspots"]), hide_index=True, width="stretch")
        with b:
            nodes, edges = ix.file_graph()
            connected = sorted({n for e in edges for n in e})
            if len(connected) > 1:
                G = nx.Graph()
                G.add_nodes_from(connected)
                G.add_edges_from(edges)
                pos = nx.spring_layout(G, seed=4, k=1.2 / max(len(G) ** .5, 1))
                ex, ey = [], []
                for u, v in edges:
                    ex += [pos[u][0], pos[v][0], None]
                    ey += [pos[u][1], pos[v][1], None]
                deg = dict(G.degree())
                fig = go.Figure([go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=1, color="#cbd5e1"), hoverinfo="none"),
                                 go.Scatter(x=[pos[n][0] for n in G], y=[pos[n][1] for n in G], mode="markers+text",
                                            text=[Path(n).name for n in G], textposition="top center", hovertext=list(G),
                                            marker=dict(size=[12 + 5 * deg[n] for n in G], color=[deg[n] for n in G],
                                                        colorscale="Viridis", showscale=False))])
                fig.update_layout(**ui.PLOT, height=420, showlegend=False, title="Module dependency graph",
                                  xaxis=dict(visible=False), yaxis=dict(visible=False))
                st.plotly_chart(fig, width="stretch", key="depgraph")
            else:
                st.caption("No module-level import links to draw.")
    with tabs[2]:
        st.markdown(ix.onboarding_guide())


def page_lab():
    st.title("🧪 Model Lab - base paper reproduction")
    st.caption("Leveraging Key Source Code Metrics for Predicting Software Vulnerabilities With Machine Learning · IEEE Access 2026 · "
               "DOI 10.1109/ACCESS.2026.3679930")
    try:
        R = _report()
    except Exception as e:
        st.error(f"Could not load the model report: {e}")
        return
    best = R["best"]
    res = R["results"]
    k = st.columns(5)
    ui.kpi(k[0], "Functions", f"{R['n_functions']:,}")
    ui.kpi(k[1], "Vulnerable", f"{R['n_vulnerable']} ({R['class_ratio']:.1%})")
    ui.kpi(k[2], f"{best} F1", f"{res[best]['f1']:.3f}", "#4f46e5")
    ui.kpi(k[3], f"{best} accuracy", f"{res[best]['accuracy']:.3f}", "#059669")
    ui.kpi(k[4], "Type-classifier acc.", f"{R['type_accuracy']:.2f}")
    st.info("**Data note:** the paper trains on C functions from 10 open-source projects. This system runs on Python, so the model is "
            "trained on a generated corpus of Python functions (vulnerable + look-alike safe code + label noise) whose metrics come from real "
            "AST analysis. Numbers below are therefore *this system's* results, not the paper's (RF: acc 0.96, F1 0.961).", icon="ℹ️")
    t = st.tabs(["Pipeline & data", "Feature selection", "Models", "ROC & confusion", "Vulnerability types", "Ablation", "Try it"])
    with t[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Pipeline (paper Fig. 1)**")
            st.markdown("1. Compute **14 source-code metrics** per function  \n2. Run **7 feature-selection methods**, keep the consensus  \n"
                        "3. **SmoteTomek** balancing (SMOTE oversampling + Tomek-link cleaning)  \n4. **Min-Max** normalisation  \n"
                        "5. Train & compare **9 models**  \n6. Classify the **vulnerability type**  \n7. Score functions inside each PR")
            st.markdown("**The 14 metrics**")
            st.dataframe(pd.DataFrame(METRICS, columns=["ID", "key", "Metric", "Meaning"]).drop(columns="key"), hide_index=True, height=300, width="stretch")
        with c2:
            fig = go.Figure(go.Bar(x=["Original train", "After SmoteTomek"], y=[R["train_size"], R["balanced_train_size"]],
                                   marker_color=["#94a3b8", "#4f46e5"], text=[R["train_size"], R["balanced_train_size"]], textposition="outside"))
            fig.update_layout(**ui.PLOT, height=280, title=f"Training set size (Tomek links removed: {R['tomek_removed']})")
            st.plotly_chart(fig, width="stretch", key="lab-bal")
            tc = R["type_counts"]
            st.plotly_chart(ui.hbar({k.replace("_", " "): v for k, v in tc.items()}, "Vulnerable functions by type", "#dc2626", 8),
                            width="stretch", key="lab-types")
    with t[1]:
        fs = pd.DataFrame(R["fs_scores"])
        norm = (fs - fs.min()) / (fs.max() - fs.min()).replace(0, 1)
        norm.index = [FEATURE_LABEL[i] for i in norm.index]
        fig = go.Figure(go.Heatmap(z=norm.values, x=list(norm.columns), y=list(norm.index), colorscale="Purples", showscale=False))
        fig.update_layout(**ui.PLOT, height=470, title="Importance of each metric per selection method (normalised)")
        fig.update_yaxes(autorange="reversed")
        a, b = st.columns([1.5, 1])
        a.plotly_chart(fig, width="stretch", key="lab-fs")
        with b:
            ks = R["k_scores"]
            fig = go.Figure(go.Scatter(x=[int(x) for x in ks], y=list(ks.values()), mode="lines+markers", line=dict(color="#4f46e5")))
            fig.add_vline(x=R["best_k"], line_dash="dash", line_color="#059669")
            fig.update_layout(**ui.PLOT, height=260, title="Validation F1 vs. number of metrics kept", xaxis_title="k", yaxis_title="F1")
            st.plotly_chart(fig, width="stretch", key="lab-k")
            st.markdown(f"**Kept {R['best_k']} metrics** (paper keeps 5): " + ", ".join(R["selected_labels"][:6]) + " …")
        votes = pd.DataFrame(R["fs_order"]).reset_index().rename(columns={"index": "metric"})
        votes["metric"] = votes["metric"].map(FEATURE_LABEL)
        st.dataframe(votes, hide_index=True, width="stretch")
    with t[2]:
        df = pd.DataFrame(res).T.reset_index().rename(columns={"index": "model"})
        fig = go.Figure()
        for m, col in zip(["accuracy", "precision", "recall", "f1"], ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b"]):
            fig.add_trace(go.Bar(name=m.title() if m != "f1" else "F1", x=df["model"], y=df[m], marker_color=col))
        fig.update_layout(**ui.PLOT, barmode="group", height=420, title="Nine models on the held-out test set", yaxis_range=[0, 1.05],
                          legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, width="stretch", key="lab-models")
        st.dataframe(df.style.format({c: "{:.3f}" for c in df.columns if c != "model"}).highlight_max(
            subset=["accuracy", "precision", "recall", "f1", "auc"], color="#dcfce7"), hide_index=True, width="stretch")
        imp = R["importance"]
        st.plotly_chart(ui.hbar(imp, "Random-forest feature importance", "#4f46e5", 14), width="stretch", key="lab-imp")
    with t[3]:
        a, b = st.columns(2)
        fig = go.Figure()
        for name, v in R["roc"].items():
            fig.add_trace(go.Scatter(x=v["fpr"], y=v["tpr"], mode="lines", name=f"{name} ({res[name]['auc']:.2f})",
                                     line=dict(width=3 if name == best else 1.5)))
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], line=dict(dash="dot", color="#9ca3af"), showlegend=False))
        fig.update_layout(**ui.PLOT, height=420, title="ROC curves", xaxis_title="False positive rate", yaxis_title="True positive rate")
        a.plotly_chart(fig, width="stretch", key="lab-roc")
        with b:
            mname = st.selectbox("Confusion matrix for", list(R["confusion"]), index=list(R["confusion"]).index(best))
            cm = np.array(R["confusion"][mname])
            fig = go.Figure(go.Heatmap(z=cm, x=["Pred safe", "Pred vulnerable"], y=["Actual safe", "Actual vulnerable"],
                                       text=cm, texttemplate="%{text}", colorscale="Blues", showscale=False))
            fig.update_layout(**ui.PLOT, height=340)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, width="stretch", key="lab-cm")
    with t[4]:
        rep = {k: v for k, v in R["type_report"].items() if k not in ("macro avg", "weighted avg")}
        df = pd.DataFrame(rep).T[["precision", "recall", "f1-score", "support"]].reset_index().rename(columns={"index": "type"})
        a, b = st.columns([1.2, 1])
        fig = go.Figure(go.Bar(x=df["type"].str.replace("_", " "), y=df["f1-score"], marker_color="#4f46e5"))
        fig.update_layout(**ui.PLOT, height=340, title=f"F1 per vulnerability type (overall accuracy {R['type_accuracy']:.2f})", yaxis_range=[0, 1])
        a.plotly_chart(fig, width="stretch", key="lab-type-f1")
        b.plotly_chart(ui.hbar(R["type_importance"], "Metrics that separate vulnerability types", "#0ea5e9", 8), width="stretch", key="lab-type-imp")
        st.caption("Type classification from metrics alone is inherently harder than detection (paper §V). In the PR pipeline the AST/taint "
                   "rules assign the precise type; this classifier is a second opinion for ML-only findings.")
    with t[5]:
        ab = pd.DataFrame(R["ablation"]).T.reset_index().rename(columns={"index": "configuration"})
        st.dataframe(ab.style.format({"recall": "{:.3f}", "precision": "{:.3f}", "f1": "{:.3f}"}), hide_index=True, width="stretch")
        st.caption("Honest comparison of the paper's exact setting (top-5 metrics) against validated feature-count selection and an "
                   "unbalanced all-metrics baseline on this corpus.")
    with t[6]:
        st.markdown("Paste a Python function - the app computes its metrics, scores it and runs the static rules.")
        default = ('def get_user(name):\n    q = f"SELECT * FROM users WHERE name = \'{name}\'"\n'
                   '    cur.execute(q)\n    return cur.fetchall()\n')
        code = st.text_area("Python code", default, height=200, key="lab-code")
        if st.button("Analyse function", type="primary", key="lab-run"):
            rows = metrics_for_source(code)
            if not rows:
                st.error("Could not parse that as Python.")
            else:
                from autosecai.mlmodel import predict_metrics
                for m in rows:
                    p = predict_metrics(m)
                    a, b = st.columns([1, 2])
                    a.plotly_chart(ui.gauge(round(p["probability"] * 100), f"{m['name']}()"), width="stretch", key=f"lab-g-{m['name']}")
                    with b:
                        st.markdown(f"**Predicted type:** {(p['vuln_type'] or 'none').replace('_', ' ')}")
                        for d in p["drivers"]:
                            st.markdown(f"- {d['feature']} = **{d['value']:g}** (safe avg {d['safe_mean']:.1f})")
                        st.dataframe(pd.DataFrame({"Metric": [FEATURE_LABEL[x] for x in FEATURE_LABEL],
                                                   "Value": [m[x] for x in FEATURE_LABEL]}), hide_index=True, height=200, width="stretch")
                fs, _ = analyze_source(code, "snippet.py")
                sec = [f for f in fs if f.category == "security"]
                if sec:
                    st.markdown("**Static findings**")
                    for f in sec:
                        st.markdown(f"- {ui.SEV_ICON[f.severity]} line {f.line}: **{f.extra.get('title') or __import__('autosecai.knowledge', fromlist=['rule']).rule(f.rule_id)['title']}**")
                else:
                    st.success("No static security findings.")
    st.divider()
    if st.button("🔄 Retrain models (≈30 s)", key="retrain"):
        from autosecai.mlmodel import train_all
        import autosecai.mlmodel as mm
        with st.spinner("Generating corpus, selecting features, balancing, training 9 models…"):
            train_all()
            mm._cache.clear()
            _report.clear()
        st.rerun()


def page_history():
    st.title("🕘 Review history")
    rows = store.list_reviews(200)
    if not rows:
        st.info("No reviews saved yet.")
        return
    df = pd.DataFrame(rows)
    a, b = st.columns([1.6, 1])
    with a:
        st.dataframe(df[["created", "title", "verdict", "score", "security", "findings", "id"]], hide_index=True, width="stretch",
                     column_config={"score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%d")})
    with b:
        d2 = df.sort_values("created")
        fig = go.Figure(go.Scatter(x=d2["created"], y=d2["score"], mode="lines+markers", line=dict(color="#4f46e5")))
        fig.update_layout(**ui.PLOT, height=250, title="Risk score over time", yaxis_range=[0, 100])
        st.plotly_chart(fig, width="stretch", key="hist-trend")
    pick = st.selectbox("Open a review", df["id"], format_func=lambda i: f"{df.set_index('id').loc[i, 'created']} - {df.set_index('id').loc[i, 'title']}")
    c1, c2 = st.columns([1, 6])
    if c2.button("🗑 Delete this review"):
        store.delete(pick)
        st.rerun()
    r = store.load(pick)
    if r:
        st.subheader(r["title"])
        render_review(r, f"h{pick}")


def page_about():
    st.title("ℹ️ About AutoSecAI")
    st.markdown("""
**Project:** AutoSecAI - Autonomous Pull Request Analysis for Security, Vulnerability Detection and Code Quality using Multi-Agent LLMs · CSE-A · Batch 11

**Abstract (implemented).** Modern teams merge pull requests too fast for manual security review, and new developers struggle to find their way
around large codebases. AutoSecAI extracts the files changed by a PR, runs static analysis, reasons over the findings with cooperating agents to
produce explanations, impact and safe remediation - and offers a natural-language codebase assistant.

**Base paper.** *Leveraging Key Source Code Metrics for Predicting Software Vulnerabilities With Machine Learning*, Abbasi & Shameli-Sendi,
IEEE Access 2026, DOI 10.1109/ACCESS.2026.3679930.
""")
    st.subheader("From paper to product")
    st.dataframe(pd.DataFrame([
        ("Predict vulnerability from source-code metrics", "ML Risk Agent scores every changed function inside the PR (paper's gap: it was offline only)"),
        ("14 metrics from a code property graph", "14 metric families computed from the Python AST/CFG (same numbering for the top metrics M1, M5, M6, M7, M9, M11)"),
        ("7 feature-selection methods + consensus", "Implemented (Pearson, SVM, Lasso, Chi², RFE-LR, RFE-RF, Variance); k validated on held-out data"),
        ("SmoteTomek + Min-Max", "Own SMOTE + Tomek-link implementation, no external imbalance library"),
        ("9 models, Random Forest best", "RF, DT, LR, SVM, KNN, NB, GB, XGBoost, soft-voting ensemble"),
        ("Vulnerability-type classification", "Random-forest type classifier over 8 types; static rules give exact CWE"),
        ("(extension) explain + fix", "Security Reasoner and Remediation agents explain flow/impact and generate re-scan-verified patches"),
        ("(extension) codebase intelligence", "Graph-based retrieval assistant with route, auth and UI discovery"),
    ], columns=["Paper contribution", "Where it lives in AutoSecAI"]), hide_index=True, width="stretch")
    st.subheader("Known limitations")
    st.markdown("""
- The ML model is trained on a **generated** Python corpus, not the paper's C datasets (which are not distributable here); treat its scores as a *prioritisation signal*, not proof.
- Deep taint analysis covers **Python** (intra-function). JavaScript/PHP/Java use pattern rules only.
- Without an API key the "reasoning" agents are deterministic knowledge-base agents; with a key, explanations for the top findings are written by Claude.
- Auto-fixes cover a curated set (SQL parameterisation, shell → argv list, `yaml.safe_load`, hash upgrade, TLS verify, debug flag, `is None`).
""")
    st.subheader("Run locally")
    st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")


{"🏠 Overview": page_overview, "🔍 PR Review": page_review, "💬 Codebase Assistant": page_codebase,
 "🧪 Model Lab": page_lab, "🕘 History": page_history, "ℹ️ About": page_about}[st.session_state.nav]()
