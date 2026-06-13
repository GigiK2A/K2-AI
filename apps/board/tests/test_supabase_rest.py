import json
from aios.supabase_rest import SupabaseREST


class FakeHTTP:
    def __init__(self):
        self.requests = []
        self.responses = []
    def __call__(self, *, method, url, headers, body):
        self.requests.append({"method": method, "url": url, "headers": headers,
                              "body": json.loads(body) if body else None})
        return self.responses.pop(0) if self.responses else []


def client():
    http = FakeHTTP()
    c = SupabaseREST(url="https://x.supabase.co", service_key="KEY", fetch=http)
    return c, http


def test_select_builds_url_and_auth_headers():
    c, http = client()
    http.responses = [[{"id": 1}]]
    out = c.select("servizi", {"select": "*", "Stato": "eq.da usare"})
    assert out == [{"id": 1}]
    r = http.requests[0]
    assert r["method"] == "GET"
    assert r["url"].startswith("https://x.supabase.co/rest/v1/servizi?")
    assert "select=%2A" in r["url"] or "select=*" in r["url"]
    assert r["headers"]["apikey"] == "KEY"
    assert r["headers"]["Authorization"] == "Bearer KEY"


def test_insert_returns_representation():
    c, http = client()
    http.responses = [[{"id": 7, "action_key": "a.b"}]]
    out = c.insert("aios_audit", {"action_key": "a.b"})
    assert out == [{"id": 7, "action_key": "a.b"}]
    r = http.requests[0]
    assert r["method"] == "POST"
    assert r["headers"]["Prefer"] == "return=representation"
    assert r["body"] == {"action_key": "a.b"}


def test_upsert_sets_merge_prefer_and_on_conflict():
    c, http = client()
    http.responses = [[{"action_key": "a.b"}]]
    c.upsert("aios_policy_state", {"action_key": "a.b", "level": 1}, on_conflict="action_key")
    r = http.requests[0]
    assert r["method"] == "POST"
    assert "on_conflict=action_key" in r["url"]
    assert "resolution=merge-duplicates" in r["headers"]["Prefer"]


def test_update_uses_patch_and_filters():
    c, http = client()
    http.responses = [[{"id": 3, "status": "APPROVED"}]]
    c.update("aios_approvals", {"id": "eq.3"}, {"status": "APPROVED"})
    r = http.requests[0]
    assert r["method"] == "PATCH"
    assert "id=eq.3" in r["url"]
    assert r["body"] == {"status": "APPROVED"}
