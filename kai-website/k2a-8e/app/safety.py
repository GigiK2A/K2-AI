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
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace("%", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        elif s.count(".") > 1:
            s = s.replace(".", "")  # più punti, nessuna virgola → separatori migliaia IT
        try:
            return float(s)
        except ValueError:
            return None
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


def bind_obblighi(deliverable: dict, inputs: dict) -> Optional[dict]:
    """Obblighi Titolo IV D.Lgs 81/08 DETERMINISTICI (no LLM): con PIÙ imprese esecutrici
    (anche non contemporanee, art.90 c.3-4) scattano INSIEME CSP, CSE e PSC (art.100) — l'LLM
    ne sbagliava la coerenza (es. PSC+CSE sì ma CSP no, impossibile: è il CSP che redige il PSC).
    Notifica preliminare (art.99): con >1 impresa OPPURE entità ≥200 uomini-giorno OPPURE rischi
    particolari Allegato XI. None se manca `num_imprese` (senza il dato non si asserisce)."""
    ob = deliverable.get("obblighi")
    if not isinstance(ob, dict) or not isinstance(inputs, dict):
        return None
    cant = deliverable.get("cantiere") or {}
    n_imprese = _num(inputs.get("num_imprese"))
    if n_imprese is None:
        n_imprese = _num(cant.get("num_imprese"))
    if n_imprese is None:
        return None
    ug = _num(inputs.get("uomini_giorno")) or _num(cant.get("uomini_giorno"))
    rs = inputs.get("rischi_speciali") or cant.get("rischi_speciali") or []
    has_rischi = bool(rs) if isinstance(rs, (list, str)) else False
    piu_imprese = n_imprese > 1
    ob["psc_necessario"] = piu_imprese
    ob["csp_necessario"] = piu_imprese          # ⇐ coerente con PSC: stessa condizione
    ob["cse_necessario"] = piu_imprese
    ob["notifica_necessaria"] = bool(piu_imprese or (ug is not None and ug >= 200) or has_rischi)
    deliverable["obblighi"] = ob
    return {"num_imprese": n_imprese, "piu_imprese": piu_imprese, "uomini_giorno": ug,
            "fonte": "art. 90/99/100 D.Lgs 81/2008 (Titolo IV)"}


def flag_costi_non_validati(deliverable: dict) -> list[str]:
    flags: list[str] = []
    cs = deliverable.get("costi_sicurezza")
    if isinstance(cs, dict) and any(_num(cs.get(k)) is not None for k in _COMPONENTI):
        flags.append("costi_sicurezza.* (apprestamenti/dpi/…): stima LLM (nessun prezzario Allegato XV) — totale e incidenza sono però somme deterministiche")
    return flags


def apply_safety(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    if not isinstance(deliverable, dict):
        return deliverable, None
    n_rischi = bind_rischi(deliverable)
    costi_meta = bind_costi_sicurezza(deliverable)
    obblighi_meta = bind_obblighi(deliverable, inputs)
    flags = flag_costi_non_validati(deliverable)
    return deliverable, {
        "rischi_ricalcolati_pxd": n_rischi,
        "costi_sicurezza": costi_meta,
        "obblighi_titolo_iv": obblighi_meta,
        "voci_non_validate": flags,
        "note": "R=P×D + totale/incidenza + obblighi PSC/CSP/CSE/notifica deterministici; "
                "singole voci di costo = stima LLM (tool prezzario assente)",
    }
