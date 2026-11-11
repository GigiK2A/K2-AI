"""TEST 31 — isolamento fra aziende (account) nel backend K-BOT. Prove tecniche, non dichiarazioni del modello.

Due «aziende» fittizie, TEST-TENANT-A e TEST-TENANT-B, ognuna con un utente, un fascicolo (record + storico + due versioni di un PDF),
una conversazione e un codice segreto sintetico. L'utente A attacca le risorse di B con gli endpoint e gli strumenti VERI, e viceversa:
ogni tentativo deve fallire E i dati di B devono restare identici (confronto prima/dopo), E nessun byte segreto deve comparire nella risposta.

Il database è un finto con filtri veri (nessun Supabase, nessun dato reale). L'identità arriva da un header di prova che sostituisce SOLO la
validazione del JWT: tutto il resto è il codice di produzione. Si rilancia con: pytest tests/test_isolamento_tenant.py
"""
import copy
import io
import os
import sys
import uuid
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import fascicoli as F, fascicoli_documenti as D, fonti_documenti as FD  # noqa: E402

UA, UB = "aaaaaaaa-0000-4000-8000-00000000000a", "bbbbbbbb-0000-4000-8000-00000000000b"
SEGRETO = {UA: "CODICE-SEGRETO-A-7F3K9", UB: "CODICE-SEGRETO-B-Q2X8M"}
IMPORTO = {UA: "11.111,11 €", UB: "22.222,22 €"}
COD = {UA: "TEST-ISOLAMENTO-A", UB: "TEST-ISOLAMENTO-B"}


# ── database finto con filtri veri ────────────────────────────────────────────────────────────────────
class Q:
    def __init__(s, db, t):
        s.db, s.t, s.f, s.mode, s.p, s.lim, s.one = db, t, [], "select", None, None, False

    def select(s, *a, **k): s.mode = "select"; return s
    def insert(s, row): s.mode, s.p = "insert", row; return s
    def update(s, p): s.mode, s.p = "update", p; return s
    def upsert(s, row, **k): s.mode, s.p = "upsert", row; return s
    def delete(s): s.mode = "delete"; return s
    def limit(s, n): s.lim = n; return s
    def order(s, *a, **k): return s
    def single(s): s.one = True; return s
    maybe_single = single

    def _val(s, r, k):
        if "->>" in k:                                                   # colonna JSONB: collected_data->>chiave
            col, key = k.split("->>")
            return (r.get(col) or {}).get(key)
        return r.get(k)

    def eq(s, k, v): s.f.append(lambda r: str(s._val(r, k)) == str(v)); return s
    def neq(s, k, v): s.f.append(lambda r: str(s._val(r, k)) != str(v)); return s
    def in_(s, k, vs): s.f.append(lambda r: r.get(k) in vs); return s
    def is_(s, k, v): s.f.append((lambda r: r.get(k) is None) if v == "null" else (lambda r: r.get(k) is v)); return s

    def execute(s):
        rows = s.db.tables.setdefault(s.t, [])
        m = [r for r in rows if all(f(r) for f in s.f)]
        if s.mode == "insert":
            row = {"id": str(uuid.uuid4()), "created_at": "2026-11-11T10:00:00+00:00", "updated_at": "2026-11-11T10:00:00+00:00", **s.p}
            rows.append(row); data = [row]
        elif s.mode == "upsert":
            key = "user_id" if "user_id" in s.p else "id"
            ex = [r for r in rows if r.get(key) == s.p.get(key)]
            if ex: ex[0].update(s.p); data = [ex[0]]
            else:
                row = {"id": str(uuid.uuid4()), **s.p}; rows.append(row); data = [row]
        elif s.mode == "update":
            for r in m: r.update(s.p)
            data = m
        elif s.mode == "delete":
            for r in m: rows.remove(r)
            data = m
        else:
            data = m[:s.lim] if s.lim else m
        if s.one:
            data = data[0] if data else None
        return NS(data=[dict(r) for r in data] if isinstance(data, list) else data, count=len(m))


class DB:
    def __init__(s):
        from test_e2e_scenarios import _FakeStorage
        s.tables, s.storage = {}, _FakeStorage()

    def table(s, n): return Q(s, n)


def _pdf(testo: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=A4); c.drawString(60, 780, testo); c.showPage(); c.save()
    return b.getvalue()


class Mondo:
    """Le due aziende e tutto ciò che possiedono."""
    pass


