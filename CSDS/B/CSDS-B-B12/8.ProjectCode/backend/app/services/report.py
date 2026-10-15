"""Multilingual PDF report (English / Hindi / Telugu) built with ReportLab + Noto fonts (HarfBuzz shaping)."""
import io
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..config import FONTS_DIR
from ..db import as_utc

LANGS = {"en": "English", "hi": "Hindi", "te": "Telugu"}
FONTS = {"en": "NotoSans", "hi": "NotoSansDevanagari", "te": "NotoSansTelugu"}
for fam in set(FONTS.values()):
    pdfmetrics.registerFont(TTFont(fam, str(FONTS_DIR / f"{fam}-Regular.ttf")))
    pdfmetrics.registerFont(TTFont(f"{fam}-Bold", str(FONTS_DIR / f"{fam}-Bold.ttf")))
    pdfmetrics.registerFontFamily(fam, normal=fam, bold=f"{fam}-Bold")

LABELS = {
    "en": {
        "title": "Chest Imaging AI Screening Report", "patient": "Patient", "age_sex": "Age / Sex", "scan": "Scan",
        "date": "Date", "modality": "Modality", "result": "AI finding", "confidence": "Confidence", "severity": "Severity",
        "affected": "Affected lung area", "probs": "Probability per class", "images": "Lung mask and Grad-CAM heatmap",
        "summary": "Summary", "explanation": "What this means", "next": "Suggested next steps",
        "ai_missing": "The AI explanation could not be generated right now; the model results above are complete.",
        "disclaimer": "This report is produced by an AI screening aid. It is not a diagnosis. A qualified doctor must review the images and confirm any finding.",
        "xray": "Chest X-ray", "ct": "Chest CT",
    },
    "hi": {
        "title": "छाती इमेजिंग एआई स्क्रीनिंग रिपोर्ट", "patient": "मरीज़", "age_sex": "आयु / लिंग", "scan": "स्कैन",
        "date": "तारीख", "modality": "जांच का प्रकार", "result": "एआई निष्कर्ष", "confidence": "विश्वास स्तर", "severity": "गंभीरता",
        "affected": "प्रभावित फेफड़े का हिस्सा", "probs": "हर श्रेणी की संभावना", "images": "फेफड़े का मास्क और ग्रैड-कैम हीटमैप",
        "summary": "सारांश", "explanation": "इसका क्या अर्थ है", "next": "सुझाए गए अगले कदम",
        "ai_missing": "एआई व्याख्या अभी तैयार नहीं हो सकी; ऊपर दिए गए मॉडल परिणाम पूरे हैं।",
        "disclaimer": "यह रिपोर्ट एक एआई स्क्रीनिंग सहायक द्वारा बनाई गई है। यह निदान नहीं है। किसी योग्य डॉक्टर को छवियों की जांच करके निष्कर्ष की पुष्टि करनी चाहिए।",
        "xray": "छाती का एक्स-रे", "ct": "छाती का सीटी स्कैन",
    },
    "te": {
        "title": "ఛాతీ ఇమేజింగ్ ఏఐ స్క్రీనింగ్ నివేదిక", "patient": "రోగి", "age_sex": "వయస్సు / లింగం", "scan": "స్కాన్",
        "date": "తేదీ", "modality": "పరీక్ష రకం", "result": "ఏఐ ఫలితం", "confidence": "నమ్మకం స్థాయి", "severity": "తీవ్రత",
        "affected": "ప్రభావిత ఊపిరితిత్తుల భాగం", "probs": "ప్రతి వర్గం సంభావ్యత", "images": "ఊపిరితిత్తుల మాస్క్ మరియు గ్రాడ్-క్యామ్ హీట్‌మ్యాప్",
        "summary": "సారాంశం", "explanation": "దీని అర్థం ఏమిటి", "next": "సూచించిన తదుపరి చర్యలు",
        "ai_missing": "ఏఐ వివరణ ప్రస్తుతం తయారు కాలేదు; పైన ఉన్న మోడల్ ఫలితాలు పూర్తిగా ఉన్నాయి.",
        "disclaimer": "ఈ నివేదిక ఏఐ స్క్రీనింగ్ సహాయకం ద్వారా తయారైంది. ఇది రోగ నిర్ధారణ కాదు. అర్హత గల వైద్యుడు చిత్రాలను పరిశీలించి ఫలితాన్ని నిర్ధారించాలి.",
        "xray": "ఛాతీ ఎక్స్-రే", "ct": "ఛాతీ సీటీ స్కాన్",
    },
}

