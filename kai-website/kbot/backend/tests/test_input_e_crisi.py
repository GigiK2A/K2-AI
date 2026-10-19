"""Crisi personale, avvisi «non ho letto tutto», numeri dell'utente non toccati dalle guardie (19/10/2026)."""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from app.lib import crisi, avvisi_input, deadline_guard, norme_evidence, norme_guard
from app.settings import MAX_LAST_USER_CHARS

from test_e2e_scenarios import (FakeAnthropic, _chiamate_chat, _make_session, client, fake_anthropic,  # noqa: F401
                                fake_db)

CRISI = "Ho 200mila euro di debiti, l'azienda sta chiudendo e non ce la faccio più. A volte penso di farla finita."


@pytest.fixture(autouse=True)
def _pulito():
    from app.lib.limiter import limiter
    try:
        limiter.reset()                      # molti test creano sessioni: il limite 20/min non c'entra qui
    except Exception:
        pass
    norme_evidence.imposta_testo_utente(None)
    yield
    norme_evidence.imposta_testo_utente(None)


# ── crisi: riconoscimento ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("t", [CRISI, "vorrei togliermi la vita", "non voglio più vivere così", "ho pensieri suicidi",
                               "penso di suicidarmi", "voglio morire", "a volte penso al suicidio", "mi voglio uccidere"])
def test_riconosce_la_crisi(t):
    assert crisi.rileva(t), t


@pytest.mark.parametrize("t", ["voglio farla finita con questo fornitore", "ne ho abbastanza, farla finita con questa causa",
                               "sarebbe un suicidio commerciale", "È una mossa suicida per l'azienda",
                               "Come funziona il TFR?", "Devo chiudere la società: quanto costa?", "il cliente è morto, cosa succede al contratto?"])
def test_non_scambia_gli_idiomi_e_i_temi_di_lavoro_per_una_crisi(t):
    assert not crisi.rileva(t), t


def test_la_risposta_fissa_ha_solo_numeri_verificati():
    t = crisi.RISPOSTA_FISSA
    assert "112" in t and "02 2327 2327" in t and "telefonoamico.it" in t
    cifre = set(re.findall(r"\d[\d ]*\d|\d", t))
    assert cifre <= {"112", "02 2327 2327"}, cifre                 # nessun altro numero di telefono
    assert not re.search(r"(?<!\d)(?:800|803)[\s.\-]?\d{3}", t)


def test_interruttore_della_crisi(monkeypatch):
    monkeypatch.setenv("KBOT_CRISI", "0")
    assert not crisi.rileva(CRISI)


# ── crisi: nessuna chiamata al modello, risposta identica ────────────────────────────────
def test_message_crisi_risposta_fissa_senza_modello(client, fake_anthropic):
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message": CRISI})
    assert r.status_code == 200
    j = r.json()
    assert j["message"] == crisi.RISPOSTA_FISSA and j["summary"] is None and j["nextAction"] == "continue"
    assert _chiamate_chat() == []                                    # il modello non è stato interpellato
    msgs = client.get(f"/api/kbot/session/{sid}").json()["session"]["messages"]
    assert [m["role"] for m in msgs][-2:] == ["user", "assistant"] and msgs[-1]["content"] == crisi.RISPOSTA_FISSA


def _sse(r):
    ev = []
    for riga in r.text.splitlines():
        if riga.startswith("data:"):
            ev.append(json.loads(riga[5:].strip()))
    return ev


def test_stream_crisi_risposta_fissa_senza_modello(client, fake_anthropic):
    sid = _make_session(client)
    r = client.post("/api/kbot/message/stream", json={"session_id": sid, "message": CRISI})
    ev = _sse(r)
    assert "".join(e.get("delta", "") for e in ev) == crisi.RISPOSTA_FISSA
    assert ev[-1]["done"] and ev[-1]["message"] == crisi.RISPOSTA_FISSA
    assert _chiamate_chat() == []


def test_un_messaggio_normale_chiama_il_modello(client, fake_anthropic):
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message": "Come funziona il TFR in azienda?"})
    assert r.status_code == 200 and r.json()["message"] != crisi.RISPOSTA_FISSA and _chiamate_chat()


