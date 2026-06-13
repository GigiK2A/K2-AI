from __future__ import annotations

from aios.agents.marketing import MarketingAgent


class AutomationLayer:
    """Strato (4) Automazione: esegue agenti/skill che producono deliverable."""

    def __init__(self, agent: MarketingAgent) -> None:
        self.agent = agent

    def run(self):
        return self.agent.run()
