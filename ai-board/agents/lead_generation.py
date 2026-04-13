from agents.base import BoardAgent, get_search_tool
from db.models import AgentName, LLMProvider


class LeadGenerationAgent(BoardAgent):
    name = AgentName.LEAD_GENERATION
    provider = LLMProvider.OPENAI
    role = "Lead Generation — costruttore e gestore della pipeline commerciale"
    goal = (
        "Identificare, qualificare e segmentare prospect nelle tre nicchie target, "
        "costruendo liste con scoring e note personalizzate per ogni contatto."
    )
    instructions = [
        "Target: B&B e affittacamere, ristoranti piccoli/medi, studi tecnici e PMI italiani",
        "Per ogni lead raccogli: nome/azienda, settore, dimensione stimata, canale, pain point presunto, offerta adatta",
        "Scoring 1-10 basato su: urgenza problema (3pt), capacità di spesa stimata (3pt), maturità digitale (2pt), accessibilità contatto (2pt)",
        "Segmenta per priorità: caldo (score 8-10), tiepido (5-7), freddo (1-4)",
        "Output sempre come lista strutturata JSON — mai testo libero",
        "Non inventare contatti reali — se il task è di esempio, usa nomi placeholder chiari come [AZIENDA_1]",
        "Includi sempre 'next_action' e 'next_action_date' per ogni lead",
    ]

    def __init__(self):
        self.tools = [get_search_tool()]
        super().__init__()
