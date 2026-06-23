"""budget_sensitivity: 3 leve × {-Δ, base, +Δ} → matrice delta_ebitda_cumulato_36m."""
from __future__ import annotations

import copy
from typing import Optional

from .calc_result import calc_result
from .engine import budget_36m
from .snapshot import get_snapshot_as_of

_TOOL = "budget_sensitivity"


def _ebitda_cum(env: dict) -> float:
    return env["outputs"]["aggregati_36m"]["ebitda_cumulato_eur"]


def budget_sensitivity(
    bilancio_base: dict,
    assunzioni: Optional[dict] = None,
    aliquota_imposte_pct: Optional[float] = None,
    delta_pct: float = 10.0,
) -> dict:
    inputs = {
        "bilancio_base": bilancio_base,
        "assunzioni": assunzioni,
        "aliquota_imposte_pct": aliquota_imposte_pct,
        "delta_pct": delta_pct,
    }
    if delta_pct <= 0:
        return calc_result(
            _TOOL,
            inputs,
            errore={"codice": "delta_invalido", "messaggio": "delta_pct deve essere > 0"},
            snapshot_as_of=get_snapshot_as_of(),
        )

    delta = delta_pct / 100.0
    base_env = budget_36m(bilancio_base, assunzioni, aliquota_imposte_pct)
    if "errore" in base_env:
        return calc_result(_TOOL, inputs, errore=base_env["errore"], snapshot_as_of=get_snapshot_as_of())
    base_ebitda = _ebitda_cum(base_env)

    leve = {}

    # leva: ricavi (modifica ricavi_eur_anno_base)
    rows = []
    for sign, label in ((-1, "minus"), (0, "base"), (1, "plus")):
        b = copy.deepcopy(bilancio_base)
        b["ricavi_eur_anno_base"] = b["ricavi_eur_anno_base"] * (1 + sign * delta)
        env = budget_36m(b, assunzioni, aliquota_imposte_pct)
        e = _ebitda_cum(env)
        rows.append({"variazione": label, "ebitda_cumulato_eur": e, "delta_eur": round(e - base_ebitda, 2)})
    leve["ricavi"] = rows

    # leva: margine_variabile (1 - cv/ricavi) → modifica cv inversamente
    # +Δ margine = riduco cv del Δ relativo equivalente: nuovo_margine = margine*(1+Δ)
    rows = []
    ricavi_b = bilancio_base["ricavi_eur_anno_base"]
    cv_b = bilancio_base["costi_variabili_eur_anno_base"]
    margine_b = 1 - cv_b / ricavi_b if ricavi_b > 0 else 0
    for sign, label in ((-1, "minus"), (0, "base"), (1, "plus")):
        b = copy.deepcopy(bilancio_base)
        nuovo_margine = margine_b * (1 + sign * delta)
        nuovo_margine = max(0.0, min(1.0, nuovo_margine))
        b["costi_variabili_eur_anno_base"] = ricavi_b * (1 - nuovo_margine)
        env = budget_36m(b, assunzioni, aliquota_imposte_pct)
        e = _ebitda_cum(env)
        rows.append({"variazione": label, "ebitda_cumulato_eur": e, "delta_eur": round(e - base_ebitda, 2)})
    leve["margine_variabile"] = rows

    # leva: costi_fissi
    rows = []
    for sign, label in ((-1, "minus"), (0, "base"), (1, "plus")):
        b = copy.deepcopy(bilancio_base)
        b["costi_fissi_eur_anno_base"] = b["costi_fissi_eur_anno_base"] * (1 + sign * delta)
        env = budget_36m(b, assunzioni, aliquota_imposte_pct)
        e = _ebitda_cum(env)
        rows.append({"variazione": label, "ebitda_cumulato_eur": e, "delta_eur": round(e - base_ebitda, 2)})
    leve["costi_fissi"] = rows

    outputs = {
        "base_ebitda_cumulato_36m_eur": base_ebitda,
        "delta_pct_applicato": delta_pct,
        "matrice": leve,
    }
    trace = [
        f"step 1: base_ebitda_cumulato_36m = {base_ebitda:.2f}",
        f"step 2: delta applicato = ±{delta_pct}%",
        "step 3: leve testate: ricavi, margine_variabile, costi_fissi",
    ]
    warnings = [{
        "codice": "sensitivity_locale",
        "messaggio": "analisi locale ±Δ%, non sostituisce monte-carlo o scenari estremi",
    }]
    return calc_result(
        _TOOL,
        inputs,
        outputs=outputs,
        snapshot_as_of=get_snapshot_as_of(),
        trace=trace,
        warnings=warnings,
    )