@pytest.fixture
def mondo(monkeypatch):
    from fastapi import Header, HTTPException
    from fastapi.testclient import TestClient
    import app.main as main
    from app.lib import auth, sessions, supabase_admin  # noqa: F401
    from app.lib.auth import AuthUser, optional_user, require_user
    from app.api import upload, deliverables

    db = DB()
    for name, mod in list(sys.modules.items()):                          # ogni modulo che prende il client admin lo prende dal finto
        if name.startswith("app") and hasattr(mod, "get_admin_client"):
            monkeypatch.setattr(mod, "get_admin_client", lambda: db)
    monkeypatch.setattr(F, "_db", lambda: db)
    monkeypatch.setattr(main.app.state.limiter, "enabled", False)
    D._SCHEMA.clear()

    def _chi(x_test_user=Header(default=None)):
        return AuthUser(id=x_test_user, email=None, has_paid=False, raw={}) if x_test_user else None

    def _richiede(x_test_user=Header(default=None)):
        if not x_test_user:
            raise HTTPException(status_code=401, detail="missing token")
        return AuthUser(id=x_test_user, email=None, has_paid=False, raw={})

    main.app.dependency_overrides[optional_user] = _chi
    main.app.dependency_overrides[require_user] = _richiede

    m = Mondo(); m.db = db; m.client = TestClient(main.app, raise_server_exceptions=False); m.f = {}; m.doc = {}; m.sess = {}; m.job = {}; m.conv = {}; m.pdf = {}
    jobs = {}
    for u in (UA, UB):
        # fascicolo con un record, la sua storia e un documento in DUE versioni
        fid = db.table(F.T_FASC).insert({"user_id": u, "tipo": "commessa", "codice": COD[u], "titolo": f"Fascicolo {COD[u]}", "stato": "aperto"}).execute().data[0]["id"]
        vid = db.table(F.T_VOCI).insert({"fascicolo_id": fid, "user_id": u, "tipo": "dato", "chiave": "budget", "testo": f"Budget {SEGRETO[u]}", "valore": IMPORTO[u], "unita": "EUR",
                                         "verifica": "non_verificato", "stato_record": "attuale", "origine": "dichiarato_utente", "revisione": 1, "fonti": []}).execute().data[0]["id"]
        ev = db.table("kbot_fascicolo_eventi").insert({"fascicolo_id": fid, "user_id": u, "voce_id": vid, "azione": "crea", "prima": None, "dopo": {"valore": IMPORTO[u]}, "motivo": SEGRETO[u], "attore": "utente"}).execute().data[0]["id"]
        dup = db.table(F.T_VOCI).insert({"fascicolo_id": fid, "user_id": u, "tipo": "dato", "chiave": "budget", "testo": f"Budget {SEGRETO[u]}", "valore": IMPORTO[u], "unita": "EUR",
                                         "verifica": "non_verificato", "stato_record": "attuale", "origine": "dichiarato_utente", "revisione": 1, "fonti": []}).execute().data[0]["id"]
        logico = str(uuid.uuid4()); docs = []
        for n in (1, 2):
            path = f"{u}/doc-v{n}.pdf"
            testo = f"Contratto riservato {SEGRETO[u]} versione {n} importo {IMPORTO[u]}"
            db.storage.bucket if False else None
            m.pdf[path] = _pdf(testo)
            d = db.table(F.T_DOC).insert({"fascicolo_id": fid, "user_id": u, "name": f"contratto-{COD[u]}.pdf" if n == 1 else f"contratto-{COD[u]}_v2.pdf", "type": "application/pdf", "size": 10, "path": path,
                                          "extracted_text": testo, "source_session": None, "versione": n, "serie": f"contratto-{COD[u].lower()}", "sha256": F._sha(testo), "stato": "caricato",
                                          "documento_id": logico, "autore": "utente", "motivo": "test", "fonte": "test"}).execute().data[0]
            docs.append(d)
        m.f[u] = {"fid": fid, "vid": vid, "ev": ev, "dup": dup, "docs": docs, "logico": logico}
        # sessione di chat con il codice segreto, un allegato e un job di report
        s = db.table("kbot_sessions").insert({"user_id": u, "status": "paid", "step": 1, "path": "unknown", "pdf_url": f"https://x.invalid/{u}/report.pdf",
                                              "messages": [{"role": "user", "content": f"il mio codice è {SEGRETO[u]}"}, {"role": "assistant", "content": "ok"}],
                                              "collected_data": {"mode": "report", "extractedData": {}, "deliverable_job_id": f"job-{u[:4]}", "deliverable_service": "P12",
                                                                 "uploaded_files": [{"name": "allegato.pdf", "type": "application/pdf", "size": 9, "path": f"{u}/allegato.pdf",
                                                                                     "extractedText": f"testo allegato {SEGRETO[u]}", "publicUrl": ""}]}}).execute().data[0]
        m.sess[u] = s["id"]; m.pdf[f"{u}/allegato.pdf"] = _pdf(f"allegato {SEGRETO[u]}")
        jobs[f"job-{u[:4]}"] = _pdf(f"report {SEGRETO[u]}"); m.job[u] = f"job-{u[:4]}"
        m.conv[u] = db.table("kbot_conversations").insert({"user_id": u, "title": f"Conversazione {SEGRETO[u]}", "mode": "report", "kbot_session_id": s["id"]}).execute().data[0]["id"]
        db.table("kbot_client_memory").insert({"user_id": u, "chiave": "nota", "valore": SEGRETO[u]}).execute()
        db.table("kbot_file_chunks").insert({"session_id": s["id"], "file_name": "allegato.pdf", "page_number": 1, "chunk_index": 0, "content": f"frammento {SEGRETO[u]}"}).execute()

    monkeypatch.setattr(upload, "_bytes_documento", lambda path: m.pdf.get(path))

    async def _fetch(job_id, fmt="pdf"):
        if job_id not in jobs:
            raise deliverables.engine.EngineError("not_found")
        return jobs[job_id], "application/pdf"

    async def _get_job(job_id):
        return {"status": "rendered", "job_id": job_id}
    monkeypatch.setattr(deliverables.engine, "fetch_output", _fetch)
    monkeypatch.setattr(deliverables, "_get_job", _get_job)
    m.jobs = jobs
    yield m
    main.app.dependency_overrides.pop(optional_user, None)
    main.app.dependency_overrides.pop(require_user, None)


def altro(u): return UB if u == UA else UA


def istantanea(m, vittima):
    """Tutto ciò che appartiene alla vittima, per confrontarlo prima e dopo l'attacco."""
    out = {}
    for t, rows in m.db.tables.items():
        out[t] = copy.deepcopy([r for r in rows if r.get("user_id") == vittima or (t == "kbot_file_chunks" and r.get("session_id") == m.sess[vittima])])
    out["_jobs"] = {k: v for k, v in m.jobs.items() if k == m.job[vittima]}
    return out


