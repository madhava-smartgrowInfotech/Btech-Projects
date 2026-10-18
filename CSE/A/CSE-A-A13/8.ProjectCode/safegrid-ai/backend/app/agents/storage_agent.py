from typing import Any

from app.agents.base_agent import BaseAgent


class StorageAgent(BaseAgent):
    """EV / storage node: charging demand, SOC target, price and grid responsiveness."""
    role = "ev_storage"

    def extra_context(self, obs: dict[str, Any]) -> dict[str, Any]:
        n = obs["nodes"][self.node_id]
        return {"ev": {"connected": bool(n["storage_available"]), "required_soc": self.options.get("required_soc", 0.80),
                       "critical_soc": self.options.get("critical_soc", 0.30),
                       "v2g_enabled": bool(self.options.get("v2g_enabled", False))}}
