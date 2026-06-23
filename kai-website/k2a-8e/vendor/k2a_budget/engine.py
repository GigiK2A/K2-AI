"""Engine: budget_36m — proiezione mensile su 36 mesi.

Convenzione anno (PIN):
- mese 1-12 = anno-1 (gia' cresciuto: ricavi_annuali_anno1 = base * (1+g)^1)
- mese 13-24 = anno-2 ((1+g)^2)
- mese 25-36 = anno-3 ((1+g)^3)
- formula mese t: anno(t) = ceil(t/12);
  ricavi(t) = base * (1+g)^anno(t) * stag[mt-1] / sum(stag)
"""
from __future__ import annotations

from math import ceil
from typing import Optional

from .calc_result import calc_result
from .models import AssunzioniProiezione, BilancioBase
from .snapshot import get_aliquota_default, get_snapshot_as_of, load_defaults

_TOOL = "budget_36m"


def _validate_aliquota(aliquota_pct: float) -> Optional[dict]:
    if aliquota_pct < 0 or aliquota_pct > 100:
        return {
            "codice": "aliquota_invalida",
            "messaggio": f"aliquota_imposte_pct={aliquota_pct} fuori range [0, 100]",
        }
    return None


def _detect_defaults_used(
    assunzioni_input: dict | None,
    aliquota_input: float | None,
) -> list[str]:
    used = []
    a = assunzioni_input or {}
    defaults_keys = {
        "crescita_ricavi_pct_anno": 2.0,
        "stagionalita_mensile_12": None,  # marker, controllato separatamente
        "elasticita_costi_variabili_su_ricavi": 1.0,
        "crescita_costi_fissi_pct_anno": 2.0,
        "capex_eur_anno": 0,
        "vita_utile_capex_anni": 5,
        "wc_giorni": 0,
    }
    for k in defaults_keys:
        if k not in a:
            used.append(f"assunzioni.{k}")
    if aliquota_input is None:
        used.append("aliquota_imposte_pct (default snapshot)")
    return used


def _compute_36m(
    bilancio: BilancioBase,
    assunzioni: AssunzioniProiezione,
    aliquota_pct: float,
    pfn_iniziale_eur: Optional[float] = None,
) -> tuple[dict, list]:
    ricavi_base = bilancio.ricavi_eur_anno_base
    cv_base = bilancio.costi_variabili_eur_anno_base
    cf_base = bilancio.costi_fissi_eur_anno_base
    amm_base = bilancio.ammortamenti_eur_anno_base
    of_base = bilancio.oneri_finanziari_eur_anno_base

    g_r = assunzioni.crescita_ricavi_pct_anno / 100.0
    g_cf = assunzioni.crescita_costi_fissi_pct_anno / 100.0
    stag = assunzioni.stagionalita_mensile_12
    stag_sum = sum(stag)
    elast = assunzioni.elasticita_costi_variabili_su_ricavi
    capex_anno = assunzioni.capex_eur_anno
    vita_utile = assunzioni.vita_utile_capex_anni
    wc_giorni = assunzioni.wc_giorni
    tax = aliquota_pct / 100.0

    cv_ratio_base = (cv_base / ricavi_base) if ricavi_base > 0 else 0.0
    ricavi_t_prev = ricavi_base / 12.0  # ricavi(0) per delta_wc

    budget_mensile = []
    annuali = {1: {}, 2: {}, 3: {}}
    for anno in (1, 2, 3):
        annuali[anno] = {
            "ricavi": 0.0,
            "costi_variabili": 0.0,
            "costi_fissi": 0.0,
            "ebitda": 0.0,
            "ammortamenti": 0.0,
            "oneri_finanziari": 0.0,
            "imposte": 0.0,
            "utile_netto": 0.0,
            "fcf": 0.0,
        }

    capex_mese = capex_anno / 12.0

    for t in range(1, 37):
        anno = ceil(t / 12)
        mese_in_anno = t - (anno - 1) * 12  # 1..12
        ricavi_annuali = ricavi_base * (1 + g_r) ** anno
        cf_annuali = cf_base * (1 + g_cf) ** anno

        ricavi_t = ricavi_annuali * stag[mese_in_anno - 1] / stag_sum
        cv_t = cv_ratio_base * elast * ricavi_t
        cf_t = cf_annuali / 12.0
        ebitda_t = ricavi_t - cv_t - cf_t

        capex_cum_t = capex_mese * t
        amm_capex_t = capex_cum_t / vita_utile / 12.0
        amm_t = amm_base / 12.0 + amm_capex_t
        of_t = of_base / 12.0
        uai_t = ebitda_t - amm_t - of_t
        imposte_t = max(0.0, uai_t) * tax
        utile_netto_t = uai_t - imposte_t

        delta_wc_t = (ricavi_t - ricavi_t_prev) * wc_giorni / 365.0
        fcf_t = ebitda_t - imposte_t - capex_mese - delta_wc_t
        ricavi_t_prev = ricavi_t

        row = {
            "mese": t,
            "ricavi": round(ricavi_t, 2),
            "costi_variabili": round(cv_t, 2),
            "costi_fissi": round(cf_t, 2),
            "ebitda": round(ebitda_t, 2),
            "ammortamenti": round(amm_t, 2),
            "oneri_finanziari": round(of_t, 2),
            "imposte": round(imposte_t, 2),
            "utile_netto": round(utile_netto_t, 2),
            "fcf": round(fcf_t, 2),
        }
        budget_mensile.append(row)

        a = annuali[anno]
        a["ricavi"] += ricavi_t
        a["costi_variabili"] += cv_t
        a["costi_fissi"] += cf_t
        a["ebitda"] += ebitda_t
        a["ammortamenti"] += amm_t
        a["oneri_finanziari"] += of_t
        a["imposte"] += imposte_t
        a["utile_netto"] += utile_netto_t
        a["fcf"] += fcf_t

    totali_annui = []
    for anno in (1, 2, 3):
        a = annuali[anno]
        totali_annui.append({
            "anno": anno,
            "ricavi": round(a["ricavi"], 2),
            "costi_variabili": round(a["costi_variabili"], 2),
            "costi_fissi": round(a["costi_fissi"], 2),
            "ebitda": round(a["ebitda"], 2),
            "ammortamenti": round(a["ammortamenti"], 2),
            "oneri_finanziari": round(a["oneri_finanziari"], 2),
            "imposte": round(a["imposte"], 2),
            "utile_netto": round(a["utile_netto"], 2),
            "fcf": round(a["fcf"], 2),
        })

    ricavi_cum = sum(a["ricavi"] for a in annuali.values())
    ebitda_cum = sum(a["ebitda"] for a in annuali.values())
    utile_cum = sum(a["utile_netto"] for a in annuali.values())
    fcf_cum = sum(a["fcf"] for a in annuali.values())

    aggregati = {
        "ricavi_cumulati_eur": round(ricavi_cum, 2),
        "ebitda_cumulato_eur": round(ebitda_cum, 2),
        "utile_cumulato_eur": round(utile_cum, 2),
        "fcf_cumulato_eur": round(fcf_cum, 2),
    }
    if pfn_iniziale_eur is not None:
        aggregati["pfn_finale_eur"] = round(pfn_iniziale_eur - fcf_cum, 2)

    trace = [
        f"step 1: convenzione anno: ricavi_annuali_anno_n = ricavi_base * (1+g)^n; g={g_r:.4f}",
        f"step 2: ricavi_base={ricavi_base:.2f}, ricavi_anno1={ricavi_base*(1+g_r):.2f}, "
        f"ricavi_anno3={ricavi_base*(1+g_r)**3:.2f}",
        f"step 3: cv_ratio_base = {cv_base:.2f} / {ricavi_base:.2f} = {cv_ratio_base:.6f}; "
        f"elasticita={elast}",
        f"step 4: cf_anno1 = {cf_base:.2f} * (1+{g_cf:.4f})^1 = {cf_base*(1+g_cf):.2f}",
        f"step 5: amm/mese = amm_base/12 + capex_cum_t/vita_utile/12; "
        f"amm_base={amm_base:.2f}, capex_anno={capex_anno:.2f}, vita={vita_utile}",
        f"step 6: aliquota={aliquota_pct}% (no loss carryforward, imposte=max(0,UAI)*tax)",
        f"step 7: fcf = ebitda - imposte - capex_mese - delta_wc; wc_giorni={wc_giorni}",
        f"step 8: aggregati 36m: ricavi_cum={ricavi_cum:.2f}, ebitda_cum={ebitda_cum:.2f}, "
        f"fcf_cum={fcf_cum:.2f}",
    ]

    outputs = {
        "budget_mensile_36m": budget_mensile,
        "totali_annui": totali_annui,
        "aggregati_36m": aggregati,
    }
    return outputs, trace