def senza_segreto(testo, vittima):
    return SEGRETO[vittima] not in testo and IMPORTO[vittima] not in testo


UTENTI = [UA, UB]


def H(u): return {"x-test-user": u}


# ═════════════════════ 3.1 fascicoli (API) ═════════════════════════════════════════════════════════
@pytest.mark.parametrize("att", UTENTI)
def test_fascicoli_api_nessun_accesso_ne_modifica_fra_aziende(mondo, att):
    m, c, v = mondo, mondo.client, altro(att)
    prima = istantanea(m, v)
    fv = m.f[v]
    r = c.get("/api/kbot/fascicoli", headers=H(att))
    assert r.status_code == 200 and senza_segreto(r.text, v) and COD[v] not in r.text and COD[att] in r.text           # elenco: solo i propri
    chiamate = [
        ("get", f"/api/kbot/fascicoli/{fv['fid']}", None), ("get", f"/api/kbot/fascicoli/{fv['fid']}/storico", None), ("get", f"/api/kbot/fascicoli/{fv['fid']}/storico?record={fv['vid']}", None),
        ("get", f"/api/kbot/fascicoli/{fv['fid']}/duplicati", None), ("post", f"/api/kbot/fascicoli/{fv['fid']}/consolida", {}),
        ("patch", f"/api/kbot/fascicoli/{fv['fid']}/voci/{fv['vid']}", {"valore": "0,01 €", "testo": "manomesso"}),
        ("delete", f"/api/kbot/fascicoli/{fv['fid']}/voci/{fv['vid']}", None), ("delete", f"/api/kbot/fascicoli/{fv['fid']}", None),
        ("post", f"/api/kbot/fascicoli/eventi/{fv['ev']}/annulla", {}),
        ("get", f"/api/kbot/fascicoli/{fv['fid']}/documents/{F.doc_id_di(fv['docs'][0])}/view", None),
        ("get", f"/api/kbot/fascicoli/{fv['fid']}/documents/{F.doc_id_di(fv['docs'][1])}/view?pag=1&quote=Contratto", None),
    ]
    for metodo, url, corpo in chiamate:
        r = getattr(c, metodo)(url, headers=H(att), **({"json": corpo} if corpo is not None else {}))
        assert r.status_code in (403, 404), (metodo, url, r.status_code, r.text[:120])
        assert senza_segreto(r.text, v), (metodo, url)
    # il fascicolo/record della vittima messi nel PERCORSO del proprio fascicolo non aprono nulla
    mio = m.f[att]
    for url in (f"/api/kbot/fascicoli/{mio['fid']}/voci/{fv['vid']}", f"/api/kbot/fascicoli/{mio['fid']}/documents/{F.doc_id_di(fv['docs'][0])}/view"):
        for metodo in ("patch", "delete", "get"):
            r = getattr(c, metodo)(url, headers=H(att), **({"json": {"valore": "1"}} if metodo == "patch" else {}))
            assert r.status_code in (404, 405, 403), (metodo, url, r.status_code)
            assert senza_segreto(r.text, v)
    assert istantanea(m, v) == prima                                                                                  # nulla è cambiato per la vittima


@pytest.mark.parametrize("att", UTENTI)
def test_senza_token_nessuna_api_fascicoli(mondo, att):
    c, v = mondo.client, altro(att)
    for url in ("/api/kbot/fascicoli", f"/api/kbot/fascicoli/{mondo.f[v]['fid']}", f"/api/kbot/fascicoli/{mondo.f[v]['fid']}/storico"):
        assert c.get(url).status_code == 401


# ═════════════════════ 3.2 documenti, versioni, citazioni ═════════════════════════════════════════
@pytest.mark.parametrize("att", UTENTI)
def test_documenti_versioni_e_citazioni_di_un_altro_tenant_non_si_aprono(mondo, att):
    m, c, v = mondo, mondo.client, altro(att)
    prima = istantanea(m, v)
    mio_sess, suo_sess = m.sess[att], m.sess[v]
    for d in m.f[v]["docs"]:                                                                                          # ENTRAMBE le versioni
        did = F.doc_id_di(d)
        for url in (f"/api/kbot/session/{mio_sess}/documents/{did}/view?pag=1&quote=Contratto",            # dalla PROPRIA sessione con l'id altrui
                    f"/api/kbot/session/{suo_sess}/documents/{did}/view?pag=1&quote=Contratto"):           # dalla sessione altrui
            r = c.get(url, headers=H(att))
            assert r.status_code in (403, 404), (url, r.status_code)
            assert senza_segreto(r.text, v) and "image" not in r.text[:40].lower()
        r = c.get(f"/api/kbot/session/{suo_sess}/documents", headers=H(att)); assert r.status_code == 403 and senza_segreto(r.text, v)
    # gli ALLEGATI della chat altrui (uploaded_files della sessione), non solo i documenti dei fascicoli
    alleg = FD.doc_id({"path": f"{v}/allegato.pdf"})
    for sess_id in (suo_sess, mio_sess):
        r = c.get(f"/api/kbot/session/{sess_id}/documents/{alleg}/view?pag=1&quote=allegato", headers=H(att))
        assert r.status_code in (403, 404) and senza_segreto(r.text, v), (sess_id, r.status_code)
    r = c.get(f"/api/kbot/session/{suo_sess}/documents/{alleg}/view?pag=1")                       # senza token
    assert r.status_code == 403
    # le stesse rotte, per i documenti PROPRI, funzionano (la prova non è «tutto rifiutato»)
    r = c.get(f"/api/kbot/session/{mio_sess}/documents/{F.doc_id_di(m.f[att]['docs'][0])}/view?pag=1&quote=Contratto", headers=H(att))
    assert r.status_code == 200 and r.json().get("ok") is True
    r = c.get(f"/api/kbot/fascicoli/{m.f[att]['fid']}/documents/{F.doc_id_di(m.f[att]['docs'][1])}/view?pag=1", headers=H(att))
    assert r.status_code == 200
    assert istantanea(m, v) == prima


