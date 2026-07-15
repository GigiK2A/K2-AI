"""Expansion Engine — economia deterministica dell'espansione internazionale.

Verificato sui numeri REALI dell'eval NaturaViva (DE/FR/NL, rotta distributore) e su casi
sintetici positivi/degradati. Il modello economico è dichiarato nel docstring di
app/expansion.py; qui si blinda che i numeri derivino dagli input (mai inventati) e che
la decisione/ranking siano coerenti.
"""
from __future__ import annotations

import math

from app import expansion as X

# --- input NaturaViva (dall'eval) ---------------------------------------------------
NV = [
    {"paese": "Germania", "target_ricavi_min": 500000, "target_ricavi_max": 600000,
     "canale": "distributore", "margine_canale_pct": 9, "sconto_pct": 38, "marketing_eur": 35000,
     "resi_pct": 10, "pagamento_giorni": 60, "esclusiva_anni": 2,
     "logistica_pct_min": 8, "logistica_pct_max": 9},
    {"paese": "Francia", "target_ricavi_min": 300000, "target_ricavi_max": 400000,
     "canale": "distributore", "margine_canale_pct": 9, "sconto_pct": 32, "marketing_eur": 20000,
     "pagamento_giorni": 45, "logistica_pct_min": 6, "logistica_pct_max": 7},
    {"paese": "Paesi Bassi", "target_ricavi_min": 150000, "target_ricavi_max": 200000,
     "canale": "distributore", "margine_canale_pct": 9, "sconto_pct": 28, "marketing_eur": 9000,
     "resi_pct": 5, "pagamento_giorni": 30, "logistica_pct_min": 5, "logistica_pct_max": 6},
]


def _by_country(eco_list):
    return {e["paese"]: e for e in eco_list}


def test_conto_economico_deriva_dagli_input_germania():
    a = X.build_expansion(NV, {"budget_eur": 250000})
    de = _by_country(a["conto_economico_mercati"])["Germania"]
    # ricavi = midpoint(500k,600k) = 550k; ricavi_netti = 550k*(1-0.10)=495k
    assert de["ricavi_target_eur"] == 550000
    assert de["ricavi_netti_eur"] == 495000
    # margine_lordo = 495k*9% = 44550; logistica = 550k*8.5% = 46750
    assert de["margine_lordo_eur"] == 44550
    assert de["costo_logistica_eur"] == 46750
    # contribuzione = 44550 - 46750 - 35000 = -37200  (rotta distributore in perdita)
    assert de["contribuzione_eur"] == -37200
    assert de["formula"] and de["assunzioni"]  # trasparenza obbligatoria


def test_nessun_numero_inventato_solo_derivati_o_assunti():
    a = X.build_expansion(NV, {})
    for e in a["conto_economico_mercati"]:
        # ogni € del conto economico è o derivato (con formula) o assunto (elencato)
        assert e["stato"] == "calcolato"
        assert "formula" in e
        # i resi/logistica assenti in Francia sono dichiarati come assunzione, non messi a caso
    fr = _by_country(a["conto_economico_mercati"])["Francia"]
    assert any("resi" in x for x in fr["assunzioni"])  # resi non dichiarati → assunti 0%


def test_ranking_ordina_per_margine_non_per_dimensione():
    # bug eval: Germania (grande ma più in perdita) veniva prima dei Paesi Bassi
    a = X.build_expansion(NV, {"budget_eur": 250000})
    ordine = [r["paese"] for r in a["ranking_mercati"]]
    assert ordine == ["Paesi Bassi", "Francia", "Germania"]
    assert all(r["decisione"] == "NO-GO" for r in a["ranking_mercati"])  # tutti in perdita


def test_budget_confrontato_col_dichiarato():
    a = X.build_expansion(NV, {"budget_eur": 250000})
    assert "250.000" in a["sintesi_budget"] and "compatibile" in a["sintesi_budget"]


def test_scenari_prudente_peggiore_di_base_aggressivo_migliore():
    a = X.build_expansion(NV, {})
    s = a["scenari_espansione"]
    assert s["prudente"]["contribuzione_eur"] < s["base"]["contribuzione_eur"] < s["aggressivo"]["contribuzione_eur"]


def test_confronto_canali_segnala_ecommerce_e_dati_mancanti():
    a = X.build_expansion(NV, {})
    c = a["confronto_canali"]
    assert c["ecommerce_margine_pct"] > c["distributore_margine_pct"]
    assert "CAC" in " ".join(c["dati_mancanti_ecommerce"]) or any("CAC" in x for x in c["dati_mancanti_ecommerce"])


def test_mercato_positivo_va_in_enter():
    # margine di canale sano (25%), costi bassi → contribuzione positiva, bassa complessità
    m = [{"paese": "Spagna", "target_ricavi": 400000, "margine_canale_pct": 25,
          "marketing_eur": 20000, "logistica_pct": 5, "resi_pct": 3, "pagamento_giorni": 30}]
    a = X.build_expansion(m, {})
    r = a["ranking_mercati"][0]
    assert r["decisione"] == "ENTER" and r["contribuzione_eur"] > 0


