from __future__ import annotations

from aios.autonomy import ActionType
from aios.agents.domain import DomainConfig

SALES_CONFIG = DomainConfig(
    name="vendite",
    action=ActionType("vendite", "azione"),
    tool_name="proponi_vendite",
    sensors=[("leggi_lead", {})],
    system=(
        "Sei il responsabile vendite di K2-AI. Rispetti il Founder Model e la "
        "conoscenza K2-AI. Analizza i lead reali (status, score, pain point, ultima "
        "azione) e proponi azioni concrete: follow-up mirati, prossimo passo, "
        "qualificazione, recupero lead fermi. Non scrivere ai clienti: PROPONI soltanto."
    ),
    skill_focus=[],
    knowledge_query="vendite lead PMI offerta servizi",
)
