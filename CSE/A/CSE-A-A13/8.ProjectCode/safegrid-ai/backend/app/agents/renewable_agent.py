from app.agents.base_agent import BaseAgent


class RenewableAgent(BaseAgent):
    """Renewable prosumer: larger PV, local load, optional battery; may curtail to protect voltage."""
    role = "renewable_prosumer"
