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


# Acceptance §2 (handoff Luca): la deliverable StrategyBoost difettosa di "Studio
# Associato Evolution" deve far scattare TUTTE e 5 le classi del contratto.
_STUDIO_EVOLUTION_DIFETTOSO = {
    "meta": {"cliente": "Studio Associato Evolution"},
    "posizionamento": {"mappa": {
        "descrizione_assi": {"asse_x": "Ampiezza offerta", "asse_y": "Segmentazione cliente"},
        "posizione_azienda": {"nome": "Studio Evolution", "coordinata_x": 0.75, "coordinata_y": 0.35,
                              "razionale": "Ampia diversificazione tecnica, segmentazione bassa."},
        "posizione_competitor": [
            {"nome": "Specialista FER", "coordinata_x": 0.25, "coordinata_y": 0.6,
             "razionale": "Focus verticale rinnovabili."},
        ],
    }},
    "analisi_mercato": {"nota": "Il target UE 2030 porta la quota FER al 72% del mix elettrico, "
                                "trainando la domanda di progettazione rinnovabili."},
    "vincoli_normativi": {"tariffe": "Le tariffe minime di settore ex DM 143/2013 restano un "
                                     "riferimento per il posizionamento di prezzo dello studio."},
    "canali_cliente": {"diagnosi": "Il profilo LinkedIn aziendale è assente e la presenza social "
                                   "è dormiente: l'acquisizione è interamente da passaparola."},
    "piano_strategico": {"iniziative": [
        {"titolo": "Ridisegno sito dual-track", "priorita": "Media"},
        {"titolo": "Presidio LinkedIn B2B", "priorita": "Media"},
        {"titolo": "Content SEO tecnico", "priorita": "Media"},
        {"titolo": "Partnership con EPC", "priorita": "Media"},
    ]},
}
_INPUTS_EVOLUTION = {"settore": "studio di ingegneria", "fatturato": "1.4M", "dipendenti": "9",
                     "servizi": "progettazione impianti, civile", "target": "PMI e PA locali"}


def test_cage_acceptance_studio_evolution():
    """I 5 difetti del contratto: C3 coordinate, C2 norma sbagliata, C2 stat non citata,
    C3 priorità piatte, C1 fatto-cliente non verificato. Citazioni vuote (il report reale
    non citava nulla)."""
    f = g.integrity_findings(_STUDIO_EVOLUTION_DIFETTOSO, citazioni=[], inputs=_INPUTS_EVOLUTION)
    codes = {x["code"] for x in f}
    assert "coordinate_falsa_precisione" in codes        # C3 — 0,75 / 0,35 inventati
    assert "norma_non_citata" in codes                   # C2 — DM 143/2013 da recall (minimi aboliti)
    assert "numero_esterno_non_grounded" in codes        # C2 — FER 72% non citato
    assert "priorita_indifferenziate" in codes           # C3 — tutte 'Media'
    assert "fatto_cliente_non_verificato" in codes       # C1 — LinkedIn assente non nell'input
    # ogni finding porta la classe del contratto
    by_code = {x["code"]: x for x in f}
    assert by_code["coordinate_falsa_precisione"]["classe"] == "C3"
    assert by_code["norma_non_citata"]["classe"] == "C2"
    assert by_code["fatto_cliente_non_verificato"]["classe"] == "C1"


def test_cage_non_flagga_fatto_cliente_se_e_nell_input():
    """C1 è un GATE, non un bavaglio: se 'LinkedIn assente' viene dall'input del cliente
    (o è marcato [IPOTESI]) NON va flaggato."""
    deliv = {"meta": {"cliente": "Studio X"},
             "canali": {"nota": "Il profilo LinkedIn è assente, come dichiarato."}}
    # caso A: il cliente stesso ha detto che non ha LinkedIn → niente flag
    f = g.integrity_findings(deliv, citazioni=[], inputs={"canali_attuali": "nessun LinkedIn, solo passaparola"})
    assert not any(x["code"] == "fatto_cliente_non_verificato" for x in f)
    # caso B: marcato [IPOTESI] → niente flag
    deliv_ip = {"meta": {"cliente": "Studio X"},
                "canali": {"nota": "[IPOTESI DA CONFERMARE] Il profilo LinkedIn risulta assente."}}
    f2 = g.integrity_findings(deliv_ip, citazioni=[], inputs={})
    assert not any(x["code"] == "fatto_cliente_non_verificato" for x in f2)


def test_cage_norma_citata_non_flaggata():
    """C2 norma: se la norma È tra le citazioni grounded, non è recall → niente flag."""
    deliv = {"meta": {"cliente": "Y"}, "sez": {"t": "Si applica il D.Lgs 81/2008 in materia di sicurezza."}}
    f = g.integrity_findings(deliv, citazioni=[{"fonte": "D.Lgs 81/2008", "valore": "art. 18"}], inputs={})
    assert not any(x["code"] == "norma_non_citata" for x in f)


def test_depth_vs_data_segnala_generico():
    # deliverable lungo (>4000 char) su input scarni (il caso reale: "non ho dati")
    lungo = {"meta": {"cliente": "Studio Reale"}, "analisi": {"testo": "x " * 3000}}
    f = g.integrity_findings(lungo, citazioni=[], inputs={"settore": "ingegneria"})
    assert any(x["code"] == "input_povero" for x in f)
    # con dati ricchi, niente warn
    f2 = g.integrity_findings(lungo, citazioni=[], inputs={
        "settore": "ingegneria", "fatturato": "2.1M", "dipendenti": "18",
        "canali": "passaparola, sito", "target": "privati edilizia", "budget": "10k"})
    assert not any(x["code"] == "input_povero" for x in f2)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
