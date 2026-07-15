"""Regressione corruzione dati FinanceBoost (eval ElectroDrive Components, 15 lug 2026).

Il cliente fornisce AGGREGATI (EBITDA/EBIT/utile/liquidità/PFN). L'autofill fabbricava
'voci' mislabellando l'EBITDA come costo → reclassify_bilancio calcolava EBITDA = ricavi −
costi = 24M − 3,36M = 20,64M; liquidità → 0 (nessun campo); PFN → debiti (8,7M). KPI: EBITDA
margin 86%, ROE 172%. Fix: gli aggregati dell'utente sono AUTORITATIVI (reclass_reconciled)
+ gate di validazione numerica. I numeri devono restare IDENTICI all'input.
"""
from __future__ import annotations

from app import finance

# ElectroDrive: aggregati reali + voci FABBRICATE dall'autofill (EBITDA come costo)
ED_INPUTS = {"bilanci": [{
    "anno": 2024,
    "ricavi": 24000000, "ebitda": 3360000, "reddito_operativo": 2150000, "utile_netto": 1150000,
    "totale_attivo": 30000000, "patrimonio_netto": 12000000, "debiti_finanziari": 8700000,
    "liquidita": 3200000, "pfn": 5500000,
    "voci": [
        {"sezione": "ricavi", "descrizione": "Ricavi", "importo": 24000000},
        {"sezione": "costi", "descrizione": "EBITDA", "importo": 3360000},  # MISLABEL
        {"sezione": "attivo", "descrizione": "Totale attivo", "importo": 30000000},
        {"sezione": "passivo", "descrizione": "Debiti finanziari", "importo": 8700000},
        {"sezione": "passivo", "descrizione": "Patrimonio netto", "importo": 12000000},
    ],
}]}


def test_aggregati_utente_restano_identici():
    rc = finance.reclass_reconciled(ED_INPUTS)
    assert rc["ce"]["ebitda"] == 3360000      # NON 20.640.000
    assert rc["ce"]["ebit"] == 2150000
    assert rc["ce"]["utile_netto"] == 1150000
    assert rc["fonte"] == "aggregati_cliente"


def test_liquidita_non_azzerata():
    rc = finance.reclass_reconciled(ED_INPUTS)
    assert rc["sp"]["liquidita"] == 3200000    # NON 0


def test_pfn_dichiarata_ha_precedenza():
    rc = finance.reclass_reconciled(ED_INPUTS)
    assert rc["indici"]["pfn"] == 5500000      # NON 8.700.000 (= debiti)
    assert abs(rc["indici"]["pfn_ebitda"] - 1.64) < 0.02  # PFN/EBITDA sano ~1,6x


def test_kpi_plausibili():
    rc = finance.reclass_reconciled(ED_INPUTS)
    idx = rc["indici"]
    assert abs(idx["ebitda_margin"] - 14.0) < 0.1   # NON 86%
    assert abs(idx["roe"] - 9.6) < 0.2              # NON 172%
    assert abs(idx["ros"] - 9.0) < 0.2              # NON 86%
    assert idx["roi"] is not None and idx["roi"] < 20  # NON 68,8%


def test_validazione_nessuna_anomalia_su_dati_corretti():
    rc = finance.reclass_reconciled(ED_INPUTS)
    assert finance.validate_kpis(rc, ED_INPUTS) == []


def test_pfn_da_liquidita_se_non_dichiarata():
    # senza pfn esplicita: PFN = debiti − liquidità = 8,7M − 3,2M = 5,5M
    inp = {"bilanci": [{"anno": 2024, "ricavi": 24000000, "ebitda": 3360000,
                        "utile_netto": 1150000, "patrimonio_netto": 12000000,
                        "debiti_finanziari": 8700000, "liquidita": 3200000}]}
    rc = finance.reclass_reconciled(inp)
    assert rc["indici"]["pfn"] == 5500000


def test_gate_becca_le_voci_corrotte():
    # se per qualche motivo passasse il reclass da voci corrotte, il gate lo intercetta
    bad = finance.reclassify_bilancio(ED_INPUTS["bilanci"][0]["voci"], 2024)
    an = finance.validate_kpis(bad, ED_INPUTS)
    codici = {a["codice"] for a in an}
    assert "ebitda_margin_implausibile" in codici
    assert "roe_implausibile" in codici
    assert "liquidita_azzerata" in codici
    assert any(a["gravita"] == "errore" for a in an)


def test_bilancio_vero_a_voci_non_regredisce():
    # un bilancio REALE trascritto a voci (senza aggregati top-level) usa ancora il path voci
    voci = [
        {"sezione": "ricavi", "descrizione": "Ricavi delle vendite", "importo": 1000000},
        {"sezione": "costi", "descrizione": "Costi materie prime", "importo": 600000},
        {"sezione": "costi", "descrizione": "Costo del personale", "importo": 250000},
        {"sezione": "attivo", "descrizione": "Disponibilità liquide", "importo": 150000},
        {"sezione": "attivo", "descrizione": "Immobilizzazioni", "importo": 650000},
        {"sezione": "passivo", "descrizione": "Patrimonio netto", "importo": 500000},
        {"sezione": "passivo", "descrizione": "Debiti v/banche", "importo": 300000},
        {"sezione": "risultato", "descrizione": "Utile del periodo", "importo": 150000},
    ]
    rc = finance.reclass_reconciled({"bilanci": [{"anno": 2023, "voci": voci}]})
    assert rc is not None and rc["ce"]["ricavi"] == 1000000
    # EBITDA = ricavi − costi operativi (senza ammortamenti) = 1M − 850k = 150k
    assert rc["ce"]["ebitda"] == 150000