TERMS = {
    "hi": {"COVID-19": "कोविड-19", "Viral Pneumonia": "वायरल निमोनिया", "Lung Opacity": "फेफड़ों में धुंधलापन (ओपेसिटी)",
           "Tuberculosis": "क्षय रोग (टीबी)", "Normal": "सामान्य", "Adenocarcinoma": "एडेनोकार्सिनोमा",
           "Large-cell Carcinoma": "लार्ज-सेल कार्सिनोमा", "Squamous-cell Carcinoma": "स्क्वैमस-सेल कार्सिनोमा",
           "None": "कोई नहीं", "Mild": "हल्की", "Moderate": "मध्यम", "Severe": "गंभीर", "Male": "पुरुष", "Female": "महिला", "Other": "अन्य"},
    "te": {"COVID-19": "కోవిడ్-19", "Viral Pneumonia": "వైరల్ న్యుమోనియా", "Lung Opacity": "ఊపిరితిత్తుల అస్పష్టత (ఒపాసిటీ)",
           "Tuberculosis": "క్షయ వ్యాధి (టీబీ)", "Normal": "సాధారణం", "Adenocarcinoma": "అడెనోకార్సినోమా",
           "Large-cell Carcinoma": "లార్జ్-సెల్ కార్సినోమా", "Squamous-cell Carcinoma": "స్క్వామస్-సెల్ కార్సినోమా",
           "None": "లేదు", "Mild": "స్వల్పం", "Moderate": "మధ్యస్థం", "Severe": "తీవ్రం", "Male": "పురుషుడు", "Female": "స్త్రీ", "Other": "ఇతర"},
}


def term(word, lang):
    return TERMS.get(lang, {}).get(word, word)


def _mixed(text, lang):
    """Escape text and render Latin runs with the Latin font (Indic fonts lack most Latin glyphs)."""
    if lang == "en":
        return escape(str(text))

    def token(m):  # the shaper uses one font per word, so choose it per whitespace-separated token
        w = m.group(0)
        if re.search(r"[A-Za-z]", w) and not re.search(r"[ऀ-౿]", w):
            return f'<font name="NotoSans">{escape(w)}</font>'
        return escape(w)

    return re.sub(r"\S+", token, str(text))


def build_pdf(scan, patient_name, patient, ai, lang, images):
    L, font = LABELS[lang], FONTS[lang]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
                            title="PulmoVision report", author="PulmoVision")
    body = ParagraphStyle("b", fontName=font, fontSize=10, leading=15, shaping=1)
    h1 = ParagraphStyle("h1", parent=body, fontName=f"{font}-Bold", fontSize=16, leading=22, textColor=colors.HexColor("#0f4c81"))
    h2 = ParagraphStyle("h2", parent=body, fontName=f"{font}-Bold", fontSize=12, leading=18, spaceBefore=8, textColor=colors.HexColor("#0f4c81"))
    small = ParagraphStyle("s", parent=body, fontSize=8.5, leading=12, textColor=colors.HexColor("#555555"))
    P = lambda t, st=body: Paragraph(_mixed(t, lang), st)  # noqa: E731

    story = [Paragraph('<font name="NotoSans-Bold">PulmoVision</font>', h1), P(L["title"], h2), Spacer(1, 4)]
    info = [
        [P(L["patient"]), P(f"{patient_name} ({patient.code})"), P(L["age_sex"]), P(f"{patient.age} / {term(patient.sex, lang)}")],
        [P(L["scan"]), P(f"#{scan.id}"), P(L["date"]), P(as_utc(scan.created_at).astimezone().strftime("%d-%m-%Y %H:%M"))],
        [P(L["modality"]), P(L[scan.modality]), P(L["result"]), Paragraph(f"<b>{_mixed(term(scan.prediction, lang), lang)}</b>", body)],
        [P(L["confidence"]), P(f"{scan.confidence * 100:.1f}%"), P(L["severity"]), P(f"{term(scan.severity, lang)} ({L['affected']}: {scan.affected_pct:.1f}%)")],
    ]
    t = Table(info, colWidths=[30 * mm, 58 * mm, 30 * mm, 60 * mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d3e0")), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f9")),
                           ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef3f9")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [t, Spacer(1, 6), P(L["probs"], h2)]
    rows = [[P(term(c, lang)), P(f"{p * 100:.1f}%")] for c, p in sorted(scan.probabilities.items(), key=lambda kv: -kv[1])]
    pt = Table(rows, colWidths=[90 * mm, 30 * mm])
    pt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dde3ea"))]))
    story += [pt, P(L["images"], h2)]
    imgs = [Image(io.BytesIO(images[k]), width=80 * mm, height=80 * mm) for k in ("mask", "heatmap")]
    story += [Table([imgs], colWidths=[88 * mm, 88 * mm])]
    if ai:
        story += [P(L["summary"], h2), P(ai.get("summary", "")), P(L["explanation"], h2), P(ai.get("explanation", "")), P(L["next"], h2)]
        story += [Paragraph('<font name="NotoSans">&#8226;</font> ' + _mixed(s, lang), body) for s in ai.get("next_steps", [])]
    else:
        story += [Spacer(1, 6), P(L["ai_missing"], small)]
    story += [Spacer(1, 10), P(L["disclaimer"], small)]
    doc.build(story)
    return buf.getvalue()
