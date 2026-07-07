"""Azioni Meta (Instagram publish/commento, Ads) — sempre su conferma, ads mai attive."""
from aios.sources import meta_actions as M
from aios import actuator


def _poster(responses):
    calls = []

    def poster(path, data, token):
        calls.append((path, data))
        return responses[len(calls) - 1]
    poster.calls = calls
    return poster


def test_publish_two_steps():
    p = _poster([{"id": "CONTAINER"}, {"id": "POST123"}])
    r = M.publish_post("ciao", "http://img/x.jpg", token="T", ig_user_id="999", post=p)
    assert r["ok"] and r["post_id"] == "POST123"
    assert p.calls[0][0] == "999/media" and p.calls[0][1]["image_url"] == "http://img/x.jpg"
    assert p.calls[1][0] == "999/media_publish" and p.calls[1][1]["creation_id"] == "CONTAINER"


def test_publish_requires_image():
    r = M.publish_post("ciao", None, token="T", ig_user_id="999", post=lambda *a: {})
    assert not r["ok"] and "image_url" in r["errore"]


def test_publish_error_surfaces_token():
    p = _poster([{"error": {"message": "bad", "code": 190}}])
    r = M.publish_post("x", "http://i", token="T", ig_user_id="9", post=p)
    assert not r["ok"] and "rinnovalo" in r["errore"].lower()


def test_reply_comment():
    p = _poster([{"id": "R1"}])
    r = M.reply_comment("C1", "grazie", token="T", post=p)
    assert r["ok"] and p.calls[0][0] == "C1/replies" and p.calls[0][1]["message"] == "grazie"


def test_ad_campaign_always_paused():
    p = _poster([{"id": "CAMP1"}])
    r = M.create_ad_campaign("Promo", "lead", token="T", ad_account_id="12345", post=p)
    assert r["ok"] and r["stato"] == "PAUSED" and r["campaign_id"] == "CAMP1"
    assert p.calls[0][0] == "act_12345/campaigns"
    assert p.calls[0][1]["status"] == "PAUSED"           # ← non spende mai da solo
    assert p.calls[0][1]["objective"] == "OUTCOME_LEADS"  # sinonimo IT → enum Meta


def test_ad_needs_account():
    r = M.create_ad_campaign("x", "lead", token="T", ad_account_id="", post=lambda *a: {})
    assert not r["ok"] and "META_AD_ACCOUNT_ID" in r["errore"]


def test_apply_dispatch(monkeypatch):
    monkeypatch.setenv("AIOS_IG_TOKEN", "T")
    monkeypatch.setenv("AIOS_IG_USER_ID", "999")
    p = _poster([{"id": "CT"}, {"id": "P1"}])
    r = M.apply({"canale": "instagram", "azione": "pubblica_post",
                 "caption": "c", "image_url": "http://i"}, post=p)
    assert r["ok"] and r["post_id"] == "P1"


def test_apply_no_token(monkeypatch):
    monkeypatch.delenv("AIOS_IG_TOKEN", raising=False)
    assert not M.apply({"azione": "pubblica_post"})["ok"]


def test_actuator_routes_meta(monkeypatch):
    seen = {}

    def fake(a, post=None):
        seen["a"] = a
        return {"ok": True, "post_id": "X"}
    monkeypatch.setattr("aios.sources.meta_actions.apply", fake)
    out = actuator.apply_action(None, {"canale": "instagram", "azione": "pubblica_post",
                                       "caption": "c", "image_url": "http://i"})
    assert out["ok"] and out["canale"] == "meta"
    assert seen["a"]["azione"] == "pubblica_post"


def test_meta_is_external_so_confirmed():
    # una azione Meta è "esterna" → il classificatore la manda in conferma, mai auto
    assert actuator.is_meta_action({"canale": "meta_ads"})
    assert actuator.is_external_action({"canale": "instagram"})
