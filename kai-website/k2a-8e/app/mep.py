"""Binder MepBoost — cablaggio determinismo economico + onestà termica.

Cosa diventa deterministico (non più fabbricato dall'LLM):
- **piano_eem**: per ogni intervento `payback_anni` / `van_15y` / `tir_pct` sono
  RICALCOLATI da `costo_eur` + `risparmio_eur` (− `incentivo_eur`) con
  `k2a_quant.compute_npv_irr` (già vendorizzato). Se manca `risparmio_eur` ma c'è
  `risparmio_kwh` e un prezzo €/kWh nel form, lo deriva; altrimenti salta onesto.

Cosa NON è cablabile (tool assente → marcato, non fabbricato):
- **audit_termico.rendimento_pct** e **classe_raggiungibile**: non esiste un tool
  APE/EPgl (UNI-TS 11300, trasmittanze ENEA/TABULA) nel 8e. Restano stima LLM →
  segnalati nel meta come `non_validato`, NON sovrascritti con numeri inventati.
- **audit_elettrico**: richiede il vendor di k2a_elettrico + input ingegneristici
  nel form (corrente/sezione/lunghezza) → vedi app/elettrico.py.

Binding strutturale: lo slot riceve il numero corretto, l'LLM non lo genera.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

_DISCOUNT_DEFAULT = 0.05   # tasso di sconto reale per VAN EEM (documentato: PNRR/GME usano 3-5%)
_ORIZZONTE_DEFAULT = 15    # anni — coerente con lo slot `van_15y` dello schema


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("€", "").replace(" ", "").replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _van_tir_payback(costo_netto: float, risparmio_annuo: float,
                     discount_rate: float, anni: int) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """(VAN, TIR%, payback_anni) deterministici via quant.compute_npv_irr."""
    from k2a_quant.npv_irr import NpvIrrInput, compute_npv_irr
    cash = [-costo_netto] + [risparmio_annuo] * anni
    out = compute_npv_irr(NpvIrrInput(cash_flows=cash, discount_rate=discount_rate))
    van = round(out.npv, 2)
    tir = round(out.irr * 100, 2) if out.irr is not None else None
    payback = round(out.payback_period, 2) if out.payback_period is not None else None
    return van, tir, payback


def bind_eem_economics(deliverable: dict, prezzo_kwh: Optional[float] = None,
                       discount_rate: float = _DISCOUNT_DEFAULT,
                       anni: int = _ORIZZONTE_DEFAULT) -> dict:
    piano = deliverable.get("piano_eem")
    if not isinstance(piano, list):
        return {"note": "piano_eem assente o non lista"}
    ricalcolati, saltati = 0, 0
    for item in piano:
        if not isinstance(item, dict):
            continue
        costo = _num(item.get("costo_eur"))
        incentivo = _num(item.get("incentivo_eur")) or 0.0
        risp_eur = _num(item.get("risparmio_eur"))
        risp_kwh = _num(item.get("risparmio_kwh"))
        # deriva risparmio_eur dai kWh SOLO se c'è un prezzo fornito (niente tariffa inventata)
        if risp_eur is None and risp_kwh is not None and prezzo_kwh:
            risp_eur = round(risp_kwh * prezzo_kwh, 2)
            item["risparmio_eur"] = risp_eur
        costo_netto = max(costo - incentivo, 0.0) if costo is not None else None
        if not costo_netto or not risp_eur or risp_eur <= 0:
            saltati += 1
            continue
        van, tir, payback = _van_tir_payback(costo_netto, risp_eur, discount_rate, anni)
        item["van_15y"] = van
        item["tir_pct"] = tir
        item["payback_anni"] = payback
        ricalcolati += 1
    return {"interventi_ricalcolati": ricalcolati, "interventi_saltati_input_mancante": saltati,
            "discount_rate": discount_rate, "orizzonte_anni": anni,
            "prezzo_kwh_usato": prezzo_kwh,
            "provenance": "quant.compute_npv_irr (math su costo+risparmio del piano)"}


def flag_termico(deliverable: dict) -> list[str]:
    """Nessun tool APE/UNI-TS-11300 nel 8e → segnala (non sovrascrive) i campi termici."""
    flags: list[str] = []
    at = deliverable.get("audit_termico")
    if isinstance(at, dict) and (at.get("rendimento_pct") is not None or at.get("generatore_tipo")):
        flags.append("audit_termico.rendimento_pct: stima LLM (nessun tool UNI-TS 11300 / rendimenti ENEA)")
    if deliverable.get("classe_raggiungibile"):
        flags.append("classe_raggiungibile: stima LLM (nessun tool APE/EPgl) — non usare per pratiche edilizie")
    return flags


def apply_mep(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    """Applica i binding MepBoost. Da chiamare DOPO la generazione LLM."""
    if not isinstance(deliverable, dict):
        return deliverable, None
    prezzo = _num((inputs or {}).get("prezzo_energia_eur_kwh"))
    eem_meta = bind_eem_economics(deliverable, prezzo_kwh=prezzo)
    termico_flags = flag_termico(deliverable)
    return deliverable, {
        "eem_economics": eem_meta,
        "termico_non_validato": termico_flags,
        "note": "EEM math deterministica (quant); termico/APE = stima LLM, tool APE assente",
    }
