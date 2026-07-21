"""Test del dominio M&A/acquisizione (test K2-AI 'analisi acquisizione azienda').
Copre: calcoli automatici (EV/EBITDA, PFN, leva, ROI), catene, confronto
comprare-vs-crescere-vs-partnership, Executive Summary guidato dalla decisione,
classificazione, gate, PDF.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import consulting, decision, insight, reasoning  # noqa: E402

# Il caso esatto del test: acquisizione di un concorrente.
_CASE = {
    "azienda": "Acquirente S.r.l.",
    "fatturato": 1_800_000, "ebitda": 340_000, "utile_netto": 165_000,
    "patrimonio_netto": 500_000, "prezzo_richiesto": 900_000,
    "debiti_finanziari": 430_000, "liquidita": 120_000,
    "concentrazione_top5": 60,
    "contesto": "Sto valutando l'acquisizione di una piccola azienda concorrente della "
                "mia zona. Non so se convenga acquistarla oppure crescere internamente.",
}


def _pack():
    return consulting.build_ma_pack(_CASE, {})


# ── routing/classificazione: NON deve finire sul legale ────────────────────────
def test_classified_as_ma():
    assert consulting.classify_problem(_CASE) == "ma_acquisizione"
    # anche senza il racconto, i dati del deal bastano
    numeric_only = {k: v for k, v in _CASE.items() if k != "contesto"}
    assert consulting.classify_problem(numeric_only) == "ma_acquisizione"


# ── Problema 4: calcoli automatici, esatti, con formula ────────────────────────
def test_valuation_metrics_exact():
    insights, _ = insight.derive_ma_insights(_CASE)
    by_id = {i["id"]: i for i in insights}
    assert by_id["ma.pfn"]["valore"] == 310_000                 # 430 − 120
    assert by_id["ma.enterprise_value"]["valore"] == 1_210_000  # 900 + 310
    assert by_id["ma.ev_ebitda"]["valore"] == 3.56              # 1210/340
    assert by_id["ma.debt_ebitda"]["valore"] == 1.26            # 430/340
    assert by_id["ma.prezzo_utile"]["valore"] == 5.45           # 900/165
    assert by_id["ma.roi_preliminare"]["valore"] == 18.3        # 165/900
    assert abs(by_id["ma.prezzo_pn"]["valore"] - 1.8) < 0.01    # 900/500
    for i in insights:
        assert i["formula"] and i["dati_usati"]                 # Problema 8: verificabili
        assert i["confidence"] == "A" and i["source"] == "system_calculated"


def test_metrics_degrade_without_data():
    # solo prezzo, niente EBITDA/PN/debiti → niente multipli inventati
    ins, _ = insight.derive_ma_insights({"prezzo_richiesto": 900_000})
    ids = {i["id"] for i in ins}
    assert "ma.ev_ebitda" not in ids and "ma.debt_ebitda" not in ids


# ── Problema 2/6: la decisione è al centro, l'Exec Summary parte da lì ──────────
def test_decision_synthesis_answers_the_question():
    dec = decision.ma_decision(_CASE, insight.derive_ma_insights(_CASE)[0])
    assert "acquisire" in dec["domanda_decisionale"].lower()
    assert "crescere" in dec["domanda_decisionale"].lower()
    assert len(dec["sintesi"]) > 200
    assert dec["fattori"]                                       # ragioni ancorate ai numeri


def _flat_text(flow) -> str:
    """Estrae il testo da un albero di flowable reportlab (Paragraph anche dentro Table)."""
    parts = []

    def walk(node):
        if hasattr(node, "text") and isinstance(getattr(node, "text"), str):
            parts.append(node.text)
        data = getattr(node, "_cellvalues", None) or getattr(node, "_cargo", None)
        if isinstance(data, list):
            for row in data:
                for cell in (row if isinstance(row, list) else [row]):
                    if isinstance(cell, list):
                        for x in cell:
                            walk(x)
                    else:
                        walk(cell)

    for f in flow:
        walk(f)
    return " ".join(parts)


def test_executive_summary_leads_with_decision():
    from app.render import _exec_summary
    from app import styling as ST
    pack = _pack()
    deliverable = {"consulenza_operativa": pack,
                   "sintesi": "Concentrazione clienti superiore al 60%."}  # il vecchio alert
    text = _flat_text(_exec_summary(deliverable, ST.styles())).lower()
    # l'Exec Summary parte dalla DECISIONE (comprare vs crescere), non dall'alert secondario
    assert "acquisire" in text and "crescere" in text
    # il vecchio alert non è più la prima cosa
    assert not text.strip().startswith("concentrazione")


# ── Problema 9: confronto reale tra alternative ────────────────────────────────
def test_three_alternatives_compared():
    conf = _pack()["confronto_soluzioni"]
    opzioni = conf["opzioni"]
    assert len(opzioni) == 3
    titoli = " ".join(o["opzione"].lower() for o in opzioni)
    assert "acquisire" in titoli and "internamente" in titoli and "partnership" in titoli
    for o in opzioni:
        for k in ("vantaggi", "svantaggi", "costi", "rischi", "tempi",
                  "quando_sceglierla", "quando_evitarla"):
            assert o.get(k), f"{o['opzione']}: manca {k}"
    assert "prezzo" in conf["conclusione_motivata"].lower()


# ── catene e simulazioni ────────────────────────────────────────────────────────
def test_chains_and_simulations():
    pack = _pack()
    assert pack["analisi_sistemica"], "servono catene causali M&A"
    for c in pack["analisi_sistemica"]:
        assert reasoning.validate_chain(c) == []
    sims = pack.get("simulazioni") or []
    assert sims, "servono simulazioni what-if"
    domande = " ".join(s["domanda"].lower() for s in sims)
    assert "closing" in domande or "ebitda" in domande
    for s in sims:
        assert s["calcolo"] and s["dati_usati"]


# ── Problema 5: i dati del deal NON spariscono (coverage) ──────────────────────
def test_deal_data_all_used():
    cov = _pack()["copertura_dati"]
    assert cov["dati_non_sfruttati"] == [], cov["dati_non_sfruttati"]


# ── gate + PDF end-to-end ───────────────────────────────────────────────────────
def test_pack_passes_gate_and_renders():
    from app import provenance as PROV
    from app.quality_gate import run_report_quality_gate
    from app.render import render_generic_pdf
    pack = _pack()
    deliverable = {"executive_summary": "x", "consulenza_operativa": pack}
    res = run_report_quality_gate(deliverable, evidence=PROV.build_evidence(_CASE))
    assert res["ok"] is True, res["report"]
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "out.pdf"
        render_generic_pdf(deliverable, {"nome": "M&A"}, [], pdf)
        content = pdf.read_bytes()
        assert content[:5] == b"%PDF-" and len(content) > 25_000
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf)) as doc:
                text = "\n".join(p.extract_text() or "" for p in doc.pages)
            assert "EV/EBITDA" in text
            assert "Acquisire" in text and "internamente" in text  # confronto
        except ImportError:
            pass
