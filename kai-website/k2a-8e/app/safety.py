"""Binder SafetyBoost — determinismo aritmetico + onestà sui costi.

Cosa diventa deterministico (math pura, nessun dato esterno richiesto):
- `rischi[].r = p × d` (matrice P×D=R, metodologia D.Lgs 81/08) — non più incoerente.
- `costi_sicurezza.totale = Σ componenti` (apprestamenti+misure+dpi+impianti+procedure).
- `costi_sicurezza.incidenza_pct = totale / importo_lavori × 100`.

Cosa NON è cablabile (nessun tool/prezzario → flag, non fabbricato):
- le SINGOLE voci di costo (apprestamenti, dpi, …) richiedono i prezzi Allegato XV:
  non esiste un tool → restano stima LLM, marcate `non_validato` nel meta.
- soglie obbligo PSC/CSP/CSE (art. 90/99): servono uomini-giorno + n. imprese verificati
  e l'algoritmo di legge — nessun tool nel 8e → non asserite come deterministiche.

Binding strutturale: lo slot riceve il numero corretto, l'LLM non lo genera.
"""
from __future__ import annotations

from typing import Any, Optional

_COMPONENTI = ["apprestamenti", "misure_preventive", "dpi", "impianti", "procedure"]


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("€", "").replace(" ", "").replace(".", "").replace(",", "."))
    except ValueError:
        return None


def bind_rischi(deliverable: dict) -> int:
    """r = p × d per ogni rischio dove p e d sono presenti. Ritorna n. corretti."""
    rischi = deliverable.get("rischi")
    if not isinstance(rischi, list):
        return 0
    n = 0
    for r in rischi:
        if not isinstance(r, dict):
            continue
        p, d = _num(r.get("p")), _num(r.get("d"))
        if p is not None and d is not None:
            r["r"] = int(round(p * d))
            n += 1
    return n


def bind_costi_sicurezza(deliverable: dict) -> dict:
    cs = deliverable.get("costi_sicurezza")
    if not isinstance(cs, dict):
        return {"ricalcolato": False, "note": "costi_sicurezza assente"}
    presenti = {k: _num(cs.get(k)) for k in _COMPONENTI if _num(cs.get(k)) is not None}
    if not presenti:
        return {"ricalcolato": False, "note": "nessuna componente di costo presente"}
    totale = round(sum(presenti.values()), 2)
    cs["totale"] = totale
    importo = _num((deliverable.get("cantiere") or {}).get("importo_lavori"))
    inc = None
    if importo and importo > 0:
        inc = round(totale / importo * 100, 2)
        cs["incidenza_pct"] = inc
    return {"ricalcolato": True, "totale": totale, "incidenza_pct": inc,
            "componenti_sommate": list(presenti),
            "provenance": "somma deterministica delle componenti (no prezzario Allegato XV)"}


def flag_costi_non_validati(deliverable: dict) -> list[str]:
    flags: list[str] = []
    cs = deliverable.get("costi_sicurezza")
    if isinstance(cs, dict) and any(_num(cs.get(k)) is not None for k in _COMPONENTI):
        flags.append("costi_sicurezza.* (apprestamenti/dpi/…): stima LLM (nessun prezzario Allegato XV) — totale e incidenza sono però somme deterministiche")
    if isinstance(deliverable.get("soglie"), (dict, list)) or "psc" in str(deliverable).lower():
        flags.append("obbligo PSC/CSP/CSE: non asserito deterministicamente (serve algoritmo art.90/99 + uomini-giorno verificati)")
    return flags


def apply_safety(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    if not isinstance(deliverable, dict):
        return deliverable, None
    n_rischi = bind_rischi(deliverable)
    costi_meta = bind_costi_sicurezza(deliverable)
    flags = flag_costi_non_validati(deliverable)
    return deliverable, {
        "rischi_ricalcolati_pxd": n_rischi,
        "costi_sicurezza": costi_meta,
        "voci_non_validate": flags,
        "note": "R=P×D + totale/incidenza deterministici; singole voci di costo = stima LLM (tool prezzario assente)",
    }
