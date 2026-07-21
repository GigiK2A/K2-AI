"""Test del report planner + pacchetto consulenziale operations (spec §6-§10, §14)
e della dedup KPI render-side (#5). Copre il Test 5 della spec: con un caso tipo
K2A (riorganizzazione commesse) il report include AS-IS, TO-BE, RACI, governance,
KPI, piano 30-60-90 e alternative tecnologiche.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import consulting, control  # noqa: E402

# Input tipo caso K2A: dati operativi + racconto libero della situazione.
_FORM = {
    "mese": "giugno", "anno": 2026, "azienda": "K2A S.r.l.",
    "fatturato": 100000, "costi_operativi": 73000,
    "progetti_in_corso": 420, "progetti_in_ritardo": 92,
    "contesto": ("Gestione commesse frammentata: gestionale interno usato in modo non "
                 "uniforme, Excel personali, WhatsApp ed email. Oltre 2000 attività aperte, "
                 "otto project manager, riunioni lunghe. Commesse in ritardo e bloccate, "
                 "serve riorganizzare i processi e il workflow di avanzamento."),
}


def _pack():
    deliverable, _ = control.apply_controlboost({"meta": {}}, _FORM)
    return consulting.build_pack("cruscotto-direzionale", _FORM, deliverable), deliverable


# ── planner ─────────────────────────────────────────────────────────────────────
def test_classifier_detects_operations_case():
    assert consulting.classify_problem(_FORM) == "operations_commesse"


def test_classifier_none_without_signals():
    assert consulting.classify_problem({"mese": "giugno", "anno": 2026,
                                        "fatturato": 1000}) is None
    assert consulting.classify_problem({"contesto": "vorrei migliorare il posizionamento "
                                                    "del brand sui social network"}) is None


# ── Test 5 spec: sezioni obbligatorie presenti ──────────────────────────────────
def test_pack_has_all_mandatory_sections():
    pack, _ = _pack()
    assert pack is not None
    for section in ("processo_as_is", "criticita_rilevate", "processo_to_be",
                    "stati_commessa", "matrice_raci", "governance", "sla_interni",
                    "requisiti_funzionali", "opzioni_tecnologiche", "piano_30_60_90",
                    "dati_da_raccogliere"):
        assert section in pack, section


def test_as_is_uses_only_provided_data():
    pack, _ = _pack()
    asis = pack["processo_as_is"]
    assert "Gestionale" in asis["strumenti_in_uso"]
    assert "Whatsapp" in asis["strumenti_in_uso"]
    assert "Excel" in asis["strumenti_in_uso"]
    assert "Erp" not in asis["strumenti_in_uso"]        # non citato → non compare
    assert asis["dati_dichiarati"]["progetti in corso"] == 420
    assert asis["confidence"] in ("A", "B", "C")
    assert asis["evidenze"]


def test_criticita_grounded_in_kpis_with_confidence():
    """Le criticità derivano SOLO dai KPI rosso/giallo del deliverable, con
    confidence A ed evidenza. KPI verdi → nessuna criticità inventata."""
    deliverable = {"kpi_processi": [
        {"nome": "Commesse in ritardo", "valore": 22, "target": 10,
         "unita": "%", "semaforo": "rosso"},
        {"nome": "Margine", "valore": 27, "target": 25, "unita": "%", "semaforo": "verde"},
    ]}
    crit = consulting._criticita_from_kpis(deliverable)
    assert len(crit) == 1                    # solo il rosso, il verde non è una criticità
    assert "Commesse in ritardo" in crit[0]["criticita"]
    assert crit[0]["confidence"] == "A"      # derivata da un KPI calcolato sui dati reali
    assert crit[0]["evidenze"]
    # nessun KPI critico → lista vuota, mai criticità inventate
    assert consulting._criticita_from_kpis({"kpi": [
        {"nome": "X", "valore": 1, "target": 1, "semaforo": "verde"}]}) == []


def test_raci_only_proposed_roles_no_person_names():
    pack, _ = _pack()
    raci = pack["matrice_raci"]
    assert all("(proposto)" in r for r in raci["ruoli"])
    assert len(raci["attivita"]) == 10       # le 10 attività richieste dalla spec §8
    # una sola A per attività
    for item in raci["attivita"]:
        marks = list(item["assegnazioni"].values())
        assert marks.count("A") == 1, item["attivita"]


def test_sla_labeled_as_proposed_thresholds():
    """§10: le soglie proposte devono essere etichettate come ipotesi."""
    pack, _ = _pack()
    sla = pack["sla_interni"]
    assert "proposta" in sla["nota"].lower() and "30 giorni" in sla["nota"]
    assert sla["source"] == "assumption"
    assert all(s["soglia_proposta"] for s in sla["soglie"])


def test_tech_options_three_and_conditional_recommendation():
    """§9: tre opzioni comparate + raccomandazione condizionata, non prescrittiva."""
    pack, _ = _pack()
    opz = pack["opzioni_tecnologiche"]
    assert len(opz["opzioni"]) == 3
    for o in opz["opzioni"]:
        assert o["vantaggi"] and o["svantaggi"]
        assert o["complessita"] and o["rischio_migrazione"]
        # niente costi inventati
        assert "costo_eur" not in o and "costo" not in {k.lower() for k in o}
    rac = opz["raccomandazione_condizionata"].lower()
    assert "verificare" in rac and "api" in rac       # "prima verificare le API..."


def test_dati_da_raccogliere_reflects_missing_inputs():
    pack, _ = _pack()
    dati = " ".join(pack["dati_da_raccogliere"]).lower()
    # ore fatturabili NON fornite nel form → richieste
    assert "ore fatturabili" in dati
    # progetti in corso forniti → NON richiesti
    assert "numero di commesse attive" not in dati
    assert "storico mensile" in dati


def test_no_pack_for_non_operations_case():
    deliverable, _ = control.apply_controlboost(
        {"meta": {}}, {"mese": "giugno", "anno": 2026, "azienda": "X",
                       "fatturato": 1000, "costi_operativi": 500})
    assert consulting.build_pack("cruscotto-direzionale",
                                 {"mese": "giugno", "anno": 2026, "fatturato": 1000},
                                 deliverable) is None


# ── il pacchetto passa il quality gate ──────────────────────────────────────────
def test_pack_passes_quality_gate_with_evidence():
    from app import provenance as PROV
    from app.quality_gate import run_report_quality_gate
    pack, deliverable = _pack()
    deliverable["consulenza_operativa"] = pack
    res = run_report_quality_gate(deliverable, evidence=PROV.build_evidence(_FORM))
    assert res["ok"] is True, res["report"]


# ── render end-to-end: il PDF si costruisce con il pacchetto ────────────────────
def test_pdf_renders_with_consulting_pack():
    from app.render import render_generic_pdf
    pack, deliverable = _pack()
    deliverable["consulenza_operativa"] = pack
    deliverable["executive_summary"] = "Riorganizzazione della gestione commesse."
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "out.pdf"
        render_generic_pdf(deliverable, {"nome": "ControlBoost"}, [], pdf)
        content = pdf.read_bytes()
        assert content[:5] == b"%PDF-"
        assert len(content) > 20_000       # PDF sostanzioso, non vuoto


# ── dedup KPI render-side (#5, Test 4 spec) ─────────────────────────────────────
def test_render_dedups_repeated_kpis():
    """Lo stesso KPI in due sezioni → tabella piena una volta sola + richiamo."""
    from app.render import render_generic_pdf
    kpi = {"nome": "Commesse in ritardo", "valore": 22, "target": 10,
           "unita": "%", "semaforo": "rosso"}
    deliverable = {
        "executive_summary": "x",
        "kpi_processi": [dict(kpi)],
        "kpi_crescita": [dict(kpi)],       # duplicato identico in altra sezione
    }
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "out.pdf"
        render_generic_pdf(deliverable, {}, [], pdf)
        assert pdf.exists()
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf)) as doc:
                text = "\n".join(p.extract_text() or "" for p in doc.pages)
            assert "Già riportati sopra" in text
        except ImportError:
            pass   # senza pdfplumber basta che il PDF si costruisca senza doppioni fatali
