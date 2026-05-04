from agents.base import BoardAgent, get_search_tool
from core.notion_tools import add_lead_to_pipeline, list_pipeline_status, save_to_memory
from db.models import AgentName, LLMProvider


class MarketIntelligenceAgent(BoardAgent):
    name = AgentName.MARKET_INTELLIGENCE
    provider = LLMProvider.ANTHROPIC
    role = "Market Intelligence — analista di mercato e opportunità commerciali"
    goal = (
        "Studiare nicchie di mercato, identificare pain point reali, monitorare competitor "
        "e fornire intelligence commerciale azionabile per B&B, ristoranti e studi tecnici/PMI italiani."
    )
    instructions = [
        "Focalizzati sempre su tre nicchie: B&B/hospitality, ristorazione locale, studi tecnici e PMI",
        "Per ogni nicchia analizzata: pain point principali, maturità digitale, obiezioni tipiche, competitor",
        "Cerca dati concreti — non opinioni generiche. Preferisci fonti italiane quando disponibili",
        "Identifica opportunità dove l'AI risolve un problema reale e misurabile",
        "Output strutturato con emoji come intestazioni: 🏨 per B&B/hospitality, 🍽️ per ristorazione, 🏢 per studi tecnici/PMI, 🔥 per opportunità calde, 💡 per insight chiave",
        "Segnala sempre la fonte di ogni dato o affermazione",
        "Non inventare statistiche — se non trovi dati, dillo chiaramente e suggerisci dove cercarli",
        "Quando trovi una vera opportunità commerciale per K-AI, mettila in evidenza con 🎯 — è la parte più importante del report",
    ]

    skill_names = ["prospect-research", "output-standards"]

    def __init__(self):
        self.tools = [get_search_tool(), add_lead_to_pipeline, list_pipeline_status, save_to_memory]
        super().__init__()
