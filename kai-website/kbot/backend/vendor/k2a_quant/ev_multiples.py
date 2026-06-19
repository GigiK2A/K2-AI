"""ev_from_multiples — EV dai multipli di settore dello snapshot (spec Luca §1.4).

EBITDA>0 → EV/EBITDA; EBITDA≤0 → EV/Ricavi (nel tool, deterministico). Sempre con
snapshot_as_of e settore_usato (flag fallback_default se il settore non è mappato).
"""
from __future__ import annotations

from .calc_result import calc_result
from . import snapshot as snap


def ev_from_multiples(settore: str, ebitda_eur: float, ricavi_eur: float, snapshot: dict) -> dict:
    inputs = {"settore": settore, "ebitda_eur": ebitda_eur, "ricavi_eur": ricavi_eur}
    asof = snap.snapshot_as_of(snapshot)

    # --- Sentinelle ATECO (PARTE D): messaggi onesti, non l'errore generico ---
    if settore == "non_coperto":
        return calc_result("ev_from_multiples", inputs, snapshot_as_of=asof,
                           errore={"code": "settore_non_coperto",
                                   "settore": settore,
                                   "messaggio": "Settore non coperto dallo snapshot Damodaran W.Europe: valutazione settoriale non disponibile (es. agricoltura/pesca). Usare metodi alternativi (asset-based, comparables specifici)."})
    if settore == "non_applicabile":
        return calc_result("ev_from_multiples", inputs, snapshot_as_of=asof,
                           errore={"code": "settore_non_applicabile",
                                   "settore": settore,
                                   "messaggio": "Ente non-impresa (PA, organizzazioni, attività di famiglie): valutazione di mercato non applicabile."})

    sec = snap.sector(snapshot, settore)
    fallback = False
    if not sec:
        sec = snap.sector(snapshot, "default")
        fallback = True
    if not sec or sec.get("ev_ebitda") is None or sec.get("ev_sales") is None:
        return calc_result("ev_from_multiples", inputs, snapshot_as_of=asof,
                           errore={"code": "multipli_assenti", "settore": settore})

    if ebitda_eur is not None and ebitda_eur > 0:
        mult = sec["ev_ebitda"]
        ev = ebitda_eur * mult
        metodo = f"EV/EBITDA {mult}x"
    else:
        mult = sec["ev_sales"]
        ev = (ricavi_eur or 0) * mult
        metodo = f"EV/Ricavi {mult}x (EBITDA non positivo)"

    warnings = ["settore_fallback_default"] if fallback else []
    outputs = {"ev_eur": round(ev, 2), "metodo": metodo, "multiplo_usato": mult,
               "settore_usato": "default" if fallback else settore, "fallback_default": fallback}
    trace = [{"step": 1, "descrizione": "EV da multiplo di settore", "formula": metodo,
              "valori": {"base": ebitda_eur if (ebitda_eur and ebitda_eur > 0) else ricavi_eur, "x": mult, "ev": round(ev, 2)}}]
    return calc_result("ev_from_multiples", inputs, outputs, snapshot_as_of=asof, trace=trace, warnings=warnings)
