"""Ops universali (report_ops): la pass è offline-safe (None senza chiave) e i blocchi
operativi (semaforo 4 livelli, matrice Impatto/Probabilità, timeline 4 orizzonti,
checklist, template) si renderizzano nel PDF su qualsiasi boost senza crash."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import llm, render, styling  # noqa: E402

_OPS = {
    "semaforo_rischi": [
        {"area": "Contrattualistica", "livello": "critico", "conseguenza": "Nullità clausole", "urgenza": "alta"},
        {"area": "Privacy & dati", "livello": "medio", "conseguenza": "Sanzione GDPR", "urgenza": "media"},
        {"area": "Fiscale", "livello": "basso", "conseguenza": "Rilievo minore", "urgenza": "bassa"},
    ],
    "matrice_rischi": [
        {"rischio": "Contratto quadro assente", "probabilita": "alta", "impatto": "critica", "priorita": "critica"},
        {"rischio": "Registro trattamenti incompleto", "probabilita": "media", "impatto": "media", "priorita": "media"},
    ],
    "timeline_operativa": [
        {"orizzonte": "immediato", "azione": "Bloccare firme in corso", "priorita": "critica",
         "responsabile": "Titolare", "impatto_atteso": "Stop esposizione"},
        {"orizzonte": "breve", "azione": "Redigere contratto quadro", "priorita": "alta",
         "responsabile": "Avvocato", "impatto_atteso": "Copertura legale"},
        {"orizzonte": "medio", "azione": "Audit privacy", "priorita": "media",
         "responsabile": "IT", "impatto_atteso": "Compliance GDPR"},
        {"orizzonte": "lungo", "azione": "Modello 231", "priorita": "media",
         "responsabile": "Consulente", "impatto_atteso": "Presidio governance"},
    ],
    "checklist": [
        {"azione": "Raccogliere contratti attivi", "responsabile": "Amministrazione",
         "scadenza": "entro 7 giorni", "stato": "Da fare"},
        {"azione": "Nominare DPO", "responsabile": "Titolare", "scadenza": "entro 30 giorni", "stato": "In corso"},
    ],
    "template": [
        {"titolo": "Email alla banca", "tipo": "email",
         "corpo": "Spett.le [NOME BANCA],\ncon la presente [NOME AZIENDA] richiede [OGGETTO].\nData: [DATA]\nCordiali saluti"},
    ],
}


def test_generate_report_ops_offline_none(monkeypatch):
    """Senza chiave Anthropic → None (no-op, il render salta le sezioni)."""
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", None)
    out = llm.generate_report_ops({"voci": [{"titolo": "X", "contenuto": "y" * 200}]}, {"azienda": "ACME"})
    assert out is None


def test_ops_components_build():
    """I 5 componenti costruiscono flowable senza eccezioni."""
    S = styling.styles()
    assert styling.semaforo_board(_OPS["semaforo_rischi"], S) is not None
    assert styling.impact_matrix(_OPS["matrice_rischi"], S) is not None
    assert styling.timeline_ops(_OPS["timeline_operativa"], S)  # lista non vuota
    assert styling.checklist_table(_OPS["checklist"], S) is not None
    assert styling.template_box(_OPS["template"][0], S) is not None


def test_ops_blocks_render_generic(tmp_path):
    """Un deliverable generico con report_ops produce un PDF valido (blocchi ops inclusi)."""
    deliverable = {
        "meta": {"azienda": "ACME S.r.l."},
        "diagnosi": {"contenuto": "Analisi di prova per esercitare il render generico."},
        "report_ops": _OPS,
    }
    bp = {"pacchetto": {"nome_commerciale": "TestBoost"}}
    p = tmp_path / "ops_generic.pdf"
    render.render_generic_pdf(deliverable, bp, [], p)
    assert p.exists() and p.stat().st_size > 5000


def test_ops_blocks_render_legal(tmp_path):
    """LegalBoost con report_ops: i blocchi ops si aggiungono senza crash."""
    deliverable = {
        "meta": {"azienda": "ACME S.r.l."},
        "voci": [{"id": "sintesi_mappa_rischi", "titolo": "Sintesi", "contenuto": "Prova."}],
        "report_ops": _OPS,
    }
    bp = {"pacchetto": {"nome_commerciale": "LegalBoost"}}
    p = tmp_path / "ops_legal.pdf"
    render.render_pdf(deliverable, bp, [], p)
    assert p.exists() and p.stat().st_size > 5000


if __name__ == "__main__":
    test_generate_report_ops_offline_none(type("M", (), {"setattr": staticmethod(setattr)})())
    test_ops_components_build()
    import tempfile
    d = Path(tempfile.mkdtemp())
    test_ops_blocks_render_generic(d)
    test_ops_blocks_render_legal(d)
    print("test_report_ops: OK")
