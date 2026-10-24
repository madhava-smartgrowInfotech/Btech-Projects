"""Report intake: read a scanned report (PDF or image) and return structured clinical fields.

PDF pages use their text layer; images and image-only PDF pages go through a local OCR engine
(RapidOCR, ONNX, no model download at run time). The text is then parsed with a clinical lexicon
that handles negation ("denies chest pain") and lab reference ranges. Every item keeps its page.
"""
import io
import re
import time
from functools import lru_cache

from .features import FLAGS, REPORT_FLAGS

# flag -> regex of phrases
LEXICON = {
    "chest_pain": r"chest (pain|pressure|tightness)|angina",
    "dyspnea": r"shortness of breath|dyspn(o)?ea|breathless(ness)?|difficulty breathing|\bsob\b",
    "altered_mental": r"confus(ed|ion)|altered (mental|consciousness|sensorium)|disorient(ed|ation)|drowsy|lethargic|unresponsive",
    "syncope": r"syncop(e|al)|passed out|loss of consciousness|collapsed|fainted",
    "fever": r"fever|febrile|pyrexia|chills|rigors",
    "abd_pain": r"abdominal pain|abdominal tenderness|epigastric pain|right lower quadrant pain|belly pain",
    "bleeding": r"bleeding|haemorrhage|hemorrhage|haematemesis|hematemesis|melena|haematuria|hematuria|blood loss",
    "stroke_signs": r"facial droop|slurred speech|speech (difficulty|change)|(left|right|one)[- ]sided weakness|hemiparesis|focal (weakness|deficit)|arm weakness",
    "severe_headache": r"(severe|worst|sudden)( \w+)? headache|thunderclap",
    "vomiting": r"vomiting|nausea and vomiting|emesis",
    "trauma": r"trauma|fall from|\bfell\b|twisted|sprain(ed)?|road traffic|motor vehicle|assault|laceration|head injury|injury|crush injury",
    "st_elevation": r"st[- ]?(segment )?elevation|stemi",
    "infiltrate": r"infiltrate|consolidation|pneumonia|opacity|pleural effusion",
    "fracture": r"fracture|fractured",
    "free_fluid": r"free (abdominal |intraperitoneal )?fluid|haemoperitoneum|hemoperitoneum",
    "ct_hemorrhage": r"intracranial (haemorrhage|hemorrhage|bleed)|subdural|subarachnoid|epidural (haematoma|hematoma)|cerebral bleed",
    "diabetes": r"diabet(es|ic)|\bt2dm\b|\bt1dm\b|\bdm2\b",
    "hypertension": r"hypertension|hypertensive|high blood pressure|\bhtn\b",
    "cardiac_hx": r"coronary artery disease|\bcad\b|myocardial infarction|prior mi|heart failure|atrial fibrillation|cardiac (disease|history)|stent|cabg",
    "copd": r"\bcopd\b|asthma|chronic obstructive|emphysema",
    "prior_stroke": r"prior (stroke|cva)|previous (stroke|cva)|history of (stroke|cva)|\btia\b",
    "anticoagulant": r"warfarin|apixaban|rivaroxaban|dabigatran|anticoagula(nt|tion)|heparin|enoxaparin|clopidogrel",
}
NEGATION = re.compile(r"\b(no|denies|denied|without|negative for|absence of|not|nil|free of|ruled out)\b[^.;\n]{0,45}$", re.I)
HISTORY_CUE = re.compile(r"(history|hx|past medical|pmh|known|background|chronic|on treatment)", re.I)

# lab name regex, flag, test(value) -> abnormal, unit hint, reference text
LABS = [
    ("Troponin", r"troponin(?: ?[it])?", "lab_troponin_high", lambda v: v > 0.04, "ng/mL", "<0.04"),
    ("Lactate", r"lactate", "lab_lactate_high", lambda v: v > 2.0, "mmol/L", "<2.0"),
    ("WBC", r"wbc|white (?:blood )?cell(?: count)?", "lab_wbc_high", lambda v: v > 11.0, "x10^9/L", "4-11"),
    ("Glucose", r"glucose|blood sugar|rbs|fbs", "lab_glucose_abn", lambda v: v < 70 or v > 250, "mg/dL", "70-250"),
    ("Creatinine", r"creatinine", "lab_creatinine_high", lambda v: v > 1.3, "mg/dL", "0.6-1.3"),
    ("Haemoglobin", r"h(?:a)?emoglobin|\bhgb\b|\bhb\b", "lab_hgb_low", lambda v: v < 10.0, "g/dL", ">10"),
]
LAB_RE = [(n, re.compile(rf"\b(?:{p})\b\s*[:=\-]?\s*(-?\d+(?:\.\d+)?)", re.I), f, t, u, ref) for n, p, f, t, u, ref in LABS]
# OCR often drops spaces ("ofbreath"), so literal spaces in phrases match zero or more whitespace
COMPILED = {k: re.compile(v.replace(" ", r"\s*"), re.I) for k, v in LEXICON.items()}


