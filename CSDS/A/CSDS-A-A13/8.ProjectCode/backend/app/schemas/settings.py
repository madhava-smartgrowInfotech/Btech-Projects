from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RulesIn(BaseModel):
    """Seating rules. Stored as workspace defaults and copied into every plan."""

    adjacency: Literal[4, 8] = Field(8, description="8 = front, back, sides and diagonals; 4 = no diagonals")
    roll_gap: int = Field(5, ge=0, le=100, description="Neighbours' roll numbers must differ by at least this much (0 = off)")
    department_mix: bool = Field(True, description="Spread departments across halls and avoid same-department neighbours")
    fill_strategy: Literal["compact", "balanced"] = Field("compact", description="compact = fewest halls; balanced = even fill")
    accessible_per_hall: int = Field(2, ge=0, le=20, description="Default accessible seats per hall when a hall file lists none")


class RulesOut(RulesIn):
    pass
