"""Binder agevolazioni DETERMINISTICO (Fix #3).

I benefici (Nuova Sabatini, Transizione 5.0, de minimis) vengono dai tool del package
`k2a_agevolazioni` vendorizzato (`vendor/k2a_agevolazioni/`), importato come libreria —
non scritti dall'LLM. Calcola ciò che il form consente; dichiara onesto il resto.

Cumulabilità: NON sommata alla cieca — gli scenari sono derivati da una regola dichiarata
(base = miglior singolo strumento, no cumulo; massimo = somma con caveat di verifica).
De minimis: massimale dal tool; il plafond residuo NON è calcolabile perché gli aiuti
pregressi nel form sono testo libero, non importi strutturati.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Optional

_VENDOR = pathlib.Path(__file__).resolve().parent.parent / "vendor"

try:
    if str(_VENDOR) not in sys.path:
        sys.path.insert(0, str(_VENDOR))
    from k2a_agevolazioni.nuova_sabatini import NuovaSabatiniInput, nuova_sabatini
    from k2a_agevolazioni.transizione_5_0 import Transizione50Input, transizione_5_0
    from k2a_agevolazioni.de_minimis import DeMinimisPlafondInput, de_minimis_plafond
    _AVAILABLE = True
    _IMPORT_ERR = None
except Exception as exc:  # pragma: no cover
    _AVAILABLE = False
    _IMPORT_ERR = str(exc)

# Eleggibilità per strumento (tipo investimento del form → strumento)
_TIPO_SABATINI = {"macchinari", "software"}                       # beni strumentali
_TIPO_T50 = {"macchinari", "software", "efficienza_energetica"}   # beni 4.0 / Allegato IV-V


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace(" ", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _investment_sums(form: dict) -> dict:
    sums: dict[str, float] = {}
    for it in (form.get("investimenti_pianificati") or []):
        if not isinstance(it, dict):
            continue
        imp, tipo = _num(it.get("importo_stimato")), it.get("tipo")
        if imp and imp > 0 and tipo:
            sums[tipo] = sums.get(tipo, 0.0) + imp
    return sums


def _settore_deminimis(form: dict) -> str:
    digits = "".join(ch for ch in str(form.get("settore_ateco") or "") if ch.isdigit())
    if digits[:2] in ("01", "02", "03"):  # agricoltura/pesca
        return "pesca_acquacoltura" if digits[:2] == "03" else "agricoltura_primaria"
    return "generale"


def compute_benefici(form: dict) -> Optional[dict]:
    """Ritorna {benefici:{scenari + dettaglio_per_strumento}, note, provenance} o None se il
    package non è disponibile."""
    if not _AVAILABLE:
        return None
    sums = _investment_sums(form)
    dettaglio: list[dict] = []
    provenance: list[dict] = []

    fin_sab = round(sum(v for t, v in sums.items() if t in _TIPO_SABATINI), 2)
    if fin_sab > 0:
        s = nuova_sabatini(NuovaSabatiniInput(finanziamento_eur=fin_sab, tipologia="industria_4_0"))
        dettaglio.append({
            "strumento_id": "nuova_sabatini", "spesa_agevolabile_eur": fin_sab,
            "beneficio_lordo_eur": s.contributo_totale_eur, "beneficio_netto_eur": s.contributo_totale_eur,
            "aliquota_pct": s.contributo_su_finanziamento_pct,
        })
        provenance.append({"strumento": "nuova_sabatini", "fonte": "k2a_agevolazioni",
                           "riferimento": s.riferimento_normativo, "avvertenze": list(s.avvertenze)})

    inv_t50 = round(sum(v for t, v in sums.items() if t in _TIPO_T50), 2)
    if inv_t50 > 0:
        t = transizione_5_0(Transizione50Input(investimento_eur=inv_t50, anno_investimento=2026))
        if t.risparmio_imposta_stimato_eur is not None:
            dettaglio.append({
                "strumento_id": "transizione_5_0",
                "spesa_agevolabile_eur": t.investimento_agevolabile_eur,
                "beneficio_lordo_eur": t.risparmio_imposta_stimato_eur,
                "beneficio_netto_eur": t.risparmio_imposta_stimato_eur,
                "aliquota_pct": t.aliquota_imposta_pct,
            })
            provenance.append({"strumento": "transizione_5_0", "fonte": "k2a_agevolazioni",
                               "riferimento": t.riferimento_normativo, "avvertenze": list(t.avvertenze)})

    # de minimis: massimale dal tool (contesto/vincolo, non un beneficio). Plafond residuo
    # non calcolabile: gli aiuti pregressi nel form sono testo libero, non importi.
    dm = de_minimis_plafond(DeMinimisPlafondInput(settore=_settore_deminimis(form)))
    provenance.append({"strumento": "de_minimis", "fonte": "k2a_agevolazioni",
                       "massimale_eur": dm.massimale_eur, "riferimento": dm.riferimento_normativo,
                       "nota": "plafond residuo non calcolabile: aiuti pregressi non strutturati nel form"})

    benefits = [d["beneficio_lordo_eur"] for d in dettaglio
                if isinstance(d.get("beneficio_lordo_eur"), (int, float))]
    if benefits:
        base = round(max(benefits), 2)
        massimo = round(sum(benefits), 2)
        ottimistico = round((base + massimo) / 2, 2)
        note = (f"Scenari: base = miglior singolo strumento (nessun cumulo); massimo = somma "
                f"(CUMULABILITÀ DA VERIFICARE — Sabatini e Transizione 5.0 sullo stesso bene non "
                f"sempre cumulabili). De minimis massimale {dm.massimale_eur:.0f}€.")
    else:
        base = ottimistico = massimo = 0.0
        note = "Nessun investimento pianificato con importo nel form → benefici non stimabili."

    return {
        "benefici": {
            "scenario_base_eur": base, "scenario_ottimistico_eur": ottimistico,
            "scenario_massimo_eur": massimo, "dettaglio_per_strumento": dettaglio,
        },
        "note": note, "provenance": provenance,
    }


def apply_agevolazioni(deliverable: dict, form: dict) -> tuple[dict, Optional[dict]]:
    """Sovrascrive `benefici_stimati` del deliverable coi numeri deterministici dei tool.
    Ritorna (deliverable, meta{note,provenance}) o (deliverable, None) se non disponibile."""
    if not isinstance(deliverable, dict):
        return deliverable, None
    c = compute_benefici(form)
    if not c:
        return deliverable, None
    out = dict(deliverable)
    out["benefici_stimati"] = c["benefici"]
    return out, {"note": c["note"], "provenance": c["provenance"]}
