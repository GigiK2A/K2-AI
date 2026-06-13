from aios.llm import FakeLLM
from aios.layers.intelligence import IntelligenceLayer


def test_insights_returns_structured_points():
    llm = FakeLLM(responses=['{"insights": [{"titolo": "Engagement basso", "evidenza": "9 like su 5 post", "azione": "caption con numeri"}]}'])
    out = IntelligenceLayer(llm).insights(context="founder...", data={"insight_ig": {"reach": 182}})
    assert isinstance(out, list) and out[0]["titolo"] == "Engagement basso"
    sys, user = llm.calls[0]
    assert "182" in user


def test_insights_robust_to_bad_json():
    out = IntelligenceLayer(FakeLLM(responses=["non json"])).insights(context="x", data={})
    assert out == []
