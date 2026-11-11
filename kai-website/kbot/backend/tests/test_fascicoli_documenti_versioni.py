"""Test 30B: registrare una revisione documentale (v2 dello stesso documento logico) attraverso gli strumenti e la chat.

Documento logico ≠ versione; versioni conservate; idempotenza; confronto; citazioni alla versione esatta; nessun marcatore grezzo;
registrare NON verifica i contenuti e NON tocca i record economici."""
import os
import sys
import uuid
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import fascicoli as F, fascicoli_documenti as D, fonti_documenti as FD, strumenti  # noqa: E402
from test_fascicoli import _DB, ctx  # noqa: E402

COD = "TEST-DOC-VERSIONI-01"
T1 = "Riepilogo commessa UM-26-041\nImponibile contrattuale 15.250,00 euro\nResiduo da liquidare 8.850,00 euro\nScadenza saldo 30/11/2026"
T2 = "Riepilogo commessa UM-26-041\nImponibile contrattuale 15.650,00 euro\nResiduo da liquidare 9.250,00 euro\nScadenza saldo 30/11/2026\nVariante n. 2 approvata dal committente"


def allegato(nome, path, testo, **k):
    return {"name": nome, "type": "application/pdf", "size": 100, "path": path, "extractedText": testo, **k}


@pytest.fixture
def db(monkeypatch):
    D._SCHEMA.clear()
    d = _DB(); monkeypatch.setattr(F, "_db", lambda: d); return d


def apri_fascicolo(db, user="A"):
    ctx(user, utente="Sì, apri il fascicolo di prova")
    F.esegui("fascicolo_salva", {"codice": COD, "titolo": "Fascicolo fittizio isolato", "voci": [
        {"tipo": "dato", "testo": "Imponibile contrattuale", "chiave": "imponibile", "valore": "15.250 €", "unita": "EUR"}]})
    return db.d[F.T_FASC][-1]["id"]


def registra(file, documento="", motivo="revisione del riepilogo", user="A", sess="s1", utente="Sì, registra l'allegato", extra=None, **k):
    col = {"uploaded_files": [dict(file)]}                           # copia: la registrazione annota l'allegato della conversazione
    ctx(user, utente=utente, collected=col, sess=sess)
    args = {"fascicolo": COD, "allegato": F.doc_id_di(file), "motivo": motivo, **({"documento": documento} if documento else {}), **k}
    return F.esegui("fascicolo_registra_versione", {**args, **(extra or {})}), col


V1 = allegato("KBot_Test_04_Riepilogo_Commessa.pdf", "s1/1-v1.pdf", T1)
V2 = allegato("KBot_Test_04_Riepilogo_Commessa_v2.pdf", "s2/2-v2.pdf", T2)


def due_versioni(db):
    apri_fascicolo(db)
    o1, _ = registra(V1, nuovo_documento=True)
    assert o1.startswith("ESITO: ok"), o1
    logico = D.sigla(db.d[F.T_DOC][0]["documento_id"])
    o2, col = registra(V2, documento=logico, sess="s2", motivo="nuova stima del committente")
    assert o2.startswith("ESITO: ok") and "idempotente" not in o2, o2
    return logico, o2, col


