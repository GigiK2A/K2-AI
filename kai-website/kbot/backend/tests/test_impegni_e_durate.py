"""Rimborsi promessi dal bot e durate calcolate dalle date dell'utente (19/10/2026)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from app.lib import deadline_guard, impegni_guard, norme_evidence

from test_e2e_scenarios import _make_session, client, fake_anthropic, fake_db  # noqa: F401


@pytest.fixture(autouse=True)
def _pulito():
    from app.lib.limiter import limiter
    try:
        limiter.reset()
    except Exception:
        pass
    norme_evidence.imposta_testo_utente(None)
    yield
    norme_evidence.imposta_testo_utente(None)


# ── impegni ──────────────────────────────────────────────────────────────────────────────
def test_la_promessa_del_caso_reale_viene_sostituita():
    t = ("Capisco la frustrazione. Una volta che vedo i fatti, ti dico cosa possiamo fare concretamente, incluso il rimborso "
         "se è il caso. Raccontami cosa è successo.")
    out = impegni_guard.sanitize(t)
    assert "rimborso se è il caso" not in out and impegni_guard.SOSTITUTA in out
    assert out.startswith("Capisco la frustrazione.") and out.endswith("Raccontami cosa è successo.")


@pytest.mark.parametrize("t", ["Ti rimborsiamo subito l'importo.", "Posso valutare un rimborso se mi dai i dettagli.",
                               "Avrai indietro i tuoi soldi, ti garantisco il rimborso.", "Ci faremo carico del danno."])
def test_altre_forme_promissorie(t):
    assert impegni_guard.SOSTITUTA in impegni_guard.sanitize(t)


@pytest.mark.parametrize("t", [
    "Hai diritto al rimborso dei costi di recupero, compreso il rimborso forfettario di 40 euro.",
    "Puoi chiedere il rimborso della caparra se l'altra parte è inadempiente.",
    "Il fornitore deve risarcire il danno secondo l'art. 1218 c.c.", "Come funziona il rimborso IVA?", "Nessuna promessa qui."])
def test_il_rimborso_come_argomento_giuridico_non_si_tocca(t):
    assert impegni_guard.sanitize(t) == t


def test_una_sola_sostituzione_e_interruttore(monkeypatch):
    t = "Ti rimborsiamo. Poi ti risarciamo anche. Fine."
    assert impegni_guard.sanitize(t).count(impegni_guard.SOSTITUTA) == 1
    monkeypatch.setenv("KBOT_IMPEGNI_GUARD", "0")
    assert impegni_guard.sanitize(t) == t


def test_end_to_end_la_promessa_non_arriva_all_utente(client, fake_anthropic):
    fake_anthropic.canned_text = "Capisco. Vediamo i fatti, e poi cosa possiamo fare, incluso il rimborso se è il caso."
    sid = _make_session(client)
    m = client.post("/api/kbot/message", json={"session_id": sid, "message": "Il vostro bot mi ha fatto perdere 5000 euro, rivoglio i soldi!"}).json()["message"]
    assert "rimborso se è il caso" not in m and "non posso prendere impegni" in m


# ── durate dalle date ────────────────────────────────────────────────────────────────────
def test_le_durate_si_ricavano_dalle_date_scritte_dall_utente():
    norme_evidence.imposta_testo_utente("Fattura del 14/04/2026 con scadenza il 14/06/2026.")
    for span in ("entro 61 giorni dalla fattura", "entro 60 giorni dalla fattura", "in 2 mesi dalla data"):
        assert norme_evidence.numero_fondato(span), span
    assert not norme_evidence.numero_fondato("entro 8 giorni dalla fattura")
    assert not norme_evidence.numero_fondato("entro 30 giorni dalla fattura")


def test_date_in_lettere_e_formati_diversi():
    norme_evidence.imposta_testo_utente("Dal 3 marzo 2026 al 20 marzo 2026, e il 5-4-2026.")
    assert norme_evidence.numero_fondato("entro 17 giorni dalla contestazione")          # 3→20 marzo
    assert norme_evidence.numero_fondato("entro 33 giorni dalla contestazione")          # 3 marzo → 5 aprile


def test_date_impossibili_o_una_sola_data_non_generano_durate():
    norme_evidence.imposta_testo_utente("Scade il 31/02/2026 e il 14/06/2026.")           # 31 febbraio non esiste
    assert not norme_evidence.numero_fondato("entro 60 giorni dalla data")
    norme_evidence.imposta_testo_utente("La fattura scade il 14/06/2026.")
    assert not norme_evidence.numero_fondato("entro 61 giorni dalla fattura")


def test_la_guardia_lascia_la_durata_calcolata_e_toglie_quella_inventata():
    norme_evidence.imposta_testo_utente("Fattura del 14/04/2026, scadenza 14/06/2026.")
    ok = deadline_guard.sanitize("La scadenza indicata è a 60 giorni dalla data della fattura, per la normativa sui pagamenti.")
    assert "60 giorni" in ok
    no = deadline_guard.sanitize("Per la normativa sui pagamenti hai 8 giorni dalla fattura per contestare.")
    assert "8 giorni" not in no
