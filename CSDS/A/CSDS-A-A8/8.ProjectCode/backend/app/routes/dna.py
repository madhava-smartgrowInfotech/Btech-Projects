from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import User, get_db
from ..services import dna, reports
from .history import save

router = APIRouter(prefix="/api/dna", tags=["dna"])


class SeqIn(BaseModel):
    sequence: str
    report: bool = True


@router.get("/samples")
def samples(user: User = Depends(current_user)):
    return dna.samples()


@router.post("/classify")
def classify(body: SeqIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        res = dna.analyse(body.sequence)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))
    if body.report:
        compact = {**res, "repeat_type": {k: v for k, v in res["repeat_type"].items() if k != "windows"}}
        res["report"] = reports.generate("dna", compact)
    seq = res["sequence"]
    res["analysis_id"] = save(db, user, "dna", f"DNA {seq['id']} ({seq['length']} bp)",
                              {k: v for k, v in res.items() if k != "report"}, res.get("report"))
    return res
