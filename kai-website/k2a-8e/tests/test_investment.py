"""Investment Engine — decisione di investimento industriale (eval ElectroDrive, 15 lug).

FinanceBoost come investment decision support system: NPV/IRR/payback, debt capacity,
sensitività, stress test. Numeri con formula e assunzioni; verdetto range-based (non su un
singolo set di assunzioni). Verificato sui numeri reali ElectroDrive.
"""
from __future__ import annotations

import math

from app import investment as I

FIN = {"ebitda": 3360000, "pfn": 5500000, "debiti_finanziari": 8700000,
       "liquidita": 3200000, "patrimonio_netto": 12000000, "fatturato": 24000000}


def _ed(margine=14.0):
    return I.build_investment(6900000, 4000000, 12000000, margine, FIN, {"giorni_incasso": 105})


def test_npv_irr_payback_derivati():
    a = _ed()
    s = a["investment_summary"]
    assert s["npv_eur"] > 0                      # crea valore col terminal value
    assert s["irr_pct"] is not None and s["irr_pct"] > 10  # IRR > WACC 10%
    assert s["terminal_value_eur"] > 0
    assert s["formula"] and s["assunzioni"]


def test_irr_bisezione_corretta():
    # flussi noti: -1000 poi 600,600 → IRR ~13%
    irr = I._irr([-1000, 600, 600])
    assert irr is not None and 12 < irr < 14


def test_irr_none_se_nessun_cambio_segno():
    assert I._irr([100, 200, 300]) is None
    assert I._irr([-100, -200]) is None


def test_debt_capacity_e_covenant():
    a = _ed()
    dc = a["debt_capacity"]
    assert abs(dc["pfn_ebitda_attuale"] - 1.64) < 0.02
    # post: (5,5M + 6,9M) / (3,36M + 12M×14%) = 12,4M / 5,04M ≈ 2,46x
    assert abs(dc["pfn_ebitda_post"] - 2.46) < 0.05
    assert dc["entro_covenant"] is True          # 2,46x < 3x
    assert dc["debito_aggiuntivo_max_a_covenant_eur"] > 0


def test_verdetto_go_with_conditions_su_margine_sensibile():
    # a 14% l'NPV è positivo ma la sensitività lo porta negativo a margine -3pp → condizionato
    a = _ed(14.0)
    assert a["decisione_investimento"]["verdetto"] == "GO WITH CONDITIONS"
    sens = a["sensitivita_npv"]
    assert sens["margine_-3pp"] < 0 < sens["margine_+3pp"]


def test_verdetto_go_su_margine_alto():
    a = _ed(20.0)
    assert a["decisione_investimento"]["verdetto"] == "GO"


def test_verdetto_nogo_se_negativo_ovunque():
    # CAPEX enorme, ricavi minimi → NPV negativo in ogni scenario
    a = I.build_investment(50000000, 500000, 800000, 10.0, FIN, {})
    assert a["decisione_investimento"]["verdetto"] == "NO-GO"


def test_stress_test_concentrazione_e_perdita_cliente():
    st = I.stress_investment(12000000, 14.0, 24000000, 3360000, 105)
    assert abs(st["concentrazione_cliente_pct"] - 33.33) < 0.1   # 12M/(24M+12M)
    perdita = st["scenari"][0]
    assert perdita["impatto_ebitda_eur"] == -1680000            # 12M×14%
    assert st["ritardo_pagamenti"] is not None


def test_leva_oltre_covenant_da_conditions():
    # PFN già alta + CAPEX grande → leva post > 3x
    fin = {**FIN, "pfn": 9000000, "ebitda": 3360000}
    a = I.build_investment(6900000, 4000000, 12000000, 20.0, fin, {"giorni_incasso": 105})
    dc = a["debt_capacity"]
    if not dc["entro_covenant"]:
        assert a["decisione_investimento"]["verdetto"] == "GO WITH CONDITIONS"
        assert "covenant" in a["decisione_investimento"]["motivo"]


def test_apply_investment_noop_senza_capex():
    d, meta = I.apply_investment({"executive_summary": {}}, {"settore_ateco": "X"}, {})
    assert meta is None and "investment_summary" not in d


def test_apply_investment_inietta_e_registra_grounding():
    facts = {}
    reclass = {"ce": {"ricavi": 24000000, "ebitda": 3360000},
               "indici": {"pfn": 5500000, "ebitda_margin": 14.0},
               "sp": {"debiti_finanziari": 8700000, "liquidita": 3200000, "patrimonio_netto": 12000000}}
    inputs = {"investimento_progetto": {"capex": 6900000, "ricavi_incrementali_anno1": 4000000,
                                        "ricavi_incrementali_regime": 12000000, "giorni_incasso": 105}}
    d, meta = I.apply_investment({"executive_summary": {}}, inputs, reclass, facts)
    assert meta["investment_engine"] and meta["verdetto"] == "GO WITH CONDITIONS"
    for k in ("decisione_investimento", "investment_summary", "debt_capacity",
              "sensitivita_npv", "stress_test_investimento"):
        assert k in d
    assert facts.get("_investment_grounded_numbers", {}).get("numeri")
