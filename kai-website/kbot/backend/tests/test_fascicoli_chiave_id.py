"""Test 28E: chiave e ID esposti, aggiornamento deterministico, nessun duplicato, dichiarazioni del modello controllate dagli strumenti davvero eseguiti."""
import os
import re
import sys
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from app.lib import fascicoli as F, fascicoli_versioni as V, strumenti  # noqa: E402
from test_fascicoli import _DB, ctx  # noqa: E402

COD = "TEST-E2E-ISOLATO-01"


@pytest.fixture
def db(monkeypatch):
    d = _DB(); monkeypatch.setattr(F, "_db", lambda: d); return d


def righe(out):
    return [r for r in out.splitlines() if r.startswith("- id=")]


def campo(riga, nome):
    m = re.search(rf"{nome}=(\S+)", riga)
    return m.group(1) if m else None


def crea(db):
    ctx("A", utente="salva nel fascicolo il budget")
    return F.esegui("fascicolo_salva", {"codice": COD, "titolo": "Fascicolo isolato di prova", "voci": [
        {"tipo": "dato", "chiave": "budget_intervento", "testo": "Budget previsto per l'intervento", "valore": "10.000 €", "unita": "EUR"}]})


def test_apri_e_storico_espongono_id_chiave_rev_stato_provenienza_e_legami(db):
    crea(db)
    ap = F.esegui("fascicolo_apri", {"fascicolo": COD})
    r = righe(ap)[0]
    assert campo(r, "id") and campo(r, "chiave") == "budget_intervento" and campo(r, "rev") == "1" and campo(r, "stato") == "attuale"
    assert "origine=dichiarato_utente" in r and "fonti=utente" in r and "verifica=non_verificato" in r
    # una proposta collegata mostra l'id del record che vuole sostituire; dopo la conferma, il vecchio mostra «sostituito da»
    vid = campo(r, "id")
    ctx("A", utente="salva la revisione")
    out = F.esegui("fascicolo_salva", {"fascicolo": COD, "voci": [{"tipo": "dato", "chiave": "budget_intervento", "testo": "Budget previsto per l'intervento", "valore": "11.000 €"}]})
    pid = re.search(r"PROPOSTA (\w{8})", out).group(1)
    ap = F.esegui("fascicolo_apri", {"fascicolo": COD})
    rp = [x for x in righe(ap) if campo(x, "id") == pid][0]
    assert f"propone di sostituire {vid}" in rp and campo(rp, "chiave") == "budget_intervento"
    ctx("A", utente="Sì, conferma la sostituzione")
    assert F.esegui("fascicolo_voce", {"fascicolo": COD, "azione": "sostituisci", "record": pid, "motivo": "nuova stima"}).startswith("ESITO: ok")
    st = F.esegui("fascicolo_voce", {"fascicolo": COD, "azione": "storico", "record": "budget_intervento"})
    assert f"id={vid}" in st and f"sostituito da {pid}" in st and f"sostituisce {vid}" in st and st.count("chiave=budget_intervento") >= 2


def test_aggiorna_per_chiave_esatta_senza_indovinare(db):
    crea(db)
    ctx("A", utente="Sì, aggiorna il budget a 12.500")
    base = {"fascicolo": COD, "valore": "12.500 €", "motivo": "nuova stima"}
    # chiave quasi giusta: NON si approssima
    out = F.esegui("fascicolo_aggiorna", {**base, "chiave": "budget_interventi"})
    assert out.startswith("ESITO: errore NON_TROVATO") and len(db.d[F.T_VOCI]) == 1 and db.d[F.T_VOCI][0]["valore"] == "10.000 €"
    out = F.esegui("fascicolo_aggiorna", {**base, "chiave": "budget_intervento"})
    assert out.startswith("ESITO: ok") and len(db.d[F.T_VOCI]) == 1 and db.d[F.T_VOCI][0]["valore"] == "12.500 €"
    # due record attivi con la stessa chiave → AMBIGUO, nessuna scelta a caso
    db.d[F.T_VOCI].append({**db.d[F.T_VOCI][0], "id": "ffffffff-0000-4000-8000-000000000000"})
    out = F.esegui("fascicolo_aggiorna", {**base, "valore": "13.000 €", "chiave": "budget_intervento"})
    assert out.startswith("ESITO: errore AMBIGUO") and "ffffffff" in out and all(v["valore"] == "12.500 €" for v in db.d[F.T_VOCI])


