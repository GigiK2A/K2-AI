"""I motori di ragionamento coprono TUTTI i domini: operations, marketing/canali,
HR/persone, legale/compliance, strategia/crescita (finanza già in
test_senior_reasoning). Per ogni dominio: classificazione, insight calcolati,
catene valide, opzioni complete, raccomandazioni coi 4 perché, gate, PDF.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import consulting, reasoning  # noqa: E402
from app.quality_gate import run_report_quality_gate  # noqa: E402

_CASES = {
    "operations_commesse": {
        "azienda": "OpsCo", "fatturato": 2_000_000,
        "progetti_in_corso": 420, "progetti_in_ritardo": 92,
        "ore_lavorate": 1600, "ore_fatturabili": 1000,
        "clienti_attivi": 40, "clienti_persi": 3,
        "contesto": "Commesse in ritardo, processi non uniformi, gestionale usato male, "
                    "riunioni lunghe: serve riorganizzare il workflow di avanzamento.",
    },
    "marketing_canali": {
        "nome": "B&B Test", "ota_dependency_pct": 78, "fatturato": 400_000,
        "budget_mensile_eur": 800, "clienti_attivi": 900, "nuovi_clienti": 120,
        "contesto": "Quasi tutte le prenotazioni arrivano da Booking: commissioni alte, "
                    "serve più canale diretto e visibilità del sito.",
    },
    "hr_persone": {
        "azienda": "HRCo", "fatturato": 1_500_000, "dipendenti": 14,
        "costi_operativi": 95_000, "ore_lavorate": 2000,
        "contesto": "Il personale è saturo, temiamo dimissioni: capire se servono "
                    "assunzioni o una riorganizzazione del team e della formazione.",
    },
    "legale_compliance": {
        "forma_giuridica": "srl", "n_dipendenti": 18, "fatturato": 1_200_000,
        "tratta_dati_personali": True, "ha_contratti_standard": False,
        "ha_sito_ecommerce": True, "usa_ai_profilazione": True,
        "opera_estero": True, "ha_marchio": False, "ha_modello_231": False,
        "quesito": "Vogliamo capire i rischi legali e privacy della nostra attività.",
    },
    "strategia_crescita": {
        "azienda": "StratCo", "fatturato": 3_000_000,
        "margine_ecommerce_pct": 45, "margine_distributore_pct": 22,
        "budget_espansione_eur": 120_000, "mol_medio_pct": 12,
        "concentrazione": "alta", "concentrazione_top3": 55,
        "obiettivo_strategico": "Espansione nel mercato tedesco: scegliere tra canale "
                                "diretto e-commerce e un distributore locale.",
    },
}


def _pack(domain):
    return consulting.build_pack("", _CASES[domain], {})


# ── classificazione: ogni caso finisce nel suo dominio ─────────────────────────
def test_classification_per_domain():
    for domain, case in _CASES.items():
        assert consulting.classify_problem(case) == domain, domain


# ── struttura comune: motori attivi in ogni dominio ────────────────────────────
def test_every_domain_pack_has_engine_output():
    for domain in _CASES:
        pack = _pack(domain)
        assert pack is not None, domain
        assert pack["_tipo"] == domain
        assert pack["insight_derivati"], f"{domain}: nessun insight"
        assert pack["analisi_sistemica"], f"{domain}: nessuna catena causale"
        assert pack["raccomandazioni_operative"], f"{domain}: nessuna raccomandazione"
        assert pack["copertura_dati"]["dati_forniti"], domain


def test_insights_have_formula_data_explanation():
    for domain in _CASES:
        for i in _pack(domain)["insight_derivati"]:
            assert i["formula"], f"{domain}:{i['id']}"
            assert i["dati_usati"], f"{domain}:{i['id']}"
            assert len(i["spiegazione"]) > 40, f"{domain}:{i['id']}"
            assert i["confidence"] == "A"


def test_chains_valid_in_every_domain():
    for domain in _CASES:
        for c in _pack(domain)["analisi_sistemica"]:
            assert reasoning.validate_chain(c) == [], f"{domain}:{c['id']}"


def test_options_complete_where_present():
    # operations tiene le opzioni tecnologiche del pack storico; gli altri ≥3 opzioni motore
    for domain in ("marketing_canali", "hr_persone", "legale_compliance",
                   "strategia_crescita"):
        conf = _pack(domain)["confronto_soluzioni"]
        assert len(conf["opzioni"]) >= 3, domain
        for o in conf["opzioni"]:
            for k in ("vantaggi", "svantaggi", "costi", "rischi", "tempi",
                      "complessita", "quando_sceglierla", "quando_evitarla"):
                assert o.get(k), f"{domain}:{o['opzione']}:{k}"
        assert conf["conclusione_motivata"], domain


def test_no_action_option_in_every_domain():
    # #5 review: l'opzione «non intervenire» deve esistere in ogni dominio decisionale.
    from app import decision
    for domain in ("marketing_canali", "hr_persone", "legale_compliance",
                   "strategia_crescita"):
        conf = _pack(domain)["confronto_soluzioni"]
        assert decision._has_no_action(conf["opzioni"]), domain


def test_recommendations_4_whys_everywhere():
    for domain in _CASES:
        for r in _pack(domain)["raccomandazioni_operative"]:
            for k in ("perche", "perche_ora", "perche_questa", "perche_non_altre"):
                assert r.get(k), f"{domain}:{r['id']}:{k}"
            assert r["operativo"]["chi"] and r["operativo"]["cadenza"], domain
            for s in r["soglie"]:
                assert s["classificazione"], f"{domain}: soglia senza classificazione"


def test_simulations_where_data_allows():
    for domain in ("operations_commesse", "marketing_canali", "hr_persone",
                   "strategia_crescita"):
        sims = _pack(domain).get("simulazioni") or []
        assert sims, f"{domain}: nessuna simulazione"
        for s in sims:
            assert s["calcolo"] and s["dati_usati"], domain
    # legale: niente simulazioni numeriche per scelta → nessuna chiave o vuota
    assert not (_pack("legale_compliance").get("simulazioni") or [])


# ── quality gate su ogni pacchetto ─────────────────────────────────────────────
def test_every_pack_passes_quality_gate():
    from app import provenance as PROV
    for domain, case in _CASES.items():
        deliverable = {"executive_summary": "x", "consulenza_operativa": _pack(domain)}
        res = run_report_quality_gate(deliverable, evidence=PROV.build_evidence(case))
        assert res["ok"] is True, f"{domain}: {res['report']}"


# ── PDF end-to-end per un dominio non-finance ──────────────────────────────────
def test_pdf_renders_legal_and_strategy_packs():
    from app.render import render_generic_pdf
    for domain in ("legale_compliance", "strategia_crescita"):
        deliverable = {"executive_summary": "Caso di test.",
                       "consulenza_operativa": _pack(domain)}
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "out.pdf"
            render_generic_pdf(deliverable, {}, [], pdf)
            assert pdf.read_bytes()[:5] == b"%PDF-", domain


# ── numeri esatti a campione ───────────────────────────────────────────────────
def test_sample_calculations():
    ops = _pack("operations_commesse")
    by_id = {i["id"]: i for i in ops["insight_derivati"]}
    assert abs(by_id["ops.pct_ritardo"]["valore"] - 21.9) < 0.1      # 92/420
    assert abs(by_id["ops.utilizzo"]["valore"] - 62.5) < 0.1         # 1000/1600

    strat = _pack("strategia_crescita")
    by_id = {i["id"]: i for i in strat["insight_derivati"]}
    assert by_id["strat.delta_margine_canali"]["valore"] == 23.0     # 45-22
    # simulazione mix: 3M × 10% × 23pp = 69.000 €
    sim = next(s for s in strat["simulazioni"] if "10%" in s["domanda"])
    assert "69" in sim["risultato"]