# ── registrazione ────────────────────────────────────────────────────────────────────────────────────
def test_v1_poi_v2_stesso_documento_logico_versioni_conservate_e_metadati(db):
    logico, o2, col = due_versioni(db)
    dd = db.d[F.T_DOC]
    assert len(dd) == 2 and dd[0]["documento_id"] == dd[1]["documento_id"]                      # UN documento logico
    assert [d["versione"] for d in dd] == [1, 2] and dd[1]["sostituisce_doc"] == dd[0]["id"]
    assert dd[0]["id"] != dd[1]["id"] and F.doc_id_di(dd[0]) != F.doc_id_di(dd[1])             # identificativo di versione ≠ del documento
    for d in dd:
        assert d["stato"] == "caricato" and d["autore"] == "utente" and d["created_at"] and d["fonte"].startswith("chat:") and d["motivo"]
    assert dd[1]["motivo"] == "nuova stima del committente" and dd[1]["fonte"] == "chat:s2:KBot_Test_04_Riepilogo_Commessa_v2.pdf"
    assert dd[0]["extracted_text"] == T1 and dd[0]["path"] == "s1/1-v1.pdf"                      # la v1 resta intera
    assert "v2 del documento " + logico in o2 and "NESSUN record" in o2 and "verificati né approvati" in o2
    assert f"[doc:{F.doc_id_di(dd[0])}]" in o2 and f"[doc:{F.doc_id_di(dd[1])}]" in o2          # l'esito rilegge e riporta TUTTE le versioni
    ev = [e for e in db.d["kbot_fascicolo_eventi"] if e["azione"] == "documento"]
    assert len(ev) == 2 and ev[1]["dopo"]["versione"] == 2 and ev[1]["motivo"] == "nuova stima del committente" and ev[1]["attore"] == "utente"
    assert col["uploaded_files"][0]["dalFascicolo"] and col["uploaded_files"][0]["versione"] == 2   # la conversazione sa che è già registrata


def test_registrare_non_tocca_i_record_ne_approva_i_contenuti(db):
    apri_fascicolo(db)
    prima = [dict(v) for v in db.d[F.T_VOCI]]
    registra(V1, nuovo_documento=True)
    logico = D.sigla(db.d[F.T_DOC][0]["documento_id"])
    registra(V2, documento=logico, sess="s2")
    assert db.d[F.T_VOCI] == prima                                                                # nessun record economico cambiato
    assert all(d["stato"] == "caricato" for d in db.d[F.T_DOC])
    assert not [e for e in db.d["kbot_fascicolo_eventi"] if e["azione"] in ("aggiorna", "sostituisce", "propone")]


def test_ripetere_il_caricamento_e_idempotente_stesso_file_o_stesso_contenuto(db):
    logico, _, _ = due_versioni(db)
    n_doc, n_ev = len(db.d[F.T_DOC]), len(db.d["kbot_fascicolo_eventi"])
    out, _ = registra(V2, documento=logico, sess="s3")                                          # stesso file
    assert out.startswith("ESITO: ok (idempotente)") and "GIÀ REGISTRATO" in out and "v2" in out
    copia = allegato("copia_rinominata.pdf", "s4/altro-percorso.pdf", T2)                       # altro nome, altro percorso, STESSO contenuto
    out, _ = registra(copia, documento=logico, sess="s4")
    assert out.startswith("ESITO: ok (idempotente)") and "stesso contenuto" in out
    out, _ = registra(copia, nuovo_documento=True, sess="s4")                                    # nemmeno come documento «nuovo»
    assert out.startswith("ESITO: ok (idempotente)")
    assert len(db.d[F.T_DOC]) == n_doc and len(db.d["kbot_fascicolo_eventi"]) == n_ev


def test_non_si_crea_un_documento_logico_indipendente_per_sbaglio(db):
    apri_fascicolo(db)
    registra(V1, nuovo_documento=True)
    out, _ = registra(V2, sess="s2")                                                             # niente `documento`, nome simile: ambiguo, nulla scritto
    assert out.startswith("ESITO: errore AMBIGUO") and "L-" in out and "nuovo_documento" in out and len(db.d[F.T_DOC]) == 1
    out, _ = registra(V2, sess="s2", nuovo_documento=True)                                        # scelta esplicita: documento diverso
    assert out.startswith("ESITO: ok") and len({d["documento_id"] for d in db.d[F.T_DOC]}) == 2


