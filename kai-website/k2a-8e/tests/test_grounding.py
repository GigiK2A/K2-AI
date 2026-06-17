"""Gate di grounding/integrità — testato sui difetti REALI del report StrategyBoost
(cliente 'Cliente', segnaposto [città]/DM FER-X, 'FER al 72%' non grounded, priorità
tutte 'Media') + un deliverable pulito che NON deve produrre findings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import grounding as g  # noqa: E402

_BAD = {
    "meta": {"cliente": "Cliente"},
    "posizionamento": {"mappa": "Posizione azienda X=0.75 Y=0.35. target UE 2030 FER al 72% nel mix elettrico."},
    "piano_strategico": {"iniziative": [
        {"titolo": "Ridisegno sito", "priorita": "Media"},
        {"titolo": "SEO", "priorita": "Media"},
        {"titolo": "LinkedIn", "priorita": "Media"},
        {"titolo": "CRM", "priorita": "Media"},
    ]},
    "discovery": {"note": "ottimizzare 'studio ingegneria [città]', aggiornamenti DM FER-X"},
}

_GOOD = {
    "meta": {"cliente": "Studio Associato Evolution"},
    "posizionamento": {"mappa": "Ampiezza alta, segmentazione bassa. Target UE 42,5% (RED III)."},
    "piano_strategico": {"iniziative": [
        {"titolo": "CRM", "priorita": "Alta"},
        {"titolo": "SEO", "priorita": "Media"},
        {"titolo": "LinkedIn", "priorita": "Bassa"},
    ]},
}


def test_gate_becca_i_difetti_reali():
    f = g.integrity_findings(_BAD, citazioni=[], inputs={})
    codes = {x["code"] for x in f}
    assert "placeholder_leak" in codes
    assert "cover_non_personalizzata" in codes
    assert "numero_esterno_non_grounded" in codes      # il 'FER al 72%' inventato
    assert "priorita_indifferenziate" in codes
    assert g.blocks(f), "i segnaposto devono essere severità block"


def test_gate_lascia_pulito_il_buono():
    f = g.integrity_findings(_GOOD, citazioni=[{"valore": "Direttiva RED III: 42,5%"}], inputs={})
    assert not g.blocks(f)
    codes = {x["code"] for x in f}
    assert "numero_esterno_non_grounded" not in codes   # 42,5% è grounded nelle citazioni
    assert "cover_non_personalizzata" not in codes
    assert "priorita_indifferenziate" not in codes


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
