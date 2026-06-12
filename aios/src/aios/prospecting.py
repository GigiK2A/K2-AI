"""Prospecting qualificato per il Marketing.

L'AI cerca sul web PMI italiane REALI in target ICP, le VALUTA (fit, non fuffa),
trova la mail (responsabile o aziendale) e prepara una BOZZA di primo contatto.
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
    "Sei un analista commerciale B2B di K2-AI. Cerchi sul web PMI italiane REALI e "
    "VERIFICABILI in target con l'ICP qui sotto. NON inventare aziende, dati o email. "
    "Per ogni azienda riporta: nome, sito ufficiale, settore, dimensione stimata, "
    "perché è (o NON è) in target per i nostri servizi, e una mail di contatto reale "
    "(del responsabile se la trovi, altrimenti quella aziendale generica) con la FONTE. "
    "Scarta esplicitamente chi è fuori target (multinazionali, micro-partite IVA non "
    "rilevanti, settori non nostri): non vogliamo fuffa. Se non trovi una mail reale, "
    "scrivilo chiaramente invece di inventarla."
)

_STRUCT_SYS = (
    "Struttura i risultati della ricerca in JSON. Per ogni azienda valuta il fit con "
    "i nostri servizi (fit_score 0-100) e spiega in 1 frase perché è un possibile "
    "cliente o perché è fuffa. Se non c'è una mail reale lascia contact_email vuoto. "
    "Prepara una BOZZA di primo contatto in italiano, brand voice K2-AI (pragmatica, "
    "del 'tu', numeri concreti, niente buzzword), 5-8 righe, specifica per quell'azienda "
    "e per il servizio più adatto. La bozza NON verrà inviata: è solo una proposta da "
    "rivedere. Non inventare numeri o dati non presenti nella ricerca."
)

_SCHEMA = {
    "type": "object",
    "properties": {"prospects": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "company": {"type": "string"}, "website": {"type": "string"},
            "sector": {"type": "string"}, "in_target": {"type": "boolean"},
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
            out += "\n\n# NOSTRI SERVIZI (cosa vendiamo)\n" + "\n".join(f"- {n}" for n in names)
        return out

    def find(self, n: int = 5) -> list[dict]:
        ctx = self._context()
        user_research = (ctx + f"\n\n# COMPITO\nTrova {n} PMI italiane reali e in target, "
                         "ben qualificate (no fuffa), con mail di contatto reale e fonte.")
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