def test_mercato_sottile_va_in_pilot():
    # margine di contribuzione ~7-8% (banda PILOT 6-12%), complessità bassa
    m = [{"paese": "Belgio", "target_ricavi": 300000, "margine_canale_pct": 16,
          "marketing_eur": 12000, "logistica_pct": 4, "resi_pct": 2, "pagamento_giorni": 30}]
    a = X.build_expansion(m, {})
    r = a["ranking_mercati"][0]
    assert r["decisione"] == "PILOT" and 6 <= r["margine_contribuzione_pct"] < 12


def test_dati_insufficienti_non_inventa():
    m = [{"paese": "Portogallo"}]  # nessun ricavo/margine
    a = X.build_expansion(m, {})
    e = a["conto_economico_mercati"][0]
    assert e["stato"] == "dati_insufficienti" and "N/D" in e["nota"]
    assert a["ranking_mercati"][0]["decisione"] == "WAIT"


def test_apply_expansion_noop_senza_mercati():
    d, meta = X.apply_expansion({"discovery": {}}, {"descrizione_azienda": "x"})
    assert meta is None and d == {"discovery": {}}


def test_apply_expansion_inietta_sezioni():
    d, meta = X.apply_expansion({"discovery": {}}, {"mercati_esteri": NV, "budget_espansione_eur": 250000})
    assert meta and meta["mercati_calcolati"] == 3
    for k in ("conto_economico_mercati", "ranking_mercati", "scenari_espansione", "confronto_canali", "raccomandazione"):
        assert k in d


def test_binder_registra_numeri_grounded_e_gate_non_li_cancella():
    # interazione critica: i numeri derivati dall'engine NON devono essere cancellati dal
    # gate di grounding (che su StrategyBoost, qualitativo, neutralizzerebbe gli hard-financial)
    from app import pipeline, quality
    inputs = {"mercati_esteri": NV, "budget_espansione_eur": 250000, "ragione_sociale": "NaturaViva"}
    facts = {}
    d, meta = pipeline.apply_deterministic_bindings(
        "flusso-strategyboost-pmi", {"discovery": {}}, facts, inputs, {})
    assert meta["expansion"]["mercati_calcolati"] == 3
    assert "_expansion_grounded_numbers" in facts  # registrati per il grounding
    known = quality.grounded_numbers(inputs, facts, [])
    assert round(37200.0, 4) in known and round(44550.0, 4) in known
    out = quality.neutralize_ungrounded_numbers(d, inputs, facts, [], hard_only=True)
    de = _by_country(out["conto_economico_mercati"])["Germania"]
    assert de["contribuzione_eur"] == -37200  # preservato, non → N/D


def test_binder_noop_su_strategyboost_senza_mercati():
    from app import pipeline
    facts = {}
    d, meta = pipeline.apply_deterministic_bindings(
        "flusso-strategyboost-pmi", {"discovery": {}}, facts, {"descrizione_azienda": "x"}, {})
    assert "expansion" not in meta and "conto_economico_mercati" not in d


def test_render_non_crasha_con_sezioni_expansion(tmp_path):
    # il renderer generico deve stampare le sezioni expansion senza eccezioni
    from app import render, assets
    inputs = {"mercati_esteri": NV, "ragione_sociale": "NaturaViva"}
    d, _ = X.apply_expansion(
        {"meta": {"cliente": "NaturaViva"}, "discovery": {"sintesi": "espansione EU"}}, inputs)
    bp = assets.load_blueprint("flusso-strategyboost-pmi") or {}
    render.render_pdf(d, bp, [], tmp_path / "exp.pdf", preliminare=True)
    assert (tmp_path / "exp.pdf").exists() and (tmp_path / "exp.pdf").stat().st_size > 1000


# --- market-entry scenario-based (eval espansione USA integratori) --------------------
USA_SCENARI = [
    {"nome": "prudente", "ricavi_anno1": 1200000, "ricavi_anno3": 3000000, "investimento": 500000},
    {"nome": "base", "ricavi_anno1": 2000000, "ricavi_anno3": 6000000, "investimento": 1800000},
    {"nome": "aggressivo", "ricavi_anno1": 3000000, "ricavi_anno3": 10000000, "investimento": 5500000},
]
USA_AZIENDA = {"fatturato": 18000000, "ebitda_pct": 16}
USA_CONC = {"cliente_top_attuale_pct": 12, "soglia_rischio_pct": 25, "soglia_eccessiva_pct": 30}
USA_PREF = ["minimi garantiti", "diritto di revoca", "durata 1-2 anni",
            "no dipendenza da un singolo cliente", "sviluppare altri canali"]


def _me():
    return X.build_market_entry(USA_SCENARI, USA_AZIENDA, USA_CONC, USA_PREF, "USA")


