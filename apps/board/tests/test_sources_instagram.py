import pytest

from aios.sources.instagram import InstagramClient, InstagramError


def make_client(responses):
    def fake_fetch(url):
        for needle, payload in responses.items():
            if needle in url:
                return payload
        raise AssertionError(f"no fake response for {url}")
    return InstagramClient(token="T", ig_user_id="999", fetch=fake_fetch)


def test_account_parses_fields():
    c = make_client({"/v21.0/999?": {"username": "k2ai",
                                      "followers_count": 1200, "media_count": 42}})
    acc = c.account()
    assert acc["followers_count"] == 1200 and acc["username"] == "k2ai"


def test_recent_media_returns_list():
    c = make_client({"/999/media?": {"data": [
        {"id": "1", "like_count": 10, "comments_count": 2},
        {"id": "2", "like_count": 5, "comments_count": 0},
    ]}})
    media = c.recent_media(limit=2)
    assert [m["id"] for m in media] == ["1", "2"]


def test_token_is_sent_in_url():
    seen = {}
    def fake_fetch(url):
        seen["url"] = url
        return {"username": "x", "followers_count": 0, "media_count": 0}
    InstagramClient(token="SECRET", ig_user_id="999", fetch=fake_fetch).account()
    assert "access_token=SECRET" in seen["url"]


def test_graph_error_raises():
    c = make_client({"/v21.0/999?": {"error": {"message": "bad token"}}})
    with pytest.raises(InstagramError):
        c.account()


def test_expired_token_gives_friendly_message():
    c = make_client({"/v21.0/999?": {"error": {
        "message": "Error validating access token: session invalidated",
        "code": 190}}})
    with pytest.raises(InstagramError) as ei:
        c.account()
    m = str(ei.value)
    assert "AIOS_IG_TOKEN" in m and "RINNOVATO" in m.upper()


def test_http_400_body_is_read(monkeypatch):
    # Meta risponde 400 con l'errore vero nel body: _urllib_fetch deve leggerlo,
    # non far propagare un generico "HTTP 400".
    import io
    import urllib.error
    from aios.sources import instagram

    def boom(url, timeout=20):
        body = io.BytesIO(b'{"error":{"message":"session invalidated","code":190}}')
        raise urllib.error.HTTPError(url, 400, "Bad Request", {}, body)

    monkeypatch.setattr(instagram.urllib.request, "urlopen", boom)
    data = instagram._urllib_fetch("http://x")
    assert data["error"]["code"] == 190


def test_comments_returns_text():
    c = make_client({"/17_1/comments?": {"data": [
        {"id": "c1", "text": "Bel post!", "username": "mario"},
    ]}})
    cm = c.comments("17_1")
    assert cm[0]["text"] == "Bel post!" and cm[0]["username"] == "mario"


def test_latest_comments_skips_zero_and_flattens():
    c = make_client({
        "/999/media?": {"data": [
            {"id": "A", "comments_count": 1, "caption": "K2-AI Gazette", "permalink": "http://p/A"},
            {"id": "B", "comments_count": 0, "caption": "no", "permalink": "http://p/B"},
        ]},
        "/A/comments?": {"data": [
            {"id": "c1", "text": "Interessante", "username": "lucia",
             "replies": {"data": [{"text": "grazie!"}]}},
        ]},
    })
    out = c.latest_comments()
    assert len(out) == 1                       # post B (0 commenti) saltato
    assert out[0]["text"] == "Interessante"
    assert out[0]["post_caption"] == "K2-AI Gazette"
    assert out[0]["replies"] == ["grazie!"]