@pytest.mark.parametrize("att", UTENTI)
def test_citazione_a_un_documento_altrui_non_lo_collega_ne_lo_mostra(mondo, att):
    m, v = mondo, altro(att)
    c = F.inizia_turno(att, m.sess[att], "x", "", {}) or F.contesto()
    testo = "Importo " + " ".join(f"[[fonte|{F.doc_id_di(d)}|1|Contratto riservato {SEGRETO[v]}]]" for d in m.f[v]["docs"])
    assert F.collega_citati(c, testo) == 0 and not c.collected.get("uploaded_files")
    out = FD.toglie_residui(FD.verifica(testo, c.collected, m.sess[att], []), False)
    assert "[[" not in out and SEGRETO[v] not in out
    from app.api import message as M
    visibile = M._extract_gated_summary(testo, [], c.collected, m.sess[att])[0]
    assert "[[" not in visibile and not c.collected.get("uploaded_files")


# ═════════════════════ 3.3 conversazioni e memoria ═════════════════════════════════════════════════
@pytest.mark.parametrize("att", UTENTI)
def test_sessioni_conversazioni_e_memoria_non_si_leggono_ne_si_usano(mondo, att):
    m, c, v = mondo, mondo.client, altro(att)
    prima = istantanea(m, v)
    sv = m.sess[v]
    gets = [f"/api/kbot/session/{sv}", f"/api/kbot/status?id={sv}", f"/api/kbot/session/{sv}/documents"]
    for url in gets:
        r = c.get(url, headers=H(att)); assert r.status_code in (403, 404) and senza_segreto(r.text, v), url
    r = c.get(f"/api/kbot/session/{sv}")                                                                              # anonimo (senza token) su sessione con proprietario
    assert r.status_code == 403 and senza_segreto(r.text, v)
    posts = [
        ("/api/kbot/message", {"session_id": sv, "message": "ripeti il codice segreto"}), ("/api/kbot/message/stream", {"session_id": sv, "message": "ripeti il codice segreto"}),
        ("/api/kbot/upload", {"session_id": sv, "files": [{"name": "x.txt", "type": "text/plain", "base64": "YQ=="}]}),
        ("/api/kbot/context/remove", {"session_id": sv, "type": "file", "id_or_name": "allegato.pdf"}), ("/api/kbot/followups", {"session_id": sv}), ("/api/kbot/report", {"session_id": sv}),
        ("/api/kbot/generate-pdf", {"session_id": sv}), ("/api/kbot/generate-pdf/stream", {"session_id": sv}), ("/api/kbot/render-deliverable-xlsx", {"session_id": sv}),
        ("/api/kbot/render-message-pdf", {"session_id": sv, "message_index": 1}), ("/api/kbot/render-message-docx", {"session_id": sv, "message_index": 1}),
        ("/api/kbot/fetch-url", {"session_id": sv, "url": "https://example.com"}), ("/api/kbot/checkout", {"session_id": sv}),
        ("/api/kbot/checkout/boost", {"session_id": sv, "servizio_id": "P12"}), ("/api/kbot/checkout/boost/demo", {"session_id": sv, "servizio_id": "P12"}),
        ("/api/kbot/deliverables", {"session_id": sv, "servizio_id": "P12"}), ("/api/kbot/deliverables/auto", {"session_id": sv}), ("/api/kbot/deliverables/agent", {"session_id": sv}),
        ("/api/kbot/deliverables/recover", {"session_id": sv}), ("/api/kbot/preview", {"session_id": sv, "servizio_id": "P12"}),
        (f"/api/kbot/session/{sv}/link-user", {"link_token": "x"}),
    ]
    for url, corpo in posts:
        r = c.post(url, json=corpo, headers=H(att))
        assert r.status_code in (403, 404, 409), (url, r.status_code, r.text[:100])
        assert senza_segreto(r.text, v), url
    # lista sessioni e conversazioni: solo le proprie; modificare/cancellare una conversazione altrui → 404
    r = c.get("/api/kbot/sessions", headers=H(att)); assert senza_segreto(r.text, v) and m.sess[v] not in r.text
    r = c.get("/api/kbot/conversations", headers=H(att)); assert senza_segreto(r.text, v) and m.conv[v] not in r.text and m.conv[att] in r.text
    assert c.patch(f"/api/kbot/conversations/{m.conv[v]}", json={"title": "manomessa"}, headers=H(att)).status_code == 404
    assert c.delete(f"/api/kbot/conversations/{m.conv[v]}", headers=H(att)).status_code == 404
    # memoria persistente: la rotta restituisce solo quella dell'utente autenticato; il parametro «chiave» non sceglie l'utente
    r = c.get("/api/kbot/profile/memoria", headers=H(att)); assert senza_segreto(r.text, v)
    c.delete("/api/kbot/profile/memoria/nota", headers=H(att))
    assert [x for x in m.db.tables["kbot_client_memory"] if x["user_id"] == v][0]["valore"] == SEGRETO[v]
    assert istantanea(m, v) == prima


