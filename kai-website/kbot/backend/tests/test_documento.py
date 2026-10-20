"""Documento separato dalla conversazione (marcatori nello stream e nel messaggio salvato)."""
import pytest

from app.lib import documento as D

MSG = ("Ecco la PEC. Controlla i dati prima dell'invio.\n\n<<<DOCUMENTO: PEC di contestazione>>>\nOggetto: contestazione fattura\n\n"
       "Spett.le DemoSoft S.r.l., con la presente contestiamo le difformità del gestionale.\n<<<FINE DOCUMENTO>>>\n\n"
       "Verifica: il numero di fattura e la data del contratto.")


def test_estrai_un_blocco_completo():
    b = D.estrai(MSG)
    assert len(b) == 1 and b[0]["titolo"] == "PEC di contestazione" and b[0]["completo"]
    assert b[0]["testo"].startswith("Oggetto: contestazione fattura") and "Verifica" not in b[0]["testo"]


def test_blocco_aperto_durante_lo_stream():
    parziale = "Ecco la PEC.\n\n<<<DOCUMENTO: PEC>>>\nOggetto: contestazione fat"
    b = D.estrai(parziale)
    assert len(b) == 1 and not b[0]["completo"] and b[0]["testo"] == "Oggetto: contestazione fat"


def test_fuori_dal_documento_e_la_conversazione():
    f = D.fuori_dal_documento(MSG)
    assert "Ecco la PEC" in f and "Verifica: il numero" in f and "Spett.le" not in f and "<<<" not in f


def test_conversazione_con_blocco_aperto_non_mostra_il_documento():
    assert "Oggetto" not in D.fuori_dal_documento("Ecco.\n\n<<<DOCUMENTO: x>>>\nOggetto: contesta")


def test_piu_versioni_ultimo_documento():
    t = MSG + "\n\n<<<DOCUMENTO: PEC di contestazione>>>\nVersione 2 aggiornata\n<<<FINE DOCUMENTO>>>"
    assert len(D.estrai(t)) == 2 and D.ultimo_documento(t)["testo"] == "Versione 2 aggiornata"


def test_senza_marcatori_nessun_blocco():
    assert D.estrai("Solo conversazione, nessun documento.") == [] and D.ultimo_documento("") is None


def test_marcatori_tollerati_con_spazi_e_maiuscole():
    b = D.estrai("<<< documento : Lettera >>>\nTesto\n<<< fine documento >>>")
    assert b and b[0]["titolo"] == "Lettera" and b[0]["completo"]


@pytest.mark.parametrize("t,atteso", [
    ("Scrivimi una PEC per contestare il software difettoso", True),
    ("Genera un documento interno di valutazione dell'incidente", True),
    ("Prepara il registro interno dei data breach", True),
    ("Redigi un verbale di consegna", True),
    ("Fammi una lettera di diffida", True),
    ("Genera il report di analisi del bilancio", False),
    ("Fai il report", False),
    ("Crea un piano di marketing in pdf", False),
    ("Posso sospendere il pagamento della fattura?", False),
    ("", False),
])
def test_richiesta_documento(t, atteso):
    assert D.richiesta_documento(t) is atteso


def test_proteggi_e_ripristina_sono_inversi_e_il_testo_protetto_non_ha_tag():
    t, m = D.proteggi(MSG)
    assert "<<<" not in t and ">>>" not in t and D.ripristina(t, m) == MSG