def test_errori_chiari_e_nessuna_scrittura(db):
    apri_fascicolo(db)
    out, _ = registra(V1, nuovo_documento=True, utente="cosa ne pensi di questo file?")
    assert out.startswith("ESITO: errore NON_ESEGUITO") and not db.d.get(F.T_DOC)                # senza conferma dell'utente
    out, _ = registra(V1, nuovo_documento=True, motivo="  ")
    assert "MOTIVO_MANCANTE" in out and not db.d.get(F.T_DOC)
    out, _ = registra(V1, nuovo_documento=True, extra={"allegato": "inesistente.pdf"})
    assert out.startswith("ESITO: errore ALLEGATO_NON_TROVATO") and "Allegati disponibili" in out and V1["name"] in out
    registra(V1, nuovo_documento=True)
    out, _ = registra(V2, documento="L-ffffffff", sess="s2")
    assert out.startswith("ESITO: errore DOCUMENTO_NON_TROVATO") and len(db.d[F.T_DOC]) == 1
    ctx("A", utente="Sì, registra", collected={"uploaded_files": []})
    assert "ALLEGATO_NON_TROVATO" in F.esegui("fascicolo_registra_versione", {"fascicolo": COD, "motivo": "x", "documento": "L-x"})
    # senza `allegato` e con UN solo allegato libero, lo sceglie da solo
    ctx("A", utente="Sì, registra", collected={"uploaded_files": [dict(V2)]}, sess="s2")
    assert F.esegui("fascicolo_registra_versione", {"fascicolo": COD, "motivo": "x", "documento": "L-" + db.d[F.T_DOC][0]["documento_id"].replace("-", "")[:8]}).startswith("ESITO: ok")


def test_isolamento_fra_utenti(db):
    logico, _, _ = due_versioni(db)
    ctx("B", utente="Sì, registra", collected={"uploaded_files": [dict(V1)]})
    assert F.esegui("fascicolo_registra_versione", {"fascicolo": COD, "allegato": F.doc_id_di(V1), "motivo": "x", "documento": logico}) == "Fascicolo non trovato."
    assert F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": logico}) == "Fascicolo non trovato."
    assert F.collega_citati(ctx("B", utente="x"), f"[[fonte|{F.doc_id_di(db.d[F.T_DOC][0])}|1|x]]") == 0     # le citazioni non aprono documenti altrui


def test_richieste_concorrenti_il_vincolo_univoco_non_crea_doppioni(db, monkeypatch):
    apri_fascicolo(db)
    registra(V1, nuovo_documento=True)
    logico = D.sigla(db.d[F.T_DOC][0]["documento_id"])
    originale = db.table

    class QUnico:
        def __init__(self, q): self.q = q
        def __getattr__(self, n): return getattr(self.q, n)
        def insert(self, row): self.q.insert(row); return self
        def update(self, p): self.q.update(p); return self
        def eq(self, k, v): self.q.eq(k, v); return self
        def execute(self):
            if self.q.mode == "insert" and self.q.t == F.T_DOC:                                  # un'altra richiesta ha già inserito la v2 un istante prima
                db.d[F.T_DOC].append({"id": str(uuid.uuid4()), **{**self.q.p, "versione": 2}})
                raise RuntimeError('duplicate key value violates unique constraint "kbot_fascicolo_documenti_uq_versione" (23505)')
            return self.q.execute()
    monkeypatch.setattr(db, "table", lambda t: QUnico(originale(t)))
    out, _ = registra(V2, documento=logico, sess="s2")
    assert out.startswith("ESITO: ok (idempotente)") and "concorrente" in out and len(db.d[F.T_DOC]) == 2


def test_migrazione_non_applicata_non_scrive_e_il_resto_funziona(db, monkeypatch):
    apri_fascicolo(db)
    monkeypatch.setattr(D, "schema_ok", lambda: False)
    out, _ = registra(V1, nuovo_documento=True)
    assert out.startswith("ESITO: errore MIGRAZIONE_MANCANTE") and not db.d.get(F.T_DOC)
    # salva con allega_documenti (percorso vecchio) continua a funzionare, senza le colonne nuove
    ctx("A", utente="Sì, salva anche il documento", collected={"uploaded_files": [dict(V1)]})
    F.esegui("fascicolo_salva", {"fascicolo": COD, "allega_documenti": True})
    assert len(db.d[F.T_DOC]) == 1 and "documento_id" not in db.d[F.T_DOC][0]


