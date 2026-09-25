import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import UPLOAD_DIR, gemini_configured
from ..db import Contract, Clause, User, get_session
from ..schemas import ClauseResponse, ClauseSummary, ContractReportResponse, ContractSummaryResponse
from ..services.graph import graph_to_json
from ..services.pipeline import process_upload

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _severity_rank(sev: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(sev, 0)


@router.post("/upload", response_model=ContractReportResponse)
async def upload_contract(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not gemini_configured():
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Add it to .env and restart the backend.",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    dest_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    contents = await file.read()
    dest_path.write_bytes(contents)

    try:
        contract = process_upload(
            session, user.id, str(dest_path), file.filename, file.content_type or ""
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        dest_path.unlink(missing_ok=True)

    return _to_report(contract)


@router.get("", response_model=list[ContractSummaryResponse])
def list_contracts(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    contracts = (
        session.query(Contract)
        .filter(Contract.user_id == user.id)
        .order_by(Contract.uploaded_at.desc())
        .all()
    )
    results = []
    for c in contracts:
        flag_count = sum(len(cl.flags) for cl in c.clauses)
        results.append(ContractSummaryResponse(
            id=c.id, filename=c.filename, uploaded_at=c.uploaded_at.isoformat(),
            complexity_grade=c.complexity_grade, complexity_score=c.complexity_score,
            flag_count=flag_count,
        ))
    return results


@router.get("/{contract_id}", response_model=ContractReportResponse)
def get_contract(contract_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    contract = _get_owned_contract(session, contract_id, user.id)
    return _to_report(contract)


@router.get("/{contract_id}/clauses/{clause_id}", response_model=ClauseResponse)
def get_clause(contract_id: int, clause_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    contract = _get_owned_contract(session, contract_id, user.id)
    clause = next((c for c in contract.clauses if c.id == clause_id), None)
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found.")
    return clause


@router.get("/{contract_id}/graph")
def get_graph(contract_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    contract = _get_owned_contract(session, contract_id, user.id)
    clause_data = [
        {
            "id": cl.id,
            "clause_type": cl.clause_type,
            "flags": [f.rule_id for f in cl.flags],
            "text_preview": cl.text[:120],
        }
        for cl in contract.clauses
    ]
    combos = contract.combo_flags_list()
    return graph_to_json(clause_data, combos)


def _get_owned_contract(session: Session, contract_id: int, user_id: int) -> Contract:
    contract = session.get(Contract, contract_id)
    if not contract or contract.user_id != user_id:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return contract


def _to_report(contract: Contract) -> ContractReportResponse:
    clauses = sorted(contract.clauses, key=lambda c: c.index_in_doc)
    clause_summaries = []
    for cl in clauses:
        severities = [f.severity for f in cl.flags]
        max_sev = max(severities, key=_severity_rank) if severities else "none"
        clause_summaries.append(ClauseSummary(
            id=cl.id, index_in_doc=cl.index_in_doc, page_number=cl.page_number,
            clause_type=cl.clause_type, text_preview=cl.text[:160],
            flag_count=len(cl.flags), max_severity=max_sev,
        ))

    return ContractReportResponse(
        id=contract.id, filename=contract.filename, uploaded_at=contract.uploaded_at.isoformat(),
        complexity_grade=contract.complexity_grade, complexity_score=contract.complexity_score,
        readability_score=contract.readability_score, legalese_density=contract.legalese_density,
        cross_reference_count=contract.cross_reference_count, avg_sentence_length=contract.avg_sentence_length,
        plain_summary=contract.plain_summary, key_obligations=contract.key_obligations_list(),
        combo_flags=contract.combo_flags_list(), clauses=clause_summaries,
    )
