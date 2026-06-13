from aios.llm import FakeLLM
from aios.founder import default_founder_model
from aios.sources.competitor_discovery import discover_competitor_handles


def test_discovers_handles_from_llm_json():
    llm = FakeLLM(responses=['{"handles": ["studioalpha", "ai_partners_it", "pmi_digitale"]}'])
    handles = discover_competitor_handles(llm, default_founder_model(), max_handles=3)
    assert handles == ["studioalpha", "ai_partners_it", "pmi_digitale"]
    _, user = llm.calls[0]
    assert "PMI" in user


def test_strips_at_and_limits():
    llm = FakeLLM(responses=['{"handles": ["@one", "@two", "@three", "@four"]}'])
    handles = discover_competitor_handles(llm, default_founder_model(), max_handles=2)
    assert handles == ["one", "two"]


def test_bad_json_returns_empty():
    llm = FakeLLM(responses=["non lo so"])
    assert discover_competitor_handles(llm, default_founder_model()) == []