def test_documenti_di_prima_della_migrazione_si_versionano_senza_modificarli(db):
    """Come in produzione: v1 salvata dalla 007, senza documento_id, serie, sha256."""
    fid = apri_fascicolo(db)
    v1 = db.table(F.T_DOC).insert({"fascicolo_id": fid, "user_id": "A", "name": V1["name"], "type": "application/pdf", "size": 9, "path": V1["path"],
                                   "extracted_text": T1, "source_session": "s0", "versione": 1}).execute().data[0]
    copia_v1 = dict(v1)
    out, _ = registra(V2, documento=V1["name"], sess="s2")                                         # per nome
    assert out.startswith("ESITO: ok"), out
    dd = db.d[F.T_DOC]
    assert len(dd) == 2 and dd[1]["documento_id"] == v1["id"] and dd[1]["versione"] == 2 and dd[1]["sostituisce_doc"] == v1["id"]
    assert dd[0] == copia_v1                                                                       # la riga vecchia NON è stata toccata
    ap = F.esegui("fascicolo_apri", {"fascicolo": COD})
    assert ap.count("Documento L-") == 1 and "2 versioni" in ap and f"v1=doc:{F.doc_id_di(dd[0])}" in ap and f"v2=doc:{F.doc_id_di(dd[1])}" in ap
    # lo stesso contenuto della v1 ricaricato: riconosciuto anche se la v1 non ha l'impronta salvata
    out, _ = registra(allegato("altra.pdf", "s9/altra.pdf", T1), documento=V1["name"], sess="s9")
    assert "idempotente" in out and len(dd) == 2


# ── recupero e confronto ─────────────────────────────────────────────────────────────────────────────
def test_recupera_tutte_le_versioni_ognuna_con_il_suo_id_per_le_citazioni(db):
    logico, _, _ = due_versioni(db)
    d1, d2 = db.d[F.T_DOC]
    ctx("A", utente="mostrami le versioni", collected={}, sess="s5")
    out = F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": logico, "versione": "tutte", "query": "residuo da liquidare"})
    assert "2 versioni conservate" in out and out.count("[doc:") >= 4
    assert f"[[fonte|{F.doc_id_di(d1)}|PAGINA" in out and f"[[fonte|{F.doc_id_di(d2)}|PAGINA" in out
    assert "8.850,00" in out and "9.250,00" in out                                                  # passaggi di entrambe
    assert "registrata il 2026-11-10" in out and "da utente" in out and "motivo: nuova stima del committente" in out
    for sel, atteso, assente in [("1", "8.850,00", "9.250,00"), ("2", "9.250,00", "8.850,00")]:
        o = F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": logico, "versione": sel, "query": "residuo da liquidare"})
        assert atteso in o.split("==", 1)[1] and assente not in o.split("==", 1)[1]
    assert "inesistente" in F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": logico, "versione": "7"})
    o = F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": F.doc_id_di(d1), "query": "residuo"})      # id di UNA versione → proprio quella
    assert "8.850,00" in o.split("==", 1)[1] and "9.250,00" not in o.split("==", 1)[1]
    o = F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": "Riepilogo_Commessa", "query": "residuo"})  # per nome → l'ultima versione
    assert "9.250,00" in o.split("==", 1)[1]


