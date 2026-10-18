from app.agents.base_agent import BaseAgent


class ProsumerAgent(BaseAgent):
    """Residential prosumer: household load + rooftop solar + battery."""
    role = "residential_prosumer"
