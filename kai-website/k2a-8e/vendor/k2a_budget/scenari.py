"""budget_scenari: base / ottimistico (+3pp) / pessimistico (-2pp) crescita ricavi."""
from __future__ import annotations

import copy
from typing import Optional

from .calc_result import calc_result
from .engine import budget_36m
from .snapshot import get_snapshot_as_of

_TOOL = "budget_scenari"


def budget_scenari(
    bilancio_base: dict,
    assunzioni: Optional[dict] = None,
    aliquota_imposte_pct: Optional[float] = None,
    pfn_iniziale_eur: Optional[float] = None,
) -> dict:
    inputs = {
        "bilancio_base": bilancio_base,
        "assunzioni": assunzioni,
        "aliquota_imposte_pct": aliquota_imposte_pct,
        "pfn_iniziale_eur": pfn_iniziale_eur,
    }
    a_base = copy.deepcopy(assunzioni) if assunzioni else {}
    g_base = a_base.get("crescita_ricavi_pct_anno", 2.0)

    scenari_def = {
        "pessimistico": g_base - 2.0,
        "base": g_base,
        "ottimistico": g_base + 3.0,
    }
    risultati = {}
    for nome, g in scenari_def.items():
        a = copy.deepcopy(a_base)
        a["crescita_ricavi_pct_anno"] = g
        env = budget_36m(bilancio_base, a, aliquota_imposte_pct, pfn_iniziale_eur)
        if "errore" in env:
            return calc_result(_TOOL, inputs, errore=env["errore"], snapshot_as_of=get_snapshot_as_of())
        risultati[nome] = {
            "crescita_ricavi_pct_anno": g,
            "totali_annui": env["outputs"]["totali_annui"],
            "aggregati_36m": env["outputs"]["aggregati_36m"],
        }

    trace = [
        f"step 1: scenari su crescita_ricavi_pct_anno (base={g_base})",
        f"step 2: pessimistico={scenari_def['pessimistico']}, "
        f"base={scenari_def['base']}, ottimistico={scenari_def['ottimistico']}",
    ]
    warnings = [{
        "codice": "scenari_solo_crescita_ricavi",
        "messaggio": "scenari v1 toccano solo crescita_ricavi_pct_anno; per shock multi-leva usare budget_sensitivity",
    }]
    return calc_result(
        _TOOL,
        inputs,
        outputs={"scenari": risultati},
        snapshot_as_of=get_snapshot_as_of(),
        trace=trace,
        warnings=warnings,
    )
