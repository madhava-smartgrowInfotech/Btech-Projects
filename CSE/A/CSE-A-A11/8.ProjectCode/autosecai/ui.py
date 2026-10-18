"""Reusable Streamlit UI components: styling, banners, charts, finding cards."""
from __future__ import annotations

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .knowledge import SEVERITY_ORDER
from .metrics import FEATURE_LABEL

SEV_COLOR = {"critical": "#7c3aed", "high": "#dc2626", "medium": "#f59e0b", "low": "#ca8a04", "info": "#3b82f6"}
SEV_ICON = {"critical": "🟣", "high": "🔴", "medium": "🟠", "low": "🟡", "info": "🔵"}
VERDICT = {
    "BLOCK": dict(color="#dc2626", bg="#fef2f2", icon="🛑", title="Merge blocked",
                  sub="High-impact security issues were introduced by this change."),
    "REQUEST_CHANGES": dict(color="#d97706", bg="#fffbeb", icon="⚠️", title="Changes requested",
                            sub="Issues worth fixing before merge were found."),
    "APPROVE": dict(color="#059669", bg="#ecfdf5", icon="✅", title="Safe to merge",
                    sub="No blocking issues were found in the changed code."),
}
PLOT = dict(template="plotly_white", font=dict(family="Inter, Segoe UI, sans-serif", size=13),
            margin=dict(l=10, r=10, t=40, b=10))

