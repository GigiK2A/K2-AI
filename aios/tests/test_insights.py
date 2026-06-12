import pytest

from aios.sources.instagram import InstagramClient
from aios.sources.tools import insights_tools
from aios.kernel import Kernel, ExecOutcome

PAYLOAD = {"data": [
    {"name": "reach", "total_value": {"value": 182}},
    {"name": "accounts_engaged", "total_value": {"value": 3}},
    {"name": "total_interactions", "total_value": {"value": 9}},
    {"name": "profile_views", "total_value": {"value": 4}},
]}


def _client():
    return InstagramClient(token="T", ig_user_id="999", fetch=lambda url: PAYLOAD)


def test_account_insights_parses_total_value():
    ins = _client().account_insights()
    assert ins == {"reach": 182, "accounts_engaged": 3,
                   "total_interactions": 9, "profile_views": 4}


def test_account_insights_sends_metric_type_total_value():
    seen = {}
    def fetch(url):
        seen["url"] = url
        return PAYLOAD
    InstagramClient(token="T", ig_user_id="999", fetch=fetch).account_insights()
    assert "metric_type=total_value" in seen["url"]
    assert "period=day" in seen["url"]


def test_insights_tool_runs_via_kernel():
    k = Kernel()
    for t in insights_tools(_client()):
        k.register_tool(t)
    res = k.execute("leggi_insight_ig", actor="marketing", args={})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result["reach"] == 182
