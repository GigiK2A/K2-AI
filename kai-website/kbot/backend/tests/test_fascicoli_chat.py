"""Memoria aziendale dalla chat vera: il modello chiama `fascicolo_salva` ma il codice scrive solo dopo la conferma dell'utente."""
import os
import sys
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import fascicoli as F, strumenti  # noqa: E402
from test_e2e_scenarios import (FakeAnthropic, _make_session, client, fake_anthropic, fake_db)  # noqa: E402,F401
from test_cerca_norma_endpoint import _flusso  # noqa: E402
from test_fascicoli import _DB  # noqa: E402


def test_chat_il_modello_non_puo_salvare_senza_conferma_poi_si(client, fake_anthropic, monkeypatch):
    from app.main import app
    from app.lib.auth import AuthUser, optional_user

    db = _DB()
    monkeypatch.setattr(app.state.limiter, "enabled", False)   # il suite crea decine di sessioni al minuto
    monkeypatch.setattr(F, "_db", lambda: db)
    monkeypatch.setattr(strumenti.web_search, "enabled", lambda: False)
    esiti = []

    def stream(self, **kw):
        sis = str(kw.get("system", ""))
        if sis.startswith("Estrai") or "tools" not in kw:
            return _flusso("ok", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        ult = kw["messages"][-1]["content"]
        if isinstance(ult, list):
            esiti.append(ult[0]["content"])
            return _flusso("Fatto.", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        return _flusso("Registro. ", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[
            NS(type="tool_use", name="fascicolo_salva", id="t1", input={"codice": "UM-26-041", "titolo": "Commessa", "voci": [{"testo": "Imponibile corretto", "valore": "15.650"}]})]))

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
    try:
        sid = _make_session(client)
        client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Com'è la commessa UM-26-041?"})
        assert esiti and esiti[-1].startswith("NON SALVATO") and not db.d.get(F.T_FASC)
        client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Sì, salva nel fascicolo l'imponibile corretto"})
        assert esiti[-1].startswith("ESITO: ok. Salvato") and db.d[F.T_FASC][0]["user_id"] == "A"
    finally:
        app.dependency_overrides.pop(optional_user, None)


# ── Test 26: strumenti realmente esposti, fascicoli grandi, citazioni dei documenti persistenti ─────────
def _flusso_tool(nome, args, tid="t1"):
    return _flusso("", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[NS(type="tool_use", name=nome, id=tid, input=args)]))


