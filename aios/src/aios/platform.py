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
from aios.sources.marketing_extra import marketing_extra_tools
from aios.sources.connectors import all_connectors
from aios.sources.sales import lead_tools
from aios.sources.domains import (finance_tools, operations_tools,
                                  legal_tools, hr_tools, catalog_tools)
from aios.sources.outputs import output_tool
from aios.sources.n8n import n8n_tool, n8n_workflows_tool
from aios.command import CommandRouter
from aios.prospecting import Prospector, prospects_tool
from aios.tools import Tool
from aios.agents.marketing import MarketingAgent
from aios.agents.domain import DomainAgent
from aios.agents.sales_config import SALES_CONFIG
from aios.agents.finance_config import FINANCE_CONFIG
from aios.agents.operations_config import OPERATIONS_CONFIG
from aios.agents.legal_config import LEGAL_CONFIG
from aios.agents.hr_config import HR_CONFIG


class Platform:
    """K2-OS: kernel condiviso + sensori + conoscenza + agenti di dominio."""

    def __init__(self, kernel: Kernel, agents: dict[str, Any], commands: Any = None) -> None:
        self.kernel = kernel
        self.agents = agents
        self.commands = commands   # CommandRouter (chat a istruzioni), impostato dopo

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
    for t in marketing_extra_tools(client):
        k.register_tool(t)
    for t in lead_tools(client):
        k.register_tool(t)
    for factory in (finance_tools, operations_tools, legal_tools, hr_tools, catalog_tools):
        for t in factory(client):
            k.register_tool(t)
    for t in all_connectors():          # connettori esterni env-gated (graceful [])
        if t.name == "leggi_inbox":
            continue                    # sostituito sotto: posta via tabella inbox_messages (n8n)
        k.register_tool(t)
    k.register_tool(n8n_tool())         # braccio esecutore esterno (env-gated)
    k.register_tool(n8n_workflows_tool())  # sensore: elenco workflow n8n (readonly)
    k.register_tool(prospects_tool(client))  # sensore: prospect marketing (readonly)
    # leggi_inbox via tabella alimentata da n8n (Outlook OAuth) — override dell'IMAP,
    # che il tenant MFA/Conditional Access blocca. Degrada a [] se la tabella è vuota.
    def _inbox_table():
        try:
            return client.select("email_messages",
                                 {"select": "*", "direction": "eq.in",
                                  "order": "received_at.desc", "limit": "30"})
        except Exception:
            return []
    k.register_tool(Tool(name="leggi_inbox", action_type=None, readonly=True,
                         run=lambda **_: _inbox_table()))
    from aios.sources.n8n import N8N_ACTION
    from aios.autonomy import AutonomyLevel as _AL
    k.policy.set_level(N8N_ACTION, _AL.L1_PROPOSE)   # esterno: mai autonomo
    k.policy.set_cap(N8N_ACTION, _AL.L1_PROPOSE)

    founder = default_founder_model()
    skills = SkillLibrary()
    knowledge = KnowledgeStore(client)
    llm = AnthropicLLM(max_tokens=4096)
    # Sonnet per i casi delicati (schema DB / codice / workflow) via CommandRouter
    llm_strong = AnthropicLLM(model="claude-sonnet-4-6", max_tokens=8192)

    def _domain(cfg):
        return DomainAgent(kernel=k, llm=llm, founder=founder, config=cfg,
                           skills=skills, knowledge=knowledge, deliverable_client=client)

    agents = {
        "marketing": MarketingAgent(kernel=k, llm=llm, founder=founder, skills=skills),
        "vendite": _domain(SALES_CONFIG),
        "finance": _domain(FINANCE_CONFIG),
        "operations": _domain(OPERATIONS_CONFIG),
        "legal": _domain(LEGAL_CONFIG),
        "hr": _domain(HR_CONFIG),
    }
    platform = Platform(k, agents)
    platform.commands = CommandRouter(platform, llm, llm_strong)   # chat a istruzioni
    # Prospecting: ricerca web (Sonnet + web search) → qualifica → bozza (mai inviata)
    llm_web = AnthropicLLM(model="claude-sonnet-4-6", max_tokens=4096, enable_web_search=True)
    def _suite():
        try:
            return k.execute("leggi_suite", actor="prospector", args={}).result
        except Exception:
            return []
    platform.prospector = Prospector(llm_web, llm_strong, founder, suite_reader=_suite)
    from aios.conversation import ConversationManager
    platform._founder = founder
    platform.conversations = ConversationManager(platform, llm_strong)  # email L1 assistito
    return platform
