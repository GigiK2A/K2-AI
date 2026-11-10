"""Ciclo completo di una commessa FITTIZIA (audit 8): creazione, recupero, revisione, storico, deduplicazione, consolidamento, sicurezza."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import fascicoli as F, fascicoli_versioni as V
from test_fascicoli import _DB, ctx


@pytest.fixture
def db(monkeypatch):
    d = _DB(); monkeypatch.setattr(F, "_db", lambda: d); return d


V1 = [
    {"tipo": "dato", "chiave": "imponibile_dichiarato", "testo": "Totale imponibile dichiarato", "valore": "15.250,00", "unita": "EUR", "doc": "d1", "pag": 1, "quote": "15.250,00"},
    {"tipo": "dato", "chiave": "imponibile_corretto", "testo": "Totale imponibile ricalcolato", "valore": "15.650,00", "unita": "EUR", "origine": "calcolato"},
    {"tipo": "dato", "chiave": "pratiche_protocollate", "testo": "Pratiche protocollate", "valore": "6", "unita": "pratiche", "doc": "d1", "pag": 1},
    {"tipo": "dato", "chiave": "maturato", "testo": "Maturato", "valore": "14.290,00", "unita": "EUR", "origine": "calcolato"},
    {"tipo": "dato", "chiave": "residuo_maturato", "testo": "Residuo maturato", "valore": "7.890,00", "unita": "EUR", "origine": "calcolato"},
]


def salva(utente, voci, user="A", fasc="UM-26-041", **extra):
    ctx(user, utente=utente, collected=extra.pop("collected", {}))
    return F.esegui("fascicolo_salva", {"codice": fasc, "titolo": "Adeguamento siti tecnici", "voci": voci, **extra})


def attuali(db, chiave):
    return [v for v in db.d[F.T_VOCI] if v.get("chiave") == chiave and v["stato_record"] == "attuale"]


def test_fase1_creazione_con_fonti_origini_e_stati(db):
    out = salva("salva nel fascicolo UM-26-041", V1)
    assert "5 record nuovi" in out
    righe = {v["chiave"]: v for v in db.d[F.T_VOCI]}
    assert righe["imponibile_dichiarato"]["origine"] == "letto_da_documento" and righe["imponibile_dichiarato"]["fonti"][0]["doc"] == "d1"
    assert righe["imponibile_corretto"]["origine"] == "calcolato" and all(v["stato_record"] == "attuale" and v["verifica"] == "non_verificato" for v in righe.values())
    assert {e["azione"] for e in db.d["kbot_fascicolo_eventi"]} == {"crea"}


def test_fase5_stesso_dato_due_volte_non_duplica_e_altra_fonte_si_aggiunge(db):
    salva("salva nel fascicolo", V1)
    out = salva("salva di nuovo", V1)
    assert "0 record nuovi, 5 già presenti" in out and len(db.d[F.T_VOCI]) == 5
    # stesso valore da un'ALTRA fonte (altra pagina/documento): un solo record con due fonti
    out = salva("aggiungi la fonte", [{**V1[0], "doc": "d2", "pag": 3, "quote": "imponibile 15.250"}])
    assert "1 con fonte aggiunta" in out and len(db.d[F.T_VOCI]) == 5
    assert len(attuali(db, "imponibile_dichiarato")[0]["fonti"]) == 2
    # stesso valore ma PERIODO diverso: non è un duplicato
    salva("salva anche il periodo successivo", [{**V1[3], "periodo": "2026-Q4"}, {**V1[3], "periodo": "2027-Q1"}])
    assert len([v for v in db.d[F.T_VOCI] if v["chiave"] == "maturato"]) == 3


def test_fase3_revisione_dichiarata_non_sostituisce_poi_conferma_e_storico(db):
    salva("salva nel fascicolo", V1)
    # nuova versione SOLO DICHIARATA: confronto, nessun documento caricato
    ctx("A", utente="la nuova versione ha imponibile 15.650, otto pratiche, maturato 15.650, residuo 9.250")
    nuovi = [{"chiave": "imponibile_dichiarato", "valore": "15.650,00"}, {"chiave": "pratiche_protocollate", "valore": "8"},
             {"chiave": "maturato", "valore": "15.650,00"}, {"chiave": "residuo_maturato", "valore": "9.250,00"}]
    cf = F.esegui("fascicolo_confronta", {"fascicolo": "UM-26-041", "valori": nuovi, "documento_caricato": False})
    assert "≠ DIVERSO" in cf and "revisione DICHIARATA" in cf and "NON PRESENTI nel nuovo" in cf
    out = salva("salva la revisione dichiarata", [{**v, "testo": "x " + v["chiave"], "stato": "da_verificare", "origine": "dichiarato_utente"} for v in nuovi])
    assert "4 proposte" in out
    assert attuali(db, "maturato")[0]["valore"] == "14.290,00"                       # l'ultimo valore documentato NON è cambiato
    prop = [v for v in db.d[F.T_VOCI] if v["stato_record"] == "da_verificare" and v["chiave"] == "pratiche_protocollate"][0]
    # sostituire richiede la conferma dell'utente (non basta che lo chieda il modello)
    ctx("A", utente="cosa ne pensi?")
    assert F.esegui("fascicolo_voce", {"fascicolo": "UM-26-041", "azione": "sostituisci", "record": prop["id"]}).count("NON ESEGUITO") == 1
    ctx("A", utente="Sì, conferma la sostituzione: è arrivato il documento")
    out = F.esegui("fascicolo_voce", {"fascicolo": "UM-26-041", "azione": "sostituisci", "record": prop["id"][:8], "motivo": "nuova versione 2 caricata e verificata"})
    assert out.startswith("ESITO: ok") and "ESEGUITO:" in out
    vecchio = [v for v in db.d[F.T_VOCI] if v["chiave"] == "pratiche_protocollate" and v["stato_record"] == "superata"][0]
    assert vecchio["valore"] == "6" and vecchio["sostituita_da"] == prop["id"] and vecchio["valido_fino"]
    assert attuali(db, "pratiche_protocollate")[0]["valore"] == "8" and attuali(db, "pratiche_protocollate")[0]["sostituisce"] == vecchio["id"]
    # fase 4: storico, valore precedente e attuale con fonti e cronologia
    st = F.esegui("fascicolo_voce", {"fascicolo": "UM-26-041", "azione": "storico", "record": "pratiche_protocollate"})
    assert "= 6" in st and "superata" in st and "= 8" in st and "attuale" in st and "sostituisce" in st and "doc d1 pag. 1" in st
    # cosa era valido a una certa data: ieri il valore era 6
    vecchio["valido_dal"] = "2026-11-01T10:00:00+00:00"; vecchio["valido_fino"] = "2026-11-08T10:00:00+00:00"
    nuovo = attuali(db, "pratiche_protocollate")[0]; nuovo["valido_dal"] = "2026-11-08T10:00:00+00:00"
    assert "= 6" in F.esegui("fascicolo_apri", {"fascicolo": "UM-26-041", "alla_data": "2026-11-05"})
    assert "= 8" in V.storico("A", db.d[F.T_FASC][0]["id"], "pratiche", "2026-11-10")


def test_valore_diverso_da_documento_resta_proposta_finche_non_si_conferma(db):
    salva("salva", V1)
    out = salva("salva anche il nuovo documento", [{**V1[0], "valore": "15.650,00", "doc": "d2", "pag": 1, "doc_versione": "2"}])
    assert "1 proposte" in out and attuali(db, "imponibile_dichiarato")[0]["valore"] == "15.250,00"


def test_consolidamento_duplicati_storici_senza_chiave_reversibile(db):
    """Dati come quelli reali di UM-26-041: stessi importi più volte, senza `chiave`, formulazioni diverse."""
    ctx("A", utente="salva"); F.esegui("fascicolo_salva", {"codice": "UM-26-041", "titolo": "C", "voci": []})
    fid = db.d[F.T_FASC][0]["id"]
    def raw(tipo, testo, valore, fonte=None):
        db.d.setdefault(F.T_VOCI, []).append({"id": f"id-{len(db.d.get(F.T_VOCI, []))}-xxxxxxxx", "fascicolo_id": fid, "user_id": "A", "tipo": tipo, "testo": testo, "valore": valore,
            "fonte": fonte or {"origine": "documento", "doc": "f9561058b1fc", "pag": 1}, "verifica": "non_verificato", "created_at": f"2026-11-0{len(db.d[F.T_VOCI]) % 9 + 1}T10:00:00+00:00"})
    raw("dato", "VERIFICATO sul documento: totale imponibile dichiarato 15.250 euro", "15.250,00 EUR (dichiarato)")
    raw("dato", "VERIFICATO sul documento: totale imponibile dichiarato 15.250 euro riportato", "15.250,00 EUR (dichiarato)")
    raw("dato", "CALCOLATO: totale imponibile corretto 4.200 + 5.440 + 4.750 + 1.260", "15.650,00 EUR (corretto, calcolato)")
    raw("dato", "CALCOLATO (non presente nel documento): totale imponibile corretto somma righe", "15.650,00 EUR (corretto, calcolato)")
    raw("dato", "VERIFICATO sul documento: acconto ricevuto il 15/10/2026", "6.400,00 EUR")
    raw("dato", "VERIFICATO sul documento: acconto ricevuto il 15/10/2026 parziale", "6.400,00 EUR")
    raw("nota", "DA CONFERMARE: a quale voce sia imputato l'acconto di 6.400", "6.400,00 EUR")     # tipo diverso: NON è un duplicato
    raw("dato", "VERIFICATO sul documento: sopralluoghi 12 x 350 euro", "4.200,00 EUR")              # valore diverso: NON è un duplicato
    prima = {v["id"]: dict(v) for v in db.d[F.T_VOCI]}
    gr = V.duplicati("A", fid)
    assert len(gr) == 3 and all(len(g["duplicati"]) == 1 for g in gr)
    ctx("A", utente="cosa vedi?")
    assert F.esegui("fascicolo_duplicati", {"fascicolo": "UM-26-041", "azione": "consolida"}).startswith("NON ESEGUITO")
    assert all(v.get("stato_record", "attuale") == "attuale" for v in db.d[F.T_VOCI])                 # nulla è cambiato senza conferma
    elenco = F.esegui("fascicolo_duplicati", {"fascicolo": "UM-26-041", "azione": "elenca"})
    assert "Gruppo 1" in elenco and "tengo" in elenco
    ctx("A", utente="Sì, consolida i duplicati")
    assert F.esegui("fascicolo_duplicati", {"fascicolo": "UM-26-041", "azione": "consolida"}).startswith("ESEGUITO: consolidati 3")
    assert len(db.d[F.T_VOCI]) == 8                                                                    # NIENTE cancellato
    assert sum(1 for v in db.d[F.T_VOCI] if v.get("stato_record") == "archiviata") == 3
    assert sum(1 for v in db.d[F.T_VOCI] if V.stato_di(v) == "attuale") == 5
    ev = [e for e in db.d["kbot_fascicolo_eventi"] if e["azione"] == "consolida"]
    assert len(ev) == 3 and all(e["prima"] for e in ev)
    for e in ev:                                                                                          # rollback
        assert V.annulla_consolidamento("A", e["id"])
    assert all(V.stato_di(v) == "attuale" for v in db.d[F.T_VOCI]) and V.annulla_consolidamento("B", ev[0]["id"]) is False


def test_documento_nuova_versione_stessa_serie_e_stesso_contenuto(db):
    col = {"uploaded_files": [{"name": "Riepilogo_v1.pdf", "path": "s1/a.pdf", "extractedText": "Imponibile 15.250"}]}
    salva("salva anche il documento", [], collected=col, allega_documenti=True)
    col2 = {"uploaded_files": [{"name": "Riepilogo_v2.pdf", "path": "s2/b.pdf", "extractedText": "Imponibile 15.650"}, {"name": "copia.pdf", "path": "s2/c.pdf", "extractedText": "Imponibile 15.250"}]}
    out = salva("salva anche i documenti", [], collected=col2, allega_documenti=True)
    docs = db.d[F.T_DOC]
    assert [(d["name"], d["versione"]) for d in docs] == [("Riepilogo_v1.pdf", 1), ("Riepilogo_v2.pdf", 2)]
    assert docs[1]["sostituisce_doc"] == docs[0]["id"] and "versione 2" in out and "non duplicato" in out
    ap = F.esegui("fascicolo_apri", {"fascicolo": "UM-26-041"})
    assert "ultima ricevuta Riepilogo_v2.pdf" in ap and "nessuna versione verificata" in ap
    ctx("A", utente="Sì, segna la v1 come verificata")
    assert F.esegui("fascicolo_documento", {"fascicolo": "UM-26-041", "documento": F.doc_id_di(docs[0]), "imposta_stato": "verificato"}).startswith("ESEGUITO")
    assert "ultima verificata v1" in F.esegui("fascicolo_apri", {"fascicolo": "UM-26-041"})


def test_fase6_sicurezza_tenant(db):
    salva("salva", V1)
    fid = db.d[F.T_FASC][0]["id"]; vid = db.d[F.T_VOCI][0]["id"]
    ctx("B", utente="Sì, salva e consolida")
    for nome, args in [("fascicolo_confronta", {"fascicolo": fid, "valori": []}), ("fascicolo_voce", {"fascicolo": fid, "azione": "archivia", "record": vid}),
                       ("fascicolo_duplicati", {"fascicolo": fid, "azione": "consolida"}), ("fascicolo_documento", {"fascicolo": fid, "documento": "x"}),
                       ("fascicolo_apri", {"fascicolo": "UM-26-041"})]:
        assert F.esegui(nome, args) in ("Fascicolo non trovato.",), nome
    assert V.storico("B", fid, "maturato") == "Record non trovato." and V.duplicati("B", fid) == []
    assert F.documento_dell_utente("B", "qualunque") is None
    assert all(v["stato_record"] == "attuale" for v in db.d[F.T_VOCI])


def _pdf():
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=A4); c.drawString(60, 780, "Totale imponibile 15.250,00 EUR"); c.showPage(); c.save(); return b.getvalue()


def test_documento_del_fascicolo_si_apre_nel_visualizzatore_da_un_altra_conversazione(db, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import upload
    from app.lib.auth import AuthUser, optional_user, require_user
    col = {"uploaded_files": [{"name": "Riepilogo.pdf", "path": "s1/r.pdf", "extractedText": "Totale imponibile 15.250,00 EUR"}]}
    salva("salva anche il documento", [], collected=col, allega_documenti=True)
    did = F.doc_id_di(db.d[F.T_DOC][0]); fid = db.d[F.T_FASC][0]["id"]
    pdf = _pdf()
    monkeypatch.setattr(upload, "_bytes_documento", lambda p: pdf if p == "s1/r.pdf" else None)
    # un'ALTRA conversazione dello stesso utente (nessun allegato proprio) e una conversazione di un altro utente
    sess = {"s9": {"id": "s9", "user_id": "A", "collected_data": {}}, "s8": {"id": "s8", "user_id": "B", "collected_data": {}}}
    monkeypatch.setattr(upload.sessions, "get_session", lambda sid: sess.get(sid))
    cl = TestClient(app)
    try:
        app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
        app.dependency_overrides[require_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
        r = cl.get(f"/api/kbot/session/s9/documents/{did}/view?pag=1&quote=15.250,00")
        assert r.status_code == 200 and r.json()["localizzato"] and r.json()["tipo"] == "pdf"
        r = cl.get(f"/api/kbot/fascicoli/{fid}/documents/{did}/view?pag=1&quote=15.250,00")
        assert r.status_code == 200 and r.json()["localizzato"]
        # tenant B: né dalla propria sessione né dal fascicolo di A
        app.dependency_overrides[optional_user] = lambda: AuthUser(id="B", email="b@b.it", has_paid=False, raw={})
        app.dependency_overrides[require_user] = lambda: AuthUser(id="B", email="b@b.it", has_paid=False, raw={})
        assert cl.get(f"/api/kbot/session/s8/documents/{did}/view?pag=1").status_code == 404
        assert cl.get(f"/api/kbot/session/s9/documents/{did}/view?pag=1").status_code == 403
        assert cl.get(f"/api/kbot/fascicoli/{fid}/documents/{did}/view?pag=1").status_code == 404
        assert cl.get(f"/api/kbot/fascicoli/{fid}/duplicati").status_code == 404
        assert cl.post(f"/api/kbot/fascicoli/{fid}/consolida", json={}).status_code == 404
        # file non più nello storage: 410 con messaggio, non un errore generico
        app.dependency_overrides[optional_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
        monkeypatch.setattr(upload, "_bytes_documento", lambda p: None)
        assert cl.get(f"/api/kbot/session/s9/documents/{did}/view?pag=1").status_code == 410
    finally:
        app.dependency_overrides.pop(optional_user, None); app.dependency_overrides.pop(require_user, None)


def test_api_storico_duplicati_consolida_e_annulla(db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.lib.auth import AuthUser, require_user
    salva("salva", V1[:1])
    fid = db.d[F.T_FASC][0]["id"]
    db.d[F.T_VOCI].append({**db.d[F.T_VOCI][0], "id": "dup-0000-xxxx", "chiave": None, "testo": "Totale imponibile dichiarato", "created_at": "2026-11-09T10:00:00+00:00"})
    db.d[F.T_VOCI][0]["chiave"] = None
    cl = TestClient(app)
    try:
        app.dependency_overrides[require_user] = lambda: AuthUser(id="A", email="a@b.it", has_paid=False, raw={})
        g = cl.get(f"/api/kbot/fascicoli/{fid}/duplicati").json()
        assert len(g["gruppi"]) == 1 and "Gruppo 1" in g["descrizione"]
        r = cl.post(f"/api/kbot/fascicoli/{fid}/consolida", json={}).json()
        assert len(r["gruppi"]) == 1 and sum(1 for v in db.d[F.T_VOCI] if v["stato_record"] == "archiviata") == 1
        assert cl.post(f"/api/kbot/fascicoli/eventi/{r['gruppi'][0]['evento']}/annulla").status_code == 200
        assert all(v["stato_record"] == "attuale" for v in db.d[F.T_VOCI])
        assert "STORICO" in cl.get(f"/api/kbot/fascicoli/{fid}/storico?record=Totale").json()["storico"]
    finally:
        app.dependency_overrides.pop(require_user, None)


def test_rilevatore_sui_dati_reali_di_um_26_041_fittizi(db):
    """31 voci del collaudo (fixture): le ripetizioni note si trovano, le voci diverse NON si fondono."""
    import json
    R = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "um_26_041_voci.json")))
    rows = [{"id": str(i), **r, "created_at": f"2026-11-{i % 28 + 1:02d}"} for i, r in enumerate(R)]
    gr = []
    for v in rows:
        for g in gr:
            if V.equivalenti(v, g[0]) and V.stesso_valore(v, g[0]):
                g.append(v); break
        else:
            gr.append([v])
    dup = sorted(sorted(int(m["id"]) for m in g) for g in gr if len(g) > 1)
    assert dup == [[4, 20], [5, 21], [6, 23], [7, 24], [9, 26], [10, 27], [11, 28], [14, 30]]   # imponibile 15.250 e 15.650, protocollate, 8 incluse, maturato, acconto 6.400, residuo, 1.360
    assert not any({10, 17} <= {int(m["id"]) for m in g} for g in gr)                            # la nota «a quale voce è imputato l'acconto» non è il dato
    assert not any({12, 31} <= {int(m["id"]) for m in g} for g in gr if len(g) > 1)              # residuo 8.850 vs 8.850+9.250: valori diversi
