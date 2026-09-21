"""SeatWise seating engine (OR-Tools CP-SAT)."""
from app.services.engine.engine import DEFAULT_HALL_BUDGET, ENGINE_VERSION, derive_seed, solve
from app.services.engine.types import EngineCandidate, EngineHall, EngineResult, Placement, Rules, Seat
from app.services.engine.validator import Scorecard, validate

__all__ = [
    "DEFAULT_HALL_BUDGET", "ENGINE_VERSION", "EngineCandidate", "EngineHall", "EngineResult", "Placement", "Rules",
    "Scorecard", "Seat", "derive_seed", "solve", "validate",
]
