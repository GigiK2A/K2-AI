"""Investment Engine — FinanceBoost come investment decision support (eval ElectroDrive +
CoolTech, 15 lug 2026).

Gira sul solo CAPEX (sostenibilità del debito: leva/DSCR/interest coverage/circolante/
financing/decision board) anche SENZA ricavi incrementali (caso CoolTech); con i ricavi
aggiunge NPV/IRR/payback/scenari. Ogni numero con formula e assunzioni; decision board con
criteri quantitativi derivati dai dati. Numeri replicabili da un CFO.
"""
from __future__ import annotations

from app import investment as I

# CoolTech: sostenibilità di un grande investimento (NO ricavi incrementali espliciti)
CT_FIN = {"ebitda": 4200000, "ebit": 2800000, "pfn": 6000000, "debiti_finanziari": 10000000,
          "liquidita": 4000000, "patrimonio_netto": 18000000, "fatturato": 30000000}
CT_PARAMS = {"giorni_incasso": 120, "durata_anni": 7, "tasso_debito_pct": 4.55, "costi_variabili_pct": 63}

# ElectroDrive: investimento con ricavi incrementali del contratto
ED_FIN = {"ebitda": 3360000, "ebit": 2150000, "pfn": 5500000, "debiti_finanziari": 8700000,
          "liquidita": 3200000, "patrimonio_netto": 12000000, "fatturato": 24000000}


# ── CoolTech: sostenibilità sul solo CAPEX (no N/D dove è calcolabile) ────────────────

def test_engine_gira_senza_ricavi_incrementali():
    a = I.build_investment(8000000, None, None, 37.0, CT_FIN, CT_PARAMS)
    assert a is not None                              # NON no-op (prima lo era)
    assert a["investment_summary"]["npv_eur"] is None  # NPV onesto: non calcolabile senza ricavi
    assert "nota" in a["investment_summary"]           # spiega PERCHÉ, niente N/D muto


def test_cooltech_debt_engine_dscr_interest_coverage():
    a = I.build_investment(8000000, None, None, 37.0, CT_FIN, CT_PARAMS)
    d = a["debt_capacity"]
    assert abs(d["pfn_ebitda_attuale"] - 1.43) < 0.02       # 6M/4,2M
    assert abs(d["pfn_ebitda_post"] - 3.33) < 0.02          # (6+8)/4,2
    assert abs(d["interessi_annui_post_eur"] - 819000) < 1  # 4,55%×18M
    assert abs(d["interest_coverage_post"] - 3.42) < 0.05   # 2,8M/819k
    assert d["dscr_post"] is not None and d["dscr_post"] > 0
    assert d["dscr_soglia"] == 1.2


def test_cooltech_working_capital_assorbimento():
    a = I.build_investment(8000000, None, None, 37.0, CT_FIN, CT_PARAMS)
    w = a["working_capital"]
    # crediti = fatturato × 120/365 ≈ 9,86M
    assert abs(w["crediti_generati_eur"] - 30000000 * 120 / 365) < 1000
    assert w["assorbimento_cassa_netto_eur"] > 0


def test_cooltech_financing_options_realistiche():
    a = I.build_investment(8000000, None, None, 37.0, CT_FIN, CT_PARAMS)
    strumenti = " ".join(o["strumento"].lower() for o in a["financing_options"]["opzioni"])
    assert "factoring" in strumenti and "leasing" in strumenti
    # la nota deve escludere il consiglio irrealistico di ridurre i termini di pagamento
    assert "riduzione dei termini" in a["financing_options"]["nota"].lower()


def test_cooltech_decision_board_go_con_condizioni():
    # leva 3,33x>3x e DSCR<1,2x ma STRUTTURABILI con equity → GO CON CONDIZIONI, non NO GO
    a = I.build_investment(8000000, None, None, 37.0, CT_FIN, CT_PARAMS)
    b = a["decision_board"]
    assert b["verdetto"] == "GO CON CONDIZIONI" and b["semaforo"] == "🟡"
    assert "Leva post ≤ 3x" in b["condizioni_go"]
    # criteri quantitativi, non generici
    assert all("dettaglio" in c for c in b["criteri"])


def test_no_go_solo_se_fondamentale():
    # interest coverage < 1,5 (non paga gli interessi) → NO GO
    fin = {**CT_FIN, "ebit": 300000}
    a = I.build_investment(8000000, None, None, 37.0, fin, CT_PARAMS)
    assert a["decision_board"]["verdetto"] == "NO GO"


# ── ElectroDrive: con ricavi → NPV/IRR/payback/scenari ────────────────────────────────

def test_electrodrive_npv_irr_scenari():
    a = I.build_investment(6900000, 4000000, 12000000, 14.0, ED_FIN, {"giorni_incasso": 105})
    s = a["investment_summary"]
    assert s["npv_eur"] is not None and s["irr_pct"] is not None
    assert s["terminal_value_eur"] > 0
    sc = a["scenari_investimento"]
    assert sc["prudente"]["npv_eur"] < sc["base"]["npv_eur"] < sc["aggressivo"]["npv_eur"]


def test_irr_bisezione_corretta():
    irr = I._irr([-1000, 600, 600])
    assert irr is not None and 12 < irr < 14
    assert I._irr([100, 200]) is None            # nessun cambio segno


def test_stress_test_concentrazione():
    st = I.stress_investment(12000000, 14.0, 24000000, 3360000, 105)
    assert abs(st["concentrazione_cliente_pct"] - 33.33) < 0.1
    assert st["scenari"][0]["impatto_ebitda_eur"] == -1680000


# ── trigger + integrazione ────────────────────────────────────────────────────────────

def test_apply_investment_noop_senza_capex():
    d, meta = I.apply_investment({"executive_summary": {}}, {"settore_ateco": "X"}, {})
    assert meta is None


def test_apply_investment_fire_su_capex_solo():
    reclass = {"ce": {"ricavi": 30000000, "ebitda": 4200000, "ebit": 2800000},
               "indici": {"pfn": 6000000, "ebitda_margin": 14.0},
               "sp": {"debiti_finanziari": 10000000, "liquidita": 4000000, "patrimonio_netto": 18000000}}
    inputs = {"investimento_progetto": {"capex": 8000000, "durata_commessa_anni": 7,
                                        "tasso_debito_pct": 4.55, "costi_variabili_pct": 63},
              "giorni_pagamento": 120}
    facts = {}
    d, meta = I.apply_investment({"executive_summary": {}}, inputs, reclass, facts)
    assert meta and meta["investment_engine"]
    for k in ("decision_board", "debt_capacity", "working_capital", "financing_options"):
        assert k in d
    assert facts.get("_investment_grounded_numbers", {}).get("numeri")
