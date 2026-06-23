"""Binder economici AdvisorBoost (SPEC wiring-economici §A-§D).

Riduce gli slot ancora-LLM di AdvisorBoost bindando numeri da fonti deterministiche:
- §A EV-synth: aggrega i metodi (EV-multipli dal quant + valore patrimoniale) → valore
  raccomandato + range + spread. DCF escluso se non disponibile (no FCF nel form).
- §B DuPont: scomposizione ROE = ROS(net)×rotazione×leva dal bilancio reale.
- §C CCII: alert crisi DETERMINABILI dal bilancio (PN, PFN/EBITDA); gli altri (DSCR,
  ritardi, CCN) NON valutabili dai dati del form → marcati onesti, non inventati.
- §D CTA: fail-closed — nessun prezzo retainer inventato (non è a catalogo).

Structural binding (lo slot riceve il valore, non lo genera l'LLM) + provenance nel meta.
"""
from __future__ import annotations

from typing import Any, Optional

_W_MULTIPLI, _W_DCF, _W_PATRIM = 0.5, 0.3, 0.2          # pesi se DCF disponibile
_W_MULTIPLI_NODCF, _W_PATRIM_NODCF = 0.6, 0.4           # pesi se DCF assente (documentati)


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("€", "").replace(" ", "").replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _latest_bilancio(inputs: dict) -> Optional[dict]:
    bs = [b for b in (inputs.get("bilanci") or []) if isinstance(b, dict)]
    if not bs:
        return None
    wy = [b for b in bs if _num(b.get("anno")) is not None]
    b = max(wy, key=lambda b: _num(b.get("anno"))) if wy else bs[-1]
    # In produzione il bilancio arriva come VOCI grezze: riclassifico con finance.py per avere
    # gli aggregati (ricavi/ebitda/utile/PN/attivo/debiti) che DuPont/CCII/EV leggono —
    # altrimenti b.get('ricavi') ecc. sono assenti e tutto §A-§D gira a vuoto.
    try:
        from . import finance
        return finance.enrich_bilancio(b)
    except Exception:
        return b


def bind_dupont(deliverable: dict, b: dict) -> None:
    ricavi, utile = _num(b.get("ricavi")), _num(b.get("utile_netto"))
    attivo, pn = _num(b.get("totale_attivo")), _num(b.get("patrimonio_netto"))
    if not (ricavi and attivo and pn):
        return
    roe = round(utile / pn * 100, 2) if (utile is not None and pn) else None
    ros = round(utile / ricavi * 100, 2) if utile is not None else None   # margine netto (per l'identità)
    rot = round(ricavi / attivo, 4)
    leva = round(attivo / pn, 4)
    scomp_ok = None
    if None not in (roe, ros):
        scomp_ok = abs(ros / 100 * rot * leva * 100 - roe) < 0.5
    deliverable.setdefault("indici", {})["dupont"] = {
        "roe_anno_n": roe, "ros_anno_n": ros, "rotazione_anno_n": rot,
        "leva_anno_n": leva, "scomposizione_ok": bool(scomp_ok),
    }


