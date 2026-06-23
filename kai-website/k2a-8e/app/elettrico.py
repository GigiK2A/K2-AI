"""Binder MepBoost `audit_elettrico` — cabla k2a_elettrico (vendorizzato, import libreria).

Calcoli deterministici dal MCP elettrico (non più dall'LLM):
- **caduta di tensione** per circuito (CEI 64-8 / 525, limite 4%) → `caduta_tensione`.
- **verifica impianto di terra** (TT / TN) → `verifica_terra`.

FEED: legge la sezione opzionale `impianto_elettrico_dettaglio` del form
(`sistema_terra`, `RA_ohm`, `circuiti[]` con corrente/lunghezza/sezione). Se assente →
`audit_elettrico` resta **non valutabile** onesto (il form dell'audit energetico non porta
i parametri per-circuito) — nessun numero inventato. Quando il form li porta, il calcolo è reale.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

_LIMITE_CDT_PCT = 4.0


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def _check_circuito(c: dict) -> Optional[dict]:
    from k2a_elettrico.caduta_v import CadutaVInput, caduta_tensione

    I, L, S = _num(c.get("corrente_a")), _num(c.get("lunghezza_m")), _num(c.get("sezione_mm2"))
    if None in (I, L, S) or I <= 0 or L <= 0 or S <= 0:
        return None
    sistema = c.get("sistema") if c.get("sistema") in ("trifase", "monofase") else "trifase"
    vn = _num(c.get("tensione_v")) or (400.0 if sistema == "trifase" else 230.0)
    o = caduta_tensione(CadutaVInput(I=I, L=L, sezione_mm2=S, sistema=sistema, Vn=vn,
                                     cosfi=_num(c.get("cosfi")) or 0.9))
    return {"nome": c.get("nome", "circuito"), "delta_v_pct": round(o.delta_V_percento, 2),
            "conforme": bool(o.verifica_CEI_525)}


def _check_terra(d: dict) -> Optional[dict]:
    from k2a_elettrico.terra import VerificaTerraInput, verifica_terra

    sistema = d.get("sistema_terra") if d.get("sistema_terra") in ("TT", "TN-S", "TN-C", "TN-C-S") else "TT"
    kw: dict[str, Any] = {"sistema": sistema}
    if _num(d.get("RA_ohm")) is not None:
        kw["RA_ohm"] = _num(d.get("RA_ohm"))
    if _num(d.get("Idn_RCD_mA")) is not None:
        kw["Idn_RCD_mA"] = _num(d.get("Idn_RCD_mA"))
    o = verifica_terra(VerificaTerraInput(**kw))
    return {"verifica_ok": bool(o.verifica_ok), "criterio": o.criterio,
            "valore": round(o.valore_calcolato, 3), "limite": round(o.valore_limite, 3)}


def bind_audit_elettrico(deliverable: dict, inputs: dict) -> dict:
    det = (inputs or {}).get("impianto_elettrico_dettaglio")
    if not isinstance(det, dict):
        return {"verificato": False,
                "note": "audit_elettrico non valutabile: manca impianto_elettrico_dettaglio nel form (FEED per-circuito assente)"}
    nc: list[dict] = []
    n_circ = 0
    for c in (det.get("circuiti") or []):
        if not isinstance(c, dict):
            continue
        r = _check_circuito(c)
        if r is None:
            continue
        n_circ += 1
        if not r["conforme"]:
            nc.append({
                "descrizione": f"Caduta di tensione {r['delta_v_pct']}% sul circuito '{r['nome']}' oltre il limite {_LIMITE_CDT_PCT}%",
                "norma": "CEI 64-8 (CEI 525)", "gravita": "maggiore",
                "azione": "Aumentare la sezione del conduttore o ridurre la lunghezza della linea",
            })
    terra = None
    if det.get("sistema_terra") or _num(det.get("RA_ohm")) is not None:
        terra = _check_terra(det)
        if terra and not terra["verifica_ok"]:
            nc.append({
                "descrizione": f"Impianto di terra non conforme ({terra['criterio']}): {terra['valore']} oltre il limite {terra['limite']}",
                "norma": "CEI 64-8 art. 413", "gravita": "critica",
                "azione": "Adeguare dispersore / coordinamento con RCD",
            })
    if n_circ == 0 and terra is None:
        return {"verificato": False,
                "note": "audit_elettrico non valutabile: nessun circuito/terra valido nel dettaglio"}
    ae = deliverable.setdefault("audit_elettrico", {})
    ae["conforme_dm37"] = len(nc) == 0
    ae["non_conformita"] = nc
    return {"verificato": True, "circuiti_verificati": n_circ, "terra_verificata": terra is not None,
            "non_conformita": len(nc),
            "provenance": "k2a_elettrico.caduta_tensione/verifica_terra (CEI 64-8) — vendorizzato"}


def apply_elettrico(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    if not isinstance(deliverable, dict):
        return deliverable, None
    return deliverable, bind_audit_elettrico(deliverable, inputs)
