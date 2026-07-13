"""Prospecting qualificato per il Marketing.

L'AI cerca sul web PMI italiane REALI che sarebbero CLIENTI (acquirenti dei nostri
servizi, in settori ICP) — NON concorrenti né fornitori del nostro stesso spazio.
Le VALUTA (fit col bisogno, non somiglianza a noi), trova la mail e prepara una BOZZA.
La bozza è SOLO una bozza: viene salvata in `marketing_prospects`, MAI inviata
in automatico (nessun canale di invio è collegato a questo flusso).
"""
from __future__ import annotations

import json
from typing import Any

from aios.autonomy import ActionType
from aios.tools import Tool

PROSPECT_ACTION = ActionType("marketing", "prospect")

_RESEARCH_SYS = (
    "Sei un analista commerciale B2B di K2-AI. K2-AI VENDE sistemi AI operativi (agenti "
    "email/CRM, automazioni amministrative, microapp documentali, RAG) ALLE PMI italiane. "
    "Devi trovare CLIENTI POTENZIALI = aziende che COMPREREBBERO questi servizi perché "
    "hanno processi manuali/ripetitivi da automatizzare. NON cerchi fornitori come noi.\n"
    "TARGET (ICP) — cerca QUI: PMI e partite IVA italiane IN UMBRIA E LAZIO (province di "
    "Perugia, Terni, Roma, Latina, Frosinone, Rieti, Viterbo): studi professionali "
    "(ingegneria, architettura, commercialisti, consulenza), manifatturiero e PMI "
    "industriali, servizi B2B; indicativamente 5-50 dipendenti, fatturato ~500k-10M €. "
    "Il focus geografico UMBRIA + LAZIO è VINCOLANTE: scarta aziende fuori da queste regioni.\n"
    "ESCLUDI TASSATIVAMENTE (NON sono clienti, sono concorrenti o pari-categoria): "
    "agenzie digitali/marketing, software house, system integrator, società di "
    "consulenza IT/AI, chi già vende AI/automazione/RPA/chatbot/sviluppo software, "
    "startup tech, big tech. Se un'azienda fa più o meno quello che facciamo noi, NON è "
    "un prospect: scartala. Escludi anche multinazionali e micro-partite IVA non rilevanti.\n"
    "Per ogni CLIENTE valido riporta: nome, sito ufficiale, settore, dimensione stimata, "
    "il PROBLEMA operativo concreto che potremmo risolvergli, e una mail di contatto reale "
    "(responsabile o aziendale) con la FONTE. NON inventare aziende, dati o email: se non "
    "trovi una mail reale, dillo."
)

_STRUCT_SYS = (
    "Struttura in JSON i CLIENTI POTENZIALI trovati. REGOLA DURA: se l'azienda OFFRE essa "
    "stessa AI/automazione/software/consulenza digitale/marketing (è un concorrente o un "
    "fornitore del nostro stesso spazio, NON un cliente) → in_target=false, fit_score basso, "
    "fit_reason='concorrente/stesso settore, non un cliente'. Un cliente valido è una PMI di "
    "ALTRO settore (studio professionale, manifatturiero, servizi B2B) con un processo "
    "concreto da automatizzare. Valuta il fit (0-100) col bisogno del cliente, non con la "
    "somiglianza a noi. Se non c'è una mail reale lascia contact_email vuoto. Prepara una "
    "BOZZA di primo contatto in italiano, brand voice K2-AI (pragmatica, del 'tu', numeri "
    "concreti, niente buzzword), 5-8 righe, specifica per quell'azienda e il suo problema. "
    "La bozza NON verrà inviata. Non inventare numeri o dati non presenti nella ricerca.\n"
    "GEO: riporta 'region' (Umbria/Lazio + provincia). Se l'azienda è FUORI da Umbria e "
    "Lazio → in_target=false e fit_score basso: cerchiamo solo lì."
)

