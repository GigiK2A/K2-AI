from __future__ import annotations

import os
from typing import Any

from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.llm import AnthropicLLM
from aios.skills import SkillLibrary
from aios.layers.knowledge import KnowledgeStore
from aios.sources.instagram import InstagramClient
from aios.sources.tools import (content_tools_rest, instagram_tools,
                                insights_tools, competitor_lookup_tool)
from aios.sources.calendar import calendar_tools
from aios.sources.sales import lead_tools
from aios.sources.outputs import output_tool
from aios.agents.marketing import MarketingAgent
from aios.agents.domain import DomainAgent
from aios.agents.sales_config import SALES_CONFIG


class Platform:
    """K2-OS: kernel condiviso + sensori + conoscenza + agenti di dominio."""

    def __init__(self, kernel: Kernel, agents: dict[str, Any]) -> None:
        self.kernel = kernel
        self.agents = agents

    def domains(self) -> list[str]:
        return list(self.agents)

    def run(self, domain: str) -> dict[str, Any]:
        if domain not in self.agents:
            raise KeyError(domain)
        res = self.agents[domain].run()
        return {"domain": domain,
                "proposte": len(getattr(res, "proposals", []) or []),
                "calendario": len(getattr(res, "calendar", []) or [])}

    def deliverables(self) -> list[dict[str, Any]]:
        return self.kernel._supabase.select(
            "aios_deliverables", {"select": "*", "order": "id.desc"})


def build_platform() -> Platform:
    k = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                  os.environ["AIOS_SUPABASE_SERVICE_KEY"])
    client = k._supabase
    ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                         ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))
    k.register_tool(output_tool(client))
    for t in content_tools_rest(client):
        k.register_tool(t)
    for t in instagram_tools(ig):
        k.register_tool(t)
    for t in insights_tools(ig):
        k.register_tool(t)
    k.register_tool(competitor_lookup_tool(ig))
    for t in calendar_tools(client):
        k.register_tool(t)
    for t in lead_tools(client):
        k.register_tool(t)

    founder = default_founder_model()
    skills = SkillLibrary()
    knowledge = KnowledgeStore(client)
    llm = AnthropicLLM(max_tokens=4096)
    agents = {
        "marketing": MarketingAgent(kernel=k, llm=llm, founder=founder, skills=skills),
        "vendite": DomainAgent(kernel=k, llm=llm, founder=founder, config=SALES_CONFIG,
                               skills=skills, knowledge=knowledge, deliverable_client=client),
    }
    return Platform(k, agents)