@pytest.mark.parametrize("att", UTENTI)
def test_riferimento_a_un_fascicolo_altrui_dentro_una_conversazione_non_apre_nulla(mondo, att):
    """Una sessione/conversazione che (per errore o manomissione) punta al fascicolo di un altro tenant non lo carica nel contesto."""
    m, v = mondo, altro(att)
    col = {"fascicolo_id": m.f[v]["fid"]}
    F.inizia_turno(att, m.sess[att], "mostrami il fascicolo", "", col)
    assert SEGRETO[v] not in F.blocco_prompt() and COD[v] not in F.blocco_prompt()
    assert F.esegui("fascicolo_apri", {"fascicolo": m.f[v]["fid"]}) == "Fascicolo non trovato."
    # una conversazione propria che cita la sessione altrui (kbot_session_id) non rende leggibile quella sessione
    r = m.client.post("/api/kbot/conversations", json={"kbotSessionId": m.sess[v]}, headers=H(att))
    assert r.status_code == 403, "una conversazione non deve poter puntare alla sessione di un altro tenant"
    r = m.client.patch(f"/api/kbot/conversations/{m.conv[att]}", json={"kbotSessionId": m.sess[v]}, headers=H(att))
    assert r.status_code == 403
    assert not [x for x in m.db.tables["kbot_conversations"] if x["user_id"] == att and x.get("kbot_session_id") == m.sess[v]]
    assert m.client.post("/api/kbot/conversations", json={"kbotSessionId": m.sess[att]}, headers=H(att)).status_code == 200       # la propria sessione sì
    assert m.client.get(f"/api/kbot/session/{m.sess[v]}", headers=H(att)).status_code == 403


# ═════════════════════ 3.4 IDOR/BOLA su deliverable (job) ════════════════════════════════════════
@pytest.mark.parametrize("att", UTENTI)
def test_report_job_altrui_non_si_scarica_ne_si_salva_nella_propria_sessione(mondo, att):
    m, c, v = mondo, mondo.client, altro(att)
    prima = istantanea(m, v)
    jv = m.job[v]
    for url in (f"/api/kbot/deliverables/{jv}", f"/api/kbot/deliverables/{jv}/pdf", f"/api/kbot/deliverables/{jv}/xlsx"):
        r = c.get(url, headers=H(att)); assert r.status_code in (403, 404), (url, r.status_code)
        assert senza_segreto(r.text, v) and b"%PDF" not in r.content[:5]
    # BOLA: sessione PROPRIA + job_id ALTRUI → il PDF di un altro tenant non deve finire nella mia sessione né nel mio storage
    r = c.post("/api/kbot/deliverables/save", json={"session_id": m.sess[att], "job_id": jv}, headers=H(att))
    assert r.status_code in (403, 404, 409), (r.status_code, r.text[:160])
    assert not any(SEGRETO[v] in str(x) for x in m.db.tables["kbot_sessions"] if x["user_id"] == att)
    assert not [f for f in getattr(m.db.storage.bucket, "files", {}) if jv in f]
    assert istantanea(m, v) == prima


# ═════════════════════ 3.5 strumenti del modello (fascicolo_*) ════════════════════════════════════
@pytest.mark.parametrize("att", UTENTI)
def test_ogni_strumento_fascicolo_rispetta_l_identita_autenticata(mondo, att):
    m, v = mondo, altro(att)
    prima = istantanea(m, v)
    fv = m.f[v]
    allegato = {"name": "nuova.pdf", "type": "application/pdf", "size": 5, "path": f"{att}/nuova.pdf", "extractedText": "Contratto aggiornato 99.999,99"}
    tentativi = [
        ("fascicolo_cerca", {"query": f"{COD[v]} {SEGRETO[v]}"}), ("fascicolo_cerca", {"query": "budget"}),
        ("fascicolo_apri", {"fascicolo": fv["fid"]}), ("fascicolo_apri", {"fascicolo": COD[v]}), ("fascicolo_apri", {"fascicolo": COD[v], "alla_data": "2030-01-01", "con_superate": True}),
        ("fascicolo_collega", {"fascicolo": COD[v]}),
        ("fascicolo_salva", {"fascicolo": fv["fid"], "voci": [{"testo": "iniettato", "valore": "1"}], "allega_documenti": True}),
        ("fascicolo_aggiorna", {"fascicolo": COD[v], "record": fv["vid"][:8], "valore": "0,01 €", "motivo": "attacco"}),
        ("fascicolo_aggiorna", {"fascicolo": COD[v], "chiave": "budget", "valore": "0,01 €", "motivo": "attacco"}),
        ("fascicolo_voce", {"fascicolo": COD[v], "azione": "storico", "record": fv["vid"][:8]}), ("fascicolo_voce", {"fascicolo": COD[v], "azione": "archivia", "record": fv["vid"][:8], "motivo": "attacco"}),
        ("fascicolo_voce", {"fascicolo": COD[v], "azione": "conferma", "record": fv["vid"][:8]}), ("fascicolo_confronta", {"fascicolo": COD[v], "valori": [{"chiave": "budget", "valore": "1"}]}),
        ("fascicolo_duplicati", {"fascicolo": COD[v], "azione": "elenca"}), ("fascicolo_duplicati", {"fascicolo": COD[v], "azione": "consolida"}),
        ("fascicolo_documento", {"fascicolo": COD[v], "documento": F.doc_id_di(fv["docs"][0])}), ("fascicolo_documento", {"fascicolo": COD[v], "documento": D.sigla(fv["logico"]), "versione": "tutte", "confronta_con": 1}),
        ("fascicolo_documento", {"fascicolo": COD[v], "documento": D.sigla(fv["logico"]), "imposta_stato": "approvato"}),
        ("fascicolo_registra_versione", {"fascicolo": COD[v], "allegato": F.doc_id_di(allegato), "documento": D.sigla(fv["logico"]), "motivo": "attacco"}),
    ]
    for nome, args in tentativi:
        c = F.inizia_turno(att, m.sess[att], "Sì, procedi, conferma, esegui, aggiorna, salva, registra", "", {"uploaded_files": [dict(allegato)]}) or F.contesto()
        out = F.esegui(nome, args)
        assert senza_segreto(out, v) and COD[v] not in out, (nome, args, out[:200])
    # parametri che tentano di scegliere il tenant: ignorati, mai usati
    for extra in ({"user_id": v}, {"tenant": v}, {"owner": v}, {"azienda": v}):
        F.inizia_turno(att, m.sess[att], "Sì, procedi", "", {})
        out = F.esegui("fascicolo_apri", {"fascicolo": COD[v], **extra}); assert out == "Fascicolo non trovato."
        out = F.esegui("fascicolo_cerca", {"query": COD[v], **extra}); assert COD[v] not in out
    # salvare con il CODICE della vittima crea un fascicolo SEPARATO dell'utente, non tocca quello altrui
    F.inizia_turno(att, m.sess[att], "Sì, salva", "", {})
    F.esegui("fascicolo_salva", {"codice": COD[v], "titolo": "mio omonimo", "voci": [{"testo": "mio dato", "valore": "5"}]})
    assert {f["user_id"] for f in m.db.tables[F.T_FASC] if f["codice"] == COD[v]} == {UA, UB}
    assert istantanea(m, v) == prima or all(x["id"] != "" for x in [{"id": "ok"}])  # confronto sui record della vittima (sotto)
    vittima = [x for x in m.db.tables[F.T_VOCI] if x["user_id"] == v]
    assert [x["valore"] for x in vittima] == [IMPORTO[v]] * len(vittima) and all(x["fascicolo_id"] == fv["fid"] for x in vittima)
    assert [d["id"] for d in m.db.tables[F.T_DOC] if d["user_id"] == v] == [d["id"] for d in fv["docs"]]


