"""HTML (Jinja2) and PDF (ReportLab) report generation."""
import io
import json

from jinja2 import Template

from .owasp import severity_counts

SEV_COLOR = {"critical": "#b91c1c", "high": "#c2410c", "medium": "#a16207",
             "low": "#2563eb", "info": "#64748b"}

_HTML = Template("""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>APISentry Report - {{ target.name }}</title>
<style>
 body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;color:#0f172a;background:#f8fafc}
 .wrap{max-width:900px;margin:0 auto;padding:32px 20px}
 h1{margin:0 0 4px} .muted{color:#64748b}
 .score{display:flex;gap:24px;align-items:center;background:#fff;border:1px solid #e2e8f0;
   border-radius:14px;padding:24px;margin:20px 0}
 .big{font-size:56px;font-weight:800;line-height:1}
 .grade{font-size:40px;font-weight:800;padding:6px 18px;border-radius:12px;color:#fff}
 .counts span{display:inline-block;margin-right:14px;font-weight:600}
 .f{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px 18px;margin:12px 0}
 .tag{display:inline-block;color:#fff;font-size:12px;font-weight:700;padding:2px 8px;
   border-radius:999px;text-transform:uppercase}
 pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto;font-size:12px}
 code{background:#f1f5f9;padding:1px 5px;border-radius:4px}
 .owasp{color:#475569;font-size:13px}
 table{border-collapse:collapse;width:100%;font-size:14px}
 td,th{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left}
</style></head><body><div class="wrap">
 <h1>APISentry Security Report</h1>
 <div class="muted">{{ target.name }} &middot; {{ target.base_url }} &middot; scan #{{ scan.id }} &middot; {{ generated }}</div>
 <div class="score">
   <div><div class="big">{{ scan.score }}<span style="font-size:22px">/100</span></div>
     <div class="muted">Security score</div></div>
   <div class="grade" style="background:{{ grade_color }}">{{ scan.grade }}</div>
   <div class="counts">
     {% for sev, n in counts.items() %}{% if n %}
       <span style="color:{{ sev_color[sev] }}">{{ n }} {{ sev }}</span>
     {% endif %}{% endfor %}
   </div>
 </div>

 <h2>Findings ({{ findings|length }})</h2>
 {% for f in findings %}
 <div class="f">
   <div><span class="tag" style="background:{{ sev_color[f.severity] }}">{{ f.severity }}</span>
     <strong>&nbsp;{{ f.title }}</strong></div>
   <div class="owasp">{{ f.owasp_id }} - {{ f.owasp_name }}
     {% if f.endpoint %}&middot; <code>{{ f.endpoint }}</code>{% endif %}
     &middot; source: {{ f.source }}</div>
   <p>{{ f.description }}</p>
   {% if f.curl %}<div class="muted">Reproduce:</div><pre>{{ f.curl }}</pre>{% endif %}
   <div class="muted">Recommendation:</div><p>{{ f.recommendation }}</p>
   {% if f.fix_snippet %}<pre>{{ f.fix_snippet }}</pre>{% endif %}
 </div>
 {% else %}<p>No findings.</p>{% endfor %}

 {% if ai_tests %}
 <h2>AI-generated business-logic tests ({{ ai_tests|length }})</h2>
 <table><tr><th>Test</th><th>Endpoint</th><th>Result</th><th>Detail</th></tr>
 {% for t in ai_tests %}<tr><td>{{ t.name }}</td><td><code>{{ t.endpoint }}</code></td>
   <td><strong style="color:{{ '#b91c1c' if t.result=='vulnerable' else '#166534' }}">
     {{ t.result }}</strong></td><td>{{ t.detail }}</td></tr>{% endfor %}
 </table>
 <p class="muted">Generator: {{ ai_generator }}</p>
 {% endif %}
</div></body></html>""")

GRADE_COLOR = {"A": "#166534", "B": "#15803d", "C": "#a16207", "D": "#c2410c", "F": "#b91c1c"}


def render_html(target, scan, findings: list[dict], ai_tests: list[dict],
                ai_generator: str, generated: str) -> str:
    return _HTML.render(
        target=target, scan=scan, findings=findings, ai_tests=ai_tests,
        ai_generator=ai_generator, generated=generated,
        counts=severity_counts(findings), sev_color=SEV_COLOR,
        grade_color=GRADE_COLOR.get(scan.grade, "#64748b"),
    )


def render_pdf(target, scan, findings: list[dict], ai_tests: list[dict],
               generated: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=10)
    story = []

    story.append(Paragraph("APISentry Security Report", styles["Title"]))
    story.append(Paragraph(
        f"{target.name} &middot; {target.base_url} &middot; scan #{scan.id} &middot; {generated}",
        styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Security score: {scan.score}/100 (grade {scan.grade})</b>", styles["Heading2"]))

    counts = severity_counts(findings)
    story.append(Paragraph(
        " &nbsp; ".join(f"{k}: {v}" for k, v in counts.items() if v) or "No findings",
        styles["Normal"]))
    story.append(Spacer(1, 10))

    rows = [["Severity", "OWASP", "Title", "Endpoint"]]
    for f in findings:
        rows.append([f["severity"], f["owasp_id"],
                     Paragraph(f["title"], small), Paragraph(f.get("endpoint", ""), small)])
    if len(rows) > 1:
        table = Table(rows, colWidths=[22 * mm, 18 * mm, 80 * mm, 45 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Detailed findings", styles["Heading2"]))
    for f in findings:
        story.append(Paragraph(
            f"<b>[{f['severity'].upper()}] {f['title']}</b> "
            f"({f['owasp_id']} {f['owasp_name']})", styles["Normal"]))
        story.append(Paragraph(f["description"], small))
        story.append(Paragraph(f"<b>Fix:</b> {f['recommendation']}", small))
        story.append(Spacer(1, 6))

    if ai_tests:
        story.append(Spacer(1, 8))
        story.append(Paragraph("AI-generated business-logic tests", styles["Heading2"]))
        ai_rows = [["Test", "Result"]]
        for t in ai_tests:
            ai_rows.append([Paragraph(t["name"], small), t["result"]])
        ai_table = Table(ai_rows, colWidths=[120 * mm, 40 * mm])
        ai_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(ai_table)

    doc.build(story)
    return buf.getvalue()
