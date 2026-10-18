"""AgentManager: builds agents and runs perception/decision for all of them concurrently."""
from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base_agent import AgentDecision, BaseAgent
from app.agents.prosumer_agent import ProsumerAgent
from app.agents.renewable_agent import RenewableAgent
from app.agents.storage_agent import StorageAgent
from app.llm.base import LLMProvider

ROLE_CLASS = {"residential_prosumer": ProsumerAgent, "ev_storage": StorageAgent, "renewable_prosumer": RenewableAgent}


class AgentManager:
    def __init__(self, node_specs, provider: LLMProvider, timeout_s: float = 20.0, agent_options: dict[str, dict] | None = None):
        agent_options = agent_options or {}
        self.agents: dict[str, BaseAgent] = {}
        for n in node_specs:
            opts = agent_options.get(n.agent_id, {})
            self.agents[n.agent_id] = ROLE_CLASS[n.role](n.agent_id, n.node_id, provider, timeout_s, opts)
        self.provider = provider
        self.latest: dict[str, dict[str, Any]] = {a: {} for a in self.agents}

    def by_node(self, node_id: str) -> BaseAgent:
        return next(a for a in self.agents.values() if a.node_id == node_id)

    async def perceive_all(self, obs: dict[str, Any]) -> dict[str, dict[str, Any]]:
        res = await asyncio.gather(*(a.perceive(obs) for a in self.agents.values()))
        return {a.agent_id: c for a, c in zip(self.agents.values(), res)}

    async def decide_all(self, contexts: dict[str, dict[str, Any]]) -> list[AgentDecision]:
        return list(await asyncio.gather(*(self.agents[aid].decide(ctx) for aid, ctx in contexts.items())))
