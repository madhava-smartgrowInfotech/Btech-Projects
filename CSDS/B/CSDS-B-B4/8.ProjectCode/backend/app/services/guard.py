"""F9 - collect-request and QR guard: catches 'you will receive money' tricks that are really debits."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import parse_qs, unquote, urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.registry import registry
from app.ml.sms import analyze
from app.models import Wallet

RECEIVE_WORDS = re.compile(
    r"(receive|refund|cashback|reward|prize|credit(ed)?|won|winning|claim|get money|money back|"
    r"रिफंड|कैशबैक|इनाम|पाने|पाएँ|जमा|रीफंड|క్యాష్‌బ్యాక్|రీఫండ్|బహుమతి|పొంద|జమ|"
    r"paane|wapas|inaam|receive karein|pondandi|bahumati)",
    re.IGNORECASE,
)


def note_analysis(note: str | None) -> dict:
    """Scores a collect-request / QR note with the SMS model + rules."""
    if not note or not note.strip():
        return {"score": 0.0, "verdict": "safe", "promises_money": False, "highlights": [], "scam_type": None}
    result = analyze(registry.bundles.get("sms"), note)
    promises = bool(RECEIVE_WORDS.search(note))
    score = result["probability"]
    if promises:
        score = max(score, 0.75)
    return {
        "score": round(float(score), 4),
        "verdict": result["verdict"] if not promises else "scam",
        "promises_money": promises,
        "highlights": result["highlights"] or [
            {"start": m.start(), "end": m.end(), "text": m.group(0), "sources": ["rule"], "rules": ["promises_money"]}
            for m in RECEIVE_WORDS.finditer(note)
        ],
        "scam_type": result["scam_type"] or ("refund_scam" if promises else None),
    }


def collect_guard(note: str | None, amount: float) -> dict:
    """Every collect request is a debit; flag notes that pretend otherwise."""
    n = note_analysis(note)
    flags = ["collect_is_debit"]
    if n["promises_money"] or n["verdict"] == "scam":
        flags.append("deceptive_note")
    return {"type": "collect", "is_debit": True, "debit_amount": amount, "note": n, "flags": flags, "note_score": n["score"]}


def _names_match(a: str, b: str) -> bool:
    norm = lambda s: re.sub(r"[^a-z]", "", s.lower())  # noqa: E731
    a, b = norm(a), norm(b)
    if not a or not b:
        return True
    return a in b or b in a or SequenceMatcher(None, a, b).ratio() >= 0.72


def parse_upi_uri(raw: str) -> dict:
    """Parses upi://pay?pa=...&pn=...&am=...&tn=...; returns {} if it is not a UPI payment QR."""
    raw = raw.strip()
    if not raw.lower().startswith("upi://"):
        return {}
    parsed = urlparse(raw)
    params = {k: unquote(v[0]) for k, v in parse_qs(parsed.query).items() if v}
    return {
        "action": parsed.netloc.lower() or parsed.path.strip("/").lower(),
        "pa": params.get("pa", "").strip().lower(),
        "pn": params.get("pn", "").strip(),
        "am": params.get("am"),
        "tn": params.get("tn", "").strip(),
        "cu": params.get("cu", "INR"),
    }


def qr_guard(db: Session, raw: str) -> dict:
    """Checks a scanned QR code before any payment screen is shown."""
    raw = (raw or "").strip()
    flags: list[str] = []
    if re.match(r"https?://", raw, re.IGNORECASE):
        return {"valid": False, "flags": ["qr_is_link"], "qr_flag": 1.0, "raw": raw, "message_code": "qr_is_link"}
    uri = parse_upi_uri(raw)
    if not uri or not uri.get("pa"):
        return {"valid": False, "flags": ["not_upi"], "qr_flag": 0.0, "raw": raw, "message_code": "not_upi"}
    wallet = db.scalar(select(Wallet).where(Wallet.upi_id == uri["pa"]))
    amount = None
    if uri.get("am"):
        try:
            amount = round(float(uri["am"]), 2)
        except ValueError:
            flags.append("bad_amount")
    note = note_analysis(uri.get("tn"))
    if wallet is None:
        flags.append("unknown_upi_id")
    elif uri.get("pn") and not _names_match(uri["pn"], wallet.display_name):
        flags.append("name_mismatch")
    if amount and note["promises_money"]:
        flags.append("scan_to_receive")
    elif note["promises_money"]:
        flags.append("receive_words")
    score = 0.0
    if "scan_to_receive" in flags:
        score = 1.0
    elif "name_mismatch" in flags or "receive_words" in flags:
        score = 0.8
    return {
        "valid": wallet is not None,
        "raw": raw,
        "payee_upi_id": uri["pa"],
        "payee_name_in_qr": uri.get("pn") or None,
        "registered_name": wallet.display_name if wallet else None,
        "amount": amount,
        "note": uri.get("tn") or None,
        "note_analysis": note,
        "flags": flags,
        "qr_flag": score,
    }


def build_upi_uri(upi_id: str, name: str, amount: float | None = None, note: str | None = None) -> str:
    from urllib.parse import quote

    parts = [f"pa={quote(upi_id)}", f"pn={quote(name)}", "cu=INR"]
    if amount:
        parts.append(f"am={amount:.2f}")
    if note:
        parts.append(f"tn={quote(note)}")
    return "upi://pay?" + "&".join(parts)
