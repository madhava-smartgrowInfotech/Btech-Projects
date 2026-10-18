"""Provider factory."""
from __future__ import annotations

from app.config import Settings
from app.llm.api_provider import APILLMProvider
from app.llm.base import LLMProvider
from app.llm.mock_provider import FailingProvider, FaultInjectingProvider, MockLLMProvider, RuleBasedProvider

PROVIDERS = ("mock", "api", "failing", "baseline")


def build_provider(name: str, settings: Settings, seed: int = 0, unsafe_rate: float = 0.25,
                   faults: list[dict] | None = None) -> LLMProvider:
    name = (name or settings.llm_provider).lower()
    if name == "api":
        p: LLMProvider = APILLMProvider(settings)
    elif name == "failing":
        p = FailingProvider()
    elif name == "baseline":
        return RuleBasedProvider()  # baseline never receives injected faults
    else:
        p = MockLLMProvider(seed=seed, unsafe_rate=unsafe_rate)
    return FaultInjectingProvider(p, faults) if faults else p