@lru_cache(maxsize=1)
def _ocr():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


def _ocr_image(img) -> str:
    import numpy as np
    img = img.convert("RGB")
    if max(img.size) < 2000:
        img = img.resize((int(img.width * 1.6), int(img.height * 1.6)))
    arr = np.array(img)
    result, _ = _ocr()(arr)
    if not result:
        return ""
    # result rows: [box, text, score]; sort into reading order by y then x
    rows = sorted(result, key=lambda r: (round(r[0][0][1] / 14), r[0][0][0]))
    lines, last_y = [], None
    for box, text, _score in rows:
        y = round(box[0][1] / 14)
        if last_y is not None and y == last_y:
            lines[-1] += " " + text
        else:
            lines.append(text)
        last_y = y
    return "\n".join(lines)


def read_pages(data: bytes, filename: str) -> list[dict]:
    """Return [{page, text, method}] for a PDF or an image upload."""
    name = (filename or "").lower()
    if name.endswith(".pdf") or data[:4] == b"%PDF":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            method = "pdf-text"
            if len(text) < 20:
                imgs = list(page.images)
                if imgs:
                    from PIL import Image
                    text = _ocr_image(Image.open(io.BytesIO(imgs[0].data)))
                    method = "ocr"
            pages.append({"page": i, "text": text, "method": method})
        return pages
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as exc:
        raise ValueError("Unsupported file. Upload a PDF, PNG or JPG scan.") from exc
    return [{"page": 1, "text": _ocr_image(img), "method": "ocr"}]


def _unwrap(text: str) -> str:
    """Join lines that were wrapped mid-sentence (long line without closing punctuation)."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if out and len(out[-1]) >= 45 and not re.search(r"[.;:]$", out[-1]) and line:
            out[-1] += " " + line
        else:
            out.append(line)
    return "\n".join(out)


def _sentences(text: str):
    for line in _unwrap(text).splitlines():
        for part in re.split(r"(?<=[.;])\s+", line):
            if part.strip():
                yield part.strip()


def parse(pages: list[dict]) -> dict:
    items = {}   # flag -> item
    labs = []
    for pg in pages:
        for sent in _sentences(pg["text"]):
            for name, rx, flag, test, unit, ref in LAB_RE:
                for m in rx.finditer(sent):
                    val = float(m.group(1))
                    labs.append({"name": name, "value": val, "unit": unit, "reference": ref,
                                 "abnormal": bool(test(val)), "page": pg["page"], "flag": flag})
            for flag, rx in COMPILED.items():
                if flag in items:
                    continue
                m = None
                for cand in rx.finditer(sent):
                    # a brain bleed is the finding "ct_hemorrhage", not the symptom "bleeding"
                    if flag == "bleeding" and re.search(r"(intracranial|subarachnoid|cerebral|subdural)\s*$", sent[: cand.start()], re.I):
                        continue
                    m = cand
                    break
                if not m:
                    continue
                if NEGATION.search(sent[: m.start()]):
                    continue
                cat = REPORT_FLAGS[flag][0]
                items[flag] = {"flag": flag, "text": m.group(0), "label": REPORT_FLAGS[flag][1],
                               "category": cat, "page": pg["page"], "context": sent[:160]}
    # lab flags: keep the first abnormal reading per lab, drop duplicate rows of the same lab/page/value
    seen, uniq = set(), []
    for lab in labs:
        key = (lab["name"], lab["value"], lab["page"])
        if key not in seen:
            seen.add(key)
            uniq.append(lab)
    flags = {f: 0 for f in FLAGS}
    for f in items:
        flags[f] = 1
    for lab in uniq:
        if lab["abnormal"]:
            flags[lab["flag"]] = 1
    return {
        "symptoms": [i for i in items.values() if i["category"] == "symptom"],
        "findings": [i for i in items.values() if i["category"] == "finding"],
        "history": [i for i in items.values() if i["category"] == "history"],
        "labs": uniq,
        "flags": flags,
    }


def extract_report(data: bytes, filename: str) -> dict:
    t0 = time.time()
    pages = read_pages(data, filename)
    parsed = parse(pages)
    parsed["pages"] = [{"page": p["page"], "method": p["method"], "chars": len(p["text"])} for p in pages]
    parsed["text"] = "\n\n".join(f"[page {p['page']}]\n{p['text']}" for p in pages)
    parsed["seconds"] = round(time.time() - t0, 3)
    if not parsed["text"].strip():
        raise ValueError("No readable text found in the upload. Try a clearer scan.")
    return parsed
