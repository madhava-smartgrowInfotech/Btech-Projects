"""BaseAgent: perceive -> decide. An agent can only *propose*; it never touches the grid."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from app.agents.policy import cost_aware_policy
from app.llm.base import LLMProvider
from app.llm.mock_provider import build_action
from app.models.actions import EnergyAction


@dataclass
class AgentDecision:
    agent_id: str
    node_id: str
    action: EnergyAction
    decision_source: str  # llm | mock | fallback | baseline | injected
    latency_ms: float
    fallback_reason: str | None
    context: dict[str, Any]


class BaseAgent:
    role = "generic"

    def __init__(self, agent_id: str, node_id: str, provider: LLMProvider, timeout_s: float = 20.0, options: dict | None = None):
        self.agent_id, self.node_id, self.provider, self.timeout_s = agent_id, node_id, provider, timeout_s
        self.options = options or {}
        self.last: dict[str, Any] | None = None  # previous action + result, fed back into the next context

    # ---- perceive ------------------------------------------------------------------------
    def extra_context(self, obs: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def perceive(self, obs: dict[str, Any]) -> dict[str, Any]:
        n, lim, cons = obs["nodes"][self.node_id], obs["limits"][self.node_id], obs["constraints"]
        avail = bool(n["storage_available"]) and lim.storage_capacity_kwh > 0
        ctx = {
            "agent_id": self.agent_id, "node_id": self.node_id, "role": self.role, "step": obs["step"], "time": obs["time"],
            "dt_minutes": obs["dt_minutes"],
            "load_kw": round(n["load_kw"], 3), "solar_kw": round(n["pv_kw"], 3),
            "battery": {"available": avail, "capacity_kwh": lim.storage_capacity_kwh, "soc": round(n["soc"], 4),
                        "max_charge_kw": lim.max_charge_kw if avail else 0.0, "max_discharge_kw": lim.max_discharge_kw if avail else 0.0,
                        "soc_min": lim.soc_min, "soc_max": lim.soc_max},
            "electricity_price": round(obs["price"], 3), "price_stats": obs["price_stats"], "weather": obs["weather"],
            "neighboring_nodes": {nid: {"net_exchange_kw": round(o["exchange_kw"], 3), "battery_soc": round(o["soc"], 3),
                                        "voltage_pu": round(o["voltage_pu"], 4)}
                                  for nid, o in obs["nodes"].items() if nid != self.node_id},
            "grid_constraints": {"v_min": cons.v_min, "v_max": cons.v_max, "line_max_loading_pct": cons.line_max_loading_pct,
                                 "node_import_limit_kw": lim.max_import_kw, "node_export_limit_kw": lim.max_export_kw,
                                 "local_voltage_pu": round(n["voltage_pu"], 4),
                                 "worst_line_loading_pct": obs["trial_summary"]["max_line_loading_pct"],
                                 "trafo_loading_pct": obs["trial_summary"]["trafo_loading_pct"]},
            "previous_action": self.last,
        }
        ctx.update(self.extra_context(obs))
        return ctx

    # ---- decide -----------------------------------------------------------------------------
    def fallback_policy(self, ctx: dict[str, Any]) -> EnergyAction:
        return build_action(ctx, cost_aware_policy(ctx))

    async def decide(self, ctx: dict[str, Any]) -> AgentDecision:
        t0 = time.perf_counter()
        reason = None
        try:
            action, source = await asyncio.wait_for(self.provider.generate(ctx), timeout=self.timeout_s)
        except Exception as e:  # any provider failure -> labelled deterministic fallback (still shielded)
            reason = f"{type(e).__name__}: {str(e)[:160]}"
            action, source = self.fallback_policy(ctx), "fallback"
        return AgentDecision(self.agent_id, self.node_id, action, source, (time.perf_counter() - t0) * 1000.0, reason, ctx)

    def remember(self, entry: dict[str, Any]) -> None:
        self.last = entry
