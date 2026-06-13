"""Competitor intelligence autonoma per il Marketing.

L'agente cerca sul web i competitor/riferimenti ITALIANI nello spazio ICP
(AI operativa per PMI, automazione processi, agenzie/studi che vendono AI alle
PMI), li profila (offerta, posizionamento, prezzo, forze/debolezze, minaccia) e
li salva in `marketing_competitors`. Nessun input umano: niente lista di URL da
dare, li trova l'AI. Dati readonly, nessuna azione esterna.
"""
from __future__ import annotations

from typing import Any

from aios.tools import Tool

_RESEARCH_SYS = (
    "Sei un analista di mercato di K2-AI. Cerchi sul web competitor e riferimenti "
    "ITALIANI reali e verificabili nello stesso spazio dell'ICP qui sotto: AI operativa "
    "per PMI, automazione processi, agenzie/studi/software house che vendono progetti AI "
    "alle PMI italiane. NON inventare aziende, dati o URL. Per ognuno riporta: nome, sito "
    "ufficiale, cosa offre concretamente, posizionamento, fascia di prezzo se nota, punti "
    "di forza e debolezze, e perché è rilevante per noi. Scarta le multinazionali "
    "generaliste (OpenAI, Google, Microsoft) e chi è fuori dal mercato italiano: vogliamo "
    "i veri concorrenti diretti su cui ci confrontiamo, non i colossi."
)

_STRUCT_SYS = (
    "Struttura i competitor trovati in JSON. Per ognuno valuta la minaccia per noi "
    "(threat 0-100: quanto ci toglie clienti nello stesso target) e spiega in 1 frase "
    "come K2-AI si differenzia. Non inventare dati non presenti nella ricerca: se un "
    "campo non risulta, lascialo vuoto. Niente colossi internazionali, solo concorrenti "
    "reali sul mercato PMI italiano."
)

_SCHEMA = {
    "type": "object",
    "properties": {"competitors": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"}, "website": {"type": "string"},
            "offering": {"type": "string"}, "positioning": {"type": "string"},
            "pricing": {"type": "string"}, "strengths": {"type": "string"},
            "weaknesses": {"type": "string"}, "threat": {"type": "integer"},
            "differentiation": {"type": "string"}, "source": {"type": "string"}},
        "required": ["name", "threat"]}}},
    "required": ["competitors"],
}


def _as_list(x) -> list[dict]:
    return [i for i in x if isinstance(i, dict)] if isinstance(x, list) else []


class CompetitorScout:
    """Trova + profila competitor italiani in modo autonomo (web search → DB)."""

    def __init__(self, llm_web: Any, llm_struct: Any, founder: Any,
                 suite_reader: Any = None) -> None:
        self.llm_web = llm_web        # AnthropicLLM con web search
        self.llm_struct = llm_struct  # LLM per output strutturato (Sonnet)
        self.founder = founder
        self.suite_reader = suite_reader  # callable -> lista servizi (catalogo)

    def _context(self) -> str:
        out = self.founder.to_prompt() if self.founder else ""
        try:
            suite = self.suite_reader() if self.suite_reader else []
        except Exception:
            suite = []
        names = []
        for s in (suite or [])[:25]:
            if isinstance(s, dict):
                v = s.get("Servizio") or s.get("servizio") or s.get("nome") or s.get("name")
                if v:
                    names.append(str(v))
        if names:
            out += "\n\n# NOSTRI SERVIZI (cosa vendiamo)\n" + "\n".join(f"- {n}" for n in names)
        return out

    def find(self, n: int = 6) -> list[dict]:
        ctx = self._context()
        user_research = (ctx + f"\n\n# COMPITO\nTrova {n} competitor/riferimenti italiani "
                         "reali nello stesso spazio, con sito ufficiale e fonte. Solo "
                         "concorrenti veri sul mercato PMI IT, niente colossi globali.")
        research = self.llm_web.complete(system=_RESEARCH_SYS, user=user_research)
        parsed = self.llm_struct.complete_json(
            system=_STRUCT_SYS,
            user=ctx + "\n\n# RISULTATI RICERCA WEB (grezzi, da strutturare)\n"
                 + str(research)[:8000],
            schema=_SCHEMA)
        return _as_list(parsed.get("competitors"))

    @staticmethod
    def to_row(c: dict) -> dict:
        """Mappa un competitor alla riga DB (status 'nuovo')."""
        return {
            "name": str(c.get("name") or "")[:200],
            "website": str(c.get("website") or "")[:300] or None,
            "offering": str(c.get("offering") or "")[:1000] or None,
            "positioning": str(c.get("positioning") or "")[:500] or None,
            "pricing": str(c.get("pricing") or "")[:200] or None,
            "strengths": str(c.get("strengths") or "")[:1000] or None,
            "weaknesses": str(c.get("weaknesses") or "")[:1000] or None,
            "threat": int(c.get("threat") or 0),
            "differentiation": str(c.get("differentiation") or "")[:1000] or None,
            "source": str(c.get("source") or "")[:300] or None,
            "status": "nuovo",
        }


def competitors_tool(client: Any) -> Tool:
    """Sensore readonly: competitor trovati dall'agente (degrada a [] se la tabella manca)."""
    def _run(**_):
        try:
            return client.select("marketing_competitors",
                                 {"select": "*", "order": "threat.desc"})
        except Exception:
            return []
    return Tool(name="leggi_competitor_trovati", action_type=None, readonly=True, run=_run)
