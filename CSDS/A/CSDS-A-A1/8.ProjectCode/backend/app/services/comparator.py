"""F6 - Plan comparison: field-by-field table from two Policy Cards plus AI trade-offs with citations."""

from __future__ import annotations

import re
import time
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import LANGUAGE_NAMES
from app.core.logging import get_logger, log_event
from app.schemas.policy_card import CARD_FIELDS, WAITING_FIELDS
from app.services.gemini_client import generate_json

log = get_logger("compare")

# Direction for a clear "better" marker: lower or higher number wins.
LOWER_IS_BETTER = {"deductible", "co_payment", "waiting_periods.initial", "waiting_periods.pre_existing",
                   "waiting_periods.specific_diseases", "waiting_periods.maternity"}
HIGHER_IS_BETTER = {"pre_hospitalization", "post_hospitalization", "free_look_period", "grace_period",
                    "cumulative_bonus"}

SYSTEM = """You compare two health-insurance policies for a buyer, using ONLY the two Policy Cards and risk
lists provided. Tags look like A:C12 (policy A, clause 12) or B:C7 (policy B, clause 7). Cite them in each
trade-off. Be balanced and concrete (amounts, months, percentages). Do not invent features or prices.
Write every text field in the requested language, in plain words."""


class TradeOff(BaseModel):
    topic: str
    policy_a: str = Field(description="What policy A offers on this topic.")
    policy_b: str = Field(description="What policy B offers on this topic.")
    better: str = Field(description="'A', 'B' or 'Depends'.")
    why: str
    tags: list[str] = Field(description="Tags like A:C12, B:C7.")


class ComparisonOut(BaseModel):
    overall: str = Field(description="3-4 sentence plain-language comparison.")
    choose_a_if: list[str]
    choose_b_if: list[str]
    trade_offs: list[TradeOff] = Field(description="5-8 most important differences.")
    next_actions: list[str]


def _get(card: dict[str, Any], path: str) -> dict[str, Any] | None:
    node: Any = card
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node if isinstance(node, dict) else None


def _comparable_number(item: dict | None) -> float | None:
    if not item or not item.get("found"):
        return None
    n = item.get("number")
    if not isinstance(n, (int, float)):
        return None
    if item.get("unit") == "days" and item.get("number") is not None:
        return float(n)
    return float(n)


def table_rows(card_a: dict[str, Any], card_b: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fields = [(k, label, k) for k, label in CARD_FIELDS[:5]] + \
             [(f"waiting_periods.{k}", label, f"waiting_periods.{k}") for k, label in WAITING_FIELDS] + \
             [(k, label, k) for k, label in CARD_FIELDS[5:]]
    for key, label, path in fields:
        a, b = _get(card_a, path), _get(card_b, path)
        better = None
        na, nb = _comparable_number(a), _comparable_number(b)
        same_unit = a and b and a.get("unit") == b.get("unit")
        if na is not None and nb is not None and same_unit:
            if key in LOWER_IS_BETTER:
                better = "a" if na < nb else "b" if nb < na else "equal"
            elif key in HIGHER_IS_BETTER:
                better = "a" if na > nb else "b" if nb > na else "equal"
        elif key in LOWER_IS_BETTER and a and b:
            # "No co-payment" / "no deductible" beats one that exists.
            fa, fb = bool(a.get("found") and na), bool(b.get("found") and nb)
            if fa != fb:
                better = "b" if fa else "a"
        rows.append({
            "key": key, "label": label, "better": better,
            "a": {k: (a or {}).get(k) for k in ("value", "found", "clause_ordinal", "page", "verified")},
            "b": {k: (b or {}).get(k) for k in ("value", "found", "clause_ordinal", "page", "verified")},
        })
    return rows


def _card_brief(tag: str, card: dict[str, Any], risks: list[dict[str, Any]]) -> str:
    lines = [f"POLICY {tag}: {card.get('product_name')} by {card.get('insurer')} ({card.get('policy_type')})"]

    def add(label: str, item: dict | None) -> None:
        if item and item.get("found"):
            ref = f" [{tag}:C{item['clause_ordinal']}]" if item.get("clause_ordinal") else ""
            lines.append(f"- {label}: {item.get('value')}{ref}")

    for key, label in CARD_FIELDS:
        add(label, card.get(key))
    for key, label in WAITING_FIELDS:
        add(f"Waiting period - {label}", (card.get("waiting_periods") or {}).get(key))
    for sub in card.get("sub_limits") or []:
        add(f"Sub-limit - {sub.get('name')}", sub)
    for cond in card.get("co_payment_conditions") or []:
        add(f"Conditional co-payment - {cond.get('name')}", cond)
    for exc in (card.get("key_exclusions") or [])[:8]:
        add(f"Exclusion - {exc.get('name')}", exc)
    for r in risks[:8]:
        ref = f" [{tag}:C{r['clause_ordinal']}]" if r.get("clause_ordinal") else ""
        lines.append(f"- Risk ({r['severity']}): {r['title']}{ref}")
    return "\n".join(lines)


def compare(card_a: dict[str, Any], risks_a: list[dict], card_b: dict[str, Any], risks_b: list[dict],
            language: str = "en", user_id: int | None = None, cache: bool = False) -> dict[str, Any]:
    t0 = time.perf_counter()
    rows = table_rows(card_a, card_b)
    prompt = (f"Requested language: {LANGUAGE_NAMES.get(language, 'English')}\n\n"
              f"{_card_brief('A', card_a, risks_a)}\n\n{_card_brief('B', card_b, risks_b)}")
    out, meta = generate_json(prompt=prompt, schema=ComparisonOut, purpose="comparison", system=SYSTEM,
                              user_id=user_id, temperature=0.2, cache=cache)

    def parse_tags(tags: list[str]) -> list[dict[str, Any]]:
        parsed = []
        for tag in tags:
            m = re.match(r"\s*([AB])\s*:\s*C?(\d+)", tag, re.I)
            if m:
                parsed.append({"policy": m.group(1).lower(), "ordinal": int(m.group(2))})
        return parsed

    severity = {"a": {}, "b": {}}
    for side, risks in (("a", risks_a), ("b", risks_b)):
        for r in risks:
            severity[side][r["severity"]] = severity[side].get(r["severity"], 0) + 1
    total_ms = round((time.perf_counter() - t0) * 1000)
    log_event(log, "compared", ms=total_ms, model=meta.model)
    return {
        "rows": rows,
        "risk_counts": severity,
        "overall": out.overall,
        "choose_a_if": out.choose_a_if,
        "choose_b_if": out.choose_b_if,
        "trade_offs": [t.model_dump() | {"tags": parse_tags(t.tags)} for t in out.trade_offs],
        "next_actions": out.next_actions,
        "model": meta.model,
        "timings": {"total_ms": total_ms},
    }
