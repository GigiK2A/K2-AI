"""La chat deve mandare il primo byte subito, o il gateway chiude prima della risposta.

Misurato in produzione il 19 ago 2026: 125 secondi e ZERO eventi, poi 502 Bad Gateway.
Il generatore non emetteva niente finché il triage — una chiamata LLM intera sul modello
locale — non aveva finito. Railway chiude una connessione muta molto prima.
"""
import time

from fastapi.testclient import TestClient

import aios.api.app as app_mod
from aios.api.app import create_app
from aios.autonomy import ActionType
from aios.kernel import Kernel
from aios.tools import Tool


class ChatLenta:
    """Come la chat vera: il primo evento arriva solo dopo un'attesa."""

    def __init__(self, attesa=0.6):
        self.attesa = attesa

    def stream(self, text, agents, history, media=None):
        time.sleep(self.attesa)
        yield {"phase": "triage", "modo": "rispondi", "agenti": []}
        yield {"phase": "done", "agent": "ceo", "text": "risposta"}
        yield {"phase": "all_done", "agents": ["ceo"]}


class PiattaformaFinta:
    def __init__(self, chat):
        self.chat = chat
        self.conversations = None
        self.commands = None


def _client(monkeypatch, chat, keepalive=0.2):
    monkeypatch.setattr(app_mod, "KEEPALIVE_SSE", keepalive)
    k = Kernel()
    k.register_tool(Tool(name="x", action_type=ActionType("a", "b"), run=lambda **kw: {}))
    return TestClient(create_app(k, platform=PiattaformaFinta(chat)))


def _righe(resp) -> list[str]:
    return [r for r in resp.text.split("\n\n") if r.strip()]


def test_il_primo_byte_arriva_prima_del_triage(monkeypatch):
    c = _client(monkeypatch, ChatLenta(attesa=0.5))
    with c.stream("POST", "/api/chat/stream", json={"text": "ciao"}) as r:
        assert r.status_code == 200
        primo = next(r.iter_lines())
        # non è un evento: è il commento che tiene aperta la connessione
        assert primo.startswith(":")


def test_ping_mentre_il_modello_pensa(monkeypatch):
    """Con attesa 0.6s e keepalive 0.2s devono partire dei ping prima del triage."""
    c = _client(monkeypatch, ChatLenta(attesa=0.6), keepalive=0.2)
    r = c.post("/api/chat/stream", json={"text": "ciao"})
    righe = _righe(r)
    assert sum(1 for x in righe if x.startswith(":")) >= 2
    assert any('"phase": "triage"' in x for x in righe)


def test_gli_eventi_veri_arrivano_tutti_e_in_ordine(monkeypatch):
    c = _client(monkeypatch, ChatLenta(attesa=0))
    r = c.post("/api/chat/stream", json={"text": "ciao"})
    fasi = [x for x in _righe(r) if x.startswith("data:")]
    assert '"phase": "triage"' in fasi[0]
    assert '"phase": "done"' in fasi[1]
    assert '"phase": "all_done"' in fasi[2]


def test_un_errore_nel_thread_arriva_al_client(monkeypatch):
    class ChatRotta:
        def stream(self, *a, **kw):
            raise RuntimeError("modello giù")
            yield  # pragma: no cover

    c = _client(monkeypatch, ChatRotta())
    r = c.post("/api/chat/stream", json={"text": "ciao"})
    assert '"phase": "error"' in r.text and "modello giù" in r.text


def test_i_commenti_non_confondono_il_parser_del_cockpit(monkeypatch):
    """Il cockpit salta le righe che non iniziano con 'data:': i ping devono essere
    commenti, non eventi con una fase inventata."""
    c = _client(monkeypatch, ChatLenta(attesa=0.5), keepalive=0.1)
    r = c.post("/api/chat/stream", json={"text": "ciao"})
    for riga in _righe(r):
        assert riga.startswith("data:") or riga.startswith(":"), riga
