"""API request/response schemas (Pydantic). Mirrored by frontend/src/services/types.js."""
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.actions import EnergyAction


class RunConfig(BaseModel):
    """Everything needed to reproduce a run (stored with it)."""
    scenario_id: str = "normal"
    seed: int = 42
    steps: int | None = Field(default=None, ge=1, le=672)
    time_step_minutes: int = Field(default=15, ge=1, le=120)
    provider: Literal["mock", "api", "failing", "baseline"] = "mock"
    unsafe_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    step_delay_s: float = Field(default=0.6, ge=0.0, le=10.0)  # live playback pacing only
    constraint_overrides: dict[str, Any] | None = None
    initial_soc: dict[str, float] | None = None
    agents: dict[str, dict[str, Any]] | None = None
    inject_faults: bool = True
    shield_enabled: bool = True  # False only for the unshielded ablation arm in experiments


class DecisionRequest(BaseModel):
    """Dry-run: ask an agent for its current proposal, or submit an operator-crafted action for shield testing."""
    action: EnergyAction | None = None


class ExperimentRequest(BaseModel):
    scenarios: list[str] | None = None
    seeds: list[int] = Field(default_factory=lambda: [0, 1, 2], max_length=20)
    steps: int | None = Field(default=None, ge=1, le=200)
    arms: list[str] | None = None
    time_step_minutes: int = Field(default=15, ge=1, le=120)
