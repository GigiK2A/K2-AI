"""Web search reale (OpenAI dietro al client-tool di Claude): invarianti puri, no rete.

Copre:
- quali campi sono RICERCABILI (competitor/mercato) vs privati (bilanci/obiettivi);
- shape del client-tool `web_search` (no max_uses: l'esecuzione è nostra → OpenAI);
- `enabled()` = flag KBOT_WEB_SEARCH + OPENAI_API_KEY;
- loop agentico di create_with_web_search (Claude chiama il tool → handler OpenAI → continua);
- estrazione citazioni dalla risposta OpenAI;
- ricerca pre-gate no-op (zero chiamate) quando non c'è nulla da cercare o è spenta;
- happy-path di merge/provenienza con create_with_web_search stubbato.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.lib import web_search, research  # noqa: E402


# --- fakes (Claude messages API) -------------------------------------------

class _TextB:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _ToolUse:
    def __init__(self, id, name, inp):
        self.type = "tool_use"
        self.id = id
        self.name = name
        self.input = inp


class _Msg:
    def __init__(self, stop, content):
        self.stop_reason = stop
        self.content = content
        self.usage = None


class _Messages:
    def __init__(self, scripted):
        self._scripted = list(scripted)
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        return self._scripted[min(len(self.calls) - 1, len(self._scripted) - 1)]


class _Client:
    def __init__(self, scripted):
        self.messages = _Messages(scripted)


# --- is_researchable -------------------------------------------------------

@pytest.mark.parametrize("campo", [
    {"id": "competitor", "label": "i 2-3 competitor principali"},
    {"id": "concorrenti", "label": "concorrenti diretti"},
    {"id": "analisi_mercato", "label": "dimensione del mercato"},
    {"id": "benchmark", "label": "benchmark di settore"},
])
def test_researchable_public_fields(campo):
    assert research.is_researchable(campo) is True


@pytest.mark.parametrize("campo", [
    {"id": "obiettivo_strategico", "label": "cosa vuole ottenere nei prossimi 1-3 anni"},
    {"id": "bilanci", "label": "bilanci degli ultimi esercizi"},
    {"id": "descrizione_azienda", "label": "settore, prodotti/servizi della tua azienda"},
    {"id": "fatturato", "label": "fatturato annuo"},
])
def test_not_researchable_private_fields(campo):
    # MAI cercare sul web dati interni privati del cliente
    assert research.is_researchable(campo) is False


# --- client-tool shape + enabled() -----------------------------------------

def test_web_search_tool_is_client_tool():
    tool = web_search.web_search_tool()
    assert tool["name"] == "web_search"
    assert "input_schema" in tool  # client-tool (no 'type' server-tool, no max_uses)
    assert "query" in tool["input_schema"]["properties"]
    assert "max_uses" not in tool


def test_enabled_needs_flag_and_openai_key(monkeypatch):
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KBOT_WEB_SEARCH", "1")
    assert web_search.enabled() is True
    monkeypatch.setenv("KBOT_WEB_SEARCH", "0")
    assert web_search.enabled() is False
    monkeypatch.setenv("KBOT_WEB_SEARCH", "1")
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", None)
    assert web_search.enabled() is False  # niente chiave OpenAI → niente ricerca


# --- create_with_web_search (loop client-tool → OpenAI) --------------------

def test_create_runs_tool_loop_via_openai(monkeypatch):
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KBOT_WEB_SEARCH", "1")
    monkeypatch.setattr(web_search, "run_openai_search", lambda q: f"RES:{q}")

    scripted = [
        _Msg("tool_use", [_TextB("cerco..."), _ToolUse("tu1", "web_search", {"query": "competitor TLC"})]),
        _Msg("end_turn", [_TextB("ecco i competitor")]),
    ]
    client = _Client(scripted)
    resp = web_search.create_with_web_search(
        client, model="m", max_tokens=50, system="s",
        messages=[{"role": "user", "content": "trova i competitor"}],
    )
    assert len(client.messages.calls) == 2          # 1 ricerca → 1 continuazione
    assert any(t.get("name") == "web_search" for t in client.messages.calls[0]["tools"])
    # il risultato OpenAI è tornato a Claude come tool_result
    tr = client.messages.calls[1]["messages"][-1]
    assert tr["role"] == "user"
    assert tr["content"][0]["content"] == "RES:competitor TLC"
    assert resp.stop_reason == "end_turn"


def test_create_no_tool_when_disabled(monkeypatch):
    monkeypatch.setenv("KBOT_WEB_SEARCH", "0")
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", "sk-test")
    client = _Client([_Msg("end_turn", [_TextB("ciao")])])
    web_search.create_with_web_search(
        client, model="m", max_tokens=10, system="s",
        messages=[{"role": "user", "content": "ciao"}],
    )
    assert "tools" not in client.messages.calls[0]


# --- OpenAI helpers --------------------------------------------------------

def test_run_openai_search_no_key(monkeypatch):
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", None)
    out = web_search.run_openai_search("qualcosa")
    assert "non configurata" in out.lower()


def test_extract_citations_dedups():
    class _Ann:
        def __init__(self, u, t):
            self.type = "url_citation"
            self.url = u
            self.title = t

    class _CB:
        def __init__(self, anns):
            self.annotations = anns

    class _Out:
        def __init__(self, content):
            self.content = content

    class _Resp:
        def __init__(self, output):
            self.output = output
            self.output_text = "txt"

    resp = _Resp([_Out([_CB([_Ann("https://a.it", "A"), _Ann("https://a.it", "A"),
                             _Ann("https://b.it", "B")])])])
    cites = web_search._extract_citations(resp)
    assert cites == [{"url": "https://a.it", "title": "A"}, {"url": "https://b.it", "title": "B"}]


# --- research pre-gate: no-op safety + happy path --------------------------

def test_research_noop_no_researchable_field(monkeypatch):
    monkeypatch.setenv("KBOT_WEB_SEARCH", "1")
    monkeypatch.setattr(research, "ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", "sk-test")
    boom = {"n": 0}
    monkeypatch.setattr(research.web_search, "create_with_web_search",
                        lambda *a, **k: boom.__setitem__("n", boom["n"] + 1))
    out, fonti = research.research_missing_fields(
        {"messages": []}, [], [{"id": "obiettivo_strategico", "obbligatorio": True}], {})
    assert out == {} and fonti == []
    assert boom["n"] == 0  # zero chiamate: niente di ricercabile


def test_research_noop_when_web_disabled(monkeypatch):
    monkeypatch.setenv("KBOT_WEB_SEARCH", "0")  # ricerca spenta
    monkeypatch.setattr(research, "ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", "sk-test")
    out, fonti = research.research_missing_fields(
        {"messages": []}, [],
        [{"id": "competitor", "obbligatorio": True, "label": "competitor"}], {})
    assert out == {} and fonti == []


def test_is_researchable_explicit_flag_overrides_heuristic():
    # un flag esplicito dal form 8e vince sull'euristica keyword
    assert research.is_researchable({"id": "x", "label": "qualcosa", "ricercabile": True}) is True
    assert research.is_researchable({"id": "competitor", "label": "competitor", "ricercabile": False}) is False
    assert research.is_researchable({"id": "x", "researchable": True}) is True


def test_generation_executes_web_search_not_stub(monkeypatch):
    # FASE 2: _run_llm_call deve ESEGUIRE la ricerca (OpenAI), non lo stub legacy.
    from app.lib import analysis
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KBOT_WEB_SEARCH", "1")
    monkeypatch.setattr(web_search, "run_openai_search", lambda q: "REALRESULT")

    scripted = [
        _Msg("tool_use", [_ToolUse("tu1", "web_search", {"query": "benchmark settore"})]),
        _Msg("end_turn", [_TextB('{"meta": {}}')]),
    ]
    client = _Client(scripted)
    out = analysis._run_llm_call(client, [], "genera", use_web_search=True)
    assert out == '{"meta": {}}'
    tr = client.messages.calls[1]["messages"][-1]
    assert tr["content"][0]["content"] == "REALRESULT"   # NON "[no client-side tool wired]"


def test_a2_agent_dispatches_web_search(monkeypatch):
    from app.lib import boost_agent
    monkeypatch.setattr(boost_agent.web_search, "run_openai_search", lambda q: f"RES:{q}")
    trace = boost_agent.Trace()
    out = boost_agent.exec_tool("web_search", {"query": "competitor IT"}, trace, set())
    assert out == {"risultati": "RES:competitor IT"}
    assert len(trace.calls) == 1  # registrato in provenienza (contesto, non numeri EV)


def test_research_fills_competitor_with_sources(monkeypatch):
    monkeypatch.setenv("KBOT_WEB_SEARCH", "1")
    monkeypatch.setattr(research, "ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(web_search, "OPENAI_API_KEY", "sk-test")
    from app.lib import analysis as _an
    monkeypatch.setattr(_an, "_build_context_block", lambda s: "ctx")

    payload = ('{"competitor": [{"nome": "Acme", "descrizione": "TLC IT"}], '
               '"_fonti": ["https://fonte.example/1"]}')
    monkeypatch.setattr(research.web_search, "create_with_web_search",
                        lambda *a, **k: _Msg("end_turn", [_TextB(payload)]))

    campo = {"id": "competitor", "obbligatorio": True, "label": "competitor", "tipo": "array"}
    out, fonti = research.research_missing_fields(
        {"messages": [{"role": "user", "content": "settore TLC Italia"}]},
        [campo], [campo], {"ragione_sociale": "K2A"})
    assert out["competitor"][0]["nome"] == "Acme"
    assert fonti == ["https://fonte.example/1"]
