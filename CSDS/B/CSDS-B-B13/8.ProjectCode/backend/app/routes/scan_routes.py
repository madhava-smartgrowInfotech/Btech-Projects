import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import AITest, Finding, Scan, Target, User, get_db, now
from ..schemas import ScanCreate
from ..services.engine import run_ai_for_scan, run_scan
from ..services.reports import render_html, render_pdf
from ..services.scope import is_in_scope, scope_error
from ..services.validation import validate

router = APIRouter(prefix="/api/scans", tags=["scans"])


def _owned_scan(db: Session, scan_id: int, user: User) -> Scan:
    scan = db.get(Scan, scan_id)
    if not scan or scan.owner_id != user.id:
        raise HTTPException(404, "Scan not found")
    return scan


def _finding_dict(f: Finding) -> dict:
    return {
        "id": f.id, "check_id": f.check_id, "title": f.title, "severity": f.severity,
        "owasp_id": f.owasp_id, "owasp_name": f.owasp_name, "endpoint": f.endpoint,
        "description": f.description, "evidence": json.loads(f.evidence_json or "{}"),
        "curl": f.curl, "recommendation": f.recommendation, "fix_snippet": f.fix_snippet,
        "vuln_key": f.vuln_key, "source": f.source,
    }


@router.post("")
async def start_scan(body: ScanCreate, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    target = db.get(Target, body.target_id)
    if not target or target.owner_id != user.id:
        raise HTTPException(404, "Target not found")
    if not body.authorized:
        raise HTTPException(
            400, "You must confirm you are authorised to test this target.")
    if not is_in_scope(target.base_url):
        raise HTTPException(403, scope_error(target.base_url))

    scan = Scan(target_id=target.id, owner_id=user.id, status="pending",
                current_step="Queued")
    db.add(scan)
    db.commit()
    db.refresh(scan)
    asyncio.create_task(run_scan(scan.id))
    return {"id": scan.id, "status": scan.status}


@router.get("")
def list_scans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (db.query(Scan).filter(Scan.owner_id == user.id)
            .order_by(Scan.id.desc()).all())
    out = []
    for s in rows:
        target = db.get(Target, s.target_id)
        out.append({
            "id": s.id, "target_id": s.target_id,
            "target_name": target.name if target else "",
            "status": s.status, "progress": s.progress, "score": s.score,
            "grade": s.grade, "ai_generated": s.ai_generated,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return out


@router.get("/{scan_id}")
def get_scan(scan_id: int, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    scan = _owned_scan(db, scan_id, user)
    target = db.get(Target, scan.target_id)
    findings = db.query(Finding).filter(Finding.scan_id == scan.id).all()
    counts = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return {
        "id": scan.id, "status": scan.status, "progress": scan.progress,
        "current_step": scan.current_step, "score": scan.score, "grade": scan.grade,
        "ai_generated": scan.ai_generated, "error": scan.error,
        "target": {"id": target.id, "name": target.name, "base_url": target.base_url},
        "finding_count": len(findings), "severity_counts": counts,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "finished_at": scan.finished_at.isoformat() if scan.finished_at else None,
    }


@router.get("/{scan_id}/findings")
def get_findings(scan_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    scan = _owned_scan(db, scan_id, user)
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    rows = db.query(Finding).filter(Finding.scan_id == scan.id).all()
    rows.sort(key=lambda f: order.get(f.severity, 9))
    return [_finding_dict(f) for f in rows]


@router.post("/{scan_id}/ai-tests")
async def create_ai_tests(scan_id: int, user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    scan = _owned_scan(db, scan_id, user)
    if scan.status != "done":
        raise HTTPException(400, "Run the scan before generating AI tests.")
    return await run_ai_for_scan(scan.id)


@router.get("/{scan_id}/ai-tests")
def get_ai_tests(scan_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    scan = _owned_scan(db, scan_id, user)
    rows = db.query(AITest).filter(AITest.scan_id == scan.id).all()
    return [{
        "id": t.id, "name": t.name, "category": t.category, "endpoint": t.endpoint,
        "rationale": t.rationale, "body": json.loads(t.spec_json or "{}"),
        "result": t.result, "detail": t.detail, "generator": t.generator,
    } for t in rows]


@router.get("/{scan_id}/validation")
def get_validation(scan_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    scan = _owned_scan(db, scan_id, user)
    target = db.get(Target, scan.target_id)
    known = json.loads(target.known_vulns_json or "[]")
    findings = [_finding_dict(f) for f in
                db.query(Finding).filter(Finding.scan_id == scan.id).all()]
    result = validate(known, findings)
    result["has_known_list"] = bool(known)
    return result


def _report_ctx(db, scan, user):
    target = db.get(Target, scan.target_id)
    findings = [_finding_dict(f) for f in
                db.query(Finding).filter(Finding.scan_id == scan.id).all()]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: order.get(f["severity"], 9))
    ai_rows = db.query(AITest).filter(AITest.scan_id == scan.id).all()
    ai = [{"name": t.name, "endpoint": t.endpoint, "result": t.result,
           "detail": t.detail} for t in ai_rows]
    generator = ai_rows[0].generator if ai_rows else ""
    return target, findings, ai, generator


@router.get("/{scan_id}/report.html", response_class=HTMLResponse)
def report_html(scan_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    scan = _owned_scan(db, scan_id, user)
    target, findings, ai, generator = _report_ctx(db, scan, user)
    html = render_html(target, scan, findings, ai, generator,
                       now().strftime("%Y-%m-%d %H:%M UTC"))
    return HTMLResponse(html)


@router.get("/{scan_id}/report.pdf")
def report_pdf(scan_id: int, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    scan = _owned_scan(db, scan_id, user)
    target, findings, ai, _ = _report_ctx(db, scan, user)
    pdf = render_pdf(target, scan, findings, ai, now().strftime("%Y-%m-%d %H:%M UTC"))
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="apisentry-scan-{scan.id}.pdf"'})
