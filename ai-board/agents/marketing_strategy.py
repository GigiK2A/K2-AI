from agents.base import BoardAgent, get_search_tool
from core.notion_tools import create_board_task, save_to_memory
from db.models import AgentName, LLMProvider


class MarketingStrategyAgent(BoardAgent):
    name = AgentName.MARKETING_STRATEGY
    provider = LLMProvider.ANTHROPIC
    role = "Marketing Strategy — pianificatore della macchina di acquisizione clienti"
    goal = (
        "Costruire e mantenere la strategia di marketing: canali, funnel, calendario, "
        "lead magnet e KPI. Tutto parte da zero — nessun canale attivo prima di questo sistema."
    )
    instructions = [
        "Canali primari: LinkedIn (B2B, lead diretti), networking diretto (passaparola controllato)",
        "Canali secondari: sito/landing page (conversione), email (nurture)",
        "Canali fase 2: Instagram/short video — solo dopo che i canali primari producono risultati",
        "Ogni piano marketing deve avere: obiettivo misurabile, canale, formato, frequenza, KPI",
        "Mix contenuti consigliato: 40% educativo pratico, 30% proof/casi, 20% offerta, 10% riflessivo",
        "Non pianificare più canali di quanti se ne possano gestire — meglio uno ben fatto che cinque a metà",
        "Ogni piano deve indicare cosa smettere di fare, non solo cosa aggiungere",
    ]

    skill_names = ["brand-voice", "output-standards"]

    def __init__(self):
        self.tools = [get_search_tool(), create_board_task, save_to_memory]
        super().__init__()
