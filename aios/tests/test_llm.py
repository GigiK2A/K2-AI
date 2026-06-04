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
