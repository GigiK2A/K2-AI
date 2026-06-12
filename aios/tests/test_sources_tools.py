from aios.kernel import Kernel, ExecOutcome
from aios.sources.tools import content_tools, instagram_tools


class _FakeConn:
    pass


class _FakeIG:
    def account(self):
        return {"username": "k2ai", "followers_count": 7}
    def recent_media(self, limit=10):
        return [{"id": "1"}][:limit]


def test_content_tools_are_readonly_and_run_via_kernel(monkeypatch):
    import aios.sources.tools as t
    monkeypatch.setattr(t, "read_servizi", lambda conn: [{"Servizio": "X"}])
    monkeypatch.setattr(t, "read_topics", lambda conn: [{"Tema": "Y"}])
    k = Kernel()
    for tool in t.content_tools(_FakeConn()):
        k.register_tool(tool)
    res = k.execute("leggi_servizi", actor="marketing", args={})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result == [{"Servizio": "X"}]


def test_instagram_tools_run_via_kernel():
    k = Kernel()
    for tool in instagram_tools(_FakeIG()):
        k.register_tool(tool)
    assert k.execute("leggi_profilo_ig", actor="marketing", args={}).result["followers_count"] == 7
    assert k.execute("leggi_post_ig", actor="marketing", args={"limit": 1}).result == [{"id": "1"}]


def test_content_tools_rest_run_via_kernel():
    from aios.sources.tools import content_tools_rest

    class _FakeClient:
        def select(self, table, params):
            return [{"row": table}]
    k = Kernel()
    for tool in content_tools_rest(_FakeClient()):
        k.register_tool(tool)
    assert k.execute("leggi_servizi", actor="m", args={}).result == [{"row": "servizi"}]
    assert k.execute("leggi_topics", actor="m", args={}).result == [{"row": "topics"}]
