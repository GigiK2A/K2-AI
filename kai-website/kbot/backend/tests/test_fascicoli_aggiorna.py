"""Test 28C: aggiornare un record per ID senza crearne uno nuovo. Backend, strumenti e chat con il modello (finto), anche da una nuova conversazione."""
import os
import sys
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import fascicoli as F, fascicoli_versioni as V, strumenti  # noqa: E402
from test_fascicoli import _DB, ctx  # noqa: E402


@pytest.fixture
def db(monkeypatch):
    d = _DB(); monkeypatch.setattr(F, "_db", lambda: d); return d


def crea_10000(db):
    ctx("A", utente="salva nel fascicolo il budget")
    F.esegui("fascicolo_salva", {"codice": "TEST-KBOT-VERSIONI-01", "titolo": "Fascicolo di prova", "voci": [
        {"tipo": "dato", "testo": "Budget previsto per intervento tecnico.", "valore": "10.000 €", "unita": "EUR",
         "contesto": "Dato fittizio di test. Provenienza: dichiarazione dell'utente a fini di test."}]})
    return db.d[F.T_VOCI][0]["id"]


def voci_attuali(db):
    return [v for v in db.d[F.T_VOCI] if v["stato_record"] == "attuale"]


def test_aggiornamento_per_id_mantiene_identita_e_storico(db):
    vid = crea_10000(db)
    ctx("A", utente="Sì, aggiorna il budget a 12.500")
    out = F.esegui("fascicolo_aggiorna", {"fascicolo": "TEST-KBOT-VERSIONI-01", "record": vid[:8], "valore": "12.500 €", "motivo": "nuova stima interna"})
    assert out.startswith("ESITO: ok") and '"revisione": 2' in out and "nessun nuovo record" in out
    assert len(db.d[F.T_VOCI]) == 1 and db.d[F.T_VOCI][0]["id"] == vid                         # stesso record, stesso ID
    v = db.d[F.T_VOCI][0]
    assert v["valore"] == "12.500 €" and v["revisione"] == 2 and v["stato_record"] == "attuale" and v["motivo"] == "nuova stima interna"
    ev = [e for e in db.d["kbot_fascicolo_eventi"] if e["azione"] == "aggiorna"]
    assert len(ev) == 1 and ev[0]["prima"]["valore"] == "10.000 €" and ev[0]["dopo"]["valore"] == "12.500 €"
    st = F.esegui("fascicolo_voce", {"fascicolo": "TEST-KBOT-VERSIONI-01", "azione": "storico", "record": vid[:8]})
    assert "10.000 €" in st and "12.500 €" in st and "VALORI PRECEDENTI" in st and "nuova stima interna" in st
    ap = F.esegui("fascicolo_apri", {"fascicolo": "TEST-KBOT-VERSIONI-01"})
    assert "12.500 €" in ap and "rev2" in ap and ap.count("\n- ") == 1


def test_stessa_richiesta_ripetuta_non_duplica_ed_e_idempotente(db):
    vid = crea_10000(db)
    ctx("A", utente="Sì, aggiorna a 12.500")
    a = {"fascicolo": "TEST-KBOT-VERSIONI-01", "record": vid[:8], "valore": "12.500 €", "motivo": "nuova stima"}
    F.esegui("fascicolo_aggiorna", a)
    n_eventi = len(db.d["kbot_fascicolo_eventi"])
    out = F.esegui("fascicolo_aggiorna", a)
    assert out.startswith("ESITO: ok (idempotente)") and "nessuna modifica" in out
    assert len(db.d[F.T_VOCI]) == 1 and db.d[F.T_VOCI][0]["revisione"] == 2 and len(db.d["kbot_fascicolo_eventi"]) == n_eventi
    # anche scrivere 12.500,00 € (stesso numero) non è una modifica
    out = F.esegui("fascicolo_aggiorna", {**a, "valore": "12.500,00 €"})
    assert "idempotente" in out and db.d[F.T_VOCI][0]["revisione"] == 2


def test_un_aggiornamento_fallito_non_crea_record(db):
    vid = crea_10000(db)
    ctx("A", utente="Sì, aggiorna")
    for args, codice in [({"record": "zzzzzzzz", "valore": "1"}, "NON_TROVATO"), ({"record": vid[:3], "valore": "1"}, "NON_TROVATO"),
                         ({"record": vid[:8], "valore": "1", "revisione_attesa": 7}, "CONFLITTO")]:
        out = F.esegui("fascicolo_aggiorna", {"fascicolo": "TEST-KBOT-VERSIONI-01", "motivo": "x", **args})
        assert out.startswith(f"ESITO: errore {codice}"), out
    out = F.esegui("fascicolo_aggiorna", {"fascicolo": "TEST-KBOT-VERSIONI-01", "record": vid[:8], "valore": "2"})
    assert "MOTIVO_MANCANTE" in out
    ctx("A", utente="cosa ne pensi del budget?")
    assert "NON_ESEGUITO" in F.esegui("fascicolo_aggiorna", {"fascicolo": "TEST-KBOT-VERSIONI-01", "record": vid[:8], "valore": "9", "motivo": "x"})
    assert len(db.d[F.T_VOCI]) == 1 and db.d[F.T_VOCI][0]["valore"] == "10.000 €" and db.d[F.T_VOCI][0]["revisione"] if "revisione" in db.d[F.T_VOCI][0] else True


