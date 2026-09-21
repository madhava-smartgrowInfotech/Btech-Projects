"""Policy Card extraction accuracy against hand-checked values (data/eval/cards.json). No API calls."""

from __future__ import annotations

from typing import Any

from ml import common  # noqa: F401

_TO_DAYS = {"days": 1.0, "months": 30.0, "hours": 1 / 24}
_TO_HOURS = {"hours": 1.0, "days": 24.0}


def _get(card: dict[str, Any], path: str) -> Any:
    node: Any = card
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def _number_in(item: dict | None, want_unit: str) -> float | None:
    if not isinstance(item, dict) or not item.get("found"):
        return None
    n, unit = item.get("number"), item.get("unit")
    if not isinstance(n, (int, float)):
        return None
    if want_unit == "months":
        if unit == "months" or unit == "none":
            return float(n)
        if unit == "days":
            return float(n) / 30.0
        return None
    if want_unit == "days":
        if unit in _TO_DAYS:
            return float(n) * _TO_DAYS[unit]
        return float(n) if unit == "none" else None
    if want_unit == "hours":
        if unit in _TO_HOURS:
            return float(n) * _TO_HOURS[unit]
        return float(n) if unit == "none" else None
    return None


def check(card: dict[str, Any], rule: dict[str, Any]) -> bool:
    kind, expected = rule["type"], rule["expected"]
    value = _get(card, rule["field"])
    if kind == "exact":
        return isinstance(value, str) and value.strip().upper() == str(expected).upper()
    if kind == "text":
        text = value.get("value") if isinstance(value, dict) else value
        if not isinstance(text, str) or (isinstance(value, dict) and not value.get("found")):
            return False
        return any(e.lower() in text.lower() for e in expected)
    if kind == "list":
        items = [v if isinstance(v, str) else (v.get("name") or "") for v in (value or [])]
        return any(e.lower() in i.lower() for i in items for e in expected)
    if kind in ("months", "days", "hours"):
        n = _number_in(value, kind)
        if n is None and isinstance(value, dict) and isinstance(value.get("value"), str):
            # Fall back to the stated text ("24 months", "30 days").
            return f"{int(expected)} {kind}" in value["value"].lower() or (
                kind == "months" and expected % 12 == 0 and f"{int(expected // 12)} year" in value["value"].lower())
        return n is not None and abs(n - float(expected)) <= max(0.5, float(expected) * 0.02)
    return False


def run(doc_ids: dict[str, int], truth: dict[str, Any], log=print) -> tuple[dict, list[dict]]:  # noqa: ANN001
    from sqlalchemy import select

    from app.core.db import SessionLocal
    from app.models import PolicyCard

    rows: list[dict] = []
    by_field: dict[str, list[bool]] = {}
    verified: list[float] = []
    with SessionLocal() as db:
        for slug, rules in truth.items():
            if slug.startswith("_") or slug not in doc_ids:
                continue
            card = db.scalar(select(PolicyCard).where(PolicyCard.document_id == doc_ids[slug]))
            if card is None:
                log(f"extraction {slug}: no Policy Card")
                continue
            verified.append(card.verified_ratio)
            for rule in rules:
                ok = check(card.data, rule)
                field = rule["field"].split(".")[-1]
                by_field.setdefault(field, []).append(ok)
                rows.append({"policy": slug, "field": rule["field"], "expected": rule["expected"], "correct": ok,
                             "extracted": (_get(card.data, rule["field"]) or {}).get("value")
                             if isinstance(_get(card.data, rule["field"]), dict) else _get(card.data, rule["field"]),
                             "model": card.model})
            log(f"extraction {slug}: {sum(r['correct'] for r in rows if r['policy'] == slug)}/{len(rules)} correct")
    total = len(rows)
    return {
        "fields": total,
        "accuracy": round(sum(r["correct"] for r in rows) / total, 4) if total else None,
        "verified_ratio": round(sum(verified) / len(verified), 4) if verified else None,
        "by_field": {k: round(sum(v) / len(v), 4) for k, v in sorted(by_field.items())},
        "by_policy": {slug: round(sum(r["correct"] for r in rows if r["policy"] == slug)
                                  / max(1, sum(1 for r in rows if r["policy"] == slug)), 4)
                      for slug in {r["policy"] for r in rows}},
        "models": sorted({r["model"] for r in rows}),
    }, rows
