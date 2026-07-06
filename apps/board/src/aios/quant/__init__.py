"""Calcolatori DETERMINISTICI vendorizzati dal motore 8e (finance + tax).

Sono gli STESSI motori che alimentano FinanceBoost/FiscoBoost del K-BOT: numeri veri,
provenance normativa, aliquote da tabella grounding (mai dall'LLM). Qui esposti come
`calcola(operazione, params)` così un agente del board può ottenere indici di bilancio
e carico fiscale REALI invece di stimarli a occhio.

Fonte: kai-website/k2a-8e/app/{finance,tax}.py (pure-python, stdlib). Vendorizzati perché
il board si deploya da apps/board (build context separato) e l'8e non espone un endpoint
di calcolo. La tabella grounding fiscale è una copia (quant/grounding/): se le aliquote
cambiano lato 8e, va ri-vendorizzata.
"""
from __future__ import annotations

from typing import Any

from . import finance, tax


def _voci(params: dict) -> list[dict]:
    v = params.get("voci")
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def indici_bilancio(params: dict) -> dict:
    """Riclassifica il bilancio e calcola indici (D/E, ROE, current/quick ratio, ecc.).
    params: {voci:[{sezione:attivo|passivo|ricavi|costi|risultato, descrizione, importo}],
             anno?:int, wacc_pct?:float}."""
    voci = _voci(params)
    if not voci:
        return {"error": "servono 'voci' (lista {sezione, descrizione, importo})"}
    anno = params.get("anno")
    reclass = finance.reclassify_bilancio(voci, anno if isinstance(anno, int) else None)
    out: dict[str, Any] = {
        "riclassificazione": finance.build_riclassificazione(reclass),
        "indici": finance.build_indici(reclass),
        "marginalita": finance.build_marginalita(reclass),
    }
    wacc = params.get("wacc_pct")
    if isinstance(wacc, (int, float)):
        out["valutazione"] = finance.build_valutazione(reclass, float(wacc))
    warn = reclass.get("warnings")
    if warn:
        out["note"] = warn
    return out


def carico_fiscale(params: dict) -> dict:
    """Stima IRES/IRPEF + IRAP di una PMI (aliquote da tabella grounding).
    params: {forma_giuridica:str, imponibile_eur:float, valore_produzione_irap_eur?:float,
             anno?:int}."""
    fg = str(params.get("forma_giuridica") or "").strip()
    imp = tax._num(params.get("imponibile_eur"))
    if not fg or imp is None:
        return {"error": "servono 'forma_giuridica' e 'imponibile_eur'"}
    vp = tax._num(params.get("valore_produzione_irap_eur"))
    note_vp = None
    if vp is None:                       # se non dato, approssimo IRAP sull'imponibile
        vp = imp
        note_vp = ("valore_produzione_irap_eur non fornito: IRAP stimata sull'imponibile "
                   "(approssimazione — fornisci il valore della produzione per l'esatto)")
    anno = params.get("anno")
    res = tax.carico_fiscale_stimato(fg, imp, vp,
                                     anno=anno if isinstance(anno, int) else 2026)
    if note_vp:
        res.setdefault("note", []).insert(0, note_vp)
    return res


def imposta(params: dict) -> dict:
    """Singola imposta. params: {tipo:'irpef'|'ires'|'irap'|'iva', base?:float,
    tipo_iva?:'ordinaria'|...}."""
    t = str(params.get("tipo") or "").strip().lower()
    base = tax._num(params.get("base"))
    if t == "irpef":
        return tax.irpef_lorda(base or 0.0)
    if t == "ires":
        return tax.ires(base or 0.0)
    if t == "irap":
        return tax.irap(base or 0.0)
    if t == "iva":
        return tax.iva_aliquota(str(params.get("tipo_iva") or "ordinaria"))
    return {"error": "tipo imposta non valido (irpef|ires|irap|iva)"}


_OPS = {
    "indici_bilancio": indici_bilancio,
    "carico_fiscale": carico_fiscale,
    "imposta": imposta,
    "aliquote": lambda _p: {"aliquote": tax.aliquote_riepilogo(),
                            "norme": tax.norme_riferimento()},
}

OPERAZIONI = tuple(_OPS)


def calcola(operazione: str, params: dict | None = None) -> dict:
    """Dispatcher deterministico. `operazione` ∈ OPERAZIONI; `params` dizionario input.
    Non solleva: gli errori tornano come {'error': ...} (no-dead-end)."""
    fn = _OPS.get(str(operazione or "").strip().lower())
    if fn is None:
        return {"error": f"operazione sconosciuta: {operazione}",
                "disponibili": list(_OPS)}
    try:
        return fn(params or {})
    except Exception as exc:
        return {"error": str(exc)[:200]}