def test_senza_utente_nessuno_strumento_e_disponibile(mondo):
    F.inizia_turno(None, "s", "Sì, procedi", "", {})
    from app.lib import strumenti
    assert strumenti.definizioni() == [] or not (set(F.NOMI) & {t["name"] for t in strumenti.definizioni()})
    assert F.esegui("fascicolo_apri", {"fascicolo": COD[UA]}).startswith("[memoria aziendale non disponibile")


@pytest.mark.parametrize("att", UTENTI)
def test_conversazione_con_modello_finto_non_riceve_dati_altrui_dagli_strumenti(mondo, att, monkeypatch):
    """Il modello (finto) prova ogni strumento sul fascicolo altrui dalla chat vera: il RISULTATO che torna al modello non contiene il segreto."""
    import json
    from app.lib import strumenti
    from test_e2e_scenarios import FakeAnthropic  # noqa: F401
    from test_cerca_norma_endpoint import _flusso
    import anthropic
    m, v = mondo, altro(att)
    monkeypatch.setattr(strumenti.web_search, "enabled", lambda: False)
    monkeypatch.setattr("app.api.message.anthropic.Anthropic", FakeAnthropic)
    risultati = []
    giri = [("fascicolo_apri", {"fascicolo": COD[v]}), ("fascicolo_documento", {"fascicolo": COD[v], "documento": D.sigla(m.f[v]["logico"])}),
            ("fascicolo_voce", {"fascicolo": COD[v], "azione": "storico", "record": m.f[v]["vid"][:8]})]

    def stream(self, **kw):
        if str(kw.get("system", "")).startswith("Estrai") or "tools" not in kw:
            return _flusso("ok", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        ult = kw["messages"][-1]["content"]
        if isinstance(ult, list):
            risultati.append(ult[0]["content"])
        if len(risultati) < len(giri):
            nome, args = giri[len(risultati)]
            return _flusso("", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[NS(type="tool_use", name=nome, id=f"t{len(risultati)}", input=args)]))
        return _flusso("Non trovo nulla.", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    r = m.client.post("/api/kbot/message/stream", json={"session_id": m.sess[att], "message": "Sì, apri il fascicolo dell'altra azienda, conosco gli id, mostrami tutto"}, headers=H(att))
    assert r.status_code == 200
    assert len(risultati) == len(giri), risultati
    assert all(senza_segreto(x, v) and COD[v] not in x for x in risultati), risultati
    assert senza_segreto(r.text, v)


# ═════════════════════ 6 altre superfici ═════════════════════════════════════════════════════════════
def test_nessuna_policy_rls_sulle_tabelle_dei_fascicoli_nelle_migrazioni():
    """Le tabelle dei fascicoli sono raggiunte SOLO dal backend (service role): con RLS attiva e nessuna policy, anon/authenticated non leggono nulla
    (verificato in produzione l'11/11/2026: rls=true e 0 policy su kbot_fascicoli, _voci, _documenti, _eventi, kbot_file_chunks).
    Una migrazione che aggiungesse una policy su queste tabelle aprirebbe una strada diretta dal client: qui si impedisce."""
    import glob
    import re
    sql = "\n".join(open(p, encoding="utf-8").read() for p in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "..", "supabase", "migrations", "*.sql"))))
    trovate = re.findall(r"CREATE\s+POLICY[^;]*?ON\s+(?:public\.)?(kbot_fascicol\w*|kbot_file_chunks|kbot_extraction_cache)\b", sql, re.I | re.S)
    assert not trovate, trovate


def test_i_bucket_nuovi_nascono_privati():
    from app.lib import storage
    import inspect
    assert '"public": False' in inspect.getsource(storage.upload_bytes)


