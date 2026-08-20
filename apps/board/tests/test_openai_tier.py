"""OpenAI come terzo fornitore, e la catena di riserve.

Il 19 ago 2026, nella stessa ora: il modello locale non rispondeva (GB10 via tailnet) e
la chiave Anthropic era invalida (401). Con un solo fornitore alternativo l'azienda si
ferma — da qui il terzo tier e la catena annidata.
"""
import json

import pytest

import aios.llm as llm_mod
from aios.llm import FallbackLLM, LocalLLM, OpenAIError, OpenAILLM, guasto_di_trasporto
from aios.platform import _incatena, _make_llm


class RispostaFinta:
    def __init__(self, payload=None, righe=None):
        self._body = json.dumps(payload).encode() if payload is not None else b""
        self._righe = [b"data: " + json.dumps(r).encode() + b"\n" for r in (righe or [])]
        if righe:
            self._righe.append(b"data: [DONE]\n")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body

    def __iter__(self):
        return iter(self._righe)


def _monta(monkeypatch, risposte):
    chiamate = []

    def fake_post(self, body, stream=False, timeout=None):
        chiamate.append(body)
        return risposte.pop(0)

    monkeypatch.setattr(OpenAILLM, "_post", fake_post)
    return chiamate


# ---- completions ----
def test_complete_json_usa_json_object(monkeypatch):
    ch = _monta(monkeypatch, [RispostaFinta({"choices": [
        {"message": {"content": '{"proposte": []}'}}], "usage": {}})])
    out = OpenAILLM(api_key="k").complete_json(system="s", user="u", schema={"type": "object"})
    assert out == {"proposte": []}
    assert ch[0]["response_format"] == {"type": "json_object"}
    # lo schema entra come guida nel system, non come json_schema strict
    assert "JSON Schema" in ch[0]["messages"][0]["content"]


def test_complete_ritorna_il_testo(monkeypatch):
    _monta(monkeypatch, [RispostaFinta({"choices": [{"message": {"content": "ciao"}}]})])
    assert OpenAILLM(api_key="k").complete(system="s", user="u") == "ciao"


def test_senza_chiave_e_un_401_riconoscibile():
    with pytest.raises(OpenAIError) as e:
        OpenAILLM(api_key="").complete(system="s", user="u")
    assert guasto_di_trasporto(e.value) is True     # la riserva deve poter entrare


# ---- streaming tool-use ----
def test_stream_accumula_le_tool_call_a_pezzi(monkeypatch):
    """OpenAI manda name e arguments a frammenti: vanno ricomposti per indice."""
    _monta(monkeypatch, [
        RispostaFinta(righe=[
            {"choices": [{"delta": {"tool_calls": [
                {"index": 0, "function": {"name": "leggi_lead", "arguments": '{"li'}}]}}]},
            {"choices": [{"delta": {"tool_calls": [
                {"index": 0, "function": {"arguments": 'mit": 5}'}}]}}]},
        ]),
        RispostaFinta(righe=[{"choices": [{"delta": {"content": "3 lead."}}]}]),
    ])
    eseguiti = []
    eventi = list(OpenAILLM(api_key="k").stream_agentic(
        system="s", user="u", tools=[{"name": "leggi_lead", "input_schema": {}}],
        tool_exec=lambda n, i: eseguiti.append((n, i)) or [{"id": 1}]))
    assert eseguiti == [("leggi_lead", {"limit": 5})]
    assert [e["phase"] for e in eventi][-1] == "done"
    assert eventi[-1]["text"] == "3 lead."


def test_stream_testo_semplice(monkeypatch):
    _monta(monkeypatch, [RispostaFinta(righe=[
        {"choices": [{"delta": {"content": "Ci"}}]},
        {"choices": [{"delta": {"content": "ao"}}]}])])
    eventi = list(OpenAILLM(api_key="k").stream_agentic(
        system="s", user="u", tools=[], tool_exec=lambda n, i: {}))
    fasi = [e["phase"] for e in eventi]
    assert fasi[0] == "thinking" and "writing" in fasi
    assert eventi[-1]["text"] == "Ciao"


