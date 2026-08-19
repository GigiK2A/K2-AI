"""La chat multi-agente gira anche sul modello locale.

Lo streaming tool-use era solo di Anthropic: con `ANTHROPIC_API_KEY` non valida
(401 authentication_error, trovato in produzione il 19 ago 2026) la chat restava muta pur
avendo un gpt-oss:120b funzionante a due passi. Qui l'implementazione su Ollama, con gli
stessi eventi della versione Anthropic così il cockpit non cambia.
"""
import json

import pytest

import aios.llm as llm_mod
from aios.llm import FakeLLM, FallbackLLM, LocalLLM, LocalLLMUnreachable


class RispostaFinta:
    """File-like che itera righe NDJSON, come la risposta di /api/chat con stream=true."""

    def __init__(self, righe):
        self._righe = [json.dumps(r).encode() + b"\n" for r in righe]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        return iter(self._righe)


class OpenerFinto:
    def __init__(self, risposte):
        self._risposte = list(risposte)
        self.richieste = []

    def open(self, req, timeout=None):
        self.richieste.append(json.loads(req.data.decode()))
        return RispostaFinta(self._risposte.pop(0))


def _monta(monkeypatch, risposte):
    op = OpenerFinto(risposte)
    monkeypatch.setattr(llm_mod, "_local_opener", lambda: op)
    return op


def test_testo_in_streaming(monkeypatch):
    op = _monta(monkeypatch, [[
        {"message": {"content": "Ciao"}, "done": False},
        {"message": {"content": " Luca"}, "done": False},
        {"message": {"content": ""}, "done": True, "eval_count": 12},
    ]])
    eventi = list(LocalLLM(model="gpt-oss:120b").stream_agentic(
        system="s", user="u", tools=[], tool_exec=lambda n, i: {}))
    fasi = [e["phase"] for e in eventi]
    assert fasi[0] == "thinking" and "writing" in fasi and fasi[-1] == "done"
    assert "".join(e["text"] for e in eventi if e["phase"] == "delta") == "Ciao Luca"
    assert eventi[-1]["text"] == "Ciao Luca"
    assert op.richieste[0]["stream"] is True


def test_tool_chiamato_ed_eseguito(monkeypatch):
    _monta(monkeypatch, [
        [{"message": {"content": "", "tool_calls": [
            {"function": {"name": "leggi_lead", "arguments": {"limit": 5}}}]}, "done": True}],
        [{"message": {"content": "Ho 3 lead."}, "done": True}],
    ])
    eseguiti = []
    eventi = list(LocalLLM().stream_agentic(
        system="s", user="u",
        tools=[{"name": "leggi_lead", "description": "d",
                "input_schema": {"type": "object", "properties": {}}}],
        tool_exec=lambda n, i: eseguiti.append((n, i)) or [{"id": 1}]))
    fasi = [e["phase"] for e in eventi]
    assert "tool" in fasi and "tool_run" in fasi
    assert eseguiti == [("leggi_lead", {"limit": 5})]
    assert eventi[-1]["text"] == "Ho 3 lead."


def test_argomenti_come_stringa_json(monkeypatch):
    """Alcune versioni di Ollama mandano gli argomenti già serializzati."""
    _monta(monkeypatch, [
        [{"message": {"tool_calls": [
            {"function": {"name": "leggi_lead", "arguments": '{"limit": 2}'}}]}, "done": True}],
        [{"message": {"content": "ok"}, "done": True}],
    ])
    visti = []
    list(LocalLLM().stream_agentic(system="s", user="u",
                                   tools=[{"name": "leggi_lead", "input_schema": {}}],
                                   tool_exec=lambda n, i: visti.append(i) or {}))
    assert visti == [{"limit": 2}]


def test_il_risultato_del_tool_torna_al_modello(monkeypatch):
    op = _monta(monkeypatch, [
        [{"message": {"tool_calls": [
            {"function": {"name": "leggi_lead", "arguments": {}}}]}, "done": True}],
        [{"message": {"content": "fine"}, "done": True}],
    ])
    list(LocalLLM().stream_agentic(system="s", user="u",
                                   tools=[{"name": "leggi_lead", "input_schema": {}}],
                                   tool_exec=lambda n, i: [{"id": 7}]))
    secondo = op.richieste[1]["messages"]
    ruoli = [m["role"] for m in secondo]
    assert "tool" in ruoli
    assert '"id": 7' in [m for m in secondo if m["role"] == "tool"][0]["content"]


def test_server_tool_anthropic_scartati(monkeypatch):
    """web_search è un server-tool Anthropic: mandarlo a Ollama farebbe fallire tutto."""
    op = _monta(monkeypatch, [[{"message": {"content": "ok"}, "done": True}]])
    list(LocalLLM().stream_agentic(
        system="s", user="u",
        tools=[{"type": "web_search_20250305", "name": "web_search"},
               {"name": "leggi_lead", "input_schema": {}}],
        tool_exec=lambda n, i: {}, web_search=True))
    nomi = [t["function"]["name"] for t in op.richieste[0].get("tools", [])]
    assert nomi == ["leggi_lead"]