def test_il_numero_verde_inventato_dal_modello_viene_tolto(client, fake_anthropic):
    fake_anthropic.canned_text = "Mi dispiace. Chiama il Numero Verde Anticidio 800 808 109, è gratuito."
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message": "Sono molto preoccupato per la mia azienda."})
    m = r.json()["message"]
    assert "800 808 109" not in m and "[numero da verificare sul sito ufficiale]" in m


def test_il_numero_verde_scritto_dall_utente_resta():
    assert crisi.sanifica_numeri("Chiama il 800 123 456", "il mio numero è 800 123 456") == "Chiama il 800 123 456"
    assert "800 123 456" not in crisi.sanifica_numeri("Chiama il 800 123 456", "")


# ── testo tagliato / copertura ────────────────────────────────────────────────────────────
def test_testo_incollato_oltre_il_tetto_avverte_modello_e_utente(client, fake_anthropic):
    lungo = "Ecco il contratto: " + ("clausola " * 1200)
    assert len(lungo) > MAX_LAST_USER_CHARS
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message": lungo})
    assert "Nota: il testo che hai incollato" in r.json()["message"] and "ne ho letti solo i primi" in r.json()["message"]
    assert "TESTO TAGLIATO" in _chiamate_chat()[-1]["system"]


def test_testo_corto_nessun_avviso(client, fake_anthropic):
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message": "Come funziona il TFR?"})
    assert "Nota:" not in r.json()["message"] and "TESTO TAGLIATO" not in _chiamate_chat()[-1]["system"]


def test_stream_testo_tagliato_il_mostrato_e_uguale_al_finale(client, fake_anthropic):
    lungo = "Ecco il contratto: " + ("clausola " * 1200)
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": lungo}))
    finale = ev[-1]["message"]
    assert "Nota: il testo che hai incollato" in finale
    assert "".join(e.get("delta", "") for e in ev).strip() == finale.strip()


def test_avvisi_input_unita():
    assert avvisi_input.testo_tagliato(100, 8000) is None
    nota, avviso = avvisi_input.testo_tagliato(12345, 8000)
    assert "12.345" in avviso and "8.000" in avviso and "NON hai letto il resto" in nota
    assert avvisi_input.copertura_allegati([{"file": "a.pdf", "mostrati": 3, "totale": 3}]) is None
    n, a = avvisi_input.copertura_allegati([{"file": "contratto.pdf", "mostrati": 10, "totale": 19, "pagine": "1, 4-5"}])
    assert "10 parti su 19" in a and "NON hai letto i documenti per intero" in n and "pagine 1, 4-5" in n
    assert avvisi_input.aggiungi("Testo.", ["A", "", "B"]) == "Testo.\n\nA\nB" and avvisi_input.aggiungi("T", []) == "T"


