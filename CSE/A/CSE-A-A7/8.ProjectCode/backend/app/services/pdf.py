"""Triage summary PDF for one patient."""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .features import PRIORITY_NAMES, VITAL_LABELS


def build_summary(p) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"ATHENA triage summary - patient {p.id}")
    ss = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=ss["Title"], fontSize=20, alignment=0)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, spaceBefore=10)
    body = ss["BodyText"]
    el = [Paragraph("ATHENA - Triage summary", h),
          Paragraph(f"Patient #{p.id} - {p.name} - recorded {p.created_at:%Y-%m-%d %H:%M} UTC", body), Spacer(1, 6)]

    el.append(Paragraph(f"Priority {p.priority} - {PRIORITY_NAMES[p.priority]} ({p.risk_level} risk)", h2))
    line = f"Model suggestion: priority {p.model_priority}, confidence {p.confidence * 100:.0f}%."
    if p.priority != p.model_priority:
        line += " A clinician changed the priority (see override log)."
    el.append(Paragraph(line, body))

    el.append(Paragraph("Vitals", h2))
    rows = [[VITAL_LABELS.get(k, k), str(v)] for k, v in p.vitals.items() if k in VITAL_LABELS or k == "arrival_mode"]
    t = Table(rows, colWidths=[60 * mm, 60 * mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    el.append(t)

    rep = p.report or {}
    for title, key in (("Symptoms", "symptoms"), ("Findings", "findings"), ("History", "history")):
        items = rep.get(key) or []
        if items:
            el.append(Paragraph(title, h2))
            el.append(Paragraph("; ".join(f"{i['label']} (page {i['page']})" for i in items), body))
    if rep.get("labs"):
        el.append(Paragraph("Lab values", h2))
        el.append(Paragraph("; ".join(f"{l['name']} {l['value']:g} {l['unit']}{' (abnormal)' if l['abnormal'] else ''} - page {l['page']}"
                                      for l in rep["labs"]), body))

    el.append(Paragraph("Why this priority (SHAP, strongest first)", h2))
    rows = [["Factor", "Value", "Effect"]] + [[s["label"], s["value"], f"{s['impact']:+.2f} {s['direction']}"] for s in p.shap]
    t = Table(rows, colWidths=[60 * mm, 35 * mm, 60 * mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                           ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    el.append(t)

    if p.overrides:
        el.append(Paragraph("Clinician overrides", h2))
        for o in p.overrides:
            el.append(Paragraph(f"{o.created_at:%Y-%m-%d %H:%M} - {o.user_name}: {o.action}, priority {o.old_priority} to "
                                f"{o.new_priority}. Reason: {o.reason or 'none given'}", body))
    el.append(Spacer(1, 10))
    el.append(Paragraph("Decision support only. The treating clinician makes the final triage decision.",
                        ParagraphStyle("f", parent=body, fontSize=8, textColor=colors.grey)))
    doc.build(el)
    return buf.getvalue()
