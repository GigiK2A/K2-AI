from aios.sources.instagram import InstagramClient
from aios.sources.tools import competitor_tools
from aios.kernel import Kernel, ExecOutcome


def _client(payload):
    return InstagramClient(token="T", ig_user_id="999", fetch=lambda url: payload)


def test_business_discovery_parses():
    payload = {"business_discovery": {"username": "rival", "followers_count": 5000,
                                      "media_count": 120,
                                      "media": {"data": [{"caption": "x", "like_count": 40}]}}}
    bd = _client(payload).business_discovery("rival")
    assert bd["followers_count"] == 5000
    assert bd["media"]["data"][0]["like_count"] == 40


def test_business_discovery_sends_username_in_fields():
    seen = {}
    def fetch(url):
        seen["url"] = url
        return {"business_discovery": {"username": "rival"}}
    InstagramClient(token="T", ig_user_id="999", fetch=fetch).business_discovery("rival")
    # Check for URL-encoded version since urllib.parse.urlencode encodes parentheses
    assert "business_discovery.username%28rival%29" in seen["url"]


def test_competitor_tool_runs_via_kernel():
    payload = {"business_discovery": {"username": "rival", "followers_count": 10}}
    k = Kernel()
    for t in competitor_tools(_client(payload), ["rival"]):
        k.register_tool(t)
    res = k.execute("leggi_competitor_ig", actor="marketing", args={})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result["rival"]["followers_count"] == 10