def _chunk(i, testo, file="contratto.pdf"):
    return {"file_name": file, "page_number": i // 2 + 1, "chunk_index": i, "content": testo}


def test_il_prompt_dichiara_la_copertura_parziale_e_alza_k_per_le_domande_ampie(monkeypatch):
    from app.lib import prompts, rag
    chunks = [_chunk(i, f"clausola numero {i} " + "x" * 100) for i in range(25)]
    monkeypatch.setattr(rag, "fetch_chunks", lambda sid, limit=500: chunks)
    uploaded = [{"name": "contratto.pdf", "extractedText": "x" * 6000}]

    def costruisci(domanda):
        sess = {"id": "s1", "collected_data": {"uploaded_files": uploaded}, "messages": [{"role": "user", "content": domanda}]}
        p = prompts.build_system_prompt_v2([], sess)
        return p, sess

    p, sess = costruisci("Quali sono le clausole più pericolose per me?")
    assert "COPERTURA DEGLI ALLEGATI" in p and "20 parti su 25" in p and "20 parti su 25" in sess["_avviso_copertura"]
    p2, sess2 = costruisci("Qual è il numero di partita IVA scritto sul frontespizio?")
    assert "10 parti su 25" in p2 and "10 parti su 25" in sess2["_avviso_copertura"]
    # documento letto per intero: nessun avviso
    monkeypatch.setattr(rag, "fetch_chunks", lambda sid, limit=500: chunks[:6])
    p3, sess3 = costruisci("Quali sono le clausole più pericolose?")
    assert "COPERTURA DEGLI ALLEGATI" not in p3 and "_avviso_copertura" not in sess3


# ── guardie: i numeri dell'utente non si toccano ──────────────────────────────────────────
def test_la_penale_scritta_dall_utente_non_viene_cancellata():
    testo = "La penale è pari al 30% del valore del contratto, senza limite massimo."
    assert "30%" not in deadline_guard.sanitize(testo)               # senza fonte: la guardia la rende descrittiva
    norme_evidence.imposta_testo_utente("Art. 19-bis. Il Fornitore corrisponderà una penale pari al 30% del valore.")
    assert "30%" in deadline_guard.sanitize(testo)


def test_il_termine_della_lettera_dell_utente_resta_ma_quello_inventato_no():
    norme_evidence.imposta_testo_utente("Ella potrà presentare le proprie giustificazioni entro 3 giorni dal ricevimento della presente.")
    ok = deadline_guard.sanitize("Hai tempo per rispondere entro 3 giorni dal ricevimento, come scrive la lettera, per la normativa sul lavoro.")
    assert "entro 3 giorni" in ok
    inventato = deadline_guard.sanitize("Per la normativa sul lavoro devi rispondere entro 8 giorni dal ricevimento.")
    assert "entro 8 giorni" not in inventato                        # un termine che l'utente NON ha scritto resta soggetto alla guardia


def test_una_citazione_scritta_dall_utente_e_consentita():
    assert not norme_evidence.citazione_consentita("art. 1341 c.c.")
    norme_evidence.imposta_testo_utente("Le clausole non sono state approvate specificamente ai sensi dell'art. 1341 c.c.")
    assert norme_evidence.citazione_consentita("art. 1341 c.c.")
    assert not norme_evidence.citazione_consentita("art. 2125 c.c.")
    assert "art. 1341 c.c." in norme_guard.sanitize("Va approvata per iscritto ai sensi dell'art. 1341 c.c. come dice il tuo contratto.")


def test_end_to_end_il_numero_del_documento_arriva_all_utente(client, fake_anthropic):
    fake_anthropic.canned_text = "Attenzione: nel contratto la penale è pari al 30% del valore, per la normativa sui contratti è molto alta."
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message":
                    "Il contratto dice: «il Fornitore corrisponderà una penale pari al 30% del valore». È rischioso per me?"})
    assert "30%" in r.json()["message"]


def test_domanda_ampia_completa_con_le_parti_senza_parole_in_comune(monkeypatch):
    from app.lib import prompts, rag
    # 19 chunk: solo i primi 5 contengono le parole della domanda, gli altri (con la clausola nascosta) no
    chunks = [_chunk(i, ("clausole pericolose " if i < 5 else "") + f"testo {i} " + ("x" * 80)) for i in range(19)]
    chunks[14]["content"] = "Art. 57.3 modifica unilaterale dei corrispettivi con preavviso di 5 giorni " + "y" * 60
    monkeypatch.setattr(rag, "fetch_chunks", lambda sid, limit=500: chunks)
    uploaded = [{"name": "contratto.pdf", "extractedText": "x" * 6000}]
    sess = {"id": "s1", "collected_data": {"uploaded_files": uploaded},
            "messages": [{"role": "user", "content": "Quali sono le clausole più pericolose per me?"}]}
    p = prompts.build_system_prompt_v2([], sess)
    assert "modifica unilaterale dei corrispettivi" in p                 # la parte «senza parole in comune» c'è
    assert "COPERTURA DEGLI ALLEGATI" not in p and "_avviso_copertura" not in sess   # 19 su 19: nessun avviso
    # domanda stretta: restano le 10 più pertinenti e l'avviso dice la verità
    sess2 = {"id": "s1", "collected_data": {"uploaded_files": uploaded},
             "messages": [{"role": "user", "content": "Che numero porta il testo 3?"}]}
    p2 = prompts.build_system_prompt_v2([], sess2)
    assert "parti su 19" in sess2["_avviso_copertura"]
