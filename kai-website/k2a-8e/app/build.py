"""Binder BuildBoost — determinismo aritmetico + onestà su oneri/CME.

Cosa diventa deterministico (math pura):
- `costi.totale_eur = lavori + professionisti + oneri + contingency` (somma, non fabbricata).

Cosa NON è cablabile (nessun tool/tabella → flag, non fabbricato):
- `costi.oneri_eur` / `iter.oneri_comunali_eur`: oneri di urbanizzazione PER-COMUNE →
  serve la tabella comunale, non esiste tool → stima LLM, marcata `non_validato`.
- `costi.lavori_eur`: computo metrico → serve un prezzario, nessun tool → stima LLM.
- `iter.tempo_totale_mesi` / `vincoli[].tempo_gg`: tempi d'iter autorizzativo → variano
  per comune/intervento, nessuna fonte deterministica → stima LLM.
"""
from __future__ import annotations

from typing import Any, Optional

_VOCI_COSTO = ["lavori_eur", "professionisti_eur", "oneri_eur", "contingency_eur"]


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("€", "").replace(" ", "").replace(".", "").replace(",", "."))
    except ValueError:
        return None


def bind_costi_totale(deliverable: dict) -> dict:
    costi = deliverable.get("costi")
    if not isinstance(costi, dict):
        return {"ricalcolato": False, "note": "costi assente"}
    presenti = {k: _num(costi.get(k)) for k in _VOCI_COSTO if _num(costi.get(k)) is not None}
    if not presenti:
        return {"ricalcolato": False, "note": "nessuna voce di costo presente"}
    totale = round(sum(presenti.values()), 2)
    costi["totale_eur"] = totale
    return {"ricalcolato": True, "totale_eur": totale, "voci_sommate": list(presenti),
            "provenance": "somma deterministica delle voci di costo"}


def flag_oneri_non_validati(deliverable: dict) -> list[str]:
    flags: list[str] = []
    costi = deliverable.get("costi")
    if isinstance(costi, dict):
        if _num(costi.get("oneri_eur")) is not None:
            flags.append("costi.oneri_eur: stima LLM (oneri urbanizzazione per-comune, nessuna tabella) — totale è somma deterministica")
        if _num(costi.get("lavori_eur")) is not None:
            flags.append("costi.lavori_eur: stima LLM (computo metrico, nessun prezzario)")
    it = deliverable.get("iter")
    if isinstance(it, dict) and (_num(it.get("oneri_comunali_eur")) is not None or _num(it.get("tempo_totale_mesi")) is not None):
        flags.append("iter.oneri_comunali_eur / tempo_totale_mesi: stima LLM (variano per comune, nessuna fonte deterministica)")
    return flags


def apply_build(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    if not isinstance(deliverable, dict):
        return deliverable, None
    costi_meta = bind_costi_totale(deliverable)
    flags = flag_oneri_non_validati(deliverable)
    return deliverable, {
        "costi_totale": costi_meta,
        "voci_non_validate": flags,
        "note": "totale_eur = somma deterministica; oneri/lavori/tempi = stima LLM (tabelle/prezzari assenti)",
    }
