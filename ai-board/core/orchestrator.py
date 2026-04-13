from typing import Optional

from loguru import logger

from agents.chief_of_staff import ChiefOfStaffAgent
from agents.content_engine import ContentEngineAgent
from agents.finance_kpi import FinanceKpiAgent
from agents.geo_seo import GeoSeoAgent
from agents.legal import LegalAgent
from agents.market_intelligence import MarketIntelligenceAgent
from agents.orchestrator import OrchestratorAgent
from agents.sales_enablement import SalesEnablementAgent
from agents.solution_architect import SolutionArchitectAgent
from db.models import AgentName

AGENT_REGISTRY: dict[AgentName, type] = {
    AgentName.ORCHESTRATOR: OrchestratorAgent,
    AgentName.CHIEF_OF_STAFF: ChiefOfStaffAgent,
    AgentName.CONTENT_ENGINE: ContentEngineAgent,
    AgentName.MARKET_INTELLIGENCE: MarketIntelligenceAgent,
    AgentName.SALES_ENABLEMENT: SalesEnablementAgent,
    AgentName.SOLUTION_ARCHITECT: SolutionArchitectAgent,
    AgentName.FINANCE_KPI: FinanceKpiAgent,
    AgentName.LEGAL: LegalAgent,
    AgentName.GEO_SEO: GeoSeoAgent,
}

AGENT_ALIAS_MAP: dict[AgentName, AgentName] = {
    AgentName.OFFER_POSITIONING: AgentName.CONTENT_ENGINE,
    AgentName.BRAND_STRATEGY: AgentName.CONTENT_ENGINE,
    AgentName.MARKETING_STRATEGY: AgentName.CONTENT_ENGINE,
    AgentName.LEAD_GENERATION: AgentName.SALES_ENABLEMENT,
    AgentName.OUTREACH: AgentName.SALES_ENABLEMENT,
    AgentName.PROJECT_OPERATIONS: AgentName.CHIEF_OF_STAFF,
    AgentName.KNOWLEDGE: AgentName.CHIEF_OF_STAFF,
    AgentName.RISK_REVIEW: AgentName.FINANCE_KPI,
}


def resolve_agent_name(name: AgentName | str) -> AgentName:
    if isinstance(name, str):
        name = AgentName(name)
    return AGENT_ALIAS_MAP.get(name, name)


def related_agent_names(name: AgentName | str) -> list[AgentName]:
    canonical = resolve_agent_name(name)
    aliases = [alias for alias, target in AGENT_ALIAS_MAP.items() if target == canonical]
    return [canonical, *aliases]


def get_agent(name: AgentName):
    """Istanzia e restituisce un agente per nome."""
    canonical_name = resolve_agent_name(name)
    cls = AGENT_REGISTRY.get(canonical_name)
    if not cls:
        raise ValueError(f"Agente non trovato: {canonical_name}")
    return cls()


def chat_agent(name: AgentName, message: str, context: Optional[dict] = None) -> str:
    """Risposta conversazionale da un agente specifico (no approval, no task DB)."""
    canonical_name = resolve_agent_name(name)
    logger.info(f"Chat agente: {canonical_name.value}")
    agent = get_agent(canonical_name)
    return agent.chat(message, context)


def run_agent(name: AgentName, task: str, context: Optional[dict] = None) -> dict:
    """Esegue un agente specifico e restituisce il risultato."""
    canonical_name = resolve_agent_name(name)
    logger.info(f"Esecuzione agente: {canonical_name.value}")
    agent = get_agent(name)
    return agent.run(task, context)


def run_objective(objective: str) -> dict:
    """
    Punto di ingresso principale: ricevi un obiettivo dal fondatore,
    passa all'Orchestrator per il piano, poi esegui i task.
    Restituisce il piano dell'Orchestrator.
    """
    logger.info(f"Nuovo obiettivo ricevuto: {objective[:80]}...")
    orchestrator = OrchestratorAgent()
    plan = orchestrator.run(objective)
    logger.info(f"Piano generato: {plan.get('approval_id', 'N/A')}")
    return plan


def list_agents() -> list[str]:
    """Lista di tutti gli agenti disponibili."""
    return [name.value for name in AGENT_REGISTRY.keys()]