def test_e2e_backend_nuovo_fascicolo_isolato_otto_passi(db):
    # 1-2 crea e recupera id/chiave
    crea(db)
    r = righe(F.esegui("fascicolo_apri", {"fascicolo": COD}))[0]
    vid, chiave = campo(r, "id"), campo(r, "chiave")
    assert vid and chiave == "budget_intervento"
    # 3 aggiorna per ID  4 verifica il nuovo valore
    ctx("A", utente="Sì, aggiorna il budget a 12.500")
    a = {"fascicolo": COD, "record": vid, "valore": "12.500 €", "motivo": "nuova stima interna", "revisione_attesa": 1}
    assert F.esegui("fascicolo_aggiorna", a).startswith("ESITO: ok")
    r2 = righe(F.esegui("fascicolo_apri", {"fascicolo": COD}))
    assert len(r2) == 1 and campo(r2[0], "id") == vid and "= 12.500 €" in r2[0] and campo(r2[0], "rev") == "2"
    # 5 valore precedente dallo storico
    st = F.esegui("fascicolo_voce", {"fascicolo": COD, "azione": "storico", "record": vid})
    assert "10.000 €" in st and "VALORI PRECEDENTI" in st
    # 6 nessun duplicato indipendente
    assert len(db.d[F.T_VOCI]) == 1 and F.esegui("fascicolo_duplicati", {"fascicolo": COD, "azione": "elenca"}) == "Nessun duplicato."
    # 7 idempotenza (anche con la revisione vecchia: il valore c'è già → nessuna modifica; con salva → già presente)
    out = F.esegui("fascicolo_aggiorna", {**a, "revisione_attesa": 2})
    assert out.startswith("ESITO: ok (idempotente)")
    ctx("A", utente="salva anche questo")
    assert "1 già presenti" in F.esegui("fascicolo_salva", {"fascicolo": COD, "voci": [{"tipo": "dato", "chiave": "budget_intervento", "testo": "Budget previsto per l'intervento", "valore": "12.500 €"}]})
    assert len(db.d[F.T_VOCI]) == 1
    # 8 nuova conversazione: ricarica da zero, stessi id/chiave/valore/storico, ripetizione idempotente
    ctx("A", utente="Sì, aggiorna a 12.500", collected={}, sess="s-nuova")
    r3 = righe(F.esegui("fascicolo_apri", {"fascicolo": COD}))[0]
    assert campo(r3, "id") == vid and campo(r3, "chiave") == chiave and "12.500 €" in r3
    assert F.esegui("fascicolo_aggiorna", {**a, "revisione_attesa": None}).startswith("ESITO: ok (idempotente)")
    assert "10.000 €" in F.esegui("fascicolo_voce", {"fascicolo": COD, "azione": "storico", "record": vid})
    assert len(db.d[F.T_VOCI]) == 1 and db.d[F.T_VOCI][0]["revisione"] == 2


# ── dichiarazioni del modello ───────────────────────────────────────────────────────────────────────────
def test_dichiarazione_di_salvataggio_senza_strumento_riuscito_viene_segnalata(db):
    crea(db)
    ctx("A", utente="Sì, aggiorna")
    # tentativo fallito (id inesistente) + il modello scrive comunque «ho aggiornato»
    F.esegui("fascicolo_aggiorna", {"fascicolo": COD, "record": "zzzzzzzz", "valore": "1", "motivo": "x"})
    out = F.verifica_dichiarazioni("Ho aggiornato il budget nel fascicolo a 12.500 €.")
    assert "Nota del sistema" in out and "ESITO: errore NON_TROVATO" in out
    # nessuno strumento chiamato
    ctx("A", utente="Sì")
    assert "Nessuno strumento di scrittura è stato eseguito" in F.verifica_dichiarazioni("Il record è stato salvato correttamente nel fascicolo.")
    assert "Nota del sistema" in F.verifica_dichiarazioni("Ho consultato il fascicolo e ho trovato tre record.")
    # con uno strumento riuscito non si aggiunge nulla
    ctx("A", utente="Sì, aggiorna il budget a 9.000")
    vid = campo(righe(F.esegui("fascicolo_apri", {"fascicolo": COD}))[0], "id")
    F.esegui("fascicolo_aggiorna", {"fascicolo": COD, "record": vid, "valore": "9.000 €", "motivo": "x"})
    assert F.verifica_dichiarazioni("Ho aggiornato il budget nel fascicolo: ora è 9.000 €.") == "Ho aggiornato il budget nel fascicolo: ora è 9.000 €."
    # frasi non pertinenti o riferite al passato non scattano
    ctx("A", utente="ciao")
    assert F.verifica_dichiarazioni("Ho creato una bozza della lettera.") == "Ho creato una bozza della lettera."
    assert F.verifica_dichiarazioni("Prima ho salvato il budget nel fascicolo.") == "Prima ho salvato il budget nel fascicolo."


def test_le_letture_non_contano_come_scrittura(db):
    crea(db)
    ctx("A", utente="mostrami il fascicolo")
    F.esegui("fascicolo_apri", {"fascicolo": COD})
    out = F.verifica_dichiarazioni("Ho salvato il nuovo importo nel fascicolo.")
    assert "Nota del sistema" in out                                   # aprire non è salvare
    assert "Nota del sistema" not in F.verifica_dichiarazioni("Ho consultato il fascicolo: il budget è 10.000 €.")