def test_immagini_passate_a_ollama(monkeypatch):
    op = _monta(monkeypatch, [[{"message": {"content": "vedo"}, "done": True}]])
    list(LocalLLM().stream_agentic(
        system="s", user="u", tools=[], tool_exec=lambda n, i: {},
        media=[{"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                            "data": "AAA"}},
               {"type": "document", "source": {"type": "base64",
                                               "media_type": "application/pdf",
                                               "data": "BBB"}}]))
    utente = [m for m in op.richieste[0]["messages"] if m["role"] == "user"][0]
    assert utente["images"] == ["AAA"]        # il PDF resta fuori


def test_ollama_giu_solleva_il_guasto_riconoscibile(monkeypatch):
    class OpenerRotto:
        def open(self, req, timeout=None):
            raise ConnectionError("rifiutata")

    monkeypatch.setattr(llm_mod, "_local_opener", lambda: OpenerRotto())
    monkeypatch.setattr(llm_mod, "_LOCAL_RETRIES", 0)
    with pytest.raises(LocalLLMUnreachable):
        list(LocalLLM().stream_agentic(system="s", user="u", tools=[],
                                       tool_exec=lambda n, i: {}))


# ---- riserva sullo stream ----
class StreamRotto:
    def stream_agentic(self, **kw):
        raise ConnectionError("primario giù")
        yield  # pragma: no cover


class StreamAMeta:
    def stream_agentic(self, **kw):
        yield {"phase": "thinking"}
        yield {"phase": "delta", "text": "metà"}
        raise ConnectionError("caduto a metà")


class StreamCheDichiaraEPoiMuore:
    """Come la versione Anthropic: annuncia `thinking` e POI prende il 401.
    Bug reale del 19 ago 2026: così la riserva non entrava mai."""

    def stream_agentic(self, **kw):
        yield {"phase": "thinking"}
        raise ConnectionError("401 dopo l'annuncio")


class StreamCheEseguePoiMuore:
    def stream_agentic(self, **kw):
        yield {"phase": "thinking"}
        yield {"phase": "tool_run", "tool": "esegui"}
        raise ConnectionError("caduto dopo aver eseguito")


class StreamBuono:
    def stream_agentic(self, **kw):
        yield {"phase": "done", "text": "dalla riserva"}


def test_se_il_primario_cade_prima_di_parlare_entra_la_riserva():
    llm = FallbackLLM(StreamRotto(), StreamBuono())
    eventi = list(llm.stream_agentic(system="s", user="u", tools=[], tool_exec=None))
    assert eventi == [{"phase": "done", "text": "dalla riserva"}]
    assert llm.fallback_usati == 1


def test_se_cade_a_meta_non_si_riparte_da_zero():
    """Ripartire duplicherebbe il testo già letto dall'utente: meglio un troncamento."""
    llm = FallbackLLM(StreamAMeta(), StreamBuono())
    with pytest.raises(ConnectionError):
        list(llm.stream_agentic(system="s", user="u", tools=[], tool_exec=None))


def test_thinking_non_conta_come_aver_parlato():
    """L'evento di stato non è output: la riserva deve poter entrare."""
    llm = FallbackLLM(StreamCheDichiaraEPoiMuore(), StreamBuono())
    eventi = list(llm.stream_agentic(system="s", user="u", tools=[], tool_exec=None))
    assert eventi[0]["phase"] == "thinking"          # l'annuncio del primario resta
    assert eventi[-1]["text"] == "dalla riserva"     # ma la risposta arriva
    assert llm.fallback_usati == 1


def test_dopo_un_tool_eseguito_non_si_riparte():
    """Un tool già eseguito è irreversibile: rifarlo raddoppierebbe l'azione."""
    llm = FallbackLLM(StreamCheEseguePoiMuore(), StreamBuono())
    with pytest.raises(ConnectionError):
        list(llm.stream_agentic(system="s", user="u", tools=[], tool_exec=None))


def test_primario_senza_streaming_usa_la_riserva():
    llm = FallbackLLM(FakeLLM(responses=["x"]), StreamBuono())
    eventi = list(llm.stream_agentic(system="s", user="u", tools=[], tool_exec=None))
    assert eventi[-1]["text"] == "dalla riserva"


# ---- parametri da interattivo (latenza) ----
def test_la_chat_usa_un_budget_corto(monkeypatch):
    """Il budget di 8192 token era il moltiplicatore della latenza: su un 120B remoto
    ogni token si paga in secondi, e una risposta di chat non ne ha bisogno."""
    op = _monta(monkeypatch, [[{"message": {"content": "ok"}, "done": True}]])
    list(LocalLLM().stream_agentic(system="s", user="u", tools=[], tool_exec=lambda n, i: {}))
    req = op.richieste[0]
    assert req["options"]["num_predict"] == llm_mod._LOCAL_CHAT_NUM_PREDICT
    assert req["options"]["num_predict"] <= 2048
    assert req["think"] == llm_mod._LOCAL_CHAT_THINK      # reasoning corto in chat


def test_il_chiamante_puo_imporre_il_suo_budget(monkeypatch):
    op = _monta(monkeypatch, [[{"message": {"content": "ok"}, "done": True}]])
    list(LocalLLM().stream_agentic(system="s", user="u", tools=[],
                                   tool_exec=lambda n, i: {}, max_tokens=4096))
    assert op.richieste[0]["options"]["num_predict"] == 4096


def test_meno_giri_di_tool_in_chat(monkeypatch):
    """Ogni giro è una generazione intera: tre bastano, sei sono minuti."""
    assert llm_mod._LOCAL_CHAT_ITERS <= 4


def test_chi_chiede_pochi_token_ne_ottiene_pochi():
    """Prima era max(richiesta, 8192): il chiamante non poteva chiedere meno."""
    assert LocalLLM(max_tokens=1000)._num_predict == 1000
    assert LocalLLM(max_tokens=10)._num_predict == llm_mod._LOCAL_NUM_PREDICT_MIN
    assert LocalLLM()._num_predict == llm_mod._LOCAL_NUM_PREDICT
