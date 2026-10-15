import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..auth import current_user, decrypt_text, require_role
from ..db import AuditLog, ChatMessage, Patient, Scan, SessionLocal, User, audit, iso
from ..services import gemini, storage
from ..services.pipeline import RejectedImage, engine
from ..services.report import LANGS, build_pdf

router = APIRouter(prefix="/api", tags=["scans"])
MAX_UPLOAD = 25 * 1024 * 1024
IMAGE_KINDS = ("original", "resized", "denoised", "enhanced", "mask", "heatmap")
DISCLAIMER = "AI screening aid for qualified clinicians - not a diagnosis."

SYSTEM = (
    "You are PulmoVision's clinical assistant, supporting radiologists and physicians who review AI chest-imaging screening results. "
    "Explain findings clearly, suggest reasonable next steps (confirmatory tests, referrals, follow-up) and note limitations of the AI. "
    "Never state a definitive diagnosis or prescribe medication doses; always say a qualified clinician must confirm. "
    "Keep answers under 180 words unless asked for more."
)


def scan_out(s: Scan, patient_name=None):
    return {
        "id": s.id, "patient_id": s.patient_id, "patient_code": s.patient.code, "patient_name": patient_name,
        "filename": s.filename, "modality": s.modality, "modality_score": s.modality_score,
        "prediction": s.prediction, "confidence": s.confidence, "probabilities": s.probabilities,
        "severity": s.severity, "affected_pct": s.affected_pct, "details": {k: v for k, v in s.details.items() if k != "files"},
        "created_at": iso(s.created_at), "disclaimer": DISCLAIMER,
    }


def findings_text(s: Scan, p: Patient):
    probs = ", ".join(f"{k} {v * 100:.1f}%" for k, v in sorted(s.probabilities.items(), key=lambda kv: -kv[1]))
    return (
        f"Patient: {p.age}-year-old {p.sex.lower()}. Imaging: {'chest X-ray' if s.modality == 'xray' else 'chest CT slice'}.\n"
        f"AI finding: {s.prediction} (calibrated confidence {s.confidence * 100:.1f}%). Class probabilities: {probs}.\n"
        f"Severity estimate: {s.severity} - {s.affected_pct:.1f}% of the lung area is covered by high Grad-CAM activation.\n"
        f"Models: EfficientNet-B0 classifier, {s.details.get('mask_method', '')} lung mask, Grad-CAM explanation."
    )


def get_scan(db, sid):
    s = db.get(Scan, sid)
    if not s:
        raise HTTPException(404, "Scan not found")
    return s


@router.post("/scans")
async def upload_scan(patient_id: int = Form(...), file: UploadFile = File(...), user: User = Depends(current_user)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "File is larger than 25 MB")
    with SessionLocal() as db:
        p = db.get(Patient, patient_id)
        if not p:
            raise HTTPException(404, "Patient not found")
        try:
            r = engine.analyze(data, file.filename or "")
        except RejectedImage as e:
            audit(db, user, "scan_rejected", f"{p.code}: {(file.filename or '')[:50]}")
            raise HTTPException(422, str(e))
        files = {"upload": storage.save(data)}
        files.update({k: storage.save(v) for k, v in r["images"].items()})
        s = Scan(patient_id=p.id, uploaded_by=user.id, filename=(file.filename or "upload")[:255], modality=r["modality"],
                 modality_score=r["modality_score"], prediction=r["prediction"], confidence=r["confidence"],
                 probabilities=r["probabilities"], severity=r["severity"], affected_pct=r["affected_pct"],
                 details={**r["details"], "files": files}, reports={})
        db.add(s)
        db.commit()
        db.refresh(s)
        audit(db, user, "scan_upload", f"scan {s.id} ({p.code})")
        return scan_out(s, decrypt_text(p.name_enc))


@router.get("/scans")
def list_scans(user: User = Depends(current_user)):
    with SessionLocal() as db:
        scans = db.query(Scan).order_by(Scan.id.desc()).limit(50).all()
        return [scan_out(s, decrypt_text(s.patient.name_enc)) for s in scans]


@router.get("/scans/{sid}")
def read_scan(sid: int, user: User = Depends(current_user)):
    with SessionLocal() as db:
        s = get_scan(db, sid)
        audit(db, user, "scan_view", f"scan {sid}")
        return scan_out(s, decrypt_text(s.patient.name_enc))


