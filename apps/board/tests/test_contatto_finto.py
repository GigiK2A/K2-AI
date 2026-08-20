"""Un lead con `test@…` è un lead che non esiste.

Nel dibattito del 20 ago Vendite proponeva `test@k2ai.com` come contatto di un lead.
Non è un segnaposto di template (`{{email}}`), quindi passava il guardrail esistente.
Il rischio non è la riga sporca: è una campagna che parte verso indirizzi inventati.

Il confine è delicato in Italia: `mail@`, `info@`, `nome.cognome@` sono indirizzi
normalissimi e devono passare. Qui si bloccano solo quelli da manuale d'istruzioni.
"""
import pytest

from aios.actuator import ActuatorError, apply_action, contatto_finto, validate


def _azione(dati, tabella="marketing_prospects", op="insert"):
    return {"tabella": tabella, "op": op, "dati": dati}


# ---- cosa si blocca ----
@pytest.mark.parametrize("mail", [
    "test@k2ai.com",           # il caso reale
    "prova@qualcosa.it",
    "esempio@azienda.it",
    "example@example.com",
    "demo@dominio.it",
    "nome@azienda.it",
    "tuaemail@gmail.com",
    "info@example.org",
    "commerciale@test.it",
])
def test_contatti_da_manuale_rifiutati(mail):
    with pytest.raises(ActuatorError, match="contatto d'esempio"):
        validate(_azione({"company": "Alfa", "contact_email": mail}))


# ---- cosa NON si blocca: indirizzi italiani veri ----
@pytest.mark.parametrize("mail", [
    "info@modulonet.com",                      # prospect veri trovati in Umbria
    "commerciale@euromeccanicasrl.net",
    "mail@carpenteria.it",                     # «mail@» è comunissimo, non è un esempio
    "nome.cognome@studiolegale.it",            # inizia per «nome.», non «nome@»
    "amministrazione@testasrl.it",             # «test» dentro un nome vero
    "protesting@azienda-vera.it",
    "rluigiluca@gmail.com",
])
def test_indirizzi_veri_passano(mail):
    tab, op, _m, dati = validate(_azione({"company": "Alfa", "contact_email": mail}))
    assert (tab, op) == ("marketing_prospects", "insert")
    assert dati["contact_email"] == mail


def test_solo_i_campi_di_contatto():
    """«test» nel nome di una campagna A/B è testo legittimo, non un contatto."""
    assert contatto_finto({"name": "test@ nuovo copy", "note": "prova@invio"}) is None
    assert contatto_finto({"contact_email": "test@k2ai.com"}) == "test@k2ai.com"


def test_il_campo_to_di_una_email_conta():
    """È `to` il campo di una email che parte: va guardato per chiave esatta, perché
    come sottostringa prenderebbe «totale» e «photo_url»."""
    assert contatto_finto({"to": "test@k2ai.com"}) == "test@k2ai.com"
    assert contatto_finto({"cc": "demo@example.com"}) == "demo@example.com"
    assert contatto_finto({"totale": "test@k2ai.com"}) is None      # non è un contatto
    assert contatto_finto({"photo_url": "prova@x.it"}) is None


def test_annidato_lo_trova():
    assert contatto_finto({"payload": {"destinatario": "demo@example.com"}}) \
        == "demo@example.com"
    assert contatto_finto([{"contact_email": "a@vera.it"},
                           {"contact_email": "test@k2ai.com"}]) == "test@k2ai.com"


def test_niente_contatti_niente_falsi_positivi():
    assert contatto_finto({}) is None
    assert contatto_finto({"company": "Test Srl"}) is None
    assert contatto_finto("test@k2ai.com") is None      # stringa nuda: nessun campo


# ---- verso l'esterno non parte, e lo dice ----
def test_un_invio_a_un_destinatario_finto_non_parte(monkeypatch):
    """Peggio di una riga sporca: una email vera a un indirizzo inventato."""
    chiamate = []
    import aios.sources.n8n as n8n
    monkeypatch.setattr(n8n, "trigger_n8n",
                        lambda wf, p: chiamate.append((wf, p)) or {"ok": True})
    out = apply_action(None, {"canale": "n8n", "workflow": "k2ai",
                              "payload": {"to": "cliente@vero.it", "subject": "s",
                                          "destinatario": "test@k2ai.com"}})
    assert out["ok"] is False
    assert "d'esempio" in out["errore"] and "test@k2ai.com" in out["errore"]
    assert chiamate == []                       # n8n non è stato chiamato
