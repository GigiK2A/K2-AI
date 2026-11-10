from app.lib import analisi_documenti, rag, prompts
from fastapi.testclient import TestClient


def _collected(n=3000):
    base = ("clausola penale art. 7 " * 40 + "recesso unilaterale " * 200) * (n // 3000 + 1)
    return {"uploaded_files": [{"name": "contratto.pdf", "type": "application/pdf", "size": 10,
                                "extractedText": base[:n] + " fideiussione 50000 euro",
                                "extractionMethod": "pdf-parse"}]}


def test_chunk_da_file_copre_tutto_il_testo():
    c = _collected(30000)
    ch = rag.chunk_da_file("s1", c["uploaded_files"])
    assert len(ch) > 15
    assert "fideiussione" in ch[-1]["content"]
    top = rag.bm25_top_k("fideiussione importo", ch, k=3)
    assert any("fideiussione 50000" in x["content"] for x in top)
    assert "[parte" in rag.format_chunks_for_prompt(top[:1])


def test_registra_e_blocco():
    c = _collected()
    assert not analisi_documenti.registra(c, "ok", "")
    assert analisi_documenti.registra(c, "Analisi: " + "x" * 900, "analizza il contratto")
    b = analisi_documenti.blocco(c)
    assert "contratto.pdf" in b and "ANALISI GIÀ SVOLTE" in b and "Non dire mai" in b
    assert analisi_documenti.blocco({}) == ""
    assert not analisi_documenti.registra({}, "x" * 900)


def test_massimo_tre_analisi():
    c = _collected()
    for i in range(5):
        analisi_documenti.registra(c, f"{i} " + "y" * 800)
    assert len(c["analisi_documenti"]) == 3


def test_endpoint_documenti_isolamento(monkeypatch):
    from app.main import app
    from app.api import upload
    from app.lib.auth import AuthUser, optional_user
    sess = {"id": "s1", "user_id": "u1", "collected_data": _collected()}
    monkeypatch.setattr(upload.sessions, "get_session", lambda sid: sess if sid == "s1" else None)
    cl = TestClient(app)
    app.dependency_overrides[optional_user] = lambda: AuthUser(id="u2", email="a@b.it", has_paid=False, raw={})
    try:
        assert cl.get("/api/kbot/session/s1/documents").status_code == 403
        app.dependency_overrides[optional_user] = lambda: AuthUser(id="u1", email="a@b.it", has_paid=False, raw={})
        r = cl.get("/api/kbot/session/s1/documents")
        assert r.status_code == 200 and r.json()["documents"][0]["nome"] == "contratto.pdf"
        assert "extractedText" not in r.text
        assert cl.get("/api/kbot/session/zz/documents").status_code == 404
    finally:
        app.dependency_overrides.pop(optional_user, None)