def test_il_modello_vede_tutti_gli_strumenti_fascicolo_con_schema_valido(client, fake_anthropic, monkeypatch):
    from app.main import app
    from app.lib.auth import AuthUser, optional_user
    monkeypatch.setattr(app.state.limiter, "enabled", False)
    monkeypatch.setattr(strumenti.web_search, "enabled", lambda: False)
    monkeypatch.setattr(F, "_db", lambda: _DB())
    viste = []

    def stream(self, **kw):
        viste.append(kw)
        return _flusso("ok", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
    try:
        sid = _make_session(client)
        client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Apri la commessa UM-26-041"})
        chat = [k for k in viste if "tools" in k]
        assert chat, "nessuna richiesta al modello con strumenti"
        nomi = [t["name"] for t in chat[0]["tools"]]
        assert set(F.NOMI) <= set(nomi) and len(F.NOMI) == 9 and "fascicolo_aggiorna" in F.NOMI
        for t in chat[0]["tools"]:
            assert t["input_schema"]["type"] == "object" and t["description"]
        sistema = str(chat[0]["system"])
        assert "fascicolo_voce" in sistema and "fascicolo_documento" in sistema          # le istruzioni citano gli strumenti nuovi
        # anonimo: nessuno strumento di memoria
        app.dependency_overrides[optional_user] = lambda: None
        viste.clear(); sid2 = _make_session(client)
        client.post("/api/kbot/message/stream", json={"session_id": sid2, "message": "Apri la commessa UM-26-041"})
        anon = [k for k in viste if "tools" in k]
        assert not anon or not (set(F.NOMI) & {t["name"] for t in anon[0]["tools"]})
    finally:
        app.dependency_overrides.pop(optional_user, None)


def test_fascicolo_grande_si_recupera_per_intero_a_pagine_senza_troncamenti(monkeypatch):
    db = _DB(); monkeypatch.setattr(F, "_db", lambda: db)
    F.inizia_turno("A", "s1", "salva", "", {})
    F.esegui("fascicolo_salva", {"codice": "BIG-1", "titolo": "Fascicolo di prova grande", "voci": []})
    fid = db.d[F.T_FASC][0]["id"]
    for i in range(230):
        db.d[F.T_VOCI].append({"id": f"{i:08x}-0000-4000-8000-000000000000", "fascicolo_id": fid, "user_id": "A", "tipo": "dato", "chiave": f"voce_{i}",
                               "testo": f"Voce numero {i} " + "descrizione lunga " * 6, "valore": str(1000 + i), "verifica": "non_verificato",
                               "stato_record": "attuale", "origine": "letto_da_documento", "fonti": [{"origine": "documento", "doc": "d1", "pag": 1}],
                               "created_at": f"2026-11-10T10:{i // 60:02d}:{i % 60:02d}+00:00"})
    visti, da, giri = set(), 0, 0
    while True:
        out = F.esegui("fascicolo_apri", {"fascicolo": "BIG-1", "da": da})
        assert len(out) <= F.MAX_CARATTERI_APRI, len(out)
        ids = {r.split()[1] for r in out.splitlines() if r.startswith("- ")}
        assert ids, out[:200]
        visti |= ids; giri += 1
        if "[COMPLETO" in out:
            break
        assert "[PARZIALE" in out and "da=" in out                   # mai troncato in silenzio
        da += len(ids)
        assert giri < 30
    assert len(visti) == 230 and giri > 1
    # ogni record ha un id visibile usabile per lo storico; filtro per testo e per id
    un = F.esegui("fascicolo_apri", {"fascicolo": "BIG-1", "cerca_testo": "voce_77"})
    assert "00000000-0000" not in un and "0000004d" in un and "[COMPLETO: 1–1 di 1" in un
    assert "STORICO" in F.esegui("fascicolo_voce", {"fascicolo": "BIG-1", "azione": "storico", "record": "0000004d"})


def test_citazione_di_un_documento_persistente_diventa_cliccabile_con_pagina_esatta(client, fake_anthropic, monkeypatch):
    """Nuova conversazione: il modello apre il documento dal fascicolo e lo cita; il backend verifica pagina e testo sui chunk della sessione d'origine."""
    from app.main import app
    from app.lib.auth import AuthUser, optional_user
    from app.lib import rag
    monkeypatch.setattr(app.state.limiter, "enabled", False)
    monkeypatch.setattr(strumenti.web_search, "enabled", lambda: False)
    db = _DB(); monkeypatch.setattr(F, "_db", lambda: db)
    fid = db.table(F.T_FASC).insert({"user_id": "A", "tipo": "commessa", "codice": "UM-26-041", "titolo": "Commessa", "stato": "aperto"}).execute().data[0]["id"]
    d = db.table(F.T_DOC).insert({"fascicolo_id": fid, "user_id": "A", "name": "Riepilogo.pdf", "type": "application/pdf", "size": 9, "path": "old/r.pdf",
                                  "extracted_text": "p1 intestazione p2 Residuo da liquidare 7.890,00 euro", "source_session": "sessione-vecchia", "versione": 1, "serie": "riepilogo"}).execute().data[0]
    did = F.doc_id_di(d)
    chunk = [{"file_name": "Riepilogo.pdf", "page_number": 1, "chunk_index": 0, "content": "Intestazione commessa UM-26-041"},
             {"file_name": "Riepilogo.pdf", "page_number": 2, "chunk_index": 1, "content": "Residuo da liquidare 7.890,00 euro"}]
    monkeypatch.setattr(rag, "fetch_chunks", lambda sid, limit=500: chunk if sid == "sessione-vecchia" else [])
    finali = []

    def stream(self, **kw):
        if str(kw.get("system", "")).startswith("Estrai") or "tools" not in kw:
            return _flusso("ok", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        ult = kw["messages"][-1]["content"]
        if isinstance(ult, list):
            res = ult[0]["content"]
            assert f"[doc:{did}]" in res and "pag.2" in res and "7.890,00" in res        # passaggi con pagina, non solo «parti»
            return _flusso(f"Il residuo è 7.890,00 € [[fonte|{did}|1|Residuo da liquidare 7.890,00 euro]].", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        return _flusso_tool("fascicolo_documento", {"fascicolo": "UM-26-041", "documento": did, "query": "residuo da liquidare"})

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
    try:
        sid = _make_session(client)
        r = client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Quanto resta da liquidare nella UM-26-041?"})
        import json
        ev = [json.loads(x[5:].strip()) for x in r.text.splitlines() if x.startswith("data:")]
        msg = [e for e in ev if e.get("done")][-1]["message"]
        # il modello aveva scritto pagina 1 (sbagliata): il backend la corregge alla pagina vera 2 perché il testo è lì
        assert f"[[fonte|{did}|2|Residuo da liquidare 7.890,00 euro|ok]]" in msg
    finally:
        app.dependency_overrides.pop(optional_user, None)


def test_dal_modello_due_conversazioni_nuove_aggiornano_per_id_senza_duplicati(client, fake_anthropic, monkeypatch):
    """Test 28C attraverso il modello: stessa richiesta in due conversazioni NUOVE → un solo record, rev 2, 10.000 nello storico."""
    from app.main import app
    from app.lib.auth import AuthUser, optional_user
    from test_fascicoli_aggiorna import crea_10000
    monkeypatch.setattr(app.state.limiter, "enabled", False)
    monkeypatch.setattr(strumenti.web_search, "enabled", lambda: False)
    db = _DB(); monkeypatch.setattr(F, "_db", lambda: db)
    vid = crea_10000(db)
    esiti, offerti = [], []

    def stream(self, **kw):
        if str(kw.get("system", "")).startswith("Estrai") or "tools" not in kw:
            return _flusso("ok", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        ult = kw["messages"][-1]["content"]
        if isinstance(ult, list):
            esiti.append(ult[0]["content"])
            return _flusso("Fatto.", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        offerti.append([t["name"] for t in kw["tools"]])
        return _flusso("", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[NS(
            type="tool_use", name="fascicolo_aggiorna", id="t1", input={"fascicolo": "TEST-KBOT-VERSIONI-01", "record": vid[:8], "valore": "12.500 €", "motivo": "nuova stima interna"})]))

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
    try:
        for _ in range(2):
            sid = _make_session(client)
            client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Sì, aggiorna il budget del fascicolo TEST-KBOT-VERSIONI-01 a 12.500 €"})
        assert all("fascicolo_aggiorna" in o for o in offerti)
        assert esiti[0].startswith("ESITO: ok") and "idempotente" not in esiti[0]
        assert esiti[1].startswith("ESITO: ok (idempotente)")                    # la seconda conversazione non duplica né rimodifica
        assert len(db.d[F.T_VOCI]) == 1 and db.d[F.T_VOCI][0]["id"] == vid and db.d[F.T_VOCI][0]["valore"] == "12.500 €" and db.d[F.T_VOCI][0]["revisione"] == 2
        assert [e["prima"]["valore"] for e in db.d["kbot_fascicolo_eventi"] if e["azione"] == "aggiorna"] == ["10.000 €"]
    finally:
        app.dependency_overrides.pop(optional_user, None)
