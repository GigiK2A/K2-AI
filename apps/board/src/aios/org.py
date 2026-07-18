"""Organigramma del board: ruoli, titoli e linee di riporto (Paperclip #2).

Prima l'AIOS aveva agenti piatti, senza gerarchia: nessuno "sapeva" chi fosse,
a chi riportasse o chi fossero i colleghi. Paperclip fa esattamente questo — "the
mental model is a company you are running" — con org chart e deleghe.

Qui l'organigramma è dato (persistibile) e viene:
- **iniettato nel contesto** di ogni agente ("sei il Direttore Finance, riporti al
  CEO, i tuoi pari sono …") → l'agente resta nel suo mandato e sa quando delegare;
- usato dal **CEO** per instradare/delegare al ruolo giusto;
- esposto via API `/api/org`.

Chiave = actor id dell'agente (finance_agent, marketing_agent, …), così combacia
con il metering (billing) e con `DomainAgent.actor`. Il CEO è la radice ("ceo").
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OrgRole:
    key: str                       # actor id (o "ceo" per la radice)
    title: str                     # titolo leggibile
    reports_to: Optional[str]      # key del manager (None = radice)
    mandate: str = ""              # una riga: di cosa risponde


# Organigramma di default di K2-AI: CEO + 6 direzioni di dominio.
DEFAULT_ROLES: list[OrgRole] = [
    OrgRole("ceo", "CEO del board", None,
            "Visione, priorità, delega ai direttori e sintesi delle decisioni."),
    OrgRole("finance_agent", "Direttore Finance & Controllo", "ceo",
            "Conti, KPI, cassa, prezzi, sostenibilità economica."),
    OrgRole("marketing_agent", "Direttore Marketing & Contenuti", "ceo",
            "Brand, contenuti, campagne, acquisizione."),
    OrgRole("vendite_agent", "Direttore Vendite", "ceo",
            "Pipeline, lead, offerte, trattative."),
    OrgRole("operations_agent", "Direttore Operations", "ceo",
            "Progetti, consegne, scadenze, capacità del team."),
    OrgRole("legal_agent", "Responsabile Legale & Compliance", "ceo",
            "Contratti, GDPR, rischi legali, adempimenti."),
    OrgRole("hr_agent", "Responsabile HR", "ceo",
            "Persone, assunzioni, competenze, clima."),
]


class OrgChart:
    """Organigramma navigabile. Immutabile dopo la costruzione."""

    def __init__(self, roles: list[OrgRole]) -> None:
        self._roles: dict[str, OrgRole] = {r.key: r for r in roles}

    # -- costruzione -------------------------------------------------------
    @classmethod
    def default(cls) -> "OrgChart":
        """Default + override opzionale via env AIOS_ORG_JSON.
        Formato: [{"key","title","reports_to","mandate"}, ...] (sostituisce tutto)."""
        raw = os.environ.get("AIOS_ORG_JSON", "").strip()
        if raw:
            try:
                roles = [OrgRole(key=r["key"], title=r["title"],
                                 reports_to=r.get("reports_to"), mandate=r.get("mandate", ""))
                         for r in json.loads(raw)]
                if roles:
                    return cls(roles)
            except Exception:
                pass
        return cls(list(DEFAULT_ROLES))

    # -- navigazione -------------------------------------------------------
    def get(self, key: str) -> Optional[OrgRole]:
        return self._roles.get(key)

    def title(self, key: str) -> str:
        r = self._roles.get(key)
        return r.title if r else key

    def manager_of(self, key: str) -> Optional[OrgRole]:
        r = self._roles.get(key)
        if not r or not r.reports_to:
            return None
        return self._roles.get(r.reports_to)

    def reports_of(self, key: str) -> list[OrgRole]:
        return [r for r in self._roles.values() if r.reports_to == key]

    def peers_of(self, key: str) -> list[OrgRole]:
        r = self._roles.get(key)
        if not r:
            return []
        return [o for o in self._roles.values()
                if o.reports_to == r.reports_to and o.key != key]

    def roster(self) -> list[OrgRole]:
        """Tutti i ruoli operativi (esclusa la radice) — per il CEO che delega."""
        return [r for r in self._roles.values() if r.reports_to is not None]

    def as_dict(self) -> list[dict]:
        return [{"key": r.key, "title": r.title, "reports_to": r.reports_to,
                 "mandate": r.mandate} for r in self._roles.values()]

    # -- contesto per il prompt -------------------------------------------
    def context_for(self, key: str) -> str:
        """Blocco da iniettare nel system/prompt dell'agente: chi è, a chi riporta,
        chi sono i pari, quando delegare."""
        r = self._roles.get(key)
        if not r:
            return ""
        mgr = self.manager_of(key)
        peers = self.peers_of(key)
        lines = ["## IL TUO RUOLO NEL BOARD",
                 f"Sei il **{r.title}** di K2-AI." + (f" {r.mandate}" if r.mandate else "")]
        if mgr:
            lines.append(f"Riporti al **{mgr.title}**: le decisioni fuori dal tuo mandato "
                         "le proponi a lui, non le prendi da solo.")
        if peers:
            colleghi = ", ".join(f"{p.title}" for p in peers)
            lines.append(f"I tuoi pari nel board: {colleghi}. "
                         "Se una proposta ricade nel loro perimetro, segnalalo e lascia a loro "
                         "l'azione invece di sconfinare.")
        return "\n".join(lines)

    def roster_context(self) -> str:
        """Elenco dei ruoli per il CEO che deve delegare al direttore giusto."""
        righe = "\n".join(f"- {r.title} ({r.key}): {r.mandate}" for r in self.roster())
        return "## DIREZIONI DEL BOARD (a chi delegare)\n" + righe


# ── Singleton di processo, cablato da build_platform ──────────────────────────
_CHART: Optional[OrgChart] = None
_LOCK = threading.Lock()


def set_chart(chart: OrgChart) -> None:
    global _CHART
    with _LOCK:
        _CHART = chart


def get_chart() -> OrgChart:
    global _CHART
    if _CHART is None:
        with _LOCK:
            if _CHART is None:
                _CHART = OrgChart.default()
    return _CHART