def test_server_tool_anthropic_scartati(monkeypatch):
    ch = _monta(monkeypatch, [RispostaFinta(righe=[{"choices": [{"delta": {"content": "ok"}}]}])])
    list(OpenAILLM(api_key="k").stream_agentic(
        system="s", user="u",
        tools=[{"type": "web_search_20250305", "name": "web_search"},
               {"name": "leggi_lead", "input_schema": {}}],
        tool_exec=lambda n, i: {}))
    assert [t["function"]["name"] for t in ch[0]["tools"]] == ["leggi_lead"]


# ---- catena di riserve ----
class Giu:
    def __init__(self, status=401):
        self.status_code = status
        self.tentativi = 0

    def complete_json(self, **kw):
        self.tentativi += 1
        raise OpenAIError("giù", status=self.status_code)


class Buono:
    def complete_json(self, **kw):
        return {"ok": True}


def test_la_catena_prova_tutti_i_tier():
    """Locale giù + Anthropic giù → risponde il terzo."""
    a, b = Giu(503), Giu(401)
    catena = _incatena([lambda: a, lambda: b, lambda: Buono()])
    assert catena.complete_json(system="s", user="u") == {"ok": True}
    assert a.tentativi == 1 and b.tentativi == 1


def test_un_solo_tier_niente_wrapper():
    solo = Buono()
    assert _incatena([lambda: solo]) is solo


def _tutte_le_chiavi(monkeypatch):
    monkeypatch.setenv("AIOS_LLM_BACKEND", "local")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setattr(llm_mod, "_anthropic_client", lambda key: object())


def test_gli_agenti_al_lavoro_girano_sul_locale(monkeypatch):
    """Regola dell'owner: il lavoro di fondo costa zero e può aspettare."""
    _tutte_le_chiavi(monkeypatch)
    for forte in (False, True):
        llm = _make_llm(max_tokens=4096, strong=forte)
        assert isinstance(llm._primario, LocalLLM), f"strong={forte} non parte dal locale"


def test_la_chat_gira_su_openai(monkeypatch):
    """In chat conta il tempo di risposta, e il GB10 va e viene."""
    _tutte_le_chiavi(monkeypatch)
    for forte in (False, True):
        llm = _make_llm(max_tokens=2048, strong=forte, per_chat=True)
        assert type(llm._primario).__name__ == "OpenAILLM"
        # e dietro resta la catena, non il vuoto
        secondo = llm._backup()
        assert type(secondo._primario).__name__ == "AnthropicLLM"
        assert isinstance(secondo._backup(), LocalLLM)


def test_la_chat_usa_openai_anche_senza_anthropic(monkeypatch):
    monkeypatch.setenv("AIOS_LLM_BACKEND", "local")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    llm = _make_llm(max_tokens=2048, per_chat=True)
    assert type(llm._primario).__name__ == "OpenAILLM"
    assert isinstance(llm._backup(), LocalLLM)


def test_backend_openai_mette_openai_per_primo(monkeypatch):
    monkeypatch.setenv("AIOS_LLM_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    llm = _make_llm(max_tokens=2000)
    assert type(llm._primario).__name__ == "OpenAILLM"
    assert isinstance(llm._backup(), LocalLLM)


def test_senza_chiavi_resta_il_locale(monkeypatch):
    monkeypatch.setenv("AIOS_LLM_BACKEND", "local")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert isinstance(_make_llm(max_tokens=4096), LocalLLM)


def test_modelli_dai_default_del_servizio(monkeypatch):
    """Usa i modelli già configurati sul servizio, senza inventarne."""
    monkeypatch.setattr(llm_mod, "_OPENAI_MODEL", "gpt-4o")
    monkeypatch.setattr(llm_mod, "_OPENAI_MINI", "gpt-4o-mini")
    assert OpenAILLM(api_key="k")._model == "gpt-4o"
    assert OpenAILLM(api_key="k", mini=True)._model == "gpt-4o-mini"
