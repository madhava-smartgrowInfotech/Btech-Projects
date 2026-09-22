"""F4 - suspicious SMS check: NLP model + scam-pattern rules, stored so it can raise the risk of related payments."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.i18n.messages import LANGS, advice, scam_type_name
from app.ml.registry import registry
from app.ml.sms import analyze
from app.models import SmsCheck, User, Wallet, utcnow


def analyze_and_store(db: Session, user: User, text: str, now: datetime | None = None) -> SmsCheck:
    result = analyze(registry.bundles.get("sms"), text)
    check = SmsCheck(
        user_id=user.id,
        text=result["text"],
        language=result["language"],
        probability=result["probability"],
        verdict=result["verdict"],
        scam_type=result["scam_type"],
        highlights=result["highlights"],
        entities=result["entities"],
        signals=result["signals"]
        + [{"model_probability": result["model_probability"], "rules_score": result["rules_score"], "model_terms": result["model_terms"], "script": result["script"]}],
        created_at=now or utcnow(),
    )
    db.add(check)
    db.flush()
    return check


def check_payload(db: Session, check: SmsCheck) -> dict:
    meta = next((s for s in check.signals if "model_probability" in s), {})
    rules = [s for s in check.signals if "rule" in s]
    upi_ids = check.entities.get("upi_ids", [])
    known = {w.upi_id: w for w in db.scalars(select(Wallet).where(Wallet.upi_id.in_(upi_ids))).all()} if upi_ids else {}
    return {
        "id": check.id,
        "text": check.text,
        "language": check.language,
        "script": meta.get("script"),
        "verdict": check.verdict,
        "probability": check.probability,
        "model_probability": meta.get("model_probability"),
        "rules_score": meta.get("rules_score"),
        "scam_type": check.scam_type,
        "scam_type_name": {lang: scam_type_name(check.scam_type, lang) for lang in LANGS} if check.scam_type else None,
        "advice": {lang: advice(check.scam_type if check.verdict != "safe" else None, lang) for lang in LANGS} if check.verdict != "safe" else None,
        "highlights": check.highlights,
        "signals": rules,
        "model_terms": meta.get("model_terms", []),
        "entities": check.entities,
        "linked_accounts": [
            {"upi_id": u, "in_sandbox": u in known, "name": known[u].display_name if u in known else None} for u in upi_ids
        ],
        "thresholds": (registry.bundles.get("sms") or {}).get("thresholds", {"scam": 0.7, "suspicious": 0.4}),
        "created_at": check.created_at,
    }
