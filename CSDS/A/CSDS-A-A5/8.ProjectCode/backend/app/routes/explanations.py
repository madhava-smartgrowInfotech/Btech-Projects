from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Explanation, User, get_db
from ..services.explainer import ExplainError, build_prompt, check_quality, generate
from .investigate import _tp, expl_out
from .pipeline import state

router = APIRouter(prefix="/api/explanations", tags=["explanations"])


@router.post("/{gstin}")
async def explain(gstin: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    s = state()
    i = _tp(s, gstin)
    t, evidence = s["taxpayers"][i], s["details"][i]["evidence"]
    if not evidence:
        raise HTTPException(400, "No evidence recorded for this taxpayer - nothing to explain")
    prompt = build_prompt(t, evidence, s["config"]["pattern_labels"])
    try:
        text, model = await run_in_threadpool(generate, prompt)
    except ExplainError as e:
        raise HTTPException(502, str(e))
    row = Explanation(run_key=s["run_key"], gstin=gstin, model=model, text=text, evidence=evidence,
                      quality=check_quality(text, evidence), user_id=user.id)
    db.add(row)
    db.commit()
    return expl_out(row)