def budget_36m(
    bilancio_base: dict,
    assunzioni: Optional[dict] = None,
    aliquota_imposte_pct: Optional[float] = None,
    pfn_iniziale_eur: Optional[float] = None,
) -> dict:
    """Proiezione budget 36 mesi (deterministico, tracciabile)."""
    inputs = {
        "bilancio_base": bilancio_base,
        "assunzioni": assunzioni,
        "aliquota_imposte_pct": aliquota_imposte_pct,
        "pfn_iniziale_eur": pfn_iniziale_eur,
    }

    aliquota = (
        aliquota_imposte_pct
        if aliquota_imposte_pct is not None
        else get_aliquota_default()
    )
    err = _validate_aliquota(aliquota)
    if err is not None:
        return calc_result(_TOOL, inputs, errore=err, snapshot_as_of=get_snapshot_as_of())

    try:
        bilancio_obj = BilancioBase(**bilancio_base)
        assunzioni_obj = AssunzioniProiezione(**(assunzioni or {}))
    except Exception as e:
        return calc_result(
            _TOOL,
            inputs,
            errore={"codice": "input_invalido", "messaggio": str(e)},
            snapshot_as_of=get_snapshot_as_of(),
        )

    outputs, trace = _compute_36m(bilancio_obj, assunzioni_obj, aliquota, pfn_iniziale_eur)

    warnings = [
        {
            "codice": "aliquota_effettiva_approssimata",
            "messaggio": (
                "aliquota effettiva approssimata (IRES+IRAP su utile, IRAP base semplificata) "
                "— non sostituisce calcolo fiscale esatto"
            ),
        },
        {
            "codice": "no_loss_carryforward",
            "messaggio": (
                "perdite non riportate a nuovo (imposte = max(0, utile_ante_imposte) × aliquota)"
            ),
        },
    ]
    defaults_used = _detect_defaults_used(assunzioni, aliquota_imposte_pct)
    if defaults_used:
        warnings.append({
            "codice": "assunzioni_default_usate",
            "messaggio": "parametri lasciati a default",
            "parametri": defaults_used,
        })

    return calc_result(
        _TOOL,
        inputs,
        outputs=outputs,
        snapshot_as_of=get_snapshot_as_of(),
        trace=trace,
        warnings=warnings,
    )
