"""Ties the scanner/AI/validation services to the database and scan lifecycle."""
import json

from ..db import AITest, Finding, Scan, SessionLocal, Target, now
from .ai_tests import run_ai_tests
from .scanner import scan_target
from .scope import is_in_scope, scope_error


async def run_scan(scan_id: int) -> None:
    """Background entrypoint: execute a scan and persist everything."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if not scan:
            return
        target = db.get(Target, scan.target_id)
        scan.status = "running"
        scan.progress = 2
        scan.current_step = "Checking scope"
        db.commit()

        if not is_in_scope(target.base_url):
            scan.status = "error"
            scan.error = scope_error(target.base_url)
            scan.current_step = "Blocked by scope guard"
            scan.finished_at = now()
            db.commit()
            return

        endpoints = json.loads(target.endpoints_json or "[]")
        auth = json.loads(target.auth_json or "{}")

        def progress_cb(pct: int, step: str):
            scan.progress = max(scan.progress, min(99, pct))
            scan.current_step = step
            db.commit()

        result = await scan_target(target.base_url, endpoints, auth, progress_cb)

        for f in result["findings"]:
            db.add(Finding(
                scan_id=scan.id, check_id=f["check_id"], title=f["title"],
                severity=f["severity"], owasp_id=f["owasp_id"],
                owasp_name=f["owasp_name"], endpoint=f.get("endpoint", ""),
                description=f["description"],
                evidence_json=json.dumps(f.get("evidence", {}))[:20000],
                curl=f.get("curl", ""), recommendation=f.get("recommendation", ""),
                fix_snippet=f.get("fix_snippet", ""), vuln_key=f.get("vuln_key", ""),
                source=f.get("source", "owasp"),
            ))
        scan.score = result["score"]
        scan.grade = result["grade"]
        scan.progress = 100
        scan.current_step = "Complete"
        scan.status = "done"
        scan.finished_at = now()
        db.commit()
    except Exception as exc:  # noqa: BLE001
        scan = db.get(Scan, scan_id)
        if scan:
            scan.status = "error"
            scan.error = str(exc)
            scan.finished_at = now()
            db.commit()
    finally:
        db.close()


async def run_ai_for_scan(scan_id: int) -> dict:
    """Generate + run AI business-logic tests for a completed scan."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if not scan:
            return {"error": "scan not found"}
        target = db.get(Target, scan.target_id)
        endpoints = json.loads(target.endpoints_json or "[]")
        auth = json.loads(target.auth_json or "{}")

        results, generator = await run_ai_tests(target.base_url, endpoints, auth)

        # Replace any previous AI tests for this scan.
        db.query(AITest).filter(AITest.scan_id == scan.id).delete()
        for r in results:
            db.add(AITest(
                scan_id=scan.id, name=r["name"], category=r["type"],
                endpoint=r["endpoint"], rationale=r.get("rationale", ""),
                spec_json=json.dumps(r.get("body", {})),
                result=r["result"], detail=r.get("detail", ""), generator=generator,
            ))
        scan.ai_generated = True
        db.commit()
        return {"generator": generator, "count": len(results)}
    finally:
        db.close()