def test_concorrenza_la_seconda_scrittura_con_revisione_vecchia_e_rifiutata(db):
    vid = crea_10000(db)
    ctx("A", utente="Sì, aggiorna")
    base = {"fascicolo": "TEST-KBOT-VERSIONI-01", "record": vid[:8], "motivo": "x"}
    assert F.esegui("fascicolo_aggiorna", {**base, "valore": "12.500 €", "revisione_attesa": 1}).startswith("ESITO: ok")
    out = F.esegui("fascicolo_aggiorna", {**base, "valore": "13.000 €", "revisione_attesa": 1})      # un altro lettore partiva dalla rev 1
    assert out.startswith("ESITO: errore CONFLITTO") and "revisione 2" in out and db.d[F.T_VOCI][0]["valore"] == "12.500 €"


def test_il_salva_non_crea_un_secondo_attuale_per_lo_stesso_dato_28c(db):
    """Il caso reale: record senza chiave a 10.000, poi salvataggio con chiave e frase di provenienza diversa a 12.500, poi di nuovo."""
    crea_10000(db)
    ctx("A", utente="salva la revisione del budget")
    v = {"tipo": "dato", "chiave": "budget_intervento_tecnico", "testo": "Budget previsto per intervento tecnico. Revisione del budget a seguito di nuova stima interna — test.",
         "valore": "12.500 €", "unita": "EUR", "contesto": "Revisione del budget a seguito di nuova stima interna — test. Provenienza: dichiarazione dell'utente a fini di test."}
    out = F.esegui("fascicolo_salva", {"fascicolo": "TEST-KBOT-VERSIONI-01", "voci": [v]})
    assert "1 proposte" in out and "fascicolo_aggiorna" in out
    assert len(voci_attuali(db)) == 1 and [x["valore"] for x in voci_attuali(db)] == ["10.000 €"]       # un solo attuale
    ctx("A", utente="salva di nuovo")
    out = F.esegui("fascicolo_salva", {"fascicolo": "TEST-KBOT-VERSIONI-01", "voci": [{**v, "contesto": "altra frase di provenienza"}]})
    assert "1 già presenti" in out and len(db.d[F.T_VOCI]) == 2                                                  # la proposta non si duplica


def test_duplicati_gia_presenti_si_archiviano_non_distruttivamente(db):
    """Ripristino del 28C simulato su dati fittizi: 10.000 (attuale) + due 12.500 uguali già creati dal vecchio comportamento."""
    vid = crea_10000(db)
    fid = db.d[F.T_FASC][0]["id"]
    for i, ctxt in enumerate(["Revisione del budget a seguito di nuova stima interna — test. Provenienza: dichiarazione dell'utente.", None]):
        db.d[F.T_VOCI].append({"id": f"d{i}000000-0000-4000-8000-000000000000", "fascicolo_id": fid, "user_id": "A", "tipo": "dato", "chiave": "budget_intervento_tecnico",
                               "testo": "Budget previsto per intervento tecnico. Revisione del budget a seguito di nuova stima interna — test.", "valore": "12.500 €",
                               "unita": "EUR", "contesto": ctxt, "stato_record": "attuale", "verifica": "non_verificato", "origine": "dichiarato_utente",
                               "fonti": [{"origine": "utente"}], "created_at": f"2026-11-10T15:{47 + i * 5}:00+00:00"})
    gr = V.duplicati("A", fid)
    assert len(gr) == 1 and len(gr[0]["duplicati"]) == 1                      # i due 12.500 sono lo stesso dato (il contesto-prosa non li distingueva)
    ctx("A", utente="Sì, archivia il duplicato d1000000 come duplicato")
    out = F.esegui("fascicolo_voce", {"fascicolo": "TEST-KBOT-VERSIONI-01", "azione": "archivia", "record": "d1000000", "motivo": "duplicato di d0000000"})
    assert out.startswith("ESITO: ok")
    ctx("A", utente="Sì, aggiorna il record originale a 12.500")
    F.esegui("fascicolo_aggiorna", {"fascicolo": "TEST-KBOT-VERSIONI-01", "record": vid[:8], "valore": "12.500 €", "motivo": "ripristino"})
    ctx("A", utente="Sì, archivia anche d0000000")
    F.esegui("fascicolo_voce", {"fascicolo": "TEST-KBOT-VERSIONI-01", "azione": "archivia", "record": "d0000000", "motivo": "duplicato di " + vid[:8]})
    assert len(db.d[F.T_VOCI]) == 3                                            # niente cancellato
    att = voci_attuali(db)
    assert len(att) == 1 and att[0]["id"] == vid and att[0]["valore"] == "12.500 €"
    assert sum(1 for v in db.d[F.T_VOCI] if v["stato_record"] == "archiviata") == 2
