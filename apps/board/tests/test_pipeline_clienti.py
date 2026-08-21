"""La tabella clienti si aggiorna dalla posta, e solo per fatti.

Un lead creato `nuovo` resta `nuovo` per sempre se nessuno lo muove: dopo due settimane
la pipeline dice «dieci lead nuovi» e non è vero per nessuno. Qui lo stato lo muove la
posta — ma solo dove c'è un fatto (è arrivata un'email, ne è partita una), non
un'interpretazione: capire se un cliente è INTERESSATO è lavoro dell'agente che legge
il testo, e uno stato inventato è peggio di uno stato indietro.
"""
from aios.pipeline_clienti import (STATI, accoppia, aggiorna_da_email, prossimo_stato,
                                   tabella)


class Client:
    def __init__(self, lead=None, email=None, rompi=None):
        self.lead = list(lead or [])
        self.email = list(email or [])
        self.patch = []
        self.rompi = rompi

    def select(self, tabella, params):
        if self.rompi == tabella:
            raise RuntimeError("connessione persa")
        return self.lead if tabella == "pipeline_leads" else self.email

    def update(self, tabella, filtri, patch):
        self.patch.append((filtri, patch))
        return [patch]


def _lead(nome, email, stato="nuovo", id_=None):
    return {"id": id_ or nome.lower(), "name": nome, "email": email, "status": stato}


def _msg(direzione="in", mittente=None, subject="Re: proposta", body="", quando="2026-08-21"):
    return {"id": subject, "from_email": mittente, "subject": subject, "body": body,
            "direction": direzione, "created_at": quando}


# ---- gli stati sono un contratto, non una convenzione ----
def test_gli_stati_sono_dichiarati_e_in_ordine():
    assert STATI[0] == "nuovo" and STATI[-1] == "scartato"
    for atteso in ("contattato", "risposto", "interessato", "riunione", "proposta",
                   "cliente", "perso"):
        assert atteso in STATI


# ---- accoppiamento email → lead ----
def test_accoppia_per_indirizzo_esatto():
    lead = [_lead("Modulo", "info@modulonet.com"), _lead("Alfa", "a@alfa.it")]
    assert accoppia(_msg(mittente="info@modulonet.com"), lead)["name"] == "Modulo"


def test_accoppia_per_dominio():
    """`commerciale@modulonet.com` e `info@modulonet.com` sono la stessa azienda."""
    lead = [_lead("Modulo", "info@modulonet.com")]
    assert accoppia(_msg(mittente="commerciale@modulonet.com"), lead)["name"] == "Modulo"


def test_i_domini_generici_non_accoppiano():
    """Due lead diversi possono avere entrambi una @gmail.com: il dominio non basta."""
    lead = [_lead("Alfa", "mario@gmail.com")]
    assert accoppia(_msg(mittente="giulia@gmail.com"), lead) is None
    # l'indirizzo esatto invece sì
    assert accoppia(_msg(mittente="mario@gmail.com"), lead)["name"] == "Alfa"


def test_senza_mittente_si_cerca_nel_testo():
    """Limite noto: n8n lascia from_email a NULL. Nel frattempo si prende quello che si
    trova nel corpo, senza indovinare."""
    lead = [_lead("Modulo", "info@modulonet.com")]
    m = _msg(mittente=None, subject="Re: automazioni",
             body="Buongiorno, la ricontatto io. info@modulonet.com")
    assert accoppia(m, lead)["name"] == "Modulo"


def test_mai_accoppiare_per_nome_azienda():
    """«Modulo» dentro una newsletter accoppierebbe a caso."""
    lead = [_lead("Modulo", "info@modulonet.com")]
    assert accoppia(_msg(mittente=None, subject="Il modulo di iscrizione",
                         body="compila il modulo"), lead) is None


# ---- le transizioni: solo fatti ----
def test_una_risposta_porta_a_risposto():
    assert prossimo_stato("nuovo", "in") == "risposto"
    assert prossimo_stato("contattato", "in") == "risposto"


def test_una_nostra_email_porta_a_contattato():
    assert prossimo_stato("nuovo", "out") == "contattato"


def test_una_nostra_email_non_declassa_chi_ha_risposto():
    assert prossimo_stato("risposto", "out") is None
    assert prossimo_stato("interessato", "out") is None


def test_dagli_stati_chiusi_non_si_torna_per_un_email():
    """Una firma non si annulla perché arriva una newsletter."""
    for chiuso in ("cliente", "perso", "scartato"):
        assert prossimo_stato(chiuso, "in") is None
        assert prossimo_stato(chiuso, "out") is None