def test_confronto_fra_versioni_mostra_le_differenze_senza_scrivere(db):
    logico, _, _ = due_versioni(db)
    prima = (len(db.d[F.T_DOC]), [dict(v) for v in db.d[F.T_VOCI]], len(db.d["kbot_fascicolo_eventi"]))
    ctx("A", utente="confronta le versioni", collected={}, sess="s5")
    out = F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": logico, "confronta_con": 1})
    assert "CONFRONTO v1" in out and "→ v2" in out
    assert "«Imponibile contrattuale 15.250,00 euro» → «Imponibile contrattuale 15.650,00 euro»" in out
    assert "Solo nella seconda" in out and "Variante n. 2" in out and "15.250,00" in out and "9.250,00" in out and "NON modifica nulla" in out
    assert prima == (len(db.d[F.T_DOC]), db.d[F.T_VOCI], len(db.d["kbot_fascicolo_eventi"]))
    assert "IDENTICI" in D.confronta(db.d[F.T_DOC][0], {**db.d[F.T_DOC][0], "versione": 3})


def test_approvare_i_contenuti_e_un_atto_distinto_dalla_registrazione(db):
    logico, _, _ = due_versioni(db)
    ctx("A", utente="fammi vedere", collected={}, sess="s5")
    assert F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": logico, "versione": "2", "imposta_stato": "verificato"}).startswith("NON ESEGUITO")
    ctx("A", utente="Sì, segna come verificata la v2", collected={}, sess="s5")
    out = F.esegui("fascicolo_documento", {"fascicolo": COD, "documento": logico, "versione": "2", "imposta_stato": "verificato"})
    assert out.startswith("ESEGUITO") and "record del fascicolo non sono cambiati" in out
    assert [d["stato"] for d in db.d[F.T_DOC]] == ["caricato", "verificato"]
    assert "ultima verificata v2" in F.esegui("fascicolo_apri", {"fascicolo": COD})


def test_aggiornare_il_record_resta_un_passo_separato_con_la_sua_conferma(db):
    logico, _, _ = due_versioni(db)
    vid = db.d[F.T_VOCI][0]["id"]
    ctx("A", utente="Sì, aggiorna l'imponibile a 15.650", collected={}, sess="s5")
    out = F.esegui("fascicolo_aggiorna", {"fascicolo": COD, "record": vid[:8], "valore": "15.650 €", "motivo": "versione 2 del riepilogo", "doc": F.doc_id_di(db.d[F.T_DOC][1]), "pag": 1})
    assert out.startswith("ESITO: ok") and db.d[F.T_VOCI][0]["valore"] == "15.650 €" and len(db.d[F.T_VOCI]) == 1


# ── citazioni alla versione esatta e marcatori ─────────────────────────────────────────────────────
def test_collega_citati_apre_una_versione_precedente_mai_aperta_in_questa_conversazione(db):
    logico, _, _ = due_versioni(db)
    d1, d2 = db.d[F.T_DOC]
    c = ctx("A", utente="x", collected={}, sess="s6")
    testo = f"Prima era 8.850,00 [[fonte|{F.doc_id_di(d1)}|0|Residuo da liquidare 8.850,00 euro]] e ora 9.250,00 [[fonte|{F.doc_id_di(d2)}|0|Residuo da liquidare 9.250,00 euro]]."
    assert F.collega_citati(c, testo) == 2
    assert {x["path"] for x in c.collected["uploaded_files"]} == {d1["path"], d2["path"]}
    out = FD.verifica(testo, c.collected, "s6", [])
    assert f"[[fonte|{F.doc_id_di(d1)}|0|Residuo da liquidare 8.850,00 euro|ok]]" in out                # la v1 continua a funzionare dopo la revisione
    assert f"[[fonte|{F.doc_id_di(d2)}|0|Residuo da liquidare 9.250,00 euro|ok]]" in out
    # una citazione alla v1 NON può puntare al testo della v2
    sbagliata = f"[[fonte|{F.doc_id_di(d1)}|0|Residuo da liquidare 9.250,00 euro]]"
    assert FD.verifica(sbagliata, c.collected, "s6", []) == ""


