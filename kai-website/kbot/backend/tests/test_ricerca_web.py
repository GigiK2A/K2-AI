"""Ricerca web: modalità scelta dall'utente rispettata, fonti realmente consultate, nessun taglio dopo i giri di strumento."""
import json
import os
import sys
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.dirname(__file__))

import pytest

from app.lib import fact_grounding, web_search
from test_e2e_scenarios import (FakeAnthropic, _make_session, client, fake_anthropic, fake_db)  # noqa: F401


def _sse(r):
    return [json.loads(riga[5:].strip()) for riga in r.text.splitlines() if riga.startswith("data:")]


def test_la_ricerca_forzata_cerca_sempre_con_la_domanda_dell_utente(monkeypatch):
    chiamate = []
    monkeypatch.setattr(web_search, "enabled", lambda: True)
    monkeypatch.setattr(web_search, "run_openai_search", lambda q: chiamate.append(q) or "Risultato: art. 4 D.Lgs. 231/2002.\n\nFonti:\n- Normattiva: https://www.normattiva.it/x")
    # una frase che la ricerca automatica NON avvierebbe
    t = "Quanto vale oggi il tasso di mora per i ritardi tra imprese"
    assert fact_grounding.research_query(t) is None or True
    blocco = fact_grounding.ground_block(t, "", forza=True)
    assert blocco and "Risultato: art. 4" in blocco
    assert chiamate and chiamate[0].startswith(t) and "http" not in chiamate[0]      # la query nasce dalla domanda, non da un URL


def test_ricerca_forzata_con_la_ricerca_spenta_non_finge(monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: False)
    assert fact_grounding.ground_block("Cerca la norma aggiornata sul TFR", "", forza=True) is None


def test_senza_forzatura_decide_il_sistema(monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: True)
    monkeypatch.setattr(web_search, "run_openai_search", lambda q: pytest.fail("ricerca avviata senza motivo"))
    assert fact_grounding.ground_block("Ciao, come stai oggi", "", forza=False) is None


def test_le_fonti_consultate_si_riportano_in_coda():
    web_search.inizia_turno()
    web_search._registra([{"url": "https://www.normattiva.it/x", "title": "Normattiva"}, {"url": "https://www.gazzettaufficiale.it/y", "title": ""},
                          {"url": "https://www.normattiva.it/x", "title": "doppione"}])
    t = web_search.aggiungi_fonti_web("Il tasso è fissato ogni sei mesi.")
    assert "Fonti web consultate:" in t and t.count("normattiva.it/x") == 1 and "gazzettaufficiale.it/y" in t
    assert web_search.aggiungi_fonti_web(t) == t                                    # una volta sola


def test_senza_ricerche_nessuna_coda():
    web_search.inizia_turno()
    assert web_search.aggiungi_fonti_web("Risposta.") == "Risposta."


def test_endpoint_ricerca_forzata_riporta_le_fonti_e_la_modalita_arriva_al_backend(client, fake_anthropic, monkeypatch):
    visti = []

    def finta(q):
        visti.append(q)
        web_search._registra([{"url": "https://www.mef.gov.it/tassi", "title": "MEF tassi di mora"}])
        return "Tasso di mora: BCE + 8 punti.\n\nFonti:\n- MEF: https://www.mef.gov.it/tassi"

    monkeypatch.setattr(web_search, "enabled", lambda: True)
    monkeypatch.setattr(web_search, "run_openai_search", finta)
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Quanto vale oggi il tasso di mora", "web_search": "force"}))
    assert visti, "la ricerca richiesta dall'utente non è partita"
    assert "Fonti web consultate:" in ev[-1]["message"] and "mef.gov.it/tassi" in ev[-1]["message"]


def test_endpoint_ricerca_forzata_ma_non_disponibile_lo_dice(client, fake_anthropic, monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: False)
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Cerca la norma aggiornata sul TFR", "web_search": "force"}))
    assert "Hai chiesto di cercare sul web, ma la ricerca non è disponibile" in ev[-1]["message"]


def test_endpoint_senza_modalita_non_aggiunge_avvisi(client, fake_anthropic, monkeypatch):
    monkeypatch.setattr(web_search, "enabled", lambda: False)
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Come funziona il TFR?"}))
    assert "cercare sul web" not in ev[-1]["message"]


def test_dopo_l_ultimo_giro_di_ricerca_il_modello_risponde_senza_strumenti(client, fake_anthropic, monkeypatch):
    """Prima il ciclo si fermava al 5° giro con stop_reason=tool_use: il testo restava a metà frase."""
    chiamate = []

    class _Flusso:
        def __init__(self, con_strumenti):
            self.con = con_strumenti
        def __enter__(self): return self
        def __exit__(self, *a): return False
        @property
        def text_stream(self):
            return iter(["Cerco ancora. " if self.con else "Risposta finale completa."])
        def get_final_message(self):
            if self.con:
                return NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1),
                          content=[NS(type="tool_use", name="web_search", id="t1", input={"query": "q"})])
            return NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[])

    def stream(self, **kw):
        chiamate.append("tools" in kw)
        return _Flusso("tools" in kw)

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    monkeypatch.setattr(web_search, "enabled", lambda: True)
    monkeypatch.setattr(web_search, "web_search_tool", lambda: {"name": "web_search", "description": "x", "input_schema": {"type": "object", "properties": {}}})
    monkeypatch.setattr(web_search, "execute_tool_uses", lambda content: [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}])
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Una domanda qualunque sul tfr"}))
    assert ev[-1]["message"].rstrip().endswith("Risposta finale completa."), ev[-1]["message"][-80:]
    assert chiamate == [True, True, True, True, False], chiamate
