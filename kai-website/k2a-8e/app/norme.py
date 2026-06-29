"""Cabla k2a_norme_tecniche (vendorizzato) — riferimenti normativi tecnici per BuildBoost.

`search()` sul corpus norme (NTC 2018 / CEI / Eurocodici). KB attualmente **VUOTA**
(scaffold NT-1): `search` torna 0 risultati onesti finché Luca non ingerisce il corpus →
nessun riferimento inventato. I risultati vanno in `filiera_meta` (BuildBoost non ha uno
slot deliverable per le citazioni tecniche; il surfacing nel report = aggiunta schema,
decisione prodotto). Quando il corpus c'è, i riferimenti sono reali e verbatim.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))


def is_available() -> bool:
    """True se il corpus norme è caricato e interrogabile: FTS su un termine comune
    delle NTC ('calcestruzzo'). Usato dall'health-check (cerca_riferimenti fa AND di
    molti termini → inadatto come sonda di disponibilità)."""
    try:
        from k2a_norme_tecniche.schemas import SearchInput
        from k2a_norme_tecniche.tools import search
        out = search(SearchInput(query="calcestruzzo", limit=1))
        return bool(list(getattr(out, "risultati", []) or []))
    except Exception:
        return False


def cerca_riferimenti(inputs: dict, limit: int = 5) -> dict:
    try:
        from k2a_norme_tecniche.schemas import SearchInput
        from k2a_norme_tecniche.tools import search
    except Exception as e:  # pragma: no cover
        return {"disponibile": False, "note": f"k2a_norme_tecniche non importabile: {e}"}
    inputs = inputs or {}
    intervento = str(inputs.get("tipo_intervento") or inputs.get("destinazione_progetto") or "").strip()
    if not intervento:
        return {"disponibile": False, "note": "nessun intervento per la query norme"}
    q = f"{intervento} distanze altezze volumetria titolo abilitativo"
    try:
        out = search(SearchInput(query=q, limit=limit))
        hits = list(getattr(out, "risultati", []) or [])
    except Exception as e:
        return {"disponibile": False, "query": q, "note": f"search norme fallita: {e}"}
    refs = [{"documento": h.documento, "paragrafo": h.paragrafo,
             "titolo": h.titolo, "snippet": (h.snippet or "")[:200]} for h in hits]
    return {
        "disponibile": True, "query": q, "n_riferimenti": len(refs), "riferimenti": refs,
        "note": ("KB norme VUOTA (scaffold NT-1): 0 riferimenti finché Luca non ingerisce il corpus (NTC2018/CEI/Eurocodici)"
                 if not refs else "riferimenti dal corpus norme tecniche"),
        "provenance": "k2a_norme_tecniche.search (vendorizzato)",
    }


def apply_norme(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    if not isinstance(deliverable, dict):
        return deliverable, None
    return deliverable, cerca_riferimenti(inputs)