def test_nessun_marcatore_grezzo_arriva_all_utente():
    col = {"uploaded_files": [allegato("a.pdf", "s/a.pdf", "Residuo da liquidare 8.850,00 euro [1] nota")]}
    d = FD.doc_id(col["uploaded_files"][0])
    casi = [
        f"A [[fonte|{d}|0]] B", f"A [[fonte|{d}]] B", f"A [[fonte|{d}|pag. 2|Residuo]] B", "A [[fonte|sconosciuto|1|x]] B", "A [[fonte|]] B",
        f"A [[fonte|{d}|0|Residuo da liquidare [1] nota]] B", "A [[fonte|x|1|testo senza chiusura B", f"A [[ Fonte | {d} | 0 | testo ]] B",
    ]
    for t in casi:
        for coll in (col, {}, {"uploaded_files": []}):
            out = FD.verifica(t, coll, "s", [])                                   # SOLO la verifica: da sola non deve lasciare forme grezze
            assert "[[" not in FD._NORMALIZZATO.sub("", out), (t, out)             # restano al massimo marcatori GIÀ verificati, mai forme grezze
            if not coll.get("uploaded_files"):
                assert "[[" not in out, (t, out)                                     # senza documenti nessun marcatore passa
    ok = FD.verifica(f"Residuo [[fonte|{d}|0|Residuo da liquidare 8.850,00 euro]].", col, "s", [])
    assert f"[[fonte|{d}|0|Residuo da liquidare 8.850,00 euro|ok]]" in ok
    assert FD.verifica(f"A [[fonte|{d}|0]] B", col, "s", []) == "A  B"                                      # forma incompleta: tolta, non lasciata a metà
    assert FD.toglie_residui("nessun marcatore") == "nessun marcatore"


# ── la funzione dalla chat vera (modello finto) ───────────────────────────────────────────────────────
from test_e2e_scenarios import (FakeAnthropic, _make_session, client, fake_anthropic, fake_db)  # noqa: E402,F401
from test_cerca_norma_endpoint import _flusso  # noqa: E402


