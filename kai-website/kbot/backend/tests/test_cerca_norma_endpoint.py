import re
"""Lo strumento `cerca_norma` dalla chat, come in produzione: il modello lo chiama, riceve l'articolo e può citarlo; senza chiamata non può dire
di aver «interrogato il database» (10/11/2026: «ricevo solo un blocco di fonti predefinito»)."""
import json
import os
import sys
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import norme_evidence as N  # noqa: E402
from test_e2e_scenarios import (FakeAnthropic, _make_session, client, fake_anthropic, fake_db)  # noqa: E402,F401

pytestmark = pytest.mark.skipif(not N.disponibile(), reason="corpus Normattiva non disponibile")


def _sse(r):
    return [json.loads(x[5:].strip()) for x in r.text.splitlines() if x.startswith("data:")]


def _flusso(testo, final):
    class _F:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        @property
        def text_stream(self): return iter([testo])
        def get_final_message(self): return final
    return _F()


def test_il_modello_chiama_cerca_norma_e_riceve_comma_versione_e_note(client, fake_anthropic, monkeypatch):
    viste = []

    def stream(self, **kw):
        viste.append(kw)
        if len([k for k in viste if not str(k.get("system", "")).startswith("Estrai")]) == 1 and "tools" in kw:
            return _flusso("Controllo l'articolo. ", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[
                NS(type="tool_use", name="cerca_norma", id="t1", input={"norma": "D.Lgs. 81/2008", "articolo": "113", "comma": "2"})]))
        return _flusso("Per le scale verticali permanenti oltre 5 metri con inclinazione superiore a 75 gradi serve la gabbia o la protezione "
                       "individuale (art. 113 D.Lgs. 81/2008, comma 2).", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Cosa prevede la norma per una scala verticale permanente di 7 metri?"}))
    chat = [k for k in viste if not str(k.get("system", "")).startswith("Estrai")]
    assert "cerca_norma" in [t["name"] for t in chat[0]["tools"]]
    ultimo = chat[1]["messages"][-1]["content"][0]
    assert ultimo["type"] == "tool_result" and "75 gradi" in ultimo["content"] and "comma 2" in ultimo["content"]
    assert re.search(r"vigent|consolidat", ultimo["content"], re.I)   # lo strumento riporta la versione in vigore
    assert "art. 113" in ev[-1]["message"]                      # la citazione che deriva dallo strumento non viene de-specificata


def test_senza_chiamare_lo_strumento_non_si_puo_dire_di_aver_interrogato_il_database(client, fake_anthropic):
    fake_anthropic.canned_text = ("Ho interrogato il database normativo e l'art. 113 non risulta tra le fonti. " * 2 +
                                  "Ti consiglio di verificare con il consulente della sicurezza.")
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Cosa dice la norma sulle scale verticali permanenti?"}))
    m = ev[-1]["message"].lower()
    assert "ho interrogato" not in m and "estratto di fonti" in m
