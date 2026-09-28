from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import User, get_db
from ..services import reports, str_match
from .history import save

router = APIRouter(prefix="/api/str", tags=["str"])


class QueryIn(BaseModel):
    profile: Dict[str, Optional[str]]
    report: bool = True


@router.get("/loci")
def loci(user: User = Depends(current_user)):
    return str_match.loci()


@router.get("/sample-query")
def sample_query(user: User = Depends(current_user)):
    return str_match.sample_query()


@router.post("/match")
def match(body: QueryIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        res = str_match.match(body.profile)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if body.report:
        top5 = [{k: v for k, v in m.items() if k != "loci"} for m in res["matches"][:5]]
        top5[0]["loci_detail"] = res["matches"][0]["loci"]
        res["report"] = reports.generate("str", {**res, "matches": top5})
    top = res["matches"][0]
    res["analysis_id"] = save(db, user, "str", f"STR query ({res['query_loci']} loci) - top {top['id']}",
                              {k: v for k, v in res.items() if k != "report"}, res.get("report"))
    return res
