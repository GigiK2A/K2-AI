"""Memoria aziendale dalla chat vera: il modello chiama `fascicolo_salva` ma il codice scrive solo dopo la conferma dell'utente."""
import os
import sys
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import fascicoli as F, strumenti  # noqa: E402
from test_e2e_scenarios import (FakeAnthropic, _make_session, client, fake_anthropic, fake_db)  # noqa: E402,F401
from test_cerca_norma_endpoint import _flusso  # noqa: E402
from test_fascicoli import _DB  # noqa: E402


def test_chat_il_modello_non_puo_salvare_senza_conferma_poi_si(client, fake_anthropic, monkeypatch):
    from app.main import app
    from app.lib.auth import AuthUser, optional_user

    db = _DB()
    monkeypatch.setattr(app.state.limiter, "enabled", False)   # il suite crea decine di sessioni al minuto
    monkeypatch.setattr(F, "_db", lambda: db)
    monkeypatch.setattr(strumenti.web_search, "enabled", lambda: False)
    esiti = []

    def stream(self, **kw):
        sis = str(kw.get("system", ""))
        if sis.startswith("Estrai") or "tools" not in kw:
            return _flusso("ok", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        ult = kw["messages"][-1]["content"]
        if isinstance(ult, list):
            esiti.append(ult[0]["content"])
            return _flusso("Fatto.", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        return _flusso("Registro. ", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[
            NS(type="tool_use", name="fascicolo_salva", id="t1", input={"codice": "UM-26-041", "titolo": "Commessa", "voci": [{"testo": "Imponibile corretto", "valore": "15.650"}]})]))

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
    try:
        sid = _make_session(client)
        client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Com'è la commessa UM-26-041?"})
        assert esiti and esiti[-1].startswith("NON SALVATO") and not db.d.get(F.T_FASC)
        client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Sì, salva nel fascicolo l'imponibile corretto"})
        assert esiti[-1].startswith("Salvato") and db.d[F.T_FASC][0]["user_id"] == "A"
    finally:
        app.dependency_overrides.pop(optional_user, None)
