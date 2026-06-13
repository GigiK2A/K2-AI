from aios.sources.tools import competitor_lookup_tool
from aios.kernel import Kernel, ExecOutcome


class _IG:
    def business_discovery(self, u):
        return {"username": u, "followers_count": {"a": 10, "b": 20}[u]}


def test_lookup_runs_for_passed_usernames():
    k = Kernel()
    k.register_tool(competitor_lookup_tool(_IG()))
    res = k.execute("analizza_competitor", actor="marketing", args={"usernames": ["a", "b"]})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result["a"]["followers_count"] == 10
    assert res.result["b"]["followers_count"] == 20


def test_lookup_empty_list_returns_empty():
    k = Kernel()
    k.register_tool(competitor_lookup_tool(_IG()))
    assert k.execute("analizza_competitor", actor="m", args={"usernames": []}).result == {}