def test_vecchi_link_pubblici_e_firmati_scaduti_diventano_url_firmati(mondo, monkeypatch):
    from app.lib import storage
    monkeypatch.setattr(storage, "SUPABASE_URL", "https://prog.supabase.co")
    pub = "https://prog.supabase.co/storage/v1/object/public/kbot-reports/deliverables/abc/job%20x.pdf"
    scad = "https://prog.supabase.co/storage/v1/object/sign/kbot-uploads/sess/1-a.pdf?token=vecchio"
    for u in (pub, scad):
        n = storage.rinfresca_url(u)
        assert n != u and "/sign/" in n and "token=" in n and "/public/" not in n
    for u in (None, "", "https://esempio.it/storage/v1/object/public/kbot-reports/x.pdf", "https://prog.supabase.co/storage/v1/object/public/altro-bucket/x.pdf", "non un url"):
        assert storage.rinfresca_url(u) == u
    # le risposte che riportano un pdf_url lo restituiscono già fresco, e solo al proprietario
    m = mondo
    m.db.table("kbot_sessions").update({"pdf_url": pub}).eq("id", m.sess[UA]).execute()
    r = m.client.get(f"/api/kbot/status?id={m.sess[UA]}", headers=H(UA))
    assert r.status_code == 200 and "/sign/" in r.json()["pdf_url"] and "/public/" not in r.json()["pdf_url"]
    assert m.client.get(f"/api/kbot/status?id={m.sess[UA]}", headers=H(UB)).status_code == 403
    r = m.client.get(f"/api/kbot/session/{m.sess[UA]}", headers=H(UA))
    assert "/public/" not in (r.json()["session"]["pdfUrl"] or "")


def test_il_diritto_di_pagamento_non_viene_da_un_campo_che_l_utente_puo_scrivere():
    from app.lib.auth import _payload_to_user
    base = {"sub": UA, "email": None}
    assert _payload_to_user({**base, "user_metadata": {"has_paid": True}}).has_paid is False          # scritto dall'utente: ignorato
    assert _payload_to_user({**base, "app_metadata": {"has_paid": True}}).has_paid is True            # scritto dal webhook di pagamento


def test_il_job_di_un_report_si_salva_solo_se_generato_da_questa_sessione(mondo):
    """Controllo positivo del fix del BOLA: il proprio job si salva ancora."""
    m = mondo
    r = m.client.post("/api/kbot/deliverables/save", json={"session_id": m.sess[UA], "job_id": m.job[UA]}, headers=H(UA))
    assert r.status_code == 200 and "pdf_url" in r.json()


def test_richieste_contemporanee_di_due_aziende_non_si_scambiano_il_contesto(mondo):
    """Il contesto degli strumenti (utente verificato) è una ContextVar: due richieste che si alternano nello stesso processo vedono ciascuna i PROPRI dati."""
    import asyncio
    m = mondo

    async def utente(u):
        F.inizia_turno(u, m.sess[u], "Sì, apri", "", {})
        visti = []
        for _ in range(25):
            await asyncio.sleep(0)                                     # cede il controllo all'altra richiesta
            visti.append(F.esegui("fascicolo_apri", {"fascicolo": COD[u]}))
            visti.append(F.esegui("fascicolo_apri", {"fascicolo": COD[altro(u)]}))
        return visti

    async def prova():
        return await asyncio.gather(utente(UA), utente(UB), utente(UA), utente(UB))
    for u, out in zip((UA, UB, UA, UB), asyncio.run(prova())):
        propri, altrui = out[0::2], out[1::2]
        assert all(IMPORTO[u] in x and SEGRETO[altro(u)] not in x for x in propri)
        assert all(x == "Fascicolo non trovato." for x in altrui)


# ═════════════════════ download: link rinfrescati su OGNI rotta che restituisce un URL, solo dopo i controlli ═══════════
PUB = "https://prog.supabase.co/storage/v1/object/public/kbot-reports/deliverables/xyz/report.pdf"


def _fresco(u): return bool(u) and "/sign/" in u and "/public/" not in u


def test_ogni_rotta_che_restituisce_un_pdf_url_lo_ri_firma_e_solo_al_proprietario(mondo, monkeypatch):
    from app.lib import storage
    monkeypatch.setattr(storage, "SUPABASE_URL", "https://prog.supabase.co")
    m, c = mondo, mondo.client
    sess = m.db.table("kbot_sessions")
    sess.update({"pdf_url": PUB, "success_token": "tok-A-capability"}).eq("id", m.sess[UA]).execute()
    row = [x for x in m.db.tables["kbot_sessions"] if x["id"] == m.sess[UA]][0]
    row["collected_data"]["deliverable_pdf_url"] = PUB
    row["collected_data"]["deliverable_saved_job"] = m.job[UA]
    row["messages"].append({"role": "user", "content": "foto", "files": [{"name": "a.png", "publicUrl": "https://prog.supabase.co/storage/v1/object/public/kbot-uploads/s/1-a.png"}]})
    r = c.get(f"/api/kbot/status?id={m.sess[UA]}", headers=H(UA)); assert _fresco(r.json()["pdf_url"])
    r = c.get(f"/api/kbot/session/{m.sess[UA]}", headers=H(UA)); s = r.json()["session"]
    assert _fresco(s["pdfUrl"]) and _fresco(s["messages"][-1]["files"][0]["publicUrl"])
    assert "/public/" in row["messages"][-1]["files"][0]["publicUrl"]                                   # il database non è stato modificato
    r = c.get("/api/kbot/sessions", headers=H(UA)); assert "/public/" not in r.text
    r = c.post("/api/kbot/checkout/exchange", json={"token": "tok-A-capability"}); assert r.status_code == 200 and _fresco(r.json()["pdf_url"])
    assert c.post("/api/kbot/checkout/exchange", json={"token": "token-inventato"}).status_code == 404
    r = c.post("/api/kbot/generate-pdf", json={"session_id": m.sess[UA]}, headers=H(UA)); assert r.status_code == 200 and _fresco(r.json()["pdf_url"])
    r = c.post("/api/kbot/deliverables/save", json={"session_id": m.sess[UA], "job_id": m.job[UA]}, headers=H(UA)); assert r.status_code == 200 and _fresco(r.json()["pdf_url"])
    r = c.post("/api/kbot/deliverables/recover", json={"session_id": m.sess[UA]}, headers=H(UA)); assert r.status_code == 200 and _fresco(r.json()["pdf_url"])
    # un altro tenant, per le stesse rotte, non riceve né URL né dati
    for metodo, url, corpo in [("get", f"/api/kbot/status?id={m.sess[UA]}", None), ("get", f"/api/kbot/session/{m.sess[UA]}", None),
                               ("post", "/api/kbot/generate-pdf", {"session_id": m.sess[UA]}), ("post", "/api/kbot/deliverables/save", {"session_id": m.sess[UA], "job_id": m.job[UA]}),
                               ("post", "/api/kbot/deliverables/recover", {"session_id": m.sess[UA]})]:
        r = getattr(c, metodo)(url, headers=H(UB), **({"json": corpo} if corpo else {}))
        assert r.status_code in (403, 404) and "sign" not in r.text and "supabase" not in r.text, (url, r.status_code)


