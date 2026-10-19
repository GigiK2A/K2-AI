"""Mappa temi → norme: le bozze non validate restano spente in produzione; i trigger scattano dove devono."""
import json
import os

import pytest

from app.lib import norme_evidence as N

# Articoli che al 19/10/2026 NON sono nel corpus (dello Statuto c'è solo l'art. 1, la L. 604/1966 non c'è):
# la mappa li nomina comunque, e si attivano da soli quando il testo viene aggiunto. Se il corpus viene
# completato questo test fallisce e ricorda di togliere l'avviso dalle note.
ASSENTI_NEL_CORPUS = {"L. 300/1970 art. 7", "L. 300/1970 art. 4", "L. 604/1966 art. 3"}


@pytest.fixture(autouse=True)
def _senza_cache():
    """`_mappa()` è in cache per processo (il file si legge una volta): ogni test riparte pulito."""
    N._mappa.cache_clear()
    yield
    N._mappa.cache_clear()


def _voci():
    return json.load(open(N._MAPPA_PATH, encoding="utf-8"))["temi"]


def test_le_bozze_sono_spente_senza_interruttore(monkeypatch):
    monkeypatch.delenv("KBOT_MAPPA_BOZZE", raising=False)
    assert N._mappa() == []
    assert N.riferimenti_da_mappa("devo dare una sanzione disciplinare al dipendente") == []


def test_con_l_interruttore_le_bozze_si_caricano(monkeypatch):
    monkeypatch.setenv("KBOT_MAPPA_BOZZE", "1")
    assert len(N._mappa()) == len(_voci())


def test_una_voce_validata_si_carica_anche_senza_interruttore(monkeypatch, tmp_path):
    monkeypatch.delenv("KBOT_MAPPA_BOZZE", raising=False)
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"temi": [
        {"id": "a", "trigger": ["caparra"], "riferimenti": ["art. 1385 c.c."], "validato_da": "Avv. Rossi"},
        {"id": "b", "trigger": ["penale"], "riferimenti": ["art. 1382 c.c."], "validato_da": ""}]}), encoding="utf-8")
    monkeypatch.setattr(N, "_MAPPA_PATH", str(p))
    assert [v["id"] for v in N._mappa()] == ["a"]


def test_ogni_voce_ha_i_campi_e_i_riferimenti_si_leggono():
    for v in _voci():
        assert v["id"] and v["trigger"] and v["riferimenti"] and v["stato"] == "bozza" and v["validato_da"] == ""
        assert len(v["riferimenti"]) <= 3, v["id"]
        for r in v["riferimenti"]:
            assert N.riferimenti_da_testo(r), f"{v['id']}: riferimento non leggibile: {r}"


@pytest.mark.parametrize("testo,tema", [
    ("Mi è arrivata una lettera di contestazione disciplinare", "procedimento-disciplinare"),
    ("Posso applicare una sanzione disciplinare al dipendente?", "procedimento-disciplinare"),
    ("Posso installare telecamere in reparto?", "controllo-a-distanza"),
    ("Voglio licenziare un dipendente per giusta causa", "licenziamento"),
    ("Quanto dura il periodo di prova?", "periodo-di-prova"),
    ("Mi hanno cambiato le mansioni, è demansionamento?", "mansioni"),
    ("C'è un patto di non concorrenza nel contratto", "patto-di-non-concorrenza"),
    ("Una clausola vessatoria va approvata specificamente", "clausole-vessatorie"),
    ("La clausola penale prevede il 15% per ritardo", "clausola-penale"),
    ("Ho versato una caparra confirmatoria", "caparra"),
    ("Voglio la risoluzione per inadempimento", "risoluzione-per-inadempimento"),
    ("Ci sono vizi della cosa venduta", "vizi-e-garanzia"),
])
def test_i_trigger_scattano(testo, tema, monkeypatch):
    monkeypatch.setenv("KBOT_MAPPA_BOZZE", "1")
    hit = [v["id"] for v in N._mappa() if any(t.search(testo) for t in v["trigger"])]
    assert tema in hit, (testo, hit)


@pytest.mark.parametrize("testo", [
    "Rischio una condanna in sede penale per questo fatto?", "Ho una causa di diritto penale in corso",
    "Come funziona la fase di prova di un software?", "Vorrei un consiglio sul marketing", "Quanto costa un ricorso al TAR?",
    "Devo pagare l'IVA trimestrale?", "Come calcolo la ritenuta d'acconto?",
])
def test_nessun_falso_positivo_su_temi_diversi(testo, monkeypatch):
    monkeypatch.setenv("KBOT_MAPPA_BOZZE", "1")
    assert [v["id"] for v in N._mappa() if any(t.search(testo) for t in v["trigger"])] == [], testo


def test_gli_articoli_nominati_esistono_nel_corpus_tranne_quelli_noti():
    if not N.disponibile():
        pytest.skip("corpus non disponibile")
    assenti = set()
    for v in _voci():
        for r in v["riferimenti"]:
            if not N.recupera(N.riferimenti_da_testo(r)[0], [], "mappa", 300):
                assenti.add(r)
    assert assenti == ASSENTI_NEL_CORPUS, (
        f"corpus cambiato: assenti ora {sorted(assenti)}; aggiorna ASSENTI_NEL_CORPUS e le note della mappa")


def test_il_pacchetto_porta_gli_articoli_della_mappa(monkeypatch):
    monkeypatch.setenv("KBOT_MAPPA_BOZZE", "1")
    refs = N.riferimenti_da_mappa("Voglio licenziare un dipendente senza preavviso")
    assert {r["articolo"] for r in refs if r["tipo"] != "legge"} >= {"2118", "2119"}