def test_gli_stati_di_giudizio_non_sono_automatici():
    """`interessato`, `riunione`, `proposta` richiedono di CAPIRE l'email: li propone
    l'agente, non questo codice. Quindi una seconda risposta non fa avanzare nulla."""
    assert prossimo_stato("risposto", "in") is None
    assert prossimo_stato("interessato", "in") is None


def test_una_seconda_risposta_aggiorna_almeno_la_data():
    """Lo stato non cambia, ma «quando l'abbiamo sentito» è ciò che dice quali lead
    stanno morendo: senza questo la pipeline non distingue un lead vivo da uno fermo."""
    c = Client(lead=[_lead("Modulo", "info@modulonet.com", "risposto")],
               email=[_msg(mittente="info@modulonet.com", subject="Re: ancora io",
                           quando="2026-08-21")])
    out = aggiorna_da_email(c)
    assert out["aggiornati"] == []                       # nessun avanzamento inventato
    assert out["contatti_registrati"][0]["lead"] == "Modulo"
    _filtri, patch = c.patch[0]
    assert patch == {"last_contact_at": "2026-08-21"}    # solo la data


def test_su_un_lead_chiuso_non_si_scrive_niente():
    c = Client(lead=[_lead("Modulo", "info@modulonet.com", "cliente")],
               email=[_msg(mittente="info@modulonet.com")])
    out = aggiorna_da_email(c)
    assert c.patch == [] and out["aggiornati"] == [] and out["contatti_registrati"] == []


# ---- il giro completo ----
def test_aggiorna_e_riporta_cosa_ha_cambiato():
    c = Client(lead=[_lead("Modulo", "info@modulonet.com"), _lead("Alfa", "a@alfa.it")],
               email=[_msg(mittente="info@modulonet.com", subject="Re: proposta")])
    out = aggiorna_da_email(c)
    assert out["accoppiate"] == 1 and len(out["aggiornati"]) == 1
    assert out["aggiornati"][0] == {"lead": "Modulo", "da": "nuovo", "a": "risposto",
                                    "email": "Re: proposta"}
    filtri, patch = c.patch[0]
    assert filtri == {"id": "eq.modulo"}
    assert patch["status"] == "risposto" and patch["last_contact_at"] == "2026-08-21"


def test_un_lead_si_muove_una_volta_per_giro():
    c = Client(lead=[_lead("Modulo", "info@modulonet.com")],
               email=[_msg(mittente="info@modulonet.com", subject="prima"),
                      _msg(mittente="info@modulonet.com", subject="seconda")])
    aggiorna_da_email(c)
    assert len(c.patch) == 1


def test_le_email_senza_mittente_sono_contate_non_nascoste():
    """È l'informazione che serve: oggi in produzione sono TUTTE così."""
    c = Client(lead=[_lead("Modulo", "info@modulonet.com")],
               email=[_msg(mittente=None, subject="Novità dal mondo dell'AI", body="")])
    out = aggiorna_da_email(c)
    assert out["senza_mittente"] == 1 and out["aggiornati"] == []
    assert c.patch == []


def test_un_errore_di_lettura_non_ferma_il_giro():
    out = aggiorna_da_email(Client(rompi="pipeline_leads"))
    assert out["errori"] and "connessione persa" in out["errori"][0]
    assert out["aggiornati"] == []


def test_senza_lead_lo_dice():
    out = aggiorna_da_email(Client(lead=[], email=[_msg()]))
    assert "nessun lead con email" in out["errori"][0]


def test_un_update_che_fallisce_finisce_negli_errori():
    class Rotto(Client):
        def update(self, *a, **kw):
            raise RuntimeError("400 Bad Request")

    c = Rotto(lead=[_lead("Modulo", "info@modulonet.com")],
              email=[_msg(mittente="info@modulonet.com")])
    out = aggiorna_da_email(c)
    assert out["aggiornati"] == [] and "400" in out["errori"][0]


# ---- la tabella ----
def test_la_tabella_conta_per_stato():
    c = Client(lead=[_lead("A", "a@a.it", "nuovo"), _lead("B", "b@b.it", "risposto"),
                     _lead("C", "c@c.it", "cliente"), _lead("D", "d@d.it", "perso")])
    t = tabella(c)
    assert t["totale"] == 4
    assert t["per_stato"] == {"nuovo": 1, "risposto": 1, "cliente": 1, "perso": 1}
    assert t["aperti"] == 2                      # cliente e perso sono chiusi
    assert t["stati_possibili"] == list(STATI)


def test_le_righe_di_sonda_non_entrano_nella_tabella():
    c = Client(lead=[_lead("Alfa", "a@a.it"), _lead("Sonda rollback", "x@x.it")])
    assert tabella(c)["totale"] == 1


def test_una_tabella_illeggibile_lo_dice():
    t = tabella(Client(rompi="pipeline_leads"))
    assert "errore" in t and t["righe"] == []
