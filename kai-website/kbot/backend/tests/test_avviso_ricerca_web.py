"""10/11/2026: «Hai chiesto di cercare sul web, ma la ricerca non è disponibile in questo momento» compariva in OGNI risposta. Causa verificata: il
pulsante «Cerca sul web» resta acceso in localStorage (`kbot.web_search`) e il frontend invia `web_search:"force"` con ogni messaggio; con la ricerca
spenta nel backend (OPENAI_API_KEY rimossa da Railway) il backend aggiungeva l'avviso a ogni turno. Ora: l'avviso una sola volta per conversazione
(o quando il messaggio chiede davvero di cercare online) e un endpoint dice al frontend se la ricerca c'è."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import web_search  # noqa: E402
from test_e2e_scenarios import (FakeAnthropic, _make_session, client, fake_anthropic, fake_db)  # noqa: E402,F401

AVVISO = "Hai chiesto di cercare sul web, ma la ricerca non è disponibile"


def _msg(client, sid, testo, forza=True):
    body = {"session_id": sid, "message": testo}
    if forza:
        body["web_search"] = "force"
    r = client.post("/api/kbot/message/stream", json=body)
    return [json.loads(x[5:].strip()) for x in r.text.splitlines() if x.startswith("data:")][-1]["message"]


def test_con_il_pulsante_acceso_ma_ricerca_spenta_l_avviso_compare_una_volta(client, fake_anthropic, monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: False)
    sid = _make_session(client)
    assert AVVISO in _msg(client, sid, "Come funziona il periodo di prova di un dipendente assunto ieri?")
    assert AVVISO not in _msg(client, sid, "E se il dipendente si ammala durante il periodo di prova che succede?")
    assert AVVISO not in _msg(client, sid, "Quanto dura al massimo il periodo di prova per un impiegato di livello quarto?")


def test_se_il_messaggio_chiede_davvero_di_cercare_online_l_avviso_torna(client, fake_anthropic, monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: False)
    sid = _make_session(client)
    _msg(client, sid, "Come funziona il periodo di prova di un dipendente assunto ieri?")
    assert AVVISO in _msg(client, sid, "Cerca sul web l'ultima circolare dell'INPS sul periodo di prova")


def test_senza_il_pulsante_nessun_avviso(client, fake_anthropic, monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: False)
    sid = _make_session(client)
    assert AVVISO not in _msg(client, sid, "Come funziona il periodo di prova di un dipendente assunto ieri?", forza=False)


def test_endpoint_capacita_dice_se_la_ricerca_web_c_e(client, monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: False)
    assert client.get("/api/kbot/capabilities").json()["webSearch"] is False
    monkeypatch.setattr(web_search, "enabled", lambda: True)
    assert client.get("/api/kbot/capabilities").json()["webSearch"] is True