def test_market_entry_decisione_go_with_conditions():
    # aggressivo profittevole in scala ma concentrazione 36% > soglia 30% → condizionato
    a = _me()
    assert a["decisione_investimento"]["verdetto"] == "GO WITH CONDITIONS"


def test_market_entry_roi_e_payback_derivati():
    a = _me()
    sc = {s["nome"]: s for s in a["simulazione_scenari"]}
    # base: ricavi_3y=2+4+6=12M, ebitda 16%=1.92M, ROI=(1.92-1.8)/1.8=6.67%
    assert abs(sc["base"]["roi_3y_pct"] - 6.67) < 0.1
    # aggressivo: EBITDA cumulato 3y < investimento 5.5M → ROI negativo (over-invest)
    assert sc["aggressivo"]["roi_3y_pct"] < 0
    # ogni scenario ha formula + assunzioni (trasparenza)
    assert all(s.get("formula") and s.get("assunzioni") for s in a["simulazione_scenari"])


def test_market_entry_quota_concentrazione():
    a = _me()
    sc = {s["nome"]: s for s in a["simulazione_scenari"]}
    # aggressivo: 10M / (18M+10M) = 35.7%
    assert abs(sc["aggressivo"]["quota_concentrazione_anno3_pct"] - 35.71) < 0.1


def test_market_entry_stress_test_quote_e_ebitda_a_rischio():
    a = _me()
    quote = [r["quota_pct"] for r in a["stress_test_concentrazione"]["tabella"]]
    assert quote == [15, 25, 35, 45]
    r35 = next(r for r in a["stress_test_concentrazione"]["tabella"] if r["quota_pct"] == 35)
    assert r35["livello"] == "critico" and r35["ebitda_a_rischio_se_perso_eur"] > 0


def test_market_entry_clausole_dalle_preferenze():
    a = _me()
    cl = a["struttura_contrattuale"]["clausole_raccomandate"]
    assert len(cl) >= 4  # minimi, revoca, durata, anti-concentrazione
    testo = " ".join(cl).lower()
    assert "minim" in testo and "recesso" in testo and "concentrazione" in testo


def test_market_entry_readiness_quattro_aree():
    a = _me()
    aree = {r["area"] for r in a["readiness"]}
    assert aree == {"produttiva", "finanziaria", "organizzativa", "normativa"}
    # normativa: flag FDA come workstream, non inventato
    norm = next(r for r in a["readiness"] if r["area"] == "normativa")
    assert "FDA" in norm["nota"]


def test_market_entry_roadmap_quattro_orizzonti():
    a = _me()
    orizzonti = [r["orizzonte"] for r in a["roadmap_ingresso"]]
    assert orizzonti == ["0-3 mesi", "3-6 mesi", "6-12 mesi", "12-24 mesi"]


def test_market_entry_no_go_se_tutti_roi_negativi():
    scen = [{"nome": "unico", "ricavi_anno1": 500000, "ricavi_anno3": 800000, "investimento": 5000000}]
    a = X.build_market_entry(scen, USA_AZIENDA, USA_CONC, [], "USA")
    assert a["decisione_investimento"]["verdetto"] == "NO-GO"


def test_apply_market_entry_noop_senza_scenari():
    d, meta = X.apply_market_entry({"discovery": {}}, {"descrizione_azienda": "x"})
    assert meta is None and d == {"discovery": {}}


def test_apply_market_entry_inietta_e_registra_grounding():
    facts = {}
    inputs = {"espansione_scenari": USA_SCENARI, "fatturato": 18000000, "ebitda_pct": 16,
              "concentrazione": USA_CONC, "preferenze_contratto": USA_PREF, "mercato_target": "USA"}
    d, meta = X.apply_market_entry({"discovery": {}}, inputs, facts)
    assert meta["verdetto"] == "GO WITH CONDITIONS" and meta["scenari_calcolati"] == 3
    for k in ("decisione_investimento", "simulazione_scenari", "stress_test_concentrazione",
              "readiness", "struttura_contrattuale", "roadmap_ingresso"):
        assert k in d
    assert facts.get("_expansion_grounded_numbers", {}).get("numeri")


def test_break_even_e_roi_coerenti():
    m = [{"paese": "Austria", "target_ricavi": 500000, "margine_canale_pct": 20,
          "marketing_eur": 30000, "logistica_pct": 6, "pagamento_giorni": 60}]
    a = X.build_expansion(m, {})
    e = a["conto_economico_mercati"][0]
    # break-even = marketing / (margine% - logistica%) = 30000/0.14 ≈ 214286
    assert math.isclose(e["break_even_ricavi_eur"], 30000 / 0.14, rel_tol=0.01)
    # capitale circolante = 500k * 60/365 ≈ 82192
    assert math.isclose(e["capitale_circolante_eur"], 500000 * 60 / 365, rel_tol=0.01)
