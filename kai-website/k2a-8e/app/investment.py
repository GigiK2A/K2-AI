"""Investment Engine — decisione di INVESTIMENTO industriale (eval ElectroDrive, 15 lug).

FinanceBoost non deve essere un referto descrittivo ma un INVESTMENT DECISION SUPPORT
SYSTEM: risponde a «questo investimento conviene? è sostenibile? quanto debito aggiuntivo
regge l'azienda? in quanto rientro del CAPEX? cosa succede se il cliente riduce gli ordini?».

Modulo DETERMINISTICO (no LLM), coerente col resto di finance.py. Ogni numero con formula e
assunzioni esplicite (regola cardine: «meglio nessun numero che un numero sbagliato»). Usa i
dati di bilancio riconciliati (EBITDA/PFN/liquidità VERI del cliente, non i derivati garbage).

Modello (dichiarato):
  FCF_t              = EBITDA_incrementale_t × (1 − aliquota) − Δcapitale_circolante_t
  Δcap.circolante    = ricavi_incrementali × (giorni_incasso / 365)   (solo anno di ramp)
  NPV                = Σ FCF_t /(1+WACC)^t − CAPEX
  IRR                = tasso che annulla l'NPV (bisezione deterministica)
  payback            = anno in cui il FCF cumulato copre il CAPEX
  ROI_semplice       = Σ FCF / CAPEX
  PFN/EBITDA post    = (PFN + quota_CAPEX_a_debito) / (EBITDA + EBITDA_incrementale_regime)
  DSCR               = (EBITDA_post − imposte) / servizio_del_debito   (se stimabile)
"""
from __future__ import annotations

from typing import Any, Optional

