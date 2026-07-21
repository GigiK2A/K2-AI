"""Test del Diagnostic Engine (review efficienza organizzativa): il consulente
RAGIONA — ipotesi con probabilità, ipotesi escluse, catena causale, KPI specifici,
niente numeri inventati, risolve la contraddizione salari.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import consulting, diagnosis  # noqa: E402

# Il caso esatto del test: utili giù, fatturato tiene, segnali di inefficienza.
_CASE = {
    "contesto": ("Negli ultimi sei mesi l'azienda sta andando peggio. Non abbiamo perso "
                 "clienti importanti, ma gli utili sono diminuiti parecchio e ho la sensazione "
                 "che qualcosa all'interno dell'organizzazione non stia funzionando. Aumento "
                 "di riunioni, livelli di approvazione, revisioni interne. Dipendenti più "
                 "occupati ma meno produttivi. Cambio del responsabile operativo pochi mesi "
                 "prima dell'inizio del problema. Nessuna nuova assunzione, nessun aumento "
                 "salariale significativo. Materie prime stabili. Numero di progetti stabile, "
                 "ore lavorate stabili."),
    "delta_fatturato_pct": 2, "costo_personale_delta_pct": 12, "spese_generali_delta_pct": 18,
}


def _pack():
    return diagnosis.build_diagnosis_pack(_CASE)


# ── routing/classificazione dai SEGNALI (non da keyword) ──────────────────────
def test_recognized_as_efficiency_case():
    assert diagnosis.is_efficiency_case(_CASE)
    assert consulting.classify_problem(_CASE) == "diagnosi_efficienza"


def test_not_efficiency_without_signals():
    assert not diagnosis.is_efficiency_case(
        {"contesto": "vorrei un piano marketing", "delta_fatturato_pct": 2})


# ── Problema 8: ipotesi con probabilità deterministiche che sommano 100 ────────
def test_diagnostic_hypotheses_probabilities():
    d = diagnosis.build_diagnosis(_CASE)
    assert sum(h["probabilita"] for h in d["ipotesi"]) == 100
    # la causa dominante è l'inefficienza organizzativa
    assert d["ipotesi"][0]["probabilita"] >= 45
    assert "organizzativa" in d["ipotesi"][0]["causa"].lower()
    # sono stime (inference), non fatti
    assert all(h["confidence"] in ("B", "C") for h in d["ipotesi"])
    # ogni ipotesi con evidenze
    assert all(h["evidenze"] for h in d["ipotesi"] if h["probabilita"] >= 10)


# ── Problema 7: ipotesi ESCLUSE col perché ─────────────────────────────────────
def test_excluded_hypotheses():
    d = diagnosis.build_diagnosis(_CASE)
    cause_escluse = " ".join(e["causa"].lower() for e in d["ipotesi_escluse"])
    assert "commerciale" in cause_escluse            # fatturato tiene
    assert "materie" in cause_escluse                # materie stabili
    assert "salariale" in cause_escluse or "assunzioni" in cause_escluse
    for e in d["ipotesi_escluse"]:
        assert e["perche_esclusa"]                    # sempre motivate


# ── Problema 2: la contraddizione salari è RISOLTA, non ripetuta ───────────────
def test_salary_contradiction_resolved():
    ins = diagnosis.derive_efficiency_insights(_CASE)
    par = next((i for i in ins if i["id"] == "eff.paradosso_produttivita"), None)
    assert par is not None, "deve rilevare costo personale su SENZA assunzioni/aumenti"
    # NON attribuisce il problema agli aumenti salariali; lo attribuisce alle ORE
    assert "non è un problema salariale" in par["spiegazione"].lower() or \
           "ore" in par["spiegazione"].lower()


# ── Problema 1: nessun valore assoluto inventato ───────────────────────────────
def test_no_invented_absolute_values():
    pack = _pack()
    # gli insight sono direzionali (punti %, conteggi), mai fatturati/costi assoluti
    for i in pack["insight_derivati"]:
        v = i["valore"]
        if isinstance(v, (int, float)):
            assert abs(v) < 1000, f"valore sospetto (assoluto?): {i['id']}={v}"
    # il pack chiede di sopprimere le sezioni KPI assolute
    assert "kpi_finanziaria" in pack["_suppress_sections"]


def test_pipeline_suppresses_invented_kpis():
    # simula ciò che fa la pipeline: rimuove le sezioni indicate dal pack
    pack = _pack()
    deliverable = {"kpi_finanziaria": [{"nome": "Fatturato", "valore": 99999}],
                   "consulenza_operativa": pack}
    for s in pack.get("_suppress_sections", []):
        deliverable.pop(s, None)
    assert "kpi_finanziaria" not in deliverable


# ── Problema 4: catena causale esplicita ───────────────────────────────────────
def test_causal_chain():
    from app import reasoning
    chains = diagnosis.build_efficiency_chain(_CASE)
    assert chains and reasoning.validate_chain(chains[0]) == []
    testo = " ".join(n["testo"].lower() for n in chains[0]["catena"])
    assert "margine" in testo
    assert "riunioni" in testo or "approvazioni" in testo or "responsabile" in testo


# ── Problema 5: KPI SPECIFICI del problema, non i soliti finanziari ────────────
def test_problem_specific_kpis():
    kpis = diagnosis.efficiency_kpis_to_measure(_CASE)
    joined = " ".join(k["kpi"].lower() for k in kpis)
    assert "approvazione" in joined
    assert "revision" in joined
    assert "riunione" in joined or "produttiv" in joined
    for k in kpis:
        assert k["perche"]                            # ogni KPI motivato


# ── PDF end-to-end: sezioni giuste, ordine ragionamento, niente inventati ──────
def test_pdf_render_diagnosis():
    from app.render import render_generic_pdf
    pack = _pack()
    deliverable = {"executive_summary": "Il fatturato tiene.", "consulenza_operativa": pack}
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "out.pdf"
        render_generic_pdf(deliverable, {"nome": "ControlBoost"}, [], pdf)
        content = pdf.read_bytes()
        assert content[:5] == b"%PDF-" and len(content) > 20_000
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf)) as doc:
                text = "\n".join(p.extract_text() or "" for p in doc.pages)
            assert "Ipotesi diagnostica" in text
            assert "escluse" in text.lower()
            assert "misurare" in text.lower()          # KPI specifici
        except ImportError:
            pass


# ── il pack passa il quality gate ──────────────────────────────────────────────
def test_pack_passes_quality_gate():
    from app import provenance as PROV
    from app.quality_gate import run_report_quality_gate
    deliverable = {"executive_summary": "x", "consulenza_operativa": _pack()}
    res = run_report_quality_gate(deliverable, evidence=PROV.build_evidence(_CASE))
    assert res["ok"] is True, res["report"]
