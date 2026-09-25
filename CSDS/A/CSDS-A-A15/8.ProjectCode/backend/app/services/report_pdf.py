import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import Inspection

SEVERITY_COLORS = {
    "low": colors.HexColor("#16a34a"),
    "medium": colors.HexColor("#d97706"),
    "high": colors.HexColor("#dc2626"),
}


def generate_inspection_pdf(inspection: Inspection, output_path: Path) -> Path:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], textColor=colors.HexColor("#111827")
    )
    heading_style = ParagraphStyle(
        "HeadingCustom", parent=styles["Heading2"], textColor=colors.HexColor("#1f2937")
    )
    body_style = ParagraphStyle("BodyCustom", parent=styles["BodyText"], leading=15)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
    )

    elements = []
    elements.append(Paragraph("VisionForge AI — Automated Inspection Report", title_style))
    elements.append(Spacer(1, 4))
    elements.append(
        Paragraph(
            f"Inspection #{inspection.id:05d} · {inspection.created_at.strftime('%d %b %Y, %H:%M')}",
            body_style,
        )
    )
    elements.append(Spacer(1, 16))

    severity_color = SEVERITY_COLORS.get(inspection.severity, colors.grey)
    summary_data = [
        ["Asset", inspection.asset_name],
        ["Detected Defect", inspection.display_name],
        ["Confidence", f"{inspection.confidence * 100:.1f}%"],
        ["Severity", inspection.severity.upper()],
    ]
    summary_table = Table(summary_data, colWidths=[4 * cm, 10 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (1, 3), (1, 3), severity_color),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 3), (1, 3), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    images_root = Path(inspection.image_path).parent.parent
    original_path = images_root / "uploads" / Path(inspection.image_path).name
    heatmap_path = images_root / "heatmaps" / Path(inspection.heatmap_path).name

    if original_path.exists() and heatmap_path.exists():
        elements.append(Paragraph("Original vs. Explainable AI Heatmap", heading_style))
        elements.append(Spacer(1, 6))
        img_table = Table(
            [[RLImage(str(original_path), width=7 * cm, height=7 * cm), RLImage(str(heatmap_path), width=7 * cm, height=7 * cm)]],
        )
        img_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        elements.append(img_table)
        elements.append(Spacer(1, 16))

    elements.append(Paragraph("Root Cause Analysis", heading_style))
    elements.append(Spacer(1, 6))
    for line in inspection.root_cause_text.split("\n"):
        if line.strip():
            elements.append(Paragraph(line, body_style))
            elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Corrective Actions", heading_style))
    elements.append(Spacer(1, 6))
    actions = json.loads(inspection.corrective_actions)
    for action in actions:
        elements.append(Paragraph(f"• {action}", body_style))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 24))
    elements.append(
        Paragraph(
            "Generated automatically by VisionForge AI. Predictions and root-cause suggestions "
            "are decision support only and should be validated by a qualified quality engineer.",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
        )
    )

    doc.build(elements)
    return output_path