_SCHEMA = {
    "type": "object",
    "properties": {"prospects": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "company": {"type": "string"}, "website": {"type": "string"},
            "sector": {"type": "string"}, "region": {"type": "string"},
            "in_target": {"type": "boolean"},
            "fit_score": {"type": "integer"}, "fit_reason": {"type": "string"},
            "contact_email": {"type": "string"}, "contact_role": {"type": "string"},
            "email_source": {"type": "string"},
            "draft_subject": {"type": "string"}, "draft_body": {"type": "string"}},
        "required": ["company", "in_target", "fit_score", "fit_reason"]}}},
    "required": ["prospects"],
}


def _as_list(x) -> list[dict]:
    return [i for i in x if isinstance(i, dict)] if isinstance(x, list) else []


class Prospector:
    """Trova + qualifica PMI in target e prepara bozze di contatto (mai inviate)."""

    def __init__(self, llm_web: Any, llm_struct: Any, founder: Any,
                 suite_reader: Any = None) -> None:
        self.llm_web = llm_web        # AnthropicLLM con web search
        self.llm_struct = llm_struct  # LLM per output strutturato (Sonnet)
        self.founder = founder
        self.suite_reader = suite_reader  # callable -> lista servizi (catalogo)

    def _context(self) -> str:
        out = self.founder.to_prompt()
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
            out += ("\n\n# COSA OFFRIAMO AI CLIENTI (per abbinare il servizio al problema)\n"
                    + "\n".join(f"- {n}" for n in names))
        out += ("\n\n# CHI CERCHIAMO\nClienti potenziali = PMI o partite IVA italiane IN UMBRIA "
                "E LAZIO (studi professionali, manifatturiero, servizi B2B; 5-50 dip.) con "
                "processi manuali da automatizzare, che COMPREREBBERO i nostri servizi. Il "
                "vincolo geografico Umbria+Lazio è tassativo.\n# CHI ESCLUDERE\nChi fa il nostro stesso "
                "mestiere o lo fornisce: agenzie, software house, system integrator, consulenza "
                "IT/AI, chi vende AI/automazione/software. Quelli sono CONCORRENTI, non clienti.")
        return out

    def find(self, n: int = 5) -> list[dict]:
        ctx = self._context()
        user_research = (ctx + f"\n\n# COMPITO\nTrova {n} CLIENTI POTENZIALI reali — PMI o "
                         "partite IVA italiane IN UMBRIA E LAZIO che comprerebbero i nostri "
                         "servizi, NON concorrenti né fornitori del nostro spazio. Settori ICP, "
                         "indica regione/provincia, mail di contatto reale e fonte. No fuffa.")
        research = self.llm_web.complete(system=_RESEARCH_SYS, user=user_research)
        parsed = self.llm_struct.complete_json(
            system=_STRUCT_SYS,
            user=ctx + "\n\n# RISULTATI RICERCA WEB (grezzi, da strutturare)\n"
                 + str(research)[:8000],
            schema=_SCHEMA)
        return _as_list(parsed.get("prospects"))

    @staticmethod
    def to_row(p: dict) -> dict:
        """Mappa un prospect alla riga DB (status 'nuovo'; bozza salvata, non inviata)."""
        return {
            "company": str(p.get("company") or "")[:200],
            "website": str(p.get("website") or "")[:300] or None,
            "sector": str(p.get("sector") or "")[:120] or None,
            "fit_score": int(p.get("fit_score") or 0),
            "fit_reason": str(p.get("fit_reason") or "")[:1000] or None,
            "contact_email": str(p.get("contact_email") or "")[:200] or None,
            "contact_role": str(p.get("contact_role") or "")[:120] or None,
            "email_source": str(p.get("email_source") or "")[:300] or None,
            "draft_subject": str(p.get("draft_subject") or "")[:300] or None,
            "draft_body": str(p.get("draft_body") or "")[:4000] or None,
            "status": "nuovo",
        }


def prospects_tool(client: Any) -> Tool:
    """Sensore readonly: prospect trovati/qualificati (degrada a [] se la tabella manca)."""
    def _run(**_):
        try:
            return client.select("marketing_prospects",
                                 {"select": "*", "order": "created_at.desc"})
        except Exception:
            return []
    return Tool(name="leggi_prospects", action_type=None, readonly=True, run=_run)
