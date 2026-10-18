"""LLM provider contract. A provider may only return a *validated proposal* (EnergyAction)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.actions import EnergyAction


class LLMUnavailableError(Exception):
    """Provider unreachable, unconfigured, timed out or errored."""


class LLMOutputError(Exception):
    """Provider answered, but not with a schema-valid proposal."""


class LLMProvider(ABC):
    name: str = "base"
    source: str = "llm"  # value stored as decision_source

    @abstractmethod
    async def generate_action(self, context: dict[str, Any]) -> EnergyAction:
        """Return a schema-validated proposal for the agent described by `context`."""

    async def generate(self, context: dict[str, Any]) -> tuple[EnergyAction, str]:
        """Proposal plus its decision_source label."""
        return await self.generate_action(context), self.source

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name, "source": self.source}
