"""Fast feasibility checks with plain-language reasons and suggestions."""
from __future__ import annotations

from collections import Counter

from app.services.engine.graph import paper_ceiling
from app.services.engine.types import EngineCandidate, EngineHall, Rules


def precheck(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules) -> list[str]:
    reasons: list[str] = []
    if not candidates:
        return ["There are no candidates registered for this session."]
    if not halls:
        return ["No halls are selected. Choose at least one hall."]

    duplicates = [k for k, n in Counter(c.key for c in candidates).items() if n > 1]
    if duplicates:
        reasons.append(f"Candidates appear more than once: {', '.join(duplicates[:5])}.")

    seats = sum(h.capacity for h in halls)
    if len(candidates) > seats:
        reasons.append(
            f"{len(candidates)} candidates but only {seats} usable seats in the selected halls. "
            f"Select halls with at least {len(candidates) - seats} more seats.")

    needs = sum(c.needs_accessible for c in candidates)
    accessible = sum(len(h.accessible_seats) for h in halls)
    if needs > accessible:
        reasons.append(
            f"{needs} candidates need an accessible seat but the selected halls have {accessible}. "
            "Select more halls or mark more accessible seats in the hall layouts.")

    ceiling = sum(paper_ceiling(h, rules.adjacency) for h in halls)
    for paper, count in sorted(Counter(c.paper for c in candidates).items(), key=lambda kv: -kv[1]):
        if count > ceiling:
            hint = " or switch to 4-neighbour adjacency" if rules.adjacency == 8 else ""
            reasons.append(
                f"Paper {paper} has {count} candidates, but the selected halls can seat at most {ceiling} "
                f"of them without two neighbours writing it. Select more halls{hint}.")
    return reasons