CSS = """
<style>
.block-container {padding-top: 1.6rem; max-width: 1280px;}
[data-testid="stSidebar"] {background: #0f172a;}
[data-testid="stSidebar"] * {color: #e2e8f0;}
[data-testid="stSidebar"] .stRadio label p {font-size: 0.95rem;}
[data-testid="stSidebar"] hr {border-color: #1e293b;}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {color: #111827 !important;}
.brand {display:flex; align-items:center; gap:.6rem; margin:.2rem 0 1rem;}
.brand .logo {width:38px; height:38px; border-radius:10px; background:linear-gradient(135deg,#6366f1,#22d3ee);
   display:flex; align-items:center; justify-content:center; font-size:1.3rem;}
.brand b {font-size:1.15rem; color:#fff;} .brand span {font-size:.72rem; color:#94a3b8; display:block; margin-top:-2px;}
.hero {background:linear-gradient(135deg,#312e81 0%,#4f46e5 55%,#0ea5e9 100%); color:#fff; padding:2rem 2.2rem; border-radius:18px;
   margin-bottom:1.2rem;}
.hero h1 {margin:0 0 .3rem; font-size:2.1rem; color:#fff;} .hero p {margin:0; opacity:.92; font-size:1.02rem; max-width:820px;}
.card {background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:1rem 1.15rem; height:100%;
   box-shadow:0 1px 2px rgba(16,24,40,.04);}
.card h4 {margin:.1rem 0 .35rem; font-size:1rem;} .card p {margin:0; color:#4b5563; font-size:.9rem; line-height:1.45;}
.kpi {background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:.85rem 1rem; box-shadow:0 1px 2px rgba(16,24,40,.04);}
.kpi .v {font-size:1.7rem; font-weight:700; line-height:1.15;} .kpi .l {font-size:.78rem; color:#6b7280; text-transform:uppercase; letter-spacing:.04em;}
.verdict {border-radius:16px; padding:1.1rem 1.4rem; display:flex; gap:1rem; align-items:center; border:1.5px solid;}
.verdict .t {font-size:1.35rem; font-weight:700;} .verdict .s {color:#374151; font-size:.95rem;}
.chip {display:inline-block; padding:.12rem .55rem; border-radius:999px; font-size:.74rem; font-weight:600; margin-right:.3rem;
   background:#eef2ff; color:#4338ca; border:1px solid #c7d2fe;}
.chip.sev {color:#fff; border:none;}
.chip.gray {background:#f3f4f6; color:#374151; border-color:#e5e7eb;}
.chip.green {background:#ecfdf5; color:#047857; border-color:#a7f3d0;}
.chip.warn {background:#fffbeb; color:#b45309; border-color:#fde68a;}
.flow {display:flex; flex-wrap:wrap; gap:.35rem; align-items:center; margin:.3rem 0 .6rem;}
.flow .n {background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:.3rem .6rem; font-size:.82rem;}
.flow .a {color:#94a3b8;}
.pipe {display:flex; flex-wrap:wrap; gap:.5rem; align-items:stretch;}
.pipe .st {flex:1 1 130px; background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:.7rem .8rem; position:relative;}
.pipe .st b {display:block; font-size:.86rem;} .pipe .st span {font-size:.76rem; color:#6b7280; line-height:1.3; display:block; margin-top:.15rem;}
.pipe .st i {font-style:normal; position:absolute; top:-9px; left:10px; background:#4f46e5; color:#fff; font-size:.68rem; padding:0 .45rem; border-radius:99px;}
.trace {border-left:3px solid #6366f1; padding:.4rem .9rem; margin:.4rem 0 .6rem; background:#fff; border-radius:0 10px 10px 0; border-top:1px solid #eef; border-bottom:1px solid #eef;}
.trace b {font-size:.93rem;} .trace .r {color:#6b7280; font-size:.8rem;} .trace .d {font-size:.86rem; margin-top:.15rem;}
.hit {background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:.6rem .9rem; margin:.4rem 0;}
.small {color:#6b7280; font-size:.82rem;}
div[data-testid="stExpander"] {background:#fff; border-radius:12px; border:1px solid #e5e7eb;}
.stTabs [data-baseweb="tab"] {font-weight:600;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x))


def kpi(col, label, value, color="#111827", help_=""):
    col.markdown(f'<div class="kpi" title="{esc(help_)}"><div class="v" style="color:{color}">{esc(value)}</div>'
                 f'<div class="l">{esc(label)}</div></div>', unsafe_allow_html=True)


def chip(text, kind=""):
    return f'<span class="chip {kind}">{esc(text)}</span>'


def sev_chip(sev):
    return f'<span class="chip sev" style="background:{SEV_COLOR[sev]}">{esc(sev.upper())}</span>'


def verdict_banner(r):
    v = VERDICT[r["verdict"]]
    st.markdown(
        f'<div class="verdict" style="background:{v["bg"]}; border-color:{v["color"]}">'
        f'<div style="font-size:2.2rem">{v["icon"]}</div><div><div class="t" style="color:{v["color"]}">{v["title"]}</div>'
        f'<div class="s">{esc(r["summary"])}</div></div></div>', unsafe_allow_html=True)


def gauge(score, title="Risk score"):
    color = "#059669" if score < 30 else "#d97706" if score < 70 else "#dc2626"
    fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title=dict(text=title, font=dict(size=14)),
                                 number=dict(font=dict(size=38, color=color)),
                                 gauge=dict(axis=dict(range=[0, 100], tickwidth=0), bar=dict(color=color, thickness=.28),
                                            bgcolor="#f3f4f6", borderwidth=0,
                                            steps=[dict(range=[0, 30], color="#d1fae5"), dict(range=[30, 70], color="#fef3c7"),
                                                   dict(range=[70, 100], color="#fee2e2")])))
    fig.update_layout(height=210, margin=dict(l=20, r=20, t=40, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def donut(by_sev: dict):
    labels = [k for k in SEV_COLOR if by_sev.get(k)]
    fig = go.Figure(go.Pie(labels=[l.title() for l in labels], values=[by_sev[l] for l in labels], hole=.62,
                           marker=dict(colors=[SEV_COLOR[l] for l in labels]), textinfo="value", sort=False))
    fig.update_layout(height=230, showlegend=True, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="v"),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def hbar(d: dict, title: str, color="#6366f1", top=8):
    items = sorted(d.items(), key=lambda kv: kv[1])[-top:]
    fig = go.Figure(go.Bar(x=[v for _, v in items], y=[k for k, _ in items], orientation="h", marker_color=color))
    fig.update_layout(**PLOT, title=dict(text=title, font=dict(size=14)), height=max(180, 34 * len(items) + 70))
    return fig


def radar(metrics: dict, safe: dict):
    keys = list(FEATURE_LABEL)
    labels = [FEATURE_LABEL[k].split(" ")[0] + " " + " ".join(FEATURE_LABEL[k].split(" ")[1:3]) for k in keys]
    vals = [metrics[k] / (max(metrics[k], safe.get(k, 0), 1)) for k in keys]
    sv = [safe.get(k, 0) / (max(metrics[k], safe.get(k, 0), 1)) for k in keys]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=sv + sv[:1], theta=labels + labels[:1], name="Typical safe function", fill="toself",
                                  line=dict(color="#10b981"), opacity=.5))
    fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=labels + labels[:1], name="This function", fill="toself",
                                  line=dict(color="#dc2626"), opacity=.55))
    fig.update_layout(height=380, polar=dict(radialaxis=dict(visible=False, range=[0, 1])), margin=dict(l=40, r=40, t=20, b=20),
                      legend=dict(orientation="h", y=-.1), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def pipeline_html():
    steps = [("Ingestion", "Parses the PR: files, hunks, changed lines"),
             ("Static Analysis", "AST + taint tracking for Python, regex rules for JS/PHP/Java"),
             ("ML Risk", "14 source-code metrics -> Random Forest (base paper)"),
             ("Security Reasoner", "Source→sink flow, impact, CWE/OWASP, ML corroboration"),
             ("Remediation", "Safe patches, verified by re-scanning"),
             ("Quality Reviewer", "Complexity, nesting, size, error handling"),
             ("Judge", "De-dupes, scores risk, verdict, PR comment")]
    return '<div class="pipe">' + "".join(
        f'<div class="st"><i>{i + 1}</i><b>{esc(n)}</b><span>{esc(d)}</span></div>' for i, (n, d) in enumerate(steps)) + "</div>"


def finding_card(f: dict, key: str):
    icon = SEV_ICON[f["severity"]]
    loc = f"{f['file']}:{f['line']}"
    tag = "" if f["in_diff"] else "  · _pre-existing_"
    with st.expander(f"{icon} **{f['title']}** · `{loc}`{tag}"):
        chips = sev_chip(f["severity"]) + chip(f"{f['confidence']} confidence", "gray")
        if f["cwe"]:
            chips += chip(f["cwe"])
        if f["owasp"]:
            chips += chip(f["owasp"], "gray")
        if f["function"]:
            chips += chip(f"in {f['function']}()", "gray")
        chips += chip({"static": "AST/taint", "regex": "pattern", "ml": "ML model"}.get(f.get("detector", ""), "rule"), "gray")
        if f.get("ml") is not None and f["ml"] >= .5:
            chips += chip(f"ML risk {f['ml']:.0%}", "warn")
        if not f["in_diff"]:
            chips += chip("pre-existing", "gray")
        st.markdown(chips, unsafe_allow_html=True)
        if f["snippet"]:
            st.code(f["snippet"], language="python" if f["file"].endswith(".py") else None)
        st.markdown(f"**What is wrong.** {f['explanation']}")
        if f["llm"]:
            st.caption("Explanation written by the LLM agent.")
        if f["flow"]:
            st.markdown('<div class="flow">' + '<span class="a">→</span>'.join(f'<span class="n">{esc(s)}</span>' for s in f["flow"])
                        + "</div>", unsafe_allow_html=True)
        if f["impact"]:
            st.markdown(f"**Impact.** {f['impact']}")
        if f["exploit"] and f["exploit"] != "n/a" and f["exploit"] != "n/a (latent)":
            st.markdown(f"**Example attack.** `{f['exploit']}`")
        if f["corroboration"]:
            st.info(f["corroboration"], icon="🤖")
        st.markdown(f"**How to fix.** {f['remediation']}")
        if f["patch"]:
            badge = chip("verified: re-scan clean", "green") if f["fix_verified"] else chip("review manually", "warn")
            st.markdown("**Suggested patch** " + badge, unsafe_allow_html=True)
            st.code(f["patch"], language="diff")
            if f["fix_note"]:
                st.caption(f["fix_note"])
        elif f["safe_example"]:
            st.markdown("**Safe pattern**")
            st.code(f["safe_example"], language="python")


def findings_frame(findings: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([dict(severity=f["severity"], title=f["title"], file=f["file"], line=f["line"], cwe=f["cwe"],
                              confidence=f["confidence"], in_diff=f["in_diff"], category=f["category"]) for f in findings])


def sort_findings(fl: list[dict]) -> list[dict]:
    return sorted(fl, key=lambda f: (not f["in_diff"], -SEVERITY_ORDER[f["severity"]], f["file"], f["line"]))
