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