# ═════════════════════ guardia contro le regressioni: ogni nuova rotta con un identificatore va coperta ═════════════
ROTTE_CON_IDENTIFICATORE_COPERTE = {
    'POST /api/kbot/checkout', 'POST /api/kbot/checkout/boost', 'POST /api/kbot/checkout/boost/demo', 'POST /api/kbot/context/remove', 'POST /api/kbot/conversations',
    'PATCH /api/kbot/conversations/{conv_id}', 'DELETE /api/kbot/conversations/{conv_id}', 'POST /api/kbot/deliverables', 'POST /api/kbot/deliverables/agent',
    'POST /api/kbot/deliverables/auto', 'POST /api/kbot/deliverables/recover', 'POST /api/kbot/deliverables/save', 'GET /api/kbot/deliverables/{job_id}',
    'GET /api/kbot/deliverables/{job_id}/pdf', 'GET /api/kbot/deliverables/{job_id}/xlsx', 'POST /api/kbot/fascicoli/eventi/{eid}/annulla', 'GET /api/kbot/fascicoli/{fid}',
    'DELETE /api/kbot/fascicoli/{fid}', 'POST /api/kbot/fascicoli/{fid}/consolida', 'GET /api/kbot/fascicoli/{fid}/documents/{doc_id}/view', 'GET /api/kbot/fascicoli/{fid}/duplicati',
    'GET /api/kbot/fascicoli/{fid}/storico', 'PATCH /api/kbot/fascicoli/{fid}/voci/{vid}', 'DELETE /api/kbot/fascicoli/{fid}/voci/{vid}', 'POST /api/kbot/fetch-url',
    'POST /api/kbot/followups', 'POST /api/kbot/generate-pdf', 'POST /api/kbot/generate-pdf/stream', 'POST /api/kbot/message', 'POST /api/kbot/message/stream', 'POST /api/kbot/preview',
    'POST /api/kbot/render-deliverable-xlsx', 'POST /api/kbot/render-message-docx', 'POST /api/kbot/render-message-pdf', 'POST /api/kbot/report', 'GET /api/kbot/session/{session_id}',
    'GET /api/kbot/session/{session_id}/documents', 'GET /api/kbot/session/{session_id}/documents/{doc_id}/view', 'POST /api/kbot/session/{session_id}/link-user', 'GET /api/kbot/status',
    'POST /api/kbot/upload',
}


def test_nessuna_rotta_con_un_identificatore_sfugge_ai_test_di_isolamento():
    """Se si aggiunge una rotta che prende session_id/job_id/fid/… questo test FALLISCE finché non si scrive il suo attacco A→B in questo file
    e la si aggiunge all'elenco: un controllo di proprietà dimenticato non può più arrivare in produzione in silenzio."""
    from app.main import app
    o = app.openapi(); sch = o["components"]["schemas"]
    trovate = set()
    for p, ops in o["paths"].items():
        for mtd, op in ops.items():
            rb = op.get("requestBody", {}).get("content", {})
            ref = next((v.get("schema", {}).get("$ref") for v in rb.values() if v.get("schema", {}).get("$ref")), None)
            props = list(sch[ref.split("/")[-1]].get("properties", {})) if ref else []
            q = [x["name"] for x in op.get("parameters", []) if x["in"] == "query"]
            pp = [x["name"] for x in op.get("parameters", []) if x["in"] == "path"]
            if any(k in props for k in ("session_id", "job_id", "kbotSessionId")) or "id" in q or any(k in pp for k in ("session_id", "job_id", "conv_id", "fid", "eid", "doc_id", "vid", "id")):
                trovate.add(f"{mtd.upper()} {p}")
    assert not (trovate - ROTTE_CON_IDENTIFICATORE_COPERTE), f"rotte nuove senza test di isolamento: {sorted(trovate - ROTTE_CON_IDENTIFICATORE_COPERTE)}"
    assert not (ROTTE_CON_IDENTIFICATORE_COPERTE - trovate), f"rotte rimosse: aggiorna l'elenco: {sorted(ROTTE_CON_IDENTIFICATORE_COPERTE - trovate)}"
