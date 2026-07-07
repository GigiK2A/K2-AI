"""GPT Image: chiamata OpenAI + tool genera_immagine (genera → Storage → url pubblico)."""
from aios import image_gen


def test_no_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = image_gen.generate_image("un gatto")
    assert r["ok"] is False and "OPENAI_API_KEY" in r["errore"]


def test_empty_prompt(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
    r = image_gen.generate_image("   ")
    assert r["ok"] is False and "vuoto" in r["errore"]


def test_generate_parses_b64(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")

    class FakeResp:
        def read(self):
            return b'{"data":[{"b64_json":"QUJD"}]}'
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(image_gen.urllib.request, "urlopen", lambda *a, **k: FakeResp())
    r = image_gen.generate_image("logo K2-AI")
    assert r["ok"] is True and r["b64"] == "QUJD"


def test_tool_genera_immagine_chains_upload(monkeypatch):
    # generate_image ritorna b64 → upload_public → url pubblico
    import aios.image_gen as ig
    import aios.storage as st
    monkeypatch.setattr(ig, "generate_image", lambda p, **k: {"ok": True, "b64": "QQ=="})
    monkeypatch.setattr(st, "upload_public",
                        lambda name, mt, data, **k: {"ok": True, "url": "https://x/pub/ai.png"})

    # replica la closure registrata in platform.py
    def _genera_immagine(prompt=None, **_):
        if not prompt:
            return {"error": "specifica 'prompt'"}
        from aios.image_gen import generate_image
        from aios.storage import upload_public
        g = generate_image(str(prompt))
        if not g.get("ok"):
            return {"error": g.get("errore")}
        if g.get("url"):
            return {"ok": True, "url": g["url"]}
        up = upload_public("ai-image.png", "image/png", g.get("b64", ""))
        return {"ok": True, "url": up["url"]} if up.get("ok") else {"error": "upload"}

    out = _genera_immagine(prompt="poster corso AI")
    assert out["ok"] is True and out["url"] == "https://x/pub/ai.png"
    assert _genera_immagine()["error"]
