"""HostBoost — KPI ricettivi DETERMINISTICI (ADR/RevPAR/occupancy/GOPPAR…).

Il campo `kpi.annuale` del deliverable lo scriveva l'LLM: su dati parziali usciva
un PLACEHOLDER ('adr':1,'revpar':1,…, cifre INVENTATE in un report pagato) mentre
`dati_mancanti` diceva onestamente "adr non disponibile" — contraddizione. Qui i KPI
si calcolano dai dati dichiarati nel form (`kpi_attuali` + camere + giorni) col tool
`metriche_hospitality`; ciò che non è calcolabile resta `null` (onesto, il render mostra
'n.d.'), MAI 1. Modellato su finance.apply_to_financeboost / tax.apply_fiscoboost.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

_VENDOR = str(Path(__file__).resolve().parent.parent / "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

try:
    from k2a_agevolazioni.hospitality import HospitalityInput, metriche_hospitality
    _AVAILABLE = True
except Exception:  # pragma: no cover
    _AVAILABLE = False


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
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _kpi_from_form(form: dict) -> Optional[dict]:
    """Estrae/deriva i KPI ricettivi dai dati del form. None se non c'è NIENTE di utile."""
    ka = form.get("kpi_attuali") if isinstance(form.get("kpi_attuali"), dict) else {}
    adr = _num(ka.get("adr_eur")) or _num(form.get("adr_eur")) or _num(form.get("prezzo_medio"))
    occ = _num(ka.get("occupancy_pct")) or _num(form.get("occupancy_pct")) or _num(form.get("occupazione_pct"))
    revpar = _num(ka.get("revpar_eur")) or _num(form.get("revpar_eur"))
    camere = _num(form.get("camere_totali")) or _num(form.get("camere")) or _num(form.get("n_camere"))
    giorni = _num(form.get("giorni_apertura")) or _num(form.get("giorni")) or 365.0
    ricavi_camere = _num(form.get("ricavi_camere_eur")) or _num(form.get("ricavi_camere"))
    ricavi_tot = _num(form.get("ricavi_totali_eur")) or _num(form.get("ricavi")) or _num(form.get("fatturato"))
    costi_op = _num(form.get("costi_operativi_eur")) or _num(form.get("costi_totali")) or _num(form.get("costi"))

    # Via ricca: col tool metriche_hospitality se abbiamo camere+occupazione(+ricavi).
    if _AVAILABLE and camere and (occ is not None or revpar is not None):
        vendute = None
        if occ is not None and giorni:
            vendute = round(camere * giorni * occ / 100.0, 2)
        rc = ricavi_camere
        if rc is None and adr is not None and vendute:
            rc = round(adr * vendute, 2)          # ricavi camere ≈ ADR × notti vendute
        if rc is None and revpar is not None and camere and giorni:
            rc = round(revpar * camere * giorni, 2)
        if rc and camere:
            try:
                out = metriche_hospitality(HospitalityInput(
                    camere=int(camere), giorni=int(giorni),
                    tasso_occupazione_pct=occ, ricavi_camere_eur=rc,
                    ricavi_totali_eur=ricavi_tot, costi_operativi_eur=costi_op))
                # NB: lo schema del deliverable vuole `occupancy` come FRAZIONE 0-1 (max:1),
                # il tool la dà in percentuale → /100.
                return {"adr": out.adr_eur, "occupancy": round(out.occupazione_pct / 100.0, 4),
                        "revpar": out.revpar_eur, "trevpar": out.trevpar_eur,
                        "goppar": out.goppar_eur, "_fonte": "metriche_hospitality"}
            except Exception:
                pass

    # Via minima: KPI dichiarati + RevPAR derivato (RevPAR = ADR × occ). Il resto null (onesto).
    if adr is None and occ is None and revpar is None:
        return None
    if revpar is None and adr is not None and occ is not None:
        revpar = round(adr * occ / 100.0, 2)
    # `occupancy` nel deliverable è una FRAZIONE 0-1 (schema max:1); l'input è in % → /100.
    occ_frac = round(occ / 100.0, 4) if occ is not None else None
    return {"adr": adr, "occupancy": occ_frac, "revpar": revpar,
            "trevpar": None, "goppar": None, "_fonte": "kpi_dichiarati"}


def apply_hostboost(deliverable: dict, form: dict) -> tuple[dict, Optional[dict]]:
    """Sovrascrive `kpi.annuale` coi KPI deterministici (no LLM). Ciò che non è
    calcolabile resta null (mai il placeholder 1). Ritorna (deliverable, meta)."""
    if not isinstance(deliverable, dict) or not isinstance(form, dict):
        return deliverable, None
    kpis = _kpi_from_form(form)
    if kpis is None:
        # nessun dato KPI: azzera il placeholder LLM ('adr':1…) → null onesto (schema nullable)
        placeholder = {"adr": None, "occupancy": None, "revpar": None,
                       "trevpar": None, "goppar": None, "alos": None,
                       "booking_window_medio_giorni": None, "cancellation_rate": None,
                       "yoy_revpar": None, "yoy_adr": None, "yoy_occupancy": None}
        fonte = "nessun_dato"
        vals = placeholder
    else:
        fonte = kpis.pop("_fonte")
        vals = kpis
    out = dict(deliverable)
    kpi = dict(out.get("kpi") or {})
    ann = dict(kpi.get("annuale") or {})
    for k in ("adr", "occupancy", "revpar", "trevpar", "goppar"):
        if k in vals:
            ann[k] = vals[k]
    # gli altri KPI (alos, booking_window, cancellation, yoy_*) l'LLM NON li può sapere
    # dai soli dati dichiarati → null onesto invece del placeholder 1.
    for k in ("alos", "booking_window_medio_giorni", "cancellation_rate",
              "yoy_revpar", "yoy_adr", "yoy_occupancy"):
        if ann.get(k) == 1 or ann.get(k) == 1.0:
            ann[k] = None
    kpi["annuale"] = ann
    # `mensile` (12 mesi) NON ha una fonte deterministica nel form (solo dati annuali) → l'LLM
    # lo inventa (su Gemma: 12 righe di '1'). Se è un placeholder, svuotalo: 12 mesi di numeri
    # finti in un pagato sono peggio del dettaglio assente. Il render salta la lista vuota;
    # un'assunzione onesta spiega come ottenerlo.
    mensile = kpi.get("mensile")
    placeholder_mensile = (isinstance(mensile, list) and mensile and all(
        isinstance(m, dict) and (m.get("adr") in (1, 1.0) or m.get("revpar") in (1, 1.0)
                                 or m.get("notti_disponibili") in (1, 1.0)) for m in mensile))
    meta = {"hostboost_kpi_fonte": fonte}
    if placeholder_mensile:
        kpi["mensile"] = []
        ass = list(out.get("assunzioni") or [])
        ass.append("Dettaglio mensile non incluso: nel form ci sono solo dati annuali. Fornisci "
                   "occupancy/ricavi per mese per la vista stagionale (ADR/RevPAR mese per mese).")
        out["assunzioni"] = ass
        meta["mensile_svuotato"] = "placeholder senza dati mensili"
    out["kpi"] = kpi
    return out, meta