def test_dalla_chat_il_modello_registra_la_v2_e_cita_entrambe_le_versioni(client, fake_anthropic, monkeypatch):
    import json
    from app.main import app
    from app.lib.auth import AuthUser, optional_user
    from app.lib import rag, sessions
    monkeypatch.setattr(app.state.limiter, "enabled", False)
    monkeypatch.setattr(strumenti.web_search, "enabled", lambda: False)
    D._SCHEMA.clear()
    db = _DB(); monkeypatch.setattr(F, "_db", lambda: db)
    fid = db.table(F.T_FASC).insert({"user_id": "A", "tipo": "commessa", "codice": COD, "titolo": "Fascicolo fittizio", "stato": "aperto"}).execute().data[0]["id"]
    lid = str(uuid.uuid4())
    v1 = db.table(F.T_DOC).insert({"fascicolo_id": fid, "user_id": "A", "name": V1["name"], "type": "application/pdf", "size": 9, "path": V1["path"], "extracted_text": T1,
                                   "source_session": "sessione-vecchia", "versione": 1, "serie": "kbot-test-04-riepilogo-commessa", "sha256": F._sha(T1), "documento_id": lid,
                                   "stato": "caricato"}).execute().data[0]
    monkeypatch.setattr(rag, "fetch_chunks", lambda sid, limit=500: [])
    i1, i2 = F.doc_id_di(v1), F.doc_id_di(V2)
    esiti, offerti = [], []

    def stream(self, **kw):
        if str(kw.get("system", "")).startswith("Estrai") or "tools" not in kw:
            return _flusso("ok", NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        ult = kw["messages"][-1]["content"]
        if isinstance(ult, list):
            esiti.append(ult[0]["content"])
            if len(esiti) == 1:
                return _flusso("", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[NS(
                    type="tool_use", name="fascicolo_documento", id="t2", input={"fascicolo": COD, "documento": D.sigla(lid), "confronta_con": 1})]))
            return _flusso(f"Registrata la v2. Il residuo passa da 8.850,00 € [[fonte|{i1}|0|Residuo da liquidare 8.850,00 euro]] a 9.250,00 € "
                           f"[[fonte|{i2}|0|Residuo da liquidare 9.250,00 euro]] e un marcatore rotto [[fonte|{i2}|pag. 1]].",
                           NS(stop_reason="end_turn", usage=NS(input_tokens=1, output_tokens=1), content=[]))
        offerti.append([t["name"] for t in kw["tools"]])
        return _flusso("", NS(stop_reason="tool_use", usage=NS(input_tokens=1, output_tokens=1), content=[NS(
            type="tool_use", name="fascicolo_registra_versione", id="t1", input={"fascicolo": COD, "allegato": i2, "documento": D.sigla(lid), "motivo": "nuova stima del committente"})]))

    monkeypatch.setattr("test_e2e_scenarios._FakeMessages.stream", stream)
    app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
    try:
        sid = _make_session(client)
        sessions.update_session(sid, {"collected_data": {"uploaded_files": [V2]}})
        r = client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Sì, registra l'allegato come nuova versione del riepilogo, motivo: nuova stima del committente"})
        ev = [json.loads(x[5:].strip()) for x in r.text.splitlines() if x.startswith("data:")]
        msg = [e for e in ev if e.get("done")][-1]["message"]
        assert "fascicolo_registra_versione" in offerti[0] and len(F.NOMI) == 10
        assert esiti[0].startswith("ESITO: ok") and "v2 del documento " + D.sigla(lid) in esiti[0]
        assert len(db.d[F.T_DOC]) == 2 and db.d[F.T_DOC][1]["documento_id"] == lid and db.d[F.T_DOC][1]["versione"] == 2 and db.d[F.T_DOC][1]["stato"] == "caricato"
        assert "CONFRONTO v1" in esiti[1]
        assert f"[[fonte|{i1}|0|Residuo da liquidare 8.850,00 euro|ok]]" in msg and f"[[fonte|{i2}|0|Residuo da liquidare 9.250,00 euro|ok]]" in msg   # v1 e v2, versione esatta
        assert "pag. 1]]" not in msg and "[[fonte|" not in msg.replace("|ok]]", "").replace("[[fonte|" + i1, "").replace("[[fonte|" + i2, "")   # il marcatore rotto è sparito
        assert "Nota del sistema" not in msg                                                          # l'affermazione «registrata» è sostenuta dallo strumento
        # stessa richiesta in una conversazione nuova: idempotente, nessuna v3
        esiti.clear()
        sid2 = _make_session(client)
        sessions.update_session(sid2, {"collected_data": {"uploaded_files": [V2]}})
        client.post("/api/kbot/message/stream", json={"session_id": sid2, "message": "Sì, registra l'allegato come nuova versione del riepilogo"})
        assert esiti[0].startswith("ESITO: ok (idempotente)") and len(db.d[F.T_DOC]) == 2
    finally:
        app.dependency_overrides.pop(optional_user, None)


def test_la_risposta_finale_non_contiene_marcatori_grezzi_con_o_senza_documenti():
    """Il percorso vero di message.py (non solo la libreria): senza documenti nella conversazione i marcatori scritti dal modello non arrivano all'utente."""
    from app.api import message as M
    raw = "Il residuo è 8.850,00 € [[fonte|abc123def456|1|Residuo da liquidare 8.850,00 euro]] e [[fonte|abc123def456|pag. 2]] fine."
    for coll in (None, {}, {"uploaded_files": []}):
        visibile = M._extract_gated_summary(raw, [], coll, "s")[0]
        assert "[[" not in visibile and "fonte|" not in visibile and "8.850,00" in visibile, (coll, visibile)
