"""Orchestrates F1-F6 for a freshly uploaded contract: parse -> split into
clauses -> classify -> detect predatory clauses -> detect risky combinations
-> score complexity -> summarize. Persists everything via SQLAlchemy."""
import json

from sqlalchemy.orm import Session

from ..db import Contract, Clause, Flag
from . import classification, complexity, explain, parsing
from .graph import detect_risky_combinations
from .rules import detect_flags
from .vectorstore import to_blob


def process_upload(session: Session, user_id: int, file_path: str, filename: str, content_type: str) -> Contract:
    pages = parsing.extract_pages(file_path, content_type)
    raw_clauses = parsing.split_into_clauses(pages)
    full_text = "\n\n".join(c["text"] for c in raw_clauses)

    contract = Contract(user_id=user_id, filename=filename)
    session.add(contract)
    session.flush()

    clause_records: list[Clause] = []
    clause_flag_map: list[dict] = []  # for graph + summary
    flags_summary = []

    for raw in raw_clauses:
        result = classification.classify_clause(raw["text"])
        clause = Clause(
            contract_id=contract.id,
            index_in_doc=raw["index_in_doc"],
            page_number=raw["page_number"],
            text=raw["text"],
            clause_type=result["clause_type"],
            classification_confidence=result["confidence"],
            classification_method=result["method"],
            embedding=to_blob(result["embedding"].tolist()),
        )
        session.add(clause)
        session.flush()
        clause_records.append(clause)

        matched_rules = detect_flags(raw["text"])
        rule_ids = []
        for rule in matched_rules:
            explanation = explain.explain_flag(raw["text"], rule)
            flag = Flag(
                clause_id=clause.id,
                rule_id=rule.id,
                rule_label=rule.label,
                severity=rule.severity,
                reason=explanation["reason"],
                provision=explanation["provision"],
                safer_wording=explanation["safer_wording"],
            )
            session.add(flag)
            rule_ids.append(rule.id)
            flags_summary.append({
                "rule_label": rule.label,
                "severity": rule.severity,
                "clause_index": raw["index_in_doc"],
            })

        clause_flag_map.append({
            "id": clause.id,
            "clause_type": result["clause_type"],
            "flags": rule_ids,
            "text_preview": raw["text"][:120],
        })

    combos = detect_risky_combinations(clause_flag_map)

    comp = complexity.score_contract(full_text, len(raw_clauses))
    summary = explain.summarize_contract([c["text"] for c in raw_clauses], flags_summary)

    contract.complexity_grade = comp["complexity_grade"]
    contract.complexity_score = comp["complexity_score"]
    contract.readability_score = comp["readability_score"]
    contract.legalese_density = comp["legalese_density"]
    contract.cross_reference_count = comp["cross_reference_count"]
    contract.avg_sentence_length = comp["avg_sentence_length"]
    contract.plain_summary = summary["plain_summary"]
    contract.key_obligations = json.dumps(summary["key_obligations"])
    contract.combo_flags = json.dumps(combos)

    session.commit()
    session.refresh(contract)
    return contract
