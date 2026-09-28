"""PDF screening report (ReportLab)."""
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .heart import LABELS, display

STAGE_COLORS = {"Low": "#15803d", "Moderate": "#ca8a04", "High": "#ea580c", "Very high": "#b91c1c"}
DISCLAIMER = ("RetinaGuard is a clinical decision-support tool. All AI results are an aid for a qualified "
              "professional and are not a final diagnosis. Confirm findings with a full clinical examination.")


def _img(path: Path, size_mm: float):
    return Image(str(path), width=size_mm * mm, height=size_mm * mm) if path.exists() else Paragraph("-", getSampleStyleSheet()["Normal"])


def _grid(cells, captions, size_mm):
    st = ParagraphStyle("cap", fontSize=7.5, alignment=1, textColor=colors.HexColor("#475569"))
    t = Table([cells, [Paragraph(c, st) for c in captions]], colWidths=[(size_mm + 3) * mm] * len(cells))
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def build_report(s, img_dir: Path) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=10 * mm,
                            bottomMargin=10 * mm, title=f"RetinaGuard screening report #{s.id}")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=18, textColor=colors.HexColor("#0f766e"), spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, textColor=colors.HexColor("#0f172a"), spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("b", parent=ss["Normal"], fontSize=9.5, leading=13)
    small = ParagraphStyle("s", parent=body, fontSize=8, textColor=colors.HexColor("#64748b"))
    p = s.patient
    rf = s.retina_findings or {}
    story = [
        Paragraph("RetinaGuard - Screening Report", h1),
        Paragraph(f"Hypertensive retinopathy and cardiovascular risk screening &nbsp;|&nbsp; Report #{s.id}", small),
        Spacer(1, 6),
    ]
    info = [
        ["Patient", f"{p.name} ({p.code})", "Date", s.created_at.strftime("%d %b %Y %H:%M UTC")],
        ["Age / Sex", f"{p.age} / {p.sex}", "Eye", s.eye or "-"],
        ["Screened by", f"{s.user.name} ({s.user.role})", "Image quality",
         "Passed" if (s.quality or {}).get("passed") else "Check: " + "; ".join((s.quality or {}).get("issues", []))],
    ]
    t = Table(info, colWidths=[28 * mm, 62 * mm, 28 * mm, 62 * mm])
    t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
                           ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#64748b")),
                           ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [t, Spacer(1, 3), Paragraph(DISCLAIMER, small)]

    if s.stage:
        c = colors.HexColor(STAGE_COLORS.get(s.stage["stage"], "#334155"))
        st = Table([[Paragraph(f"<b>Overall risk stage: {s.stage['stage'].upper()}</b>",
                               ParagraphStyle("st", fontSize=14, textColor=colors.white, leading=18))]],
                   colWidths=[180 * mm])
        st.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), c), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
        story += [Spacer(1, 8), st]
        for r in s.stage.get("reasons", []):
            story.append(Paragraph("- " + r, body))

    story.append(Paragraph("Retinal findings (LeNet on Haar wavelet features)", h2))
    if rf:
        story.append(Paragraph(
            f"<b>{rf.get('label')}</b> - probability {rf.get('probability', 0):.0%} "
            f"(decision threshold {rf.get('threshold', 0.5):.0%}). Vessel density {rf.get('vessels', {}).get('vessel_density', 0):.1%}, "
            f"mean vessel width {rf.get('vessels', {}).get('mean_vessel_width_px', 0):.1f} px (Frangi vessel map).", body))
    story.append(Spacer(1, 4))
    story.append(_grid([_img(img_dir / n, 33) for n in ("original.png", "clahe.png", "heatmap.png", "vessels.png")],
                       ["Fundus image", "Green channel + CLAHE", "Grad-CAM heatmap", "Frangi vessel map"], 33))
    story.append(Spacer(1, 4))
    story.append(_grid([_img(img_dir / f"2_{b}.png", 22) for b in ("LL", "LH", "HL", "HH")]
                       + [_img(img_dir / f"1_{b}.png", 22) for b in ("LH", "HL")],
                       ["Level-2 LL", "Level-2 LH", "Level-2 HL", "Level-2 HH", "Level-1 LH", "Level-1 HL"], 22))

    story.append(Paragraph("Clinical heart-disease risk (Random Forest + SHAP)", h2))
    if s.heart_prob is not None:
        story.append(Paragraph(f"<b>Heart-disease probability {s.heart_prob:.0%}</b>. Top contributing factors:", body))
        rows = [["Factor", "Value", "Effect", "SHAP impact"]]
        for f in s.heart_factors or []:
            rows.append([f["label"], display(f["feature"], f["value"]), f["direction"], f"{f['impact']:+.3f}"])
        ft = Table(rows, colWidths=[75 * mm, 30 * mm, 40 * mm, 35 * mm])
        ft.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 8.5), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1"))]))
        story.append(ft)
        if s.clinical:
            vals = ", ".join(f"{LABELS.get(k, k)}: {display(k, v)}" for k, v in s.clinical.items())
            story.append(Spacer(1, 3))
            story.append(Paragraph("Inputs - " + vals, small))
    else:
        story.append(Paragraph("Clinical data not entered.", body))

    if s.stage:
        story.append(Paragraph("Recommendations", h2))
        for r in s.stage.get("recommendations", []):
            story.append(Paragraph("- " + r, body))
    doc.build(story)
    return buf.getvalue()
