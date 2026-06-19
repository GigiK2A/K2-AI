"""Mappa di posizionamento StrategyBoost resa come QUADRANTE 2x2 a bande (grafico),
non coordinate testuali. Verifica che: il grafico si rende, i decimali inventati
(0.75) NON finiscono nel PDF (C3 grounding contract: a bande, mai falsa precisione),
il razionale e i competitor restano."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import styling as ST  # noqa: E402
from app.render import render_generic_pdf  # noqa: E402

_MAPPA = {
    "descrizione_assi": {"asse_x": "Ampiezza offerta", "asse_y": "Segmentazione cliente"},
    "posizione_azienda": {"nome": "Studio Evolution", "coordinata_x": 0.75, "coordinata_y": 0.35,
                          "razionale": "Ampia diversificazione tecnica ma segmentazione bassa."},
    "posizione_competitor": [
        {"nome": "Specialista FER", "coordinata_x": 0.25, "coordinata_y": 0.55, "razionale": "Focus verticale."},
    ],
}


def test_quadrant_map_costruisce_e_banda():
    ST.styles()
    q = ST.quadrant_map(_MAPPA)
    assert q is not None
    # 0.75 → banda alto (2); 0.35 → banda basso (0)
    assert q.azienda[1] == 2 and q.azienda[2] == 0
    assert len(q.competitor) == 1


def test_render_mappa_quadrante_senza_falsa_precisione():
    bp = json.load(open(Path(__file__).resolve().parent.parent / "blueprints" / "flusso-strategyboost-pmi" / "blueprint.json"))
    deliv = {"meta": {"cliente": "Studio Associato Evolution"}, "posizionamento": {"mappa": _MAPPA}}
    p = Path(tempfile.mktemp(suffix=".pdf"))
    render_generic_pdf(deliv, bp, [], p)
    assert p.stat().st_size > 5000
    try:
        from pypdf import PdfReader
    except ImportError:
        return  # estrazione testo non disponibile: basta che renda
    txt = " ".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    assert "0.75" not in txt and "0.35" not in txt          # niente falsa precisione
    assert "diversificazione tecnica" in txt                 # razionale tenuto
    assert "Specialista FER" in txt                          # competitor nel grafico


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