@router.get("/scans/{sid}/image/{kind}")
def scan_image(sid: int, kind: str, user: User = Depends(current_user)):
    if kind not in IMAGE_KINDS:
        raise HTTPException(404, "Unknown image")
    with SessionLocal() as db:
        s = get_scan(db, sid)
        return Response(storage.load(s.details["files"][kind]), media_type="image/png", headers={"Cache-Control": "private, max-age=3600"})


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    lang: str = "en"


@router.get("/scans/{sid}/assistant")
def chat_history(sid: int, user: User = Depends(require_role("doctor"))):
    with SessionLocal() as db:
        get_scan(db, sid)
        msgs = db.query(ChatMessage).filter(ChatMessage.scan_id == sid).order_by(ChatMessage.id).all()
        return [{"role": m.role, "content": m.content, "model": m.model} for m in msgs]


@router.post("/scans/{sid}/assistant")
def ask(sid: int, body: AskIn, user: User = Depends(require_role("doctor"))):
    with SessionLocal() as db:
        s = get_scan(db, sid)
        prior = db.query(ChatMessage).filter(ChatMessage.scan_id == sid).order_by(ChatMessage.id).all()
        history = [("user", "Screening result for context:\n" + findings_text(s, s.patient)), ("assistant", "Understood. I have the screening result.")]
        history += [(m.role, m.content) for m in prior[-10:]]
        lang_note = f" Answer in {LANGS.get(body.lang, 'English')}." if body.lang != "en" else ""
        try:
            answer, model = gemini.generate(body.question + lang_note, SYSTEM, history)
        except gemini.GeminiError as e:
            raise HTTPException(503, str(e))
        db.add_all([ChatMessage(scan_id=sid, role="user", content=body.question),
                    ChatMessage(scan_id=sid, role="assistant", content=answer, model=model)])
        db.commit()
        audit(db, user, "assistant_question", f"scan {sid}")
        return {"answer": answer, "model": model}


def ai_report_text(db, s: Scan, lang: str):
    if lang in (s.reports or {}):
        return s.reports[lang]
    prompt = (
        findings_text(s, s.patient)
        + f"\n\nWrite a patient-friendly report section in {LANGS[lang]} (simple words, no jargon without explanation). "
        'Return JSON: {"summary": "2-3 sentences", "explanation": "what the finding and severity mean, 3-5 sentences, '
        'mention the AI result must be confirmed by a doctor", "next_steps": ["3-5 short concrete steps"]}. '
        f"All values must be written in {LANGS[lang]}."
    )
    data, model = gemini.generate_json(prompt, SYSTEM)
    if not isinstance(data, dict) or "summary" not in data:
        raise gemini.GeminiError("AI response missing fields")
    data = {"summary": str(data.get("summary", "")), "explanation": str(data.get("explanation", "")),
            "next_steps": [str(x) for x in data.get("next_steps", [])][:6], "model": model}
    s.reports = {**(s.reports or {}), lang: data}
    db.commit()
    return data


@router.get("/scans/{sid}/report")
def report(sid: int, lang: str = "en", user: User = Depends(require_role("doctor"))):
    if lang not in LANGS:
        raise HTTPException(400, "lang must be en, hi or te")
    with SessionLocal() as db:
        s = get_scan(db, sid)
        try:
            ai = ai_report_text(db, s, lang)
            ai_status = "ok"
        except gemini.GeminiError as e:
            ai, ai_status = None, str(e)
        images = {k: storage.load(s.details["files"][k]) for k in ("mask", "heatmap")}
        pdf = build_pdf(s, decrypt_text(s.patient.name_enc), s.patient, ai, lang, images)
        audit(db, user, "report_download", f"scan {sid} ({lang})")
        return Response(pdf, media_type="application/pdf", headers={
            "Content-Disposition": f'inline; filename="pulmovision_scan{sid}_{lang}.pdf"',
            "X-AI-Status": json.dumps(ai_status)[:300], "Access-Control-Expose-Headers": "X-AI-Status"})


@router.get("/audit")
def audit_log(user: User = Depends(require_role("doctor"))):
    with SessionLocal() as db:
        rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
        return [{"id": r.id, "user": r.user_email, "action": r.action, "target": r.target, "at": iso(r.created_at)} for r in rows]
