"""Offline, reproducible providers used for tests, demos and experiments."""
from __future__ import annotations

import asyncio
import random
from typing import Any

from app.agents.policy import baseline_policy, cost_aware_policy
from app.llm.base import LLMOutputError, LLMProvider, LLMUnavailableError
from app.models.actions import EnergyAction


def build_action(ctx: dict[str, Any], raw: dict[str, Any]) -> EnergyAction:
    return EnergyAction(agent_id=ctx["agent_id"], duration_minutes=int(ctx["dt_minutes"]), target_node=None, **raw)


class MockLLMProvider(LLMProvider):
    """Stands in for an LLM: sensible proposals plus seeded, LLM-like imperfections
    (oversized requests, occasional wrong-direction moves) so the shield has work to do."""

    name, source = "mock", "mock"

    def __init__(self, seed: int = 0, unsafe_rate: float = 0.25, latency_ms: float = 0.0):
        self.seed, self.unsafe_rate, self.latency_ms = seed, unsafe_rate, latency_ms

    async def generate_action(self, context: dict[str, Any]) -> EnergyAction:
        if self.latency_ms:
            await asyncio.sleep(self.latency_ms / 1000.0)
        rng = random.Random(f"{self.seed}:{context['agent_id']}:{context['step']}")
        raw = cost_aware_policy(context)
        if raw["action_type"] != "idle" and rng.random() < self.unsafe_rate:
            raw = dict(raw)
            r = rng.random()
            if r < 0.7:  # oversize the request
                raw["power_kw"] = round(raw["power_kw"] * rng.uniform(1.6, 4.0), 3)
                raw["reason_codes"] = raw["reason_codes"] + ["AGGRESSIVE_SIZING"]
            else:  # over-eager: use the full battery rating regardless of headroom
                b = context["battery"]
                kw = max(b["max_charge_kw"], b["max_discharge_kw"], raw["power_kw"]) * 1.5
                raw["power_kw"] = round(kw, 3)
                raw["reason_codes"] = raw["reason_codes"] + ["MAX_RATE_REQUEST"]
            raw["confidence"] = round(min(0.95, raw["confidence"] + 0.05), 2)
        raw["reason_codes"] = raw["reason_codes"][:8]
        return build_action(context, raw)

    def describe(self):
        return {"provider": "mock", "seed": self.seed, "unsafe_rate": self.unsafe_rate}


class RuleBasedProvider(LLMProvider):
    """Non-LLM deterministic baseline controller (still passes through the shield)."""

    name, source = "baseline", "baseline"

    async def generate_action(self, context: dict[str, Any]) -> EnergyAction:
        return build_action(context, baseline_policy(context))


class FailingProvider(LLMProvider):
    """Simulates an unavailable LLM API to exercise the fallback path."""

    name, source = "failing", "llm"

    async def generate_action(self, context: dict[str, Any]) -> EnergyAction:
        raise LLMUnavailableError("simulated LLM outage")


class FaultInjectingProvider(LLMProvider):
    """Wraps another provider and replaces chosen agent/step proposals by intentionally unsafe or
    malformed ones (scenario fault injection). The shield must stop them."""

    def __init__(self, inner: LLMProvider, faults: list[dict[str, Any]]):
        self.inner, self.faults = inner, faults
        self.name, self.source = inner.name, inner.source

    def _match(self, ctx: dict[str, Any]) -> dict[str, Any] | None:
        for f in self.faults:
            if f["agent_id"] == ctx["agent_id"] and f["from_step"] <= ctx["step"] <= f["to_step"]:
                return f
        return None

    async def generate_action(self, context: dict[str, Any]) -> EnergyAction:
        return (await self.generate(context))[0]

    async def generate(self, context: dict[str, Any]) -> tuple[EnergyAction, str]:
        f = self._match(context)
        if f is None:
            return await self.inner.generate(context)
        if f.get("kind") == "malformed":
            raise LLMOutputError("injected malformed model output")
        act = EnergyAction(agent_id=context["agent_id"], action_type=f["action_type"], power_kw=f["power_kw"],
                           duration_minutes=int(f.get("duration_minutes", context["dt_minutes"])),
                           target_node=f.get("target_node"), reason_codes=["INJECTED_FAULT"], confidence=0.99)
        return act, "injected"

    def describe(self):
        return {**self.inner.describe(), "fault_injection": True}
