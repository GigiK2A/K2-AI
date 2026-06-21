"""capm_cost_of_equity — costo dell'equity con relevering, ASSUNZIONI DAL SNAPSHOT.

Differenza chiave vs il WACC esistente (k2a_quant/wacc.py): l'agente NON passa più
beta/ERP/rf/size_premium → vengono dallo snapshot dato il settore (criterio #1 di
Luca: le assunzioni stanno nel tool). La matematica è identica al WACC esistente
(Hamada relevering + CAPM), qui solo "instradata" dallo snapshot.

  βL = βU·(1 + (1−t)·D/E)   ;   ke = rf + βL·ERP + size_premium
"""
from __future__ import annotations

from typing import Optional

from .calc_result import calc_result
from . import snapshot as snap


def capm_cost_of_equity(
    settore: str,
    pfn_eur: float,
    patrimonio_netto_eur: float,
    fatturato_eur: float,
    snapshot: dict,
    *,
    paese: str = "italy",
    tax_rate_pct: Optional[float] = None,
) -> dict:
    inputs = {
        "settore": settore, "pfn_eur": pfn_eur, "patrimonio_netto_eur": patrimonio_netto_eur,
        "fatturato_eur": fatturato_eur, "paese": paese, "tax_rate_pct": tax_rate_pct,
    }
    asof = snap.snapshot_as_of(snapshot)
    sec = snap.sector(snapshot, settore)
    if not sec:
        return calc_result("capm_cost_of_equity", inputs, snapshot_as_of=asof,
                           errore={"code": "settore_non_trovato", "settore": settore,
                                   "available": list((snapshot.get("sectors") or {}).keys())[:12]})

    # ---- GUARD FINANCIALS: no numero, messaggio onesto ----
    # I sector finanziari (banche/assicurazioni) hanno depositi/passività tecniche trattati
    # come 'debito' nel rapporto D/E Damodaran → βU spurio → re-levering Hamada non valido.
    # Non emetto un ke fittizio: ritorno guard. Resta disponibile beta_regression nel sector.
    if sec.get("is_financial"):
        return calc_result(
            "capm_cost_of_equity", inputs, snapshot_as_of=asof,
            errore={
                "code": "settore_finanziario_capm_non_applicabile",
                "settore": settore,
                "messaggio": ("Settore finanziario: valutazione CAPM/multipli standard non "
                              "applicabile (depositi/passività tecniche come 'debito' rendono "
                              "βU non valido per il re-levering). Metodo dedicato richiesto. "
                              "Per riferimento: beta_regression (beta levered di regressione) "
                              "disponibile nel sector dello snapshot, da usare senza re-levering."),
                "beta_regression": sec.get("beta_regression"),
            },
        )

    cd = snap.country(snapshot, paese)
    beta_u = sec.get("beta_unlevered")
    rf = cd.get("rf_10y")
    erp = cd.get("erp")
    tax = (tax_rate_pct / 100) if tax_rate_pct is not None else cd.get("tax_rate", 0.279)
    if beta_u is None or rf is None or erp is None:
        return calc_result("capm_cost_of_equity", inputs, snapshot_as_of=asof,
                           errore={"code": "snapshot_incompleto", "msg": "manca beta_unlevered / rf_10y / erp"})
    if not patrimonio_netto_eur or patrimonio_netto_eur == 0:
        return calc_result("capm_cost_of_equity", inputs, snapshot_as_of=asof,
                           errore={"code": "pn_non_valido", "msg": "patrimonio_netto deve essere != 0"})

    d_e = pfn_eur / patrimonio_netto_eur
    beta_l = beta_u * (1 + (1 - tax) * d_e)
    fascia, size_prem = snap.size_premium(fatturato_eur)
    ke = rf + beta_l * erp + size_prem

    trace = [
        {"step": 1, "descrizione": "relevering beta (Hamada)", "formula": "βL = βU·(1+(1−t)·D/E)",
         "valori": {"βU": beta_u, "D/E": round(d_e, 3), "t": tax, "βL": round(beta_l, 4)}},
        {"step": 2, "descrizione": "CAPM + size premium", "formula": "ke = rf + βL·ERP + size",
         "valori": {"rf": rf, "ERP": erp, "size_premium": size_prem, "ke": round(ke, 4)}},
    ]
    outputs = {
        "ke_pct": round(ke * 100, 2), "beta_unlevered": beta_u, "beta_levered": round(beta_l, 4),
        "risk_free_pct": round(rf * 100, 2), "erp_pct": round(erp * 100, 2),
        "size_premium_pct": round(size_prem * 100, 2), "fascia_size": fascia, "settore_usato": settore,
    }
    return calc_result("capm_cost_of_equity", inputs, outputs, snapshot_as_of=asof, trace=trace)