_TAX = 0.279       # aliquota effettiva proxy (allineata a finance._TAX_PROXY)
_WACC_DEFAULT = 10.0
_COVENANT_PFN_EBITDA = 3.0   # soglia bancaria tipica PFN/EBITDA
_ORIZZONTE_DEFAULT = 5


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace("%", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _npv(rate_pct: float, flows: list[float]) -> float:
    """flows[0] = t0 (di norma −CAPEX), flows[t] = FCF anno t."""
    r = rate_pct / 100.0
    return sum(f / (1 + r) ** t for t, f in enumerate(flows))


def _irr(flows: list[float]) -> Optional[float]:
    """IRR in % via bisezione (deterministica, no scipy). None se non c'è cambio di segno
    o non converge (es. tutti i flussi positivi/negativi)."""
    if not flows or all(f >= 0 for f in flows) or all(f <= 0 for f in flows):
        return None
    lo, hi = -90.0, 1000.0
    f_lo, f_hi = _npv(lo, flows), _npv(hi, flows)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = _npv(mid, flows)
        if abs(f_mid) < 1e-6:
            return round(mid, 2)
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return round((lo + hi) / 2.0, 2)


def _payback(capex: float, fcf_annui: list[float]) -> Optional[float]:
    """Anni per recuperare il CAPEX dal FCF cumulato (interpolazione lineare nell'anno di
    attraversamento). None se non si recupera nell'orizzonte."""
    cum = 0.0
    for i, f in enumerate(fcf_annui, 1):
        prev = cum
        cum += f
        if cum >= capex:
            resto = capex - prev
            return round((i - 1) + (resto / f if f > 0 else 0), 2)
    return None


def _ramp(anno1: float, regime: float, orizzonte: int) -> list[float]:
    """Ramp lineare dei ricavi incrementali da anno1 a regime sull'orizzonte, poi piatto."""
    if orizzonte <= 1:
        return [regime]
    n_ramp = min(3, orizzonte)  # ramp su ~3 anni fino al potenziale
    out = []
    for t in range(1, orizzonte + 1):
        if t < n_ramp:
            out.append(anno1 + (regime - anno1) * (t - 1) / (n_ramp - 1))
        else:
            out.append(regime)
    return out


def _fcf_series(r1: float, reg: float, margine_pct: float, orizzonte: int,
                giorni: float, wacc: float, g_terminale: float = 1.0):
    """FCF operativi per anno + terminal value. FCF = EBITDA×(1−tax) − ΔWC."""
    ricavi_series = _ramp(r1, reg, orizzonte)
    ebitda_series = [rv * margine_pct / 100.0 for rv in ricavi_series]
    dwc_series, prev = [], 0.0
    for rv in ricavi_series:
        dwc_series.append((rv - prev) * (giorni / 365.0) if giorni else 0.0)
        prev = rv
    fcf = [ebitda_series[i] * (1 - _TAX) - dwc_series[i] for i in range(orizzonte)]
    fcf_regime = ebitda_series[-1] * (1 - _TAX)  # a regime niente ΔWC
    tv = fcf_regime / ((wacc - g_terminale) / 100.0) if wacc > g_terminale else 0.0
    return fcf, ricavi_series, round(tv, 2)


def _sensitivity(r1, reg, margine, orizzonte, giorni, wacc, capex):
    """NPV al variare di margine, WACC e orizzonte: la decisione non deve dipendere da un
    singolo set di assunzioni (spec: sensitività + scenari)."""
    def npv_for(m=margine, w=wacc, o=orizzonte):
        fcf, _, tv = _fcf_series(r1, reg, m, o, giorni, w)
        fl = [-capex] + list(fcf)
        fl[-1] += tv
        return round(_npv(w, fl), 2)
    return {
        "margine_-3pp": npv_for(m=max(0.0, margine - 3)),
        "margine_base": npv_for(),
        "margine_+3pp": npv_for(m=margine + 3),
        "wacc_+2pp": npv_for(w=wacc + 2),
        "wacc_-2pp": npv_for(w=max(1.0, wacc - 2)),
        "orizzonte_7a": npv_for(o=7),
        "orizzonte_10a": npv_for(o=10),
    }


def build_investment(capex: float, ricavi_incr_anno1: Optional[float],
                     ricavi_incr_regime: Optional[float], margine_ebitda_pct: float,
                     financials: dict, params: Optional[dict] = None) -> Optional[dict]:
    """Analisi di un investimento. financials = {ebitda, pfn, debiti_finanziari, liquidita,
    patrimonio_netto, fatturato} (dal bilancio riconciliato). params opzionali:
    {wacc_pct, giorni_incasso, orizzonte_anni, quota_debito_pct, oneri_finanziari}."""
    if not capex or capex <= 0:
        return None
    p = params or {}
    orizzonte = int(_num(p.get("orizzonte_anni")) or _ORIZZONTE_DEFAULT)
    wacc = _num(p.get("wacc_pct")) or _WACC_DEFAULT
    giorni = _num(p.get("giorni_incasso")) or 0.0
    quota_debito = _num(p.get("quota_debito_pct"))
    assunzioni: list[str] = []

    r1 = _num(ricavi_incr_anno1)
    reg = _num(ricavi_incr_regime) or r1
    if r1 is None:
        r1 = reg
    if r1 is None or reg is None:
        return None
    if _num(p.get("wacc_pct")) is None:
        assunzioni.append(f"WACC assunto {wacc:g}% (non dichiarato)")
    assunzioni.append(f"EBITDA incrementale = ricavi incrementali × {margine_ebitda_pct:g}% "
                      "(margine del business esistente; da validare per il nuovo contratto)")
    if giorni:
        assunzioni.append(f"capitale circolante = ricavi × {giorni:g}gg/365 (assorbimento nell'anno di ramp)")

    fcf_annui, ricavi_series, tv = _fcf_series(r1, reg, margine_ebitda_pct, orizzonte, giorni, wacc)
    # Il TERMINAL VALUE (perpetuità del FCF a regime) rappresenta la vita dell'asset OLTRE
    # l'orizzonte: senza, un CAPEX industriale che rende in perpetuità sembra distruggere
    # valore per il solo troncamento a N anni. g=1% prudente. Sommato all'ultimo anno.
    flows = [-capex] + list(fcf_annui)
    flows[-1] += tv
    assunzioni.append(f"terminal value = FCF a regime / (WACC − 1%) al termine dell'orizzonte "
                      f"(€{tv:,.0f}), per la vita dell'asset oltre i {orizzonte} anni".replace(",", "."))

    npv = _npv(wacc, flows)
    irr = _irr(flows)
    payback = _payback(capex, fcf_annui)  # payback sul FCF operativo (senza TV): prudente
    roi = (sum(fcf_annui) + tv) / capex * 100.0 if capex else None

    ebitda_now = _num(financials.get("ebitda")) or 0.0
    pfn_now = _num(financials.get("pfn"))
    ebitda_regime_incr = reg * margine_ebitda_pct / 100.0  # EBITDA incrementale a regime
    ebitda_post = ebitda_now + ebitda_regime_incr
    # quota del CAPEX a debito: se non dichiarata, assume tutto a debito (conservativo per la
    # capacità di indebitamento) → segnala l'assunzione.
    if quota_debito is None:
        quota_debito = 100.0
        assunzioni.append("quota del CAPEX finanziata a debito assunta 100% (conservativo): "
                          "con equity/cassa la leva post è più bassa")
    capex_debito = capex * quota_debito / 100.0
    pfn_post = (pfn_now + capex_debito) if pfn_now is not None else None
    lev_now = (pfn_now / ebitda_now) if (pfn_now is not None and ebitda_now) else None
    lev_post = (pfn_post / ebitda_post) if (pfn_post is not None and ebitda_post) else None

    def _r(x):
        return round(x, 2) if isinstance(x, (int, float)) else x

    debt_capacity = {
        "pfn_attuale_eur": _r(pfn_now), "pfn_ebitda_attuale": _r(lev_now),
        "pfn_post_investimento_eur": _r(pfn_post), "pfn_ebitda_post": _r(lev_post),
        "covenant_soglia": _COVENANT_PFN_EBITDA,
        "entro_covenant": (lev_post is not None and lev_post <= _COVENANT_PFN_EBITDA),
        # debito aggiuntivo massimo a covenant 3x, dato l'EBITDA post
        "debito_aggiuntivo_max_a_covenant_eur": _r(
            _COVENANT_PFN_EBITDA * ebitda_post - (pfn_now or 0)) if ebitda_post else None,
        "formula": "PFN/EBITDA post = (PFN + CAPEX a debito) / (EBITDA + EBITDA incrementale a regime)",
    }

    sens = _sensitivity(r1, reg, margine_ebitda_pct, orizzonte, giorni, wacc, capex)
    verdetto, motivo = _decisione(npv, irr, wacc, payback, orizzonte, lev_post, sens)
    return {
        "decisione_investimento": {"verdetto": verdetto, "motivo": motivo},
        "investment_summary": {
            "capex_eur": _r(capex), "npv_eur": _r(npv), "irr_pct": irr, "wacc_pct": _r(wacc),
            "payback_anni": payback, "roi_semplice_pct": _r(roi),
            "orizzonte_anni": orizzonte,
            "fcf_per_anno_eur": [_r(x) for x in fcf_annui],
            "ricavi_incrementali_per_anno_eur": [_r(x) for x in ricavi_series],
            "terminal_value_eur": _r(tv),
            "formula": ("NPV = Σ FCF/(1+WACC)^t + TV/(1+WACC)^N − CAPEX; FCF = EBITDA incr.×"
                        "(1−aliquota) − ΔWC; IRR = tasso che annulla l'NPV; payback = anno di "
                        "recupero del CAPEX sul FCF operativo"),
            "assunzioni": assunzioni,
        },
        "sensitivita_npv": sens,
        "debt_capacity": debt_capacity,
        "metodo_investimento": ("Investment decision support: NPV/IRR/payback sul flusso di cassa "
                                "incrementale, capacità di indebitamento (PFN/EBITDA post vs covenant) "
                                "e stress test. Numeri derivati dai dati del cliente."),
    }


def _decisione(npv, irr, wacc, payback, orizzonte, lev_post, sens=None) -> tuple[str, str]:
    if npv is None:
        return "NO-GO", "flussi non stimabili"
    over_covenant = lev_post is not None and lev_post > _COVENANT_PFN_EBITDA
    # RANGE della sensitività: la decisione non deve dipendere da un singolo set di assunzioni.
    vals = [v for v in (sens or {}).values() if isinstance(v, (int, float))]
    tutti_negativi = bool(vals) and all(v <= 0 for v in vals)
    qualche_negativo = bool(vals) and any(v <= 0 for v in vals)
    if npv <= 0 and (tutti_negativi or not vals):
        return "NO-GO", (f"NPV negativo (€{npv:,.0f}) e tale in tutti gli scenari di sensitività "
                         f"(margine/WACC/orizzonte): l'investimento non crea valore.".replace(",", "."))
    if over_covenant:
        return "GO WITH CONDITIONS", (f"l'investimento crea valore (NPV €{npv:,.0f}, IRR {irr}% > WACC), "
                                      f"MA la leva post {lev_post:.1f}x supera il covenant "
                                      f"{_COVENANT_PFN_EBITDA:g}x: strutturare parte con equity/cassa, "
                                      "scaglionare il CAPEX o negoziare i covenant.".replace(",", "."))
    if npv <= 0 or qualche_negativo or (payback is not None and payback > orizzonte * 0.7):
        return "GO WITH CONDITIONS", (f"NPV base €{npv:,.0f} ma il risultato dipende dalle assunzioni "
                                      f"(margine del nuovo contratto, orizzonte, ramp): validare il "
                                      f"margine incrementale e il potenziale prima di impegnare il CAPEX; "
                                      f"attenzione alla concentrazione cliente.".replace(",", "."))
    return "GO", (f"NPV positivo (€{npv:,.0f}), IRR {irr}% > WACC {wacc:g}%, leva post entro il covenant "
                  "e positivo negli scenari di sensitività: investimento sostenibile e creatore di "
                  "valore.".replace(",", "."))


_STRESS_QUOTE = (15.0, 25.0, 35.0, 45.0)


def stress_investment(ricavi_incr_regime: float, margine_ebitda_pct: float,
                      fatturato: float, ebitda_now: float, giorni_incasso: float = 0.0) -> dict:
    """Stress test dell'investimento: perdita cliente / riduzione volumi / ritardo pagamenti.
    Impatto su EBITDA e concentrazione."""
    ebitda_incr = ricavi_incr_regime * margine_ebitda_pct / 100.0
    tot_post = fatturato + ricavi_incr_regime if fatturato else None
    quota = ricavi_incr_regime / tot_post * 100.0 if tot_post else None
    scenari = [
        {"scenario": "perdita del cliente", "impatto_ebitda_eur": -round(ebitda_incr, 2),
         "nota": "l'intero EBITDA incrementale salta; il CAPEX resta da ammortizzare"},
        {"scenario": "-30% volumi", "impatto_ebitda_eur": -round(ebitda_incr * 0.30, 2),
         "nota": "ricavi incrementali sotto le attese"},
        {"scenario": "-50% volumi", "impatto_ebitda_eur": -round(ebitda_incr * 0.50, 2),
         "nota": "ordine dimezzato"},
    ]
    ritardo = None
    if giorni_incasso:
        wc_extra = ricavi_incr_regime * (30 / 365.0)  # +30gg di ritardo
        ritardo = {"scenario": "+30gg ritardo pagamenti",
                   "capitale_circolante_aggiuntivo_eur": round(wc_extra, 2),
                   "nota": "assorbimento di cassa aggiuntivo, nessun impatto su EBITDA ma su liquidità"}
    return {
        "concentrazione_cliente_pct": round(quota, 2) if quota is not None else None,
        "scenari": scenari,
        "ritardo_pagamenti": ritardo,
        "lettura": ("La perdita del nuovo cliente è il rischio dominante: dimensiona il CAPEX e "
                    "i covenant su uno scenario prudente, non sul potenziale pieno."),
        "formula": "EBITDA incrementale = ricavi incrementali × margine EBITDA",
    }


def _collect_numbers(obj) -> list:
    out: list = []
    if isinstance(obj, dict):
        for v in obj.values():
            out.extend(_collect_numbers(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_collect_numbers(v))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(round(float(obj), 4))
        out.append(round(abs(float(obj)), 4))
    return out


def apply_investment(deliverable: dict, inputs: dict, reclass: Optional[dict],
                     facts: Optional[dict] = None) -> tuple[dict, Optional[dict]]:
    """Hook FinanceBoost: se gli input descrivono un investimento (`investimento_progetto`
    o `capex` + ricavi incrementali), inietta l'analisi di investimento. No-op altrimenti."""
    if not isinstance(deliverable, dict) or not isinstance(inputs, dict):
        return deliverable, None
    prog = inputs.get("investimento_progetto") if isinstance(inputs.get("investimento_progetto"), dict) else {}
    capex = _num(prog.get("capex") or inputs.get("investimento_eur") or inputs.get("capex")
                 or prog.get("investimento"))
    if not capex or capex <= 0:
        return deliverable, None
    r1 = (prog.get("ricavi_incrementali_anno1") or inputs.get("ricavi_incrementali_anno1")
          or prog.get("contratto_iniziale_eur"))
    reg = (prog.get("ricavi_incrementali_regime") or inputs.get("ricavi_incrementali_potenziale")
           or prog.get("potenziale_eur"))
    rc = reclass or {}
    ce, idx, sp = rc.get("ce") or {}, rc.get("indici") or {}, rc.get("sp") or {}
    fatturato = _num(ce.get("ricavi"))
    ebitda = _num(ce.get("ebitda"))
    margine = _num(prog.get("margine_ebitda_pct") or inputs.get("margine_incrementale_pct"))
    if margine is None:
        margine = idx.get("ebitda_margin") or 14.0
    financials = {"ebitda": ebitda, "pfn": idx.get("pfn"),
                  "debiti_finanziari": sp.get("debiti_finanziari"),
                  "liquidita": sp.get("liquidita"), "patrimonio_netto": sp.get("patrimonio_netto"),
                  "fatturato": fatturato}
    params = {"wacc_pct": _num(prog.get("wacc_pct") or inputs.get("wacc_pct")),
              "giorni_incasso": _num(prog.get("giorni_incasso") or inputs.get("giorni_pagamento")),
              "orizzonte_anni": _num(prog.get("orizzonte_anni")),
              "quota_debito_pct": _num(prog.get("quota_debito_pct"))}
    analisi = build_investment(capex, r1, reg, margine, financials, params)
    if not analisi:
        return deliverable, None
    if fatturato and ebitda is not None and reg:
        analisi["stress_test_investimento"] = stress_investment(
            _num(reg) or 0.0, margine, fatturato, ebitda, params["giorni_incasso"] or 0.0)
    out = dict(deliverable)
    for k, v in analisi.items():
        if v is not None:
            out[k] = v
    if isinstance(facts, dict):
        facts["_investment_grounded_numbers"] = {"numeri": _collect_numbers(analisi)}
    return out, {"investment_engine": True, "verdetto": analisi["decisione_investimento"]["verdetto"],
                 "npv_eur": analisi["investment_summary"]["npv_eur"]}
