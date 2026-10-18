"""Strict schema for everything an agent/LLM is allowed to say. Anything else is rejected before the shield."""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ACTION_TYPES = (
    "charge_battery", "discharge_battery", "import_power", "export_power",
    "curtail_generation", "shift_load", "idle",
)
ActionType = Literal[
    "charge_battery", "discharge_battery", "import_power", "export_power",
    "curtail_generation", "shift_load", "idle",
]
_REASON_RE = re.compile(r"^[A-Z0-9_]{1,48}$")


class EnergyAction(BaseModel):
    """A *proposal*. It has no ability to execute anything."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=1, max_length=64)
    action_type: ActionType
    power_kw: float = Field(ge=0, le=1_000_000, allow_inf_nan=False)
    duration_minutes: int = Field(ge=1, le=1440)
    target_node: str | None = Field(default=None, max_length=64)
    reason_codes: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("reason_codes")
    @classmethod
    def _reason_codes_are_codes(cls, v):
        for code in v:
            if not isinstance(code, str) or not _REASON_RE.match(code):
                raise ValueError(f"reason code {code!r} must match [A-Z0-9_]{{1,48}}")
        return v