def bind_ev_synth(deliverable: dict, b: dict) -> dict:
    ev = deliverable.setdefault("enterprise_value", {})
    multipli = _num((ev.get("multipli_ebitda") or {}).get("ev_mediano_eur"))
    dcf_eq = _num((ev.get("dcf") or {}).get("equity_value_eur"))
    pn = _num(b.get("patrimonio_netto"))
    ebitda = _num(b.get("ebitda"))
    ev.setdefault("patrimoniale", {})["valore_eur"] = pn
    methods = {"multipli": multipli, "dcf": dcf_eq, "patrimoniale": pn}
    present = {k: v for k, v in methods.items() if v is not None}
    if not present:
        return {"valore_raccomandato": None, "note": "nessun metodo di valutazione disponibile"}
    if "dcf" in present:
        w = {"multipli": _W_MULTIPLI, "dcf": _W_DCF, "patrimoniale": _W_PATRIM}
    else:
        w = {"multipli": _W_MULTIPLI_NODCF, "patrimoniale": _W_PATRIM_NODCF}
    wsum = sum(w[k] for k in present if k in w) or 1.0
    racc = round(sum(present[k] * w.get(k, 0) for k in present) / wsum, 2)
    vals = list(present.values())
    ev["valore_raccomandato_eur"] = racc
    ev["range_plausibile_eur"] = {"min": round(min(vals), 2), "max": round(max(vals), 2)}
    if racc:
        ev["spread_percentuale"] = round((max(vals) - min(vals)) / racc * 100, 1)
    return {"valore_raccomandato": racc, "metodi_usati": list(present),
            "dcf_incluso": "dcf" in present,
            "note": ("DCF escluso: FCF previsti non nel form" if "dcf" not in present else None)}


def _sem_pn(pn: Optional[float]) -> str:
    if pn is None:
        return "giallo"
    return "rosso" if pn <= 0 else "verde"


def bind_ccii(deliverable: dict, b: dict) -> None:
    pn = _num(b.get("patrimonio_netto"))
    ebitda = _num(b.get("ebitda"))
    debiti_fin = _num(b.get("debiti_finanziari"))
    det: list[dict] = []
    # determinabili dal bilancio
    det.append({"tipo": "PN_negativo_o_sotto_soglia", "stato": _sem_pn(pn),
                "commento": f"patrimonio netto {pn}€" if pn is not None else "PN assente"})
    if ebitda and ebitda > 0 and debiti_fin is not None:
        ratio = debiti_fin / ebitda
        stato = "rosso" if ratio > 6 else ("giallo" if ratio >= 4 else "verde")
        det.append({"tipo": "PFN_EBITDA_oltre_6", "stato": stato,
                    "commento": f"debiti finanziari/EBITDA ≈ {round(ratio,2)} (proxy: liquidità non nel form → PFN non netta)"})
    # NON determinabili dai dati del form → onesto, non inventato
    for tipo, manca in [("DSCR_12m_sotto_1", "DSCR / cash flow prospettico"),
                        ("ritardi_oltre_90gg", "scadenziario fornitori/erario"),
                        ("CCN_negativo_persistente", "attivo/passivo corrente storico")]:
        det.append({"tipo": tipo, "stato": "giallo",
                    "commento": f"non valutabile dai dati del form (serve {manca})"})
    alert_attivi = sum(1 for d in det if d["stato"] == "rosso")
    deliverable.setdefault("indici", {})["ccii"] = {
        "alert_attivi": alert_attivi, "dettaglio": det,
        "raccomandazione_turnaround": bool(alert_attivi >= 2 or (pn is not None and pn <= 0)),
    }


def bind_cta(deliverable: dict) -> dict:
    # fail-closed: il retainer NON è un prezzo a catalogo → non si inventa.
    deliverable["cta"] = {"retainer_attivo": False, "prezzo_retainer_mensile_eur": 0.0}
    return {"note": "CTA retainer fail-closed: prezzo non a catalogo, da configurare (nessun valore inventato)"}


def apply_advisor(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    """Applica i binding economici §A-§D al deliverable AdvisorBoost. Da chiamare DOPO
    quant.bind_quant_slots (che popola enterprise_value.multipli_ebitda)."""
    if not isinstance(deliverable, dict):
        return deliverable, None
    b = _latest_bilancio(inputs)
    if b is None:
        return deliverable, {"note": "nessun bilancio: binding economici saltati"}
    bind_dupont(deliverable, b)
    ev_meta = bind_ev_synth(deliverable, b)
    bind_ccii(deliverable, b)
    cta_meta = bind_cta(deliverable)
    return deliverable, {"ev_synth": ev_meta, "cta": cta_meta,
                         "provenance": "advisor.py (bilancio reale) + quant (EV-multipli)", "note": "§A-§D wired"}
