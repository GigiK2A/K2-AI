"""Risposte lunghe su più turni (test 09-11, 22/10/2026): al 3º turno il modello riceveva le proprie risposte precedenti tagliate a
900 car. + «…» e le imitava. Qui si guarda cosa riceve davvero il modello, passando dall'endpoint come in produzione."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from test_e2e_scenarios import (FakeAnthropic, _make_session, client, fake_anthropic, fake_db)  # noqa: F401

LUNGA = ("Per prima cosa conta che l'ordine sia stato eseguito, perché da quel momento la revoca non è più possibile. " * 30).strip()
FINE = " Questa è la conclusione completa della risposta."


def _sse(resp):
    return [json.loads(r[5:]) for r in resp.text.splitlines() if r.startswith("data:")]


def _turno(client, sid, testo):
    return _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": testo}))[-1]


def test_il_modello_riceve_intere_le_sue_ultime_risposte(client, fake_anthropic):
    fake_anthropic.canned_text = LUNGA + FINE
    sid = _make_session(client)
    for i in range(1, 5):
        _turno(client, sid, f"Domanda numero {i}: cosa dobbiamo fare adesso con il bonifico?")
    ultima = fake_anthropic.captured_calls[-1]["messages"]
    risposte = [m["content"] for m in ultima if m["role"] == "assistant"]
    assert len(risposte) >= 3
    for r in risposte[-2:]:
        assert r.rstrip().endswith("completa della risposta."), r[-80:]       # intere: niente tagli a metà frase
    for r in risposte:
        assert not r.rstrip().endswith(("…", "...")), r[-80:]


def test_la_risposta_al_quarto_turno_non_finisce_con_ellissi(client, fake_anthropic):
    fake_anthropic.canned_text = LUNGA + FINE
    sid = _make_session(client)
    for i in range(1, 5):
        fin = _turno(client, sid, f"Domanda {i}: cosa facciamo?")
    assert fin["message"].rstrip().endswith("risposta.") and "…" not in fin["message"][-5:]
