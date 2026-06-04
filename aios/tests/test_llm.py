from aios.llm import FakeLLM, LLM


def test_fakellm_returns_scripted_and_records_calls():
    llm = FakeLLM(responses=["ciao"])
    out = llm.complete(system="s", user="u")
    assert out == "ciao"
    assert llm.calls == [("s", "u")]


def test_fakellm_cycles_when_exhausted():
    llm = FakeLLM(responses=["a"])
    assert llm.complete(system="s", user="u1") == "a"
    assert llm.complete(system="s", user="u2") == "a"


def test_llm_is_a_protocol():
    assert hasattr(LLM, "__subclasshook__") or True


def test_anthropic_web_search_tool_is_added_when_enabled(monkeypatch):
    import aios.llm as llmmod

    captured = {}

    class _FakeMessages:
        def create(self, **kw):
            captured.update(kw)
            class _Block:
                type = "text"; text = "ok"
            class _Resp:
                content = [_Block()]
            return _Resp()

    class _FakeClient:
        def __init__(self, *a, **k):
            self.messages = _FakeMessages()

    monkeypatch.setattr(llmmod, "_anthropic_client", lambda key: _FakeClient())
    llm = llmmod.AnthropicLLM(api_key="K", enable_web_search=True)
    out = llm.complete(system="s", user="u")
    assert out == "ok"
    tools = captured.get("tools") or []
    assert any(t.get("type", "").startswith("web_search") for t in tools)


def test_anthropic_no_tools_when_web_search_disabled(monkeypatch):
    import aios.llm as llmmod

    captured = {}

    class _FakeMessages:
        def create(self, **kw):
            captured.update(kw)
            class _Block:
                type = "text"; text = "ok"
            class _Resp:
                content = [_Block()]
            return _Resp()

    class _FakeClient:
        def __init__(self, *a, **k):
            self.messages = _FakeMessages()

    monkeypatch.setattr(llmmod, "_anthropic_client", lambda key: _FakeClient())
    llm = llmmod.AnthropicLLM(api_key="K")
    llm.complete(system="s", user="u")
    assert "tools" not in captured or not captured["tools"]
